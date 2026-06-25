import { useEffect, useState } from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts';
import axios from 'axios';
import { DollarSign } from 'lucide-react';

const TotalExposureGauge = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const token = localStorage.getItem('token');
        const response = await axios.get(`${import.meta.env.VITE_API_URL||(import.meta.env.VITE_API_URL||'http://localhost:8002')}/api/executive/exposure`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setData(response.data);
      } catch (error) {
        console.error('Error fetching exposure data:', error);
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

  const formatValue = (value) => {
    if (value >= 1e9) return `${(value / 1e9).toFixed(2)}B`;
    if (value >= 1e7) return `${(value / 1e7).toFixed(1)}Cr`;
    if (value >= 1e6) return `${(value / 1e6).toFixed(1)}M`;
    if (value >= 1e3) return `${(value / 1e3).toFixed(1)}K`;
    return value.toFixed(0);
  };

  // Create gauge data
  const gaugeData = [
    { name: 'Risk', value: data.exposure_pct },
    { name: 'Safe', value: 100 - data.exposure_pct }
  ];

  const getColorForExposure = (pct) => {
    if (pct >= 70) return '#E53935';  // Red
    if (pct >= 40) return '#FFB300';  // Amber
    return '#43A047';  // Green
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 h-full">
      <div className="flex items-center gap-2 mb-2">
        <DollarSign className="w-5 h-5 text-yellow-500" />
        <span className="text-xs text-slate-400 uppercase tracking-wider">
          Total Exposure
        </span>
      </div>

      <div className="text-4xl font-bold text-yellow-400 mb-4">
        ₹ {formatValue(data.total_value_inr)}
      </div>

      <div className="relative">
        <ResponsiveContainer width="100%" height={200}>
          <PieChart>
            <Pie
              data={gaugeData}
              cx="50%"
              cy="100%"
              startAngle={180}
              endAngle={0}
              innerRadius={80}
              outerRadius={120}
              paddingAngle={0}
              dataKey="value"
            >
              <Cell fill={getColorForExposure(data.exposure_pct)} />
              <Cell fill="#1E293B" />
            </Pie>
          </PieChart>
        </ResponsiveContainer>

        <div className="absolute bottom-0 left-0 right-0 text-center">
          <div className="text-3xl font-bold" style={{ color: getColorForExposure(data.exposure_pct) }}>
            {data.exposure_pct}%
          </div>
          <div className="text-xs text-slate-500">Risk Exposure</div>
        </div>
      </div>
    </div>
  );
};

export default TotalExposureGauge;
