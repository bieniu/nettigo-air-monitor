"""Constants for nettigo-air-monitor library."""
ATTR_DATA = "data"
ATTR_SENSOR_VALUES = "sensordatavalues"
ATTR_VALUES = "values"

HTTP_OK = 200

ENDPOINTS = {
    ATTR_DATA: "http://{host}/data.json",
    ATTR_VALUES: "http://{host}/values",
}

MAC_PATTERN = r"([0-9a-fA-F]{2}[:]){5}([0-9a-fA-F]{2})"
