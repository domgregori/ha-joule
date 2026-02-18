"""Temperature sensor entity for the Joule Sous Vide integration."""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import JouleCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the temperature sensor from a config entry."""
    coordinator: JouleCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([JouleTemperatureSensor(coordinator, entry)])


class JouleTemperatureSensor(CoordinatorEntity[JouleCoordinator], SensorEntity):
    """Reports the current water temperature read from the Joule device.

    Becomes unavailable automatically when the coordinator fails to poll
    the device (BLE connection lost, device powered off, etc.).
    """

    _attr_has_entity_name = True
    _attr_name = "Current Temperature"
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: JouleCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_current_temperature"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Joule Sous Vide",
            manufacturer="ChefSteps",
            model="Joule",
        )

    @property
    def native_value(self) -> StateType:
        """Return the current temperature from coordinator data."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get("current_temperature")
