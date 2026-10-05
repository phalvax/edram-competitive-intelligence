"""
Configuration centrale — toutes les constantes du projet.
NE PAS coder en dur des poids ou seuils ailleurs que dans ce fichier.
"""

from pathlib import Path

# ── Chemins ────────────────────────────────────────────────────────────────────
ROOT_DIR               = Path(__file__).parent
DATA_DIR               = ROOT_DIR / "data"
CACHE_DIR              = DATA_DIR / "cache"
POLITICAL_FILE         = ROOT_DIR / "political_events.json"
GROUND_TRUTH_FILE      = ROOT_DIR / "ground_truth_master.json"

# ── Année cible (affichage principal) ─────────────────────────────────────────
DISPLAY_YEAR = 2026   # Seule cette année est prédite et affichée
START_YEAR   = 2022   # Données historiques pour normalisation z-score (4 ans)
END_YEAR     = 2026

# ── Pays et tickers ────────────────────────────────────────────────────────────
COUNTRIES = ["France", "Germany", "Italy", "Spain", "Netherlands", "Switzerland"]

COUNTRY_TICKERS: dict = {
    "France":      "^FCHI",
    "Germany":     "^GDAXI",
    "Italy":       "FTSEMIB.MI",
    "Spain":       "^IBEX",
    "Netherlands": "^AEX",
    "Switzerland": "^SSMI",
}

MSCI_EUROPE_TICKER     = "IEUR"
MSCI_EUROPE_TICKER_ALT = "EXV1.DE"

SOVEREIGN_YIELD_FRED: dict = {
    "France":      "IRLTLT01FRM156N",
    "Germany":     "IRLTLT01DEM156N",
    "Italy":       "IRLTLT01ITM156N",
    "Spain":       "IRLTLT01ESM156N",
    "Netherlands": "IRLTLT01NLM156N",
    "Switzerland": "IRLTLT01CHM156N",
}
BUND_FRED_ID = "IRLTLT01DEM156N"

OECD_GDP_CODES: dict = {
    "France":      "FRA",
    "Germany":     "DEU",
    "Italy":       "ITA",
    "Spain":       "ESP",
    "Netherlands": "NLD",
    "Switzerland": "CHE",
    "Eurozone":    "EA20",
}

COUNTRY_ISO3: dict = {
    "France":      "FRA",
    "Germany":     "DEU",
    "Italy":       "ITA",
    "Spain":       "ESP",
    "Netherlands": "NLD",
    "Switzerland": "CHE",
}

COUNTRY_NAMES_FR: dict = {
    "France":      "France",
    "Germany":     "Allemagne",
    "Italy":       "Italie",
    "Spain":       "Espagne",
    "Netherlands": "Pays-Bas",
    "Switzerland": "Suisse",
}

