"""Cooking control switch entity for the Joule Sous Vide integration."""
from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DEFAULT_COOK_TIME_MINUTES, DEFAULT_TARGET_TEMPERATURE, DOMAIN
from .coordinator import JouleCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the cooking switch from a config entry."""
    coordinator: JouleCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([JouleSousVideSwitch(coordinator, entry)])


class JouleSousVideSwitch(CoordinatorEntity[JouleCoordinator], SwitchEntity):
    """Controls starting and stopping the sous vide cooking cycle.

    Delegates all BLE operations to the coordinator. State reflects the last
    known cooking status; the device does not expose a readable cooking-status
    characteristic so this is tracked internally by the coordinator.
    """

    _attr_has_entity_name = True
    _attr_name = "Sous Vide"

    def __init__(self, coordinator: JouleCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_switch"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Joule Sous Vide",
            manufacturer="ChefSteps",
            model="Joule",
        )

    @property
    def is_on(self) -> bool:
        """Return True if the device is currently cooking."""
        if self.coordinator.data is None:
            return False
        return bool(self.coordinator.data.get("is_cooking", False))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose target temperature and cook time as additional state attributes."""
        if self.coordinator.data is None:
            return {}
        return {
            "target_temperature": self.coordinator.data.get("target_temperature"),
            "cook_time_minutes": self.coordinator.data.get("cook_time_minutes"),
        }

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Start cooking using the currently stored target temperature and cook time."""
        data = self.coordinator.data or {}
        target_temp = data.get("target_temperature", DEFAULT_TARGET_TEMPERATURE)
        cook_time = data.get("cook_time_minutes", DEFAULT_COOK_TIME_MINUTES)
        await self.coordinator.async_start_cooking(target_temp, cook_time)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Stop the cooking cycle."""
        await self.coordinator.async_stop_cooking()
