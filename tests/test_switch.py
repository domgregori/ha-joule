"""Tests for the sous vide switch entity (switch.py)."""
from unittest.mock import MagicMock

import pytest
from homeassistant.const import STATE_OFF, STATE_ON, STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.joule_sous_vide.const import (
    DEFAULT_COOK_TIME_MINUTES,
    DEFAULT_TARGET_TEMPERATURE,
    DOMAIN,
)
from custom_components.joule_sous_vide.coordinator import JouleCoordinator
from custom_components.joule_sous_vide.joule_ble import JouleBLEError

from .conftest import TEST_ENTRY_ID

SWITCH_UNIQUE_ID = f"{TEST_ENTRY_ID}_switch"


def _get_switch_entity_id(hass: HomeAssistant) -> str:
    registry = er.async_get(hass)
    entity_id = registry.async_get_entity_id("switch", DOMAIN, SWITCH_UNIQUE_ID)
    assert entity_id is not None, "Sous vide switch entity not found in registry"
    return entity_id


# ---------------------------------------------------------------------------
# Entity registration
# ---------------------------------------------------------------------------


async def test_switch_is_registered(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
) -> None:
    """The switch entity is registered in the entity registry."""
    registry = er.async_get(hass)
    entry = registry.async_get_entity_id("switch", DOMAIN, SWITCH_UNIQUE_ID)
    assert entry is not None


async def test_switch_unique_id(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
) -> None:
    """The switch has the expected unique ID."""
    registry = er.async_get(hass)
    entry = registry.async_get(
        registry.async_get_entity_id("switch", DOMAIN, SWITCH_UNIQUE_ID)
    )
    assert entry.unique_id == SWITCH_UNIQUE_ID


async def test_switch_device_info(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
) -> None:
    """The switch belongs to the same device as the sensor."""
    from homeassistant.helpers import device_registry as dr

    dev_registry = dr.async_get(hass)
    entity_registry = er.async_get(hass)

    entity_id = _get_switch_entity_id(hass)
    entity_entry = entity_registry.async_get(entity_id)
    device = dev_registry.async_get(entity_entry.device_id)

    assert device is not None
    assert device.manufacturer == "ChefSteps"
    assert device.model == "Joule"


# ---------------------------------------------------------------------------
# Initial state
# ---------------------------------------------------------------------------


async def test_switch_is_off_initially(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
) -> None:
    """Switch starts in the off state when the integration loads."""
    entity_id = _get_switch_entity_id(hass)
    state = hass.states.get(entity_id)
    assert state.state == STATE_OFF


async def test_switch_state_attributes_at_defaults(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
) -> None:
    """State attributes start at the defined defaults."""
    entity_id = _get_switch_entity_id(hass)
    state = hass.states.get(entity_id)

    assert state.attributes.get("target_temperature") == DEFAULT_TARGET_TEMPERATURE
    assert state.attributes.get("cook_time_minutes") == DEFAULT_COOK_TIME_MINUTES


# ---------------------------------------------------------------------------
# Turn on
# ---------------------------------------------------------------------------


async def test_turn_on_starts_cooking_on_device(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    mock_ble_api: MagicMock,
) -> None:
    """Turning the switch on sends the full cooking sequence to the device."""
    entity_id = _get_switch_entity_id(hass)

    await hass.services.async_call(
        "switch", "turn_on", {"entity_id": entity_id}, blocking=True
    )
    await hass.async_block_till_done()

    mock_ble_api.ensure_connected.assert_called()


async def test_turn_on_uses_default_temperature(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    mock_ble_api: MagicMock,
) -> None:
    """Turn on uses the default target temperature (60°C) when none has been set."""
    entity_id = _get_switch_entity_id(hass)

    await hass.services.async_call(
        "switch", "turn_on", {"entity_id": entity_id}, blocking=True
    )
    await hass.async_block_till_done()

    mock_ble_api.ensure_connected.assert_called()


async def test_turn_on_sets_switch_state_to_on(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    mock_ble_api: MagicMock,
) -> None:
    """After turn on, the switch reports state On."""
    entity_id = _get_switch_entity_id(hass)

    await hass.services.async_call(
        "switch", "turn_on", {"entity_id": entity_id}, blocking=True
    )
    await hass.async_block_till_done()

    assert hass.states.get(entity_id).state == STATE_ON


async def test_turn_on_updates_state_attributes(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    mock_ble_api: MagicMock,
) -> None:
    """State attributes reflect the temperature and time used in the last cook."""
    coordinator: JouleCoordinator = hass.data[DOMAIN][setup_integration.entry_id]
    entity_id = _get_switch_entity_id(hass)

    # Start a cook with custom values to populate coordinator.data.
    await coordinator.async_start_cooking(75.0, 120.0)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state.attributes.get("target_temperature") == 75.0
    assert state.attributes.get("cook_time_minutes") == 120.0


# ---------------------------------------------------------------------------
# Turn off
# ---------------------------------------------------------------------------


async def test_turn_off_stops_cooking_on_device(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    mock_ble_api: MagicMock,
) -> None:
    """Turning the switch off sends the stop command to the device."""
    entity_id = _get_switch_entity_id(hass)

    # Start first.
    await hass.services.async_call(
        "switch", "turn_on", {"entity_id": entity_id}, blocking=True
    )
    await hass.async_block_till_done()

    await hass.services.async_call(
        "switch", "turn_off", {"entity_id": entity_id}, blocking=True
    )
    await hass.async_block_till_done()

    mock_ble_api.ensure_connected.assert_called()


async def test_turn_off_sets_switch_state_to_off(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    mock_ble_api: MagicMock,
) -> None:
    """After turn off, the switch reports state Off."""
    entity_id = _get_switch_entity_id(hass)

    await hass.services.async_call(
        "switch", "turn_on", {"entity_id": entity_id}, blocking=True
    )
    await hass.async_block_till_done()

    await hass.services.async_call(
        "switch", "turn_off", {"entity_id": entity_id}, blocking=True
    )
    await hass.async_block_till_done()

    assert hass.states.get(entity_id).state == STATE_OFF


# ---------------------------------------------------------------------------
# Unavailability
# ---------------------------------------------------------------------------


async def test_switch_becomes_unavailable_on_ble_failure(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    mock_ble_api: MagicMock,
) -> None:
    """When the coordinator cannot reach the device, the switch shows Unavailable."""
    coordinator: JouleCoordinator = hass.data[DOMAIN][setup_integration.entry_id]

    mock_ble_api.ensure_connected.side_effect = JouleBLEError("Lost")
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    entity_id = _get_switch_entity_id(hass)
    assert hass.states.get(entity_id).state == STATE_UNAVAILABLE


async def test_switch_recovers_after_ble_failure(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    mock_ble_api: MagicMock,
) -> None:
    """The switch recovers from Unavailable once the device is reachable again."""
    coordinator: JouleCoordinator = hass.data[DOMAIN][setup_integration.entry_id]
    entity_id = _get_switch_entity_id(hass)

    # Cause failure.
    mock_ble_api.ensure_connected.side_effect = JouleBLEError("Lost")
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert hass.states.get(entity_id).state == STATE_UNAVAILABLE

    # Recover.
    mock_ble_api.ensure_connected.side_effect = None
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    assert hass.states.get(entity_id).state == STATE_OFF
