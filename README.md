# FOMO Market Simulation

A browser-based multi-agent stock market simulation for exploring FOMO, panic selling, order imbalance, price limits, and stochastic market maker shocks.

The simulation runs without any API key. Gemini chat is optional.

## Features

- Mesa-based retail and institutional investor agents.
- Network contagion for the `Neutral -> Aware` transition.
- Simple Limit Order Book using aggregate buy/sell imbalance.
- Configurable upper and lower price limits.
- Stochastic market maker dump scenarios.
- Pixel trading terminal dashboard UI.
- Live price and volume chart in the `Live Market` panel.
- Interactive Mesa network graph in the `Graph` panel.
- Scrollable market event and chat feeds.
- Optional Gemini-powered market chat.

## Project Structure

```text
.
|-- backend/
|   |-- api/server.py          # FastAPI simulation endpoints
|   |-- engine/agent.py        # Mesa agents and order model
|   |-- engine/model.py        # StockMarketModel, LOB, price limits, shocks
|   |-- llm/rotator.py         # Optional Gemini key rotator
|   `-- requirements.txt
|-- frontend/
|   |-- index.html             # Dashboard UI
|   `-- sketch.js              # p5 graph, Chart.js chart, API polling
|-- ARCHITECTURE.md
|-- COMMIT_CONVENTION.md
`-- README.md
```

## Requirements

- Python 3.11+
- A modern browser
- Internet access for frontend CDNs: p5.js and Chart.js

Install backend dependencies from the project root:

```bash
python -m pip install -r backend/requirements.txt
```

## Run Without API Keys

Start the backend:

```bash
GEMINI_API_KEY= GEMINI_API_KEYS= uvicorn backend.api.server:app --host 127.0.0.1 --port 8000 --reload
```

Start the frontend in another terminal:

```bash
cd frontend
python -m http.server 5501
```

Open:

```text
http://127.0.0.1:5501
```

The frontend expects the backend at `http://127.0.0.1:8000`.

## Pixel Trading Terminal UI

The dashboard keeps trading/simulation terminology visible for presentation clarity:

- `Graph`: Mesa agent network graph.
- `Live Market`: price and volume chart.
- `Order Book`: buy/sell volume and price limit state.
- `Controls`: runtime parameters and presets.
- `Market Events` / `Market Chat`: scrollable feeds for newer and older messages.

## Optional Market Chat

The simulation can generate short retail trader messages from Gemini, OpenRouter, or local Ollama. Without provider config, chat stays empty but the simulation still works.

Gemini:

```bash
CHAT_PROVIDER=gemini GEMINI_API_KEY="your_api_key" uvicorn backend.api.server:app --host 127.0.0.1 --port 8000 --reload
```

OpenRouter:

```bash
CHAT_PROVIDER=openrouter OPENROUTER_API_KEY="your_api_key" OPENROUTER_MODEL="meta-llama/llama-3.2-3b-instruct:free" uvicorn backend.api.server:app --host 127.0.0.1 --port 8000 --reload
```

Local Ollama:

```bash
CHAT_PROVIDER=ollama OLLAMA_BASE_URL="http://localhost:11434" OLLAMA_MODEL="qwen3.5:4b" uvicorn backend.api.server:app --host 127.0.0.1 --port 8000 --reload
```

The `/state` and `/tick` responses include chat diagnostics:

```json
"chat": {
  "enabled": true,
  "provider": "openrouter",
  "model": "meta-llama/llama-3.2-3b-instruct:free",
  "lastError": null
}
```

## Dashboard Controls

- `Run` / `Pause`: start or stop live polling.
- `Step`: advance one simulation tick.
- `Apply`: reset the model using the current parameters.
- `FOMO Pump`: emphasizes awareness and buy pressure.
- `Maker Dump`: enables stochastic market maker sell shocks.
- `Lower Limit Spiral`: stress scenario for drawdown and lower-limit behavior.

Useful parameters:

| Parameter | Meaning |
| --- | --- |
| `Base Price` | Initial and reference price for upper/lower limits |
| `Beta` | Social exposure sensitivity |
| `Price Impact` | Price movement from order imbalance |
| `Upper Limit %` | Upper price limit from base price |
| `Lower Limit %` | Lower price limit from base price |
| `Shock Probability` | Chance of market maker dump per eligible tick |
| `Shock Min/Max Vol` | Random sell shock volume range |
| `Panic Drawdown` | Drawdown threshold before panic can spread |
| `Panic Sensitivity` | Probability multiplier for panic after drawdown |
| `Panic Sell Mult` | Sell volume multiplier for panic agents |

## Simulation Mechanics

The model is stochastic. Random draws are used for graph generation, agent order, initial states, awareness spread, and market maker shocks.

Awareness transition:

```text
P(Exposure) = 1 - (1 - beta)^k
```

Where `k` is the number of neighboring panic agents.

Price discovery:

```text
imbalance = (buyVolume - sellVolume) / totalVolume
candidatePrice = currentPrice * (1 + priceImpact * imbalance)
```

Price limits:

```text
upperLimit = basePrice * (1 + upperLimitPercent)
lowerLimit = basePrice * (1 - lowerLimitPercent)
```

Market maker shock:

```text
shock happens if random() < shockProbability
shockVolume = random integer between shockMinVolume and shockMaxVolume
```

## API

Default backend URL:

```text
http://127.0.0.1:8000
```

Endpoints:

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/state` | Read current simulation state |
| `GET` | `/tick` | Advance one tick |
| `POST` | `/reset` | Reset model with new config |

## Verify

Compile backend code:

```bash
python -m compileall backend
```

Check frontend JavaScript syntax:

```bash
node --check frontend/sketch.js
```

## Troubleshooting

- Frontend shows offline: make sure the backend is running on port `8000`.
- Backend port is busy: run Uvicorn on another port and update `API_BASE` in `frontend/sketch.js`.
- Frontend port is busy: use another static server port, for example `python -m http.server 5502`.
- Chat is empty: this is expected when no Gemini API key is configured.

## Notes

- Read `ARCHITECTURE.md` before changing module boundaries.
- Follow `COMMIT_CONVENTION.md` for commits.
- The backend engine is independent from the frontend and API layer.
- This is a behavioral simulation, not a market prediction tool.
