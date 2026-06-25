import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { ArrowLeft, Map, Loader2, AlertTriangle, Globe, Shield, TrendingDown } from 'lucide-react';
import { MapContainer, TileLayer, CircleMarker, Popup, Tooltip as MapTooltip } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import ExposureCard from '../../components/enterprise/metrics/ExposureCard';

export default function GeoPoliticalRiskMap() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const contractId = searchParams.get('contractId') || 'CONTRACT_X';

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [riskData, setRiskData] = useState(null);

  useEffect(() => {
    loadGeoRiskData();
  }, [contractId]);

  const loadGeoRiskData = async () => {
    try {
      setLoading(true);
      setError('');

      // Mock data - will connect to backend
      const mockData = {
        total_geo_risk_score: 0.42,
        high_risk_countries: 3,
        sanctions_count: 2,
        countries: [
          {
            name: 'India',
            lat: 20.5937,
            lng: 78.9629,
            risk_score: 0.25,
            instability_index: 0.2,
            has_sanctions: false,
            supplier_count: 5,
            exposure: 15000000
          },
          {
            name: 'China',
            lat: 35.8617,
            lng: 104.1954,
            risk_score: 0.65,
            instability_index: 0.45,
            has_sanctions: true,
            supplier_count: 3,
            exposure: 8000000
          },
          {
            name: 'Russia',
            lat: 61.5240,
            lng: 105.3188,
            risk_score: 0.85,
            instability_index: 0.75,
            has_sanctions: true,
            supplier_count: 1,
            exposure: 3000000
          },
          {
            name: 'Germany',
            lat: 51.1657,
            lng: 10.4515,
            risk_score: 0.15,
            instability_index: 0.1,
            has_sanctions: false,
            supplier_count: 4,
            exposure: 12000000
          },
          {
            name: 'USA',
            lat: 37.0902,
            lng: -95.7129,
            risk_score: 0.20,
            instability_index: 0.15,
            has_sanctions: false,
            supplier_count: 6,
            exposure: 20000000
          },
          {
            name: 'Brazil',
            lat: -14.2350,
            lng: -51.9253,
            risk_score: 0.40,
            instability_index: 0.35,
            has_sanctions: false,
            supplier_count: 2,
            exposure: 5000000
          }
        ]
      };

      setRiskData(mockData);
    } catch (err) {
      setError(err.message || 'Failed to load geo-political risk data');
      console.error('Geo risk error:', err);
    } finally {
      setLoading(false);
    }
  };

  const getRiskColor = (riskScore) => {
    if (riskScore >= 0.7) return '#ef4444'; // High risk - red
    if (riskScore >= 0.4) return '#f59e0b'; // Medium risk - amber
    return '#10b981'; // Low risk - green
  };

  const getRiskRadius = (exposure) => {
    return Math.max(10, Math.min(50, exposure / 500000));
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
        <div className="text-center">
          <Loader2 className="w-12 h-12 text-emerald-400 animate-spin mx-auto mb-4" />
          <p className="text-slate-400 text-lg">Loading Geo-Political Risk Map...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
        <div className="text-center max-w-md">
          <AlertTriangle className="w-16 h-16 text-red-400 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-white mb-2">Error Loading Map</h2>
          <p className="text-slate-400 mb-6">{error}</p>
          <button
            onClick={loadGeoRiskData}
            className="px-6 py-3 bg-emerald-500 hover:bg-emerald-600 text-white rounded-xl font-semibold transition-all"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/enterprise/risk-dashboard')}
            className="p-3 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 hover:border-emerald-500/50 transition-all"
          >
            <ArrowLeft className="w-5 h-5 text-slate-400" />
          </button>
          <div className="flex items-center gap-3">
            <div className="p-3 rounded-xl bg-gradient-to-br from-emerald-500/20 to-green-500/20 border border-emerald-500/30">
              <Globe className="w-8 h-8 text-emerald-400" />
            </div>
            <div>
              <h1 className="text-3xl font-black text-transparent bg-clip-text bg-gradient-to-r from-white via-emerald-200 to-green-300">
                Geo-Political Risk Heatmap
              </h1>
              <p className="text-slate-400 text-sm">Global Supplier & Country Risk Exposure</p>
            </div>
          </div>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
        <ExposureCard
          title="Geo-Political Risk Score"
          value={`${(riskData.total_geo_risk_score * 100).toFixed(0)}%`}
          subtitle="Weighted average"
          icon={Globe}
          color="emerald"
        />

        <ExposureCard
          title="High Risk Countries"
          value={riskData.high_risk_countries}
          subtitle="Risk score > 70%"
          icon={AlertTriangle}
          color="red"
        />

        <ExposureCard
          title="Active Sanctions"
          value={riskData.sanctions_count}
          subtitle="Trade restrictions"
          icon={Shield}
          color="amber"
        />
      </div>

      {/* Map Container */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Map */}
        <div className="lg:col-span-2">
          <div className="bg-gradient-to-br from-slate-800/60 to-slate-900/60 backdrop-blur-xl border border-emerald-500/20 rounded-2xl p-6 shadow-[0_0_30px_rgba(16,185,129,0.15)]">
            <div className="rounded-xl overflow-hidden border border-slate-700" style={{ height: '600px' }}>
              <MapContainer
                center={[20, 0]}
                zoom={2}
                style={{ height: '100%', width: '100%' }}
                scrollWheelZoom={true}
              >
                <TileLayer
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                  attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                />

                {riskData.countries.map((country, index) => (
                  <CircleMarker
                    key={index}
                    center={[country.lat, country.lng]}
                    radius={getRiskRadius(country.exposure)}
                    fillColor={getRiskColor(country.risk_score)}
                    fillOpacity={0.7}
                    color="#fff"
                    weight={2}
                  >
                    <Popup>
                      <div className="p-2">
                        <h3 className="font-bold text-lg mb-2">{country.name}</h3>
                        <div className="space-y-1 text-sm">
                          <p><strong>Risk Score:</strong> {(country.risk_score * 100).toFixed(0)}%</p>
                          <p><strong>Instability:</strong> {(country.instability_index * 100).toFixed(0)}%</p>
                          <p><strong>Suppliers:</strong> {country.supplier_count}</p>
                          <p><strong>Exposure:</strong> ₹{(country.exposure / 1000000).toFixed(1)}M</p>
                          <p><strong>Sanctions:</strong> {country.has_sanctions ? 'Yes' : 'No'}</p>
                        </div>
                      </div>
                    </Popup>
                    <MapTooltip direction="top" offset={[0, -10]} opacity={0.9}>
                      <span className="font-semibold">{country.name}</span>
                    </MapTooltip>
                  </CircleMarker>
                ))}
              </MapContainer>
            </div>

            {/* Legend */}
            <div className="mt-4 flex items-center justify-center gap-6">
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 rounded-full bg-emerald-500"></div>
                <span className="text-sm text-slate-300">Low Risk (&lt;40%)</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 rounded-full bg-amber-500"></div>
                <span className="text-sm text-slate-300">Medium Risk (40-70%)</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 rounded-full bg-red-500"></div>
                <span className="text-sm text-slate-300">High Risk (&gt;70%)</span>
              </div>
            </div>
          </div>
        </div>

        {/* Country List */}
        <div className="lg:col-span-1">
          <div className="bg-gradient-to-br from-slate-800/60 to-slate-900/60 backdrop-blur-xl border border-violet-500/20 rounded-2xl p-6 shadow-[0_0_30px_rgba(139,92,246,0.15)]">
            <h3 className="text-xl font-bold text-white mb-4">Country Risk Breakdown</h3>

            <div className="space-y-3 max-h-[540px] overflow-y-auto pr-2">
              {riskData.countries
                .sort((a, b) => b.risk_score - a.risk_score)
                .map((country, index) => (
                  <div
                    key={index}
                    className="p-4 rounded-xl bg-slate-900/50 border border-slate-700 hover:border-emerald-500/50 transition-all"
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <h4 className="font-bold text-white flex items-center gap-2">
                          {country.name}
                          {country.has_sanctions && (
                            <span className="px-2 py-0.5 text-[10px] bg-red-500/20 text-red-400 rounded-full border border-red-500/30 font-black uppercase">
                              Sanctioned
                            </span>
                          )}
                        </h4>
                        <p className="text-xs text-slate-400 mt-1">
                          {country.supplier_count} supplier{country.supplier_count !== 1 ? 's' : ''}
                        </p>
                      </div>
                      <div className={`px-3 py-1 rounded-lg font-bold text-sm ${
                        country.risk_score >= 0.7
                          ? 'bg-red-500/20 text-red-400 border border-red-500/30'
                          : country.risk_score >= 0.4
                          ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                          : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                      }`}>
                        {(country.risk_score * 100).toFixed(0)}%
                      </div>
                    </div>

                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-slate-400">Instability:</span>
                        <span className="text-white font-medium">
                          {(country.instability_index * 100).toFixed(0)}%
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">Exposure:</span>
                        <span className="text-white font-medium">
                          ₹{(country.exposure / 1000000).toFixed(1)}M
                        </span>
                      </div>
                    </div>

                    {/* Risk bar */}
                    <div className="mt-3 h-2 bg-slate-700 rounded-full overflow-hidden">
                      <div
                        className="h-full transition-all duration-1000"
                        style={{
                          width: `${country.risk_score * 100}%`,
                          backgroundColor: getRiskColor(country.risk_score)
                        }}
                      />
                    </div>
                  </div>
                ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
