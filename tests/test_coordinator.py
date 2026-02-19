"""Tests for JouleCoordinator (coordinator.py)."""
from unittest.mock import MagicMock

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import UpdateFailed
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.joule_sous_vide.const import (
    DEFAULT_COOK_TIME_MINUTES,
    DEFAULT_TARGET_TEMPERATURE,
    DOMAIN,
)
from custom_components.joule_sous_vide.coordinator import JouleCoordinator
from custom_components.joule_sous_vide.joule_ble import JouleBLEError


# ---------------------------------------------------------------------------
# Polling
# ---------------------------------------------------------------------------


async def test_update_data_returns_expected_shape(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    mock_ble_api: MagicMock,
) -> None:
    """Coordinator data dict contains all expected keys after a successful poll."""
    coordinator: JouleCoordinator = hass.data[DOMAIN][setup_integration.entry_id]

    assert "current_temperature" in coordinator.data
    assert "is_cooking" in coordinator.data
    assert "target_temperature" in coordinator.data
    assert "cook_time_minutes" in coordinator.data


async def test_update_data_reflects_device_temperature(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    mock_ble_api: MagicMock,
) -> None:
    """current_temperature matches the value returned by get_current_temperature."""
    coordinator: JouleCoordinator = hass.data[DOMAIN][setup_integration.entry_id]

    mock_ble_api.get_current_temperature.return_value = 72.3
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    assert coordinator.data["current_temperature"] == pytest.approx(72.3)


async def test_update_data_raises_update_failed_on_ble_error(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    mock_ble_api: MagicMock,
) -> None:
    """A JouleBLEError during polling raises UpdateFailed."""
    coordinator: JouleCoordinator = hass.data[DOMAIN][setup_integration.entry_id]

    mock_ble_api.get_current_temperature.side_effect = JouleBLEError("BLE lost")

    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()


async def test_update_data_raises_update_failed_on_connect_error(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    mock_ble_api: MagicMock,
) -> None:
    """A JouleBLEError from ensure_connected also raises UpdateFailed."""
    coordinator: JouleCoordinator = hass.data[DOMAIN][setup_integration.entry_id]

    mock_ble_api.ensure_connected.side_effect = JouleBLEError("Cannot reconnect")

    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()


async def test_initial_cooking_state_is_false(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
) -> None:
    """is_cooking is False when the integration first starts."""
    coordinator: JouleCoordinator = hass.data[DOMAIN][setup_integration.entry_id]
    assert coordinator.data["is_cooking"] is False


async def test_initial_defaults(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
) -> None:
    """target_temperature and cook_time_minutes start at their defined defaults."""
    coordinator: JouleCoordinator = hass.data[DOMAIN][setup_integration.entry_id]
    assert coordinator.data["target_temperature"] == DEFAULT_TARGET_TEMPERATURE
    assert coordinator.data["cook_time_minutes"] == DEFAULT_COOK_TIME_MINUTES


# ---------------------------------------------------------------------------
# async_start_cooking
# ---------------------------------------------------------------------------


async def test_start_cooking_sends_temperature_to_device(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    mock_ble_api: MagicMock,
) -> None:
    """async_start_cooking writes the target temperature to the BLE device."""
    coordinator: JouleCoordinator = hass.data[DOMAIN][setup_integration.entry_id]

    await coordinator.async_start_cooking(65.0, 90.0)

    mock_ble_api.set_temperature.assert_called_once_with(65.0)


async def test_start_cooking_sends_cook_time_to_device(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    mock_ble_api: MagicMock,
) -> None:
    """async_start_cooking writes the cook time to the BLE device."""
    coordinator: JouleCoordinator = hass.data[DOMAIN][setup_integration.entry_id]

    await coordinator.async_start_cooking(65.0, 90.0)

    mock_ble_api.set_cook_time.assert_called_once_with(90.0)


async def test_start_cooking_sends_start_command(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    mock_ble_api: MagicMock,
) -> None:
    """async_start_cooking calls start_cooking on the BLE device."""
    coordinator: JouleCoordinator = hass.data[DOMAIN][setup_integration.entry_id]

    await coordinator.async_start_cooking(65.0, 90.0)

    mock_ble_api.start_cooking.assert_called_once()


async def test_start_cooking_updates_is_cooking(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    mock_ble_api: MagicMock,
) -> None:
    """After async_start_cooking, coordinator data reflects is_cooking=True."""
    coordinator: JouleCoordinator = hass.data[DOMAIN][setup_integration.entry_id]

    await coordinator.async_start_cooking(65.0, 90.0)
    await hass.async_block_till_done()

    assert coordinator.data["is_cooking"] is True


async def test_start_cooking_stores_settings_in_data(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    mock_ble_api: MagicMock,
) -> None:
    """After async_start_cooking, target_temperature and cook_time_minutes are updated."""
    coordinator: JouleCoordinator = hass.data[DOMAIN][setup_integration.entry_id]

    await coordinator.async_start_cooking(65.0, 90.0)
    await hass.async_block_till_done()

    assert coordinator.data["target_temperature"] == 65.0
    assert coordinator.data["cook_time_minutes"] == 90.0


async def test_start_cooking_raises_homeassistant_error_on_ble_failure(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    mock_ble_api: MagicMock,
) -> None:
    """A JouleBLEError during start_cooking raises HomeAssistantError."""
    coordinator: JouleCoordinator = hass.data[DOMAIN][setup_integration.entry_id]

    mock_ble_api.start_cooking.side_effect = JouleBLEError("Write failed")

    with pytest.raises(HomeAssistantError):
        await coordinator.async_start_cooking(65.0, 90.0)


# ---------------------------------------------------------------------------
# async_stop_cooking
# ---------------------------------------------------------------------------


async def test_stop_cooking_sends_stop_command(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    mock_ble_api: MagicMock,
) -> None:
    """async_stop_cooking calls stop_cooking on the BLE device."""
    coordinator: JouleCoordinator = hass.data[DOMAIN][setup_integration.entry_id]

    await coordinator.async_stop_cooking()

    mock_ble_api.stop_cooking.assert_called_once()


async def test_stop_cooking_updates_is_cooking(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    mock_ble_api: MagicMock,
) -> None:
    """After async_stop_cooking, coordinator data reflects is_cooking=False."""
    coordinator: JouleCoordinator = hass.data[DOMAIN][setup_integration.entry_id]

    # Start first so we have something to stop.
    await coordinator.async_start_cooking(65.0, 90.0)
    await hass.async_block_till_done()
    assert coordinator.data["is_cooking"] is True

    await coordinator.async_stop_cooking()
    await hass.async_block_till_done()

    assert coordinator.data["is_cooking"] is False


async def test_stop_cooking_raises_homeassistant_error_on_ble_failure(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    mock_ble_api: MagicMock,
) -> None:
    """A JouleBLEError during stop_cooking raises HomeAssistantError."""
    coordinator: JouleCoordinator = hass.data[DOMAIN][setup_integration.entry_id]

    mock_ble_api.stop_cooking.side_effect = JouleBLEError("Write failed")

    with pytest.raises(HomeAssistantError):
        await coordinator.async_stop_cooking()
