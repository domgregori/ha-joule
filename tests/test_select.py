"""Tests for the temperature unit select entity (select.py)."""
from unittest.mock import MagicMock

import pytest
from homeassistant.const import STATE_UNAVAILABLE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.joule_sous_vide.const import DEFAULT_TEMPERATURE_UNIT, DOMAIN
from custom_components.joule_sous_vide.coordinator import JouleCoordinator
from custom_components.joule_sous_vide.joule_ble import JouleBLEError

from .conftest import TEST_ENTRY_ID

SELECT_UNIQUE_ID = f"{TEST_ENTRY_ID}_temperature_unit"


def _get_select_entity_id(hass: HomeAssistant) -> str:
    registry = er.async_get(hass)
    entity_id = registry.async_get_entity_id("select", DOMAIN, SELECT_UNIQUE_ID)
    assert entity_id is not None, "Temperature unit select entity not found in registry"
    return entity_id


# ---------------------------------------------------------------------------
# Entity registration
# ---------------------------------------------------------------------------


async def test_select_is_registered(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
) -> None:
    """Temperature unit select entity is registered in the entity registry."""
    registry = er.async_get(hass)
    assert registry.async_get_entity_id("select", DOMAIN, SELECT_UNIQUE_ID) is not None


async def test_select_unique_id(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
) -> None:
    """Select entity has the expected unique ID."""
    registry = er.async_get(hass)
    entry = registry.async_get(
        registry.async_get_entity_id("select", DOMAIN, SELECT_UNIQUE_ID)
    )
    assert entry.unique_id == SELECT_UNIQUE_ID


async def test_select_belongs_to_joule_device(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
) -> None:
    """Select entity belongs to the ChefSteps Joule device."""
    from homeassistant.helpers import device_registry as dr

    dev_registry = dr.async_get(hass)
    entity_registry = er.async_get(hass)

    entity_id = _get_select_entity_id(hass)
    entity_entry = entity_registry.async_get(entity_id)
    device = dev_registry.async_get(entity_entry.device_id)

    assert device is not None
    assert device.manufacturer == "ChefSteps"
    assert device.model == "Joule"


# ---------------------------------------------------------------------------
# Initial state
# ---------------------------------------------------------------------------


async def test_select_default_option_is_fahrenheit(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
) -> None:
    """Temperature unit defaults to °F."""
    entity_id = _get_select_entity_id(hass)
    state = hass.states.get(entity_id)
    assert state.state == DEFAULT_TEMPERATURE_UNIT
    assert state.state == UnitOfTemperature.FAHRENHEIT


async def test_select_options_are_f_and_c(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
) -> None:
    """Select entity offers exactly °F and °C as options."""
    entity_id = _get_select_entity_id(hass)
    state = hass.states.get(entity_id)
    options = state.attributes.get("options", [])
    assert UnitOfTemperature.FAHRENHEIT in options
    assert UnitOfTemperature.CELSIUS in options
    assert len(options) == 2


# ---------------------------------------------------------------------------
# Selecting options
# ---------------------------------------------------------------------------


async def test_select_celsius_updates_coordinator(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
) -> None:
    """Selecting °C updates the coordinator's temperature_unit."""
    coordinator: JouleCoordinator = hass.data[DOMAIN][setup_integration.entry_id]
    entity_id = _get_select_entity_id(hass)

    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": entity_id, "option": UnitOfTemperature.CELSIUS},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert coordinator.data["temperature_unit"] == UnitOfTemperature.CELSIUS


async def test_select_fahrenheit_updates_coordinator(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
) -> None:
    """Selecting °F updates the coordinator's temperature_unit."""
    coordinator: JouleCoordinator = hass.data[DOMAIN][setup_integration.entry_id]
    entity_id = _get_select_entity_id(hass)

    # Switch to °C first, then back to °F
    await coordinator.async_set_temperature_unit(UnitOfTemperature.CELSIUS)
    await hass.async_block_till_done()

    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": entity_id, "option": UnitOfTemperature.FAHRENHEIT},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert coordinator.data["temperature_unit"] == UnitOfTemperature.FAHRENHEIT


async def test_select_option_reflected_in_state(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
) -> None:
    """After selecting °C, the entity state shows °C."""
    entity_id = _get_select_entity_id(hass)

    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": entity_id, "option": UnitOfTemperature.CELSIUS},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert hass.states.get(entity_id).state == UnitOfTemperature.CELSIUS


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------


async def test_selecting_celsius_persists_to_config_entry(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
) -> None:
    """Selecting °C via the select entity writes the unit to config entry options."""
    entity_id = _get_select_entity_id(hass)

    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": entity_id, "option": UnitOfTemperature.CELSIUS},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert setup_integration.options.get("temperature_unit") == UnitOfTemperature.CELSIUS


# ---------------------------------------------------------------------------
# Unavailability
# ---------------------------------------------------------------------------


async def test_select_becomes_unavailable_on_ble_failure(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    mock_ble_api: MagicMock,
) -> None:
    """Select entity shows Unavailable when the coordinator cannot reach the device."""
    coordinator: JouleCoordinator = hass.data[DOMAIN][setup_integration.entry_id]

    mock_ble_api.ensure_connected.side_effect = JouleBLEError("Lost")
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    entity_id = _get_select_entity_id(hass)
    assert hass.states.get(entity_id).state == STATE_UNAVAILABLE
