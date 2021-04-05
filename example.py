import asyncio
import logging

from aiohttp import ClientError, ClientSession

from nettigo import ApiError, InvalidSensorData, Nettigo

HOST = "192.168.172.12"

logging.basicConfig(level=logging.DEBUG)


async def main():
    async with ClientSession() as websession:
        try:
            nettigo = Nettigo(websession, HOST)
            data = await nettigo.async_update()

            mac = await nettigo.async_get_mac_address()

        except (
            ApiError,
            ClientError,
            InvalidSensorData,
            asyncio.TimeoutError,
        ) as error:
            print(f"Error: {error}")
        else:
            print(f"MAC address: {mac}")
            print(f"Data: {data}")


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.close()
