"""Tests for nettigo package."""

import json
from http import HTTPStatus
from typing import Any
from unittest.mock import Mock, patch

import pytest
from aiohttp import ClientConnectorError, ClientResponseError, ClientSession
from aioresponses import aioresponses
from syrupy import SnapshotAssertion
from tenacity import RetryError

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

CONFIG_HEADER_NETTIGO = "MAC: AA:BB:CC:DD:EE:FF<br/>"
CONFIG_HEADER_SENSOR_COMMUNITY = ">ID: 1122334 (aabbccddeeff) <br />"

DATA_JSON_URL = "http://192.168.172.12/data.json"
CONFIG_URL = "http://192.168.172.12/config"
VALUES_URL = "http://192.168.172.12/values"


@pytest.mark.asyncio
async def test_valid_data(
    snapshot: SnapshotAssertion, valid_data: dict[str, Any]
) -> None:
    """Test with valid data."""
    session = ClientSession()
    options = ConnectionOptions(VALID_IP)

    with aioresponses() as session_mock:
        session_mock.get(CONFIG_URL, payload=CONFIG_HEADER_NETTIGO)
        session_mock.get(DATA_JSON_URL, payload=valid_data)

        nam = await NettigoAirMonitor.create(session, options)
        sensors = await nam.async_update()

    await session.close()

    assert nam.mac == "aa:bb:cc:dd:ee:ff"
    assert nam.software_version == "NAMF-2020-36"
    assert nam.latitude == 52.284921
    assert nam.longitude == 20.889263
    assert nam.altitude == 102.8
    assert sensors == snapshot


@pytest.mark.asyncio
async def test_caqi_value(snapshot: SnapshotAssertion) -> None:
    """Test CAQI value when PM10 and PM2.5 is None."""
    data = {"software_version": "NAMF-2020-36", "sensordatavalues": []}

    session = ClientSession()
    options = ConnectionOptions(VALID_IP)

    with aioresponses() as session_mock:
        session_mock.get(CONFIG_URL, payload=CONFIG_HEADER_NETTIGO)
        session_mock.get(DATA_JSON_URL, payload=data)

        nam = await NettigoAirMonitor.create(session, options)
        sensors = await nam.async_update()

    await session.close()

    assert sensors == snapshot


@pytest.mark.asyncio
async def test_valid_data_with_auth(
    snapshot: SnapshotAssertion, valid_data: dict[str, Any]
) -> None:
    """Test with valid data with authorization."""
    session = ClientSession()
    options = ConnectionOptions(VALID_IP, "user", "pass")

    with aioresponses() as session_mock:
        session_mock.get(CONFIG_URL, payload=CONFIG_HEADER_NETTIGO)
        session_mock.get(DATA_JSON_URL, payload=valid_data)

        nam = await NettigoAirMonitor.create(session, options)
        sensors = await nam.async_update()

    await session.close()

    assert nam.mac == "aa:bb:cc:dd:ee:ff"
    assert nam.software_version == "NAMF-2020-36"
    assert sensors == snapshot


@pytest.mark.asyncio
async def test_auth_failed() -> None:
    """Test auth failed."""
    session = ClientSession()
    options = ConnectionOptions(VALID_IP, "user", "pass")

    with aioresponses() as session_mock:
        session_mock.get(CONFIG_URL, payload=CONFIG_HEADER_NETTIGO)

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
async def test_auth_enabled() -> None:
    """Test auth failed."""
    session = ClientSession()
    options = ConnectionOptions(VALID_IP, "user", "pass")

    with aioresponses() as session_mock:
        session_mock.get(
            CONFIG_URL,
            exception=ClientResponseError(
                Mock(), Mock(), status=HTTPStatus.UNAUTHORIZED.value
            ),
        )
        with pytest.raises(AuthFailedError) as excinfo:
            await NettigoAirMonitor.create(session, options)

    await session.close()

    assert str(excinfo.value) == "Authorization has failed"


@pytest.mark.asyncio
async def test_http_404_code() -> None:
    """Test request ends with error."""
    session = ClientSession()
    options = ConnectionOptions(VALID_IP, "user", "pass")

    with aioresponses() as session_mock:
        session_mock.get(
            CONFIG_URL,
            exception=ClientResponseError(
                Mock(), Mock(), status=HTTPStatus.NOT_FOUND.value
            ),
        )
        with pytest.raises(ApiError) as excinfo:
            await NettigoAirMonitor.create(session, options)

    assert str(excinfo.value) == "Invalid response from device 192.168.172.12: 404"

    await session.close()


