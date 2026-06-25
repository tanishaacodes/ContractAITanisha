import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { ArrowLeft, Zap, FileText, Sparkles, Brain, Activity, Clock, DollarSign, Users, Calendar } from "lucide-react";
import api from "../utils/api";
import AgentPanel from "../components/AgentPanel";
import useThemeStore from "../store/themeStore";

const AgenticAIDetails = () => {
  const { theme } = useThemeStore();
  const { contractId } = useParams();
  const navigate = useNavigate();
  const [contract, setContract] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    setIsVisible(true);
  }, []);

  useEffect(() => {
    loadContract();
  }, [contractId]);

  const loadContract = async () => {
    try {
      const res = await api.get(`/contracts/${contractId}`);
      setContract(res.data.contract);
    } catch (error) {
      console.error("Error loading contract:", error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="relative mb-6">
            <div className="animate-spin rounded-full h-20 w-20 border-4 border-blue-500 border-t-transparent mx-auto"></div>
            <div className="absolute inset-0 animate-ping rounded-full h-20 w-20 border border-purple-500 opacity-30 mx-auto"></div>
            <Brain className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-8 h-8 text-blue-400 animate-pulse" />
          </div>
          <p className="text-slate-400 text-lg animate-pulse">Loading AI Analysis...</p>
          <p className="text-slate-500 text-sm mt-2">Preparing intelligent contract insights</p>
        </div>
      </div>
    );
  }

  if (!contract) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center animate-fadeIn">
          <div className="relative inline-block mb-6">
            <FileText size={80} className="text-slate-700 animate-pulse" />
            <div className="absolute inset-0 animate-ping">
              <FileText size={80} className="text-red-500 opacity-20" />
            </div>
          </div>
          <p className="text-slate-400 text-xl mb-3">Contract not found</p>
          <p className="text-slate-500 mb-6">The contract you're looking for doesn't exist</p>
          <button
            onClick={() => navigate('/agentic-ai')}
            className="px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white rounded-lg transition-all duration-300 shadow-lg hover:shadow-xl hover:scale-105"
          >
            Back to Agentic AI
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen p-6 space-y-6">
      {/* Animated Background Gradient */}
      <div className="fixed inset-0 -z-10 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-96 h-96 bg-blue-500 rounded-full mix-blend-multiply filter blur-2xl opacity-10"></div>
        <div className="absolute -bottom-40 -left-40 w-96 h-96 bg-purple-500 rounded-full mix-blend-multiply filter blur-2xl opacity-10"></div>
      </div>

      {/* Back Button */}
      <div className={`transition-all duration-700 ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 -translate-y-4'}`}>
        <button
          onClick={() => navigate('/agentic-ai')}
          className="group flex items-center gap-2 text-slate-400 hover:text-white transition-all duration-300 hover:gap-3"
        >
          <ArrowLeft size={20} className="transition-transform group-hover:-translate-x-1" />
          <span>Back to Agentic AI</span>
        </button>
      </div>

      {/* Header */}
      <div className={`mb-6 transition-all duration-700 ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`} style={{ transitionDelay: '100ms' }}>
        <div className="flex items-center gap-4 mb-4">
          <div className="relative group">
            <div className="absolute inset-0 bg-gradient-to-br from-blue-600 to-purple-600 rounded-2xl blur-xl opacity-50 group-hover:opacity-75 transition-opacity duration-300"></div>
            <div className="relative flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-br from-blue-600 to-purple-600 shadow-lg shadow-blue-500/50">
              <Zap className="w-7 h-7 text-white animate-pulse" />
            </div>
          </div>
          <div>
            <h1 className="text-3xl font-bold text-white mb-1 bg-gradient-to-r from-white via-blue-100 to-purple-100 bg-clip-text text-transparent">
              AI Contract Analysis
            </h1>
            <p className="text-slate-400 flex items-center gap-2">
              <Activity className="w-4 h-4 text-purple-400 animate-pulse" />
              Powered by advanced LangGraph intelligence
            </p>
          </div>
        </div>

        {/* Contract Info */}
        <div className="group bg-slate-900 p-6 rounded-xl border border-slate-800 hover:border-blue-500/50 transition-all duration-300 hover:shadow-xl hover:shadow-blue-500/20 animate-slideIn">
          <div className="flex items-start gap-4">
            <div className="p-3 bg-blue-500/10 rounded-lg group-hover:bg-blue-500/20 transition-colors duration-300 group-hover:scale-110 transform">
              <FileText className="w-6 h-6 text-blue-400 group-hover:rotate-12 transition-transform duration-300" />
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-4">
                <h2 className="text-xl font-bold text-white group-hover:text-blue-300 transition-colors duration-300">
                  {contract.original_filename}
                </h2>
                <Sparkles className="w-5 h-5 text-purple-400 opacity-0 group-hover:opacity-100 transition-opacity duration-300 animate-pulse" />
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {/* Type */}
                <div className="p-3 bg-slate-800/50 rounded-lg border border-slate-700 hover:border-blue-500/50 transition-all duration-300 hover:scale-105">
                  <div className="flex items-center gap-2 mb-2">
                    <FileText className="w-4 h-4 text-blue-400" />
                    <span className="text-xs text-slate-400 font-semibold uppercase">Type</span>
                  </div>
                  <span className="text-white font-semibold">{contract.contract_type || "—"}</span>
                </div>

                {/* Value */}
                <div className="p-3 bg-slate-800/50 rounded-lg border border-slate-700 hover:border-green-500/50 transition-all duration-300 hover:scale-105">
                  <div className="flex items-center gap-2 mb-2">
                    <DollarSign className="w-4 h-4 text-green-400" />
                    <span className="text-xs text-slate-400 font-semibold uppercase">Value</span>
                  </div>
                  <span className="text-white font-semibold">{contract.contract_value || "—"}</span>
                </div>

                {/* Party */}
                <div className="p-3 bg-slate-800/50 rounded-lg border border-slate-700 hover:border-purple-500/50 transition-all duration-300 hover:scale-105">
                  <div className="flex items-center gap-2 mb-2">
                    <Users className="w-4 h-4 text-purple-400" />
                    <span className="text-xs text-slate-400 font-semibold uppercase">Parties</span>
                  </div>
                  <span className="text-white font-semibold text-sm leading-tight">
                    {contract.party_a && contract.party_b
                      ? `${contract.party_a} & ${contract.party_b}`
                      : contract.party_name || "—"}
                  </span>
                </div>

                {/* Duration */}
                <div className="p-3 bg-slate-800/50 rounded-lg border border-slate-700 hover:border-yellow-500/50 transition-all duration-300 hover:scale-105">
                  <div className="flex items-center gap-2 mb-2">
                    <Calendar className="w-4 h-4 text-yellow-400" />
                    <span className="text-xs text-slate-400 font-semibold uppercase">Duration</span>
                  </div>
                  <span className="text-white font-semibold">{contract.contract_duration || "—"}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* AI Analysis Panel */}
      <div className={`bg-slate-900 border border-slate-800 rounded-xl overflow-hidden hover:border-slate-700 transition-all duration-500 hover:shadow-xl hover:shadow-purple-500/10 ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`} style={{ transitionDelay: '200ms' }}>
        <div className="bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 px-6 py-5 border-b border-slate-700">
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center gap-3 mb-2">
                <div className="p-2 bg-purple-500/10 rounded-lg">
                  <Brain className="w-5 h-5 text-purple-400 animate-pulse" />
                </div>
                <h3 className="text-xl font-bold text-white">
                  Agentic AI Analysis
                </h3>
              </div>
              <p className="text-sm text-slate-400 flex items-center gap-2">
                <Activity className="w-3 h-3 text-blue-400 animate-pulse" />
                Intelligent multi-step contract analysis powered by LangGraph
              </p>
            </div>
            <div className="px-4 py-2 bg-gradient-to-r from-blue-500/10 to-purple-500/10 border border-blue-500/30 rounded-full flex items-center gap-2 animate-pulse">
              <div className="w-2 h-2 bg-green-400 rounded-full animate-ping"></div>
              <span className="text-sm text-blue-300 font-semibold">Active</span>
            </div>
          </div>
        </div>

        <div className="p-6 bg-gradient-to-b from-slate-900/50 to-slate-900">
          <AgentPanel contractId={contractId} />
        </div>
      </div>
    </div>
  );
};

export default AgenticAIDetails;
