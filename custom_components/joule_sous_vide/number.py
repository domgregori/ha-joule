"""Number entities for configuring Joule cooking parameters."""
from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DEFAULT_COOK_TIME_MINUTES,
    DEFAULT_TARGET_TEMPERATURE,
    DOMAIN,
    MAX_COOK_TIME_MINUTES,
    MAX_TARGET_TEMPERATURE,
    MIN_COOK_TIME_MINUTES,
    MIN_TARGET_TEMPERATURE,
    STEP_COOK_TIME_MINUTES,
    STEP_TARGET_TEMPERATURE,
)
from .coordinator import JouleCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the number entities from a config entry."""
    coordinator: JouleCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        JouleTargetTemperatureNumber(coordinator, entry),
        JouleCookTimeNumber(coordinator, entry),
    ])


def _device_info(entry: ConfigEntry) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name="Joule Sous Vide",
        manufacturer="ChefSteps",
        model="Joule",
    )


class JouleTargetTemperatureNumber(CoordinatorEntity[JouleCoordinator], NumberEntity):
    """Sets the water temperature the Joule will heat to when started.

    The value is stored in the coordinator and passed to the device the next
    time the Sous Vide switch is turned on. Changing this entity does not
    affect a cook that is already in progress.
    """

    _attr_has_entity_name = True
    _attr_name = "Target Temperature"
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_native_min_value = MIN_TARGET_TEMPERATURE
    _attr_native_max_value = MAX_TARGET_TEMPERATURE
    _attr_native_step = STEP_TARGET_TEMPERATURE
    _attr_mode = NumberMode.BOX

    def __init__(self, coordinator: JouleCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_target_temperature"
        self._attr_device_info = _device_info(entry)

    @property
    def native_value(self) -> float:
        """Return the current target temperature from coordinator data."""
        if self.coordinator.data is None:
            return DEFAULT_TARGET_TEMPERATURE
        return self.coordinator.data.get("target_temperature", DEFAULT_TARGET_TEMPERATURE)

    async def async_set_native_value(self, value: float) -> None:
        """Update the target temperature in the coordinator."""
        await self.coordinator.async_set_target_temperature(value)


class JouleCookTimeNumber(CoordinatorEntity[JouleCoordinator], NumberEntity):
    """Sets how long the Joule will cook when started.

    A value of 0 means no time limit. The value is stored in the coordinator
    and passed to the device the next time the Sous Vide switch is turned on.
    Changing this entity does not affect a cook that is already in progress.
    """

    _attr_has_entity_name = True
    _attr_name = "Cook Time"
    _attr_native_unit_of_measurement = "min"
    _attr_native_min_value = MIN_COOK_TIME_MINUTES
    _attr_native_max_value = MAX_COOK_TIME_MINUTES
    _attr_native_step = STEP_COOK_TIME_MINUTES
    _attr_mode = NumberMode.BOX

    def __init__(self, coordinator: JouleCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_cook_time_minutes"
        self._attr_device_info = _device_info(entry)

    @property
    def native_value(self) -> float:
        """Return the current cook time from coordinator data."""
        if self.coordinator.data is None:
            return DEFAULT_COOK_TIME_MINUTES
        return self.coordinator.data.get("cook_time_minutes", DEFAULT_COOK_TIME_MINUTES)

    async def async_set_native_value(self, value: float) -> None:
        """Update the cook time in the coordinator."""
        await self.coordinator.async_set_cook_time(value)
