"""Shared fixtures for Joule Sous Vide tests."""
from unittest.mock import MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.joule_sous_vide.const import CONF_MAC_ADDRESS, DOMAIN
from custom_components.joule_sous_vide.coordinator import JouleCoordinator

TEST_MAC = "AA:BB:CC:DD:EE:FF"
TEST_ENTRY_ID = "test_entry_id"


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return a mock config entry with a test MAC address."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={CONF_MAC_ADDRESS: TEST_MAC},
        entry_id=TEST_ENTRY_ID,
        title=f"Joule {TEST_MAC}",
        unique_id=TEST_MAC,
    )


@pytest.fixture
def mock_ble_api():
    """Patch JouleBLEAPI in the coordinator to prevent real BLE connections.

    All BLE methods are replaced with MagicMock (synchronous) since they are
    called via hass.async_add_executor_job, not awaited directly.
    """
    with patch(
        "custom_components.joule_sous_vide.coordinator.JouleBLEAPI"
    ) as mock_cls:
        instance = MagicMock()
        mock_cls.return_value = instance
        yield instance


@pytest.fixture(autouse=True)
def _fast_notification_timeout(monkeypatch: pytest.MonkeyPatch):
    """Patch NOTIFICATION_TIMEOUT on the class so all tests run fast.

    This applies before the coordinator is instantiated, so the first
    refresh during async_config_entry_first_refresh uses the patched value.
    """
    monkeypatch.setattr(JouleCoordinator, "NOTIFICATION_TIMEOUT", 0.01)


@pytest.fixture
async def setup_integration(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_ble_api: MagicMock,
) -> MockConfigEntry:
    """Set up the full integration with a mocked BLE layer.

    Returns the MockConfigEntry so tests can access entry_id and state.
    """
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    return mock_config_entry
