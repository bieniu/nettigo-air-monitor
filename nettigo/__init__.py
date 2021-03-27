"""
Python wrapper for getting air quality data from Nettigo Air Monitor devices.
"""
import logging
import re
from typing import Optional, Union

from aiohttp import ClientSession

from .const import ATTR_DATA, ATTR_VALUES, ENDPOINTS, HTTP_OK, MAC_PATTERN

_LOGGER = logging.getLogger(__name__)


class Nettigo:
    """Main class to perform Nettigo requests"""

    def __init__(self, session: ClientSession, host: Optional[str] = None):
        """Initialize."""
        self._session = session
        self._host = host

    @staticmethod
    def _construct_url(arg: str, **kwargs) -> str:
        """Construct Nettigo URL."""
        return ENDPOINTS[arg].format(**kwargs)

    async def _async_get_data(self, url: str, use_json=True) -> Union[dict, str]:
        """Retreive data from the device."""
        async with self._session.get(url) as resp:
            if resp.status != HTTP_OK:
                raise ApiError(
                    f"Invalid response from device {self._host}: {resp.status}"
                )
            _LOGGER.debug("Data retrieved from %s, status: %s", self._host, resp.status)
            return await resp.json() if use_json else await resp.text()

    async def async_update(self) -> dict:
        """Retreive data from the device."""
        url = self._construct_url(ATTR_DATA, host=self._host)
        data = await self._async_get_data(url)

        return data

    async def async_get_mac_address(self) -> str:
        """Retreive the device MAC address."""
        url = self._construct_url(ATTR_VALUES, host=self._host)
        data = await self._async_get_data(url, use_json=False)
        mac = re.search(MAC_PATTERN, data)

        if not mac:
            raise CannotGetMac("Cannot get MAC address from device")

        return mac[0]


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
