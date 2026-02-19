"""Select entity for choosing the temperature display unit."""
from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DEFAULT_TEMPERATURE_UNIT, DOMAIN
from .coordinator import JouleCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the temperature unit select entity from a config entry."""
    coordinator: JouleCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([JouleTemperatureUnitSelect(coordinator, entry)])


class JouleTemperatureUnitSelect(CoordinatorEntity[JouleCoordinator], SelectEntity):
    """Chooses whether temperatures are displayed in °F or °C.

    This preference is stored in the coordinator and read by the Target
    Temperature number entity to convert between the display unit and the
    internal °C value used by the device.
    """

    _attr_has_entity_name = True
    _attr_name = "Temperature Unit"
    _attr_options = [UnitOfTemperature.FAHRENHEIT, UnitOfTemperature.CELSIUS]

    def __init__(self, coordinator: JouleCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_temperature_unit"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Joule Sous Vide",
            manufacturer="ChefSteps",
            model="Joule",
        )

    @property
    def current_option(self) -> str:
        """Return the currently selected temperature unit."""
        if self.coordinator.data is None:
            return DEFAULT_TEMPERATURE_UNIT
        return self.coordinator.data.get("temperature_unit", DEFAULT_TEMPERATURE_UNIT)

    async def async_select_option(self, option: str) -> None:
        """Update the temperature unit preference in the coordinator."""
        await self.coordinator.async_set_temperature_unit(option)
