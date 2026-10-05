"""
Page 1 : Consensus marché 2026 — Où investissent les concurrents ?
"""
import json
import streamlit as st
import pandas as pd

from config import (
    COUNTRIES, COUNTRY_NAMES_FR, DEFAULT_WEIGHTS,
    FONDS, FUND_KEYS, FUNDS, GROUND_TRUTH_FILE,
    POSITION_COLORS, POSITION_LABELS, PREDICTION_YEAR,
)
from data.fetchers.macro_data import fetch_gdp_growth
from data.fetchers.market_data import compute_annual_returns, fetch_equity_prices, fetch_per_data, fetch_sovereign_spreads
from data.fetchers.political_data import load_political_scores
from data.processors.scoring import build_full_scores
from data.processors.confidence import compute_probabilities
from data.processors.consensus import compute_market_consensus
from components.charts import make_consensus_heatmap, make_consensus_bar
from components.map import make_choropleth_europe

st.set_page_config(page_title="Consensus Marché", page_icon="🌍", layout="wide")
st.title(f"Consensus marché {PREDICTION_YEAR}")
st.caption("Où investissent les 31 fonds concurrents en 2026 ? · Modèle factoriel macro")

# ── Chargement ────────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def _load_all():
    prices  = fetch_equity_prices()
    returns = compute_annual_returns(prices)
    gdp     = fetch_gdp_growth()
    spreads = fetch_sovereign_spreads()
    pol     = load_political_scores()
    per     = fetch_per_data()
    return returns, gdp, spreads, pol, per

with st.spinner("Chargement des données..."):
    annual_returns, gdp_growth, spreads, political, per_data = _load_all()

weights = st.session_state.get("weights") or DEFAULT_WEIGHTS
scores  = build_full_scores(annual_returns, gdp_growth, spreads, political, per_data, weights=weights)

if scores["warnings"]:
    with st.expander(f"{len(scores['warnings'])} avertissement(s)", expanded=False):
        for w in scores["warnings"]:
            st.warning(w)

# ── Probabilités Monte Carlo ──────────────────────────────────────────────────
proba_df = compute_probabilities(
    factor_scores={k: scores[k] for k in ["F1","F2","F3","F4","F5"]},
    composite_scores=scores["composite"],
    predicted_positions=scores["positions"],
    weights=weights,
    year=PREDICTION_YEAR,
)

# ── Préparation des positions par fonds ───────────────────────────────────────
# Pour chaque fonds : utiliser ground_truth 2025 si disponible, sinon modèle 2026
gt_master = {}
try:
    with open(GROUND_TRUTH_FILE, encoding="utf-8") as f:
        gt_master = json.load(f)
except FileNotFoundError:
    pass

all_fund_positions = {}
for fk in FUND_KEYS:
    # Chercher position réelle 2025 en GT (le plus récent connu)
    gt_2025 = gt_master.get(fk, {}).get("2025", {})
    positions_fund = {}
    for country in COUNTRIES:
        country_fr = COUNTRY_NAMES_FR.get(country, country)
        gt_pos = gt_2025.get(country_fr)
        if gt_pos in ("OW", "N", "UW"):
            positions_fund[country] = gt_pos
        else:
            # Modèle 2026
            if PREDICTION_YEAR in scores["positions"].index and country in scores["positions"].columns:
                positions_fund[country] = scores["positions"].at[PREDICTION_YEAR, country]
            else:
                positions_fund[country] = "N"
    all_fund_positions[fk] = positions_fund

# ── Consensus ─────────────────────────────────────────────────────────────────
consensus_df = compute_market_consensus(all_fund_positions, PREDICTION_YEAR)

# ── KPIs ──────────────────────────────────────────────────────────────────────
st.divider()
n_fw_ow = (consensus_df["consensus_position"] == "OW").sum()
n_fw_uw = (consensus_df["consensus_position"] == "UW").sum()
n_fw_n  = (consensus_df["consensus_position"] == "N").sum()
avg_str = consensus_df["consensus_strength"].mean()

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Fonds analysés", len(FUND_KEYS))
k2.metric("Pays OW consensus", n_fw_ow)
k3.metric("Pays neutres", n_fw_n)
k4.metric("Pays UW consensus", n_fw_uw)
k5.metric("Force consensus moy.", f"{avg_str:.0%}")

