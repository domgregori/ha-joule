# FUZZER/BREAKER Role Guidelines

## Role Purpose

As FUZZER/BREAKER, you systematically attack implementations to find edge cases, vulnerabilities, and failure modes that normal testing might miss. Your goal is to break things before users do.

## Core Responsibilities

1. Identify and test edge cases and boundary conditions
2. Inject malicious or malformed inputs
3. Stress test with extreme loads
4. Find security vulnerabilities
5. Test concurrent operations and race conditions
6. Verify proper resource cleanup
7. Document all discovered issues

## Attack Mindset

Think like an adversary:
- What would a malicious user try?
- What if the network fails right... now?
- What happens with 1000x the expected load?
- What if the API returns garbage?
- Can I make this leak memory?
- Can I bypass validation?

---

# BACKEND ATTACK VECTORS

## 1. Data Validation Attacks

### Null/None Injection
```python
import pytest
from custom_components.my_integration.coordinator import MyCoordinator

async def test_coordinator_handles_none_response(
    hass, mock_config_entry, mock_api
):
    """Test coordinator handles None from API."""
    mock_api.async_get_data.return_value = None
    
    coordinator = MyCoordinator(hass, mock_config_entry)
    await coordinator.async_config_entry_first_refresh()
    
    # Should not crash
    assert coordinator.data is None or coordinator.data == {}
    
    # Entities should handle None gracefully
    state = hass.states.get("sensor.test_temperature")
    assert state.state == STATE_UNAVAILABLE


async def test_entity_handles_missing_keys(hass, setup_integration, mock_api):
    """Test entity handles missing keys in coordinator data."""
    coordinator = hass.data[DOMAIN]["test_entry_id"]
    
    # Inject data with missing keys
    coordinator.async_set_updated_data({})
    await hass.async_block_till_done()
    
    state = hass.states.get("sensor.test_temperature")
    assert state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN, "0")
```

### Malformed Data
```python
async def test_coordinator_handles_malformed_json(
    hass, mock_config_entry, mock_api
):
    """Test coordinator handles malformed data."""
    malformed_data = [
        {"temperature": "not_a_number"},  # Wrong type
        {"temperature": float('inf')},     # Infinity
        {"temperature": float('nan')},     # NaN
        {"temperature": [1, 2, 3]},        # List instead of number
        {"temperature": {"nested": "bad"}}, # Dict instead of number
        {},                                 # Empty dict
        [],                                 # List instead of dict
        "string",                           # String instead of dict
    ]
    
    for bad_data in malformed_data:
        mock_api.async_get_data.return_value = bad_data
        
        coordinator = MyCoordinator(hass, mock_config_entry)
        
        # Should not crash
        try:
            await coordinator.async_config_entry_first_refresh()
        except UpdateFailed:
            pass  # Expected for some cases
        
        # Entities should be unavailable, not crashed
        state = hass.states.get("sensor.test_temperature")
        assert state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN)
```

### Extreme Values
```python
async def test_sensor_handles_extreme_values(hass, setup_integration):
    """Test sensor handles extreme numeric values."""
    coordinator = hass.data[DOMAIN]["test_entry_id"]
    
    extreme_values = [
        -999999999,
        999999999,
        1e308,      # Near float max
        1e-308,     # Near float min
        -0,
        0,
    ]
    
    for value in extreme_values:
        coordinator.async_set_updated_data({"temperature": value})
        await hass.async_block_till_done()
        
        state = hass.states.get("sensor.test_temperature")
        # Should not crash, state should be valid or unavailable
        assert state
```

### String Injection Attacks
```python
async def test_config_flow_sql_injection_attempt(hass, mock_api):
    """Test config flow sanitizes SQL injection attempts."""
    injection_attempts = [
        "'; DROP TABLE users;--",
        "1' OR '1'='1",
        "admin'--",
        "' UNION SELECT * FROM passwords--",
    ]
    
    for attempt in injection_attempts:
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "host": attempt,
                "api_key": attempt,
            },
        )
        
        # Should handle gracefully, not execute
        assert result["type"] in (
            data_entry_flow.RESULT_TYPE_FORM,
            data_entry_flow.RESULT_TYPE_ABORT,
        )
```

