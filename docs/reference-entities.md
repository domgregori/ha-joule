# Entity Reference

This page describes every entity the Joule Sous Vide integration creates in Home Assistant, what each one shows, and how to use it.

---

## Device

All entities belong to a single device:

| Field | Value |
|---|---|
| **Name** | Joule Sous Vide |
| **Manufacturer** | ChefSteps |
| **Model** | Joule |
| **Identified by** | Bluetooth MAC address entered during setup |

---

## Current Temperature

**Entity ID:** `sensor.joule_[mac]_current_temperature`
**Type:** Sensor

Shows the current water temperature inside your Joule bath, in degrees Celsius.

### Properties

| Property | Value |
|---|---|
| Unit | °C |
| Update interval | Every 30 seconds |
| Device class | Temperature |
| State class | Measurement |

### States

| State | Meaning |
|---|---|
| A number (e.g. `58.3`) | Current water temperature in °C |
| **Unavailable** | HA cannot reach the Joule. Reconnects automatically once in range and powered on. |
| **Unknown** | No reading received yet since HA started. Wait up to 30 seconds. |

---

## Sous Vide

**Entity ID:** `switch.joule_[mac]_sous_vide`
**Type:** Switch

Starts and stops the Joule cooking cycle.

### States

| State | Meaning |
|---|---|
| **On** | The Joule is actively heating and circulating water |
| **Off** | The Joule is idle |
| **Unavailable** | HA cannot reach the Joule over Bluetooth |

### State Attributes

| Attribute | Unit | Description |
|---|---|---|
| `target_temperature` | °C | The temperature sent to the device when cooking last started |
| `cook_time_minutes` | min | The cook duration sent to the device when cooking last started |

### Behaviour

- **Turning on:** reads the current **Target Temperature** and **Cook Time** values and sends them to the device, then starts the cooking cycle.
- **Turning off:** sends a stop command to the device immediately.
- **State tracking:** tracked by HA internally, not read back from the device. If you stop the Joule from the ChefSteps app, HA will not detect this automatically.

### Services

| Service | What it does |
|---|---|
| `switch.turn_on` | Starts the cooking cycle |
| `switch.turn_off` | Stops the cooking cycle |
| `switch.toggle` | Starts if off; stops if on |

```yaml
service: switch.turn_on
target:
  entity_id: switch.joule_d4_9a_20_01_f3_8b_sous_vide
```

---

## Target Temperature

**Entity ID:** `number.joule_[mac]_target_temperature`
**Type:** Number

Sets the water temperature the Joule will heat to when the Sous Vide switch is turned on.

### Properties

| Property | Value |
|---|---|
| Default | 140 °F (60 °C) |
| Range (°F) | 32 – 212 °F |
| Range (°C) | 0 – 100 °C |
| Step (°F) | 1 °F |
| Step (°C) | 0.5 °C |
| Display unit | Controlled by the **Temperature Unit** select entity |

### Behaviour

- The value is stored in Home Assistant. **Changing it does not affect a cook already in progress** — the new value takes effect the next time the switch is turned on.
- The device always receives the temperature in °C regardless of the display unit.

### Services

```yaml
service: number.set_value
target:
  entity_id: number.joule_d4_9a_20_01_f3_8b_target_temperature
data:
  value: 140
```

---

## Cook Time

**Entity ID:** `number.joule_[mac]_cook_time_minutes`
**Type:** Number

Sets how long the Joule will cook when the Sous Vide switch is turned on.

### Properties

| Property | Value |
|---|---|
| Unit | minutes |
| Default | 0 (no time limit) |
| Range | 0 – 1440 minutes (24 hours) |
| Step | 1 minute |

### Behaviour

- **0** means no time limit — the Joule will run until you turn it off manually.
- Changing this value does not affect a cook already in progress.

### Services

```yaml
service: number.set_value
target:
  entity_id: number.joule_d4_9a_20_01_f3_8b_cook_time_minutes
data:
  value: 120
```

---

## Temperature Unit

**Entity ID:** `select.joule_[mac]_temperature_unit`
**Type:** Select

Controls whether the **Target Temperature** entity displays and accepts values in °F or °C.

### Properties

| Property | Value |
|---|---|
| Options | °F, °C |
| Default | °F |
| Persisted | Yes — survives Home Assistant restarts |

### Behaviour

- Changing this entity updates the display unit and the min/max range of the Target Temperature entity immediately.
- The stored temperature value in °C is not changed when you switch units — only the display converts.
- The Joule device always receives °C over Bluetooth regardless of this setting.

### Services

```yaml
service: select.select_option
target:
  entity_id: select.joule_d4_9a_20_01_f3_8b_temperature_unit
data:
  option: "°C"
```

---

## Customising Entity Names

You can rename any entity to something easier to say or remember:

1. Go to **Settings** → **Devices & Services** → your Joule device.
2. Click the entity you want to rename.
3. Click the **pencil icon** next to the entity name.
4. Type a new name and click **Update**.

> ✅ The new name will be used across dashboards, automations, and voice assistants.

---

## Related Guides

- [Getting Started →](getting-started.md)
- [How To: Start a Cooking Session →](how-to-start-cooking.md)
- [How To: Monitor Temperature →](how-to-monitor-temperature.md)
- [How To: Automate Your Joule →](how-to-automate.md)
- [Troubleshooting →](troubleshooting.md)
