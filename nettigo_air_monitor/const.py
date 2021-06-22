"""Constants for nettigo-air-monitor library."""
from typing import Dict

ATTR_DATA: str = "data"
ATTR_SENSOR_VALUES: str = "sensordatavalues"
ATTR_UPTIME = "uptime"
ATTR_VALUES: str = "values"

HTTP_OK: int = 200

RETRIES: int = 4
TIMEOUT: int = 5

ENDPOINTS: Dict[str, str] = {
    ATTR_DATA: "http://{host}/data.json",
    ATTR_VALUES: "http://{host}/values",
}

RENAME_KEY_MAP = [
    ("conc_co2_ppm", "mhz14a_carbon_dioxide"),
    ("humidity", "dht22_humidity"),
    ("sds_p1", "sds011_p1"),
    ("sds_p2", "sds011_p2"),
    ("temperature", "dht22_temperature"),
]

MAC_PATTERN: str = r"([0-9a-fA-F]{2}[:]){5}([0-9a-fA-F]{2})"
