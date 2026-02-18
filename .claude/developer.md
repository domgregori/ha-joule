# DEVELOPER Role Guidelines

This guide covers both BACKEND DEVELOPER (Python) and FRONTEND DEVELOPER (TypeScript/JavaScript) patterns.

---

# BACKEND DEVELOPER (Python)

## Core Responsibilities

1. Implement Home Assistant integrations following best practices
2. Use proper async patterns throughout
3. Implement coordinators for data fetching
4. Create proper entity implementations
5. Build user-friendly config flows
6. Handle errors gracefully at all layers

## Essential Code Patterns

### 1. Integration Setup (__init__.py)

```python
"""The <domain> integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import DOMAIN
from .coordinator import MyCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up from a config entry."""
    coordinator = MyCoordinator(hass, entry)
    
    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception as err:
        raise ConfigEntryNotReady(f"Failed to connect: {err}") from err
    
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    
    return unload_ok
```

### 2. Data Update Coordinator

```python
"""Data coordinator for <integration>."""
from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import MyAPIClient, MyAPIError
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class MyCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching data from the API."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize."""
        self.api = MyAPIClient(
            host=entry.data["host"],
            api_key=entry.data["api_key"],
        )
        
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=30),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data via library."""
        try:
            data = await self.api.async_get_data()
            return data
        except MyAPIError as error:
            raise UpdateFailed(f"Error communicating with API: {error}") from error
```

### 3. Config Flow

```python
"""Config flow for <integration>."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_API_KEY, CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .api import MyAPIClient, CannotConnect, InvalidAuth
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_API_KEY): str,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, str]:
    """Validate the user input allows us to connect."""
    api = MyAPIClient(data[CONF_HOST], data[CONF_API_KEY])
    
    try:
        await api.async_test_connection()
    except CannotConnect as err:
        raise CannotConnect from err
    except InvalidAuth as err:
        raise InvalidAuth from err

    return {"title": f"Device at {data[CONF_HOST]}"}


class MyConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )
```

### 4. Sensor Entity

```python
"""Sensor platform for <integration>."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import MyCoordinator


@dataclass
class MySensorEntityDescription(SensorEntityDescription):
    """Describes sensor entity."""

    value_fn: Callable[[dict[str, Any]], StateType] = lambda data: None


SENSOR_TYPES: tuple[MySensorEntityDescription, ...] = (
    MySensorEntityDescription(
        key="temperature",
        name="Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("temperature"),
    ),
    MySensorEntityDescription(
        key="humidity",
        name="Humidity",
        native_unit_of_measurement="%",
        device_class=SensorDeviceClass.HUMIDITY,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("humidity"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensors from a config entry."""
    coordinator: MyCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        MySensorEntity(coordinator, entry, description)
        for description in SENSOR_TYPES
    )


class MySensorEntity(CoordinatorEntity[MyCoordinator], SensorEntity):
    """Representation of a sensor."""

    entity_description: MySensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: MyCoordinator,
        entry: ConfigEntry,
        description: MySensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "My Manufacturer",
            "model": "My Model",
        }

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        return self.entity_description.value_fn(self.coordinator.data)
```

### 5. Constants File

```python
"""Constants for the <integration>."""
from typing import Final

DOMAIN: Final = "my_integration"

# Configuration keys
CONF_DEVICE_ID: Final = "device_id"

# Default values
DEFAULT_SCAN_INTERVAL: Final = 30
DEFAULT_TIMEOUT: Final = 10
```

## Backend Development Checklist

Before considering code complete:

- [ ] All functions have type hints
- [ ] Async/await used properly (no blocking calls)
- [ ] Coordinator pattern for API polling
- [ ] Proper error handling with specific exceptions
- [ ] Logging at appropriate levels
- [ ] Unique IDs are stable and deterministic
- [ ] Device info properly configured
- [ ] Entity naming follows HA conventions
- [ ] Config flow validates all inputs
- [ ] Strings extracted to strings.json
- [ ] Manifest.json properly configured
- [ ] No hardcoded values (use constants)
- [ ] Resources cleaned up in async_unload_entry

---

# FRONTEND DEVELOPER (TypeScript/JavaScript)

## Core Responsibilities

1. Create custom Lovelace cards using Lit
2. Implement visual configuration editors
3. Follow Home Assistant design system
4. Handle entity states properly
5. Make cards responsive and accessible
6. Optimize performance

## Essential Code Patterns

### 1. Basic Custom Card

