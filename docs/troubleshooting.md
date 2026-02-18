# Troubleshooting

This page covers the most common problems with the Joule Sous Vide integration and how to fix them.

---

## Quick Checklist

Before diving in, run through this list:

- [ ] The Joule is **plugged in and powered on**
- [ ] The Joule is **within ~10 metres** of your Home Assistant host
- [ ] **No other app** (e.g. ChefSteps) is connected to the Joule at the same time
- [ ] You are running **Home Assistant 2024.2 or newer**
- [ ] The `custom_components/joule_sous_vide/` folder is in the right place and HA has been restarted since you copied it

---

## Problem: "Failed to connect" during setup

**Symptom:** After entering your MAC address and clicking Submit, the setup dialog shows an error saying it could not connect.

**Try these fixes in order:**

1. **Check the Joule is powered on.**
   It should be plugged in and showing its LED. If it is off, plug it in and try again.

2. **Check Bluetooth range.**
   Move your Home Assistant host (or the Joule) to within a few metres and try again.

3. **Close the ChefSteps app.**
   The Joule can only accept one Bluetooth connection at a time. If the ChefSteps app is open and connected, it blocks HA from connecting. Force-quit the app on your phone, then try setup again.

4. **Double-check the MAC address.**
   The address must be in exactly this format: `AA:BB:CC:DD:EE:FF` — six pairs of letters and numbers, uppercase, separated by colons. A common mistake is using dashes (`AA-BB-CC-DD-EE-FF`) instead of colons.

5. **Restart Home Assistant and try again.**
   Go to **Settings** → **System** → **Restart**.

---

## Problem: Entities show "Unavailable" after a successful setup

**Symptom:** Setup completed without errors, but the temperature sensor and/or switch show "Unavailable" on the dashboard.

**Causes and fixes:**

1. **The Joule has been unplugged or turned off.**
   Plug it back in. The integration will reconnect automatically within 30 seconds and entities will return to normal.

2. **The Joule has moved out of Bluetooth range.**
   Move the Joule closer to your HA host. The integration will reconnect automatically once it is in range.

3. **Another device connected to the Joule.**
   The ChefSteps app (or another Bluetooth device) may have grabbed the connection. Close the app. The integration will reconnect on its next poll (within 30 seconds).

4. **Home Assistant host Bluetooth issue.**
   Restart the HA host. Go to **Settings** → **System** → **Restart**.

---

## Problem: The temperature sensor is not updating

**Symptom:** The sensor shows a temperature reading, but it never changes even while the Joule is heating.

**Explanation:** The sensor updates every **30 seconds**. If you are watching the dashboard, wait at least 30 seconds and refresh the page.

**If it still doesn't update after a minute:**

1. Check that the sensor is not showing **Unavailable** — if it is, see the section above.
2. Go to **Settings** → **System** → **Logs** and search for `joule_sous_vide`. Look for any `ERROR` or `WARNING` lines and see below for guidance on reading logs.

---

## Problem: The switch turns on but the Joule doesn't start heating

**Symptom:** The Sous Vide switch flips to "On" in HA, but the Joule does not actually start.

**Causes and fixes:**

1. **The BLE command failed silently.**
   Check the HA logs for errors from `joule_sous_vide`. If you see a BLE error, the command did not reach the device. Try turning the switch off and on again.

2. **The Joule is in a fault state.**
   Unplug the Joule for 10 seconds, plug it back in, and try again.

3. **Bluetooth characteristic UUIDs are not yet confirmed.**
   This integration is early-stage (v0.3). The Bluetooth protocol characteristics are based on reverse-engineering and may not be finalised. If control consistently fails, please [open an issue on GitHub](https://github.com/acato/ha-joule/issues) with your HA logs attached.

---

## Problem: HA shows the switch as "On" but the Joule is actually off

**Symptom:** The switch shows "On" in HA, but the Joule's LED shows it is not cooking.

**Explanation:** The Joule's cooking state cannot be read back from the device — Home Assistant tracks it internally based on commands it has sent. If the Joule was stopped from the ChefSteps app, from the device itself, or lost power, HA will not automatically detect this.

**Fix:** Turn the switch **Off** in HA, then **On** again if you want to resume cooking. This resynchronises the state.

---

## Problem: The integration does not appear in the "Add Integration" search

**Symptom:** You search for "Joule" in the integration picker, but nothing appears.

**Causes and fixes:**

1. **The `custom_components` folder is in the wrong location.**
   It must be inside your HA **configuration directory** (the same folder that contains `configuration.yaml`), not anywhere else. Double-check the path.

2. **Home Assistant was not restarted after copying the files.**
   Go to **Settings** → **System** → **Restart** and try again.

3. **The folder name is wrong.**
   The folder must be named exactly `joule_sous_vide` (with underscores, all lowercase). Check for typos.

---

## Reading the Logs

When something goes wrong, the logs are the best place to find out why.

1. Go to **Settings** → **System** → **Logs**.
2. Click **Load Full Logs** (bottom of the page).
3. Use your browser's **Find** function (Ctrl+F / Cmd+F) and search for `joule_sous_vide`.
4. Look for lines that contain `ERROR` or `WARNING`.

**Common log messages:**

| Log message | What it means |
|---|---|
| `BLE communication failed: Failed to connect to AA:BB:CC:DD:EE:FF` | HA could not reach the device over Bluetooth |
| `Cannot connect to Joule at AA:BB:CC:DD:EE:FF` | Seen during startup — device was not reachable when HA started. It will retry. |
| `Failed to start cooking` | The start cooking command failed to reach the device |

---

## Still Stuck?

If none of the above resolves your issue, please [open an issue on GitHub](https://github.com/acato/ha-joule/issues).

Include:

1. Your **Home Assistant version** (Settings → System → About)
2. The relevant **log lines** from `joule_sous_vide` (copy and paste the full lines)
3. **What you tried** from this guide
4. **What happened** (exact error message or unexpected behaviour)

This helps the maintainers reproduce and fix the problem faster.
