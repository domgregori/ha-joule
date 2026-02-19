# ChefSteps Joule Sous Vide — Home Assistant Integration

Control and monitor your **ChefSteps Joule** circulator directly from Home Assistant, without the ChefSteps app.

> **Status: Early-stage (v0.3).** The core integration works. Some Bluetooth characteristic UUIDs are still being confirmed against real hardware. See [Known Limitations](#known-limitations).

---

## What You Get

Once set up, Home Assistant creates two entities for your Joule:

| Entity | What it does |
|---|---|
| **Current Temperature** sensor | Shows the live water temperature in °C, updated every 30 seconds |
| **Sous Vide** switch | Starts and stops the cooking cycle |

Both entities appear under a single **ChefSteps Joule Sous Vide** device in Home Assistant.

---

## Requirements

- Home Assistant **2024.2** or newer
- Your HA host within **~10 metres** of the Joule (Bluetooth range)
- The Joule **powered on** and not connected to the ChefSteps app
- The Joule's **Bluetooth MAC address** (see [Finding Your MAC Address](#finding-your-mac-address))

---

## Installation

### 1 — Copy the integration files

1. Download or clone this repository.
2. Copy the `custom_components/joule_sous_vide/` folder into the `custom_components/` folder inside your HA configuration directory (the folder that contains `configuration.yaml`).

```
config/
└── custom_components/
    └── joule_sous_vide/
        ├── __init__.py
        ├── config_flow.py
        ├── coordinator.py
        └── ...
```

3. **Restart Home Assistant.**

### 2 — Add the integration

1. Go to **Settings** → **Devices & Services**.
2. Click **+ Add Integration**.
3. Search for **Joule** and select **ChefSteps Joule Sous Vide**.

### 3 — Enter your MAC address

Enter your Joule's Bluetooth MAC address in the format `AA:BB:CC:DD:EE:FF` and click **Submit**. Home Assistant will connect to the device — this can take up to 30 seconds.

> ✅ On success, a **"Joule AA:BB:CC:DD:EE:FF"** device appears in Devices & Services with its two entities ready to use.

---

## Finding Your MAC Address

**Easiest — phone app:**
1. Install a free Bluetooth scanner (iOS/Android: "nRF Connect" or "BLE Scanner").
2. Power on your Joule and open the app.
3. Scan for devices and look for one named **"Joule"**.
4. The address shown (e.g. `D4:9A:20:01:F3:8B`) is what you need.

**Linux / Raspberry Pi host:**
```bash
bluetoothctl scan on
# Wait a few seconds, find the entry named "Joule", press Ctrl+C to stop
```

---

## Using the Integration

**Start a cooking session:** Toggle the **Sous Vide** switch on. The Joule will heat to its default target temperature (60 °C).

**Stop cooking:** Toggle the switch off. The Joule stops immediately.

**Monitor temperature:** The **Current Temperature** sensor updates every 30 seconds and works in dashboards, automations, and templates.

**Automate:** Use standard HA automations to schedule cooks, send alerts when the target temperature is reached, or control the Joule with a voice assistant.

```yaml
# Example: notify when the bath is up to temperature
trigger:
  - platform: numeric_state
    entity_id: sensor.joule_current_temperature
    above: 59.5
action:
  - service: notify.mobile_app
    data:
      message: "Water bath is ready!"
```

---

## Known Limitations

| Limitation | Details |
|---|---|
| **Bluetooth characteristic UUIDs** | The BLE protocol is based on reverse-engineering and is not fully confirmed. Control commands may not work on all firmware versions. |
| **State tracking** | The Joule's on/off state is tracked by HA, not read back from the device. If you stop the Joule from the ChefSteps app or physically unplug it, HA will not detect the change automatically. |
| **Temperature control** | Target temperature and cook time currently use fixed defaults (60 °C, unlimited). Custom values via the HA UI are planned for a future version. |
| **One connection at a time** | Bluetooth only supports one active connection. Close the ChefSteps app before using this integration. |

---

## Troubleshooting

**Entities show "Unavailable":** The Joule is out of Bluetooth range, powered off, or another app has the connection. The integration reconnects automatically once the device is available again.

**"Failed to connect" during setup:** Check the Joule is powered on, within range, and not connected to the ChefSteps app. Double-check the MAC address format (`AA:BB:CC:DD:EE:FF` with colons, uppercase).

**Integration not appearing in the search:** Make sure the folder is named exactly `joule_sous_vide`, is inside the `custom_components/` directory, and Home Assistant was restarted after copying it.

For full troubleshooting steps, see **[docs/troubleshooting.md](docs/troubleshooting.md)**.

---

## Documentation

- [Getting Started](docs/getting-started.md)
- [How To: Start a Cooking Session](docs/how-to-start-cooking.md)
- [How To: Monitor Temperature](docs/how-to-monitor-temperature.md)
- [How To: Automate Your Joule](docs/how-to-automate.md)
- [Entity Reference](docs/reference-entities.md)
- [Troubleshooting](docs/troubleshooting.md)

---

## Road Map

These are the next planned improvements, in priority order:

### 1 — Set a target temperature

Right now the Joule always heats to the default 60 °C. The next step is to add a `number` entity for target temperature (and optionally cook time) that the user sets from the dashboard or an automation. When the Sous Vide switch is turned on, it reads the current value of that entity and passes it to the device — no configuration flow changes required.

### 2 — Custom Lovelace card

A dedicated dashboard card that shows the current water temperature, the target temperature, a start/stop button, and a countdown timer in one place. This would replace the current approach of arranging individual entities manually on a dashboard.

### 3 — HACS integration and install workflow

Package the integration for the [Home Assistant Community Store (HACS)](https://hacs.xyz) so users can install and update it in one click without copying files manually. This involves adding a `hacs.json` manifest, a GitHub Actions release workflow that tags versions and publishes a release, and submitting the repository for HACS default inclusion.

---

## Contributing

Issues and pull requests are welcome at [github.com/acato/ha-joule](https://github.com/acato/ha-joule).

When reporting a bug, please include your Home Assistant version and the relevant log lines from `joule_sous_vide` (Settings → System → Logs).
