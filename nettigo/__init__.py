"""
Python wrapper for getting air quality data from Nettigo Air Monitor devices.
"""
import asyncio
import logging
import re
from typing import Optional

import async_timeout
from aiohttp import ClientSession
from aiohttp.client_exceptions import ClientConnectorError

from .const import ATTR_DATA, ATTR_VALUES, ENDPOINTS, HTTP_OK, MAC_PATTERN

_LOGGER = logging.getLogger(__name__)


class DictToObj(dict):
    """Dictionary to object class."""

    def __getattr__(self, name):
        if name in self:
            return self[name]
        raise AttributeError("No such attribute: " + name)


class Nettigo:
    """Main class to perform Nettigo requests"""

    def __init__(self, session: ClientSession, host: Optional[str] = None):
        """Initialize."""
        self._session = session
        self._host = host
        self._software_version = None

    @staticmethod
    def _construct_url(arg: str, **kwargs) -> str:
        """Construct Nettigo URL."""
        return ENDPOINTS[arg].format(**kwargs)

    @staticmethod
    def _parse_sensor_data(data: dict) -> dict:
        """Parse sensor data dict."""
        return {
            item["value_type"].lower(): int(item["value"])
            if item["value_type"] == "signal"
            else (
                round(float(item["value"]) / 100)
                if item["value_type"] in ["BME280_pressure", "BMP280_pressure"]
                else round(float(item["value"]), 1)
            )
            for item in data
        }

    async def _async_get_data(self, url: str, retries=3, timeout=5, use_json=True):
        """Retreive data from the device."""
        with async_timeout.timeout(retries * timeout):
            last_error = None
            for retry in range(retries):
                try:
                    resp = await self._session.get(url)
                except ClientConnectorError as error:
                    _LOGGER.info(
                        "Invalid response from device: %s, retry: %s", self._host, retry
                    )
                    last_error = error
                else:
                    if resp.status != HTTP_OK:
                        raise ApiError(
                            f"Invalid response from device {self._host}: {resp.status}"
                        )

                    _LOGGER.debug(
                        "Data retrieved from %s, status: %s", self._host, resp.status
                    )
                    return await resp.json() if use_json else await resp.text()
                _LOGGER.debug("Waiting %s seconds...", timeout + retry)
                await asyncio.sleep(timeout + retry)

            raise ApiError(str(last_error))

    async def async_update(self) -> DictToObj:
        """Retreive data from the device."""
        url = self._construct_url(ATTR_DATA, host=self._host)

        data = await self._async_get_data(url)

        self._software_version = data["software_version"]

        try:
            sensors = self._parse_sensor_data(data["sensordatavalues"])
        except (TypeError, TypeError) as err:
            raise InvalidSensorData("Invalid sensor data") from err

        return DictToObj(sensors)

    async def async_get_mac_address(self):
        """Retreive the device MAC address."""
        url = self._construct_url(ATTR_VALUES, host=self._host)
        data = await self._async_get_data(url, use_json=False)
        mac = re.search(MAC_PATTERN, data)

        if not mac:
            raise CannotGetMac("Cannot get MAC address from device")

        return mac[0]

    @property
    def software_version(self) -> Optional[str]:
        """Return software version."""
        return self._software_version


class ApiError(Exception):
    """Raised when request ended in error."""

    def __init__(self, status: str):
        """Initialize."""
        super().__init__(status)
        self.status = status


class CannotGetMac(Exception):
    """Raised when cannot get device MAC address."""

    def __init__(self, status: str):
        """Initialize."""
        super().__init__(status)
        self.status = status


class InvalidSensorData(Exception):
    """Raised when sensor data is invalid."""

    def __init__(self, status: str):
        """Initialize."""
        super().__init__(status)
        self.status = status
