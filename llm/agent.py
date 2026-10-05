"""
Agent LLM — Analyse narrative pour les recommandations Edram.
"""
import pandas as pd

from config import (
    COUNTRIES, COUNTRY_NAMES_FR, FACTOR_LABELS,
    LLM_MAX_TOKENS, LLM_MODEL, POSITION_LABELS,
)


def generate_recommendation_analysis(
    api_key: str,
    consensus_df: pd.DataFrame,
    recommendation_df: pd.DataFrame,
    probabilities_df: pd.DataFrame,
    mode: str = "consensus",
    weights: dict | None = None,
) -> str:
    """
    Génère une analyse narrative markdown pour Edram.

    mode : "consensus" → suivre le marché | "contrarian" → se différencier
    """
    system_prompt = (
        "Tu es un analyste senior en allocation d'actifs chez Edmond de Rothschild AM (Edram), "
        "un family office européen de premier plan. "
        "Tu analyses les données quantitatives de marché pour formuler des recommandations "
        "d'allocation géographique sur les actions européennes. "
        "Ton style est concis, factuel et actionnable. Réponds uniquement en français. "
        "Chaque recommandation est justifiée par des données chiffrées. "
        "Tu identifies les risques et les opportunités de différenciation."
    )

    # ── Construction du contexte données ─────────────────────────────────────
    mode_label = "Suivre le consensus de marché" if mode == "consensus" else "Stratégie contrarian"
    lines = [f"STRATÉGIE EDRAM : {mode_label}\n"]

    # Consensus marché
    lines.append("CONSENSUS MARCHÉ 2026 (positions des 31 fonds concurrents) :")
    lines.append(
        f"{'Pays':<16} | {'Consensus':<10} | {'Force':>6} | "
        f"{'%OW':>5} | {'%N':>5} | {'%UW':>5} | {'Prob.modèle':>11} | {'Confiance':>9}"
    )
    lines.append("-" * 80)
    for country in COUNTRIES:
        if country not in consensus_df.index:
            continue
        c  = consensus_df.loc[country]
        p  = probabilities_df.loc[country] if country in probabilities_df.index else {}
        country_fr = COUNTRY_NAMES_FR.get(country, country)
        prob = float(p.get("prob_predicted", 0.5)) if hasattr(p, "get") else 0.5
        conf = p.get("confidence_level", "?") if hasattr(p, "get") else "?"
        lines.append(
            f"{country_fr:<16} | {c['consensus_label']:<10} | {c['consensus_strength']:>5.0%} | "
            f"{c['pct_OW']:>4.0%} | {c['pct_N']:>4.0%} | {c['pct_UW']:>4.0%} | "
            f"{prob:>10.0%} | {conf:>9}"
        )

    # Recommandations
    lines.append("\nRECOMMANDATIONS EDRAM :")
    pos_col = "follow_consensus" if mode == "consensus" else "contrarian"
    just_col = "follow_justification" if mode == "consensus" else "contrarian_justification"
    for country in COUNTRIES:
        if country not in recommendation_df.index:
            continue
        r = recommendation_df.loc[country]
        country_fr = COUNTRY_NAMES_FR.get(country, country)
        rec_pos = r.get(pos_col, "N")
        conv    = r.get("conviction_level", "?")
        just    = r.get(just_col, "")
        lines.append(
            f"  {country_fr}: {POSITION_LABELS.get(rec_pos, rec_pos)} "
            f"(conviction {conv}) — {just}"
        )

    user_prompt = "\n".join(lines) + """

Sur la base de ces données, produis une analyse structurée en 4 sections :

## (a) Tendances 2026 — ce que font les concurrents
Synthèse en 3-4 phrases des principales tendances observées dans les positions des fonds concurrents. Quels pays font consensus ? Où les avis divergent-ils ?

## (b) Recommandation d'allocation Edram — pays par pays
Pour chaque pays, 2-3 phrases : position recommandée, justification factuelle (citer les chiffres de consensus et de probabilité), niveau de conviction.

## (c) Risques à surveiller
2-3 pays où le consensus est faible, la probabilité modèle est incertaine, ou des facteurs externes pourraient modifier la donne. Être précis et factuel.

## (d) Opportunités de différenciation contrarian
1-2 pays où Edram pourrait se démarquer des concurrents de façon justifiée, avec un rapport risque/opportunité favorable."""

    return _call_llm(api_key, system_prompt, user_prompt)


def _call_llm(api_key: str, system_prompt: str, user_prompt: str) -> str:
    """
    Appelle Groq via l'API compatible OpenAI.
    Modèle : llama-3.3-70b-versatile
    """
    if not api_key:
        raise ValueError(
            "Clé API Groq non configurée. "
            "Obtenez une clé gratuite sur console.groq.com "
            "et configurez-la dans la Page Paramètres."
        )
    try:
        from openai import OpenAI
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1",
        )
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=2048,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt},
            ],
        )
        return response.choices[0].message.content
    except Exception as e:
        if "401" in str(e) or "authentication" in str(e).lower():
            raise ValueError(
                "Clé API Groq invalide. "
                "Vérifiez votre clé sur console.groq.com"
            )
        elif "rate_limit" in str(e).lower() or "429" in str(e):
            raise RuntimeError(
                "Limite de débit Groq atteinte. "
                "Patientez quelques secondes et réessayez."
            )
        else:
            raise RuntimeError(f"Erreur Groq : {e}") from e
