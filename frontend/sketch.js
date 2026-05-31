const LOCAL_API_BASE = "http://localhost:8000";
const PROD_API_BASE = window.FOMO_API_BASE || window.location.origin;
const API_BASE = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1" ? LOCAL_API_BASE : PROD_API_BASE;
const HISTORY_LIMIT = 160;
const STATE_PALETTE = {
  N: "#00f5d4",
  A: "#fee440",
  P: "#ff4d6d",
};

let nodes = [];
let nodeMap = new Map();
let pulses = [];
let lastPayload = null;
let networkCanvas;
let marketChart;
let pollTimer = null;
let isRunning = true;
let tickSpeedMs = 1200;
let history = [];
let chatMessageCount = 0;
let eventMessageCount = 0;

const PRESETS = {
  fomo: {
    shockEnabled: false,
    shockProbability: 0,
    shockCooldownTicks: 5,
    shockMinVolume: 25,
    shockMaxVolume: 80,
    panicDrawdownThreshold: 0.05,
    panicSensitivity: 8,
    panicSellMultiplier: 3,
    initialAwareFraction: 0.12,
    initialPanicFraction: 0.08,
    beta: 0.25,
    priceImpact: 0.02,
    upperLimitPercent: 0.25,
    lowerLimitPercent: 0.15,
  },
  dump: {
    shockEnabled: true,
    shockProbability: 0.35,
    shockCooldownTicks: 5,
    shockMinVolume: 90,
    shockMaxVolume: 180,
    panicDrawdownThreshold: 0.015,
    panicSensitivity: 35,
    panicSellMultiplier: 5,
    initialAwareFraction: 0.18,
    initialPanicFraction: 0.02,
    beta: 0.18,
    priceImpact: 0.08,
    upperLimitPercent: 0.25,
    lowerLimitPercent: 0.15,
  },
  lowerLimit: {
    shockEnabled: true,
    shockProbability: 0.75,
    shockCooldownTicks: 2,
    shockMinVolume: 180,
    shockMaxVolume: 360,
    panicDrawdownThreshold: 0.005,
    panicSensitivity: 100,
    panicSellMultiplier: 8,
    initialAwareFraction: 0.25,
    initialPanicFraction: 0,
    beta: 0.2,
    priceImpact: 0.18,
    upperLimitPercent: 0.2,
    lowerLimitPercent: 0.08,
  },
};

function setup() {
  const host = document.getElementById("network-canvas");
  networkCanvas = createCanvas(host.offsetWidth, host.offsetHeight);
  networkCanvas.parent(host);
  frameRate(30);
  initChart();
  initControls();
  fetchState();
  restartPolling();
}

function windowResized() {
  const host = document.getElementById("network-canvas");
  resizeCanvas(host.offsetWidth, host.offsetHeight);
  layoutNodes();
}

function draw() {
  background("#080d18");
  drawGrid();
  drawConnections();
  drawPulses();
  drawNodes();
}

function initControls() {
  document.getElementById("run-toggle").addEventListener("click", toggleRun);
  document.getElementById("step-button").addEventListener("click", stepOnce);
  document.getElementById("apply-button").addEventListener("click", applyConfig);
  document.getElementById("preset-fomo").addEventListener("click", () => applyPreset("fomo"));
  document.getElementById("preset-dump").addEventListener("click", () => applyPreset("dump"));
  document.getElementById("preset-lower-limit").addEventListener("click", () => applyPreset("lowerLimit"));
  document.getElementById("tickSpeed").addEventListener("change", () => {
    tickSpeedMs = clampNumber(readNumber("tickSpeed"), 150, 10000);
    restartPolling();
  });
}

