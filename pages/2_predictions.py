"""
Page 2 : Prédictions détaillées par fonds — 2026.
"""
import streamlit as st
import pandas as pd

from config import (
    COUNTRIES, COUNTRY_NAMES_FR, DEFAULT_WEIGHTS,
    FACTOR_LABELS, FONDS, FUNDS, FUND_KEYS,
    POSITION_COLORS, POSITION_LABELS, PREDICTION_YEAR, get_fund_key,
)
from data.fetchers.macro_data import fetch_gdp_growth
from data.fetchers.market_data import compute_annual_returns, fetch_equity_prices, fetch_per_data, fetch_sovereign_spreads
from data.fetchers.political_data import load_political_scores
from data.processors.scoring import build_full_scores, get_factor_contributions
from data.processors.confidence import compute_probabilities, compute_prediction_interval
from components.charts import make_radar_chart, make_waterfall_contributions

st.set_page_config(page_title="Prédictions détaillées", page_icon="📊", layout="wide")
st.title(f"Prédictions détaillées — {PREDICTION_YEAR}")
st.caption("Analyse factorielle par fonds · Intervalles de confiance Monte Carlo")

st.info(
    "ℹ️ Les prédictions sont basées sur 5 facteurs macro pays (F1-F5). "
    "Le modèle produit la même prédiction macro pour tous les fonds sur un même pays. "
    "La différenciation par fonds reflète leurs positions réelles historiques "
    "disponibles dans ground_truth_master.json. "
    "Pour enrichir les prédictions fonds par fonds, utilisez la collecte "
    "automatique dans la Page Paramètres."
)

if st.button("🔄 Forcer le rechargement des données"):
    st.cache_data.clear()
    st.rerun()

# ── Sélecteurs ────────────────────────────────────────────────────────────────
col_fund, col_country = st.columns([2, 2])
with col_fund:
    fund_nom = st.selectbox("Fonds", FUNDS, key="pred_fund")
with col_country:
    country_fr = st.selectbox("Pays (waterfall)", [COUNTRY_NAMES_FR.get(c, c) for c in COUNTRIES], key="pred_country")

selected_country = next((c for c in COUNTRIES if COUNTRY_NAMES_FR.get(c, c) == country_fr), COUNTRIES[0])

# ── Données ────────────────────────────────────────────────────────────────────
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

st.divider()

# ── Tableau de prédiction ─────────────────────────────────────────────────────
st.subheader(f"Prédictions {PREDICTION_YEAR} — {fund_nom}")
st.caption("Toutes les prédictions sont issues du modèle factoriel macro (même modèle pour tous les fonds).")

rows = []
for country in COUNTRIES:
    score_val = float(scores["composite"].at[PREDICTION_YEAR, country]) \
        if PREDICTION_YEAR in scores["composite"].index else 0.0
    pos = scores["positions"].at[PREDICTION_YEAR, country] \
        if PREDICTION_YEAR in scores["positions"].index else "N"

    interval = compute_prediction_interval(
        {k: scores[k] for k in ["F1","F2","F3","F4","F5"]},
        weights, PREDICTION_YEAR, country,
    )
    p = proba_df.loc[country] if country in proba_df.index else {}

    rows.append({
        "Pays":           COUNTRY_NAMES_FR.get(country, country),
        "Score composite": f"{score_val:+.3f}",
        "Position":       POSITION_LABELS.get(pos, pos),
        "Prob. OW":       f"{p.get('prob_OW', 0):.0%}",
        "Prob. N":        f"{p.get('prob_N', 0):.0%}",
        "Prob. UW":       f"{p.get('prob_UW', 0):.0%}",
        "Intervalle [P10;P90]": f"[{interval['score_p10']:+.3f} ; {interval['score_p90']:+.3f}]",
        "Confiance":      p.get("confidence_level", "?"),
        "_pos":           pos,
    })

pred_df = pd.DataFrame(rows)

def _style_pos(val):
    colors = {"Surpondéré": POSITION_COLORS["OW"] + "33",
              "Neutre":     POSITION_COLORS["N"]  + "22",
              "Sous-pondéré": POSITION_COLORS["UW"] + "33"}
    return f"background-color: {colors.get(val, '')}"

def _style_conf(val):
    c = {"Haute": "#d5f5e3", "Moyenne": "#fef9e7", "Faible": "#fadbd8"}
    return f"background-color: {c.get(val, '')}"

styled = (
    pred_df.drop(columns=["_pos"])
    .style.applymap(_style_pos, subset=["Position"])
    .applymap(_style_conf, subset=["Confiance"])
)
st.dataframe(styled, use_container_width=True, hide_index=True)

st.divider()

# ── Radar + Waterfall côte à côte ─────────────────────────────────────────────
col_radar, col_wf = st.columns([1, 1])

with col_radar:
    st.subheader("Radar — Scores composites par pays")
    fig_radar = make_radar_chart(scores["composite"], PREDICTION_YEAR)
    st.plotly_chart(fig_radar, use_container_width=True)

with col_wf:
    st.subheader(f"Contributions factorielles — {country_fr}")
    comp_val = float(scores["composite"].at[PREDICTION_YEAR, selected_country]) \
        if PREDICTION_YEAR in scores["composite"].index else 0.0
    fig_wf = make_waterfall_contributions(
        {k: scores[k] for k in ["F1","F2","F3","F4","F5"]},
        weights, selected_country, PREDICTION_YEAR, comp_val,
    )
    st.plotly_chart(fig_wf, use_container_width=True)

st.divider()

# ── Tableau F1-F5 ─────────────────────────────────────────────────────────────
st.subheader("Scores par facteur — tous les pays")

factor_rows = []
for country in COUNTRIES:
    row = {"Pays": COUNTRY_NAMES_FR.get(country, country)}
    for fi in ["F1", "F2", "F3", "F4", "F5"]:
        df_fi = scores.get(fi)
        v = 0.0
        if df_fi is not None and PREDICTION_YEAR in df_fi.index and country in df_fi.columns:
            v = float(df_fi.at[PREDICTION_YEAR, country])
        row[FACTOR_LABELS.get(fi, fi)] = f"{v:+.3f}"
    factor_rows.append(row)

st.dataframe(pd.DataFrame(factor_rows), use_container_width=True, hide_index=True)
