"""Tests for nettigo package."""
import asyncio
import json
from http import HTTPStatus
from unittest.mock import Mock, patch

import aiohttp
import pytest
from aiohttp import ClientResponseError
from aioresponses import aioresponses

from nettigo_air_monitor import (
    ApiError,
    AuthFailedError,
    CannotGetMacError,
    ConnectionOptions,
    InvalidSensorDataError,
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
    options = ConnectionOptions(VALID_IP)

    with aioresponses() as session_mock:
        session_mock.get(
            "http://192.168.172.12/config.json",
            payload={"www_basicauth_enabled": False},
        )
        session_mock.get(
            "http://192.168.172.12/data.json",
            payload=data,
        )
        session_mock.get(
            "http://192.168.172.12/values",
            payload=VALUES,
        )

        nam = await NettigoAirMonitor.create(session, options)
        mac = await nam.async_get_mac_address()
        result = await nam.async_update()

    await session.close()

    assert mac == "AA:BB:CC:DD:EE:FF"

    assert nam.software_version == "NAMF-2020-36"
    assert result.bme280_humidity == 85.3
    assert result.bme280_pressure == 989.206
    assert result.bme280_temperature == 10.6
    assert result.bmp180_pressure == 996.784
    assert result.bmp180_temperature == 10.8
    assert result.bmp280_pressure == 1022.012
    assert result.bmp280_temperature == 5.6
    assert result.dht22_humidity == 46.2
    assert result.dht22_temperature == 6.3
    assert result.heca_humidity == 59.7
    assert result.heca_temperature == 15.1
    assert result.mhz14a_carbon_dioxide == 865
    assert result.pms_p0 == 6
    assert result.pms_p1 == 10
    assert result.pms_p2 == 11
    assert result.pms_caqi == 19
    assert result.pms_caqi_level == "very_low"
    assert result.sds011_p1 == 22.7
    assert result.sds011_p2 == 20
    assert result.sds011_caqi == 34
    assert result.sds011_caqi_level == "low"
    assert result.sht3x_humidity == 34.7
    assert result.sht3x_temperature == 6.3
    assert result.signal == -85
    assert result.sps30_p0 == 31.2
    assert result.sps30_p1 == 21.2
    assert result.sps30_p2 == 34.3
    assert result.sps30_p4 == 24.7
    assert result.sps30_caqi == 54
    assert result.sps30_caqi_level == "medium"
    assert result.uptime == 45632


@pytest.mark.asyncio
async def test_caqi_value():
    """Test CAQI value when PM10 and PM2.5 is None."""
    data = {"software_version": "NAMF-2020-36", "sensordatavalues": []}

    session = aiohttp.ClientSession()
    options = ConnectionOptions(VALID_IP)

    with aioresponses() as session_mock:
        session_mock.get(
            "http://192.168.172.12/config.json",
            payload={"www_basicauth_enabled": False},
        )
        session_mock.get(
            "http://192.168.172.12/data.json",
            payload=data,
        )
        session_mock.get(
            "http://192.168.172.12/values",
            payload=VALUES,
        )

        nam = await NettigoAirMonitor.create(session, options)
        result = await nam.async_update()

    await session.close()

    assert result.sds011_p1 is None
    assert result.sds011_p2 is None
    assert result.sds011_caqi is None
    assert result.sds011_caqi_level is None
    assert result.sps30_p1 is None
    assert result.sps30_p2 is None
    assert result.sps30_caqi is None
    assert result.sps30_caqi_level is None


@pytest.mark.asyncio
async def test_valid_data_with_auth():
    """Test with valid data with authorization."""
    with open("tests/fixtures/valid_data.json", encoding="utf-8") as file:
        data = json.load(file)

    session = aiohttp.ClientSession()
    options = ConnectionOptions(VALID_IP, "user", "pass")

    with aioresponses() as session_mock:
        session_mock.get(
            "http://192.168.172.12/config.json",
            payload={"www_basicauth_enabled": True},
        )
        session_mock.get(
            "http://192.168.172.12/data.json",
            payload=data,
        )
        session_mock.get(
            "http://192.168.172.12/values",
            payload=VALUES,
        )

        nam = await NettigoAirMonitor.create(session, options)
        mac = await nam.async_get_mac_address()
        result = await nam.async_update()

    await session.close()

    assert mac == "AA:BB:CC:DD:EE:FF"

    assert nam.software_version == "NAMF-2020-36"
    assert nam.auth_enabled is True
    assert result.bme280_humidity == 85.3
    assert result.bme280_pressure == 989.206
    assert result.bme280_temperature == 10.6
    assert result.bmp180_pressure == 996.784
    assert result.bmp180_temperature == 10.8
    assert result.bmp280_pressure == 1022.012
    assert result.bmp280_temperature == 5.6
    assert result.dht22_humidity == 46.2
    assert result.dht22_temperature == 6.3
    assert result.heca_humidity == 59.7
    assert result.heca_temperature == 15.1
    assert result.mhz14a_carbon_dioxide == 865
    assert result.sds011_p1 == 22.7
    assert result.sds011_p2 == 20
    assert result.sht3x_humidity == 34.7
    assert result.sht3x_temperature == 6.3
    assert result.signal == -85
    assert result.sps30_p0 == 31.2
    assert result.sps30_p1 == 21.2
    assert result.sps30_p2 == 34.3
    assert result.sps30_p4 == 24.7
    assert result.uptime == 45632


@pytest.mark.asyncio
async def test_auth_failed():
    """Test auth failed."""
    session = aiohttp.ClientSession()
    options = ConnectionOptions(VALID_IP, "user", "pass")

    with aioresponses() as session_mock:
        session_mock.get(
            "http://192.168.172.12/config.json",
            payload={"www_basicauth_enabled": False},
        )

        nam = await NettigoAirMonitor.create(session, options)

    with aioresponses() as session_mock:
        session_mock.post(
            "http://192.168.172.12/reset",
            exception=ClientResponseError(
                Mock(), Mock(), status=HTTPStatus.UNAUTHORIZED.value
            ),
        )

        with pytest.raises(AuthFailedError) as excinfo:
            await nam.async_restart()

    assert str(excinfo.value) == "Authorization has failed"

    await session.close()


@pytest.mark.asyncio
async def test_auth_enabled():
    """Test auth failed."""
    session = aiohttp.ClientSession()
    options = ConnectionOptions(VALID_IP, "user", "pass")

    with aioresponses() as session_mock:
        session_mock.get(
            "http://192.168.172.12/config.json",
            exception=ClientResponseError(
                Mock(), Mock(), status=HTTPStatus.UNAUTHORIZED.value
            ),
        )

        nam = await NettigoAirMonitor.create(session, options)

    await session.close()

    assert nam.auth_enabled is True


@pytest.mark.asyncio
async def test_http_404_code():
    """Test request ends with error."""
    session = aiohttp.ClientSession()
    options = ConnectionOptions(VALID_IP, "user", "pass")

    with aioresponses() as session_mock:
        session_mock.get(
            "http://192.168.172.12/config.json",
            exception=ClientResponseError(
                Mock(), Mock(), status=HTTPStatus.NOT_FOUND.value
            ),
        )
        with pytest.raises(ApiError) as excinfo:
            await NettigoAirMonitor.create(session, options)

    assert str(excinfo.value) == "Invalid response from device 192.168.172.12: 404"

    await session.close()


@pytest.mark.asyncio
async def test_api_error():
    """Test API error."""
    session = aiohttp.ClientSession()
    options = ConnectionOptions(VALID_IP)

    with aioresponses() as session_mock:
        session_mock.get(
            "http://192.168.172.12/config.json",
            payload={"www_basicauth_enabled": False},
        )

        nam = await NettigoAirMonitor.create(session, options)

    with aioresponses() as session_mock:
        session_mock.get(
            "http://192.168.172.12/data.json",
            status=HTTPStatus.ACCEPTED.value,
        )
        with pytest.raises(ApiError) as excinfo:
            await nam.async_update()

    assert str(excinfo.value) == "Invalid response from device 192.168.172.12: 202"

    await session.close()


@pytest.mark.asyncio
async def test_cache_empty():
    """Test error request when cache is empty."""
    session = aiohttp.ClientSession()
    options = ConnectionOptions(VALID_IP)

    with aioresponses() as session_mock:
        session_mock.get(
            "http://192.168.172.12/config.json",
            payload={"www_basicauth_enabled": False},
        )

        nam = await NettigoAirMonitor.create(session, options)

    with aioresponses() as session_mock:
        session_mock.get(
            "http://192.168.172.12/data.json",
            exception=asyncio.TimeoutError(Mock(), Mock()),
        )

        with pytest.raises(ApiError) as excinfo:
            await nam.async_update()

    assert str(excinfo.value) == "The device 192.168.172.12 is not responding"

    await session.close()


@pytest.mark.asyncio
async def test_data_cached():
    """Test error request when the data is cached."""
    with open("tests/fixtures/valid_data.json", encoding="utf-8") as file:
        data = json.load(file)

    session = aiohttp.ClientSession()
    options = ConnectionOptions(VALID_IP)

    with aioresponses() as session_mock:
        session_mock.get(
            "http://192.168.172.12/config.json",
            payload={"www_basicauth_enabled": False},
        )
        session_mock.get(
            "http://192.168.172.12/data.json",
            payload=data,
        )
        session_mock.get(
            "http://192.168.172.12/data.json",
            exception=asyncio.TimeoutError(Mock(), Mock()),
        )

        nam = await NettigoAirMonitor.create(session, options)
        await nam.async_update()
        result = await nam.async_update()

    await session.close()

    assert nam.software_version == "NAMF-2020-36"
    assert result.bme280_humidity == 85.3
    assert result.bme280_pressure == 989.206
    assert result.bme280_temperature == 10.6
    assert result.bmp180_pressure == 996.784
    assert result.bmp180_temperature == 10.8
    assert result.bmp280_pressure == 1022.012
    assert result.bmp280_temperature == 5.6
    assert result.dht22_humidity == 46.2
    assert result.dht22_temperature == 6.3
    assert result.heca_humidity == 59.7
    assert result.heca_temperature == 15.1
    assert result.mhz14a_carbon_dioxide == 865
    assert result.sds011_p1 == 22.7
    assert result.sds011_p2 == 20
    assert result.sht3x_humidity == 34.7
    assert result.sht3x_temperature == 6.3
    assert result.signal == -85
    assert result.sps30_p0 == 31.2
    assert result.sps30_p1 == 21.2
    assert result.sps30_p2 == 34.3
    assert result.sps30_p4 == 24.7
    assert result.uptime == 45632


@pytest.mark.asyncio
async def test_invalid_sensor_data():
    """Test InvalidSensorDataError."""
    with open("tests/fixtures/invalid_data.json", encoding="utf-8") as file:
        data = json.load(file)

    session = aiohttp.ClientSession()
    options = ConnectionOptions(VALID_IP)

    with aioresponses() as session_mock:
        session_mock.get(
            "http://192.168.172.12/config.json",
            payload={"www_basicauth_enabled": False},
        )

        nam = await NettigoAirMonitor.create(session, options)

    with aioresponses() as session_mock:
        session_mock.get(
            "http://192.168.172.12/data.json",
            payload=data,
        )

        with pytest.raises(InvalidSensorDataError) as excinfo:
            await nam.async_update()

    assert str(excinfo.value) == "Invalid sensor data"

    await session.close()


@pytest.mark.asyncio
async def test_cannot_get_mac():
    """Test CannotGetMacError error."""
    session = aiohttp.ClientSession()
    options = ConnectionOptions(VALID_IP)

    with aioresponses() as session_mock:
        session_mock.get(
            "http://192.168.172.12/config.json",
            payload={"www_basicauth_enabled": False},
        )

        nam = await NettigoAirMonitor.create(session, options)

    with aioresponses() as session_mock:
        session_mock.get(
            "http://192.168.172.12/values",
            payload="lorem ipsum",
        )

        with pytest.raises(CannotGetMacError) as excinfo:
            await nam.async_get_mac_address()

    assert str(excinfo.value) == "Cannot get MAC address from device"

    await session.close()


@pytest.mark.asyncio
async def test_init_device_not_repond():
    """Test init when device is not responding."""
    session = aiohttp.ClientSession()
    options = ConnectionOptions(VALID_IP)

    with aioresponses() as session_mock:
        session_mock.get(
            "http://192.168.172.12/config.json",
            exception=asyncio.TimeoutError(Mock(), Mock()),
        )

        with pytest.raises(ApiError) as excinfo:
            await NettigoAirMonitor.create(session, options)

    assert str(excinfo.value) == "The device 192.168.172.12 is not responding"

    await session.close()


@pytest.mark.asyncio
async def test_get_ma_device_not_repond():
    """Test get_mac when device is not responding."""
    session = aiohttp.ClientSession()
    options = ConnectionOptions(VALID_IP)

    with aioresponses() as session_mock:
        session_mock.get(
            "http://192.168.172.12/config.json",
            payload={"www_basicauth_enabled": False},
        )

        nam = await NettigoAirMonitor.create(session, options)

    with aioresponses() as session_mock:
        session_mock.get(
            "http://192.168.172.12/values",
            exception=asyncio.TimeoutError(Mock(), Mock()),
        )

        with pytest.raises(ApiError) as excinfo:
            await nam.async_get_mac_address()

    await session.close()

    assert str(excinfo.value) == "The device 192.168.172.12 is not responding"


@pytest.mark.asyncio
async def test_username_without_password():
    """Test error when username is provided without password."""
    with pytest.raises(
        ValueError, match="Supply both username and password"
    ) as excinfo:
        ConnectionOptions(VALID_IP, "user")

    assert str(excinfo.value) == "Supply both username and password"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("method", "endpoint"), [("async_restart", "reset"), ("async_ota_update", "ota")]
)
async def test_post_methods(method, endpoint):
    """Test post methods."""
    session = aiohttp.ClientSession()
    options = ConnectionOptions(VALID_IP)

    with aioresponses() as session_mock:
        session_mock.get(
            "http://192.168.172.12/config.json",
            payload={"www_basicauth_enabled": False},
        )

        nam = await NettigoAirMonitor.create(session, options)

    with aioresponses() as session_mock, patch(
        "nettigo_air_monitor.NettigoAirMonitor._async_http_request"
    ) as mock_request:
        session_mock.post(f"http://192.168.172.12/{endpoint}")

        method_to_call = getattr(nam, method)
        await method_to_call()

    await session.close()

    assert mock_request.call_count == 1
    assert mock_request.call_args[0][0] == "post"
    assert mock_request.call_args[0][1] == f"http://192.168.172.12/{endpoint}"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("method", "endpoint"), [("async_restart", "reset"), ("async_ota_update", "ota")]
)
async def test_post_methods_fail(method, endpoint):
    """Test fail of the post methods."""
    session = aiohttp.ClientSession()
    options = ConnectionOptions(VALID_IP, "user", "pass")

    with aioresponses() as session_mock:
        session_mock.get(
            "http://192.168.172.12/config.json",
            payload={"www_basicauth_enabled": True},
        )

        nam = await NettigoAirMonitor.create(session, options)

    with aioresponses() as session_mock:
        session_mock.post(
            f"http://192.168.172.12/{endpoint}",
            exception=asyncio.TimeoutError(Mock(), Mock()),
        )

        method_to_call = getattr(nam, method)
        with pytest.raises(ApiError) as excinfo:
            await method_to_call()

    assert str(excinfo.value) == "The device 192.168.172.12 is not responding"

    await session.close()
