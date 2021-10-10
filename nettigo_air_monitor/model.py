"""Type definitions for NAM."""
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class NAMSensors:
    """Data class for NAM sensors."""

    bme280_humidity: Optional[float]
    bme280_pressure: Optional[int]
    bme280_temperature: Optional[float]
    bmp180_pressure: Optional[int]
    bmp180_temperature: Optional[float]
    bmp280_pressure: Optional[int]
    bmp280_temperature: Optional[float]
    dht22_humidity: Optional[float]
    dht22_temperature: Optional[float]
    heca_humidity: Optional[float]
    heca_temperature: Optional[float]
    mhz14a_carbon_dioxide: Optional[int]
    sds011_p1: Optional[int]
    sds011_p2: Optional[int]
    sht3x_humidity: Optional[float]
    sht3x_temperature: Optional[float]
    signal: Optional[int]
    sps30_p0: Optional[int]
    sps30_p1: Optional[int]
    sps30_p2: Optional[int]
    sps30_p4: Optional[int]
    uptime: Optional[int]
