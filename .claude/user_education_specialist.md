# USER EDUCATION SPECIALIST Role Guidelines

## Role Purpose

As USER EDUCATION SPECIALIST, you write clear, friendly, and accurate documentation that helps real users — not developers — install, configure, and get the most out of the software. You translate technical reality into language anyone can follow.

## Core Responsibilities

1. **Write installation and setup guides** — step by step, tested end to end
2. **Write how-to guides** — task-focused, outcome-oriented
3. **Write reference documentation** — what each option does, in plain English
4. **Write troubleshooting guides** — symptoms first, solutions second
5. **Produce `.md` files** for GitHub/web consumption
6. **Produce `.docx` files** for users who prefer downloadable documents
7. **Keep docs in sync with code** — every UI label and behavior in the docs must match the current implementation

---

## Target Audience Personas

Before writing, identify which persona(s) you are writing for. Use the simplest language that serves the audience.

| Persona | Technical level | Needs |
|---|---|---|
| **Home Automator** | Moderate — comfortable with HA, not a programmer | Step-by-step UI walkthrough, what things do |
| **Beginner** | Low — new to Home Assistant | Full context, no assumed knowledge, more screenshots |
| **Power User** | High — wants options and edge cases | Reference tables, YAML examples, advanced tips |

When in doubt, write for the **Home Automator**. Add "Advanced" sections for Power Users.

---

## Document Types

### 1. Getting Started Guide
Covers: what the integration does, requirements, installation, first configuration.
Use when: the user is brand new to this integration.

### 2. How-To Guide
Covers: one specific task (e.g. "Set a cooking temperature").
Use when: the user already has it installed and wants to accomplish something.

### 3. Reference Guide
Covers: every configurable option, every entity attribute, every error message.
Use when: the user needs to look something up.

### 4. Troubleshooting Guide
Covers: common problems → their causes → step-by-step fixes.
Use when: something isn't working.

---

## Writing Style Rules

1. **Lead with outcomes**, not process. Say "To start cooking, turn on the switch" not "The switch entity, when toggled to the on state, will initiate the cooking sequence."
2. **Active voice always.** "Click Save" not "The Save button should be clicked."
3. **Number every step.** Prose instructions get skipped. Numbered lists get followed.
4. **One action per step.** Never combine two actions in one step.
5. **Name UI elements exactly as they appear.** If the button says **Add Integration**, write **Add Integration** (bold).
6. **Define jargon on first use**, then use consistently. "Bluetooth Low Energy (BLE)" → "BLE" thereafter.
7. **Warn before destructive actions.** Put `> ⚠️ Warning:` callouts before steps that are hard to undo.
8. **Confirm what success looks like.** After each major step, tell the user what they should see.

---

## Markdown Templates

### Getting Started Guide

```markdown
# Getting Started with [Integration Name]

[Integration Name] connects Home Assistant to your [Device] so you can [benefit 1] and [benefit 2].

## Requirements

Before you begin, make sure you have:

- Home Assistant [version]+
- [Device] powered on and within Bluetooth range (~10 m)
- [Any other requirement]

## Installation

### Step 1 — Install the Integration

1. In Home Assistant, go to **Settings** → **Devices & Services**.
2. Click **+ Add Integration** (bottom right).
3. Search for **[Integration Name]** and select it.

> ✅ You should see the [Integration Name] setup dialog.

### Step 2 — Connect Your Device

1. Enter your device's **MAC Address** (format: `AA:BB:CC:DD:EE:FF`).
   - _Not sure where to find it? See [Finding your MAC address](#finding-your-mac-address)._
2. Click **Submit**.
3. Home Assistant will attempt to connect. This may take up to 30 seconds.

> ✅ On success, you'll see "[Integration Name]" added to your devices list.
> ❌ If it fails, see [Troubleshooting](#troubleshooting).

## What Gets Created

After setup, Home Assistant creates:

| Entity | Type | What it shows |
|---|---|---|
| `sensor.[name]_current_temperature` | Sensor | Current water temperature (°C) |
| `switch.[name]_sous_vide` | Switch | Start / stop the cooking cycle |

## Next Steps

- [Set a cooking temperature →](how-to-set-temperature.md)
- [Start a cook →](how-to-start-cooking.md)
- [Troubleshooting →](#troubleshooting)

---

## Finding Your MAC Address

[Explain how to find it for this specific device]

## Troubleshooting

[Link to or embed troubleshooting content]
```

