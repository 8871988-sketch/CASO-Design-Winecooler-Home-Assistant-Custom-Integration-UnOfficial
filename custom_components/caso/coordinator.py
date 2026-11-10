"""Data update coordinator for the CASO wine cooler integration."""

from __future__ import annotations

from dataclasses import replace
from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, HomeAssistantError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import CasoAuthError, CasoClient, CasoError, CasoStatus
from .const import CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL, DOMAIN, ZONE_ALL

_LOGGER = logging.getLogger(__name__)

# Failed polls in a row that keep the last state before entities go unavailable.
MAX_FAILED_POLLS = 2


class CasoCoordinator(DataUpdateCoordinator[CasoStatus]):
    """Polls the CASO cloud."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, client: CasoClient) -> None:
        """Initialize."""
        minutes = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(minutes=minutes),
        )
        self.client = client
        self._failed_polls = 0

    async def _async_update_data(self) -> CasoStatus:
        try:
            status = await self.client.async_get_status()
        except CasoAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except CasoError as err:
            if self.data is not None and self._failed_polls < MAX_FAILED_POLLS:
                self._failed_polls += 1
                _LOGGER.debug(
                    "Poll failed (%s), keeping last state (%d/%d)",
                    err, self._failed_polls, MAX_FAILED_POLLS,
                )
                return self.data
            raise UpdateFailed(str(err)) from err
        self._failed_polls = 0
        return status

    async def async_set_light(self, zone: int, on: bool) -> None:
        """Switch a light and update the state locally.

        No extra status call: the cloud is meant to be polled rarely.
        """
        try:
            await self.client.async_set_light(zone, on)
        except CasoAuthError as err:
            self.config_entry.async_start_reauth(self.hass)
            raise HomeAssistantError(f"CASO API key rejected: {err}") from err
        except CasoError as err:
            raise HomeAssistantError(f"Switching the light failed: {err}") from err
        if self.data is None:
            return
        zones = dict(self.data.zones)
        for number in zones if zone == ZONE_ALL else (zone,):
            if number in zones:
                zones[number] = replace(zones[number], light=on)
        self.async_set_updated_data(replace(self.data, zones=zones))
