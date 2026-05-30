# FOMO Market Simulation

A multi-agent stock market simulation for exploring FOMO dynamics, panic selling, order imbalance, auto rejection, and stochastic market maker shocks.

The project uses a decoupled architecture:

- The backend runs the core simulation engine with Mesa, NetworkX, and FastAPI.
- The frontend renders an interactive browser dashboard with p5.js and Chart.js.
- LLM-powered chat is optional. The simulation runs normally without API keys.

## Key Features

- Multi-agent market simulation with retail and institutional investors.
- Network contagion for the `Neutral -> Aware` transition.
- Agent states:
  - `N`: Neutral
  - `A`: Aware
  - `P`: Panic/FOMO
- Simple Limit Order Book based on aggregate order imbalance.
- Configurable upper auto rejection (ARA) and lower auto rejection (ARB).
- Stochastic market maker dump:
  - shock events occur by probability
  - dump volume is random within a configured range
  - retail panic is triggered by drawdown-based probability
- Live market chart:
  - price line
  - buy/sell volume bars
  - markers for shock/ARB/ARA events
- Agent network graph with state colors.
- Runtime simulation controls from the frontend.
- Scenario presets:
  - `FOMO Pump`
  - `Maker Dump`
  - `ARB Spiral`
- Optional Gemini chat rotator for panic agents.

## Project Structure

```text
.
|-- backend/
|   |-- api/
|   |   `-- server.py          # FastAPI endpoints and simulation config
|   |-- engine/
|   |   |-- agent.py           # RetailInvestor, InstitutionalInvestor, Order
|   |   `-- model.py           # StockMarketModel, LOB, ARA/ARB, shock logic
|   |-- llm/
|   |   `-- rotator.py         # Gemini API key round-robin rotator
|   `-- requirements.txt
|-- frontend/
|   |-- index.html             # Dashboard layout and controls
|   `-- sketch.js              # p5 graph, API polling, Chart.js updates
|-- ARCHITECTURE.md
|-- COMMIT_CONVENTION.md
`-- README.md
```

## Requirements

- Python 3.11+ recommended
- A modern browser
- Internet access is only required by the frontend CDNs:
  - p5.js
  - Chart.js
- Gemini API key is optional

Install backend dependencies:

```bash
cd /home/hitchgernn/projects/fomo-simulation-revised
python -m pip install -r backend/requirements.txt
```

## Running the Project

### 1. Run the backend without API keys

Use this mode when you only want to test the simulation, frontend, chart, and controls without LLM chat:

```bash
cd /home/hitchgernn/projects/fomo-simulation-revised
GEMINI_API_KEY= GEMINI_API_KEYS= uvicorn backend.api.server:app --host 127.0.0.1 --port 8000 --reload
```

Backend endpoints:

```text
http://127.0.0.1:8000/state
http://127.0.0.1:8000/tick
```

The root URL `http://127.0.0.1:8000/` is not used and may return `404`.

### 2. Run the frontend

```bash
cd /home/hitchgernn/projects/fomo-simulation-revised/frontend
python -m http.server 5501
```

Open:

```text
http://127.0.0.1:5501
```

If port `5501` is already in use, choose another port:

```bash
python -m http.server 5502
```

### 3. Run with an optional Gemini API key

To enable panic-agent chat:

```bash
cd /home/hitchgernn/projects/fomo-simulation-revised
GEMINI_API_KEY="your_api_key" uvicorn backend.api.server:app --host 127.0.0.1 --port 8000 --reload
```

For multiple keys:

```bash
GEMINI_API_KEYS="key_1,key_2,key_3" uvicorn backend.api.server:app --host 127.0.0.1 --port 8000 --reload
```

If no key is configured, `chat_rotator=None` and the simulation still works.

## Dashboard Usage

1. Make sure the backend is running at `http://localhost:8000`.
2. Open the frontend.
3. Choose a preset:
   - `FOMO Pump`: shock off, emphasizes FOMO-buy contagion.
   - `Maker Dump`: probabilistic market maker sell shock.
   - `ARB Spiral`: more aggressive shock settings to stress the lower rejection band.
4. Adjust parameters if needed.
5. Click `Apply` to reset the model with the new config.
6. Use:
   - `Pause` / `Run` to stop or resume polling.
   - `Step` to advance one tick manually.

## Simulation Parameters

| Parameter | Meaning |
| --- | --- |
| `numRetail` | Number of retail agents |
| `numInstitutional` | Number of institutional agents |
| `basePrice` | Base stock price |
| `beta` | Social exposure sensitivity for `N -> A` |
| `priceImpact` | Price impact from order imbalance |
| `initialAwareFraction` | Initial fraction of Aware retail agents |
| `initialPanicFraction` | Initial fraction of Panic retail agents |
| `araPercent` | Maximum upside limit from base price |
| `arbPercent` | Maximum downside limit from base price |
| `shockEnabled` | Enables market maker dump shocks |
| `shockProbability` | Shock probability per eligible tick |
| `shockCooldownTicks` | Minimum tick gap between shocks |
| `shockMinVolume` | Minimum sell shock volume |
| `shockMaxVolume` | Maximum sell shock volume |
| `panicDrawdownThreshold` | Minimum drawdown before panic can trigger |
| `panicSensitivity` | Panic probability multiplier after drawdown exceeds threshold |
| `panicSellMultiplier` | Sell volume multiplier for Panic agents in crash regime |
| `rng` | Optional seed for pseudo-stochastic reproducibility |

