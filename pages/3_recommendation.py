"""
Page 3 : Recommandation Edram — Suivre le consensus ou stratégie contrarian.
"""
import json

import streamlit as st
import pandas as pd

from config import (
    COUNTRIES, COUNTRY_NAMES_FR, DEFAULT_WEIGHTS,
    FONDS, FUND_KEYS, POSITION_COLORS, POSITION_LABELS,
    PREDICTION_YEAR, GROUND_TRUTH_FILE,
)
from data.fetchers.macro_data import fetch_gdp_growth
from data.fetchers.market_data import compute_annual_returns, fetch_equity_prices, fetch_per_data, fetch_sovereign_spreads
from data.fetchers.political_data import load_political_scores
from data.processors.scoring import build_full_scores
from data.processors.confidence import compute_probabilities
from data.processors.consensus import compute_market_consensus, generate_edram_recommendation
from components.map import make_choropleth_europe, make_double_choropleth
from llm.agent import generate_recommendation_analysis

st.set_page_config(page_title="Recommandation Edram", page_icon="🎯", layout="wide")
st.title(f"Recommandation Edram — {PREDICTION_YEAR}")
st.caption("Stratégie d'allocation géographique · Suivre le consensus ou se différencier")

# ── Mode ───────────────────────────────────────────────────────────────────────
mode = st.radio(
    "Stratégie Edram",
    options=["consensus", "contrarian"],
    format_func=lambda x: "Suivre le consensus de marché" if x == "consensus" else "Stratégie contrarian",
    horizontal=True,
    key="reco_mode",
)

st.divider()

# ── Données ────────────────────────────────────────────────────────────────────
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

proba_df = compute_probabilities(
    factor_scores={k: scores[k] for k in ["F1","F2","F3","F4","F5"]},
    composite_scores=scores["composite"],
    predicted_positions=scores["positions"],
    weights=weights,
    year=PREDICTION_YEAR,
)

# ── Positions consensus (mêmes que page 1) ────────────────────────────────────
gt_master = {}
try:
    with open(GROUND_TRUTH_FILE, encoding="utf-8") as f:
        gt_master = json.load(f)
except FileNotFoundError:
    pass

all_fund_positions = {}
for fk in FUND_KEYS:
    gt_2025 = gt_master.get(fk, {}).get("2025", {})
    positions_fund = {}
    for country in COUNTRIES:
        country_fr = COUNTRY_NAMES_FR.get(country, country)
        gt_pos = gt_2025.get(country_fr)
        if gt_pos in ("OW", "N", "UW"):
            positions_fund[country] = gt_pos
        else:
            if PREDICTION_YEAR in scores["positions"].index and country in scores["positions"].columns:
                positions_fund[country] = scores["positions"].at[PREDICTION_YEAR, country]
            else:
                positions_fund[country] = "N"
    all_fund_positions[fk] = positions_fund

consensus_df    = compute_market_consensus(all_fund_positions, PREDICTION_YEAR)
recommendation_df = generate_edram_recommendation(consensus_df, proba_df)

# ── Tableau de recommandation ─────────────────────────────────────────────────
st.subheader("Recommandations par pays")

pos_col  = "follow_consensus" if mode == "consensus" else "contrarian"
just_col = "follow_justification" if mode == "consensus" else "contrarian_justification"

rows = []
for country in COUNTRIES:
    if country not in recommendation_df.index:
        continue
    r  = recommendation_df.loc[country]
    c  = consensus_df.loc[country] if country in consensus_df.index else {}
    p  = proba_df.loc[country] if country in proba_df.index else {}

    rec_pos = r.get(pos_col, "N")
    rows.append({
        "Pays":           COUNTRY_NAMES_FR.get(country, country),
        "Recommandation": POSITION_LABELS.get(rec_pos, rec_pos),
        "Consensus":      c.get("consensus_label", "?") if hasattr(c, "get") else "?",
        "Force consensus": f"{float(c.get('consensus_strength', 0)):.0%}" if hasattr(c, "get") else "?",
        "Prob. modèle":   f"{float(p.get('prob_predicted', 0)):.0%}" if hasattr(p, "get") else "?",
        "Conviction":     r.get("conviction_level", "?"),
        "Justification":  r.get(just_col, ""),
        "_rec_pos":       rec_pos,
    })

reco_df = pd.DataFrame(rows)