# ── Fonds (31 fonds européens) ─────────────────────────────────────────────────
# Champs : nom, url_base, lien_rapport, marchés, aum_md_eur, frais_bps,
#          croissance_collecte_pct, typologie, type_source, mots_cles_recherche
FONDS: dict = {
    "amundi": {
        "nom": "Amundi",
        "url_base": "https://research-center.amundi.com",
        "lien_rapport": "https://research-center.amundi.com/article/investment-outlook",
        "marches": ["Actions Europe", "Obligations", "Multi-asset"],
        "aum_md_eur": 2380,
        "frais_bps": 16,
        "croissance_collecte_pct": 3.2,
        "typologie": "Généraliste Volume",
        "type_source": ["pdf", "html"],
        "mots_cles_recherche": ["Amundi CIO views allocation Europe géographique overweight underweight"],
    },
    "bnp": {
        "nom": "BNP Paribas AM",
        "url_base": "https://www.bnpparibas-am.com/fr/",
        "lien_rapport": "https://www.bnpparibas-am.com/fr/nos-publications/multi-asset-views/",
        "marches": ["Actions Europe", "Obligations", "Multi-asset"],
        "aum_md_eur": 1600,
        "frais_bps": 21,
        "croissance_collecte_pct": 1.8,
        "typologie": "Banque Privée",
        "type_source": ["pdf", "html"],
        "mots_cles_recherche": ["BNP Paribas AM multi-asset views Europe allocation géographique"],
    },
    "axa_im": {
        "nom": "AXA Investment Managers",
        "url_base": "https://www.axa-im.fr/insights",
        "lien_rapport": "https://www.axa-im.fr/insights/investment-strategy/our-views",
        "marches": ["Actions Europe", "Obligations", "Immobilier"],
        "aum_md_eur": 880,
        "frais_bps": 19,
        "croissance_collecte_pct": 2.1,
        "typologie": "Assureur",
        "type_source": ["pdf", "html"],
        "mots_cles_recherche": ["AXA IM allocation géographique Europe pays actions 2026 outlook"],
    },
    "natixis": {
        "nom": "Natixis Investment Managers",
        "url_base": "https://www.im.natixis.com/fr-fr/insights",
        "lien_rapport": "https://www.im.natixis.com/fr-fr/insights/portfolio-analysis-and-consulting/2026-outlook",
        "marches": ["Actions Europe", "Obligations", "Alternatif"],
        "aum_md_eur": 1323,
        "frais_bps": 24,
        "croissance_collecte_pct": 0.9,
        "typologie": "Banque Privée",
        "type_source": ["pdf", "html"],
        "mots_cles_recherche": ["Natixis Investment Managers allocation géographique Europe 2026 outlook"],
    },
    "dnca": {
        "nom": "DNCA Finance",
        "url_base": "https://www.dnca-investments.com/fr/publications",
        "lien_rapport": "https://www.dnca-investments.com/fr/publications/perspectives",
        "marches": ["Actions Europe", "Obligations convertibles"],
        "aum_md_eur": 63.3,
        "frais_bps": 60,
        "croissance_collecte_pct": -1.2,
        "typologie": "Boutique",
        "type_source": ["pdf", "html"],
        "mots_cles_recherche": ["DNCA Finance allocation géographique Europe 2026 pays overweight"],
    },
    "pictet": {
        "nom": "Pictet Asset Management",
        "url_base": "https://am.pictet/fr/france/global-perspectives",
        "lien_rapport": "https://am.pictet/fr/france/global-perspectives/investment-outlook",
        "marches": ["Actions Europe", "Marchés émergents", "Thématique"],
        "aum_md_eur": 838.5,
        "frais_bps": 55,
        "croissance_collecte_pct": 4.1,
        "typologie": "Banque Privée",
        "type_source": ["pdf", "html"],
        "mots_cles_recherche": ["Pictet AM allocation géographique Europe overweight underweight 2026"],
    },
    "ubs": {
        "nom": "UBS Asset Management",
        "url_base": "https://www.ubs.com/global/en/asset-management/insights.html",
        "lien_rapport": "https://www.ubs.com/global/en/asset-management/insights/asset-class-views.html",
        "marches": ["Actions Europe", "Obligations", "Multi-asset"],
        "aum_md_eur": 1600,
        "frais_bps": 17,
        "croissance_collecte_pct": 2.5,
        "typologie": "Banque Privée",
        "type_source": ["pdf", "html"],
        "mots_cles_recherche": ["UBS AM asset class views Europe allocation géographique 2026"],
    },
    "dws": {
        "nom": "DWS Group",
        "url_base": "https://www.dws.com/fr-fr/insights/",
        "lien_rapport": "https://www.dws.com/fr-fr/insights/dws-research/capital-market-outlook/",
        "marches": ["Actions Europe", "Obligations", "Immobilier"],
        "aum_md_eur": 1085,
        "frais_bps": 25,
        "croissance_collecte_pct": 1.4,
        "typologie": "Banque Privée",
        "type_source": ["pdf", "html"],
        "mots_cles_recherche": ["DWS allocation géographique Europe 2026 pays overweight underweight"],
    },
    "allianz_gi": {
        "nom": "Allianz Global Investors",
        "url_base": "https://fr.allianzgi.com/fr-fr/insights",
        "lien_rapport": "https://fr.allianzgi.com/fr-fr/insights/outlook-and-commentary/investment-outlook",
        "marches": ["Actions Europe", "Obligations", "Alternatif"],
        "aum_md_eur": 562,
        "frais_bps": 38,
        "croissance_collecte_pct": -0.5,
        "typologie": "Assureur",
        "type_source": ["pdf", "html"],
        "mots_cles_recherche": ["Allianz GI allocation géographique Europe 2026 overweight pays actions"],
    },
    "candriam": {
        "nom": "Candriam",
        "url_base": "https://www.candriam.com/fr/professional/market-insights/",
        "lien_rapport": "https://www.candriam.com/fr/professional/market-insights/investment-outlook/",
        "marches": ["Actions Europe", "Obligations", "ESG"],
        "aum_md_eur": 156,
        "frais_bps": 33,
        "croissance_collecte_pct": 5.2,
        "typologie": "Banque Privée",
        "type_source": ["pdf", "html"],
        "mots_cles_recherche": ["Candriam allocation géographique Europe 2026 overweight underweight pays"],
    },
    "lombard_odier": {
        "nom": "Lombard Odier Investment Managers",
        "url_base": "https://am.lombardodier.com/fr/home/news-and-insights.html",
        "lien_rapport": "https://am.lombardodier.com/fr/home/news-and-insights/investment-outlook.html",
        "marches": ["Actions Europe", "Obligations", "Multi-asset"],
        "aum_md_eur": 232,
        "frais_bps": 48,
        "croissance_collecte_pct": 3.7,
        "typologie": "Banque Privée",
        "type_source": ["pdf", "html"],
        "mots_cles_recherche": ["Lombard Odier allocation actions Europe overweight pays 2026"],
    },
    "generali": {
        "nom": "Generali Investments",
        "url_base": "https://www.generali-investments.com/fr/fr/institutional/article/outlook/",
        "lien_rapport": "https://www.generali-investments.com/fr/fr/institutional/article/outlook/annual-outlook",
        "marches": ["Actions Europe", "Obligations", "Multi-asset"],
        "aum_md_eur": 645.2,
        "frais_bps": 21,
        "croissance_collecte_pct": 2.8,
        "typologie": "Assureur",
        "type_source": ["pdf", "html"],
        "mots_cles_recherche": ["Generali Investments allocation géographique Europe 2026 overweight pays"],
    },
    "eurizon": {
        "nom": "Eurizon Capital",
        "url_base": "https://www.eurizoncapital.com/en/insights/",
        "lien_rapport": "https://www.eurizoncapital.com/en/insights/market-outlook/",
        "marches": ["Actions Europe", "Obligations", "Multi-asset"],
        "aum_md_eur": 413,
        "frais_bps": 16,
        "croissance_collecte_pct": 1.6,
        "typologie": "Banque Privée",
        "type_source": ["pdf", "html"],
        "mots_cles_recherche": ["Eurizon Capital allocation géographique Europe 2026 overweight pays"],
    },
    "carmignac": {
        "nom": "Carmignac",
        "url_base": "https://www.carmignac.com/fr_FR/article",
        "lien_rapport": "https://www.carmignac.com/fr_FR/article/carmignac-s-notes",
        "marches": ["Actions Europe", "Actions mondiales", "Obligations"],
        "aum_md_eur": 35,
        "frais_bps": 67,
        "croissance_collecte_pct": -3.1,
        "typologie": "Boutique",
        "type_source": ["pdf", "html"],
        "mots_cles_recherche": ["Carmignac allocation géographique Europe 2026 pays actions"],
    },
    "lazard": {
        "nom": "Lazard Asset Management",
        "url_base": "https://www.lazardassetmanagement.com/fr/fr/research-insights",
        "lien_rapport": "https://www.lazardassetmanagement.com/fr/fr/research-insights/perspectives",
        "marches": ["Actions Europe", "Actions mondiales", "Multi-asset"],
        "aum_md_eur": 230,
        "frais_bps": 45,
        "croissance_collecte_pct": -0.8,
        "typologie": "Banque Privée",
        "type_source": ["pdf", "html"],
        "mots_cles_recherche": ["Lazard AM allocation géographique Europe 2026 overweight underweight pays"],
    },
    "robeco": {
        "nom": "Robeco",
        "url_base": "https://www.robeco.com/fr-fr/insights/",
        "lien_rapport": "https://www.robeco.com/fr-fr/insights/outlook/",
        "marches": ["Actions Europe", "Obligations", "Quant"],
        "aum_md_eur": 335,
        "frais_bps": 35,
        "croissance_collecte_pct": 2.3,
        "typologie": "Banque Privée",
        "type_source": ["pdf", "html"],
        "mots_cles_recherche": ["Robeco allocation géographique Europe 2026 overweight pays"],
    },
    "blackrock": {
        "nom": "BlackRock (EUR)",
        "url_base": "https://www.blackrock.com/fr/professionnels/insights/investment-directions",
        "lien_rapport": "https://www.blackrock.com/fr/professionnels/insights/investment-directions",
        "marches": ["Actions Europe", "ETF/iShares", "Multi-asset"],
        "aum_md_eur": 14000,
        "frais_bps": 14,
        "croissance_collecte_pct": 8.4,
        "typologie": "Généraliste Volume",
        "type_source": ["pdf", "html"],
        "mots_cles_recherche": ["BlackRock investment outlook allocation Europe pays géographique"],
    },
    "jpmorgan": {
        "nom": "J.P. Morgan Asset Management",
        "url_base": "https://am.jpmorgan.com/fr/fr/asset-management/adv/insights/",
        "lien_rapport": "https://am.jpmorgan.com/fr/fr/asset-management/adv/insights/market-insights/guide-to-the-markets/",
        "marches": ["Actions Europe", "Actions mondiales", "Multi-asset"],
        "aum_md_eur": 4100,
        "frais_bps": 29,
        "croissance_collecte_pct": 6.1,
        "typologie": "Banque Privée",
        "type_source": ["pdf", "html"],
        "mots_cles_recherche": ["JPMorgan AM allocation géographique Europe 2026 overweight pays"],
    },
    "fidelity": {
        "nom": "Fidelity International",
        "url_base": "https://www.fidelityinternational.com/editorial/blog/",
        "lien_rapport": "https://www.fidelityinternational.com/editorial/article/investment-outlook/",
        "marches": ["Actions Europe", "Obligations", "Multi-asset"],
        "aum_md_eur": 714,
        "frais_bps": 53,
        "croissance_collecte_pct": 1.9,
        "typologie": "Généraliste Volume",
        "type_source": ["pdf", "html"],
        "mots_cles_recherche": ["Fidelity International allocation géographique Europe overweight 2026"],
    },
    "schroders": {
        "nom": "Schroders",
        "url_base": "https://www.schroders.com/fr-fr/fr/investisseur-particulier/insights/",
        "lien_rapport": "https://www.schroders.com/fr-fr/fr/investisseur-particulier/insights/global-outlook/",
        "marches": ["Actions Europe", "Obligations", "Immobilier"],
        "aum_md_eur": 990,
        "frais_bps": 36,
        "croissance_collecte_pct": 0.7,
        "typologie": "Banque Privée",
        "type_source": ["pdf", "html"],
        "mots_cles_recherche": ["Schroders allocation géographique Europe actions pays 2026"],
    },
    "caixabank": {
        "nom": "CaixaBank Asset Management",
        "url_base": "https://www.caixabank.com/aplweb/GIPB/html/en/",
        "lien_rapport": "https://www.caixabank.com/aplweb/GIPB/html/en/investment-strategy.html",
        "marches": ["Actions Europe", "Obligations", "Multi-asset"],
        "aum_md_eur": 105,
        "frais_bps": 23,
        "croissance_collecte_pct": 4.8,
        "typologie": "Généraliste Volume",
        "type_source": ["pdf", "html"],
        "mots_cles_recherche": ["CaixaBank AM allocation géographique Europe 2026 overweight pays"],
    },
    "santander": {
        "nom": "Santander Asset Management",
        "url_base": "https://www.santanderassetmanagement.com/",
        "lien_rapport": "https://www.santanderassetmanagement.com/insights/investment-outlook",
        "marches": ["Actions Europe", "Obligations", "Multi-asset"],
        "aum_md_eur": 265,
        "frais_bps": 25,
        "croissance_collecte_pct": 3.5,
        "typologie": "Généraliste Volume",
        "type_source": ["pdf", "html"],
        "mots_cles_recherche": ["Santander AM allocation géographique Europe 2026 pays overweight"],
    },
    "bbva": {
        "nom": "BBVA Asset Management",
        "url_base": "https://www.bbva.com/es/salud-financiera/inversion/",
        "lien_rapport": "https://www.bbva.com/es/salud-financiera/inversion/perspectivas-de-mercado/",
        "marches": ["Actions Europe", "Obligations"],
        "aum_md_eur": 60,
        "frais_bps": 23,
        "croissance_collecte_pct": 2.1,
        "typologie": "Généraliste Volume",
        "type_source": ["pdf", "html"],
        "mots_cles_recherche": ["BBVA AM allocation géographique Europe 2026 pays overweight"],
    },
    "unicaja": {
        "nom": "Unicaja Asset Management",
        "url_base": "https://www.unicaja.es/es/banca-inversiones/fondos-inversion/",
        "lien_rapport": "https://www.unicaja.es/es/banca-inversiones/fondos-inversion/perspectivas/",
        "marches": ["Actions Europe", "Obligations"],
        "aum_md_eur": 20,
        "frais_bps": 23,
        "croissance_collecte_pct": 1.3,
        "typologie": "Généraliste Volume",
        "type_source": ["pdf", "html"],
        "mots_cles_recherche": ["Unicaja AM allocation géographique Europe 2026 pays"],
    },
    "mapfre": {
        "nom": "Mapfre Asset Management",
        "url_base": "https://www.mapfre.es/inversiones/",
        "lien_rapport": "https://www.mapfre.com/en/communications/reports/economic-financial-report/",
        "marches": ["Actions Europe", "Obligations"],
        "aum_md_eur": 11,
        "frais_bps": 34,
        "croissance_collecte_pct": 0.4,
        "typologie": "Assureur",
        "type_source": ["pdf", "html"],
        "mots_cles_recherche": ["Mapfre AM allocation géographique Europe 2026 pays overweight"],
    },
    "anima": {
        "nom": "ANIMA SGR",
        "url_base": "https://www.animasgr.it/EN/Pages/default.aspx",
        "lien_rapport": "https://www.animasgr.it/EN/Insights/Pages/default.aspx",
        "marches": ["Actions Europe", "Obligations Italia", "Multi-asset"],
        "aum_md_eur": 50,
        "frais_bps": 25,
        "croissance_collecte_pct": 2.9,
        "typologie": "Généraliste Volume",
        "type_source": ["pdf", "html"],
        "mots_cles_recherche": ["ANIMA SGR allocation géographique Europe 2026 pays overweight"],
    },
    "gsam": {
        "nom": "Goldman Sachs Asset Management",
        "url_base": "https://www.gsam.com/content/gsam/fr/fr/advisors/market-insights.html",
        "lien_rapport": "https://www.gsam.com/content/gsam/fr/fr/advisors/market-insights/investment-outlook.html",
        "marches": ["Actions Europe", "Actions mondiales", "Multi-asset"],
        "aum_md_eur": 2800,
        "frais_bps": 30,
        "croissance_collecte_pct": 5.6,
        "typologie": "Banque Privée",
        "type_source": ["pdf", "html"],
        "mots_cles_recherche": ["Goldman Sachs AM allocation géographique Europe 2026 overweight pays"],
    },
    "columbia": {
        "nom": "Columbia Threadneedle Investments",
        "url_base": "https://www.columbiathreadneedle.fr/fr/institutional/insights/",
        "lien_rapport": "https://www.columbiathreadneedle.fr/fr/institutional/insights/investment-outlook/",
        "marches": ["Actions Europe", "Obligations", "Multi-asset"],
        "aum_md_eur": 650,
        "frais_bps": 32,
        "croissance_collecte_pct": 1.1,
        "typologie": "Banque Privée",
        "type_source": ["pdf", "html"],
        "mots_cles_recherche": ["Columbia Threadneedle allocation géographique Europe 2026 overweight pays"],
    },
    "alliancebernstein": {
        "nom": "AllianceBernstein",
        "url_base": "https://www.alliancebernstein.com/fr/institutional/insights.htm",
        "lien_rapport": "https://www.alliancebernstein.com/fr/institutional/insights/investment-outlook.htm",
        "marches": ["Actions Europe", "Obligations", "Quant"],
        "aum_md_eur": 725,
        "frais_bps": 35,
        "croissance_collecte_pct": 2.7,
        "typologie": "Banque Privée",
        "type_source": ["pdf", "html"],
        "mots_cles_recherche": ["AllianceBernstein allocation géographique Europe 2026 overweight pays"],
    },
    "ssga": {
        "nom": "State Street Global Advisors",
        "url_base": "https://www.ssga.com/fr/fr/institutional/ic/insights",
        "lien_rapport": "https://www.ssga.com/fr/fr/institutional/ic/insights/investment-outlooks",
        "marches": ["ETF/SPDR", "Actions Europe", "Multi-asset"],
        "aum_md_eur": 3700,
        "frais_bps": 12,
        "croissance_collecte_pct": 7.2,
        "typologie": "Généraliste Volume",
        "type_source": ["pdf", "html"],
        "mots_cles_recherche": ["State Street SSGA allocation géographique Europe 2026 overweight pays"],
    },
    "janus": {
        "nom": "Janus Henderson Investors",
        "url_base": "https://www.janushenderson.com/fr-fr/advisor/insights/",
        "lien_rapport": "https://www.janushenderson.com/fr-fr/advisor/insights/investment-outlook/",
        "marches": ["Actions Europe", "Obligations", "Alternatif"],
        "aum_md_eur": 330,
        "frais_bps": 40,
        "croissance_collecte_pct": 0.3,
        "typologie": "Banque Privée",
        "type_source": ["pdf", "html"],
        "mots_cles_recherche": ["Janus Henderson allocation géographique Europe 2026 overweight pays"],
    },
}