## Stochastic Model

This project is not purely deterministic. It uses random draws in multiple places:

- Network graph generation uses a random seed.
- Agent step order is shuffled every tick.
- Initial retail agent states are shuffled.
- The `Neutral -> Aware` transition uses probability:

```text
P(Exposure) = 1 - (1 - beta)^k
```

Where:

- `beta`: information sensitivity.
- `k`: number of neighboring agents in state `P`.

The market maker dump is stochastic too:

```text
shock happens if random() < shockProbability
shockVolume = random integer between shockMinVolume and shockMaxVolume
```

Retail panic after a crash:

```text
panicPressure = max(0, drawdown - panicDrawdownThreshold) * panicSensitivity
panicProbability = clamp(panicPressure, 0, 1)
```

If `rng` is provided, the result becomes reproducible pseudo-stochastic. It is still based on random draws, but the same seed tends to produce the same pattern.

## Price Discovery

Every tick:

1. Agents generate buy/sell orders.
2. A market maker shock may add a large sell order.
3. The backend computes aggregate volume:

```text
imbalance = (buyVolume - sellVolume) / totalVolume
```

4. Price changes:

```text
candidatePrice = currentPrice * (1 + priceImpact * imbalance)
```

5. Price is clamped by ARA/ARB:

```text
araLimit = basePrice * (1 + araPercent)
arbLimit = basePrice * (1 - arbPercent)
```

## API

Default base URL:

```text
http://127.0.0.1:8000
```

### GET `/state`

Returns the current simulation state without advancing a tick.

### GET `/tick`

Advances the simulation by one tick and returns the latest state.

### POST `/reset`

Resets the model with a new config.

Example body:

```json
{
  "numRetail": 100,
  "numInstitutional": 5,
  "basePrice": 100,
  "beta": 0.15,
  "priceImpact": 0.02,
  "initialAwareFraction": 0.1,
  "initialPanicFraction": 0.05,
  "araPercent": 0.25,
  "arbPercent": 0.15,
  "shockEnabled": true,
  "shockProbability": 0.35,
  "shockCooldownTicks": 5,
  "shockMinVolume": 90,
  "shockMaxVolume": 180,
  "panicDrawdownThreshold": 0.015,
  "panicSensitivity": 35,
  "panicSellMultiplier": 5,
  "rng": 42
}
```

Main response fields:

- `tick`
- `config`
- `price`
- `orderBook`
- `market`
- `events`
- `stateCounts`
- `nodes`
- `chats`

## Testing and Verification

Compile the backend:

```bash
python -m compileall backend
```

Check frontend JavaScript syntax:

```bash
node --check frontend/sketch.js
```

Run a direct API smoke test from Python:

```bash
python - <<'PY'
import os
os.environ.pop("GEMINI_API_KEY", None)
os.environ.pop("GEMINI_API_KEYS", None)

from backend.api import server
from backend.api.server import SimulationConfig

payload = server.reset(SimulationConfig(
    numRetail=40,
    numInstitutional=0,
    priceImpact=0.2,
    arbPercent=0.05,
    shockEnabled=True,
    shockProbability=1.0,
    shockCooldownTicks=2,
    shockMinVolume=300,
    shockMaxVolume=300,
    panicDrawdownThreshold=0.01,
    panicSensitivity=100,
    panicSellMultiplier=7,
    initialAwareFraction=0.4,
    initialPanicFraction=0.0,
    rng=10,
))

payload = server.tick()
assert payload["market"]["shockVolume"] == 300
assert payload["events"]
assert payload["price"]["arbLimit"] <= payload["price"]["current"] <= payload["price"]["araLimit"]
print("ok", payload["market"]["regime"], payload["price"]["drawdown"])
PY
```

## Troubleshooting

### Frontend status is `Offline`

The backend is not running or is not available at `localhost:8000`.

Run:

```bash
GEMINI_API_KEY= GEMINI_API_KEYS= uvicorn backend.api.server:app --host 127.0.0.1 --port 8000 --reload
```

### Backend port is already in use

Find the process using the port, or run the backend on a different port.

If the backend port changes, update `API_BASE` in `frontend/sketch.js`.

### Frontend port is already in use

Use another static server port:

```bash
cd frontend
python -m http.server 5502
```

### Chat is empty

This is normal if no Gemini API key is configured. Simulation, chart, network graph, and shock features still work.

### Chart does not appear

Make sure the browser can access the Chart.js CDN:

```text
https://cdn.jsdelivr.net/npm/chart.js
```

For a fully offline setup, download Chart.js and p5.js into the frontend folder and update the script tags in `index.html`.

## Development Notes

- Follow `COMMIT_CONVENTION.md`.
- Use Conventional Commits.
- Do not bundle engine, API, frontend, and docs changes in one large commit.
- The backend must not depend on the UI.
- The frontend only polls the API and renders state.

## Current Limitations

- The LOB is still aggregate imbalance, not a full bid/ask level book.
- Market maker dump is modeled as a synthetic sell order, not a separate Mesa agent.
- This simulation is for market behavior exploration, not real price prediction.
- There is no database persistence; state lives in the FastAPI process memory.

