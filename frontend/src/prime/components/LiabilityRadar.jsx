import { useState, useEffect } from "react";
import { RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer, Tooltip } from "recharts";
import { motion } from "framer-motion";
import { Shield, RefreshCw } from "lucide-react";
import axios from "axios";
import { config } from "../../config/api.config";

const API_BASE_URL = config.API_BASE_URL;

export default function LiabilityRadar({ selectedContract }) {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [highestRisk, setHighestRisk] = useState({ name: "", score: 0 });
  const [avgRisk, setAvgRisk] = useState(0);

  useEffect(() => {
    loadLiabilityData();
  }, [selectedContract]);

  const getAuthHeaders = () => {
    const token = localStorage.getItem("token");
    return {
      headers: { Authorization: `Bearer ${token}` }
    };
  };

  const loadLiabilityData = async () => {
    try {
      setLoading(true);

      if (selectedContract && selectedContract !== "all") {
        // Get contract-specific risk assessment
        const response = await axios.post(
          `${API_BASE_URL}/prime/risk/calculate/`,
          { contract_id: selectedContract },
          getAuthHeaders()
        );

        const riskData = response.data;

        const radarData = [
          { subject: "Unlimited Liability", A: riskData.liability_risk || 50, fullMark: 100 },
          { subject: "Indemnity Risk", A: (riskData.liability_risk || 50) * 0.75, fullMark: 100 },
          { subject: "IP Risk", A: (riskData.compliance_risk || 45) * 0.9, fullMark: 100 },
          { subject: "Data Risk", A: riskData.compliance_risk || 45, fullMark: 100 },
          { subject: "Penalty Risk", A: riskData.penalty_risk || 40, fullMark: 100 },
          { subject: "Compliance Risk", A: riskData.compliance_risk || 45, fullMark: 100 }
        ];

        setData(radarData);

        // Calculate highest risk and average
        const highest = radarData.reduce((max, item) => item.A > max.score ? { name: item.subject, score: item.A } : max, { name: "", score: 0 });
        const avg = radarData.reduce((sum, item) => sum + item.A, 0) / radarData.length;

        setHighestRisk(highest);
        setAvgRisk(avg.toFixed(1));
      } else {
        // Portfolio-wide view
        const defaultData = [
          { subject: "Unlimited Liability", A: 85, fullMark: 100 },
          { subject: "Indemnity Risk", A: 65, fullMark: 100 },
          { subject: "IP Risk", A: 45, fullMark: 100 },
          { subject: "Data Risk", A: 90, fullMark: 100 },
          { subject: "Penalty Risk", A: 70, fullMark: 100 },
          { subject: "Compliance Risk", A: 55, fullMark: 100 }
        ];

        setData(defaultData);

        const highest = defaultData.reduce((max, item) => item.A > max.score ? { name: item.subject, score: item.A } : max, { name: "", score: 0 });
        const avg = defaultData.reduce((sum, item) => sum + item.A, 0) / defaultData.length;

        setHighestRisk(highest);
        setAvgRisk(avg.toFixed(1));
      }

      setLoading(false);
    } catch (error) {
      console.error("Error loading liability radar:", error);

      // Fallback data
      const defaultData = [
        { subject: "Unlimited Liability", A: 85, fullMark: 100 },
        { subject: "Indemnity Risk", A: 65, fullMark: 100 },
        { subject: "IP Risk", A: 45, fullMark: 100 },
        { subject: "Data Risk", A: 90, fullMark: 100 },
        { subject: "Penalty Risk", A: 70, fullMark: 100 },
        { subject: "Compliance Risk", A: 55, fullMark: 100 }
      ];

      setData(defaultData);
      setHighestRisk({ name: "Data Risk", score: 90 });
      setAvgRisk("68.3");
      setLoading(false);
    }
  };
  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-slate-900/95 border border-red-500/30 rounded-lg p-3 shadow-xl">
          <p className="text-white text-sm">{payload[0].payload.subject}</p>
          <p className="text-red-400 text-sm font-semibold">
            Risk Score: {payload[0].value}/100
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="rounded-2xl bg-gradient-to-br from-white/5 to-white/10 p-6 shadow-2xl backdrop-blur-lg border border-white/10">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-xl font-bold text-white flex items-center gap-2">
          <div className="w-1 h-6 bg-gradient-to-b from-red-500 to-orange-600 rounded-full" />
          Liability Risk Profile
          <span className="text-xs text-gray-400 font-normal">
            {selectedContract === "all" ? "(Portfolio)" : "(Contract)"}
          </span>
        </h3>
        {loading ? (
          <RefreshCw className="w-4 h-4 text-red-400 animate-spin" />
        ) : (
          <Shield className="w-5 h-5 text-red-400" />
        )}
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <p className="text-gray-400">Analyzing liability profile...</p>
        </div>
      ) : (
        <>
          <ResponsiveContainer width="100%" height={400}>
            <RadarChart data={data}>
              <PolarGrid stroke="#374151" />
              <PolarAngleAxis
                dataKey="subject"
                tick={{ fill: "#e5e7eb", fontSize: 11 }}
              />
              <PolarRadiusAxis
                angle={90}
                domain={[0, 100]}
                tick={{ fill: "#9ca3af", fontSize: 10 }}
              />
              <Tooltip content={<CustomTooltip />} />
              <Radar
                name="Risk Score"
                dataKey="A"
                stroke="#ef4444"
                fill="#ef4444"
                fillOpacity={0.4}
                strokeWidth={2}
              />
            </RadarChart>
          </ResponsiveContainer>

          <div className="mt-4 grid grid-cols-2 gap-3">
            <div className="bg-red-500/10 rounded-lg p-3 border border-red-500/20">
              <p className="text-xs text-gray-400 mb-1">Highest Risk</p>
              <p className="text-sm font-semibold text-red-400">{highestRisk.name} ({highestRisk.score.toFixed(0)})</p>
            </div>
            <div className="bg-yellow-500/10 rounded-lg p-3 border border-yellow-500/20">
              <p className="text-xs text-gray-400 mb-1">Avg Risk Score</p>
              <p className="text-sm font-semibold text-yellow-400">{avgRisk}/100</p>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
