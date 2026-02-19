# Architecture: ChefSteps Joule Sous Vide — Home Assistant Integration

## Overview

This integration connects Home Assistant to a **ChefSteps Joule Sous Vide** device over **Bluetooth Low Energy (BLE)**. It exposes five HA entities across four platforms:

| Platform | Entity | Purpose |
|---|---|---|
| `sensor` | Current Temperature | Live water temperature read from device (°C) |
| `switch` | Sous Vide | Starts / stops the cooking cycle |
| `number` | Target Temperature | Sets the temperature to heat to (displayed in °F or °C) |
| `number` | Cook Time | Sets the cook duration in minutes (0 = unlimited) |
| `select` | Temperature Unit | Chooses the display unit for Target Temperature (°F default) |

All communication with the physical device goes exclusively through `JouleBLEAPI`, which wraps the `pygatt` GATT library. Protobuf encoding/decoding is handled by `joule_proto.py`. Entities never access BLE directly — they call coordinator methods and read from `coordinator.data`.

---

## Component Diagram

```mermaid
graph TD
    HA[Home Assistant Core] -->|async_setup| INIT[__init__.py]
    HA -->|async_setup_entry| INIT

    INIT -->|registers static path| HTTP[hass.http\n/joule_sous_vide/joule-card.js]
    INIT -->|creates + first refresh| COORD[coordinator.py\nJouleCoordinator]
    INIT -->|forward_entry_setups| NUMBER[number.py]
    INIT -->|forward_entry_setups| SELECT[select.py]
    INIT -->|forward_entry_setups| SENSOR[sensor.py]
    INIT -->|forward_entry_setups| SWITCH[switch.py]

    COORD -->|build_* / parse_*| PROTO[joule_proto.py\nProtobuf encode/decode]
    COORD -->|async_add_executor_job| BLE[joule_ble.py\nJouleBLEAPI]
    BLE -->|pygatt GATTToolBackend| JOULE[(Joule Device\nBLE / GATT)]

    NUMBER -->|CoordinatorEntity reads coordinator.data| COORD
    NUMBER -->|async_set_target_temperature °C| COORD
    NUMBER -->|async_set_cook_time| COORD

    SELECT -->|CoordinatorEntity reads coordinator.data| COORD
    SELECT -->|async_set_temperature_unit| COORD

    SENSOR -->|CoordinatorEntity reads coordinator.data| COORD

    SWITCH -->|CoordinatorEntity reads coordinator.data| COORD
    SWITCH -->|async_start_cooking / async_stop_cooking| COORD

    CFG[config_flow.py] -->|validates MAC via BLE| BLE
    CFG -->|creates ConfigEntry| INIT

    CONST[const.py] -.->|DOMAIN, UUIDs, defaults, bounds| COORD
    CONST -.-> BLE
    CONST -.-> NUMBER
    CONST -.-> CFG

    CARD[www/joule-card.js\ncustom:joule-sous-vide-card] -->|callService| HA
    HTTP -.->|serves| CARD
```

---

## Temperature Unit Architecture

The integration maintains a strict separation between **display units** and **internal units**:

```
User sets Target Temperature (e.g. 167 °F)
        │
        ▼
JouleTargetTemperatureNumber.async_set_native_value(167)
        │  converts °F → °C: (167 - 32) × 5/9 = 75.0
        ▼
coordinator._target_temperature = 75.0  (always °C)
        │
        ├──► coordinator.data["target_temperature"] = 75.0
        │           read back by number entity → displayed as 167 °F
        │
        └──► async_start_cooking(75.0, ...)
                → build_start_cook_message(75.0, seconds)
                → api.write_message(protobuf bytes)
                  BLE device always receives °C
```

The `JouleTemperatureUnitSelect` entity only changes `coordinator._temperature_unit`; it never touches `_target_temperature`. All conversions are localised to `number.py`.

---

## Data Flow: Start a Cooking Session

