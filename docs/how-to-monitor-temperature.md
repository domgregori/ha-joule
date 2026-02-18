# How To: Monitor Temperature

**Time required:** 5–10 minutes
**Requires:** Integration installed and Joule connected — see [Getting Started](getting-started.md)

---

## Overview

The **Current Temperature** sensor reports the water temperature in your Joule bath, updated every 30 seconds. You can display it on a dashboard, use it to trigger alerts, and track it in the Home Assistant history.

---

## Add a Temperature Card to Your Dashboard

1. Open the dashboard where you want to add the card.
2. Click the **pencil icon** (✏️) in the top-right corner to enter edit mode.
3. Click **+ Add Card**.
4. Select **Entity** from the card types.
5. In the **Entity** field, search for and select **Current Temperature** (your Joule device).
6. Click **Save**.

> ✅ The card appears on your dashboard showing the current water temperature in °C.

**Tip:** For a larger, more visual display, try the **Gauge** card instead. Set the minimum to `0` and maximum to `100` for a full sous vide temperature range.

---

## Add the Temperature to the History Graph

Home Assistant automatically records sensor history. To view it:

1. Go to **History** in the left sidebar.
2. In the entity search field, type **Current Temperature** and select your Joule sensor.
3. Choose a time range (last hour, day, week).

> ✅ A graph of water temperature over time appears. This is useful for confirming that your bath held a steady temperature throughout a long cook.

---

## Set Up a Temperature Alert

You can get a notification when your Joule reaches the target temperature using an automation.

### Example: Notify when water is up to temperature

This example sends a notification to your phone when the water temperature reaches or exceeds 60°C.

1. Go to **Settings** → **Automations & Scenes** → **+ Create Automation**.
2. Click **Create new automation**.
3. Under **Triggers**, click **+ Add Trigger** → **Numeric state**.
   - **Entity:** Current Temperature (your Joule)
   - **Above:** `59.5`
4. Under **Actions**, click **+ Add Action** → **Send a notification**.
   - **Message:** `Joule is up to temperature! Ready to cook.`
5. Click **Save** and give the automation a name like "Joule — Temperature Ready".

> ✅ You'll receive a notification on your phone the next time the water reaches 60°C.

---

## What the Sensor Shows When Something Is Wrong

| Sensor state | What it means |
|---|---|
| A temperature reading (e.g. `58.3`) | Normal — Joule is reachable and reporting |
| **Unavailable** | Joule is off, unplugged, or out of Bluetooth range. HA will reconnect automatically. |
| **Unknown** | HA has not yet received a reading since startup. Wait 30 seconds. |

---

## What's Next

- [Start a cooking session →](how-to-start-cooking.md)
- [Automate your Joule →](how-to-automate.md)
- [Full entity reference →](reference-entities.md)
