# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Home Assistant custom integration for the ChefSteps Joule Sous Vide, communicating over BLE (Bluetooth Low Energy). The integration lives under `custom_components/joule_sous_vide/`.

**Target environment:** Home Assistant Core 2024.2+, Python 3.12+

## Commands

```bash
# Run tests
pytest tests/ -v --cov=custom_components.joule_sous_vide

# Run a single test file
pytest tests/test_sensor.py -v

# Run a single test
pytest tests/test_sensor.py::test_sensors_created -v

# Type checking
mypy custom_components/joule_sous_vide

# Linting
ruff check custom_components/joule_sous_vide
```

Frontend (if a Lovelace card is added under `src/`):
```bash
npm run build    # Production build
npm run watch    # Dev build with watch
npm test -- --coverage
```

## Multi-Agent Role System

This project uses specialized agent roles defined in `.claude/`:

- **As ARCHITECT** → `.claude/architect.md` — system design, component architecture
- **As BACKEND DEVELOPER** → `.claude/developer.md` — Python/HA patterns
- **As FRONTEND DEVELOPER** → `.claude/developer.md` — TypeScript/Lit/Lovelace cards
- **As SDET** → `.claude/sdet.md` — pytest/Jest test patterns and fixtures
- **As FUZZER** → `.claude/fuzzer.md` — security testing and edge cases

When a role isn't specified, infer it from the task type.

## Architecture

### Integration Structure

The integration follows the standard HA custom component layout:

```
custom_components/joule_sous_vide/
├── __init__.py       # async_setup_entry / async_unload_entry
├── manifest.json     # domain, version, requirements
├── joule_ble.py      # JouleBLEAPI — BLE communication via pygatt
├── sensor.py         # JouleTemperatureSensor entity
└── switch.py         # JouleSousVideSwitch entity (start/stop cooking)
```

### Key Design Patterns

**Coordinator pattern** — Data fetching should be centralized in a `coordinator.py` using `DataUpdateCoordinator`. Entities extend `CoordinatorEntity` and read from `coordinator.data` rather than managing connections directly. (The current code predates this and needs refactoring.)

**Async throughout** — All HA callbacks must be `async`. BLE calls via `pygatt` are synchronous/blocking and must be wrapped with `hass.async_add_executor_job()`.

**Config flow** — User setup goes through `config_flow.py` (not yet implemented). The `__init__.py` entry point should raise `ConfigEntryNotReady` on connection failure.

**Entity uniqueness** — Every entity needs a stable `_attr_unique_id` and `_attr_device_info`.

### Current State

The integration is at prototype stage (v0.2):
- BLE characteristic UUIDs in `joule_ble.py` are placeholders (`YOUR_*`)
- `__init__.py` imports a non-existent `your_joule_library`
- No `coordinator.py`, `config_flow.py`, or `const.py` yet
- Sensor and switch manage BLE directly (should delegate to coordinator)
- No tests exist yet

### Standard Imports

```python
from __future__ import annotations
from typing import Any
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, CoordinatorEntity

_LOGGER = logging.getLogger(__name__)
```
