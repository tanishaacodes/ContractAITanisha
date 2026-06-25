"""
Market Feed Engine
==================
Fetches real-time macro market signals relevant to specific contract types.

Contract type → signals:
  Software/IT/Service    → NASDAQ, USD/INR, US10Y, Nifty50
  Construction/Civil     → Steel (MT), Crude (CL=F), USD/INR, US10Y
  Real Estate/Lease      → India Bank Nifty (rate proxy), NSE Realty, USD/INR, US10Y
  Logistics/Transport    → Crude (CL=F), USD/INR, US10Y, Nifty50
  Financial/Loan         → US10Y, India Bank Nifty, USD/INR, Nifty50
  General/Default        → USD/INR, US10Y, Nifty50, Crude
"""

import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def _fetch_ticker_signal(signal_type, signal_name, ticker_symbol):
    try:
        import yfinance as yf
        ticker = yf.Ticker(ticker_symbol)
        hist = ticker.history(period="7d")
        hist = hist[hist['Close'].notna()]
        if len(hist) < 2:
            raise ValueError(f"Not enough data for {ticker_symbol}")

        current = float(hist['Close'].iloc[-1])
        previous = float(hist['Close'].iloc[-2])
        percent_change = ((current - previous) / previous) * 100 if previous != 0 else 0.0

        # 5-day average absolute daily move (volatility proxy)
        closes = hist['Close'].tolist()
        daily_moves = [abs((closes[i] - closes[i-1]) / closes[i-1] * 100)
                       for i in range(1, len(closes))]
        avg_volatility = round(sum(daily_moves) / len(daily_moves), 4) if daily_moves else 0.5

        return {
            "signal_type": signal_type,
            "signal_name": signal_name,
            "ticker": ticker_symbol,
            "current_value": round(current, 4),
            "previous_value": round(previous, 4),
            "percent_change": round(percent_change, 4),
            "avg_volatility": avg_volatility,   # 5d avg move — used for exposure if today is flat
            "fetched_at": datetime.utcnow().isoformat(),
            "status": "live",
        }
    except Exception as e:
        logger.warning(f"Market feed error for {ticker_symbol}: {e}")
        return _fallback_signal(signal_type, signal_name, ticker_symbol, str(e))


def _fallback_signal(signal_type, signal_name, ticker_symbol, error_msg="unavailable"):
    return {
        "signal_type": signal_type,
        "signal_name": signal_name,
        "ticker": ticker_symbol,
        "current_value": None,
        "previous_value": None,
        "percent_change": 0.0,
        "avg_volatility": 0.5,   # default 0.5% daily move
        "fetched_at": datetime.utcnow().isoformat(),
        "status": "fallback",
        "error": error_msg,
    }


# ─────────────────────────────────────────────
# Individual signal getters
# Using reliable, liquid tickers
# ─────────────────────────────────────────────
def get_steel_price():
    # ArcelorMittal (MT) — more reliable than SLX ETF
    return _fetch_ticker_signal("commodity", "Steel (ArcelorMittal)", "MT")

def get_interest_rate():
    return _fetch_ticker_signal("interest_rate", "US 10Y Treasury", "^TNX")

def get_usd_inr():
    return _fetch_ticker_signal("fx", "USD/INR", "INR=X")

def get_crude_oil():
    # WTI Crude Futures — most liquid crude oil ticker
    return _fetch_ticker_signal("commodity", "Crude Oil (WTI)", "CL=F")

def get_nasdaq():
    return _fetch_ticker_signal("equity", "NASDAQ Composite", "^IXIC")

def get_nifty50():
    return _fetch_ticker_signal("equity", "Nifty 50", "^NSEI")

def get_nifty_bank():
    # India Bank Nifty — best proxy for RBI interest rate moves
    return _fetch_ticker_signal("interest_rate", "Nifty Bank (Rate Proxy)", "^NSEBANK")

def get_nifty_realty():
    # NSE Realty Index — tracks real estate/construction sector
    return _fetch_ticker_signal("equity", "DLF (Realty Proxy)", "DLF.NS")

def get_copper():
    return _fetch_ticker_signal("commodity", "Copper (Futures)", "HG=F")


# ─────────────────────────────────────────────
# Contract-type → signal mapping
# ─────────────────────────────────────────────
CONTRACT_SIGNAL_MAP = {
    "Software/IT/Service": [
        ("nasdaq",        get_nasdaq),          # Tech sector health
        ("usd_inr",       get_usd_inr),         # IT services billed in USD
        ("interest_rate", get_interest_rate),   # Cost of capital / payment risk
        ("nifty50",       get_nifty50),         # Indian market confidence
    ],
    "Physical/Procurement": [
        ("steel",         get_steel_price),     # Primary raw material (ArcelorMittal)
        ("crude_oil",     get_crude_oil),       # Energy/logistics (WTI)
        ("usd_inr",       get_usd_inr),         # Import cost exposure
        ("interest_rate", get_interest_rate),   # Project financing rate
    ],
    "Real Estate/Lease": [
        ("nifty_bank",    get_nifty_bank),      # RBI rate moves → EMI/rent impact
        ("nifty_realty",  get_nifty_realty),    # Real estate sector health
        ("usd_inr",       get_usd_inr),         # FX if foreign tenant/funding
        ("interest_rate", get_interest_rate),   # Benchmark financing rate
    ],
    "Logistics/Transport": [
        ("crude_oil",     get_crude_oil),       # Fuel cost — primary driver
        ("usd_inr",       get_usd_inr),         # Import/export exposure
        ("interest_rate", get_interest_rate),   # Working capital rate
        ("nifty50",       get_nifty50),         # Demand proxy
    ],
    "Financial/Loan": [
        ("interest_rate", get_interest_rate),   # Core signal
        ("nifty_bank",    get_nifty_bank),      # India rate proxy
        ("usd_inr",       get_usd_inr),         # FX exposure
        ("nifty50",       get_nifty50),         # Credit risk proxy
    ],
    "default": [
        ("usd_inr",       get_usd_inr),
        ("interest_rate", get_interest_rate),
        ("nifty50",       get_nifty50),
        ("crude_oil",     get_crude_oil),
    ],
}


def get_signals_for_contract_type(contract_type: str) -> dict:
    """Fetch the 4 market signals most relevant to the given contract type."""
    signal_list = CONTRACT_SIGNAL_MAP.get(contract_type, CONTRACT_SIGNAL_MAP["default"])
    result = {}
    for key, fetcher in signal_list:
        try:
            result[key] = fetcher()
        except Exception as e:
            logger.warning(f"Signal fetch failed for {key}: {e}")
            result[key] = _fallback_signal("unknown", key, key, str(e))
    return result


def get_all_signals():
    """Fetch default signals for /api/market/signals/ endpoint."""
    return [
        get_steel_price(),
        get_interest_rate(),
        get_usd_inr(),
        get_crude_oil(),
    ]
