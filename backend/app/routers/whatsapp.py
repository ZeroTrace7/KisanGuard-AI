"""
KisanGuard AI - whatsapp.py
WhatsApp gateway router for farmer access in India.

Works with Meta Cloud API for WhatsApp.
Farmers can check prices, forecasts, and market recommendations by sending messages.
"""

from fastapi import APIRouter, Request, HTTPException, Query, Response
from typing import Optional, Dict
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import logging
import httpx

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/whatsapp", tags=["WhatsApp"])

# ── Data Path ─────────────────────────────────────────────────────────────────
DATA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "data", "raw", "agmarknet_prices_india.csv"
)

# Default markets for quick lookup
DEFAULT_MARKETS = ["Azadpur", "Vashi", "Koyambedu", "Lasalgaon", "Bowenpally", "Gultekdi"]

# WhatsApp constants
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN", "dummy_token")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID", "dummy_phone_id")
VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "kisan_guard_verify")

# Simple in-memory session dict (phone_number -> session state)
sessions: Dict[str, dict] = {}


# ── Data helpers (lightweight) ────────────────────────────────────────────────

def load_data() -> pd.DataFrame:
    """Load and normalise Agmarknet price CSV."""
    try:
        df = pd.read_csv(DATA_PATH)
    except FileNotFoundError:
        return pd.DataFrame()

    df.columns = [c.strip().lower() for c in df.columns]
    rename_map = {}
    for col in df.columns:
        if "date" in col:
            rename_map[col] = "date"
        elif col in ("cmname", "commodity", "cm_name"):
            rename_map[col] = "commodity"
        elif col in ("mktname", "market", "mkt_name"):
            rename_map[col] = "market"
        elif col in ("price", "modal_price", "min_price", "max_price"):
            # prioritize modal_price or price
            if "price" not in rename_map or col == "modal_price":
                rename_map[col] = "price"
        elif col in ("cur", "currency", "currname"):
            rename_map[col] = "currency"
        elif col in ("unit", "um_name", "umname"):
            rename_map[col] = "unit"
    df.rename(columns=rename_map, inplace=True)

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df.dropna(subset=["date", "price"], inplace=True)
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df.dropna(subset=["price"], inplace=True)
    df["commodity"] = df["commodity"].str.strip().str.title()
    df["market"] = df["market"].str.strip().str.title()
    return df


def get_latest_price(df: pd.DataFrame, commodity: str, market: str) -> Optional[dict]:
    """Return latest price info for a commodity-market pair."""
    subset = df[
        (df["commodity"].str.lower() == commodity.lower()) &
        (df["market"].str.lower() == market.lower())
    ].sort_values("date")

    if subset.empty:
        return None

    latest = subset.iloc[-1]
    currency = str(latest.get("currency", "INR")) if "currency" in subset.columns else "INR"
    unit = str(latest.get("unit", "Quintal")) if "unit" in subset.columns else "Quintal"

    # Simple trend: compare last price to 30 days ago
    cutoff = latest["date"] - timedelta(days=30)
    past = subset[subset["date"] <= cutoff]
    trend_arrow = ""
    if not past.empty:
        old_price = float(past.iloc[-1]["price"])
        new_price = float(latest["price"])
        pct = ((new_price - old_price) / (old_price + 1e-9)) * 100
        if pct > 2:
            trend_arrow = f" 📈 +{abs(pct):.0f}%"
        elif pct < -2:
            trend_arrow = f" 📉 -{abs(pct):.0f}%"
        else:
            trend_arrow = " ➡️ stable"

    return {
        "price": round(float(latest["price"]), 0),
        "currency": currency,
        "unit": unit,
        "date": latest["date"].strftime("%d %b %Y"),
        "trend": trend_arrow,
    }


