"""Config flow for the CASO wine cooler integration."""

from __future__ import annotations

from collections.abc import Mapping
import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_API_KEY, CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import TextSelector, TextSelectorConfig, TextSelectorType

from .api import CasoAuthError, CasoClient, CasoConnectionError, CasoDeviceError, CasoError
from .const import (
    CONF_DEVICE_ID,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MAX_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = "Wine Cooler"
_SECRET = TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD))

USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME, default=DEFAULT_NAME): str,
        vol.Required(CONF_API_KEY): _SECRET,
        vol.Required(CONF_DEVICE_ID): str,
    }
)
REAUTH_SCHEMA = vol.Schema({vol.Required(CONF_API_KEY): _SECRET})


async def _async_validate(hass: HomeAssistant, api_key: str, device_id: str) -> dict[str, str]:
    """Read the status once. Return errors (empty if fine)."""
    client = CasoClient(async_get_clientsession(hass), api_key, device_id)
    try:
        await client.async_get_status()
    except CasoAuthError:
        return {"base": "invalid_auth"}
    except CasoDeviceError:
        return {"base": "invalid_device"}
    except CasoConnectionError:
        return {"base": "cannot_connect"}
    except CasoError:
        _LOGGER.exception("Unexpected response from the CASO cloud")
        return {"base": "unknown"}
    except Exception:  # noqa: BLE001
        _LOGGER.exception("Unexpected error")
        return {"base": "unknown"}
    return {}


class CasoConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Ask for API key and device id."""
        errors: dict[str, str] = {}
        if user_input is not None:
            device_id = user_input[CONF_DEVICE_ID].strip()
            api_key = user_input[CONF_API_KEY].strip()
            await self.async_set_unique_id(device_id)
            self._abort_if_unique_id_configured()
            errors = await _async_validate(self.hass, api_key, device_id)
            if not errors:
                return self.async_create_entry(
                    title=user_input[CONF_NAME].strip() or DEFAULT_NAME,
                    data={CONF_API_KEY: api_key, CONF_DEVICE_ID: device_id},
                )
        suggested = {k: v for k, v in (user_input or {}).items() if k != CONF_API_KEY}
        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(USER_SCHEMA, suggested),
            errors=errors,
        )

    async def async_step_reauth(self, entry_data: Mapping[str, Any]) -> ConfigFlowResult:
        """API key stopped working."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask for a new API key."""
        return await self._async_new_key("reauth_confirm", self._get_reauth_entry(), user_input)

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Replace the API key (e.g. after renewing it)."""
        return await self._async_new_key("reconfigure", self._get_reconfigure_entry(), user_input)

    async def _async_new_key(
        self, step_id: str, entry: ConfigEntry, user_input: dict[str, Any] | None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            api_key = user_input[CONF_API_KEY].strip()
            errors = await _async_validate(self.hass, api_key, entry.data[CONF_DEVICE_ID])
            if not errors:
                return self.async_update_reload_and_abort(
                    entry, data_updates={CONF_API_KEY: api_key}
                )
        return self.async_show_form(
            step_id=step_id,
            data_schema=REAUTH_SCHEMA,
            description_placeholders={"name": entry.title},
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Options."""
        return CasoOptionsFlow()


class CasoOptionsFlow(OptionsFlow):
    """Polling interval."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Manage options."""
        if user_input is not None:
            return self.async_create_entry(data=user_input)
        current = self.config_entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_SCAN_INTERVAL, default=current): vol.All(
                        vol.Coerce(int), vol.Range(min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL)
                    )
                }
            ),
        )