## 2. Network Failure Scenarios

### Timeout Handling
```python
import asyncio

async def test_coordinator_handles_timeout(hass, mock_config_entry, mock_api):
    """Test coordinator handles API timeouts."""
    async def timeout_side_effect():
        await asyncio.sleep(100)  # Simulate timeout
        
    mock_api.async_get_data.side_effect = timeout_side_effect
    
    coordinator = MyCoordinator(hass, mock_config_entry)
    
    with pytest.raises(UpdateFailed):
        await asyncio.wait_for(
            coordinator.async_config_entry_first_refresh(),
            timeout=5
        )


async def test_multiple_consecutive_failures(hass, mock_config_entry, mock_api):
    """Test coordinator handles multiple consecutive failures."""
    mock_api.async_get_data.side_effect = [
        Exception("Failure 1"),
        Exception("Failure 2"),
        Exception("Failure 3"),
        {"temperature": 23.5},  # Finally succeeds
    ]
    
    coordinator = MyCoordinator(hass, mock_config_entry)
    
    # First three should fail
    for _ in range(3):
        with pytest.raises(UpdateFailed):
            await coordinator.async_refresh()
    
    # Fourth should succeed
    await coordinator.async_refresh()
    assert coordinator.data == {"temperature": 23.5}
```

### Connection Errors
```python
async def test_various_connection_errors(hass, mock_config_entry, mock_api):
    """Test handling of various connection errors."""
    import aiohttp
    
    errors = [
        aiohttp.ClientConnectionError(),
        aiohttp.ClientTimeout(),
        aiohttp.ServerTimeoutError(),
        ConnectionRefusedError(),
        OSError("Network unreachable"),
    ]
    
    for error in errors:
        mock_api.async_get_data.side_effect = error
        
        coordinator = MyCoordinator(hass, mock_config_entry)
        
        with pytest.raises(UpdateFailed):
            await coordinator.async_config_entry_first_refresh()
```

## 3. Concurrency and Race Conditions

### Rapid Updates
```python
async def test_rapid_entity_updates(hass, setup_integration):
    """Test rapid successive updates don't cause issues."""
    coordinator = hass.data[DOMAIN]["test_entry_id"]
    
    # Fire 100 rapid updates
    for i in range(100):
        coordinator.async_set_updated_data({"temperature": i})
    
    await hass.async_block_till_done()
    
    # Should not crash
    state = hass.states.get("sensor.test_temperature")
    assert state
    assert float(state.state) < 100  # Got some update


async def test_concurrent_service_calls(hass, setup_integration):
    """Test concurrent service calls don't corrupt state."""
    tasks = []
    
    for i in range(50):
        task = hass.services.async_call(
            "my_integration",
            "set_value",
            {"entity_id": "sensor.test", "value": i},
            blocking=False,
        )
        tasks.append(task)
    
    await asyncio.gather(*tasks)
    await hass.async_block_till_done()
    
    # Should not crash, final state should be valid
    state = hass.states.get("sensor.test")
    assert state
```

### Setup/Teardown Stress
```python
async def test_rapid_setup_teardown(hass, mock_config_entry, mock_api):
    """Test rapid setup and teardown doesn't leak resources."""
    for _ in range(10):
        mock_config_entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()
        
        assert await hass.config_entries.async_unload(mock_config_entry.entry_id)
        await hass.async_block_till_done()
        
        # Clean up for next iteration
        hass.data[DOMAIN].pop(mock_config_entry.entry_id, None)
```

## 4. Resource Exhaustion

### Memory Leaks
```python
import gc
import sys

async def test_no_memory_leak_on_updates(hass, setup_integration, mock_api):
    """Test coordinator doesn't leak memory on updates."""
    coordinator = hass.data[DOMAIN]["test_entry_id"]
    
    # Get baseline
    gc.collect()
    initial_objects = len(gc.get_objects())
    
    # Perform 1000 updates
    for i in range(1000):
        mock_api.async_get_data.return_value = {
            "temperature": i,
            "data": "x" * 1000,  # Some bulk data
        }
        await coordinator.async_refresh()
    
    # Force garbage collection
    gc.collect()
    final_objects = len(gc.get_objects())
    
    # Object count shouldn't grow significantly
    growth = final_objects - initial_objects
    assert growth < 1000, f"Memory leak detected: {growth} objects created"
```

