"""
AI Delay Prediction Model
=========================
Uses GradientBoostingRegressor trained on action item features.
Provides both:
  - Rule-based prediction (always available, no training needed)
  - ML-based prediction (requires trained model file)

Features used:
  risk_score, complexity_score, financial_exposure,
  dependency_count, task_count_in_dept, priority_weight
"""

import os
import logging
import pickle
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)

MODEL_PATH = Path(__file__).resolve().parent.parent / 'ml_models' / 'delay_model.pkl'
MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)

# ─── Priority weight mapping ──────────────────────────────────────────────────
PRIORITY_WEIGHT = {'Low': 0.2, 'Medium': 0.4, 'High': 0.7, 'Critical': 1.0}

# ─── Base delay days per dept (rule-based fallback) ──────────────────────────
BASE_DELAY = {
    'Civil': 14, 'Mechanical': 10, 'Electrical': 8, 'MEP': 7,
    'Legal': 5,  'Finance': 3,     'HSE': 4,       'Planning': 6,
    'Procurement': 12, 'QA/QC': 5, 'Signaling': 10,
}


# ─── Feature builder ─────────────────────────────────────────────────────────

def build_features(risk_score: float, complexity_score: float,
                   financial_exposure: float, dependency_count: int,
                   task_count_in_dept: int, priority: str) -> list:
    """Returns feature vector for the delay model."""
    return [
        float(risk_score),
        float(complexity_score),
        float(financial_exposure) / 1_000_000_000,   # normalise to billions
        int(dependency_count),
        int(task_count_in_dept),
        PRIORITY_WEIGHT.get(priority, 0.4),
    ]


# ─── Rule-based prediction (always available) ────────────────────────────────

def predict_delay_rule_based(dept_name: str, avg_risk: float,
                             task_count: int) -> int:
    """
    Deterministic formula:
    delay = base_days × (1 + avg_risk) × (1 + task_count × 0.02)
    """
    base  = BASE_DELAY.get(dept_name, 7)
    days  = base * (1.0 + avg_risk) * (1.0 + task_count * 0.02)
    return max(1, round(days))


# ─── ML-based prediction ─────────────────────────────────────────────────────

def train_model(X: list, y: list) -> None:
    """
    Train GradientBoostingRegressor on historical delay data.

    Args:
        X: list of feature vectors (from build_features())
        y: list of actual delay days (float/int)
    """
    try:
        from sklearn.ensemble import GradientBoostingRegressor
        from sklearn.preprocessing import StandardScaler
        from sklearn.pipeline import Pipeline

        model = Pipeline([
            ('scaler', StandardScaler()),
            ('gb',     GradientBoostingRegressor(
                n_estimators=200,
                learning_rate=0.05,
                max_depth=4,
                subsample=0.8,
                random_state=42,
            )),
        ])
        X_arr = np.array(X, dtype=float)
        y_arr = np.array(y, dtype=float)
        model.fit(X_arr, y_arr)

        with open(MODEL_PATH, 'wb') as f:
            pickle.dump(model, f)

        logger.info(f"[DelayModel] Trained on {len(X)} samples → saved to {MODEL_PATH}")
    except Exception as e:
        logger.exception(f"[DelayModel] Training failed: {e}")


def predict_delay_ml(features: list, dept_name: str = '',
                     avg_risk: float = 0.0, task_count: int = 0) -> int:
    """
    Predict delay days using ML model.
    Falls back to rule-based if model not available.
    """
    if MODEL_PATH.exists():
        try:
            with open(MODEL_PATH, 'rb') as f:
                model = pickle.load(f)
            days = model.predict([features])[0]
            return max(1, round(float(days)))
        except Exception as e:
            logger.warning(f"[DelayModel] ML prediction failed ({e}), using rule-based")

    # Fallback
    return predict_delay_rule_based(dept_name, avg_risk, task_count)


# ─── Batch prediction for all departments in a tender ────────────────────────

def predict_delays_for_tender(tender_id: int) -> dict:
    """
    Returns a dict of {dept_name: predicted_days} for all departments
    that have action items in the given tender.
    Uses ML if model exists, rule-based otherwise.
    """
    from tenders.models import BidActionItem
    from django.db.models import Avg, Count

    dept_stats = (
        BidActionItem.objects
        .filter(tender_id=tender_id)
        .values('department__name')
        .annotate(
            avg_risk=Avg('risk_score'),
            avg_complexity=Avg('complexity_score'),
            count=Count('id'),
        )
    )

    results = {}
    for row in dept_stats:
        name = row['department__name']
        if not name:
            continue
        avg_risk = row['avg_risk'] or 0.0
        avg_cplx = row['avg_complexity'] or 0.0
        count    = row['count'] or 0

        features = build_features(
            risk_score=avg_risk,
            complexity_score=avg_cplx,
            financial_exposure=0,
            dependency_count=0,
            task_count_in_dept=count,
            priority='Medium',
        )
        results[name] = predict_delay_ml(features, name, avg_risk, count)

    return results


# ─── Synthetic training data generator (for bootstrap) ───────────────────────

def generate_synthetic_training_data(n: int = 500) -> tuple:
    """
    Generate synthetic (X, y) training data for bootstrapping the model
    when no historical data is available.
    Formula mirrors the rule-based prediction with added noise.
    """
    import random
    random.seed(42)

    X, y = [], []
    dept_names = list(BASE_DELAY.keys())
    priorities = list(PRIORITY_WEIGHT.keys())

    for _ in range(n):
        dept        = random.choice(dept_names)
        risk        = random.uniform(0.0, 0.99)
        complexity  = random.uniform(0.0, 0.95)
        exposure    = random.uniform(0, 2e9)
        dep_count   = random.randint(0, 5)
        task_count  = random.randint(1, 50)
        priority    = random.choice(priorities)

        feat = build_features(risk, complexity, exposure, dep_count,
                              task_count, priority)
        X.append(feat)

        # Label = rule-based + noise
        base_days = predict_delay_rule_based(dept, risk, task_count)
        noise     = random.gauss(0, base_days * 0.1)
        y.append(max(1, base_days + noise))

    return X, y


def ensure_model_trained() -> None:
    """Train on synthetic data if no model file exists yet."""
    if not MODEL_PATH.exists():
        logger.info("[DelayModel] No model found, training on synthetic data...")
        X, y = generate_synthetic_training_data(n=1000)
        train_model(X, y)
