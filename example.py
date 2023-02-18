"""An example of using Nettigo Air Monitor package."""

import asyncio
import logging

import async_timeout
from aiohttp import ClientConnectorError, ClientError, ClientSession

from nettigo_air_monitor import (
    ApiError,
    AuthFailed,
    ConnectionOptions,
    InvalidSensorData,
    NettigoAirMonitor,
)

logging.basicConfig(level=logging.DEBUG)


async def main():
    """Run main fynction."""
    websession = ClientSession()
    options = ConnectionOptions(host="nam", username="user", password="password")

    nam = await NettigoAirMonitor.create(websession, options)
    try:
        async with async_timeout.timeout(10):
            data = await nam.async_update()
            mac = await nam.async_get_mac_address()
    except (
        ApiError,
        AuthFailed,
        ClientConnectorError,
        ClientError,
        InvalidSensorData,
        asyncio.exceptions.TimeoutError,
    ) as error:
        print(f"Error: {error}")
    else:
        print(f"Auth enabled: {nam.auth_enabled}")
        print(f"Firmware: {nam.software_version}")
        print(f"MAC address: {mac}")
        print(f"Data: {data}")

    await websession.close()


loop = asyncio.new_event_loop()
loop.run_until_complete(main())
loop.close()
