"""Data update coordinator for the Joule Sous Vide integration."""
from __future__ import annotations

import asyncio
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
from .joule_proto import (
    CirculatorDataPoint,
    ProgramStep,
    build_live_feed_message,
    build_start_cook_message,
    build_stop_cook_message,
    parse_notification,
)

_LOGGER = logging.getLogger(__name__)


class JouleCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Single owner of the BLE connection; provides data to all entities.

    Entities must not create their own BLE connections. They read exclusively
    from coordinator.data and call coordinator methods for control actions.

    Polling sends a BeginLiveFeedRequest and waits for a CirculatorDataPoint
    notification containing the current bath temperature and cooking state.
    """

    NOTIFICATION_TIMEOUT: float = 10.0  # seconds; overridden in tests

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self._entry = entry
        self.api = JouleBLEAPI(entry.data[CONF_MAC_ADDRESS])
        self._is_cooking: bool = False
        self._target_temperature: float = DEFAULT_TARGET_TEMPERATURE  # always °C
        self._cook_time_minutes: float = DEFAULT_COOK_TIME_MINUTES
        self._temperature_unit: str = entry.options.get(
            "temperature_unit", DEFAULT_TEMPERATURE_UNIT
        )
        self._latest_data_point: CirculatorDataPoint | None = None
        self._notification_received: asyncio.Event = asyncio.Event()
        self._subscribed: bool = False

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )

    def _on_notification(self, handle: int, value: bytes) -> None:
        """Handle a BLE notification callback from the BLE client thread."""
        data_point = parse_notification(bytes(value))
        if data_point is not None:
            self._latest_data_point = data_point
            self.hass.loop.call_soon_threadsafe(self._notification_received.set)

    async def _async_update_data(self) -> dict[str, Any]:
        """Poll the device for the current temperature.

        Subscribes to notifications on the first poll, then sends a
        BeginLiveFeedRequest to trigger a CirculatorDataPoint notification.
        """
        try:
            await self.hass.async_add_executor_job(self.api.ensure_connected)

            if not self._subscribed:
                await self.hass.async_add_executor_job(
                    self.api.subscribe, self._on_notification
                )
                self._subscribed = True

            self._notification_received.clear()
            payload = build_live_feed_message()
            await self.hass.async_add_executor_job(self.api.write_message, payload)

            try:
                async with asyncio.timeout(self.NOTIFICATION_TIMEOUT):
                    await self._notification_received.wait()
            except TimeoutError:
                _LOGGER.warning("Timed out waiting for data from Joule")

        except JouleBLEError as err:
            raise UpdateFailed(f"BLE communication failed: {err}") from err

        current_temperature: float = 0.0
        if self._latest_data_point is not None:
            current_temperature = self._latest_data_point.bath_temp

            step = self._latest_data_point.program_step
            if step in (
                ProgramStep.PRE_HEAT,
                ProgramStep.WAIT_FOR_FOOD,
                ProgramStep.COOK,
            ):
                self._is_cooking = True
            elif step in (ProgramStep.UNKNOWN, ProgramStep.WAIT_FOR_REMOVE_FOOD):
                self._is_cooking = False

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
        """Send a protobuf StartProgramRequest to the device."""
        self._target_temperature = target_temperature
        self._cook_time_minutes = cook_time_minutes
        try:
            await self.hass.async_add_executor_job(self.api.ensure_connected)
            cook_time_seconds = int(cook_time_minutes * 60)
            payload = build_start_cook_message(target_temperature, cook_time_seconds)
            await self.hass.async_add_executor_job(self.api.write_message, payload)
        except JouleBLEError as err:
            raise HomeAssistantError(f"Failed to start cooking: {err}") from err

        self._is_cooking = True
        await self.async_refresh()

    async def async_set_target_temperature(self, value_celsius: float) -> None:
        """Update the target temperature (always in °C) without starting a cook."""
        self._target_temperature = value_celsius
        await self.async_refresh()

    async def async_set_temperature_unit(self, unit: str) -> None:
        """Update the display unit preference and persist it to the config entry."""
        self._temperature_unit = unit
        self.hass.config_entries.async_update_entry(
            self._entry,
            options={**self._entry.options, "temperature_unit": unit},
        )
        await self.async_refresh()

    async def async_set_cook_time(self, value: float) -> None:
        """Update the cook time without starting a cook."""
        self._cook_time_minutes = value
        await self.async_refresh()

    async def async_stop_cooking(self) -> None:
        """Send a protobuf StopCirculatorRequest to the device."""
        try:
            await self.hass.async_add_executor_job(self.api.ensure_connected)
            payload = build_stop_cook_message()
            await self.hass.async_add_executor_job(self.api.write_message, payload)
        except JouleBLEError as err:
            raise HomeAssistantError(f"Failed to stop cooking: {err}") from err

        self._is_cooking = False
        await self.async_refresh()
