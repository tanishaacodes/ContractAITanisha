import { useState, useEffect } from 'react';
import { DollarSign, TrendingDown, AlertTriangle, Shield, BarChart3 } from 'lucide-react';
import { getCFOMetrics } from '../services/searchIntelligence';

const fmtVal = (v) => {
  if (!v || v === 0) return '$0';
  if (v >= 1e9) return `$${(v/1e9).toFixed(1)}B`;
  if (v >= 1e6) return `$${(v/1e6).toFixed(1)}M`;
  if (v >= 1e3) return `$${(v/1e3).toFixed(0)}K`;
  return `$${v.toFixed(0)}`;
};

function CFOFinancialMetricsPanel() {
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadReport();
  }, []);

  const loadReport = async () => {
    setLoading(true);
    try {
      const data = await getCFOMetrics('report');
      setReport(data.report);
    } catch (error) {
      console.error('CFO metrics error:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="bg-slate-800/60 border border-slate-700/50 rounded-xl p-8 text-center">
        <div className="inline-block w-8 h-8 border-3 border-emerald-500 border-t-transparent rounded-full animate-spin mb-3" />
        <div className="text-slate-400 text-sm">Loading CFO metrics...</div>
      </div>
    );
  }

  if (!report) return null;

  const summary = report.portfolio_summary || {};
  const var95 = report.value_at_risk?.var_95 || {};
  const riskMetrics = report.risk_metrics || {};
  const topRisks = report.top_risk_contributors || [];

  return (
    <div className="bg-slate-800/60 border border-slate-700/50 rounded-xl p-5 space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-white font-semibold flex items-center gap-2">
            <DollarSign size={16} className="text-emerald-400" />
            CFO Financial Risk Metrics
          </h3>
          <p className="text-slate-400 text-xs mt-1">Expected Loss, VaR, and Portfolio Risk Exposure</p>
        </div>
        <button onClick={loadReport} className="px-3 py-1.5 bg-slate-700 text-slate-300 text-xs rounded-lg hover:bg-slate-600 transition">
          Refresh
        </button>
      </div>

      <div className="grid grid-cols-4 gap-3">
        <div className="bg-slate-900/50 border border-slate-700/30 rounded-lg p-3">
          <div className="text-xs text-slate-400 mb-1">Portfolio Value</div>
          <div className="text-lg font-bold text-emerald-400">{fmtVal(summary.total_portfolio_value)}</div>
        </div>
        <div className="bg-slate-900/50 border border-slate-700/30 rounded-lg p-3">
          <div className="text-xs text-slate-400 mb-1">Expected Loss</div>
          <div className="text-lg font-bold text-red-400">{fmtVal(summary.total_expected_loss)}</div>
        </div>
        <div className="bg-slate-900/50 border border-slate-700/30 rounded-lg p-3">
          <div className="text-xs text-slate-400 mb-1">VaR (95%)</div>
          <div className="text-lg font-bold text-orange-400">{fmtVal(var95.var)}
          </div>
        </div>
        <div className="bg-slate-900/50 border border-slate-700/30 rounded-lg p-3">
          <div className="text-xs text-slate-400 mb-1">Risk Discount</div>
          <div className="text-lg font-bold text-yellow-400">
            {summary.portfolio_discount_rate?.toFixed(2)}%
          </div>
        </div>
      </div>

      <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-lg p-4">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-xs text-emerald-400 mb-1">Risk-Adjusted Portfolio Value</div>
            <div className="text-2xl font-bold text-emerald-300">{fmtVal(summary.risk_adjusted_portfolio_value)}</div>
          </div>
          <TrendingDown size={32} className="text-emerald-400 opacity-50" />
        </div>
      </div>

      {topRisks.length > 0 && (
        <div className="space-y-2">
          <div className="text-sm text-white font-semibold flex items-center gap-2">
            <AlertTriangle size={14} className="text-red-400" />
            Top Risk Contributors
          </div>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {topRisks.slice(0, 5).map((risk, i) => (
              <div key={i} className="bg-slate-900/50 border border-slate-700/30 rounded-lg p-3 flex items-center justify-between">
                <div className="flex-1 min-w-0">
                  <div className="text-sm text-white truncate">{risk.title}</div>
                  <div className="text-xs text-slate-400 mt-1">
                    Value: {fmtVal(risk.value)} · Risk: {(risk.risk_score * 100).toFixed(0)}%
                  </div>
                </div>
                <div className="text-right ml-3">
                  <div className="text-xs text-slate-400">Expected Loss</div>
                  <div className="text-sm font-bold text-red-400">{fmtVal(risk.expected_loss)}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="grid grid-cols-2 gap-3">
        <div className="bg-slate-900/50 border border-slate-700/30 rounded-lg p-3">
          <div className="flex items-center gap-2 mb-2">
            <Shield size={14} className="text-cyan-400" />
            <span className="text-sm text-white font-medium">Risk Profile</span>
          </div>
          <div className="space-y-1 text-xs">
            <div className="flex justify-between">
              <span className="text-slate-400">High Risk Contracts:</span>
              <span className="text-white font-medium">{riskMetrics.high_risk_contracts}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">High Risk Exposure:</span>
              <span className="text-white font-medium">{fmtVal(riskMetrics.high_risk_exposure)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Avg Risk Score:</span>
              <span className="text-white font-medium">{(riskMetrics.average_risk_score * 100).toFixed(1)}%</span>
            </div>
          </div>
        </div>

        <div className="bg-slate-900/50 border border-slate-700/30 rounded-lg p-3">
          <div className="flex items-center gap-2 mb-2">
            <BarChart3 size={14} className="text-blue-400" />
            <span className="text-sm text-white font-medium">VaR Analysis</span>
          </div>
          <div className="space-y-1 text-xs">
            <div className="flex justify-between">
              <span className="text-slate-400">VaR 99%:</span>
              <span className="text-white font-medium">{fmtVal(report.value_at_risk?.var_99?.var)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Expected Shortfall:</span>
              <span className="text-white font-medium">{fmtVal(var95.expected_shortfall)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Max Single Loss:</span>
              <span className="text-white font-medium">{fmtVal(var95.max_single_loss)}</span>
            </div>
          </div>
        </div>
      </div>

      {report.recommendations && report.recommendations.length > 0 && (
        <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4">
          <div className="text-sm text-blue-400 font-semibold mb-2">CFO Recommendations</div>
          <ul className="space-y-1 text-xs text-blue-300">
            {report.recommendations.map((rec, i) => (
              <li key={i} className="flex items-start gap-2">
                <span className="text-blue-500 shrink-0">•</span>
                <span>{rec}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export default CFOFinancialMetricsPanel;
