"""Config flow for the Joule Sous Vide integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .const import CONF_MAC_ADDRESS, DOMAIN
from .joule_ble import JouleBLEAPI, JouleBLEError

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_MAC_ADDRESS): str,
    }
)


class JouleConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the user-facing configuration flow.

    Prompts for the Joule's Bluetooth MAC address and validates it by
    attempting a real BLE connection before creating the config entry.
    """

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Show the MAC address form and validate the connection."""
        errors: dict[str, str] = {}

        if user_input is not None:
            mac_address = user_input[CONF_MAC_ADDRESS]

            await self.async_set_unique_id(mac_address)
            self._abort_if_unique_id_configured()

            api = JouleBLEAPI(mac_address)
            try:
                await self.hass.async_add_executor_job(api.connect)
                await self.hass.async_add_executor_job(api.disconnect)
            except JouleBLEError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected error connecting to Joule at %s", mac_address)
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=f"Joule {mac_address}",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )
