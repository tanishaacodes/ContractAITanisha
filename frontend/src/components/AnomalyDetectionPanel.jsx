import { useState, useEffect } from 'react';
import { AlertTriangle, Shield, FileText, DollarSign, AlertCircle } from 'lucide-react';
import { detectAnomalies } from '../services/searchIntelligence';

function AnomalyDetectionPanel({ onContractClick }) {
  const [anomalies, setAnomalies] = useState([]);
  const [loading, setLoading] = useState(false);
  const [totalCount, setTotalCount] = useState(0);

  useEffect(() => {
    loadAnomalies();
  }, []);

  const loadAnomalies = async () => {
    setLoading(true);
    try {
      const data = await detectAnomalies();
      setAnomalies(data.anomalies || []);
      setTotalCount(data.count || 0);
    } catch (error) {
      console.error('Anomaly detection error:', error);
    } finally {
      setLoading(false);
    }
  };

  const getSeverityColor = (severity) => {
    if (severity === 'HIGH') return 'border-red-500/40 bg-red-500/10 text-red-400';
    if (severity === 'MEDIUM') return 'border-orange-500/40 bg-orange-500/10 text-orange-400';
    return 'border-yellow-500/40 bg-yellow-500/10 text-yellow-400';
  };

  const getScoreColor = (score) => {
    // Lower (more negative) scores are more anomalous
    if (score < -0.5) return 'text-red-400';
    if (score < -0.2) return 'text-orange-400';
    return 'text-yellow-400';
  };

  if (loading) {
    return (
      <div className="bg-slate-800/60 border border-slate-700/50 rounded-xl p-8 text-center">
        <div className="inline-block w-8 h-8 border-3 border-cyan-500 border-t-transparent rounded-full animate-spin mb-3" />
        <div className="text-slate-400 text-sm">Detecting anomalies...</div>
        <div className="text-slate-500 text-xs mt-1">Analyzing contract portfolio using Isolation Forest</div>
      </div>
    );
  }

  return (
    <div className="bg-slate-800/60 border border-slate-700/50 rounded-xl p-5">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-white font-semibold flex items-center gap-2">
            <AlertCircle size={16} className="text-red-400" />
            Anomaly Detection
          </h3>
          <p className="text-slate-400 text-xs mt-1">
            {totalCount > 0 ? `Found ${totalCount} anomalous contracts` : 'No anomalies detected'}
          </p>
        </div>
        <button
          onClick={loadAnomalies}
          className="px-3 py-1.5 bg-slate-700 text-slate-300 text-xs rounded-lg hover:bg-slate-600 transition"
        >
          Refresh
        </button>
      </div>

      {anomalies.length === 0 ? (
        <div className="text-center py-8">
          <Shield size={32} className="text-emerald-600 mx-auto mb-3" />
          <div className="text-slate-400 text-sm">No anomalous contracts detected</div>
          <div className="text-slate-500 text-xs mt-1">Your portfolio appears normal</div>
        </div>
      ) : (
        <div className="space-y-3 max-h-[500px] overflow-y-auto">
          {anomalies.map((anomaly, idx) => {
            const contract = anomaly.contract_data;
            return (
              <div
                key={idx}
                onClick={() => onContractClick && onContractClick(anomaly.contract_id)}
                className={`border rounded-lg p-4 cursor-pointer transition hover:border-opacity-70 ${getSeverityColor(anomaly.severity)}`}
              >
                {/* Header */}
                <div className="flex items-start justify-between gap-3 mb-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <FileText size={14} className="shrink-0" />
                      <span className="text-white text-sm font-medium">
                        {anomaly.contract_title || `Contract #${anomaly.contract_id?.slice(0,8)}`}
                      </span>
                      <span className={`px-2 py-0.5 text-xs rounded-full border ${getSeverityColor(anomaly.severity)}`}>
                        {anomaly.severity}
                      </span>
                    </div>
                    <div className="text-xs opacity-90">{anomaly.reason}</div>
                  </div>
                  <div className="text-right shrink-0">
                    <div className="text-xs text-slate-400">Anomaly Score</div>
                    <div className={`text-lg font-bold ${getScoreColor(anomaly.anomaly_score)}`}>
                      {anomaly.anomaly_score.toFixed(2)}
                    </div>
                  </div>
                </div>

                {/* Contract Details */}
                <div className="grid grid-cols-2 gap-3 text-xs mt-3 pt-3 border-t border-current/20">
                  <div className="flex items-center gap-2">
                    <Shield size={12} className="opacity-70" />
                    <span className="text-slate-400">Risk Score:</span>
                    <span className="font-medium">{(contract.risk_score * 100).toFixed(1)}%</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <FileText size={12} className="opacity-70" />
                    <span className="text-slate-400">Clauses:</span>
                    <span className="font-medium">{contract.num_clauses}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <DollarSign size={12} className="opacity-70" />
                    <span className="text-slate-400">Value:</span>
                    <span className="font-medium">
                      {contract.contract_value > 1000000
                        ? `$${(contract.contract_value / 1000000).toFixed(1)}M`
                        : contract.contract_value > 1000
                        ? `$${(contract.contract_value / 1000).toFixed(0)}k`
                        : `$${contract.contract_value}`}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <AlertTriangle size={12} className="opacity-70" />
                    <span className="text-slate-400">Liability:</span>
                    <span className="font-medium">{(contract.liability_score * 100).toFixed(0)}%</span>
                  </div>
                </div>

                {/* Explanation */}
                {anomaly.reason && (
                  <div className="mt-3 pt-3 border-t border-current/20">
                    <div className="text-xs text-slate-400 mb-1">Why anomalous:</div>
                    <div className="text-xs opacity-90 leading-relaxed">
                      {anomaly.reason}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Summary Statistics */}
      {totalCount > 0 && (
        <div className="mt-4 pt-4 border-t border-slate-700/50">
          <div className="grid grid-cols-3 gap-3 text-center text-xs">
            <div>
              <div className="text-slate-400 mb-1">Total Detected</div>
              <div className="text-white font-semibold text-lg">{totalCount}</div>
            </div>
            <div>
              <div className="text-slate-400 mb-1">High Severity</div>
              <div className="text-red-400 font-semibold text-lg">
                {anomalies.filter(a => a.severity === 'HIGH').length}
              </div>
            </div>
            <div>
              <div className="text-slate-400 mb-1">Medium Severity</div>
              <div className="text-orange-400 font-semibold text-lg">
                {anomalies.filter(a => a.severity === 'MEDIUM').length}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default AnomalyDetectionPanel;
