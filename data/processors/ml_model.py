"""
Modèle Random Forest par pays.
Entraîné sur les données historiques (ground_truth_master.json).
Prédit les positions OW/N/UW pour 2026.
N'importe PAS streamlit.
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path

from config import (
    COUNTRIES, COUNTRY_NAMES_FR, GROUND_TRUTH_FILE,
    HISTORY_YEARS, PREDICTION_YEAR, POSITION_LABELS,
)


LABEL_MAP     = {"OW": 2, "N": 1, "UW": 0}
LABEL_REVERSE = {2: "OW", 1: "N", 0: "UW"}
FR_TO_EN = {
    "France": "France", "Allemagne": "Germany", "Italie": "Italy",
    "Espagne": "Spain", "Pays-Bas": "Netherlands", "Suisse": "Switzerland",
}


def load_ground_truth() -> dict:
    """Charge ground_truth_master.json. Retourne {} si absent."""
    path = GROUND_TRUTH_FILE
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build_training_dataset(
    all_features: dict,
    ground_truth: dict,
    country: str,
) -> tuple:
    """
    Construit X (features) et y (labels) pour un pays.
    Utilise toutes les années historiques de tous les fonds disponibles.

    Retourne (X, y) ou (None, None) si pas assez de données.
    """
    from config import FONDS
    country_fr = COUNTRY_NAMES_FR.get(country, country)
    features_df = all_features.get(country)

    if features_df is None:
        return None, None

    X_rows = []
    y_labels = []

    for fund_key, fund_data in ground_truth.items():
        for year_str, year_positions in fund_data.items():
            year = int(year_str)
            if year not in HISTORY_YEARS:
                continue

            # Récupérer la position réelle
            pos_raw = year_positions.get(country_fr)
            if pos_raw not in ("OW", "N", "UW"):
                continue

            # Récupérer les features pour ce pays/année
            if year not in features_df.index:
                continue

            row = features_df.loc[year].to_dict()
            # Ajouter le type de fonds comme feature catégorielle encodée
            fund_cfg = FONDS.get(fund_key, {})
            typologie = fund_cfg.get("typologie", "Généraliste Volume")
            row["fund_type_score"] = {
                "Généraliste Volume": 0.0,
                "Banque Privée": 0.3,
                "Assureur": -0.1,
                "Boutique": 0.5,
            }.get(typologie, 0.0)

            X_rows.append(row)
            y_labels.append(LABEL_MAP[pos_raw])

    if len(X_rows) < 6:
        return None, None

    X = pd.DataFrame(X_rows).fillna(0.0)
    y = pd.Series(y_labels)
    return X, y


def train_country_model(
    country: str,
    all_features: dict,
    ground_truth: dict,
) -> dict:
    """
    Entraîne un Random Forest pour un pays.
    Retourne un dict avec le modèle, les métriques, et l'importance des features.

    Retourne {"status": "insufficient_data"} si pas assez d'observations.
    """
    try:
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.model_selection import cross_val_score, StratifiedKFold
    except ImportError:
        return {
            "status": "error",
            "country": country,
            "message": "scikit-learn non installé. Exécutez : pip install scikit-learn",
        }

    X, y = build_training_dataset(all_features, ground_truth, country)

    if X is None or len(X) < 6:
        return {
            "status": "insufficient_data",
            "country": country,
            "n_samples": 0 if X is None else len(X),
            "message": f"Seulement {0 if X is None else len(X)} observations — minimum 6 requis",
        }

    # Random Forest avec hyperparamètres adaptés aux petits datasets
    clf = RandomForestClassifier(
        n_estimators=100,
        max_depth=3,
        min_samples_leaf=2,
        class_weight="balanced",
        random_state=42,
    )

    # Cross-validation avec K-Fold stratifié (si assez de données)
    cv_scores = None
    if len(X) >= 9:
        k = min(3, len(X) // 3)
        cv = StratifiedKFold(n_splits=k, shuffle=True, random_state=42)
        try:
            cv_scores = cross_val_score(clf, X, y, cv=cv, scoring="accuracy")
        except Exception:
            cv_scores = None

    # Entraînement final sur toutes les données
    clf.fit(X, y)

    # Importance des features
    feature_importance = dict(zip(X.columns, clf.feature_importances_))
    top_features = sorted(
        feature_importance.items(), key=lambda x: x[1], reverse=True
    )[:5]

    # Précision sur les données d'entraînement (pour référence)
    y_pred_train = clf.predict(X)
    train_accuracy = (y_pred_train == y.values).mean()

    return {
        "status": "trained",
        "country": country,
        "model": clf,
        "feature_names": list(X.columns),
        "n_samples": len(X),
        "train_accuracy": round(float(train_accuracy), 3),
        "cv_accuracy": round(float(cv_scores.mean()), 3) if cv_scores is not None else None,
        "cv_std": round(float(cv_scores.std()), 3) if cv_scores is not None else None,
        "feature_importance": feature_importance,
        "top_features": top_features,
    }


def predict_country_2026(
    country: str,
    model_result: dict,
    all_features: dict,
) -> dict:
    """
    Fait la prédiction pour PREDICTION_YEAR en utilisant le modèle entraîné.
    Retourne position prédite + probabilités.
    """
    if model_result.get("status") != "trained":
        return {
            "position": "N",
            "prob_OW": 0.33,
            "prob_N": 0.34,
            "prob_UW": 0.33,
            "confidence": "Faible",
            "source": "fallback_factoriel",
        }

    clf = model_result["model"]
    feature_names = model_result["feature_names"]
    features_df = all_features.get(country)

    if features_df is None or PREDICTION_YEAR not in features_df.index:
        return {
            "position": "N",
            "prob_OW": 0.33,
            "prob_N": 0.34,
            "prob_UW": 0.33,
            "confidence": "Faible",
            "source": "données_manquantes",
        }

    # Vecteur de features pour 2026
    row = features_df.loc[PREDICTION_YEAR].to_dict()
    row["fund_type_score"] = 0.0  # valeur neutre pour la prédiction générique

    # Aligner sur les features d'entraînement
    X_pred = pd.DataFrame([row])[feature_names].fillna(0.0)

    # Prédiction + probabilités
    pred_label = int(clf.predict(X_pred)[0])
    probas = clf.predict_proba(X_pred)[0]

    # Mapping classes → OW/N/UW
    classes = clf.classes_
    prob_dict = {LABEL_REVERSE.get(int(c), "N"): float(p)
                 for c, p in zip(classes, probas)}
    prob_ow = prob_dict.get("OW", 0.0)
    prob_n  = prob_dict.get("N",  0.0)
    prob_uw = prob_dict.get("UW", 0.0)

    predicted_position = LABEL_REVERSE.get(pred_label, "N")
    prob_predicted = prob_dict.get(predicted_position, 0.0)

    confidence = (
        "Haute"   if prob_predicted >= 0.70
        else "Moyenne" if prob_predicted >= 0.50
        else "Faible"
    )

    return {
        "position": predicted_position,
        "prob_OW": round(prob_ow, 3),
        "prob_N":  round(prob_n,  3),
        "prob_UW": round(prob_uw, 3),
        "confidence": confidence,
        "source": "random_forest",
    }


def train_all_countries(
    all_features: dict,
    ground_truth: dict = None,
) -> dict:
    """
    Entraîne les modèles pour tous les pays.
    Retourne : {country: model_result}
    """
    if ground_truth is None:
        ground_truth = load_ground_truth()

    results = {}
    for country in COUNTRIES:
        results[country] = train_country_model(
            country, all_features, ground_truth
        )
    return results


def predict_all_countries_2026(
    ml_models: dict,
    all_features: dict,
) -> dict:
    """
    Prédit les positions 2026 pour tous les pays.
    Retourne : {country: prediction_dict}
    """
    predictions = {}
    for country in COUNTRIES:
        model_result = ml_models.get(country, {"status": "not_trained"})
        predictions[country] = predict_country_2026(
            country, model_result, all_features
        )
    return predictions


def get_ml_summary(
    ml_models: dict,
    ml_predictions: dict,
) -> pd.DataFrame:
    """
    Construit un DataFrame de synthèse des résultats ML.
    """
    rows = []
    for country in COUNTRIES:
        model = ml_models.get(country, {})
        pred  = ml_predictions.get(country, {})

        status = model.get("status", "not_trained")
        top_f  = model.get("top_features", [])
        top_f_str = ", ".join(
            f"{f[0]} ({f[1]:.0%})" for f in top_f[:3]
        ) if top_f else "—"

        position = pred.get("position", "N")
        if position == "OW":
            prob_key = "prob_OW"
        elif position == "UW":
            prob_key = "prob_UW"
        else:
            prob_key = "prob_N"

        rows.append({
            "Pays":             COUNTRY_NAMES_FR.get(country, country),
            "Statut":           "✅ Entraîné" if status == "trained" else "⚠ Données insuffisantes",
            "Observations":     model.get("n_samples", 0),
            "Précision train":  f"{model.get('train_accuracy', 0):.0%}" if status == "trained" else "—",
            "Précision CV":     f"{model.get('cv_accuracy', 0):.0%}" if model.get("cv_accuracy") else "—",
            "Position ML":      POSITION_LABELS.get(position, "Neutre"),
            "Prob. prédite":    f"{pred.get(prob_key, 0):.0%}",
            "Confiance":        pred.get("confidence", "Faible"),
            "Top 3 features":   top_f_str,
        })

    return pd.DataFrame(rows)
