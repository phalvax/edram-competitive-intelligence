"""
Fetch des données de marché :
  F1 — performance boursière (yfinance)
  F3 — spreads souverains (FRED ou fallback)
  F5 — PER relatif (yfinance info ou fallback)
"""
import os
import numpy as np
import pandas as pd
import streamlit as st

from config import (
    COUNTRIES,
    COUNTRY_TICKERS,
    FALLBACK_PER,
    FALLBACK_SPREADS,
    HISTORY_YEARS,
    MSCI_EUROPE_TICKER,
    MSCI_EUROPE_TICKER_ALT,
    PREDICTION_YEAR,
    SOVEREIGN_YIELD_FRED,
    BUND_FRED_ID,
)

_ALL_YEARS = HISTORY_YEARS + [PREDICTION_YEAR]


# ── F1 : Prix actions ─────────────────────────────────────────────────────────

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_equity_prices() -> pd.DataFrame:
    """Retourne DataFrame (dates × tickers) des prix de clôture ajustés."""
    try:
        import yfinance as yf
        tickers = list(COUNTRY_TICKERS.values()) + [MSCI_EUROPE_TICKER]
        start = f"{min(_ALL_YEARS)-1}-01-01"
        data = yf.download(tickers, start=start, auto_adjust=True,
                           progress=False, show_errors=False)
        if "Close" in data.columns.get_level_values(0):
            prices = data["Close"]
        else:
            prices = data
        # Rename tickers → country names
        rev = {v: k for k, v in COUNTRY_TICKERS.items()}
        prices = prices.rename(columns=rev)
        # Fallback MSCI ticker
        if MSCI_EUROPE_TICKER not in prices.columns and MSCI_EUROPE_TICKER_ALT in prices.columns:
            prices = prices.rename(columns={MSCI_EUROPE_TICKER_ALT: MSCI_EUROPE_TICKER})
        prices = prices.rename(columns={MSCI_EUROPE_TICKER: "MSCI_Europe"})
        return prices
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=3600, show_spinner=False)
def compute_annual_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """Retourne les rendements annuels (%) par pays + MSCI_Europe."""
    if prices.empty:
        return pd.DataFrame()
    annual = prices.resample("YE").last().pct_change() * 100
    annual.index = annual.index.year
    annual.index.name = "year"
    return annual.reindex(_ALL_YEARS)


# ── F3 : Spreads souverains ───────────────────────────────────────────────────

def _fetch_fred_series(series_id: str, api_key: str) -> pd.Series | None:
    try:
        import requests
        resp = requests.get(
            "https://api.stlouisfed.org/fred/series/observations",
            params={"series_id": series_id, "api_key": api_key,
                    "file_type": "json", "frequency": "a"},
            timeout=10,
        )
        resp.raise_for_status()
        obs = resp.json().get("observations", [])
        return pd.Series(
            {int(o["date"][:4]): float(o["value"]) for o in obs if o["value"] != "."},
            dtype=float,
        )
    except Exception:
        return None


def _fallback_spreads_df() -> pd.DataFrame:
    data = {c: {yr: FALLBACK_SPREADS.get(c, {}).get(yr, 0.0) for yr in _ALL_YEARS}
            for c in COUNTRIES}
    df = pd.DataFrame(data, index=_ALL_YEARS)
    df.index.name = "year"
    return df


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_sovereign_spreads(fred_api_key: str = "") -> pd.DataFrame:
    """
    Retourne DataFrame (années × pays) de spreads vs Bund (bps).
    FRED si clé disponible, sinon FALLBACK_SPREADS.
    """
    key = (fred_api_key
           or st.session_state.get("fred_api_key", "")
           or os.getenv("FRED_API_KEY", ""))

    if not key:
        return _fallback_spreads_df()

    bund = _fetch_fred_series(BUND_FRED_ID, key)
    if bund is None:
        return _fallback_spreads_df()

    data = {}
    for country in COUNTRIES:
        if country == "Germany":
            data[country] = {yr: 0.0 for yr in _ALL_YEARS}
            continue
        series_id = SOVEREIGN_YIELD_FRED.get(country)
        if not series_id:
            data[country] = {yr: FALLBACK_SPREADS.get(country, {}).get(yr, 0.0) for yr in _ALL_YEARS}
            continue
        series = _fetch_fred_series(series_id, key)
        if series is None:
            data[country] = {yr: FALLBACK_SPREADS.get(country, {}).get(yr, 0.0) for yr in _ALL_YEARS}
            continue
        spread_series = (series - bund) * 100  # % → bps
        data[country] = {yr: spread_series.get(yr, FALLBACK_SPREADS.get(country, {}).get(yr, 0.0))
                         for yr in _ALL_YEARS}

    df = pd.DataFrame(data, index=_ALL_YEARS)
    df.index.name = "year"
    return df


# ── F5 : PER ──────────────────────────────────────────────────────────────────

_PER_TICKERS = {
    "France":      "EWQ",
    "Germany":     "EWG",
    "Italy":       "EWI",
    "Spain":       "EWP",
    "Netherlands": "EWN",
    "Switzerland": "EWL",
    "MSCI_Europe": "IEUR",
}


def _fallback_per_df() -> pd.DataFrame:
    data = {k: {yr: FALLBACK_PER.get(k, {}).get(yr, 14.0) for yr in _ALL_YEARS}
            for k in list(_PER_TICKERS.keys())}
    df = pd.DataFrame(data, index=_ALL_YEARS)
    df.index.name = "year"
    return df


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_per_data() -> pd.DataFrame:
    """
    Retourne DataFrame (années × pays+MSCI_Europe) de PER.
    Valeur courante via yfinance.info, données historiques depuis FALLBACK_PER.
    """
    # Partir du fallback complet
    data = {k: {yr: FALLBACK_PER.get(k, {}).get(yr, 14.0) for yr in _ALL_YEARS}
            for k in list(_PER_TICKERS.keys())}

    # Enrichir avec yfinance pour l'année courante (PREDICTION_YEAR)
    try:
        import yfinance as yf
        for name, ticker in _PER_TICKERS.items():
            try:
                info = yf.Ticker(ticker).fast_info
                pe = getattr(info, "pe_ratio", None)
                if pe and not np.isnan(pe) and 3 < pe < 100:
                    data[name][PREDICTION_YEAR] = round(float(pe), 1)
            except Exception:
                pass
    except ImportError:
        pass

    df = pd.DataFrame(data, index=_ALL_YEARS)
    df.index.name = "year"
    return df
