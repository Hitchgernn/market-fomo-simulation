# Pixel Trading Terminal Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesign the existing vanilla frontend into a cyberpunk pixel-noir trading dashboard while preserving all backend APIs, data models, controls, and market terminology.

**Architecture:** Keep the existing vanilla HTML/CSS/JS structure. Replace the current card/sidebar layout with a trading-first CSS grid: top stat strip, main row with square `Graph`, wider `Live Market`, right-side controls/events/chat, and bottom `Order Book`. Keep p5.js for Mesa network graph and Chart.js for market chart; only restyle and adjust layout/rendering.

**Tech Stack:** Vanilla HTML, CSS custom properties, p5.js, Chart.js, FastAPI backend endpoints (`/state`, `/tick`, `/reset`), online Google Fonts/pixel assets.

---

## File structure

- Modify `frontend/index.html`: replace page CSS and markup structure; keep script imports and all element IDs used by `frontend/sketch.js`.
- Modify `frontend/sketch.js`: keep API calls and control behavior; adjust canvas sizing, chart styling, status labels, loading/error handling, and preserve readable Mesa graph rendering.
- No backend files change.
- No new production files required.

## Required implementation constraints

- Keep IDs referenced by JS: `network-canvas`, `market-chart`, `tick-label`, `price-value`, `imbalance-value`, `neutral-count`, `aware-count`, `panic-count`, `market-regime`, `buy-volume`, `sell-volume`, `upper-limit-value`, `lower-limit-value`, `limit-state`, `buy-bar`, `sell-bar`, `price-band`, `limit-bar`, `status-light`, `api-status`, `event-feed`, `event-count`, `chat-feed`, `chat-count`, all input IDs, preset buttons, run/step/apply buttons.
- Keep labels: `Graph`, `Live Market`, `Order Book`, `Controls`, `Market Events`, `Market Chat`.
- Keep backend endpoints unchanged.
- Use online asset only for visual polish, e.g. Google Fonts import.
- Commit after major frontend redesign, no `Co-Authored-By` trailer.

---

### Task 1: Rewrite frontend layout and pixel design system

**Files:**
- Modify: `frontend/index.html`

- [ ] **Step 1: Replace Google/CDN head assets with pixel font plus existing libraries**

In `frontend/index.html`, keep Chart.js and p5.js scripts, add Google Fonts preconnect/import for `Press Start 2P` and `Share Tech Mono`:

```html
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Press+Start+2P&family=Share+Tech+Mono&display=swap" rel="stylesheet" />
<link rel="preconnect" href="https://cdn.jsdelivr.net" />
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/p5@1.9.4/lib/p5.min.js"></script>
```

- [ ] **Step 2: Replace CSS variables and base styles**

Replace the existing `<style>` content with CSS that defines 8px grid tokens and pixel components. Use this complete style block as the implementation target:

