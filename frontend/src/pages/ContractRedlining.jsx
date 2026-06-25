import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { AlertTriangle, ChevronDown, ChevronUp, ArrowLeft, Loader, CheckCircle, Download } from 'lucide-react';
import api from '../utils/api';
import RedliningPanel from '../components/RedliningPanel';
import { config } from '../config/api.config';

const ContractRedlining = () => {
  const { contractId } = useParams();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [contractName, setContractName] = useState('');
  const [riskLevel, setRiskLevel] = useState('');
  const [riskyClauses, setRiskyClauses] = useState([]);
  const [expandedClauseId, setExpandedClauseId] = useState(null);
  const [correctionsLoading, setCorrectionsLoading] = useState({});
  const [corrections, setCorrections] = useState({});
  const [acceptedClauses, setAcceptedClauses] = useState(new Set());

  useEffect(() => {
    fetchRiskyClauses();
  }, [contractId]);

  const fetchRiskyClauses = async () => {
    try {
      setLoading(true);
      const response = await api.get(`/contracts/${contractId}/risky-clauses`);

      setContractName(response.data.contract_name || 'Unknown Contract');
      setRiskLevel(response.data.risk_level || 'UNKNOWN');
      setRiskyClauses(response.data.risky_clauses || []);

      // Show message if no risk analysis found
      if (response.data.risk_level === 'UNKNOWN') {
        console.log('No risk analysis found for this contract');
      }

    } catch (error) {
      console.error('Error fetching risky clauses:', error);
      alert(error.response?.data?.message || 'Failed to load risky clauses');
    } finally {
      setLoading(false);
    }
  };

  const loadAutoCorrection = async (clauseId) => {
    if (corrections[clauseId]) return; // Already loaded

    try {
      setCorrectionsLoading((prev) => ({ ...prev, [clauseId]: true }));

      const response = await api.post(`/contracts/clauses/${clauseId}/auto-correct`);

      setCorrections((prev) => ({
        ...prev,
        [clauseId]: {
          suggested_text: response.data.suggested_text,
          explanation: response.data.explanation,
        },
      }));

    } catch (error) {
      console.error('Error loading auto-correction:', error);
      alert(error.response?.data?.message || 'Failed to generate auto-correction');
    } finally {
      setCorrectionsLoading((prev) => ({ ...prev, [clauseId]: false }));
    }
  };

  const handleToggleClause = async (clauseId) => {
    if (expandedClauseId === clauseId) {
      setExpandedClauseId(null);
    } else {
      setExpandedClauseId(clauseId);
      // Load auto-correction when expanding
      if (!corrections[clauseId] && !correctionsLoading[clauseId]) {
        await loadAutoCorrection(clauseId);
      }
    }
  };

  const handleAccept = async (clauseId, suggestedText) => {
    try {
      console.log('Accepting clause:', clauseId, suggestedText);

      // Call the accept suggestion API
      const response = await api.post(`/contracts/clauses/${clauseId}/accept-suggestion`, {
        accepted_text: suggestedText,
        generate_pdf: true
      });

      // Update UI to show clause as accepted
      setAcceptedClauses((prev) => new Set(prev).add(clauseId));

      // Check if PDF was generated
      if (response.data.pdf_generated && response.data.download_url) {
        // Create a success message
        const message = `Suggestion accepted successfully!\n\n` +
          `✓ Clause "${response.data.clause_name}" has been updated\n` +
          `✓ Modified PDF generated with ${response.data.total_accepted_clauses} accepted clause(s)\n\n` +
          `Click OK to download the modified contract.`;

        if (window.confirm(message)) {
          // Trigger download by creating a temporary link
          const downloadUrl = `${config.BASE_URL}${response.data.download_url}`;
          const link = document.createElement('a');
          link.href = downloadUrl;
          link.download = response.data.filename;
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
        }
      } else {
        alert(`Suggestion accepted successfully!\n\n${response.data.message || 'The clause has been updated in the database.'}`);
      }

    } catch (error) {
      console.error('Error accepting suggestion:', error);
      alert(error.response?.data?.message || 'Failed to accept suggestion. Please try again.');
    }
  };

  const handleReject = (clauseId) => {
    console.log('Rejected clause:', clauseId);
    alert('Original clause kept.');
  };

  const handleEdit = (clauseId, editedText) => {
    console.log('Edited clause:', clauseId, editedText);
    setCorrections((prev) => ({
      ...prev,
      [clauseId]: {
        ...prev[clauseId],
        suggested_text: editedText,
      },
    }));
  };

  const handleDownloadModifiedContract = async () => {
    try {
      if (acceptedClauses.size === 0) {
        alert('Please accept at least one clause suggestion before downloading the modified contract.');
        return;
      }

      // Use the download endpoint
      const downloadUrl = config.CONTRACT_DOWNLOAD_URL(contractId);

      // Create a temporary link to trigger download
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.setAttribute('download', ''); // Let the server specify the filename

      // Add auth token to the request
      const token = localStorage.getItem('token');
      if (token) {
        // For direct download, we'll use fetch with blob
        const response = await fetch(downloadUrl, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.message || 'Failed to download modified contract');
        }

        // Get filename from Content-Disposition header
        const contentDisposition = response.headers.get('Content-Disposition');
        let filename = 'Modified_Contract.pdf';
        if (contentDisposition) {
          const filenameMatch = contentDisposition.match(/filename="(.+)"/);
          if (filenameMatch) {
            filename = filenameMatch[1];
          }
        }

        // Create blob and download
        const blob = await response.blob();
        const blobUrl = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = blobUrl;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(blobUrl);

        console.log('Modified contract downloaded successfully');
      }

    } catch (error) {
      console.error('Error downloading modified contract:', error);
      alert(error.message || 'Failed to download modified contract. Please try again.');
    }
  };

  const getRiskLevelColor = (level) => {
    const colors = {
      HIGH: 'bg-red-600',
      MEDIUM: 'bg-yellow-600',
      LOW: 'bg-green-600',
      UNKNOWN: 'bg-gray-600',
    };
    return colors[level] || 'bg-gray-600';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <Loader size={48} className="animate-spin text-blue-600 mx-auto mb-4" />
          <p className="text-slate-600">Loading risky clauses...</p>
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
            onClick={() => navigate(`/contracts/${contractId}`)}
            className="flex items-center gap-2 text-slate-400 hover:text-white mb-4 transition"
          >
            <ArrowLeft size={20} />
            <span className="text-sm font-medium">Back to Contract</span>
          </button>

          <div className="bg-slate-800 rounded-xl shadow-lg border border-slate-700 p-6">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-2xl font-bold text-white mb-2">Risky Clause Redlining</h1>
                <p className="text-slate-300">{contractName}</p>
              </div>
              <div className="text-right">
                <div className="flex items-center gap-3 mb-2">
                  <span className={`px-4 py-2 rounded-lg text-white text-sm font-semibold ${getRiskLevelColor(riskLevel)}`}>
                    {riskLevel} RISK
                  </span>
                  {acceptedClauses.size > 0 && (
                    <button
                      onClick={handleDownloadModifiedContract}
                      className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition font-medium"
                      title="Download modified contract with accepted changes"
                    >
                      <Download size={18} />
                      Download Modified Contract
                    </button>
                  )}
                </div>
                <p className="text-sm text-slate-400">
                  {riskyClauses.length} high-risk {riskyClauses.length === 1 ? 'clause' : 'clauses'} found
                  {acceptedClauses.size > 0 && ` • ${acceptedClauses.size} accepted`}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* No Risky Clauses */}
        {riskyClauses.length === 0 ? (
          riskLevel === 'UNKNOWN' ? (
            <div className="bg-yellow-900/20 border border-yellow-700 rounded-xl p-8 text-center">
              <AlertTriangle size={48} className="text-yellow-500 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-yellow-400 mb-2">No Risk Analysis Found</h3>
              <p className="text-yellow-300 mb-4">Please run risk analysis on this contract first to detect risky clauses.</p>
              <button
                onClick={() => navigate(`/risk-analysis?contract=${contractId}`)}
                className="bg-yellow-600 hover:bg-yellow-700 text-white px-6 py-2 rounded-lg"
              >
                Run Risk Analysis
              </button>
            </div>
          ) : (
            <div className="bg-green-900/20 border border-green-700 rounded-xl p-8 text-center">
              <CheckCircle size={48} className="text-green-500 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-green-400 mb-2">No High-Risk Clauses Detected</h3>
              <p className="text-green-300">This contract appears to have balanced and fair terms.</p>
            </div>
          )
        ) : (
          /* Risky Clauses List */
          <div className="space-y-4">
            {riskyClauses.map((clause, index) => {
              const isExpanded = expandedClauseId === clause.id;
              const isAccepted = acceptedClauses.has(clause.id);
              const correction = corrections[clause.id];
              const isLoadingCorrection = correctionsLoading[clause.id];

              return (
                <div
                  key={clause.id}
                  className={`bg-slate-800 rounded-xl shadow-md border-2 overflow-hidden transition ${
                    isAccepted ? 'border-green-400' : 'border-slate-700 hover:border-blue-500'
                  }`}
                >
                  {/* Clause Header */}
                  <div
                    onClick={() => handleToggleClause(clause.id)}
                    className="flex items-center justify-between p-5 cursor-pointer hover:bg-slate-700 transition"
                  >
                    <div className="flex items-center gap-4 flex-1">
                      <div className="flex items-center justify-center w-10 h-10 rounded-full bg-red-900/30 text-red-400 font-bold border border-red-700">
                        {index + 1}
                      </div>
                      <div className="flex-1">
                        <h3 className="text-lg font-semibold text-white">{clause.clause_name}</h3>
                        <p className="text-sm text-slate-400 mt-1">
                          {clause.deviation_type?.replace('_', ' ')} • {clause.severity} Severity
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-3">
                      {isAccepted && (
                        <span className="px-3 py-1 rounded-full bg-green-900/30 text-green-400 text-xs font-semibold border border-green-700">
                          ✓ Accepted
                        </span>
                      )}
                      {isExpanded ? (
                        <ChevronUp size={24} className="text-slate-400" />
                      ) : (
                        <ChevronDown size={24} className="text-slate-400" />
                      )}
                    </div>
                  </div>

                  {/* Expanded Content */}
                  {isExpanded && (
                    <div className="border-t border-slate-700 p-6 bg-slate-900">
                      {isLoadingCorrection ? (
                        <div className="flex items-center justify-center py-12">
                          <div className="text-center">
                            <Loader size={32} className="animate-spin text-blue-600 mx-auto mb-3" />
                            <p className="text-sm text-slate-600">Generating AI-powered correction...</p>
                          </div>
                        </div>
                      ) : (
                        <RedliningPanel
                          clause={{
                            ...clause,
                            original_text: clause.description,
                            suggested_text: correction?.suggested_text,
                            explanation: correction?.explanation,
                          }}
                          onAccept={(text) => handleAccept(clause.id, text)}
                          onReject={() => handleReject(clause.id)}
                          onEdit={(text) => handleEdit(clause.id, text)}
                        />
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {/* Summary Actions */}
        {riskyClauses.length > 0 && (
          <div className="mt-8 bg-blue-900/20 border border-blue-700 rounded-xl p-6">
            <div className="flex items-start gap-4">
              <AlertTriangle size={24} className="text-blue-400 flex-shrink-0 mt-1" />
              <div className="flex-1">
                <h4 className="font-semibold text-blue-300 mb-2">Next Steps</h4>
                <p className="text-sm text-blue-200 mb-3">
                  Review each high-risk clause above and accept AI-suggested alternatives to reduce legal risk.
                  You can also edit suggestions before accepting them.
                </p>
                <p className="text-xs text-blue-300">
                  💡 Accepted changes: {acceptedClauses.size} of {riskyClauses.length}
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ContractRedlining;