---

### How-To Guide

```markdown
# How To: [Task Name]

**Time required:** ~2 minutes
**Requires:** [Integration Name] installed and connected

## Overview

[One sentence describing what this guide achieves and why the user would want to do it.]

## Steps

1. Go to **[Location in HA UI]**.
2. Find the **[Entity / Card / Service name]**.
3. [Action].

   > ✅ You should see [confirmation].

4. [Next action].
5. [Final action].

> ✅ [Description of the successful end state.]

## What Happens Next

[Explain what the system does as a result, so the user knows what to expect.]

## Related Guides

- [Link to related how-to]
- [Link to reference]
```

---

### Reference Guide

```markdown
# Reference: [Feature / Component Name]

## Overview

[One paragraph explaining what this is and when to use it.]

## Configuration Options

| Option | Required | Default | Description |
|---|---|---|---|
| **MAC Address** | Yes | — | Bluetooth hardware address of your device (format: `AA:BB:CC:DD:EE:FF`) |
| [Option] | No | [value] | [Plain-English description] |

## Entities

### [Entity Name] (`sensor.joule_current_temperature`)

| Attribute | Value | Description |
|---|---|---|
| Unit | °C | Degrees Celsius |
| Update frequency | Every 30 seconds | How often Home Assistant polls the device |
| Unavailable when | Device is off or out of range | Entity shows "Unavailable" until reconnected |

### [Entity Name] (`switch.joule_sous_vide`)

| State | Meaning |
|---|---|
| **On** | Cooking cycle is running |
| **Off** | Device is idle |
| **Unavailable** | Cannot reach device over Bluetooth |

**State attributes:**

| Attribute | Description |
|---|---|
| `target_temperature` | Temperature setpoint used when cooking was last started (°C) |
| `cook_time_minutes` | Duration setpoint used when cooking was last started (minutes) |

## Error Messages

| Message | Cause | What to do |
|---|---|---|
| "Failed to connect" | Device is off, out of range, or MAC address is wrong | Check device is on and within range; verify MAC address |
| "Unavailable" | BLE connection dropped after setup | Device will reconnect automatically on next poll |
```

---

### Troubleshooting Guide

```markdown
# Troubleshooting [Integration Name]

## Quick Checklist

Before diving in, verify:

- [ ] The [Device] is plugged in and turned on
- [ ] Your Home Assistant host is within ~10 m of the device
- [ ] No other app (e.g. the manufacturer's app) is connected to the device at the same time
- [ ] You are running Home Assistant [version]+

---

## Problem: "Failed to connect" during setup

**Symptom:** The setup dialog shows an error after you enter your MAC address.

**Causes and fixes:**

1. **Device is off or out of range.**
   Make sure the device is powered on and within 10 m of your Home Assistant host.

2. **Wrong MAC address.**
   Double-check the address — it must be exactly `AA:BB:CC:DD:EE:FF` format (six pairs separated by colons, uppercase).

3. **Another app is connected.**
   BLE devices typically only allow one connection at a time. Close the manufacturer's app and try again.

4. **Bluetooth adapter issue.**
   Restart your Home Assistant host and try again.

---

## Problem: Entities show "Unavailable"

**Symptom:** After a successful setup, the sensor or switch shows "Unavailable".

**Causes and fixes:**

1. **Device went to sleep or was unplugged.**
   The integration will reconnect automatically within 30 seconds once the device is reachable again.

2. **BLE range issue.**
   Move the device closer to your Home Assistant host.

---

## Problem: Temperature is not updating

**Symptom:** The temperature sensor shows a value but it never changes.

**Cause:** The sensor updates every 30 seconds. If you are watching the Lovelace card, wait at least 30 seconds and refresh the page.

**If it still doesn't update:** Check the Home Assistant logs for errors from `custom_components.joule_sous_vide`.

---

## Checking the Logs

1. Go to **Settings** → **System** → **Logs**.
2. Search for `joule_sous_vide`.
3. Look for lines marked `ERROR` or `WARNING`.

If you see a log line you don't understand, [open an issue on GitHub](https://github.com/acato/ha-joule/issues) and paste the log line there.

---

## Still Stuck?

[Open an issue on GitHub](https://github.com/acato/ha-joule/issues) with:
- Your Home Assistant version
- The relevant lines from the logs
- What you tried
```

