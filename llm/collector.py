"""
Pipeline de collecte automatique des outlooks de fonds d'investissement.

Étapes :
  1. Construction des URLs candidates (lien_rapport en priorité, puis SerpAPI)
  2. Téléchargement robuste (PDF → bytes base64, HTML → texte)
  3. Extraction des positions via Claude (Opus pour PDF, Sonnet pour HTML)
  4. Validation + cache JSON par fonds/année
"""

import base64
import json
import logging
import time
from pathlib import Path

import requests
import urllib3

from config import (
    CACHE_DIR,
    FONDS,
    PROMPT_EXTRACTION,
    COUNTRIES,
    COUNTRY_NAMES_FR,
)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logger = logging.getLogger(__name__)

# Mapping EN → FR pour la normalisation
COUNTRY_EN_TO_FR = {k: COUNTRY_NAMES_FR[k] for k in COUNTRIES}

MAX_TEXT_CHARS = 20000
LLM_MODEL_PDF  = "claude-opus-4-6"    # Meilleure extraction PDF
LLM_MODEL_HTML = "claude-sonnet-4-6"  # Suffisant pour HTML

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/pdf,*/*;q=0.8",
}


# ── Étape 1 : Construction des URLs candidates ────────────────────────────────

def _search_serpapi(query: str, api_key: str, max_results: int = 5) -> list[dict]:
    """Recherche via SerpAPI Google Search. Retourne liste {url, title, snippet}."""
    try:
        resp = requests.get(
            "https://serpapi.com/search",
            params={"q": query, "api_key": api_key, "num": max_results, "hl": "fr"},
            timeout=15,
            headers=_HEADERS,
            verify=False,
        )
        resp.raise_for_status()
        data = resp.json()
        return [
            {"url": r.get("link", ""), "title": r.get("title", ""), "snippet": r.get("snippet", "")}
            for r in data.get("organic_results", [])[:max_results]
            if r.get("link")
        ]
    except Exception as e:
        logger.warning(f"SerpAPI indisponible : {e}")
        return []


def _search_duckduckgo(query: str, max_results: int = 5) -> list[dict]:
    """Fallback DuckDuckGo gratuit."""
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            return [
                {"url": r.get("href", ""), "title": r.get("title", ""), "snippet": r.get("body", "")}
                for r in ddgs.text(query, max_results=max_results)
                if r.get("href")
            ]
    except Exception as e:
        logger.warning(f"DuckDuckGo indisponible : {e}")
        return []


def _get_candidate_urls(fund_key: str, year: int, serp_api_key: str = "") -> list[str]:
    """
    Construit la liste ordonnée des URLs à essayer :
    1. lien_rapport du fonds (priorité absolue)
    2. url_base du fonds
    3. Résultats SerpAPI (si clé disponible)
    4. Fallback DuckDuckGo
    Retourne une liste de strings URL (dédupliquée, sans None/vide).
    """
    fund_cfg = FONDS.get(fund_key, {})
    fund_nom = fund_cfg.get("nom", fund_key)
    mots_cles = fund_cfg.get("mots_cles_recherche", [fund_nom])
    query = f"{mots_cles[0]} {year}"

    seen  = set()
    urls  = []

    def _add(url: str):
        if url and url not in seen:
            seen.add(url)
            urls.append(url)

    # Priorité 1 : rapport officiel
    _add(fund_cfg.get("lien_rapport", ""))
    # Priorité 2 : URL de base
    _add(fund_cfg.get("url_base", ""))

    # Priorité 3 : SerpAPI
    if serp_api_key:
        serp_results = _search_serpapi(query, serp_api_key, max_results=5)
        if serp_results:
            for r in serp_results:
                _add(r["url"])
        else:
            # SerpAPI a échoué → fallback DuckDuckGo
            for r in _search_duckduckgo(query, max_results=5):
                _add(r["url"])
    else:
        # Pas de clé SerpAPI → DuckDuckGo directement
        for r in _search_duckduckgo(query, max_results=5):
            _add(r["url"])

    return urls


# ── Étape 2 : Téléchargement robuste ──────────────────────────────────────────

def _download_url(url: str) -> tuple[bytes | str, bool]:
    """
    Télécharge une URL.
    Retourne (contenu, is_pdf).
      - is_pdf=True  → contenu est bytes
      - is_pdf=False → contenu est str (texte HTML)
    Retourne (None, False) en cas d'échec.
    """
    try:
        resp = requests.get(
            url, headers=_HEADERS, timeout=15,
            allow_redirects=True, verify=False,
        )
        if resp.status_code in (403, 429, 401):
            logger.warning(f"Accès refusé ({resp.status_code}) : {url}")
            return None, False
        resp.raise_for_status()

        ct = resp.headers.get("Content-Type", "").lower()
        is_pdf = "pdf" in ct or url.lower().endswith(".pdf")
        if is_pdf:
            return resp.content, True
        return resp.text, False

    except Exception as e:
        logger.warning(f"Téléchargement échoué ({url}) : {e}")
        return None, False


def _html_to_text(html: str) -> str:
    """Extrait le texte principal d'une page HTML."""
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "nav", "header", "footer",
                         "aside", "form", "iframe", "noscript"]):
            tag.decompose()
        main = (
            soup.find("article") or soup.find("main") or
            soup.find(id="content") or
            soup.find(class_=lambda c: c and any(
                x in str(c).lower() for x in ["content", "article", "insight", "body"]
            )) or soup.find("body")
        )
        text = (main or soup).get_text(separator="\n", strip=True)
        lines = [l.strip() for l in text.split("\n") if len(l.strip()) > 20]
        return "\n".join(lines)[:MAX_TEXT_CHARS]
    except Exception as e:
        logger.warning(f"Extraction HTML échouée : {e}")
        import re
        return re.sub(r"<[^>]+>", " ", html)[:MAX_TEXT_CHARS]


# ── Étape 3a : Extraction Claude depuis PDF (base64) ──────────────────────────

def _extract_positions_from_pdf(
    pdf_bytes: bytes,
    source_url: str,
    fund_nom: str,
    year: int,
    api_key: str,
) -> dict | None:
    """
    Envoie le PDF encodé en base64 à Claude Opus pour extraction des positions.
    """
    try:
        import anthropic
        b64_data = base64.standard_b64encode(pdf_bytes).decode("utf-8")
        client   = anthropic.Anthropic(api_key=api_key)
        message  = client.messages.create(
            model=LLM_MODEL_PDF,
            max_tokens=512,
            system=PROMPT_EXTRACTION,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": "application/pdf",
                            "data": b64_data,
                        },
                    },
                    {
                        "type": "text",
                        "text": (
                            f"Fonds: {fund_nom}\n"
                            f"Année: {year}\n"
                            f"URL: {source_url}\n\n"
                            "Extrais les positions d'allocation géographique selon les instructions."
                        ),
                    },
                ],
            }],
        )
        return _parse_llm_json(message.content[0].text)
    except Exception as e:
        logger.warning(f"Extraction PDF Claude échouée ({source_url}) : {e}")
        return None


# ── Étape 3b : Extraction Claude depuis texte HTML ────────────────────────────

def _extract_positions_from_html(
    text: str,
    source_url: str,
    fund_nom: str,
    year: int,
    api_key: str,
) -> dict | None:
    """
    Envoie le texte HTML nettoyé à Claude Sonnet pour extraction des positions.
    """
    try:
        import anthropic
        client  = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model=LLM_MODEL_HTML,
            max_tokens=512,
            system=PROMPT_EXTRACTION,
            messages=[{
                "role": "user",
                "content": (
                    f"Fonds: {fund_nom}\n"
                    f"Année: {year}\n"
                    f"URL: {source_url}\n\n"
                    f"--- DOCUMENT ---\n{text[:MAX_TEXT_CHARS]}\n--- FIN ---\n\n"
                    "Extrais les positions d'allocation géographique selon les instructions."
                ),
            }],
        )
        return _parse_llm_json(message.content[0].text)
    except Exception as e:
        logger.warning(f"Extraction HTML Claude échouée ({source_url}) : {e}")
        return None


# ── Étape 4 : Validation du JSON ──────────────────────────────────────────────

def _parse_llm_json(text: str) -> dict | None:
    """
    Parse la réponse Claude en JSON. Tolère du texte avant/après le bloc JSON.
    Retourne None si le JSON est invalide ou ne contient pas de positions.
    """
    text = text.strip()
    start = text.find("{")
    end   = text.rfind("}") + 1
    if start == -1 or end == 0:
        logger.warning("Réponse LLM sans bloc JSON détecté.")
        return None
    try:
        data = json.loads(text[start:end])
        return data
    except json.JSONDecodeError as e:
        logger.warning(f"JSON invalide dans la réponse LLM : {e}")
        return None


def _count_valid_positions(result: dict) -> int:
    """Compte les positions OW/N/UW valides dans le résultat extrait."""
    positions = result.get("positions", {})
    return sum(1 for v in positions.values() if v in ("OW", "N", "UW"))


# ── Cache ─────────────────────────────────────────────────────────────────────

def _get_cache_path(fund_key: str, year: int) -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR / f"ground_truth_{fund_key}_{year}.json"


def load_cached_positions(fund_key: str, year: int) -> dict | None:
    path = _get_cache_path(fund_key, year)
    if path.exists():
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None
    return None


def save_cached_positions(fund_key: str, year: int, data: dict) -> None:
    path = _get_cache_path(fund_key, year)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ── Pipeline principal ─────────────────────────────────────────────────────────

def collect_fund_positions(
    fund_key: str,
    year: int,
    anthropic_api_key: str,
    serp_api_key: str = "",
    force_refresh: bool = False,
    progress_callback=None,
) -> dict:
    """
    Pipeline complet pour un fonds et une année.
    Retourne un dict avec les positions extraites, ou {"erreur": ..., "positions": {}}.

    Args:
        fund_key           : clé du fonds dans config.FONDS
        year               : année de l'outlook à collecter
        anthropic_api_key  : clé API Claude (obligatoire)
        serp_api_key       : clé SerpAPI (optionnel, DDG si absent)
        force_refresh      : ignorer le cache existant
        progress_callback  : fonction(str) pour afficher la progression
    """
    def _log(msg: str):
        logger.info(msg)
        if progress_callback:
            progress_callback(msg)

    # ── Cache ─────────────────────────────────────────────────────────────────
    if not force_refresh:
        cached = load_cached_positions(fund_key, year)
        if cached:
            _log(f"Cache disponible pour {fund_key} {year} — chargement direct.")
            return cached

    fund_cfg = FONDS.get(fund_key)
    if not fund_cfg:
        return {"erreur": f"Fonds inconnu : {fund_key}", "positions": {}}

    fund_nom = fund_cfg["nom"]

    # ── Étape 1 : URLs candidates ─────────────────────────────────────────────
    _log(f"[1/4] Recherche des URLs candidates pour {fund_nom} {year}...")
    candidate_urls = _get_candidate_urls(fund_key, year, serp_api_key)

    if not candidate_urls:
        _log("Aucune URL candidate trouvée.")
        return {
            "erreur": "Aucune URL candidate — vérifiez la clé SerpAPI ou la config du fonds.",
            "positions": {},
            "fund_key": fund_key,
            "year": year,
        }

    _log(f"[1/4] {len(candidate_urls)} URL(s) candidate(s).")

    # ── Étapes 2+3 : Téléchargement + Extraction ──────────────────────────────
    best_result = None

    for i, url in enumerate(candidate_urls):
        _log(f"[2/4] Tentative {i+1}/{len(candidate_urls)} : {url[:90]}...")

        content, is_pdf = _download_url(url)
        if content is None:
            _log("  → Téléchargement échoué, URL suivante.")
            time.sleep(2)
            continue

        if is_pdf:
            if len(content) < 1000:
                _log(f"  → PDF trop petit ({len(content)} octets), URL suivante.")
                time.sleep(2)
                continue
            _log(f"  → PDF téléchargé ({len(content):,} octets). Extraction Claude Opus...")
            result = _extract_positions_from_pdf(content, url, fund_nom, year, anthropic_api_key)
        else:
            text = _html_to_text(content)
            if len(text) < 200:
                _log(f"  → Contenu HTML insuffisant ({len(text)} chars), URL suivante.")
                time.sleep(2)
                continue
            _log(f"  → HTML extrait ({len(text):,} chars). Extraction Claude Sonnet...")
            result = _extract_positions_from_html(text, url, fund_nom, year, anthropic_api_key)

        if result is None:
            _log("  → Extraction LLM échouée, URL suivante.")
            time.sleep(2)
            continue

        valid_count = _count_valid_positions(result)
        if valid_count >= 2:
            result["source_url"]  = url
            result["source_type"] = "pdf" if is_pdf else "html"
            result["fund_key"]    = fund_key
            result["year"]        = year
            _log(
                f"  → Succès : {valid_count} positions extraites "
                f"(confiance : {result.get('confiance', '?')})"
            )
            best_result = result
            break
        else:
            _log(f"  → Seulement {valid_count} position(s) valide(s), URL suivante.")

        time.sleep(2)

    # ── Résultat ──────────────────────────────────────────────────────────────
    if best_result is None:
        _log(f"Extraction échouée sur {len(candidate_urls)} URL(s) pour {fund_nom} {year}.")
        return {
            "erreur": "Aucune position extraite sur toutes les URLs testées",
            "positions": {},
            "fund_key": fund_key,
            "year": year,
            "urls_testees": candidate_urls,
        }

    _log("[4/4] Sauvegarde en cache.")
    save_cached_positions(fund_key, year, best_result)
    return best_result


# ── Intégration ground truth master ───────────────────────────────────────────

def update_ground_truth_master(
    fund_key: str,
    year: int,
    extracted_result: dict,
    master_file_path: Path,
) -> dict:
    """
    Intègre les positions extraites dans ground_truth_master.json.
    Retourne le master mis à jour.
    """
    master = {}
    if master_file_path.exists():
        try:
            with open(master_file_path, encoding="utf-8") as f:
                master = json.load(f)
        except Exception:
            master = {}

    if fund_key not in master:
        master[fund_key] = {}

    positions = extracted_result.get("positions", {})
    master[fund_key][str(year)] = {
        **positions,
        "_source_url":    extracted_result.get("source_url", ""),
        "_confiance":     extracted_result.get("confiance", "inconnue"),
        "_date_collecte": __import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M"),
    }

    with open(master_file_path, "w", encoding="utf-8") as f:
        json.dump(master, f, ensure_ascii=False, indent=2)

    return master


# ── Collecte multi-fonds ──────────────────────────────────────────────────────

def collect_all_funds(
    year: int,
    anthropic_api_key: str,
    serp_api_key: str = "",
    fund_keys: list | None = None,
    force_refresh: bool = False,
    progress_callback=None,
    master_file_path: Path | None = None,
) -> dict:
    """
    Lance la collecte pour tous les fonds (ou la liste fund_keys).
    Retourne un dict {fund_key: result_dict}.
    """
    if master_file_path is None:
        from config import GROUND_TRUTH_FILE
        master_file_path = GROUND_TRUTH_FILE

    if fund_keys is None:
        fund_keys = list(FONDS.keys())

    results = {}
    for i, fk in enumerate(fund_keys):
        if progress_callback:
            progress_callback(f"\n=== Fonds {i+1}/{len(fund_keys)} : {FONDS[fk]['nom']} ===")

        result = collect_fund_positions(
            fund_key=fk,
            year=year,
            anthropic_api_key=anthropic_api_key,
            serp_api_key=serp_api_key,
            force_refresh=force_refresh,
            progress_callback=progress_callback,
        )
        results[fk] = result

        if "erreur" not in result and result.get("positions"):
            update_ground_truth_master(fk, year, result, master_file_path)

        time.sleep(3)

    return results
