"""Tests for nettigo package."""
import json
from datetime import date
from unittest.mock import Mock, patch

import aiohttp
import pytest
from aioresponses import aioresponses

from nettigo import ApiError, InvalidSensorData, Nettigo

VALID_IP = "192.168.172.12"
INVALID_HOST = "http://nettigo.org"

VALUES = "MAC: AA:BB:CC:DD:EE:FF<br/>"


@pytest.mark.asyncio
async def test_valid_data():
    """Test with valid data."""
    with open("tests/fixtures/valid_data.json") as file:
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

        nettigo = Nettigo(session, VALID_IP)

        result = await nettigo.async_get_mac_address()

        assert result == "AA:BB:CC:DD:EE:FF"

        result = await nettigo.async_update()

    await session.close()

    assert nettigo.software_version == "NAMF-2020-36"
    assert result.sds_p1 == 22.7
    assert result.sds_p2 == 20.0
    assert result.bme280_temperature == 10.6
    assert result.bme280_humidity == 85.3
    assert result.bme280_pressure == 989
    assert result.heca_temperature == 15.1
    assert result.heca_humidity == 59.7
    assert result.signal == -85
    assert result.test is None


@pytest.mark.asyncio
async def test_api_error():
    """Test API error."""
    session = aiohttp.ClientSession()

    with aioresponses() as session_mock:
        session_mock.get(
            "http://192.168.172.12/data.json",
            status=404,
        )

        nettigo = Nettigo(session, VALID_IP)

        try:
            await nettigo.async_update()
        except ApiError as error:
            assert (
                str(error.status) == "Invalid response from device 192.168.172.12: 404"
            )

    await session.close()

@pytest.mark.asyncio
async def test_invalid_sensor_data():
    """Test InvalidSensorData error."""
    with open("tests/fixtures/invalid_data.json") as file:
        data = json.load(file)

    session = aiohttp.ClientSession()

    with aioresponses() as session_mock:
        session_mock.get(
            "http://192.168.172.12/data.json",
            payload=data,
        )
        nettigo = Nettigo(session, VALID_IP)

        try:
            await nettigo.async_update()
        except InvalidSensorData as error:
            assert (
                str(error.status) == "Invalid sensor data"
            )

    await session.close()
