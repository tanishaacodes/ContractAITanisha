import { useState, useEffect } from 'react';
import { Database, CheckCircle, XCircle, RefreshCw, GitBranch, Network } from 'lucide-react';
import axios from 'axios';
import { API_BASE_URL } from '../config/api';
import GraphVisualization from '../components/GraphVisualization';

/**
 * Neo4j Graph Status Dashboard
 * Shows connection status and allows syncing clause data
 */
const GraphStatus = () => {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [syncResult, setSyncResult] = useState(null);
  const [graphData, setGraphData] = useState(null);
  const [showGraph, setShowGraph] = useState(false);

  useEffect(() => {
    fetchStatus();
  }, []);

  const fetchStatus = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_BASE_URL}/graph/status/`);
      setStatus(response.data);
    } catch (err) {
      console.error('Error fetching graph status:', err);
      setStatus({ connected: false, message: 'Failed to connect to backend' });
    } finally {
      setLoading(false);
    }
  };

  const fetchGraphData = async () => {
    try {
      // Fetch all clause evolution data for visualization
      // For now, we'll fetch the first clause as a sample
      // In production, you'd want to fetch all or allow selecting specific clauses
      const response = await axios.get(`${API_BASE_URL}/graph/status/`);

      // Mock graph data structure for now
      // You can enhance this to fetch actual graph data from a new endpoint
      const mockData = {
        nodes: [
          { id: 1, version: 1, risk_score: 0.3, text_preview: 'Initial version' },
          { id: 2, version: 2, risk_score: 0.5, text_preview: 'Updated terms' },
          { id: 3, version: 3, risk_score: 0.2, text_preview: 'Risk mitigation added' },
        ],
        links: [
          { source: 1, target: 2 },
          { source: 2, target: 3 },
        ],
      };

      setGraphData(mockData);
      setShowGraph(true);
    } catch (err) {
      console.error('Error fetching graph data:', err);
    }
  };

  const handleSync = async () => {
    try {
      setSyncing(true);
      setSyncResult(null);

      const response = await axios.post(
        `${API_BASE_URL}/graph/sync/`,
        {},
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('token')}`
          }
        }
      );

      setSyncResult({
        success: true,
        message: response.data.message
      });

      // Refresh status after sync
      await fetchStatus();
    } catch (err) {
      console.error('Error syncing to graph:', err);
      setSyncResult({
        success: false,
        message: err.response?.data?.error || 'Failed to sync data'
      });
    } finally {
      setSyncing(false);
    }
  };

  const handleInitialize = async () => {
    try {
      setSyncing(true);
      setSyncResult(null);

      const response = await axios.post(`${API_BASE_URL}/graph/initialize/`);

      setSyncResult({
        success: true,
        message: response.data.message
      });

      await fetchStatus();
    } catch (err) {
      console.error('Error initializing graph:', err);
      setSyncResult({
        success: false,
        message: err.response?.data?.error || 'Failed to initialize schema'
      });
    } finally {
      setSyncing(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-[#0B1437]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0B1437] p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-white flex items-center gap-2">
          <Database className="w-8 h-8 text-blue-400" />
          Neo4j Clause Evolution Graph
        </h1>
        <p className="text-gray-400 mt-2">
          Track clause lineage, evolution, and real-world outcomes
        </p>
      </div>

      {/* Connection Status Card */}
      <div className="bg-[#1a2951] rounded-lg shadow-lg border border-gray-700 p-6 mb-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            {status?.connected ? (
              <CheckCircle className="w-6 h-6 text-green-500" />
            ) : (
              <XCircle className="w-6 h-6 text-red-500" />
            )}
            Connection Status
          </h2>

          <button
            onClick={fetchStatus}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors flex items-center gap-2"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
        </div>

        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-gray-400">Status:</span>
            <span className={`font-semibold ${status?.connected ? 'text-green-400' : 'text-red-400'}`}>
              {status?.connected ? 'Connected' : 'Not Connected'}
            </span>
          </div>

          {status?.uri && (
            <div className="flex items-center justify-between">
              <span className="text-gray-400">URI:</span>
              <span className="text-white font-mono text-sm">{status.uri}</span>
            </div>
          )}

          {status?.message && !status?.connected && (
            <div className="mt-4 p-4 bg-yellow-900/30 border border-yellow-700/50 rounded-lg">
              <p className="text-yellow-400 text-sm">{status.message}</p>
            </div>
          )}
        </div>
      </div>

      {/* Graph Statistics */}
      {status?.connected && status?.stats && (
        <div className="bg-[#1a2951] rounded-lg shadow-lg border border-gray-700 p-6 mb-6">
          <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
            <GitBranch className="w-6 h-6 text-blue-400" />
            Graph Statistics
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-blue-900/30 rounded-lg p-4 border border-blue-700/50">
              <p className="text-blue-400 text-sm mb-1">Clause Nodes</p>
              <p className="text-3xl font-bold text-white">{status.stats.clauses || 0}</p>
            </div>

            <div className="bg-purple-900/30 rounded-lg p-4 border border-purple-700/50">
              <p className="text-purple-400 text-sm mb-1">Version Nodes</p>
              <p className="text-3xl font-bold text-white">{status.stats.versions || 0}</p>
            </div>

            <div className="bg-green-900/30 rounded-lg p-4 border border-green-700/50">
              <p className="text-green-400 text-sm mb-1">Event Nodes</p>
              <p className="text-3xl font-bold text-white">{status.stats.events || 0}</p>
            </div>
          </div>

          {/* View Graph Button */}
          <div className="mt-4">
            <button
              onClick={fetchGraphData}
              className="px-6 py-3 bg-cyan-600 text-white rounded-md hover:bg-cyan-700 transition-colors flex items-center gap-2"
            >
              <Network className="w-5 h-5" />
              {showGraph ? 'Refresh Graph' : 'View Interactive Graph'}
            </button>
          </div>
        </div>
      )}

      {/* Graph Visualization */}
      {showGraph && graphData && (
        <div className="bg-[#1a2951] rounded-lg shadow-lg border border-gray-700 p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <Network className="w-6 h-6 text-cyan-400" />
              Graph Visualization
            </h2>
            <button
              onClick={() => setShowGraph(false)}
              className="text-gray-400 hover:text-white transition-colors"
            >
              ✕ Close
            </button>
          </div>

          <div className="h-[600px]">
            <GraphVisualization
              data={graphData}
              onNodeClick={(node) => console.log('Clicked node:', node)}
            />
          </div>
        </div>
      )}

      {/* Actions */}
      {!status?.connected && status?.config_needed && (
        <div className="bg-[#1a2951] rounded-lg shadow-lg border border-gray-700 p-6 mb-6">
          <h2 className="text-xl font-bold text-white mb-4">Setup Required</h2>

          <div className="space-y-4">
            <p className="text-gray-300">
              Neo4j is not configured. To enable graph features, you need to:
            </p>

            <ol className="list-decimal list-inside space-y-2 text-gray-300 ml-4">
              <li>Install Neo4j Desktop or run Neo4j via Docker</li>
              <li>Set environment variables in backend/.env:</li>
            </ol>

            <div className="bg-gray-900 rounded-lg p-4 border border-gray-700 font-mono text-sm">
              <div className="text-blue-400">NEO4J_URI={status.config_needed.NEO4J_URI}</div>
              <div className="text-blue-400">NEO4J_USER={status.config_needed.NEO4J_USER}</div>
              <div className="text-blue-400">NEO4J_PASSWORD={status.config_needed.NEO4J_PASSWORD}</div>
            </div>

            <button
              onClick={handleInitialize}
              disabled={syncing}
              className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors disabled:bg-gray-600"
            >
              {syncing ? 'Initializing...' : 'Initialize Schema (After Setup)'}
            </button>
          </div>
        </div>
      )}

      {/* Sync Data */}
      {status?.connected && (
        <div className="bg-[#1a2951] rounded-lg shadow-lg border border-gray-700 p-6">
          <h2 className="text-xl font-bold text-white mb-4">Sync Clause Data</h2>

          <p className="text-gray-300 mb-4">
            Sync your clause data from MySQL to Neo4j for evolution tracking and analysis.
          </p>

          <button
            onClick={handleSync}
            disabled={syncing}
            className="px-6 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors disabled:bg-gray-600 flex items-center gap-2"
          >
            {syncing ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                Syncing...
              </>
            ) : (
              <>
                <Database className="w-4 h-4" />
                Sync All Clauses
              </>
            )}
          </button>

          {syncResult && (
            <div className={`mt-4 p-4 rounded-lg ${
              syncResult.success
                ? 'bg-green-900/30 border border-green-700/50'
                : 'bg-red-900/30 border border-red-700/50'
            }`}>
              <p className={syncResult.success ? 'text-green-400' : 'text-red-400'}>
                {syncResult.message}
              </p>
            </div>
          )}
        </div>
      )}

      {/* Documentation Link */}
      <div className="mt-6 bg-[#1a2951] rounded-lg shadow-lg border border-gray-700 p-4">
        <p className="text-gray-400 text-sm">
          📖 For detailed setup instructions, see:{' '}
          <code className="text-blue-400 bg-gray-900 px-2 py-1 rounded">
            backend/NEO4J_SETUP.md
          </code>
        </p>
      </div>
    </div>
  );
};

export default GraphStatus;
