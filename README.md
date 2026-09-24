# 🌾 KisanGuard AI

> **Agricultural intelligence for India** — crop price conveyance, crop price forecasting (using quant strategies), market intelligence, and weather insights & forecasts for smallholder farmers, delivered via a **WhatsApp Voice Bot** (powered by Bhashini) and a Streamlit dashboard.

*Adapted for the **Hack The Weather 2026** hackathon (from the original AgriGuard architecture).*

## Objectives

KisanGuard AI exists to serve four things:

1. **Crop price conveyance** — get price data to farmers seamlessly via a WhatsApp Voice Bot (text or regional language voice notes).
2. **Crop price prediction / forecasting** — XGBoost forecasting per crop and Indian Mandi, factoring in Kharif/Rabi seasons and market arrivals.
3. **Market intelligence** — cross-mandi comparisons, arbitrage signals, biggest movers, national summaries.
4. **Weather insights & forecasts** — historical and forecast weather, conveyed alongside price signals.

## Status at a glance

| Layer | State |
|---|---|
| FastAPI backend — forecasts, markets, WhatsApp | **Working.** Wired into `main.py`, backed by Indian AGMARKNET CSV. |
| Streamlit dashboard | **Working.** Reads from the backend over HTTP. |
| Price forecasting (backtested ensemble / XGBoost) | **Working**, with Kharif/Rabi seasonal features and calibrated intervals (INR). |
| WhatsApp Bot / Bhashini Integration | **Working.** Webhook handler at `/whatsapp/webhook` and local simulator at `/whatsapp/simulate`. |
| Weather data collection | **Working as a standalone script**, not yet joined into the forecasting features. |
| `quant/` package | **Working, fully tested.** Backtesting, prediction intervals, and risk metrics. |

## Problem

Indian farmers face compounding challenges:

- **Price blindness** — no reliable way to know if today is a good day to sell at the local APMC Mandi.
- **Market fragmentation** — price gaps between mandis go unexploited because farmers lack data.
- **Language barriers** — traditional apps require literacy, locking out many smallholder farmers.

## Solution

| Module | What it does | How |
|---|---|---|
| **Price Conveyance** | Delivers current and predicted prices to farmers over WhatsApp | WhatsApp Business API + Bhashini for Voice-to-Text translation in Hindi/Marathi/etc. |
| **Price Forecasting** | Predicts crop prices weeks ahead, per mandi | XGBoost on AGMARKNET price history, factoring in Indian crop seasons. |
| **Market Intelligence** | Cross-market comparisons, biggest movers | FastAPI serving the AGMARKNET dataset with trend analytics. |

Accessible via a **Streamlit Dashboard** and a **WhatsApp interface**
(`/whatsapp/simulate` locally; a real bot requires a WhatsApp Business token).

## Architecture

```
┌───────────────────────────────────────────────────────┐
│  Streamlit Frontend  (port 8501)                       │
│  Home · Dashboard · Price Forecast · WhatsApp Sim      │
└────────────────────┬─────────────────────────────────── ┘
                      │ HTTP / REST
┌────────────────────▼─────────────────────────────────── ┐
│  FastAPI Backend  (port 8000)                            │
│  /forecasts/*  /markets/*  /whatsapp/*                   │
│  /api/v1/predict  /health                                 │
└──────┬─────────────┬──────────────┬───────────────────── ┘
       │              │              │
  XGBoost         Prophet        SQLite (dev)
  .pkl in ml/models/  fallback       / MySQL (prod)
       │
  data/raw/agmarknet_prices_india.csv  ←  scripts/download_agmarknet_data.py
```

## Quick Start

### 1. Clone and set up environment

```bash
git clone https://github.com/YourOrg/KisanGuard.git
cd AgriGuard
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp config/.env.example config/.env
# edit config/.env to add your AGMARKNET, WhatsApp, and Bhashini API keys
```

### 3. Run with Docker Compose (Recommended)

```bash
docker compose up -d --build
```
This will automatically download the Indian dataset, train the XGBoost models, and start the API and frontend.
- Dashboard: http://localhost:8501
- API docs:  http://localhost:8000/docs

### 4. Run Manually (Without Docker)

```bash
# Terminal 1 — Download data and train model
python scripts/download_agmarknet_data.py
python scripts/train_models.py

# Terminal 2 — Start backend
uvicorn backend.app.main:app --reload --port 8000

# Terminal 3 — Start frontend
cd frontend && streamlit run Home.py --server.port 8501
```

## Data Sources

- **AGMARKNET (data.gov.in)** — Daily crop prices from APMC mandis across India.
- **Open-Meteo** — Free daily weather + 16-day forecast.
- **Bhashini ULCA API** — National Language Translation Mission (Speech-to-Text & Text-to-Speech).

## Roadmap for Hackathon

- [ ] Connect the Bhashini API stubs to the live ULCA translation endpoints
- [ ] Connect the WhatsApp webhook stubs to a live Twilio Sandbox / Meta App
- [ ] Join weather data (monsoon lag) into the price-forecasting feature set
- [ ] Add counterfeit seed/fertilizer detection via WhatsApp photo + OCR

## License

Dual-licensed: **AGPL-3.0** for open-source/non-commercial use.
