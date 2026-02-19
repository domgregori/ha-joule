# How To: Start a Cooking Session

**Time required:** ~2 minutes
**Requires:** Integration installed and Joule connected — see [Getting Started](getting-started.md)

---

## Overview

Starting a cook in Home Assistant takes three steps:

1. Choose your display unit (°F or °C)
2. Set your target temperature and cook time
3. Turn on the Sous Vide switch

The Joule reads the current Target Temperature and Cook Time values at the moment the switch is turned on, then begins heating.

---

## Step 1 — Choose Your Temperature Unit

By default the **Target Temperature** entity displays in **°F**. If you prefer °C:

1. Go to **Settings** → **Devices & Services** → **ChefSteps Joule Sous Vide**.
2. Click on the **Temperature Unit** entity.
3. Select **°C**.

> ✅ Your preference is saved and will persist across Home Assistant restarts.

---

## Step 2 — Set Your Target Temperature

1. On the same device page, click on the **Target Temperature** entity.
2. Enter your desired temperature and press **Set**.
   - Default: **140 °F** (60 °C)
   - Range: 32–212 °F (0–100 °C)

You can also set it from the dashboard by adding a **Number** card for the Target Temperature entity, or from an automation before starting a cook.

---

## Step 3 — Set Your Cook Time (optional)

1. Click on the **Cook Time** entity.
2. Enter the number of minutes you want to cook for and press **Set**.
   - **0** means no time limit — the Joule will run until you turn it off.
   - Range: 0–1440 minutes (24 hours)

---

## Step 4 — Start Cooking

### From the Dashboard

1. Find the **Sous Vide** switch for your Joule.
2. Toggle it to **On**.

> ✅ The Joule begins heating to your target temperature. The **Current Temperature** sensor updates every 30 seconds.

### From the Entity Detail View

1. Go to **Settings** → **Devices & Services** → **ChefSteps Joule Sous Vide**.
2. Click on **Sous Vide**.
3. Click **Turn On**.

---

## Stopping a Cook

1. Find the **Sous Vide** switch.
2. Toggle it to **Off**, or click **Turn Off**.

> ✅ The Joule stops heating and circulating immediately.

---

## Checking the Current Temperature

While cooking, the **Current Temperature** sensor shows the live water temperature:

- Updates every **30 seconds**.
- If it shows **Unavailable**, the Joule is out of Bluetooth range or has lost power — see [Troubleshooting](troubleshooting.md).

---

## Notes

| Behaviour | Detail |
|---|---|
| Target temperature and cook time are read at start | Changing them while cooking has no effect on the current cook |
| Cook time of 0 | The Joule runs until you turn the switch off |
| Stopping from the ChefSteps app | HA won't detect this automatically — turn the switch off in HA to resynchronise |

---

## What's Next

- [Monitor temperature and set alerts →](how-to-monitor-temperature.md)
- [Automate your Joule →](how-to-automate.md)
