"""Sensors of the CASO wine cooler."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import EntityCategory, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import CasoConfigEntry
from .api import CasoZone
from .entity import ZONE_KEYS, CasoEntity, CasoZoneEntity


@dataclass(frozen=True, kw_only=True)
class CasoZoneSensorDescription(SensorEntityDescription):
    """Zone sensor."""

    value_fn: Callable[[CasoZone], int | None]


ZONE_SENSORS = (
    CasoZoneSensorDescription(
        key="temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_fn=lambda zone: zone.temperature,
    ),
    CasoZoneSensorDescription(
        key="target_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_fn=lambda zone: zone.target_temperature,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: CasoConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the sensors."""
    coordinator = entry.runtime_data
    entities: list[SensorEntity] = [
        CasoZoneSensor(coordinator, zone, description)
        for zone in ZONE_KEYS
        for description in ZONE_SENSORS
    ]
    entities.append(CasoLastUpdateSensor(coordinator, "last_update"))
    async_add_entities(entities)


class CasoZoneSensor(CasoZoneEntity, SensorEntity):
    """Temperature of a zone."""

    entity_description: CasoZoneSensorDescription

    def __init__(self, coordinator, zone: int, description: CasoZoneSensorDescription) -> None:
        """Initialize."""
        super().__init__(coordinator, zone, description.key)
        self.entity_description = description
        self._attr_translation_key = f"{ZONE_KEYS[zone]}_{description.key}"

    @property
    def native_value(self) -> int | None:
        """Value."""
        zone = self.zone
        return None if zone is None else self.entity_description.value_fn(zone)


class CasoLastUpdateSensor(CasoEntity, SensorEntity):
    """Time of the last report of the device to the cloud."""

    _attr_translation_key = "last_update"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self) -> datetime | None:
        """Value."""
        data = self.coordinator.data
        return data.updated if data else None
