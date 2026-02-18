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

This sensor shows the current water temperature inside your Joule bath, in degrees Celsius.

### Properties

| Property | Value |
|---|---|
| Unit | °C (degrees Celsius) |
| Update interval | Every 30 seconds |
| Device class | Temperature |
| State class | Measurement |

### States

| State | Meaning |
|---|---|
| A number (e.g. `58.3`) | The current water temperature in °C |
| **Unavailable** | HA cannot reach the Joule over Bluetooth. It will reconnect automatically once the device is in range and powered on. |
| **Unknown** | No reading has been received yet since HA started. Wait up to 30 seconds. |

### Notes

- The temperature is read from the Joule device via Bluetooth. If the device is mid-heatup, the reading reflects the current bath temperature, not the target.
- You can use this sensor in the **History** panel to confirm a bath held a steady temperature over a long cook.
- The sensor is suitable for use in automations and Lovelace cards as a standard numeric state.

---

## Sous Vide

**Entity ID:** `switch.joule_[mac]_sous_vide`
**Type:** Switch

This switch starts and stops the Joule cooking cycle.

### States

| State | Meaning |
|---|---|
| **On** | The Joule is actively heating and circulating water |
| **Off** | The Joule is idle (not heating) |
| **Unavailable** | HA cannot reach the Joule over Bluetooth |

### State Attributes

These extra details are shown alongside the switch state and can be used in templates and automations:

| Attribute | Unit | Default | Description |
|---|---|---|---|
| `target_temperature` | °C | 60.0 | The temperature the Joule was last instructed to heat to |
| `cook_time_minutes` | minutes | 0.0 | The cook duration the Joule was last instructed to use. `0` means no time limit. |

**Example — reading attributes in a template:**

```yaml
{{ state_attr('switch.joule_d4_9a_20_01_f3_8b_sous_vide', 'target_temperature') }}
```

### Behaviour

- **Turning on:** HA sends the current `target_temperature` (default 60°C) and `cook_time_minutes` (default 0, meaning unlimited) to the Joule, then starts the cooking cycle.
- **Turning off:** HA sends a stop command to the Joule immediately.
- **State tracking:** The on/off state is tracked by Home Assistant, not read back from the device. If you start or stop the Joule using the ChefSteps app or the physical device, Home Assistant will not automatically detect this change.

> ⚠️ **Current limitation:** In v0.3, the target temperature and cook time can only be changed by the integration internally (they default to 60°C and unlimited). Custom temperature control through the HA UI is planned for a future version.

### Services

The switch responds to standard HA switch services:

| Service | What it does |
|---|---|
| `switch.turn_on` | Starts the cooking cycle |
| `switch.turn_off` | Stops the cooking cycle |
| `switch.toggle` | Starts cooking if off; stops if on |

**Example — calling the service from an automation action:**

```yaml
service: switch.turn_on
target:
  entity_id: switch.joule_d4_9a_20_01_f3_8b_sous_vide
```

---

## Customising Entity Names

You can rename both entities to something easier to say or remember:

1. Go to **Settings** → **Devices & Services** → your Joule device.
2. Click the entity you want to rename.
3. Click the **pencil icon** next to the entity name.
4. Type a new name (e.g. "Water Bath Temperature" or "Sous Vide Cooker").
5. Click **Update**.

> ✅ The new name will be used across dashboards, automations, and voice assistants.

---

## Related Guides

- [Getting Started →](getting-started.md)
- [How To: Start a Cooking Session →](how-to-start-cooking.md)
- [How To: Monitor Temperature →](how-to-monitor-temperature.md)
- [How To: Automate Your Joule →](how-to-automate.md)
- [Troubleshooting →](troubleshooting.md)