# Liste des noms de fonds pour les dropdowns
FUNDS = [FONDS[k]["nom"] for k in FONDS]
FUND_KEYS = list(FONDS.keys())


def get_fund_key(nom: str) -> str | None:
    """Retourne la clé courte d'un fonds à partir de son nom complet."""
    for k, v in FONDS.items():
        if v["nom"] == nom:
            return k
    return None


def get_fund_nom(key: str) -> str:
    """Retourne le nom complet d'un fonds à partir de sa clé."""
    return FONDS.get(key, {}).get("nom", key)


# ── Poids par défaut ───────────────────────────────────────────────────────────
DEFAULT_WEIGHTS: dict = {
    "F1": 0.30,
    "F2": 0.25,
    "F3": 0.20,
    "F4": 0.15,
    "F5": 0.10,
}

# ── Seuils de classification ───────────────────────────────────────────────────
THRESHOLD_OW =  0.10
THRESHOLD_UW = -0.10

POSITION_LABELS: dict = {
    "OW": "Surpondéré",
    "N":  "Neutre",
    "UW": "Sous-pondéré",
}

POSITION_COLORS: dict = {
    "OW": "#2ecc71",
    "N":  "#95a5a6",
    "UW": "#e74c3c",
}

# ── Normalisation z-score ──────────────────────────────────────────────────────
ZSCORE_WINDOW = 4   # Fenêtre glissante en années pour le z-score (2022-2025)

