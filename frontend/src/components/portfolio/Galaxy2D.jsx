import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { ScatterChart, Scatter, XAxis, YAxis, ZAxis, Tooltip, ResponsiveContainer, CartesianGrid, Cell, Legend } from 'recharts';
import { TrendingUp, AlertCircle, Loader } from 'lucide-react';

const Galaxy2D = ({ filters }) => {
  const navigate = useNavigate();
  const [data, setData] = useState([]);
  const [statistics, setStatistics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchData();
  }, [filters]);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      const token = localStorage.getItem('token');

      // Build query parameters from filters
      const params = new URLSearchParams();
      if (filters?.industry) params.append('industry', filters.industry);
      if (filters?.jurisdiction) params.append('jurisdiction', filters.jurisdiction);
      if (filters?.vendor) params.append('vendor', filters.vendor);

      const url = `${import.meta.env.VITE_API_URL||(import.meta.env.VITE_API_URL||'http://localhost:8002')}/api/executive/clustering-galaxy${params.toString() ? `?${params.toString()}` : ''}`;

      const response = await axios.get(url, {
        headers: { Authorization: `Bearer ${token}` }
      });

      setData(response.data.contracts || []);
      setStatistics(response.data.statistics || null);
    } catch (error) {
      console.error('Error fetching clustering data:', error);
      setError(error.response?.data?.message || 'Failed to load clustering data');
    } finally {
      setLoading(false);
    }
  };

  const getColor = (contract) => {
    // Outliers are always red
    if (contract.outlier) return '#E53935'; // Red
    // High risk is amber
    if (contract.risk_score >= 70) return '#FFB300'; // Amber
    // Medium risk is yellow
    if (contract.risk_score >= 40) return '#FDD835'; // Yellow
    // Low risk is green
    return '#43A047'; // Green
  };

  const getRadius = (contract) => {
    // Outliers get larger dots
    if (contract.outlier) return 9;
    // High risk gets medium dots
    if (contract.risk_score >= 70) return 7;
    // Normal risk gets small dots
    return 5;
  };

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const contract = payload[0].payload;
      return (
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-3 shadow-xl max-w-xs">
          <p className="text-white font-semibold text-sm mb-2">{contract.contract_name}</p>
          <div className="space-y-1 text-xs">
            <p className="text-slate-300">
              <span className="text-slate-400">Cluster:</span> {contract.cluster}
            </p>
            <p className="text-slate-300">
              <span className="text-slate-400">Industry:</span> {contract.industry}
            </p>
            <p className="text-slate-300">
              <span className="text-slate-400">Jurisdiction:</span> {contract.jurisdiction}
            </p>
            <p className="text-slate-300">
              <span className="text-slate-400">Vendor:</span> {contract.vendor}
            </p>
            <p className="text-slate-300">
              <span className="text-slate-400">Risk Score:</span> {contract.risk_score}/100
            </p>
            {contract.outlier && (
              <p className="text-red-400 font-semibold mt-2">
                🚨 OUTLIER - Non-standard pattern
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
    const radius = getRadius(payload);
    const color = getColor(payload);

    return (
      <circle
        cx={cx}
        cy={cy}
        r={radius}
        fill={color}
        fillOpacity={payload.outlier ? 0.9 : 0.7}
        stroke={payload.outlier ? '#ffffff' : color}
        strokeWidth={payload.outlier ? 2 : 1}
        onClick={() => navigate(`/contracts/${payload.id}`)}
        className="cursor-pointer hover:opacity-100 transition-opacity"
        style={{ cursor: 'pointer' }}
      />
    );
  };

  if (loading) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-8">
        <div className="flex items-center justify-center h-96">
          <div className="text-center">
            <Loader className="w-12 h-12 animate-spin text-blue-400 mx-auto mb-4" />
            <p className="text-slate-400 text-sm">Clustering contracts...</p>
            <p className="text-slate-500 text-xs mt-2">Generating semantic embeddings</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-slate-900 border border-red-800 rounded-xl p-8">
        <div className="flex items-center justify-center h-96">
          <div className="text-center">
            <AlertCircle className="w-12 h-12 text-red-400 mx-auto mb-4" />
            <p className="text-red-400 text-sm mb-2">Clustering Error</p>
            <p className="text-slate-500 text-xs">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-8">
        <div className="flex items-center justify-center h-96">
          <div className="text-center">
            <TrendingUp className="w-12 h-12 text-slate-600 mx-auto mb-4" />
            <p className="text-slate-400 text-sm">No contracts to cluster</p>
            <p className="text-slate-500 text-xs mt-2">Upload contracts to see the galaxy</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Statistics Cards */}
      {statistics && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
            <p className="text-slate-400 text-xs mb-1">Total Contracts</p>
            <p className="text-white text-2xl font-bold">{statistics.total_contracts}</p>
          </div>
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
            <p className="text-slate-400 text-xs mb-1">Clusters Detected</p>
            <p className="text-white text-2xl font-bold">{statistics.total_clusters}</p>
          </div>
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
            <p className="text-slate-400 text-xs mb-1">Outliers</p>
            <p className="text-red-400 text-2xl font-bold">{statistics.total_outliers}</p>
          </div>
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
            <p className="text-slate-400 text-xs mb-1">Outlier Rate</p>
            <p className="text-amber-400 text-2xl font-bold">
              {((statistics.total_outliers / statistics.total_contracts) * 100).toFixed(1)}%
            </p>
          </div>
        </div>
      )}

      {/* Galaxy Chart */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-blue-500" />
            <span className="text-xs text-slate-400 uppercase tracking-wider">
              Contract Clustering Galaxy
            </span>
          </div>
          <div className="flex items-center gap-4 text-xs">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-green-500"></div>
              <span className="text-slate-400">Low Risk</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-amber-500"></div>
              <span className="text-slate-400">High Risk</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded-full bg-red-500 border-2 border-white"></div>
              <span className="text-slate-400">Outlier</span>
            </div>
          </div>
        </div>

        <ResponsiveContainer width="100%" height={600}>
          <ScatterChart margin={{ top: 20, right: 30, bottom: 60, left: 60 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.2} />

            <XAxis
              type="number"
              dataKey="x"
              name="Dimension 1"
              tick={{ fill: '#94a3b8', fontSize: 12 }}
              label={{
                value: 'Semantic Dimension 1',
                position: 'insideBottom',
                offset: -10,
                style: { fill: '#64748b', fontSize: 12 }
              }}
              stroke="#475569"
            />

            <YAxis
              type="number"
              dataKey="y"
              name="Dimension 2"
              tick={{ fill: '#94a3b8', fontSize: 12 }}
              label={{
                value: 'Semantic Dimension 2',
                angle: -90,
                position: 'insideLeft',
                style: { fill: '#64748b', fontSize: 12 }
              }}
              stroke="#475569"
            />

            <ZAxis type="number" dataKey="z" range={[50, 400]} />

            <Tooltip content={<CustomTooltip />} cursor={{ strokeDasharray: '3 3', stroke: '#6366f1' }} />

            <Scatter
              data={data}
              shape={<CustomDot />}
              animationDuration={1000}
            />
          </ScatterChart>
        </ResponsiveContainer>

        <div className="mt-4 flex items-center justify-between text-xs text-slate-500">
          <span>Each dot represents a contract. Proximity indicates semantic similarity. Outliers marked in red.</span>
          <span className="text-emerald-400">{data.length} contract(s) visualized</span>
        </div>
      </div>

      {/* Cluster Details */}
      {statistics && statistics.clusters && statistics.clusters.length > 0 && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Cluster Analysis</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {statistics.clusters.map((cluster) => (
              <div key={cluster.cluster_id} className="bg-slate-800 border border-slate-700 rounded-lg p-4">
                <h4 className="text-white font-semibold text-sm mb-2">{cluster.cluster_name}</h4>
                <div className="space-y-1 text-xs text-slate-300">
                  <p><span className="text-slate-400">Contracts:</span> {cluster.contract_count}</p>
                  <p><span className="text-slate-400">Avg Risk:</span> {cluster.avg_risk_score}/100</p>
                  <p><span className="text-slate-400">Outliers:</span> {cluster.outlier_count} ({cluster.outlier_percentage}%)</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default Galaxy2D;
