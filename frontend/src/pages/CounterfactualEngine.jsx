import { useState, useEffect } from 'react';
import {
  Beaker,
  RefreshCw,
  Clock,
  BarChart3,
  AlertTriangle,
  CheckCircle,
  Scale,
  Sparkles,
  TrendingUp,
  TrendingDown,
  Zap,
  Activity
} from 'lucide-react';
import { counterfactualAPI, getRiskColor, formatRiskDelta } from '../services/advancedAI';
import useThemeStore from '../store/themeStore';

export default function CounterfactualEngine() {
  const { theme } = useThemeStore();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    contract_id: '',
    contract_text: '',
    original_clause: '',
    modified_clause: '',
  });
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [history, setHistory] = useState([]);
  const [activeTab, setActiveTab] = useState('simulate');
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    setIsVisible(true);
  }, []);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSimulate = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const simulationResult = await counterfactualAPI.simulate(formData);
      setResult(simulationResult);
      loadHistory();
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to run simulation');
    } finally {
      setLoading(false);
    }
  };

  const loadHistory = async () => {
    try {
      const historyData = await counterfactualAPI.getHistory(null, 10);
      setHistory(historyData.scenarios || []);
    } catch (err) {
      console.error('Error loading history:', err);
    }
  };

  useEffect(() => {
    loadHistory();
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-purple-950/20 to-slate-950 py-8 px-4 sm:px-6 lg:px-8 relative overflow-hidden">
      {/* Animated Background Elements */}
      <div className="fixed inset-0 -z-10 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 -left-48 w-96 h-96 bg-purple-500 rounded-full mix-blend-multiply filter blur-3xl opacity-10 animate-blob"></div>
        <div className="absolute top-1/3 -right-48 w-96 h-96 bg-pink-500 rounded-full mix-blend-multiply filter blur-3xl opacity-10 animate-blob animation-delay-2000"></div>
        <div className="absolute -bottom-32 left-1/3 w-96 h-96 bg-blue-500 rounded-full mix-blend-multiply filter blur-3xl opacity-10 animate-blob animation-delay-4000"></div>

        {/* Grid Pattern */}
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#8882_1px,transparent_1px),linear-gradient(to_bottom,#8882_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_80%_50%_at_50%_0%,#000_70%,transparent_110%)]"></div>
      </div>

      <div className="max-w-7xl mx-auto relative">
        {/* Header */}
        <div className={`mb-8 transition-all duration-1000 ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 -translate-y-10'}`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="relative group">
                {/* Glow Effect */}
                <div className="absolute inset-0 bg-gradient-to-br from-purple-600 to-pink-600 rounded-2xl blur-xl opacity-50 group-hover:opacity-75 transition-opacity duration-500 animate-pulse"></div>

                {/* Icon Container */}
                <div className="relative flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-purple-600 via-purple-500 to-pink-600 shadow-2xl shadow-purple-500/50 transform group-hover:scale-110 group-hover:rotate-3 transition-all duration-500">
                  <Beaker className="w-8 h-8 text-white animate-pulse" />
                  <Sparkles className="absolute -top-1 -right-1 w-4 h-4 text-yellow-300 animate-ping" />
                </div>
              </div>

              <div>
                <h1 className="text-4xl font-bold bg-gradient-to-r from-white via-purple-200 to-pink-200 bg-clip-text text-transparent mb-2 animate-gradient">
                  Counterfactual Engine
                </h1>
                <p className="text-slate-400 flex items-center gap-2">
                  <Activity className="w-4 h-4 text-purple-400 animate-pulse" />
                  Simulate "what-if" scenarios with AI-powered predictions
                  <Zap className="w-4 h-4 text-yellow-400 animate-bounce" />
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className={`mb-6 border-b border-slate-800 transition-all duration-1000 ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'}`} style={{ transitionDelay: '100ms' }}>
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => setActiveTab('simulate')}
              className={`group relative whitespace-nowrap py-4 px-1 font-medium text-sm transition-all duration-300 ${
                activeTab === 'simulate'
                  ? 'text-purple-400'
                  : 'text-slate-500 hover:text-slate-300'
              }`}
            >
              <div className="flex items-center gap-2">
                <Beaker className={`h-5 w-5 transition-transform duration-300 ${activeTab === 'simulate' ? 'rotate-12' : 'group-hover:rotate-12'}`} />
                New Simulation
              </div>
              {activeTab === 'simulate' && (
                <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-purple-600 via-pink-500 to-purple-600 animate-gradient"></div>
              )}
            </button>

            <button
              onClick={() => {
                setActiveTab('history');
                loadHistory();
              }}
              className={`group relative whitespace-nowrap py-4 px-1 font-medium text-sm transition-all duration-300 ${
                activeTab === 'history'
                  ? 'text-purple-400'
                  : 'text-slate-500 hover:text-slate-300'
              }`}
            >
              <div className="flex items-center gap-2">
                <Clock className={`h-5 w-5 transition-transform duration-300 ${activeTab === 'history' ? 'rotate-12' : 'group-hover:rotate-12'}`} />
                Simulation History
              </div>
              {activeTab === 'history' && (
                <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-purple-600 via-pink-500 to-purple-600 animate-gradient"></div>
              )}
            </button>
          </nav>
        </div>

        {/* Simulate Tab */}
        {activeTab === 'simulate' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Input Form */}
            <div className={`transition-all duration-1000 ${isVisible ? 'opacity-100 translate-x-0' : 'opacity-0 -translate-x-10'}`} style={{ transitionDelay: '200ms' }}>
              <div className="group relative">
                {/* Card Glow */}
                <div className="absolute inset-0 bg-gradient-to-br from-purple-600/20 to-pink-600/20 rounded-2xl blur-xl opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>

                <div className="relative bg-slate-900/90 backdrop-blur-xl rounded-2xl shadow-2xl border border-slate-800 p-6 hover:border-purple-500/50 transition-all duration-500">
                  <div className="flex items-center gap-2 mb-6">
                    <div className="h-8 w-1 bg-gradient-to-b from-purple-500 to-pink-500 rounded-full"></div>
                    <h2 className="text-xl font-bold text-white">Simulation Parameters</h2>
                  </div>

                  <form onSubmit={handleSimulate} className="space-y-5">
                    <div className="group/input">
                      <label className="block text-sm font-medium text-slate-400 mb-2 group-hover/input:text-purple-400 transition-colors">
                        Contract ID
                      </label>
                      <input
                        type="text"
                        name="contract_id"
                        value={formData.contract_id}
                        onChange={handleInputChange}
                        className="w-full px-4 py-3 bg-slate-800/50 border border-slate-700 text-white rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all duration-300 hover:bg-slate-800 placeholder-slate-500"
                        placeholder="e.g., CONTRACT_001"
                        required
                      />
                    </div>

                    <div className="group/input">
                      <label className="block text-sm font-medium text-slate-400 mb-2 group-hover/input:text-purple-400 transition-colors">
                        Contract Context
                      </label>
                      <textarea
                        name="contract_text"
                        value={formData.contract_text}
                        onChange={handleInputChange}
                        rows={3}
                        className="w-full px-4 py-3 bg-slate-800/50 border border-slate-700 text-white rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all duration-300 hover:bg-slate-800 placeholder-slate-500 resize-none"
                        placeholder="Provide relevant contract context..."
                        required
                      />
                    </div>

                    <div className="group/input">
                      <label className="block text-sm font-medium text-slate-400 mb-2 group-hover/input:text-purple-400 transition-colors">
                        Original Clause
                      </label>
                      <textarea
                        name="original_clause"
                        value={formData.original_clause}
                        onChange={handleInputChange}
                        rows={3}
                        className="w-full px-4 py-3 bg-slate-800/50 border border-slate-700 text-white rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all duration-300 hover:bg-slate-800 placeholder-slate-500 resize-none"
                        placeholder="Enter the current clause text..."
                        required
                      />
                    </div>

                    <div className="group/input">
                      <label className="block text-sm font-medium text-slate-400 mb-2 group-hover/input:text-purple-400 transition-colors">
                        Modified Clause (What-If)
                      </label>
                      <textarea
                        name="modified_clause"
                        value={formData.modified_clause}
                        onChange={handleInputChange}
                        rows={3}
                        className="w-full px-4 py-3 bg-slate-800/50 border border-slate-700 text-white rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all duration-300 hover:bg-slate-800 placeholder-slate-500 resize-none"
                        placeholder="Enter the alternative clause to test..."
                        required
                      />
                    </div>

                    <button
                      type="submit"
                      disabled={loading}
                      className="group/btn relative w-full overflow-hidden bg-gradient-to-r from-purple-600 via-purple-500 to-pink-600 text-white py-4 px-6 rounded-xl font-semibold hover:shadow-2xl hover:shadow-purple-500/50 transition-all duration-500 disabled:opacity-50 disabled:cursor-not-allowed transform hover:scale-105 hover:-translate-y-1"
                    >
                      {/* Button Shine Effect */}
                      <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent translate-x-[-200%] group-hover/btn:translate-x-[200%] transition-transform duration-1000"></div>

                      <div className="relative flex items-center justify-center gap-3">
                        {loading ? (
                          <>
                            <RefreshCw className="h-5 w-5 animate-spin" />
                            <span className="animate-pulse">Running Simulation...</span>
                          </>
                        ) : (
                          <>
                            <Beaker className="h-5 w-5 group-hover/btn:rotate-12 transition-transform duration-300" />
                            <span>Run Simulation</span>
                            <Sparkles className="h-5 w-5 group-hover/btn:animate-bounce" />
                          </>
                        )}
                      </div>
                    </button>
                  </form>

                  {error && (
                    <div className="mt-4 bg-red-500/10 border border-red-500/50 rounded-xl p-4 backdrop-blur-sm animate-shake">
                      <div className="flex items-start gap-3">
                        <AlertTriangle className="h-5 w-5 text-red-400 flex-shrink-0 mt-0.5 animate-pulse" />
                        <p className="text-sm text-red-400">{error}</p>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Results */}
            <div className={`transition-all duration-1000 ${isVisible ? 'opacity-100 translate-x-0' : 'opacity-0 translate-x-10'}`} style={{ transitionDelay: '300ms' }}>
              <div className="group relative">
                {/* Card Glow */}
                <div className="absolute inset-0 bg-gradient-to-br from-purple-600/20 to-pink-600/20 rounded-2xl blur-xl opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>

                <div className="relative bg-slate-900/90 backdrop-blur-xl rounded-2xl shadow-2xl border border-slate-800 p-6 hover:border-purple-500/50 transition-all duration-500">
                  <div className="flex items-center gap-2 mb-6">
                    <div className="h-8 w-1 bg-gradient-to-b from-pink-500 to-purple-500 rounded-full"></div>
                    <h2 className="text-xl font-bold text-white">Simulation Results</h2>
                  </div>

                  {!result && !loading && (
                    <div className="flex flex-col items-center justify-center py-16 text-center">
                      <div className="relative">
                        <div className="absolute inset-0 bg-purple-500/20 rounded-full blur-2xl animate-pulse"></div>
                        <Beaker className="relative h-20 w-20 text-slate-600 mb-4 animate-float" />
                      </div>
                      <p className="text-slate-500 text-lg">Run a simulation to see results here</p>
                      <p className="text-slate-600 text-sm mt-2">AI-powered predictions await...</p>
                    </div>
                  )}

                  {loading && (
                    <div className="flex flex-col items-center justify-center py-16">
                      <div className="relative">
                        <div className="absolute inset-0 bg-purple-500/30 rounded-full blur-3xl animate-pulse"></div>
                        <RefreshCw className="relative h-16 w-16 text-purple-500 animate-spin mb-6" />
                      </div>
                      <p className="text-slate-400 text-lg mb-2 animate-pulse">Analyzing outcomes...</p>
                      <div className="flex gap-1">
                        <div className="w-2 h-2 bg-purple-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                        <div className="w-2 h-2 bg-purple-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                        <div className="w-2 h-2 bg-purple-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                      </div>
                    </div>
                  )}

                  {result && (
                    <div className="space-y-4 animate-fadeIn">
                      {/* Risk Overview */}
                      <div className="relative overflow-hidden bg-gradient-to-br from-purple-500/10 via-pink-500/10 to-purple-500/10 rounded-xl p-5 border border-purple-500/30 group/card hover:border-purple-500/60 transition-all duration-500">
                        <div className="absolute top-0 right-0 w-32 h-32 bg-purple-500/10 rounded-full blur-3xl group-hover/card:bg-purple-500/20 transition-all duration-500"></div>

                        <div className="relative">
                          <div className="flex items-center justify-between mb-3">
                            <span className="text-sm font-semibold text-purple-300 flex items-center gap-2">
                              <Activity className="w-4 h-4 animate-pulse" />
                              Risk Assessment
                            </span>
                            <span
                              className="px-3 py-1 rounded-full text-xs font-bold animate-pulse"
                              style={{
                                backgroundColor: getRiskColor(result.metadata?.risk_level) + '30',
                                color: getRiskColor(result.metadata?.risk_level),
                                boxShadow: `0 0 20px ${getRiskColor(result.metadata?.risk_level)}40`
                              }}
                            >
                              {result.metadata?.risk_level || 'MEDIUM'}
                            </span>
                          </div>
                          <div className="flex items-baseline gap-3 mb-2">
                            <span className="text-4xl font-bold bg-gradient-to-r from-purple-300 to-pink-300 bg-clip-text text-transparent">
                              {(result.confidence_score * 100).toFixed(0)}%
                            </span>
                            <span className="text-sm text-purple-400">confidence</span>
                          </div>
                          {result.risk_delta !== undefined && (
                            <div className="flex items-center gap-2 text-sm text-purple-300">
                              {result.risk_delta > 0 ? (
                                <TrendingUp className="w-4 h-4 text-red-400 animate-bounce" />
                              ) : (
                                <TrendingDown className="w-4 h-4 text-green-400 animate-bounce" />
                              )}
                              {formatRiskDelta(result.risk_delta)}
                            </div>
                          )}
                        </div>
                      </div>

                      {/* Impact Analysis */}
                      <div className="space-y-3">
                        {result.simulation?.business_impact && (
                          <div className="group/impact relative overflow-hidden bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-xl p-4 hover:border-blue-500/50 transition-all duration-500 hover:shadow-lg hover:shadow-blue-500/20">
                            <div className="absolute top-0 left-0 w-1 h-full bg-gradient-to-b from-blue-500 to-blue-600 group-hover/impact:w-2 transition-all duration-300"></div>
                            <div className="flex items-center gap-3 mb-3">
                              <div className="p-2 bg-blue-500/20 rounded-lg group-hover/impact:scale-110 group-hover/impact:rotate-3 transition-transform duration-300">
                                <BarChart3 className="h-5 w-5 text-blue-400" />
                              </div>
                              <span className="font-semibold text-white">Business Impact</span>
                            </div>
                            <p className="text-sm text-slate-300 leading-relaxed whitespace-pre-wrap pl-1">
                              {result.simulation.business_impact}
                            </p>
                          </div>
                        )}

                        {result.simulation?.legal_impact && (
                          <div className="group/impact relative overflow-hidden bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-xl p-4 hover:border-amber-500/50 transition-all duration-500 hover:shadow-lg hover:shadow-amber-500/20">
                            <div className="absolute top-0 left-0 w-1 h-full bg-gradient-to-b from-amber-500 to-amber-600 group-hover/impact:w-2 transition-all duration-300"></div>
                            <div className="flex items-center gap-3 mb-3">
                              <div className="p-2 bg-amber-500/20 rounded-lg group-hover/impact:scale-110 group-hover/impact:rotate-3 transition-transform duration-300">
                                <Scale className="h-5 w-5 text-amber-400" />
                              </div>
                              <span className="font-semibold text-white">Legal Impact</span>
                            </div>
                            <p className="text-sm text-slate-300 leading-relaxed whitespace-pre-wrap pl-1">
                              {result.simulation.legal_impact}
                            </p>
                          </div>
                        )}

                        {result.simulation?.operational_impact && (
                          <div className="group/impact relative overflow-hidden bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-xl p-4 hover:border-green-500/50 transition-all duration-500 hover:shadow-lg hover:shadow-green-500/20">
                            <div className="absolute top-0 left-0 w-1 h-full bg-gradient-to-b from-green-500 to-green-600 group-hover/impact:w-2 transition-all duration-300"></div>
                            <div className="flex items-center gap-3 mb-3">
                              <div className="p-2 bg-green-500/20 rounded-lg group-hover/impact:scale-110 group-hover/impact:rotate-3 transition-transform duration-300">
                                <CheckCircle className="h-5 w-5 text-green-400" />
                              </div>
                              <span className="font-semibold text-white">Operational Impact</span>
                            </div>
                            <p className="text-sm text-slate-300 leading-relaxed whitespace-pre-wrap pl-1">
                              {result.simulation.operational_impact}
                            </p>
                          </div>
                        )}
                      </div>

                      {/* Similar Outcomes */}
                      {result.similar_outcomes && result.similar_outcomes.length > 0 && (
                        <div className="mt-6 pt-6 border-t border-slate-800">
                          <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                            <Sparkles className="w-4 h-4 text-purple-400 animate-pulse" />
                            Similar Historical Contracts ({result.metadata?.num_similar_contracts || 0})
                          </h3>
                          <div className="space-y-2">
                            {result.similar_outcomes.slice(0, 3).map((outcome, idx) => (
                              <div
                                key={idx}
                                className="group/outcome bg-slate-800/50 rounded-lg p-3 border border-slate-700 hover:border-purple-500/50 transition-all duration-300 hover:shadow-lg hover:shadow-purple-500/10 animate-fadeIn"
                                style={{ animationDelay: `${idx * 100}ms` }}
                              >
                                <div className="flex justify-between items-start">
                                  <span className="font-medium text-white group-hover/outcome:text-purple-300 transition-colors">{outcome.contract_type}</span>
                                  <span className="text-slate-400 text-sm">
                                    {(outcome.score * 100).toFixed(0)}% similar
                                  </span>
                                </div>
                                {outcome.dispute_occurred && (
                                  <span className="text-red-400 mt-2 block text-sm flex items-center gap-1 animate-pulse">
                                    <AlertTriangle className="w-3 h-3" />
                                    Had disputes
                                  </span>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* History Tab */}
        {activeTab === 'history' && (
          <div className={`transition-all duration-1000 ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'}`} style={{ transitionDelay: '200ms' }}>
            <div className="group relative">
              <div className="absolute inset-0 bg-gradient-to-br from-purple-600/20 to-pink-600/20 rounded-2xl blur-xl opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>

              <div className="relative bg-slate-900/90 backdrop-blur-xl rounded-2xl shadow-2xl border border-slate-800 p-6 hover:border-purple-500/50 transition-all duration-500">
                <div className="flex items-center gap-2 mb-6">
                  <div className="h-8 w-1 bg-gradient-to-b from-purple-500 to-pink-500 rounded-full"></div>
                  <h2 className="text-xl font-bold text-white">Simulation History</h2>
                </div>

                {history.length === 0 ? (
                  <div className="flex flex-col items-center justify-center py-16 text-center">
                    <div className="relative">
                      <div className="absolute inset-0 bg-purple-500/20 rounded-full blur-2xl animate-pulse"></div>
                      <Clock className="relative h-20 w-20 text-slate-600 mb-4 animate-float" />
                    </div>
                    <p className="text-slate-500 text-lg">No simulation history yet</p>
                    <p className="text-slate-600 text-sm mt-2">Start simulating to build your history</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {history.map((scenario, idx) => (
                      <div
                        key={scenario.id}
                        className="group/history relative overflow-hidden bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-xl p-5 hover:border-purple-500/50 transition-all duration-500 cursor-pointer hover:shadow-lg hover:shadow-purple-500/20 hover:-translate-y-1 animate-fadeIn"
                        style={{ animationDelay: `${idx * 50}ms` }}
                      >
                        <div className="absolute top-0 right-0 w-32 h-32 bg-purple-500/5 rounded-full blur-2xl group-hover/history:bg-purple-500/10 transition-all duration-500"></div>

                        <div className="relative flex items-start justify-between mb-3">
                          <div className="flex-1">
                            <div className="flex items-center gap-3 mb-2">
                              <span className="font-semibold text-white group-hover/history:text-purple-300 transition-colors">{scenario.contract_id}</span>
                              <span
                                className="px-2.5 py-1 rounded-full text-xs font-bold"
                                style={{
                                  backgroundColor: getRiskColor(scenario.risk_level) + '30',
                                  color: getRiskColor(scenario.risk_level)
                                }}
                              >
                                {scenario.risk_level}
                              </span>
                            </div>
                            <p className="text-sm text-slate-400 line-clamp-2 group-hover/history:text-slate-300 transition-colors">
                              {scenario.modified_clause}
                            </p>
                          </div>
                          <div className="text-right ml-6">
                            <div className="text-lg font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
                              {(scenario.confidence_score * 100).toFixed(0)}%
                            </div>
                            <div className="text-xs text-slate-500 mt-1">
                              {new Date(scenario.created_at).toLocaleDateString()}
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>

      <style jsx>{`
        @keyframes gradient {
          0%, 100% { background-position: 0% 50%; }
          50% { background-position: 100% 50%; }
        }

        @keyframes blob {
          0%, 100% { transform: translate(0, 0) scale(1); }
          33% { transform: translate(30px, -50px) scale(1.1); }
          66% { transform: translate(-20px, 20px) scale(0.9); }
        }

        @keyframes float {
          0%, 100% { transform: translateY(0px); }
          50% { transform: translateY(-20px); }
        }

        @keyframes shake {
          0%, 100% { transform: translateX(0); }
          25% { transform: translateX(-5px); }
          75% { transform: translateX(5px); }
        }

        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }

        .animate-gradient {
          background-size: 200% 200%;
          animation: gradient 3s ease infinite;
        }

        .animate-blob {
          animation: blob 7s infinite;
        }

        .animation-delay-2000 {
          animation-delay: 2s;
        }

        .animation-delay-4000 {
          animation-delay: 4s;
        }

        .animate-float {
          animation: float 3s ease-in-out infinite;
        }

        .animate-shake {
          animation: shake 0.5s ease-in-out;
        }

        .animate-fadeIn {
          animation: fadeIn 0.5s ease-out forwards;
        }
      `}</style>
    </div>
  );
}