```css
:root {
  color-scheme: dark;
  --bg: #070914;
  --panel: #0b1020;
  --panel-soft: #101828;
  --panel-deep: #05070d;
  --grid: #17213a;
  --line: #273653;
  --text: #e8f7ff;
  --muted: #8ca3b8;
  --cyan: #00bbf9;
  --mint: #00f5d4;
  --magenta: #f15bb5;
  --yellow: #fee440;
  --red: #ff4d6d;
  --violet: #9b5de5;
  --shadow: #000;
  --space-1: 8px;
  --space-2: 16px;
  --space-3: 24px;
  --space-4: 32px;
  --font-pixel: "Press Start 2P", monospace;
  --font-body: "Share Tech Mono", ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}

* {
  box-sizing: border-box;
}

html {
  background: var(--bg);
}

body {
  margin: 0;
  min-height: 100vh;
  background:
    linear-gradient(rgb(7 9 20 / 92%), rgb(7 9 20 / 92%)),
    repeating-linear-gradient(0deg, transparent 0 6px, rgb(255 255 255 / 4%) 6px 8px),
    radial-gradient(circle at 20% 0%, rgb(0 245 212 / 16%), transparent 32%),
    radial-gradient(circle at 90% 10%, rgb(241 91 181 / 18%), transparent 28%),
    var(--bg);
  color: var(--text);
  font-family: var(--font-body);
  image-rendering: pixelated;
}

body::before {
  content: "";
  position: fixed;
  inset: 0;
  pointer-events: none;
  background: repeating-linear-gradient(0deg, transparent 0 5px, rgb(255 255 255 / 5%) 5px 6px);
  mix-blend-mode: screen;
  opacity: 0.35;
  animation: scanline-scroll 8s linear infinite;
  z-index: 10;
}

button,
input {
  font: inherit;
}

button:focus-visible,
input:focus-visible {
  outline: 3px dashed var(--yellow);
  outline-offset: 3px;
}

.shell {
  display: grid;
  grid-template-rows: auto minmax(420px, 1fr) auto;
  gap: var(--space-2);
  min-height: 100vh;
  padding: var(--space-2);
}

.pixel-panel,
.topbar,
.network-panel,
.chart-panel,
.metrics-panel,
.control-panel,
.event-panel,
.chat-panel {
  border: 4px solid var(--line);
  border-radius: 0;
  background: var(--panel);
  box-shadow: 8px 8px 0 var(--shadow);
}

.topbar {
  display: grid;
  grid-template-columns: minmax(240px, 1.4fr) repeat(6, minmax(112px, 1fr));
  gap: var(--space-1);
  align-items: stretch;
  padding: var(--space-1);
  border-color: var(--cyan);
}

.brand {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: var(--space-1);
  min-width: 0;
  padding: var(--space-1);
  background: var(--panel-soft);
  border: 3px solid var(--line);
}

.brand h1,
.panel-header h2,
.chat-header h2 {
  margin: 0;
  font-family: var(--font-pixel);
  font-size: 12px;
  line-height: 1.5;
  letter-spacing: 0;
  text-transform: uppercase;
}

.brand span,
.metric span,
.chat-meta,
.status,
label {
  color: var(--muted);
  font-size: 14px;
}

.metric {
  min-width: 0;
  padding: var(--space-1);
  background: var(--panel-soft);
  border: 3px solid var(--line);
  box-shadow: 4px 4px 0 var(--shadow);
}

.metric strong {
  display: block;
  margin-top: var(--space-1);
  color: var(--text);
  font-family: var(--font-pixel);
  font-size: 12px;
  line-height: 1.5;
  word-break: break-word;
}

.metric .up,
.up {
  color: var(--mint);
}

.metric .down,
.down {
  color: var(--red);
}

.dashboard-grid {
  display: grid;
  grid-template-columns: minmax(280px, 0.95fr) minmax(360px, 1.35fr) 360px;
  gap: var(--space-2);
  min-height: 0;
}

.network-panel,
.chart-panel,
.control-panel,
.event-panel,
.chat-panel,
.metrics-panel {
  min-width: 0;
  overflow: hidden;
}

.network-panel {
  display: grid;
  grid-template-rows: auto minmax(280px, 1fr) auto;
  border-color: var(--cyan);
}

.chart-panel {
  display: grid;
  grid-template-rows: auto minmax(320px, 1fr);
  border-color: var(--mint);
  padding: var(--space-2);
}

.side {
  display: grid;
  grid-template-rows: auto minmax(180px, 1fr) minmax(180px, 1fr);
  gap: var(--space-2);
  min-height: 0;
}

.panel-header,
.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-1);
  padding: var(--space-2);
  border-bottom: 3px solid var(--line);
  background: var(--panel-soft);
}

.chart-panel .panel-header {
  padding: 0 0 var(--space-2);
  border-bottom: 0;
  background: transparent;
}

.network-stage {
  position: relative;
  min-height: 280px;
  background:
    linear-gradient(rgb(8 13 24 / 94%), rgb(8 13 24 / 94%)),
    linear-gradient(var(--grid) 1px, transparent 1px),
    linear-gradient(90deg, var(--grid) 1px, transparent 1px);
  background-size: auto, 24px 24px, 24px 24px;
  border-top: 3px solid var(--line);
  border-bottom: 3px solid var(--line);
}

#network-canvas {
  position: absolute;
  inset: 0;
}

.legend {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-1);
  padding: var(--space-1);
  background: var(--panel-soft);
}

.legend-item {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  color: var(--muted);
  font-size: 13px;
}

.dot {
  width: 10px;
  height: 10px;
  border-radius: 0;
  box-shadow: 2px 2px 0 var(--shadow);
}

.chart-wrap {
  position: relative;
  min-height: 0;
  background:
    linear-gradient(rgb(5 7 13 / 94%), rgb(5 7 13 / 94%)),
    linear-gradient(var(--grid) 1px, transparent 1px),
    linear-gradient(90deg, var(--grid) 1px, transparent 1px);
  background-size: auto, 32px 32px, 32px 32px;
  border: 3px solid var(--line);
  padding: var(--space-1);
}

.metrics-panel {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--space-1);
  padding: var(--space-1);
  border-color: var(--violet);
}

.bar {
  height: 12px;
  margin-top: var(--space-1);
  overflow: hidden;
  background: var(--panel-deep);
  border: 2px solid var(--line);
}

.bar div {
  width: 50%;
  height: 100%;
  background: repeating-linear-gradient(90deg, var(--mint) 0 8px, transparent 8px 12px);
}

.control-panel {
  border-color: var(--yellow);
}

.event-panel {
  display: grid;
  grid-template-rows: auto minmax(0, 1fr);
  border-color: var(--red);
}

.chat-panel {
  display: grid;
  grid-template-rows: auto minmax(0, 1fr);
  border-color: var(--magenta);
}

.preset-row,
.button-row {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--space-1);
  padding: var(--space-1) var(--space-2);
}

.control-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-1);
  padding: var(--space-2);
}

.field {
  display: grid;
  gap: 4px;
  min-width: 0;
}

input {
  width: 100%;
  min-height: 40px;
  padding: var(--space-1);
  color: var(--text);
  background: var(--panel-deep);
  border: 3px solid var(--line);
  border-radius: 0;
}

input[type="checkbox"] {
  width: 20px;
  min-height: 20px;
  accent-color: var(--red);
}

.toggle-field {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 40px;
  padding: var(--space-1);
  background: var(--panel-deep);
  border: 3px solid var(--line);
}

button {
  min-height: 40px;
  color: var(--text);
  background: var(--panel-soft);
  border: 3px solid var(--line);
  border-radius: 0;
  box-shadow: 4px 4px 0 var(--shadow);
  cursor: pointer;
  transition: transform 80ms linear, box-shadow 80ms linear, border-color 80ms linear;
}

button:hover {
  border-color: var(--mint);
}

button:active {
  transform: translate(2px, 2px);
  box-shadow: 2px 2px 0 var(--shadow);
}

button.primary {
  color: var(--panel-deep);
  background: var(--mint);
  border-color: var(--mint);
  font-weight: 700;
}

#event-feed,
#chat-feed {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  min-height: 0;
  overflow: auto;
  padding: var(--space-2);
}

.event-message,
.chat-message {
  padding: var(--space-1);
  background: var(--panel-soft);
  border: 3px solid var(--line);
  box-shadow: 4px 4px 0 var(--shadow);
}

.event-message.danger {
  border-color: var(--red);
}

.event-message.warning {
  border-color: var(--yellow);
}

.event-message.success {
  border-color: var(--mint);
}

.event-message p,
.chat-message p {
  margin: 4px 0 0;
  color: var(--text);
  font-size: 14px;
  line-height: 1.35;
}

.status {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  white-space: nowrap;
}

.status-light {
  width: 10px;
  height: 10px;
  background: var(--yellow);
  box-shadow: 2px 2px 0 var(--shadow);
}

.status-light.online {
  background: var(--mint);
  animation: pixel-blink 1s steps(2, end) infinite;
}

.status-light.offline {
  background: var(--red);
}

@keyframes pixel-blink {
  50% { opacity: 0.35; }
}

@keyframes scanline-scroll {
  from { transform: translateY(0); }
  to { transform: translateY(8px); }
}

@media (max-width: 1180px) {
  .topbar,
  .metrics-panel,
  .dashboard-grid {
    grid-template-columns: 1fr 1fr;
  }

  .brand,
  .chart-panel,
  .side {
    grid-column: 1 / -1;
  }

  .side {
    grid-template-columns: 1fr 1fr;
    grid-template-rows: auto auto;
  }

  .control-panel {
    grid-column: 1 / -1;
  }
}

@media (max-width: 760px) {
  .shell {
    padding: var(--space-1);
  }

  .topbar,
  .dashboard-grid,
  .metrics-panel,
  .side,
  .control-grid,
  .preset-row,
  .button-row {
    grid-template-columns: 1fr;
  }

  .brand,
  .chart-panel,
  .side,
  .control-panel {
    grid-column: auto;
  }

  .network-panel,
  .chart-panel {
    min-height: 360px;
  }
}
```

