#!/usr/bin/env python3
"""
Download AGMARKNET commodity price data for India.
Falls back to generating realistic synthetic data if the API is unavailable.
Run from repo root: python scripts/download_agmarknet_data.py
"""

import os
import sys
import requests
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)

# ── paths ──────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "raw"
OUT_FILE = OUT_DIR / "agmarknet_prices_india.csv"

# ── data.gov.in source ─────────────────────────────────────────────────────────
API_ENDPOINT = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"

INDIAN_MARKETS = {
    "Azadpur": {"state": "Delhi", "district": "Delhi"},
    "Vashi": {"state": "Maharashtra", "district": "Mumbai"},
    "Koyambedu": {"state": "Tamil Nadu", "district": "Chennai"},
    "Devaraja": {"state": "Karnataka", "district": "Mysore"},
    "Lasalgaon": {"state": "Maharashtra", "district": "Nashik"},
    "Bowenpally": {"state": "Telangana", "district": "Hyderabad"},
    "Gultekdi": {"state": "Maharashtra", "district": "Pune"},
    "Jalandhar": {"state": "Punjab", "district": "Jalandhar"},
    "Indore": {"state": "Madhya Pradesh", "district": "Indore"},
    "Patna": {"state": "Bihar", "district": "Patna"},
}

COMMODITIES = {
    "Tomato": {"base": 2000, "vol": 0.35},
    "Onion": {"base": 1500, "vol": 0.30},
    "Potato": {"base": 1200, "vol": 0.20},
    "Wheat": {"base": 2200, "vol": 0.10},
    "Rice (Paddy)": {"base": 2000, "vol": 0.12},
    "Maize": {"base": 1800, "vol": 0.15},
    "Soybean": {"base": 4500, "vol": 0.18},
    "Chana (Chickpea)": {"base": 5000, "vol": 0.16},
    "Moong": {"base": 7000, "vol": 0.20},
    "Mustard": {"base": 5500, "vol": 0.14},
}

def try_api_download() -> bool:
    """Download the AGMARKNET CSV directly from data.gov.in API."""
    api_key = os.environ.get("AGMARKNET_API_KEY")
    if not api_key:
        log.warning("AGMARKNET_API_KEY environment variable not set.")
        return False
        
    log.info("Trying data.gov.in API download …")
    try:
        # For simplicity, we just do one large request up to limit. 
        # In a full sync, pagination logic would be here.
        params = {
            "api-key": api_key,
            "format": "csv",
            "limit": "10000",
            "offset": "0"
        }
        r = requests.get(API_ENDPOINT, params=params, timeout=30)
        r.raise_for_status()
        
        # Save temp output
        temp_file = OUT_DIR / "agmarknet_temp.csv"
        with open(temp_file, "wb") as f:
            f.write(r.content)
            
        df = pd.read_csv(temp_file, low_memory=False)
        
        # Rename and shape columns to match the standard schema
        df = df.rename(columns={
            "arrival_date": "date"
        })
        df["unit"] = "Quintal"
        df["currency"] = "INR"
        df["pricetype"] = "Wholesale"
        df["price"] = df["modal_price"]
        df["arrival_tonnes"] = np.nan # Optional if not provided by API directly
        
        # Keep necessary columns, adding defaults if missing
        cols_to_keep = ["date", "state", "district", "market", "commodity", "variety", 
                        "unit", "currency", "pricetype", "price", "min_price", "max_price", "arrival_tonnes"]
        for col in cols_to_keep:
            if col not in df.columns:
                df[col] = np.nan
                
        df = df[cols_to_keep]
        df.to_csv(OUT_FILE, index=False)
        temp_file.unlink()
        
        log.info(f"  ✓ API: {len(df):,} rows → {OUT_FILE}")
        return True
    except Exception as e:
        log.warning(f"  API download failed: {e}")
        return False


def get_seasonal_factor(month: int) -> float:
    """Calculate seasonal factor based on Kharif (Jun-Oct), Rabi (Nov-Mar), Zaid (Apr-May)."""
    # Simply using a sine wave approach modified for standard seasons 
    # Kharif harvest typically late (Oct-Nov) leading to lower prices
    # Rabi harvest typically (Mar-Apr)
    # Zaid harvest typically (May-Jun)
    # For now, let's keep a generic two peak seasonal factor
    return 1 + 0.15 * np.sin(2 * np.pi * (month - 3) / 12)

def generate_synthetic_data() -> None:
    """
    Generate realistic Indian market food price data (2018-present).
    """
    log.info("Generating synthetic AGMARKNET-schema data …")
    rng = np.random.default_rng(42)
    rows = []

    start = datetime(2018, 1, 1)
    end   = datetime.now().replace(day=1)
    months = []
    cur = start
    while cur <= end:
        months.append(cur)
        # advance one month
        m = cur.month + 1
        y = cur.year + (m > 12)
        cur = cur.replace(year=y, month=(m - 1) % 12 + 1, day=1)

    for market_name, market_info in INDIAN_MARKETS.items():
        for commodity, meta in COMMODITIES.items():
            price = float(meta["base"])
            for dt in months:
                seasonal = get_seasonal_factor(dt.month)
                # annual inflation ~5 %
                annual_factor = 1.05 ** ((dt.year - 2018) + dt.month / 12)
                # random walk noise
                shock = rng.normal(1.0, meta["vol"] / 4)
                price = max(
                    meta["base"] * 0.4,
                    price * seasonal * shock,
                )
                
                final_price = round(price * annual_factor, 2)
                min_p = round(final_price * 0.9, 2)
                max_p = round(final_price * 1.1, 2)
                
                rows.append({
                    "date":      dt.strftime("%Y-%m-%d"),
                    "state":     market_info["state"],
                    "district":  market_info["district"],
                    "market":    market_name,
                    "commodity": commodity,
                    "variety":   "FAQ",  # Fair Average Quality
                    "unit":      "Quintal",
                    "currency":  "INR",
                    "pricetype": "Wholesale",
                    "price":     final_price,
                    "min_price": min_p,
                    "max_price": max_p,
                    "arrival_tonnes": round(rng.uniform(10, 500), 1),
                })

    df = pd.DataFrame(rows)
    df.to_csv(OUT_FILE, index=False)
    log.info(f"  ✓ Synthetic: {len(df):,} rows → {OUT_FILE}")


def validate_output() -> None:
    df = pd.read_csv(OUT_FILE)
    required = {"date", "market", "commodity", "price"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Output CSV missing columns: {missing}")
    log.info(
        f"Validation OK — {len(df):,} rows, "
        f"{df['commodity'].nunique()} commodities, "
        f"{df['market'].nunique()} markets, "
        f"date range {df['date'].min()} → {df['date'].max()}"
    )


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    if OUT_FILE.exists():
        size_kb = OUT_FILE.stat().st_size / 1024
        log.info(f"Existing file found ({size_kb:.0f} KB). Delete to re-download.")
        validate_output()
        return

    success = try_api_download()
    if not success:
        log.warning("API download failed — using synthetic data.")
        generate_synthetic_data()

    validate_output()
    log.info("Done ✓")


if __name__ == "__main__":
    main()
