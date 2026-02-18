# How To: Automate Your Joule

**Time required:** 5–15 minutes per automation
**Requires:** Integration installed and Joule connected — see [Getting Started](getting-started.md)

---

## Overview

Automations let you control your Joule without touching the app or dashboard. This guide covers the most useful real-world examples.

---

## Example 1 — Turn the Joule On at a Scheduled Time

Start preheating your water bath before you get home from work.

1. Go to **Settings** → **Automations & Scenes** → **+ Create Automation**.
2. Click **Create new automation**.
3. Under **Triggers**, click **+ Add Trigger** → **Time**.
   - Set the time, for example `17:00` (5:00 PM).
4. Under **Actions**, click **+ Add Action** → **Call service**.
   - **Service:** `switch.turn_on`
   - **Entity:** Sous Vide (your Joule)
5. Click **Save** and name it "Joule — Preheat at 5pm".

> ✅ Every day at 5:00 PM, the Joule will start heating the water to 60°C.

---

## Example 2 — Turn the Joule Off After a Set Duration

Since the current version does not set a cook timer automatically, you can use an automation to turn the Joule off after a number of hours.

1. Go to **Settings** → **Automations & Scenes** → **+ Create Automation**.
2. Under **Triggers**, click **+ Add Trigger** → **State**.
   - **Entity:** Sous Vide (your Joule)
   - **To:** `on`
   - **For:** `02:00:00` (2 hours — adjust to your recipe)
3. Under **Actions**, click **+ Add Action** → **Call service**.
   - **Service:** `switch.turn_off`
   - **Entity:** Sous Vide (your Joule)
4. Click **Save** and name it "Joule — Auto off after 2 hours".

> ✅ The Joule will turn off automatically 2 hours after it is switched on, regardless of how it was started.

---

## Example 3 — Notify When Water Is Up to Temperature

Get a phone notification when the bath is ready to drop your food in.

1. Go to **Settings** → **Automations & Scenes** → **+ Create Automation**.
2. Under **Triggers**, click **+ Add Trigger** → **Numeric state**.
   - **Entity:** Current Temperature (your Joule)
   - **Above:** `59.5`
3. Under **Conditions**, click **+ Add Condition** → **State**.
   - **Entity:** Sous Vide (your Joule)
   - **State:** `on`
   _(This prevents the alert from firing if the temperature happens to be warm for another reason.)_
4. Under **Actions**, click **+ Add Action** → **Send a notification**.
   - **Message:** `Your Joule water bath is ready! Drop your food in.`
5. Click **Save** and name it "Joule — Ready notification".

> ✅ You'll get a notification as soon as the water reaches 60°C while the Joule is on.

---

## Example 4 — Voice Control via a Voice Assistant

If you have Google Assistant, Amazon Alexa, or Apple Siri configured in Home Assistant, you can control the Joule by voice once the integration is set up — no extra configuration needed.

| Say this | What happens |
|---|---|
| "Turn on the sous vide" | Joule starts cooking |
| "Turn off the sous vide" | Joule stops cooking |
| "What's the sous vide temperature?" | Reads out the current water temperature |

> ℹ️ The exact wake word and phrasing depend on your voice assistant. The entity names can be customised in **Settings** → **Devices & Services** to make them easier to say.

---

## Example 5 — Dashboard Button with a Script

If you want a single dashboard button that starts a complete cook (and another to stop it), use a script.

1. Go to **Settings** → **Automations & Scenes** → **Scripts** → **+ Add Script**.
2. Give it a name: "Start Joule Cook".
3. Under **Actions**, add:
   - **Call service:** `switch.turn_on` → Sous Vide (your Joule)
4. Save the script.
5. Repeat to create a "Stop Joule Cook" script with `switch.turn_off`.
6. Add **Button** cards to your dashboard pointing to these scripts.

> ✅ You now have clean Start / Stop buttons on your dashboard.

---

## Tips for Reliable Automations

- **Always check if the Joule is available** before triggering automations that depend on it. Add a **State** condition checking that the Sous Vide switch is not `unavailable`.
- **Add a notification for failures.** If your Joule goes unavailable during a cook, you'll want to know. Create an automation that triggers when the Sous Vide entity becomes `unavailable` and sends you an alert.
- **Avoid starting the Joule from both HA and the ChefSteps app at the same time.** HA tracks cooking state internally — if you start or stop the Joule from the app, HA won't reflect that change until you interact with the switch from HA again.

---

## What's Next

- [Full entity reference →](reference-entities.md)
- [Troubleshooting →](troubleshooting.md)