- [ ] **Step 3: Replace body markup with trading-first structure**

In `frontend/index.html`, replace everything inside `<body>` except final `<script src="./sketch.js"></script>` with this structure. It preserves required IDs and labels:

```html
<div class="shell">
  <section class="topbar" aria-label="Market status">
    <div class="brand">
      <h1>FOMO Market Simulation</h1>
      <span id="tick-label">Tick 0</span>
    </div>
    <div class="metric"><span>Price</span><strong id="price-value">--</strong></div>
    <div class="metric"><span>Imbalance</span><strong id="imbalance-value">--</strong></div>
    <div class="metric"><span>Neutral</span><strong id="neutral-count">--</strong></div>
    <div class="metric"><span>Aware</span><strong id="aware-count">--</strong></div>
    <div class="metric"><span>Panic</span><strong id="panic-count">--</strong></div>
    <div class="metric"><span>Regime</span><strong id="market-regime">--</strong></div>
  </section>

  <main class="dashboard-grid">
    <section class="network-panel" aria-label="Graph">
      <div class="panel-header">
        <h2>Graph</h2>
        <span class="status">Mesa Network</span>
      </div>
      <div class="network-stage">
        <div id="network-canvas"></div>
      </div>
      <div class="legend" aria-label="Agent state legend">
        <span class="legend-item"><span class="dot" style="background: var(--mint)"></span>Neutral</span>
        <span class="legend-item"><span class="dot" style="background: var(--yellow)"></span>Aware</span>
        <span class="legend-item"><span class="dot" style="background: var(--red)"></span>Panic</span>
      </div>
    </section>

    <section class="chart-panel" aria-label="Live Market">
      <div class="panel-header">
        <h2>Live Market</h2>
        <span id="history-label" class="status">0 samples</span>
      </div>
      <div class="chart-wrap">
        <canvas id="market-chart"></canvas>
      </div>
    </section>

    <aside class="side">
      <section class="control-panel" aria-label="Controls">
        <div class="panel-header">
          <h2>Controls</h2>
          <span class="status"><span id="status-light" class="status-light"></span><span id="api-status">Connecting</span></span>
        </div>
        <div class="control-grid">
          <label class="field">Retail Agents<input id="numRetail" type="number" min="0" max="1000" step="1" value="100" /></label>
          <label class="field">Institutional<input id="numInstitutional" type="number" min="0" max="100" step="1" value="5" /></label>
          <label class="field">Base Price<input id="basePrice" type="number" min="1" step="1" value="100" /></label>
          <label class="field">Beta<input id="beta" type="number" min="0" max="1" step="0.01" value="0.15" /></label>
          <label class="field">Price Impact<input id="priceImpact" type="number" min="0" max="1" step="0.005" value="0.02" /></label>
          <label class="field">Tick Speed ms<input id="tickSpeed" type="number" min="150" max="10000" step="50" value="1200" /></label>
          <label class="field">Aware Fraction<input id="initialAwareFraction" type="number" min="0" max="1" step="0.01" value="0.10" /></label>
          <label class="field">Panic Fraction<input id="initialPanicFraction" type="number" min="0" max="1" step="0.01" value="0.05" /></label>
          <label class="field">Upper Limit %<input id="upperLimitPercent" type="number" min="0" max="1" step="0.01" value="0.25" /></label>
          <label class="field">Lower Limit %<input id="lowerLimitPercent" type="number" min="0" max="1" step="0.01" value="0.15" /></label>
          <label class="field">Shock Enabled<span class="toggle-field"><span>Market maker dump</span><input id="shockEnabled" type="checkbox" /></span></label>
          <label class="field">Shock Probability<input id="shockProbability" type="number" min="0" max="1" step="0.01" value="0" /></label>
          <label class="field">Shock Cooldown<input id="shockCooldownTicks" type="number" min="0" max="1000" step="1" value="5" /></label>
          <label class="field">Shock Min Vol<input id="shockMinVolume" type="number" min="1" step="1" value="25" /></label>
          <label class="field">Shock Max Vol<input id="shockMaxVolume" type="number" min="1" step="1" value="80" /></label>
          <label class="field">Panic Drawdown<input id="panicDrawdownThreshold" type="number" min="0" max="1" step="0.005" value="0.05" /></label>
          <label class="field">Panic Sensitivity<input id="panicSensitivity" type="number" min="0" max="1000" step="1" value="8" /></label>
          <label class="field">Panic Sell Mult<input id="panicSellMultiplier" type="number" min="1" max="1000" step="1" value="3" /></label>
        </div>
        <div class="preset-row">
          <button id="preset-fomo" type="button">FOMO Pump</button>
          <button id="preset-dump" type="button">Maker Dump</button>
          <button id="preset-lower-limit" type="button">Lower Limit Spiral</button>
        </div>
        <div class="button-row">
          <button id="run-toggle" type="button">Pause</button>
          <button id="step-button" type="button">Step</button>
          <button id="apply-button" class="primary" type="button">Apply</button>
        </div>
      </section>

      <section class="event-panel" aria-label="Market Events">
        <div class="panel-header">
          <h2>Market Events</h2>
          <span id="event-count" class="status">0 events</span>
        </div>
        <div id="event-feed"></div>
      </section>

      <section class="chat-panel" aria-label="Market Chat">
        <div class="chat-header">
          <h2>Market Chat</h2>
          <span id="chat-count" class="status">0 messages</span>
        </div>
        <div id="chat-feed"></div>
      </section>
    </aside>
  </main>

  <section class="metrics-panel" aria-label="Order Book">
    <div class="metric">
      <span>Buy Volume</span>
      <strong id="buy-volume">--</strong>
      <div class="bar"><div id="buy-bar"></div></div>
    </div>
    <div class="metric">
      <span>Sell Volume</span>
      <strong id="sell-volume">--</strong>
      <div class="bar"><div id="sell-bar"></div></div>
    </div>
    <div class="metric">
      <span>Upper / Lower</span>
      <strong><span id="upper-limit-value">--</span> / <span id="lower-limit-value">--</span></strong>
      <div class="bar"><div id="price-band"></div></div>
    </div>
    <div class="metric">
      <span>Limit State</span>
      <strong id="limit-state">Clear</strong>
      <div class="bar"><div id="limit-bar"></div></div>
    </div>
  </section>
</div>
```