st.divider()

# ── Heatmap principale ────────────────────────────────────────────────────────
st.subheader("Heatmap des positions — tous les fonds")
st.caption(
    "Vert = Surpondéré · Gris = Neutre · Rouge = Sous-pondéré. "
    "Annotation = position (OW/N/UW). "
    "Les probabilités Monte Carlo sont identiques pour tous les fonds d'un même pays "
    "(facteurs macro pays, pas fonds-spécifiques) — voir tableau ci-dessous."
)
fund_display_names = {fk: FONDS[fk]["nom"] for fk in FUND_KEYS}
fig_heatmap = make_consensus_heatmap(all_fund_positions, fund_display_names, proba_df)
st.plotly_chart(fig_heatmap, use_container_width=True)

st.divider()

# ── Barre empilée + tableau ────────────────────────────────────────────────────
col_bar, col_table = st.columns([1.2, 1])

with col_bar:
    st.subheader("Consensus par pays — distribution OW / N / UW")
    fig_bar = make_consensus_bar(consensus_df)
    st.plotly_chart(fig_bar, use_container_width=True)

with col_table:
    st.subheader("Synthèse du consensus")
    display = consensus_df[["country_fr", "consensus_label", "consensus_strength",
                              "n_OW", "n_N", "n_UW"]].copy()
    display.columns = ["Pays", "Consensus", "Force", "# OW", "# N", "# UW"]
    display["Force"] = display["Force"].map(lambda x: f"{x:.0%}")

    # Ajouter probabilité Monte Carlo (une seule valeur par pays, indépendante du fonds)
    if proba_df is not None:
        display["Prob. MC"] = display.index.map(
            lambda c: f"{proba_df.at[c, 'prob_predicted']:.0%}"
            if c in proba_df.index else "—"
        )

    def _style_consensus(val):
        if "OW" in str(val):
            return f"background-color: {POSITION_COLORS['OW']}33"
        if "UW" in str(val):
            return f"background-color: {POSITION_COLORS['UW']}33"
        return ""

    styled = display.style.applymap(_style_consensus, subset=["Consensus"])
    st.dataframe(styled, use_container_width=True, hide_index=True)

st.divider()

# ── Carte choroplèthe ─────────────────────────────────────────────────────────
st.subheader("Carte Europe — position consensus")

# Construire un DataFrame de positions et scores à partir du consensus
consensus_positions = pd.DataFrame(
    {c: {PREDICTION_YEAR: consensus_df.at[c, "consensus_position"]} for c in COUNTRIES}
)
consensus_positions.index.name = "year"
consensus_composite = pd.DataFrame(
    {c: {PREDICTION_YEAR: float(consensus_df.at[c, "consensus_strength"] *
                                 (1 if consensus_df.at[c, "consensus_position"] == "OW"
                                  else -1 if consensus_df.at[c, "consensus_position"] == "UW"
                                  else 0))}
     for c in COUNTRIES}
)
consensus_composite.index.name = "year"

fig_map = make_choropleth_europe(consensus_positions, consensus_composite, PREDICTION_YEAR,
                                  f"Consensus marché {PREDICTION_YEAR}")
st.plotly_chart(fig_map, use_container_width=True)

# ── Probabilités détaillées ───────────────────────────────────────────────────
with st.expander("Probabilités Monte Carlo par pays", expanded=False):
    prob_display = proba_df[["position", "prob_OW", "prob_N", "prob_UW",
                               "prob_predicted", "confidence_level"]].copy()
    prob_display.index = [COUNTRY_NAMES_FR.get(c, c) for c in prob_display.index]
    prob_display.columns = ["Position prédite", "Prob. OW", "Prob. N",
                             "Prob. UW", "Prob. prédite", "Confiance"]
    for col in ["Prob. OW", "Prob. N", "Prob. UW", "Prob. prédite"]:
        prob_display[col] = prob_display[col].map(lambda x: f"{x:.0%}")
    prob_display["Position prédite"] = prob_display["Position prédite"].map(
        lambda x: POSITION_LABELS.get(x, x))
    st.dataframe(prob_display, use_container_width=True)