function initChart() {
  const canvas = document.getElementById("market-chart");
  if (!window.Chart || !canvas) {
    return;
  }

  marketChart = new Chart(canvas, {
    data: {
      labels: [],
      datasets: [
        {
          type: "line",
          label: "Price",
          data: [],
          borderColor: "#00f5d4",
          backgroundColor: "rgb(0 245 212 / 12%)",
          borderWidth: 2,
          pointRadius: 3,
          pointHoverRadius: 5,
          tension: 0.22,
          yAxisID: "price",
        },
        {
          type: "bar",
          label: "Buy",
          data: [],
          backgroundColor: "rgb(0 245 212 / 42%)",
          borderColor: "#00f5d4",
          borderWidth: 1,
          yAxisID: "volume",
        },
        {
          type: "bar",
          label: "Sell",
          data: [],
          backgroundColor: "rgb(255 77 109 / 38%)",
          borderColor: "#ff4d6d",
          borderWidth: 1,
          yAxisID: "volume",
        },
      ],
    },
    options: {
      animation: false,
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: "index", intersect: false },
      plugins: {
        legend: {
          labels: {
            color: "#8ca3b8",
            boxWidth: 12,
            boxHeight: 12,
            font: { family: "Share Tech Mono" },
          },
        },
      },
      scales: {
        x: {
          ticks: {
            color: "#8ca3b8",
            maxTicksLimit: 8,
            font: { family: "Share Tech Mono" },
          },
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
    },
  });
}

function restartPolling() {
  if (pollTimer) {
    clearInterval(pollTimer);
  }
  if (isRunning) {
    pollTimer = setInterval(pollTick, tickSpeedMs);
  }
}

async function fetchState() {
  try {
    const payload = await requestJson(`${API_BASE}/state`);
    setStatus("Live", "online");
    ingestPayload(payload, { appendChart: true, pushChat: false });
    syncControls(payload.config);
  } catch (error) {
    setStatus("Offline", "offline");
  }
}

async function pollTick() {
  if (!isRunning) {
    return;
  }
  try {
    const payload = await requestJson(`${API_BASE}/tick`);
    setStatus("Live", "online");
    ingestPayload(payload);
  } catch (error) {
    setStatus("Offline", "offline");
  }
}

async function stepOnce() {
  const wasRunning = isRunning;
  isRunning = false;
  updateRunButton();
  restartPolling();

  try {
    const payload = await requestJson(`${API_BASE}/tick`);
    setStatus("Live", "online");
    ingestPayload(payload);
  } catch (error) {
    setStatus("Offline", "offline");
  }

  isRunning = wasRunning;
  updateRunButton();
  restartPolling();
}

async function applyConfig() {
  const config = readConfig();
  if (config.initialAwareFraction + config.initialPanicFraction > 1) {
    setStatus("Invalid mix", "offline");
    return;
  }

  try {
    const payload = await requestJson(`${API_BASE}/reset`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(config),
    });
    clearHistory();
    clearChat();
    clearEvents();
    setStatus("Live", "online");
    ingestPayload(payload, { appendChart: true, pushChat: false, pushEvent: false });
    syncControls(payload.config);
    tickSpeedMs = config.tickSpeed;
    restartPolling();
  } catch (error) {
    setStatus("Reset failed", "offline");
  }
}

async function applyPreset(name) {
  const preset = PRESETS[name];
  if (!preset) {
    return;
  }
  syncControls(preset);
  await applyConfig();
}

function toggleRun() {
  isRunning = !isRunning;
  updateRunButton();
  restartPolling();
}

function updateRunButton() {
  document.getElementById("run-toggle").textContent = isRunning ? "Pause" : "Run";
}

async function requestJson(url, options) {
  const response = await fetch(url, { cache: "no-store", ...options });
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
  return response.json();
}

function ingestPayload(payload, options = {}) {
  const appendChart = options.appendChart !== false;
  const pushChat = options.pushChat !== false;
  const pushEvent = options.pushEvent !== false;
  lastPayload = payload;
  nodes = payload.nodes.map((node) => {
    const existing = nodeMap.get(node.id);
    return {
      ...node,
      x: existing?.x ?? random(width * 0.15, width * 0.85),
      y: existing?.y ?? random(height * 0.15, height * 0.85),
      vx: existing?.vx ?? 0,
      vy: existing?.vy ?? 0,
      color: STATE_PALETTE[node.state] || node.color,
    };
  });
  nodeMap = new Map(nodes.map((node) => [node.id, node]));
  layoutNodes();
  updateMetrics(payload);
  if (appendChart) {
    appendHistory(payload);
  }
  if (pushChat) {
    pushChats(payload.chats);
  }
  if (pushEvent) {
    pushEvents(payload.events);
  }
}

