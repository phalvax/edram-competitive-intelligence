"""
Fetch des données PIB (F2) — FRED si clé disponible, sinon fallback OCDE.
"""
import os
import pandas as pd
import streamlit as st

from config import FALLBACK_GDP, HISTORY_YEARS, PREDICTION_YEAR, OECD_GDP_CODES

_ALL_YEARS = HISTORY_YEARS + [PREDICTION_YEAR]

# Séries FRED PIB trimestriel (CVMNACSCAB1GQ = Chain volume, seasonally adjusted)
_FRED_GDP_SERIES = {
    "France":      "CLVMNACSCAB1GQFR",
    "Germany":     "CLVMNACSCAB1GQDE",
    "Italy":       "CLVMNACSCAB1GQIT",
    "Spain":       "CLVMNACSCAB1GQES",
    "Netherlands": "CLVMNACSCAB1GQNL",
    "Switzerland": "CLVMNACSCAB1GQCH",
    "Eurozone":    "CLVMNACSCAB1GQEA",
}


def _fallback_gdp_df() -> pd.DataFrame:
    """Retourne le DataFrame de fallback depuis config.FALLBACK_GDP."""
    data = {country: {yr: FALLBACK_GDP.get(country, {}).get(yr, 0.0) for yr in _ALL_YEARS}
            for country in list(_FRED_GDP_SERIES.keys())}
    df = pd.DataFrame(data, index=_ALL_YEARS)
    df.index.name = "year"
    return df


def _fetch_fred_quarterly(series_id: str, api_key: str) -> pd.Series | None:
    """Fetch une série FRED trimestrielle, retourne croissance annuelle par année."""
    try:
        import requests
        url = "https://api.stlouisfed.org/fred/series/observations"
        resp = requests.get(url, params={
            "series_id": series_id,
            "api_key":   api_key,
            "file_type": "json",
            "frequency": "q",
            "observation_start": f"{min(_ALL_YEARS)-1}-01-01",
        }, timeout=10)
        resp.raise_for_status()
        obs = resp.json().get("observations", [])
        if not obs:
            return None

        s = pd.Series(
            {o["date"][:7]: float(o["value"]) for o in obs if o["value"] != "."},
            dtype=float,
        )
        s.index = pd.to_datetime(s.index + "-01")
        s = s.sort_index()

        # Croissance annuelle = variation sur 4 trimestres (yoy)
        yoy = s.pct_change(4) * 100
        # Moyenne annuelle
        annual = yoy.groupby(yoy.index.year).mean().dropna()
        return annual
    except Exception:
        return None


@st.cache_data(ttl=86400, show_spinner=False)
def fetch_gdp_growth(fred_api_key: str = "") -> pd.DataFrame:
    """
    Retourne DataFrame (années × pays+Eurozone) de la croissance PIB annuelle (%).
    Utilise FRED si clé disponible, sinon FALLBACK_GDP (OCDE).
    """
    key = (fred_api_key
           or st.session_state.get("fred_api_key", "")
           or os.getenv("FRED_API_KEY", ""))

    if key:
        data = {}
        failed = []
        for country, series_id in _FRED_GDP_SERIES.items():
            annual = _fetch_fred_quarterly(series_id, key)
            if annual is not None and len(annual) > 0:
                data[country] = {yr: annual.get(yr, FALLBACK_GDP.get(country, {}).get(yr, 0.0))
                                 for yr in _ALL_YEARS}
            else:
                failed.append(country)
                data[country] = {yr: FALLBACK_GDP.get(country, {}).get(yr, 0.0)
                                 for yr in _ALL_YEARS}

        df = pd.DataFrame(data, index=_ALL_YEARS)
        df.index.name = "year"
        return df

    # Pas de clé FRED → fallback silencieux
    return _fallback_gdp_df()
