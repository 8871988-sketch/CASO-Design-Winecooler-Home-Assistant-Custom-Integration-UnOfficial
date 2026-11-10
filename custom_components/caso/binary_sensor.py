"""Binary sensors of the CASO wine cooler."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import CasoConfigEntry
from .entity import ZONE_KEYS, CasoZoneEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: CasoConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the binary sensors."""
    coordinator = entry.runtime_data
    async_add_entities(CasoZonePower(coordinator, zone) for zone in ZONE_KEYS)


class CasoZonePower(CasoZoneEntity, BinarySensorEntity):
    """Zone switched on (cooling active)."""

    _attr_device_class = BinarySensorDeviceClass.POWER

    def __init__(self, coordinator, zone: int) -> None:
        """Initialize."""
        super().__init__(coordinator, zone, "power")
        self._attr_translation_key = f"{ZONE_KEYS[zone]}_power"

    @property
    def is_on(self) -> bool | None:
        """Zone on."""
        zone = self.zone
        return None if zone is None else zone.power
