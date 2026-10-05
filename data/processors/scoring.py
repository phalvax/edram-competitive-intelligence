"""
Moteur de scoring — logique métier pure, sans Streamlit.
Calcule F1-F5 via z-score rolling, puis le score composite et les positions.
"""
import numpy as np
import pandas as pd

from config import (
    COUNTRIES,
    DEFAULT_WEIGHTS,
    FALLBACK_GDP,
    FALLBACK_PER,
    FALLBACK_SPREADS,
    F3_DELTA_WEIGHT,
    F3_LEVEL_WEIGHT,
    HISTORY_YEARS,
    PREDICTION_YEAR,
    THRESHOLD_OW,
    THRESHOLD_UW,
    ZSCORE_WINDOW,
)

ALL_YEARS = HISTORY_YEARS + [PREDICTION_YEAR]


# ── Z-score rolling ────────────────────────────────────────────────────────────

def rolling_zscore(series: pd.Series, window: int = ZSCORE_WINDOW) -> pd.Series:
    result = pd.Series(0.0, index=series.index, dtype=float)
    for i in range(len(series)):
        vals = series.iloc[max(0, i - window + 1): i + 1].dropna()
        if len(vals) < 2:
            result.iloc[i] = 0.0
            continue
        std      = vals.std(ddof=1)
        val_range = vals.max() - vals.min()
        current   = series.iloc[i]
        if pd.isna(current):
            result.iloc[i] = 0.0
        elif len(vals) < 4:
            # Moins de 4 points : min-max dans [-1, +1]
            if val_range > 0:
                result.iloc[i] = float(
                    np.clip(2 * (current - vals.min()) / val_range - 1, -1.0, 1.0)
                )
            else:
                result.iloc[i] = 0.0
        else:
            # 4+ points : z-score standard clippé dans [-1, +1]
            if std == 0 or pd.isna(std):
                result.iloc[i] = 0.0
            else:
                result.iloc[i] = float(
                    np.clip((current - vals.mean()) / std, -1.0, 1.0)
                )
    return result


def _safe_df(df: pd.DataFrame, years: list, countries: list) -> pd.DataFrame:
    """Reindex un DataFrame sur les années/pays voulus, remplit NaN→0."""
    return df.reindex(index=years, columns=countries).fillna(0.0)


# ── F1 : Performance boursière relative ───────────────────────────────────────

def score_f1(annual_returns: pd.DataFrame, years: list = None) -> tuple[pd.DataFrame, list]:
    years = years or ALL_YEARS
    warnings = []

    if annual_returns.empty or "MSCI_Europe" not in annual_returns.columns:
        warnings.append("F1 neutralisé — données boursières (yfinance) indisponibles.")
        return pd.DataFrame(0.0, index=years, columns=COUNTRIES), warnings

    msci = annual_returns["MSCI_Europe"].reindex(years).fillna(0.0)
    result = {}
    missing = []
    for country in COUNTRIES:
        if country not in annual_returns.columns:
            missing.append(country)
            result[country] = pd.Series(0.0, index=years)
        else:
            excess = (annual_returns[country].reindex(years).fillna(0.0) - msci)
            result[country] = rolling_zscore(excess)

    if missing:
        warnings.append(f"F1 neutralisé pour : {', '.join(missing)}")

    df = pd.DataFrame(result, index=years)
    df.index.name = "year"
    return df, warnings


# ── F2 : Écart croissance PIB ─────────────────────────────────────────────────

def score_f2(gdp_growth: pd.DataFrame, years: list = None) -> tuple[pd.DataFrame, list]:
    years = years or ALL_YEARS
    warnings = []

    if gdp_growth.empty or "Eurozone" not in gdp_growth.columns:
        warnings.append("F2 neutralisé — données PIB indisponibles.")
        return pd.DataFrame(0.0, index=years, columns=COUNTRIES), warnings

    ez = gdp_growth["Eurozone"].reindex(years).fillna(0.0)
    result = {}
    missing = []
    for country in COUNTRIES:
        if country not in gdp_growth.columns:
            missing.append(country)
            result[country] = pd.Series(0.0, index=years)
        else:
            gap = (gdp_growth[country].reindex(years).fillna(0.0) - ez)
            result[country] = rolling_zscore(gap)

    if missing:
        warnings.append(f"F2 neutralisé pour : {', '.join(missing)}")

    df = pd.DataFrame(result, index=years)
    df.index.name = "year"
    return df, warnings