def get_market_ranking(df: pd.DataFrame, commodity: str) -> list[dict]:
    """Rank all markets by latest price for a commodity (highest first)."""
    markets = df[df["commodity"].str.lower() == commodity.lower()]["market"].unique()
    results = []
    for mkt in markets:
        record = get_latest_price(df, commodity, mkt)
        if record:
            results.append({"market": mkt, **record})
    return sorted(results, key=lambda x: x["price"], reverse=True)


def get_simple_forecast(df: pd.DataFrame, commodity: str, horizon: int = 7) -> dict:
    """
    Lightweight linear forecast — no Prophet dependency.
    Returns predicted direction and estimated price in N days.
    """
    subset = df[
        df["commodity"].str.lower() == commodity.lower()
    ].sort_values("date").tail(24)

    if len(subset) < 4:
        return {"available": False}

    prices = subset["price"].values
    x = np.arange(len(prices))
    slope, intercept = np.polyfit(x, prices, 1)
    future_price = intercept + slope * (len(prices) + horizon)
    current_price = prices[-1]
    pct_change = ((future_price - current_price) / (current_price + 1e-9)) * 100

    currency = str(subset.iloc[-1].get("currency", "INR")) if "currency" in subset.columns else "INR"
    unit = str(subset.iloc[-1].get("unit", "Quintal")) if "unit" in subset.columns else "Quintal"

    if pct_change > 3:
        direction = f"RISE to ~₹{max(future_price,0):,.0f}/{unit}"
        advice = "Consider waiting to sell."
    elif pct_change < -3:
        direction = f"FALL to ~₹{max(future_price,0):,.0f}/{unit}"
        advice = "Sell soon for better price."
    else:
        direction = "stay STABLE"
        advice = "Good time to sell."

    return {
        "available": True,
        "current_price": round(float(current_price), 0),
        "direction": direction,
        "pct_change": round(pct_change, 1),
        "advice": advice,
        "currency": currency,
        "unit": unit,
    }


def get_top_movers(df: pd.DataFrame, top_n: int = 3) -> dict:
    """Get top price gainers and losers over the last 30 days for display."""
    latest_date = df["date"].max()
    if pd.isna(latest_date):
        return {"gainers": [], "losers": []}
        
    cutoff = latest_date - timedelta(days=30)

    movers = []
    for (commodity, market), group in df.groupby(["commodity", "market"]):
        group = group.sort_values("date")
        recent = group[group["date"] >= cutoff]
        past = group[group["date"] < cutoff]
        if recent.empty or past.empty:
            continue
        latest_p = float(recent.iloc[-1]["price"])
        prev_p = float(past.iloc[-1]["price"])
        pct = ((latest_p - prev_p) / (prev_p + 1e-9)) * 100
        movers.append({"commodity": commodity, "market": market, "pct": round(pct, 1)})

    if not movers:
        return {"gainers": [], "losers": []}

    movers_df = pd.DataFrame(movers)
    gainers = movers_df.nlargest(top_n, "pct").to_dict(orient="records")
    losers = movers_df.nsmallest(top_n, "pct").to_dict(orient="records")
    return {"gainers": gainers, "losers": losers}


def fuzzy_match_commodity(df: pd.DataFrame, user_input: str) -> Optional[str]:
    """
    Find the best matching commodity name from user's typed input.
    Handles partial matches.
    """
    user_clean = user_input.strip().lower()
    all_commodities = df["commodity"].unique()

    # Exact match first
    for c in all_commodities:
        if c.lower() == user_clean:
            return c

    # Starts-with match
    for c in all_commodities:
        if c.lower().startswith(user_clean):
            return c

    # Contains match
    for c in all_commodities:
        if user_clean in c.lower():
            return c

    return None


def truncate(text: str, limit: int = 4096) -> str:
    """Ensure WhatsApp response stays within character limit (WhatsApp allows up to 4096 chars)."""
    if len(text) <= limit:
        return text
    return text[:limit - 3] + "..."


# ── Bhashini Integration Stubs ────────────────────────────────────────────────

