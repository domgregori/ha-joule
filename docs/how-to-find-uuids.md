# Advanced: Finding the Joule's BLE GATT UUIDs

**Audience:** Advanced users comfortable with Bluetooth tools and/or Android developer options.

The integration uses five BLE GATT characteristic UUIDs to communicate with the Joule. These are currently placeholders in `const.py` pending confirmation against real hardware. This guide explains how to discover the correct values for your device.

---

## Background

The Joule communicates over **Bluetooth Low Energy (BLE)** using the **GATT** (Generic Attribute Profile) protocol. Every BLE device exposes a tree of **services**, each containing **characteristics** — the actual data endpoints you read from or write to. Each characteristic has a globally unique identifier: a **UUID** (e.g. `6e400002-b5a3-f393-e0a9-e50e24dcca9e`).

The integration needs five of these:

| Constant in `const.py` | Purpose |
|---|---|
| `JOULE_SERVICE_UUID` | Primary GATT service the Joule advertises |
| `TEMPERATURE_CHAR_UUID` | Write: target temperature setpoint (centidegrees, 2-byte LE) |
| `TIME_CHAR_UUID` | Write: cook duration (seconds, 4-byte LE) |
| `START_STOP_CHAR_UUID` | Write: `0x01` = start, `0x00` = stop |
| `CURRENT_TEMP_CHAR_UUID` | Read: current water temperature (centidegrees, 2-byte LE) |

---

## Method 1 — nRF Connect (recommended starting point)

**nRF Connect** is a free BLE inspector app by Nordic Semiconductor. It lets you browse every service and characteristic on any BLE device and manually read or write values to identify what each one does.