@pytest.mark.asyncio
async def test_api_error() -> None:
    """Test API error."""
    session = ClientSession()
    options = ConnectionOptions(VALID_IP)

    with aioresponses() as session_mock:
        session_mock.get(CONFIG_URL, payload=CONFIG_HEADER_NETTIGO)

        nam = await NettigoAirMonitor.create(session, options)

    with aioresponses() as session_mock:
        session_mock.get(DATA_JSON_URL, status=HTTPStatus.ACCEPTED.value)
        with pytest.raises(ApiError) as excinfo:
            await nam.async_update()

    assert str(excinfo.value) == "Invalid response from device 192.168.172.12: 202"

    await session.close()


@pytest.mark.asyncio
async def test_invalid_sensor_data() -> None:
    """Test InvalidSensorDataError."""
    with open("tests/fixtures/invalid_data.json", encoding="utf-8") as file:
        data = json.load(file)

    session = ClientSession()
    options = ConnectionOptions(VALID_IP)

    with aioresponses() as session_mock:
        session_mock.get(CONFIG_URL, payload=CONFIG_HEADER_NETTIGO)

        nam = await NettigoAirMonitor.create(session, options)

    with aioresponses() as session_mock:
        session_mock.get(DATA_JSON_URL, payload=data)

        with pytest.raises(InvalidSensorDataError) as excinfo:
            await nam.async_update()

    assert str(excinfo.value) == "Invalid sensor data"

    await session.close()


@pytest.mark.asyncio
async def test_cannot_get_mac() -> None:
    """Test CannotGetMacError error."""
    session = ClientSession()
    options = ConnectionOptions(VALID_IP)

    with aioresponses() as session_mock:
        session_mock.get(CONFIG_URL, payload="lorem ipsum")

        with pytest.raises(CannotGetMacError) as excinfo:
            await NettigoAirMonitor.create(session, options)

    assert str(excinfo.value) == "Cannot get MAC address from device"

    await session.close()


@pytest.mark.asyncio
async def test_init_device_not_repond() -> None:
    """Test init when device is not responding."""
    session = ClientSession()
    options = ConnectionOptions(VALID_IP)

    with aioresponses() as session_mock:
        session_mock.get(CONFIG_URL, exception=TimeoutError(Mock(), Mock()))

        with pytest.raises(ApiError) as excinfo:
            await NettigoAirMonitor.create(session, options)

    assert str(excinfo.value) == "The device 192.168.172.12 is not responding"

    await session.close()


@pytest.mark.asyncio
async def test_get_mac_device_not_repond() -> None:
    """Test get_mac when device is not responding."""
    session = ClientSession()
    options = ConnectionOptions(VALID_IP)

    with aioresponses() as session_mock:
        session_mock.get(CONFIG_URL, exception=TimeoutError(Mock(), Mock()))

        with pytest.raises(ApiError) as excinfo:
            await NettigoAirMonitor.create(session, options)

    await session.close()

    assert str(excinfo.value) == "The device 192.168.172.12 is not responding"


@pytest.mark.asyncio
async def test_username_without_password() -> None:
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
async def test_post_methods(method: str, endpoint: str) -> None:
    """Test post methods."""
    session = ClientSession()
    options = ConnectionOptions(VALID_IP)

    with aioresponses() as session_mock:
        session_mock.get(CONFIG_URL, payload=CONFIG_HEADER_NETTIGO)

        nam = await NettigoAirMonitor.create(session, options)

    with (
        aioresponses() as session_mock,
        patch(
            "nettigo_air_monitor.NettigoAirMonitor._async_http_request"
        ) as mock_request,
    ):
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
async def test_post_methods_fail(method: str, endpoint: str) -> None:
    """Test fail of the post methods."""
    session = ClientSession()
    options = ConnectionOptions(VALID_IP, "user", "pass")

    with aioresponses() as session_mock:
        session_mock.get(CONFIG_URL, payload=CONFIG_HEADER_NETTIGO)

        nam = await NettigoAirMonitor.create(session, options)

    with aioresponses() as session_mock:
        session_mock.post(
            f"http://192.168.172.12/{endpoint}", exception=TimeoutError(Mock(), Mock())
        )

        method_to_call = getattr(nam, method)
        with pytest.raises(ApiError) as excinfo:
            await method_to_call()

    assert str(excinfo.value) == "The device 192.168.172.12 is not responding"

    await session.close()


