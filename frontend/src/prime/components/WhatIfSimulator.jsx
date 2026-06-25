import { useState, useEffect } from "react";
import { Sliders, TrendingUp, TrendingDown, AlertTriangle, CheckCircle } from "lucide-react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart } from "recharts";

export default function WhatIfSimulator({ selectedContract, contractData }) {
  const [liabilityCap, setLiabilityCap] = useState(10);
  const [penaltyReduction, setPenaltyReduction] = useState(10);
  const [noticePeriod, setNoticePeriod] = useState(30);
  const [indemnityLimit, setIndemnityLimit] = useState(50);

  const [projections, setProjections] = useState({
    currentRisk: 80,
    projectedRisk: 65,
    currentMargin: 15,
    projectedMargin: 18.5,
    riskReduction: 15,
    marginImprovement: 3.5
  });

  const [chartData, setChartData] = useState([]);

  useEffect(() => {
    calculateProjections();
  }, [liabilityCap, penaltyReduction, noticePeriod, indemnityLimit, selectedContract]);

  const calculateProjections = () => {
    // Base values (can be contract-specific)
    let baseRisk = 80;
    let baseMargin = 15;

    // If a specific contract is selected, use contract-specific values
    if (selectedContract && selectedContract !== "all" && contractData) {
      // Hash-based variance for contract-specific baseline
      const hash = selectedContract.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
      baseRisk = 60 + (hash % 30);
      baseMargin = 12 + (hash % 8);
    }

    // Calculate risk reduction based on parameters
    const liabilityCapImpact = (liabilityCap / 40) * 15; // Up to 15% risk reduction
    const penaltyImpact = (penaltyReduction / 10) * 12; // Up to 12% risk reduction
    const noticeImpact = (noticePeriod / 90) * 8; // Up to 8% risk reduction
    const indemnityImpact = (indemnityLimit / 100) * 10; // Up to 10% risk reduction

    const totalRiskReduction = liabilityCapImpact + penaltyImpact + noticeImpact + indemnityImpact;
    const projectedRisk = Math.max(20, baseRisk - totalRiskReduction);

    // Calculate margin improvement
    const marginImprovement = totalRiskReduction * 0.25; // Each % of risk reduction = 0.25% margin improvement
    const projectedMargin = Math.min(30, baseMargin + marginImprovement);

    setProjections({
      currentRisk: baseRisk,
      projectedRisk: Math.round(projectedRisk * 10) / 10,
      currentMargin: baseMargin,
      projectedMargin: Math.round(projectedMargin * 10) / 10,
      riskReduction: Math.round(totalRiskReduction * 10) / 10,
      marginImprovement: Math.round(marginImprovement * 10) / 10
    });

    // Generate chart data showing progression
    const steps = 10;
    const data = Array.from({ length: steps + 1 }, (_, i) => {
      const progress = i / steps;
      return {
        step: i,
        risk: baseRisk - (totalRiskReduction * progress),
        margin: baseMargin + (marginImprovement * progress),
        name: `${i * 10}%`
      };
    });
    setChartData(data);
  };

  const resetToDefaults = () => {
    setLiabilityCap(10);
    setPenaltyReduction(10);
    setNoticePeriod(30);
    setIndemnityLimit(50);
  };

  const getRiskColor = (risk) => {
    if (risk >= 70) return "text-red-400";
    if (risk >= 50) return "text-yellow-400";
    return "text-green-400";
  };

  return (
    <div className="rounded-2xl bg-gradient-to-br from-white/5 to-white/10 p-6 shadow-2xl backdrop-blur-lg border border-white/10">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-xl font-bold text-white flex items-center gap-2">
          <div className="w-1 h-6 bg-gradient-to-b from-blue-500 to-purple-600 rounded-full" />
          What-If Scenario Simulator
          <span className="text-xs text-gray-400 font-normal">
            ({selectedContract === "all" ? "Portfolio" : "Contract"})
          </span>
        </h3>
        <Sliders className="w-5 h-5 text-blue-400" />
      </div>

      {/* Control Sliders */}
      <div className="space-y-6 mb-6">
        {/* Liability Cap */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="text-sm text-gray-300 font-medium">
              Liability Cap (Multiple of Annual Fees)
            </label>
            <span className="text-sm font-bold text-white bg-blue-500/20 px-2 py-1 rounded">
              {liabilityCap}x
            </span>
          </div>
          <input
            type="range"
            min="0"
            max="40"
            value={liabilityCap}
            onChange={(e) => setLiabilityCap(Number(e.target.value))}
            className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer slider-blue"
          />
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>None</span>
            <span>Unlimited</span>
          </div>
        </div>

        {/* Penalty Reduction */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="text-sm text-gray-300 font-medium">
              Penalty Reduction (%)
            </label>
            <span className="text-sm font-bold text-white bg-purple-500/20 px-2 py-1 rounded">
              {penaltyReduction}%
            </span>
          </div>
          <input
            type="range"
            min="0"
            max="10"
            value={penaltyReduction}
            onChange={(e) => setPenaltyReduction(Number(e.target.value))}
            className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer slider-purple"
          />
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>0%</span>
            <span>10%</span>
          </div>
        </div>

        {/* Notice Period */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="text-sm text-gray-300 font-medium">
              Termination Notice Period (Days)
            </label>
            <span className="text-sm font-bold text-white bg-emerald-500/20 px-2 py-1 rounded">
              {noticePeriod} days
            </span>
          </div>
          <input
            type="range"
            min="0"
            max="90"
            step="30"
            value={noticePeriod}
            onChange={(e) => setNoticePeriod(Number(e.target.value))}
            className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer slider-emerald"
          />
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>0</span>
            <span>30</span>
            <span>60</span>
            <span>90</span>
          </div>
        </div>

        {/* Indemnity Limit */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="text-sm text-gray-300 font-medium">
              Indemnity Scope Limit (%)
            </label>
            <span className="text-sm font-bold text-white bg-amber-500/20 px-2 py-1 rounded">
              {indemnityLimit}%
            </span>
          </div>
          <input
            type="range"
            min="0"
            max="100"
            value={indemnityLimit}
            onChange={(e) => setIndemnityLimit(Number(e.target.value))}
            className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer slider-amber"
          />
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>Direct Only</span>
            <span>All Damages</span>
          </div>
        </div>
      </div>

      {/* Projection Results */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="bg-gradient-to-br from-red-500/10 to-red-600/5 border border-red-500/30 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle className="w-4 h-4 text-red-400" />
            <p className="text-xs text-gray-400">Risk Score</p>
          </div>
          <div className="flex items-baseline gap-2">
            <p className={`text-2xl font-bold ${getRiskColor(projections.currentRisk)}`}>
              {projections.currentRisk}
            </p>
            <TrendingDown className="w-4 h-4 text-green-400" />
            <p className="text-xl font-bold text-green-400">
              {projections.projectedRisk}
            </p>
          </div>
          <p className="text-xs text-green-400 mt-1">
            ↓ {projections.riskReduction}% Reduction
          </p>
        </div>

        <div className="bg-gradient-to-br from-green-500/10 to-green-600/5 border border-green-500/30 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <CheckCircle className="w-4 h-4 text-green-400" />
            <p className="text-xs text-gray-400">Profit Margin</p>
          </div>
          <div className="flex items-baseline gap-2">
            <p className="text-2xl font-bold text-white">
              {projections.currentMargin}%
            </p>
            <TrendingUp className="w-4 h-4 text-green-400" />
            <p className="text-xl font-bold text-green-400">
              {projections.projectedMargin}%
            </p>
          </div>
          <p className="text-xs text-green-400 mt-1">
            ↑ {projections.marginImprovement}% Improvement
          </p>
        </div>
      </div>

      {/* Progression Chart */}
      <div className="bg-slate-900/50 rounded-lg p-4 mb-4">
        <p className="text-sm text-gray-400 mb-3">Projected Impact Over Time</p>
        <ResponsiveContainer width="100%" height={180}>
          <AreaChart data={chartData}>
            <defs>
              <linearGradient id="riskGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#ef4444" stopOpacity={0.8}/>
                <stop offset="95%" stopColor="#ef4444" stopOpacity={0}/>
              </linearGradient>
              <linearGradient id="marginGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#10b981" stopOpacity={0.8}/>
                <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis dataKey="name" stroke="#64748b" style={{ fontSize: '10px' }} />
            <YAxis stroke="#64748b" style={{ fontSize: '10px' }} />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1e293b',
                border: '1px solid #334155',
                borderRadius: '8px',
                fontSize: '12px'
              }}
            />
            <Area
              type="monotone"
              dataKey="risk"
              stroke="#ef4444"
              fillOpacity={1}
              fill="url(#riskGradient)"
              name="Risk Score"
            />
            <Area
              type="monotone"
              dataKey="margin"
              stroke="#10b981"
              fillOpacity={1}
              fill="url(#marginGradient)"
              name="Margin %"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Reset Button */}
      <button
        onClick={resetToDefaults}
        className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white py-3 rounded-lg font-semibold transition-all transform hover:scale-105"
      >
        Reset to Defaults
      </button>

      {/* Custom Slider Styles */}
      <style jsx>{`
        .slider-blue::-webkit-slider-thumb {
          appearance: none;
          width: 20px;
          height: 20px;
          background: linear-gradient(135deg, #3b82f6, #8b5cf6);
          cursor: pointer;
          border-radius: 50%;
          box-shadow: 0 0 10px rgba(59, 130, 246, 0.5);
        }
        .slider-purple::-webkit-slider-thumb {
          appearance: none;
          width: 20px;
          height: 20px;
          background: linear-gradient(135deg, #8b5cf6, #a855f7);
          cursor: pointer;
          border-radius: 50%;
          box-shadow: 0 0 10px rgba(139, 92, 246, 0.5);
        }
        .slider-emerald::-webkit-slider-thumb {
          appearance: none;
          width: 20px;
          height: 20px;
          background: linear-gradient(135deg, #10b981, #14b8a6);
          cursor: pointer;
          border-radius: 50%;
          box-shadow: 0 0 10px rgba(16, 185, 129, 0.5);
        }
        .slider-amber::-webkit-slider-thumb {
          appearance: none;
          width: 20px;
          height: 20px;
          background: linear-gradient(135deg, #f59e0b, #f97316);
          cursor: pointer;
          border-radius: 50%;
          box-shadow: 0 0 10px rgba(245, 158, 11, 0.5);
        }
      `}</style>
    </div>
  );
}