```typescript
import { LitElement, html, css, CSSResultGroup, TemplateResult } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';
import { HomeAssistant, LovelaceCardConfig } from 'custom-card-helpers';

interface MyCardConfig extends LovelaceCardConfig {
  entity: string;
  name?: string;
  show_icon?: boolean;
}

@customElement('my-custom-card')
export class MyCustomCard extends LitElement {
  @property({ attribute: false }) public hass!: HomeAssistant;
  @state() private config!: MyCardConfig;

  public static getConfigElement(): HTMLElement {
    return document.createElement('my-custom-card-editor');
  }

  public static getStubConfig(): MyCardConfig {
    return {
      type: 'custom:my-custom-card',
      entity: '',
    };
  }

  public setConfig(config: MyCardConfig): void {
    if (!config.entity) {
      throw new Error('You need to define an entity');
    }
    this.config = config;
  }

  protected render(): TemplateResult {
    if (!this.hass || !this.config) {
      return html``;
    }

    const entity = this.hass.states[this.config.entity];
    
    if (!entity) {
      return html`
        <ha-card>
          <div class="warning">Entity ${this.config.entity} not found</div>
        </ha-card>
      `;
    }

    return html`
      <ha-card>
        <div class="card-header">
          ${this.config.name || entity.attributes.friendly_name}
        </div>
        <div class="card-content">
          <div class="state">${entity.state}</div>
          ${entity.attributes.unit_of_measurement 
            ? html`<div class="unit">${entity.attributes.unit_of_measurement}</div>`
            : ''
          }
        </div>
      </ha-card>
    `;
  }

  static get styles(): CSSResultGroup {
    return css`
      :host {
        display: block;
      }
      
      ha-card {
        padding: 16px;
      }
      
      .card-header {
        font-weight: 500;
        font-size: 16px;
        margin-bottom: 8px;
      }
      
      .warning {
        color: var(--error-color);
        padding: 16px;
      }
      
      .state {
        font-size: 2em;
        font-weight: bold;
        color: var(--primary-text-color);
      }
      
      .unit {
        color: var(--secondary-text-color);
        margin-left: 4px;
      }
    `;
  }
}

declare global {
  interface HTMLElementTagNameMap {
    'my-custom-card': MyCustomCard;
  }
}
```

### 2. Card Editor

```typescript
import { LitElement, html, TemplateResult } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';
import { HomeAssistant } from 'custom-card-helpers';

@customElement('my-custom-card-editor')
export class MyCustomCardEditor extends LitElement {
  @property({ attribute: false }) public hass!: HomeAssistant;
  @state() private config!: MyCardConfig;

  public setConfig(config: MyCardConfig): void {
    this.config = config;
  }

  private _valueChanged(ev: CustomEvent): void {
    if (!this.config || !this.hass) {
      return;
    }

    const target = ev.target as any;
    const configValue = target.configValue;

    if (this.config[configValue] === target.value) {
      return;
    }

    const newConfig = {
      ...this.config,
      [configValue]: target.value,
    };

    const event = new CustomEvent('config-changed', {
      detail: { config: newConfig },
      bubbles: true,
      composed: true,
    });
    this.dispatchEvent(event);
  }

  protected render(): TemplateResult {
    if (!this.hass || !this.config) {
      return html``;
    }

    return html`
      <div class="card-config">
        <ha-entity-picker
          .label=${'Entity (Required)'}
          .hass=${this.hass}
          .value=${this.config.entity}
          .configValue=${'entity'}
          @value-changed=${this._valueChanged}
          allow-custom-entity
        ></ha-entity-picker>
        
        <ha-textfield
          .label=${'Name (Optional)'}
          .value=${this.config.name || ''}
          .configValue=${'name'}
          @input=${this._valueChanged}
        ></ha-textfield>
        
        <ha-formfield .label=${'Show Icon'}>
          <ha-switch
            .checked=${this.config.show_icon !== false}
            .configValue=${'show_icon'}
            @change=${this._valueChanged}
          ></ha-switch>
        </ha-formfield>
      </div>
    `;
  }
}
```

### 3. Calling Services

```typescript
private _toggle(): void {
  this.hass.callService('light', 'toggle', {
    entity_id: this.config.entity,
  });
}

private _setValue(value: number): void {
  this.hass.callService('input_number', 'set_value', {
    entity_id: this.config.entity,
    value: value,
  });
}

private async _callServiceWithResponse(): Promise<void> {
  try {
    const response = await this.hass.callService(
      'my_domain',
      'my_service',
      { entity_id: this.config.entity },
      { return_response: true }
    );
    console.log('Service response:', response);
  } catch (err) {
    console.error('Service call failed:', err);
  }
}
```

### 4. Firing Events

```typescript
// Show more-info dialog
private _showMoreInfo(): void {
  const event = new CustomEvent('hass-more-info', {
    detail: { entityId: this.config.entity },
    bubbles: true,
    composed: true,
  });
  this.dispatchEvent(event);
}

// Navigate to a different view
private _navigate(path: string): void {
  window.history.pushState(null, '', path);
  const event = new CustomEvent('location-changed', {
    detail: { replace: false },
    bubbles: true,
    composed: true,
  });
  this.dispatchEvent(event);
}
```

### 5. Responsive Design

```typescript
@state() private _narrow = false;

public connectedCallback(): void {
  super.connectedCallback();
  this._updateNarrow();
  window.addEventListener('resize', this._updateNarrow);
}

public disconnectedCallback(): void {
  super.disconnectedCallback();
  window.removeEventListener('resize', this._updateNarrow);
}

private _updateNarrow = (): void => {
  this._narrow = window.innerWidth < 600;
};

// In styles
static get styles(): CSSResultGroup {
  return css`
    .card-content {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 16px;
    }
    
    @media (max-width: 600px) {
      .card-content {
        grid-template-columns: 1fr;
      }
    }
  `;
}
```

