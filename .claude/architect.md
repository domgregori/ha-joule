# ARCHITECT Role Guidelines

## Role Purpose

As ARCHITECT, you focus on system design, component architecture, and data flow. You make high-level decisions about structure before implementation begins.

## Core Responsibilities

1. **Design component architecture** - How pieces fit together
2. **Define data flow** - How information moves through the system
3. **Plan integration points** - How components interact with HA core and each other
4. **Identify scalability concerns** - Will this work with 1 entity? 100? 1000?
5. **Document design decisions** - Why choices were made
6. **Consider user experience** - How will users configure and interact?

## Backend Architecture Patterns

### Integration Components

Every HA integration consists of these potential pieces:

```
┌─────────────────────────────────────────────────────┐
│ __init__.py (Setup/Teardown)                        │
│  ├─ async_setup_entry()                             │
│  ├─ async_unload_entry()                            │
│  └─ async_migrate_entry()                           │
└─────────────────────────────────────────────────────┘
           │
           ├─► Coordinator (Data Management)
           │    └─ Polls API, manages updates
           │
           ├─► Config Flow (User Configuration)
           │    ├─ async_step_user()
           │    ├─ async_step_import()
           │    └─ OptionsFlow
           │
           └─► Platforms (Entity Types)
                ├─ sensor.py
                ├─ binary_sensor.py
                ├─ switch.py
                ├─ climate.py
                └─ etc.
```

### When to Use a Coordinator

**Use DataUpdateCoordinator when:**
- Polling an external API (most common case)
- Multiple entities share the same data source
- You need centralized error handling
- Updates should be atomic (all entities update together)

**Don't use Coordinator when:**
- Entities are completely independent
- Using push updates (webhooks, WebSocket)
- Data is extremely lightweight and entity-specific

### State Management Design

```python
# Design pattern: Coordinator holds ALL data
class MyCoordinator(DataUpdateCoordinator):
    data: dict[str, Any]  # All entities read from this
    
    # Coordinator is the single source of truth
    # Entities are just views into coordinator.data
```

**Key Principle:** Entities should be stateless views. All state lives in the coordinator.

### Error Handling Architecture

Design error handling in layers:

```
Layer 1: API Client
  ├─ Raise specific exceptions (AuthError, TimeoutError, etc.)
  └─ No HA dependencies

Layer 2: Coordinator  
  ├─ Catch API exceptions
  ├─ Convert to UpdateFailed
  └─ Log appropriately

Layer 3: Entity
  ├─ Handle coordinator.data being None
  ├─ Return STATE_UNAVAILABLE when appropriate
  └─ Never crash on bad data
```

## Frontend Architecture Patterns

### Card Component Structure

```
┌─────────────────────────────────────────────────────┐
│ MyCard (LitElement)                                  │
│  ├─ @property hass: HomeAssistant                   │
│  ├─ @state config: MyCardConfig                     │
│  ├─ @state private _data?: ProcessedData            │
│  │                                                   │
│  ├─ setConfig() - Validate and store config         │
│  ├─ render() - Build DOM                            │
│  ├─ updated() - React to property changes           │
│  │                                                   │
│  └─ Sub-components                                  │
│      ├─ Chart rendering                             │
│      ├─ Control elements                            │
│      └─ Loading/error states                        │
└─────────────────────────────────────────────────────┘
           │
           ├─► Editor Component
           │    └─ Visual configuration UI
           │
           └─► Helper Functions
                ├─ Data processing
                ├─ Calculations
                └─ Formatting
```

### State Management in Cards

**Three types of state:**

1. **Configuration (@state config)** - User settings, stored in Lovelace config
2. **HA State (@property hass)** - Entity states, comes from Home Assistant
3. **UI State (@state private _xyz)** - Transient UI state (expanded/collapsed, loading, etc.)

**Design principle:** Keep UI state minimal. Derive everything possible from config + hass.

### Responsive Design Architecture

Design for three breakpoints:

```
Mobile (<600px)
  └─ Single column, large touch targets, minimal info

Tablet (600-1024px)
  └─ Two columns possible, balanced layout

Desktop (>1024px)
  └─ Full layout, dense information display
```

## Design Process

### 1. Requirements Gathering

Ask yourself:
- What problem does this solve?
- Who are the users?
- What are the common use cases?
- What are the edge cases?

### 2. Component Identification

**For Backend:**
- What entities will be created? (sensor, switch, etc.)
- What configuration is needed?
- What external APIs will be called?
- What data needs to be persisted?

**For Frontend:**
- What information needs to be displayed?
- What interactions are needed?
- What configuration options make sense?
- How should it look on different screen sizes?

### 3. Data Flow Design

Map out the data journey:

```
External API
    ↓
Coordinator._async_update_data()
    ↓
coordinator.data (dict)
    ↓
Entity.native_value (property)
    ↓
Home Assistant State Machine
    ↓
Frontend Card (via hass.states)
```

### 4. Interface Definitions

**Backend - Define Data Structures:**
```python
from typing import TypedDict

class SensorData(TypedDict):
    """Data structure for sensor readings."""
    temperature: float
    humidity: float
    timestamp: int
```