# Fallback : normalisation linéaire si pas assez de données pour z-score
F1_NORM_FACTOR  = 0.15
F2_NORM_FACTOR  = 2.0
F3_LEVEL_WEIGHT = 0.60
F3_DELTA_WEIGHT = 0.40
F3_LEVEL_NORM   = 200.0
F3_DELTA_NORM   = 50.0
F5_NORM_FACTOR  = 0.30

# ── Seuils de confiance ────────────────────────────────────────────────────────
CONFIDENCE_MARGIN_HAUTE   = 0.15
CONFIDENCE_MARGIN_MOYENNE = 0.05
CONFIDENCE_ALIGN_HAUTE    = 0.80
CONFIDENCE_ALIGN_MOYENNE  = 0.60
CONFIDENCE_HIGH   = 0.70   # probabilité > 70% → confiance haute
CONFIDENCE_MEDIUM = 0.50   # probabilité > 50% → confiance moyenne

# ── Année de prédiction + historique ──────────────────────────────────────────
PREDICTION_YEAR = 2026
HISTORY_YEARS   = [2022, 2023, 2024, 2025]

# ── Fallback F2 — PIB annuel % (source OCDE) ──────────────────────────────────
FALLBACK_GDP: dict = {
    "France":      {2022: 2.5,  2023: 0.9,  2024: 1.1,  2025: 0.7,  2026: 0.9},
    "Germany":     {2022: 1.8,  2023: -0.3, 2024: -0.2, 2025: 0.2,  2026: 1.0},
    "Italy":       {2022: 3.7,  2023: 0.9,  2024: 0.7,  2025: 0.6,  2026: 0.8},
    "Spain":       {2022: 5.8,  2023: 2.5,  2024: 3.2,  2025: 2.6,  2026: 2.2},
    "Netherlands": {2022: 4.3,  2023: 0.1,  2024: 0.6,  2025: 1.2,  2026: 1.5},
    "Switzerland": {2022: 2.7,  2023: 1.3,  2024: 1.5,  2025: 1.2,  2026: 1.3},
    "Eurozone":    {2022: 3.4,  2023: 0.4,  2024: 0.7,  2025: 1.0,  2026: 1.2},
}

