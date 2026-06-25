import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Sparkles,
  AlertTriangle,
  CheckCircle,
  Clock,
  User,
  Shield,
  TrendingUp,
  FileText,
  Target,
  Loader2,
} from 'lucide-react';
import api from '../utils/api';
import IntentVisualizations from '../components/IntentVisualizations';

const IntentAnalysis = () => {
  const { contractId } = useParams();
  const navigate = useNavigate();

  const [contract, setContract] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [analysisResult, setAnalysisResult] = useState(null);
  const [intentsData, setIntentsData] = useState(null);

  // Load contract details and check if intents already exist
  useEffect(() => {
    loadContractAndIntents();
  }, [contractId]);

  const loadContractAndIntents = async () => {
    try {
      setLoading(true);

      // Load contract details
      const contractRes = await api.get(`/contracts/${contractId}`);
      setContract(contractRes.data.contract);

      // Check if intents already exist
      try {
        const intentsRes = await api.get(`/contracts/${contractId}/intents`);
        if (intentsRes.data.intents && intentsRes.data.intents.length > 0) {
          setIntentsData(intentsRes.data);
        }
      } catch (err) {
        // Intents don't exist yet - that's okay
        console.log('No intents found yet');
      }
    } catch (err) {
      setError('Failed to load contract');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyze = async () => {
    try {
      setAnalyzing(true);
      setError('');

      // Trigger intent analysis
      const response = await api.post(`/contracts/${contractId}/intents/analyze`);

      setAnalysisResult(response.data);

      // Reload intents data
      const intentsRes = await api.get(`/contracts/${contractId}/intents`);
      setIntentsData(intentsRes.data);

    } catch (err) {
      const errorMsg = err.response?.data?.error || err.response?.data?.message || 'Failed to analyze intents';
      setError(errorMsg);
      console.error(err);
    } finally {
      setAnalyzing(false);
    }
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'HIGH':
        return 'text-red-400 bg-red-900/30 border-red-700';
      case 'MEDIUM':
        return 'text-yellow-400 bg-yellow-900/30 border-yellow-700';
      case 'LOW':
        return 'text-green-400 bg-green-900/30 border-green-700';
      default:
        return 'text-slate-400 bg-slate-900/30 border-slate-700';
    }
  };

  const getRiskColor = (riskScore) => {
    if (riskScore >= 0.7) return 'text-red-400 bg-red-900/30 border-red-700';
    if (riskScore >= 0.4) return 'text-yellow-400 bg-yellow-900/30 border-yellow-700';
    return 'text-green-400 bg-green-900/30 border-green-700';
  };

  const getPartyIcon = (party) => {
    switch (party) {
      case 'YOUR_COMPANY':
        return <Shield className="w-4 h-4 text-blue-400" />;
      case 'COUNTERPARTY':
        return <User className="w-4 h-4 text-orange-400" />;
      case 'BOTH':
        return <Target className="w-4 h-4 text-purple-400" />;
      default:
        return <FileText className="w-4 h-4 text-slate-400" />;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-slate-900">
        <div className="text-center">
          <Loader2 className="w-12 h-12 text-blue-500 animate-spin mx-auto mb-4" />
          <p className="text-slate-400">Loading contract...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-900 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <button
            onClick={() => navigate(`/contract/${contractId}/clauses`)}
            className="flex items-center gap-2 text-slate-400 hover:text-white mb-4 transition"
          >
            <ArrowLeft size={20} />
            Back to Contract
          </button>
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-white mb-2">Intent Mining Analysis</h1>
              <p className="text-slate-400">
                {contract?.originalFilename || 'Contract'}
              </p>
            </div>
            {!intentsData && (
              <button
                onClick={handleAnalyze}
                disabled={analyzing}
                className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-700 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition"
              >
                {analyzing ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-5 h-5" />
                    Analyze Intents
                  </>
                )}
              </button>
            )}
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-900/20 border border-red-800 text-red-300 rounded-lg p-4 mb-6 flex items-center gap-3">
            <AlertTriangle size={20} />
            <span>{error}</span>
          </div>
        )}

        {/* Analysis Progress */}
        {analyzing && (
          <div className="bg-slate-800 border border-slate-700 rounded-xl p-8 mb-6">
            <div className="text-center">
              <Loader2 className="w-16 h-16 text-blue-500 animate-spin mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-white mb-2">Analyzing Contract Intents</h3>
              <p className="text-slate-400 mb-4">
                This may take 30-60 seconds. We're discovering legal intents, extracting obligations, and analyzing rights...
              </p>
              <div className="w-full bg-slate-700 rounded-full h-2 overflow-hidden">
                <div className="h-full bg-gradient-to-r from-blue-500 to-purple-500 animate-pulse" style={{ width: '60%' }}></div>
              </div>
            </div>
          </div>
        )}

        {/* Analysis Result Summary */}
        {analysisResult && !analyzing && (
          <div className="bg-gradient-to-br from-green-900/20 to-blue-900/20 border border-green-700/50 rounded-xl p-6 mb-6">
            <div className="flex items-center gap-3 mb-4">
              <CheckCircle className="w-8 h-8 text-green-400" />
              <div>
                <h3 className="text-xl font-semibold text-white">Analysis Complete!</h3>
                <p className="text-slate-300">Successfully analyzed contract intents</p>
              </div>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
              <div className="bg-slate-800/50 rounded-lg p-4">
                <div className="text-sm text-slate-400 mb-1">Clauses Processed</div>
                <div className="text-2xl font-bold text-white">{analysisResult.clauses_processed || 0}</div>
              </div>
              <div className="bg-slate-800/50 rounded-lg p-4">
                <div className="text-sm text-slate-400 mb-1">Intents Discovered</div>
                <div className="text-2xl font-bold text-blue-400">{analysisResult.intents_discovered || 0}</div>
              </div>
              <div className="bg-slate-800/50 rounded-lg p-4">
                <div className="text-sm text-slate-400 mb-1">Obligations</div>
                <div className="text-2xl font-bold text-yellow-400">{analysisResult.obligations_extracted || 0}</div>
              </div>
              <div className="bg-slate-800/50 rounded-lg p-4">
                <div className="text-sm text-slate-400 mb-1">Rights</div>
                <div className="text-2xl font-bold text-green-400">{analysisResult.rights_extracted || 0}</div>
              </div>
            </div>
          </div>
        )}

        {/* Visualizations */}
        {intentsData && intentsData.intents && intentsData.intents.length > 0 && (
          <>
            <IntentVisualizations intentsData={intentsData} />

            {/* Detailed Intent Breakdown */}
            <div className="bg-slate-800 border border-slate-700 rounded-xl overflow-hidden mb-6">
              <div className="px-6 py-4 border-b border-slate-700">
                <h2 className="text-xl font-semibold text-white flex items-center gap-2">
                  <Target className="w-6 h-6" />
                  Discovered Intents & Details
                </h2>
              </div>

              <div className="divide-y divide-slate-700">
                {intentsData.intents.map((intentItem, idx) => (
                  <div key={idx} className="p-6">
                    {/* Intent Header */}
                    <div className="mb-4">
                      <h3 className="text-lg font-semibold text-white mb-2">
                        {intentItem.intent.name}
                      </h3>
                      <p className="text-slate-400 text-sm mb-3">{intentItem.intent.description}</p>
                      <div className="flex gap-3 text-sm">
                        <span className="px-3 py-1 bg-blue-900/30 text-blue-400 rounded-full border border-blue-700">
                          Confidence: {(intentItem.intent.confidence * 100).toFixed(0)}%
                        </span>
                        <span className="px-3 py-1 bg-purple-900/30 text-purple-400 rounded-full border border-purple-700">
                          {intentItem.intent.occurrence_count} occurrence{intentItem.intent.occurrence_count !== 1 ? 's' : ''}
                        </span>
                        <span className="px-3 py-1 bg-yellow-900/30 text-yellow-400 rounded-full border border-yellow-700">
                          {intentItem.obligation_count} obligation{intentItem.obligation_count !== 1 ? 's' : ''}
                        </span>
                        <span className="px-3 py-1 bg-green-900/30 text-green-400 rounded-full border border-green-700">
                          {intentItem.rights_count} right{intentItem.rights_count !== 1 ? 's' : ''}
                        </span>
                      </div>
                    </div>

                    {/* Obligations */}
                    {intentItem.obligations && intentItem.obligations.length > 0 && (
                      <div className="mb-4">
                        <h4 className="text-md font-semibold text-slate-300 mb-3 flex items-center gap-2">
                          <AlertTriangle className="w-4 h-4" />
                          Obligations ({intentItem.obligations.length})
                        </h4>
                        <div className="space-y-3">
                          {intentItem.obligations.map((obl, oblIdx) => (
                            <div key={oblIdx} className="bg-slate-900/50 border border-slate-700 rounded-lg p-4">
                              <div className="flex items-start justify-between mb-2">
                                <div className="flex items-center gap-2">
                                  {getPartyIcon(obl.party)}
                                  <span className="text-sm font-medium text-slate-300">{obl.party.replace('_', ' ')}</span>
                                </div>
                                <div className="flex gap-2">
                                  <span className={`px-2 py-1 text-xs rounded-full border ${getPriorityColor(obl.priority)}`}>
                                    {obl.priority}
                                  </span>
                                  <span className={`px-2 py-1 text-xs rounded-full border ${getRiskColor(obl.risk_score)}`}>
                                    Risk: {(obl.risk_score * 100).toFixed(0)}%
                                  </span>
                                </div>
                              </div>
                              <p className="text-slate-400 text-sm mb-2">{obl.action}</p>
                              {obl.condition && (
                                <p className="text-slate-500 text-xs">
                                  <span className="font-semibold">Condition:</span> {obl.condition}
                                </p>
                              )}
                              {obl.deadline && (
                                <p className="text-slate-500 text-xs flex items-center gap-1 mt-1">
                                  <Clock className="w-3 h-3" />
                                  <span className="font-semibold">Deadline:</span> {obl.deadline}
                                </p>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Rights */}
                    {intentItem.rights && intentItem.rights.length > 0 && (
                      <div>
                        <h4 className="text-md font-semibold text-slate-300 mb-3 flex items-center gap-2">
                          <CheckCircle className="w-4 h-4" />
                          Rights ({intentItem.rights.length})
                        </h4>
                        <div className="space-y-3">
                          {intentItem.rights.map((right, rightIdx) => (
                            <div key={rightIdx} className="bg-slate-900/50 border border-slate-700 rounded-lg p-4">
                              <div className="flex items-start justify-between mb-2">
                                <div className="flex items-center gap-2">
                                  {getPartyIcon(right.party)}
                                  <span className="text-sm font-medium text-slate-300">{right.party.replace('_', ' ')}</span>
                                </div>
                                <span className={`px-2 py-1 text-xs rounded-full border ${getRiskColor(right.risk_score)}`}>
                                  Risk: {(right.risk_score * 100).toFixed(0)}%
                                </span>
                              </div>
                              <p className="text-slate-400 text-sm mb-2">{right.entitlement}</p>
                              {right.trigger && (
                                <p className="text-slate-500 text-xs">
                                  <span className="font-semibold">Trigger:</span> {right.trigger}
                                </p>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </>
        )}

        {/* No Intents Yet */}
        {!intentsData && !analyzing && !analysisResult && (
          <div className="bg-slate-800 border border-slate-700 rounded-xl p-12 text-center">
            <Sparkles className="w-16 h-16 text-slate-600 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-white mb-2">No Intent Analysis Yet</h3>
            <p className="text-slate-400 mb-6 max-w-md mx-auto">
              Discover legal intents, obligations, and rights in this contract using AI-powered analysis.
            </p>
            <button
              onClick={handleAnalyze}
              className="px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-700 hover:to-purple-700 transition inline-flex items-center gap-2"
            >
              <Sparkles className="w-5 h-5" />
              Start Analysis
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default IntentAnalysis;
