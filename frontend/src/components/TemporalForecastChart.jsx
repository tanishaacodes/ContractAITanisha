/**
 * Temporal Forecast Chart - Risk Evolution Over Time
 * Line/Area chart showing risk probability trajectories
 */

import React from 'react';
import {
  LineChart,
  Line,
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

const TemporalForecastChart = ({
  forecastData,
  timeUnit = 'months',
  showCriticalThreshold = true,
  criticalThreshold = 0.60,
  height = 400,
  chartType = 'line' // 'line' or 'area'
}) => {
  if (!forecastData || !forecastData.trajectories) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height,
        backgroundColor: '#F3F4F6',
        borderRadius: '8px'
      }}>
        <p style={{ color: '#6B7280' }}>No forecast data available</p>
      </div>
    );
  }

  // Transform trajectories into chart data
  const chartData = transformTrajectories(forecastData.trajectories);

  // Get outcomes to display
  const outcomes = Object.keys(forecastData.trajectories);

  // Color mapping for different outcomes
  const colorMap = {
    'fm_invocation': '#DC2626',
    'project_delay': '#EA580C',
    'cost_overrun': '#F59E0B',
    'contract_suspension': '#8B5CF6',
    'contract_termination': '#EF4444'
  };

  const ChartComponent = chartType === 'area' ? AreaChart : LineChart;
  const DataComponent = chartType === 'area' ? Area : Line;

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div style={{
          backgroundColor: 'white',
          padding: '12px',
          border: '1px solid #E5E7EB',
          borderRadius: '6px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
        }}>
          <p style={{ margin: '0 0 8px 0', fontWeight: 'bold', color: '#1F2937' }}>
            Time: {label} {timeUnit}
          </p>
          {payload.map((entry, index) => (
            <div key={index} style={{ margin: '4px 0', fontSize: '13px' }}>
              <span style={{ color: entry.color, fontWeight: 'bold' }}>
                {entry.name}:
              </span>
              {' '}
              <span style={{ color: '#4B5563' }}>
                {(entry.value * 100).toFixed(1)}%
              </span>
            </div>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <div>
      {/* Chart */}
      <ResponsiveContainer width="100%" height={height}>
        <ChartComponent data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
          <XAxis
            dataKey="time_step"
            label={{ value: `Time (${timeUnit})`, position: 'insideBottom', offset: -5 }}
            tick={{ fontSize: 12 }}
          />
          <YAxis
            label={{ value: 'Probability', angle: -90, position: 'insideLeft' }}
            tick={{ fontSize: 12 }}
            tickFormatter={(value) => `${(value * 100).toFixed(0)}%`}
            domain={[0, 1]}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend
            wrapperStyle={{ paddingTop: '20px' }}
            formatter={(value) => value.replace(/_/g, ' ').toUpperCase()}
          />

          {/* Critical threshold line */}
          {showCriticalThreshold && (
            <ReferenceLine
              y={criticalThreshold}
              stroke="#DC2626"
              strokeDasharray="5 5"
              label={{
                value: `Critical (${(criticalThreshold * 100).toFixed(0)}%)`,
                position: 'right',
                fill: '#DC2626',
                fontSize: 11
              }}
            />
          )}

          {/* Plot each outcome */}
          {outcomes.map((outcome, index) => (
            <DataComponent
              key={outcome}
              type="monotone"
              dataKey={outcome}
              stroke={colorMap[outcome] || `hsl(${index * 60}, 70%, 50%)`}
              fill={colorMap[outcome] || `hsl(${index * 60}, 70%, 50%)`}
              fillOpacity={chartType === 'area' ? 0.3 : 1}
              strokeWidth={2}
              dot={{ r: 3 }}
              activeDot={{ r: 5 }}
              name={outcome.replace(/_/g, ' ')}
            />
          ))}
        </ChartComponent>
      </ResponsiveContainer>

      {/* Trajectory Analysis Summary */}
      {forecastData.trajectory_analysis && (
        <div style={{
          marginTop: '20px',
          padding: '15px',
          backgroundColor: '#F9FAFB',
          borderRadius: '8px',
          border: '1px solid #E5E7EB'
        }}>
          <h4 style={{ margin: '0 0 12px 0', fontSize: '14px', fontWeight: 'bold', color: '#1F2937' }}>
            Trajectory Analysis
          </h4>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '12px' }}>
            {outcomes.map(outcome => {
              const analysis = forecastData.trajectory_analysis[outcome];
              if (!analysis) return null;

              return (
                <div key={outcome} style={{
                  padding: '12px',
                  backgroundColor: 'white',
                  borderRadius: '6px',
                  border: '1px solid #E5E7EB'
                }}>
                  <div style={{ fontWeight: 'bold', marginBottom: '8px', color: '#374151', fontSize: '13px' }}>
                    {outcome.replace(/_/g, ' ').toUpperCase()}
                  </div>
                  <div style={{ fontSize: '12px', color: '#6B7280', marginBottom: '4px' }}>
                    <strong>Trend:</strong>
                    <span style={{
                      marginLeft: '4px',
                      color: analysis.trend === 'increasing' ? '#DC2626' : '#10B981',
                      fontWeight: 'bold'
                    }}>
                      {analysis.trend} ({(analysis.trend_magnitude * 100).toFixed(1)}%)
                    </span>
                  </div>
                  <div style={{ fontSize: '12px', color: '#6B7280', marginBottom: '4px' }}>
                    <strong>Peak:</strong> {(analysis.peak_probability * 100).toFixed(1)}%
                    at step {analysis.peak_time_step}
                  </div>
                  <div style={{ fontSize: '12px', color: '#6B7280' }}>
                    <strong>Volatility:</strong> {(analysis.volatility * 100).toFixed(1)}%
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Critical Windows */}
      {forecastData.critical_windows && forecastData.critical_windows.length > 0 && (
        <div style={{
          marginTop: '15px',
          padding: '15px',
          backgroundColor: '#FEF2F2',
          borderRadius: '8px',
          border: '1px solid #FEE2E2'
        }}>
          <h4 style={{ margin: '0 0 10px 0', fontSize: '14px', fontWeight: 'bold', color: '#991B1B' }}>
            ⚠️ Critical Time Windows
          </h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {forecastData.critical_windows.slice(0, 5).map((window, index) => (
              <div key={index} style={{
                fontSize: '12px',
                padding: '8px',
                backgroundColor: 'white',
                borderRadius: '4px'
              }}>
                <span style={{ fontWeight: 'bold', color: '#DC2626' }}>
                  {window.outcome.replace(/_/g, ' ').toUpperCase()}:
                </span>
                {' '}
                Steps {window.start_time}-{window.end_time}
                ({window.duration} {timeUnit}, peak: {(window.max_probability * 100).toFixed(0)}%)
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recommendations */}
      {forecastData.recommendations && forecastData.recommendations.length > 0 && (
        <div style={{
          marginTop: '15px',
          padding: '15px',
          backgroundColor: '#F0FDF4',
          borderRadius: '8px',
          border: '1px solid #BBF7D0'
        }}>
          <h4 style={{ margin: '0 0 10px 0', fontSize: '14px', fontWeight: 'bold', color: '#166534' }}>
            💡 Recommendations
          </h4>
          <ul style={{ margin: 0, paddingLeft: '20px', fontSize: '12px', color: '#166534' }}>
            {forecastData.recommendations.slice(0, 5).map((rec, index) => (
              <li key={index} style={{ marginBottom: '4px' }}>{rec}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

// Helper function to transform trajectories into chart data
const transformTrajectories = (trajectories) => {
  const outcomes = Object.keys(trajectories);
  if (outcomes.length === 0) return [];

  const timeSteps = trajectories[outcomes[0]].length;
  const chartData = [];

  for (let t = 0; t < timeSteps; t++) {
    const dataPoint = { time_step: t };

    outcomes.forEach(outcome => {
      dataPoint[outcome] = trajectories[outcome][t].probability;
    });

    chartData.push(dataPoint);
  }

  return chartData;
};

export default TemporalForecastChart;
