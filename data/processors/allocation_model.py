"""
Modèle de conversion Position OW/N/UW → Montants € investis par pays.

5 sources pour estimer l'allocation d'un fonds sur un pays :
  Source 1 : AUM actions européennes réel par fonds (EUROPEAN_EQUITY_AUM)
             Remplace AUM_global × ratio forfaitaire (trop imprécis)
  Source 2 : Biais home-country (HOME_COUNTRY_BIAS)
             Les fonds domestiques surpondèrent structurellement leur marché national
  Source 3 : Déviation OW/N/UW calibrée (POSITION_DEVIATIONS)
             Issue du modèle factoriel ou des données réelles ground truth
  Source 4 : Style de gestion passive vs active (FUND_STYLE)
             Les ETF ne peuvent pas dévier significativement du MSCI
  Source 5 : Plafond de capacité de marché (MARKET_CAP_REFERENCE)
             Normalisation pro-rata si le total dépasse la capacité d'absorption

N'importe PAS streamlit.
"""

import json
import pandas as pd
from pathlib import Path

from config import (
    FONDS, COUNTRIES, COUNTRY_NAMES_FR, PREDICTION_YEAR,
    MSCI_EUROPE_WEIGHTS, POSITION_DEVIATIONS, CONFIDENCE_MARGINS,
    EQUITY_EUROPE_SHARE, GROUND_TRUTH_FILE,
    MARKET_CAP_REFERENCE, FOREIGN_INSTITUTIONAL_OWNERSHIP, OUR_FUNDS_MARKET_SHARE,
    EUROPEAN_EQUITY_AUM, HOME_COUNTRY_BIAS, FUND_STYLE,
    PASSIVE_MAX_DEVIATION, SEMI_PASSIVE_MAX_DEVIATION,
    DEVIATION_AMPLIFIER_BY_TYPE, FUND_CONVICTION_OVERRIDE,
)

HOLDINGS_FILE = Path(__file__).parent.parent.parent / "holdings_master.json"


def load_holdings_master() -> dict:
    """Charge holdings_master.json. Retourne {} si absent."""
    if not HOLDINGS_FILE.exists():
        return {}
    with open(HOLDINGS_FILE, encoding="utf-8") as f:
        return json.load(f)


