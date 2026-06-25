"""
Temporal Analysis and Anomaly Detection for Smart Search
Tracks risk evolution over time and detects outlier contracts/clauses
"""
import numpy as np
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta
from collections import defaultdict
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler


class TemporalRiskAnalyzer:
    """
    Analyzes risk evolution over time for contracts and clauses.
    Tracks trends, detects drift, and predicts future risk levels.
    """

    def __init__(self):
        """Initialize temporal analyzer."""
        self.risk_history = defaultdict(list)  # contract_id -> [(timestamp, risk_score)]
        self.clause_history = defaultdict(list)  # clause_id -> [(timestamp, risk_score)]

    def add_risk_snapshot(
        self,
        contract_id: int,
        risk_score: float,
        timestamp: Optional[datetime] = None
    ):
        """
        Add a risk score snapshot for temporal tracking.

        Args:
            contract_id: Contract ID
            risk_score: Risk score at this point in time
            timestamp: When the risk was measured (defaults to now)
        """
        if timestamp is None:
            timestamp = datetime.now()

        self.risk_history[contract_id].append((timestamp, risk_score))

    def get_risk_trend(
        self,
        contract_id: int,
        days_back: int = 90
    ) -> Dict[str, any]:
        """
        Analyze risk trend for a contract.

        Args:
            contract_id: Contract ID
            days_back: How many days of history to analyze

        Returns:
            Dict with trend analysis
        """
        if contract_id not in self.risk_history:
            return {'error': 'No risk history found'}

        history = self.risk_history[contract_id]
        cutoff_date = datetime.now() - timedelta(days=days_back)

        # Filter to recent history
        recent_history = [(ts, score) for ts, score in history if ts >= cutoff_date]

        if len(recent_history) < 2:
            return {'error': 'Insufficient historical data'}

        # Extract scores
        timestamps = [ts.timestamp() for ts, _ in recent_history]
        scores = [score for _, score in recent_history]

        # Calculate trend
        z = np.polyfit(timestamps, scores, 1)
        slope = z[0]

        # Determine trend direction
        if slope > 0.01:
            trend = 'INCREASING'
            severity = 'HIGH' if slope > 0.05 else 'MEDIUM'
        elif slope < -0.01:
            trend = 'DECREASING'
            severity = 'LOW'
        else:
            trend = 'STABLE'
            severity = 'MEDIUM'

        # Calculate volatility
        volatility = np.std(scores)

        return {
            'contract_id': contract_id,
            'trend': trend,
            'slope': float(slope),
            'severity': severity,
            'current_risk': scores[-1],
            'risk_change': scores[-1] - scores[0],
            'volatility': float(volatility),
            'data_points': len(recent_history),
            'time_range_days': days_back,
            'timestamps': [ts.isoformat() for ts, _ in recent_history],
            'risk_scores': scores
        }

    def predict_future_risk(
        self,
        contract_id: int,
        days_forward: int = 30
    ) -> Dict[str, any]:
        """
        Predict future risk score using linear extrapolation.

        Args:
            contract_id: Contract ID
            days_forward: How many days to predict forward

        Returns:
            Dict with prediction
        """
        trend_data = self.get_risk_trend(contract_id, days_back=90)

        if 'error' in trend_data:
            return trend_data

        slope = trend_data['slope']
        current_risk = trend_data['current_risk']

        # Extrapolate (days_forward * seconds_per_day * slope)
        predicted_risk = current_risk + (days_forward * 86400 * slope)

        # Clamp to [0, 1]
        predicted_risk = max(0.0, min(1.0, predicted_risk))

        # Confidence decreases with time
        confidence = 1.0 - (days_forward / 90.0)
        confidence = max(0.1, confidence)

        return {
            'contract_id': contract_id,
            'current_risk': current_risk,
            'predicted_risk': float(predicted_risk),
            'days_forward': days_forward,
            'confidence': float(confidence),
            'trend': trend_data['trend'],
            'slope': slope,
            'warning': predicted_risk > 0.7
        }

    def detect_risk_spike(
        self,
        contract_id: int,
        threshold: float = 0.15
    ) -> Optional[Dict]:
        """
        Detect sudden risk spikes (anomalies in time series).

        Args:
            contract_id: Contract ID
            threshold: Minimum change to be considered a spike

        Returns:
            Dict with spike info if detected, None otherwise
        """
        if contract_id not in self.risk_history or len(self.risk_history[contract_id]) < 2:
            return None

        history = self.risk_history[contract_id]
        latest_score = history[-1][1]
        previous_score = history[-2][1]

        change = latest_score - previous_score

        if abs(change) >= threshold:
            return {
                'contract_id': contract_id,
                'spike_detected': True,
                'direction': 'UP' if change > 0 else 'DOWN',
                'magnitude': float(abs(change)),
                'previous_risk': previous_score,
                'current_risk': latest_score,
                'timestamp': history[-1][0].isoformat(),
                'severity': 'CRITICAL' if abs(change) > 0.3 else 'HIGH'
            }

        return None

    def get_contracts_with_drift(
        self,
        min_drift: float = 0.2,
        days_back: int = 90
    ) -> List[Dict]:
        """
        Find all contracts with significant risk drift.

        Args:
            min_drift: Minimum drift to include
            days_back: Time window to analyze

        Returns:
            List of contracts with drift info
        """
        drifting_contracts = []

        for contract_id in self.risk_history.keys():
            trend = self.get_risk_trend(contract_id, days_back=days_back)

            if 'error' not in trend and abs(trend.get('risk_change', 0)) >= min_drift:
                drifting_contracts.append({
                    'contract_id': contract_id,
                    'drift': trend['risk_change'],
                    'trend': trend['trend'],
                    'current_risk': trend['current_risk'],
                    'volatility': trend['volatility']
                })

        # Sort by drift magnitude
        drifting_contracts.sort(key=lambda x: abs(x['drift']), reverse=True)

        return drifting_contracts


