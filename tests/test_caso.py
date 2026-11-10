"""Tests for the CASO wine cooler integration."""

from __future__ import annotations

from datetime import timedelta

from homeassistant import config_entries
from homeassistant.const import STATE_OFF, STATE_ON, STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import MockConfigEntry, async_fire_time_changed

from custom_components.caso.api import parse_status
from custom_components.caso.const import DOMAIN, LIGHT_URL

from .conftest import API_KEY, DEVICE_ID, FakeCloud

TOP_T = "sensor.weinkuhlschrank_top_zone_temperature"
TOP_SET = "sensor.weinkuhlschrank_top_zone_target_temperature"
BOTTOM_T = "sensor.weinkuhlschrank_bottom_zone_temperature"
BOTTOM_SET = "sensor.weinkuhlschrank_bottom_zone_target_temperature"
TOP_LIGHT = "light.weinkuhlschrank_top_zone_light"
BOTTOM_LIGHT = "light.weinkuhlschrank_bottom_zone_light"
ALL_LIGHT = "light.weinkuhlschrank_light"


async def _setup(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


def test_parse_status() -> None:
    """Zones are mapped 1 = top, 2 = bottom; missing values are None."""
    status = parse_status({"temperature1": 12, "targetTemperature2": 6, "power2": True})
    assert status.zones[1].temperature == 12
    assert status.zones[1].target_temperature is None
    assert status.zones[2].target_temperature == 6
    assert status.zones[2].power is True
    assert status.updated is None


async def test_user_flow(hass: HomeAssistant, cloud: FakeCloud) -> None:
    """Wrong key -> error, right key -> entry; key is not echoed back."""
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    assert result["type"] is FlowResultType.FORM

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"name": "Weinkühlschrank", "api_key": "wrong", "device_id": DEVICE_ID}
    )
    assert result["errors"] == {"base": "invalid_auth"}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"name": "Weinkühlschrank", "api_key": API_KEY, "device_id": "nope"}
    )
    assert result["errors"] == {"base": "invalid_device"}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"name": "Weinkühlschrank", "api_key": f" {API_KEY} ", "device_id": DEVICE_ID}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {"api_key": API_KEY, "device_id": DEVICE_ID}
    assert result["result"].unique_id == DEVICE_ID


async def test_cannot_connect(hass: HomeAssistant, cloud: FakeCloud) -> None:
    """Server error -> cannot_connect."""
    cloud.http_status = 503
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
        data={"name": "W", "api_key": API_KEY, "device_id": DEVICE_ID},
    )
    assert result["errors"] == {"base": "cannot_connect"}


async def test_entities(hass: HomeAssistant, cloud: FakeCloud, config_entry: MockConfigEntry) -> None:
    """Temperatures and zones are read correctly (no swapped values)."""
    await _setup(hass, config_entry)
    assert hass.states.get(TOP_T).state == "12"
    assert hass.states.get(TOP_SET).state == "12"
    assert hass.states.get(BOTTOM_T).state == "7"
    assert hass.states.get(BOTTOM_SET).state == "6"
    assert hass.states.get("binary_sensor.weinkuhlschrank_top_zone").state == STATE_ON
    assert hass.states.get(TOP_LIGHT).state == STATE_OFF
    assert hass.states.get(ALL_LIGHT).state == STATE_OFF
    assert hass.states.get("sensor.weinkuhlschrank_last_report").state.startswith("2026-11-10T11:58:03")


async def test_lights(
    hass: HomeAssistant, cloud: FakeCloud, config_entry: MockConfigEntry, aioclient_mock
) -> None:
    """Light calls use zone 1/2/0 and update the state without an extra poll."""
    await _setup(hass, config_entry)
    polls = sum(1 for url, *_ in cloud.requests if url != LIGHT_URL)

    await hass.services.async_call("light", "turn_on", {"entity_id": BOTTOM_LIGHT}, blocking=True)
    assert cloud.requests[-1][1] == {"technicalDeviceId": DEVICE_ID, "zone": 2, "lightOn": True}
    assert hass.states.get(BOTTOM_LIGHT).state == STATE_ON
    assert hass.states.get(TOP_LIGHT).state == STATE_OFF
    assert hass.states.get(ALL_LIGHT).state == STATE_ON

    await hass.services.async_call("light", "turn_off", {"entity_id": ALL_LIGHT}, blocking=True)
    assert cloud.requests[-1][1] == {"technicalDeviceId": DEVICE_ID, "zone": 0, "lightOn": False}
    assert hass.states.get(BOTTOM_LIGHT).state == STATE_OFF

    await hass.services.async_call("light", "turn_on", {"entity_id": TOP_LIGHT}, blocking=True)
    assert cloud.requests[-1][1]["zone"] == 1
    assert sum(1 for url, *_ in cloud.requests if url != LIGHT_URL) == polls


async def test_outage_and_reauth(
    hass: HomeAssistant, cloud: FakeCloud, config_entry: MockConfigEntry
) -> None:
    """Short outage keeps values; a rejected key starts reauth."""
    await _setup(hass, config_entry)
    cloud.http_status = 503
    now = dt_util.utcnow()
    for minutes in (6, 12):
        async_fire_time_changed(hass, now + timedelta(minutes=minutes))
        await hass.async_block_till_done()
        assert hass.states.get(TOP_T).state == "12"
    async_fire_time_changed(hass, now + timedelta(minutes=18))
    await hass.async_block_till_done()
    assert hass.states.get(TOP_T).state == STATE_UNAVAILABLE

    cloud.http_status = 401
    async_fire_time_changed(hass, now + timedelta(minutes=24))
    await hass.async_block_till_done()
    flows = hass.config_entries.flow.async_progress()
    assert any(f["context"]["source"] == "reauth" for f in flows)


async def test_reconfigure_new_key(
    hass: HomeAssistant, cloud: FakeCloud, config_entry: MockConfigEntry
) -> None:
    """The API key can be replaced in the UI."""
    await _setup(hass, config_entry)
    result = await config_entry.start_reconfigure_flow(hass)
    assert result["step_id"] == "reconfigure"
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"api_key": "wrong"})
    assert result["errors"] == {"base": "invalid_auth"}
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"api_key": API_KEY})
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
