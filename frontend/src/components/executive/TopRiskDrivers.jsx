import { useEffect, useState } from 'react';
import axios from 'axios';
import { AlertTriangle } from 'lucide-react';

const TopRiskDrivers = () => {
  const [drivers, setDrivers] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const token = localStorage.getItem('token');
        const response = await axios.get(`${import.meta.env.VITE_API_URL||(import.meta.env.VITE_API_URL||'http://localhost:8002')}/api/executive/risk-drivers`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setDrivers(response.data);
      } catch (error) {
        console.error('Error fetching risk drivers:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 h-full">
        <div className="animate-pulse">
          <div className="h-4 bg-slate-800 rounded w-32 mb-4"></div>
          <div className="space-y-3">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-8 bg-slate-800 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  const getColorForWeight = (weight) => {
    if (weight >= 70) return 'bg-red-500';
    if (weight >= 40) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 h-full">
      <div className="flex items-center gap-2 mb-4">
        <AlertTriangle className="w-5 h-5 text-red-500" />
        <span className="text-xs text-slate-400 uppercase tracking-wider">
          Top Risk Drivers
        </span>
      </div>

      <div className="space-y-4">
        {drivers.map((driver, index) => (
          <div key={index}>
            <div className="flex items-center justify-between mb-1">
              <span className="text-sm text-slate-300">{driver.name}</span>
              <span className="text-xs font-semibold text-slate-400">{driver.weight}%</span>
            </div>
            <div className="w-full bg-slate-800 rounded-full h-2">
              <div
                className={`h-2 rounded-full ${getColorForWeight(driver.weight)}`}
                style={{ width: `${driver.weight}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default TopRiskDrivers;
