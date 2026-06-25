/**
 * Gartner-Style Magic Quadrant Component
 * Reusable scatter plot with 50/50 reference lines
 */
import React from 'react';
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  ResponsiveContainer,
  Legend
} from 'recharts';

const MagicQuadrant = ({
  data,
  xLabel,
  yLabel,
  onDotClick,
  showLegend = true
}) => {
  // Group data by business unit for colored clusters
  const groupByBU = (data) => {
    return data.reduce((acc, item) => {
      const bu = item.business_unit || 'Others';
      if (!acc[bu]) acc[bu] = [];
      acc[bu].push(item);
      return acc;
    }, {});
  };

  const groupedData = groupByBU(data);

  // Create unique key based on data + hash to force re-render when data changes
  const dataHash = data.length > 0
    ? data.slice(0, 5).map(d => `${d.x.toFixed(1)}-${d.y.toFixed(1)}`).join('_')
    : 'empty';
  const dataKey = `chart-${data.length}-${dataHash}`;

  // Custom tooltip
  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload[0]) {
      const data = payload[0].payload;
      return (
        <div className="bg-white p-3 border border-gray-300 rounded shadow-lg">
          <p className="font-semibold text-sm">{data.label}</p>
          <p className="text-xs text-gray-600">BU: {data.business_unit}</p>
          <p className="text-xs">{xLabel}: {data.x.toFixed(1)}</p>
          <p className="text-xs">{yLabel}: {data.y.toFixed(1)}</p>
        </div>
      );
    }
    return null;
  };

  // Handle dot click
  const handleClick = (data) => {
    if (onDotClick) {
      onDotClick(data);
    }
  };

  return (
    <div key={`wrapper-${dataKey}`} style={{ width: '100%', height: 500 }}>
      <ResponsiveContainer width="100%" height={500} key={`container-${dataKey}`}>
      <ScatterChart
        key={`scatter-${dataKey}`}
        margin={{ top: 20, right: 140, bottom: 60, left: 60 }}
      >
        <CartesianGrid strokeDasharray="3 3" />

        <XAxis
          type="number"
          dataKey="x"
          domain={[0, 100]}
          label={{
            value: xLabel,
            position: 'insideBottom',
            offset: -10,
            style: { fontSize: 14, fontWeight: 'bold' }
          }}
          tick={{ fontSize: 12 }}
        />

        <YAxis
          type="number"
          dataKey="y"
          domain={[0, 100]}
          label={{
            value: yLabel,
            angle: -90,
            position: 'insideLeft',
            style: { fontSize: 14, fontWeight: 'bold' }
          }}
          tick={{ fontSize: 12 }}
        />

        {/* Quadrant dividers at 50/50 */}
        <ReferenceLine x={50} stroke="#999" strokeWidth={2} strokeDasharray="5 5" />
        <ReferenceLine y={50} stroke="#999" strokeWidth={2} strokeDasharray="5 5" />

        <Tooltip content={<CustomTooltip />} />

        {showLegend && (
          <Legend
            verticalAlign="middle"
            align="right"
            layout="vertical"
            iconType="circle"
            wrapperStyle={{
              paddingLeft: '20px',
              fontSize: '13px'
            }}
          />
        )}

        {/* Render each business unit as separate scatter */}
        {Object.entries(groupedData).map(([bu, points]) => (
          <Scatter
            key={`${bu}-${points.length}-${points[0]?.y || 0}`}
            name={bu}
            data={points}
            fill={points[0]?.color || '#1976d2'}
            onClick={handleClick}
            cursor="pointer"
            isAnimationActive={true}
            animationDuration={800}
            animationEasing="ease-out"
            shape="circle"
            r={8}
            stroke="#fff"
            strokeWidth={2}
          />
        ))}
      </ScatterChart>
    </ResponsiveContainer>
    </div>
  );
};

export default MagicQuadrant;
