"""Data update coordinator for the Joule Sous Vide integration."""
from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_MAC_ADDRESS,
    DEFAULT_COOK_TIME_MINUTES,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_TARGET_TEMPERATURE,
    DEFAULT_TEMPERATURE_UNIT,
    DOMAIN,
)
from .joule_ble import JouleBLEAPI, JouleBLEError

_LOGGER = logging.getLogger(__name__)


class JouleCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Single owner of the BLE connection; provides data to all entities.

    Entities must not create their own BLE connections. They read exclusively
    from coordinator.data and call coordinator methods for control actions.

    Polling fetches the current water temperature. Cooking state is tracked
    internally since the device does not expose a readable cooking-status
    characteristic.
    """

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.api = JouleBLEAPI(entry.data[CONF_MAC_ADDRESS])
        self._is_cooking: bool = False
        self._target_temperature: float = DEFAULT_TARGET_TEMPERATURE  # always °C
        self._cook_time_minutes: float = DEFAULT_COOK_TIME_MINUTES
        self._temperature_unit: str = DEFAULT_TEMPERATURE_UNIT

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Poll the device for the current temperature.

        Reconnects automatically if the BLE connection has dropped.
        Raises UpdateFailed on any BLE error, which causes CoordinatorEntity
        to mark all dependent entities as unavailable.
        """
        try:
            await self.hass.async_add_executor_job(self.api.ensure_connected)
            current_temperature = await self.hass.async_add_executor_job(
                self.api.get_current_temperature
            )
        except JouleBLEError as err:
            raise UpdateFailed(f"BLE communication failed: {err}") from err

        return {
            "current_temperature": current_temperature,
            "is_cooking": self._is_cooking,
            "target_temperature": self._target_temperature,  # °C
            "cook_time_minutes": self._cook_time_minutes,
            "temperature_unit": self._temperature_unit,
        }

    async def async_start_cooking(
        self, target_temperature: float, cook_time_minutes: float
    ) -> None:
        """Write temperature/time settings to the device and start cooking."""
        self._target_temperature = target_temperature
        self._cook_time_minutes = cook_time_minutes
        try:
            await self.hass.async_add_executor_job(self.api.ensure_connected)
            await self.hass.async_add_executor_job(
                self.api.set_temperature, target_temperature
            )
            await self.hass.async_add_executor_job(
                self.api.set_cook_time, cook_time_minutes
            )
            await self.hass.async_add_executor_job(self.api.start_cooking)
        except JouleBLEError as err:
            raise HomeAssistantError(f"Failed to start cooking: {err}") from err

        self._is_cooking = True
        await self.async_refresh()

    async def async_set_target_temperature(self, value_celsius: float) -> None:
        """Update the target temperature (always in °C) without starting a cook."""
        self._target_temperature = value_celsius
        await self.async_refresh()

    async def async_set_temperature_unit(self, unit: str) -> None:
        """Update the display unit preference without affecting the stored °C value."""
        self._temperature_unit = unit
        await self.async_refresh()

    async def async_set_cook_time(self, value: float) -> None:
        """Update the cook time without starting a cook."""
        self._cook_time_minutes = value
        await self.async_refresh()

    async def async_stop_cooking(self) -> None:
        """Stop the cooking cycle."""
        try:
            await self.hass.async_add_executor_job(self.api.ensure_connected)
            await self.hass.async_add_executor_job(self.api.stop_cooking)
        except JouleBLEError as err:
            raise HomeAssistantError(f"Failed to stop cooking: {err}") from err

        self._is_cooking = False
        await self.async_refresh()
