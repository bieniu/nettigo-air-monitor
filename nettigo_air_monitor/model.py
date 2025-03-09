"""Type definitions for NAM."""

from dataclasses import dataclass

import aiohttp


@dataclass
class ConnectionOptions:
    """Options for NAM."""

    host: str
    username: str | None = None
    password: str | None = None
    auth: aiohttp.BasicAuth | None = None

    def __post_init__(self) -> None:
        """Call after initialization."""
        if self.username is not None:
            if self.password is None:
                raise ValueError("Supply both username and password")

            object.__setattr__(
                self, "auth", aiohttp.BasicAuth(self.username, self.password)
            )


@dataclass(frozen=True)
class NAMSensors:
    """Data class for NAM sensors."""

    bh1750_illuminance: float | None
    bme280_humidity: float | None
    bme280_pressure: float | None
    bme280_temperature: float | None
    bmp180_pressure: float | None
    bmp180_temperature: float | None
    bmp280_pressure: float | None
    bmp280_temperature: float | None
    dht22_humidity: float | None
    dht22_temperature: float | None
    ds18b20_temperature: float | None
    heca_humidity: float | None
    heca_temperature: float | None
    mhz14a_carbon_dioxide: float | None
    pms_caqi: int | None
    pms_caqi_level: str | None
    pms_p0: float | None
    pms_p1: float | None
    pms_p2: float | None
    sds011_caqi: int | None
    sds011_caqi_level: str | None
    sds011_p1: float | None
    sds011_p2: float | None
    sht3x_humidity: float | None
    sht3x_temperature: float | None
    signal: float | None
    sps30_caqi: int | None
    sps30_caqi_level: str | None
    sps30_p0: float | None
    sps30_p1: float | None
    sps30_p2: float | None
    sps30_p4: float | None
    uptime: int | None
