import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Zap, FileText, Clock, TrendingUp, AlertTriangle, CheckCircle, Sparkles, Brain, Rocket, Activity } from "lucide-react";
import api from "../utils/api";
import useThemeStore from "../store/themeStore";

const AgenticAI = () => {
  const { theme } = useThemeStore();
  const navigate = useNavigate();
  const [contracts, setContracts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isVisible, setIsVisible] = useState(false);
  const [stats, setStats] = useState({
    total: 0,
    analyzed: 0,
    pending: 0,
    highRisk: 0,
  });

  useEffect(() => {
    setIsVisible(true);
  }, []);

  useEffect(() => {
    loadContracts();
  }, []);

  const loadContracts = async () => {
    try {
      const res = await api.get("/contracts/list");
      const contractsList = res.data.contracts || [];
      setContracts(contractsList);

      // Calculate stats
      setStats({
        total: contractsList.length,
        analyzed: 0, // We'll update this when we track analysis
        pending: contractsList.length,
        highRisk: 0,
      });
    } catch (error) {
      console.error("Error loading contracts:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleContractClick = (contractId) => {
    // Navigate to contract details with AI panel
    navigate(`/agentic-ai/${contractId}`);
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="relative">
            <div className="animate-spin rounded-full h-16 w-16 border-4 border-blue-500 border-t-transparent mx-auto"></div>
            <div className="absolute inset-0 animate-ping rounded-full h-16 w-16 border border-purple-500 opacity-30 mx-auto"></div>
          </div>
          <p className="text-slate-400 mt-4 animate-pulse">Loading AI-Powered Analysis...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen p-6 space-y-8">
      {/* Animated Background Gradient */}
      <div className="fixed inset-0 -z-10 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-96 h-96 bg-blue-500 rounded-full mix-blend-multiply filter blur-2xl opacity-10"></div>
        <div className="absolute -bottom-40 -left-40 w-96 h-96 bg-purple-500 rounded-full mix-blend-multiply filter blur-2xl opacity-10"></div>
      </div>

      {/* Header */}
      <div className={`mb-8 transition-all duration-700 ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 -translate-y-4'}`}>
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-4 mb-3">
              <div className="relative group">
                <div className="absolute inset-0 bg-gradient-to-br from-blue-600 to-purple-600 rounded-2xl blur-lg opacity-30 group-hover:opacity-50 transition-opacity duration-300"></div>
                <div className="relative flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-600 to-purple-600 shadow-lg shadow-blue-500/50">
                  <Zap className="w-8 h-8 text-white" />
                </div>
              </div>
              <div>
                <h1 className="text-4xl font-bold text-white mb-1 bg-gradient-to-r from-white via-blue-100 to-purple-100 bg-clip-text text-transparent">
                  Agentic AI Analysis
                </h1>
                <p className="text-slate-400 text-lg flex items-center gap-2">
                  <Brain className="w-5 h-5 text-purple-400" />
                  Intelligent multi-step contract analysis powered by LangGraph
                </p>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="px-4 py-2 bg-gradient-to-r from-blue-500/10 to-purple-500/10 border border-blue-500/30 rounded-full flex items-center gap-2">
              <Activity className="w-4 h-4 text-blue-400 animate-pulse" />
              <span className="text-sm text-blue-300 font-semibold">AI Powered</span>
            </div>
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      <div className={`grid grid-cols-1 md:grid-cols-4 gap-6 mb-8 transition-all duration-700 ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`} style={{ transitionDelay: '100ms' }}>
        {/* Total Contracts */}
        <div className="group relative bg-slate-900 border border-slate-800 rounded-xl p-6 hover:border-blue-500/50 transition-all duration-300 hover:shadow-xl hover:shadow-blue-500/20 hover:scale-105 overflow-hidden animate-slideIn">
          <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
          <div className="relative z-10">
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 bg-blue-500/10 rounded-lg group-hover:scale-110 transition-transform duration-300">
                <FileText className="w-6 h-6 text-blue-400 group-hover:rotate-12 transition-transform duration-300" />
              </div>
              <Sparkles className="w-4 h-4 text-blue-400 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
            </div>
            <p className="text-sm text-slate-400 mb-2">Total Contracts</p>
            <p className="text-3xl font-bold text-white group-hover:text-blue-300 transition-colors duration-300">{stats.total}</p>
            <div className="mt-3 h-1 bg-slate-700 rounded-full overflow-hidden">
              <div className="h-full bg-gradient-to-r from-blue-500 to-blue-400 transition-all duration-1000 ease-out" style={{ width: '100%' }}></div>
            </div>
          </div>
        </div>

        {/* Analyzed */}
        <div className="group relative bg-slate-900 border border-slate-800 rounded-xl p-6 hover:border-green-500/50 transition-all duration-300 hover:shadow-xl hover:shadow-green-500/20 hover:scale-105 overflow-hidden animate-slideIn" style={{ animationDelay: '100ms' }}>
          <div className="absolute inset-0 bg-gradient-to-br from-green-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
          <div className="relative z-10">
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 bg-green-500/10 rounded-lg group-hover:scale-110 transition-transform duration-300">
                <CheckCircle className="w-6 h-6 text-green-400 group-hover:rotate-12 transition-transform duration-300" />
              </div>
              <Sparkles className="w-4 h-4 text-green-400 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
            </div>
            <p className="text-sm text-slate-400 mb-2">Analyzed</p>
            <p className="text-3xl font-bold text-white group-hover:text-green-300 transition-colors duration-300">{stats.analyzed}</p>
            <div className="mt-3 h-1 bg-slate-700 rounded-full overflow-hidden">
              <div className="h-full bg-gradient-to-r from-green-500 to-emerald-400 transition-all duration-1000 ease-out" style={{ width: `${stats.total > 0 ? (stats.analyzed / stats.total) * 100 : 0}%` }}></div>
            </div>
          </div>
        </div>

        {/* Pending Analysis */}
        <div className="group relative bg-slate-900 border border-slate-800 rounded-xl p-6 hover:border-yellow-500/50 transition-all duration-300 hover:shadow-xl hover:shadow-yellow-500/20 hover:scale-105 overflow-hidden animate-slideIn" style={{ animationDelay: '200ms' }}>
          <div className="absolute inset-0 bg-gradient-to-br from-yellow-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
          <div className="relative z-10">
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 bg-yellow-500/10 rounded-lg group-hover:scale-110 transition-transform duration-300">
                <Clock className="w-6 h-6 text-yellow-400 group-hover:rotate-12 transition-transform duration-300" />
              </div>
              <Sparkles className="w-4 h-4 text-yellow-400 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
            </div>
            <p className="text-sm text-slate-400 mb-2">Pending Analysis</p>
            <p className="text-3xl font-bold text-white group-hover:text-yellow-300 transition-colors duration-300">{stats.pending}</p>
            <div className="mt-3 h-1 bg-slate-700 rounded-full overflow-hidden">
              <div className="h-full bg-gradient-to-r from-yellow-500 to-orange-400 transition-all duration-1000 ease-out" style={{ width: `${stats.total > 0 ? (stats.pending / stats.total) * 100 : 0}%` }}></div>
            </div>
          </div>
        </div>

        {/* High Risk */}
        <div className="group relative bg-slate-900 border border-slate-800 rounded-xl p-6 hover:border-red-500/50 transition-all duration-300 hover:shadow-xl hover:shadow-red-500/20 hover:scale-105 overflow-hidden animate-slideIn" style={{ animationDelay: '300ms' }}>
          <div className="absolute inset-0 bg-gradient-to-br from-red-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
          <div className="relative z-10">
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 bg-red-500/10 rounded-lg group-hover:scale-110 transition-transform duration-300">
                <AlertTriangle className="w-6 h-6 text-red-400 group-hover:rotate-12 transition-transform duration-300" />
              </div>
              <Sparkles className="w-4 h-4 text-red-400 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
            </div>
            <p className="text-sm text-slate-400 mb-2">High Risk</p>
            <p className="text-3xl font-bold text-white group-hover:text-red-300 transition-colors duration-300">{stats.highRisk}</p>
            <div className="mt-3 h-1 bg-slate-700 rounded-full overflow-hidden">
              <div className="h-full bg-gradient-to-r from-red-500 to-rose-400 transition-all duration-1000 ease-out" style={{ width: `${stats.total > 0 ? (stats.highRisk / stats.total) * 100 : 0}%` }}></div>
            </div>
          </div>
        </div>
      </div>

      {/* Contracts List */}
      <div className={`bg-slate-900 border border-slate-800 rounded-xl overflow-hidden hover:border-slate-700 transition-all duration-500 hover:shadow-xl hover:shadow-purple-500/10 ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`} style={{ transitionDelay: '400ms' }}>
        <div className="bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 px-6 py-5 border-b border-slate-700">
          <div className="flex items-center justify-between">
            <h2 className="text-2xl font-bold text-white flex items-center gap-3">
              <Rocket className="w-6 h-6 text-purple-400" />
              Select Contract for AI Analysis
            </h2>
            <div className="px-3 py-1 bg-purple-500/10 border border-purple-500/30 rounded-full">
              <span className="text-sm text-purple-300 font-semibold">{contracts.length} Available</span>
            </div>
          </div>
        </div>

        <div className="divide-y divide-slate-800">
          {contracts.length === 0 ? (
            <div className="text-center py-16 animate-fadeIn">
              <div className="relative inline-block mb-6">
                <FileText size={64} className="text-slate-700 animate-pulse" />
                <div className="absolute inset-0 animate-ping">
                  <FileText size={64} className="text-blue-500 opacity-20" />
                </div>
              </div>
              <p className="text-slate-400 text-lg mb-2">No contracts found</p>
              <p className="text-slate-500 text-sm">Upload some contracts to get started with AI analysis</p>
            </div>
          ) : (
            contracts.map((contract, index) => (
              <div
                key={contract.id}
                onClick={() => handleContractClick(contract.id)}
                className="group px-6 py-5 hover:bg-slate-800/50 cursor-pointer transition-all duration-300 hover:scale-[1.01] border-l-4 border-transparent hover:border-blue-500 animate-slideIn"
                style={{ animationDelay: `${index * 50}ms` }}
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-3">
                      <div className="p-2 bg-blue-500/10 rounded-lg group-hover:bg-blue-500/20 transition-colors duration-300 group-hover:scale-110 transform">
                        <FileText className="w-5 h-5 text-blue-400 group-hover:rotate-12 transition-transform duration-300" />
                      </div>
                      <h3 className="text-lg font-semibold text-white group-hover:text-blue-300 transition-colors duration-300">
                        {contract.original_filename}
                      </h3>
                    </div>
                    <div className="flex items-center gap-6 text-sm ml-11">
                      <div className="flex items-center gap-2">
                        <div className="w-1.5 h-1.5 bg-blue-400 rounded-full"></div>
                        <span className="text-slate-400">
                          <strong className="text-slate-300">Type:</strong> {contract.contract_type || "Not classified"}
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="w-1.5 h-1.5 bg-purple-400 rounded-full"></div>
                        <span className="text-slate-400">
                          <strong className="text-slate-300">Uploaded:</strong> {new Date(contract.uploaded_at).toLocaleDateString()}
                        </span>
                      </div>
                      {contract.contract_value && (
                        <div className="flex items-center gap-2">
                          <div className="w-1.5 h-1.5 bg-green-400 rounded-full"></div>
                          <span className="text-slate-400">
                            <strong className="text-slate-300">Value:</strong> {contract.contract_value}
                          </span>
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-4">
                    <div className={`px-4 py-2 rounded-full text-sm font-semibold transition-all duration-300 ${
                      contract.status === 'APPROVED'
                        ? 'bg-green-500/20 text-green-400 border border-green-500/30 hover:bg-green-500/30'
                        : contract.status === 'REJECTED'
                        ? 'bg-red-500/20 text-red-400 border border-red-500/30 hover:bg-red-500/30'
                        : 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30 hover:bg-yellow-500/30'
                    }`}>
                      {contract.status}
                    </div>

                    <button
                      className="group/btn relative flex items-center gap-2 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white px-5 py-2.5 rounded-lg transition-all duration-300 shadow-lg shadow-blue-500/30 hover:shadow-xl hover:shadow-blue-500/50 hover:scale-105 overflow-hidden"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleContractClick(contract.id);
                      }}
                    >
                      <div className="absolute inset-0 bg-gradient-to-r from-purple-600 to-blue-600 opacity-0 group-hover/btn:opacity-100 transition-opacity duration-300"></div>
                      <Zap className="w-4 h-4 relative z-10 group-hover/btn:rotate-12 transition-transform duration-300" />
                      <span className="relative z-10 font-semibold">Analyze</span>
                      <Sparkles className="w-3 h-3 relative z-10 opacity-0 group-hover/btn:opacity-100 transition-opacity duration-300" />
                    </button>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default AgenticAI;
