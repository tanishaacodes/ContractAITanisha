import { useState, useEffect } from 'react';
import { AlertTriangle, TrendingDown } from 'lucide-react';
import axios from 'axios';
import useThemeStore from '../store/themeStore';
import ExposureGauge from '../components/loss/ExposureGauge';
import LossForecast from '../components/loss/LossForecast';
import TailRiskChart from '../components/loss/TailRiskChart';
import UnlimitedWatchlist from '../components/loss/UnlimitedWatchlist';
import ClauseLossWaterfall from '../components/loss/ClauseLossWaterfall';

const LossSentinel = () => {
  const { theme } = useThemeStore();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const response = await axios.get(`${import.meta.env.VITE_API_URL||(import.meta.env.VITE_API_URL||'http://localhost:8002')}/api/loss-sentinel/dashboard`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setData(response.data);
    } catch (error) {
      console.error('Error fetching loss sentinel data:', error);
      setError(error.response?.data?.message || 'Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 to-slate-900 p-6">
        <div className="flex items-center justify-center h-96">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-500 mx-auto mb-4"></div>
            <p className="text-slate-400 text-sm">Loading loss predictions...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 to-slate-900 p-6">
        <div className="bg-red-900/20 border border-red-500/50 rounded-lg p-4">
          <p className="text-red-400">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 to-slate-900 p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-2">
          <div className="p-2 bg-red-500/20 rounded-lg">
            <AlertTriangle className="w-6 h-6 text-red-400" />
          </div>
          <div>
            <h1 className={`text-2xl font-bold ${theme.colors.textPrimary}`}>
              Loss Prediction & Liability Sentinel
            </h1>
            <p className="text-sm text-slate-400">
              Early-warning system for future losses, tail risks & unlimited liability exposure
            </p>
          </div>
        </div>
      </div>

      {/* Alert Banner */}
      <div className="mb-6 bg-gradient-to-r from-red-900/20 to-orange-900/20 border border-red-500/30 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <TrendingDown className="w-5 h-5 text-red-400 mt-1 flex-shrink-0" />
          <div>
            <p className="text-red-400 font-semibold mb-1">Financial Risk Intelligence</p>
            <p className="text-gray-300 text-sm">
              This dashboard forecasts expected losses across 12/24/36 month horizons using{' '}
              <span className="font-semibold text-white">Monte Carlo simulation</span> and{' '}
              <span className="font-semibold text-white">tail risk modeling (VaR/CVaR)</span>.
              Contracts with unlimited liability are flagged for immediate review.
            </p>
          </div>
        </div>
      </div>

      {/* Key Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
          <p className="text-xs text-slate-400 mb-1">Total Exposure</p>
          <p className="text-2xl font-bold text-white">₹{data.total_exposure_inr.toLocaleString()}</p>
          <p className="text-xs text-slate-500 mt-1">${data.total_exposure_usd.toLocaleString()} USD</p>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
          <p className="text-xs text-slate-400 mb-1">Expected Loss (12m)</p>
          <p className="text-2xl font-bold text-orange-400">₹{data.loss_forecast['12m'].toLocaleString()}</p>
          <p className="text-xs text-slate-500 mt-1">{((data.loss_forecast['12m'] / data.total_exposure_inr) * 100).toFixed(1)}% of exposure</p>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
          <p className="text-xs text-slate-400 mb-1">95% VaR</p>
          <p className="text-2xl font-bold text-red-400">₹{data.var_cvar.var_95.toLocaleString()}</p>
          <p className="text-xs text-slate-500 mt-1">Worst-case (95% confidence)</p>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
          <p className="text-xs text-slate-400 mb-1">Unlimited Liability</p>
          <p className="text-2xl font-bold text-red-500">{data.unlimited_liability_watchlist.length}</p>
          <p className="text-xs text-slate-500 mt-1">contracts require review</p>
        </div>
      </div>

      {/* Main Dashboard Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        {/* Exposure Gauge */}
        <div className="lg:col-span-1">
          <ExposureGauge
            value={data.exposure_percentage}
            totalContracts={data.total_contracts}
            highRiskContracts={data.high_risk_contracts}
          />
        </div>

        {/* Loss Forecast */}
        <div className="lg:col-span-2">
          <LossForecast
            forecast={data.loss_forecast}
            varCvar={data.var_cvar}
            totalExposure={data.total_exposure_inr}
          />
        </div>
      </div>

      {/* Tail Risk Distribution */}
      <div className="mb-6">
        <TailRiskChart data={data.tail_risk_distribution} />
      </div>

      {/* Bottom Row: Watchlist + Clause Attribution */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Unlimited Liability Watchlist */}
        <UnlimitedWatchlist contracts={data.unlimited_liability_watchlist} />

        {/* Clause Loss Attribution */}
        <ClauseLossWaterfall data={data.clause_loss_attribution} />
      </div>
    </div>
  );
};

export default LossSentinel;
