"""
Page 5 : Paramètres — Poids, seuils, clés API, données F4, cache.
"""
import json
import os
import shutil
from pathlib import Path

import streamlit as st
import pandas as pd

from config import (
    CACHE_DIR, COUNTRIES, COUNTRY_NAMES_FR, DEFAULT_WEIGHTS,
    ENV_ANTHROPIC_KEY, ENV_FRED_KEY, ENV_SERP_KEY,
    FACTOR_LABELS, POLITICAL_FILE, PREDICTION_YEAR,
    THRESHOLD_OW, THRESHOLD_UW,
)
from data.fetchers.political_data import load_political_raw, save_political_scores

st.set_page_config(page_title="Paramètres", page_icon="⚙️", layout="wide")
st.title("Paramètres")
st.caption("Poids des facteurs · Seuils OW/UW · Clés API · Données politiques F4 · Cache")

# ── Poids W1-W5 ───────────────────────────────────────────────────────────────
st.subheader("Poids des facteurs (W1-W5)")
st.caption("La somme doit être égale à 1.00. Les poids sont appliqués immédiatement à toutes les pages.")

current_weights = st.session_state.get("weights") or DEFAULT_WEIGHTS.copy()

col_sliders = st.columns(5)
new_weights = {}
factor_keys = ["F1", "F2", "F3", "F4", "F5"]

for i, fi in enumerate(factor_keys):
    with col_sliders[i]:
        new_weights[fi] = st.slider(
            FACTOR_LABELS.get(fi, fi),
            min_value=0.0,
            max_value=1.0,
            value=float(current_weights.get(fi, DEFAULT_WEIGHTS[fi])),
            step=0.05,
            key=f"weight_{fi}",
        )

weight_sum = sum(new_weights.values())
if abs(weight_sum - 1.0) > 0.001:
    st.warning(f"Somme des poids : **{weight_sum:.2f}** ≠ 1.00. Les poids seront normalisés automatiquement.")
    total = weight_sum if weight_sum > 0 else 1.0
    new_weights = {k: round(v / total, 4) for k, v in new_weights.items()}

col_apply, col_reset = st.columns([1, 4])
with col_apply:
    if st.button("Appliquer les poids", type="primary"):
        st.session_state["weights"] = new_weights
        st.success("Poids mis à jour. Rechargez les autres pages pour voir l'effet.")
with col_reset:
    if st.button("Réinitialiser aux poids par défaut"):
        st.session_state["weights"] = DEFAULT_WEIGHTS.copy()
        st.rerun()

# Afficher la somme actuelle
active_weights = st.session_state.get("weights") or DEFAULT_WEIGHTS
weight_preview = " + ".join(f"W{i+1}={active_weights[f]:.0%}" for i, f in enumerate(factor_keys))
st.info(f"Poids actifs : {weight_preview} = {sum(active_weights.values()):.0%}")

st.divider()

# ── Seuils OW/UW ──────────────────────────────────────────────────────────────
st.subheader("Seuils de classification OW / UW")
st.caption("Le score composite est comparé à ces seuils pour classer chaque pays.")

col_ow, col_uw, _ = st.columns([1, 1, 2])
with col_ow:
    thr_ow = st.number_input(
        "Seuil Surpondéré (OW)",
        min_value=0.01, max_value=0.99,
        value=float(st.session_state.get("threshold_ow", THRESHOLD_OW)),
        step=0.01, format="%.2f",
        key="thr_ow_input",
    )
with col_uw:
    thr_uw = st.number_input(
        "Seuil Sous-pondéré (UW)",
        min_value=-0.99, max_value=-0.01,
        value=float(st.session_state.get("threshold_uw", THRESHOLD_UW)),
        step=0.01, format="%.2f",
        key="thr_uw_input",
    )

if st.button("Appliquer les seuils"):
    st.session_state["threshold_ow"] = thr_ow
    st.session_state["threshold_uw"] = thr_uw
    st.success(f"Seuils mis à jour : OW > {thr_ow:+.2f} | UW < {thr_uw:+.2f}")

st.divider()

# ── Clés API ──────────────────────────────────────────────────────────────────
st.subheader("Clés API")

col_a, col_b = st.columns(2)

with col_a:
    groq_key = st.text_input(
        "Clé Groq (analyse IA — gratuit)",
        value=st.session_state.get("groq_api_key", ""),
        type="password",
        placeholder="gsk_...",
        help="Clé gratuite sur console.groq.com — pas de carte bancaire.",
        key="settings_groq_key",
    )
with col_b:
    fred_key = st.text_input(
        "Clé FRED (données macro)",
        value=st.session_state.get("fred_api_key", ""),
        type="password",
        placeholder="abcdef1234567890...",
        key="settings_fred_key",
    )

col_c, col_d = st.columns(2)
with col_c:
    anthropic_key = st.text_input(
        "Clé Anthropic (collecteur PDF — optionnel)",
        value=st.session_state.get("anthropic_api_key", ""),
        type="password",
        placeholder="sk-ant-api03-... (optionnel)",
        help="Uniquement nécessaire pour la collecte automatique des outlooks PDF.",
        key="settings_anthropic_key",
    )
with col_d:
    serp_key = st.text_input(
        "Clé SerpAPI (collecte)",
        value=st.session_state.get("serp_api_key", ""),
        type="password",
        placeholder="...",
        key="settings_serp_key",
    )