- [ ] **Step 4: Run HTML smoke check**

Run:

```bash
grep -o 'id="[^"]*"' frontend/index.html | sort
```

Expected: output includes all existing IDs listed in Required implementation constraints. No missing IDs.

---

### Task 2: Restyle Chart.js and make Live Market readable

**Files:**
- Modify: `frontend/sketch.js`

- [ ] **Step 1: Update chart colors and axis styling**

In `initChart()`, update dataset and options colors to match pixel terminal. Keep existing dataset structure. Use these values:

```js
borderColor: "#00f5d4",
backgroundColor: "rgb(0 245 212 / 12%)",
```

for price line, buy bar:

```js
backgroundColor: "rgb(0 245 212 / 42%)",
borderColor: "#00f5d4",
```

sell bar:

```js
backgroundColor: "rgb(255 77 109 / 38%)",
borderColor: "#ff4d6d",
```

Set chart option colors:

```js
plugins: {
  legend: {
    labels: { color: "#8ca3b8", boxWidth: 12, boxHeight: 12, font: { family: "Share Tech Mono" } },
  },
},
scales: {
  x: {
    ticks: { color: "#8ca3b8", maxTicksLimit: 8, font: { family: "Share Tech Mono" } },
    grid: { color: "#17213a" },
  },
  price: {
    position: "left",
    ticks: { color: "#8ca3b8", font: { family: "Share Tech Mono" } },
    grid: { color: "#17213a" },
  },
  volume: {
    position: "right",
    beginAtZero: true,
    ticks: { color: "#8ca3b8", font: { family: "Share Tech Mono" } },
    grid: { drawOnChartArea: false },
  },
},
```

