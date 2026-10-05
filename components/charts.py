"""Factories Plotly réutilisables."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from config import (
    COUNTRIES, COUNTRY_NAMES_FR, FACTOR_LABELS,
    POSITION_COLORS, POSITION_LABELS,
    THRESHOLD_OW, THRESHOLD_UW,
)


# ── Consensus heatmap ─────────────────────────────────────────────────────────

def make_consensus_heatmap(
    all_fund_positions: dict,
    fund_display_names: dict,
    probabilities_df: pd.DataFrame | None = None,
) -> go.Figure:
    """
    Heatmap : lignes = pays, colonnes = fonds.
    all_fund_positions : {fund_key: {country: "OW"/"N"/"UW"}}
    fund_display_names : {fund_key: nom_affiche}
    """
    fund_keys  = list(all_fund_positions.keys())
    fund_names = [fund_display_names.get(fk, fk) for fk in fund_keys]
    countries_fr = [COUNTRY_NAMES_FR.get(c, c) for c in COUNTRIES]

    pos_to_num = {"OW": 1, "N": 0, "UW": -1}

    z_matrix   = []
    text_matrix = []

    for country in COUNTRIES:
        z_row    = []
        text_row = []
        for fk in fund_keys:
            pos = all_fund_positions[fk].get(country, "N")
            z_row.append(pos_to_num.get(pos, 0))

            # Texte : position seule (la probabilité est identique pour tous les fonds
            # d'un même pays — elle est affichée dans le tableau de synthèse)
            text_row.append(pos)
        z_matrix.append(z_row)
        text_matrix.append(text_row)

    fig = go.Figure(data=go.Heatmap(
        z=z_matrix,
        x=fund_names,
        y=countries_fr,
        colorscale=[
            [0.0, POSITION_COLORS["UW"]],
            [0.5, POSITION_COLORS["N"]],
            [1.0, POSITION_COLORS["OW"]],
        ],
        zmin=-1, zmax=1,
        text=text_matrix,
        texttemplate="%{text}",
        textfont=dict(size=10),
        hovertemplate="<b>%{y}</b> — %{x}<br>Position: %{text}<extra></extra>",
        showscale=False,
    ))
    fig.update_layout(
        height=max(300, 50 * len(COUNTRIES)),
        xaxis=dict(side="top", tickangle=-45, tickfont=dict(size=9)),
        yaxis=dict(tickfont=dict(size=12)),
        margin=dict(l=10, r=10, t=80, b=10),
    )
    return fig


# ── Barre de consensus empilée ────────────────────────────────────────────────

def make_consensus_bar(consensus_df: pd.DataFrame) -> go.Figure:
    """Barre empilée % OW / N / UW par pays, triée par force décroissante."""
    df = consensus_df.copy().sort_values("consensus_strength", ascending=False)
    countries_fr = df["country_fr"].tolist()

    fig = go.Figure()
    for pos, color in [("OW", POSITION_COLORS["OW"]), ("N", POSITION_COLORS["N"]), ("UW", POSITION_COLORS["UW"])]:
        vals = (df[f"pct_{pos}"] * 100).round(1).tolist()
        fig.add_trace(go.Bar(
            name=POSITION_LABELS.get(pos, pos),
            x=countries_fr,
            y=vals,
            marker_color=color,
            text=[f"{v:.0f}%" for v in vals],
            textposition="inside",
            hovertemplate=f"{POSITION_LABELS.get(pos, pos)}: %{{y:.1f}}%<extra></extra>",
        ))
    fig.update_layout(
        barmode="stack",
        height=350,
        yaxis=dict(title="% des fonds", ticksuffix="%", range=[0, 105]),
        legend=dict(orientation="h", y=-0.15),
        margin=dict(l=40, r=20, t=20, b=60),
    )
    return fig


# ── Radar chart des scores composites ────────────────────────────────────────

def make_radar_chart(composite_scores: pd.DataFrame, year: int) -> go.Figure:
    """Radar à 6 axes (pays) visualisant les scores composites."""
    countries_fr = [COUNTRY_NAMES_FR.get(c, c) for c in COUNTRIES]
    values = []
    for c in COUNTRIES:
        v = 0.0
        if year in composite_scores.index and c in composite_scores.columns:
            v = float(composite_scores.at[year, c])
        values.append(round(v, 3))

    # Fermer le polygone
    theta  = countries_fr + [countries_fr[0]]
    r_vals = values + [values[0]]

    fig = go.Figure()
    # Zones OW/UW en fond
    r_ow = [THRESHOLD_OW] * (len(COUNTRIES) + 1)
    r_uw = [THRESHOLD_UW] * (len(COUNTRIES) + 1)

    fig.add_trace(go.Scatterpolar(
        r=r_ow, theta=theta, fill=None,
        line=dict(color=POSITION_COLORS["OW"], dash="dash", width=1),
        name="Seuil OW", showlegend=True,
    ))
    fig.add_trace(go.Scatterpolar(
        r=r_uw, theta=theta, fill=None,
        line=dict(color=POSITION_COLORS["UW"], dash="dash", width=1),
        name="Seuil UW", showlegend=True,
    ))
    fig.add_trace(go.Scatterpolar(
        r=r_vals, theta=theta, fill="toself",
        fillcolor="rgba(52,152,219,0.25)",
        line=dict(color="#2980b9", width=2),
        name="Score composite",
        hovertemplate="<b>%{theta}</b><br>Score: %{r:.3f}<extra></extra>",
    ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(range=[-1.1, 1.1], tickfont=dict(size=9)),
        ),
        height=380,
        margin=dict(l=40, r=40, t=40, b=40),
        legend=dict(orientation="h", y=-0.1),
    )
    return fig


# ── Waterfall contributions factorielles ─────────────────────────────────────

def make_waterfall_contributions(
    factor_scores: dict,
    weights: dict,
    country: str,
    year: int,
    composite_score: float,
) -> go.Figure:
    """Waterfall : contribution pondérée de chaque facteur au score composite."""
    factors = ["F1", "F2", "F3", "F4", "F5"]
    contribs = []
    for fi in factors:
        df = factor_scores.get(fi)
        v = 0.0
        if df is not None and year in df.index and country in df.columns:
            v = float(df.at[year, country])
        contribs.append(round(weights.get(fi, 0.0) * v, 4))

    labels    = [FACTOR_LABELS.get(fi, fi) for fi in factors] + ["Score final"]
    measure   = ["relative"] * len(factors) + ["total"]
    y_vals    = contribs + [composite_score]
    colors    = [POSITION_COLORS["OW"] if c > 0 else POSITION_COLORS["UW"] if c < 0 else POSITION_COLORS["N"]
                 for c in contribs] + ["#2c3e50"]

    fig = go.Figure(go.Waterfall(
        name="Contributions",
        orientation="v",
        measure=measure,
        x=labels,
        y=y_vals,
        connector=dict(line=dict(color="#ccc", width=0.5)),
        increasing=dict(marker_color=POSITION_COLORS["OW"]),
        decreasing=dict(marker_color=POSITION_COLORS["UW"]),
        totals=dict(marker_color="#2c3e50"),
        text=[f"{v:+.3f}" for v in y_vals],
        textposition="outside",
    ))
    fig.add_hline(y=THRESHOLD_OW, line_dash="dash", line_color=POSITION_COLORS["OW"],
                  annotation_text="Seuil OW", annotation_position="right")
    fig.add_hline(y=THRESHOLD_UW, line_dash="dash", line_color=POSITION_COLORS["UW"],
                  annotation_text="Seuil UW", annotation_position="right")
    fig.update_layout(
        height=380,
        yaxis=dict(title="Contribution au score composite", range=[-1.4, 1.4]),
        margin=dict(l=40, r=80, t=20, b=80),
        showlegend=False,
        xaxis=dict(tickangle=-20),
    )
    return fig


# ── Tableau de précision historique ─────────────────────────────────────────

def make_accuracy_heatmap(accuracy_df: pd.DataFrame) -> go.Figure:
    """
    Heatmap de précision : fonds × années.
    accuracy_df : index=fonds_nom, colonnes=années (float 0-1 ou None).
    """
    z, text, x_labels, y_labels = [], [], list(accuracy_df.columns), list(accuracy_df.index)

    for fund in y_labels:
        row_z, row_t = [], []
        for yr in x_labels:
            val = accuracy_df.at[fund, yr]
            if val is None or (isinstance(val, float) and np.isnan(val)):
                row_z.append(None)
                row_t.append("—")
            else:
                row_z.append(float(val))
                row_t.append(f"{val:.0%}")
        z.append(row_z)
        text.append(row_t)

    fig = go.Figure(data=go.Heatmap(
        z=z, x=[str(c) for c in x_labels], y=y_labels,
        colorscale=[[0, POSITION_COLORS["UW"]], [0.5, "#f39c12"], [1, POSITION_COLORS["OW"]]],
        zmin=0, zmax=1,
        text=text, texttemplate="%{text}", textfont=dict(size=11),
        hovertemplate="<b>%{y}</b> — %{x}<br>Précision: %{text}<extra></extra>",
        showscale=True, colorbar=dict(title="Précision", tickformat=".0%"),
    ))
    fig.update_layout(
        height=max(200, 40 * len(y_labels) + 60),
        margin=dict(l=10, r=10, t=20, b=40),
        xaxis=dict(tickfont=dict(size=11)),
        yaxis=dict(tickfont=dict(size=11)),
    )
    return fig


# ── Courbe de précision dans le temps ────────────────────────────────────────

def make_accuracy_timeline(accuracy_df: pd.DataFrame) -> go.Figure:
    """Courbe de précision par fonds dans le temps."""
    fig = go.Figure()
    colors_cycle = px.colors.qualitative.Plotly

    for i, fund in enumerate(accuracy_df.index):
        xs, ys = [], []
        for yr in accuracy_df.columns:
            v = accuracy_df.at[fund, yr]
            if v is not None and not (isinstance(v, float) and np.isnan(v)):
                xs.append(str(yr))
                ys.append(float(v) * 100)
        if xs:
            fig.add_trace(go.Scatter(
                x=xs, y=ys, name=fund,
                mode="lines+markers",
                line=dict(color=colors_cycle[i % len(colors_cycle)], width=2),
                hovertemplate=f"<b>{fund}</b><br>%{{x}}: %{{y:.0f}}%<extra></extra>",
            ))

    fig.add_hline(y=70, line_dash="dash", line_color=POSITION_COLORS["OW"],
                  annotation_text="70% — fiable", annotation_position="right")
    fig.add_hline(y=50, line_dash="dot", line_color="#f39c12",
                  annotation_text="50% — partiel", annotation_position="right")
    fig.update_layout(
        height=350,
        yaxis=dict(title="Précision (%)", range=[0, 105], ticksuffix="%"),
        xaxis=dict(title="Année"),
        margin=dict(l=40, r=80, t=20, b=40),
        legend=dict(orientation="h", y=-0.2),
    )
    return fig
