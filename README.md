# 📈 Edram Competitive Intelligence 2026

> Anticipate where **31 competing asset managers** will overweight or underweight **6 European equity markets** in 2026 — to support allocation decisions (follow the consensus or go contrarian).

**School case study for Edmond de Rothschild Asset Management · March 2026**

> Reference data files (fund ground truth, political events, holdings) and API keys are **not** included.

---

## How it works
**A 5-factor model, scored per country and per fund**

| Factor | Signal | Source | Weight |
|---|---|---|---|
| F1 | Relative equity performance vs MSCI Europe | yfinance | 30 % |
| F2 | GDP growth gap vs Euro area | FRED / OECD fallback | 25 % |
| F3 | Sovereign spread vs Bund | FRED / fallback | 20 % |
| F4 | Political stability score | curated events file | 15 % |
| F5 | Relative P/E vs MSCI Europe | yfinance ETFs | 10 % |

1. Each factor normalised with a rolling z-score (4-year window).
2. Weighted composite → **OW / N / UW** classification per fund × country.
3. **Monte Carlo (1,000 runs)** turns scores into probabilities.
4. Consensus across the 31 funds → recommendation for Edram.
5. Back-testing against a **ground truth of real fund positions 2022–2025**, collected from published outlooks.
6. An LLM (Llama 3.3 70B via Groq) writes the narrative analysis of the recommendation.

**Dashboard (Streamlit, 5 pages):** consensus heatmap (31 funds × 6 countries), factor detail per fund, Edram recommendation + LLM analysis, validation vs history, editable parameters (weights, thresholds, political events).

## Run it
```bash
pip install -r requirements.txt
cp .env.example .env        # GROQ_API_KEY, FRED_API_KEY (optional)
streamlit run app.py
```
`ground_truth_master.json` and `political_events.json` are expected at the root (not versioned); FRED-less fallbacks keep the factor model running.

| Path | Content |
|---|---|
| `data/fetchers/` | market (yfinance), macro (FRED/fallback), political factors |
| `data/processors/` | factor scoring, Monte Carlo confidence, consensus — no Streamlit, testable alone |
| `pages/` | consensus, predictions, recommendation, validation, settings, allocations |
| `llm/` | Groq narrative agent, outlook collector |
| `config.py` | single source of truth for weights, thresholds, tickers, funds |

## Stack
`Python 3.12` `Streamlit` `Plotly` `pandas` `yfinance` `FRED API` `Monte Carlo` `Groq / Llama 3.3` `SerpAPI` `PDF extraction`

---

### 🇫🇷 En bref
Tableau de bord Streamlit pour Edmond de Rothschild AM : prédire le positionnement (Surpondéré / Neutre / Sous-pondéré) de 31 fonds concurrents sur 6 pays européens en 2026, via un modèle à 5 facteurs (performance, PIB, spreads, politique, PER), des probabilités Monte Carlo, un consensus, une validation sur les positions réelles 2022-2025 et une analyse narrative par LLM. Données de référence non publiées.