# ── Fallback F3 — Spreads souverains vs Bund (bps, moyenne annuelle) ──────────
FALLBACK_SPREADS: dict = {
    "France":      {2022: 52,   2023: 58,   2024: 77,   2025: 80,   2026: 75},
    "Italy":       {2022: 209,  2023: 172,  2024: 135,  2025: 115,  2026: 110},
    "Spain":       {2022: 108,  2023: 97,   2024: 82,   2025: 70,   2026: 65},
    "Netherlands": {2022: 18,   2023: 22,   2024: 28,   2025: 25,   2026: 22},
    "Switzerland": {2022: -35,  2023: -42,  2024: -38,  2025: -35,  2026: -32},
    "Germany":     {2022: 0,    2023: 0,    2024: 0,    2025: 0,    2026: 0},
}

# ── Fallback F5 — PER (sources Bloomberg/Factset) ─────────────────────────────
FALLBACK_PER: dict = {
    "France":      {2022: 13.2, 2023: 14.1, 2024: 14.8, 2025: 12.9, 2026: 13.5},
    "Germany":     {2022: 11.8, 2023: 12.3, 2024: 13.1, 2025: 11.2, 2026: 13.8},
    "Italy":       {2022: 9.1,  2023: 9.8,  2024: 9.5,  2025: 9.0,  2026: 9.4},
    "Spain":       {2022: 11.3, 2023: 12.1, 2024: 12.8, 2025: 13.2, 2026: 13.5},
    "Netherlands": {2022: 16.2, 2023: 17.1, 2024: 17.8, 2025: 16.5, 2026: 17.0},
    "Switzerland": {2022: 17.8, 2023: 18.2, 2024: 19.1, 2025: 17.9, 2026: 18.5},
    "MSCI_Europe": {2022: 13.1, 2023: 13.8, 2024: 14.2, 2025: 13.5, 2026: 14.0},
}

# ── Cache TTL ─────────────────────────────────────────────────────────────────
MARKET_CACHE_TTL    = 3600
MACRO_CACHE_TTL     = 86400
POLITICAL_CACHE_TTL = 0

# ── LLM ───────────────────────────────────────────────────────────────────────
LLM_MODEL        = "llama-3.3-70b-versatile"
LLM_MAX_TOKENS   = 2048
LLM_PROVIDER     = "groq"
GROQ_BASE_URL    = "https://api.groq.com/openai/v1"
ENV_GROQ_KEY     = "GROQ_API_KEY"

# ── Variables d'environnement ─────────────────────────────────────────────────
ENV_ANTHROPIC_KEY = "ANTHROPIC_API_KEY"
ENV_FRED_KEY      = "FRED_API_KEY"
ENV_SERP_KEY      = "SERP_API_KEY"

# ── Labels des facteurs ───────────────────────────────────────────────────────
FACTOR_LABELS: dict = {
    "F1": "Perf. actions vs MSCI Europe",
    "F2": "Écart croissance PIB vs Zone Euro",
    "F3": "Spread souverain vs Bund",
    "F4": "Stabilité politique",
    "F5": "PER relatif vs MSCI Europe",
}

# ── Facteurs spécifiques par pays ─────────────────────────────────────────────
COUNTRY_SPECIFIC_FACTORS: dict = {
    "Germany": {
        "factors": [
            "perf_boursiere",
            "ifo_business_climate",
            "defense_spending_gdp",
            "per_relatif",
            "spread_bund",
            "pib_relatif",
        ],
        "description": "Allemagne : moteur fiscal, défense, industrie exportatrice",
        "primary_drivers": ["ifo_business_climate", "defense_spending_gdp", "per_relatif"],
    },
    "France": {
        "factors": [
            "perf_boursiere",
            "spread_oat_bund",
            "deficit_pib",
            "stabilite_politique",
            "pib_relatif",
            "per_relatif",
        ],
        "description": "France : spread OAT et risque politique dominent",
        "primary_drivers": ["spread_oat_bund", "deficit_pib", "stabilite_politique"],
    },
    "Italy": {
        "factors": [
            "perf_boursiere",
            "spread_btp_bund",
            "dette_pib",
            "stabilite_politique",
            "pib_relatif",
            "per_relatif",
        ],
        "description": "Italie : spread BTP et stabilité Meloni dominent",
        "primary_drivers": ["spread_btp_bund", "dette_pib", "stabilite_politique"],
    },
    "Spain": {
        "factors": [
            "perf_boursiere",
            "pib_relatif",
            "tourisme_pib",
            "spread_bonos_bund",
            "chomage_variation",
            "stabilite_politique",
        ],
        "description": "Espagne : croissance PIB et tourisme différenciants",
        "primary_drivers": ["pib_relatif", "tourisme_pib", "perf_boursiere"],
    },
    "Netherlands": {
        "factors": [
            "perf_boursiere",
            "exports_variation",
            "per_relatif",
            "pib_relatif",
            "spread_nl_bund",
            "stabilite_politique",
        ],
        "description": "Pays-Bas : économie ouverte, commerce mondial et tech",
        "primary_drivers": ["exports_variation", "per_relatif", "perf_boursiere"],
    },
    "Switzerland": {
        "factors": [
            "perf_boursiere",
            "eurchf_momentum",
            "per_relatif",
            "stabilite_politique",
            "pib_relatif",
            "inflation_relative",
        ],
        "description": "Suisse : devise et valorisation dominent",
        "primary_drivers": ["eurchf_momentum", "per_relatif", "stabilite_politique"],
    },
}

