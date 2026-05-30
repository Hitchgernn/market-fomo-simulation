# FOMO Market Simulation

Simulasi pasar saham berbasis multi-agent untuk mengamati dinamika FOMO, panic selling, order imbalance, auto rejection, dan shock market maker secara stokastik.

Project ini memakai arsitektur decoupled:

- Backend menjalankan core simulation engine dengan Mesa, NetworkX, dan FastAPI.
- Frontend merender dashboard interaktif di browser dengan p5.js dan Chart.js.
- LLM chat bersifat opsional. Tanpa API key, simulasi tetap berjalan normal.

## Fitur Utama

- Multi-agent market simulation dengan agen ritel dan institusi.
- Network contagion untuk transisi `Neutral -> Aware`.
- State agen:
  - `N`: Neutral
  - `A`: Aware
  - `P`: Panic/FOMO
- Limit Order Book sederhana berbasis aggregate order imbalance.
- Auto Rejection Atas (ARA) dan Auto Rejection Bawah (ARB) configurable.
- Stochastic market maker dump:
  - shock muncul berdasarkan probabilitas
  - volume dump random dalam range
  - retail panic terjadi berdasarkan drawdown dan probabilitas
- Live market chart:
  - price line
  - buy/sell volume bars
  - marker untuk shock/ARB/ARA
- Network graph agent dengan warna state.
- Parameter simulation controls dari frontend.
- Preset scenario:
  - `FOMO Pump`
  - `Maker Dump`
  - `ARB Spiral`
- Optional Gemini chat rotator untuk agen panic.

## Struktur Project

```text
.
|-- backend/
|   |-- api/
|   |   `-- server.py          # FastAPI endpoints dan simulation config
|   |-- engine/
|   |   |-- agent.py           # RetailInvestor, InstitutionalInvestor, Order
|   |   `-- model.py           # StockMarketModel, LOB, ARA/ARB, shock logic
|   |-- llm/
|   |   `-- rotator.py         # Gemini API key round-robin rotator
|   `-- requirements.txt
|-- frontend/
|   |-- index.html             # Dashboard layout dan controls
|   `-- sketch.js              # p5 graph, polling API, Chart.js updates
|-- ARCHITECTURE.md
|-- COMMIT_CONVENTION.md
`-- README.md
```

## Requirements

- Python 3.11+ direkomendasikan
- Browser modern
- Internet hanya dibutuhkan frontend untuk CDN:
  - p5.js
  - Chart.js
- Gemini API key opsional

Install dependency backend:

```bash
cd /home/hitchgernn/projects/fomo-simulation-revised
python -m pip install -r backend/requirements.txt
```

## Menjalankan Project

### 1. Jalankan backend tanpa API key

Gunakan ini kalau hanya ingin test simulasi, frontend, chart, dan controls tanpa chat LLM:

```bash
cd /home/hitchgernn/projects/fomo-simulation-revised
GEMINI_API_KEY= GEMINI_API_KEYS= uvicorn backend.api.server:app --host 127.0.0.1 --port 8000 --reload
```

Endpoint backend:

```text
http://127.0.0.1:8000/state
http://127.0.0.1:8000/tick
```

Root `http://127.0.0.1:8000/` memang tidak dipakai dan bisa mengembalikan `404`.

### 2. Jalankan frontend

```bash
cd /home/hitchgernn/projects/fomo-simulation-revised/frontend
python -m http.server 5501
```

Buka:

```text
http://127.0.0.1:5501
```

Kalau port `5501` sudah dipakai, ganti ke port lain:

```bash
python -m http.server 5502
```

### 3. Jalankan dengan Gemini API key opsional

Untuk mengaktifkan chat agent panic:

```bash
cd /home/hitchgernn/projects/fomo-simulation-revised
GEMINI_API_KEY="your_api_key" uvicorn backend.api.server:app --host 127.0.0.1 --port 8000 --reload
```

Untuk banyak key:

```bash
GEMINI_API_KEYS="key_1,key_2,key_3" uvicorn backend.api.server:app --host 127.0.0.1 --port 8000 --reload
```

Jika key tidak ada, `chat_rotator=None` dan simulasi tetap berjalan.

## Cara Pakai Dashboard

1. Pastikan backend berjalan di `http://localhost:8000`.
2. Buka frontend.
3. Pilih preset:
   - `FOMO Pump`: shock off, lebih menonjolkan FOMO-buy contagion.
   - `Maker Dump`: market maker sell shock aktif secara probabilistik.
   - `ARB Spiral`: shock lebih agresif untuk mensimulasikan tekanan ke ARB.
4. Ubah parameter jika perlu.
5. Klik `Apply` untuk reset model dengan config baru.
6. Gunakan:
   - `Pause` / `Run` untuk menghentikan atau melanjutkan polling.
   - `Step` untuk menjalankan satu tick manual.

## Parameter Simulasi

