import { useState, useEffect } from "react";
import { LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer, Legend } from "recharts";
import { motion } from "framer-motion";
import { Activity } from "lucide-react";

export default function DriftTrend({ selectedContract }) {
  const [data, setData] = useState([]);
  const [driftPercent, setDriftPercent] = useState(23);

  useEffect(() => {
    // Generate drift data based on selection
    const generateData = () => {
      // Generate contract-specific baseline using hash of selectedContract
      let baseline = 85;
      if (selectedContract && selectedContract !== "all") {
        // Create deterministic baseline from contract ID
        const hash = selectedContract.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
        baseline = 60 + (hash % 30); // Range: 60-90
      }

      const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"];
      const driftRate = selectedContract === "all" ? 2.5 : 3 + (baseline % 3); // Different drift rates

      return months.map((month, index) => ({
        month,
        original: baseline,
        current: Math.max(baseline - (index * driftRate) - Math.random() * 5, 40),
        threshold: 90
      }));
    };

    const newData = generateData();
    setData(newData);

    // Calculate drift percentage
    if (newData.length > 0) {
      const latestDrift = ((newData[0].original - newData[newData.length - 1].current) / newData[0].original) * 100;
      setDriftPercent(Math.round(latestDrift));
    }
  }, [selectedContract]);
  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-slate-900/95 border border-cyan-500/30 rounded-lg p-3 shadow-xl">
          <p className="text-white text-sm mb-2">{payload[0].payload.month}</p>
          {payload.map((entry, index) => (
            <p key={index} className="text-sm" style={{ color: entry.color }}>
              {entry.name}: {entry.value}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="rounded-2xl bg-gradient-to-br from-white/5 to-white/10 p-6 shadow-2xl backdrop-blur-lg border border-white/10">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-xl font-bold text-white flex items-center gap-2">
          <div className="w-1 h-6 bg-gradient-to-b from-purple-500 to-pink-600 rounded-full" />
          Contract Drift Analysis
          <span className="text-xs text-gray-400 font-normal">
            {selectedContract === "all" ? "(Portfolio Avg)" : "(Contract)"}
          </span>
        </h3>
        <Activity className="w-5 h-5 text-purple-400" />
      </div>

      {driftPercent > 15 && (
        <div className="mb-4 bg-yellow-500/10 border border-yellow-500/20 rounded-lg p-3">
          <p className="text-xs text-yellow-400 flex items-center gap-2">
            <span className="w-2 h-2 bg-yellow-400 rounded-full animate-pulse" />
            Alert: {driftPercent}% drift detected from original terms
          </p>
        </div>
      )}

      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis
            dataKey="month"
            stroke="#9ca3af"
            tick={{ fill: "#9ca3af", fontSize: 11 }}
          />
          <YAxis
            stroke="#9ca3af"
            tick={{ fill: "#9ca3af", fontSize: 11 }}
            domain={[0, 100]}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend
            wrapperStyle={{ color: "#e5e7eb", fontSize: "12px" }}
            iconType="circle"
          />
          <Line
            type="monotone"
            dataKey="original"
            stroke="#10b981"
            strokeWidth={2}
            name="Original Terms"
            dot={{ r: 4 }}
          />
          <Line
            type="monotone"
            dataKey="current"
            stroke="#a855f7"
            strokeWidth={2}
            name="Current Terms"
            dot={{ r: 4 }}
          />
          <Line
            type="monotone"
            dataKey="threshold"
            stroke="#ef4444"
            strokeWidth={1}
            strokeDasharray="5 5"
            name="Risk Threshold"
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
