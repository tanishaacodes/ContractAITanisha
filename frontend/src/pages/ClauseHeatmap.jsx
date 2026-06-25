import { useState, useEffect } from 'react';
import {
  TrendingUp, AlertTriangle, Shield, Activity,
  Loader2, Target, ArrowLeft, BarChart3
} from 'lucide-react';
import {
  ScatterChart, Scatter, XAxis, YAxis, ZAxis,
  CartesianGrid, Tooltip, ResponsiveContainer,
  Cell, BarChart, Bar, Legend
} from 'recharts';
import { useNavigate } from 'react-router-dom';
import api from '../utils/api';

const ClauseHeatmap = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [heatmapData, setHeatmapData] = useState(null);

  useEffect(() => {
    loadHeatmap();
  }, []);

  const loadHeatmap = async () => {
    try {
      setLoading(true);
      setError('');
      const response = await api.get('/clause-heatmap/portfolio');
      if (response.data.success) {
        setHeatmapData(response.data.data);
      } else {
        setError('Failed to load heatmap data');
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to load heatmap');
      console.error('Heatmap error:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-12 h-12 text-blue-400 animate-spin mx-auto mb-4" />
          <p className="text-slate-400">Loading Clause Heatmap...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-slate-900 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center gap-4 mb-6">
            <button
              onClick={() => navigate('/dashboard')}
              className="p-2 hover:bg-slate-800 rounded-lg transition-colors"
            >
              <ArrowLeft className="w-6 h-6 text-blue-400" />
            </button>
            <h1 className="text-4xl font-bold text-white">Clause Heatmap</h1>
          </div>
          <div className="bg-red-900/20 border border-red-800 rounded-lg p-6">
            <div className="flex items-start gap-3">
              <AlertTriangle className="w-6 h-6 text-red-400 flex-shrink-0 mt-1" />
              <div>
                <h3 className="text-red-400 font-semibold mb-1">Error Loading Heatmap</h3>
                <p className="text-red-300">{error}</p>
                <button
                  onClick={loadHeatmap}
                  className="mt-4 px-4 py-2 bg-red-600 hover:bg-red-700 rounded-lg text-white transition-colors"
                >
                  Retry
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!heatmapData || heatmapData.total_clauses === 0) {
    return (
      <div className="min-h-screen bg-slate-900 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center gap-4 mb-6">
            <button
              onClick={() => navigate('/dashboard')}
              className="p-2 hover:bg-slate-800 rounded-lg transition-colors"
            >
              <ArrowLeft className="w-6 h-6 text-blue-400" />
            </button>
            <h1 className="text-4xl font-bold text-white">Clause Heatmap</h1>
          </div>
          <div className="bg-slate-800 border border-slate-700 rounded-lg p-12 text-center">
            <Target className="w-16 h-16 text-slate-600 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-white mb-2">No Clauses Found</h3>
            <p className="text-slate-400 mb-6">
              Upload and process contracts to see clause risk analysis
            </p>
            <button
              onClick={() => navigate('/upload')}
              className="px-6 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg text-white font-semibold transition-colors"
            >
              Upload Contract
            </button>
          </div>
        </div>
      </div>
    );
  }

  const { matrix, metrics, top_risks, type_breakdown } = heatmapData;

  return (
    <div className="min-h-screen bg-slate-900 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/dashboard')}
            className="p-2 hover:bg-slate-800 rounded-lg transition-colors"
          >
            <ArrowLeft className="w-6 h-6 text-blue-400" />
          </button>
          <div className="flex-1">
            <h1 className="text-4xl font-bold text-white">Clause Risk Heatmap</h1>
            <p className="text-slate-400 mt-1">
              Portfolio-wide risk analysis across {heatmapData.contracts_analyzed} contracts
            </p>
          </div>
        </div>

        {/* Metrics Cards */}
        <MetricsGrid metrics={metrics} />

        {/* Main Heatmap */}
        <RiskHeatmapMatrix data={matrix} />

        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <TopRiskyClausesTable risks={top_risks} navigate={navigate} />
          <ClauseTypeBreakdown breakdown={type_breakdown} />
        </div>
      </div>
    </div>
  );
};

// Metrics Grid Component
const MetricsGrid = ({ metrics }) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <MetricCard
        title="Total Clauses"
        value={metrics.total_clauses}
        icon={Activity}
        color="blue"
      />
      <MetricCard
        title="High Risk Clauses"
        value={metrics.high_risk_count}
        icon={AlertTriangle}
        color="red"
        subtitle={`${((metrics.high_risk_count / metrics.total_clauses) * 100).toFixed(1)}% of total`}
      />
      <MetricCard
        title="Average Risk Score"
        value={`${(metrics.average_risk * 100).toFixed(0)}%`}
        icon={TrendingUp}
        color="orange"
      />
      <MetricCard
        title="Portfolio Health"
        value={`${metrics.portfolio_health.toFixed(0)}%`}
        icon={Shield}
        color={metrics.portfolio_health > 70 ? 'green' : metrics.portfolio_health > 40 ? 'yellow' : 'red'}
      />
    </div>
  );
};