def process_voice_note(audio_url: str, source_lang: str = "hi") -> str:
    """
    Stub for Bhashini ASR API call.
    Downloads the audio from WhatsApp URL, sends it to Bhashini for transcription.
    
    Args:
        audio_url: The URL to the WhatsApp audio message.
        source_lang: The assumed language of the user (e.g., "hi" for Hindi).
        
    Returns:
        str: The transcribed text.
    """
    logger.info(f"Mock Bhashini ASR: Transcribing {audio_url} from {source_lang}")
    return "This is a transcribed voice note placeholder."


def text_to_speech(text: str, target_lang: str = "hi") -> Optional[str]:
    """
    Stub for Bhashini TTS API call.
    Converts text to an audio file URL to be sent back via WhatsApp.
    
    Args:
        text: The text to convert to speech.
        target_lang: The target language.
        
    Returns:
        Optional[str]: URL of the generated audio file.
    """
    logger.info(f"Mock Bhashini TTS: Synthesizing text to {target_lang}")
    return "https://example.com/mock_audio.ogg"


# ── WhatsApp Messaging Helpers ────────────────────────────────────────────────

async def send_whatsapp_message(phone_number: str, text: str):
    """Send a text message to a WhatsApp user using Meta Cloud API."""
    if WHATSAPP_TOKEN == "dummy_token":
        # In dev/simulation, we just log it
        logger.info(f"Mock sending WhatsApp to {phone_number}: {text}")
        return

    url = f"https://graph.facebook.com/v17.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": phone_number,
        "type": "text",
        "text": {"body": text}
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
        except Exception as e:
            logger.error(f"Failed to send WhatsApp message: {e}")


def get_main_menu() -> str:
    return (
        "🌱 *KisanGuard AI*\n"
        "India Farm Prices\n"
        "──────────────\n"
        "1️⃣ Check Crop Price\n"
        "2️⃣ Best Market to Sell\n"
        "3️⃣ Price Forecast\n"
        "4️⃣ Top Movers Today\n"
        "5️⃣ About KisanGuard AI\n\n"
        "Reply with a number to choose. Type *0* anytime to return here."
    )


# ── Menu State Machine ────────────────────────────────────────────────────────