- [ ] **Step 2: Update point colors**

In `updateChart()`, use pixel palette:

```js
marketChart.data.datasets[0].pointBackgroundColor = history.map((sample) => {
  if (sample.lowerLimitTriggered) {
    return "#ff4d6d";
  }
  if (sample.hasDump) {
    return "#f15bb5";
  }
  if (sample.upperLimitTriggered) {
    return "#00f5d4";
  }
  return "#00bbf9";
});
```

- [ ] **Step 3: Run frontend syntax check**

Run:

```bash
node --check frontend/sketch.js
```

Expected: `frontend/sketch.js` has no syntax errors.

---

### Task 3: Keep Mesa Graph readable in new square panel

**Files:**
- Modify: `frontend/sketch.js`

- [ ] **Step 1: Adjust graph drawing colors only**

In `draw()`, `drawGrid()`, `drawConnections()`, `drawPulses()`, and `drawNodes()`, keep node positions and connection logic. Update colors only:

```js
function draw() {
  background("#080d18");
  drawGrid();
  drawConnections();
  drawPulses();
  drawNodes();
}

function drawGrid() {
  stroke("#17213a");
  strokeWeight(1);
  for (let x = 0; x < width; x += 24) {
    line(x, 0, x, height);
  }
  for (let y = 0; y < height; y += 24) {
    line(0, y, width, y);
  }
}

function drawConnections() {
  stroke("#40506d");
  strokeWeight(1.5);
  for (const node of nodes) {
    for (const targetId of node.connections) {
      if (node.id > targetId) {
        continue;
      }
      const target = nodeMap.get(targetId);
      if (!target) {
        continue;
      }
      line(node.x, node.y, target.x, target.y);
    }
  }
}
```

