import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { ScatterChart, Scatter, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, CartesianGrid, Legend } from 'recharts';
import { TrendingUp, AlertCircle } from 'lucide-react';
import CurrencyToggle from './CurrencyToggle';

const RiskValueMatrix = ({ filters }) => {
  const navigate = useNavigate();
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [currency, setCurrency] = useState('INR');

  useEffect(() => {
    fetchData();
  }, [filters]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');

      // Build query parameters from filters
      const params = new URLSearchParams();
      if (filters.geography) params.append('geography', filters.geography);
      if (filters.vendor) params.append('vendor', filters.vendor);
      if (filters.business_unit) params.append('business_unit', filters.business_unit);
      if (filters.contract_type) params.append('contract_type', filters.contract_type);

      const url = `${import.meta.env.VITE_API_URL||(import.meta.env.VITE_API_URL||'http://localhost:8002')}/api/executive/risk-value-matrix${params.toString() ? `?${params.toString()}` : ''}`;

      const response = await axios.get(url, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setData(response.data);
    } catch (error) {
      console.error('Error fetching risk matrix:', error);
    } finally {
      setLoading(false);
    }
  };

  const getColor = (riskScore) => {
    if (riskScore >= 70) return '#E53935'; // Red
    if (riskScore >= 40) return '#FFB300'; // Amber
    return '#43A047'; // Green
  };

  const formatValue = (valueInr) => {
    if (currency === 'INR') {
      return `₹${(valueInr / 10000000).toFixed(2)} Cr`;
    } else {
      const valueUsd = valueInr / 83; // Conversion rate
      return `$${(valueUsd / 1000000).toFixed(2)}M`;
    }
  };

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-3 shadow-xl">
          <p className="text-white font-semibold text-sm mb-2">{data.name}</p>
          <div className="space-y-1 text-xs">
            <p className="text-slate-300">
              <span className="text-slate-400">Value:</span> {formatValue(data.value_inr)}
            </p>
            <p className="text-slate-300">
              <span className="text-slate-400">Risk Score:</span> {data.risk_score}/100
            </p>
            <p className="text-slate-300">
              <span className="text-slate-400">Exposure:</span> {formatValue(data.exposure)}
            </p>
            <p className="text-slate-300">
              <span className="text-slate-400">Liability:</span> {data.liability_level || 'N/A'}
            </p>
            <p className="text-slate-300">
              <span className="text-slate-400">Arbitration:</span> {data.has_arbitration ? 'Yes' : 'No'}
            </p>
            {data.business_unit && data.business_unit !== 'N/A' && (
              <p className="text-slate-300">
                <span className="text-slate-400">BU:</span> {data.business_unit}
              </p>
            )}
          </div>
          <p className="text-purple-400 text-xs mt-2">Click to view details →</p>
        </div>
      );
    }
    return null;
  };

  const CustomDot = (props) => {
    const { cx, cy, payload } = props;
    const radius = Math.max(8, Math.min(25, payload.exposure / 5000000)); // Scale bubble size
    const color = getColor(payload.risk_score);

    return (
      <circle
        cx={cx}
        cy={cy}
        r={radius}
        fill={color}
        fillOpacity={0.75}
        stroke={color}
        strokeWidth={2}
        strokeOpacity={0.9}
        onClick={() => navigate(`/contracts/${payload.id}`)}
        className="cursor-pointer hover:opacity-100 transition-opacity"
        style={{ cursor: 'pointer' }}
      />
    );
  };

  if (loading) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-8">
        <div className="animate-pulse">
          <div className="h-6 bg-slate-800 rounded w-64 mb-4"></div>
          <div className="h-96 bg-slate-800 rounded"></div>
        </div>
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-8">
        <div className="flex items-center gap-2 mb-4">
          <TrendingUp className="w-5 h-5 text-blue-500" />
          <span className="text-xs text-slate-400 uppercase tracking-wider">
            Risk vs Value Matrix
          </span>
        </div>
        <div className="flex flex-col items-center justify-center h-96 text-slate-500">
          <AlertCircle className="w-12 h-12 mb-4 opacity-50" />
          <p className="text-sm">No contract data available</p>
          <p className="text-xs mt-2">Upload contracts with values to see the matrix</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <TrendingUp className="w-5 h-5 text-blue-500" />
          <span className="text-xs text-slate-400 uppercase tracking-wider">
            Risk vs Value Matrix
          </span>
        </div>
        <div className="flex items-center gap-6">
          <CurrencyToggle currency={currency} onCurrencyChange={setCurrency} />
          <div className="flex items-center gap-4 text-xs">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-green-500"></div>
              <span className="text-slate-400">Low (&lt;40)</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-amber-500"></div>
              <span className="text-slate-400">Medium (40-70)</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-red-500"></div>
              <span className="text-slate-400">High (&gt;70)</span>
            </div>
          </div>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={500}>
        <ScatterChart margin={{ top: 20, right: 30, bottom: 60, left: 80 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.3} />

          <XAxis
            type="number"
            dataKey="value_inr"
            name="Contract Value"
            tickFormatter={(value) => {
              if (currency === 'INR') {
                return `₹${(value / 10000000).toFixed(1)}Cr`;
              } else {
                const valueUsd = value / 83;
                return `$${(valueUsd / 1000000).toFixed(1)}M`;
              }
            }}
            tick={{ fill: '#94a3b8', fontSize: 12 }}
            label={{
              value: currency === 'INR' ? 'Contract Value (INR Cr)' : 'Contract Value (USD M)',
              position: 'insideBottom',
              offset: -15,
              style: { fill: '#94a3b8', fontSize: 13, fontWeight: 500 }
            }}
            stroke="#475569"
          />

          <YAxis
            type="number"
            dataKey="risk_score"
            name="Risk Score"
            domain={[0, 100]}
            tick={{ fill: '#94a3b8', fontSize: 12 }}
            label={{
              value: 'Risk Score (0-100)',
              angle: -90,
              position: 'insideLeft',
              offset: -5,
              style: { fill: '#94a3b8', fontSize: 13, fontWeight: 500 }
            }}
            stroke="#475569"
          />

          <Tooltip content={<CustomTooltip />} cursor={{ strokeDasharray: '3 3', stroke: '#6366f1' }} />

          <Scatter
            data={data}
            shape={<CustomDot />}
            animationDuration={800}
          />
        </ScatterChart>
      </ResponsiveContainer>

      <div className="mt-4 flex items-center justify-between text-xs text-slate-500">
        <span>Bubble size represents exposure (20% potential loss). Click any bubble to view contract details.</span>
        <span className="text-emerald-400">{data.length} contract(s) displayed</span>
      </div>
    </div>
  );
};

export default RiskValueMatrix;
