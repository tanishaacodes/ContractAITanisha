import { useEffect, useState } from 'react';
import { LineChart, Line, ResponsiveContainer } from 'recharts';
import axios from 'axios';
import { TrendingUp, TrendingDown } from 'lucide-react';

const RiskTrend = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const token = localStorage.getItem('token');
        const response = await axios.get(`${import.meta.env.VITE_API_URL||(import.meta.env.VITE_API_URL||'http://localhost:8002')}/api/executive/risk-trend`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setData(response.data);
      } catch (error) {
        console.error('Error fetching risk trend data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading || !data) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 h-full">
        <div className="animate-pulse">
          <div className="h-4 bg-slate-800 rounded w-32 mb-4"></div>
          <div className="h-8 bg-slate-800 rounded w-24"></div>
        </div>
      </div>
    );
  }

  const isPositive = data.qoq_change > 0;
  const TrendIcon = isPositive ? TrendingUp : TrendingDown;

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 h-full">
      <div className="flex items-center gap-2 mb-2">
        <TrendIcon className={`w-5 h-5 ${isPositive ? 'text-red-500' : 'text-green-500'}`} />
        <span className="text-xs text-slate-400 uppercase tracking-wider">
          Risk Trend
        </span>
      </div>

      <div className={`text-4xl font-bold mb-4 ${isPositive ? 'text-red-500' : 'text-green-500'}`}>
        {isPositive ? '↑' : '↓'} {Math.abs(data.qoq_change)}% QoQ
      </div>

      <ResponsiveContainer width="100%" height={160}>
        <LineChart data={data.trend}>
          <Line
            type="monotone"
            dataKey="v"
            stroke={isPositive ? '#E53935' : '#43A047'}
            strokeWidth={3}
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>

      <div className="text-xs text-slate-500 mt-2">
        Last 4 quarters
      </div>
    </div>
  );
};

export default RiskTrend;
