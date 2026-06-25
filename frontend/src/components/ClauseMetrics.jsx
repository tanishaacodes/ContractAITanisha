import { TrendingUp, Activity, AlertCircle, BarChart3 } from 'lucide-react';

export default function ClauseMetrics({ data }) {
  return (
    <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
      {/* Header */}
      <div className="flex items-center text-gray-300 mb-4">
        <BarChart3 className="w-5 h-5 mr-2" />
        <h3 className="font-semibold">Drift Metrics</h3>
      </div>

      {/* Metrics Grid */}
      <div className="space-y-4">
        <MetricRow
          icon={Activity}
          label="Clause Volatility Index"
          value={data.volatility_index.toFixed(2)}
          tooltip="Measures how frequently this clause changes"
          color="text-blue-400"
        />

        <MetricRow
          icon={TrendingUp}
          label="Historical Deviation"
          value={`${data.historical_deviation_pct}%`}
          tooltip="Percentage change from original clause"
          color="text-purple-400"
        />

        <MetricRow
          icon={AlertCircle}
          label="Counterparty Bias Score"
          value={data.counterparty_bias.toFixed(2)}
          tooltip="Likelihood of one-sided clause modifications"
          color="text-orange-400"
        />
      </div>

      {/* Interpretation Guide */}
      <div className="mt-4 pt-4 border-t border-gray-700">
        <p className="text-xs text-gray-500 mb-2 font-semibold">Interpretation Guide</p>
        <div className="space-y-2 text-xs text-gray-400">
          <p>
            <span className="font-semibold text-blue-400">Volatility:</span> 0.0 = stable, 1.0 = highly volatile
          </p>
          <p>
            <span className="font-semibold text-purple-400">Deviation:</span> % change from original text
          </p>
          <p>
            <span className="font-semibold text-orange-400">Bias:</span> 0.0 = balanced, 1.0 = highly biased
          </p>
        </div>
      </div>
    </div>
  );
}

function MetricRow({ icon: Icon, label, value, tooltip, color }) {
  return (
    <div className="group relative">
      <div className="flex items-center justify-between p-3 bg-gray-900/50 rounded-lg hover:bg-gray-900/80 transition">
        <div className="flex items-center">
          <Icon className={`w-4 h-4 mr-3 ${color}`} />
          <p className="text-sm text-gray-400">{label}</p>
        </div>
        <p className={`text-lg font-bold ${color}`}>{value}</p>
      </div>

      {/* Tooltip */}
      {tooltip && (
        <div className="absolute left-0 bottom-full mb-2 hidden group-hover:block z-10">
          <div className="bg-gray-950 border border-gray-700 rounded-lg p-2 text-xs text-gray-300 whitespace-nowrap shadow-xl">
            {tooltip}
            <div className="absolute left-4 top-full w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-gray-700" />
          </div>
        </div>
      )}
    </div>
  );
}
