/**
 * Joule Sous Vide — Custom Lovelace Card
 * Version: 0.5.0
 *
 * Config:
 *   type: custom:joule-sous-vide-card
 *   title: "Joule"                  (optional)
 *   entity_switch:       switch.joule_sous_vide
 *   entity_current_temp: sensor.joule_current_temperature
 *   entity_target_temp:  number.joule_target_temperature
 *   entity_cook_time:    number.joule_cook_time
 *   entity_unit:         select.joule_temperature_unit
 */

const CARD_VERSION = "0.5.0";
console.info(
  `%c JOULE-SOUS-VIDE-CARD %c v${CARD_VERSION} `,
  "color: white; background: #03a9f4; font-weight: bold; padding: 2px 6px; border-radius: 3px 0 0 3px;",
  "color: #03a9f4; background: #e8f5e9; font-weight: bold; padding: 2px 6px; border-radius: 0 3px 3px 0;"
);

class JouleSousVideCard extends HTMLElement {
  /* ─── Lovelace lifecycle ─────────────────────────────────────── */

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  setConfig(config) {
    if (
      !config.entity_switch ||
      !config.entity_current_temp ||
      !config.entity_target_temp ||
      !config.entity_cook_time ||
      !config.entity_unit
    ) {
      throw new Error(
        "joule-sous-vide-card requires: entity_switch, entity_current_temp, " +
          "entity_target_temp, entity_cook_time, entity_unit"
      );
    }
    this._config = config;
    if (!this.shadowRoot) {
      this.attachShadow({ mode: "open" });
    }
  }

  getCardSize() {
    return 4;
  }

  /* ─── Rendering ─────────────────────────────────────────────── */

