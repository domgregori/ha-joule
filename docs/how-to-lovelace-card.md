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

## Add the Card to a Dashboard

### Step 1 — Register the card as a Lovelace resource

The integration registers the card file automatically at startup. To tell Lovelace about it:

1. Go to **Settings** → **Dashboards**.
2. Click **⋮** (menu) → **Resources**.
3. Click **+ Add resource**.
4. Enter URL: `/joule_sous_vide/joule-card.js`
5. Set resource type to **JavaScript module**.
6. Click **Create**.
7. **Reload the browser tab.**

> ✅ The card is now available in the card picker.

### Step 2 — Add the card to a dashboard

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

**The card is not found in the card picker:** Make sure you added the resource URL correctly (step 1) and reloaded the browser. The URL must be `/joule_sous_vide/joule-card.js` (no trailing slash).

**Config validation error on save:** All five entity IDs are required. Copy them from the entity detail pages as described above.

---

## What's Next

- [Automate your Joule →](how-to-automate.md)
- [Entity Reference →](reference-entities.md)