# Mapping facteurs → sources de données
FACTOR_SOURCES: dict = {
    "perf_boursiere":       "market_data.compute_annual_returns",
    "pib_relatif":          "macro_data.fetch_gdp_growth",
    "spread_oat_bund":      "market_data.fetch_sovereign_spreads",
    "spread_btp_bund":      "market_data.fetch_sovereign_spreads",
    "spread_bonos_bund":    "market_data.fetch_sovereign_spreads",
    "spread_nl_bund":       "market_data.fetch_sovereign_spreads",
    "spread_bund":          "market_data.fetch_sovereign_spreads",
    "per_relatif":          "market_data.fetch_per_data",
    "stabilite_politique":  "political_data.load_political_scores",
    "deficit_pib":          "macro_data.fetch_fiscal_data",
    "dette_pib":            "macro_data.fetch_fiscal_data",
    "ifo_business_climate": "macro_data.fetch_sentiment_data",
    "defense_spending_gdp": "macro_data.fetch_defense_spending",
    "tourisme_pib":         "macro_data.fetch_tourism_data",
    "chomage_variation":    "macro_data.fetch_unemployment",
    "exports_variation":    "macro_data.fetch_trade_data",
    "eurchf_momentum":      "market_data.fetch_fx_momentum",
    "inflation_relative":   "macro_data.fetch_inflation_data",
}

# ── Fallbacks pour les nouveaux facteurs (sources FMI/OCDE/Eurostat) ──────────
FALLBACK_IFO: dict = {2022: 94.2, 2023: 87.3, 2024: 85.7, 2025: 88.4, 2026: 91.0}

FALLBACK_DEFENSE_GDP: dict = {
    "Germany":     {2022: 1.44, 2023: 1.57, 2024: 2.12, 2025: 2.40, 2026: 2.80},
    "France":      {2022: 1.90, 2023: 1.93, 2024: 2.06, 2025: 2.18, 2026: 2.25},
    "Italy":       {2022: 1.51, 2023: 1.46, 2024: 1.49, 2025: 1.58, 2026: 1.70},
    "Spain":       {2022: 1.01, 2023: 1.26, 2024: 1.28, 2025: 1.35, 2026: 1.50},
    "Netherlands": {2022: 1.44, 2023: 1.70, 2024: 1.93, 2025: 2.05, 2026: 2.20},
    "Switzerland": {2022: 0.74, 2023: 0.74, 2024: 0.76, 2025: 0.82, 2026: 0.90},
}

FALLBACK_DEFICIT_PIB: dict = {
    "France":      {2022: -4.7, 2023: -5.5, 2024: -6.1, 2025: -5.4, 2026: -4.8},
    "Germany":     {2022: -2.5, 2023: -2.5, 2024: -2.8, 2025: -3.5, 2026: -3.8},
    "Italy":       {2022: -8.0, 2023: -7.2, 2024: -3.4, 2025: -3.8, 2026: -3.5},
    "Spain":       {2022: -4.6, 2023: -3.5, 2024: -3.1, 2025: -3.0, 2026: -2.8},
    "Netherlands": {2022: -0.1, 2023: -0.4, 2024: -1.8, 2025: -2.2, 2026: -2.0},
    "Switzerland": {2022:  1.1, 2023:  1.0, 2024:  0.6, 2025:  0.4, 2026:  0.5},
}

FALLBACK_DETTE_PIB: dict = {
    "France":      {2022: 111.6, 2023: 110.6, 2024: 113.0, 2025: 115.0, 2026: 116.5},
    "Germany":     {2022:  66.4, 2023:  63.6, 2024:  62.9, 2025:  64.5, 2026:  66.0},
    "Italy":       {2022: 141.7, 2023: 137.3, 2024: 135.8, 2025: 136.5, 2026: 137.0},
    "Spain":       {2022: 113.2, 2023: 107.7, 2024: 103.4, 2025: 101.0, 2026:  99.5},
    "Netherlands": {2022:  50.1, 2023:  46.5, 2024:  46.5, 2025:  48.0, 2026:  49.5},
    "Switzerland": {2022:  38.8, 2023:  37.0, 2024:  36.5, 2025:  36.0, 2026:  35.5},
}

FALLBACK_TOURISME_PIB: dict = {
    "Spain":  {2022: 8.5, 2023: 9.8, 2024: 10.6, 2025: 11.0, 2026: 11.2},
    "France": {2022: 5.2, 2023: 6.1, 2024: 6.3,  2025: 6.4,  2026: 6.5},
    "Italy":  {2022: 5.8, 2023: 7.1, 2024: 7.4,  2025: 7.6,  2026: 7.7},
}

FALLBACK_CHOMAGE: dict = {
    "France":      {2022: 7.3, 2023: 7.3, 2024: 7.5, 2025: 7.6, 2026: 7.4},
    "Germany":     {2022: 5.3, 2023: 5.7, 2024: 6.0, 2025: 5.8, 2026: 5.5},
    "Italy":       {2022: 8.1, 2023: 6.7, 2024: 6.2, 2025: 6.0, 2026: 5.8},
    "Spain":       {2022: 12.9, 2023: 12.2, 2024: 11.6, 2025: 11.0, 2026: 10.5},
    "Netherlands": {2022: 3.5, 2023: 3.6, 2024: 3.9, 2025: 4.0, 2026: 3.8},
    "Switzerland": {2022: 2.2, 2023: 2.1, 2024: 2.3, 2025: 2.4, 2026: 2.2},
}

FALLBACK_EXPORTS_GROWTH: dict = {
    "Netherlands": {2022: 8.5,  2023: -1.5, 2024: 2.1, 2025: 2.8, 2026: 3.2},
    "Germany":     {2022: 3.2,  2023: -1.8, 2024: 0.4, 2025: 1.2, 2026: 2.5},
    "France":      {2022: 8.9,  2023:  1.4, 2024: 0.8, 2025: 1.5, 2026: 2.0},
}

FALLBACK_EURCHF: dict = {
    2022: -8.2,
    2023: -2.1,
    2024: -1.8,
    2025: -3.5,
    2026: -1.0,
}

