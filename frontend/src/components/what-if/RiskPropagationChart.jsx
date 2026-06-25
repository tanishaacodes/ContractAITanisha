import { useState } from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine
} from 'recharts';
import { Activity, Info } from 'lucide-react';
import useThemeStore from '../../store/themeStore';

/**
 * Risk Propagation Chart with Monte Carlo Confidence Bands
 * Shows risk evolution over time with P50/P75/P90 confidence intervals
 */
export default function RiskPropagationChart({ timeline, monteCarlo, title = 'Risk Propagation' }) {
  const { currentTheme } = useThemeStore();
  const theme = currentTheme;

  const [showBands, setShowBands] = useState(true);

  if (!timeline && !monteCarlo) return null;

  // Prepare chart data
  const prepareChartData = () => {
    const data = [];

    console.log('[RiskPropagationChart] Timeline data:', timeline);
    console.log('[RiskPropagationChart] Monte Carlo data:', monteCarlo);

    // Check different possible data structures
    if (timeline?.timeline && Array.isArray(timeline.timeline)) {
      // Structure: { timeline: [...] }
      console.log('[RiskPropagationChart] Using timeline.timeline array');

      // Calculate CUMULATIVE risk - each step adds to previous
      let cumulativeRisk = 0;

      timeline.timeline.forEach((step, index) => {
        console.log(`[RiskPropagationChart] Step ${index + 1} raw data:`, step);

        // Calculate risk from activated_clauses in THIS step
        if (step.activated_clauses && Array.isArray(step.activated_clauses)) {
          const stepRiskSum = step.activated_clauses.reduce((sum, clause) => {
            return sum + (clause.risk_score || 0);
          }, 0);

          cumulativeRisk = stepRiskSum; // This step's TOTAL active risk
          console.log(`[RiskPropagationChart] Step ${index + 1} calculated from ${step.activated_clauses.length} clauses: ${stepRiskSum}`);
        }
        // If no activated_clauses, check for newly_activated and ADD to cumulative
        else if (step.newly_activated && Array.isArray(step.newly_activated)) {
          const newRisk = step.newly_activated.reduce((sum, clause) => {
            return sum + (clause.risk_score || clause.accumulated_risk || 0);
          }, 0);

          cumulativeRisk += newRisk; // ADD new risk to cumulative
          console.log(`[RiskPropagationChart] Step ${index + 1} added ${step.newly_activated.length} new clauses: +${newRisk}, total: ${cumulativeRisk}`);
        }

        console.log(`[RiskPropagationChart] Step ${index + 1} CUMULATIVE risk value:`, cumulativeRisk);

        data.push({
          step: index + 1,
          risk: cumulativeRisk
        });
      });
    }
    else if (Array.isArray(timeline)) {
      // Timeline IS the array
      console.log('[RiskPropagationChart] Timeline is array directly');

      let cumulativeRisk = 0;

      timeline.forEach((step, index) => {
        console.log(`[RiskPropagationChart] Step ${index + 1} raw data:`, step);

        // Calculate cumulative risk
        if (step.activated_clauses && Array.isArray(step.activated_clauses)) {
          cumulativeRisk = step.activated_clauses.reduce((sum, clause) => {
            return sum + (clause.risk_score || 0);
          }, 0);
        } else if (step.newly_activated && Array.isArray(step.newly_activated)) {
          const newRisk = step.newly_activated.reduce((sum, clause) => {
            return sum + (clause.risk_score || clause.accumulated_risk || 0);
          }, 0);
          cumulativeRisk += newRisk;
        }

        console.log(`[RiskPropagationChart] Step ${index + 1} cumulative risk:`, cumulativeRisk);

        data.push({
          step: index + 1,
          risk: cumulativeRisk
        });
      });
    }
    else if (timeline && typeof timeline === 'object' && timeline.total_risk !== undefined) {
      // Single data point
      console.log('[RiskPropagationChart] Single timeline data point');
      data.push({
        step: 1,
        risk: timeline.total_risk || 0
      });
    }

    console.log('[RiskPropagationChart] Prepared chart data:', data);
    return data;
  };

  const chartData = prepareChartData();

  if (chartData.length === 0) {
    return (
      <div className={`rounded-lg p-6 ${
        theme === 'dark' ? 'bg-gray-800 border border-gray-700' : 'bg-white border border-gray-200'
      }`}>
        <p className={`text-sm ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
          No risk propagation data available
        </p>
      </div>
    );
  }

  const CustomTooltip = ({ active, payload }) => {
    if (!active || !payload || payload.length === 0) return null;

    return (
      <div className={`rounded-lg p-3 shadow-lg border ${
        theme === 'dark'
          ? 'bg-gray-800 border-gray-700'
          : 'bg-white border-gray-300'
      }`}>
        <p className={`text-sm font-semibold mb-2 ${
          theme === 'dark' ? 'text-white' : 'text-gray-900'
        }`}>
          Step {payload[0]?.payload?.step}
        </p>
        {payload.map((entry, index) => (
          <p key={index} className="text-xs" style={{ color: entry.color }}>
            {entry.name}: {entry.value?.toFixed(3)}
          </p>
        ))}
      </div>
    );
  };

  return (
    <div className={`rounded-lg shadow-lg p-6 ${
      theme === 'dark' ? 'bg-gray-800 border border-gray-700' : 'bg-white'
    }`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <Activity className="w-5 h-5 text-blue-500" />
          <h3 className={`text-lg font-semibold ${
            theme === 'dark' ? 'text-white' : 'text-gray-900'
          }`}>
            {title}
          </h3>
        </div>
      </div>

      {/* Info Banner */}
      <div className={`mb-4 p-3 rounded-lg flex items-start space-x-2 ${
        theme === 'dark'
          ? 'bg-blue-900 bg-opacity-30 border border-blue-800'
          : 'bg-blue-50 border border-blue-200'
      }`}>
        <Info className="w-4 h-4 text-blue-500 mt-0.5 flex-shrink-0" />
        <p className={`text-xs ${theme === 'dark' ? 'text-blue-300' : 'text-blue-700'}`}>
          This chart shows how contract risk evolves through propagation steps.
          Risk scores range from 0 (no risk) to higher values indicating greater risk.
        </p>
      </div>

      {/* Chart */}
      <ResponsiveContainer width="100%" height={300}>
        <AreaChart data={chartData}>
          <defs>
            {/* Confidence band gradients */}
            <linearGradient id="p90Fill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.1} />
              <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.05} />
            </linearGradient>
            <linearGradient id="p75Fill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.2} />
              <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.1} />
            </linearGradient>
            <linearGradient id="riskFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#ef4444" stopOpacity={0.4} />
              <stop offset="95%" stopColor="#ef4444" stopOpacity={0.1} />
            </linearGradient>
          </defs>

          <CartesianGrid
            strokeDasharray="3 3"
            stroke={theme === 'dark' ? '#374151' : '#e5e7eb'}
          />

          <XAxis
            dataKey="step"
            label={{ value: 'Propagation Step', position: 'insideBottom', offset: -5 }}
            tick={{ fill: theme === 'dark' ? '#9ca3af' : '#6b7280' }}
            stroke={theme === 'dark' ? '#4b5563' : '#d1d5db'}
          />

          <YAxis
            label={{ value: 'Risk Score', angle: -90, position: 'insideLeft' }}
            tick={{ fill: theme === 'dark' ? '#9ca3af' : '#6b7280' }}
            stroke={theme === 'dark' ? '#4b5563' : '#d1d5db'}
            domain={[0, 'auto']}
          />

          <Tooltip content={<CustomTooltip />} />

          <Legend
            wrapperStyle={{
              paddingTop: '20px',
              color: theme === 'dark' ? '#d1d5db' : '#374151'
            }}
          />

          {/* No confidence bands - Monte Carlo measures exposure (₹), not risk scores */}

          {/* Main risk line */}
          <Area
            type="monotone"
            dataKey="risk"
            stroke="#ef4444"
            strokeWidth={2}
            fill="url(#riskFill)"
            name="Risk Score"
          />

        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
