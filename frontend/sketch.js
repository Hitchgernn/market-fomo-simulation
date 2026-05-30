const API_URL = "http://localhost:8000/tick";
const POLL_INTERVAL_MS = 1200;

let nodes = [];
let nodeMap = new Map();
let pulses = [];
let lastPayload = null;
let networkCanvas;

function setup() {
  const host = document.getElementById("network-canvas");
  networkCanvas = createCanvas(host.offsetWidth, host.offsetHeight);
  networkCanvas.parent(host);
  frameRate(30);
  pollTick();
  setInterval(pollTick, POLL_INTERVAL_MS);
}

function windowResized() {
  const host = document.getElementById("network-canvas");
  resizeCanvas(host.offsetWidth, host.offsetHeight);
  layoutNodes();
}

function draw() {
  background("#151718");
  drawGrid();
  drawConnections();
  drawPulses();
  drawNodes();
}

async function pollTick() {
  try {
    const response = await fetch(API_URL, { cache: "no-store" });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    const payload = await response.json();
    setStatus("Live", "online");
    ingestPayload(payload);
  } catch (error) {
    setStatus("Offline", "offline");
  }
}

function ingestPayload(payload) {
  lastPayload = payload;
  nodes = payload.nodes.map((node) => {
    const existing = nodeMap.get(node.id);
    return {
      ...node,
      x: existing?.x ?? random(width * 0.15, width * 0.85),
      y: existing?.y ?? random(height * 0.15, height * 0.85),
      vx: existing?.vx ?? 0,
      vy: existing?.vy ?? 0,
    };
  });
  nodeMap = new Map(nodes.map((node) => [node.id, node]));
  layoutNodes();
  updateMetrics(payload);
  pushChats(payload.chats);
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
  stroke("#242829");
  strokeWeight(1);
  for (let x = 0; x < width; x += 36) {
    line(x, 0, x, height);
  }
  for (let y = 0; y < height; y += 36) {
    line(0, y, width, y);
  }
}

function drawConnections() {
  stroke("#3a3f40");
  strokeWeight(1);
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
    const size = node.state === "P" ? 15 : node.state === "A" ? 12 : 10;
    noStroke();
    fill(node.color);
    circle(node.x, node.y, size);
    fill("#f2f5f1");
    text(node.id, node.x, node.y - 16);
  }
}

function updateMetrics(payload) {
  const price = payload.price;
  const orderBook = payload.orderBook;
  const totalVolume = orderBook.buyVolume + orderBook.sellVolume || 1;
  const buyShare = (orderBook.buyVolume / totalVolume) * 100;
  const sellShare = (orderBook.sellVolume / totalVolume) * 100;
  const priceBand = ((price.current - price.arbLimit) / (price.araLimit - price.arbLimit)) * 100;

  setText("tick-label", `Tick ${payload.tick}`);
  setText("price-value", formatNumber(price.current));
  setText("imbalance-value", orderBook.imbalance.toFixed(3));
  setText("ara-value", formatNumber(price.araLimit));
  setText("arb-value", formatNumber(price.arbLimit));
  setText("buy-volume", orderBook.buyVolume);
  setText("sell-volume", orderBook.sellVolume);

  document.getElementById("buy-bar").style.width = `${buyShare}%`;
  document.getElementById("sell-bar").style.width = `${sellShare}%`;
  document.getElementById("price-band").style.width = `${constrain(priceBand, 0, 100)}%`;

  const rejection = price.araTriggered ? "ARA" : price.arbTriggered ? "ARB" : "Clear";
  setText("rejection-state", rejection);
  document.getElementById("rejection-state").className =
    price.araTriggered ? "up" : price.arbTriggered ? "down" : "";
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
  }

  while (feed.children.length > 40) {
    feed.removeChild(feed.lastChild);
  }
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