# ── F3 : Spread souverain vs Bund ─────────────────────────────────────────────

def score_f3(sovereign_spreads: pd.DataFrame, years: list = None) -> tuple[pd.DataFrame, list]:
    years = years or ALL_YEARS
    warnings = []

    if sovereign_spreads.empty or sovereign_spreads.isna().all().all():
        warnings.append("F3 neutralisé — spreads souverains indisponibles (clé FRED manquante).")
        return pd.DataFrame(0.0, index=years, columns=COUNTRIES), warnings

    result = {}
    missing = []
    for country in COUNTRIES:
        if country == "Germany":
            result[country] = pd.Series(0.0, index=years)
            continue
        if country not in sovereign_spreads.columns:
            missing.append(country)
            result[country] = pd.Series(0.0, index=years)
            continue

        col = sovereign_spreads[country].reindex(years).fillna(0.0)
        z_level = rolling_zscore(-col)
        z_delta = rolling_zscore(-col.diff().fillna(0.0))
        result[country] = (F3_LEVEL_WEIGHT * z_level + F3_DELTA_WEIGHT * z_delta).clip(-1.0, 1.0)

    if missing:
        warnings.append(f"F3 neutralisé pour : {', '.join(missing)}")

    df = pd.DataFrame(result, index=years)
    df.index.name = "year"
    return df, warnings


# ── F4 : Stabilité politique ──────────────────────────────────────────────────

def score_f4(political_scores: pd.DataFrame, years: list = None) -> tuple[pd.DataFrame, list]:
    years = years or ALL_YEARS
    warnings = []

    if political_scores.empty:
        warnings.append("F4 neutralisé — données politiques indisponibles.")
        return pd.DataFrame(0.0, index=years, columns=COUNTRIES), warnings

    result = {}
    missing = []
    for country in COUNTRIES:
        if country not in political_scores.columns:
            missing.append(country)
            result[country] = pd.Series(0.0, index=years)
        else:
            result[country] = political_scores[country].reindex(years).fillna(0.0).clip(-1.0, 1.0)

    if missing:
        warnings.append(f"F4 neutralisé pour : {', '.join(missing)}")

    df = pd.DataFrame(result, index=years)
    df.index.name = "year"
    return df, warnings


# ── F5 : PER relatif ──────────────────────────────────────────────────────────

def score_f5(per_data: pd.DataFrame, years: list = None) -> tuple[pd.DataFrame, list]:
    years = years or ALL_YEARS
    warnings = []

    if per_data.empty or "MSCI_Europe" not in per_data.columns:
        warnings.append("F5 neutralisé — données PER indisponibles.")
        return pd.DataFrame(0.0, index=years, columns=COUNTRIES), warnings

    msci_per = per_data["MSCI_Europe"].reindex(years)
    result = {}
    missing = []
    for country in COUNTRIES:
        if country not in per_data.columns:
            missing.append(country)
            result[country] = pd.Series(0.0, index=years)
            continue

        col = per_data[country].reindex(years)
        relative = pd.Series(dtype=float, index=years)
        for yr in years:
            p = col.get(yr, np.nan)
            m = msci_per.get(yr, np.nan)
            relative[yr] = (1.0 - p / m) if (not pd.isna(p) and not pd.isna(m) and m > 0) else 0.0

        result[country] = rolling_zscore(relative)

    if missing:
        warnings.append(f"F5 neutralisé pour : {', '.join(missing)}")

    df = pd.DataFrame(result, index=years)
    df.index.name = "year"
    return df, warnings


# ── Score composite + classification ─────────────────────────────────────────

def classify_position(score: float) -> str:
    if score > THRESHOLD_OW:
        return "OW"
    if score < THRESHOLD_UW:
        return "UW"
    return "N"


