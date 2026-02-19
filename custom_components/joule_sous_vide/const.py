"""Constants for the Joule Sous Vide integration."""
from __future__ import annotations

from typing import Final

DOMAIN: Final = "joule_sous_vide"

# Configuration keys
CONF_MAC_ADDRESS: Final = "mac_address"

# Defaults
DEFAULT_TARGET_TEMPERATURE: Final = 60.0  # °C
DEFAULT_COOK_TIME_MINUTES: Final = 0.0
DEFAULT_SCAN_INTERVAL: Final = 30  # seconds

# Target temperature bounds — Celsius
MIN_TARGET_TEMPERATURE: Final = 0.0
MAX_TARGET_TEMPERATURE: Final = 100.0
STEP_TARGET_TEMPERATURE: Final = 0.5

# Target temperature bounds — Fahrenheit
MIN_TARGET_TEMPERATURE_F: Final = 32.0
MAX_TARGET_TEMPERATURE_F: Final = 212.0
STEP_TARGET_TEMPERATURE_F: Final = 1.0

# Cook time bounds (minutes); 0 means no time limit
MIN_COOK_TIME_MINUTES: Final = 0.0
MAX_COOK_TIME_MINUTES: Final = 1440.0  # 24 hours
STEP_COOK_TIME_MINUTES: Final = 1.0

# Temperature unit preference
DEFAULT_TEMPERATURE_UNIT: Final = "°F"

# BLE GATT UUIDs — reverse-engineered from the Joule Android app
# Source: https://github.com/li-dennis/chromeJoule/blob/master/src/constants.ts
JOULE_SERVICE_UUID: Final = "700b4321-9836-4383-a2b2-31a9098d1473"
WRITE_CHAR_UUID: Final = "700b4322-9836-4383-a2b2-31a9098d1473"
READ_CHAR_UUID: Final = "700b4323-9836-4383-a2b2-31a9098d1473"
SUBSCRIBE_CHAR_UUID: Final = "700b4325-9836-4383-a2b2-31a9098d1473"
FILE_CHAR_UUID: Final = "700b4326-9836-4383-a2b2-31a9098d1473"

# BLE manufacturer ID (used during discovery/scanning)
JOULE_MANUFACTURER_ID: Final = 0x0159