### File Descriptor Leaks
```python
import psutil
import os

async def test_no_file_descriptor_leak(hass, mock_config_entry, mock_api):
    """Test integration doesn't leak file descriptors."""
    process = psutil.Process(os.getpid())
    initial_fds = process.num_fds() if hasattr(process, 'num_fds') else 0
    
    # Setup and teardown 20 times
    for _ in range(20):
        mock_config_entry.add_to_hass(hass)
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()
        
        await hass.config_entries.async_unload(mock_config_entry.entry_id)
        await hass.async_block_till_done()
        
        hass.data[DOMAIN].pop(mock_config_entry.entry_id, None)
    
    final_fds = process.num_fds() if hasattr(process, 'num_fds') else 0
    
    if initial_fds > 0:
        assert final_fds - initial_fds < 10, "File descriptor leak detected"
```

## 5. Security Vulnerabilities

### Credential Exposure
```python
import logging

async def test_no_credentials_in_logs(hass, mock_config_entry, caplog):
    """Test API keys and passwords are not logged."""
    caplog.set_level(logging.DEBUG)
    
    sensitive_data = [
        "test_api_key_12345",
        "password123",
        "secret_token",
    ]
    
    mock_config_entry.data = {
        "host": "test.local",
        "api_key": sensitive_data[0],
        "password": sensitive_data[1],
    }
    
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    
    # Check logs don't contain sensitive data
    log_output = caplog.text
    for secret in sensitive_data:
        assert secret not in log_output, f"Credential '{secret}' found in logs!"
```

---

# FRONTEND ATTACK VECTORS

## 1. XSS and Injection Attacks

### HTML Injection
```typescript
describe('XSS Protection', () => {
  it('should escape HTML in entity state', async () => {
    const xssPayloads = [
      '<script>alert("xss")</script>',
      '<img src=x onerror=alert(1)>',
      '<svg/onload=alert(1)>',
      'javascript:alert(1)',
      '<iframe src="javascript:alert(1)">',
    ];

    for (const payload of xssPayloads) {
      element.hass = {
        states: {
          'sensor.test': {
            entity_id: 'sensor.test',
            state: payload,
            attributes: { friendly_name: payload },
          },
        },
      } as any;

      element.setConfig({ type: 'custom:my-card', entity: 'sensor.test' });
      await element.updateComplete;

      // Should display as text, not execute
      const content = element.shadowRoot!.textContent;
      expect(content).toContain(payload);

      // Should not create script elements
      const scripts = element.shadowRoot!.querySelectorAll('script');
      expect(scripts.length).toBe(0);
    }
  });

  it('should not use innerHTML with user data', async () => {
    element.setConfig({
      type: 'custom:my-card',
      entity: 'sensor.test',
    });
    await element.updateComplete;

    // Check that innerHTML is not used anywhere
    const html = element.shadowRoot!.innerHTML;
    
    // This is a heuristic - better to review code manually
    expect(element.innerHTML).not.toContain('<script>');
  });
});
```

### CSS Injection
```typescript
describe('CSS Injection', () => {
  it('should not allow CSS injection via config', async () => {
    const cssInjection = '"; background: url("javascript:alert(1)"); "';
    
    element.setConfig({
      type: 'custom:my-card',
      entity: 'sensor.test',
      name: cssInjection,
    });
    await element.updateComplete;

    // Should not execute JavaScript
    // Visual inspection or automated tools needed
  });
});
```

## 2. Malformed Configuration

