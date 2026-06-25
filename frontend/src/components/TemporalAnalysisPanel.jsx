import { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, Minus, AlertTriangle, Activity } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { getTemporalAnalysis } from '../services/searchIntelligence';

function TemporalAnalysisPanel({ contractId }) {
  const [trendData, setTrendData] = useState(null);
  const [predictionData, setPredictionData] = useState(null);
  const [spikeData, setSpikeData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [activeView, setActiveView] = useState('trend'); // 'trend', 'predict', 'spike'

  useEffect(() => {
    if (contractId) {
      loadData();
    }
  }, [contractId, activeView]);

  const loadData = async () => {
    if (!contractId) return;
    setLoading(true);
    try {
      const data = await getTemporalAnalysis(contractId, activeView, 90, 30);
      if (activeView === 'trend') {
        setTrendData(data.result);
      } else if (activeView === 'predict') {
        setPredictionData(data.result);
      } else if (activeView === 'spike') {
        setSpikeData(data.result);
      }
    } catch (error) {
      console.error('Temporal analysis error:', error);
    } finally {
      setLoading(false);
    }
  };

  const getTrendIcon = (trend) => {
    if (trend === 'INCREASING') return <TrendingUp size={16} className="text-red-400" />;
    if (trend === 'DECREASING') return <TrendingDown size={16} className="text-emerald-400" />;
    return <Minus size={16} className="text-slate-400" />;
  };

  const getTrendColor = (trend) => {
    if (trend === 'INCREASING') return 'text-red-400';
    if (trend === 'DECREASING') return 'text-emerald-400';
    return 'text-slate-400';
  };

  const renderTrendView = () => {
    if (!trendData) return null;
    if (trendData.error) return <div className="text-slate-400 text-sm">{trendData.error}</div>;

    const chartData = trendData.timestamps?.map((ts, i) => ({
      date: new Date(ts).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      risk: trendData.risk_scores[i]
    })) || [];

    return (
      <div className="space-y-4">
        <div className="grid grid-cols-3 gap-3">
          <div className="bg-slate-900/50 border border-slate-700/30 rounded-lg p-3">
            <div className="text-xs text-slate-400 mb-1">Trend</div>
            <div className={`text-lg font-bold ${getTrendColor(trendData.trend)} flex items-center gap-2`}>
              {getTrendIcon(trendData.trend)}
              {trendData.trend}
            </div>
          </div>
          <div className="bg-slate-900/50 border border-slate-700/30 rounded-lg p-3">
            <div className="text-xs text-slate-400 mb-1">Current Risk</div>
            <div className="text-lg font-bold text-cyan-400">
              {(trendData.current_risk * 100).toFixed(1)}%
            </div>
          </div>
          <div className="bg-slate-900/50 border border-slate-700/30 rounded-lg p-3">
            <div className="text-xs text-slate-400 mb-1">Change</div>
            <div className={`text-lg font-bold ${trendData.risk_change > 0 ? 'text-red-400' : 'text-emerald-400'}`}>
              {trendData.risk_change > 0 ? '+' : ''}{(trendData.risk_change * 100).toFixed(1)}%
            </div>
          </div>
        </div>

        <div className="bg-slate-900/50 border border-slate-700/30 rounded-lg p-4">
          <h4 className="text-white text-sm font-semibold mb-3">Risk Trend (Last 90 Days)</h4>
          <ResponsiveContainer width="100%" height={180}>
            <LineChart data={chartData}>
              <XAxis
                dataKey="date"
                tick={{ fill: '#94a3b8', fontSize: 10 }}
                angle={-45}
                textAnchor="end"
                height={60}
              />
              <YAxis
                tick={{ fill: '#94a3b8', fontSize: 10 }}
                tickFormatter={v => `${(v * 100).toFixed(0)}%`}
              />
              <Tooltip
                contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8 }}
                formatter={v => [`${(v * 100).toFixed(1)}%`, 'Risk Score']}
              />
              <Line
                type="monotone"
                dataKey="risk"
                stroke={trendData.trend === 'INCREASING' ? '#F16667' : trendData.trend === 'DECREASING' ? '#68BC00' : '#4C8EDA'}
                strokeWidth={2}
                dot={{ fill: '#fff', r: 3 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-slate-900/50 border border-slate-700/30 rounded-lg p-3">
          <div className="grid grid-cols-2 gap-3 text-xs">
            <div>
              <span className="text-slate-400">Volatility:</span>
              <span className="text-white ml-2 font-medium">{trendData.volatility?.toFixed(3)}</span>
            </div>
            <div>
              <span className="text-slate-400">Severity:</span>
              <span className={`ml-2 font-medium ${
                trendData.severity === 'HIGH' ? 'text-red-400' :
                trendData.severity === 'MEDIUM' ? 'text-yellow-400' :
                'text-emerald-400'
              }`}>{trendData.severity}</span>
            </div>
          </div>
        </div>
      </div>
    );
  };

  const renderPredictionView = () => {
    if (!predictionData) return null;
    if (predictionData.error) return <div className="text-slate-400 text-sm">{predictionData.error}</div>;

    return (
      <div className="space-y-4">
        <div className="grid grid-cols-3 gap-3">
          <div className="bg-slate-900/50 border border-slate-700/30 rounded-lg p-3">
            <div className="text-xs text-slate-400 mb-1">Current Risk</div>
            <div className="text-lg font-bold text-cyan-400">
              {(predictionData.current_risk * 100).toFixed(1)}%
            </div>
          </div>
          <div className="bg-slate-900/50 border border-slate-700/30 rounded-lg p-3">
            <div className="text-xs text-slate-400 mb-1">Predicted Risk (30d)</div>
            <div className={`text-lg font-bold ${predictionData.predicted_risk > predictionData.current_risk ? 'text-red-400' : 'text-emerald-400'}`}>
              {(predictionData.predicted_risk * 100).toFixed(1)}%
            </div>
          </div>
          <div className="bg-slate-900/50 border border-slate-700/30 rounded-lg p-3">
            <div className="text-xs text-slate-400 mb-1">Confidence</div>
            <div className="text-lg font-bold text-blue-400">
              {(predictionData.confidence * 100).toFixed(0)}%
            </div>
          </div>
        </div>

        {predictionData.warning && (
          <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 flex items-start gap-3">
            <AlertTriangle size={20} className="text-red-400 shrink-0 mt-0.5" />
            <div>
              <div className="text-red-400 font-semibold text-sm mb-1">High Risk Warning</div>
              <div className="text-slate-300 text-xs">
                Predicted risk score exceeds 70% threshold. Recommend immediate review and risk mitigation planning.
              </div>
            </div>
          </div>
        )}

        <div className="bg-slate-900/50 border border-slate-700/30 rounded-lg p-3">
          <div className="text-xs text-slate-400 mb-2">Trend Direction</div>
          <div className={`flex items-center gap-2 ${getTrendColor(predictionData.trend)}`}>
            {getTrendIcon(predictionData.trend)}
            <span className="font-medium">{predictionData.trend}</span>
            <span className="text-slate-500 ml-auto">Slope: {predictionData.slope?.toFixed(6)}</span>
          </div>
        </div>
      </div>
    );
  };

  const renderSpikeView = () => {
    if (!spikeData) return null;

    if (!spikeData.spike_detected) {
      return (
        <div className="bg-slate-900/50 border border-slate-700/30 rounded-lg p-8 text-center">
          <Activity size={32} className="text-slate-600 mx-auto mb-3" />
          <div className="text-slate-400 text-sm">No significant risk spikes detected</div>
          <div className="text-slate-500 text-xs mt-1">Risk changes are within normal range</div>
        </div>
      );
    }

    return (
      <div className="space-y-4">
        <div className={`border rounded-lg p-4 ${
          spikeData.severity === 'CRITICAL'
            ? 'bg-red-500/10 border-red-500/30'
            : 'bg-orange-500/10 border-orange-500/30'
        }`}>
          <div className="flex items-start gap-3">
            <AlertTriangle size={24} className={spikeData.severity === 'CRITICAL' ? 'text-red-400' : 'text-orange-400'} />
            <div className="flex-1">
              <div className={`font-semibold text-sm mb-2 ${spikeData.severity === 'CRITICAL' ? 'text-red-400' : 'text-orange-400'}`}>
                {spikeData.severity} Risk Spike Detected
              </div>
              <div className="text-slate-300 text-xs">
                Risk {spikeData.direction === 'UP' ? 'increased' : 'decreased'} by {(spikeData.magnitude * 100).toFixed(1)}%
                at {new Date(spikeData.timestamp).toLocaleString()}
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div className="bg-slate-900/50 border border-slate-700/30 rounded-lg p-3">
            <div className="text-xs text-slate-400 mb-1">Previous Risk</div>
            <div className="text-lg font-bold text-slate-300">
              {(spikeData.previous_risk * 100).toFixed(1)}%
            </div>
          </div>
          <div className="bg-slate-900/50 border border-slate-700/30 rounded-lg p-3">
            <div className="text-xs text-slate-400 mb-1">Current Risk</div>
            <div className={`text-lg font-bold ${spikeData.direction === 'UP' ? 'text-red-400' : 'text-emerald-400'}`}>
              {(spikeData.current_risk * 100).toFixed(1)}%
            </div>
          </div>
        </div>
      </div>
    );
  };

  if (!contractId) {
    return (
      <div className="bg-slate-800/60 border border-slate-700/50 rounded-xl p-8 text-center">
        <Activity size={32} className="text-slate-600 mx-auto mb-3" />
        <div className="text-slate-400 text-sm">Select a contract to view temporal analysis</div>
      </div>
    );
  }

  return (
    <div className="bg-slate-800/60 border border-slate-700/50 rounded-xl p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-white font-semibold flex items-center gap-2">
          <Activity size={16} className="text-cyan-400" />
          Temporal Risk Analysis
        </h3>
        <div className="flex gap-2">
          <button
            onClick={() => setActiveView('trend')}
            className={`px-3 py-1.5 text-xs rounded-lg transition ${
              activeView === 'trend'
                ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30'
                : 'bg-slate-700 text-slate-400 hover:text-slate-300'
            }`}
          >
            Trend
          </button>
          <button
            onClick={() => setActiveView('predict')}
            className={`px-3 py-1.5 text-xs rounded-lg transition ${
              activeView === 'predict'
                ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30'
                : 'bg-slate-700 text-slate-400 hover:text-slate-300'
            }`}
          >
            Predict
          </button>
          <button
            onClick={() => setActiveView('spike')}
            className={`px-3 py-1.5 text-xs rounded-lg transition ${
              activeView === 'spike'
                ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30'
                : 'bg-slate-700 text-slate-400 hover:text-slate-300'
            }`}
          >
            Spikes
          </button>
        </div>
      </div>

      {loading ? (
        <div className="text-center py-8">
          <div className="inline-block w-6 h-6 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin" />
          <div className="text-slate-400 text-sm mt-2">Loading analysis...</div>
        </div>
      ) : (
        <>
          {activeView === 'trend' && renderTrendView()}
          {activeView === 'predict' && renderPredictionView()}
          {activeView === 'spike' && renderSpikeView()}
        </>
      )}
    </div>
  );
}

export default TemporalAnalysisPanel;
