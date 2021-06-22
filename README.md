[![GitHub Release][releases-shield]][releases]
[![PyPI][pypi-releases-shield]][pypi-releases]
[![PyPI - Downloads][pypi-downloads]][pypi-statistics]
[![Buy me a coffee][buy-me-a-coffee-shield]][buy-me-a-coffee]
[![PayPal_Me][paypal-me-shield]][paypal-me]

# nettigo-air-monitor

Python wrapper for getting air quality data from Nettigo Air Monitor devices.


## How to use package

```python
import asyncio
import logging

import async_timeout
from aiohttp import ClientError, ClientSession

from nettigo_air_monitor import ApiError, InvalidSensorData, NettigoAirMonitor

HOST = "192.168.172.12"

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
        print(f"Firmware: {nam.software_version}")
        print(f"MAC address: {mac}")
        print(f"Data: {data}")


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.close()
```

[releases]: https://github.com/bieniu/nettigo-air-monitor/releases
[releases-shield]: https://img.shields.io/github/release/bieniu/nettigo-air-monitor.svg?style=popout
[pypi-releases]: https://pypi.org/project/nettigo-air-monitor/
[pypi-statistics]: https://pepy.tech/project/nettigo-air-monitor
[pypi-releases-shield]: https://img.shields.io/pypi/v/nettigo-air-monitor
[pypi-downloads]: https://pepy.tech/badge/nettigo-air-monitor/month
[buy-me-a-coffee-shield]: https://img.shields.io/static/v1.svg?label=%20&message=Buy%20me%20a%20coffee&color=6f4e37&logo=buy%20me%20a%20coffee&logoColor=white
[buy-me-a-coffee]: https://www.buymeacoffee.com/QnLdxeaqO
[paypal-me-shield]: https://img.shields.io/static/v1.svg?label=%20&message=PayPal.Me&logo=paypal
[paypal-me]: https://www.paypal.me/bieniu79
