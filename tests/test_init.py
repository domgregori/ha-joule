"""Tests for integration setup and teardown (__init__.py)."""
from unittest.mock import MagicMock

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.joule_sous_vide.const import DOMAIN
from custom_components.joule_sous_vide.coordinator import JouleCoordinator
from custom_components.joule_sous_vide.joule_ble import JouleBLEError

from .conftest import TEST_ENTRY_ID


async def test_setup_entry_stores_coordinator(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
) -> None:
    """Successful setup stores a JouleCoordinator in hass.data."""
    assert DOMAIN in hass.data
    assert TEST_ENTRY_ID in hass.data[DOMAIN]
    assert isinstance(hass.data[DOMAIN][TEST_ENTRY_ID], JouleCoordinator)


async def test_setup_entry_creates_all_entities(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
) -> None:
    """Successful setup creates the sensor, switch, and both number entities."""
    from homeassistant.helpers import entity_registry as er

    registry = er.async_get(hass)

    sensor_id = registry.async_get_entity_id(
        "sensor", DOMAIN, f"{TEST_ENTRY_ID}_current_temperature"
    )
    switch_id = registry.async_get_entity_id(
        "switch", DOMAIN, f"{TEST_ENTRY_ID}_switch"
    )
    target_temp_id = registry.async_get_entity_id(
        "number", DOMAIN, f"{TEST_ENTRY_ID}_target_temperature"
    )
    cook_time_id = registry.async_get_entity_id(
        "number", DOMAIN, f"{TEST_ENTRY_ID}_cook_time_minutes"
    )

    assert sensor_id is not None, "Temperature sensor entity was not created"
    assert switch_id is not None, "Sous vide switch entity was not created"
    assert target_temp_id is not None, "Target temperature number entity was not created"
    assert cook_time_id is not None, "Cook time number entity was not created"


async def test_setup_entry_config_entry_not_ready_on_ble_failure(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_ble_api: MagicMock,
) -> None:
    """Setup raises ConfigEntryNotReady when the first BLE poll fails.

    HA should set the entry state to SETUP_RETRY so it tries again later.
    """
    mock_ble_api.ensure_connected.side_effect = JouleBLEError("Cannot reach device")

    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state == ConfigEntryState.SETUP_RETRY


async def test_unload_entry_disconnects_ble(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    mock_ble_api: MagicMock,
) -> None:
    """Unloading the entry calls disconnect() on the BLE API."""
    assert await hass.config_entries.async_unload(setup_integration.entry_id)
    await hass.async_block_till_done()

    mock_ble_api.disconnect.assert_called_once()


async def test_unload_entry_removes_coordinator_from_hass_data(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    mock_ble_api: MagicMock,
) -> None:
    """Unloading the entry removes the coordinator from hass.data."""
    assert await hass.config_entries.async_unload(setup_integration.entry_id)
    await hass.async_block_till_done()

    assert TEST_ENTRY_ID not in hass.data.get(DOMAIN, {})


async def test_unload_entry_state(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    mock_ble_api: MagicMock,
) -> None:
    """Unloaded entry has NOT_LOADED state."""
    assert await hass.config_entries.async_unload(setup_integration.entry_id)
    await hass.async_block_till_done()

    assert setup_integration.state == ConfigEntryState.NOT_LOADED
