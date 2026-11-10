"""Fixtures."""

from __future__ import annotations

import json

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import (
    AiohttpClientMocker,
    AiohttpClientMockResponse,
)

from custom_components.caso.const import CONF_DEVICE_ID, DOMAIN, LIGHT_URL, STATUS_URL

API_KEY = "test-key"
DEVICE_ID = "1001-abcdef"


class FakeCloud:
    """Fake CASO public kitchen API."""

    def __init__(self) -> None:
        self.status = {
            "temperature1": 12, "targetTemperature1": 12, "power1": True, "light1": False,
            "temperature2": 7, "targetTemperature2": 6, "power2": True, "light2": False,
            "logTimestampUtc": "2026-11-10T11:58:03.123Z", "hint": "",
        }
        self.http_status = 200
        self.requests: list[tuple[str, dict, dict]] = []

    def handle(self, url: str, payload: dict, headers: dict) -> tuple[int, str]:
        self.requests.append((url, payload, headers))
        if self.http_status != 200:
            return self.http_status, "error"
        if headers.get("x-api-key") != API_KEY:
            return 401, "unauthorized"
        if payload.get("technicalDeviceId") != DEVICE_ID:
            return 400, "unknown device"
        if url == STATUS_URL:
            return 200, json.dumps(self.status)
        if url == LIGHT_URL:
            zones = (1, 2) if payload["zone"] == 0 else (payload["zone"],)
            for zone in zones:
                self.status[f"light{zone}"] = payload["lightOn"]
            return 200, ""
        return 404, ""


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations."""
    return


@pytest.fixture
def cloud(aioclient_mock: AiohttpClientMocker) -> FakeCloud:
    """Route API calls to the fake cloud."""
    fake = FakeCloud()

    def make(url_const: str):
        async def handler(method, url, data):
            headers = dict(aioclient_mock.mock_calls[-1][3] or {})
            payload = data if isinstance(data, dict) else json.loads(data or "{}")
            status, text = fake.handle(url_const, payload, headers)
            return AiohttpClientMockResponse(method, url, status=status, text=text)

        return handler

    for url_const in (STATUS_URL, LIGHT_URL):
        aioclient_mock.post(url_const, side_effect=make(url_const))
    return fake


@pytest.fixture
def config_entry() -> MockConfigEntry:
    """Config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="Weinkühlschrank",
        unique_id=DEVICE_ID,
        data={"api_key": API_KEY, CONF_DEVICE_ID: DEVICE_ID},
    )
