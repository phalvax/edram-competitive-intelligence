"""
Construction des vecteurs de features différenciés par pays.
Chaque pays a ses propres facteurs déterminants selon COUNTRY_SPECIFIC_FACTORS.
Sans Streamlit.
"""

import numpy as np
import pandas as pd

from config import (
    COUNTRIES, COUNTRY_SPECIFIC_FACTORS, HISTORY_YEARS, PREDICTION_YEAR,
    FALLBACK_IFO, FALLBACK_DEFENSE_GDP, FALLBACK_DEFICIT_PIB,
    FALLBACK_DETTE_PIB, FALLBACK_TOURISME_PIB, FALLBACK_CHOMAGE,
    FALLBACK_EXPORTS_GROWTH, FALLBACK_EURCHF, FALLBACK_INFLATION_RELATIVE,
)

ALL_YEARS = HISTORY_YEARS + [PREDICTION_YEAR]


def build_country_feature_vector(
    country: str,
    year: int,
    scores: dict,
    raw_data: dict,
) -> dict:
    """
    Construit le vecteur de features pour un pays et une année donnés.
    Retourne un dict {feature_name: float_value}.

    scores   : résultat de build_full_scores() contenant F1-F5
    raw_data : dict avec clés optionnelles :
        - "gdp_growth" : DataFrame
        - "spreads"    : DataFrame
        - "per_data"   : DataFrame
        - "political"  : DataFrame
    """
    country_config = COUNTRY_SPECIFIC_FACTORS.get(country, {})
    factor_list = country_config.get("factors", [])
    features = {}

    for factor in factor_list:
        features[factor] = _extract_factor_value(
            factor, country, year, scores, raw_data
        )

    return features


def _extract_factor_value(
    factor: str,
    country: str,
    year: int,
    scores: dict,
    raw_data: dict,
) -> float:
    """Extrait la valeur d'un facteur pour un pays/année. Retourne 0.0 si manquant."""

    try:
        # Facteurs issus du scoring existant (déjà normalisés)
        if factor == "perf_boursiere":
            return _safe_score(scores.get("F1"), year, country)

        elif factor == "pib_relatif":
            return _safe_score(scores.get("F2"), year, country)

        elif factor in ("spread_oat_bund", "spread_btp_bund",
                        "spread_bonos_bund", "spread_nl_bund", "spread_bund"):
            return _safe_score(scores.get("F3"), year, country)

        elif factor == "stabilite_politique":
            return _safe_score(scores.get("F4"), year, country)

        elif factor == "per_relatif":
            return _safe_score(scores.get("F5"), year, country)

        # Nouveaux facteurs — valeurs brutes normalisées manuellement
        elif factor == "ifo_business_climate":
            raw_val = FALLBACK_IFO.get(year, 88.0)
            # Normaliser autour de la moyenne historique (90 = neutre)
            return float(np.clip((raw_val - 90.0) / 10.0, -1.0, 1.0))

        elif factor == "defense_spending_gdp":
            val = FALLBACK_DEFENSE_GDP.get(country, {}).get(year, 1.5)
            # Signal positif si > 2% PIB (cible OTAN) = catalyseur d'investissement
            return float(np.clip((val - 1.5) / 1.0, -1.0, 1.0))

        elif factor == "deficit_pib":
            val = FALLBACK_DEFICIT_PIB.get(country, {}).get(year, -3.0)
            # Déficit élevé = signal négatif pour investisseurs
            return float(np.clip(-val / 5.0, -1.0, 1.0))

        elif factor == "dette_pib":
            val = FALLBACK_DETTE_PIB.get(country, {}).get(year, 80.0)
            # Dette élevée = signal négatif, normalisée autour de 80%
            return float(np.clip(-(val - 80.0) / 60.0, -1.0, 1.0))

        elif factor == "tourisme_pib":
            val = FALLBACK_TOURISME_PIB.get(country, {}).get(year, 5.0)
            # Tourisme élevé = positif pour économie de services
            return float(np.clip((val - 5.0) / 5.0, -1.0, 1.0))

        elif factor == "chomage_variation":
            chomage = FALLBACK_CHOMAGE.get(country, {})
            val_now  = chomage.get(year, 7.0)
            val_prev = chomage.get(year - 1, 7.0)
            delta = val_now - val_prev
            # Hausse du chômage = signal négatif
            return float(np.clip(-delta / 2.0, -1.0, 1.0))

        elif factor == "exports_variation":
            val = FALLBACK_EXPORTS_GROWTH.get(country, {}).get(year, 2.0)
            return float(np.clip(val / 8.0, -1.0, 1.0))

        elif factor == "eurchf_momentum":
            val = FALLBACK_EURCHF.get(year, -2.0)
            # CHF fort (val négatif) = signal négatif pour actions suisses en EUR
            return float(np.clip(val / 8.0, -1.0, 1.0))

        elif factor == "inflation_relative":
            val = FALLBACK_INFLATION_RELATIVE.get(country, {}).get(year, 0.0)
            # Inflation relative faible = avantage compétitif → positif
            return float(np.clip(-val / 3.0, -1.0, 1.0))

        else:
            return 0.0

    except Exception:
        return 0.0


def _safe_score(df: pd.DataFrame, year: int, country: str) -> float:
    """Extrait une valeur d'un DataFrame scores de façon sécurisée."""
    try:
        if df is None:
            return 0.0
        val = df.at[year, country]
        return float(val) if not pd.isna(val) else 0.0
    except (KeyError, TypeError):
        return 0.0


def build_all_features(
    scores: dict,
    raw_data: dict,
    years: list = None,
) -> dict:
    """
    Construit les vecteurs de features pour tous les pays et toutes les années.
    Retourne : {country: DataFrame(years × features)}
    """
    if years is None:
        years = ALL_YEARS

    result = {}
    for country in COUNTRIES:
        rows = {}
        for year in years:
            features = build_country_feature_vector(
                country, year, scores, raw_data
            )
            rows[year] = features
        result[country] = pd.DataFrame(rows).T
        result[country].index.name = "year"

    return result
