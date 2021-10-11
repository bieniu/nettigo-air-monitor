"""Constants for nettigo-air-monitor library."""
from __future__ import annotations

from typing import Final

ATTR_DATA: Final[str] = "data"
ATTR_SENSOR_VALUES: Final[str] = "sensordatavalues"
ATTR_UPTIME: Final[str] = "uptime"
ATTR_VALUES: Final[str] = "values"

RETRIES: Final[int] = 4
TIMEOUT: Final[int] = 5

ENDPOINTS: Final[dict[str, str]] = {
    ATTR_DATA: "http://{host}/data.json",
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
