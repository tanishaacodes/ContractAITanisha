import { useEffect, useState } from "react";
import { Layers, PlayCircle, Info, TrendingUp, ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight, ArrowUpDown, ArrowUp, ArrowDown, Filter, BarChart3 } from "lucide-react";
import api from "../utils/api";

const ContractClassify = () => {
  const [contracts, setContracts] = useState([]);
  const [loadingId, setLoadingId] = useState(null);
  const [selectedContract, setSelectedContract] = useState(null);

  const [clusterHtml, setClusterHtml] = useState("");
  const [clusterError, setClusterError] = useState(false);
  const [loadingClusters, setLoadingClusters] = useState(false);

  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(10);

  // Sorting state
  const [sortField, setSortField] = useState(null);
  const [sortDirection, setSortDirection] = useState("asc");

  // Filter state
  const [filterType, setFilterType] = useState("all");
  const [filterConfidence, setFilterConfidence] = useState("all");

  // ===============================
  // Fetch contracts
  // ===============================
  const fetchContracts = async () => {
    try {
      const res = await api.get("/contracts/classify/");
      setContracts(res.data || []);
    } catch {
      setContracts([]);
    }
  };

  // ===============================
  // Fetch BERTopic clusters
  // ===============================
  const fetchClusters = async () => {
    try {
      setLoadingClusters(true);
      const res = await api.get("/contracts/classify/clusters/");
      setClusterHtml(res.data.html || "");
      setClusterError(false);
    } catch {
      setClusterError(true);
      setClusterHtml("");
    } finally {
      setLoadingClusters(false);
    }
  };

  // ===============================
  // Initial load
  // ===============================
  useEffect(() => {
    fetchContracts();
  }, []);

  // Load clusters once enough contracts exist
  useEffect(() => {
    if (contracts.length >= 3) {
      fetchClusters();
    }
  }, [contracts]);

  // ===============================
  // Trigger classification
  // ===============================
  const handleClassify = async (contractId) => {
    try {
      setLoadingId(contractId);
      const res = await api.post(`/contracts/classify/${contractId}/`);

      // Show detailed results
      if (res.data) {
        setSelectedContract({
          id: contractId,
          ...res.data
        });
      }

      await fetchContracts();
      await fetchClusters();
    } catch (err) {
      alert("Classification failed: " + (err.response?.data?.error || err.message));
    } finally {
      setLoadingId(null);
    }
  };

  // ===============================
  // Sorting function
  // ===============================
  const handleSort = (field) => {
    if (sortField === field) {
      setSortDirection(sortDirection === "asc" ? "desc" : "asc");
    } else {
      setSortField(field);
      setSortDirection("asc");
    }
    setCurrentPage(1); // Reset to first page on sort
  };

  // ===============================
  // Get filtered and sorted contracts
  // ===============================
  const getProcessedContracts = () => {
    let processed = [...contracts];

    // Apply filters
    if (filterType !== "all") {
      processed = processed.filter(c => c.primary_class === filterType);
    }

    if (filterConfidence !== "all") {
      if (filterConfidence === "high") {
        processed = processed.filter(c => c.confidence >= 70);
      } else if (filterConfidence === "medium") {
        processed = processed.filter(c => c.confidence >= 40 && c.confidence < 70);
      } else if (filterConfidence === "low") {
        processed = processed.filter(c => c.confidence < 40);
      }
    }

    // Apply sorting
    if (sortField) {
      processed.sort((a, b) => {
        let aVal = a[sortField];
        let bVal = b[sortField];

        // Handle null/undefined values
        if (aVal == null) aVal = "";
        if (bVal == null) bVal = "";

        // String comparison
        if (typeof aVal === "string") {
          return sortDirection === "asc"
            ? aVal.localeCompare(bVal)
            : bVal.localeCompare(aVal);
        }

        // Number comparison
        return sortDirection === "asc"
          ? aVal - bVal
          : bVal - aVal;
      });
    }

    return processed;
  };

  // ===============================
  // Pagination logic
  // ===============================
  const processedContracts = getProcessedContracts();
  const totalPages = Math.ceil(processedContracts.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const paginatedContracts = processedContracts.slice(startIndex, endIndex);

  // Get unique contract types for filter
  const uniqueTypes = [...new Set(contracts.map(c => c.primary_class).filter(Boolean))];

  // Calculate statistics
  const stats = {
    total: contracts.length,
    classified: contracts.filter(c => c.primary_class && c.primary_class !== "Not Classified").length,
    avgConfidence: contracts.length > 0
      ? (contracts.reduce((sum, c) => sum + (c.confidence || 0), 0) / contracts.length).toFixed(1)
      : 0,
    uniqueTypes: uniqueTypes.length
  };

  return (
    <div className="p-6 text-white space-y-6">
      {/* ================= HEADER ================= */}
      <div className="flex items-center gap-3">
        <Layers className="text-blue-500" />
        <h1 className="text-2xl font-bold">Contract Classification</h1>
      </div>

      {/* ================= STATISTICS DASHBOARD ================= */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-slate-900 rounded-lg border border-slate-700 p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-slate-400 text-sm">Total Contracts</p>
              <p className="text-2xl font-bold text-white mt-1">{stats.total}</p>
            </div>
            <BarChart3 className="text-blue-500" size={32} />
          </div>
        </div>

        <div className="bg-slate-900 rounded-lg border border-slate-700 p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-slate-400 text-sm">Classified</p>
              <p className="text-2xl font-bold text-green-400 mt-1">{stats.classified}</p>
            </div>
            <Layers className="text-green-500" size={32} />
          </div>
        </div>

        <div className="bg-slate-900 rounded-lg border border-slate-700 p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-slate-400 text-sm">Avg Confidence</p>
              <p className="text-2xl font-bold text-purple-400 mt-1">{stats.avgConfidence}%</p>
            </div>
            <TrendingUp className="text-purple-500" size={32} />
          </div>
        </div>

        <div className="bg-slate-900 rounded-lg border border-slate-700 p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-slate-400 text-sm">Unique Types</p>
              <p className="text-2xl font-bold text-orange-400 mt-1">{stats.uniqueTypes}</p>
            </div>
            <Filter className="text-orange-500" size={32} />
          </div>
        </div>
      </div>

      {/* ================= FILTERS ================= */}
      <div className="bg-slate-900 rounded-lg border border-slate-700 p-4">
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex items-center gap-2">
            <Filter className="text-slate-400" size={18} />
            <span className="text-slate-400 text-sm font-medium">Filters:</span>
          </div>

          {/* Type Filter */}
          <select
            value={filterType}
            onChange={(e) => {
              setFilterType(e.target.value);
              setCurrentPage(1);
            }}
            className="bg-slate-800 border border-slate-600 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:border-blue-500"
          >
            <option value="all">All Types</option>
            {uniqueTypes.map(type => (
              <option key={type} value={type}>{type}</option>
            ))}
          </select>

          {/* Confidence Filter */}
          <select
            value={filterConfidence}
            onChange={(e) => {
              setFilterConfidence(e.target.value);
              setCurrentPage(1);
            }}
            className="bg-slate-800 border border-slate-600 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:border-blue-500"
          >
            <option value="all">All Confidence Levels</option>
            <option value="high">High (≥70%)</option>
            <option value="medium">Medium (40-69%)</option>
            <option value="low">Low (&lt;40%)</option>
          </select>

          {/* Items per page */}
          <select
            value={itemsPerPage}
            onChange={(e) => {
              setItemsPerPage(Number(e.target.value));
              setCurrentPage(1);
            }}
            className="bg-slate-800 border border-slate-600 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:border-blue-500"
          >
            <option value={5}>5 per page</option>
            <option value={10}>10 per page</option>
            <option value={25}>25 per page</option>
            <option value={50}>50 per page</option>
          </select>

          {/* Results count */}
          <span className="text-slate-400 text-sm ml-auto">
            Showing {processedContracts.length === 0 ? 0 : startIndex + 1}-{Math.min(endIndex, processedContracts.length)} of {processedContracts.length}
          </span>
        </div>
      </div>

      {/* ================= FUSION RESULTS MODAL ================= */}
      {selectedContract && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
          <div className="bg-slate-900 rounded-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto border border-slate-700">
            {/* Header */}
            <div className="p-6 border-b border-slate-700 flex justify-between items-center">
              <div>
                <h2 className="text-2xl font-bold text-white flex items-center gap-2">
                  <TrendingUp className="text-green-500" />
                  Classification Results
                </h2>
                <p className="text-slate-400 text-sm mt-1">
                  Fusion: BERTopic + Contracts-BERT
                </p>
              </div>
              <button
                onClick={() => setSelectedContract(null)}
                className="text-slate-400 hover:text-white text-2xl"
              >
                ×
              </button>
            </div>

            {/* Content */}
            <div className="p-6 space-y-6">
              {/* Primary Classification */}
              <div className="bg-gradient-to-r from-blue-600/20 to-purple-600/20 rounded-lg p-5 border border-blue-500/30">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-slate-400 text-sm">Primary Classification</p>
                    <h3 className="text-3xl font-bold text-white mt-1">
                      {selectedContract.contractType}
                    </h3>
                  </div>
                  <div className="text-right">
                    <p className="text-slate-400 text-sm">Confidence</p>
                    <p className="text-3xl font-bold text-green-400">
                      {selectedContract.confidenceScore?.toFixed(1)}%
                    </p>
                  </div>
                </div>
              </div>

              {/* Explanation */}
              {selectedContract.explanation && (
                <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
                  <div className="flex items-start gap-2">
                    <Info className="text-blue-400 mt-1 flex-shrink-0" size={18} />
                    <div>
                      <p className="text-sm font-semibold text-slate-300 mb-1">
                        Classification Reasoning
                      </p>
                      <p className="text-sm text-slate-400">
                        {selectedContract.explanation}
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Intent Distribution */}
              {selectedContract.intents && Object.keys(selectedContract.intents).length > 0 && (
                <div className="bg-slate-800 rounded-lg p-5 border border-slate-700">
                  <h4 className="text-lg font-semibold mb-4">Legal Intent Distribution</h4>
                  <div className="space-y-2">
                    {Object.entries(selectedContract.intents)
                      .sort(([, a], [, b]) => b - a)
                      .slice(0, 5)
                      .map(([intent, weight]) => (
                        <div key={intent}>
                          <div className="flex justify-between text-sm mb-1">
                            <span className="text-slate-300">{intent}</span>
                            <span className="text-slate-400">{(weight * 100).toFixed(1)}%</span>
                          </div>
                          <div className="w-full bg-slate-700 rounded-full h-2">
                            <div
                              className="bg-gradient-to-r from-blue-500 to-purple-500 h-2 rounded-full"
                              style={{ width: `${weight * 100}%` }}
                            />
                          </div>
                        </div>
                      ))}
                  </div>
                </div>
              )}

              {/* Alternative Classifications */}
              {selectedContract.fusedScores && (
                <div className="bg-slate-800 rounded-lg p-5 border border-slate-700">
                  <h4 className="text-lg font-semibold mb-4">Alternative Classifications</h4>
                  <div className="space-y-2">
                    {Object.entries(selectedContract.fusedScores)
                      .sort(([, a], [, b]) => b - a)
                      .slice(0, 5)
                      .map(([type, score]) => (
                        <div key={type} className="flex justify-between text-sm">
                          <span className="text-slate-300">{type}</span>
                          <span className="text-slate-400">{(score * 100).toFixed(1)}%</span>
                        </div>
                      ))}
                  </div>
                </div>
              )}

              {/* BERTopic Details */}
              {selectedContract.topics && (
                <div className="bg-slate-800 rounded-lg p-5 border border-slate-700">
                  <h4 className="text-lg font-semibold mb-3">BERTopic Analysis</h4>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <p className="text-slate-400">Topic Name</p>
                      <p className="text-white font-medium">
                        {selectedContract.topics.contractType || "N/A"}
                      </p>
                    </div>
                    <div>
                      <p className="text-slate-400">Topic ID</p>
                      <p className="text-white font-medium">
                        {selectedContract.topics.topicId ?? "N/A"}
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="p-4 border-t border-slate-700 flex justify-end">
              <button
                onClick={() => setSelectedContract(null)}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg text-white transition"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ================= TABLE ================= */}
      <div className="bg-slate-900 rounded-xl overflow-hidden border border-slate-700">
        <table className="w-full text-sm">
          <thead className="bg-slate-800 text-slate-300">
            <tr>
              <th className="px-4 py-3 text-left">
                <button
                  onClick={() => handleSort("file_name")}
                  className="flex items-center gap-1 hover:text-white transition"
                >
                  Contract
                  {sortField === "file_name" ? (
                    sortDirection === "asc" ? <ArrowUp size={14} /> : <ArrowDown size={14} />
                  ) : (
                    <ArrowUpDown size={14} className="opacity-50" />
                  )}
                </button>
              </th>
              <th className="px-4 py-3 text-left">
                <button
                  onClick={() => handleSort("primary_class")}
                  className="flex items-center gap-1 hover:text-white transition"
                >
                  Type
                  {sortField === "primary_class" ? (
                    sortDirection === "asc" ? <ArrowUp size={14} /> : <ArrowDown size={14} />
                  ) : (
                    <ArrowUpDown size={14} className="opacity-50" />
                  )}
                </button>
              </th>
              <th className="px-4 py-3 text-left">
                <button
                  onClick={() => handleSort("confidence")}
                  className="flex items-center gap-1 hover:text-white transition"
                >
                  Confidence
                  {sortField === "confidence" ? (
                    sortDirection === "asc" ? <ArrowUp size={14} /> : <ArrowDown size={14} />
                  ) : (
                    <ArrowUpDown size={14} className="opacity-50" />
                  )}
                </button>
              </th>
              <th className="px-4 py-3 text-left">Action</th>
            </tr>
          </thead>

          <tbody>
            {paginatedContracts.length === 0 && (
              <tr>
                <td colSpan="4" className="text-center py-6 text-slate-400">
                  {contracts.length === 0 ? "No contracts found" : "No contracts match the current filters"}
                </td>
              </tr>
            )}

            {paginatedContracts.map((c) => (
              <tr
                key={c.id}
                className="border-t border-slate-800 hover:bg-slate-800/40 transition"
              >
                <td className="px-4 py-3">
                  {c.file_name || "Contract"}
                </td>

                <td className="px-4 py-3">
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                    c.primary_class && c.primary_class !== "Not Classified"
                      ? "bg-blue-900/30 text-blue-300 border border-blue-700"
                      : "bg-slate-800 text-slate-400 border border-slate-700"
                  }`}>
                    {c.primary_class || "Not Classified"}
                  </span>
                </td>

                <td className="px-4 py-3">
                  {c.confidence !== null && c.confidence !== undefined ? (
                    <div className="flex items-center gap-2">
                      <div className="w-20 bg-slate-700 rounded-full h-2">
                        <div
                          className={`h-2 rounded-full ${
                            c.confidence >= 70 ? "bg-green-500" :
                            c.confidence >= 40 ? "bg-yellow-500" :
                            "bg-red-500"
                          }`}
                          style={{ width: `${c.confidence}%` }}
                        />
                      </div>
                      <span className={`text-xs font-medium ${
                        c.confidence >= 70 ? "text-green-400" :
                        c.confidence >= 40 ? "text-yellow-400" :
                        "text-red-400"
                      }`}>
                        {c.confidence}%
                      </span>
                    </div>
                  ) : (
                    <span className="text-slate-500">-</span>
                  )}
                </td>

                <td className="px-4 py-3">
                  <button
                    onClick={() => handleClassify(c.id)}
                    disabled={loadingId === c.id}
                    className="flex items-center gap-2 px-3 py-1.5 bg-blue-600 hover:bg-blue-500 rounded-lg text-white text-xs transition disabled:opacity-50"
                  >
                    <PlayCircle size={14} />
                    {loadingId === c.id ? "Classifying..." : "Classify"}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {/* ================= PAGINATION ================= */}
        {totalPages > 1 && (
          <div className="border-t border-slate-800 px-4 py-3 flex items-center justify-between">
            <div className="text-sm text-slate-400">
              Page {currentPage} of {totalPages}
            </div>

            <div className="flex items-center gap-2">
              {/* First Page */}
              <button
                onClick={() => setCurrentPage(1)}
                disabled={currentPage === 1}
                className="p-1.5 rounded-lg border border-slate-700 hover:bg-slate-800 disabled:opacity-50 disabled:cursor-not-allowed transition"
              >
                <ChevronsLeft size={16} />
              </button>

              {/* Previous Page */}
              <button
                onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                disabled={currentPage === 1}
                className="p-1.5 rounded-lg border border-slate-700 hover:bg-slate-800 disabled:opacity-50 disabled:cursor-not-allowed transition"
              >
                <ChevronLeft size={16} />
              </button>

              {/* Page Numbers */}
              {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                let pageNum;
                if (totalPages <= 5) {
                  pageNum = i + 1;
                } else if (currentPage <= 3) {
                  pageNum = i + 1;
                } else if (currentPage >= totalPages - 2) {
                  pageNum = totalPages - 4 + i;
                } else {
                  pageNum = currentPage - 2 + i;
                }

                return (
                  <button
                    key={pageNum}
                    onClick={() => setCurrentPage(pageNum)}
                    className={`px-3 py-1.5 rounded-lg border transition ${
                      currentPage === pageNum
                        ? "bg-blue-600 border-blue-500 text-white"
                        : "border-slate-700 hover:bg-slate-800 text-slate-300"
                    }`}
                  >
                    {pageNum}
                  </button>
                );
              })}

              {/* Next Page */}
              <button
                onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                disabled={currentPage === totalPages}
                className="p-1.5 rounded-lg border border-slate-700 hover:bg-slate-800 disabled:opacity-50 disabled:cursor-not-allowed transition"
              >
                <ChevronRight size={16} />
              </button>

              {/* Last Page */}
              <button
                onClick={() => setCurrentPage(totalPages)}
                disabled={currentPage === totalPages}
                className="p-1.5 rounded-lg border border-slate-700 hover:bg-slate-800 disabled:opacity-50 disabled:cursor-not-allowed transition"
              >
                <ChevronsRight size={16} />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* ================= BERTopic Visualization ================= */}
      <div className="bg-slate-900 rounded-xl border border-slate-700 p-5">
        <h2 className="text-lg font-semibold mb-4">
          Contract Topic Clusters (BERTopic)
        </h2>

        {clusterError && (
          <p className="text-slate-400 text-sm">
            Not enough classified contracts to generate clustering.
          </p>
        )}

        {loadingClusters && (
          <p className="text-slate-400 text-sm">
            Generating clusters…
          </p>
        )}

        {!loadingClusters && clusterHtml && (
          <iframe
            title="BERTopic Clusters"
            srcDoc={clusterHtml}
            className="w-full rounded-lg border"
            style={{
              height: "600px",
              background: "white",
            }}
          />
        )}
      </div>
    </div>
  );
};

export default ContractClassify;
