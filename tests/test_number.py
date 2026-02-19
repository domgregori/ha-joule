"""Tests for the target temperature and cook time number entities (number.py)."""
from unittest.mock import MagicMock

import pytest
from homeassistant.const import STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.joule_sous_vide.const import (
    DEFAULT_COOK_TIME_MINUTES,
    DEFAULT_TARGET_TEMPERATURE,
    DOMAIN,
    MAX_COOK_TIME_MINUTES,
    MAX_TARGET_TEMPERATURE,
    MIN_COOK_TIME_MINUTES,
    MIN_TARGET_TEMPERATURE,
)
from custom_components.joule_sous_vide.coordinator import JouleCoordinator
from custom_components.joule_sous_vide.joule_ble import JouleBLEError

from .conftest import TEST_ENTRY_ID

TARGET_TEMP_UNIQUE_ID = f"{TEST_ENTRY_ID}_target_temperature"
COOK_TIME_UNIQUE_ID = f"{TEST_ENTRY_ID}_cook_time_minutes"


def _get_entity_id(hass: HomeAssistant, unique_id: str) -> str:
    registry = er.async_get(hass)
    entity_id = registry.async_get_entity_id("number", DOMAIN, unique_id)
    assert entity_id is not None, f"Number entity {unique_id!r} not found in registry"
    return entity_id


# ---------------------------------------------------------------------------
# Entity registration
# ---------------------------------------------------------------------------


async def test_target_temperature_is_registered(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
) -> None:
    """Target temperature number entity is registered in the entity registry."""
    registry = er.async_get(hass)
    assert registry.async_get_entity_id("number", DOMAIN, TARGET_TEMP_UNIQUE_ID) is not None


async def test_cook_time_is_registered(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
) -> None:
    """Cook time number entity is registered in the entity registry."""
    registry = er.async_get(hass)
    assert registry.async_get_entity_id("number", DOMAIN, COOK_TIME_UNIQUE_ID) is not None


async def test_target_temperature_unique_id(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
) -> None:
    """Target temperature entity has the expected unique ID."""
    registry = er.async_get(hass)
    entry = registry.async_get(
        registry.async_get_entity_id("number", DOMAIN, TARGET_TEMP_UNIQUE_ID)
    )
    assert entry.unique_id == TARGET_TEMP_UNIQUE_ID


async def test_cook_time_unique_id(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
) -> None:
    """Cook time entity has the expected unique ID."""
    registry = er.async_get(hass)
    entry = registry.async_get(
        registry.async_get_entity_id("number", DOMAIN, COOK_TIME_UNIQUE_ID)
    )
    assert entry.unique_id == COOK_TIME_UNIQUE_ID


async def test_number_entities_belong_to_joule_device(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
) -> None:
    """Both number entities belong to the ChefSteps Joule device."""
    from homeassistant.helpers import device_registry as dr

    dev_registry = dr.async_get(hass)
    entity_registry = er.async_get(hass)

    for unique_id in (TARGET_TEMP_UNIQUE_ID, COOK_TIME_UNIQUE_ID):
        entity_id = _get_entity_id(hass, unique_id)
        entity_entry = entity_registry.async_get(entity_id)
        device = dev_registry.async_get(entity_entry.device_id)
        assert device is not None
        assert device.manufacturer == "ChefSteps"
        assert device.model == "Joule"


# ---------------------------------------------------------------------------
# Initial state
# ---------------------------------------------------------------------------


async def test_target_temperature_default_value(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
) -> None:
    """Target temperature starts at the default value."""
    entity_id = _get_entity_id(hass, TARGET_TEMP_UNIQUE_ID)
    state = hass.states.get(entity_id)
    assert float(state.state) == pytest.approx(DEFAULT_TARGET_TEMPERATURE)


async def test_cook_time_default_value(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
) -> None:
    """Cook time starts at the default value."""
    entity_id = _get_entity_id(hass, COOK_TIME_UNIQUE_ID)
    state = hass.states.get(entity_id)
    assert float(state.state) == pytest.approx(DEFAULT_COOK_TIME_MINUTES)


async def test_target_temperature_min_max(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
) -> None:
    """Target temperature entity exposes the correct min and max values."""
    entity_id = _get_entity_id(hass, TARGET_TEMP_UNIQUE_ID)
    state = hass.states.get(entity_id)
    assert float(state.attributes["min"]) == MIN_TARGET_TEMPERATURE
    assert float(state.attributes["max"]) == MAX_TARGET_TEMPERATURE


