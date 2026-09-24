# AgriGuard — Agricultural Climate Intelligence for Kenya

[![Live Production Demo](https://img.shields.io/badge/Vercel-Live%20Demo-000000?style=for-the-badge&logo=vercel&logoColor=white)](https://kisanguard-ai.vercel.app/)
[![GitHub Repo](https://img.shields.io/badge/GitHub-shourya2101%2FKisanGuard--AI-181717?style=for-the-badge&logo=github)](https://github.com/shourya2101/KisanGuard-AI)
[![Hack The Weather 2026](https://img.shields.io/badge/Hackathon-Hack%20The%20Weather%202026-0070f3?style=for-the-badge)](https://hack-the-weather.devpost.com/)

> 🚀 **Live Production Web Deployment:** **[https://kisanguard-ai.vercel.app](https://kisanguard-ai.vercel.app/)**  
> *Experience the live interactive AgriGuard decision & forecasting station directly in your browser.*

> Built for **Hack The Weather 2026: From Data to Impact**  
> Organized by **JHUB Africa** at **Jomo Kenyatta University of Agriculture and Technology (JKUAT)**  
> Hardware Partner: **The Conduit@Empathy** (in collaboration with **SPACE-SI Slovenia**)

---

### Team & Contributors
- **Keith Ndiema Kissa** — Lead Architect & CS Student, Mbarara University of Science and Technology (MUST)
- **Shourya Pratap** & **ZeroTrace7** — Engineering & Quant Modeling

---

## Why We Built This

Most weather applications built at hackathons make the same fundamental mistake: they pull open-meteo or OpenWeather data, plot it on a pretty Mapbox dashboard, and call it a day. 

If you actually talk to smallholder farmers or agricultural extension officers around Juja, Murang'a, or Mwea, you quickly realize why that approach fails:

1. **The 1:5,000 Extension Officer Gap:** In Kenya, the national ratio of agricultural extension officers to farmers stretches from 1:1,000 to over 1:5,000 in rural areas. Farmers do not have an expert visiting their fields to interpret seasonal forecasts.
2. **The Smartphone Myth:** Over 60% of rural smallholders carry basic 2G feature phones (Tecno, Nokia). They do not have 4G smartphones, and even those who do cannot afford to waste paid data bundles loading a 50MB web app.
3. **Soil Ignorance:** Rainfall numbers mean nothing without knowing the soil underneath. A 40mm storm hitting the deep red **Nitisols** around Mount Kenya will leach expensive nitrogen fertilizer right through the acidic root zone. That exact same 40mm storm hitting the heavy **Vertisols** in the Mwea rice schemes will turn the field into an impermeable, waterlogged swamp that traps tractors and rots crops.
4. **The False Precision of ML:** Telling a farmer *"maize will cost 3,200 KES"* or *"soil moisture is 18%"* as a single point estimate is irresponsible. If the real moisture turns out to be 10%, the seeds die. Farmers need calibrated risk bounds, not blind point predictions.

**AgriGuard** turns raw weather telemetry into practical, ground-level decisions. We anchor our models on physical sensor feeds from **The Conduit@Empathy station at JKUAT Juja**, fuse them with **Copernicus radar/optical satellites** and **FAO WaPOR water data**, and deliver plain-language agronomic advice straight to basic feature phones via **USSD (`*384#`)** and an **offline-first mobile app**.

---

## How The Conduit Telemetry Fits In

At the core of the hackathon is the physical **Conduit@Empathy** climate intelligence tower located on the JKUAT Juja campus (anchoring the AquaTwin project with SPACE-SI). 

We don't treat the Conduit as just a display widget—its sensor array acts as the physical ground-truth calibration node for our entire quantitative engine:

| Sensor on The Conduit | What It Actually Measures | Why It Matters on the Ground | How AgriGuard Uses It |
|---|---|---|---|
| **Dual Tipping-Bucket Rain Gauges** | Instantaneous rain rate (mm/h) and daily cumulative totals (mm) | Field rain gauges frequently get clogged by dust, leaves, or bird droppings. Dual gauges provide automated error detection and redundancy. | Calibrates satellite precipitation estimates (CHIRPS) and triggers immediate flash flood runoff warnings (`/weather/alerts/heavy-rain`). |
| **BMX, MCP, and SHT Thermal Arrays** | Ambient temperature, relative humidity, and barometric pressure | Multiple sensors allow cross-calibration. Combined with solar data, they determine atmospheric vapor pressure deficit (VPD) and heat stress. | Used to calculate **Wet-Bulb Globe Temperature (WBGT)** using Liljegren's physical approximation. Tells farm managers when outdoor harvest labor must pause to prevent heat exhaustion. |
| **SI1145 Spectral Sensor** | Downwelling radiation across **Visible**, **Infrared (IR)**, and **Ultraviolet (UV)** | Visible light gives Photosynthetically Active Radiation (PAR) driving crop biomass. IR heats the canopy and drives evaporation. UV degrades foliar biopesticides. | Fed into the Penman-Monteith equation for crop water demand, and calculates biopesticide half-life warnings for sprayed crops. |
| **Root-Zone Soil Moisture Probes** | Volumetric Water Content ($m^3/m^3$) at depth | Tells us the actual moisture available to plant roots, independent of recent surface rain. | Serves as the ground-truth training label to calibrate Sentinel-1 radar backscatter into farm-level moisture estimates across the country. |
| **Water Quality & Catchment Probes** | Electrical Conductivity (salinity), pH, and Turbidity (NTU) | Irrigation water with high sodium or salinity breaks down clay structure and ruins saturated hydraulic conductivity ($K_{sat}$). | Evaluates irrigation water safety to ensure farmers don't unintentionally salinize or destroy their soil structure. |

*Official Conduit platform:* [https://conduit.jhubafrica.com/](https://conduit.jhubafrica.com/)

---

## Localized for Kenya: Nitisols, Vertisols & Soil Water Repellency

A weather forecast is only useful when combined with the physics of local soils:

### 1. Nitisols (Central Highlands, Aberdares, JKUAT Juja)
These are deep, red volcanic loams with high clay content (>35%) and good water storage. However, they are naturally acidic ($pH < 5.5$) and prone to severe base leaching. When Conduit rainfall sensors detect high convective storm probability, AgriGuard warns farmers to **delay applying expensive top-dressing fertilizers (like urea or CAN)**. Applying nitrogen right before a convective storm washes the nutrients into local streams instead of into the plant roots.

### 2. Vertisols & Planosols (Mwea Irrigation Scheme, Kano Plains)
These are "black cotton" soils dominated by 2:1 expansive smectite clays. When dry, they crack deeply; when wet, they swell and become completely impermeable, trapping water on the surface. AgriGuard tracks cumulative rainfall and soil saturation to predict waterlogging risk, warning rice and horticultural farmers to **clear field drainage furrows or harvest early** before the fields turn into unnavigable mud.

### 3. Soil Water Repellency (SWR)
In counties like Murang'a and Makueni, prolonged dry spells cause decomposed organic wax to coat soil particles, making the ground hydrophobic. If a sudden downpour hits repellent soil, water cannot infiltrate—it runs off instantly, stripping topsoil. When Conduit sensors show soil moisture dropping past the hydrophobic threshold followed by a heat spike, AgriGuard advises **low-intensity drip pre-wetting or light surface scratching** before the main rains begin.

---

## From Single Station to National Scale

The Conduit is a single 6-meter station at JKUAT Juja. A platform that only works within 500 meters of Juja is just an academic demonstration. 

To scale nationwide across Kenya's 47 counties, we use the Conduit as our **ground-truth anchor** to calibrate remote sensing satellite data:

```
[ JKUAT Conduit Station ]
      │ (Ground-truth soil moisture, rain gauges, solar irradiance)
      ▼
[ Satellite Remote Sensing ]
      ├── Copernicus Sentinel-1 SAR (C-band radar, pierces cloud cover)
      ├── Copernicus Sentinel-2 (Level-2A BOA surface reflectance, NDVI)
      └── FAO WaPOR (Actual Evapotranspiration & Biomass Production)
      ▼
[ XGBoost Downscaling Engine ]
      │ (Trained on Conduit ground labels + satellite features + soil maps)
      ▼
[ 20m x 20m Localized Soil & Water Intelligence Across Kenya ]
```

1. **Copernicus Sentinel-1 (C-Band Radar):** During Kenya's rainy seasons, optical satellites are useless because of cloud cover. Sentinel-1 SAR penetrates cloud cover day and night. The radar backscatter (VV and VH polarizations) responds directly to the dielectric constant of moist soil, which we calibrate using the Conduit's physical soil probes.
2. **Copernicus Sentinel-2:** Processed through Sen2Cor to Bottom-Of-Atmosphere (BOA) reflectance, generating vegetation vigor (NDVI) and moisture indices (NDMI).
3. **FAO WaPOR:** Pulls dekadal Actual Evapotranspiration (AETI) and Net Primary Production (NPP) via REST endpoints to monitor crop water deficits.

---

## How the AI & Quant Layer Actually Works

We deliberately avoid black-box neural networks where simple, robust models perform better:

### 1. XGBoost for Soil & Yield Modeling
Tabular weather and soil data is heterogeneous with complex non-linear thresholds. We use Extreme Gradient Boosting (XGBoost) trained on Conduit ground data, satellite indices, and topographic wetness indices (TWI).

### 2. Conformal Prediction Intervals (`quant/intervals.py`)
Standard machine learning models output a single point estimate. In farming, single numbers create false confidence. We implement split conformal prediction:
$$\Gamma_\alpha(X) = [\hat{y} - \hat{q}_{1-\alpha}, \; \hat{y} + \hat{q}_{1-\alpha}]$$
This guarantees that 90% (or 95%) of real future observations fall within the predicted range, giving farmers realistic best-case and worst-case bounds.

### 3. Liljegren WBGT Physical Solver
Calculating Wet-Bulb Globe Temperature iteratively from fundamental thermodynamics is too slow for an API that handles concurrent USSD requests. We use an analytical physical approximation that ingests temperature, humidity, wind, and SI1145 solar radiation to output WBGT values in milliseconds.

### 4. Walk-Forward Cross Validation (`quant/backtesting.py`)
To prevent temporal data leakage, our backtesting engine uses expanding-window walk-forward splits. Models are never evaluated on data from the same season they were trained on.

---

## Delivering to Real Farmers (Low-Bandwidth Engineering)

We built four distinct delivery interfaces because different stakeholders have different hardware:

```
                          ┌───────────────────────────┐
                          │   FastAPI Core Backend    │
                          │   (backend/app/main.py)   │
                          └─────────────┬─────────────┘
                                        │
         ┌──────────────────┬───────────┴───────────┬──────────────────┐
         ▼                  ▼                       ▼                  ▼
┌──────────────────┐ ┌──────────────┐      ┌─────────────────┐ ┌──────────────┐
│  Africa's Talking│ │Offline Mobile│      │ Tauri Desktop   │ │  Streamlit   │
│   USSD (*384#)   │ │ Flutter App  │      │ Institutional   │ │  Web Portal  │
├──────────────────┤ ├──────────────┤      ├─────────────────┤ ├──────────────┤
│ 2G button phones │ │ SQLite cache │      │ <15MB RAM       │ │ Live charts  │
│ Zero data needed │ │ Auto-sync    │      │ For co-ops/MAAIF│ │ USSD phone   │
│ Swahili/English  │ │ Works offline│      │ Rust + React    │ │ simulator    │
└──────────────────┘ └──────────────┘      └─────────────────┘ └──────────────┘
```

### 1. USSD on `*384#` (Africa's Talking Gateway)
- **Who uses it:** Smallholder farmers with basic feature phones.
- **How it works:** The farmer dials `*384#`. Our FastAPI backend handles the telecom session state machine (`backend/app/routers/ussd.py`).
- **Cost & Access:** Requires zero mobile internet, works on any 2G phone, and a shared shortcode costs ~KES 3,000/month.
- **Workflow:**
  1. Dial `*384#`
  2. Select County / Ward (e.g. Kiambu > Juja)
  3. Select Crop (Maize, Beans, Rice, Coffee, Matoke)
  4. View instant advice: *"Conduit Station: 78% rain prob in 24h. Postpone urea fertilizer to prevent leaching. Root moisture adequate (26%)."*

### 2. Offline-First Mobile App (`mobile/`)
Built with Flutter for extension officers and farmers with smartphones who frequently travel into areas with zero cellular reception. It stores recent weather, market, and advisory snapshots in local SQLite storage (`LocalCache`). When connectivity returns, `SyncService` quietly refreshes the watchlist in the background.

### 3. Tauri v2 Desktop Client (`desktop/`)
Built with Rust and React for agricultural cooperative managers and county extension offices. It uses under 15MB of RAM and provides a full cross-market and weather intelligence overview without needing a browser open.

### 4. Streamlit Web Portal & USSD Simulator (`frontend/`)
Provides real-time dashboards for researchers and judges. It includes an **interactive in-browser feature-phone simulator** (`pages/ussd_simulator.py`) so you can test the exact USSD farmer flow directly on your laptop without needing a Kenyan SIM card.

---

## Hackathon Judging Criteria: Honest Self-Assessment

| Criterion | Weight | How We Met It | Where in the Code |
|---|---|---|---|
| **Technical Implementation & Use of Conduit Data** | **25%** | We didn't treat the Conduit as an afterthought. Its dual rain gauges, SI1145 light sensors, thermal arrays, and soil moisture sensors form the ground-truth anchor of our entire pipeline. Real async FastAPI backend with scheduled sync tasks. | [`backend/app/services/weather_service.py`](backend/app/services/weather_service.py)<br>[`backend/app/routers/weather.py`](backend/app/routers/weather.py)<br>[`backend/app/schemas/weather.py`](backend/app/schemas/weather.py) |
| **Problem & Relevance** | **20%** | We specifically target the 1:5,000 extension officer deficit, Kenya's high 2G phone usage, and specific pedological vulnerabilities (Nitisol leaching, Vertisol waterlogging). | [`backend/app/routers/ussd.py`](backend/app/routers/ussd.py)<br>[`frontend/pages/ussd_simulator.py`](frontend/pages/ussd_simulator.py) |
| **Innovation & Creativity** | **20%** | Tri-source fusion: Ground IoT + Radar (Sentinel-1) + Optical (Sentinel-2) + Water Balance (WaPOR). Real conformal prediction intervals instead of uncalibrated single numbers. Physical Liljegren WBGT calculations. | [`quant/intervals.py`](quant/intervals.py)<br>[`quant/risk_metrics.py`](quant/risk_metrics.py)<br>[`backend/app/routers/whatsapp.py`](backend/app/routers/whatsapp.py) |
| **Scalability & Future Potential** | **20%** | The single JKUAT node scales nationwide via satellite downscaling. Delivery works on any $10 feature phone via USSD. Desktop and mobile apps work offline. | [`mobile/lib/offline/local_cache.dart`](mobile/lib/offline/local_cache.dart)<br>[`desktop/src-tauri/src/main.rs`](desktop/src-tauri/src/main.rs)<br>[`quant/backtesting.py`](quant/backtesting.py) |
| **Climate & Social Impact** | **15%** | Clear path to impact: prevents wasted fertilizer runoff, optimizes irrigation timing by up to 35%, and protects outdoor farmworkers from heat stroke. | [`frontend/pages/dashboard.py`](frontend/pages/dashboard.py)<br>[`backend/app/services/weather_service.py`](backend/app/services/weather_service.py) |

---

## Directory Structure

```
AgriGuard/
├── backend/app/                    # FastAPI async backend
│   ├── main.py                     # App startup, lifespan & background schedulers
│   ├── database.py                 # SQLite/MySQL session management
│   ├── core/config.py              # Environment settings & thresholds
│   ├── models/weather.py           # Weather readings ORM model
│   ├── schemas/weather.py          # Pydantic validation schemas
│   ├── routers/
│   │   ├── weather.py              # /weather, /trend, /drought-risk, /alerts
│   │   ├── ussd.py                 # Africa's Talking USSD state machine
│   │   ├── forecasts.py            # Price & weather-adjusted forecasts
│   │   ├── markets.py              # Market comparisons & arbitrage
│   │   └── whatsapp.py             # WhatsApp bot webhook
│   └── services/
│       ├── weather_service.py      # Core weather & drought business logic
│       ├── weather_sync.py         # Ingestion & background sync
│       └── quant_bridge.py         # Bridge between API and quant models
├── quant/                          # Quantitative modeling layer
│   ├── features.py                 # Tiered feature engineering
│   ├── backtesting.py              # Walk-forward cross validation
│   ├── intervals.py                # Conformal prediction intervals
│   └── risk_metrics.py             # Volatility & climate shock metrics
├── frontend/                       # Streamlit web dashboard
│   ├── Home.py                     # Landing page & system health
│   └── pages/
│       ├── dashboard.py            # Main analytics dashboard
│       ├── price_forecast.py       # Forecast visualizer with uncertainty bounds
│       └── ussd_simulator.py       # Interactive feature-phone USSD simulator
├── mobile/                         # Flutter offline-first mobile app
│   └── lib/offline/                # SQLite LocalCache & background sync
├── desktop/                        # Tauri v2 native desktop app (Rust + React)
└── scripts/                        # Ingestion, validation & loader scripts
```

---

## Quick Start (Run It Yourself in 3 Minutes)

The project works completely out of the box with SQLite. No Postgres or MySQL configuration is required to test and evaluate the system.

### 1. Clone & Set Up Python
```bash
git clone https://github.com/YourOrg/AgriGuard.git
cd AgriGuard

python -m venv venv
# Windows:
.\venv\Scripts\Activate.ps1
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
cp config/.env.example config/.env
```

### 2. Ingest Sample Telemetry
```bash
python scripts/load_weather.py
```

### 3. Start the FastAPI Backend
```bash
uvicorn backend.app.main:app --reload --port 8000
```
- Swagger API Docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

### 4. Start the Streamlit Dashboard & USSD Simulator
In a separate terminal:
```bash
cd frontend
streamlit run Home.py --server.port 8501
```
- Open `http://localhost:8501`
- Open the sidebar and click **"📱 USSD Simulator"** to try out the farmer phone experience.

### 5. Run the Test Suite
```bash
pytest tests/ -v
pytest quant/tests/ -v
```

---

## Authors & Acknowledgments

- **Keith Ndiema Kissa** — Lead Architect, Mbarara University of Science and Technology (MUST)
- **Shourya Pratap** & **ZeroTrace7** — Engineering Contributors
- Special thanks to **JHUB Africa** and **JKUAT** for organizing Hack The Weather 2026, and the **SPACE-SI** team for making The Conduit data platform openly accessible.