### Invalid Entity IDs
```typescript
describe('Entity ID Fuzzing', () => {
  it('should handle malicious entity IDs', async () => {
    const maliciousIds = [
      '../../../etc/passwd',
      '../../config/secrets.yaml',
      'sensor.test"; DROP TABLE entities;--',
      'sensor.test<script>alert(1)</script>',
      '\x00\x00\x00',
      'A'.repeat(10000),
      String.fromCharCode(0),
      '${alert(1)}',
      '{{constructor.constructor("alert(1)")()}}',
    ];

    for (const entityId of maliciousIds) {
      element.hass = {
        states: {
          [entityId]: {
            entity_id: entityId,
            state: 'on',
            attributes: {},
          },
        },
      } as any;

      expect(() => {
        element.setConfig({ type: 'custom:my-card', entity: entityId });
      }).not.toThrow();

      await element.updateComplete;
      expect(element.shadowRoot).toBeTruthy();
    }
  });
});
```

### Config Pollution
```typescript
describe('Prototype Pollution', () => {
  it('should not be vulnerable to prototype pollution', async () => {
    const pollutionAttempts = [
      { type: 'custom:my-card', entity: 'sensor.test', '__proto__': { polluted: true } },
      { type: 'custom:my-card', entity: 'sensor.test', 'constructor.prototype': { polluted: true } },
    ];

    for (const config of pollutionAttempts) {
      element.setConfig(config as any);
      await element.updateComplete;

      // Check prototype wasn't polluted
      expect((Object.prototype as any).polluted).toBeUndefined();
    }
  });
});
```

## 3. Performance Attacks

### Rapid Updates
```typescript
describe('Performance Attacks', () => {
  it('should handle 1000s of rapid state changes', async () => {
    element.setConfig({
      type: 'custom:my-card',
      entity: 'sensor.test',
    });

    const start = performance.now();

    for (let i = 0; i < 1000; i++) {
      element.hass = {
        states: {
          'sensor.test': {
            entity_id: 'sensor.test',
            state: String(i),
            attributes: {},
          },
        },
      } as any;
    }

    await element.updateComplete;
    const end = performance.now();

    // Should not take more than 5 seconds
    expect(end - start).toBeLessThan(5000);
  });

  it('should handle extreme number of entities', async () => {
    const manyEntities: any = {};
    
    for (let i = 0; i < 1000; i++) {
      manyEntities[`sensor.test_${i}`] = {
        entity_id: `sensor.test_${i}`,
        state: String(i),
        attributes: {},
      };
    }

    element.hass = { states: manyEntities } as any;
    element.setConfig({
      type: 'custom:my-card',
      entities: Object.keys(manyEntities),
    } as any);

    await element.updateComplete;

    // Should render without freezing
    expect(element.shadowRoot).toBeTruthy();
  });
});
```

### Memory Leaks
```typescript
describe('Memory Leaks', () => {
  it('should not leak memory on rapid creation/destruction', async () => {
    const initialMemory = (performance as any).memory?.usedJSHeapSize;

    for (let i = 0; i < 1000; i++) {
      const card = await fixture(html`<my-custom-card></my-custom-card>`);
      card.hass = mockHass as HomeAssistant;
      card.setConfig({ type: 'custom:my-card', entity: 'sensor.test' });
      await card.updateComplete;
      card.remove();
    }

    if (global.gc) {
      global.gc();
    }

    const finalMemory = (performance as any).memory?.usedJSHeapSize;
    
    if (initialMemory && finalMemory) {
      const growth = finalMemory - initialMemory;
      expect(growth).toBeLessThan(10 * 1024 * 1024); // Less than 10MB
    }
  });

  it('should clean up event listeners', async () => {
    const card = await fixture(html`<my-custom-card></my-custom-card>`);
    card.hass = mockHass as HomeAssistant;
    card.setConfig({ type: 'custom:my-card', entity: 'sensor.test' });
    
    // Mock addEventListener to track
    const originalAdd = window.addEventListener;
    const originalRemove = window.removeEventListener;
    let listenersAdded = 0;
    let listenersRemoved = 0;
    
    window.addEventListener = ((...args: any[]) => {
      listenersAdded++;
      return originalAdd.apply(window, args as any);
    }) as any;
    
    window.removeEventListener = ((...args: any[]) => {
      listenersRemoved++;
      return originalRemove.apply(window, args as any);
    }) as any;
    
    await card.updateComplete;
    card.remove();
    
    // Cleanup should remove all listeners
    expect(listenersRemoved).toBeGreaterThanOrEqual(listenersAdded);
    
    window.addEventListener = originalAdd;
    window.removeEventListener = originalRemove;
  });
});
```

