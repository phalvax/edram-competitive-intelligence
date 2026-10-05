"""
Calcul de probabilités via Monte Carlo — sans Streamlit.
Pour chaque prédiction de pays/année, estime la distribution des positions possibles
en simulant des perturbations gaussiennes sur chaque facteur.
"""
import numpy as np
import pandas as pd

from config import (
    COUNTRIES,
    CONFIDENCE_HIGH,
    CONFIDENCE_MEDIUM,
    HISTORY_YEARS,
    THRESHOLD_OW,
    THRESHOLD_UW,
)


def _classify(score: float) -> str:
    if score > THRESHOLD_OW:
        return "OW"
    if score < THRESHOLD_UW:
        return "UW"
    return "N"


def _get_factor_stats(factor_scores: dict, country: str, year: int) -> dict:
    """
    Pour chaque facteur, retourne (valeur_annee, std_historique).
    std_historique calculé sur HISTORY_YEARS pour estimer l'incertitude du modèle.
    """
    stats = {}
    for fi in ["F1", "F2", "F3", "F4", "F5"]:
        df = factor_scores.get(fi)
        if df is None or country not in df.columns:
            stats[fi] = {"val": 0.0, "std": 0.10}
            continue

        # Valeur courante
        val = float(df.at[year, country]) if year in df.index else 0.0

        # Std historique sur HISTORY_YEARS (sans l'année de prédiction)
        hist = [float(df.at[yr, country]) for yr in HISTORY_YEARS
                if yr in df.index and not pd.isna(df.at[yr, country])]
        std = float(np.std(hist, ddof=1)) if len(hist) >= 2 else 0.10
        # Éviter std = 0 (facteur constant → quand même une incertitude minimale)
        std = max(std, 0.05)

        stats[fi] = {"val": val, "std": std}
    return stats


def compute_probabilities(
    factor_scores: dict,
    composite_scores: pd.DataFrame,
    predicted_positions: pd.DataFrame,
    weights: dict,
    year: int,
    n_simulations: int = 1000,
) -> pd.DataFrame:
    """
    Retourne DataFrame indexé par country avec :
    position, prob_OW, prob_N, prob_UW, prob_predicted, confidence_level
    """
    rng = np.random.default_rng(42)
    rows = []

    for country in COUNTRIES:
        stats = _get_factor_stats(factor_scores, country, year)

        # Simuler n_simulations perturbations
        sims = np.zeros(n_simulations)
        for fi in ["F1", "F2", "F3", "F4", "F5"]:
            w_i   = weights.get(fi, 0.0)
            val_i = stats[fi]["val"]
            std_i = stats[fi]["std"]
            sims += w_i * (val_i + rng.normal(0, std_i, n_simulations))

        n_ow = int(np.sum(sims > THRESHOLD_OW))
        n_uw = int(np.sum(sims < THRESHOLD_UW))
        n_n  = n_simulations - n_ow - n_uw

        prob_ow = n_ow / n_simulations
        prob_n  = n_n  / n_simulations
        prob_uw = n_uw / n_simulations

        pred_pos = "N"
        if (predicted_positions is not None
                and year in predicted_positions.index
                and country in predicted_positions.columns):
            pred_pos = predicted_positions.at[year, country]

        prob_pred = {"OW": prob_ow, "N": prob_n, "UW": prob_uw}.get(pred_pos, 0.5)

        if prob_pred >= CONFIDENCE_HIGH:
            conf_level = "Haute"
        elif prob_pred >= CONFIDENCE_MEDIUM:
            conf_level = "Moyenne"
        else:
            conf_level = "Faible"

        rows.append({
            "country":          country,
            "position":         pred_pos,
            "prob_OW":          round(prob_ow, 3),
            "prob_N":           round(prob_n, 3),
            "prob_UW":          round(prob_uw, 3),
            "prob_predicted":   round(prob_pred, 3),
            "confidence_level": conf_level,
        })

    return pd.DataFrame(rows).set_index("country")


def compute_prediction_interval(
    factor_scores: dict,
    weights: dict,
    year: int,
    country: str,
    n_simulations: int = 1000,
) -> dict:
    """
    Retourne les percentiles [P10, P25, P75, P90] du score composite simulé.
    """
    rng = np.random.default_rng(42)
    stats = _get_factor_stats(factor_scores, country, year)

    sims = np.zeros(n_simulations)
    base = 0.0
    for fi in ["F1", "F2", "F3", "F4", "F5"]:
        w_i   = weights.get(fi, 0.0)
        val_i = stats[fi]["val"]
        std_i = stats[fi]["std"]
        base += w_i * val_i
        sims += w_i * (val_i + rng.normal(0, std_i, n_simulations))

    p10, p25, p75, p90 = np.percentile(sims, [10, 25, 75, 90])

    return {
        "score_base":    round(base, 4),
        "score_p10":     round(float(p10), 4),
        "score_p25":     round(float(p25), 4),
        "score_p75":     round(float(p75), 4),
        "score_p90":     round(float(p90), 4),
        "position_base": _classify(base),
        "position_p10":  _classify(float(p10)),
        "position_p90":  _classify(float(p90)),
    }
