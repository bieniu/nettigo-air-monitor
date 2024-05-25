"""Tests for nettigo package."""

import json
from http import HTTPStatus
from typing import Any
from unittest.mock import Mock, patch

import aiohttp
import pytest
from aiohttp import ClientResponseError
from aioresponses import aioresponses
from syrupy import SnapshotAssertion

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


@pytest.mark.asyncio()
async def test_valid_data(
    snapshot: SnapshotAssertion, valid_data: dict[str, Any]
) -> None:
    """Test with valid data."""
    session = aiohttp.ClientSession()
    options = ConnectionOptions(VALID_IP)

    with aioresponses() as session_mock:
        session_mock.get(
            "http://192.168.172.12/config.json",
            payload={"www_basicauth_enabled": False},
        )
        session_mock.get(
            "http://192.168.172.12/data.json",
            payload=valid_data,
        )
        session_mock.get(
            "http://192.168.172.12/values",
            payload=VALUES,
        )

        nam = await NettigoAirMonitor.create(session, options)
        mac = await nam.async_get_mac_address()
        sensors = await nam.async_update()

    await session.close()

    assert mac == "AA:BB:CC:DD:EE:FF"

    assert nam.software_version == "NAMF-2020-36"
    assert sensors == snapshot


@pytest.mark.asyncio()
async def test_caqi_value(snapshot: SnapshotAssertion) -> None:
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
        sensors = await nam.async_update()

    await session.close()

    assert sensors == snapshot


@pytest.mark.asyncio()
async def test_valid_data_with_auth(
    snapshot: SnapshotAssertion, valid_data: dict[str, Any]
) -> None:
    """Test with valid data with authorization."""
    session = aiohttp.ClientSession()
    options = ConnectionOptions(VALID_IP, "user", "pass")

    with aioresponses() as session_mock:
        session_mock.get(
            "http://192.168.172.12/config.json",
            payload={"www_basicauth_enabled": True},
        )
        session_mock.get(
            "http://192.168.172.12/data.json",
            payload=valid_data,
        )
        session_mock.get(
            "http://192.168.172.12/values",
            payload=VALUES,
        )

        nam = await NettigoAirMonitor.create(session, options)
        mac = await nam.async_get_mac_address()
        sensors = await nam.async_update()

    await session.close()

    assert mac == "AA:BB:CC:DD:EE:FF"

    assert nam.software_version == "NAMF-2020-36"
    assert nam.auth_enabled is True
    assert sensors == snapshot


@pytest.mark.asyncio()
async def test_auth_failed() -> None:
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


@pytest.mark.asyncio()
async def test_auth_enabled() -> None:
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


@pytest.mark.asyncio()
async def test_http_404_code() -> None:
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


@pytest.mark.asyncio()
async def test_api_error() -> None:
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


@pytest.mark.asyncio()
async def test_invalid_sensor_data() -> None:
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


@pytest.mark.asyncio()
async def test_cannot_get_mac() -> None:
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


@pytest.mark.asyncio()
async def test_init_device_not_repond() -> None:
    """Test init when device is not responding."""
    session = aiohttp.ClientSession()
    options = ConnectionOptions(VALID_IP)

    with aioresponses() as session_mock:
        session_mock.get(
            "http://192.168.172.12/config.json",
            exception=TimeoutError(Mock(), Mock()),
        )

        with pytest.raises(ApiError) as excinfo:
            await NettigoAirMonitor.create(session, options)

    assert str(excinfo.value) == "The device 192.168.172.12 is not responding"

    await session.close()


@pytest.mark.asyncio()
async def test_get_ma_device_not_repond() -> None:
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
            exception=TimeoutError(Mock(), Mock()),
        )

        with pytest.raises(ApiError) as excinfo:
            await nam.async_get_mac_address()

    await session.close()

    assert str(excinfo.value) == "The device 192.168.172.12 is not responding"


@pytest.mark.asyncio()
async def test_username_without_password() -> None:
    """Test error when username is provided without password."""
    with pytest.raises(
        ValueError, match="Supply both username and password"
    ) as excinfo:
        ConnectionOptions(VALID_IP, "user")

    assert str(excinfo.value) == "Supply both username and password"


@pytest.mark.asyncio()
@pytest.mark.parametrize(
    ("method", "endpoint"), [("async_restart", "reset"), ("async_ota_update", "ota")]
)
async def test_post_methods(method: str, endpoint: str) -> None:
    """Test post methods."""
    session = aiohttp.ClientSession()
    options = ConnectionOptions(VALID_IP)

    with aioresponses() as session_mock:
        session_mock.get(
            "http://192.168.172.12/config.json",
            payload={"www_basicauth_enabled": False},
        )

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


@pytest.mark.asyncio()
@pytest.mark.parametrize(
    ("method", "endpoint"), [("async_restart", "reset"), ("async_ota_update", "ota")]
)
async def test_post_methods_fail(method: str, endpoint: str) -> None:
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
            exception=TimeoutError(Mock(), Mock()),
        )

        method_to_call = getattr(nam, method)
        with pytest.raises(ApiError) as excinfo:
            await method_to_call()

    assert str(excinfo.value) == "The device 192.168.172.12 is not responding"

    await session.close()
