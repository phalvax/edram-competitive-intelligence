"""
Agrégation des prédictions inter-fonds et recommandation Edram.
Sans Streamlit.
"""
import pandas as pd

from config import (
    COUNTRIES,
    COUNTRY_NAMES_FR,
    CONFIDENCE_HIGH,
    CONFIDENCE_MEDIUM,
    POSITION_LABELS,
)


def compute_market_consensus(
    all_fund_positions: dict,
    year: int = None,
) -> pd.DataFrame:
    """
    Calcule le consensus de marché à partir des positions de tous les fonds.

    all_fund_positions : {fund_key: {country: "OW"/"N"/"UW"}}
                         (positions pour l'année cible, déjà extraites)

    Retourne DataFrame indexé par country avec :
    pct_OW, pct_N, pct_UW, n_OW, n_N, n_UW, n_total,
    consensus_position, consensus_strength, consensus_label, country_fr
    """
    rows = []
    for country in COUNTRIES:
        counts = {"OW": 0, "N": 0, "UW": 0}
        n_total = 0
        for fk, positions in all_fund_positions.items():
            pos = positions.get(country)
            if pos in counts:
                counts[pos] += 1
                n_total += 1

        if n_total == 0:
            rows.append({
                "country": country, "country_fr": COUNTRY_NAMES_FR.get(country, country),
                "pct_OW": 0.0, "pct_N": 1.0, "pct_UW": 0.0,
                "n_OW": 0, "n_N": 0, "n_UW": 0, "n_total": 0,
                "consensus_position": "N", "consensus_strength": 0.0, "consensus_label": "Divisé",
            })
            continue

        pct_ow = counts["OW"] / n_total
        pct_n  = counts["N"]  / n_total
        pct_uw = counts["UW"] / n_total

        consensus_pos = max(counts, key=counts.get)
        strength = max(pct_ow, pct_n, pct_uw)

        if strength >= 0.67:
            prefix = "Fort"
        elif strength >= 0.50:
            prefix = "Modéré"
        else:
            prefix = "Divisé"

        if prefix == "Divisé" or consensus_pos == "N":
            label = "Divisé" if prefix == "Divisé" else "Neutre"
        elif consensus_pos == "OW":
            label = f"{prefix} OW"
        else:
            label = f"{prefix} UW"

        rows.append({
            "country":            country,
            "country_fr":         COUNTRY_NAMES_FR.get(country, country),
            "pct_OW":             round(pct_ow, 3),
            "pct_N":              round(pct_n,  3),
            "pct_UW":             round(pct_uw, 3),
            "n_OW":               counts["OW"],
            "n_N":                counts["N"],
            "n_UW":               counts["UW"],
            "n_total":            n_total,
            "consensus_position": consensus_pos,
            "consensus_strength": round(strength, 3),
            "consensus_label":    label,
        })

    return pd.DataFrame(rows).set_index("country")


def generate_edram_recommendation(
    consensus_df: pd.DataFrame,
    probabilities_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Génère les recommandations Edram (suivre/contrarian) pour chaque pays.

    Retourne DataFrame indexé par country avec :
    country_fr, follow_consensus, contrarian, recommended_action,
    conviction_level, conviction_score, follow_justification, contrarian_justification
    """
    rows = []
    _pos_fr = {
        "OW": "Surpondérer",
        "N":  "Maintenir",
        "UW": "Sous-pondérer",
    }
    _contrarian_map = {"OW": "UW", "UW": "OW", "N": "N"}

    for country in COUNTRIES:
        if country not in consensus_df.index:
            continue
        c = consensus_df.loc[country]
        p = probabilities_df.loc[country] if country in probabilities_df.index else {}

        consensus_pos = c["consensus_position"]
        strength      = float(c["consensus_strength"])
        pct_ow        = float(c["pct_OW"])
        pct_uw        = float(c["pct_UW"])
        prob_pred     = float(p.get("prob_predicted", 0.5)) if hasattr(p, "get") else 0.5
        country_fr    = c["country_fr"]

        contrarian_pos = _contrarian_map.get(consensus_pos, "N")
        conviction     = round(strength * prob_pred, 3)

        if conviction >= CONFIDENCE_HIGH:
            conv_level = "Haute"
        elif conviction >= CONFIDENCE_MEDIUM:
            conv_level = "Moyenne"
        else:
            conv_level = "Faible"

        # Justifications textuelles
        n_ow = int(c["n_OW"]); n_uw = int(c["n_UW"]); n_total = int(c["n_total"])
        follow_just = (
            f"{pct_ow:.0%} des fonds surpondèrent {country_fr} — "
            f"consensus {c['consensus_label']} ({n_ow}/{n_total} OW). "
            f"Probabilité modèle : {prob_pred:.0%}."
        ) if consensus_pos == "OW" else (
            f"{pct_uw:.0%} des fonds sous-pondèrent {country_fr} — "
            f"consensus {c['consensus_label']} ({n_uw}/{n_total} UW). "
            f"Probabilité modèle : {prob_pred:.0%}."
        ) if consensus_pos == "UW" else (
            f"Consensus neutre sur {country_fr} — "
            f"fonds divisés ({n_ow} OW / {int(c['n_N'])} N / {n_uw} UW). "
            f"Probabilité modèle : {prob_pred:.0%}."
        )

        contrarian_just = (
            f"Contre-pied du consensus {c['consensus_label']} : "
            f"si les marchés sur-réagissent à la dynamique {'positive' if consensus_pos == 'OW' else 'négative'} "
            f"de {country_fr}, une position {POSITION_LABELS.get(contrarian_pos, contrarian_pos)} "
            f"offre un potentiel de différenciation."
        )

        rows.append({
            "country":                  country,
            "country_fr":               country_fr,
            "follow_consensus":         consensus_pos,
            "contrarian":               contrarian_pos,
            "recommended_action":       _pos_fr.get(consensus_pos, consensus_pos),
            "conviction_level":         conv_level,
            "conviction_score":         conviction,
            "follow_justification":     follow_just,
            "contrarian_justification": contrarian_just,
        })

    return pd.DataFrame(rows).set_index("country")