@pytest.mark.parametrize(
    "exc", [TimeoutError(Mock(), Mock()), ClientConnectorError(Mock(), Mock())]
)
@pytest.mark.asyncio
async def test_retry_success(valid_data: dict[str, Any], exc: Exception) -> None:
    """Test retry which succeeded."""
    session = ClientSession()
    options = ConnectionOptions(VALID_IP)

    with aioresponses() as session_mock, patch("asyncio.sleep") as sleep_mock:
        session_mock.get(CONFIG_URL, payload=CONFIG_HEADER_NETTIGO)
        session_mock.get(DATA_JSON_URL, exception=exc, repeat=4)
        session_mock.get(DATA_JSON_URL, payload=valid_data)

        nam = await NettigoAirMonitor.create(session, options)
        await nam.async_update()

    assert sleep_mock.call_count == 4
    assert sleep_mock.call_args_list[0][0][0] == 5
    assert sleep_mock.call_args_list[1][0][0] == 10
    assert sleep_mock.call_args_list[2][0][0] == 15
    assert sleep_mock.call_args_list[3][0][0] == 20

    await session.close()


@pytest.mark.parametrize(
    "exc", [TimeoutError(Mock(), Mock()), ClientConnectorError(Mock(), Mock())]
)
@pytest.mark.asyncio
async def test_retry_fail(exc: Exception) -> None:
    """Test retry that failed."""
    session = ClientSession()
    options = ConnectionOptions(VALID_IP)

    with aioresponses() as session_mock, patch("asyncio.sleep") as sleep_mock:
        session_mock.get(CONFIG_URL, payload=CONFIG_HEADER_NETTIGO)
        session_mock.get(DATA_JSON_URL, exception=exc, repeat=5)

        nam = await NettigoAirMonitor.create(session, options)
        with pytest.raises(RetryError) as excinfo:
            await nam.async_update()

    await session.close()

    assert sleep_mock.call_count == 4
    assert sleep_mock.call_args_list[0][0][0] == 5
    assert sleep_mock.call_args_list[1][0][0] == 10
    assert sleep_mock.call_args_list[2][0][0] == 15
    assert sleep_mock.call_args_list[3][0][0] == 20

    assert "RetryError" in str(excinfo.value)


@pytest.mark.asyncio
async def test_illuminance_wrong_value() -> None:
    """Test with wrong value for illuminance."""
    session = ClientSession()
    options = ConnectionOptions(VALID_IP)

    data = {
        "software_version": "NAMF-2020-36",
        "age": "144",
        "measurements": "285",
        "uptime": "45632",
        "sensordatavalues": [{"value_type": "ambient_light", "value": "-1"}],
    }

    with aioresponses() as session_mock:
        session_mock.get(CONFIG_URL, payload=CONFIG_HEADER_NETTIGO)
        session_mock.get(DATA_JSON_URL, payload=data)

        nam = await NettigoAirMonitor.create(session, options)
        sensors = await nam.async_update()

    await session.close()

    assert sensors.bh1750_illuminance is None


@pytest.mark.asyncio
async def test_sensor_community_firmware(
    snapshot: SnapshotAssertion, sensor_community_data: dict[str, Any]
) -> None:
    """Test Sensor.Community firmware."""
    session = ClientSession()
    options = ConnectionOptions(VALID_IP)

    with aioresponses() as session_mock:
        session_mock.get(CONFIG_URL, payload=CONFIG_HEADER_SENSOR_COMMUNITY)
        session_mock.get(DATA_JSON_URL, payload=sensor_community_data)

        nam = await NettigoAirMonitor.create(session, options)
        sensors = await nam.async_update()

    await session.close()

    assert nam.mac == "aa:bb:cc:dd:ee:ff"
    assert nam.software_version == "NRZ-2024-135"
    assert sensors == snapshot
