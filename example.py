import asyncio
import logging

import async_timeout
from aiohttp import ClientError, ClientSession

from nettigo import ApiError, InvalidSensorData, Nettigo

HOST = "192.168.172.12"

logging.basicConfig(level=logging.DEBUG)


async def main():
    try:
        async with ClientSession() as websession, async_timeout.timeout(20):
            nettigo = Nettigo(websession, HOST)
            data = await nettigo.async_update()

            mac = await nettigo.async_get_mac_address()

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