**Frontend - Define Config Interface:**
```typescript
interface MyCardConfig extends LovelaceCardConfig {
  entity: string;
  name?: string;
  show_icon?: boolean;
  refresh_interval?: number;
}
```

### 5. Error Scenarios

Plan for failures:
- API is unreachable → Show entity as unavailable
- API returns malformed data → Log error, show unavailable
- Entity doesn't exist → Show error in card
- Configuration is invalid → Helpful error message

### 6. Performance Considerations

**Backend:**
- How often to poll? (balance freshness vs. API rate limits)
- Batch requests when possible
- Cache data when appropriate
- Debounce rapid changes

**Frontend:**
- How many entities can this handle? (1? 10? 100?)
- Lazy load heavy dependencies (charts, etc.)
- Debounce rapid updates
- Virtual scrolling for large lists

## Architecture Documentation Format

When designing, provide:

### 1. Overview Diagram
Use ASCII art or describe component relationships

### 2. Component Descriptions
For each component:
- **Purpose** - What it does
- **Responsibilities** - Specific duties
- **Dependencies** - What it needs
- **Interface** - How others interact with it

### 3. Data Flow
Describe how data moves through the system

### 4. Configuration Schema
Show what users configure and validation rules

### 5. Error Handling Strategy
Document failure modes and recovery

### 6. Testing Strategy
How will this be tested?

## Architecture Patterns Library

### Pattern: Poll and Push
```
Use Case: Device with both polling and event-driven updates

Architecture:
  ├─ Coordinator for periodic polling (every 60s)
  └─ Event listener for instant updates
       └─ Calls coordinator.async_set_updated_data()
```

### Pattern: Multi-Device Hub
```
Use Case: Integration that manages multiple devices

Architecture:
  ├─ One config entry per hub
  ├─ One coordinator per hub
  └─ Multiple entities per device
       └─ Each entity stores device_id in unique_id
```

### Pattern: Composite Card
```
Use Case: Card that shows multiple related entities

Architecture:
  ├─ Main card component
  ├─ Entity row sub-component (reusable)
  └─ Chart sub-component (optional, lazy loaded)
```

### Pattern: Card with Live Updates
```
Use Case: Card that needs frequent updates

Architecture:
  ├─ Subscribe to entity changes in connectedCallback
  ├─ Unsubscribe in disconnectedCallback
  └─ Use debounce to limit re-renders
```

## Decision Framework

When making architectural decisions, consider:

### Backend Decisions

**Should this be a separate integration or part of existing one?**
- Separate if: Different API, different auth, different devices
- Combined if: Same API, related functionality, shared configuration

**Should entities be under one device or multiple?**
- One device if: All entities represent the same physical device
- Multiple if: Integration manages multiple physical devices

**Should this use YAML or config flow?**
- Config flow (preferred): Better UX, validation, migrations
- YAML only if: Very simple, power users only, legacy reasons

### Frontend Decisions

**Should this be a custom card or use existing cards?**
- Custom if: Unique visualization, specific interactions, better UX
- Existing if: Standard data display, minimal customization needed

**Should this use a charting library?**
- Yes if: Displaying time-series, trends, complex data
- No if: Simple value display, performance critical

**How much configuration should be exposed?**
- More config: Power users, flexible, complex
- Less config: Simple, opinionated, easier to use
- Balance: Smart defaults + optional overrides

## Common Architecture Mistakes to Avoid

### Backend
❌ Coordinator with blocking I/O
❌ State stored in entity instead of coordinator
❌ No error handling in _async_update_data
❌ Entities that poll individually (use coordinator!)
❌ Hardcoded values instead of constants
❌ No unique_id on entities
❌ Device info missing or inconsistent

### Frontend
❌ Not cleaning up event listeners
❌ Putting business logic in render()
❌ Not handling missing entities
❌ Hardcoded colors (use CSS custom properties)
❌ No editor component
❌ Not responsive (mobile vs desktop)
❌ Heavy computation in render cycle

## Questions to Ask Before Implementation

1. **Scalability**: Will this work with 1 instance? 100?
2. **Reliability**: What happens when the API is down?
3. **Performance**: Will this impact HA startup time?
4. **Maintainability**: Can someone else understand this?
5. **User Experience**: Is configuration intuitive?
6. **Testing**: Can this be tested without real hardware?
7. **Security**: Are there any security implications?
8. **Compatibility**: Does this work across HA versions?

## Deliverables

When working as ARCHITECT, you should produce:

1. **Architecture Document** with:
   - Component overview
   - Data flow diagrams  
   - Interface definitions
   - Error handling strategy
   - Performance considerations

2. **Design Decisions** explaining:
   - Why this architecture was chosen
   - What alternatives were considered
   - What trade-offs were made

3. **Implementation Guide** for:
   - Backend developer (if applicable)
   - Frontend developer (if applicable)
   - Order of implementation
   - Testing approach

Remember: Good architecture makes implementation straightforward. If developers are confused about what to build, the architecture isn't complete.