class AnomalyDetector:
    """
    Detects anomalous contracts and clauses using Isolation Forest.
    Identifies outliers in risk profiles, clause patterns, and metadata.
    """

    def __init__(self, contamination: float = 0.1):
        """
        Initialize anomaly detector.

        Args:
            contamination: Expected proportion of outliers (0.0-0.5)
        """
        self.contamination = contamination
        self.model = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_estimators=100
        )
        self.scaler = StandardScaler()
        self.is_fitted = False

    def fit(self, contracts: List[Dict]):
        """
        Fit anomaly detector on contract portfolio.

        Args:
            contracts: List of contract dicts with numerical features
        """
        if not contracts:
            return

        # Extract features
        features = []
        for contract in contracts:
            feature_vector = [
                contract.get('risk_score', 0),
                contract.get('liability_score', 0),
                contract.get('fm_risk_score', 0),
                contract.get('num_clauses', 0),
                contract.get('contract_value', 0) / 1000000,  # Scale to millions
                len(contract.get('high_risk_clauses', [])),
                contract.get('obligation_count', 0)
            ]
            features.append(feature_vector)

        X = np.array(features)

        # Scale features
        X_scaled = self.scaler.fit_transform(X)

        # Fit Isolation Forest
        self.model.fit(X_scaled)
        self.is_fitted = True

        print(f"✅ Anomaly detector fitted on {len(contracts)} contracts")

    def detect_anomalies(self, contracts: List[Dict]) -> List[Dict]:
        """
        Detect anomalous contracts in the portfolio.

        Args:
            contracts: List of contract dicts

        Returns:
            List of anomalous contracts with anomaly scores
        """
        if not self.is_fitted:
            print("⚠️  Detector not fitted. Call fit() first.")
            return []

        if not contracts:
            return []

        # Extract features (same as fit)
        contract_ids = []
        features = []

        for contract in contracts:
            contract_ids.append(contract.get('id', 0))
            feature_vector = [
                contract.get('risk_score', 0),
                contract.get('liability_score', 0),
                contract.get('fm_risk_score', 0),
                contract.get('num_clauses', 0),
                contract.get('contract_value', 0) / 1000000,
                len(contract.get('high_risk_clauses', [])),
                contract.get('obligation_count', 0)
            ]
            features.append(feature_vector)

        X = np.array(features)
        X_scaled = self.scaler.transform(X)

        # Predict anomalies (-1 = anomaly, 1 = normal)
        predictions = self.model.predict(X_scaled)

        # Get anomaly scores (lower = more anomalous)
        anomaly_scores = self.model.score_samples(X_scaled)

        # Filter anomalies
        anomalies = []
        for i, (contract_id, pred, score) in enumerate(zip(contract_ids, predictions, anomaly_scores)):
            if pred == -1:  # Anomaly detected
                anomalies.append({
                    'contract_id': contract_id,
                    'anomaly_score': float(score),
                    'severity': 'HIGH' if score < -0.5 else 'MEDIUM',
                    'reason': self._explain_anomaly(contracts[i]),
                    'contract_data': contracts[i]
                })

        # Sort by anomaly score
        anomalies.sort(key=lambda x: x['anomaly_score'])

        return anomalies

    def _explain_anomaly(self, contract: Dict) -> str:
        """Generate human-readable explanation for why contract is anomalous."""
        reasons = []

        risk_score = contract.get('risk_score', 0)
        if risk_score > 0.8:
            reasons.append(f"Very high risk score ({risk_score:.2f})")
        elif risk_score < 0.1:
            reasons.append(f"Unusually low risk score ({risk_score:.2f})")

        num_clauses = contract.get('num_clauses', 0)
        if num_clauses > 50:
            reasons.append(f"Unusually high clause count ({num_clauses})")
        elif num_clauses < 3:
            reasons.append(f"Unusually low clause count ({num_clauses})")

        contract_value = contract.get('contract_value', 0)
        if contract_value > 10000000:
            reasons.append(f"Very high contract value (${contract_value/1000000:.1f}M)")
        elif contract_value < 1000:
            reasons.append(f"Very low contract value (${contract_value})")

        fm_risk = contract.get('fm_risk_score', 0)
        if fm_risk > 0.7:
            reasons.append(f"High Force Majeure risk ({fm_risk:.2f})")

        if not reasons:
            reasons.append("Atypical combination of features")

        return " | ".join(reasons)

    def get_anomaly_report(self, contracts: List[Dict]) -> Dict:
        """
        Generate comprehensive anomaly report.

        Args:
            contracts: List of contract dicts

        Returns:
            Dict with anomaly statistics and detected outliers
        """
        if not self.is_fitted:
            self.fit(contracts)

        anomalies = self.detect_anomalies(contracts)

        return {
            'total_contracts': len(contracts),
            'anomalies_detected': len(anomalies),
            'anomaly_rate': len(anomalies) / len(contracts) if contracts else 0,
            'high_severity': len([a for a in anomalies if a['severity'] == 'HIGH']),
            'medium_severity': len([a for a in anomalies if a['severity'] == 'MEDIUM']),
            'anomalies': anomalies[:10],  # Top 10 most anomalous
            'summary': f"Detected {len(anomalies)} anomalous contracts out of {len(contracts)} total ({100*len(anomalies)/len(contracts) if contracts else 0:.1f}%)"
        }


# Singleton instances
_temporal_analyzer = None
_anomaly_detector = None

def get_temporal_analyzer() -> TemporalRiskAnalyzer:
    """Get or create temporal analyzer singleton."""
    global _temporal_analyzer
    if _temporal_analyzer is None:
        _temporal_analyzer = TemporalRiskAnalyzer()
    return _temporal_analyzer

def get_anomaly_detector() -> AnomalyDetector:
    """Get or create anomaly detector singleton."""
    global _anomaly_detector
    if _anomaly_detector is None:
        _anomaly_detector = AnomalyDetector()
    return _anomaly_detector