def process_message(phone: str, text_in: str, df: pd.DataFrame) -> str:
    text_in = text_in.strip()
    
    # Always reset to main menu on 0
    if text_in == "0" or phone not in sessions:
        sessions[phone] = {"step": "main"}
        if text_in != "0" and text_in not in ["1", "2", "3", "4", "5"]:
            return get_main_menu()
            
    session = sessions[phone]
    step = session.get("step", "main")
    
    # ══════════════════════════════════════════════════════════════════════════
    # Main Menu Routing
    # ══════════════════════════════════════════════════════════════════════════
    if step == "main":
        if text_in == "1":
            sessions[phone] = {"step": "price_crop"}
            return "🔍 *Check Crop Price*\nEnter crop name (e.g., Tomato, Onion, Wheat):"
            
        elif text_in == "2":
            sessions[phone] = {"step": "best_crop"}
            return "🏆 *Best Market to Sell*\nEnter crop name (e.g., Tomato, Onion):"
            
        elif text_in == "3":
            sessions[phone] = {"step": "forecast_crop"}
            return "🔮 *Price Forecast (7 days)*\nEnter crop name (e.g., Tomato, Onion):"
            
        elif text_in == "4":
            movers = get_top_movers(df, top_n=3)
            if not movers["gainers"] and not movers["losers"]:
                return "No mover data available today.\n\nType *0* for Main Menu."

            lines = ["📊 *Top Movers (30 days)*\n"]
            if movers["gainers"]:
                lines.append("📈 *RISING:*")
                for g in movers["gainers"]:
                    lines.append(f"• {g['commodity']} ({g['market']}): +{g['pct']}%")

            if movers["losers"]:
                lines.append("\n📉 *FALLING:*")
                for l in movers["losers"]:
                    lines.append(f"• {l['commodity']} ({l['market']}): {l['pct']}%")

            lines.append("\nType *0* for Main Menu.")
            return "\n".join(lines)
            
        elif text_in == "5":
            return (
                "ℹ️ *About KisanGuard AI*\n"
                "Agricultural Intelligence for Indian Farmers.\n\n"
                "✅ Real-time prices\n✅ Market comparisons\n✅ Price forecasts\n\n"
                "Free service.\n"
                "Type *0* for Main Menu."
            )
            
        else:
            return get_main_menu()

    # ══════════════════════════════════════════════════════════════════════════
    # OPTION 1 — Check Crop Price
    # ══════════════════════════════════════════════════════════════════════════
    elif step == "price_crop":
        commodity = fuzzy_match_commodity(df, text_in)
        if not commodity:
            return f"❌ Sorry, '{text_in}' not found.\nTry: Tomato, Onion, Wheat.\n\nType *0* for Main Menu."
            
        session["crop"] = commodity
        session["step"] = "price_market"
        
        market_menu = "\n".join([f"{i+1}. {m}" for i, m in enumerate(DEFAULT_MARKETS)])
        return f"📍 Select mandi for *{commodity}*:\n{market_menu}\n7. Other (type name)\n\nType *0* for Main Menu."
        
    elif step == "price_market":
        commodity = session.get("crop")
        
        if text_in == "7":
            session["step"] = "price_market_other"
            return "Type the name of the Mandi:"
            
        if text_in.isdigit():
            idx = int(text_in) - 1
            if 0 <= idx < len(DEFAULT_MARKETS):
                market = DEFAULT_MARKETS[idx]
            else:
                return "❌ Invalid market selection. Please try again."
        else:
            market = text_in.strip().title()
            
        record = get_latest_price(df, commodity, market)
        if not record:
            return f"❌ No price data for {commodity} in {market}.\nTry another market.\n\nType *0* for Main Menu."
            
        # Complete
        sessions[phone] = {"step": "main"}
        return (
            f"🛒 *{commodity}* | *{market}*\n"
            f"Price: ₹{record['price']:,.0f}/{record['unit']}\n"
            f"Trend: {record['trend']}\n"
            f"Date: {record['date']}\n\n"
            f"Type *0* for Main Menu."
        )

    elif step == "price_market_other":
        commodity = session.get("crop")
        market = text_in.strip().title()
        
        record = get_latest_price(df, commodity, market)
        sessions[phone] = {"step": "main"}
        
        if not record:
            return f"❌ No data for {commodity} in {market}.\n\nType *0* for Main Menu."
            
        return (
            f"🛒 *{commodity}* | *{market}*\n"
            f"Price: ₹{record['price']:,.0f}/{record['unit']}\n"
            f"Trend: {record['trend']}\n"
            f"Date: {record['date']}\n\n"
            f"Type *0* for Main Menu."
        )

    # ══════════════════════════════════════════════════════════════════════════
    # OPTION 2 — Best Market to Sell
    # ══════════════════════════════════════════════════════════════════════════
    elif step == "best_crop":
        commodity = fuzzy_match_commodity(df, text_in)
        if not commodity:
            return f"❌ Crop '{text_in}' not found.\nTry: Tomato, Onion, Wheat.\n\nType *0* for Main Menu."
            
        ranking = get_market_ranking(df, commodity)
        sessions[phone] = {"step": "main"}
        
        if not ranking:
            return f"❌ No market data for {commodity}.\n\nType *0* for Main Menu."
            
        top = ranking[:4]
        lines = [f"🏆 *{commodity}* - Best Markets:\n"]
        for i, r in enumerate(top):
            marker = " 🌟" if i == 0 else ""
            lines.append(
                f"{i+1}. {r['market']}: ₹{r['price']:,.0f}{r['trend']}{marker}"
            )
        lines.append(f"\n✅ Best: *{top[0]['market']}*")
        if len(ranking) > 1:
            lines.append(f"⚠️ Avoid: *{ranking[-1]['market']}*")
        lines.append("\nType *0* for Main Menu.")
        
        return "\n".join(lines)

    # ══════════════════════════════════════════════════════════════════════════
    # OPTION 3 — Price Forecast
    # ══════════════════════════════════════════════════════════════════════════
    elif step == "forecast_crop":
        commodity = fuzzy_match_commodity(df, text_in)
        if not commodity:
            return f"❌ Crop '{text_in}' not found.\n\nType *0* for Main Menu."
            
        fc = get_simple_forecast(df, commodity, horizon=7)
        sessions[phone] = {"step": "main"}
        
        if not fc["available"]:
            return f"❌ Not enough data to forecast {commodity}.\n\nType *0* for Main Menu."
            
        direction_icon = "📈" if fc["pct_change"] > 0 else "📉" if fc["pct_change"] < 0 else "➡️"
        
        return (
            f"🔮 *{commodity} - 7 Day Forecast*\n"
            f"Now: ₹{fc['current_price']:,.0f}/{fc['unit']}\n"
            f"Expected to {fc['direction']} {direction_icon}\n"
            f"Change: {fc['pct_change']:+.1f}%\n"
            f"💡 Advice: {fc['advice']}\n\n"
            f"Type *0* for Main Menu."
        )

    # Fallback
    sessions[phone] = {"step": "main"}
    return get_main_menu()


