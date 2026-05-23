<!-- CLAUDE.md is a symlink to this file — edit only AGENTS.md -->
# Instructions for AI Agents (Copilot, Claude, Codex)

## Repository context

- This repository is a Python async wrapper for the GIOŚ (Główny Inspektorat Ochrony Środowiska) air quality API
- The publishable package is `gios` (PyPI name: `gios`)
- The public API surface is the `Gios` class in `gios/__init__.py` and the models in `gios/model.py`
- API base URL: `https://api.gios.gov.pl/pjp-api/v1/rest`
- API Swagger UI: `https://api.gios.gov.pl/pjp-api/swagger-ui/index.html`

## Project layout

```text
gios/
├── __init__.py        # Main client (Gios)
├── const.py           # Endpoints, attribute names, pollutant/state maps
├── exceptions.py      # GiosError (base), ApiError, InvalidSensorsDataError, NoStationError
├── model.py           # Dataclasses: GiosSensors, GiosStation, Sensor
└── py.typed           # Type hint marker

tests/
├── conftest.py        # Fixtures (session, session_mock, stations, station, sensors, indexes)
├── test_init.py       # All tests
├── fixtures/          # JSON response fixtures
└── snapshots/         # syrupy snapshot files
```

## Python and environment

- Target Python: >=3.13 (also tested on 3.14)
- Use the local venv in ./venv
- Activate with: source venv/bin/activate
- `scripts/setup-local-env.sh` creates the venv, installs `uv`, then installs all dependencies from `pyproject.toml`
- The setup script also runs `prek install`
- Package manager: `uv` — dependencies declared in `pyproject.toml`

## Linting, formatting, typing

- Lint: `ruff check <files> --fix`
- Format: `ruff format <files>`
- Types: `ty check <files>`
- Pre-commit hooks managed via `prek` (runs ruff, ty, codespell, etc.)
- Avoid silencing rules unless there is a strong reason

## Testing

- Run with `pytest` (async tests use `pytest-asyncio`)
- Mock HTTP via `aioresponses`; do not hit real endpoints in tests
- Snapshots use `syrupy` (`tests/snapshots/`) — update with `pytest --snapshot-update` when output structures change
- Update both snapshots and fixtures together when response shapes change

## Implementation guidelines

- Keep all I/O async; accept `aiohttp.ClientSession` from the caller
- Use `aiohttp`'s built-in `.json()` for response parsing and `dacite.from_dict` for mapping to dataclasses
- Use `yarl.URL` for all endpoint construction; keep all URLs/constants in `gios/const.py`
- Preserve the public API and model shapes; breaking changes require explicit discussion
- Prefer specific exception types (`ApiError`, `InvalidSensorsDataError`, `NoStationError`) and use lazy logging (`_LOGGER.debug("msg %s", value)`)
- Avoid very long docstrings; prefer one-line docstrings and keep them to 3 lines at most
