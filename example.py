"""An example of using Nettigo Air Monitor package."""

import asyncio
import logging

from aiohttp import ClientConnectorError, ClientError, ClientSession
from tenacity import RetryError

from nettigo_air_monitor import (
    ApiError,
    AuthFailedError,
    ConnectionOptions,
    InvalidSensorDataError,
    NettigoAirMonitor,
)

logging.basicConfig(level=logging.DEBUG)

HOST = "nam"
USERNAME = "user"
PASSWORD = "password"


async def main() -> None:
    """Run main function."""
    options = ConnectionOptions(host=HOST, username=USERNAME, password=PASSWORD)

    async with ClientSession() as websession:
        nam = await NettigoAirMonitor.create(websession, options)

        try:
            data = await nam.async_update()
        except (
            TimeoutError,
            ApiError,
            AuthFailedError,
            ClientConnectorError,
            ClientError,
            InvalidSensorDataError,
            RetryError,
        ) as error:
            print(f"Error: {error}")
        else:
            print(f"Firmware: {nam.software_version}")
            print(f"MAC address: {nam.mac}")
            print(f"Latitude: {nam.latitude}, Longitude: {nam.longitude}")
            print(f"Data: {data}")


loop = asyncio.new_event_loop()
loop.run_until_complete(main())
loop.close()