async def test_cook_time_min_max(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
) -> None:
    """Cook time entity exposes the correct min and max values."""
    entity_id = _get_entity_id(hass, COOK_TIME_UNIQUE_ID)
    state = hass.states.get(entity_id)
    assert float(state.attributes["min"]) == MIN_COOK_TIME_MINUTES
    assert float(state.attributes["max"]) == MAX_COOK_TIME_MINUTES


# ---------------------------------------------------------------------------
# Setting values
# ---------------------------------------------------------------------------


async def test_set_target_temperature_updates_coordinator(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
) -> None:
    """Setting target temperature updates the coordinator's stored value."""
    coordinator: JouleCoordinator = hass.data[DOMAIN][setup_integration.entry_id]
    entity_id = _get_entity_id(hass, TARGET_TEMP_UNIQUE_ID)

    await hass.services.async_call(
        "number", "set_value", {"entity_id": entity_id, "value": 75.0}, blocking=True
    )
    await hass.async_block_till_done()

    assert coordinator.data["target_temperature"] == pytest.approx(75.0)


async def test_set_cook_time_updates_coordinator(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
) -> None:
    """Setting cook time updates the coordinator's stored value."""
    coordinator: JouleCoordinator = hass.data[DOMAIN][setup_integration.entry_id]
    entity_id = _get_entity_id(hass, COOK_TIME_UNIQUE_ID)

    await hass.services.async_call(
        "number", "set_value", {"entity_id": entity_id, "value": 90.0}, blocking=True
    )
    await hass.async_block_till_done()

    assert coordinator.data["cook_time_minutes"] == pytest.approx(90.0)


async def test_set_target_temperature_reflected_in_state(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
) -> None:
    """After setting target temperature, the entity state reflects the new value."""
    entity_id = _get_entity_id(hass, TARGET_TEMP_UNIQUE_ID)

    await hass.services.async_call(
        "number", "set_value", {"entity_id": entity_id, "value": 63.5}, blocking=True
    )
    await hass.async_block_till_done()

    assert float(hass.states.get(entity_id).state) == pytest.approx(63.5)


async def test_set_cook_time_reflected_in_state(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
) -> None:
    """After setting cook time, the entity state reflects the new value."""
    entity_id = _get_entity_id(hass, COOK_TIME_UNIQUE_ID)

    await hass.services.async_call(
        "number", "set_value", {"entity_id": entity_id, "value": 120.0}, blocking=True
    )
    await hass.async_block_till_done()

    assert float(hass.states.get(entity_id).state) == pytest.approx(120.0)


async def test_turn_on_switch_uses_updated_target_temperature(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    mock_ble_api: MagicMock,
) -> None:
    """When the switch is turned on, it uses the target temperature set via the number entity."""
    temp_entity_id = _get_entity_id(hass, TARGET_TEMP_UNIQUE_ID)
    switch_entity_id = er.async_get(hass).async_get_entity_id(
        "switch", DOMAIN, f"{TEST_ENTRY_ID}_switch"
    )

    await hass.services.async_call(
        "number", "set_value", {"entity_id": temp_entity_id, "value": 82.0}, blocking=True
    )
    await hass.async_block_till_done()

    await hass.services.async_call(
        "switch", "turn_on", {"entity_id": switch_entity_id}, blocking=True
    )
    await hass.async_block_till_done()

    mock_ble_api.set_temperature.assert_called_once_with(82.0)


# ---------------------------------------------------------------------------
# Unavailability
# ---------------------------------------------------------------------------


async def test_number_entities_become_unavailable_on_ble_failure(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    mock_ble_api: MagicMock,
) -> None:
    """Both number entities show Unavailable when the coordinator cannot reach the device."""
    coordinator: JouleCoordinator = hass.data[DOMAIN][setup_integration.entry_id]

    mock_ble_api.get_current_temperature.side_effect = JouleBLEError("Lost")
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    for unique_id in (TARGET_TEMP_UNIQUE_ID, COOK_TIME_UNIQUE_ID):
        entity_id = _get_entity_id(hass, unique_id)
        assert hass.states.get(entity_id).state == STATE_UNAVAILABLE
