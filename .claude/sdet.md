# SDET Role Guidelines

## Role Purpose

As SDET (Software Development Engineer in Test), you create comprehensive test suites that ensure code quality, catch bugs early, and enable confident refactoring.

## Core Responsibilities

1. Write comprehensive test suites for all code
2. Achieve high test coverage (80%+ overall, 100% for critical paths)
3. Create reusable test fixtures and helpers
4. Test both happy paths and error scenarios
5. Ensure tests are fast, reliable, and maintainable
6. Document test strategies and edge cases

---

# BACKEND TESTING (Python/pytest)

## Test Structure

```
tests/
├── conftest.py                 # Shared fixtures
├── __init__.py
├── test_init.py                # Integration setup/teardown
├── test_config_flow.py         # Configuration UI tests
├── test_coordinator.py         # Data coordinator tests
└── test_sensor.py              # Entity tests
```

## Essential Fixtures (conftest.py)

```python
"""Fixtures for tests."""
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.my_integration.const import DOMAIN


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            "host": "test.local",
            "api_key": "test_key",
        },
        entry_id="test_entry_id",
        title="Test Device",
    )


@pytest.fixture
def mock_api():
    """Mock the API client."""
    with patch(
        "custom_components.my_integration.MyAPIClient", autospec=True
    ) as mock_api:
        api_instance = mock_api.return_value
        api_instance.async_get_data = AsyncMock(
            return_value={
                "temperature": 23.5,
                "humidity": 45,
            }
        )
        api_instance.async_test_connection = AsyncMock(return_value=True)
        yield api_instance


@pytest.fixture
async def setup_integration(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_api,
) -> None:
    """Set up the integration."""
    mock_config_entry.add_to_hass(hass)
    
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
```

## Test Patterns

### 1. Testing Integration Setup

```python
"""Test integration setup and unload."""
import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from custom_components.my_integration.const import DOMAIN


async def test_setup_entry(hass: HomeAssistant, setup_integration) -> None:
    """Test successful setup of entry."""
    assert DOMAIN in hass.data
    assert len(hass.data[DOMAIN]) == 1


async def test_setup_entry_failure(
    hass: HomeAssistant, mock_config_entry, mock_api
) -> None:
    """Test setup fails when API connection fails."""
    mock_api.async_get_data.side_effect = Exception("Connection failed")
    
    mock_config_entry.add_to_hass(hass)
    assert not await hass.config_entries.async_setup(mock_config_entry.entry_id)
    
    assert mock_config_entry.state == ConfigEntryState.SETUP_RETRY


async def test_unload_entry(
    hass: HomeAssistant, mock_config_entry, setup_integration
) -> None:
    """Test successful unload of entry."""
    assert await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    
    assert mock_config_entry.entry_id not in hass.data[DOMAIN]
    assert mock_config_entry.state == ConfigEntryState.NOT_LOADED
```

### 2. Testing Config Flow

```python
"""Test config flow."""
from homeassistant import config_entries, data_entry_flow
from homeassistant.core import HomeAssistant

from custom_components.my_integration.const import DOMAIN


async def test_form(hass: HomeAssistant, mock_api) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["errors"] == {}


async def test_form_valid_input(hass: HomeAssistant, mock_api) -> None:
    """Test successful flow with valid input."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "host": "192.168.1.100",
            "api_key": "test_key",
        },
    )
    await hass.async_block_till_done()

    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == "Device at 192.168.1.100"
    assert result["data"] == {
        "host": "192.168.1.100",
        "api_key": "test_key",
    }


async def test_form_cannot_connect(hass: HomeAssistant, mock_api) -> None:
    """Test we handle cannot connect error."""
    from custom_components.my_integration.api import CannotConnect
    
    mock_api.async_test_connection.side_effect = CannotConnect
    
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "host": "192.168.1.100",
            "api_key": "test_key",
        },
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_form_invalid_auth(hass: HomeAssistant, mock_api) -> None:
    """Test we handle invalid auth error."""
    from custom_components.my_integration.api import InvalidAuth
    
    mock_api.async_test_connection.side_effect = InvalidAuth
    
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "host": "192.168.1.100",
            "api_key": "wrong_key",
        },
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["errors"] == {"base": "invalid_auth"}


async def test_form_duplicate(hass: HomeAssistant, mock_config_entry) -> None:
    """Test duplicate detection."""
    mock_config_entry.add_to_hass(hass)
    
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "host": "test.local",
            "api_key": "test_key",
        },
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "already_configured"
```