- **iOS:** [nRF Connect on the App Store](https://apps.apple.com/app/nrf-connect-for-mobile/id1054362403)
- **Android:** [nRF Connect on Google Play](https://play.google.com/store/apps/details?id=no.nordicsemi.android.mcp)

### Steps

1. **Power on the Joule** and make sure the **ChefSteps app is closed** (BLE allows only one connection at a time).
2. Open nRF Connect → tap **SCAN**.
3. Find the **Joule** device in the list and tap **Connect**.
4. The app shows a tree of **services** (identified by UUIDs). Expand each one to see its characteristics.
5. For each characteristic, note:
   - The **UUID**
   - The **properties**: Read, Write, Write Without Response, Notify
6. Tap the **↓ Read** button on readable characteristics to see current values.
7. Screenshot the full service tree — you will cross-reference it against the sniff log in Method 2.

> **Note on iOS:** Apple replaces BLE MAC addresses with random per-app UUIDs for privacy. This does not affect UUID discovery — all service and characteristic UUIDs are shown accurately.

### What to look for

- A characteristic with **Write** property and a value that changes when you set a temperature in the ChefSteps app → likely `TEMPERATURE_CHAR_UUID`
- A characteristic with **Read** or **Notify** that changes as the water heats up → likely `CURRENT_TEMP_CHAR_UUID`
- A characteristic that changes when you press Start/Stop → likely `START_STOP_CHAR_UUID`
- Characteristics are grouped under a parent **service** UUID → that is `JOULE_SERVICE_UUID`

nRF Connect alone tells you the UUIDs. To confirm the **byte encoding** (how temperature values are packed), use Method 2.

---

## Method 2 — Android HCI Snoop Log + Wireshark

This captures the raw BLE traffic between the ChefSteps app and the Joule. It shows exactly which UUID is written, and the exact byte sequence, for every action you perform. This confirms both the UUIDs and the encoding assumed in `joule_ble.py`.

### Requirements

- An Android phone (any version with Developer Options)
- [Wireshark](https://www.wireshark.org/) on a desktop (free)
- USB cable + `adb` installed

### Steps

**1. Enable HCI snoop logging on Android**

1. Go to **Settings → About Phone** → tap **Build Number** seven times to unlock Developer Options.
2. Go to **Settings → Developer Options** → enable **Bluetooth HCI snoop log**.
3. Toggle Bluetooth off and back on to ensure logging starts cleanly.

**2. Capture the traffic**

1. Open the **ChefSteps app** and connect to the Joule.
2. Perform these actions one by one, with a pause between each:
   - Set a target temperature (e.g. change it from 140 °F to 150 °F)
   - Set a cook time
   - Tap **Start**
   - Tap **Stop**
3. Close the ChefSteps app.

**3. Pull the log**

```bash
adb pull /sdcard/btsnoop_hci.log ~/Desktop/btsnoop_hci.log
```

> The exact path may vary by device. If the above fails, try:
> ```bash
> adb shell find /sdcard -name "btsnoop*" 2>/dev/null
> ```

**4. Open in Wireshark**

1. Open `btsnoop_hci.log` in Wireshark.
2. In the filter bar, enter:
   ```
   btatt
   ```
3. Look for **ATT Write Request** packets — these are the bytes the app sends to the Joule.
4. Each packet shows:
   - **Handle** (a number pointing to a characteristic)
   - **Value** (the raw bytes written)

**5. Map handles to UUIDs**

Handles are dynamic, but Wireshark also logs the GATT discovery packets that map handle numbers to UUIDs. Use **Edit → Find Packet** or scroll up to find `ATT Read By Type Response` or `ATT Find By Type Value Response` packets — these contain the UUID-to-handle mapping.

Alternatively, filter for:
```
btatt.opcode == 0x12
```
(opcode `0x12` = Write Request) to list all write operations, then cross-reference handles with the nRF Connect screenshot from Method 1.

### Reading the values

Once you find the Write Request for "set temperature", the **Value** column shows the raw bytes. For example:

```
Value: dc 1d
```

`0x1ddc` in little-endian = `7644` in decimal. Divide by 100 → **76.44 °C** (≈ 170 °F). This confirms the encoding in `joule_ble.py`: temperature × 100, 2-byte little-endian.

Do the same for start/stop (expect `01` or `00`) and cook time (4-byte LE, value in seconds).

---

## Method 3 — Decompile the Android APK

The UUIDs are almost always hardcoded as string constants in the app's source code.

```bash
# 1. Pull the APK from a connected Android device
adb shell pm path com.chefsteps.mobile
# → package:/data/app/com.chefsteps.mobile-xxx/base.apk
adb pull /data/app/com.chefsteps.mobile-xxx/base.apk chefsteps.apk

# 2. Decompile with jadx (https://github.com/skylot/jadx)
jadx -d out/ chefsteps.apk

# 3. Search for UUID patterns
grep -r "[0-9a-f]\{8\}-[0-9a-f]\{4\}-[0-9a-f]\{4\}-[0-9a-f]\{4\}-[0-9a-f]\{12\}" out/
```

Look for a class or constants file with names like `JouleGattAttributes`, `BleConstants`, or `JouleUUIDs`. The five relevant UUIDs will be in a small cluster.

---

## Updating the Integration

Once you have the confirmed UUIDs, replace the placeholders in `custom_components/joule_sous_vide/const.py` (lines 34–40):

```python
# BLE GATT characteristic UUIDs
JOULE_SERVICE_UUID: Final       = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
TEMPERATURE_CHAR_UUID: Final    = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
TIME_CHAR_UUID: Final           = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
START_STOP_CHAR_UUID: Final     = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
CURRENT_TEMP_CHAR_UUID: Final   = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
```

If the byte encoding in `joule_ble.py` differs from what the sniff reveals (e.g. temperature is encoded differently), update the relevant methods in `joule_ble.py` accordingly — see `set_temperature()` (line 59), `set_cook_time()` (line 70), and `get_current_temperature()` (line 95).

If you have confirmed UUIDs, please open a pull request or file an issue at [github.com/acato/ha-joule](https://github.com/acato/ha-joule/issues) — this will help all users of the integration.

---

## See Also

- [Troubleshooting](troubleshooting.md)
- [Getting Started](getting-started.md)
- [Entity Reference](reference-entities.md)
