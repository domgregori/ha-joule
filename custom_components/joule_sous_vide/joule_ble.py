"""BLE API client for the ChefSteps Joule Sous Vide.

All methods are synchronous (pygatt is a blocking library) and must be
called via hass.async_add_executor_job() from an async context.
"""
from __future__ import annotations

import logging

import pygatt

from .const import (
    CURRENT_TEMP_CHAR_UUID,
    START_STOP_CHAR_UUID,
    TEMPERATURE_CHAR_UUID,
    TIME_CHAR_UUID,
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

    def set_temperature(self, temperature: float) -> None:
        """Write the target temperature to the device.

        Converts °C to centidegrees and encodes as a 2-byte little-endian integer.
        """
        try:
            value = int(temperature * 100)
            self._device.char_write(TEMPERATURE_CHAR_UUID, value.to_bytes(2, "little"))
        except pygatt.exceptions.BLEError as err:
            raise JouleBLEError(f"Failed to set temperature to {temperature}°C") from err

    def set_cook_time(self, time_minutes: float) -> None:
        """Write the cook duration to the device.

        Converts minutes to seconds and encodes as a 4-byte little-endian integer.
        """
        try:
            value = int(time_minutes * 60)
            self._device.char_write(TIME_CHAR_UUID, value.to_bytes(4, "little"))
        except pygatt.exceptions.BLEError as err:
            raise JouleBLEError(f"Failed to set cook time to {time_minutes} minutes") from err

    def start_cooking(self) -> None:
        """Write 0x01 to the start/stop characteristic to begin cooking."""
        try:
            self._device.char_write(START_STOP_CHAR_UUID, bytearray([0x01]))
        except pygatt.exceptions.BLEError as err:
            raise JouleBLEError("Failed to start cooking") from err

    def stop_cooking(self) -> None:
        """Write 0x00 to the start/stop characteristic to stop cooking."""
        try:
            self._device.char_write(START_STOP_CHAR_UUID, bytearray([0x00]))
        except pygatt.exceptions.BLEError as err:
            raise JouleBLEError("Failed to stop cooking") from err

    def get_current_temperature(self) -> float:
        """Read the current water temperature from the device.

        Returns temperature in °C. The device encodes it as centidegrees in a
        little-endian integer.
        """
        try:
            raw = self._device.char_read(CURRENT_TEMP_CHAR_UUID)
            return int.from_bytes(raw, "little") / 100
        except pygatt.exceptions.BLEError as err:
            raise JouleBLEError("Failed to read current temperature") from err