```mermaid
sequenceDiagram
    participant User
    participant NUM as JouleTargetTemperatureNumber
    participant SEL as JouleTemperatureUnitSelect
    participant COORD as JouleCoordinator
    participant PROTO as joule_proto
    participant BLE as JouleBLEAPI
    participant DEV as Joule BLE Device

    User->>SEL: select_option("°F")
    SEL->>COORD: async_set_temperature_unit("°F")
    COORD-->>COORD: _temperature_unit = "°F"

    User->>NUM: set_value(167.0)
    NUM->>NUM: convert 167°F → 75.0°C
    NUM->>COORD: async_set_target_temperature(75.0)
    COORD-->>COORD: _target_temperature = 75.0

    User->>COORD: (switch turn_on)
    COORD->>BLE: ensure_connected()
    COORD->>PROTO: build_start_cook_message(75.0, 5400)
    PROTO-->>COORD: protobuf bytes
    COORD->>BLE: write_message(protobuf bytes)
    BLE->>DEV: char_write(WRITE_CHAR_UUID, bytes)
    COORD-->>COORD: _is_cooking = True
    COORD->>COORD: async_refresh() → entities update
```

## Data Flow: Periodic Temperature Poll

```mermaid
sequenceDiagram
    participant HA as Home Assistant (scheduler)
    participant COORD as JouleCoordinator
    participant PROTO as joule_proto
    participant BLE as JouleBLEAPI
    participant DEV as Joule BLE Device
    participant SENSOR as JouleTemperatureSensor

    HA->>COORD: _async_update_data() [every 30 s]
    COORD->>BLE: ensure_connected()
    COORD->>BLE: subscribe(_on_notification) [first poll only]
    COORD->>PROTO: build_live_feed_message()
    PROTO-->>COORD: protobuf bytes
    COORD->>BLE: write_message(protobuf bytes)
    BLE->>DEV: char_write(WRITE_CHAR_UUID, bytes)
    DEV-->>BLE: notification on SUBSCRIBE_CHAR_UUID
    BLE-->>COORD: _on_notification(handle, value)
    COORD->>PROTO: parse_notification(value)
    PROTO-->>COORD: CirculatorDataPoint(bath_temp, program_step, ...)
    COORD-->>COORD: returns coordinator.data dict
    COORD-->>SENSOR: _handle_coordinator_update()
    SENSOR-->>HA: state = current_temperature (°C)
```

---

## File-by-File Function Reference

### `__init__.py` — Integration Entry Point

| Function | Signature | What it does |
|---|---|---|
| `async_setup` | `(hass, config) → bool` | Registers `www/joule-card.js` as a static HTTP resource at `/joule_sous_vide/joule-card.js` via `hass.http.async_register_static_paths`. No-ops (returns `True`) if `hass.http` is `None` (e.g. in tests). |
| `async_setup_entry` | `(hass, entry) → bool` | Creates a `JouleCoordinator`, calls `async_config_entry_first_refresh()` (raises `ConfigEntryNotReady` on failure), stores the coordinator in `hass.data[DOMAIN][entry.entry_id]`, then forwards setup to all four platforms. |
| `async_unload_entry` | `(hass, entry) → bool` | Unloads all platforms, removes the coordinator from `hass.data`, and calls `coordinator.api.disconnect()`. |

---

### `coordinator.py` — `JouleCoordinator`

Single owner of the BLE connection. Entities read from `coordinator.data` and call coordinator methods for all control operations.

**Internal state:**

| Attribute | Type | Default | Description |
|---|---|---|---|
| `_is_cooking` | `bool` | `False` | Whether a cook is in progress (updated from device `program_step` during polling) |
| `_target_temperature` | `float` | `60.0` | Target temperature in **°C** |
| `_cook_time_minutes` | `float` | `0.0` | Cook duration (0 = unlimited) |
| `_temperature_unit` | `str` | `"°F"` | Display unit preference — loaded from `entry.options["temperature_unit"]` on startup, persisted there on change |
| `_latest_data_point` | `CirculatorDataPoint \| None` | `None` | Last parsed notification from device |
| `_notification_received` | `asyncio.Event` | — | Signalled when a CirculatorDataPoint notification arrives |
| `_subscribed` | `bool` | `False` | Whether we have subscribed to BLE notifications |

