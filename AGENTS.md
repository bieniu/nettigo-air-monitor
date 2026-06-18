<!-- CLAUDE.md is a symlink to this file — edit only AGENTS.md -->
# Instructions for AI Agents (Copilot, Claude, Codex)

## Repository context

- This repository is a Python async wrapper for local [Nettigo Air Monitor](https://nettigo.eu) (NAM) devices
- The publishable package is `nettigo_air_monitor` (PyPI name: `nettigo_air_monitor`)
- NAM devices expose a local HTTP API; this library communicates directly with the device on the local network — there is no remote cloud API
- The public API surface is the `NettigoAirMonitor` class in `nettigo_air_monitor/__init__.py` and the models in `nettigo_air_monitor/model.py`
- Device endpoints (all HTTP, host-local): `http://{host}/data.json`, `http://{host}/config`, `http://{host}/ota`, `http://{host}/reset`

## Project layout

```text
nettigo_air_monitor/
├── __init__.py        # Main client (NettigoAirMonitor)
├── const.py           # Endpoints, attribute names, key rename/ignore maps, MAC regex
├── exceptions.py      # NamError (base), ApiError, NotRespondingError, AuthFailedError,
│                      #   CannotGetMacError, InvalidSensorDataError
├── model.py           # Dataclasses: ConnectionOptions, NAMSensors
└── py.typed           # Type hint marker

tests/
├── conftest.py        # Fixtures: valid_data, snapshot, sensor_community_data
├── test_init.py       # All tests
├── fixtures/          # JSON response fixtures (valid_data.json, sensor_community_data.json,
│                      #   invalid_data.json)
└── snapshots/         # syrupy snapshot files
```

## Public API

### `NettigoAirMonitor` class

```python
# Always use the async factory — do NOT call __init__ directly
session: ClientSession
options: ConnectionOptions
nam = await NettigoAirMonitor.create(session, options)

# Properties (available after create())
nam.host             # str
nam.mac              # str  (e.g. "aa:bb:cc:dd:ee:ff")
nam.software_version # str | None
nam.latitude         # float | None  (from GPS sensor, set on first update)
nam.longitude        # float | None
nam.altitude         # float | None

# Async methods
sensors: NAMSensors = await nam.async_update()
await nam.async_restart()
await nam.async_ota_update()
mac: str = await nam.async_get_mac_address()
```

### `ConnectionOptions` dataclass (`model.py`)

```python
@dataclass
class ConnectionOptions:
    host: str
    username: str | None = None   # requires password to also be set
    password: str | None = None
    auth: aiohttp.BasicAuth | None = None  # auto-set by __post_init__
```

### `NAMSensors` frozen dataclass (`model.py`)

All fields are `float | None` except `uptime: int | None`, `pms_caqi: int | None`,
`sds011_caqi: int | None`, `sps30_caqi: int | None`, and the `*_caqi_level: str | None` fields.
Supported sensors: BH1750, BME280, BMP180, BMP280, DHT22, DS18B20, HECA, MHZ14A,
PMS (PM1/PM2.5/PM10 + CAQI), SDS011 (PM2.5/PM10 + CAQI), SHT3x, SPS30 (PM + CAQI), signal, uptime.

### Exceptions (`exceptions.py`)

| Exception | When raised |
|---|---|
| `ApiError` | Non-200 or unexpected HTTP response |
| `NotRespondingError` | Timeout or connection error (triggers retry) |
| `AuthFailedError` | HTTP 401 Unauthorized |
| `CannotGetMacError` | MAC address not found in `/config` response |
| `InvalidSensorDataError` | Malformed `sensordatavalues` payload |

`async_update()` retries up to 5 times on `NotRespondingError` (tenacity, incrementing wait starting at 5 s).

## Python and environment

- Target Python: >=3.13 (also tested on 3.14)
- Use the local venv in `./.venv`
- Activate with: `source .venv/bin/activate`
- `scripts/setup-local-env.sh` creates the venv, installs `uv`, then installs all dependency groups from `pyproject.toml`, then runs `prek install`
- Package manager: `uv` — dependencies declared in `pyproject.toml`
- Runtime deps: `aiohttp`, `aqipy-atmotech` (CAQI calculation), `dacite` (dict→dataclass), `tenacity` (retry)

## Linting, formatting, typing

- Lint: `ruff check <files> --fix`
- Format: `ruff format <files>`
- Types: `ty check <files>`
- Pre-commit hooks managed via `prek` (runs ruff, ty, codespell, etc.)
- Avoid silencing rules unless there is a strong reason

## Testing

- Run with `pytest` (async tests use `pytest-asyncio`)
- Mock HTTP via `aiointercept`; do not hit real endpoints in tests
- Test constants: `VALID_IP = "192.168.172.12"`, `CONFIG_HEADER_NETTIGO`, `CONFIG_HEADER_SENSOR_COMMUNITY`
- Snapshots use `syrupy` (`tests/snapshots/`) — update with `pytest --snapshot-update` when output structures change
- Update both snapshots and fixtures together when response shapes change

## Implementation guidelines

- Keep all I/O async; accept `aiohttp.ClientSession` from the caller
- Use `aiohttp`'s built-in `.json()` / `.text()` for response parsing and `dacite.from_dict` for mapping to dataclasses
- Build device URLs via `ENDPOINTS[key].format(host=host)`; keep all constants in `nettigo_air_monitor/const.py`
- Preserve the public API and model shapes; breaking changes require explicit discussion
- Prefer specific exception types and use lazy logging: `_LOGGER.debug("msg %s", value)`
- Avoid very long docstrings; prefer one-line docstrings and keep them to 3 lines at most
- CAQI is computed with `aqipy.caqi_eu.get_caqi(with_level=True, pm10_1h=..., pm25_1h=...)` for PMS, SDS011, and SPS30 sensors
