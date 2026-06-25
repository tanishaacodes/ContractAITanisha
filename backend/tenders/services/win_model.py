"""
Win Probability Prediction Model
=================================
Uses RandomForestClassifier to predict bid win probability based on:
  - Tender financial metrics
  - Company financial health
  - Historical win rate
  - Bid competitiveness (margin vs market)
  - Eligibility match score
  - Risk score
  - Readiness index

Features engineered from:
  - TenderModel
  - CompanyProfile
  - BidScenario
  - BidReadiness
  - TenderRisk aggregates
"""

import os
import logging
import pickle
from pathlib import Path
from typing import List, Tuple, Optional

import numpy as np

logger = logging.getLogger(__name__)

MODEL_PATH = Path(__file__).resolve().parent.parent / 'ml_models' / 'win_model.pkl'
MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)


# ─────────────────────────────────────────────────────────────────────────────
# Feature Engineering
# ─────────────────────────────────────────────────────────────────────────────

def build_features_for_tender(
    tender_value: float,
    company_turnover: float,
    company_net_worth: float,
    past_win_rate: float,
    bid_margin: float,
    market_avg_margin: float,
    eligibility_match: float,
    avg_risk_score: float,
    readiness_index: float,
    company_projects_completed: int,
    similar_projects_completed: int,
    years_in_business: int,
) -> List[float]:
    """
    Build feature vector for win probability prediction.

    Args:
        tender_value: Tender estimated value (USD)
        company_turnover: Annual turnover (USD)
        company_net_worth: Net worth (USD)
        past_win_rate: Historical win rate (0-1)
        bid_margin: Proposed margin percentage (0-100)
        market_avg_margin: Market average margin (0-100)
        eligibility_match: Eligibility score (0-1)
        avg_risk_score: Average risk score (0-1)
        readiness_index: Bid readiness (0-100)
        company_projects_completed: Total projects
        similar_projects_completed: Similar projects
        years_in_business: Years in business

    Returns:
        Feature vector [12 features]
    """
    # Financial ratios
    turnover_ratio = (company_turnover / tender_value) if tender_value > 0 else 0
    net_worth_ratio = (company_net_worth / tender_value) if tender_value > 0 else 0

    # Competitiveness
    margin_competitiveness = (market_avg_margin - bid_margin) / market_avg_margin if market_avg_margin > 0 else 0

    # Experience factors
    experience_factor = min(1.0, years_in_business / 20)
    similar_project_ratio = (similar_projects_completed / company_projects_completed) if company_projects_completed > 0 else 0

    return [
        float(turnover_ratio),           # 0: Financial strength
        float(net_worth_ratio),          # 1: Financial buffer
        float(past_win_rate),            # 2: Track record
        float(bid_margin / 100),         # 3: Proposed margin (normalized)
        float(margin_competitiveness),   # 4: Price competitiveness
        float(eligibility_match),        # 5: Eligibility fit
        float(1 - avg_risk_score),       # 6: Risk safety (inverted)
        float(readiness_index / 100),    # 7: Preparation level
        float(experience_factor),        # 8: Business maturity
        float(similar_project_ratio),    # 9: Relevant experience
        float(min(1.0, company_projects_completed / 50)),  # 10: Portfolio size
        float(min(1.0, tender_value / 1e9)),               # 11: Project scale (normalized to $1B)
    ]


# ─────────────────────────────────────────────────────────────────────────────
# Model Training
# ─────────────────────────────────────────────────────────────────────────────

