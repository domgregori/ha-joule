# Advanced: Joule BLE GATT UUIDs

**Audience:** Advanced users comfortable with Bluetooth tools and/or Android developer options.

## Known UUIDs

The Joule's BLE UUIDs have been reverse-engineered from the [chromeJoule](https://github.com/li-dennis/chromeJoule/blob/master/src/constants.ts) project and are populated in `const.py`:

| Constant in `const.py` | UUID | Purpose |
|---|---|---|
| `JOULE_SERVICE_UUID` | `700b4321-9836-4383-a2b2-31a9098d1473` | Primary GATT service |
| `WRITE_CHAR_UUID` | `700b4322-9836-4383-a2b2-31a9098d1473` | Write: send protobuf commands |
| `READ_CHAR_UUID` | `700b4323-9836-4383-a2b2-31a9098d1473` | Read: receive protobuf responses |
| `SUBSCRIBE_CHAR_UUID` | `700b4325-9836-4383-a2b2-31a9098d1473` | Notify: async notifications |
| `FILE_CHAR_UUID` | `700b4326-9836-4383-a2b2-31a9098d1473` | File transfer (firmware) |

The Joule uses **protobuf-encoded messages** (StreamMessage wrappers via `base.proto` / `remote.proto`) over a single service. All commands go through `WRITE_CHAR_UUID`; responses come back on `READ_CHAR_UUID` or `SUBSCRIBE_CHAR_UUID`.

---

## Background

The Joule communicates over **Bluetooth Low Energy (BLE)** using the **GATT** (Generic Attribute Profile) protocol. Every BLE device exposes a tree of **services**, each containing **characteristics** — the actual data endpoints you read from or write to. Each characteristic has a globally unique identifier: a **UUID** (e.g. `6e400002-b5a3-f393-e0a9-e50e24dcca9e`).

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

- The service `700b4321-9836-4383-a2b2-31a9098d1473` should appear with four characteristics (`...4322`, `...4323`, `...4325`, `...4326`)
- `...4322` (Write) — write protobuf commands here
- `...4323` (Read) — read protobuf responses here
- `...4325` (Notify) — subscribe for async protobuf notifications
- `...4326` (Write Without Response) — used for file/firmware transfers

nRF Connect confirms the UUIDs match the values in `const.py`. To understand the **protobuf encoding** (how commands are packed), use Method 2.

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

## Next Step: Protobuf Decoding

The UUIDs are now populated in `const.py`. The remaining challenge is implementing the **protobuf message encoding/decoding**. The Joule protocol uses Google Protocol Buffers (`base.proto` / `remote.proto`) to serialize all commands and responses.

Key resources for the protobuf layer:
- [JouleUWP JOULE_PROTOCOL.md](https://github.com/mitchcapper/JouleUWP/blob/master/JOULE_PROTOCOL.md) — protocol documentation
- [chromeJoule](https://github.com/li-dennis/chromeJoule) — working JavaScript implementation using CirculatorSDK
- Android HCI snoop logs (Method 2 above) — capture raw protobuf bytes for analysis

If you have confirmed UUIDs, please open a pull request or file an issue at [github.com/acato/ha-joule](https://github.com/acato/ha-joule/issues) — this will help all users of the integration.

---

## See Also

- [Troubleshooting](troubleshooting.md)
- [Getting Started](getting-started.md)
- [Entity Reference](reference-entities.md)
