"""BLE API client for the ChefSteps Joule Sous Vide.

All methods are synchronous (pygatt is a blocking library) and must be
called via hass.async_add_executor_job() from an async context.
"""
from __future__ import annotations

import logging

import pygatt

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
        self._adapter = pygatt.GATTToolBackend()
        self._device = None

    def ensure_connected(self) -> None:
        """Connect to the device if not already connected."""
        if self._device is None:
            self.connect()

    def connect(self) -> None:
        """Start the GATT adapter and open a BLE connection to the device."""
        try:
            self._adapter.start()
            self._device = self._adapter.connect(self.mac_address)
            _LOGGER.info("Connected to Joule at %s", self.mac_address)
        except pygatt.exceptions.BLEError as err:
            self._device = None
            raise JouleBLEError(f"Failed to connect to {self.mac_address}") from err

    def disconnect(self) -> None:
        """Close the BLE connection and stop the GATT adapter."""
        try:
            if self._device is not None:
                self._device.disconnect()
                self._device = None
            self._adapter.stop()
        except pygatt.exceptions.BLEError as err:
            _LOGGER.warning("Error during disconnect from %s: %s", self.mac_address, err)

    def write_message(self, payload: bytes) -> None:
        """Write a protobuf-encoded message to the device."""
        try:
            self._device.char_write(WRITE_CHAR_UUID, bytearray(payload))
        except pygatt.exceptions.BLEError as err:
            raise JouleBLEError("Failed to write message to Joule") from err

    def read_message(self) -> bytes:
        """Read a protobuf-encoded response from the device."""
        try:
            return bytes(self._device.char_read(READ_CHAR_UUID))
        except pygatt.exceptions.BLEError as err:
            raise JouleBLEError("Failed to read message from Joule") from err

    def subscribe(self, callback) -> None:
        """Subscribe to notifications on the subscribe characteristic.

        ``callback`` is called with ``(handle, value)`` for each notification.
        """
        try:
            self._device.subscribe(SUBSCRIBE_CHAR_UUID, callback=callback)
        except pygatt.exceptions.BLEError as err:
            raise JouleBLEError("Failed to subscribe to Joule notifications") from err