### 6. Using HA Design System

```typescript
// Import HA components (available in HA frontend)
// No need to import, they're globally available:
// - ha-card
// - ha-icon
// - ha-textfield
// - ha-switch
// - ha-button
// - ha-entity-picker
// - ha-select
// - ha-formfield

// Use CSS custom properties
static get styles(): CSSResultGroup {
  return css`
    .element {
      color: var(--primary-text-color);
      background: var(--card-background-color);
      border: 1px solid var(--divider-color);
    }
    
    .state-on {
      color: var(--state-on-color);
    }
    
    .state-off {
      color: var(--state-off-color);
    }
    
    .error {
      color: var(--error-color);
    }
  `;
}
```

### 7. Chart Integration

```typescript
import { Chart } from 'chart.js/auto';
import { query } from 'lit/decorators.js';

@query('#myChart') private _chartCanvas?: HTMLCanvasElement;
private _chart?: Chart;

protected firstUpdated(): void {
  if (!this._chartCanvas) return;
  
  this._chart = new Chart(this._chartCanvas, {
    type: 'line',
    data: {
      labels: this._getLabels(),
      datasets: [{
        label: 'Temperature',
        data: this._getData(),
        borderColor: 'var(--primary-color)',
        backgroundColor: 'rgba(var(--rgb-primary-color), 0.1)',
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          labels: {
            color: 'var(--primary-text-color)',
          },
        },
      },
    },
  });
}

protected updated(changedProps: PropertyValues): void {
  if (changedProps.has('hass') && this._chart) {
    this._updateChart();
  }
}

public disconnectedCallback(): void {
  super.disconnectedCallback();
  if (this._chart) {
    this._chart.destroy();
    this._chart = undefined;
  }
}
```

## Frontend Development Checklist

Before considering code complete:

- [ ] TypeScript strict mode enabled
- [ ] Proper Lit decorators used (@property, @state, @query)
- [ ] Editor component created
- [ ] getStubConfig() implemented
- [ ] Handles missing entities gracefully
- [ ] Responsive design (mobile, tablet, desktop)
- [ ] Uses CSS custom properties for theming
- [ ] No hardcoded colors
- [ ] Event listeners cleaned up in disconnectedCallback
- [ ] Charts/heavy components destroyed properly
- [ ] No XSS vulnerabilities (no innerHTML with user data)
- [ ] Accessible (keyboard navigation, ARIA labels)
- [ ] No console.log in production code
- [ ] Version number in package.json

## Build Configuration

### package.json
```json
{
  "name": "my-custom-card",
  "version": "1.0.0",
  "description": "A custom Lovelace card",
  "main": "dist/my-custom-card.js",
  "scripts": {
    "build": "rollup -c",
    "watch": "rollup -c --watch",
    "lint": "eslint src --ext .ts"
  },
  "devDependencies": {
    "@rollup/plugin-node-resolve": "^15.0.0",
    "@rollup/plugin-typescript": "^11.0.0",
    "rollup": "^4.0.0",
    "rollup-plugin-terser": "^7.0.0",
    "typescript": "^5.0.0"
  },
  "dependencies": {
    "custom-card-helpers": "^1.9.0",
    "lit": "^3.0.0"
  }
}
```

### rollup.config.js
```javascript
import typescript from '@rollup/plugin-typescript';
import resolve from '@rollup/plugin-node-resolve';
import { terser } from 'rollup-plugin-terser';

export default {
  input: 'src/my-custom-card.ts',
  output: {
    file: 'dist/my-custom-card.js',
    format: 'es',
  },
  plugins: [
    resolve(),
    typescript(),
    terser(),
  ],
};
```

### tsconfig.json
```json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "ESNext",
    "lib": ["ES2020", "DOM"],
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true,
    "strict": true,
    "moduleResolution": "node",
    "esModuleInterop": true,
    "skipLibCheck": true,
    "experimentalDecorators": true,
    "useDefineForClassFields": false
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist"]
}
```

## Common Mistakes to Avoid

### Backend
❌ Using blocking I/O in async functions
❌ Not handling UpdateFailed in coordinator
❌ Forgetting to set unique_id
❌ Not cleaning up in async_unload_entry
❌ Using `self.hass.states.get()` in entity (use coordinator data)

### Frontend  
❌ Not removing event listeners in disconnectedCallback
❌ Using innerHTML with user data (XSS risk)
❌ Not checking if entity exists before accessing
❌ Hardcoding colors instead of using CSS variables
❌ Heavy computation in render() method
❌ Not destroying charts/maps on disconnect

## Performance Tips

### Backend
- Use coordinator to batch API calls
- Cache expensive computations
- Use debounce for rapid state changes
- Limit polling frequency

### Frontend
- Lazy load heavy dependencies (charts, maps)
- Debounce rapid updates
- Use virtual scrolling for long lists
- Optimize re-renders with proper state management
