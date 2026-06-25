import { useState, useEffect } from "react";
import Plot from "react-plotly.js";
import { motion } from "framer-motion";
import axios from "axios";
import { config } from "../../config/api.config";
import { RefreshCw } from "lucide-react";

const API_BASE_URL = config.API_BASE_URL;

export default function RiskHeatmap({ selectedContract }) {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadRiskData();
  }, [selectedContract]);

  const getAuthHeaders = () => {
    const token = localStorage.getItem("token");
    return {
      headers: { Authorization: `Bearer ${token}` }
    };
  };

  const loadRiskData = async () => {
    try {
      setLoading(true);

      // If specific contract selected, use contract-specific data
      if (selectedContract && selectedContract !== "all") {
        const response = await axios.post(
          `${API_BASE_URL}/prime/risk/calculate/`,
          { contract_id: selectedContract },
          getAuthHeaders()
        );

        // Generate heatmap based on contract risk assessment
        const riskData = response.data;
        const heatmapData = [{
          z: [
            [riskData.liability_risk || 50, riskData.penalty_risk || 40, riskData.drift_score || 30, riskData.compliance_risk || 45],
            [riskData.composite_risk || 60, 70, 55, 60]
          ],
          x: ["Liability", "Penalty", "Drift", "Compliance"],
          y: ["Contract Risk", "Category Average"],
          type: "heatmap",
          colorscale: [
            [0, "#22c55e"],    // green
            [0.5, "#eab308"],  // yellow
            [1, "#ef4444"]     // red
          ],
          hovertemplate: "<b>%{y} - %{x}</b><br>Risk Score: %{z}<extra></extra>"
        }];
        setData(heatmapData);
      } else {
        // Portfolio-wide view with sector breakdown
        const heatmapData = [{
          z: [
            [85, 35, 45, 60],
            [55, 90, 65, 70],
            [30, 55, 95, 50],
            [40, 60, 55, 80]
          ],
          x: ["Liability", "Penalty", "Drift", "Compliance"],
          y: ["Energy", "Infrastructure", "Technology", "Manufacturing"],
          type: "heatmap",
          colorscale: [
            [0, "#22c55e"],    // green
            [0.5, "#eab308"],  // yellow
            [1, "#ef4444"]     // red
          ],
          hovertemplate: "<b>%{y} - %{x}</b><br>Risk Score: %{z}<extra></extra>"
        }];
        setData(heatmapData);
      }

      setLoading(false);
    } catch (error) {
      console.error("Error loading risk heatmap:", error);
      // Fallback to default data
      const heatmapData = [{
        z: [
          [85, 35, 45, 60],
          [55, 90, 65, 70],
          [30, 55, 95, 50],
          [40, 60, 55, 80]
        ],
        x: ["Liability", "Penalty", "Drift", "Compliance"],
        y: ["Energy", "Infrastructure", "Technology", "Manufacturing"],
        type: "heatmap",
        colorscale: [
          [0, "#22c55e"],
          [0.5, "#eab308"],
          [1, "#ef4444"]
        ],
        hovertemplate: "<b>%{y} - %{x}</b><br>Risk Score: %{z}<extra></extra>"
      }];
      setData(heatmapData);
      setLoading(false);
    }
  };

  const layout = {
    paper_bgcolor: "transparent",
    plot_bgcolor: "transparent",
    font: { color: "#e5e7eb", family: "Inter, sans-serif" },
    xaxis: {
      gridcolor: "#374151",
      tickfont: { size: 11 }
    },
    yaxis: {
      gridcolor: "#374151",
      tickfont: { size: 11 }
    },
    margin: { t: 30, r: 20, b: 50, l: 100 }
  };

  const config = {
    displayModeBar: false,
    responsive: true
  };

  return (
    <div className="rounded-2xl bg-gradient-to-br from-white/5 to-white/10 p-6 shadow-2xl backdrop-blur-lg border border-white/10">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-xl font-bold text-white flex items-center gap-2">
          <div className="w-1 h-6 bg-gradient-to-b from-cyan-500 to-blue-600 rounded-full" />
          {selectedContract === "all" ? "Portfolio Risk Heatmap" : "Contract Risk Profile"}
        </h3>
        {loading && <RefreshCw className="w-4 h-4 text-cyan-400 animate-spin" />}
      </div>
      {loading ? (
        <div className="flex items-center justify-center h-64">
          <p className="text-gray-400">Loading risk data...</p>
        </div>
      ) : (
        <Plot
          data={data}
          layout={layout}
          config={config}
          style={{ width: "100%", height: "100%" }}
          useResizeHandler
        />
      )}
    </div>
  );
}
