"""Constants for nettigo-air-monitor library."""
from __future__ import annotations

from typing import Final

from aiohttp.client import ClientTimeout

ATTR_CONFIG: Final[str] = "config"
ATTR_DATA: Final[str] = "data"
ATTR_OTA: Final[str] = "ota"
ATTR_RESTART: Final[str] = "restart"
ATTR_SENSOR_VALUES: Final[str] = "sensordatavalues"
ATTR_UPTIME: Final[str] = "uptime"
ATTR_VALUES: Final[str] = "values"

DEFAULT_TIMEOUT: Final[ClientTimeout] = ClientTimeout(total=5)

RESPONSES_FROM_CACHE: Final[int] = 3

VALUES_TO_ROUND: Final[list[str]] = [
    "conc_co2_ppm",
    "pms_p0",
    "pms_p1",
    "pms_p2",
    "sds_p1",
    "sds_p2",
    "sps30_p0",
    "sps30_p1",
    "sps30_p2",
    "sps30_p4",
    "signal",
]

ENDPOINTS: Final[dict[str, str]] = {
    ATTR_CONFIG: "http://{host}/config.json",
    ATTR_DATA: "http://{host}/data.json",
    ATTR_OTA: "http://{host}/ota",
    ATTR_RESTART: "http://{host}/reset",
    ATTR_VALUES: "http://{host}/values",
}

RENAME_KEY_MAP: Final[list[tuple[str, str]]] = [
    ("bmp_pressure", "bmp180_pressure"),
    ("bmp_temperature", "bmp180_temperature"),
    ("conc_co2_ppm", "mhz14a_carbon_dioxide"),
    ("humidity", "dht22_humidity"),
    ("sds_p1", "sds011_p1"),
    ("sds_p2", "sds011_p2"),
    ("temperature", "dht22_temperature"),
]

MAC_PATTERN: Final[str] = r"([0-9a-fA-F]{2}[:]){5}([0-9a-fA-F]{2})"
