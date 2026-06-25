import { useState, useEffect } from 'react';
import { Shield, TrendingUp, AlertTriangle, BarChart3, Network } from 'lucide-react';
import useThemeStore from '../store/themeStore';
import axios from 'axios';
import RiskMatrixHeatmap from '../components/RiskMatrixHeatmap';
import RiskCharts from '../components/RiskCharts';
import RiskCategoryTable from '../components/RiskCategoryTable';

const RiskExposure = () => {
  const { theme } = useThemeStore();
  const [loading, setLoading] = useState(true);
  const [portfolioData, setPortfolioData] = useState(null);
  const [heatmapData, setHeatmapData] = useState([]);
  const [topVendors, setTopVendors] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);

      const token = localStorage.getItem('token');
      const config = {
        headers: { Authorization: `Bearer ${token}` }
      };

      // Load portfolio overview
      const portfolioRes = await axios.get(
        `${import.meta.env.VITE_API_URL||(import.meta.env.VITE_API_URL||'http://localhost:8002')}/api/risk/portfolio/overview`,
        config
      );
      setPortfolioData(portfolioRes.data.data);

      // Load regional heatmap
      const heatmapRes = await axios.get(
        `${import.meta.env.VITE_API_URL||(import.meta.env.VITE_API_URL||'http://localhost:8002')}/api/risk/heatmap/regional`,
        config
      );
      setHeatmapData(heatmapRes.data.data);

      // Load top vendors
      const vendorsRes = await axios.get(
        `${import.meta.env.VITE_API_URL||(import.meta.env.VITE_API_URL||'http://localhost:8002')}/api/risk/vendors/top-exposure?limit=5`,
        config
      );
      setTopVendors(vendorsRes.data.data);

    } catch (err) {
      console.error('Error loading risk data:', err);
      setError(err.response?.data?.error || 'Failed to load risk data');
    } finally {
      setLoading(false);
    }
  };

  const getRiskColor = (score) => {
    if (score < 0.3) return '#22c55e'; // Green
    if (score < 0.6) return '#eab308'; // Yellow
    if (score < 0.8) return '#f97316'; // Orange
    return '#ef4444'; // Red
  };

  const getRiskLevel = (score) => {
    if (score < 0.3) return 'LOW';
    if (score < 0.6) return 'MEDIUM';
    if (score < 0.8) return 'HIGH';
    return 'CRITICAL';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className={`text-xl ${theme.colors.textSecondary}`}>
          Loading risk analysis...
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8">
        <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-6">
          <div className="flex items-center gap-3 text-red-400">
            <AlertTriangle size={24} />
            <div>
              <h3 className="font-bold text-lg">Error</h3>
              <p>{error}</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 lg:p-8 space-y-6">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-3">
            <div className="p-2 bg-blue-500/10 rounded-lg">
              <Shield size={32} className="text-blue-500" />
            </div>
            <div>
              <h1 className={`text-3xl font-bold ${theme.colors.textPrimary}`}>
                Cross-Contract Risk & Exposure
              </h1>
              <p className={`${theme.colors.textSecondary} text-sm mt-1`}>
                AI-powered risk intelligence across your contract portfolio
              </p>
            </div>
          </div>
          <div className="h-1 w-24 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full"></div>
        </div>

        {/* Portfolio Overview Stats */}
        {portfolioData && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 lg:gap-6 mb-8">
            {/* Total Contracts */}
            <div className={`${theme.colors.surface} rounded-xl p-6 border ${theme.colors.surfaceBorder} hover:shadow-lg transition-all`}>
              <div className="flex items-center justify-between mb-4">
                <BarChart3 size={24} className="text-blue-500" />
                <span className={`text-sm ${theme.colors.textSecondary}`}>Total</span>
              </div>
              <div className={`text-3xl font-bold ${theme.colors.textPrimary} mb-1`}>
                {portfolioData.total_contracts}
              </div>
              <div className={`text-sm ${theme.colors.textSecondary}`}>
                Contracts
              </div>
            </div>

            {/* Analyzed Contracts */}
            <div className={`${theme.colors.surface} rounded-xl p-6 border ${theme.colors.surfaceBorder} hover:shadow-lg transition-all`}>
              <div className="flex items-center justify-between mb-4">
                <Shield size={24} className="text-green-500" />
                <span className={`text-sm ${theme.colors.textSecondary}`}>Analyzed</span>
              </div>
              <div className={`text-3xl font-bold ${theme.colors.textPrimary} mb-1`}>
                {portfolioData.analyzed_contracts}
              </div>
              <div className={`text-sm ${theme.colors.textSecondary}`}>
                Risk Analyzed
              </div>
            </div>

            {/* Average Risk Score */}
            <div className={`${theme.colors.surface} rounded-xl p-6 border ${theme.colors.surfaceBorder} hover:shadow-lg transition-all`}>
              <div className="flex items-center justify-between mb-4">
                <TrendingUp size={24} style={{ color: getRiskColor(portfolioData.average_risk_score) }} />
                <span className={`text-sm ${theme.colors.textSecondary}`}>Avg Risk</span>
              </div>
              <div className={`text-3xl font-bold mb-1`} style={{ color: getRiskColor(portfolioData.average_risk_score) }}>
                {portfolioData.average_risk_score.toFixed(2)}
              </div>
              <div className={`text-sm ${theme.colors.textSecondary}`}>
                {getRiskLevel(portfolioData.average_risk_score)} RISK
              </div>
            </div>

            {/* High Risk Contracts */}
            <div className={`${theme.colors.surface} rounded-xl p-6 border ${theme.colors.surfaceBorder} hover:shadow-lg transition-all`}>
              <div className="flex items-center justify-between mb-4">
                <AlertTriangle size={24} className="text-red-500" />
                <span className={`text-sm ${theme.colors.textSecondary}`}>Critical</span>
              </div>
              <div className={`text-3xl font-bold text-red-400 mb-1`}>
                {portfolioData.risk_distribution.high}
              </div>
              <div className={`text-sm ${theme.colors.textSecondary}`}>
                High Risk
              </div>
            </div>
          </div>
        )}

        {/* 5x5 Risk Matrix Heatmap - PRIORITY PLACEMENT */}
        <RiskMatrixHeatmap data={portfolioData?.risk_matrix_data || []} />

        {/* Risk Charts (Donut + Bar Charts) */}
        <RiskCharts portfolioData={portfolioData} />

        {/* Regional Risk Heatmap */}
        <div className={`${theme.colors.surface} rounded-xl p-6 border ${theme.colors.surfaceBorder} shadow-sm`}>
          <h2 className={`text-2xl font-bold ${theme.colors.textPrimary} mb-6 flex items-center gap-2`}>
            <BarChart3 size={24} className="text-blue-500" />
            Regional Risk Heatmap
          </h2>

          {heatmapData.length === 0 ? (
            <div className={`text-center py-12 ${theme.colors.textSecondary}`}>
              <p>No regional risk data available.</p>
              <p className="text-sm mt-2">Analyze contracts to see regional risk breakdown.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
              {heatmapData.map((region) => (
                <div
                  key={region.region}
                  className="rounded-lg p-6 text-white shadow-lg transform transition hover:scale-105"
                  style={{ backgroundColor: getRiskColor(region.risk) }}
                >
                  <div className="text-sm font-medium opacity-90 mb-2">{region.region}</div>
                  <div className="text-3xl font-bold mb-2">{region.risk.toFixed(2)}</div>
                  <div className="text-sm opacity-80">
                    {region.contract_count} contracts
                  </div>
                  <div className="text-xs opacity-70 mt-2">
                    {getRiskLevel(region.risk)} RISK
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Top Vendors by Exposure */}
        <div className={`${theme.colors.surface} rounded-xl p-6 border ${theme.colors.surfaceBorder} shadow-sm`}>
          <h2 className={`text-2xl font-bold ${theme.colors.textPrimary} mb-6 flex items-center gap-2`}>
            <Network size={24} className="text-purple-500" />
            Top Vendors by Risk Exposure
          </h2>

          {topVendors.length === 0 ? (
            <div className={`text-center py-12 ${theme.colors.textSecondary}`}>
              <p>No vendor exposure data available.</p>
              <p className="text-sm mt-2">Analyze contracts to see vendor risk exposure.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {topVendors.map((vendor, index) => (
                <div
                  key={index}
                  className={`p-4 rounded-lg border ${theme.colors.surfaceBorder} hover:${theme.colors.surfaceHover} transition`}
                >
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <div
                        className="w-3 h-3 rounded-full"
                        style={{ backgroundColor: getRiskColor(vendor.average_risk) }}
                      />
                      <span className={`font-bold ${theme.colors.textPrimary}`}>
                        {vendor.vendor_name}
                      </span>
                    </div>
                    <div className="text-right">
                      <div className={`text-sm ${theme.colors.textSecondary}`}>
                        Exposure Score
                      </div>
                      <div
                        className="text-2xl font-bold"
                        style={{ color: getRiskColor(vendor.average_risk) }}
                      >
                        {vendor.total_exposure.toFixed(2)}
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <div className={`text-xs ${theme.colors.textSecondary} mb-1`}>
                        Contracts
                      </div>
                      <div className={`font-medium ${theme.colors.textPrimary}`}>
                        {vendor.contract_count}
                      </div>
                    </div>
                    <div>
                      <div className={`text-xs ${theme.colors.textSecondary} mb-1`}>
                        Avg Risk
                      </div>
                      <div className="font-medium" style={{ color: getRiskColor(vendor.average_risk) }}>
                        {vendor.average_risk.toFixed(2)} - {getRiskLevel(vendor.average_risk)}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Top Risk Contracts */}
        {portfolioData && portfolioData.top_risk_contracts.length > 0 && (
          <div className={`${theme.colors.surface} rounded-xl p-6 border ${theme.colors.surfaceBorder} shadow-sm`}>
            <h2 className={`text-2xl font-bold ${theme.colors.textPrimary} mb-6 flex items-center gap-2`}>
              <AlertTriangle size={24} className="text-red-500" />
              Highest Risk Contracts
            </h2>

            <div className="space-y-3">
              {portfolioData.top_risk_contracts.map((contract) => (
                <div
                  key={contract.contract_id}
                  className={`p-4 rounded-lg border ${theme.colors.surfaceBorder} hover:${theme.colors.surfaceHover} transition`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3 flex-1">
                      <div
                        className="w-3 h-3 rounded-full"
                        style={{ backgroundColor: getRiskColor(contract.risk_score) }}
                      />
                      <span className={`font-medium ${theme.colors.textPrimary} truncate`}>
                        {contract.contract_name}
                      </span>
                      {contract.region && (
                        <span className={`text-xs px-2 py-1 rounded ${theme.colors.surfaceHover}`}>
                          {contract.region}
                        </span>
                      )}
                    </div>
                    <div className="text-right">
                      <div
                        className="text-xl font-bold"
                        style={{ color: getRiskColor(contract.risk_score) }}
                      >
                        {contract.risk_score.toFixed(2)}
                      </div>
                      <div className={`text-xs ${theme.colors.textSecondary}`}>
                        {getRiskLevel(contract.risk_score)}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Risk Category Table */}
        <RiskCategoryTable risks={portfolioData?.risk_categories || []} />

        {/* Info Box */}
        <div className="bg-gradient-to-r from-blue-500/10 to-purple-500/10 border-2 border-blue-500/20 rounded-xl p-6 shadow-sm">
          <div className="flex items-start gap-3">
            <Shield size={24} className="text-blue-400 mt-1" />
            <div>
              <h3 className="font-bold text-blue-400 mb-2">About Cross-Contract Risk Analysis</h3>
              <p className={theme.colors.textSecondary}>
                This dashboard uses AI-powered risk intelligence combining Neo4j graph analysis,
                Qdrant semantic similarity, and Qwen 7B LLM scoring to identify cross-contract
                risks, vendor exposure, and systemic vulnerabilities across your contract portfolio.
              </p>
              <p className={`${theme.colors.textSecondary} mt-2 text-sm`}>
                Navigate to individual contracts to trigger risk analysis and see detailed correlation reports.
              </p>
            </div>
          </div>
        </div>
      </div>
  );
};

export default RiskExposure;
