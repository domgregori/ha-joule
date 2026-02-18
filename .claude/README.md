# Claude Code Initialization Files for Home Assistant Development

This directory contains a complete set of initialization files for Claude Code to help you develop Home Assistant integrations and custom Lovelace cards with expert-level guidance.

## Files Overview

### `init` - Main Initialization File
- **Purpose**: Core project context, always loaded when Claude Code starts
- **Contains**: Project overview, role definitions, common patterns, resources
- **Usage**: This is automatically loaded - you don't need to reference it explicitly

### `architect.md` - Architecture Role
- **Purpose**: System design, component architecture, data flow planning
- **When to use**: "As ARCHITECT, design the data flow for my thermostat integration"
- **Focus**: High-level design, component interactions, UX planning, performance considerations

### `developer.md` - Developer Role (Backend & Frontend)
- **Purpose**: Implementation patterns for both Python integrations and TypeScript cards
- **When to use**: 
  - "As BACKEND DEVELOPER, implement the coordinator"
  - "As FRONTEND DEVELOPER, create the custom card"
- **Focus**: Code patterns, best practices, proper async usage, HA design system

### `sdet.md` - Testing Role
- **Purpose**: Comprehensive testing strategies for both backend and frontend
- **When to use**: "As SDET, create tests for the config flow"
- **Focus**: Test coverage, fixtures, integration tests, test patterns

### `fuzzer.md` - Security/Breaking Role
- **Purpose**: Attack vectors, edge cases, security vulnerabilities
- **When to use**: "As FUZZER, try to break the temperature validation"
- **Focus**: XSS prevention, data validation, memory leaks, race conditions

## How to Use

### 1. Copy to Your Project

Copy this entire `.claude` directory to the root of your Home Assistant project:

```bash
cp -r .claude /path/to/your/ha-project/
```

### 2. Start Claude Code

Navigate to your project directory and start Claude Code:

```bash
cd /path/to/your/ha-project
claude
```

The `init` file will be automatically loaded.

### 3. Use Role-Based Commands

When interacting with Claude Code, specify which role you want:

```bash
# Architecture phase
claude "As ARCHITECT, design a custom integration for my Ecobee thermostat"

# Implementation phase
claude "As BACKEND DEVELOPER, implement the coordinator from the architecture"

# Testing phase
claude "As SDET, create comprehensive tests for the coordinator"

# Breaking phase
claude "As FUZZER, attack the config flow with malicious inputs"
```

## Workflow Examples

### Backend Integration Workflow

```bash
# 1. Design
claude "As ARCHITECT, I need to integrate a device with REST API that polls every 30 seconds for temperature and humidity data"

# 2. Implement
claude "As BACKEND DEVELOPER, implement the integration based on the architecture"

# 3. Test
claude "As SDET, create tests for the integration"

# 4. Break
claude "As FUZZER, try to break the API error handling"

# 5. Refine
claude "Review all code and ensure it follows Home Assistant best practices"
```

### Frontend Card Workflow

```bash
# 1. Design
claude "As ARCHITECT, design a custom gauge card that shows temperature with color gradients and historical trend"

# 2. Implement
claude "As FRONTEND DEVELOPER, implement the gauge card with Lit and Chart.js"

# 3. Test
claude "As SDET, create Jest tests for the gauge card"

# 4. Break
claude "As FUZZER, test for XSS vulnerabilities and memory leaks"

# 5. Polish
claude "Optimize performance and ensure responsive design"
```

### Full-Stack Workflow

```bash
# Backend
claude "As ARCHITECT, design backend integration for smart blinds with position and tilt control"
claude "As BACKEND DEVELOPER, implement the integration"
claude "As SDET, test the integration"

# Frontend
claude "As ARCHITECT, design a custom card to control the blinds with sliders"
claude "As FRONTEND DEVELOPER, implement the blinds control card"
claude "As SDET, test the card"

# Integration
claude "Test the backend and frontend working together"
claude "As FUZZER, stress test the complete system"
```

## Role Transitions

Claude will naturally apply the appropriate context when you switch roles. You can also combine roles:

```bash
claude "As ARCHITECT and BACKEND DEVELOPER, design and implement the sensor platform"
```

## Best Practices

### 1. Start with Architecture
Always begin with the ARCHITECT role to plan before implementing.

### 2. Test as You Go
Use SDET role immediately after implementing each component.

### 3. Break It Early
Use FUZZER role before considering code complete.

### 4. Document Decisions
Ask Claude to update the init file or create additional .md files with learned patterns.

### 5. Role-Specific Focus
Stay in one role at a time for cleaner context and better results.

## Customization

You can customize these files for your specific needs:

### Add Project-Specific Patterns
Edit `init` to add patterns you use frequently:

```markdown
## Custom Patterns

### Our Standard Sensor Structure
```python
# Your team's preferred pattern
```
```

### Add Domain Knowledge
Create new .md files for specific domains:

```bash
# Create a new role file
echo "# ENERGY EXPERT Role" > .claude/energy-expert.md
```

Then reference it:
```bash
claude "As ENERGY EXPERT, review my solar integration"
```

### Team Standards
Update `developer.md` with your team's specific standards:
- Naming conventions
- Error handling patterns
- Logging preferences
- Testing requirements

## File Structure in Your Project

```
your-ha-project/
├── .claude/
│   ├── init                    # Main initialization (auto-loaded)
│   ├── architect.md            # Architecture role
│   ├── developer.md            # Backend & Frontend development
│   ├── sdet.md                 # Testing role
│   └── fuzzer.md               # Security/breaking role
├── custom_components/          # Your Python integration
│   └── your_integration/
├── custom_cards/               # Your frontend cards (if any)
│   └── your_card/
└── tests/                      # Test suites
    ├── integration/            # Python tests
    └── cards/                  # JavaScript tests
```

## Troubleshooting

### Claude doesn't seem to apply role context
- Make sure you're using the exact phrase "As ROLE" (case-insensitive)
- Verify the .claude directory is in your project root
- Check that Claude Code is started from the project directory

### Need more context for a specific task
- Reference role files explicitly: "Review the ARCHITECT guidelines and design..."
- Combine roles: "As ARCHITECT and DEVELOPER..."
- Create custom role files for specialized domains

### Want to disable certain guidance
- Comment out sections in the .md files using HTML comments
- Or create a minimal init file with only what you need

## Additional Resources

The init file contains links to:
- Home Assistant Developer Docs
- Lit Documentation
- Testing Libraries
- Example Integrations

Review these for deeper understanding of the patterns used in these files.

## Updates and Maintenance

These files represent best practices as of February 2025. As Home Assistant evolves:

1. **Monitor HA Releases** - Update patterns for new HA features
2. **Refine Based on Experience** - Add patterns you discover
3. **Share Improvements** - Contribute back patterns that work well
4. **Version Control** - Keep .claude files in your repo

## Getting Help

If you're stuck:

1. Ask Claude to review the appropriate role file
2. Request examples: "Show me an example of the coordinator pattern from developer.md"
3. Ask for clarification: "Explain the testing strategy from sdet.md"
4. Combine with web search: "Search for latest HA integration best practices and update our guidelines"

## Credits

These files were generated to provide comprehensive, role-based guidance for Home Assistant development, incorporating official HA developer documentation, community best practices, and security considerations.

Happy developing! 🏠✨