FALLBACK_INFLATION_RELATIVE: dict = {
    "France":      {2022:  0.4, 2023:  0.5, 2024:  0.6, 2025:  0.3, 2026:  0.2},
    "Germany":     {2022:  1.8, 2023:  1.3, 2024:  0.8, 2025:  0.5, 2026:  0.3},
    "Italy":       {2022:  2.1, 2023:  0.5, 2024: -0.2, 2025: -0.1, 2026:  0.1},
    "Spain":       {2022:  2.5, 2023: -0.8, 2024: -0.5, 2025: -0.3, 2026:  0.0},
    "Netherlands": {2022:  5.2, 2023:  1.8, 2024:  0.3, 2025:  0.2, 2026:  0.1},
    "Switzerland": {2022: -4.5, 2023: -3.2, 2024: -2.8, 2025: -2.5, 2026: -2.0},
}

# ── MSCI Europe — pondérations neutres par pays (benchmark allocation) ────────
# Source : MSCI Europe Index, données Q4 2025
# Représente l'allocation "neutre" quand la position est N
MSCI_EUROPE_WEIGHTS: dict = {
    "France":       0.157,   # 15.7% du MSCI Europe
    "Germany":      0.145,   # 14.5%
    "Italy":        0.073,   # 7.3%
    "Spain":        0.089,   # 8.9%
    "Netherlands":  0.068,   # 6.8%
    "Switzerland":  0.142,   # 14.2%
    "Other_Europe": 0.316,   # Reste Europe (UK, Suède, Danemark, etc.)
}

# Déviations appliquées selon position OW/N/UW (en points de pourcentage vs MSCI)
# Calibrées sur les fonds dont on a les données réelles
POSITION_DEVIATIONS: dict = {
    "OW": {
        "France":      +0.040,
        "Germany":     +0.055,
        "Italy":       +0.025,
        "Spain":       +0.035,
        "Netherlands": +0.030,
        "Switzerland": +0.028,
    },
    "N": {
        "France":      0.000,
        "Germany":     0.000,
        "Italy":       0.000,
        "Spain":       0.000,
        "Netherlands": 0.000,
        "Switzerland": 0.000,
    },
    "UW": {
        "France":      -0.035,
        "Germany":     -0.045,
        "Italy":       -0.020,
        "Spain":       -0.028,
        "Netherlands": -0.025,
        "Switzerland": -0.022,
    },
}

# Marge d'erreur par source de données (fraction de l'allocation estimée)
CONFIDENCE_MARGINS: dict = {
    "ground_truth_confirmed": 0.12,  # Position confirmée par rapport officiel
    "outlook_pdf_extracted":  0.20,  # Extraite d'un PDF d'outlook
    "model_predicted":        0.35,  # Prédite par le modèle factoriel
    "ml_predicted":           0.25,  # Prédite par Random Forest
}

# Part des AUM investie en actions européennes par type de fonds
# Utilisé uniquement en fallback si EUROPEAN_EQUITY_AUM n'est pas disponible
EQUITY_EUROPE_SHARE: dict = {
    "Généraliste Volume": 0.35,
    "Banque Privée":      0.28,
    "Assureur":           0.22,
    "Boutique":           0.45,
}

# ── SOURCE 1 : AUM actions européennes par fonds (Md€) ────────────────────────
# Source : rapports annuels 2025, factsheets Morningstar, statistiques EFAMA
# Remplace global_AUM × ratio_forfaitaire pour une estimation plus précise.
# Les AUM globaux surestiment massivement l'exposition Europe (ex: BlackRock
# gère 14 000 Md€ globalement mais seulement ~950 Md€ en actions européennes).
EUROPEAN_EQUITY_AUM: dict = {
    "blackrock":         620,   # Fonds actifs Europe uniquement (ETF pur réplication exclu)
    "ssga":              240,   # Part active/tilt des SPDR — ETF réplication pure exclue
    "jpmorgan":          380,   # JPMorgan European equity strategies
    "gsam":              245,   # Goldman Sachs European equity
    "amundi":            520,   # Amundi (base domestique française forte)
    "bnp":               320,   # BNP Paribas AM European equity
    "natixis":           275,   # Natixis (multi-boutique Harris/DNCA)
    "dws":               310,   # DWS European active equity
    "ubs":               375,   # UBS European equity (Suisse + continental)
    "schroders":         255,   # Schroders European equity
    "fidelity":          175,   # Fidelity European equity strategies
    "alliancebernstein": 150,   # AB European equity
    "columbia":          165,   # Columbia Threadneedle European
    "axa_im":            210,   # AXA IM European equity
    "allianz_gi":        140,   # AllianzGI European equity
    "generali":          190,   # Generali European equity (base italienne)
    "robeco":            122,   # Robeco European equity + quant
    "pictet":            190,   # Pictet European + thématique Europe
    "eurizon":           170,   # Eurizon European equity (groupe Intesa)
    "janus":              92,   # Janus Henderson European equity
    "lazard":             82,   # Lazard European equity
    "lombard_odier":      88,   # Lombard Odier European
    "candriam":           82,   # Candriam European (base belge)
    "carmignac":          29,   # Carmignac Investissement Europe
    "dnca":               55,   # DNCA Finance (boutique européenne pure)
    "santander":          60,   # Santander AM European equity
    "caixabank":          27,   # CaixaBank AM European equity
    "bbva":               14,   # BBVA AM European equity
    "anima":              40,   # ANIMA European equity (focus Italie)
    "unicaja":             7,   # Unicaja (petite boutique espagnole)
    "mapfre":              4,   # Mapfre AM European equity
}