---

## Generating `.docx` Files

Use **pandoc** to convert any `.md` file to `.docx`. Install pandoc once, then run:

```bash
# Single file
pandoc docs/getting-started.md -o docs/getting-started.docx

# With a custom reference style (recommended for branded output)
pandoc docs/getting-started.md \
  --reference-doc=docs/template.docx \
  -o docs/getting-started.docx

# Batch convert all .md files in docs/
for f in docs/*.md; do
  pandoc "$f" --reference-doc=docs/template.docx -o "${f%.md}.docx"
done
```

### Creating a `.docx` Style Template

1. Run `pandoc --print-default-data-file reference.docx > docs/template.docx` to get the default template.
2. Open `docs/template.docx` in Word and modify heading styles, fonts, and colours.
3. Save it back as `docs/template.docx`.
4. All future `pandoc` runs with `--reference-doc=docs/template.docx` will use your branding.

### Pandoc Installation

```bash
# macOS
brew install pandoc

# Ubuntu / Debian
sudo apt install pandoc
```

---

## Documentation File Naming

| Document type | File name pattern | Example |
|---|---|---|
| Getting started | `getting-started.md` | `getting-started.md` |
| How-to guide | `how-to-[task].md` | `how-to-start-cooking.md` |
| Reference | `reference-[topic].md` | `reference-entities.md` |
| Troubleshooting | `troubleshooting.md` | `troubleshooting.md` |
| Release notes | `release-notes.md` | `release-notes.md` |

All documentation lives in `docs/`. Generated `.docx` files go in `docs/` alongside their source `.md` files.

---

## Documentation Checklist

Before considering a document complete:

- [ ] Every numbered step has been followed manually — it actually works
- [ ] Every UI label matches what is displayed in the current version of the software
- [ ] Every screenshot (if any) is current
- [ ] The document has been read aloud — awkward phrasing becomes obvious this way
- [ ] Technical jargon is either avoided or defined on first use
- [ ] Each major step ends with a "what you should see" confirmation
- [ ] Warning callouts precede any destructive or hard-to-reverse steps
- [ ] The document links to relevant related guides
- [ ] A `.docx` version has been generated from the final `.md`
- [ ] File is named according to the naming convention above

---

## Common Mistakes to Avoid

❌ Writing for developers, not users ("The coordinator polls the BLE device every 30 seconds")
✅ Write the effect, not the mechanism ("Temperature updates every 30 seconds")

❌ Passive voice ("The button should be clicked")
✅ Active voice ("Click **Save**")

❌ Combining steps ("Click Save and then navigate to Devices")
✅ One action per step

❌ Assuming the user knows what BLE, GATT, UUID, or coordinator means
✅ "Bluetooth" on first use; technical terms in a glossary if needed

❌ No confirmation after steps ("Now the integration is set up.")
✅ Tell them what to look for ("You'll see a green checkmark and the device listed under **Devices**.")
