"""CASO wine cooler integration (CASO public kitchen API)."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import CasoClient
from .const import CONF_DEVICE_ID
from .coordinator import CasoCoordinator

PLATFORMS: list[Platform] = [Platform.BINARY_SENSOR, Platform.LIGHT, Platform.SENSOR]

type CasoConfigEntry = ConfigEntry[CasoCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: CasoConfigEntry) -> bool:
    """Set up a CASO wine cooler from a config entry."""
    client = CasoClient(
        async_get_clientsession(hass), entry.data[CONF_API_KEY], entry.data[CONF_DEVICE_ID]
    )
    coordinator = CasoCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: CasoConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _async_update_listener(hass: HomeAssistant, entry: CasoConfigEntry) -> None:
    """Reload when options change."""
    await hass.config_entries.async_reload(entry.entry_id)