col_save, col_env = st.columns([1, 3])
with col_save:
    if st.button("Sauvegarder dans la session"):
        st.session_state["groq_api_key"]       = groq_key
        st.session_state["anthropic_api_key"]  = anthropic_key
        st.session_state["fred_api_key"]       = fred_key
        st.session_state["serp_api_key"]       = serp_key
        st.success("Clés sauvegardées dans la session courante.")

with col_env:
    if st.button("Écrire dans .env (persistant)"):
        env_path = Path(__file__).parent.parent / ".env"
        lines = []
        existing = {}
        if env_path.exists():
            for line in env_path.read_text(encoding="utf-8").splitlines():
                if "=" in line and not line.strip().startswith("#"):
                    k, _, v = line.partition("=")
                    existing[k.strip()] = v.strip()
                else:
                    lines.append(line)

        existing["GROQ_API_KEY"]    = groq_key
        existing[ENV_ANTHROPIC_KEY] = anthropic_key
        existing[ENV_FRED_KEY]      = fred_key
        existing[ENV_SERP_KEY]      = serp_key

        env_content = "\n".join(
            [f"{k}={v}" for k, v in existing.items()] + lines
        )
        env_path.write_text(env_content, encoding="utf-8")
        st.session_state["groq_api_key"]       = groq_key
        st.session_state["anthropic_api_key"]  = anthropic_key
        st.session_state["fred_api_key"]       = fred_key
        st.session_state["serp_api_key"]       = serp_key
        st.success(f"Clés écrites dans {env_path}")

st.divider()

# ── F4 — Données politiques ───────────────────────────────────────────────────
st.subheader("Données politiques — Facteur F4")
st.caption(
    "Scores de stabilité politique par pays et par année. "
    "Plage : -1 (très instable) → +1 (très stable)."
)

pol_raw = load_political_raw()

# Édition en tableau
years_to_show = [2022, 2023, 2024, 2025, 2026]

pol_edit_rows = []
for country in COUNTRIES:
    country_fr = COUNTRY_NAMES_FR.get(country, country)
    row = {"Pays": country_fr}
    for yr in years_to_show:
        val = pol_raw.get(country, {}).get(str(yr), {}).get("score", 0.0)
        row[str(yr)] = float(val)
    pol_edit_rows.append(row)

pol_edit_df = pd.DataFrame(pol_edit_rows)

edited_df = st.data_editor(
    pol_edit_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        str(yr): st.column_config.NumberColumn(
            str(yr), min_value=-1.0, max_value=1.0, step=0.05, format="%.2f"
        )
        for yr in years_to_show
    },
    key="pol_editor",
)

if st.button("Sauvegarder les données F4"):
    # Reconstruire le dict complet
    new_pol = {}
    for _, row in edited_df.iterrows():
        country_fr = row["Pays"]
        # Trouver la clé anglaise
        country_en = next(
            (c for c, fr in COUNTRY_NAMES_FR.items() if fr == country_fr),
            country_fr
        )
        if country_en not in new_pol:
            new_pol[country_en] = {}
        for yr in years_to_show:
            score = float(row[str(yr)])
            if country_en in pol_raw and str(yr) in pol_raw[country_en]:
                entry = dict(pol_raw[country_en][str(yr)])
                entry["score"] = score
            else:
                entry = {"score": score}
            new_pol[country_en][str(yr)] = entry

    # Préserver les années non affichées
    for country_en, years_data in pol_raw.items():
        if country_en not in new_pol:
            new_pol[country_en] = {}
        for yr_str, yr_data in years_data.items():
            if yr_str not in [str(y) for y in years_to_show]:
                new_pol[country_en][yr_str] = yr_data

    save_political_scores(new_pol)
    st.success("Données politiques sauvegardées dans political_events.json.")
    st.cache_data.clear()

st.divider()

# ── Gestion du cache ───────────────────────────────────────────────────────────
st.subheader("Gestion du cache")

cache_files = list(CACHE_DIR.glob("*.parquet")) if CACHE_DIR.exists() else []
cache_size  = sum(f.stat().st_size for f in cache_files) / 1024

col_info, col_btns = st.columns([2, 1])
with col_info:
    st.info(
        f"Cache Streamlit (session) + {len(cache_files)} fichier(s) Parquet "
        f"({cache_size:.0f} Ko) dans `{CACHE_DIR}`"
    )

with col_btns:
    if st.button("Vider le cache Streamlit"):
        st.cache_data.clear()
        st.success("Cache Streamlit vidé. Les données seront rechargées au prochain accès.")

    if st.button("Supprimer les fichiers Parquet", type="secondary"):
        deleted = 0
        for f in cache_files:
            f.unlink(missing_ok=True)
            deleted += 1
        st.success(f"{deleted} fichier(s) Parquet supprimé(s).")

st.divider()

# ── Informations système ───────────────────────────────────────────────────────
with st.expander("Informations système", expanded=False):
    import sys
    import streamlit
    import pandas
    import plotly

    st.markdown(f"""
| Composant | Version |
|-----------|---------|
| Python | `{sys.version.split()[0]}` |
| Streamlit | `{streamlit.__version__}` |
| Pandas | `{pandas.__version__}` |
| Plotly | `{plotly.__version__}` |
| Répertoire | `{Path(__file__).parent.parent}` |
| Année prédite | `{PREDICTION_YEAR}` |
    """)
