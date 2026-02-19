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
4. Under **Actions**, add two steps:
   - **First action — set temperature:**
     - **Service:** `number.set_value`
     - **Entity:** Target Temperature (your Joule)
     - **Value:** your target temperature (e.g. `140` for 140 °F)
   - **Second action — start cooking:**
     - **Service:** `switch.turn_on`
     - **Entity:** Sous Vide (your Joule)
5. Click **Save** and name it "Joule — Preheat at 5pm".

> ✅ Every day at 5:00 PM, the Joule will set the temperature and start heating.

---

## Example 2 — Set Cook Time and Auto-Stop

Use the Cook Time entity so the Joule stops automatically after your recipe time.

1. Go to **Settings** → **Automations & Scenes** → **+ Create Automation**.
2. Under **Triggers**, click **+ Add Trigger** → **Time** → set your start time.
3. Under **Actions**, add three steps:
   - **Service:** `number.set_value` → Target Temperature → your temperature
   - **Service:** `number.set_value` → Cook Time → minutes (e.g. `120` for 2 hours)
   - **Service:** `switch.turn_on` → Sous Vide
4. Click **Save**.

> ✅ The Joule will start, cook for the set time, and stop automatically.

---

## Example 3 — Notify When Water Is Up to Temperature

Get a phone notification when the bath is ready to drop your food in.

1. Go to **Settings** → **Automations & Scenes** → **+ Create Automation**.
2. Under **Triggers**, click **+ Add Trigger** → **Numeric state**.
   - **Entity:** Current Temperature (your Joule)
   - **Above:** your target temperature minus 0.5 (e.g. `139.5` for a 140 °F target)
3. Under **Conditions**, click **+ Add Condition** → **State**.
   - **Entity:** Sous Vide (your Joule)
   - **State:** `on`
4. Under **Actions**, click **+ Add Action** → **Send a notification**.
   - **Message:** `Your Joule water bath is ready! Drop your food in.`
5. Click **Save** and name it "Joule — Ready notification".

> ✅ You'll get a notification as soon as the water reaches your target temperature.

**Tip:** You can make the threshold dynamic using a template trigger instead of a fixed value:
```yaml
trigger:
  - platform: template
    value_template: >
      {{ states('sensor.joule_current_temperature') | float >=
         state_attr('switch.joule_sous_vide', 'target_temperature') | float - 0.5 }}
```

---

## Example 4 — Voice Control via a Voice Assistant

If you have Google Assistant, Amazon Alexa, or Apple Siri configured in Home Assistant, you can control the Joule by voice once the integration is set up — no extra configuration needed.

| Say this | What happens |
|---|---|
| "Turn on the sous vide" | Joule starts cooking at the current target temperature |
| "Turn off the sous vide" | Joule stops cooking |
| "What's the sous vide temperature?" | Reads out the current water temperature |
| "Set the sous vide temperature to 140" | Sets the Target Temperature entity |

> ℹ️ The exact wake word and phrasing depend on your voice assistant. Entity names can be customised in **Settings** → **Devices & Services** to make them easier to say.

---

## Example 5 — Dashboard Script Buttons

A single dashboard button that sets temperature, sets cook time, and starts cooking in one tap.

1. Go to **Settings** → **Automations & Scenes** → **Scripts** → **+ Add Script**.
2. Give it a name, e.g. "Start Chicken at 140°F / 2h".
3. Under **Actions**, add:
   - `number.set_value` → Target Temperature → `140`
   - `number.set_value` → Cook Time → `120`
   - `switch.turn_on` → Sous Vide
4. Save the script.
5. Add a **Button** card to your dashboard pointing to this script.

> ✅ One tap starts a fully configured cook. Create one script per recipe.

---

## Tips for Reliable Automations

- **Check availability before triggering.** Add a **State** condition checking that the Sous Vide switch is not `unavailable` before attempting to start a cook.
- **Alert on loss of connection.** Create an automation that triggers when the Sous Vide entity becomes `unavailable` during a cook and sends you a notification.
- **Don't mix HA and the ChefSteps app.** HA tracks cooking state internally — if you stop the Joule from the app, HA won't reflect that until you interact with the switch from HA again.

---

## What's Next

- [Full entity reference →](reference-entities.md)
- [Troubleshooting →](troubleshooting.md)