# ── SOURCE 2 : Biais home-country par fonds ────────────────────────────────────
# Source : littérature académique sur home-bias institutionnel
# (Coval & Moskowitz 1999, Ferreira & Matos 2008, Gomez-Biscarri et al. 2022)
# Les fonds domestiques surpondèrent structurellement leur marché national
# par rapport au benchmark MSCI, indépendamment de leur position OW/N/UW.
# Format : {fund_key: {country_EN: multiplicateur_sur_poids_MSCI}}
HOME_COUNTRY_BIAS: dict = {
    # Fonds espagnols : forte surpondération Espagne (~3-5x MSCI weight)
    "caixabank":     {"Spain": 3.2},
    "santander":     {"Spain": 2.4},
    "bbva":          {"Spain": 2.8},
    "unicaja":       {"Spain": 3.5},
    "mapfre":        {"Spain": 2.5},
    # Fonds italiens : forte surpondération Italie
    "generali":      {"Italy": 2.6},
    "eurizon":       {"Italy": 3.0},
    "anima":         {"Italy": 3.8},
    # Fonds suisses : forte surpondération Suisse (marché domestique hors MSCI Europe souvent)
    "ubs":           {"Switzerland": 2.2},
    "pictet":        {"Switzerland": 2.5},
    "lombard_odier": {"Switzerland": 2.3},
    # Fonds français : léger biais France
    "dnca":          {"France": 1.8},
    "carmignac":     {"France": 1.5},
    "natixis":       {"France": 1.4},
    "amundi":        {"France": 1.3},
    "bnp":           {"France": 1.3},
    "axa_im":        {"France": 1.3},
    # Fonds allemands : léger biais Allemagne
    "dws":           {"Germany": 1.4},
    "allianz_gi":    {"Germany": 1.3},
}

# ── SOURCE 3 : Style de gestion (actif / semi-passif / passif) ────────────────
# Source : classification Morningstar active/passif + factsheets fonds
# Les fonds passifs ne peuvent pas dévier significativement du benchmark MSCI.
FUND_STYLE: dict = {
    "ssga":      "passif",       # SPDR ETFs : pure réplication indicielle
    "blackrock": "semi_passif",  # iShares ETFs + quelques fonds actifs
    # Tous les autres : "actif" (valeur par défaut)
}
PASSIVE_MAX_DEVIATION:      float = 0.005   # ±0.5 pt % max (fonds passifs)
SEMI_PASSIVE_MAX_DEVIATION: float = 0.015   # ±1.5 pt % max (semi-passifs)

# ── SOURCE 4 : Amplificateur de déviation par type de gestion ─────────────────
# Source : études Morningstar active share par catégorie (SPIVA Europe 2024,
# Cremers & Petajisto 2009 sur l'active share)
# Un boutique high-conviction dévie ~2x plus du benchmark qu'un généraliste.
# Un assureur est contraint par Solvabilité II → déviations limitées.
DEVIATION_AMPLIFIER_BY_TYPE: dict = {
    "Généraliste Volume": 0.75,  # Low active share, tracking error contrôlé (20-35%)
    "Banque Privée":      1.10,  # Active share modéré (45-60%), mandats clients variés
    "Assureur":           0.60,  # Contraintes Solvabilité II, ALM strict
    "Boutique":           1.85,  # High active share (65-90%), gestion conviction
}

# Surcharges fonds-spécifiques (override du type)
# Basé sur les factsheets et reports annuels des fonds
FUND_CONVICTION_OVERRIDE: dict = {
    # Fonds quasi-passifs
    "ssga":          0.10,  # SPDR ETFs — pure réplication
    "blackrock":     0.40,  # iShares dominant + quelques actifs
    # Boutiques haute conviction
    "dnca":          2.20,  # DNCA : gestion très concentrée (30-40 lignes)
    "carmignac":     2.30,  # Carmignac : high-conviction, fort track-record déviation
    "pictet":        1.55,  # Pictet : thématique + régional, fort active share
    "lombard_odier": 1.45,  # LO : gestion patrimoniale active
    "candriam":      1.35,  # Candriam : active ESG avec fortes convictions
    "lazard":        1.45,  # Lazard : value equity avec concentration pays
    "robeco":        1.30,  # Robeco : quant + active, déviation mesurée
    # Banques privées avec forte conviction géographique
    "dws":           1.20,  # DWS : fort biais Allemagne + convictions
    "allianz_gi":    0.90,  # AllianzGI : plus contraint que DWS
    # Généralistes avec conviction modérée
    "jpmorgan":      1.05,  # JPMAM : actif modéré, large univers
    "gsam":          1.15,  # GSAM : macro tilts significatifs
    "schroders":     1.10,  # Schroders : stock-picking actif
    "fidelity":      1.10,  # Fidelity : stock-picking pays actif
}

# Capitalisation boursière des marchés actions par pays (Md€, estimation 2026)
MARKET_CAP_REFERENCE: dict = {
    "France":       2800,
    "Germany":      1900,
    "Italy":         750,
    "Spain":         800,
    "Netherlands":  1100,
    "Switzerland":  1600,
}

# Part des marchés actions détenue par les institutionnels étrangers
# Source : estimations BCE / Banque de France / données OCDE
FOREIGN_INSTITUTIONAL_OWNERSHIP: dict = {
    "France":       0.42,
    "Germany":      0.45,
    "Italy":        0.38,
    "Spain":        0.44,
    "Netherlands":  0.55,
    "Switzerland":  0.48,
}

# Part que nos 31 fonds représentent parmi les institutionnels étrangers
# sur ces marchés — nos 31 fonds sont les TOP managers européens (source EFAMA 2025)
OUR_FUNDS_MARKET_SHARE: float = 0.52

# ── Prompt d'extraction des positions (utilisé dans collector.py) ──────────────
PROMPT_EXTRACTION = """
Tu es un analyste financier expert. Ton rôle est d'extraire les positions
d'allocation géographique d'un document de fonds d'investissement.

Pour chaque pays mentionné parmi : France, Allemagne, Italie, Espagne,
Pays-Bas, Suisse — extrais la position du fonds :
- Overweight (OW) : surpondéré, positif, favorable, buy, surexposé
- Neutral (N) : neutre, pondération marché, hold, en ligne avec le benchmark
- Underweight (UW) : sous-pondéré, négatif, défavorable, sell, sous-exposé

Si un pays n'est pas mentionné ou si l'information est absente, retourne "Non disponible".

Réponds UNIQUEMENT en JSON valide, sans aucun texte avant ou après :
{
  "fonds": "nom du fonds détecté dans le document",
  "annee": "année de l'outlook (ex: 2026)",
  "source_url": "url source fournie",
  "confiance": "haute|moyenne|faible",
  "positions": {
    "France": "OW|N|UW|Non disponible",
    "Allemagne": "OW|N|UW|Non disponible",
    "Italie": "OW|N|UW|Non disponible",
    "Espagne": "OW|N|UW|Non disponible",
    "Pays-Bas": "OW|N|UW|Non disponible",
    "Suisse": "OW|N|UW|Non disponible"
  }
}
"""
