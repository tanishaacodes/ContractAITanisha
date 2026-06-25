import { useState, useEffect } from 'react';
import {
  AlertTriangle,
  Bell,
  BarChart3,
  Clock,
  CheckCircle,
  RefreshCw,
  Filter,
  Scan,
  Activity,
  Shield,
  TrendingUp,
  Radio,
  Zap,
  Eye
} from 'lucide-react';
import { driftAPI, getSeverityColor, getDriftStatusStyle } from '../services/advancedAI';
import useThemeStore from '../store/themeStore';

export default function DriftDetection() {
  const { theme } = useThemeStore();
  const [loading, setLoading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [activeTab, setActiveTab] = useState('detect');
  const [formData, setFormData] = useState({
    contract_id: '',
    contract_terms: '',
    observed_behavior: '',
    data_source: 'manual',
  });
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [driftList, setDriftList] = useState([]);
  const [dashboard, setDashboard] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [filters, setFilters] = useState({
    status: '',
    min_severity: '',
    limit: 20
  });
  const [isVisible, setIsVisible] = useState(false);
  const [focusedInput, setFocusedInput] = useState(null);
  const [analysisStep, setAnalysisStep] = useState('');

  useEffect(() => {
    setIsVisible(true);
    loadDashboard();
    loadAlerts();
  }, []);

  const loadDashboard = async () => {
    try {
      const data = await driftAPI.getDashboard();
      setDashboard(data);
    } catch (err) {
      console.error('Error loading dashboard:', err);
    }
  };

  const loadAlerts = async () => {
    try {
      const data = await driftAPI.getAlerts(5);
      setAlerts(data.alerts || []);
    } catch (err) {
      console.error('Error loading alerts:', err);
    }
  };

  const loadDriftList = async () => {
    try {
      setLoading(true);
      const data = await driftAPI.list(filters);
      setDriftList(data.drifts || []);
    } catch (err) {
      console.error('Error loading drift list:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDetectDrift = async (e) => {
    e.preventDefault();
    setLoading(true);
    setAnalyzing(true);
    setError(null);
    setResult(null);

    // Simulate analysis steps
    const steps = [
      'Parsing contract terms...',
      'Analyzing behavioral patterns...',
      'Detecting divergence vectors...',
      'Calculating risk severity...',
      'Generating remediation plan...'
    ];

    let stepIndex = 0;
    const stepInterval = setInterval(() => {
      if (stepIndex < steps.length) {
        setAnalysisStep(steps[stepIndex]);
        stepIndex++;
      }
    }, 800);

    try {
      const detectionResult = await driftAPI.detect(formData);
      clearInterval(stepInterval);
      setResult(detectionResult);
      setAnalysisStep('');
      loadDashboard();
      loadAlerts();
    } catch (err) {
      clearInterval(stepInterval);
      setError(err.response?.data?.error || 'Failed to detect drift');
      setAnalysisStep('');
    } finally {
      setLoading(false);
      setAnalyzing(false);
    }
  };

  const getSeverityLabel = (severity) => {
    if (severity >= 9) return 'Critical';
    if (severity >= 7) return 'High';
    if (severity >= 4) return 'Medium';
    return 'Low';
  };

  const getSeverityIcon = (severity) => {
    if (severity >= 9) return <AlertTriangle className="w-5 h-5" />;
    if (severity >= 7) return <TrendingUp className="w-5 h-5" />;
    return <Activity className="w-5 h-5" />;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 py-8 px-4 sm:px-6 lg:px-8 relative overflow-hidden">
      {/* Animated Background */}
      <div className="fixed inset-0 -z-10 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 -left-64 w-[600px] h-[600px] bg-red-500/5 rounded-full blur-[120px] animate-pulse"></div>
        <div className="absolute bottom-1/4 -right-64 w-[600px] h-[600px] bg-orange-500/5 rounded-full blur-[120px] animate-pulse" style={{ animationDelay: '1s' }}></div>

        {/* Neural Grid Pattern */}
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808008_1px,transparent_1px),linear-gradient(to_bottom,#80808008_1px,transparent_1px)] bg-[size:3rem_3rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_110%)]"></div>
      </div>

      <div className="max-w-7xl mx-auto relative">
        {/* Header with Sophisticated Animation */}
        <div className={`mb-10 transition-all duration-1000 ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 -translate-y-8'}`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-5">
              {/* Premium Icon Container */}
              <div className="relative group">
                <div className="absolute inset-0 bg-gradient-to-br from-red-600 to-orange-600 rounded-2xl blur-2xl opacity-40 group-hover:opacity-60 transition-opacity duration-700 animate-pulse"></div>
                <div className="relative flex items-center justify-center w-20 h-20 rounded-2xl bg-gradient-to-br from-red-600 via-red-500 to-orange-600 shadow-2xl shadow-red-500/30">
                  <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-white/10 to-transparent"></div>
                  <AlertTriangle className="w-10 h-10 text-white relative z-10" strokeWidth={2.5} />
                  {/* AI Scan Lines */}
                  <div className="absolute inset-0 rounded-2xl overflow-hidden">
                    <div className="absolute inset-0 bg-gradient-to-b from-transparent via-white/20 to-transparent h-full w-full animate-scan"></div>
                  </div>
                </div>
              </div>

              <div>
                <div className="flex items-center gap-3 mb-2">
                  <h1 className="text-4xl font-bold bg-gradient-to-r from-white via-slate-100 to-slate-300 bg-clip-text text-transparent">
                    Drift Detection
                  </h1>
                  <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-red-500/10 border border-red-500/30">
                    <Radio className="w-3 h-3 text-red-400 animate-pulse" />
                    <span className="text-xs font-semibold text-red-400 uppercase tracking-wider">Live</span>
                  </div>
                </div>
                <p className="text-slate-400 flex items-center gap-2 text-sm">
                  <Scan className="w-4 h-4 text-red-400" />
                  AI-powered behavioral divergence monitoring
                  <span className="text-slate-600">•</span>
                  <span className="text-slate-500">Real-time risk analysis</span>
                </p>
              </div>
            </div>

            {/* Alert Bell with Enterprise Badge */}
            {alerts.length > 0 && (
              <div className={`relative transition-all duration-700 ${isVisible ? 'opacity-100 scale-100' : 'opacity-0 scale-90'}`} style={{ transitionDelay: '200ms' }}>
                <button
                  onClick={() => setActiveTab('dashboard')}
                  className="group relative p-4 rounded-xl bg-slate-900/50 backdrop-blur-sm border border-slate-800 hover:border-red-500/50 transition-all duration-500 hover:shadow-lg hover:shadow-red-500/20"
                >
                  <div className="absolute inset-0 bg-gradient-to-br from-red-500/5 to-orange-500/5 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
                  <Bell className="relative w-6 h-6 text-red-400 group-hover:scale-110 transition-transform duration-300" />
                  <div className="absolute -top-1 -right-1 min-w-[24px] h-6 px-1.5 rounded-full bg-gradient-to-br from-red-600 to-red-700 border-2 border-slate-950 shadow-lg flex items-center justify-center">
                    <span className="text-xs font-bold text-white">{alerts.length}</span>
                  </div>
                  <div className="absolute -top-1 -right-1 w-6 h-6 rounded-full bg-red-500 animate-ping opacity-75"></div>
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Refined Tab Navigation */}
        <div className={`mb-8 transition-all duration-1000 ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`} style={{ transitionDelay: '300ms' }}>
          <div className="relative bg-slate-900/30 backdrop-blur-sm rounded-2xl border border-slate-800/50 p-1.5">
            <div className="flex gap-2">
              {[
                { id: 'detect', label: 'Detect Drift', icon: Scan },
                { id: 'list', label: 'Drift History', icon: Clock },
                { id: 'dashboard', label: 'Analytics', icon: BarChart3 }
              ].map((tab) => {
                const Icon = tab.icon;
                const isActive = activeTab === tab.id;
                return (
                  <button
                    key={tab.id}
                    onClick={() => {
                      setActiveTab(tab.id);
                      if (tab.id === 'list') loadDriftList();
                      if (tab.id === 'dashboard') loadDashboard();
                    }}
                    className={`relative flex-1 flex items-center justify-center gap-2 py-3.5 px-6 rounded-xl font-medium text-sm transition-all duration-500 ${
                      isActive
                        ? 'text-white'
                        : 'text-slate-500 hover:text-slate-300'
                    }`}
                  >
                    {isActive && (
                      <div className="absolute inset-0 bg-gradient-to-br from-red-600/90 to-orange-600/90 rounded-xl shadow-lg shadow-red-500/30"></div>
                    )}
                    <Icon className={`relative w-4 h-4 transition-transform duration-300 ${isActive ? 'scale-110' : ''}`} />
                    <span className="relative">{tab.label}</span>
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        {/* Detect Tab - Premium Enterprise Design */}
        {activeTab === 'detect' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Detection Form - Left Panel */}
            <div className={`transition-all duration-1000 ${isVisible ? 'opacity-100 translate-x-0' : 'opacity-0 -translate-x-10'}`} style={{ transitionDelay: '400ms' }}>
              <div className="group relative">
                <div className="absolute inset-0 bg-gradient-to-br from-red-600/10 to-orange-600/10 rounded-3xl blur-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-700"></div>

                <div className="relative bg-slate-900/60 backdrop-blur-xl rounded-2xl border border-slate-800/50 shadow-2xl overflow-hidden">
                  {/* Top Accent Bar */}
                  <div className="h-1 bg-gradient-to-r from-red-600 via-orange-500 to-red-600 animate-gradient"></div>

                  <div className="p-8">
                    <div className="flex items-center justify-between mb-6">
                      <div className="flex items-center gap-3">
                        <div className="w-1 h-8 bg-gradient-to-b from-red-500 to-orange-500 rounded-full"></div>
                        <h2 className="text-xl font-bold text-white">Detection Parameters</h2>
                      </div>
                      <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800/50">
                        <Eye className="w-3.5 h-3.5 text-slate-400" />
                        <span className="text-xs text-slate-400 font-medium">Enterprise Mode</span>
                      </div>
                    </div>

                    <form onSubmit={handleDetectDrift} className="space-y-6">
                      {/* Contract ID Input */}
                      <div className="group/input">
                        <label className={`block text-sm font-semibold text-slate-300 mb-2.5 transition-colors ${focusedInput === 'contract_id' ? 'text-red-400' : ''}`}>
                          Contract Identifier
                          <span className="text-red-400 ml-1">*</span>
                        </label>
                        <div className="relative">
                          <input
                            type="text"
                            value={formData.contract_id}
                            onChange={(e) => setFormData({ ...formData, contract_id: e.target.value })}
                            onFocus={() => setFocusedInput('contract_id')}
                            onBlur={() => setFocusedInput(null)}
                            className="w-full px-4 py-3.5 bg-slate-800/50 border border-slate-700 text-white rounded-xl focus:ring-2 focus:ring-red-500/50 focus:border-red-500/50 transition-all duration-300 hover:bg-slate-800/70 placeholder-slate-500 font-medium"
                            placeholder="e.g., CONTRACT_2024_001"
                            required
                          />
                          {focusedInput === 'contract_id' && (
                            <div className="absolute inset-0 rounded-xl bg-gradient-to-r from-red-500/20 to-orange-500/20 pointer-events-none animate-pulse"></div>
                          )}
                        </div>
                      </div>

                      {/* Contract Terms Textarea */}
                      <div className="group/input">
                        <label className={`block text-sm font-semibold text-slate-300 mb-2.5 transition-colors ${focusedInput === 'contract_terms' ? 'text-red-400' : ''}`}>
                          Contract Terms (Baseline)
                          <span className="text-red-400 ml-1">*</span>
                        </label>
                        <div className="relative">
                          <textarea
                            value={formData.contract_terms}
                            onChange={(e) => setFormData({ ...formData, contract_terms: e.target.value })}
                            onFocus={() => setFocusedInput('contract_terms')}
                            onBlur={() => setFocusedInput(null)}
                            rows={5}
                            className="w-full px-4 py-3.5 bg-slate-800/50 border border-slate-700 text-white rounded-xl focus:ring-2 focus:ring-red-500/50 focus:border-red-500/50 transition-all duration-300 hover:bg-slate-800/70 placeholder-slate-500 resize-none"
                            placeholder="Enter original contractual obligations..."
                            required
                          />
                          {focusedInput === 'contract_terms' && (
                            <div className="absolute inset-0 rounded-xl bg-gradient-to-r from-red-500/20 to-orange-500/20 pointer-events-none animate-pulse"></div>
                          )}
                        </div>
                      </div>

                      {/* Observed Behavior Textarea */}
                      <div className="group/input">
                        <label className={`block text-sm font-semibold text-slate-300 mb-2.5 transition-colors ${focusedInput === 'observed_behavior' ? 'text-red-400' : ''}`}>
                          Observed Behavior (Actual Reality)
                          <span className="text-red-400 ml-1">*</span>
                        </label>
                        <div className="relative">
                          <textarea
                            value={formData.observed_behavior}
                            onChange={(e) => setFormData({ ...formData, observed_behavior: e.target.value })}
                            onFocus={() => setFocusedInput('observed_behavior')}
                            onBlur={() => setFocusedInput(null)}
                            rows={5}
                            className="w-full px-4 py-3.5 bg-slate-800/50 border border-slate-700 text-white rounded-xl focus:ring-2 focus:ring-red-500/50 focus:border-red-500/50 transition-all duration-300 hover:bg-slate-800/70 placeholder-slate-500 resize-none"
                            placeholder="Describe actual behaviors that diverge from contract..."
                            required
                          />
                          {focusedInput === 'observed_behavior' && (
                            <div className="absolute inset-0 rounded-xl bg-gradient-to-r from-red-500/20 to-orange-500/20 pointer-events-none animate-pulse"></div>
                          )}
                        </div>
                      </div>

                      {/* Data Source Selector */}
                      <div className="group/input">
                        <label className="block text-sm font-semibold text-slate-300 mb-2.5">
                          Evidence Source
                        </label>
                        <select
                          value={formData.data_source}
                          onChange={(e) => setFormData({ ...formData, data_source: e.target.value })}
                          className="w-full px-4 py-3.5 bg-slate-800/50 border border-slate-700 text-white rounded-xl focus:ring-2 focus:ring-red-500/50 focus:border-red-500/50 transition-all duration-300 hover:bg-slate-800/70 cursor-pointer"
                        >
                          <option value="manual">Manual Entry</option>
                          <option value="crm">CRM System</option>
                          <option value="billing">Billing Records</option>
                          <option value="support">Support Tickets</option>
                          <option value="email">Email Communications</option>
                          <option value="slack">Slack Archive</option>
                        </select>
                      </div>

                      {/* Premium CTA Button */}
                      <button
                        type="submit"
                        disabled={loading}
                        className="group/btn relative w-full overflow-hidden bg-gradient-to-r from-red-600 via-red-500 to-orange-600 text-white py-4 px-6 rounded-xl font-bold text-base shadow-xl shadow-red-500/30 hover:shadow-2xl hover:shadow-red-500/40 transition-all duration-500 disabled:opacity-50 disabled:cursor-not-allowed transform hover:scale-[1.02] active:scale-[0.98]"
                      >
                        {/* Shine Effect */}
                        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent translate-x-[-200%] group-hover/btn:translate-x-[200%] transition-transform duration-1000"></div>

                        <div className="relative flex items-center justify-center gap-3">
                          {loading ? (
                            <>
                              <RefreshCw className="w-5 h-5 animate-spin" />
                              <span className="font-bold">Analyzing Divergence...</span>
                            </>
                          ) : (
                            <>
                              <Scan className="w-5 h-5 group-hover/btn:rotate-90 transition-transform duration-500" />
                              <span>Detect Contract Drift</span>
                              <Zap className="w-5 h-5 group-hover/btn:scale-110 transition-transform duration-300" />
                            </>
                          )}
                        </div>
                      </button>
                    </form>

                    {/* Error Display */}
                    {error && (
                      <div className="mt-6 bg-red-500/10 border border-red-500/30 rounded-xl p-4 backdrop-blur-sm animate-shake">
                        <div className="flex items-start gap-3">
                          <AlertTriangle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5 animate-pulse" />
                          <div>
                            <p className="text-sm font-semibold text-red-400 mb-1">Detection Failed</p>
                            <p className="text-xs text-red-300">{error}</p>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* Results Panel - Right Side */}
            <div className={`transition-all duration-1000 ${isVisible ? 'opacity-100 translate-x-0' : 'opacity-0 translate-x-10'}`} style={{ transitionDelay: '500ms' }}>
              <div className="group relative">
                <div className="absolute inset-0 bg-gradient-to-br from-red-600/10 to-orange-600/10 rounded-3xl blur-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-700"></div>

                <div className="relative bg-slate-900/60 backdrop-blur-xl rounded-2xl border border-slate-800/50 shadow-2xl overflow-hidden min-h-[600px]">
                  {/* Top Accent */}
                  <div className="h-1 bg-gradient-to-r from-orange-600 via-red-500 to-orange-600 animate-gradient"></div>

                  <div className="p-8">
                    <div className="flex items-center gap-3 mb-6">
                      <div className="w-1 h-8 bg-gradient-to-b from-orange-500 to-red-500 rounded-full"></div>
                      <h2 className="text-xl font-bold text-white">Analysis Results</h2>
                    </div>

                    {/* Empty State - Premium */}
                    {!result && !loading && (
                      <div className="flex flex-col items-center justify-center py-20 text-center">
                        <div className="relative mb-6">
                          <div className="absolute inset-0 bg-red-500/20 rounded-full blur-3xl animate-pulse"></div>
                          <div className="relative w-24 h-24 rounded-2xl bg-gradient-to-br from-slate-800 to-slate-900 border border-slate-700 flex items-center justify-center">
                            <Shield className="w-12 h-12 text-slate-600 animate-float" />
                          </div>
                        </div>
                        <p className="text-slate-400 text-lg font-medium mb-2">Awaiting Analysis</p>
                        <p className="text-slate-600 text-sm">Run detection to identify behavioral divergence</p>
                      </div>
                    )}

                    {/* Loading State - AI Analysis Animation */}
                    {loading && (
                      <div className="flex flex-col items-center justify-center py-20">
                        <div className="relative mb-8">
                          <div className="absolute inset-0 bg-red-500/30 rounded-full blur-3xl animate-pulse"></div>
                          <div className="relative w-24 h-24 rounded-2xl bg-gradient-to-br from-red-600 to-orange-600 shadow-2xl shadow-red-500/50 flex items-center justify-center">
                            <Scan className="w-12 h-12 text-white animate-spin" />
                            {/* Scan Lines */}
                            <div className="absolute inset-0 rounded-2xl overflow-hidden">
                              <div className="absolute inset-0 bg-gradient-to-b from-transparent via-white/30 to-transparent h-full w-full animate-scan"></div>
                            </div>
                          </div>
                        </div>

                        <div className="space-y-3 text-center">
                          <p className="text-white text-lg font-semibold animate-pulse">Analyzing Contract Divergence</p>
                          {analysisStep && (
                            <p className="text-red-400 text-sm font-medium flex items-center justify-center gap-2">
                              <Activity className="w-4 h-4 animate-pulse" />
                              {analysisStep}
                            </p>
                          )}

                          {/* Progress Dots */}
                          <div className="flex justify-center gap-2 pt-2">
                            <div className="w-2 h-2 bg-red-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                            <div className="w-2 h-2 bg-red-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                            <div className="w-2 h-2 bg-red-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Results Display */}
                    {result && (
                      <div className="space-y-5 animate-fadeIn">
                        {/* Severity Card - Hero */}
                        <div
                          className="relative overflow-hidden rounded-2xl p-6 border-2 shadow-2xl"
                          style={{
                            backgroundColor: getSeverityColor(result.severity) + '15',
                            borderColor: getSeverityColor(result.severity) + '50',
                            boxShadow: `0 20px 60px ${getSeverityColor(result.severity)}30`
                          }}
                        >
                          <div className="absolute top-0 right-0 w-48 h-48 rounded-full blur-3xl opacity-20" style={{ backgroundColor: getSeverityColor(result.severity) }}></div>

                          <div className="relative">
                            <div className="flex items-center justify-between mb-4">
                              <div className="flex items-center gap-3">
                                <div className="p-2.5 rounded-xl" style={{ backgroundColor: getSeverityColor(result.severity) + '20' }}>
                                  {getSeverityIcon(result.severity)}
                                </div>
                                <span className="text-sm font-bold uppercase tracking-wider" style={{ color: getSeverityColor(result.severity) }}>
                                  Drift Severity Analysis
                                </span>
                              </div>
                              <div className="px-4 py-2 rounded-full font-bold text-xs uppercase tracking-wider shadow-lg"
                                style={{
                                  backgroundColor: getSeverityColor(result.severity) + '30',
                                  color: getSeverityColor(result.severity),
                                  boxShadow: `0 0 30px ${getSeverityColor(result.severity)}40`
                                }}
                              >
                                {getSeverityLabel(result.severity)} Risk
                              </div>
                            </div>

                            <div className="flex items-baseline gap-3">
                              <span className="text-6xl font-black bg-gradient-to-br from-white to-slate-300 bg-clip-text text-transparent">
                                {result.severity}
                              </span>
                              <span className="text-3xl font-bold text-slate-400">/10</span>
                            </div>
                          </div>
                        </div>

                        {/* Drift Type Badge */}
                        <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-5 border border-slate-700/50">
                          <div className="flex items-center justify-between">
                            <div>
                              <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Classification</p>
                              <div className="inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-orange-500/20 to-red-500/20 border border-orange-500/30 rounded-lg">
                                <Activity className="w-4 h-4 text-orange-400" />
                                <span className="text-sm font-bold text-orange-300">{result.drift_type}</span>
                              </div>
                            </div>
                          </div>
                        </div>

                        {/* Analysis Sections */}
                        {result.analysis && (
                          <div className="space-y-4">
                            {result.analysis.drift_identification && (
                              <div className="group/card bg-slate-800/30 backdrop-blur-sm rounded-xl p-5 border border-slate-700/50 hover:border-red-500/30 transition-all duration-500">
                                <div className="flex items-start gap-3 mb-3">
                                  <div className="p-2 rounded-lg bg-blue-500/20">
                                    <Eye className="w-4 h-4 text-blue-400" />
                                  </div>
                                  <div>
                                    <h3 className="font-bold text-white text-sm mb-1">Drift Identification</h3>
                                    <p className="text-xs text-slate-500">AI-detected divergence patterns</p>
                                  </div>
                                </div>
                                <p className="text-sm text-slate-300 leading-relaxed whitespace-pre-wrap pl-11">
                                  {result.analysis.drift_identification}
                                </p>
                              </div>
                            )}

                            {result.analysis.legal_risk && (
                              <div className="group/card bg-red-500/5 backdrop-blur-sm rounded-xl p-5 border border-red-500/20 hover:border-red-500/40 transition-all duration-500">
                                <div className="flex items-start gap-3 mb-3">
                                  <div className="p-2 rounded-lg bg-red-500/20">
                                    <AlertTriangle className="w-4 h-4 text-red-400" />
                                  </div>
                                  <div>
                                    <h3 className="font-bold text-red-300 text-sm mb-1">Legal Risk Assessment</h3>
                                    <p className="text-xs text-red-400/70">Compliance exposure analysis</p>
                                  </div>
                                </div>
                                <p className="text-sm text-red-200/90 leading-relaxed whitespace-pre-wrap pl-11">
                                  {result.analysis.legal_risk}
                                </p>
                              </div>
                            )}

                            {result.analysis.remediation && (
                              <div className="group/card bg-green-500/5 backdrop-blur-sm rounded-xl p-5 border border-green-500/20 hover:border-green-500/40 transition-all duration-500">
                                <div className="flex items-start gap-3 mb-3">
                                  <div className="p-2 rounded-lg bg-green-500/20">
                                    <CheckCircle className="w-4 h-4 text-green-400" />
                                  </div>
                                  <div>
                                    <h3 className="font-bold text-green-300 text-sm mb-1">Remediation Plan</h3>
                                    <p className="text-xs text-green-400/70">AI-recommended actions</p>
                                  </div>
                                </div>
                                <p className="text-sm text-green-200/90 leading-relaxed whitespace-pre-wrap pl-11">
                                  {result.analysis.remediation}
                                </p>
                              </div>
                            )}
                          </div>
                        )}

                        {/* Metadata Footer */}
                        <div className="pt-5 border-t border-slate-800">
                          <div className="flex items-center justify-between text-xs">
                            <div className="flex items-center gap-2 text-slate-500">
                              <div className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse"></div>
                              <span>Analysis ID: {result.drift_id}</span>
                            </div>
                            <div className="text-slate-600">
                              <Clock className="w-3 h-3 inline mr-1" />
                              {new Date(result.detected_at).toLocaleString()}
                            </div>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Other tabs implementation continues... */}
        {activeTab === 'list' && (
          <div className="animate-fadeIn">
            {/* Drift History content - implement similar premium styling */}
          </div>
        )}

        {activeTab === 'dashboard' && dashboard && (
          <div className="animate-fadeIn">
            {/* Dashboard content - implement similar premium styling */}
          </div>
        )}
      </div>

      {/* Custom Animations */}
      <style jsx>{`
        @keyframes scan {
          0% { transform: translateY(-100%); }
          100% { transform: translateY(200%); }
        }

        @keyframes gradient {
          0%, 100% { background-position: 0% 50%; }
          50% { background-position: 100% 50%; }
        }

        @keyframes float {
          0%, 100% { transform: translateY(0px); }
          50% { transform: translateY(-15px); }
        }

        @keyframes shake {
          0%, 100% { transform: translateX(0); }
          25% { transform: translateX(-4px); }
          75% { transform: translateX(4px); }
        }

        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }

        .animate-scan {
          animation: scan 2s linear infinite;
        }

        .animate-gradient {
          background-size: 200% 200%;
          animation: gradient 3s ease infinite;
        }

        .animate-float {
          animation: float 3s ease-in-out infinite;
        }

        .animate-shake {
          animation: shake 0.4s ease-in-out;
        }

        .animate-fadeIn {
          animation: fadeIn 0.6s ease-out forwards;
        }
      `}</style>
    </div>
  );
}