### 3. Testing Coordinator

```python
"""Test coordinator."""
from datetime import timedelta
from unittest.mock import AsyncMock

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed
from homeassistant.util import dt as dt_util

from custom_components.my_integration.coordinator import MyCoordinator


async def test_coordinator_update_success(
    hass: HomeAssistant, mock_config_entry, mock_api
) -> None:
    """Test successful data update."""
    coordinator = MyCoordinator(hass, mock_config_entry)
    
    await coordinator.async_config_entry_first_refresh()
    
    assert coordinator.data == {
        "temperature": 23.5,
        "humidity": 45,
    }


async def test_coordinator_update_failed(
    hass: HomeAssistant, mock_config_entry, mock_api
) -> None:
    """Test failed data update raises UpdateFailed."""
    mock_api.async_get_data.side_effect = Exception("API Error")
    
    coordinator = MyCoordinator(hass, mock_config_entry)
    
    with pytest.raises(UpdateFailed):
        await coordinator.async_config_entry_first_refresh()


async def test_coordinator_update_interval(
    hass: HomeAssistant, mock_config_entry, mock_api
) -> None:
    """Test coordinator respects update interval."""
    coordinator = MyCoordinator(hass, mock_config_entry)
    await coordinator.async_config_entry_first_refresh()
    
    # Fast-forward time
    future = dt_util.utcnow() + timedelta(seconds=30)
    
    with patch("homeassistant.util.dt.utcnow", return_value=future):
        await coordinator.async_refresh()
    
    # Should have called API twice (initial + after interval)
    assert mock_api.async_get_data.call_count == 2
```

### 4. Testing Entities

```python
"""Test sensor entities."""
from homeassistant.const import STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant


async def test_sensors_created(hass: HomeAssistant, setup_integration) -> None:
    """Test sensor entities are created."""
    state = hass.states.get("sensor.test_device_temperature")
    assert state
    assert state.state == "23.5"
    assert state.attributes["unit_of_measurement"] == "°C"
    
    state = hass.states.get("sensor.test_device_humidity")
    assert state
    assert state.state == "45"
    assert state.attributes["unit_of_measurement"] == "%"


async def test_sensor_unique_id(hass: HomeAssistant, setup_integration) -> None:
    """Test sensor unique ID."""
    entity_registry = er.async_get(hass)
    
    entry = entity_registry.async_get("sensor.test_device_temperature")
    assert entry
    assert entry.unique_id == "test_entry_id_temperature"


async def test_sensor_unavailable_on_update_failure(
    hass: HomeAssistant, mock_config_entry, mock_api
) -> None:
    """Test sensor becomes unavailable when update fails."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    
    state = hass.states.get("sensor.test_device_temperature")
    assert state.state == "23.5"
    
    # Cause update to fail
    mock_api.async_get_data.side_effect = Exception("API Error")
    
    # Trigger update
    coordinator = hass.data[DOMAIN][mock_config_entry.entry_id]
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    
    state = hass.states.get("sensor.test_device_temperature")
    assert state.state == STATE_UNAVAILABLE
```

## Backend Testing Checklist

- [ ] Integration setup tested (success and failure)
- [ ] Integration unload tested
- [ ] Config flow tested (all steps, all error cases)
- [ ] Coordinator update tested (success and failure)
- [ ] All entities created and have correct state
- [ ] Unique IDs are stable
- [ ] Device info is correct
- [ ] Entities become unavailable on coordinator failure
- [ ] Service calls tested (if any)
- [ ] Options flow tested (if applicable)
- [ ] Migration tested (if updating schema)
- [ ] Minimum 80% code coverage

---

# FRONTEND TESTING (Jest + Testing Library)

## Test Structure

```
tests/
├── jest.config.js              # Jest configuration
├── setup.ts                    # Test environment setup
├── __mocks__/                  # Mock modules
│   └── ha-frontend.ts
└── src/
    ├── my-custom-card.test.ts
    └── editor.test.ts
```

## Jest Configuration

```javascript
// jest.config.js
export default {
  preset: 'ts-jest',
  testEnvironment: 'jsdom',
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
  },
  setupFilesAfterEnv: ['<rootDir>/tests/setup.ts'],
  collectCoverageFrom: [
    'src/**/*.ts',
    '!src/**/*.d.ts',
  ],
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80,
    },
  },
};
```