**`coordinator.data` keys** (refreshed every 30 s):

| Key | Type | Description |
|---|---|---|
| `current_temperature` | `float` | Latest temperature read from device (°C) |
| `is_cooking` | `bool` | Mirrors `_is_cooking` |
| `target_temperature` | `float` | Mirrors `_target_temperature` (°C) |
| `cook_time_minutes` | `float` | Mirrors `_cook_time_minutes` |
| `temperature_unit` | `str` | Mirrors `_temperature_unit` |

**Methods:**

| Method | What it does |
|---|---|
| `_on_notification(handle, value)` | Synchronous callback from pygatt's notification thread. Parses the notification via `parse_notification()`, stores the `CirculatorDataPoint`, and signals `_notification_received` via `call_soon_threadsafe`. |
| `_async_update_data()` | Subscribes to notifications (first poll only), sends a `BeginLiveFeedRequest` via `write_message()`, waits for a `CirculatorDataPoint` notification (with timeout), reads `bath_temp` and `program_step`. Raises `UpdateFailed` on `JouleBLEError`. |
| `async_start_cooking(target_temperature, cook_time_minutes)` | Stores parameters, sends a protobuf `StartProgramRequest` via `api.write_message()`, sets `_is_cooking = True`, calls `async_refresh()`. |
| `async_stop_cooking()` | Sends a protobuf `StopCirculatorRequest` via `api.write_message()`, sets `_is_cooking = False`, calls `async_refresh()`. |
| `async_set_target_temperature(value_celsius)` | Updates `_target_temperature` (°C) and refreshes. No BLE call. |
| `async_set_cook_time(value)` | Updates `_cook_time_minutes` and refreshes. No BLE call. |
| `async_set_temperature_unit(unit)` | Updates `_temperature_unit`, persists the value to `ConfigEntry.options` via `async_update_entry`, and refreshes. No BLE call, no conversion of the stored °C temperature. |

> `async_refresh()` is used (not `async_request_refresh()`) because control actions require immediate state reflection. `async_request_refresh` is debounced and would delay the state update.

---

### `joule_proto.py` — Protobuf Encoding/Decoding

