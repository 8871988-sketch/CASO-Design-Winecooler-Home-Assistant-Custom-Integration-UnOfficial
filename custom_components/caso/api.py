"""Async client for the CASO public kitchen API (wine coolers).

API: https://publickitchenapi.casoapp.com (Swagger under /swagger).

* ``POST /api/v1.1/Winecooler/Status``   body ``{"technicalDeviceId": "..."}``
* ``POST /api/v1.1/Winecooler/SetLight`` body ``{"technicalDeviceId": "...",
  "zone": 0|1|2, "lightOn": true|false}`` (0 = all zones, 1 = top, 2 = bottom)

The API key is sent in the ``x-api-key`` header. Temperatures are whole °C.

This module has no Home Assistant dependencies so it can be tested alone.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
import logging
from typing import Any

import aiohttp

from .const import LIGHT_URL, STATUS_URL

_LOGGER = logging.getLogger(__name__)


class CasoError(Exception):
    """Base error."""


class CasoConnectionError(CasoError):
    """Cloud not reachable, timeout or server error."""


class CasoAuthError(CasoError):
    """API key rejected."""


class CasoDeviceError(CasoError):
    """Device id unknown or request rejected."""


class CasoRateLimitError(CasoError):
    """Too many requests."""


@dataclass
class CasoZone:
    """State of one zone."""

    temperature: int | None
    target_temperature: int | None
    power: bool | None
    light: bool | None


@dataclass
class CasoStatus:
    """Status of the whole wine cooler."""

    zones: dict[int, CasoZone]
    updated: datetime | None
    hint: str | None


def _int(value: Any) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _bool(value: Any) -> bool | None:
    return value if isinstance(value, bool) else None


def _time(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def parse_status(data: dict[str, Any]) -> CasoStatus:
    """Parse the JSON of the Status call."""
    if not isinstance(data, dict):
        raise CasoError(f"Unexpected status response: {data!r:.100}")
    zones = {
        zone: CasoZone(
            temperature=_int(data.get(f"temperature{zone}")),
            target_temperature=_int(data.get(f"targetTemperature{zone}")),
            power=_bool(data.get(f"power{zone}")),
            light=_bool(data.get(f"light{zone}")),
        )
        for zone in (1, 2)
    }
    hint = data.get("hint")
    return CasoStatus(
        zones=zones,
        updated=_time(data.get("logTimestampUtc")),
        hint=hint if isinstance(hint, str) and hint else None,
    )


class CasoClient:
    """Client for one CASO wine cooler."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        api_key: str,
        device_id: str,
        timeout: float = 30,
    ) -> None:
        """Initialize."""
        self._session = session
        self._api_key = api_key.strip()
        self.device_id = device_id.strip()
        self._timeout = aiohttp.ClientTimeout(total=timeout)

    async def _post(self, url: str, payload: dict[str, Any]) -> Any:
        headers = {
            "x-api-key": self._api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        try:
            async with self._session.post(
                url, json=payload, headers=headers, timeout=self._timeout
            ) as resp:
                text = await resp.text()
                status = resp.status
        except (aiohttp.ClientError, TimeoutError) as err:
            raise CasoConnectionError(f"Error talking to the CASO cloud: {err!r}") from err
        if status in (401, 403):
            raise CasoAuthError(f"API key rejected (HTTP {status})")
        if status == 429:
            raise CasoRateLimitError("Too many requests (HTTP 429)")
        if status >= 500:
            raise CasoConnectionError(f"CASO cloud error (HTTP {status})")
        if status != 200:
            raise CasoDeviceError(f"Request rejected (HTTP {status}): {text[:200]}")
        if not text:
            return None
        try:
            return json.loads(text)
        except ValueError:
            return text

    async def async_get_status(self) -> CasoStatus:
        """Read the current status."""
        data = await self._post(STATUS_URL, {"technicalDeviceId": self.device_id})
        return parse_status(data)

    async def async_set_light(self, zone: int, on: bool) -> None:
        """Switch the light of a zone (0 = all zones)."""
        await self._post(
            LIGHT_URL,
            {"technicalDeviceId": self.device_id, "zone": int(zone), "lightOn": bool(on)},
        )
