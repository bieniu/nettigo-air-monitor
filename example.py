import asyncio
import logging

import async_timeout
from aiohttp import ClientConnectorError, ClientError, ClientSession

from nettigo_air_monitor import (
    ApiError,
    AuthRequired,
    ConnectionOptions,
    InvalidSensorData,
    create_device,
)

logging.basicConfig(level=logging.DEBUG)


async def main():
    websession = ClientSession()
    options = ConnectionOptions(host="nam")
    try:
        nam = await create_device(websession, options)
        await asyncio.sleep(1)
        async with async_timeout.timeout(30):
            data = await nam.async_update()
            mac = await nam.async_get_mac_address()
    except (
        ApiError,
        AuthRequired,
        ClientError,
        InvalidSensorData,
        asyncio.exceptions.TimeoutError,
    ) as error:
        print(f"Error: {error}")
    else:
        print(f"Firmware: {nam.software_version}")
        print(f"MAC address: {mac}")
        print(f"Data: {data}")

    # try:
    #     await nam.restart()
    # except (ApiError, AuthRequired, ClientConnectorError) as error:
    #     print(f"Error: {error}")

    await websession.close()


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.close()
