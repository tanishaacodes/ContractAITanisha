import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Sliders, TrendingDown, DollarSign, RefreshCw } from "lucide-react";
import axios from "axios";
import { config } from "../../config/api.config";

const API_BASE_URL = config.API_BASE_URL;

export default function WhatIfPanel({ selectedContract }) {
  const [liabilityCap, setLiabilityCap] = useState(10);
  const [penaltyReduction, setPenaltyReduction] = useState(20);
  const [complianceLevel, setComplianceLevel] = useState(75);
  const [baseRisk, setBaseRisk] = useState(80);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadBaseRisk();
  }, [selectedContract]);

  const getAuthHeaders = () => {
    const token = localStorage.getItem("token");
    return {
      headers: { Authorization: `Bearer ${token}` }
    };
  };

  const loadBaseRisk = async () => {
    if (!selectedContract || selectedContract === "all") {
      setBaseRisk(80); // Portfolio average
      return;
    }

    try {
      setLoading(true);
      const response = await axios.post(
        `${API_BASE_URL}/prime/risk/calculate/`,
        { contract_id: selectedContract },
        getAuthHeaders()
      );

      setBaseRisk(response.data.composite_risk || 80);
      setLoading(false);
    } catch (error) {
      console.error("Error loading base risk:", error);
      setBaseRisk(80);
      setLoading(false);
    }
  };

  // Calculate projected impact
  const projectedRisk = Math.max(0, baseRisk - liabilityCap * 2 - penaltyReduction * 0.5 - (100 - complianceLevel) * 0.2);
  const riskReduction = baseRisk - projectedRisk;
  const marginImprovement = riskReduction * 0.3;

  return (
    <div className="rounded-2xl bg-gradient-to-br from-white/5 to-white/10 p-6 shadow-2xl backdrop-blur-lg border border-white/10">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-xl font-bold text-white flex items-center gap-2">
          <div className="w-1 h-6 bg-gradient-to-b from-blue-500 to-indigo-600 rounded-full" />
          What-If Simulator
          <span className="text-xs text-gray-400 font-normal">
            {selectedContract === "all" ? "(Portfolio)" : "(Contract)"}
          </span>
        </h3>
        {loading ? (
          <RefreshCw className="w-4 h-4 text-blue-400 animate-spin" />
        ) : (
          <Sliders className="w-5 h-5 text-blue-400" />
        )}
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <p className="text-gray-400">Loading simulation data...</p>
        </div>
      ) : (
        <>

      {/* Controls */}
      <div className="space-y-6 mb-6">
        <div>
          <div className="flex justify-between mb-2">
            <label className="text-sm text-gray-300">Liability Cap Multiplier</label>
            <span className="text-sm font-semibold text-cyan-400">{liabilityCap}x</span>
          </div>
          <input
            type="range"
            min="0"
            max="40"
            value={liabilityCap}
            onChange={(e) => setLiabilityCap(Number(e.target.value))}
            className="w-full h-2 bg-white/10 rounded-lg appearance-none cursor-pointer accent-cyan-500"
          />
        </div>

        <div>
          <div className="flex justify-between mb-2">
            <label className="text-sm text-gray-300">Penalty Reduction (%)</label>
            <span className="text-sm font-semibold text-cyan-400">{penaltyReduction}%</span>
          </div>
          <input
            type="range"
            min="0"
            max="100"
            value={penaltyReduction}
            onChange={(e) => setPenaltyReduction(Number(e.target.value))}
            className="w-full h-2 bg-white/10 rounded-lg appearance-none cursor-pointer accent-cyan-500"
          />
        </div>

        <div>
          <div className="flex justify-between mb-2">
            <label className="text-sm text-gray-300">Compliance Level (%)</label>
            <span className="text-sm font-semibold text-cyan-400">{complianceLevel}%</span>
          </div>
          <input
            type="range"
            min="0"
            max="100"
            value={complianceLevel}
            onChange={(e) => setComplianceLevel(Number(e.target.value))}
            className="w-full h-2 bg-white/10 rounded-lg appearance-none cursor-pointer accent-cyan-500"
          />
        </div>
      </div>

      {/* Results */}
      <div className="grid grid-cols-2 gap-4">
        <div
          className="bg-gradient-to-br from-green-500/20 to-green-600/10 border border-green-500/30 rounded-lg p-4"
        >
          <div className="flex items-center gap-2 mb-2">
            <TrendingDown className="w-4 h-4 text-green-400" />
            <p className="text-xs text-gray-300">Risk Reduction</p>
          </div>
          <p className="text-2xl font-bold text-green-400">-{riskReduction.toFixed(1)}%</p>
        </div>

        <div
          className="bg-gradient-to-br from-blue-500/20 to-blue-600/10 border border-blue-500/30 rounded-lg p-4"
        >
          <div className="flex items-center gap-2 mb-2">
            <DollarSign className="w-4 h-4 text-blue-400" />
            <p className="text-xs text-gray-300">Margin Impact</p>
          </div>
          <p className="text-2xl font-bold text-blue-400">+{marginImprovement.toFixed(1)}%</p>
        </div>
      </div>

          <div className="mt-4 bg-cyan-500/10 border border-cyan-500/20 rounded-lg p-3">
            <p className="text-xs text-cyan-400 flex justify-between items-center">
              <span>Base Risk: <span className="font-bold text-lg">{baseRisk.toFixed(1)}</span></span>
              <span>→</span>
              <span>Projected: <span className="font-bold text-lg">{projectedRisk.toFixed(1)}</span></span>
            </p>
          </div>
        </>
      )}
    </div>
  );
}