  _render() {
    if (!this._hass || !this._config) return;

    const hass = this._hass;
    const cfg = this._config;

    const switchState = hass.states[cfg.entity_switch];
    const currentTempState = hass.states[cfg.entity_current_temp];
    const targetTempState = hass.states[cfg.entity_target_temp];
    const cookTimeState = hass.states[cfg.entity_cook_time];
    const unitState = hass.states[cfg.entity_unit];

    const unavailable =
      !switchState ||
      !currentTempState ||
      !targetTempState ||
      !cookTimeState ||
      !unitState;

    const isCooking = !unavailable && switchState.state === "on";
    const currentTemp = unavailable
      ? "–"
      : parseFloat(currentTempState.state).toFixed(1);
    const targetTemp = unavailable
      ? "–"
      : parseFloat(targetTempState.state).toFixed(1);
    const cookTime = unavailable ? 0 : parseFloat(cookTimeState.state);
    const unit = unavailable
      ? "°F"
      : unitState.state;

    // Convert current temperature for display in selected unit
    const currentTempDisplay = unavailable
      ? "–"
      : unit === "°F"
      ? ((parseFloat(currentTempState.state) * 9) / 5 + 32).toFixed(1)
      : currentTemp;

    const targetMin = unavailable
      ? 32
      : parseFloat(targetTempState.attributes.min);
    const targetMax = unavailable
      ? 212
      : parseFloat(targetTempState.attributes.max);
    const targetStep = unavailable
      ? 1
      : parseFloat(targetTempState.attributes.step);

    const cookMin = unavailable ? 0 : parseFloat(cookTimeState.attributes.min);
    const cookMax = unavailable
      ? 1440
      : parseFloat(cookTimeState.attributes.max);

    const cookTimeDisplay =
      cookTime === 0 ? "∞" : `${Math.floor(cookTime / 60)}h ${cookTime % 60}m`;

    const title = cfg.title || "Joule Sous Vide";

    this.shadowRoot.innerHTML = `
      <style>
        :host {
          --card-bg: var(--ha-card-background, var(--card-background-color, white));
          --primary: var(--primary-color, #03a9f4);
          --on-primary: var(--text-primary-color, white);
          --text: var(--primary-text-color, #212121);
          --secondary-text: var(--secondary-text-color, #727272);
          --divider: var(--divider-color, #e0e0e0);
          --danger: #f44336;
          --success: #4caf50;
          --warning: #ff9800;
        }

        .card {
          background: var(--card-bg);
          border-radius: var(--ha-card-border-radius, 12px);
          box-shadow: var(--ha-card-box-shadow, 0 2px 4px rgba(0,0,0,.14));
          padding: 16px;
          font-family: var(--paper-font-body1_-_font-family, sans-serif);
          color: var(--text);
        }

        .card.unavailable {
          opacity: 0.6;
        }

        /* Header */
        .header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: 16px;
        }

        .title {
          font-size: 16px;
          font-weight: 500;
          color: var(--text);
        }

        .status-dot {
          width: 10px;
          height: 10px;
          border-radius: 50%;
          background: var(--divider);
        }

        .status-dot.cooking { background: var(--success); animation: pulse 2s infinite; }
        .status-dot.unavailable { background: var(--danger); }

        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.4; }
        }

        /* Current temperature — big display */
        .temp-display {
          text-align: center;
          padding: 12px 0 8px;
        }

        .current-temp-value {
          font-size: 52px;
          font-weight: 300;
          line-height: 1;
          color: var(--primary);
        }

        .current-temp-label {
          font-size: 12px;
          color: var(--secondary-text);
          margin-top: 2px;
        }

        /* Divider */
        hr {
          border: none;
          border-top: 1px solid var(--divider);
          margin: 12px 0;
        }

        /* Control rows */
        .control-row {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 6px 0;
        }

        .control-label {
          font-size: 13px;
          color: var(--secondary-text);
          min-width: 100px;
        }

        .stepper {
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .stepper-value {
          font-size: 15px;
          font-weight: 500;
          min-width: 60px;
          text-align: center;
        }

        button {
          cursor: pointer;
          border: none;
          border-radius: 50%;
          width: 32px;
          height: 32px;
          font-size: 18px;
          line-height: 1;
          display: inline-flex;
          align-items: center;
          justify-content: center;
          background: var(--divider);
          color: var(--text);
          transition: background 0.15s;
        }

        button:hover:not(:disabled) { background: var(--primary); color: var(--on-primary); }
        button:disabled { opacity: 0.35; cursor: default; }

        /* Unit toggle */
        .unit-toggle {
          display: flex;
          border: 1px solid var(--divider);
          border-radius: 16px;
          overflow: hidden;
          height: 28px;
        }

        .unit-btn {
          padding: 0 12px;
          font-size: 12px;
          font-weight: 500;
          border-radius: 0;
          width: auto;
          height: 100%;
          background: transparent;
          color: var(--secondary-text);
        }

        .unit-btn.active {
          background: var(--primary);
          color: var(--on-primary);
        }

        /* Start/Stop button */
        .action-row {
          margin-top: 16px;
        }

        .action-btn {
          width: 100%;
          height: 44px;
          border-radius: 22px;
          font-size: 15px;
          font-weight: 600;
          letter-spacing: 0.5px;
        }

        .action-btn.start {
          background: var(--primary);
          color: var(--on-primary);
        }

        .action-btn.stop {
          background: var(--danger);
          color: white;
        }

        .action-btn:hover:not(:disabled) {
          filter: brightness(1.1);
        }

        .unavailable-msg {
          text-align: center;
          color: var(--secondary-text);
          font-size: 13px;
          padding: 8px 0;
        }
      </style>

      <div class="card${unavailable ? " unavailable" : ""}">
        <div class="header">
          <span class="title">${title}</span>
          <span class="status-dot${
            unavailable ? " unavailable" : isCooking ? " cooking" : ""
          }"></span>
        </div>

        ${
          unavailable
            ? `<p class="unavailable-msg">Device unavailable</p>`
            : `
          <div class="temp-display">
            <div class="current-temp-value">${currentTempDisplay}${unit}</div>
            <div class="current-temp-label">Current temperature</div>
          </div>

          <hr>

          <div class="control-row">
            <span class="control-label">Target temp</span>
            <div class="stepper">
              <button id="target-down" title="Decrease">−</button>
              <span class="stepper-value">${targetTemp}${unit}</span>
              <button id="target-up" title="Increase">+</button>
            </div>
          </div>

          <div class="control-row">
            <span class="control-label">Cook time</span>
            <div class="stepper">
              <button id="time-down" title="−5 min">−</button>
              <span class="stepper-value">${cookTimeDisplay}</span>
              <button id="time-up" title="+5 min">+</button>
            </div>
          </div>

          <div class="control-row">
            <span class="control-label">Unit</span>
            <div class="unit-toggle">
              <button class="unit-btn${unit === "°F" ? " active" : ""}" id="unit-f">°F</button>
              <button class="unit-btn${unit === "°C" ? " active" : ""}" id="unit-c">°C</button>
            </div>
          </div>

          <div class="action-row">
            <button class="action-btn ${isCooking ? "stop" : "start"}" id="toggle-cooking">
              ${isCooking ? "Stop cooking" : "Start cooking"}
            </button>
          </div>
        `
        }
      </div>
    `;

    if (unavailable) return;

    // Wire up target temperature steppers
    this.shadowRoot
      .getElementById("target-down")
      .addEventListener("click", () => {
        const newVal = Math.max(targetMin, parseFloat(targetTemp) - targetStep);
        this._callService("number", "set_value", cfg.entity_target_temp, {
          value: newVal,
        });
      });

    this.shadowRoot
      .getElementById("target-up")
      .addEventListener("click", () => {
        const newVal = Math.min(targetMax, parseFloat(targetTemp) + targetStep);
        this._callService("number", "set_value", cfg.entity_target_temp, {
          value: newVal,
        });
      });

    // Wire up cook time steppers (±5 min)
    this.shadowRoot
      .getElementById("time-down")
      .addEventListener("click", () => {
        const newVal = Math.max(cookMin, cookTime - 5);
        this._callService("number", "set_value", cfg.entity_cook_time, {
          value: newVal,
        });
      });

    this.shadowRoot
      .getElementById("time-up")
      .addEventListener("click", () => {
        const newVal = Math.min(cookMax, cookTime + 5);
        this._callService("number", "set_value", cfg.entity_cook_time, {
          value: newVal,
        });
      });

    // Wire up unit toggle
    this.shadowRoot.getElementById("unit-f").addEventListener("click", () => {
      if (unit !== "°F") {
        this._callService("select", "select_option", cfg.entity_unit, {
          option: "°F",
        });
      }
    });

    this.shadowRoot.getElementById("unit-c").addEventListener("click", () => {
      if (unit !== "°C") {
        this._callService("select", "select_option", cfg.entity_unit, {
          option: "°C",
        });
      }
    });

    // Wire up start/stop
    this.shadowRoot
      .getElementById("toggle-cooking")
      .addEventListener("click", () => {
        if (isCooking) {
          this._callService("switch", "turn_off", cfg.entity_switch);
        } else {
          this._callService("switch", "turn_on", cfg.entity_switch);
        }
      });
  }

  /* ─── Helpers ───────────────────────────────────────────────── */

  _callService(domain, service, entityId, serviceData = {}) {
    this._hass.callService(domain, service, {
      entity_id: entityId,
      ...serviceData,
    });
  }
}

customElements.define("joule-sous-vide-card", JouleSousVideCard);

// Register for the Lovelace card picker (picked up by HACS and the card editor)
window.customCards = window.customCards || [];
window.customCards.push({
  type: "joule-sous-vide-card",
  name: "Joule Sous Vide",
  description:
    "Control and monitor your ChefSteps Joule directly from a Lovelace dashboard.",
  version: CARD_VERSION,
  preview: false,
  documentationURL: "https://github.com/acato/ha-joule",
});
