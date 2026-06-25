import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Network, ArrowLeft, Sparkles, Info } from 'lucide-react';
import ContractNetworkGraph from '../components/graph/ContractNetworkGraph';
import api from '../utils/api';

const ContractGraphExplorer = () => {
  const navigate = useNavigate();
  const [contracts, setContracts] = useState([]);
  const [selectedContractId, setSelectedContractId] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadContracts();
  }, []);

  const loadContracts = async () => {
    try {
      const response = await api.get('/contracts/list');
      const data = response.data?.contracts || [];
      setContracts(data);
      if (data.length > 0) {
        setSelectedContractId(data[0].id);
      }
    } catch (error) {
      console.error('Error loading contracts:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-900 via-purple-900 to-indigo-900 border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-6 py-8">
          <button
            onClick={() => navigate('/dashboard')}
            className="flex items-center text-gray-300 hover:text-white mb-4 transition-colors"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Dashboard
          </button>

          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <div className="p-3 bg-blue-500/20 rounded-lg mr-4">
                <Network className="w-8 h-8 text-blue-400" />
              </div>
              <div>
                <h1 className="text-3xl font-bold text-white mb-2">
                  Contract Graph Explorer
                </h1>
                <p className="text-gray-300">
                  Neo4j-powered interactive knowledge graph visualization
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2 px-4 py-2 bg-blue-500/10 border border-blue-500/30 rounded-lg">
              <Sparkles className="w-5 h-5 text-blue-400" />
              <span className="text-sm font-semibold text-blue-300">AI-Powered</span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Contract Selector */}
        {!loading && contracts.length > 0 && (
          <div className="mb-6 bg-gray-800 rounded-lg p-4 border border-gray-700">
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Select Contract
            </label>
            <select
              value={selectedContractId}
              onChange={(e) => setSelectedContractId(e.target.value)}
              className="w-full md:w-1/2 px-4 py-2 bg-gray-900 border border-gray-600 rounded-lg text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {contracts.map((contract) => (
                <option key={contract.id} value={contract.id}>
                  {contract.original_filename || contract.originalFilename || contract.name || contract.title || `Contract ${contract.id.substring(0, 8)}`}
                </option>
              ))}
            </select>
          </div>
        )}

        {/* Info Panel */}
        <div className="mb-6 bg-blue-900/20 border border-blue-700/50 rounded-lg p-4">
          <div className="flex items-start">
            <Info className="w-5 h-5 text-blue-400 mr-3 mt-0.5 flex-shrink-0" />
            <div className="text-sm text-gray-300">
              <p className="font-semibold text-blue-300 mb-1">How to use:</p>
              <ul className="list-disc list-inside space-y-1">
                <li>Click and drag nodes to explore relationships</li>
                <li>Use mouse wheel to zoom in/out</li>
                <li>Click on a node to view detailed information</li>
                <li>Use the search bar to find specific entities</li>
                <li>Filter by entity type to focus on specific aspects</li>
              </ul>
            </div>
          </div>
        </div>

        {/* Graph Visualization */}
        {selectedContractId && (
          <ContractNetworkGraph contractId={selectedContractId} />
        )}

        {/* Empty State */}
        {!loading && contracts.length === 0 && (
          <div className="bg-gray-800 rounded-lg p-12 text-center border border-gray-700">
            <Network className="w-16 h-16 text-gray-600 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-gray-300 mb-2">
              No Contracts Found
            </h3>
            <p className="text-gray-400 mb-6">
              Upload a contract to start exploring the knowledge graph
            </p>
            <button
              onClick={() => navigate('/contracts/upload')}
              className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-semibold transition-colors"
            >
              Upload Contract
            </button>
          </div>
        )}

        {/* Feature Highlights */}
        <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <div className="w-12 h-12 bg-green-500/20 rounded-lg flex items-center justify-center mb-4">
              <Network className="w-6 h-6 text-green-400" />
            </div>
            <h3 className="text-lg font-semibold text-gray-100 mb-2">
              Graph Database
            </h3>
            <p className="text-gray-400 text-sm">
              Powered by Neo4j for fast relationship traversal and pattern matching
            </p>
          </div>

          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <div className="w-12 h-12 bg-blue-500/20 rounded-lg flex items-center justify-center mb-4">
              <Sparkles className="w-6 h-6 text-blue-400" />
            </div>
            <h3 className="text-lg font-semibold text-gray-100 mb-2">
              AI Extraction
            </h3>
            <p className="text-gray-400 text-sm">
              AI-powered entity and relationship extraction from contract text
            </p>
          </div>

          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <div className="w-12 h-12 bg-purple-500/20 rounded-lg flex items-center justify-center mb-4">
              <Network className="w-6 h-6 text-purple-400" />
            </div>
            <h3 className="text-lg font-semibold text-gray-100 mb-2">
              Interactive Viz
            </h3>
            <p className="text-gray-400 text-sm">
              React Flow with Neo4j-inspired styling for beautiful graph exploration
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ContractGraphExplorer;