def compute_composite(f1, f2, f3, f4, f5, weights, years) -> pd.DataFrame:
    w = weights or DEFAULT_WEIGHTS
    total = sum(w.values())
    if abs(total - 1.0) > 0.02:
        raise ValueError(f"Somme des poids = {total:.2f} ≠ 1.0")

    composite = (
        w["F1"] * _safe_df(f1, years, COUNTRIES)
        + w["F2"] * _safe_df(f2, years, COUNTRIES)
        + w["F3"] * _safe_df(f3, years, COUNTRIES)
        + w["F4"] * _safe_df(f4, years, COUNTRIES)
        + w["F5"] * _safe_df(f5, years, COUNTRIES)
    )
    composite.index.name = "year"
    return composite


# ── Pipeline principal ─────────────────────────────────────────────────────────

def build_full_scores(
    annual_returns: pd.DataFrame,
    gdp_growth: pd.DataFrame,
    sovereign_spreads: pd.DataFrame,
    political_scores: pd.DataFrame,
    per_data: pd.DataFrame,
    weights: dict | None = None,
    years: list | None = None,
) -> dict:
    """
    Orchestre F1-F5 → composite → positions.
    Retourne : {F1..F5, composite, positions, warnings}
    """
    years = years or ALL_YEARS
    w = weights or DEFAULT_WEIGHTS.copy()

    f1, w1 = score_f1(annual_returns, years)
    f2, w2 = score_f2(gdp_growth, years)
    f3, w3 = score_f3(sovereign_spreads, years)
    f4, w4 = score_f4(political_scores, years)
    f5, w5 = score_f5(per_data, years)
    all_warnings = w1 + w2 + w3 + w4 + w5

    try:
        composite = compute_composite(f1, f2, f3, f4, f5, w, years)
    except ValueError as e:
        all_warnings.append(str(e))
        composite = pd.DataFrame(0.0, index=years, columns=COUNTRIES)

    positions = composite.map(classify_position)

    return {
        "F1": f1, "F2": f2, "F3": f3, "F4": f4, "F5": f5,
        "composite": composite,
        "positions": positions,
        "warnings": list(dict.fromkeys(all_warnings)),
    }


def prepare_ml_training_data(
    scores_history: dict,
    ground_truth_master: dict,
    fund_metadata: dict,
) -> "pd.DataFrame":
    """
    PRÉPARÉ POUR FUTURE IMPLÉMENTATION ML — NE PAS SUPPRIMER.

    Construit le DataFrame d'entraînement pour un modèle de classification
    (Random Forest ou Régression Logistique) qui apprend la relation
    facteurs → position OW/N/UW par type de fonds.

    Structure du DataFrame de sortie :
    Colonnes features :
      - f1_score, f2_score, f3_score, f4_score, f5_score (float, z-score)
      - fund_type (catégorielle : "Généraliste Volume", "Banque Privée",
                  "Assureur", "Boutique")
      - country (catégorielle : France, Germany, Italy, Spain,
                Netherlands, Switzerland)
      - year (int)
    Colonne cible :
      - position_reelle (str : "OW", "N", "UW")

    Taille attendue pour entraînement fiable :
      31 fonds × 4 années × 6 pays = ~744 observations
      (avec données GT disponibles pour au moins 10+ fonds)

    Algorithmes recommandés :
      1. Régression Logistique Multinomiale (baseline, interprétable)
      2. Random Forest (meilleure précision, feature importance)
      3. XGBoost (optimal si > 500 observations)

    Métriques cibles : accuracy > 70%, F1-score macro > 0.65
    """
    raise NotImplementedError(
        "ML non encore implémenté. "
        "Alimentez d'abord ground_truth_master.json avec 10+ fonds "
        "via la collecte automatique (Page Paramètres)."
    )


def get_factor_contributions(scores: dict, country: str, year: int, weights: dict | None = None) -> dict:
    """Contribution pondérée de chaque facteur pour un pays/année."""
    w = weights or DEFAULT_WEIGHTS
    result = {}
    for fi in ["F1", "F2", "F3", "F4", "F5"]:
        df = scores.get(fi)
        try:
            v = float(df.at[year, country]) if df is not None else 0.0
        except (KeyError, TypeError):
            v = 0.0
        result[fi] = round(w.get(fi, 0.0) * v, 4)
    return result