## Test Setup

```typescript
// tests/setup.ts
import '@testing-library/jest-dom';

// Mock Home Assistant components
global.customElements.define = jest.fn();

// Mock window.customCards
(window as any).customCards = [];
```

## Test Patterns

### 1. Basic Card Rendering

```typescript
import { fixture, html } from '@open-wc/testing';
import { HomeAssistant } from 'custom-card-helpers';
import '../src/my-custom-card';
import { MyCustomCard } from '../src/my-custom-card';

const mockHass: Partial<HomeAssistant> = {
  states: {
    'sensor.test': {
      entity_id: 'sensor.test',
      state: '23.5',
      attributes: {
        friendly_name: 'Test Sensor',
        unit_of_measurement: '°C',
      },
      last_changed: '2024-01-01T00:00:00Z',
      last_updated: '2024-01-01T00:00:00Z',
      context: { id: '', parent_id: null, user_id: null },
    },
  },
  callService: jest.fn(),
  connection: {} as any,
};

describe('MyCustomCard', () => {
  let element: MyCustomCard;

  beforeEach(async () => {
    element = await fixture(html`<my-custom-card></my-custom-card>`);
    element.hass = mockHass as HomeAssistant;
  });

  it('should render the card', () => {
    expect(element).toBeTruthy();
    expect(element.shadowRoot).toBeTruthy();
  });

  it('should display entity state', async () => {
    element.setConfig({
      type: 'custom:my-custom-card',
      entity: 'sensor.test',
    });
    await element.updateComplete;

    const state = element.shadowRoot!.querySelector('.state');
    expect(state?.textContent).toContain('23.5');
  });

  it('should display entity name', async () => {
    element.setConfig({
      type: 'custom:my-custom-card',
      entity: 'sensor.test',
      name: 'Custom Name',
    });
    await element.updateComplete;

    const header = element.shadowRoot!.querySelector('.card-header');
    expect(header?.textContent).toBe('Custom Name');
  });

  it('should use friendly_name when name not provided', async () => {
    element.setConfig({
      type: 'custom:my-custom-card',
      entity: 'sensor.test',
    });
    await element.updateComplete;

    const header = element.shadowRoot!.querySelector('.card-header');
    expect(header?.textContent).toBe('Test Sensor');
  });
});
```

### 2. Error Handling Tests

```typescript
describe('Error Handling', () => {
  it('should show error for missing entity', async () => {
    element.setConfig({
      type: 'custom:my-custom-card',
      entity: 'sensor.nonexistent',
    });
    await element.updateComplete;

    const warning = element.shadowRoot!.querySelector('.warning');
    expect(warning).toBeTruthy();
    expect(warning?.textContent).toContain('not found');
  });

  it('should throw error if entity not provided in config', () => {
    expect(() => {
      element.setConfig({ type: 'custom:my-custom-card' } as any);
    }).toThrow('You need to define an entity');
  });

  it('should handle undefined state gracefully', async () => {
    const hassWithUndefinedState = {
      ...mockHass,
      states: {
        'sensor.test': {
          ...mockHass.states!['sensor.test'],
          state: undefined as any,
        },
      },
    };
    
    element.hass = hassWithUndefinedState as HomeAssistant;
    element.setConfig({
      type: 'custom:my-custom-card',
      entity: 'sensor.test',
    });
    await element.updateComplete;

    // Should not crash
    expect(element.shadowRoot!.querySelector('.state')).toBeTruthy();
  });
});
```

### 3. User Interaction Tests

```typescript
describe('User Interactions', () => {
  it('should call service on button click', async () => {
    element.setConfig({
      type: 'custom:my-custom-card',
      entity: 'light.test',
    });
    await element.updateComplete;

    const button = element.shadowRoot!.querySelector('button');
    button?.click();

    expect(mockHass.callService).toHaveBeenCalledWith(
      'light',
      'toggle',
      { entity_id: 'light.test' }
    );
  });

  it('should fire more-info event', async () => {
    element.setConfig({
      type: 'custom:my-custom-card',
      entity: 'sensor.test',
    });
    await element.updateComplete;

    const moreInfoSpy = jest.fn();
    element.addEventListener('hass-more-info', moreInfoSpy);

    const card = element.shadowRoot!.querySelector('ha-card');
    card?.click();

    expect(moreInfoSpy).toHaveBeenCalled();
    expect(moreInfoSpy.mock.calls[0][0].detail.entityId).toBe('sensor.test');
  });
});
```

