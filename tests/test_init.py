"""Tests for nettigo package."""
import json
from unittest.mock import Mock

import aiohttp
import pytest
from aiohttp.client_exceptions import ClientConnectorError
from aioresponses import aioresponses

from nettigo_air_monitor import (
    ApiError,
    CannotGetMac,
    InvalidSensorData,
    NettigoAirMonitor,
)

VALID_IP = "192.168.172.12"
INVALID_HOST = "http://nam.org"

VALUES = "MAC: AA:BB:CC:DD:EE:FF<br/>"


@pytest.mark.asyncio
async def test_valid_data():
    """Test with valid data."""
    with open("tests/fixtures/valid_data.json", encoding="utf-8") as file:
        data = json.load(file)

    session = aiohttp.ClientSession()

    with aioresponses() as session_mock:
        session_mock.get(
            "http://192.168.172.12/data.json",
            payload=data,
        )
        session_mock.get(
            "http://192.168.172.12/values",
            payload=VALUES,
        )

        nam = NettigoAirMonitor(session, VALID_IP)

        result = await nam.async_get_mac_address()

        assert result == "AA:BB:CC:DD:EE:FF"

        result = await nam.async_update()

    await session.close()

    assert nam.software_version == "NAMF-2020-36"
    assert result.bme280_humidity == 85.3
    assert result.bme280_pressure == 989
    assert result.bme280_temperature == 10.6
    assert result.bmp280_pressure == 1022
    assert result.bmp280_temperature == 5.6
    assert result.dht22_humidity == 46.2
    assert result.dht22_temperature == 6.3
    assert result.heca_humidity == 59.7
    assert result.heca_temperature == 15.1
    assert result.mhz14a_carbon_dioxide == 865
    assert result.sds011_p1 == 23
    assert result.sds011_p2 == 20
    assert result.sht3x_humidity == 34.7
    assert result.sht3x_temperature == 6.3
    assert result.signal == -85
    assert result.sps30_p0 == 31
    assert result.sps30_p1 == 21
    assert result.sps30_p2 == 34
    assert result.sps30_p4 == 25
    assert result.uptime == 45632


@pytest.mark.asyncio
async def test_api_error():
    """Test API error."""
    session = aiohttp.ClientSession()

    with aioresponses() as session_mock:
        session_mock.get(
            "http://192.168.172.12/data.json",
            status=404,
        )

        nam = NettigoAirMonitor(session, VALID_IP)

        try:
            await nam.async_update()
        except ApiError as error:
            assert (
                str(error.status) == "Invalid response from device 192.168.172.12: 404"
            )

    await session.close()


@pytest.mark.asyncio
async def test_retry():
    """Test retry request."""
    session = aiohttp.ClientSession()

    with aioresponses() as session_mock:
        session_mock.get(
            "http://192.168.172.12/data.json",
            exception=ClientConnectorError(Mock(), Mock()),
        )
        session_mock.get(
            "http://192.168.172.12/data.json",
            exception=ClientConnectorError(Mock(), Mock()),
        )
        session_mock.get(
            "http://192.168.172.12/data.json",
            exception=ClientConnectorError(Mock(), Mock()),
        )
        session_mock.get(
            "http://192.168.172.12/data.json",
            exception=ClientConnectorError(Mock(), Mock()),
        )

        nam = NettigoAirMonitor(session, VALID_IP)

        try:
            await nam.async_update()
        except ApiError as error:
            assert "Cannot connect to host" in str(error)

    await session.close()


@pytest.mark.asyncio
async def test_invalid_sensor_data():
    """Test InvalidSensorData error."""
    with open("tests/fixtures/invalid_data.json", encoding="utf-8") as file:
        data = json.load(file)

    session = aiohttp.ClientSession()

    with aioresponses() as session_mock:
        session_mock.get(
            "http://192.168.172.12/data.json",
            payload=data,
        )
        nam = NettigoAirMonitor(session, VALID_IP)

        try:
            await nam.async_update()
        except InvalidSensorData as error:
            assert str(error.status) == "Invalid sensor data"

    await session.close()


@pytest.mark.asyncio
async def test_cannot_get_mac():
    """Test CannotGetMac error."""
    session = aiohttp.ClientSession()

    with aioresponses() as session_mock:
        session_mock.get(
            "http://192.168.172.12/values",
            payload="lorem ipsum",
        )
        nam = NettigoAirMonitor(session, VALID_IP)

        try:
            await nam.async_get_mac_address()
        except CannotGetMac as error:
            assert str(error.status) == "Cannot get MAC address from device"

    await session.close()
