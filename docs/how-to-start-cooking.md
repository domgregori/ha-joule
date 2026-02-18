# How To: Start a Cooking Session

**Time required:** ~1 minute
**Requires:** Integration installed and Joule connected — see [Getting Started](getting-started.md)

---

## Overview

Turning on the **Sous Vide** switch tells your Joule to start heating the water and circulating. In the current version of this integration (v0.3), the Joule always starts at a default of **60°C** with **no time limit**.

> ℹ️ **Want a different temperature?** Temperature control through the HA UI is coming in a future version. For now, the best approach is to set the temperature via the ChefSteps app first, then use HA to start and stop the session. You can also set a custom temperature through an HA automation — see [How To: Automate Your Joule](how-to-automate.md).

---

## Starting a Cook

### From the Dashboard

1. Open your Home Assistant dashboard.
2. Find the **Sous Vide** switch for your Joule.
   - If you haven't added it to a dashboard card yet, go to **Settings** → **Devices & Services** → your Joule device → click the **Sous Vide** entity.
3. Toggle the switch to **On**.

> ✅ The switch turns on and the Joule begins heating. The **Current Temperature** sensor will start updating every 30 seconds.

---

### From the Entity Detail View

1. Go to **Settings** → **Devices & Services**.
2. Find **ChefSteps Joule Sous Vide** and click on it.
3. Click on **Sous Vide** (the switch entity).
4. Click **Turn On**.

> ✅ The state changes to **On** and cooking begins.

---

## Stopping a Cook

1. Find the **Sous Vide** switch (same as above).
2. Toggle the switch to **Off**, or click **Turn Off**.

> ✅ The Joule stops the cooking cycle. The water stops being heated and circulated.

---

## Checking the Current Temperature

While cooking, the **Current Temperature** sensor shows the live water temperature:

- The value updates every **30 seconds**.
- If the sensor shows **Unavailable**, the Joule is out of Bluetooth range or has lost power — see [Troubleshooting](troubleshooting.md).

---

## Current Limitations

| Limitation | Workaround |
|---|---|
| Temperature is fixed at **60°C** when started from HA | Set temperature via the ChefSteps app before starting |
| Cook time defaults to **unlimited** (0 minutes) | Use an HA automation to turn the switch off after a set duration |
| If you stop/start the Joule from the ChefSteps app, HA won't know | Always use HA to control the Joule when HA is managing the session |

---

## What's Next

- [Monitor temperature and set alerts →](how-to-monitor-temperature.md)
- [Automate your Joule →](how-to-automate.md)
