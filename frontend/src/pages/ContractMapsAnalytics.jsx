/**
 * Contract Maps Analytics Page
 * Gartner-style intelligent clustering visualizations
 * Features 5 strategic maps with drill-down capabilities
 */
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import useAuthStore from '../store/authStore';
import MagicQuadrant from '../components/MagicQuadrant';
import ClauseDrilldownPanel from '../components/ClauseDrilldownPanel';
import TimeSlider from '../components/TimeSlider';
import { TrendingUp, DollarSign, Globe, Shield, Target, Info } from 'lucide-react';

const ContractMapsAnalytics = () => {
  const { user } = useAuthStore();
  const [activeMap, setActiveMap] = useState('strategic');
  const [mapData, setMapData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedContract, setSelectedContract] = useState(null);
  const [version, setVersion] = useState(1);
  const [versions, setVersions] = useState({ min: 1, max: 1 });
  const [renderKey, setRenderKey] = useState(0);
  const [showVersionChange, setShowVersionChange] = useState(false);

  // Map configurations
  const maps = [
    {
      id: 'strategic',
      name: 'Strategic Quadrant',
      icon: Target,
      endpoint: '/api/maps/strategic/',
      xLabel: 'Financial Exposure (Low → High)',
      yLabel: 'Legal & IP Risk (Low → High)',
      description: 'CXO portfolio health view - combines financial exposure with legal/IP risk'
    },
    {
      id: 'risk-value',
      name: 'Risk vs Value',
      icon: TrendingUp,
      endpoint: '/api/maps/risk-value/',
      xLabel: 'Contract Value (Low → High)',
      yLabel: 'Overall Risk Score (Low → High)',
      description: 'Identifies big money, big danger scenarios'
    },
    {
      id: 'risk-liability',
      name: 'Risk vs Liability',
      icon: DollarSign,
      endpoint: '/api/maps/risk-liability/',
      xLabel: 'Risk Score (Low → High)',
      yLabel: 'Liability Exposure % (Low → High)',
      description: 'Is risk backed by real financial pain?'
    },
    {
      id: 'geo-value',
      name: 'Geography vs Value',
      icon: Globe,
      endpoint: '/api/maps/geo-value/',
      xLabel: 'Geography Risk (Low → High)',
      yLabel: 'Contract Value (Low → High)',
      description: 'Exposure in dangerous regions - board-level favorite'
    },
    {
      id: 'ip-liability',
      name: 'IP vs Liability',
      icon: Shield,
      endpoint: '/api/maps/ip-liability/',
      xLabel: 'IP Risk (Low → High)',
      yLabel: 'Liability Exposure (Low → High)',
      description: 'Could IP issues bankrupt us?'
    }
  ];

  const currentMap = maps.find(m => m.id === activeMap);

  useEffect(() => {
    fetchVersions();
  }, []);

  useEffect(() => {
    if (user?.id) {
      setShowVersionChange(true);
      fetchMapData();
      setTimeout(() => setShowVersionChange(false), 2000);
    }
  }, [activeMap, user, version]);

  const fetchVersions = async () => {
    try {
      const token = localStorage.getItem('token');
      const userId = user?.id || localStorage.getItem('userId');

      const response = await axios.get(
        `${import.meta.env.VITE_API_URL || (import.meta.env.VITE_API_URL||(import.meta.env.VITE_API_URL||'http://localhost:8002'))}/api/maps/versions/?user_id=${userId}`,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      setVersions({
        min: response.data.min || 1,
        max: response.data.max || 1
      });
    } catch {}
  };

  const fetchMapData = async () => {
    setLoading(true);
    setMapData([]); // Clear data immediately to force unmount
    try {
      const token = localStorage.getItem('token');
      const userId = user?.id || localStorage.getItem('userId');

      const url = `${import.meta.env.VITE_API_URL || (import.meta.env.VITE_API_URL||(import.meta.env.VITE_API_URL||'http://localhost:8002'))}${currentMap.endpoint}?user_id=${userId}&version=${version}`;

      const response = await axios.get(url, {
        headers: { Authorization: `Bearer ${token}` }
      });

      setMapData(response.data);
      setRenderKey(prev => prev + 1);
    } catch {
      setMapData([]);
    } finally {
      setLoading(false);
    }
  };

  const handleDotClick = (data) => {
    setSelectedContract(data); // Store entire data object (has contract_id, label, business_unit)
  };

  return (
    <div className="min-h-screen">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-white mb-2">
            Contract Portfolio Intelligence
          </h1>
          <p className="text-gray-400">
            Gartner-style analytics with deterministic, auditable risk scoring
          </p>
        </div>

        {/* Map Selector */}
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-6">
          {maps.map((map) => {
            const Icon = map.icon;
            return (
              <button
                key={map.id}
                onClick={() => setActiveMap(map.id)}
                className={`p-4 rounded-lg border-2 transition-all ${
                  activeMap === map.id
                    ? 'border-blue-500 bg-blue-900/30 shadow-lg shadow-blue-500/20'
                    : 'border-gray-700 bg-gray-800/50 hover:border-blue-500/50 hover:bg-gray-800'
                }`}
              >
                <Icon
                  className={`w-6 h-6 mx-auto mb-2 ${
                    activeMap === map.id ? 'text-blue-400' : 'text-gray-400'
                  }`}
                />
                <p
                  className={`text-sm font-semibold text-center ${
                    activeMap === map.id ? 'text-blue-300' : 'text-gray-300'
                  }`}
                >
                  {map.name}
                </p>
              </button>
            );
          })}
        </div>

        {/* Map Info */}
        <div className="bg-blue-900/20 border border-blue-500/30 rounded-lg p-4 mb-6 flex items-start gap-3">
          <Info className="w-5 h-5 text-blue-400 mt-0.5 flex-shrink-0" />
          <div>
            <p className="text-sm font-semibold text-blue-300 mb-1">
              {currentMap.name}
            </p>
            <p className="text-sm text-blue-200/80">
              {currentMap.description}
            </p>
          </div>
        </div>

        {/* Time Slider */}
        <div className="mb-6">
          <TimeSlider
            version={version}
            setVersion={setVersion}
            minVersion={versions.min}
            maxVersion={versions.max}
          />
        </div>

        {/* Map Visualization */}
        <div className={`bg-gray-800/50 backdrop-blur-sm rounded-lg shadow-xl border p-6 relative transition-all duration-500 ${
          showVersionChange ? 'border-blue-500 shadow-[0_0_30px_rgba(59,130,246,0.5)]' : 'border-gray-700'
        }`}>
          {showVersionChange && (
            <div className="absolute top-4 right-4 z-10 px-4 py-2 bg-blue-500/90 backdrop-blur-sm border border-blue-400 rounded-lg shadow-lg animate-pulse">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-white rounded-full animate-ping"></div>
                <span className="text-white font-bold text-sm">Updating positions...</span>
              </div>
            </div>
          )}

          <h2 className="text-xl font-bold text-white mb-4">
            {currentMap.name}
          </h2>

          {loading ? (
            <div className="flex items-center justify-center h-[500px]">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
            </div>
          ) : mapData.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-[500px] text-gray-400">
              <p className="text-lg mb-2">No data available</p>
              <p className="text-sm">Upload contracts and ensure business_unit and total_liability are populated</p>
              <button
                onClick={fetchMapData}
                className="mt-4 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition"
              >
                Retry
              </button>
            </div>
          ) : (
            <MagicQuadrant
              key={`chart-${activeMap}-v${version}-render${renderKey}`}
              data={mapData}
              xLabel={currentMap.xLabel}
              yLabel={currentMap.yLabel}
              onDotClick={handleDotClick}
            />
          )}
        </div>

        {/* Quadrant Legend */}
        <div className="mt-6 bg-gray-800/50 backdrop-blur-sm rounded-lg shadow-xl border border-gray-700 p-6">
          <h3 className="text-lg font-bold text-white mb-4">Quadrant Interpretation</h3>
          <div className="grid grid-cols-2 gap-4">
            <div className="p-4 bg-red-900/30 border border-red-500/30 rounded">
              <p className="font-semibold text-red-300 mb-1">High-High Quadrant ↗</p>
              <p className="text-sm text-red-200/80">Requires immediate executive attention and risk mitigation</p>
            </div>
            <div className="p-4 bg-yellow-900/30 border border-yellow-500/30 rounded">
              <p className="font-semibold text-yellow-300 mb-1">Low-High Quadrant ↖</p>
              <p className="text-sm text-yellow-200/80">Monitor closely - potential risk escalation</p>
            </div>
            <div className="p-4 bg-orange-900/30 border border-orange-500/30 rounded">
              <p className="font-semibold text-orange-300 mb-1">High-Low Quadrant ↘</p>
              <p className="text-sm text-orange-200/80">High exposure but manageable risk</p>
            </div>
            <div className="p-4 bg-green-900/30 border border-green-500/30 rounded">
              <p className="font-semibold text-green-300 mb-1">Low-Low Quadrant ↙</p>
              <p className="text-sm text-green-200/80">Optimal zone - low risk, low exposure</p>
            </div>
          </div>
        </div>

        {/* Explainability Note */}
        <div className="mt-6 bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-lg p-4">
          <p className="text-sm text-gray-300">
            <strong className="text-green-400">✅ Court-Ready Analytics:</strong> All risk scores are deterministic and traceable.
            No AI hallucination. Click any dot to see exact clause-level risk factors.
          </p>
        </div>
      </div>

      {/* Clause Drill-Down Panel */}
      {selectedContract && (
        <ClauseDrilldownPanel
          contractId={selectedContract.contract_id}
          contractName={selectedContract.label}
          businessUnit={selectedContract.business_unit}
          version={version}
          onClose={() => setSelectedContract(null)}
        />
      )}
    </div>
  );
};

export default ContractMapsAnalytics;
