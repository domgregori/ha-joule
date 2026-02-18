# Getting Started with Joule Sous Vide for Home Assistant

This integration connects your **ChefSteps Joule Sous Vide** circulator to Home Assistant over Bluetooth. Once set up, you can monitor the water temperature and control the cooking cycle directly from your HA dashboard, automations, and voice assistants.

---

## What You Get

After setup, Home Assistant creates two things for your Joule:

| What | What it does |
|---|---|
| **Current Temperature** sensor | Shows the live water temperature in °C, updated every 30 seconds |
| **Sous Vide** switch | Turns the cooking cycle on and off |

---

## Before You Begin

Make sure you have:

- **Home Assistant** 2024.2 or newer
- **Python** 3.12 or newer (already met if you run a standard HA installation)
- Your **Joule device** plugged in and powered on
- Your Home Assistant host within **~10 metres** of the Joule (Bluetooth range)
- The **Bluetooth MAC address** of your Joule — see [Finding Your Joule's MAC Address](#finding-your-joules-mac-address) below

> ⚠️ **One connection at a time.** Bluetooth devices can only be connected to one app at a time. If the ChefSteps app is connected to your Joule, close it before setting up this integration.

---

## Installation

This integration is installed manually by copying files into your Home Assistant configuration.

### Step 1 — Copy the integration files

1. Download or clone this repository.
2. Copy the `custom_components/joule_sous_vide/` folder into the `custom_components/` folder inside your Home Assistant configuration directory.

Your configuration directory structure should look like this:

```
config/
└── custom_components/
    └── joule_sous_vide/
        ├── __init__.py
        ├── config_flow.py
        ├── coordinator.py
        ├── ...
```

3. **Restart Home Assistant.**

> ✅ After restarting, the integration will be available to add.

---

### Step 2 — Add the Integration

1. In Home Assistant, go to **Settings** → **Devices & Services**.
2. Click **+ Add Integration** in the bottom-right corner.
3. In the search box, type **Joule** and select **ChefSteps Joule Sous Vide**.

> ✅ A setup dialog titled "Connect to Joule Sous Vide" will appear.

---

### Step 3 — Enter Your MAC Address

1. In the **MAC Address** field, enter your Joule's Bluetooth MAC address.
   - Format: `AA:BB:CC:DD:EE:FF` (six pairs of letters/numbers, separated by colons)
   - Example: `D4:9A:20:01:F3:8B`
2. Click **Submit**.

Home Assistant will now attempt to connect to your Joule over Bluetooth. This can take up to **30 seconds**.

> ✅ On success, you'll see **"Joule AA:BB:CC:DD:EE:FF"** appear in your Devices & Services list.
> ❌ If it fails, see [Troubleshooting](troubleshooting.md).

---

### Step 4 — Check Your New Entities

1. Go to **Settings** → **Devices & Services**.
2. Find **ChefSteps Joule Sous Vide** and click on it.
3. You should see two entities:

| Entity | Example name |
|---|---|
| Current Temperature (sensor) | `sensor.joule_d4_9a_20_01_f3_8b_current_temperature` |
| Sous Vide (switch) | `switch.joule_d4_9a_20_01_f3_8b_sous_vide` |

> ✅ You're ready to go! Continue to [How To: Start a Cooking Session](how-to-start-cooking.md).

---

## Finding Your Joule's MAC Address

The Joule's MAC address is a unique identifier for its Bluetooth radio. You need it to set up the integration.

### Option A — Bluetooth scanner app (easiest)

1. Install a free Bluetooth scanner on your phone:
   - **iOS:** "BLE Scanner" or "nRF Connect"
   - **Android:** "nRF Connect" or "BLE Scanner"
2. Make sure your Joule is **plugged in and powered on**.
3. Open the app and scan for devices.
4. Look for a device named **"Joule"** in the list.
5. The address shown (e.g. `D4:9A:20:01:F3:8B`) is the MAC address you need.

### Option B — Linux/Raspberry Pi host

If your Home Assistant runs on a Raspberry Pi or Linux machine with Bluetooth:

1. Open a terminal on your HA host.
2. Run: `bluetoothctl scan on`
3. Wait a few seconds. Devices in range will appear with their MAC addresses.
4. Look for the entry named **Joule**.
5. Press `Ctrl+C` to stop scanning.

---

## What's Next

- [How To: Start a Cooking Session →](how-to-start-cooking.md)
- [How To: Monitor Temperature →](how-to-monitor-temperature.md)
- [How To: Automate Your Joule →](how-to-automate.md)
- [Entity Reference →](reference-entities.md)
- [Troubleshooting →](troubleshooting.md)