| Parameter | Makna |
| --- | --- |
| `numRetail` | Jumlah agen ritel |
| `numInstitutional` | Jumlah agen institusi |
| `basePrice` | Harga dasar saham |
| `beta` | Sensitivitas social exposure untuk `N -> A` |
| `priceImpact` | Dampak order imbalance ke harga |
| `initialAwareFraction` | Proporsi awal agen ritel Aware |
| `initialPanicFraction` | Proporsi awal agen ritel Panic |
| `araPercent` | Batas kenaikan maksimal dari base price |
| `arbPercent` | Batas penurunan maksimal dari base price |
| `shockEnabled` | Mengaktifkan market maker dump |
| `shockProbability` | Probabilitas shock per tick saat cooldown selesai |
| `shockCooldownTicks` | Jarak minimal antar shock |
| `shockMinVolume` | Volume sell shock minimum |
| `shockMaxVolume` | Volume sell shock maksimum |
| `panicDrawdownThreshold` | Drawdown minimum untuk mulai memicu panic |
| `panicSensitivity` | Pengali probabilitas panic setelah drawdown melewati threshold |
| `panicSellMultiplier` | Pengali volume sell untuk agen Panic saat crash regime |
| `rng` | Seed opsional untuk pseudo-stochastic reproducibility |

## Model Stokastik

Project ini bukan deterministic murni. Ia memakai random draw di beberapa bagian:

- Network graph dibuat dari random seed.
- Urutan agent step diacak setiap tick.
- State awal agen ritel di-shuffle.
- Transisi `Neutral -> Aware` memakai probabilitas:

```text
P(Exposure) = 1 - (1 - beta)^k
```

Dengan:

- `beta`: sensitivitas informasi.
- `k`: jumlah tetangga yang berada dalam state `P`.

Market maker dump juga stokastik:

```text
shock happens if random() < shockProbability
shockVolume = random integer between shockMinVolume and shockMaxVolume
```

Retail panic akibat crash:

```text
panicPressure = max(0, drawdown - panicDrawdownThreshold) * panicSensitivity
panicProbability = clamp(panicPressure, 0, 1)
```

Jika `rng` diisi, hasil menjadi reproducible pseudo-stochastic. Artinya tetap random-draw based, tetapi seed yang sama cenderung menghasilkan pola yang sama.

## Price Discovery

Setiap tick:

1. Agen menghasilkan order buy/sell.
2. Market maker shock bisa menambahkan sell order besar.
3. Backend menghitung aggregate volume:

```text
imbalance = (buyVolume - sellVolume) / totalVolume
```

4. Harga berubah:

```text
candidatePrice = currentPrice * (1 + priceImpact * imbalance)
```

5. Harga di-clamp oleh ARA/ARB:

```text
araLimit = basePrice * (1 + araPercent)
arbLimit = basePrice * (1 - arbPercent)
```

## API

Base URL default:

```text
http://127.0.0.1:8000
```

### GET `/state`

Mengambil state saat ini tanpa menjalankan tick.

### GET `/tick`

Menjalankan satu tick simulasi, lalu mengembalikan state terbaru.

### POST `/reset`

Reset model dengan config baru.

Contoh body:

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

Response utama berisi:

- `tick`
- `config`
- `price`
- `orderBook`
- `market`
- `events`
- `stateCounts`
- `nodes`
- `chats`

## Testing dan Verifikasi

Compile backend:

```bash
python -m compileall backend
```

Syntax check frontend JavaScript:

```bash
node --check frontend/sketch.js
```

Smoke test API langsung dari Python:

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

### Frontend status `Offline`

Backend belum jalan atau tidak berada di `localhost:8000`.

Jalankan:

```bash
GEMINI_API_KEY= GEMINI_API_KEYS= uvicorn backend.api.server:app --host 127.0.0.1 --port 8000 --reload
```

### Port backend sudah dipakai

Cari proses yang memakai port, atau jalankan backend di port lain.

Jika backend diganti port, update `API_BASE` di `frontend/sketch.js`.

### Port frontend sudah dipakai

Ganti port static server:

```bash
cd frontend
python -m http.server 5502
```

### Chat kosong

Itu normal jika tidak ada Gemini API key. Semua fitur simulasi, chart, network graph, dan shock tetap berjalan.

### Chart tidak muncul

Pastikan browser bisa mengakses CDN Chart.js:

```text
https://cdn.jsdelivr.net/npm/chart.js
```

Jika offline penuh, download Chart.js dan p5.js ke folder frontend, lalu ubah script tag di `index.html`.

## Development Notes

- Ikuti aturan commit di `COMMIT_CONVENTION.md`.
- Gunakan Conventional Commits.
- Jangan campur perubahan engine, API, frontend, dan docs dalam satu commit besar.
- Backend tidak boleh bergantung pada UI.
- Frontend hanya polling API dan merender state.

## Limitasi Saat Ini

- LOB masih aggregate imbalance, belum full bid/ask level book.
- Market maker dump dimodelkan sebagai synthetic sell order, bukan agent Mesa terpisah.
- Simulasi ini untuk eksplorasi perilaku pasar, bukan prediksi harga nyata.
- Tidak ada persistence database; state hidup di memori proses FastAPI.
