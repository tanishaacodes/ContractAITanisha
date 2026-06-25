import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Download, AlertTriangle, Sparkles, Loader2, Eye, FileText, ListChecks } from "lucide-react";
import api from "../utils/api";

const AlfrescoContractGrid = ({ contracts, onRefresh }) => {
  const [downloading, setDownloading] = useState({});
  const [extractingClauses, setExtractingClauses] = useState({});
  const navigate = useNavigate();

  /* =========================
     DOWNLOAD CONTRACT HANDLER
  ========================= */
  const handleDownload = async (contract) => {
    try {
      setDownloading(prev => ({ ...prev, [contract.id]: true }));

      const response = await api.get(`/contracts/${contract.id}/download`, {
        responseType: 'blob'
      });

      // Check if response is actually a blob (successful download)
      if (response.data.size === 0) {
        throw new Error('File is empty or not available');
      }

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', contract.original_filename || contract.name || 'contract.pdf');
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Download failed:', error);

      // Try to extract error message from blob response
      let errorMessage = 'Failed to download contract';
      if (error.response?.data instanceof Blob) {
        try {
          const text = await error.response.data.text();
          const errorData = JSON.parse(text);
          errorMessage = errorData.message || errorMessage;
        } catch (e) {
          // If we can't parse the error, use default message
        }
      } else if (error.response?.data?.message) {
        errorMessage = error.response.data.message;
      } else if (error.message) {
        errorMessage = error.message;
      }

      // Add helpful suggestion if file not found
      if (errorMessage.includes('not found')) {
        errorMessage += '\n\nTip: If this is an older contract, try re-syncing from Alfresco to restore the file.';
      }

      alert(errorMessage);
    } finally {
      setDownloading(prev => ({ ...prev, [contract.id]: false }));
    }
  };

  /* =========================
     EXTRACT CLAUSES HANDLER
  ========================= */
  const handleExtractClauses = async (contract) => {
    try {
      setExtractingClauses(prev => ({ ...prev, [contract.id]: true }));

      const response = await api.post(`/contracts/${contract.id}/extract-clauses`);

      if (response.data.message || response.data.clauses) {
        // Navigate to contract details page where clauses will be visible
        navigate(`/contracts/${contract.id}`);
      } else {
        throw new Error('Clause extraction failed');
      }
    } catch (error) {
      console.error('Extract clauses failed:', error);
      const errorMessage = error.response?.data?.message || error.response?.data?.error || error.message || 'Failed to extract clauses';

      // Only show alert if it's not a "contract not found" error (which can happen for stale data)
      if (!errorMessage.toLowerCase().includes('not found')) {
        alert(`Failed to extract clauses: ${errorMessage}`);
      } else {
        // For "not found" errors, just log to console to avoid annoying popups
        console.warn(`Contract ${contract.id} not found - it may have been deleted or the page needs to be refreshed`);
      }
    } finally {
      setExtractingClauses(prev => ({ ...prev, [contract.id]: false }));
    }
  };

  /* =========================
     EXTRACTION STATUS HELPER
  ========================= */
  const getExtractionStatusBadge = (contract) => {
    const hasIntelligence = contract.has_intelligence || contract.intelligence_extracted;

    if (hasIntelligence) {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-green-900/30 text-green-400 border border-green-800">
          <Sparkles size={12} />
          Extracted
        </span>
      );
    }

    return (
      <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-slate-700/50 text-slate-400 border border-slate-600">
        Pending
      </span>
    );
  };

  if (!contracts || contracts.length === 0) {
    return (
      <div className="bg-slate-900 border border-slate-700 rounded-xl p-12 text-center">
        <FileText className="w-16 h-16 text-slate-600 mx-auto mb-4" />
        <h3 className="text-xl font-semibold text-white mb-2">No Contracts Synced</h3>
        <p className="text-slate-400">
          Click "Start Sync" to import contracts from Alfresco
        </p>
      </div>
    );
  }

  return (
    <div className="bg-slate-900 border border-slate-700 rounded-xl p-4">
      {/* HEADER */}
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-white">
          Synced Contracts ({contracts.length})
        </h2>
      </div>

      {/* TABLE */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm text-slate-300">
          <thead className="bg-slate-800 text-slate-100">
            <tr>
              <th className="px-4 py-3 text-left">File Name</th>
              <th className="px-4 py-3 text-left">Type</th>
              <th className="px-4 py-3 text-left">Uploaded</th>
              <th className="px-4 py-3 text-left">Intelligence</th>
              <th className="px-4 py-3 text-left">Actions</th>
            </tr>
          </thead>

          <tbody>
            {contracts.map((contract) => (
              <tr
                key={contract.id}
                className="border-t border-slate-700 hover:bg-slate-800 transition"
              >
                {/* FILE NAME */}
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <FileText className="w-4 h-4 text-blue-400" />
                    <span className="text-white font-medium">
                      {contract.original_filename || contract.name || 'Unnamed Contract'}
                    </span>
                  </div>
                </td>

                {/* TYPE */}
                <td className="px-4 py-3">
                  <span className="px-2 py-1 bg-slate-700 rounded text-xs">
                    {contract.contractType || contract.contract_type || 'NDA'}
                  </span>
                </td>

                {/* UPLOADED DATE */}
                <td className="px-4 py-3">
                  {contract.uploaded_at
                    ? new Date(contract.uploaded_at).toLocaleDateString()
                    : 'N/A'
                  }
                </td>

                {/* EXTRACTION STATUS BADGE */}
                <td className="px-4 py-3">
                  {getExtractionStatusBadge(contract)}
                </td>

                {/* ACTIONS COLUMN */}
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    {/* View Contract Button */}
                    <button
                      onClick={() => navigate(`/contracts/${contract.id}`)}
                      className="flex items-center gap-1 bg-blue-600 hover:bg-blue-700 text-white px-3 py-1.5 rounded text-xs transition"
                      title="View Contract"
                    >
                      <Eye size={14} />
                      View
                    </button>

                    {/* Extract Clauses Button */}
                    <button
                      onClick={() => handleExtractClauses(contract)}
                      disabled={extractingClauses[contract.id]}
                      className="flex items-center gap-1 bg-teal-600 hover:bg-teal-700 disabled:bg-teal-800 disabled:cursor-not-allowed text-white px-3 py-1.5 rounded text-xs transition"
                      title="Extract Clauses"
                    >
                      {extractingClauses[contract.id] ? (
                        <Loader2 size={14} className="animate-spin" />
                      ) : (
                        <ListChecks size={14} />
                      )}
                      Clauses
                    </button>

                    {/* Risk Analysis Button */}
                    <button
                      onClick={() => {
                        console.log('Navigating to risk analysis for contract:', contract.id);
                        navigate(`/risk-analysis/${contract.id}`);
                      }}
                      className="flex items-center gap-1 bg-orange-600 hover:bg-orange-700 text-white px-3 py-1.5 rounded text-xs transition"
                      title="Analyze Risk"
                    >
                      <AlertTriangle size={14} />
                      Risk
                    </button>

                    {/* Download Button */}
                    <button
                      onClick={() => handleDownload(contract)}
                      disabled={downloading[contract.id]}
                      className="flex items-center gap-1 bg-purple-600 hover:bg-purple-700 disabled:bg-purple-800 disabled:cursor-not-allowed text-white px-3 py-1.5 rounded text-xs transition"
                      title="Download Contract"
                    >
                      {downloading[contract.id] ? (
                        <Loader2 size={14} className="animate-spin" />
                      ) : (
                        <Download size={14} />
                      )}
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default AlfrescoContractGrid;
