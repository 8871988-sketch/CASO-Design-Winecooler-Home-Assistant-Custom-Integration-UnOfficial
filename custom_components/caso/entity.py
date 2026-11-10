"""Base entity for the CASO wine cooler integration."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import CasoZone
from .const import DOMAIN, MANUFACTURER
from .coordinator import CasoCoordinator

ZONE_KEYS = {1: "top", 2: "bottom"}


class CasoEntity(CoordinatorEntity[CasoCoordinator]):
    """Entity of the wine cooler."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: CasoCoordinator, key: str) -> None:
        """Initialize."""
        super().__init__(coordinator)
        device_id = coordinator.client.device_id
        self._attr_unique_id = f"{device_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            name=coordinator.config_entry.title,
            manufacturer=MANUFACTURER,
            model="Wine cooler (2 zones)",
            configuration_url="https://www.casoapp.com/devices",
        )


class CasoZoneEntity(CasoEntity):
    """Entity of one zone."""

    def __init__(self, coordinator: CasoCoordinator, zone: int, key: str) -> None:
        """Initialize."""
        super().__init__(coordinator, f"{ZONE_KEYS[zone]}_{key}")
        self._zone = zone

    @property
    def zone(self) -> CasoZone | None:
        """Current state of the zone."""
        data = self.coordinator.data
        return data.zones.get(self._zone) if data else None
