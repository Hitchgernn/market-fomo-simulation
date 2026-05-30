TAHAP 1: Simpan File architecture.md (MiroFish-Style)

Buat satu file architecture.md di folder proyekmu dan tempel cetak biru ini. Codex akan membacanya sebagai pedoman struktur repositori yang ketat.
Markdown

# FOMO Market Simulation - Multi-Agent Architecture (MiroFish-Style)

## 1. Tujuan Sistem & Separation of Concerns
Sistem simulasi pasar saham berbasis agen dengan arsitektur decoupled. Backend bertugas penuh menjalankan logika simulasi berat (Mesa), sementara Frontend (p5.js) murni bertugas merender visualisasi di browser untuk menghilangkan bottleneck rendering (lag).

## 2. Struktur Repository
```text
fomo-market-sim/
├── backend/
│   ├── engine/
│   │   ├── model.py         # Logika makro, Order Book, ARA/ARB
│   │   ├── agent.py         # Perilaku mikro, transisi stokastik N -> A -> P
│   ├── api/
│   │   ├── server.py        # FastAPI server (Entry point backend)
│   ├── llm/
│   │   ├── rotator.py       # API Key Load Balancer (Round-robin)
│   ├── requirements.txt
├── frontend/
│   ├── index.html           # Dashboard UI murni (HTML/CSS)
│   ├── sketch.js            # Logika p5.js untuk merender network graph
├── architecture.md          # Dokumen pedoman AI
├── .env                     # Konfigurasi kunci API (Gemini/OpenRouter)

3. Teori & Matematika (Micro-Laws)

Model diadaptasi dari "A Differential Equation Model for the Dynamics of Youth Gambling". Terdapat 3 status agen: Neutral (N), Aware (A), Panic/FOMO (P).
Peluang stokastik transisi N -> A dipicu oleh kontagion sosial di jaringan:
P(Exposure) = 1 - (1 - \beta)^k
Di mana \beta adalah sensitivitas informasi, dan k adalah jumlah tetangga di graph yang panik (P).
4. Mekanisme Pasar (Macro-Laws)

    Limit Order Book: Menghitung order imbalance.

    Auto Rejection Atas (ARA): Batas harian maksimal naik +25%.

    Auto Rejection Bawah (ARB): Batas harian maksimal turun -15%.

5. Integrasi LLM (AI Chat)

Agen ritel yang berstatus Panic (P) memiliki peluang 5% setiap tick untuk menghasilkan chat slang ("to the moon", "cutloss"). LLM Rotator harus menangani limit API (Error 429) secara otomatis.


---

### TAHAP 2: Prompt Codex (Eksekusi Modular)

Buka sesi obrolan baru dengan Codex dan jalankan *prompt* ini secara berurutan.

#### 🛠️ Prompt 1: Membangun Backend Engine (Logika Mesa)
> **Instruksi:**
> Baca file `architecture.md` untuk memahami konteks dan struktur folder proyek.
> Tugas pertamamu: Buat isi file `backend/engine/agent.py` dan `backend/engine/model.py`.
> 
> Di `agent.py`, buat class `RetailInvestor` dan `InstitutionalInvestor` menggunakan struktur Mesa. Terapkan logika probabilitas transisi $P(\text{Exposure})$ pada fungsi `step()`.
> 
> Di `model.py`, buat class `StockMarketModel` menggunakan `NetworkGrid`. Terapkan mekanisme penghitungan harga *Limit Order Book* sederhana serta batasan persentase ARA dan ARB.
> Tulis Python backend murni. Jangan pedulikan UI atau API dulu.

#### 🔌 Prompt 2: Membangun Backend LLM (Rotator)
> **Instruksi:**
> Sekarang, bangun file `backend/llm/rotator.py`.
> Buat modul `AgentChatRotator` menggunakan `google-generativeai`. Modul ini menerima *list* kunci API dan menggunakan taktik *round-robin* `try-except`. Jika API pertama gagal/limit 429, otomatis pindah ke API berikutnya.
> 
> Setelah selesai, perbarui kode `backend/engine/agent.py` sebelumnya. Masukkan logika agar agen berstatus 'P' memiliki probabilitas 5% untuk memanggil rotator ini demi memproduksi teks obrolan slang, dan menyimpannya di variabel *state* model.

#### 🚀 Prompt 3: Membangun Backend Server (FastAPI)
> **Instruksi:**
> Mari selesaikan *backend* dengan membuat titik komunikasi (API). Buat file `backend/api/server.py` menggunakan `FastAPI` (jangan gunakan Streamlit).
> 
> Buat sebuah *endpoint* `GET /tick` yang akan melangkah (menjalankan `model.step()`) satu kali dalam simulasi Mesa setiap kali dipanggil, lalu mengembalikan data respons JSON utuh berisi:
> - Harga saham terkini dan indikator ARA/ARB.
> - Data node agen (ID, warna status N/A/P, dan daftar koneksi tetangga).
> - Teks obrolan baru (jika ada yang digenerate oleh Gemini di *tick* tersebut).
> Pastikan *server* menggunakan *CORS middleware* agar bisa diakses oleh *frontend* terpisah.

#### 🎨 Prompt 4: Membangun Frontend (UI + p5.js)
> **Instruksi:**
> Fokus pada folder `frontend/`. Kita butuh desain visualisasi yang ringan di *browser*. 
> 
> 1. Buat `frontend/index.html` dengan desain dasbor *Dark Mode* siber-finansial. Buat satu area grafik statis (atau siapkan div untuk Chart.js) dan satu *container div* khusus untuk visualisasi jaring p5.js. Tambahkan kolom obrolan (chat feed) di sisi kanan.
> 2. Buat `frontend/sketch.js` menggunakan library `p5.js`. Tulis logika untuk memanggil API `GET http://localhost:8000/tick` secara berulang (misalnya dengan fungsi `setInterval`).
> 3. Gambar *node* dan koneksi jaringan menggunakan kanvas p5.js berdasarkan JSON yang diterima. Warnai node: Hijau (N), Kuning (A), Merah (P). Jika node mengeluarkan chat, buat efek *pulse* di kanvas dan dorong teks obrolannya ke dalam *div chat feed* di HTML.

---

Dengan arsitektur *frontend* dan *backend* yang terpisah ini, *rendering* animasi visual ditanggung oleh mesin peramban web (*browser*), sementara kalkulasi berat tetap aman berada di mesin Python murni. 

Apakah kamu mau menggunakan metode *HTTP polling* biasa untuk komunikasi data *tick-by-tick* antara antarmuka dan *backend*, atau kamu ingin kita