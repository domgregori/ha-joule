"""Tests for the temperature sensor entity (sensor.py)."""
from unittest.mock import MagicMock

import pytest
from homeassistant.const import STATE_UNAVAILABLE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.joule_sous_vide.const import DOMAIN
from custom_components.joule_sous_vide.joule_ble import JouleBLEError

from .conftest import TEST_ENTRY_ID

SENSOR_UNIQUE_ID = f"{TEST_ENTRY_ID}_current_temperature"


def _get_sensor_entity_id(hass: HomeAssistant) -> str:
    registry = er.async_get(hass)
    entity_id = registry.async_get_entity_id("sensor", DOMAIN, SENSOR_UNIQUE_ID)
    assert entity_id is not None, "Temperature sensor entity not found in registry"
    return entity_id


# ---------------------------------------------------------------------------
# Entity registration
# ---------------------------------------------------------------------------


async def test_sensor_is_registered(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
) -> None:
    """The temperature sensor is registered in the entity registry."""
    registry = er.async_get(hass)
    entry = registry.async_get_entity_id("sensor", DOMAIN, SENSOR_UNIQUE_ID)
    assert entry is not None


async def test_sensor_unique_id(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
) -> None:
    """The sensor has the expected unique ID."""
    registry = er.async_get(hass)
    entry = registry.async_get(
        registry.async_get_entity_id("sensor", DOMAIN, SENSOR_UNIQUE_ID)
    )
    assert entry.unique_id == SENSOR_UNIQUE_ID


async def test_sensor_device_info(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
) -> None:
    """The sensor is associated with the Joule device."""
    from homeassistant.helpers import device_registry as dr

    dev_registry = dr.async_get(hass)
    entity_registry = er.async_get(hass)

    entity_id = _get_sensor_entity_id(hass)
    entity_entry = entity_registry.async_get(entity_id)
    device = dev_registry.async_get(entity_entry.device_id)

    assert device is not None
    assert device.manufacturer == "ChefSteps"
    assert device.model == "Joule"


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------


async def test_sensor_state_matches_device_temperature(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    mock_ble_api: MagicMock,
) -> None:
    """Sensor state reflects the temperature returned by the BLE device."""
    from custom_components.joule_sous_vide.const import DOMAIN
    from custom_components.joule_sous_vide.coordinator import JouleCoordinator

    coordinator: JouleCoordinator = hass.data[DOMAIN][setup_integration.entry_id]

    mock_ble_api.get_current_temperature.return_value = 58.75
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    entity_id = _get_sensor_entity_id(hass)
    state = hass.states.get(entity_id)

    assert state is not None
    assert float(state.state) == pytest.approx(58.75)


async def test_sensor_unit_of_measurement(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
) -> None:
    """Sensor reports temperature in degrees Celsius."""
    entity_id = _get_sensor_entity_id(hass)
    state = hass.states.get(entity_id)

    assert state.attributes.get("unit_of_measurement") == UnitOfTemperature.CELSIUS


async def test_sensor_becomes_unavailable_on_ble_failure(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    mock_ble_api: MagicMock,
) -> None:
    """When the coordinator cannot reach the device, the sensor shows Unavailable."""
    from custom_components.joule_sous_vide.coordinator import JouleCoordinator

    coordinator: JouleCoordinator = hass.data[DOMAIN][setup_integration.entry_id]

    mock_ble_api.get_current_temperature.side_effect = JouleBLEError("Connection lost")
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    entity_id = _get_sensor_entity_id(hass)
    state = hass.states.get(entity_id)

    assert state.state == STATE_UNAVAILABLE


async def test_sensor_recovers_after_ble_failure(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    mock_ble_api: MagicMock,
) -> None:
    """After a BLE failure, the sensor recovers when the device becomes reachable again."""
    from custom_components.joule_sous_vide.coordinator import JouleCoordinator

    coordinator: JouleCoordinator = hass.data[DOMAIN][setup_integration.entry_id]

    # Cause a failure.
    mock_ble_api.get_current_temperature.side_effect = JouleBLEError("Lost")
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    entity_id = _get_sensor_entity_id(hass)
    assert hass.states.get(entity_id).state == STATE_UNAVAILABLE

    # Recover.
    mock_ble_api.get_current_temperature.side_effect = None
    mock_ble_api.get_current_temperature.return_value = 63.0
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    assert float(hass.states.get(entity_id).state) == pytest.approx(63.0)
