import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ChevronLeft, ChevronRight, AlertTriangle, CheckSquare, Square, Sparkles, Loader2, Edit, Trash2, UserPlus, Eye, Shield, Scale } from "lucide-react";
import api from "../utils/api";
import useThemeStore from "../store/themeStore";

const DocumentGrid = ({ showPagination = false, itemsPerPage = 5 }) => {
  const { theme } = useThemeStore();
  const [contracts, setContracts] = useState([]);
  const [search, setSearch] = useState("");
  const [sortOrder, setSortOrder] = useState("latest");
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedContracts, setSelectedContracts] = useState([]);
  const [bulkActionsLoading, setBulkActionsLoading] = useState(false);
  const [deleting, setDeleting] = useState({});
  const [assignModalOpen, setAssignModalOpen] = useState(false);
  const [contractToAssign, setContractToAssign] = useState(null);
  const [assignEmail, setAssignEmail] = useState('');
  const [assigning, setAssigning] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    api.get("/contracts/list").then((res) => {
      setContracts(res.data.contracts || []);
    });
  }, []);

  const toggleSelectAll = () => {
    if (selectedContracts.length === visibleContracts.length) {
      setSelectedContracts([]);
    } else {
      setSelectedContracts(visibleContracts.map(c => c.id));
    }
  };

  const toggleSelectContract = (contractId) => {
    setSelectedContracts(prev =>
      prev.includes(contractId)
        ? prev.filter(id => id !== contractId)
        : [...prev, contractId]
    );
  };

  const isContractSelected = (contractId) => selectedContracts.includes(contractId);

  const handleDelete = async (contract) => {
    if (!window.confirm(`Are you sure you want to delete "${contract.original_filename}"?\n\nThis action cannot be undone.`)) return;
    try {
      setDeleting(prev => ({ ...prev, [contract.id]: true }));
      await api.delete(`/contracts/${contract.id}/delete`);
      setContracts(prev => prev.filter(c => c.id !== contract.id));
      setSelectedContracts(prev => prev.filter(id => id !== contract.id));
      alert('Contract deleted successfully');
    } catch (error) {
      console.error('Delete failed:', error);
      alert(error.response?.data?.message || 'Failed to delete contract');
    } finally {
      setDeleting(prev => ({ ...prev, [contract.id]: false }));
    }
  };

  const handleAssignClick = (contract) => {
    setContractToAssign(contract);
    setAssignModalOpen(true);
    setAssignEmail('');
  };

  const handleAssignSubmit = async () => {
    if (!assignEmail.trim()) {
      alert('Please enter an email address');
      return;
    }
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(assignEmail)) {
      alert('Please enter a valid email address');
      return;
    }
    setAssigning(true);
    try {
      await api.post(`/contracts/${contractToAssign.id}/assign`, { email: assignEmail.trim() });
      alert(`Contract successfully assigned to ${assignEmail}`);
      setAssignModalOpen(false);
      setContractToAssign(null);
      setAssignEmail('');
    } catch (error) {
      console.error('Assignment failed:', error);
      alert(error.response?.data?.message || 'Failed to assign contract');
    } finally {
      setAssigning(false);
    }
  };

  const handleForceMajeureClick = async (contract) => {
    try {
      // Fetch full contract details including full_text
      const response = await api.get(`/contracts/${contract.id}`);
      const fullContract = response.data.contract;

      // Navigate with the complete contract data including all metadata
      navigate('/force-majeure', {
        state: {
          contractId: fullContract.id,
          contractTitle: fullContract.original_filename || fullContract.filename,
          contractText: fullContract.full_text || fullContract.fullText || '',
          contractValue: fullContract.contract_value || fullContract.contractValue || fullContract.total_liability || 0,
          jurisdiction: fullContract.jurisdiction || fullContract.governing_law || '',
          projectLocation: fullContract.project_location || fullContract.projectLocation || fullContract.location || '',
          supplierLocations: fullContract.supplier_locations || fullContract.supplierLocations || fullContract.suppliers || ''
        }
      });
    } catch (error) {
      console.error('Failed to fetch contract details:', error);
      alert('Failed to load contract. Please try again.');
    }
  };

  const handleBulkExtractIntelligence = async () => {
    if (selectedContracts.length === 0) {
      alert('Please select contracts first');
      return;
    }
    setBulkActionsLoading(true);
    try {
      await api.post('/contracts/bulk/extract-intelligence', { contract_ids: selectedContracts });
      alert(`Intelligence extraction started for ${selectedContracts.length} contracts`);
      setSelectedContracts([]);
      const res = await api.get("/contracts/list");
      setContracts(res.data.contracts || []);
    } catch (error) {
      console.error('Bulk extraction failed:', error);
      alert('Failed to start bulk extraction');
    } finally {
      setBulkActionsLoading(false);
    }
  };

  const handleBulkRiskAnalysis = async () => {
    if (selectedContracts.length === 0) {
      alert('Please select contracts first');
      return;
    }
    setBulkActionsLoading(true);
    try {
      await api.post('/contracts/bulk/risk-analysis', { contract_ids: selectedContracts });
      alert(`Risk analysis started for ${selectedContracts.length} contracts`);
      setSelectedContracts([]);
    } catch (error) {
      console.error('Bulk risk analysis failed:', error);
      alert('Failed to start bulk risk analysis');
    } finally {
      setBulkActionsLoading(false);
    }
  };

  const getExtractionStatusBadge = (contract) => {
    const hasIntelligence = contract.has_intelligence || contract.intelligence_extracted;
    if (hasIntelligence) {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-green-500/20 text-green-400 border border-green-500/30">
          <Sparkles size={10} />
          Yes
        </span>
      );
    }
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-slate-700/50 text-slate-400 border border-slate-600/50">
        No
      </span>
    );
  };

  const getRiskBadge = (contract) => {
    if (!contract.hasRiskAnalysis && !contract.has_analysis) {
      return <span className="text-slate-500">—</span>;
    }
    const riskLevel = contract.risk_level || 'LOW';
    const riskConfig = {
      'CRITICAL': { label: 'Critical', color: 'bg-red-500/20 text-red-400 border-red-500/30' },
      'HIGH': { label: 'High', color: 'bg-orange-500/20 text-orange-400 border-orange-500/30' },
      'MEDIUM': { label: 'Medium', color: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30' },
      'LOW': { label: 'Low', color: 'bg-green-500/20 text-green-400 border-green-500/30' }
    };
    const config = riskConfig[riskLevel] || riskConfig['LOW'];
    return (
      <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium border ${config.color}`}>
        <AlertTriangle size={10} />
        {config.label}
      </span>
    );
  };

  const filteredContracts = contracts.filter((c) =>
    c.original_filename?.toLowerCase().includes(search.toLowerCase())
  );

  const sortedContracts = [...filteredContracts].sort((a, b) => {
    const dateA = new Date(a.uploaded_at);
    const dateB = new Date(b.uploaded_at);
    return sortOrder === "latest" ? dateB - dateA : dateA - dateB;
  });

  const totalPages = Math.ceil(sortedContracts.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const visibleContracts = sortedContracts.slice(startIndex, startIndex + itemsPerPage);

  return (
    <div className={`mt-6 ${theme.colors.surface} border ${theme.colors.surfaceBorder} rounded-xl p-5`}>
      {/* HEADER */}
      <div className="flex items-center justify-between mb-4">
        <h2 className={`text-lg font-semibold ${theme.colors.textPrimary}`}>
          Summary of Contracts
        </h2>
        <div className="flex gap-2">
          <input
            type="text"
            placeholder="Search file..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className={`${theme.colors.surfaceHover} ${theme.colors.textPrimary} text-sm px-3 py-1.5 rounded-lg border ${theme.colors.surfaceBorder} focus:border-blue-500 outline-none`}
          />
          <select
            value={sortOrder}
            onChange={(e) => setSortOrder(e.target.value)}
            className={`${theme.colors.surfaceHover} ${theme.colors.textPrimary} text-sm px-3 py-1.5 rounded-lg border ${theme.colors.surfaceBorder} outline-none cursor-pointer`}
          >
            <option value="latest">Latest</option>
            <option value="oldest">Oldest</option>
          </select>
          <button
            onClick={() => navigate("/contracts")}
            className="bg-blue-600 hover:bg-blue-700 text-white text-sm px-4 py-1.5 rounded-lg font-medium"
          >
            View All
          </button>
        </div>
      </div>

      {/* BULK ACTIONS */}
      {selectedContracts.length > 0 && (
        <div className="mb-4 bg-blue-900/20 border border-blue-700/50 rounded-lg p-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-blue-400 font-medium text-sm">
              {selectedContracts.length} selected
            </span>
            <button onClick={() => setSelectedContracts([])} className="text-slate-400 hover:text-blue-400 text-sm">
              Clear
            </button>
          </div>
          <div className="flex gap-2">
            <button
              onClick={handleBulkExtractIntelligence}
              disabled={bulkActionsLoading}
              className="flex items-center gap-1.5 bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white px-3 py-1.5 rounded-lg text-sm font-medium"
            >
              {bulkActionsLoading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5" />}
              Extract Intel
            </button>
            <button
              onClick={handleBulkRiskAnalysis}
              disabled={bulkActionsLoading}
              className="flex items-center gap-1.5 bg-orange-600 hover:bg-orange-700 disabled:opacity-50 text-white px-3 py-1.5 rounded-lg text-sm font-medium"
            >
              {bulkActionsLoading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <AlertTriangle className="w-3.5 h-3.5" />}
              Analyze Risk
            </button>
          </div>
        </div>
      )}

      {/* TABLE */}
      <div className="rounded-lg border border-slate-700/50 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-800/50">
            <tr className="text-slate-400 text-xs uppercase">
              <th className="px-3 py-3 text-left w-10">
                <button onClick={toggleSelectAll} className="hover:text-blue-400">
                  {selectedContracts.length === visibleContracts.length && visibleContracts.length > 0 ? (
                    <CheckSquare size={16} className="text-blue-400" />
                  ) : (
                    <Square size={16} />
                  )}
                </button>
              </th>
              <th className="px-3 py-3 text-left">File</th>
              <th className="px-3 py-3 text-left">Type</th>
              <th className="px-3 py-3 text-left">Value</th>
              <th className="px-3 py-3 text-left">Parties</th>
              <th className="px-3 py-3 text-left">Duration</th>
              <th className="px-3 py-3 text-left">Date</th>
              <th className="px-3 py-3 text-left">Status</th>
              <th className="px-3 py-3 text-left">Risk</th>
              <th className="px-3 py-3 text-left">Intel</th>
              <th className="px-3 py-3 text-left">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-700/30">
            {visibleContracts.map((c) => {
              const partyA = c.partyA || c.party_a || "—";
              const partyB = c.partyB || c.party_b || null;
              const contractValue = c.contractValue || c.contract_value || "—";

              return (
                <tr key={c.id} className={`hover:bg-slate-800/30 ${isContractSelected(c.id) ? 'bg-blue-900/10' : ''}`}>
                  <td className="px-3 py-3">
                    <button onClick={() => toggleSelectContract(c.id)} className="hover:text-blue-400">
                      {isContractSelected(c.id) ? (
                        <CheckSquare size={16} className="text-blue-400" />
                      ) : (
                        <Square size={16} className="text-slate-500" />
                      )}
                    </button>
                  </td>
                  <td className="px-3 py-3">
                    <span
                      onClick={() => navigate(`/contracts/${c.id}`)}
                      className="text-blue-400 hover:text-blue-300 cursor-pointer truncate block max-w-[140px]"
                      title={c.original_filename}
                    >
                      {c.original_filename}
                    </span>
                  </td>
                  <td className="px-3 py-3 text-slate-400">
                    {c.contractType || c.contract_type || "NDA"}
                  </td>
                  <td className="px-3 py-3 text-white font-medium">
                    {contractValue}
                  </td>
                  <td className="px-3 py-3">
                    <div className="max-w-[100px]">
                      <div className="text-slate-300 truncate text-xs">{partyA}</div>
                      {partyB && <div className="text-slate-500 truncate text-xs">vs {partyB}</div>}
                    </div>
                  </td>
                  <td className="px-3 py-3 text-slate-500">—</td>
                  <td className="px-3 py-3 text-slate-400 text-xs">
                    {new Date(c.uploaded_at || c.uploadedAt).toLocaleDateString('en-GB', {
                      day: '2-digit', month: '2-digit', year: '2-digit'
                    })}
                  </td>
                  <td className="px-3 py-3">
                    <span className="px-2 py-0.5 rounded text-xs font-medium bg-slate-700/50 text-slate-300 border border-slate-600/50">
                      {c.status || 'Draft'}
                    </span>
                  </td>
                  <td className="px-3 py-3">{getRiskBadge(c)}</td>
                  <td className="px-3 py-3">{getExtractionStatusBadge(c)}</td>
                  <td className="px-3 py-3">
                    <div className="flex items-center gap-1">
                      <button
                        onClick={() => navigate(`/contracts/${c.id}`)}
                        className="p-1.5 rounded bg-blue-600 hover:bg-blue-700 text-white"
                        title="View"
                      >
                        <Eye size={14} />
                      </button>
                      {(c.status === 'DRAFT' || !c.status) && (
                        <button
                          onClick={() => navigate(`/contracts/${c.id}/edit`)}
                          className="p-1.5 rounded bg-purple-600 hover:bg-purple-700 text-white"
                          title="Edit"
                        >
                          <Edit size={14} />
                        </button>
                      )}
                      <button
                        onClick={() => navigate(`/risk-analysis/${c.id}`)}
                        className="p-1.5 rounded bg-orange-600 hover:bg-orange-700 text-white"
                        title="Risk Analysis"
                      >
                        <AlertTriangle size={14} />
                      </button>
                      <button
                        onClick={() => handleForceMajeureClick(c)}
                        className="p-1.5 rounded bg-indigo-600 hover:bg-indigo-700 text-white"
                        title="Force Majeure Analysis"
                      >
                        <Shield size={14} />
                      </button>
                      <button
                        onClick={() => handleDelete(c)}
                        disabled={deleting[c.id]}
                        className="p-1.5 rounded bg-red-600 hover:bg-red-700 disabled:opacity-50 text-white"
                        title="Delete"
                      >
                        {deleting[c.id] ? <Loader2 size={14} className="animate-spin" /> : <Trash2 size={14} />}
                      </button>
                      <button
                        onClick={() => handleAssignClick(c)}
                        className="p-1.5 rounded bg-teal-600 hover:bg-teal-700 text-white"
                        title="Assign"
                      >
                        <UserPlus size={14} />
                      </button>
                      <button
                        onClick={() => navigate(`/contracts/${c.id}/legal-review`)}
                        className="p-1.5 rounded bg-violet-600 hover:bg-violet-700 text-white"
                        title="Legal Review"
                      >
                        <Scale size={14} />
                      </button>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* PAGINATION */}
      {showPagination && totalPages > 1 && (
        <div className="flex items-center justify-between mt-4 pt-4 border-t border-slate-700/50">
          <div className="text-sm text-slate-400">
            Page <span className="text-white">{currentPage}</span> of <span className="text-white">{totalPages}</span> · <span className="text-white">{sortedContracts.length}</span> total contracts
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setCurrentPage((p) => Math.max(p - 1, 1))}
              disabled={currentPage === 1}
              className={`flex items-center gap-1 px-3 py-1.5 rounded-lg text-sm ${
                currentPage === 1 ? 'bg-slate-800/50 text-slate-600 cursor-not-allowed' : 'bg-slate-800 text-white hover:bg-slate-700'
              }`}
            >
              <ChevronLeft size={16} /> Previous
            </button>
            <button
              onClick={() => setCurrentPage((p) => Math.min(p + 1, totalPages))}
              disabled={currentPage === totalPages}
              className={`flex items-center gap-1 px-3 py-1.5 rounded-lg text-sm ${
                currentPage === totalPages ? 'bg-slate-800/50 text-slate-600 cursor-not-allowed' : 'bg-slate-800 text-white hover:bg-slate-700'
              }`}
            >
              Next <ChevronRight size={16} />
            </button>
          </div>
        </div>
      )}

      {/* ASSIGN MODAL */}
      {assignModalOpen && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50">
          <div className="bg-slate-900 border border-slate-700 rounded-xl p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold text-white mb-4">Assign Contract</h3>
            <p className="text-slate-400 mb-4">
              Assign <span className="text-blue-400">{contractToAssign?.original_filename}</span> to another user
            </p>
            <div className="mb-4">
              <label className="block text-sm text-slate-300 mb-2">User Email</label>
              <input
                type="email"
                value={assignEmail}
                onChange={(e) => setAssignEmail(e.target.value)}
                placeholder="user@example.com"
                className="w-full bg-slate-800 text-white px-4 py-2 rounded-lg border border-slate-700 focus:border-blue-500 outline-none"
                disabled={assigning}
              />
            </div>
            <div className="flex gap-2 justify-end">
              <button
                onClick={() => { setAssignModalOpen(false); setContractToAssign(null); setAssignEmail(''); }}
                disabled={assigning}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg"
              >
                Cancel
              </button>
              <button
                onClick={handleAssignSubmit}
                disabled={assigning || !assignEmail.trim()}
                className="flex items-center gap-2 px-4 py-2 bg-teal-600 hover:bg-teal-700 disabled:opacity-50 text-white rounded-lg"
              >
                {assigning ? <Loader2 size={16} className="animate-spin" /> : <UserPlus size={16} />}
                Assign
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DocumentGrid;
