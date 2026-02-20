"""BLE API client for the ChefSteps Joule Sous Vide.

All methods are synchronous and must be
called via hass.async_add_executor_job() from an async context.
"""
from __future__ import annotations

import asyncio
import logging
from threading import Lock, Thread
from typing import Any, Callable

from bleak import BleakClient
from bleak.exc import BleakError

from .const import (
    READ_CHAR_UUID,
    SUBSCRIBE_CHAR_UUID,
    WRITE_CHAR_UUID,
)

_LOGGER = logging.getLogger(__name__)


class JouleBLEError(Exception):
    """Raised for any BLE communication failure with the Joule device."""


class JouleBLEAPI:
    """Manages the BLE connection and GATT characteristic I/O."""

    def __init__(self, mac_address: str) -> None:
        self.mac_address = mac_address
        self._client: BleakClient | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: Thread | None = None
        self._lock = Lock()

    def _ensure_event_loop(self) -> None:
        """Start a dedicated event loop thread for bleak operations."""
        with self._lock:
            if self._loop is not None and self._thread is not None and self._thread.is_alive():
                return

            loop = asyncio.new_event_loop()

            def _runner() -> None:
                asyncio.set_event_loop(loop)
                loop.run_forever()

            thread = Thread(target=_runner, name="joule-ble-loop", daemon=True)
            thread.start()
            self._loop = loop
            self._thread = thread

    def _stop_event_loop(self) -> None:
        """Stop and clean up the dedicated bleak event loop thread."""
        with self._lock:
            loop = self._loop
            thread = self._thread
            self._loop = None
            self._thread = None

        if loop is not None:
            loop.call_soon_threadsafe(loop.stop)
        if thread is not None:
            thread.join(timeout=1.0)
        if loop is not None and not loop.is_closed():
            loop.close()

    def _run_coro(self, coro: Any) -> Any:
        """Run a coroutine on the dedicated event loop and block for result."""
        self._ensure_event_loop()
        if self._loop is None:
            raise JouleBLEError("BLE event loop was not initialized")
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result()

    async def _connect_async(self) -> None:
        """Open a BLE connection if not already connected."""
        if self._client is not None and self._client.is_connected:
            return

        if self._client is None:
            self._client = BleakClient(self.mac_address)

        await self._client.connect()

    async def _disconnect_async(self) -> None:
        """Close the BLE connection if one exists."""
        if self._client is None:
            return

        if self._client.is_connected:
            try:
                await self._client.stop_notify(SUBSCRIBE_CHAR_UUID)
            except BleakError:
                pass
            await self._client.disconnect()

        self._client = None

    def ensure_connected(self) -> None:
        """Connect to the device if not already connected."""
        if self._client is None or not self._client.is_connected:
            self.connect()

    def connect(self) -> None:
        """Open a BLE connection to the device."""
        try:
            self._run_coro(self._connect_async())
            _LOGGER.info("Connected to Joule at %s", self.mac_address)
        except (BleakError, Exception) as err:  # noqa: BLE001
            self._client = None
            raise JouleBLEError(f"Failed to connect to {self.mac_address}") from err

    def disconnect(self) -> None:
        """Close the BLE connection and stop the BLE event loop."""
        try:
            self._run_coro(self._disconnect_async())
        except (BleakError, Exception) as err:  # noqa: BLE001
            _LOGGER.warning("Error during disconnect from %s: %s", self.mac_address, err)
        finally:
            self._stop_event_loop()

    def write_message(self, payload: bytes) -> None:
        """Write a protobuf-encoded message to the device."""
        try:
            self._run_coro(self._write_message_async(payload))
        except (BleakError, Exception) as err:  # noqa: BLE001
            raise JouleBLEError("Failed to write message to Joule") from err

    async def _write_message_async(self, payload: bytes) -> None:
        """Coroutine implementation for writing to the Joule characteristic."""
        if self._client is None or not self._client.is_connected:
            raise JouleBLEError("Not connected to Joule")
        await self._client.write_gatt_char(WRITE_CHAR_UUID, payload, response=False)

    def read_message(self) -> bytes:
        """Read a protobuf-encoded response from the device."""
        try:
            return self._run_coro(self._read_message_async())
        except (BleakError, Exception) as err:  # noqa: BLE001
            raise JouleBLEError("Failed to read message from Joule") from err

    async def _read_message_async(self) -> bytes:
        """Coroutine implementation for reading from the Joule characteristic."""
        if self._client is None or not self._client.is_connected:
            raise JouleBLEError("Not connected to Joule")
        return bytes(await self._client.read_gatt_char(READ_CHAR_UUID))

    def subscribe(self, callback) -> None:
        """Subscribe to notifications on the subscribe characteristic.

        ``callback`` is called with ``(handle, value)`` for each notification.
        """
        try:
            self._run_coro(self._subscribe_async(callback))
        except (BleakError, Exception) as err:  # noqa: BLE001
            raise JouleBLEError("Failed to subscribe to Joule notifications") from err

    async def _subscribe_async(self, callback: Callable[[int, bytes], None]) -> None:
        """Coroutine implementation for notification subscription."""
        if self._client is None or not self._client.is_connected:
            raise JouleBLEError("Not connected to Joule")

        def _bleak_callback(sender: Any, data: bytearray) -> None:
            handle = sender if isinstance(sender, int) else getattr(sender, "handle", 0)
            callback(handle, bytes(data))

        await self._client.start_notify(SUBSCRIBE_CHAR_UUID, _bleak_callback)
