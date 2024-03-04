"""An example of using Nettigo Air Monitor package."""

import asyncio
import logging

from aiohttp import ClientConnectorError, ClientError, ClientSession

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
            mac = await nam.async_get_mac_address()
        except (
            TimeoutError,
            ApiError,
            AuthFailedError,
            ClientConnectorError,
            ClientError,
            InvalidSensorDataError,
        ) as error:
            print(f"Error: {error}")
        else:
            print(f"Auth enabled: {nam.auth_enabled}")
            print(f"Firmware: {nam.software_version}")
            print(f"MAC address: {mac}")
            print(f"Data: {data}")


loop = asyncio.new_event_loop()
loop.run_until_complete(main())
loop.close()
