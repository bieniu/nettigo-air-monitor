import asyncio
import logging

import async_timeout
from aiohttp import ClientError, ClientSession

from nettigo_air_monitor import ApiError, InvalidSensorData, NettigoAirMonitor

HOST = "nam"

logging.basicConfig(level=logging.DEBUG)


async def main():
    try:
        async with ClientSession() as websession, async_timeout.timeout(30):
            nam = NettigoAirMonitor(websession, HOST)
            data = await nam.async_update()

            mac = await nam.async_get_mac_address()

    except (
        asyncio.exceptions.TimeoutError,
        ApiError,
        ClientError,
        InvalidSensorData,
    ) as error:
        print(f"Error: {error}")
    else:
        print(f"MAC address: {mac}")
        print(f"Data: {data}")


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.close()
