import { useEffect, useState } from "react";
import { TrendingUp, AlertTriangle, DollarSign, Target, Activity, Info, CheckCircle, XCircle, AlertCircle } from "lucide-react";
import api from "../utils/api";
import useThemeStore from "../store/themeStore";

const PortfolioRiskIntelligence = ({ contractId }) => {
  const { theme } = useThemeStore();
  const [riskData, setRiskData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchRiskIntelligence = async () => {
      try {
        setLoading(true);
        const res = await api.get(`/contracts/${contractId}/portfolio-risk-detail`);

        if (res.data.success) {
          setRiskData(res.data.data);
        } else {
          setError(res.data.error || "Failed to load portfolio risk intelligence");
        }
      } catch (err) {
        setError(err.response?.data?.error || "Failed to load portfolio risk intelligence");
      } finally {
        setLoading(false);
      }
    };

    fetchRiskIntelligence();
  }, [contractId]);

  if (loading) {
    return (
      <div className={`text-center ${theme.colors.textSecondary} py-10`}>
        Loading Portfolio Risk Intelligence...
      </div>
    );
  }

  if (error) {
    return (
      <div className={`p-4 rounded-lg border ${theme.colors.surfaceBorder} ${theme.colors.surface}`}>
        <div className="flex items-center gap-2 text-red-400">
          <AlertTriangle size={20} />
          <span>{error}</span>
        </div>
      </div>
    );
  }

  if (!riskData || !riskData.contract.has_counterparty) {
    return (
      <div className="rounded-xl p-6" style={{
        border: '1px solid rgba(234,179,8,0.3)',
        background: 'rgba(15,23,42,0.88)',
        boxShadow: '0 0 18px rgba(234,179,8,0.08), inset 0 1px 0 rgba(234,179,8,0.06)',
      }}>
        <div className="flex items-center gap-2 mb-3" style={{ color: '#facc15' }}>
          <Info size={18} />
          <h3 className="text-sm font-bold tracking-wide uppercase">No Counterparty Data</h3>
        </div>
        <p className="text-slate-400 text-sm leading-relaxed">
          This contract does not have a counterparty linked. Portfolio risk intelligence requires counterparty data to generate exposure and correlation analysis.
        </p>
      </div>
    );
  }

  const formatCurrency = (value) => {
    if (value >= 10000000) {
      return `Rs ${(value / 10000000).toFixed(2)} Cr`;
    } else if (value >= 100000) {
      return `Rs ${(value / 100000).toFixed(2)} L`;
    } else {
      return `Rs ${value.toLocaleString()}`;
    }
  };

  const getQuadrantColor = (quadrant) => {
    switch (quadrant) {
      case 'IMMEDIATE_ACTION':
        return 'text-red-400 bg-red-500/10 border-red-500/30';
      case 'MONITOR':
        return 'text-yellow-400 bg-yellow-500/10 border-yellow-500/30';
      case 'REVIEW':
        return 'text-orange-400 bg-orange-500/10 border-orange-500/30';
      case 'SAFE':
        return 'text-green-400 bg-green-500/10 border-green-500/30';
      default:
        return 'text-gray-400 bg-gray-500/10 border-gray-500/30';
    }
  };

  const getPriorityIcon = (priority) => {
    switch (priority) {
      case 'CRITICAL':
        return <XCircle size={16} className="text-red-400" />;
      case 'HIGH':
        return <AlertCircle size={16} className="text-orange-400" />;
      case 'MEDIUM':
        return <AlertCircle size={16} className="text-yellow-400" />;
      case 'LOW':
        return <Info size={16} className="text-blue-400" />;
      case 'INFO':
        return <CheckCircle size={16} className="text-green-400" />;
      default:
        return <Info size={16} className="text-gray-400" />;
    }
  };

  const getRiskLevelColor = (level) => {
    switch (level) {
      case 'HIGH':
        return 'text-red-400';
      case 'MEDIUM':
        return 'text-yellow-400';
      case 'LOW':
        return 'text-green-400';
      default:
        return 'text-gray-400';
    }
  };

  return (
    <div className="space-y-6">
      {/* Executive Summary Card */}
      <div className={`p-6 rounded-lg border ${theme.colors.surfaceBorder} ${theme.colors.surface}`}>
        <div className="flex items-center gap-2 mb-4">
          <Target size={24} className="text-blue-400" />
          <h3 className={`text-xl font-bold ${theme.colors.textPrimary}`}>Executive Risk Summary</h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Risk Quadrant */}
          <div className={`p-4 rounded-lg border ${getQuadrantColor(riskData.risk_quadrant)}`}>
            <div className="text-sm font-medium mb-1">Risk Quadrant</div>
            <div className="text-2xl font-bold">{riskData.risk_quadrant.replace('_', ' ')}</div>
          </div>

          {/* Reliability Score */}
          <div className={`p-4 rounded-lg border ${theme.colors.surfaceBorder} bg-blue-500/10`}>
            <div className="text-sm text-gray-400 mb-1">Counterparty Reliability</div>
            <div className="text-2xl font-bold text-blue-400">
              {(riskData.reliability_breakdown.overall_score * 100).toFixed(1)}%
            </div>
          </div>

          {/* Total Exposure */}
          <div className={`p-4 rounded-lg border ${theme.colors.surfaceBorder} bg-purple-500/10`}>
            <div className="text-sm text-gray-400 mb-1">Financial Exposure</div>
            <div className="text-2xl font-bold text-purple-400">
              {formatCurrency(riskData.financial_exposure.total)}
            </div>
          </div>

          {/* Failure Probability */}
          <div className={`p-4 rounded-lg border ${theme.colors.surfaceBorder} bg-red-500/10`}>
            <div className="text-sm text-gray-400 mb-1">Failure Probability</div>
            <div className={`text-2xl font-bold ${getRiskLevelColor(riskData.failure_analysis.risk_level)}`}>
              {(riskData.failure_analysis.probability * 100).toFixed(1)}%
            </div>
          </div>
        </div>
      </div>

      {/* Counterparty Intelligence */}
      <div className={`p-6 rounded-lg border ${theme.colors.surfaceBorder} ${theme.colors.surface}`}>
        <div className="flex items-center gap-2 mb-4">
          <Activity size={24} className="text-green-400" />
          <h3 className={`text-xl font-bold ${theme.colors.textPrimary}`}>Counterparty Intelligence</h3>
        </div>

        <div className="space-y-4">
          {/* Counterparty Profile */}
          <div>
            <div className={`text-sm font-medium ${theme.colors.textSecondary} mb-2`}>Profile</div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <div className="text-xs text-gray-500">Name</div>
                <div className={`font-medium ${theme.colors.textPrimary}`}>{riskData.counterparty_profile.name}</div>
              </div>
              <div>
                <div className="text-xs text-gray-500">Industry</div>
                <div className={`font-medium ${theme.colors.textPrimary}`}>{riskData.counterparty_profile.industry}</div>
              </div>
              <div>
                <div className="text-xs text-gray-500">Risk Profile</div>
                <div className={`font-medium ${theme.colors.textPrimary}`}>{riskData.counterparty_profile.risk_profile}</div>
              </div>
              <div>
                <div className="text-xs text-gray-500">Total Contracts</div>
                <div className={`font-medium ${theme.colors.textPrimary}`}>{riskData.counterparty_profile.total_contracts}</div>
              </div>
            </div>
          </div>

          {/* Reliability Breakdown */}
          <div>
            <div className={`text-sm font-medium ${theme.colors.textSecondary} mb-2`}>
              Reliability Scoring Breakdown ({riskData.reliability_breakdown.history_records} negotiation records)
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span className="text-gray-500">Acceptance Rate (40%)</span>
                  <span className="text-green-400 font-medium">{(riskData.reliability_breakdown.acceptance_rate * 100).toFixed(1)}%</span>
                </div>
                <div className="w-full bg-gray-700 rounded-full h-2">
                  <div
                    className="bg-green-500 h-2 rounded-full"
                    style={{ width: `${riskData.reliability_breakdown.acceptance_rate * 100}%` }}
                  />
                </div>
              </div>

              <div className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span className="text-gray-500">Stall Behavior (30%)</span>
                  <span className="text-yellow-400 font-medium">{(riskData.reliability_breakdown.stall_rate * 100).toFixed(1)}%</span>
                </div>
                <div className="w-full bg-gray-700 rounded-full h-2">
                  <div
                    className="bg-yellow-500 h-2 rounded-full"
                    style={{ width: `${riskData.reliability_breakdown.stall_rate * 100}%` }}
                  />
                </div>
              </div>

              <div className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span className="text-gray-500">Redline Score (20%)</span>
                  <span className="text-blue-400 font-medium">{(riskData.reliability_breakdown.redline_score * 100).toFixed(1)}%</span>
                </div>
                <div className="text-xs text-gray-500 mt-1">
                  Avg: {riskData.reliability_breakdown.avg_redline_rounds} rounds
                </div>
              </div>

              <div className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span className="text-gray-500">Deviation Score (10%)</span>
                  <span className="text-purple-400 font-medium">{(riskData.reliability_breakdown.deviation_score * 100).toFixed(1)}%</span>
                </div>
                <div className="text-xs text-gray-500 mt-1">
                  Avg: {(riskData.reliability_breakdown.avg_deviation * 100).toFixed(1)}%
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Financial Exposure Breakdown */}
      <div className={`p-6 rounded-lg border ${theme.colors.surfaceBorder} ${theme.colors.surface}`}>
        <div className="flex items-center gap-2 mb-4">
          <DollarSign size={24} className="text-purple-400" />
          <h3 className={`text-xl font-bold ${theme.colors.textPrimary}`}>Financial Exposure Breakdown</h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="p-4 border border-purple-500/30 rounded-lg bg-purple-500/5">
            <div className="text-xs text-gray-500 mb-1">Total Exposure</div>
            <div className="text-xl font-bold text-purple-400">
              {formatCurrency(riskData.financial_exposure.total)}
            </div>
          </div>

          <div className="p-4 border border-gray-600 rounded-lg">
            <div className="text-xs text-gray-500 mb-1">Contract Value</div>
            <div className={`text-lg font-semibold ${theme.colors.textPrimary}`}>
              {formatCurrency(riskData.financial_exposure.contract_value)}
            </div>
          </div>

          <div className="p-4 border border-gray-600 rounded-lg">
            <div className="text-xs text-gray-500 mb-1">Total Liability</div>
            <div className={`text-lg font-semibold ${theme.colors.textPrimary}`}>
              {formatCurrency(riskData.financial_exposure.total_liability)}
            </div>
          </div>

          <div className="p-4 border border-gray-600 rounded-lg">
            <div className="text-xs text-gray-500 mb-1">Silent Risk Exposure</div>
            <div className={`text-lg font-semibold ${theme.colors.textPrimary}`}>
              {formatCurrency(riskData.financial_exposure.silent_risk_exposure)}
            </div>
          </div>
        </div>
      </div>

      {/* Bayesian Failure Analysis */}
      <div className={`p-6 rounded-lg border ${theme.colors.surfaceBorder} ${theme.colors.surface}`}>
        <div className="flex items-center gap-2 mb-4">
          <AlertTriangle size={24} className="text-red-400" />
          <h3 className={`text-xl font-bold ${theme.colors.textPrimary}`}>Bayesian Failure Analysis</h3>
        </div>

        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-gray-500">Failure Probability</div>
              <div className={`text-3xl font-bold ${getRiskLevelColor(riskData.failure_analysis.risk_level)}`}>
                {(riskData.failure_analysis.probability * 100).toFixed(1)}%
              </div>
            </div>
            <div className={`px-4 py-2 rounded-lg border ${getQuadrantColor(riskData.risk_quadrant)}`}>
              <div className="text-lg font-bold">{riskData.failure_analysis.risk_level} RISK</div>
            </div>
          </div>

          <div className={`p-4 rounded-lg border ${theme.colors.surfaceBorder} bg-gray-500/5`}>
            <div className="text-xs text-gray-500 mb-2">Calculation Method</div>
            <div className={`text-sm ${theme.colors.textSecondary} font-mono`}>
              {riskData.failure_analysis.explanation}
            </div>
            {riskData.failure_analysis.avg_clause_risk !== null && (
              <div className="text-xs text-gray-500 mt-2">
                Average Clause Risk Score: {(riskData.failure_analysis.avg_clause_risk * 100).toFixed(1)}%
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Portfolio Context */}
      <div className={`p-6 rounded-lg border ${theme.colors.surfaceBorder} ${theme.colors.surface}`}>
        <div className="flex items-center gap-2 mb-4">
          <TrendingUp size={24} className="text-blue-400" />
          <h3 className={`text-xl font-bold ${theme.colors.textPrimary}`}>Portfolio Context</h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 border border-gray-600 rounded-lg">
            <div className="text-xs text-gray-500 mb-1">Counterparty Total Exposure</div>
            <div className={`text-xl font-bold ${theme.colors.textPrimary}`}>
              {formatCurrency(riskData.portfolio_context.counterparty_total_exposure)}
            </div>
            <div className="text-xs text-gray-500 mt-1">
              Across {riskData.portfolio_context.related_contracts_count} contracts
            </div>
          </div>

          <div className="p-4 border border-gray-600 rounded-lg">
            <div className="text-xs text-gray-500 mb-1">Portfolio Contribution</div>
            <div className={`text-xl font-bold ${theme.colors.textPrimary}`}>
              {riskData.portfolio_context.portfolio_percentage.toFixed(2)}%
            </div>
            <div className="text-xs text-gray-500 mt-1">
              Of total portfolio exposure
            </div>
          </div>

          <div className="p-4 border border-gray-600 rounded-lg">
            <div className="text-xs text-gray-500 mb-1">Total Portfolio Exposure</div>
            <div className={`text-xl font-bold ${theme.colors.textPrimary}`}>
              {formatCurrency(riskData.portfolio_context.user_total_exposure)}
            </div>
            <div className="text-xs text-gray-500 mt-1">
              All contracts combined
            </div>
          </div>
        </div>
      </div>

      {/* Recommended Actions */}
      <div className={`p-6 rounded-lg border ${theme.colors.surfaceBorder} ${theme.colors.surface}`}>
        <div className="flex items-center gap-2 mb-4">
          <CheckCircle size={24} className="text-green-400" />
          <h3 className={`text-xl font-bold ${theme.colors.textPrimary}`}>Recommended Actions</h3>
        </div>

        <div className="space-y-3">
          {riskData.recommended_actions.map((action, index) => (
            <div
              key={index}
              className={`p-4 rounded-lg border ${theme.colors.surfaceBorder} bg-gray-500/5 hover:bg-gray-500/10 transition-colors`}
            >
              <div className="flex items-start gap-3">
                {getPriorityIcon(action.priority)}
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className={`text-xs font-bold px-2 py-1 rounded ${
                      action.priority === 'CRITICAL' ? 'bg-red-500/20 text-red-400' :
                      action.priority === 'HIGH' ? 'bg-orange-500/20 text-orange-400' :
                      action.priority === 'MEDIUM' ? 'bg-yellow-500/20 text-yellow-400' :
                      action.priority === 'LOW' ? 'bg-blue-500/20 text-blue-400' :
                      'bg-green-500/20 text-green-400'
                    }`}>
                      {action.priority}
                    </span>
                  </div>
                  <div className={`font-medium ${theme.colors.textPrimary} mb-1`}>
                    {action.action}
                  </div>
                  <div className={`text-sm ${theme.colors.textSecondary}`}>
                    {action.rationale}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default PortfolioRiskIntelligence;