def train_model(X: List[List[float]], y: List[int]) -> None:
    """
    Train RandomForestClassifier on historical bid outcomes.

    Args:
        X: List of feature vectors
        y: List of outcomes (1=Won, 0=Lost)
    """
    try:
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.preprocessing import StandardScaler
        from sklearn.pipeline import Pipeline

        X_arr = np.array(X, dtype=float)
        y_arr = np.array(y, dtype=int)

        model = Pipeline([
            ('scaler', StandardScaler()),
            ('rf', RandomForestClassifier(
                n_estimators=200,
                max_depth=8,
                min_samples_split=10,
                min_samples_leaf=5,
                class_weight='balanced',
                random_state=42,
            )),
        ])

        model.fit(X_arr, y_arr)

        with open(MODEL_PATH, 'wb') as f:
            pickle.dump(model, f)

        logger.info(f"[WinModel] Trained on {len(X)} samples → saved to {MODEL_PATH}")

    except Exception as e:
        logger.exception(f"[WinModel] Training failed: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# Prediction
# ─────────────────────────────────────────────────────────────────────────────

def predict_win_probability(features: List[float]) -> float:
    """
    Predict win probability for a tender bid.

    Args:
        features: Feature vector from build_features_for_tender()

    Returns:
        Win probability (0.0 to 1.0)
    """
    if MODEL_PATH.exists():
        try:
            with open(MODEL_PATH, 'rb') as f:
                model = pickle.load(f)

            features_arr = np.array([features], dtype=float)
            prob = model.predict_proba(features_arr)[0][1]  # Probability of class 1 (Win)

            return min(0.99, max(0.01, float(prob)))

        except Exception as e:
            logger.warning(f"[WinModel] ML prediction failed ({e}), using rule-based")

    # Fallback: rule-based estimate
    return predict_win_probability_rule_based(features)


def predict_win_probability_rule_based(features: List[float]) -> float:
    """
    Rule-based win probability estimation.
    Used when ML model is not available.

    Args:
        features: Feature vector

    Returns:
        Win probability (0.0 to 1.0)
    """
    turnover_ratio = features[0]
    net_worth_ratio = features[1]
    past_win_rate = features[2]
    bid_margin = features[3]
    margin_competitiveness = features[4]
    eligibility_match = features[5]
    risk_safety = features[6]
    readiness = features[7]
    experience_factor = features[8]
    similar_project_ratio = features[9]

    # Weighted scoring
    financial_score = min(1.0, (turnover_ratio * 0.5 + net_worth_ratio * 0.5))
    competitiveness_score = margin_competitiveness * 0.7 + (1 - bid_margin) * 0.3
    preparation_score = readiness * 0.6 + eligibility_match * 0.4
    experience_score = experience_factor * 0.5 + similar_project_ratio * 0.5

    # Final weighted average
    win_prob = (
        financial_score * 0.25 +
        competitiveness_score * 0.30 +
        preparation_score * 0.20 +
        experience_score * 0.15 +
        risk_safety * 0.10
    )

    # Adjust by historical performance
    win_prob = win_prob * 0.7 + past_win_rate * 0.3

    return min(0.95, max(0.05, float(win_prob)))


# ─────────────────────────────────────────────────────────────────────────────
# Synthetic Training Data (Bootstrap)
# ─────────────────────────────────────────────────────────────────────────────

def generate_synthetic_training_data(n: int = 1000) -> Tuple[List[List[float]], List[int]]:
    """
    Generate synthetic training data for bootstrapping the model.

    Args:
        n: Number of samples

    Returns:
        (X, y) tuple
    """
    import random
    random.seed(42)

    X, y = [], []

    for _ in range(n):
        # Generate random features
        turnover_ratio = random.uniform(0.5, 5.0)
        net_worth_ratio = random.uniform(0.1, 2.0)
        past_win_rate = random.uniform(0.1, 0.8)
        bid_margin = random.uniform(0.05, 0.25)
        market_avg_margin = random.uniform(0.10, 0.20)
        margin_competitiveness = (market_avg_margin - bid_margin) / market_avg_margin
        eligibility_match = random.uniform(0.5, 1.0)
        avg_risk_score = random.uniform(0.2, 0.8)
        readiness_index = random.uniform(40, 100)
        experience_factor = random.uniform(0.3, 1.0)
        similar_project_ratio = random.uniform(0.2, 1.0)
        portfolio_size = random.uniform(0.2, 1.0)
        project_scale = random.uniform(0.1, 1.0)

        features = [
            turnover_ratio, net_worth_ratio, past_win_rate, bid_margin,
            margin_competitiveness, eligibility_match, 1 - avg_risk_score,
            readiness_index / 100, experience_factor, similar_project_ratio,
            portfolio_size, project_scale
        ]

        # Label: probabilistic based on features
        base_prob = predict_win_probability_rule_based(features)
        noise = random.gauss(0, 0.1)
        win_prob = min(0.99, max(0.01, base_prob + noise))

        outcome = 1 if random.random() < win_prob else 0

        X.append(features)
        y.append(outcome)

    return X, y


def ensure_model_trained() -> None:
    """Train on synthetic data if no model file exists."""
    if not MODEL_PATH.exists():
        logger.info("[WinModel] No model found, training on synthetic data...")
        X, y = generate_synthetic_training_data(n=2000)
        train_model(X, y)


# ─────────────────────────────────────────────────────────────────────────────
# High-Level API for Tender
# ─────────────────────────────────────────────────────────────────────────────

def calculate_win_probability_for_tender(
    tender,
    company_profile,
    bid_margin: float = 15.0,
    market_avg_margin: float = 12.0,
) -> float:
    """
    Calculate win probability for a tender given company profile.

    Args:
        tender: Tender model instance
        company_profile: CompanyProfile model instance
        bid_margin: Proposed bid margin percentage
        market_avg_margin: Market average margin percentage

    Returns:
        Win probability (0.0 to 1.0)
    """
    from django.db.models import Avg
    from tenders.models import BidActionItem
    from tenders.services.readiness_engine import calculate_readiness

    # Extract features
    tender_value = float(tender.estimated_value or 0)
    company_turnover = float(company_profile.annual_turnover or 0)
    company_net_worth = float(company_profile.net_worth or 0)
    past_win_rate = float(company_profile.past_win_rate or 0.5)

    # Eligibility match (simplified - could be more sophisticated)
    eligibility = tender.eligibility if hasattr(tender, 'eligibility') else None
    eligibility_match = 0.8  # Default
    if eligibility:
        if eligibility.min_turnover and company_turnover < eligibility.min_turnover:
            eligibility_match -= 0.3
        if eligibility.min_net_worth and company_net_worth < eligibility.min_net_worth:
            eligibility_match -= 0.2

    # Risk score
    risks = tender.risks.all() if hasattr(tender, 'risks') else []
    avg_risk_score = sum(r.severity_score for r in risks) / len(risks) if risks else 0.3

    # Readiness
    readiness_report = calculate_readiness(tender)
    readiness_index = readiness_report.get('readiness_index', 50.0)

    features = build_features_for_tender(
        tender_value=tender_value,
        company_turnover=company_turnover,
        company_net_worth=company_net_worth,
        past_win_rate=past_win_rate,
        bid_margin=bid_margin,
        market_avg_margin=market_avg_margin,
        eligibility_match=eligibility_match,
        avg_risk_score=avg_risk_score,
        readiness_index=readiness_index,
        company_projects_completed=company_profile.total_projects_completed or 0,
        similar_projects_completed=company_profile.similar_projects_completed or 0,
        years_in_business=company_profile.years_in_business or 5,
    )

    return predict_win_probability(features)


# Auto-train on startup if needed
ensure_model_trained()
