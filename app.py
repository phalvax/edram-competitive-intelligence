"""
Edram — Intelligence Concurrentielle 2026
Point d'entrée principal du dashboard Streamlit.
"""
import os

import streamlit as st
from dotenv import load_dotenv

from config import DEFAULT_WEIGHTS, FONDS, PREDICTION_YEAR

load_dotenv()

st.set_page_config(
    page_title="Edram — Intelligence Concurrentielle 2026",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)


def init_session_state():
    defaults = {
        "groq_api_key":      os.getenv("GROQ_API_KEY", ""),
        "anthropic_api_key": os.getenv("ANTHROPIC_API_KEY", ""),
        "fred_api_key":      os.getenv("FRED_API_KEY", ""),
        "serp_api_key":      os.getenv("SERP_API_KEY", ""),
        "weights":           DEFAULT_WEIGHTS.copy(),
        "threshold_ow":      0.10,
        "threshold_uw":      -0.10,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


init_session_state()

# ── Page d'accueil ─────────────────────────────────────────────────────────────
st.title("Edram — Intelligence Concurrentielle")
st.subheader(f"Allocation géographique européenne {PREDICTION_YEAR} · Analyse des {len(FONDS)} fonds concurrents")

st.markdown("""
Ce dashboard permet à **Edmond de Rothschild AM** d'anticiper les allocations géographiques
des principaux fonds d'investissement européens sur 6 pays, afin de prendre des décisions
éclairées — en suivant le consensus ou en se différenciant intentionnellement.

---
""")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.markdown("""
    ### 🌍 Consensus
    **Page 1**
    Carte de chaleur des positions prédites pour tous les concurrents.
    Où va le marché en 2026 ?
    """)
    st.page_link("pages/1_consensus.py", label="Ouvrir →", use_container_width=True)

with col2:
    st.markdown("""
    ### 📊 Prédictions
    **Page 2**
    Détail factoriel par fonds. Radar chart, waterfall des contributions, intervalles de confiance.
    """)
    st.page_link("pages/2_predictions.py", label="Ouvrir →", use_container_width=True)

with col3:
    st.markdown("""
    ### 🎯 Recommandation
    **Page 3**
    Recommandation Edram. Mode "Suivre" ou "Contrarian". Analyse narrative Claude.
    """)
    st.page_link("pages/3_recommendation.py", label="Ouvrir →", use_container_width=True)

with col4:
    st.markdown("""
    ### ✅ Validation
    **Page 4**
    Précision historique du modèle sur 2022-2025. Le modèle est-il fiable ?
    """)
    st.page_link("pages/4_validation.py", label="Ouvrir →", use_container_width=True)

with col5:
    st.markdown("""
    ### ⚙️ Paramètres
    **Page 5**
    Poids W1-W5, seuils, clés API, données politiques F4, cache.
    """)
    st.page_link("pages/5_settings.py", label="Ouvrir →", use_container_width=True)

st.divider()

# ── Statut des données ─────────────────────────────────────────────────────────
st.subheader("Statut des données")
c1, c2, c3 = st.columns(3)
with c1:
    key_groq = "✅ Configurée" if st.session_state.get("groq_api_key") else "⚠ Non configurée"
    st.metric("Clé API Groq (analyse IA)", key_groq)
with c2:
    key_fred = "✅ Configurée" if st.session_state.get("fred_api_key") else "⚠ Fallback OCDE"
    st.metric("Clé API FRED", key_fred)
with c3:
    from config import GROUND_TRUTH_FILE
    import json
    gt_count = 0
    if GROUND_TRUTH_FILE.exists():
        with open(GROUND_TRUTH_FILE, encoding="utf-8") as f:
            gt = json.load(f)
        gt_count = sum(len(years) for years in gt.values())
    st.metric("Positions en base GT", f"{gt_count} entrées")

st.caption(
    "Modèle factoriel 5 composantes · z-score rolling · Monte Carlo 1000 simulations · "
    f"Prédictions {PREDICTION_YEAR} basées sur données 2022-2025."
)
