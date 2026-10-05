"""
Page 6 : Allocations estimées — Montants investis par pays.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from config import (
    FONDS, COUNTRIES, COUNTRY_NAMES_FR, PREDICTION_YEAR, DEFAULT_WEIGHTS,
    MSCI_EUROPE_WEIGHTS,
)
import importlib
import config as _config_mod
importlib.reload(_config_mod)
import data.processors.allocation_model as _alloc_mod
importlib.reload(_alloc_mod)
from data.processors.allocation_model import (
    compute_all_allocations,
    get_allocation_summary,
    get_country_total,
)

st.set_page_config(page_title="Allocations €", page_icon="💰", layout="wide")
st.title("Allocations estimées — Montants investis par pays")
st.caption(
    "Estimation des montants investis par chaque fonds concurrent "
    "dans chaque pays européen. "
    "Les montants sont calculés à partir des AUM connus, "
    "des positions OW/N/UW et des pondérations MSCI Europe."
)

# ── Chargement des données brutes (cacheable) ─────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def _load_base_data():
    from data.fetchers.market_data import (
        fetch_equity_prices, compute_annual_returns,
        fetch_sovereign_spreads, fetch_per_data,
    )
    from data.fetchers.macro_data import fetch_gdp_growth
    from data.fetchers.political_data import load_political_scores
    prices  = fetch_equity_prices()
    returns = compute_annual_returns(prices)
    gdp     = fetch_gdp_growth()
    spreads = fetch_sovereign_spreads()
    pol     = load_political_scores()
    per     = fetch_per_data()
    return returns, gdp, spreads, pol, per


with st.spinner("Calcul des allocations en cours..."):
    annual_returns, gdp_growth, spreads, political, per_data = _load_base_data()

    weights = st.session_state.get("weights") or DEFAULT_WEIGHTS

    from data.processors.scoring import build_full_scores
    from data.processors.ml_model import (
        load_ground_truth, train_all_countries, predict_all_countries_2026,
    )
    from data.processors.country_factors import build_all_features

    scores = build_full_scores(
        annual_returns, gdp_growth, spreads, political, per_data,
        weights=weights,
    )
    gt = load_ground_truth()

    # Prédictions factorielles : position 2026 par pays (identique pour tous les fonds)
    positions_df = scores.get("positions")
    factoriel_preds = {}
    for country in COUNTRIES:
        position_2026 = "N"
        if (
            positions_df is not None
            and PREDICTION_YEAR in positions_df.index
            and country in positions_df.columns
        ):
            position_2026 = positions_df.at[PREDICTION_YEAR, country]
        factoriel_preds[country] = {fk: position_2026 for fk in FONDS}

    # Prédictions ML
    all_features = build_all_features(
        scores=scores,
        raw_data={
            "gdp_growth": gdp_growth,
            "spreads":    spreads,
            "per_data":   per_data,
            "political":  political,
        },
    )
    ml_models      = train_all_countries(all_features, gt)
    ml_predictions = predict_all_countries_2026(ml_models, all_features)

    allocations, normalization_by_country = compute_all_allocations(
        predictions=factoriel_preds,
        ground_truth=gt,
        ml_predictions=ml_predictions,
        year=PREDICTION_YEAR,
    )
    df_summary = get_allocation_summary(allocations)

# ── KPIs ──────────────────────────────────────────────────────────────────────
st.divider()
col1, col2, col3, col4 = st.columns(4)

total_aum    = sum(f.get("aum_md_eur", 0) for f in FONDS.values())
total_eu_est = df_summary["Montant (Md€)"].sum()
n_fonds_gt   = len([
    fk for fk in FONDS
    if any(
        allocations.get(fk, {}).get(c, {}).get("source") == "ground_truth_confirmed"
        for c in COUNTRIES
    )
])

col1.metric("AUM total 31 fonds", f"{total_aum:,.0f} Md€")
col2.metric("Investi Europe (estimé)", f"{total_eu_est:,.1f} Md€")
col3.metric("Fonds avec données réelles", f"{n_fonds_gt} / 31")
col4.metric("Année prédite", str(PREDICTION_YEAR))

# ── Sélecteurs ────────────────────────────────────────────────────────────────
st.divider()
col_f, col_c = st.columns(2)
with col_f:
    selected_fund = st.selectbox(
        "Fonds",
        options=list(FONDS.keys()),
        format_func=lambda k: FONDS[k]["nom"],
        key="alloc_fund",
    )
with col_c:
    selected_country = st.selectbox(
        "Pays (vue détaillée)",
        options=COUNTRIES,
        format_func=lambda c: COUNTRY_NAMES_FR.get(c, c),
        key="alloc_country",
    )

# ── Vue fonds sélectionné ─────────────────────────────────────────────────────
st.subheader(f"Allocations — {FONDS[selected_fund]['nom']}")
fund_data = allocations.get(selected_fund, {})

rows_fund = []
for country in COUNTRIES:
    alloc = fund_data.get(country, {})
    rows_fund.append({
        "Pays":          COUNTRY_NAMES_FR.get(country, country),
        "Position":      alloc.get("position", "N"),
        "Montant (Md€)": alloc.get("montant_central_md", 0),
        "Min (Md€)":     alloc.get("montant_min_md", 0),
        "Max (Md€)":     alloc.get("montant_max_md", 0),
        "% AUM Europe":  alloc.get("allocation_pct", 0),
        "Confiance":     f"{alloc.get('confiance_pct', 0)}%",
        "Source":        alloc.get("source", ""),
    })

df_fund = pd.DataFrame(rows_fund)

# Graphique barres avec intervalles de confiance
fig_fund = go.Figure()
fig_fund.add_trace(go.Bar(
    x=df_fund["Pays"],
    y=df_fund["Montant (Md€)"],
    error_y=dict(
        type="data",
        symmetric=False,
        array=(df_fund["Max (Md€)"] - df_fund["Montant (Md€)"]).tolist(),
        arrayminus=(df_fund["Montant (Md€)"] - df_fund["Min (Md€)"]).tolist(),
    ),
    marker_color=[
        "rgba(46,204,113,0.8)" if p == "OW"
        else "rgba(231,76,60,0.8)" if p == "UW"
        else "rgba(149,165,166,0.8)"
        for p in df_fund["Position"]
    ],
    text=df_fund["Montant (Md€)"].apply(lambda x: f"{x:.2f} Md€"),
    textposition="outside",
))
fig_fund.update_layout(
    title=f"Montants estimés par pays — {FONDS[selected_fund]['nom']}",
    yaxis_title="Montant (Md€)",
    height=400,
    showlegend=False,
)
st.plotly_chart(fig_fund, use_container_width=True)


def color_source(val):
    colors = {
        "ground_truth_confirmed": "background-color: #d5f5e3",
        "ml_predicted":           "background-color: #d6eaf8",
        "model_predicted":        "background-color: #fef9e7",
        "outlook_pdf_extracted":  "background-color: #e8daef",
    }
    return colors.get(val, "")


def color_position(val):
    colors = {
        "OW": "color: #27ae60; font-weight: bold",
        "UW": "color: #e74c3c; font-weight: bold",
        "N":  "color: #7f8c8d",
    }
    return colors.get(val, "")


st.dataframe(
    df_fund.style
    .applymap(color_position, subset=["Position"])
    .applymap(color_source, subset=["Source"]),
    use_container_width=True,
    hide_index=True,
)

st.caption(
    "🟢 Vert = données réelles confirmées | "
    "🔵 Bleu = prédiction ML | "
    "🟡 Jaune = modèle factoriel | "
    "🟣 Violet = PDF extrait"
)

# ── Vue pays sélectionné (tous les fonds) ─────────────────────────────────────
st.divider()
country_fr_label = COUNTRY_NAMES_FR.get(selected_country, selected_country)
st.subheader(f"Tous les fonds — {country_fr_label}")

country_total = get_country_total(allocations, selected_country)

norm = normalization_by_country.get(selected_country, {})
if norm.get("normalized"):
    plafond = norm["plafond_agrege"]
    st.info(
        "Les montants ont été normalisés par rapport à la capacité "
        "d'absorption réelle du marché (market cap × taux institutionnels "
        "étrangers × part de notre univers de fonds). "
        f"Plafond appliqué : {plafond:.0f} Md€"
    )

col1, col2, col3 = st.columns(3)
col1.metric(
    "Total estimé investi",
    f"{country_total['total_central_md']:.1f} Md€",
)
col2.metric(
    "Fourchette",
    f"[{country_total['total_min_md']:.1f} ; {country_total['total_max_md']:.1f}] Md€",
)
col3.metric("Fonds analysés", f"{country_total['n_fonds']}")

country_rows = []
for fund_key, countries in allocations.items():
    alloc = countries.get(selected_country, {})
    if alloc:
        country_rows.append({
            "Fonds":                FONDS[fund_key]["nom"],
            "AUM total (Md€)":      FONDS[fund_key].get("aum_md_eur", 0),
            "Montant estimé (Md€)": alloc.get("montant_central_md", 0),
            "Min (Md€)":            alloc.get("montant_min_md", 0),
            "Max (Md€)":            alloc.get("montant_max_md", 0),
            "Position":             alloc.get("position", "N"),
            "Confiance":            f"{alloc.get('confiance_pct', 0)}%",
            "Source":               alloc.get("source", ""),
        })

df_country = pd.DataFrame(country_rows).sort_values(
    "Montant estimé (Md€)", ascending=False
)

fig_country = px.bar(
    df_country.head(15),
    x="Montant estimé (Md€)",
    y="Fonds",
    orientation="h",
    color="Position",
    color_discrete_map={
        "OW": "rgba(46,204,113,0.8)",
        "N":  "rgba(149,165,166,0.8)",
        "UW": "rgba(231,76,60,0.8)",
    },
    error_x=(
        df_country.head(15)["Max (Md€)"]
        - df_country.head(15)["Montant estimé (Md€)"]
    ).tolist(),
    title=f"Top 15 fonds — Exposition {country_fr_label}",
)
fig_country.update_layout(height=500, yaxis=dict(autorange="reversed"))
st.plotly_chart(fig_country, use_container_width=True)

# ── Vue conviction : déviation vs MSCI ────────────────────────────────────────
st.divider()
st.subheader(f"Signal de conviction — Déviation vs MSCI Europe ({country_fr_label})")
st.caption(
    "Représente l'écart entre l'allocation estimée de chaque fonds et le poids MSCI neutre. "
    "Un boutique OW apparaît en tête même avec de petits AUM — c'est son SIGNAL d'allocation, "
    "pas sa taille absolue. Trié par conviction décroissante."
)

msci_w = MSCI_EUROPE_WEIGHTS.get(selected_country, 0.05)  # poids MSCI neutre du pays

deviation_rows = []
for fund_key, countries in allocations.items():
    alloc = countries.get(selected_country, {})
    if not alloc:
        continue
    # Utilise la déviation intentionnelle (signal pur avant normalisation du plafond)
    deviation_pp = alloc.get("intended_deviation_pp", 0.0)
    deviation_rows.append({
        "Fonds":         FONDS[fund_key]["nom"],
        "Dév. (pp)":     deviation_pp,
        "Position":      alloc.get("position", "N"),
        "Source":        alloc.get("source", ""),
        "Montant (Md€)": alloc.get("montant_central_md", 0),
        "Typologie":     FONDS[fund_key].get("typologie", ""),
    })

df_dev = (
    pd.DataFrame(deviation_rows)
    .assign(AbsDev=lambda d: d["Dév. (pp)"].abs())
    .sort_values("AbsDev", ascending=False)
    .drop(columns="AbsDev")
)

fig_dev = go.Figure()
for pos, color, label in [
    ("OW", "rgba(46,204,113,0.85)",  "Surpondéré"),
    ("N",  "rgba(149,165,166,0.75)", "Neutre"),
    ("UW", "rgba(231,76,60,0.85)",   "Sous-pondéré"),
]:
    sub = df_dev[df_dev["Position"] == pos]
    if sub.empty:
        continue
    fig_dev.add_trace(go.Bar(
        name=label,
        x=sub["Dév. (pp)"],
        y=sub["Fonds"],
        orientation="h",
        marker_color=color,
        text=sub["Dév. (pp)"].apply(lambda v: f"{v:+.1f} pp"),
        textposition="outside",
        customdata=sub[["Montant (Md€)", "Typologie", "Source"]].values,
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Déviation : %{x:+.2f} pp vs MSCI<br>"
            "Montant : %{customdata[0]:.1f} Md€<br>"
            "Typologie : %{customdata[1]}<br>"
            "Source : %{customdata[2]}<extra></extra>"
        ),
    ))

fig_dev.add_vline(x=0, line_dash="dash", line_color="rgba(100,100,100,0.5)", line_width=1)
fig_dev.update_layout(
    barmode="overlay",
    height=max(400, 22 * len(df_dev)),
    xaxis=dict(title="Déviation vs poids MSCI Europe (points de %)", zeroline=True),
    yaxis=dict(autorange="reversed", tickfont=dict(size=10)),
    legend=dict(orientation="h", y=-0.08),
    margin=dict(l=10, r=80, t=30, b=40),
)
st.plotly_chart(fig_dev, use_container_width=True)
st.caption(
    f"Référence MSCI neutre pour {country_fr_label} : {msci_w*100:.1f}% du portefeuille actions Europe. "
    "Déviation positive = surpondération, négative = sous-pondération."
)
