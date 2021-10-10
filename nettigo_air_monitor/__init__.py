"""
Python wrapper for getting air quality data from Nettigo Air Monitor devices.
"""
from __future__ import annotations

import asyncio
import logging
import re
from http import HTTPStatus
from typing import Any, cast

from aiohttp import ClientSession
from aiohttp.client_exceptions import ClientConnectorError
from dacite import from_dict

from .const import (
    ATTR_DATA,
    ATTR_UPTIME,
    ATTR_VALUES,
    ENDPOINTS,
    MAC_PATTERN,
    RENAME_KEY_MAP,
    RETRIES,
    TIMEOUT,
)
from .model import NAMSensors

_LOGGER = logging.getLogger(__name__)


class NettigoAirMonitor:
    """Main class to perform Nettigo Air Monitor requests"""

    def __init__(self, session: ClientSession, host: str) -> None:
        """Initialize."""
        self._session = session
        self._host = host
        self._software_version: str

    @staticmethod
    def _construct_url(arg: str, **kwargs: str) -> str:
        """Construct Nettigo Air Monitor URL."""
        return ENDPOINTS[arg].format(**kwargs)

    @staticmethod
    def _parse_sensor_data(data: dict[Any, Any]) -> dict[str, int | float]:
        """Parse sensor data dict."""
        result = {
            item["value_type"].lower(): round(float(item["value"]), 1) for item in data
        }

        for key, value in result.items():
            if "pressure" in key and value is not None:
                result[key] = round(value / 100)
            if (
                key
                in (
                    "conc_co2_ppm",
                    "sds_p1",
                    "sds_p2",
                    "sps30_p0",
                    "sps30_p1",
                    "sps30_p2",
                    "sps30_p4",
                    "signal",
                )
                and value is not None
            ):
                result[key] = round(value)

        for old_key, new_key in RENAME_KEY_MAP:
            if result.get(old_key) is not None:
                result[new_key] = result.pop(old_key)

        return result

    async def _async_get_data(self, url: str, use_json: bool = True) -> Any:
        """Retreive data from the device."""
        last_error = None
        for retry in range(RETRIES):
            try:
                resp = await self._session.get(url)
            except ClientConnectorError as error:
                _LOGGER.info(
                    "Invalid response from device: %s, retry: %s", self._host, retry
                )
                last_error = error
            else:
                _LOGGER.debug(
                    "Data retrieved from %s, status: %s", self._host, resp.status
                )
                if resp.status != HTTPStatus.OK.value:
                    raise ApiError(
                        f"Invalid response from device {self._host}: {resp.status}"
                    )

                return await resp.json() if use_json else await resp.text()

            wait = TIMEOUT + retry
            _LOGGER.debug("Waiting %s seconds for device %s", wait, self._host)
            await asyncio.sleep(wait)

        raise ApiError(str(last_error))

    async def async_update(self) -> NAMSensors:
        """Retreive data from the device."""
        url = self._construct_url(ATTR_DATA, host=self._host)

        data = await self._async_get_data(url)

        self._software_version = data["software_version"]

        try:
            sensors = self._parse_sensor_data(data["sensordatavalues"])
        except (TypeError, KeyError) as err:
            raise InvalidSensorData("Invalid sensor data") from err

        if ATTR_UPTIME in data:
            sensors[ATTR_UPTIME] = int(data[ATTR_UPTIME])

        return from_dict(data_class=NAMSensors, data=sensors)

    async def async_get_mac_address(self) -> str:
        """Retreive the device MAC address."""
        url = self._construct_url(ATTR_VALUES, host=self._host)
        data = await self._async_get_data(url, use_json=False)

        if not (mac := re.search(MAC_PATTERN, data)):
            raise CannotGetMac("Cannot get MAC address from device")

        return cast(str, mac[0])

    @property
    def software_version(self) -> str:
        """Return software version."""
        return self._software_version


class ApiError(Exception):
    """Raised when request ended in error."""

    def __init__(self, status: str) -> None:
        """Initialize."""
        super().__init__(status)
        self.status = status


class CannotGetMac(Exception):
    """Raised when cannot get device MAC address."""

    def __init__(self, status: str) -> None:
        """Initialize."""
        super().__init__(status)
        self.status = status


class InvalidSensorData(Exception):
    """Raised when sensor data is invalid."""

    def __init__(self, status: str) -> None:
        """Initialize."""
        super().__init__(status)
        self.status = status
