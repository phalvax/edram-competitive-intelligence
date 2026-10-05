"""
Chargement des données de stabilité politique (F4) depuis political_events.json.
"""
import json
import pandas as pd
from config import POLITICAL_FILE, COUNTRIES, HISTORY_YEARS, PREDICTION_YEAR


def load_political_raw() -> dict:
    """Charge le JSON brut {country: {year: {flags}}}."""
    if not POLITICAL_FILE.exists():
        return {}
    with open(POLITICAL_FILE, encoding="utf-8") as f:
        return json.load(f)


def save_political_scores(data: dict) -> None:
    """Sauvegarde le JSON brut mis à jour."""
    with open(POLITICAL_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_political_scores() -> pd.DataFrame:
    """
    Retourne un DataFrame (années × pays) avec les scores F4 dans [-1, +1].
    Années : HISTORY_YEARS + PREDICTION_YEAR.
    """
    raw = load_political_raw()
    years = HISTORY_YEARS + [PREDICTION_YEAR]
    data = {}
    for country in COUNTRIES:
        col = {}
        country_data = raw.get(country, {})
        for year in years:
            entry = country_data.get(str(year), {})
            if entry:
                score = entry.get("score", 0.0)
            else:
                # Valeur par défaut neutre si manquant
                score = 0.0
            col[year] = float(score)
        data[country] = col

    df = pd.DataFrame(data, index=years)
    df.index.name = "year"
    return df
