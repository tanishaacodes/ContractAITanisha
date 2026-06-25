import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import axios from "axios";
import { DollarSign, AlertTriangle, Calendar, Shield, TrendingUp, Filter, ChevronDown, RefreshCw } from "lucide-react";
import KPICard from "../components/KPICard";
import RiskHeatmap from "../components/RiskHeatmap";
import MonteCarloChart from "../components/MonteCarloChart";
import LiabilityRadar from "../components/LiabilityRadar";
import DriftTrend from "../components/DriftTrend";
import WhatIfPanel from "../components/WhatIfPanel";
import CounterfactualPanel from "../components/CounterfactualPanel";
import Contract3DGraph from "../components/Contract3DGraph";
import SimpleGlobeMap from "../components/SimpleGlobeMap";
import Neo4jExplorer from "../components/Neo4jExplorer";
import { config } from "../../config/api.config";
import BoardReportExporter from "../components/BoardReportExporter";
import RealTimeIndicator from "../components/RealTimeIndicator";

const API_BASE_URL = config.API_BASE_URL;

export default function ExecutiveDashboard() {
  const [loading, setLoading] = useState(true);
  const [contracts, setContracts] = useState([]);
  const [selectedContract, setSelectedContract] = useState("all");
  const [dashboardStats, setDashboardStats] = useState(null);
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState({
    dateRange: "all",
    riskLevel: "all",
    status: "all"
  });
  const [lastUpdate, setLastUpdate] = useState(null);
  const [isConnected, setIsConnected] = useState(true);

  useEffect(() => {
    loadInitialData();
  }, []);

  useEffect(() => {
    if (selectedContract) {
      loadDashboardData();
    }
  }, [selectedContract, filters]);

  const getAuthHeaders = () => {
    const token = localStorage.getItem("token");
    return {
      headers: { Authorization: `Bearer ${token}` }
    };
  };

  const loadInitialData = async () => {
    try {
      setLoading(true);

      // Load contracts list
      const contractsRes = await axios.get(
        `${API_BASE_URL}/contracts/list`,
        getAuthHeaders()
      );

      setContracts(contractsRes.data.contracts || []);

      // Load dashboard stats
      await loadDashboardData();
      setLastUpdate(new Date().toISOString());
      setIsConnected(true);

      setLoading(false);
    } catch (error) {
      console.error("Error loading initial data:", error);
      setLoading(false);
    }
  };

  const loadDashboardData = async () => {
    try {
      const params = selectedContract && selectedContract !== "all"
        ? { contract_id: selectedContract }
        : {};

      const statsRes = await axios.get(
        `${API_BASE_URL}/prime/stats/`,
        {
          ...getAuthHeaders(),
          params: params
        }
      );

      setDashboardStats(statsRes.data);
    } catch (error) {
      console.error("Error loading dashboard stats:", error);
    }
  };

  const handleContractChange = (contractId) => {
    setSelectedContract(contractId);
  };

  const handleRefresh = async () => {
    try {
      setIsConnected(true);
      await loadDashboardData();
      setLastUpdate(new Date().toISOString());
    } catch {
      setIsConnected(false);
    }
  };

  const getFilteredContracts = () => {
    if (!contracts) return [];

    return contracts.filter(contract => {
      // Filter by risk level
      if (filters.riskLevel !== "all") {
        if (filters.riskLevel === "high" && contract.liability_level !== "HIGH") return false;
        if (filters.riskLevel === "medium" && contract.liability_level !== "MEDIUM") return false;
        if (filters.riskLevel === "low" && contract.liability_level !== "LOW") return false;
      }

      // Filter by status
      if (filters.status !== "all" && contract.status !== filters.status) {
        return false;
      }

      return true;
    });
  };

  const selectedContractData = selectedContract === "all"
    ? null
    : contracts.find(c => c.id === selectedContract);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <RefreshCw className="w-12 h-12 text-cyan-400 animate-spin mx-auto mb-4" />
          <p className="text-gray-400">Loading UniContractAI...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="text-white">
      {/* Header with Controls */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-cyan-400 via-blue-500 to-purple-600 bg-clip-text text-transparent mb-2">
              UniContractAI
            </h1>
            <p className="text-gray-400">Executive Control Tower — Real-Time Contract Intelligence</p>
          </div>

          <div className="flex items-center gap-3">
            <RealTimeIndicator
              isConnected={isConnected}
              lastUpdate={lastUpdate}
              onRefresh={handleRefresh}
            />
            <button
              onClick={handleRefresh}
              className="flex items-center gap-2 px-4 py-2 bg-cyan-500/10 hover:bg-cyan-500/20 border border-cyan-500/30 rounded-lg transition-colors"
            >
              <RefreshCw className="w-4 h-4 text-cyan-400" />
              <span className="text-sm text-cyan-400">Refresh</span>
            </button>

            <button
              onClick={() => setShowFilters(!showFilters)}
              className="flex items-center gap-2 px-4 py-2 bg-purple-500/10 hover:bg-purple-500/20 border border-purple-500/30 rounded-lg transition-colors"
            >
              <Filter className="w-4 h-4 text-purple-400" />
              <span className="text-sm text-purple-400">Filters</span>
              <ChevronDown className={`w-4 h-4 text-purple-400 transition-transform ${showFilters ? "rotate-180" : ""}`} />
            </button>
          </div>
        </div>

        {/* Contract Selector & Filters */}
        <div className="bg-white/5 rounded-xl p-4 border border-white/10">
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
            {/* Contract Selector */}
            <div>
              <label className="block text-sm text-gray-400 mb-2">Select Contract</label>
              <select
                value={selectedContract}
                onChange={(e) => handleContractChange(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-cyan-500"
              >
                <option value="all">All Contracts (Portfolio View)</option>
                {getFilteredContracts().map((contract) => (
                  <option key={contract.id} value={contract.id}>
                    {contract.original_filename} - {contract.contract_value || "N/A"}
                  </option>
                ))}
              </select>
            </div>

            {/* Risk Level Filter */}
            {showFilters && (
              <>
                <div>
                  <label className="block text-sm text-gray-400 mb-2">Risk Level</label>
                  <select
                    value={filters.riskLevel}
                    onChange={(e) => setFilters({...filters, riskLevel: e.target.value})}
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-purple-500"
                  >
                    <option value="all">All Risk Levels</option>
                    <option value="high">High Risk</option>
                    <option value="medium">Medium Risk</option>
                    <option value="low">Low Risk</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm text-gray-400 mb-2">Status</label>
                  <select
                    value={filters.status}
                    onChange={(e) => setFilters({...filters, status: e.target.value})}
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-purple-500"
                  >
                    <option value="all">All Statuses</option>
                    <option value="APPROVED">Approved</option>
                    <option value="DRAFT">Draft</option>
                    <option value="LEGAL_REVIEW">Legal Review</option>
                    <option value="BUSINESS_REVIEW">Business Review</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm text-gray-400 mb-2">Date Range</label>
                  <select
                    value={filters.dateRange}
                    onChange={(e) => setFilters({...filters, dateRange: e.target.value})}
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-purple-500"
                  >
                    <option value="all">All Time</option>
                    <option value="30">Last 30 Days</option>
                    <option value="60">Last 60 Days</option>
                    <option value="90">Last 90 Days</option>
                  </select>
                </div>
              </>
            )}
          </div>

          {/* Selected Contract Info */}
          {selectedContractData && (
            <div className="mt-4 pt-4 border-t border-white/10">
              <div className="grid grid-cols-5 gap-4 text-sm">
                <div>
                  <p className="text-gray-400">Contract Type</p>
                  <p className="font-semibold text-cyan-400">{selectedContractData.contract_type || "N/A"}</p>
                </div>
                <div>
                  <p className="text-gray-400">Value</p>
                  <p className="font-semibold text-green-400">{selectedContractData.contract_value || "N/A"}</p>
                </div>
                <div>
                  <p className="text-gray-400">Party</p>
                  <p className="font-semibold text-blue-400">{selectedContractData.party_name || selectedContractData.party_a || "N/A"}</p>
                </div>
                <div>
                  <p className="text-gray-400">Liability</p>
                  <p className={`font-semibold ${
                    selectedContractData.liability_level === "HIGH" ? "text-red-400" :
                    selectedContractData.liability_level === "MEDIUM" ? "text-yellow-400" : "text-green-400"
                  }`}>
                    {selectedContractData.liability_level || "N/A"}
                  </p>
                </div>
                <div>
                  <p className="text-gray-400">Status</p>
                  <p className="font-semibold text-purple-400">{selectedContractData.status || "N/A"}</p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* KPI Section */}
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4 mb-6">
        <KPICard
          title="Portfolio Value"
          value={dashboardStats?.portfolio_value || "$0"}
          icon={DollarSign}
        />
        <KPICard
          title="Risk Adjusted Margin"
          value={dashboardStats?.risk_adjusted_margin || "0%"}
          icon={TrendingUp}
        />
        <KPICard
          title="Contracts Expiring < 60d"
          value={dashboardStats?.expiring_contracts || 0}
          icon={Calendar}
        />
        <KPICard
          title="Unlimited Liability"
          value={dashboardStats?.unlimited_liability_count || 0}
          danger
          icon={AlertTriangle}
        />
        <KPICard
          title="Auto Renewals Flagged"
          value={dashboardStats?.auto_renewals_flagged || 0}
          icon={Shield}
        />
      </div>

      {/* Risk Analysis Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <RiskHeatmap selectedContract={selectedContract} />
        <LiabilityRadar selectedContract={selectedContract} />
      </div>

      {/* Monte Carlo & Drift Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <MonteCarloChart selectedContract={selectedContract} />
        <DriftTrend selectedContract={selectedContract} />
      </div>

      {/* AI Simulation Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <WhatIfPanel selectedContract={selectedContract} />
        <CounterfactualPanel selectedContract={selectedContract} contractData={selectedContractData} />
      </div>

      {/* Advanced Visualization Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <Contract3DGraph selectedContract={selectedContract} contracts={getFilteredContracts()} />
        <SimpleGlobeMap selectedContract={selectedContract} contracts={getFilteredContracts()} />
      </div>

      {/* Neo4j Knowledge Graph */}
      <div className="mb-6">
        <Neo4jExplorer selectedContract={selectedContract} contractData={contracts} />
      </div>

      {/* Board Report Export */}
      <div className="mb-6">
        <BoardReportExporter
          selectedContract={selectedContract}
          dashboardData={{
            portfolioValue: dashboardStats?.portfolio_value,
            totalContracts: dashboardStats?.total_contracts,
            highRiskContracts: dashboardStats?.high_risk_contracts,
            riskAdjustedMargin: dashboardStats?.risk_adjusted_margin
              ? dashboardStats.risk_adjusted_margin + '%'
              : undefined,
          }}
        />
      </div>

      {/* Footer */}
      <div className="text-center text-gray-500 text-sm mt-8 pb-4">
        <p>UniContractAI © 2026 — Powered by AI, Neo4j, and Monte Carlo Simulation</p>
        <p className="mt-2">Bloomberg Terminal for Contracts | Palantir for Legal Risk</p>
        <p className="mt-1 text-xs">
          Viewing: {selectedContract === "all" ? "Portfolio Overview" : selectedContractData?.original_filename} |
          {getFilteredContracts().length} contracts loaded
        </p>
      </div>
    </div>
  );
}
