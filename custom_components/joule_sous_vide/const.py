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

# Target temperature bounds (°C)
MIN_TARGET_TEMPERATURE: Final = 0.0
MAX_TARGET_TEMPERATURE: Final = 100.0
STEP_TARGET_TEMPERATURE: Final = 0.5

# Cook time bounds (minutes); 0 means no time limit
MIN_COOK_TIME_MINUTES: Final = 0.0
MAX_COOK_TIME_MINUTES: Final = 1440.0  # 24 hours
STEP_COOK_TIME_MINUTES: Final = 1.0

# BLE GATT characteristic UUIDs
# TODO: Replace with real Joule UUIDs once reverse-engineered
JOULE_SERVICE_UUID: Final = "YOUR_JOULE_SERVICE_UUID"
TEMPERATURE_CHAR_UUID: Final = "YOUR_TEMPERATURE_CHAR_UUID"
TIME_CHAR_UUID: Final = "YOUR_TIME_CHAR_UUID"
START_STOP_CHAR_UUID: Final = "YOUR_START_STOP_CHAR_UUID"
CURRENT_TEMP_CHAR_UUID: Final = "YOUR_CURRENT_TEMP_CHAR_UUID"
