"""
Predictive Risk Engine
======================
Forecasts future clause risk scores using:
1. Linear trend regression (always available, fast)
2. XGBoost if installed
3. Simple exponential smoothing as fallback

Inputs:  Historical clause risk_score values per clause_type + date
Outputs: 6-month forward forecast with confidence intervals
"""

import logging
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


def _linear_forecast(y: List[float], horizon: int = 6) -> Dict:
    """Least-squares linear forecast."""
    n = len(y)
    x = np.arange(n, dtype=float)
    if n < 2:
        last = y[-1] if y else 0.5
        return {
            'forecast': [last] * horizon,
            'lower': [max(0, last - 0.1)] * horizon,
            'upper': [min(1, last + 0.1)] * horizon,
            'method': 'constant',
        }
    m, b = np.polyfit(x, y, 1)
    forecast = [float(np.clip(m * (n + i) + b, 0.0, 1.0)) for i in range(horizon)]
    residuals = np.std(y)
    return {
        'forecast': forecast,
        'lower': [max(0, f - residuals) for f in forecast],
        'upper': [min(1, f + residuals) for f in forecast],
        'method': 'linear',
    }


def _xgb_forecast(y: List[float], horizon: int = 6) -> Dict:
    """XGBoost time-series forecast using lag features."""
    try:
        import xgboost as xgb
    except ImportError:
        return None

    if len(y) < 4:
        return None

    try:
        LAG = min(3, len(y) - 1)
        X, Y = [], []
        for i in range(LAG, len(y)):
            X.append(y[i - LAG:i])
            Y.append(y[i])
        X, Y = np.array(X), np.array(Y)

        model = xgb.XGBRegressor(n_estimators=50, max_depth=3, verbosity=0)
        model.fit(X, Y)

        window = list(y[-LAG:])
        forecast = []
        for _ in range(horizon):
            pred = float(np.clip(model.predict(np.array([window]))[0], 0.0, 1.0))
            forecast.append(pred)
            window = window[1:] + [pred]

        residuals = float(np.std(np.abs(model.predict(X) - Y)))
        return {
            'forecast': forecast,
            'lower': [max(0, f - residuals) for f in forecast],
            'upper': [min(1, f + residuals) for f in forecast],
            'method': 'xgboost',
        }
    except Exception as e:
        logger.warning(f"XGBoost forecast failed: {e}")
        return None


def _exp_smoothing(y: List[float], horizon: int = 6, alpha: float = 0.3) -> Dict:
    """Exponential smoothing forecast."""
    if not y:
        return {'forecast': [0.5] * horizon, 'lower': [0.4] * horizon, 'upper': [0.6] * horizon, 'method': 'exp_smoothing'}
    smoothed = y[0]
    for val in y[1:]:
        smoothed = alpha * val + (1 - alpha) * smoothed
    forecast = [float(np.clip(smoothed, 0, 1))] * horizon
    std = float(np.std(y)) if len(y) > 1 else 0.05
    return {
        'forecast': forecast,
        'lower': [max(0, f - std) for f in forecast],
        'upper': [min(1, f + std) for f in forecast],
        'method': 'exp_smoothing',
    }


def forecast_risk(y: List[float], horizon: int = 6) -> Dict:
    """
    Best-available forecast: try XGBoost → linear → exp smoothing.
    """
    if len(y) >= 4:
        result = _xgb_forecast(y, horizon)
        if result:
            return result
    if len(y) >= 2:
        return _linear_forecast(y, horizon)
    return _exp_smoothing(y, horizon)


class PredictiveRiskEngine:
    """
    Loads historical risk scores per clause type from MySQL and generates forecasts.
    """

    def get_history(self, clause_type: str, user=None) -> List[Dict]:
        """
        Returns monthly avg risk score for a clause type, sorted by date.
        """
        from core.models import Clause
        from django.db.models.functions import TruncMonth
        from django.db.models import Avg

        qs = Clause.objects.filter(
            clause_type=clause_type,
            risk_score__isnull=False,
        ).exclude(risk_score=0)
        if user:
            qs = qs.filter(contract__user=user)

        monthly = qs.annotate(
            month=TruncMonth('contract__created_at')
        ).values('month').annotate(
            avg_risk=Avg('risk_score')
        ).order_by('month')

        return [
            {
                'month': row['month'].strftime('%Y-%m') if row['month'] else None,
                'avg_risk': round(float(row['avg_risk']), 4),
            }
            for row in monthly if row['month']
        ]

    def forecast_clause_type(self, clause_type: str, user=None, horizon: int = 6) -> Dict:
        """
        Forecast risk for a specific clause type for the next `horizon` months.
        """
        history = self.get_history(clause_type, user)
        if not history:
            return {
                'clause_type': clause_type,
                'history': [],
                'forecast': [],
                'method': 'no_data',
                'error': 'No historical data',
            }

        y = [h['avg_risk'] for h in history]
        forecast_result = forecast_risk(y, horizon=horizon)

        # Generate future month labels
        last_month = history[-1]['month']
        base = datetime.strptime(last_month, '%Y-%m')
        future_months = [(base + timedelta(days=30 * (i + 1))).strftime('%Y-%m') for i in range(horizon)]

        forecast_with_labels = [
            {
                'month': future_months[i],
                'predicted_risk': round(forecast_result['forecast'][i], 4),
                'lower': round(forecast_result['lower'][i], 4),
                'upper': round(forecast_result['upper'][i], 4),
            }
            for i in range(horizon)
        ]

        # Trend direction
        if len(y) >= 2:
            trend = 'increasing' if y[-1] > y[0] else 'decreasing' if y[-1] < y[0] else 'stable'
        else:
            trend = 'stable'

        avg_forecast = np.mean(forecast_result['forecast'])
        risk_outlook = 'HIGH' if avg_forecast > 0.7 else 'MEDIUM' if avg_forecast > 0.4 else 'LOW'

        return {
            'clause_type': clause_type,
            'history': history,
            'forecast': forecast_with_labels,
            'method': forecast_result['method'],
            'trend': trend,
            'risk_outlook': risk_outlook,
            'current_avg_risk': round(y[-1], 4) if y else 0,
            'forecast_avg_risk': round(float(avg_forecast), 4),
        }

    def forecast_all_types(self, user=None, horizon: int = 6) -> List[Dict]:
        """
        Forecast all clause types for a user. Returns top results sorted by forecast risk.
        """
        from core.models import Clause
        clause_types = list(
            Clause.objects.filter(
                risk_score__isnull=False
            ).exclude(clause_type__isnull=True).exclude(clause_type='')
        )
        seen = set()
        unique_types = []
        for c in clause_types:
            if c.clause_type not in seen:
                seen.add(c.clause_type)
                unique_types.append(c.clause_type)
        if user:
            unique_types = list(
                Clause.objects.filter(
                    contract__user=user
                ).exclude(clause_type__isnull=True).exclude(clause_type='')
                .values_list('clause_type', flat=True).distinct()
            )

        results = []
        for ctype in unique_types[:20]:  # Limit for performance
            r = self.forecast_clause_type(ctype, user=user, horizon=horizon)
            if 'error' not in r:
                results.append(r)

        results.sort(key=lambda x: x.get('forecast_avg_risk', 0), reverse=True)
        return results


_engine = None


def get_predictive_risk_engine() -> PredictiveRiskEngine:
    global _engine
    if _engine is None:
        _engine = PredictiveRiskEngine()
    return _engine