# ── WhatsApp Endpoints ────────────────────────────────────────────────────────

@router.get("/webhook")
async def verify_webhook(
    mode: str = Query(None, alias="hub.mode"),
    token: str = Query(None, alias="hub.verify_token"),
    challenge: str = Query(None, alias="hub.challenge")
):
    """Webhook verification endpoint for Meta API."""
    if mode == "subscribe" and token == VERIFY_TOKEN:
        logger.info("Webhook verified successfully!")
        return Response(content=challenge, media_type="text/plain")
    raise HTTPException(status_code=403, detail="Invalid verification token")


@router.post("/webhook")
async def whatsapp_webhook(request: Request):
    """Receives WhatsApp messages from Meta Cloud API."""
    data = await request.json()
    
    try:
        # Parse standard Meta WhatsApp webhook format
        entry = data.get("entry", [])[0]
        changes = entry.get("changes", [])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])
        
        if not messages:
            return {"status": "ok"}
            
        message = messages[0]
        phone_number = message.get("from")
        msg_type = message.get("type")
        
        if msg_type == "text":
            text_body = message.get("text", {}).get("body", "")
            
            # Process text and update session
            df = load_data()
            reply_text = process_message(phone_number, text_body, df)
            
            # Send reply
            await send_whatsapp_message(phone_number, truncate(reply_text))
            
        elif msg_type == "audio":
            # For Bhashini audio processing stub
            audio_id = message.get("audio", {}).get("id")
            # In a real app we'd fetch media URL, download, then:
            # text_body = process_voice_note(audio_url)
            # reply_text = process_message(phone_number, text_body, df)
            
            reply_text = "Voice note received! (This is a stub, Bhashini processing would happen here).\n\nType *0* for Main Menu."
            await send_whatsapp_message(phone_number, reply_text)
            
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        
    return {"status": "ok"}


# ── Test / Simulator Endpoint (dev only) ─────────────────────────────────────

@router.get("/simulate", response_class=Response)
async def simulate_whatsapp(
    text: str = "",
    phone: str = "+919000000000",
):
    """
    DEV ONLY — Simulate a WhatsApp session in the browser.
    Maintains session based on the phone number.
    Pass the text input as ?text=1
    """
    df = load_data()
    reply = process_message(phone, text, df)
    return Response(content=reply, media_type="text/plain")