## 4. Race Conditions

### Concurrent Operations
```typescript
describe('Race Conditions', () => {
  it('should handle config changes during rendering', async () => {
    element.setConfig({
      type: 'custom:my-card',
      entity: 'sensor.test1',
    });

    // Change config while rendering
    const renderPromise = element.updateComplete;
    
    element.setConfig({
      type: 'custom:my-card',
      entity: 'sensor.test2',
    });

    await renderPromise;
    await element.updateComplete;

    // Should not crash
    expect(element.shadowRoot).toBeTruthy();
  });

  it('should handle disconnection during async operation', async () => {
    element.setConfig({
      type: 'custom:my-card',
      entity: 'sensor.test',
    });

    const updatePromise = element.updateComplete;
    
    // Disconnect immediately
    element.remove();

    // Should not throw
    await expect(updatePromise).resolves.not.toThrow();
  });
});
```

## 5. Browser Compatibility

### Old Browser Simulation
```typescript
describe('Browser Compatibility', () => {
  it('should handle lack of Shadow DOM', async () => {
    // Temporarily remove attachShadow
    const originalAttachShadow = Element.prototype.attachShadow;
    (Element.prototype as any).attachShadow = undefined;

    try {
      const card = document.createElement('my-custom-card') as MyCustomCard;
      card.hass = mockHass as HomeAssistant;
      card.setConfig({ type: 'custom:my-card', entity: 'sensor.test' });
      
      // Should fall back gracefully or polyfill
      expect(card).toBeTruthy();
    } finally {
      Element.prototype.attachShadow = originalAttachShadow;
    }
  });
});
```

## Fuzzing Checklist

### Backend
- [ ] All None/null values tested
- [ ] Empty collections tested
- [ ] Malformed API responses handled
- [ ] All timeout scenarios covered
- [ ] Rate limiting tested
- [ ] Concurrent operations safe
- [ ] No resource leaks
- [ ] No credentials in logs
- [ ] State restoration after crashes
- [ ] Extreme numeric values handled

### Frontend
- [ ] XSS attempts blocked
- [ ] HTML injection prevented
- [ ] CSS injection prevented
- [ ] Malicious entity IDs handled
- [ ] Prototype pollution prevented
- [ ] Memory leaks checked
- [ ] Event listeners cleaned up
- [ ] Rapid updates don't crash
- [ ] Concurrent operations safe
- [ ] Large datasets handled

## Tools and Techniques

### Hypothesis (Property-Based Testing)
```python
from hypothesis import given, strategies as st

@given(st.one_of(st.none(), st.text(), st.integers(), st.floats()))
async def test_entity_handles_any_value(hass, setup_integration, value):
    """Property test: entity handles any value type."""
    coordinator = hass.data[DOMAIN]["test_entry_id"]
    coordinator.async_set_updated_data({"temperature": value})
    
    # Should not crash regardless of value
    await hass.async_block_till_done()
    state = hass.states.get("sensor.test_temperature")
    assert state
```

### Chaos Engineering
```python
import random

async def test_random_failures(hass, mock_config_entry, mock_api):
    """Randomly fail API calls to test resilience."""
    call_count = 0
    
    async def random_fail(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        
        if random.random() < 0.3:  # 30% failure rate
            raise Exception("Random failure")
        return {"temperature": call_count}
    
    mock_api.async_get_data.side_effect = random_fail
    
    coordinator = MyCoordinator(hass, mock_config_entry)
    
    # Should eventually succeed despite random failures
    for _ in range(20):
        try:
            await coordinator.async_refresh()
        except UpdateFailed:
            pass
    
    # At least some updates should have succeeded
    assert call_count > 0
```

Remember: The goal is not just to break things, but to find and document failure modes so they can be handled gracefully!