Hand-rolled protobuf encoder/decoder. No external dependencies — uses only `struct` and `dataclasses`. Field numbers and types are reverse-engineered from [chromeJoule's base.proto](https://github.com/li-dennis/chromeJoule/blob/master/dist/protobuf-files/base.proto).

**Enums:**

| Enum | Values |
|---|---|
| `ProgramType` | `MANUAL` (0), `AUTOMATIC` (1) |
| `ProgramStep` | `UNKNOWN` (0), `PRE_HEAT` (1), `WAIT_FOR_FOOD` (2), `COOK` (3), `WAIT_FOR_REMOVE_FOOD` (4), `ERROR` (5) |
| `ErrorState` | `NO_ERROR` (0), `SOFT_ERROR` (1), `HARD_ERROR` (2) |

**Dataclasses (message types):**

| Class | Key Fields | StreamMessage oneof field # |
|---|---|---|
| `CirculatorProgram` | `set_point` (float °C), `cook_time` (uint32 seconds), `program_type` | — (embedded in StartProgramRequest) |
| `StartProgramRequest` | `circulator_program` (embedded) | 50 |
| `StopCirculatorRequest` | (empty) | 60 |
| `BeginLiveFeedRequest` | `feed_id` (uint32) | 70 |
| `CirculatorDataPoint` | `bath_temp` (float °C), `program_step`, `time_remaining` (seconds) | 90 |
| `StreamMessage` | `handle`, `sender_address`, `recipient_address` + oneof content | — (root envelope) |

**High-level API** (used by coordinator):

| Function | What it does |
|---|---|
| `build_start_cook_message(set_point_celsius, cook_time_seconds)` | Returns serialized `StreamMessage` with `StartProgramRequest`. |
| `build_stop_cook_message()` | Returns serialized `StreamMessage` with `StopCirculatorRequest`. |
| `build_live_feed_message(feed_id=1)` | Returns serialized `StreamMessage` with `BeginLiveFeedRequest`. |
| `parse_notification(data)` | Parses bytes as `StreamMessage`; returns `CirculatorDataPoint` if present, else `None`. Never raises. |

---

### `joule_ble.py` — `JouleBLEAPI`

All methods are **synchronous** and must be called via `hass.async_add_executor_job`.

| Method | What it does |
|---|---|
| `__init__(mac_address)` | Stores MAC address, creates a `pygatt.GATTToolBackend`, sets `self.device = None`. |
| `ensure_connected()` | No-op if already connected. Otherwise starts the adapter and connects to the device. Raises `JouleBLEError` on failure. |
| `disconnect()` | Disconnects the device and stops the adapter. |
| `write_message(payload)` | Writes a protobuf-encoded byte payload to `WRITE_CHAR_UUID`. |
| `read_message()` | Reads a protobuf-encoded response from `READ_CHAR_UUID`. |
| `subscribe(callback)` | Subscribes to notifications on `SUBSCRIBE_CHAR_UUID`. Callback receives `(handle, value)`. |

**BLE GATT UUIDs** (reverse-engineered from the Joule Android app via [chromeJoule](https://github.com/li-dennis/chromeJoule)):

| Constant | UUID | Purpose |
|---|---|---|
| `JOULE_SERVICE_UUID` | `700b4321-...-31a9098d1473` | Primary GATT service |
| `WRITE_CHAR_UUID` | `700b4322-...-31a9098d1473` | Write: send protobuf commands |
| `READ_CHAR_UUID` | `700b4323-...-31a9098d1473` | Read: receive protobuf responses |
| `SUBSCRIBE_CHAR_UUID` | `700b4325-...-31a9098d1473` | Notify: async protobuf notifications |
| `FILE_CHAR_UUID` | `700b4326-...-31a9098d1473` | File transfer (firmware updates) |

---

### `sensor.py` — `JouleTemperatureSensor`

| Method / Property | What it does |
|---|---|
| `async_setup_entry(hass, entry, async_add_entities)` | Retrieves the coordinator from `hass.data`, instantiates `JouleTemperatureSensor`, registers it. |
| `__init__(coordinator, entry)` | Sets `unique_id = f"{entry.entry_id}_current_temperature"`, configures device info. |
| `native_value` *(property)* | Returns `coordinator.data["current_temperature"]` (°C). `None` if data is unavailable. |

Static attributes: `device_class=TEMPERATURE`, `state_class=MEASUREMENT`, `unit=°C`.

---

### `switch.py` — `JouleSousVideSwitch`

| Method / Property | What it does |
|---|---|
| `async_setup_entry(hass, entry, async_add_entities)` | Retrieves coordinator, instantiates and registers `JouleSousVideSwitch`. |
| `__init__(coordinator, entry)` | Sets `unique_id = f"{entry.entry_id}_switch"`, configures device info. |
| `is_on` *(property)* | Returns `coordinator.data["is_cooking"]`. |
| `extra_state_attributes` *(property)* | Exposes `target_temperature` (°C) and `cook_time_minutes` from `coordinator.data`. |
| `async_turn_on(**kwargs)` | Reads `target_temperature` and `cook_time_minutes` from `coordinator.data`, calls `coordinator.async_start_cooking(temp_c, time)`. |
| `async_turn_off(**kwargs)` | Calls `coordinator.async_stop_cooking()`. |

---

### `number.py` — `JouleTargetTemperatureNumber` and `JouleCookTimeNumber`

#### `JouleTargetTemperatureNumber`

| Method / Property | What it does |
|---|---|
| `__init__(coordinator, entry)` | Sets `unique_id = f"{entry.entry_id}_target_temperature"`. |
| `_current_unit()` | Returns `coordinator.data["temperature_unit"]` (°F by default). |
| `native_unit_of_measurement` *(property)* | Returns the current display unit (°F or °C). |
| `native_min_value` *(property)* | Returns 32.0 (°F) or 0.0 (°C) depending on current unit. |
| `native_max_value` *(property)* | Returns 212.0 (°F) or 100.0 (°C) depending on current unit. |
| `native_step` *(property)* | Returns 1.0 (°F) or 0.5 (°C). |
| `native_value` *(property)* | Reads `coordinator.data["target_temperature"]` (°C) and converts to the display unit for presentation. |
| `async_set_native_value(value)` | Converts the input from the display unit to °C, calls `coordinator.async_set_target_temperature(value_celsius)`. |

#### `JouleCookTimeNumber`

Static attributes: `unit="min"`, `min=0`, `max=1440`, `step=1`. No unit conversion needed.

| Method / Property | What it does |
|---|---|
| `native_value` *(property)* | Returns `coordinator.data["cook_time_minutes"]`. |
| `async_set_native_value(value)` | Calls `coordinator.async_set_cook_time(value)` directly. |

---

### `select.py` — `JouleTemperatureUnitSelect`

| Method / Property | What it does |
|---|---|
| `__init__(coordinator, entry)` | Sets `unique_id = f"{entry.entry_id}_temperature_unit"`. Options: `["°F", "°C"]`. |
| `current_option` *(property)* | Returns `coordinator.data["temperature_unit"]`. |
| `async_select_option(option)` | Calls `coordinator.async_set_temperature_unit(option)`. |

---

### `config_flow.py` — `JouleConfigFlow`

| Method | What it does |
|---|---|
| `async_step_user(user_input)` | Shows MAC address input form. On submit, attempts `ensure_connected()` + `disconnect()` to validate the address. Calls `async_set_unique_id(mac)` and aborts if already configured. Creates the config entry on success. |

---

## Repository Structure

```
.github/
├── workflows/
│   ├── ci.yml          # Runs tests on push/PR to main
│   └── release.yml     # Packages and publishes a release on v* tag push
hacs.json               # HACS custom repository manifest
custom_components/joule_sous_vide/
├── __init__.py           # async_setup (static path) + entry setup / unload; 4 platforms
├── config_flow.py        # UI configuration (MAC address input + BLE validation)
├── coordinator.py        # JouleCoordinator — single BLE connection owner
├── joule_ble.py          # JouleBLEAPI — synchronous BLE I/O (pygatt)
├── joule_proto.py        # Hand-rolled protobuf encode/decode for Joule messages
├── number.py             # Target Temperature + Cook Time number entities
├── select.py             # Temperature Unit select entity
├── sensor.py             # Current Temperature sensor entity
├── switch.py             # Sous Vide switch entity
├── const.py              # DOMAIN, UUIDs, defaults, temperature bounds
├── manifest.json         # Integration metadata
├── strings.json          # Config flow UI strings
├── translations/
│   └── en.json           # English translations
└── www/
    └── joule-card.js     # custom:joule-sous-vide-card Lovelace card
```

---

## Architectural Constraints and Known Limitations

| Constraint | Detail |
|---|---|
| **Cooking state feedback** | `is_cooking` is now updated from `CirculatorDataPoint.program_step` during polling. However, between poll intervals (30 s), state may be stale if the device is controlled from the ChefSteps app. |
| **Protobuf coverage** | Hand-rolled encoder/decoder in `joule_proto.py` covers `StartProgramRequest`, `StopCirculatorRequest`, `BeginLiveFeedRequest`, and `CirculatorDataPoint`. Other message types (IdentifyCirculator, KeepAlive, WiFi, firmware) are decoded as unknown and silently skipped. |
| **One BLE connection at a time** | `pygatt` holds a single connection per `JouleBLEAPI` instance. The ChefSteps app must be closed while this integration is active. |
| **Temperature unit is persisted** | `_temperature_unit` is written to `ConfigEntry.options` on every change and read back on startup. It survives HA restarts. |
