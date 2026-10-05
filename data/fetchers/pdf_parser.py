"""
Extraction de données financières depuis des PDFs d'outlooks.
Utilise pdfplumber pour extraire le texte, puis cherche
les patterns d'allocation géographique et sectorielle.
N'importe PAS streamlit.
"""

import re
import json
from pathlib import Path
from typing import Optional

try:
    import pdfplumber
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

from config import COUNTRIES, COUNTRY_NAMES_FR

# Patterns de recherche dans les PDFs
COUNTRY_PATTERNS = {
    "Germany":     ["allemagne", "germany", "dax", "allemand", "bund"],
    "France":      ["france", "français", "cac", "oat", "paris"],
    "Italy":       ["italie", "italy", "btp", "italien", "milan"],
    "Spain":       ["espagne", "spain", "espagnol", "ibex", "madrid"],
    "Netherlands": ["pays-bas", "netherlands", "dutch", "aex"],
    "Switzerland": ["suisse", "switzerland", "swiss", "smi"],
}

POSITION_PATTERNS = {
    "OW": [
        "surpondéré", "surpondération", "overweight", "positif", "favorable",
        "préférons", "opportunité", "attractif", "sous-évalué", "achat",
        "exposition accrue", "augmentons", "augmenter notre exposition",
    ],
    "UW": [
        "sous-pondéré", "sous-pondération", "underweight", "négatif",
        "défavorable", "prudent", "risque", "réduisons", "réduire",
        "exposition réduite", "éviter", "ventes",
    ],
    "N": [
        "neutre", "neutral", "pondération marché", "benchmark",
        "maintenir", "stable", "pas de changement",
    ],
}

AMOUNT_PATTERNS = [
    r"(\d+[,.]?\d*)\s*(milliard|billion|md|bn|million|mn|m)\s*[€$]?",
    r"(\d+[,.]?\d*)\s*[€$]\s*(milliard|billion|md|bn|million|mn|m)",
    r"(\d+[,.]?\d*)\s*(Md€|M€|B€)",
]


def extract_text_from_pdf(pdf_path: str) -> Optional[str]:
    """Extrait le texte brut d'un PDF."""
    if not PDF_AVAILABLE:
        return None
    try:
        text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text.lower()
    except Exception as e:
        print(f"Erreur extraction PDF {pdf_path}: {e}")
        return None


def detect_positions_from_text(text: str) -> dict:
    """
    Analyse un texte et détecte les positions OW/N/UW par pays.
    Retourne {country: {"position": "OW/N/UW", "confiance": float, "extraits": []}}
    """
    text_lower = text.lower()
    results = {}

    for country, keywords in COUNTRY_PATTERNS.items():
        country_mentions = []

        for kw in keywords:
            positions_in_text = [
                m.start() for m in re.finditer(re.escape(kw), text_lower)
            ]
            country_mentions.extend(positions_in_text)

        if not country_mentions:
            results[country] = {
                "position": "N",
                "confiance": 0.3,
                "extraits": [],
                "source": "non_mentionné",
            }
            continue

        position_scores = {"OW": 0, "N": 0, "UW": 0}
        extraits = []

        for pos in country_mentions[:5]:
            start = max(0, pos - 200)
            end = min(len(text_lower), pos + 200)
            context = text_lower[start:end]
            extraits.append(context[:100] + "...")

            for position, pos_keywords in POSITION_PATTERNS.items():
                for pk in pos_keywords:
                    if pk in context:
                        position_scores[position] += 1

        max_score = max(position_scores.values())
        if max_score == 0:
            detected_position = "N"
            confiance = 0.40
        else:
            detected_position = max(position_scores, key=position_scores.get)
            total = sum(position_scores.values())
            confiance = min(0.85, 0.40 + (max_score / total) * 0.45)

        results[country] = {
            "position":  detected_position,
            "confiance": round(confiance, 2),
            "extraits":  extraits[:2],
            "scores":    position_scores,
            "source":    "pdf_extracted",
        }

    return results


def parse_pdf_outlook(
    pdf_path: str,
    fund_key: str,
    year: int,
) -> Optional[dict]:
    """
    Parse un PDF d'outlook et retourne les positions détectées.
    Format de retour compatible avec ground_truth_master.json.
    """
    text = extract_text_from_pdf(pdf_path)
    if not text:
        return None

    positions = detect_positions_from_text(text)

    import datetime
    result = {}
    for country, data in positions.items():
        country_fr = COUNTRY_NAMES_FR.get(country, country)
        result[country_fr] = data["position"]

    result["_source_pdf"]        = str(pdf_path)
    result["_confiance_globale"] = "moyenne"
    result["_methode"]           = "pdf_parsing"
    result["_date_collecte"]     = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    return {fund_key: {str(year): result}}


def parse_bnp_outlook_2026_from_text(text_content: str) -> dict:
    """
    Parser spécialisé pour le document BNP/AXA Perspectives 2026.

    Ce document confirme pour BNP/AXA en 2026 :
    - Allemagne : OW fort (changement budgétaire majeur, 500Md€)
    - France    : UW (risque budgétaire, spread OAT)
    - Italie    : N
    - Espagne   : N
    - Pays-Bas  : N
    - Suisse    : N

    Secteurs prioritaires : Défense, Industrials, Utilities, Bancaire
    """
    return {
        "bnp": {
            "2026": {
                "France":    "UW",
                "Allemagne": "OW",
                "Italie":    "N",
                "Espagne":   "N",
                "Pays-Bas":  "N",
                "Suisse":    "N",
                "_source_url": "FINAL_IO_FR_2026_03122025.pdf",
                "_confiance":  "haute",
                "_secteurs_prioritaires": [
                    "Defense", "Industrials", "Utilities",
                    "Financials", "Infrastructure",
                ],
                "_date_collecte": "2026-03-22 00:00",
                "_methode": "pdf_manuel",
            }
        }
    }
