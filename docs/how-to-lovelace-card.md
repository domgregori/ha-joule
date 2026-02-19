# How To: Use the Custom Lovelace Card

**Requires:** Integration installed — see [Getting Started](getting-started.md)

---

## Overview

The **Joule Sous Vide** card gives you a single, at-a-glance panel for your Joule. From one card you can:

- See the **current water temperature** in your chosen unit
- Adjust the **target temperature** with + / − buttons
- Set the **cook time** in 5-minute increments (0 = unlimited)
- Toggle the **temperature unit** between °F and °C
- **Start or stop** a cooking session with one button

---

## Install the Card

There are two ways to get the card resource into Home Assistant. Choose the one that matches how you prefer to manage your setup.

### Option A — HACS (recommended)

The card is available in HACS as a standalone Frontend plugin from the same repository as the integration.

1. In Home Assistant, go to **HACS** → **Frontend**.
2. Click **⋮** → **Custom repositories**.
3. Add `https://github.com/acato/ha-joule`, category **Frontend**.
4. Search for **ChefSteps Joule Sous Vide** and click **Download**.
5. **Reload the browser tab.**

> ✅ HACS automatically registers the card as a Lovelace resource — no manual resource step needed.

### Option B — Bundled with the integration (manual resource)

If you installed the integration via HACS or manually, the card file is already served by Home Assistant at startup. You just need to register it as a Lovelace resource:

1. Go to **Settings** → **Dashboards**.
2. Click **⋮** (menu) → **Resources**.
3. Click **+ Add resource**.
4. Enter URL: `/joule_sous_vide/joule-card.js`
5. Set resource type to **JavaScript module**.
6. Click **Create**.
7. **Reload the browser tab.**

> ✅ The card is now available in the card picker.

---

## Add the Card to a Dashboard

1. Edit your dashboard.
2. Click **+ Add card**.
3. Search for **Joule Sous Vide** and select it, **or** choose **Manual** and paste the YAML below.

---

## Card Configuration

```yaml
type: custom:joule-sous-vide-card
title: "Joule"                          # optional — default "Joule Sous Vide"
entity_switch:       switch.joule_sous_vide
entity_current_temp: sensor.joule_current_temperature
entity_target_temp:  number.joule_target_temperature
entity_cook_time:    number.joule_cook_time
entity_unit:         select.joule_temperature_unit
```

### Configuration options

| Key | Required | Description |
|---|---|---|
| `type` | ✅ | Must be `custom:joule-sous-vide-card` |
| `entity_switch` | ✅ | Entity ID of the Sous Vide switch |
| `entity_current_temp` | ✅ | Entity ID of the Current Temperature sensor |
| `entity_target_temp` | ✅ | Entity ID of the Target Temperature number |
| `entity_cook_time` | ✅ | Entity ID of the Cook Time number |
| `entity_unit` | ✅ | Entity ID of the Temperature Unit select |
| `title` | ❌ | Card title. Default: `"Joule Sous Vide"` |

> **Finding your entity IDs:** Go to **Settings** → **Devices & Services** → **ChefSteps Joule Sous Vide**. Each entity's ID is shown on its detail page.

---

## Using the Card

| Element | What it does |
|---|---|
| Status dot (top right) | Green pulsing = cooking, grey = idle, red = unavailable |
| Large temperature display | Current water temperature in your selected unit |
| **−** / **+** next to Target temp | Decreases/increases by 1 °F or 0.5 °C per tap |
| **−** / **+** next to Cook time | Decreases/increases by 5 minutes per tap |
| **°F** / **°C** toggle | Switches the display unit (saved across restarts) |
| **Start cooking** / **Stop cooking** | Starts or stops the cook |

---

## Troubleshooting

**The card shows "Device unavailable":** The Joule is out of Bluetooth range, powered off, or another app has the connection. The card updates automatically when the device comes back online.

**The card is not found in the card picker:** If you used Option B, check the resource URL is exactly `/joule_sous_vide/joule-card.js` and that you reloaded the browser. If you used HACS Frontend, check that the download completed successfully in HACS.

**Config validation error on save:** All five entity IDs are required. Copy them from the entity detail pages as described above.

---

## What's Next

- [Automate your Joule →](how-to-automate.md)
- [Entity Reference →](reference-entities.md)