def save_holdings_master(data: dict) -> None:
    """Sauvegarde holdings_master.json."""
    with open(HOLDINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_equity_europe_aum(fund_key: str) -> float:
    """
    Retourne les AUM actions européennes d'un fonds (Md€).
    Priorité : EUROPEAN_EQUITY_AUM (données réelles) > AUM_global × ratio_type.
    """
    if fund_key in EUROPEAN_EQUITY_AUM:
        return float(EUROPEAN_EQUITY_AUM[fund_key])
    fund_cfg = FONDS.get(fund_key, {})
    aum_total = fund_cfg.get("aum_md_eur", 0.0)
    typologie = fund_cfg.get("typologie", "Généraliste Volume")
    return aum_total * EQUITY_EUROPE_SHARE.get(typologie, 0.35)


def compute_fund_allocation(
    fund_key: str,
    country: str,
    position: str,
    source: str = "model_predicted",
) -> tuple:
    """
    Calcule le montant estimé d'un fonds sur un pays donné.
    Combine 4 sources pour une estimation réaliste.
    Retourne (montant_central, montant_min, montant_max) en Md€.
    """
    if position not in ("OW", "N", "UW"):
        position = "N"

    fund_cfg = FONDS.get(fund_key, {})

    # Source 1 : AUM actions européennes (données réelles si disponibles)
    equity_europe = get_equity_europe_aum(fund_key)

    # Source 2 : Poids MSCI de base × biais home-country
    msci_weight = MSCI_EUROPE_WEIGHTS.get(country, 0.05)
    home_bias = HOME_COUNTRY_BIAS.get(fund_key, {}).get(country, 1.0)
    effective_msci_weight = msci_weight * home_bias

    # Source 3 : Déviation OW/N/UW de base (calibrée sur les fonds confirmés)
    base_deviation = POSITION_DEVIATIONS.get(position, {}).get(country, 0.0)

    # Source 4a : Amplificateur conviction (boutique dévie ~2x plus qu'un généraliste)
    typologie = fund_cfg.get("typologie", "Généraliste Volume")
    amplifier = FUND_CONVICTION_OVERRIDE.get(
        fund_key,
        DEVIATION_AMPLIFIER_BY_TYPE.get(typologie, 1.0)
    )
    deviation = base_deviation * amplifier

    # Source 4b : Contrainte passive — plafonne la déviation pour les ETF/index
    style = FUND_STYLE.get(fund_key, "actif")
    if style == "passif":
        deviation = max(-PASSIVE_MAX_DEVIATION, min(PASSIVE_MAX_DEVIATION, deviation))
    elif style == "semi_passif":
        deviation = max(-SEMI_PASSIVE_MAX_DEVIATION, min(SEMI_PASSIVE_MAX_DEVIATION, deviation))

    montant_brut = equity_europe * max(0.001, effective_msci_weight + deviation)

    # Déviation intentionnelle en points de % (avant normalisation = signal pur)
    # = (home_bias - 1) × MSCI + déviation position × amplificateur
    msci_base = MSCI_EUROPE_WEIGHTS.get(country, 0.05)
    intended_deviation_pp = ((effective_msci_weight - msci_base) + deviation) * 100

    # Marge d'erreur selon fiabilité de la source de la position
    confidence_margin = CONFIDENCE_MARGINS.get(source, 0.35)
    montant_min = montant_brut * (1 - confidence_margin)
    montant_max = montant_brut * (1 + confidence_margin)

    return montant_brut, montant_min, montant_max, intended_deviation_pp


def compute_country_total(country: str, raw_allocs: dict) -> tuple:
    """
    Agrège les montants de tous les fonds sur un pays.
    Source 5 : Applique un plafond agrégé basé sur la capitalisation réelle du marché.

    raw_allocs : {fund_key: (montant_central, montant_min, montant_max)}
    Retourne : (total_brut, total_min, total_max, normalized, plafond_agrege)
    """
    total_brut = sum(a[0] for a in raw_allocs.values())
    total_min  = sum(a[1] for a in raw_allocs.values())
    total_max  = sum(a[2] for a in raw_allocs.values())

    market_cap = MARKET_CAP_REFERENCE.get(country, 1000.0)
    foreign_share = FOREIGN_INSTITUTIONAL_OWNERSHIP.get(country, 0.40)
    plafond_agrege = market_cap * foreign_share * OUR_FUNDS_MARKET_SHARE

    if total_brut > plafond_agrege and total_brut > 0:
        facteur = plafond_agrege / total_brut
        return plafond_agrege, total_min * facteur, total_max * facteur, True, plafond_agrege
    return total_brut, total_min, total_max, False, plafond_agrege


def compute_all_allocations(
    predictions: dict,
    ground_truth: dict,
    ml_predictions: dict = None,
    year: int = None,
) -> tuple:
    """
    Calcule les allocations pour tous les fonds et tous les pays.
    Applique les 5 sources d'estimation, puis le plafond agrégé par pays.

    predictions     : {country: {fund_key: "OW/N/UW"}}  (modèle factoriel)
    ground_truth    : ground_truth_master.json
    ml_predictions  : {country: {"position": "OW/N/UW", ...}}
    year            : année cible (défaut = PREDICTION_YEAR)

    Retourne : (allocations, normalization_by_country)
      allocations              : {fund_key: {country: allocation_dict}}
      normalization_by_country : {country: {"normalized": bool, "plafond_agrege": float}}
    """
    if year is None:
        year = PREDICTION_YEAR

    year_str = str(year)

    # Phase 1 : allocations brutes par (country, fund_key)
    raw_by_country = {country: {} for country in COUNTRIES}

    for fund_key in FONDS:
        for country in COUNTRIES:
            country_fr = COUNTRY_NAMES_FR.get(country, country)
            position = None
            source = "model_predicted"

            # 1. Ground truth confirmé (meilleure source)
            gt_year = ground_truth.get(fund_key, {}).get(year_str, {})
            if gt_year.get(country_fr) in ("OW", "N", "UW"):
                position = gt_year[country_fr]
                source = "ground_truth_confirmed"

            # 2. Prédiction ML
            if position is None and ml_predictions:
                ml_pred = ml_predictions.get(country, {})
                if ml_pred.get("position") in ("OW", "N", "UW"):
                    position = ml_pred["position"]
                    source = "ml_predicted"

            # 3. Modèle factoriel (fallback)
            if position is None:
                position = predictions.get(country, {}).get(fund_key, "N")
                source = "model_predicted"

            central, fmin, fmax, intended_dev = compute_fund_allocation(fund_key, country, position, source)
            raw_by_country[country][fund_key] = (central, fmin, fmax, source, position, intended_dev)

    # Phase 2 : calculer les facteurs de normalisation par pays (plafond agrégé)
    normalization_by_country = {}
    facteurs = {}

    for country in COUNTRIES:
        raw_tuples = {fk: v[:3] for fk, v in raw_by_country[country].items()}
        total_brut = sum(a[0] for a in raw_tuples.values())

        market_cap = MARKET_CAP_REFERENCE.get(country, 1000.0)
        foreign_share = FOREIGN_INSTITUTIONAL_OWNERSHIP.get(country, 0.40)
        plafond_agrege = market_cap * foreign_share * OUR_FUNDS_MARKET_SHARE

        if total_brut > plafond_agrege and total_brut > 0:
            facteurs[country] = plafond_agrege / total_brut
            normalized = True
        else:
            facteurs[country] = 1.0
            normalized = False

        normalization_by_country[country] = {
            "normalized":     normalized,
            "plafond_agrege": round(plafond_agrege, 1),
        }

    # Phase 3 : construire le dict final {fund_key: {country: allocation_dict}}
    result = {}
    for fund_key in FONDS:
        result[fund_key] = {}
        for country in COUNTRIES:
            central, fmin, fmax, source, position, intended_dev = raw_by_country[country][fund_key]
            facteur = facteurs[country]

            central_adj = central * facteur
            fmin_adj    = fmin    * facteur
            fmax_adj    = fmax    * facteur

            equity_europe = get_equity_europe_aum(fund_key)
            allocation_pct = (central_adj / equity_europe * 100) if equity_europe > 0 else 0.0
            marge = CONFIDENCE_MARGINS.get(source, 0.35)
            confiance = max(10, min(95, int((1 - marge) * 100)))

            result[fund_key][country] = {
                "montant_central_md":   round(central_adj, 3),
                "montant_min_md":       round(fmin_adj, 3),
                "montant_max_md":       round(fmax_adj, 3),
                "allocation_pct":       round(allocation_pct, 2),
                "intended_deviation_pp": round(intended_dev, 2),  # signal pur avant normalisation
                "marge_erreur_pct":     round(marge * 100, 1),
                "confiance_pct":        confiance,
                "source":               source,
                "position":             position,
            }

    return result, normalization_by_country


def get_allocation_summary(allocations: dict) -> pd.DataFrame:
    """Construit un DataFrame de synthèse des allocations."""
    rows = []
    for fund_key, countries in allocations.items():
        fund_cfg  = FONDS.get(fund_key, {})
        fund_name = fund_cfg.get("nom", fund_key)
        aum_total = fund_cfg.get("aum_md_eur", 0)

        for country, alloc in countries.items():
            country_fr = COUNTRY_NAMES_FR.get(country, country)
            rows.append({
                "Fonds":           fund_name,
                "Pays":            country_fr,
                "AUM total (Md€)": aum_total,
                "Montant (Md€)":   alloc["montant_central_md"],
                "Min (Md€)":       alloc["montant_min_md"],
                "Max (Md€)":       alloc["montant_max_md"],
                "% portefeuille":  alloc["allocation_pct"],
                "Marge erreur":    f"±{alloc['marge_erreur_pct']}%",
                "Confiance":       f"{alloc['confiance_pct']}%",
                "Position":        alloc["position"],
                "Source":          alloc["source"],
            })

    return pd.DataFrame(rows)


def get_country_total(allocations: dict, country: str) -> dict:
    """
    Agrège les montants de tous les fonds pour un pays donné.
    Les plafonds ont déjà été appliqués dans compute_all_allocations.
    """
    total_central = 0.0
    total_min = 0.0
    total_max = 0.0
    n_fonds = 0

    for fund_key, countries in allocations.items():
        alloc = countries.get(country, {})
        if alloc:
            total_central += alloc.get("montant_central_md", 0)
            total_min     += alloc.get("montant_min_md", 0)
            total_max     += alloc.get("montant_max_md", 0)
            n_fonds += 1

    return {
        "pays":             COUNTRY_NAMES_FR.get(country, country),
        "total_central_md": round(total_central, 2),
        "total_min_md":     round(total_min, 2),
        "total_max_md":     round(total_max, 2),
        "n_fonds":          n_fonds,
    }