- [ ] **Step 2: Update node drawing without pixelizing graph**

Replace `drawNodes()` with readable circular network nodes:

```js
function drawNodes() {
  textAlign(CENTER, CENTER);
  textSize(10);
  for (const node of nodes) {
    const size = node.state === "P" ? 16 : node.state === "A" ? 13 : 11;
    stroke("#05070d");
    strokeWeight(2);
    fill(node.color);
    circle(node.x, node.y, size);
    noStroke();
    fill("#e8f7ff");
    text(node.id, node.x, node.y - 16);
  }
}
```

- [ ] **Step 3: Update API state colors to palette-compatible values**

In `frontend/sketch.js`, no API color source exists. Colors come from backend `STATE_COLORS`. In `ingestPayload()`, map backend colors to frontend palette without changing payload shape:

```js
const STATE_PALETTE = {
  N: "#00f5d4",
  A: "#fee440",
  P: "#ff4d6d",
};
```

Place near constants. Then in node mapping:

```js
color: STATE_PALETTE[node.state] || node.color,
```

- [ ] **Step 4: Run frontend syntax check**

Run:

```bash
node --check frontend/sketch.js
```

Expected: no syntax errors.

---

### Task 4: Add pixel loading/offline/error feedback without changing API logic

**Files:**
- Modify: `frontend/sketch.js`
- Modify: `frontend/index.html`

