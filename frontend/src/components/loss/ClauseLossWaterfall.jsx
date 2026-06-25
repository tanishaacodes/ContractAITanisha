import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { FileText, TrendingUp } from 'lucide-react';

const ClauseLossWaterfall = ({ data }) => {
  // Sort data by impact (highest first)
  const sortedData = [...data].sort((a, b) => b.impact_inr - a.impact_inr);

  // Define colors for bars (gradient from red to orange)
  const colors = ['#ef4444', '#f97316', '#fb923c', '#fbbf24', '#fcd34d', '#fde047'];

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-3 shadow-xl">
          <p className="text-white font-semibold text-sm mb-2">{data.clause}</p>
          <p className="text-red-400 text-xs mb-1">
            Loss Contribution: ₹{data.impact_inr.toLocaleString()}
          </p>
          <p className="text-slate-400 text-xs">
            ₹{data.impact_millions}M
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 h-full">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <FileText className="w-5 h-5 text-orange-400" />
          <h3 className="text-sm font-semibold text-white">Clause → Loss Attribution</h3>
        </div>
        <TrendingUp className="w-4 h-4 text-slate-600" />
      </div>

      {/* Chart */}
      {sortedData && sortedData.length > 0 ? (
        <>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart
              data={sortedData}
              margin={{ top: 10, right: 30, left: 0, bottom: 80 }}
              layout="vertical"
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.3} />
              <XAxis
                type="number"
                tick={{ fill: '#94a3b8', fontSize: 11 }}
                stroke="#475569"
                label={{
                  value: 'Loss Contribution (₹ Millions)',
                  position: 'insideBottom',
                  offset: -5,
                  style: { fill: '#64748b', fontSize: 11 }
                }}
              />
              <YAxis
                type="category"
                dataKey="clause"
                tick={{ fill: '#94a3b8', fontSize: 10 }}
                stroke="#475569"
                width={150}
              />
              <Tooltip content={<CustomTooltip />} />
              <Bar
                dataKey="impact_millions"
                radius={[0, 4, 4, 0]}
                animationDuration={1000}
              >
                {sortedData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>

          {/* Clause Details List */}
          <div className="mt-6 space-y-2 max-h-[200px] overflow-y-auto">
            {sortedData.map((item, index) => (
              <div
                key={index}
                className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg"
              >
                <div className="flex items-center gap-3">
                  <div
                    className="w-3 h-3 rounded-full flex-shrink-0"
                    style={{ backgroundColor: colors[index % colors.length] }}
                  />
                  <span className="text-sm text-slate-300">{item.clause}</span>
                </div>
                <div className="text-right">
                  <p className="text-sm font-semibold text-white">₹{item.impact_millions}M</p>
                  <p className="text-xs text-slate-500">{item.impact_inr.toLocaleString()}</p>
                </div>
              </div>
            ))}
          </div>
        </>
      ) : (
        <div className="flex items-center justify-center h-[300px] bg-slate-800/30 rounded-lg">
          <p className="text-slate-500 text-sm">No clause attribution data available</p>
        </div>
      )}

      {/* Interpretation */}
      <div className="mt-6 p-3 bg-orange-900/20 border border-orange-500/30 rounded-lg">
        <p className="text-xs text-orange-400 font-semibold mb-1">How to Read This</p>
        <p className="text-xs text-slate-400">
          Each bar shows how much financial loss is attributable to specific clause types.
          Focus renegotiation efforts on the top contributors to maximize risk reduction.
        </p>
      </div>

      {/* Total Attribution */}
      {sortedData.length > 0 && (
        <div className="mt-4 pt-4 border-t border-slate-800">
          <div className="flex items-center justify-between text-sm">
            <span className="text-slate-400">Total Attributed Loss</span>
            <span className="text-red-400 font-bold">
              ₹{sortedData.reduce((sum, item) => sum + item.impact_millions, 0).toFixed(0)}M
            </span>
          </div>
        </div>
      )}
    </div>
  );
};

export default ClauseLossWaterfall;
