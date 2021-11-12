"""Tests for nettigo package."""
import json
from http import HTTPStatus
from unittest.mock import Mock, patch

import aiohttp
import pytest
from aiohttp import ClientResponseError
from aioresponses import aioresponses

from nettigo_air_monitor import (
    ApiError,
    AuthFailed,
    CannotGetMac,
    ConnectionOptions,
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
            "http://192.168.172.12/config.json",
            payload={},
        )
        session_mock.get(
            "http://192.168.172.12/data.json",
            payload=data,
        )
        session_mock.get(
            "http://192.168.172.12/values",
            payload=VALUES,
        )

        options = ConnectionOptions(VALID_IP)
        nam = await NettigoAirMonitor.create(session, options)

        result = await nam.async_get_mac_address()

        assert result == "AA:BB:CC:DD:EE:FF"

        result = await nam.async_update()

    await session.close()

    assert nam.software_version == "NAMF-2020-36"
    assert result.bme280_humidity == 85.3
    assert result.bme280_pressure == 989
    assert result.bme280_temperature == 10.6
    assert result.bmp180_pressure == 997
    assert result.bmp180_temperature == 10.8
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
async def test_valid_data_with_auth():
    """Test with valid data with authorization."""
    with open("tests/fixtures/valid_data.json", encoding="utf-8") as file:
        data = json.load(file)

    session = aiohttp.ClientSession()

    with aioresponses() as session_mock:
        session_mock.get(
            "http://192.168.172.12/config.json",
            payload={},
        )
        session_mock.get(
            "http://192.168.172.12/data.json",
            payload=data,
        )
        session_mock.get(
            "http://192.168.172.12/values",
            payload=VALUES,
        )

        options = ConnectionOptions(VALID_IP, "user", "pass")
        nam = await NettigoAirMonitor.create(session, options)

        result = await nam.async_get_mac_address()

        assert result == "AA:BB:CC:DD:EE:FF"

        result = await nam.async_update()

    await session.close()

    assert nam.software_version == "NAMF-2020-36"
    assert result.bme280_humidity == 85.3
    assert result.bme280_pressure == 989
    assert result.bme280_temperature == 10.6
    assert result.bmp180_pressure == 997
    assert result.bmp180_temperature == 10.8
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
async def test_auth_failed():
    """Test auth failed."""
    session = aiohttp.ClientSession()

    with aioresponses() as session_mock:
        session_mock.get(
            "http://192.168.172.12/config.json",
            exception=ClientResponseError(
                Mock(), Mock(), code=HTTPStatus.UNAUTHORIZED.value
            ),
        )

        options = ConnectionOptions(VALID_IP, "user", "pass")
        try:
            await NettigoAirMonitor.create(session, options)
        except AuthFailed as error:
            assert str(error) == "Authorization has failed"

    await session.close()


@pytest.mark.asyncio
async def test_api_error():
    """Test API error."""
    session = aiohttp.ClientSession()

    with aioresponses() as session_mock:
        session_mock.get(
            "http://192.168.172.12/config.json",
            payload={},
        )
        session_mock.get(
            "http://192.168.172.12/data.json",
            status=HTTPStatus.ACCEPTED.value,
        )

        options = ConnectionOptions(VALID_IP)
        nam = await NettigoAirMonitor.create(session, options)

        try:
            await nam.async_update()
        except ApiError as error:
            assert (
                str(error.status) == "Invalid response from device 192.168.172.12: 202"
            )

    await session.close()


# @pytest.mark.asyncio
# async def test_retry():
#     """Test retry request."""
#     session = aiohttp.ClientSession()

#     with aioresponses() as session_mock:
#         session_mock.get(
#             "http://192.168.172.12/config.json",
#             payload={},
#         )
#         session_mock.get(
#             "http://192.168.172.12/data.json",
#             exception=ClientConnectorError(Mock(), Mock()),
#         )
#         session_mock.get(
#             "http://192.168.172.12/data.json",
#             exception=ClientConnectorError(Mock(), Mock()),
#         )
#         session_mock.get(
#             "http://192.168.172.12/data.json",
#             exception=ClientConnectorError(Mock(), Mock()),
#         )
#         session_mock.get(
#             "http://192.168.172.12/data.json",
#             exception=ClientConnectorError(Mock(), Mock()),
#         )

#         options = ConnectionOptions(VALID_IP)
#         nam = await NettigoAirMonitor.create(session, options)

#         try:
#             await nam.async_update()
#         except ApiError as error:
#             assert "Cannot connect to host" in str(error)

#     await session.close()


@pytest.mark.asyncio
async def test_invalid_sensor_data():
    """Test InvalidSensorData error."""
    with open("tests/fixtures/invalid_data.json", encoding="utf-8") as file:
        data = json.load(file)

    session = aiohttp.ClientSession()

    with aioresponses() as session_mock:
        session_mock.get(
            "http://192.168.172.12/config.json",
            payload={},
        )
        session_mock.get(
            "http://192.168.172.12/data.json",
            payload=data,
        )
        options = ConnectionOptions(VALID_IP)
        nam = await NettigoAirMonitor.create(session, options)

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
            "http://192.168.172.12/config.json",
            payload={},
        )
        session_mock.get(
            "http://192.168.172.12/values",
            payload="lorem ipsum",
        )
        options = ConnectionOptions(VALID_IP)
        nam = await NettigoAirMonitor.create(session, options)

        try:
            await nam.async_get_mac_address()
        except CannotGetMac as error:
            assert str(error.status) == "Cannot get MAC address from device"

    await session.close()


@pytest.mark.asyncio
async def test_username_without_password():
    """Test error when username is provided without password."""
    try:
        ConnectionOptions(VALID_IP, "user")
    except ValueError as error:
        assert str(error) == "Supply both username and password"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "method,endpoint", [("async_restart", "reset"), ("async_ota_update", "ota")]
)
async def test_post_methods(method, endpoint):
    """Test post methods."""
    session = aiohttp.ClientSession()

    with aioresponses() as session_mock:
        session_mock.get(
            "http://192.168.172.12/config.json",
            payload={},
        )
        session_mock.post(f"http://192.168.172.12/{endpoint}")

        options = ConnectionOptions(VALID_IP)
        nam = await NettigoAirMonitor.create(session, options)

        method_to_call = getattr(nam, method)

        with patch(
            "nettigo_air_monitor.NettigoAirMonitor._async_http_request"
        ) as mock_request:
            await method_to_call()

        assert mock_request.call_count == 1
        assert mock_request.call_args[0][0] == "post"
        assert mock_request.call_args[0][1] == f"http://192.168.172.12/{endpoint}"

    await session.close()