- [ ] **Step 1: Add status text helper behavior**

Update `setStatus(label, stateClass)` in `frontend/sketch.js` to keep existing API status but allow pixel terminal language:

```js
function setStatus(label, stateClass) {
  setText("api-status", label);
  const light = document.getElementById("status-light");
  light.className = `status-light ${stateClass}`;
}
```

This function may already match. If unchanged, leave it as-is.

- [ ] **Step 2: Keep failure labels explicit**

Confirm catch blocks use these labels:

```js
setStatus("Offline", "offline");
setStatus("Reset failed", "offline");
setStatus("Invalid mix", "offline");
```

Do not replace them with game terms like `GAME OVER`.

- [ ] **Step 3: Add empty states in markup**

In `frontend/index.html`, inside `#event-feed` and `#chat-feed`, keep them empty initially because JS uses `replaceChildren()` and `prepend()`. Do not add permanent child nodes that would affect counters.

- [ ] **Step 4: Run syntax check**

Run:

```bash
node --check frontend/sketch.js
```

Expected: no syntax errors.

---

### Task 5: Full verification and commit

**Files:**
- Modified: `frontend/index.html`
- Modified: `frontend/sketch.js`

- [ ] **Step 1: Run backend compile check**

Run:

```bash
python -m compileall backend
```

Expected: compile succeeds.

- [ ] **Step 2: Run frontend syntax check**

Run:

```bash
node --check frontend/sketch.js
```

Expected: no syntax errors.

- [ ] **Step 3: Start backend**

Run:

```bash
GEMINI_API_KEY= GEMINI_API_KEYS= uvicorn backend.api.server:app --host 127.0.0.1 --port 8000 --reload
```

Expected: Uvicorn starts and listens on `127.0.0.1:8000`.

- [ ] **Step 4: Start frontend**

Run in separate shell:

```bash
python -m http.server 5501 --directory frontend
```

Expected: frontend server starts and serves `http://127.0.0.1:5501`.

- [ ] **Step 5: Manual browser verification**

Open `http://127.0.0.1:5501`. Verify:

- Top stat strip displays values after `/state`.
- `Graph` panel is left, square-ish, and shows readable Mesa network graph.
- `Live Market` panel is center, wider than graph, and chart is visible.
- `Controls` remain usable.
- `Run/Pause`, `Step`, and `Apply` work.
- `FOMO Pump`, `Maker Dump`, and `Lower Limit Spiral` work.
- `Order Book` shows buy/sell/limits/limit state.
- `Market Events` receives events during shock presets.
- `Market Chat` remains empty without Gemini key and layout does not break.
- Mobile/narrow layout stacks: stats, Graph, Live Market, Controls, Order Book, events, chat.

- [ ] **Step 6: Inspect diff**

Run:

```bash
git diff -- frontend/index.html frontend/sketch.js
```

Expected: only frontend presentation changes; no backend changes.

- [ ] **Step 7: Commit frontend redesign**

Run:

```bash
git add frontend/index.html frontend/sketch.js
git commit -m "feat(frontend): redesign pixel trading terminal"
```

Expected: commit created with no `Co-Authored-By` trailer.

---

## Self-review

- Spec coverage: layout, visual system, components, data integration, UX behavior, accessibility, and testing are covered by Tasks 1-5.
- Placeholder scan: no TBD/TODO/fill-later placeholders.
- Type/property consistency: existing IDs, payload fields, API endpoints, and function names remain consistent with current frontend.
- Scope check: frontend-only redesign; backend untouched.
