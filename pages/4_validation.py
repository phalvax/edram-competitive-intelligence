"""
Page 4 : Validation historique du modèle — Précision 2022-2025.
"""
import json

import numpy as np
import streamlit as st
import pandas as pd

from config import (
    COUNTRIES, COUNTRY_NAMES_FR, DEFAULT_WEIGHTS,
    FUND_KEYS, FONDS, GROUND_TRUTH_FILE, HISTORY_YEARS,
    POSITION_LABELS,
)
from data.fetchers.macro_data import fetch_gdp_growth
from data.fetchers.market_data import compute_annual_returns, fetch_equity_prices, fetch_per_data, fetch_sovereign_spreads
from data.fetchers.political_data import load_political_scores
from data.processors.scoring import build_full_scores
from components.charts import make_accuracy_heatmap, make_accuracy_timeline

st.set_page_config(page_title="Validation historique", page_icon="✅", layout="wide")
st.title("Validation historique du modèle")
st.caption(f"Précision des prédictions sur {min(HISTORY_YEARS)}–{max(HISTORY_YEARS)} · Comparaison avec les positions réelles des fonds")

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

# ── Ground truth ───────────────────────────────────────────────────────────────
gt_master = {}
try:
    with open(GROUND_TRUTH_FILE, encoding="utf-8") as f:
        gt_master = json.load(f)
except FileNotFoundError:
    st.error("Fichier ground_truth_master.json introuvable.")
    st.stop()

# ── Calcul de la précision ─────────────────────────────────────────────────────
def _compute_accuracy(fund_key: str, year: int) -> float | None:
    """Calcule la précision du modèle pour un fonds/année donnés."""
    gt_positions = gt_master.get(fund_key, {}).get(str(year), {})
    if not gt_positions:
        return None

    correct = 0
    total   = 0
    for country in COUNTRIES:
        country_fr = COUNTRY_NAMES_FR.get(country, country)
        gt_pos = gt_positions.get(country_fr)
        if gt_pos not in ("OW", "N", "UW"):
            continue

        if year in scores["positions"].index and country in scores["positions"].columns:
            pred_pos = scores["positions"].at[year, country]
        else:
            continue

        total += 1
        if pred_pos == gt_pos:
            correct += 1

    return correct / total if total > 0 else None


# Fonds qui ont des données GT
funds_with_gt = {
    fk: FONDS[fk]["nom"]
    for fk in FUND_KEYS
    if any(str(y) in gt_master.get(fk, {}) for y in HISTORY_YEARS)
}

if not funds_with_gt:
    st.warning("Aucune donnée de validation (ground truth) disponible.")
    st.info("Alimentez le fichier `ground_truth_master.json` avec des positions réelles pour activer cette page.")
    st.stop()

# ── KPIs globaux ───────────────────────────────────────────────────────────────
all_accuracies = []
for fk in funds_with_gt:
    for yr in HISTORY_YEARS:
        acc = _compute_accuracy(fk, yr)
        if acc is not None:
            all_accuracies.append(acc)

global_acc = np.mean(all_accuracies) if all_accuracies else 0.0
n_samples  = len(all_accuracies)

st.divider()
k1, k2, k3, k4 = st.columns(4)
k1.metric("Précision globale", f"{global_acc:.0%}")
k2.metric("Fonds validés", len(funds_with_gt))
k3.metric("Mesures disponibles", n_samples)
k4.metric("Fiabilité", "✅ Fiable" if global_acc >= 0.70 else "⚠ Partielle" if global_acc >= 0.50 else "❌ Insuffisante")

st.divider()

# ── Tableau précision fonds × années ──────────────────────────────────────────
st.subheader("Précision par fonds et par année")

accuracy_data = {}
for fk, fname in funds_with_gt.items():
    row = {}
    for yr in HISTORY_YEARS:
        row[yr] = _compute_accuracy(fk, yr)
    accuracy_data[fname] = row

accuracy_df = pd.DataFrame(accuracy_data).T
accuracy_df.columns = HISTORY_YEARS

fig_heatmap = make_accuracy_heatmap(accuracy_df)
st.plotly_chart(fig_heatmap, use_container_width=True)

st.divider()

# ── Tableau détaillé ───────────────────────────────────────────────────────────
col_tl, col_detail = st.columns([1.3, 1])

with col_tl:
    st.subheader("Évolution de la précision")
    fig_timeline = make_accuracy_timeline(accuracy_df)
    st.plotly_chart(fig_timeline, use_container_width=True)

