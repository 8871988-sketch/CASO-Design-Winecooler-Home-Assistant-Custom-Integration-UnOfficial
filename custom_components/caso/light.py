"""Interior lights of the CASO wine cooler."""

from __future__ import annotations

from typing import Any

from homeassistant.components.light import ColorMode, LightEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import CasoConfigEntry
from .const import ZONE_ALL
from .entity import ZONE_KEYS, CasoEntity, CasoZoneEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: CasoConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the lights."""
    coordinator = entry.runtime_data
    entities: list[LightEntity] = [CasoZoneLight(coordinator, zone) for zone in ZONE_KEYS]
    entities.append(CasoAllLights(coordinator, "light"))
    async_add_entities(entities)


class CasoZoneLight(CasoZoneEntity, LightEntity):
    """Light of one zone."""

    _attr_color_mode = ColorMode.ONOFF
    _attr_supported_color_modes = {ColorMode.ONOFF}

    def __init__(self, coordinator, zone: int) -> None:
        """Initialize."""
        super().__init__(coordinator, zone, "light")
        self._attr_translation_key = f"{ZONE_KEYS[zone]}_light"

    @property
    def is_on(self) -> bool | None:
        """Light on."""
        zone = self.zone
        return None if zone is None else zone.light

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on."""
        await self.coordinator.async_set_light(self._zone, True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off."""
        await self.coordinator.async_set_light(self._zone, False)


class CasoAllLights(CasoEntity, LightEntity):
    """Lights of all zones together."""

    _attr_translation_key = "light"
    _attr_color_mode = ColorMode.ONOFF
    _attr_supported_color_modes = {ColorMode.ONOFF}

    @property
    def is_on(self) -> bool | None:
        """On when any zone light is on."""
        data = self.coordinator.data
        if data is None:
            return None
        states = [zone.light for zone in data.zones.values() if zone.light is not None]
        return any(states) if states else None

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on."""
        await self.coordinator.async_set_light(ZONE_ALL, True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off."""
        await self.coordinator.async_set_light(ZONE_ALL, False)
