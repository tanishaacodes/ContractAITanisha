import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { LineChart, Line } from 'recharts';
import {
  FileText,
  AlertTriangle,
  DollarSign,
  Brain,
  Clock,
  TrendingDown,
  Activity
} from 'lucide-react';
import axios from 'axios';

const GlobalCommandHeader = () => {
  const navigate = useNavigate();
  const [currency, setCurrency] = useState('INR');
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchHeaderData = async () => {
      try {
        const token = localStorage.getItem('token');
        const response = await axios.get(`${import.meta.env.VITE_API_URL||(import.meta.env.VITE_API_URL||'http://localhost:8002')}/api/dashboard/header`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setData(response.data);
      } catch (error) {
        console.error('Error fetching dashboard header data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchHeaderData();
  }, []);

  if (loading || !data) {
    return (
      <div className="bg-gradient-to-r from-slate-900 to-slate-800 border-b border-slate-700 px-6 py-3">
        <div className="flex items-center justify-center">
          <div className="animate-pulse text-slate-400">Loading metrics...</div>
        </div>
      </div>
    );
  }

  const formatValue = (value) => {
    if (value >= 1e9) return `${(value / 1e9).toFixed(2)}B`;
    if (value >= 1e7) return `${(value / 1e7).toFixed(1)}Cr`;
    if (value >= 1e6) return `${(value / 1e6).toFixed(1)}M`;
    if (value >= 1e3) return `${(value / 1e3).toFixed(1)}K`;
    return value.toFixed(0);
  };

  const toggleCurrency = () => {
    setCurrency(currency === 'INR' ? 'USD' : 'INR');
  };

  return (
    <div className="bg-gradient-to-r from-slate-900 to-slate-800 border-b border-slate-700 px-6 py-3 shadow-lg">
      {/* Top Row - User Info & AI Status */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <Activity className="w-5 h-5 text-emerald-400" />
            <span className="text-white font-semibold">UniContractAI</span>
          </div>
          <div className="h-4 w-px bg-slate-600" />
          <span className="text-slate-300 text-sm">{data.user_role}</span>
        </div>

        <div className="flex items-center gap-2">
          {data.ai_active && (
            <div className="flex items-center gap-2 bg-emerald-500/20 px-3 py-1 rounded-full">
              <div className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse" />
              <span className="text-emerald-400 text-xs font-medium">AI ACTIVE</span>
            </div>
          )}
        </div>
      </div>

      {/* KPI Tiles Grid */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        {/* Total Contracts */}
        <KpiTile
          icon={<FileText className="w-5 h-5 text-blue-400" />}
          label="Total Contracts"
          value={data.total_contracts}
          trend={data.contracts_trend}
          color="blue"
          drillTo="/contracts"
          navigate={navigate}
        />

        {/* High Risk Contracts */}
        <KpiTile
          icon={<AlertTriangle className="w-5 h-5 text-red-400" />}
          label="High-Risk Contracts"
          value={data.high_risk_contracts}
          trend={data.high_risk_trend}
          color="red"
          drillTo="/contracts?risk=high"
          navigate={navigate}
        />

        {/* Total Value with Currency Toggle */}
        <KpiTile
          icon={<DollarSign className="w-5 h-5 text-yellow-400" />}
          label={`Contract Value (${currency})`}
          value={formatValue(data.total_value[currency])}
          prefix={currency === 'INR' ? '₹' : '$'}
          trend={data.value_trend}
          color="yellow"
          drillTo="/contracts?sort=value"
          navigate={navigate}
          rightElement={
            <button
              onClick={(e) => {
                e.stopPropagation();
                toggleCurrency();
              }}
              className="text-xs bg-slate-700 hover:bg-slate-600 px-2 py-1 rounded transition-colors z-10"
            >
              {currency === 'INR' ? '$' : '₹'}
            </button>
          }
        />

        {/* AI Confidence */}
        <KpiTile
          icon={<Brain className="w-5 h-5 text-purple-400" />}
          label="AI Confidence"
          value={`${data.ai_confidence}%`}
          trend={data.ai_confidence_trend}
          color="purple"
          drillTo="/low-confidence-contracts"
          navigate={navigate}
        />

        {/* Review Time */}
        <KpiTile
          icon={<Clock className="w-5 h-5 text-emerald-400" />}
          label="Avg Review Time"
          value={`${data.review_time.after}h`}
          subtext={`Before: ${data.review_time.before}h`}
          color="emerald"
          drillTo="/review-time-analytics"
          navigate={navigate}
          rightElement={
            <div className="flex items-center gap-1">
              <TrendingDown className="w-4 h-4 text-emerald-400" />
              <span className="text-xs text-emerald-400 font-medium">
                -{data.review_time_improvement}%
              </span>
            </div>
          }
        />
      </div>
    </div>
  );
};

/* KPI Tile Component */
const KpiTile = ({ icon, label, value, prefix, trend, color, rightElement, subtext, drillTo, navigate }) => {
  const colorClasses = {
    blue: 'bg-blue-500/10 border-blue-500/30',
    red: 'bg-red-500/10 border-red-500/30',
    yellow: 'bg-yellow-500/10 border-yellow-500/30',
    purple: 'bg-purple-500/10 border-purple-500/30',
    emerald: 'bg-emerald-500/10 border-emerald-500/30',
  };

  const textColorClasses = {
    blue: 'text-blue-400',
    red: 'text-red-400',
    yellow: 'text-yellow-400',
    purple: 'text-purple-400',
    emerald: 'text-emerald-400',
  };

  const handleClick = () => {
    if (drillTo && navigate) {
      navigate(drillTo);
    }
  };

  return (
    <div
      className={`${colorClasses[color]} border rounded-lg p-3 transition-all ${drillTo ? 'cursor-pointer hover:scale-105 hover:shadow-lg' : ''}`}
      onClick={handleClick}
    >
      <div className="flex items-start justify-between mb-2">
        {icon}
        {rightElement}
      </div>

      <div className="text-xs text-slate-400 mb-1">{label}</div>

      <div className={`text-xl font-bold ${textColorClasses[color]} mb-1`}>
        {prefix && <span className="text-sm">{prefix}</span>}
        {value}
      </div>

      {subtext && (
        <div className="text-xs text-slate-500 mb-2">{subtext}</div>
      )}

      {/* Mini Sparkline */}
      {trend && (
        <div className="mt-2">
          <LineChart width={100} height={30} data={trend}>
            <Line
              type="monotone"
              dataKey="v"
              stroke={`var(--${color}-400)`}
              strokeWidth={2}
              dot={false}
            />
          </LineChart>
        </div>
      )}
    </div>
  );
};

export default GlobalCommandHeader;