with col_detail:
    st.subheader("Synthèse par fonds")
    summary_rows = []
    for fk, fname in funds_with_gt.items():
        accs = [accuracy_data[fname].get(yr) for yr in HISTORY_YEARS]
        valid_accs = [a for a in accs if a is not None]
        mean_acc = np.mean(valid_accs) if valid_accs else None
        best_yr  = None
        if valid_accs:
            idx = np.argmax(valid_accs)
            best_yr = HISTORY_YEARS[[i for i,y in enumerate(HISTORY_YEARS)
                                     if accuracy_data[fname].get(y) is not None][idx]]
        summary_rows.append({
            "Fonds":      fname,
            "Précision moy.": f"{mean_acc:.0%}" if mean_acc is not None else "—",
            "Meilleure année": str(best_yr) if best_yr else "—",
            "Fiabilité":  "Haute" if mean_acc and mean_acc >= 0.70
                          else "Moyenne" if mean_acc and mean_acc >= 0.50
                          else "Faible",
            "_acc": mean_acc or 0.0,
        })

    summary_df = pd.DataFrame(summary_rows).sort_values("_acc", ascending=False).drop(columns=["_acc"])

    def _style_fiab(val):
        c = {"Haute": "#d5f5e3", "Moyenne": "#fef9e7", "Faible": "#fadbd8"}
        return f"background-color: {c.get(val, '')}"

    st.dataframe(
        summary_df.style.applymap(_style_fiab, subset=["Fiabilité"]),
        use_container_width=True, hide_index=True
    )

st.divider()

# ── Précision par pays ─────────────────────────────────────────────────────────
st.subheader("Fiabilité par pays")

country_acc = {}
for country in COUNTRIES:
    country_fr = COUNTRY_NAMES_FR.get(country, country)
    correct_total = 0
    n = 0
    for fk in funds_with_gt:
        for yr in HISTORY_YEARS:
            gt_pos = gt_master.get(fk, {}).get(str(yr), {}).get(country_fr)
            if gt_pos not in ("OW", "N", "UW"):
                continue
            if yr in scores["positions"].index and country in scores["positions"].columns:
                pred = scores["positions"].at[yr, country]
                n += 1
                if pred == gt_pos:
                    correct_total += 1
    country_acc[country_fr] = correct_total / n if n > 0 else None

country_rows = []
for cname, acc in country_acc.items():
    country_rows.append({
        "Pays":       cname,
        "Précision":  f"{acc:.0%}" if acc is not None else "—",
        "Fiabilité":  "Haute" if acc and acc >= 0.70
                      else "Moyenne" if acc and acc >= 0.50
                      else "Faible" if acc is not None else "N/D",
        "_acc": acc or -1,
    })

country_df = pd.DataFrame(country_rows).sort_values("_acc", ascending=False).drop(columns=["_acc"])
st.dataframe(
    country_df.style.applymap(_style_fiab, subset=["Fiabilité"]),
    use_container_width=True, hide_index=True
)

st.divider()

# ── Matrice de confusion globale ───────────────────────────────────────────────
st.subheader("Matrice de confusion globale")

conf_mat = {true: {pred: 0 for pred in ("OW", "N", "UW")} for true in ("OW", "N", "UW")}

for fk in funds_with_gt:
    for yr in HISTORY_YEARS:
        gt_year = gt_master.get(fk, {}).get(str(yr), {})
        for country in COUNTRIES:
            country_fr = COUNTRY_NAMES_FR.get(country, country)
            true_pos = gt_year.get(country_fr)
            if true_pos not in ("OW", "N", "UW"):
                continue
            if yr in scores["positions"].index and country in scores["positions"].columns:
                pred_pos = scores["positions"].at[yr, country]
                if pred_pos in conf_mat[true_pos]:
                    conf_mat[true_pos][pred_pos] += 1

conf_data = []
for true in ("OW", "N", "UW"):
    row = {"Position réelle \\ Prédite": POSITION_LABELS.get(true, true)}
    for pred in ("OW", "N", "UW"):
        row[POSITION_LABELS.get(pred, pred)] = conf_mat[true][pred]
    conf_data.append(row)

st.dataframe(pd.DataFrame(conf_data), use_container_width=True, hide_index=True)

st.divider()

# ── Conclusion automatique ─────────────────────────────────────────────────────
st.subheader("Conclusion")

