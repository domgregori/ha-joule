"""Tests for the config flow (config_flow.py)."""
from unittest.mock import MagicMock, patch

import pytest
from homeassistant import config_entries, data_entry_flow
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.joule_sous_vide.const import CONF_MAC_ADDRESS, DOMAIN
from custom_components.joule_sous_vide.joule_ble import JouleBLEError

from .conftest import TEST_MAC


async def test_form_is_shown(hass: HomeAssistant) -> None:
    """Initiating the flow shows the MAC address form with no errors."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}


async def test_form_creates_entry_on_valid_mac(hass: HomeAssistant) -> None:
    """A successful BLE connection creates a config entry with the MAC address."""
    with patch(
        "custom_components.joule_sous_vide.config_flow.JouleBLEAPI"
    ) as mock_cls:
        instance = MagicMock()
        mock_cls.return_value = instance

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_MAC_ADDRESS: TEST_MAC}
        )

    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["title"] == f"Joule {TEST_MAC}"
    assert result["data"] == {CONF_MAC_ADDRESS: TEST_MAC}


async def test_form_shows_cannot_connect_on_ble_error(hass: HomeAssistant) -> None:
    """A JouleBLEError during validation shows a cannot_connect error on the form."""
    with patch(
        "custom_components.joule_sous_vide.config_flow.JouleBLEAPI"
    ) as mock_cls:
        instance = MagicMock()
        instance.connect.side_effect = JouleBLEError("Bluetooth failed")
        mock_cls.return_value = instance

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_MAC_ADDRESS: TEST_MAC}
        )

    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_form_shows_unknown_error_on_unexpected_exception(
    hass: HomeAssistant,
) -> None:
    """An unexpected exception during validation shows an unknown error."""
    with patch(
        "custom_components.joule_sous_vide.config_flow.JouleBLEAPI"
    ) as mock_cls:
        instance = MagicMock()
        instance.connect.side_effect = RuntimeError("Unexpected crash")
        mock_cls.return_value = instance

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_MAC_ADDRESS: TEST_MAC}
        )

    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["errors"] == {"base": "unknown"}


async def test_form_aborts_if_already_configured(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Submitting the same MAC address as an existing entry aborts the flow."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.joule_sous_vide.config_flow.JouleBLEAPI"
    ) as mock_cls:
        instance = MagicMock()
        mock_cls.return_value = instance

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_MAC_ADDRESS: TEST_MAC}
        )

    assert result["type"] == data_entry_flow.FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_connect_and_disconnect_called_during_validation(
    hass: HomeAssistant,
) -> None:
    """The config flow connects then immediately disconnects to validate the MAC."""
    with patch(
        "custom_components.joule_sous_vide.config_flow.JouleBLEAPI"
    ) as mock_cls:
        instance = MagicMock()
        mock_cls.return_value = instance

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_MAC_ADDRESS: TEST_MAC}
        )

    instance.connect.assert_called_once()
    instance.disconnect.assert_called_once()
