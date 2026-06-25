import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Sparkles } from 'lucide-react';
import CounterProposalGenerator from '../components/clauses/CounterProposalGenerator';
import useThemeStore from '../store/themeStore';
import api from '../utils/api';

function CounterProposalPage() {
  const { contractId } = useParams();
  const navigate = useNavigate();
  const { theme } = useThemeStore();
  const [clauses, setClauses] = useState([]);
  const [selectedClause, setSelectedClause] = useState(null);
  const [counterparties, setCounterparties] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, [contractId]);

  const fetchData = async () => {
    try {
      // Fetch clauses
      const response = await api.get(`/contracts/${contractId}/risk-details`);
      if (response.data && response.data.contract && response.data.contract.clauses) {
        const clauseList = response.data.contract.clauses;
        setClauses(clauseList);
        // Auto-select first high-risk clause
        const highRiskClause = clauseList.find(c => c.risk_score > 0.7);
        setSelectedClause(highRiskClause || clauseList[0]);
      }

      // Fetch counterparties (if API exists)
      try {
        const cpResponse = await api.get('/counterparties/list');
        if (cpResponse.data && cpResponse.data.counterparties) {
          setCounterparties(cpResponse.data.counterparties);
        }
      } catch (error) {
        // Counterparties endpoint might not exist, that's okay
        console.log('Counterparties not available');
      }

      setLoading(false);
    } catch (error) {
      console.error('Error fetching data:', error);
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        minHeight: '100vh',
        background: theme === 'dark'
          ? 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)'
          : 'linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%)',
      }}
    >
      <div className="container mx-auto px-6 py-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <button
            onClick={() => navigate(`/contract/${contractId}`)}
            className="flex items-center gap-2 px-4 py-2 rounded-lg hover:bg-slate-700/50 transition-colors"
          >
            <ArrowLeft size={20} />
            <span>Back to Contract</span>
          </button>

          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg flex items-center justify-center" style={{
              background: '#f59e0b14',
              border: '1px solid #f59e0b28',
            }}>
              <Sparkles size={20} style={{ color: '#f59e0b' }} />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white">Counter-Proposal Generator</h1>
              <p className="text-sm text-gray-400">Generate AI-powered counter-proposals for negotiation</p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Clause List Sidebar */}
          <div className="lg:col-span-1">
            <div className="rounded-xl p-4" style={{
              background: 'rgba(15,23,42,0.82)',
              border: '1px solid rgba(51,65,85,0.35)',
            }}>
              <h3 className="text-sm font-bold text-white mb-4">Select Clause to Negotiate</h3>

              {loading ? (
                <div className="text-center py-8 text-gray-400">Loading clauses...</div>
              ) : clauses.length === 0 ? (
                <div className="text-center py-8 text-gray-400">No clauses found</div>
              ) : (
                <div className="space-y-2 max-h-[calc(100vh-300px)] overflow-y-auto">
                  {clauses.map(clause => (
                    <button
                      key={clause.id}
                      onClick={() => setSelectedClause(clause)}
                      className={`w-full text-left p-3 rounded-lg transition-all ${
                        selectedClause?.id === clause.id
                          ? 'bg-orange-500/20 border-orange-500/50'
                          : 'bg-slate-800/50 border-slate-700/50 hover:bg-slate-700/50'
                      }`}
                      style={{ border: '1px solid' }}
                    >
                      <div className="font-medium text-sm mb-1">{clause.clause_name}</div>
                      <div className="text-xs text-gray-400 line-clamp-2">
                        {clause.extracted_text?.slice(0, 80)}...
                      </div>
                      {clause.risk_score && (
                        <div className="mt-2">
                          <span className={`text-xs px-2 py-0.5 rounded ${
                            clause.risk_score > 0.7 ? 'bg-red-500/20 text-red-300' :
                            clause.risk_score > 0.4 ? 'bg-yellow-500/20 text-yellow-300' :
                            'bg-green-500/20 text-green-300'
                          }`}>
                            Risk: {(clause.risk_score * 100).toFixed(0)}%
                          </span>
                        </div>
                      )}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Counter-Proposal Generator Component */}
          <div className="lg:col-span-2">
            {selectedClause ? (
              <CounterProposalGenerator
                clause={selectedClause}
                counterparties={counterparties}
              />
            ) : (
              <div className="rounded-xl p-12 text-center" style={{
                background: 'rgba(15,23,42,0.82)',
                border: '1px solid rgba(51,65,85,0.35)',
              }}>
                <div className="text-gray-400">
                  Select a clause from the left to generate counter-proposals
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default CounterProposalPage;
