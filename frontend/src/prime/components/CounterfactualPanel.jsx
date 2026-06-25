import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Brain, ArrowRight, CheckCircle, AlertTriangle, RefreshCw } from "lucide-react";
import axios from "axios";
import { config } from "../../config/api.config";

const API_BASE_URL = config.API_BASE_URL;

export default function CounterfactualPanel({ selectedContract, contractData }) {
  const [suggestions, setSuggestions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadSuggestions();
  }, [selectedContract]);

  const getAuthHeaders = () => {
    const token = localStorage.getItem("token");
    return {
      headers: { Authorization: `Bearer ${token}` }
    };
  };

  const loadSuggestions = async () => {
    try {
      setLoading(true);

      if (selectedContract && selectedContract !== "all") {
        // Get AI suggestions for specific contract
        const response = await axios.post(
          `${API_BASE_URL}/prime/counterfactual/suggestions/`,
          {
            contract_id: selectedContract,
            max_suggestions: 5
          },
          getAuthHeaders()
        );

        // Transform backend suggestions to component format
        const transformedSuggestions = (response.data.suggestions || []).map(s => ({
          title: s.description || s.modification_type || "Optimization",
          riskReduction: s.impact?.risk_reduction_percent || 0,
          marginImprovement: s.impact?.margin_improvement || 0,
          feasibility: s.feasibility || "medium",
          impact: s.impact_level || "medium"
        }));

        setSuggestions(transformedSuggestions.slice(0, 3)); // Top 3
      } else {
        // Portfolio-wide suggestions
        const defaultSuggestions = [
          {
            title: "Cap Liability at 2x Annual Fees",
            riskReduction: 28,
            marginImprovement: 4.2,
            feasibility: "high",
            impact: "high"
          },
          {
            title: "Add Force Majeure Clause",
            riskReduction: 15,
            marginImprovement: 2.1,
            feasibility: "high",
            impact: "medium"
          },
          {
            title: "Reduce Penalty from 10% to 5%",
            riskReduction: 22,
            marginImprovement: 3.8,
            feasibility: "medium",
            impact: "high"
          }
        ];
        setSuggestions(defaultSuggestions);
      }

      setLoading(false);
    } catch (error) {
      console.error("Error loading counterfactual suggestions:", error);

      // Fallback to default suggestions
      const defaultSuggestions = [
        {
          title: "Cap Liability at 2x Annual Fees",
          riskReduction: 28,
          marginImprovement: 4.2,
          feasibility: "high",
          impact: "high"
        },
        {
          title: "Add Force Majeure Clause",
          riskReduction: 15,
          marginImprovement: 2.1,
          feasibility: "high",
          impact: "medium"
        },
        {
          title: "Reduce Penalty from 10% to 5%",
          riskReduction: 22,
          marginImprovement: 3.8,
          feasibility: "medium",
          impact: "high"
        }
      ];
      setSuggestions(defaultSuggestions);
      setLoading(false);
    }
  };

  const handleGenerateMore = () => {
    loadSuggestions();
  };
  return (
    <div className="rounded-2xl bg-gradient-to-br from-white/5 to-white/10 p-6 shadow-2xl backdrop-blur-lg border border-white/10">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-xl font-bold text-white flex items-center gap-2">
          <div className="w-1 h-6 bg-gradient-to-b from-purple-500 to-pink-600 rounded-full" />
          AI Counterfactual Suggestions
          <span className="text-xs text-gray-400 font-normal">
            {selectedContract === "all" ? "(Portfolio)" : "(Contract)"}
          </span>
        </h3>
        {loading ? (
          <RefreshCw className="w-4 h-4 text-purple-400 animate-spin" />
        ) : (
          <Brain className="w-5 h-5 text-purple-400 animate-pulse" />
        )}
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <p className="text-gray-400">Generating AI suggestions...</p>
        </div>
      ) : (
        <div className="space-y-4">
        {suggestions.map((suggestion, index) => (
          <div
            key={index}
            className="bg-gradient-to-r from-purple-500/10 to-pink-500/10 border border-purple-500/30 rounded-lg p-4 cursor-pointer hover:scale-[1.02] hover:translate-x-1 transition-transform"
          >
            <div className="flex items-start justify-between mb-3">
              <h4 className="text-sm font-semibold text-white flex-1">{suggestion.title}</h4>
              <div className="flex gap-2">
                {suggestion.feasibility === "high" && (
                  <CheckCircle className="w-4 h-4 text-green-400" />
                )}
                {suggestion.impact === "high" && (
                  <AlertTriangle className="w-4 h-4 text-yellow-400" />
                )}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3 mb-3">
              <div className="bg-green-500/10 rounded p-2">
                <p className="text-xs text-gray-400">Risk Reduction</p>
                <p className="text-lg font-bold text-green-400">-{suggestion.riskReduction}%</p>
              </div>
              <div className="bg-blue-500/10 rounded p-2">
                <p className="text-xs text-gray-400">Margin Gain</p>
                <p className="text-lg font-bold text-blue-400">+{suggestion.marginImprovement}%</p>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <div className="flex gap-2">
                <span className={`text-xs px-2 py-1 rounded ${
                  suggestion.feasibility === "high"
                    ? "bg-green-500/20 text-green-400"
                    : "bg-yellow-500/20 text-yellow-400"
                }`}>
                  {suggestion.feasibility} feasibility
                </span>
                <span className={`text-xs px-2 py-1 rounded ${
                  suggestion.impact === "high"
                    ? "bg-red-500/20 text-red-400"
                    : "bg-blue-500/20 text-blue-400"
                }`}>
                  {suggestion.impact} impact
                </span>
              </div>
              <ArrowRight className="w-4 h-4 text-purple-400" />
            </div>
          </div>
        ))}
        </div>
      )}

      {!loading && (
        <motion.button
          onClick={handleGenerateMore}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          className="mt-4 w-full bg-gradient-to-r from-purple-600 to-pink-600 text-white py-3 rounded-lg font-semibold hover:from-purple-500 hover:to-pink-500 transition-all"
        >
          Regenerate Suggestions
        </motion.button>
      )}
    </div>
  );
}
