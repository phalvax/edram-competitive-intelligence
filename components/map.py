"""Carte choroplèthe Europe."""
import pandas as pd
import plotly.express as px

from config import COUNTRIES, COUNTRY_ISO3, COUNTRY_NAMES_FR, POSITION_COLORS


def make_choropleth_europe(
    positions: pd.DataFrame,
    composite_scores: pd.DataFrame,
    year: int,
    title: str = "",
) -> "go.Figure":
    rows = []
    for country in COUNTRIES:
        pos = "N"
        score = 0.0
        if year in positions.index and country in positions.columns:
            pos = positions.at[year, country]
        if year in composite_scores.index and country in composite_scores.columns:
            score = float(composite_scores.at[year, country])
        rows.append({
            "iso3":    COUNTRY_ISO3.get(country, ""),
            "country": COUNTRY_NAMES_FR.get(country, country),
            "pos":     pos,
            "score":   score,
            "color_val": {"OW": 1, "N": 0, "UW": -1}.get(pos, 0),
        })

    df = pd.DataFrame(rows)
    fig = px.choropleth(
        df,
        locations="iso3",
        color="color_val",
        hover_name="country",
        hover_data={"score": ":.3f", "pos": True, "color_val": False, "iso3": False},
        color_continuous_scale=[
            [0.0, POSITION_COLORS["UW"]],
            [0.5, POSITION_COLORS["N"]],
            [1.0, POSITION_COLORS["OW"]],
        ],
        range_color=[-1, 1],
        scope="europe",
        labels={"score": "Score", "pos": "Position"},
        title=title or f"Europe — {year}",
    )
    fig.update_coloraxes(showscale=False)
    fig.update_layout(
        margin=dict(l=0, r=0, t=30, b=0),
        height=380,
        geo=dict(
            showframe=False,
            showcoastlines=True,
            projection_type="natural earth",
            center={"lat": 48, "lon": 10},
            projection_scale=3,
        ),
    )
    return fig


def make_double_choropleth(
    positions_left: pd.DataFrame,
    composite_left: pd.DataFrame,
    positions_right: pd.DataFrame,
    composite_right: pd.DataFrame,
    year: int,
    title_left: str = "Consensus",
    title_right: str = "Recommandation",
) -> tuple:
    """Retourne (fig_left, fig_right) pour un affichage côte à côte."""
    return (
        make_choropleth_europe(positions_left, composite_left, year, title_left),
        make_choropleth_europe(positions_right, composite_right, year, title_right),
    )
