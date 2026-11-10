"""Constants for the CASO wine cooler integration."""

from __future__ import annotations

DOMAIN = "caso"
MANUFACTURER = "CASO Design"

BASE_URL = "https://publickitchenapi.casoapp.com"
STATUS_URL = f"{BASE_URL}/api/v1.1/Winecooler/Status"
LIGHT_URL = f"{BASE_URL}/api/v1.1/Winecooler/SetLight"

CONF_DEVICE_ID = "device_id"
CONF_SCAN_INTERVAL = "scan_interval"
# The CASO cloud is meant to be polled at most every 5 minutes.
DEFAULT_SCAN_INTERVAL = 5  # minutes
MIN_SCAN_INTERVAL = 5
MAX_SCAN_INTERVAL = 60

# Light zones of the SetLight call.
ZONE_ALL = 0
ZONE_TOP = 1
ZONE_BOTTOM = 2
