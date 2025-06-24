"""Python wrapper for getting air quality data from Nettigo Air Monitor devices."""

from __future__ import annotations

import logging
import re
from http import HTTPStatus
from typing import Any

from aiohttp import (
    ClientConnectorError,
    ClientResponse,
    ClientResponseError,
    ClientSession,
)
from aqipy import caqi_eu
from dacite import from_dict
from tenacity import (
    after_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_incrementing,
)

from .const import (
    ATTR_CONFIG,
    ATTR_DATA,
    ATTR_GPS_HEIGHT,
    ATTR_GPS_LAT,
    ATTR_GPS_LON,
    ATTR_OTA,
    ATTR_RESTART,
    ATTR_UPTIME,
    DEFAULT_TIMEOUT,
    ENDPOINTS,
    IGNORE_KEYS,
    MAC_PATTERN,
    RENAME_KEY_MAP,
)
from .exceptions import (
    ApiError,
    AuthFailedError,
    CannotGetMacError,
    InvalidSensorDataError,
    NotRespondingError,
)
from .model import ConnectionOptions, NAMSensors

_LOGGER = logging.getLogger(__name__)


class NettigoAirMonitor:
    """Main class to perform Nettigo Air Monitor requests."""

    def __init__(self, session: ClientSession, options: ConnectionOptions) -> None:
        """Initialize."""
        self.host = options.host
        self._options = options
        self._session = session
        self._software_version: str | None = None
        self._update_errors: int = 0
        self._latitude: float | None = None
        self._longitude: float | None = None
        self._altitude: float | None = None
        self._mac: str

    @classmethod
    async def create(
        cls, session: ClientSession, options: ConnectionOptions
    ) -> NettigoAirMonitor:
        """Create a new device instance."""
        instance = cls(session, options)
        await instance.initialize()
        return instance

    async def initialize(self) -> None:
        """Initialize."""
        _LOGGER.debug("Initializing device %s", self.host)

        self._mac = await self.async_get_mac_address()

    @staticmethod
    def _construct_url(arg: str, **kwargs: str) -> str:
        """Construct Nettigo Air Monitor URL."""
        return ENDPOINTS[arg].format(**kwargs)

    @staticmethod
    def _parse_sensor_data(data: dict[Any, Any]) -> dict[str, int | float]:
        """Parse sensor data dict."""
        result = {
            item["value_type"].lower(): float(item["value"])
            for item in data
            if item["value_type"] not in IGNORE_KEYS
        }

        for key, value in result.items():
            if "pressure" in key and value is not None:
                result[key] = value / 100

        if result.get("ambient_light") == -1:
            result.pop("ambient_light")

        for old_key, new_key in RENAME_KEY_MAP:
            if result.get(old_key) is not None:
                result[new_key] = result.pop(old_key)

        return result

    async def _async_http_request(self, method: str, url: str) -> ClientResponse:
        """Retrieve data from the device."""
        try:
            _LOGGER.debug("Requesting %s, method: %s", url, method)
            resp = await self._session.request(
                method,
                url,
                raise_for_status=True,
                auth=self._options.auth,
                timeout=DEFAULT_TIMEOUT,
            )
        except ClientResponseError as error:
            if error.status == HTTPStatus.UNAUTHORIZED.value:
                raise AuthFailedError("Authorization has failed") from error
            raise ApiError(
                f"Invalid response from device {self.host}: {error.status}"
            ) from error
        except (TimeoutError, ClientConnectorError) as error:
            _LOGGER.info("Invalid response from device: %s", self.host)
            raise NotRespondingError(
                f"The device {self.host} is not responding"
            ) from error

        _LOGGER.debug("Data retrieved from %s, status: %s", self.host, resp.status)

        if resp.status != HTTPStatus.OK.value:
            raise ApiError(f"Invalid response from device {self.host}: {resp.status}")

        return resp

    @retry(
        retry=retry_if_exception_type(NotRespondingError),
        stop=stop_after_attempt(5),
        wait=wait_incrementing(start=5, increment=5),
        after=after_log(_LOGGER, logging.DEBUG),
    )
    async def async_update(self) -> NAMSensors:
        """Retrieve data from the device."""
        url = self._construct_url(ATTR_DATA, host=self.host)

        resp = await self._async_http_request("get", url)

        data = await resp.json()

        self._software_version = data["software_version"]

        try:
            sensors = self._parse_sensor_data(data["sensordatavalues"])
        except (TypeError, KeyError) as error:
            raise InvalidSensorDataError("Invalid sensor data") from error

        if ATTR_GPS_LAT in sensors and self._latitude is None:
            self._latitude = sensors.pop(ATTR_GPS_LAT)

        if ATTR_GPS_LON in sensors and self._longitude is None:
            self._longitude = sensors.pop(ATTR_GPS_LON)

        if ATTR_GPS_HEIGHT in sensors and self._altitude is None:
            self._altitude = sensors.pop(ATTR_GPS_HEIGHT)

        if ATTR_UPTIME in data:
            sensors[ATTR_UPTIME] = int(data[ATTR_UPTIME])

        for sensor in ("pms", "sds011", "sps30"):
            value, data = caqi_eu.get_caqi(
                pm10_1h=sensors.get(f"{sensor}_p1"),
                pm25_1h=sensors.get(f"{sensor}_p2"),
                with_level=True,
            )
            if value is not None and value > -1:
                sensors[f"{sensor}_caqi"] = value
                sensors[f"{sensor}_caqi_level"] = data["level"].replace(" ", "_")

        result: NAMSensors = from_dict(data_class=NAMSensors, data=sensors)

        return result

    async def async_get_mac_address(self) -> str:
        """Retrieve the device MAC address."""
        url = self._construct_url(ATTR_CONFIG, host=self.host)

        try:
            resp = await self._async_http_request("get", url)
        except NotRespondingError as error:
            raise ApiError(error.status) from error

        data = await resp.text()

        if not (match := re.search(MAC_PATTERN, data)):
            raise CannotGetMacError("Cannot get MAC address from device")

        mac = match.group(0).replace("(", "").replace(")", "").replace(":", "").lower()
        return ":".join(mac[i : i + 2] for i in range(0, 12, 2))

    @property
    def software_version(self) -> str | None:
        """Return software version."""
        return self._software_version

    @property
    def mac(self) -> str:
        """Return device MAC address."""
        return self._mac

    async def async_restart(self) -> None:
        """Restart the device."""
        url = self._construct_url(ATTR_RESTART, host=self.host)

        try:
            await self._async_http_request("post", url)
        except NotRespondingError as error:
            raise ApiError(error.status) from error

    async def async_ota_update(self) -> None:
        """Trigger OTA update."""
        url = self._construct_url(ATTR_OTA, host=self.host)

        try:
            await self._async_http_request("post", url)
        except NotRespondingError as error:
            raise ApiError(error.status) from error

    @property
    def latitude(self) -> float | None:
        """Return latitude."""
        return self._latitude

    @property
    def longitude(self) -> float | None:
        """Return longitude."""
        return self._longitude

    @property
    def altitude(self) -> float | None:
        """Return altitude."""
        return self._altitude
