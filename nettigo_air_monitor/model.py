"""Type definitions for NAM."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class NAMSensors:  # pylint: disable=too-many-instance-attributes
    """Data class for NAM sensors."""

    bme280_humidity: Optional[float]
    bme280_pressure: Optional[float]
    bme280_temperature: Optional[float]
    bmp280_pressure: Optional[float]
    bmp280_temperature: Optional[float]
    dht22_humidity: Optional[float]
    dht22_temperature: Optional[float]
    heca_humidity: Optional[float]
    heca_temperature: Optional[float]
    mhz14a_carbon_dioxide: Optional[int]
    sds_p1: Optional[float]
    sds_p2: Optional[float]
    sht3x_humidity: Optional[float]
    sht3x_temperature: Optional[float]
    signal: Optional[int]
    sps30_p0: Optional[float]
    sps30_p1: Optional[float]
    sps30_p2: Optional[float]
    sps30_p4: Optional[float]
    uptime: Optional[int]