// Metric Card Component
const MetricCard = ({ title, value, icon: Icon, color, subtitle }) => {
  const colorClasses = {
    blue: 'from-blue-900/30 to-blue-800/20 border-blue-700/50 text-blue-400',
    red: 'from-red-900/30 to-red-800/20 border-red-700/50 text-red-400',
    orange: 'from-orange-900/30 to-orange-800/20 border-orange-700/50 text-orange-400',
    green: 'from-green-900/30 to-green-800/20 border-green-700/50 text-green-400',
    yellow: 'from-yellow-900/30 to-yellow-800/20 border-yellow-700/50 text-yellow-400',
  };

  const [gradient, border, textColor] = colorClasses[color].split(' ');

  return (
    <div className={`bg-gradient-to-br ${gradient} border ${border} rounded-lg p-5`}>
      <div className="flex items-center justify-between mb-2">
        <span className={`text-sm ${textColor}`}>{title}</span>
        <Icon className={`w-5 h-5 ${textColor}`} />
      </div>
      <div className="text-3xl font-bold text-white">{value}</div>
      {subtitle && <div className="text-xs text-slate-400 mt-1">{subtitle}</div>}
    </div>
  );
};

// Risk Heatmap Matrix Component
const RiskHeatmapMatrix = ({ data }) => {
  // Filter out cells with 0 clauses and map to scatter data
  const scatterData = data
    .filter(cell => cell.count > 0)  // Only show cells with clauses
    .map(cell => ({
      x: cell.likelihood,  // No jitter - clean positions
      y: cell.impact,
      z: Math.max(cell.count * 50, 100),  // Size based on count
      severity: cell.severity,
      count: cell.count,
      contracts: cell.contracts || []
    }));

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'CRITICAL': return '#dc2626';
      case 'HIGH': return '#f97316';
      case 'MEDIUM': return '#facc15';
      case 'LOW': return '#22c55e';
      default: return '#64748b';
    }
  };

  return (
    <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
      <h2 className="text-2xl font-bold text-white mb-4 flex items-center gap-2">
        <Target className="w-6 h-6 text-blue-400" />
        Clause Risk Matrix (Likelihood vs Impact)
      </h2>

      <ResponsiveContainer width="100%" height={500}>
        <ScatterChart margin={{ top: 20, right: 30, bottom: 60, left: 60 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />

          <XAxis
            type="number"
            dataKey="x"
            name="Likelihood"
            domain={[0.5, 5.5]}
            ticks={[1, 2, 3, 4, 5]}
            stroke="#94a3b8"
            label={{
              value: 'Likelihood of Risk Occurrence',
              position: 'bottom',
              offset: 40,
              fill: '#94a3b8'
            }}
          />

          <YAxis
            type="number"
            dataKey="y"
            name="Impact"
            domain={[0.5, 5.5]}
            ticks={[1, 2, 3, 4, 5]}
            stroke="#94a3b8"
            label={{
              value: 'Risk Impact Severity',
              angle: -90,
              position: 'left',
              offset: 40,
              fill: '#94a3b8'
            }}
          />

          <ZAxis
            type="number"
            dataKey="z"
            range={[100, 1000]}
            name="Clause Count"
          />

          <Tooltip
            cursor={{ strokeDasharray: '3 3' }}
            content={({ active, payload }) => {
              if (active && payload && payload.length) {
                const data = payload[0].payload;
                return (
                  <div className="bg-slate-800 border border-slate-600 rounded-lg p-3 shadow-xl max-w-xs">
                    <p className="text-white font-semibold mb-1">
                      {data.severity} Risk
                    </p>
                    <p className="text-slate-300 text-sm">
                      Likelihood: {data.x} | Impact: {data.y}
                    </p>
                    <p className="text-slate-300 text-sm mb-2">
                      Clauses: {data.count}
                    </p>
                    {data.contracts && data.contracts.length > 0 && (
                      <div className="border-t border-slate-600 pt-2 mt-2">
                        <p className="text-slate-400 text-xs font-semibold mb-1">Contracts:</p>
                        <div className="space-y-0.5">
                          {data.contracts.map((contract, idx) => (
                            <p key={idx} className="text-slate-300 text-xs truncate">
                              • {contract}
                            </p>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                );
              }
              return null;
            }}
          />

          <Scatter name="Risk Cells" data={scatterData} shape="circle">
            {scatterData.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={getSeverityColor(entry.severity)}
                fillOpacity={0.85}
              />
            ))}
          </Scatter>
        </ScatterChart>
      </ResponsiveContainer>

      {/* Legend */}
      <div className="flex justify-center gap-6 mt-4">
        <LegendItem color="#22c55e" label="Low Risk" />
        <LegendItem color="#facc15" label="Medium Risk" />
        <LegendItem color="#f97316" label="High Risk" />
        <LegendItem color="#dc2626" label="Critical Risk" />
      </div>
    </div>
  );
};

// Legend Item Component
const LegendItem = ({ color, label }) => (
  <div className="flex items-center gap-2">
    <div className="w-4 h-4 rounded" style={{ backgroundColor: color, opacity: 0.7 }} />
    <span className="text-sm text-slate-300">{label}</span>
  </div>
);

// Top Risky Clauses Table Component
const TopRiskyClausesTable = ({ risks, navigate }) => {
  return (
    <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
      <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
        <AlertTriangle className="w-5 h-5 text-red-400" />
        Top Risky Clauses
      </h2>

      <div className="space-y-3">
        {risks.length === 0 ? (
          <p className="text-slate-400 text-center py-8">No risky clauses found</p>
        ) : (
          risks.slice(0, 5).map((clause, index) => (
            <div
              key={clause.id}
              className="bg-slate-900/50 border border-slate-700 rounded-lg p-4 hover:bg-slate-900 transition-colors cursor-pointer"
              onClick={() => navigate(`/contracts/${clause.contract_id}`)}
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex-1">
                  <h3 className="text-white font-semibold">{clause.clause_name}</h3>
                  <p className="text-sm text-slate-400">{clause.clause_type}</p>
                </div>
                <RiskBadge level={clause.risk_level} />
              </div>
              <p className="text-xs text-slate-400 mb-2 line-clamp-2">{clause.extracted_text}</p>
              <div className="flex items-center gap-4 text-xs text-slate-500">
                <span>Risk: {(clause.risk_score * 100).toFixed(0)}%</span>
                <span>L: {clause.likelihood.toFixed(1)}</span>
                <span>I: {clause.impact.toFixed(1)}</span>
                <span className="truncate">{clause.contract_name}</span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

// Risk Badge Component
const RiskBadge = ({ level }) => {
  const colors = {
    HIGH: 'bg-red-900/30 text-red-400 border-red-700',
    MEDIUM: 'bg-yellow-900/30 text-yellow-400 border-yellow-700',
    LOW: 'bg-green-900/30 text-green-400 border-green-700',
  };

  return (
    <span className={`px-2 py-1 rounded text-xs font-semibold border ${colors[level] || colors.MEDIUM}`}>
      {level || 'UNKNOWN'}
    </span>
  );
};

// Clause Type Breakdown Component
const ClauseTypeBreakdown = ({ breakdown }) => {
  const chartData = breakdown.map(item => ({
    name: item.clause_type.length > 20 ? item.clause_type.substring(0, 20) + '...' : item.clause_type,
    risk: (item.avg_risk * 100).toFixed(0),
    count: item.count,
    high: item.high_risk_count
  }));

  return (
    <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
      <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
        <BarChart3 className="w-5 h-5 text-blue-400" />
        Risk by Clause Type
      </h2>

      {breakdown.length === 0 ? (
        <p className="text-slate-400 text-center py-8">No data available</p>
      ) : (
        <ResponsiveContainer width="100%" height={350}>
          <BarChart data={chartData} margin={{ bottom: 80 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis
              dataKey="name"
              stroke="#94a3b8"
              angle={-45}
              textAnchor="end"
              height={80}
              interval={0}
              tick={{ fontSize: 12 }}
            />
            {/* Left Y-axis for Risk Percentage */}
            <YAxis
              yAxisId="left"
              stroke="#3b82f6"
              label={{ value: 'Avg Risk %', angle: -90, position: 'insideLeft', fill: '#3b82f6' }}
              domain={[0, 100]}
            />
            {/* Right Y-axis for High Risk Count */}
            <YAxis
              yAxisId="right"
              orientation="right"
              stroke="#ef4444"
              label={{ value: 'High Risk Count', angle: 90, position: 'insideRight', fill: '#ef4444' }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1e293b',
                border: '1px solid #475569',
                borderRadius: '0.5rem'
              }}
              formatter={(value, name) => {
                if (name === 'risk') return [`${value}%`, 'Avg Risk'];
                if (name === 'count') return [value, 'Total Clauses'];
                if (name === 'high') return [value, 'High Risk Count'];
                return [value, name];
              }}
            />
            <Legend />
            <Bar dataKey="risk" fill="#3b82f6" name="Avg Risk %" yAxisId="left" />
            <Bar dataKey="high" fill="#ef4444" name="High Risk Count" yAxisId="right" />
          </BarChart>
        </ResponsiveContainer>
      )}
    </div>
  );
};

export default ClauseHeatmap;