### 4. Editor Tests

```typescript
import { MyCustomCardEditor } from '../src/editor';

describe('MyCustomCardEditor', () => {
  let element: MyCustomCardEditor;

  beforeEach(async () => {
    element = await fixture(html`<my-custom-card-editor></my-custom-card-editor>`);
    element.hass = mockHass as HomeAssistant;
  });

  it('should emit config-changed on input', async () => {
    const config = {
      type: 'custom:my-custom-card',
      entity: 'sensor.test',
    };
    element.setConfig(config);
    await element.updateComplete;

    const configChangedSpy = jest.fn();
    element.addEventListener('config-changed', configChangedSpy);

    const input = element.shadowRoot!.querySelector('ha-textfield') as any;
    input.value = 'New Name';
    input.dispatchEvent(new Event('input'));

    expect(configChangedSpy).toHaveBeenCalled();
    const newConfig = configChangedSpy.mock.calls[0][0].detail.config;
    expect(newConfig.name).toBe('New Name');
  });

  it('should handle entity picker change', async () => {
    element.setConfig({
      type: 'custom:my-custom-card',
      entity: 'sensor.test',
    });
    await element.updateComplete;

    const configChangedSpy = jest.fn();
    element.addEventListener('config-changed', configChangedSpy);

    const picker = element.shadowRoot!.querySelector('ha-entity-picker') as any;
    picker.value = 'sensor.new';
    picker.dispatchEvent(new CustomEvent('value-changed', {
      detail: { value: 'sensor.new' },
    }));

    expect(configChangedSpy).toHaveBeenCalled();
    const newConfig = configChangedSpy.mock.calls[0][0].detail.config;
    expect(newConfig.entity).toBe('sensor.new');
  });
});
```

### 5. Accessibility Tests

```typescript
import { axe, toHaveNoViolations } from 'jest-axe';

expect.extend(toHaveNoViolations);

describe('Accessibility', () => {
  it('should be accessible', async () => {
    element.setConfig({
      type: 'custom:my-custom-card',
      entity: 'sensor.test',
    });
    await element.updateComplete;

    const results = await axe(element);
    expect(results).toHaveNoViolations();
  });

  it('should have proper ARIA labels', async () => {
    element.setConfig({
      type: 'custom:my-custom-card',
      entity: 'sensor.test',
    });
    await element.updateComplete;

    const button = element.shadowRoot!.querySelector('button');
    expect(button?.getAttribute('aria-label')).toBeTruthy();
  });
});
```

## Frontend Testing Checklist

- [ ] Card renders without errors
- [ ] Displays correct entity state
- [ ] Handles missing entities
- [ ] Handles undefined/null states
- [ ] Config validation works
- [ ] Editor emits config-changed events
- [ ] All user interactions tested
- [ ] Service calls work correctly
- [ ] Event firing works (more-info, navigation)
- [ ] Responsive at different widths
- [ ] Accessible (no axe violations)
- [ ] No memory leaks (listeners cleaned up)
- [ ] Charts/heavy components destroyed
- [ ] Minimum 80% code coverage

## Advanced Testing Techniques

### Snapshot Testing
```typescript
it('should match snapshot', async () => {
  element.setConfig({
    type: 'custom:my-custom-card',
    entity: 'sensor.test',
  });
  await element.updateComplete;

  expect(element.shadowRoot!.innerHTML).toMatchSnapshot();
});
```

### Performance Testing
```typescript
it('should not cause memory leaks', async () => {
  const initialMemory = (performance as any).memory?.usedJSHeapSize;
  
  for (let i = 0; i < 1000; i++) {
    const card = await fixture(html`<my-custom-card></my-custom-card>`);
    card.remove();
  }
  
  if (global.gc) global.gc();
  
  const finalMemory = (performance as any).memory?.usedJSHeapSize;
  const growth = finalMemory - initialMemory;
  
  expect(growth).toBeLessThan(10 * 1024 * 1024); // Less than 10MB
});
```

## Coverage Requirements

- **Statements**: 80%+
- **Branches**: 80%+
- **Functions**: 80%+
- **Lines**: 80%+
- **Critical paths**: 100% (config validation, error handling)

Run coverage with:
```bash
npm test -- --coverage
```