function layoutNodes() {
  if (!nodes.length) {
    return;
  }

  const centerX = width / 2;
  const centerY = height / 2;
  const radius = Math.max(90, Math.min(width, height) * 0.38);

  nodes.forEach((node, index) => {
    const angle = (index / nodes.length) * TWO_PI;
    const targetX = centerX + Math.cos(angle) * radius;
    const targetY = centerY + Math.sin(angle) * radius;
    node.x = lerp(node.x, targetX, 0.45);
    node.y = lerp(node.y, targetY, 0.45);
  });
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

function drawPulses() {
  pulses = pulses.filter((pulse) => pulse.life > 0);
  noFill();
  for (const pulse of pulses) {
    const node = nodeMap.get(pulse.agentId);
    if (!node) {
      pulse.life = 0;
      continue;
    }
    const alpha = map(pulse.life, 0, 1, 0, 190);
    stroke(239, 68, 68, alpha);
    strokeWeight(2);
    circle(node.x, node.y, 54 + (1 - pulse.life) * 46);
    pulse.life -= 0.035;
  }
}

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

function updateMetrics(payload) {
  const price = payload.price;
  const orderBook = payload.orderBook;
  const counts = payload.stateCounts || { N: 0, A: 0, P: 0 };
  const market = payload.market || { regime: "normal", shockVolume: 0 };
  const totalVolume = orderBook.buyVolume + orderBook.sellVolume || 1;
  const buyShare = (orderBook.buyVolume / totalVolume) * 100;
  const sellShare = (orderBook.sellVolume / totalVolume) * 100;
  const bandWidth = price.upperLimit - price.lowerLimit || 1;
  const priceBand = ((price.current - price.lowerLimit) / bandWidth) * 100;

  setText("tick-label", `Tick ${payload.tick}`);
  setText("price-value", formatNumber(price.current));
  setText("imbalance-value", orderBook.imbalance.toFixed(3));
  setText("neutral-count", counts.N ?? 0);
  setText("aware-count", counts.A ?? 0);
  setText("panic-count", counts.P ?? 0);
  setText("market-regime", market.regime);
  setText("upper-limit-value", formatNumber(price.upperLimit));
  setText("lower-limit-value", formatNumber(price.lowerLimit));
  setText("buy-volume", orderBook.buyVolume);
  setText("sell-volume", orderBook.sellVolume);

  document.getElementById("buy-bar").style.width = `${buyShare}%`;
  document.getElementById("sell-bar").style.width = `${sellShare}%`;
  document.getElementById("price-band").style.width = `${constrain(priceBand, 0, 100)}%`;

  const limitState = price.upperLimitTriggered
    ? "Upper Limit"
    : price.lowerLimitTriggered
      ? "Lower Limit"
      : "Clear";
  setText("limit-state", limitState);
  document.getElementById("limit-state").className =
    price.upperLimitTriggered ? "up" : price.lowerLimitTriggered ? "down" : "";
  document.getElementById("limit-bar").style.width =
    price.upperLimitTriggered || price.lowerLimitTriggered ? "100%" : "0%";
}

function appendHistory(payload) {
  if (history.some((sample) => sample.tick === payload.tick)) {
    return;
  }

  history.push({
    tick: payload.tick,
    price: payload.price.current,
    buyVolume: payload.orderBook.buyVolume,
    sellVolume: payload.orderBook.sellVolume,
    drawdown: payload.price.drawdown ?? 0,
    regime: payload.market?.regime ?? "normal",
    shockVolume: payload.market?.shockVolume ?? 0,
    hasDump: payload.events?.some((event) => event.type === "market_maker_dump") ?? false,
    upperLimitTriggered: payload.price.upperLimitTriggered,
    lowerLimitTriggered: payload.price.lowerLimitTriggered,
  });

  while (history.length > HISTORY_LIMIT) {
    history.shift();
  }

  updateChart();
}

function updateChart() {
  setText("history-label", `${history.length} samples`);
  if (!marketChart) {
    return;
  }

  marketChart.data.labels = history.map((sample) => sample.tick);
  marketChart.data.datasets[0].data = history.map((sample) => sample.price);
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
  marketChart.data.datasets[1].data = history.map((sample) => sample.buyVolume);
  marketChart.data.datasets[2].data = history.map((sample) => sample.sellVolume);
  marketChart.update();
}

function pushChats(chats) {
  if (!Array.isArray(chats) || chats.length === 0) {
    return;
  }

  const feed = document.getElementById("chat-feed");
  for (const chat of chats) {
    pulses.push({ agentId: chat.agentId, life: 1 });
    const item = document.createElement("article");
    item.className = "chat-message";
    item.innerHTML = `
      <div class="chat-meta">Agent ${chat.agentId}</div>
      <p></p>
    `;
    item.querySelector("p").textContent = chat.message;
    feed.prepend(item);
    chatMessageCount += 1;
  }

  while (feed.children.length > 40) {
    feed.removeChild(feed.lastChild);
  }
  setText("chat-count", `${chatMessageCount} messages`);
}

function pushEvents(events) {
  if (!Array.isArray(events) || events.length === 0) {
    return;
  }

  const feed = document.getElementById("event-feed");
  for (const event of events) {
    const item = document.createElement("article");
    item.className = `event-message ${event.severity || ""}`;
    item.innerHTML = `
      <div class="chat-meta">Tick ${event.tick} · ${event.type}</div>
      <p></p>
    `;
    item.querySelector("p").textContent = event.message;
    feed.prepend(item);
    eventMessageCount += 1;
  }

  while (feed.children.length > 50) {
    feed.removeChild(feed.lastChild);
  }
  setText("event-count", `${eventMessageCount} events`);
}

function clearHistory() {
  history = [];
  updateChart();
}

function clearChat() {
  pulses = [];
  chatMessageCount = 0;
  setText("chat-count", "0 messages");
  document.getElementById("chat-feed").replaceChildren();
}

function clearEvents() {
  eventMessageCount = 0;
  setText("event-count", "0 events");
  document.getElementById("event-feed").replaceChildren();
}

function readConfig() {
  const shockMinVolume = Math.round(clampNumber(readNumber("shockMinVolume"), 1, 1000000));
  const shockMaxVolume = Math.round(clampNumber(readNumber("shockMaxVolume"), 1, 1000000));
  return {
    numRetail: Math.round(clampNumber(readNumber("numRetail"), 0, 1000)),
    numInstitutional: Math.round(clampNumber(readNumber("numInstitutional"), 0, 100)),
    basePrice: clampNumber(readNumber("basePrice"), 1, 1000000),
    beta: clampNumber(readNumber("beta"), 0, 1),
    priceImpact: clampNumber(readNumber("priceImpact"), 0, 1),
    initialAwareFraction: clampNumber(readNumber("initialAwareFraction"), 0, 1),
    initialPanicFraction: clampNumber(readNumber("initialPanicFraction"), 0, 1),
    upperLimitPercent: clampNumber(readNumber("upperLimitPercent"), 0, 1),
    lowerLimitPercent: clampNumber(readNumber("lowerLimitPercent"), 0, 1),
    shockEnabled: document.getElementById("shockEnabled").checked,
    shockProbability: clampNumber(readNumber("shockProbability"), 0, 1),
    shockCooldownTicks: Math.round(clampNumber(readNumber("shockCooldownTicks"), 0, 1000)),
    shockMinVolume,
    shockMaxVolume: Math.max(shockMinVolume, shockMaxVolume),
    panicDrawdownThreshold: clampNumber(readNumber("panicDrawdownThreshold"), 0, 1),
    panicSensitivity: clampNumber(readNumber("panicSensitivity"), 0, 1000),
    panicSellMultiplier: Math.round(clampNumber(readNumber("panicSellMultiplier"), 1, 1000)),
    chatMode: document.getElementById("chat-mode-ai").checked ? "ai" : "scripted",
    tickSpeed: Math.round(clampNumber(readNumber("tickSpeed"), 150, 10000)),
  };
}

function syncControls(config) {
  if (!config) {
    return;
  }
  document.getElementById("chat-mode-scripted").checked = config.chatMode !== "ai";
  document.getElementById("chat-mode-ai").checked = config.chatMode === "ai";
  for (const [key, value] of Object.entries(config)) {
    const input = document.getElementById(key);
    if (input && value !== null && value !== undefined) {
      if (input.type === "checkbox") {
        input.checked = Boolean(value);
      } else {
        input.value = value;
      }
    }
  }
}

function readNumber(id) {
  return Number(document.getElementById(id).value);
}

function clampNumber(value, lower, upper) {
  if (!Number.isFinite(value)) {
    return lower;
  }
  return Math.min(Math.max(value, lower), upper);
}

function setStatus(label, stateClass) {
  setText("api-status", label);
  const light = document.getElementById("status-light");
  light.className = `status-light ${stateClass}`;
}

function setText(id, value) {
  document.getElementById(id).textContent = value;
}

function formatNumber(value) {
  return Number(value).toLocaleString("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}