if global_acc >= 0.70:
    st.success(
        f"Le modèle atteint une précision globale de **{global_acc:.0%}** "
        f"sur {n_samples} mesures ({len(funds_with_gt)} fonds, {min(HISTORY_YEARS)}–{max(HISTORY_YEARS)}). "
        f"Ce seuil de 70% valide la fiabilité des prédictions pour une utilisation en production."
    )
elif global_acc >= 0.50:
    st.warning(
        f"Le modèle atteint **{global_acc:.0%}** de précision globale. "
        f"Fiabilité partielle : les prédictions sont indicatives mais doivent être confirmées "
        f"par une analyse qualitative avant toute décision d'allocation."
    )
else:
    st.error(
        f"Précision globale de **{global_acc:.0%}** insuffisante. "
        f"Vérifiez la qualité des données de facteurs et envisagez de recalibrer les poids W1-W5 "
        f"dans la page Paramètres."
    )

st.divider()

# ── Modèle Machine Learning ────────────────────────────────────────────────────
st.subheader("Modèle Machine Learning — Random Forest par pays")
st.caption(
    "Un Random Forest distinct est entraîné pour chaque pays, "
    "avec des features spécifiques à sa structure économique. "
    f"Données d'entraînement : {len(gt_master)} fonds × "
    f"{len(HISTORY_YEARS)} années = positions historiques réelles."
)

from data.processors.country_factors import build_all_features
from data.processors.ml_model import (
    train_all_countries, predict_all_countries_2026,
    get_ml_summary, load_ground_truth,
)

with st.spinner("Entraînement des modèles Random Forest..."):
    all_features = build_all_features(
        scores=scores,
        raw_data={
            "gdp_growth": gdp_growth,
            "spreads":    spreads,
            "per_data":   per_data,
            "political":  political,
        },
    )
    ml_models      = train_all_countries(all_features, gt_master)
    ml_predictions = predict_all_countries_2026(ml_models, all_features)
    ml_summary_df  = get_ml_summary(ml_models, ml_predictions)

def _style_ml_status(val):
    return "background-color: #d5f5e3" if "✅" in str(val) else "background-color: #fef9e7"

def _style_ml_conf(val):
    c = {"Haute": "#d5f5e3", "Moyenne": "#fef9e7", "Faible": "#fadbd8"}
    return f"background-color: {c.get(val, '')}"

st.dataframe(
    ml_summary_df.style
    .applymap(_style_ml_status, subset=["Statut"])
    .applymap(_style_ml_conf, subset=["Confiance"]),
    use_container_width=True,
    hide_index=True,
)

n_trained = sum(1 for m in ml_models.values() if m.get("status") == "trained")
if n_trained > 0:
    st.success(
        f"{n_trained}/{len(COUNTRIES)} pays ont un modèle RF entraîné. "
        "Les prédictions ML sont disponibles sur la Page 1 et Page 3."
    )
    st.info(
        "**Interprétation** : La précision CV (cross-validation) est "
        "l'indicateur de fiabilité réel — elle mesure la capacité du "
        "modèle à prédire des données qu'il n'a pas vues. "
        "Avec seulement 3 fonds × 4 ans = ~12 observations par pays, "
        "une précision CV de 60%+ est déjà significative. "
        "Elle s'améliorera automatiquement en ajoutant des fonds dans "
        "ground_truth_master.json."
    )
else:
    st.warning(
        "Aucun modèle RF entraîné — ground_truth_master.json contient "
        "moins de 6 observations par pays. Enrichissez les données "
        "historiques pour activer le ML."
    )

with st.expander("Importance des features par pays", expanded=False):
    for country in COUNTRIES:
        model = ml_models.get(country, {})
        if model.get("status") != "trained":
            continue
        country_fr = COUNTRY_NAMES_FR.get(country, country)
        st.markdown(f"**{country_fr}**")
        top_f = model.get("top_features", [])
        if top_f:
            import plotly.graph_objects as go
            fig_fi = go.Figure(go.Bar(
                x=[f[1] for f in top_f],
                y=[f[0] for f in top_f],
                orientation="h",
                marker_color="#3498db",
                text=[f"{f[1]:.0%}" for f in top_f],
                textposition="outside",
            ))
            fig_fi.update_layout(
                height=200,
                margin=dict(l=150, r=60, t=10, b=30),
                xaxis=dict(title="Importance", tickformat=".0%"),
                showlegend=False,
            )
            st.plotly_chart(fig_fi, use_container_width=True)
