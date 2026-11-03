# SilverSurf

A resilient, low-latency monitoring service and real-time dashboard for IBJA (India Bullion and Jewellers Association) Silver 999 benchmark rates.

SilverSurf tracks opening (AM) and closing (PM) physical market benchmark quotes from Mumbai, validates incoming data against historical baselines, and streams live updates to an editorial dashboard.

---

## Features

- **Automated Benchmark Scraping:** Adaptive scheduler tuned to official publication windows with exponential backoff and SHA-256 snapshot deduplication.
- **Validation Pipeline:** Anomaly detection (price boundaries, whole-rupee validation, and day-over-day price spike quarantine).
- **Real-Time Streaming:** Server-Sent Events (SSE) push live benchmark publications and revisions directly to connected clients.
- **Warm Editorial UI:** Clean, responsive interface featuring interactive price trends, session archives, CSV exports, unit conversions (kg, 10g, g), and derived +3% GST calculations.
- **Containerized & Hardened:** Non-root Docker containers, loopback-restricted port bindings, and security-header-enabled Nginx reverse proxy.

---

## Tech Stack

- **Backend:** Python 3.12, FastAPI, SQLite (aiosqlite / WAL mode), httpx, selectolax
- **Frontend:** React 19, TypeScript, Vite, Tailwind CSS, Lucide icons
- **Infrastructure:** Docker, Docker Compose, Nginx

---

## Getting Started

### Prerequisites

- [Docker](https://www.docker.com/) & Docker Compose
- *Or* Python 3.12+ and Node.js 20+ for manual local development.

### Running with Docker (Recommended)

1. Clone and enter the repository:
   ```bash
   git clone https://github.com/<your-username>/silversurf.git
   cd silversurf
   ```

2. Start the services:
   ```bash
   docker compose up --build
   ```

3. Access the services:
   - **Web Dashboard:** [http://localhost:3000](http://localhost:3000)
   - **Backend API & Swagger Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)

---

### Local Development

#### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Run backend tests:
```bash
pytest tests/ -v
```

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

Build frontend for production:
```bash
npm run build
```

---

## API Overview

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/v1/silver/latest` | Most recent valid published Silver 999 benchmark rate |
| `GET` | `/v1/silver/stream` | Server-Sent Events stream for live rate publications |
| `GET` | `/v1/silver/{date}` | Benchmark rate for a specific date (`YYYY-MM-DD`) |
| `GET` | `/v1/silver` | Historical rates with pagination and CSV export (`?format=csv`) |
| `GET` | `/v1/health` | Operational health, scheduler mode, and quarantine status |
| `POST` | `/v1/silver/quarantine/{id}/approve` | Approve a quarantined anomalous record (admin auth required) |

---

## Attribution & Disclaimer

Benchmark rates are sourced from the [India Bullion and Jewellers Association Ltd. (IBJA)](https://ibjarates.com/). SilverSurf is an independent open-source tool for informational and tracking purposes.