def _style_rec(val):
    colors = {
        "Surpondéré":   POSITION_COLORS["OW"] + "33",
        "Neutre":       POSITION_COLORS["N"]  + "22",
        "Sous-pondéré": POSITION_COLORS["UW"] + "33",
    }
    return f"background-color: {colors.get(val, '')}"

def _style_conv(val):
    c = {"Haute": "#d5f5e3", "Moyenne": "#fef9e7", "Faible": "#fadbd8"}
    return f"background-color: {c.get(val, '')}"

styled = (
    reco_df.drop(columns=["_rec_pos"])
    .style
    .applymap(_style_rec,  subset=["Recommandation"])
    .applymap(_style_conv, subset=["Conviction"])
)
st.dataframe(styled, use_container_width=True, hide_index=True)

st.divider()

# ── Double choroplèthe ────────────────────────────────────────────────────────
st.subheader("Carte comparée — Consensus marché vs Recommandation Edram")

# Consensus positions DataFrame
consensus_positions = pd.DataFrame(
    {c: {PREDICTION_YEAR: consensus_df.at[c, "consensus_position"]} for c in COUNTRIES}
)
consensus_composite = pd.DataFrame(
    {c: {PREDICTION_YEAR: float(
        consensus_df.at[c, "consensus_strength"] *
        (1 if consensus_df.at[c, "consensus_position"] == "OW"
         else -1 if consensus_df.at[c, "consensus_position"] == "UW"
         else 0)
    )} for c in COUNTRIES}
)

# Edram recommendation positions DataFrame
reco_positions = pd.DataFrame(
    {c: {PREDICTION_YEAR: recommendation_df.at[c, pos_col]}
     for c in COUNTRIES if c in recommendation_df.index}
)
reco_composite = pd.DataFrame(
    {c: {PREDICTION_YEAR: float(
        recommendation_df.at[c, "conviction_score"] *
        (1 if recommendation_df.at[c, pos_col] == "OW"
         else -1 if recommendation_df.at[c, pos_col] == "UW"
         else 0)
    )} for c in COUNTRIES if c in recommendation_df.index}
)

try:
    fig_left, fig_right = make_double_choropleth(
        consensus_positions, consensus_composite,
        reco_positions, reco_composite,
        PREDICTION_YEAR,
        f"Consensus marché {PREDICTION_YEAR}",
        f"Edram — {'Suivre consensus' if mode == 'consensus' else 'Contrarian'}",
    )
    col_l, col_r = st.columns(2)
    with col_l:
        st.plotly_chart(fig_left, use_container_width=True)
    with col_r:
        st.plotly_chart(fig_right, use_container_width=True)
except Exception as e:
    st.warning(f"Carte non disponible : {e}")

st.divider()

# ── Analyse narrative Claude ───────────────────────────────────────────────────
st.subheader("Analyse narrative — Intelligence artificielle")
st.caption("Génération par Groq · Llama-3.3-70b-versatile · Gratuit sur console.groq.com")

api_key = st.session_state.get("groq_api_key", "")
if not api_key:
    st.info(
        "Cette fonctionnalité utilise **Groq** (gratuit). "
        "Obtenez votre clé sur console.groq.com — "
        "inscription gratuite, pas de carte bancaire requise."
    )
    inline_key = st.text_input(
        "Clé API Groq",
        type="password",
        placeholder="gsk_...",
        key="reco_groq_key_inline",
    )
    if inline_key:
        st.session_state["groq_api_key"] = inline_key
        st.rerun()

mode_label = "Suivre le consensus" if mode == "consensus" else "Stratégie contrarian"
btn_disabled = not bool(api_key)

if st.button(
    f"Générer l'analyse — {mode_label}",
    disabled=btn_disabled,
    type="primary",
    key="reco_generate_btn",
):
    with st.spinner("Analyse en cours par Groq (Llama 3.3)..."):
        try:
            analysis = generate_recommendation_analysis(
                api_key=st.session_state.get("groq_api_key", ""),
                consensus_df=consensus_df,
                recommendation_df=recommendation_df,
                probabilities_df=proba_df,
                mode=mode,
                weights=weights,
            )
            st.session_state["reco_analysis"] = analysis
        except Exception as e:
            st.error(f"Erreur lors de l'appel Claude : {e}")

if "reco_analysis" in st.session_state:
    st.markdown(st.session_state["reco_analysis"])
    st.download_button(
        "Télécharger l'analyse (Markdown)",
        data=st.session_state["reco_analysis"],
        file_name=f"edram_analyse_{PREDICTION_YEAR}_{mode}.md",
        mime="text/markdown",
    )
