import { AlertTriangle, TrendingUp } from 'lucide-react';

export default function IntentAlerts({ intentDrift, counterpartyMismatch }) {
  const hasAlerts = intentDrift || counterpartyMismatch?.level === 'HIGH';

  if (!hasAlerts) return null;

  return (
    <div className="mb-6 space-y-3">
      {/* Intent Drift Alert */}
      {intentDrift && (
        <div className="bg-yellow-900/30 border border-yellow-500/50 rounded-lg p-4 flex items-start">
          <TrendingUp className="w-5 h-5 text-yellow-400 mr-3 mt-1 flex-shrink-0" />
          <div>
            <p className="text-yellow-400 font-semibold mb-1">Intent Drift Detected</p>
            <p className="text-gray-300 text-sm">
              This contract's negotiation intent has shifted across versions. Significant changes
              detected in risk transfer, termination leverage, or payment control clauses.
            </p>
          </div>
        </div>
      )}

      {/* Counterparty Mismatch Alert */}
      {counterpartyMismatch?.level === 'HIGH' && (
        <div className="bg-red-900/30 border border-red-500/50 rounded-lg p-4 flex items-start">
          <AlertTriangle className="w-5 h-5 text-red-400 mr-3 mt-1 flex-shrink-0" />
          <div>
            <p className="text-red-400 font-semibold mb-1">
              High Counterparty Bias Detected
            </p>
            <p className="text-gray-300 text-sm">
              This contract shows strong bias toward one party. High levels of risk transfer,
              liability shielding, and termination leverage detected. Consider negotiation strategy
              adjustment.
            </p>
            <p className="text-gray-400 text-xs mt-2">
              Bias Score: {(counterpartyMismatch.score * 100).toFixed(0)}%
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
