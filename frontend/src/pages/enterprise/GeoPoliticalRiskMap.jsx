import { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  ArrowLeft, Globe, AlertTriangle, Shield, RefreshCw,
  Users, TrendingUp, TrendingDown, AlertCircle, Activity,
  Wifi, Clock
} from 'lucide-react';
import { MapContainer, TileLayer, CircleMarker, Popup, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import ExposureCard from '../../components/enterprise/metrics/ExposureCard';
import ContractSelector from '../../components/enterprise/ContractSelector';
import enterpriseRiskService from '../../services/enterpriseRiskService';

// ── Risk helpers ──────────────────────────────────────────────────────────────
const riskColor  = (s) => s >= 0.7 ? '#ef4444' : s >= 0.4 ? '#f59e0b' : '#10b981';
const riskLabel  = (s) => s >= 0.7 ? 'HIGH'    : s >= 0.4 ? 'MEDIUM'  : 'LOW';
const riskBg     = (s) =>
  s >= 0.7 ? 'bg-red-500/20 text-red-400 border-red-500/30'
  : s >= 0.4 ? 'bg-amber-500/20 text-amber-400 border-amber-500/30'
  : 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30';

const fmtPop = (n) => {
  if (!n) return '—';
  if (n >= 1e9) return `${(n / 1e9).toFixed(2)}B`;
  if (n >= 1e6) return `${(n / 1e6).toFixed(1)}M`;
  return `${(n / 1e3).toFixed(0)}K`;
};

// Pulse animation via Leaflet DivIcon — injected once
let _pulseStyleInjected = false;
function injectPulseStyle() {
  if (_pulseStyleInjected) return;
  _pulseStyleInjected = true;
  const style = document.createElement('style');
  style.textContent = `
    @keyframes geoRipple {
      0%   { transform: scale(1);   opacity: 0.8; }
      100% { transform: scale(2.8); opacity: 0;   }
    }
    .geo-pulse-ring {
      border-radius: 50%;
      animation: geoRipple 1.8s ease-out infinite;
    }
  `;
  document.head.appendChild(style);
}

// ── Map auto-resize helper ────────────────────────────────────────────────────
function MapResizer() {
  const map = useMap();
  useEffect(() => { setTimeout(() => map.invalidateSize(), 100); }, [map]);
  return null;
}

// ── Pulsing circle marker ─────────────────────────────────────────────────────
import L from 'leaflet';
function PulsingMarker({ country, onClick }) {
  const color = riskColor(country.risk_score);
  const radius = Math.max(12, Math.min(48, 12 + (country.supplier_count || 0) * 4 + (country.exposure / 5e7)));
  const isHigh = country.risk_score >= 0.7;

  const icon = L.divIcon({
    className: '',
    html: `
      <div style="position:relative;width:${radius*2}px;height:${radius*2}px;">
        ${isHigh ? `<div class="geo-pulse-ring" style="
          position:absolute;top:0;left:0;width:100%;height:100%;
          background:${color};opacity:0.35;
        "></div>` : ''}
        <div style="
          position:absolute;
          top:50%;left:50%;
          transform:translate(-50%,-50%);
          width:${radius * 1.2}px;height:${radius * 1.2}px;
          border-radius:50%;
          background:${color};
          opacity:0.85;
          border:2px solid ${isHigh ? '#fff' : color};
          box-shadow:0 0 ${isHigh ? 18 : 8}px ${color}99;
          cursor:pointer;
        "></div>
      </div>
    `,
    iconSize: [radius * 2, radius * 2],
    iconAnchor: [radius, radius],
  });

  return (
    <CircleMarker
      center={[country.lat, country.lng]}
      radius={0}
      pathOptions={{ opacity: 0, fillOpacity: 0 }}
      eventHandlers={{ click: () => onClick(country) }}
    >
      {/* invisible circle just for Leaflet event binding; visual is the DivIcon overlay */}
    </CircleMarker>
  );
}

// ── Overlay markers using DivIcon ─────────────────────────────────────────────
import { Marker } from 'react-leaflet';
function CountryMarker({ country, onClick }) {
  injectPulseStyle();
  const color = riskColor(country.risk_score);
  const baseR = Math.max(10, Math.min(44, 10 + (country.supplier_count || 0) * 3 + (country.exposure / 6e7)));
  const isHigh = country.risk_score >= 0.7;
  const isMed  = country.risk_score >= 0.4;

  const icon = L.divIcon({
    className: '',
    html: `
      <div style="position:relative;width:${baseR*2}px;height:${baseR*2}px;">
        ${isHigh ? `
          <div class="geo-pulse-ring" style="
            position:absolute;top:0;left:0;
            width:${baseR*2}px;height:${baseR*2}px;
            background:${color};opacity:0.3;
          "></div>` : ''}
        <div style="
          position:absolute;
          top:50%;left:50%;
          transform:translate(-50%,-50%);
          width:${baseR*1.4}px;height:${baseR*1.4}px;
          border-radius:50%;
          background:${color};
          opacity:0.88;
          border:${isHigh ? 3 : 2}px solid rgba(255,255,255,${isHigh ? 0.8 : 0.3});
          box-shadow:0 0 ${isHigh ? 20 : isMed ? 10 : 6}px ${color};
          cursor:pointer;
        "></div>
        ${country.has_sanctions ? `
          <div style="
            position:absolute;top:-4px;right:-4px;
            width:14px;height:14px;border-radius:50%;
            background:#ef4444;border:1.5px solid #fff;
            display:flex;align-items:center;justify-content:center;
            font-size:8px;color:#fff;font-weight:900;
          ">!</div>` : ''}
      </div>
    `,
    iconSize: [baseR * 2, baseR * 2],
    iconAnchor: [baseR, baseR],
    popupAnchor: [0, -baseR],
  });

  return (
    <Marker
      position={[country.lat, country.lng]}
      icon={icon}
      eventHandlers={{ click: () => onClick(country) }}
    />
  );
}

// ── Main component ────────────────────────────────────────────────────────────
export default function GeoPoliticalRiskMap() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const contractId = searchParams.get('contractId') || '';

  const [loading,     setLoading]     = useState(true);
  const [error,       setError]       = useState('');
  const [riskData,    setRiskData]    = useState(null);
  const [selected,    setSelected]    = useState(null);
  const [lastFetched, setLastFetched] = useState(null);
  const [refreshing,  setRefreshing]  = useState(false);
  const refreshRef = useRef(null);

  const handleContractSelect = (id) => {
    if (id) setSearchParams({ contractId: id });
    else    setSearchParams({});
  };

  const loadData = useCallback(async (silent = false) => {
    try {
      if (!silent) setLoading(true);
      else setRefreshing(true);
      setError('');

      const apiData = await enterpriseRiskService.getGeoPoliticalRisk(contractId);

      const countries = (apiData.countries || []).map(c => ({
        name:             c.country || c.name,
        lat:              c.lat,
        lng:              c.lng,
        risk_score:       c.risk_score ?? 0.5,
        risk_severity:    c.risk_severity || 'MEDIUM',
        instability_index: c.risk_score ?? 0.5,  // risk_score is already inverted (1-stability) from backend
        has_sanctions:    c.has_sanctions || false,
        sanction_details: c.sanction_details || '',
        supplier_count:   c.supplier_count || 0,
        exposure:         c.exposure || 0,
        gdp_growth:       c.gdp_growth ?? null,
        inflation:        c.inflation ?? null,
        currency_stability: c.currency_stability ?? null,
        // live fields
        population:       c.population || 0,
        capital:          c.capital || '',
        currency:         c.currency || '',
        flag:             c.flag || '',
        cca2:             c.cca2 || '',
        region:           c.region || c.subregion || '',
      }));

      setRiskData({
        countries,
        total_exposure:     apiData.total_exposure || 0,
        high_risk_countries: apiData.high_risk_countries ?? countries.filter(c => c.risk_score >= 0.7).length,
        sanctions_count:    apiData.sanctioned_countries ?? countries.filter(c => c.has_sanctions).length,
        avg_risk:           apiData.avg_risk_score ?? (countries.reduce((s, c) => s + c.risk_score, 0) / Math.max(countries.length, 1)),
        live:               apiData.live ?? false,
        fetched_at:         apiData.fetched_at || Math.floor(Date.now() / 1000),
      });
      setLastFetched(new Date());
    } catch (err) {
      setError(err.message || 'Failed to load geo-political risk data');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [contractId]);

  useEffect(() => { loadData(); }, [loadData]);

  // Auto-refresh every 5 minutes
  useEffect(() => {
    refreshRef.current = setInterval(() => loadData(true), 5 * 60 * 1000);
    return () => clearInterval(refreshRef.current);
  }, [loadData]);

  if (loading) return (
    <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-slate-900 via-[#0a1628] to-slate-900">
      <div className="text-center">
        <div className="relative w-20 h-20 mx-auto mb-6">
          <div className="absolute inset-0 rounded-full border-4 border-emerald-500/20 animate-ping" />
          <div className="absolute inset-2 rounded-full border-4 border-cyan-400/30 animate-pulse" />
          <Globe className="w-8 h-8 text-emerald-400 absolute inset-0 m-auto" />
        </div>
        <p className="text-white font-bold text-xl mb-1">Loading Geo-Political Intelligence</p>
        <p className="text-slate-400 text-sm">Fetching live country risk data…</p>
      </div>
    </div>
  );

  if (error) return (
    <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      <div className="text-center max-w-md">
        <AlertTriangle className="w-16 h-16 text-red-400 mx-auto mb-4" />
        <h2 className="text-2xl font-bold text-white mb-2">Error Loading Map</h2>
        <p className="text-slate-400 mb-6">{error}</p>
        <button onClick={() => loadData()} className="px-6 py-3 bg-emerald-500 hover:bg-emerald-600 text-white rounded-xl font-semibold transition-all">
          Retry
        </button>
      </div>
    </div>
  );

  const { countries, high_risk_countries, sanctions_count, avg_risk, live } = riskData;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-[#0a1628] to-slate-900 p-6">

      {/* Header */}
      <div className="mb-5 flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/enterprise/risk-dashboard')}
            className="p-3 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 hover:border-emerald-500/50 transition-all"
          >
            <ArrowLeft className="w-5 h-5 text-slate-400" />
          </button>
          <div className="flex items-center gap-3">
            <div className="p-3 rounded-xl bg-gradient-to-br from-emerald-500/20 to-cyan-500/20 border border-emerald-500/30 shadow-[0_0_20px_rgba(16,185,129,0.3)]">
              <Globe className="w-8 h-8 text-emerald-400" />
            </div>
            <div>
              <div className="flex items-center gap-3">
                <h1 className="text-3xl font-black text-transparent bg-clip-text bg-gradient-to-r from-white via-emerald-200 to-cyan-300">
                  Geo-Political Risk Heatmap
                </h1>
                {live && (
                  <span className="flex items-center gap-1.5 px-2.5 py-1 bg-emerald-500/15 border border-emerald-500/30 rounded-full text-xs font-bold text-emerald-400">
                    <Wifi className="w-3 h-3" /> LIVE
                  </span>
                )}
              </div>
              <div className="flex items-center gap-3 mt-0.5">
                <p className="text-slate-400 text-sm">Global Supplier & Country Risk Exposure · {countries.length} countries</p>
                {lastFetched && (
                  <span className="flex items-center gap-1 text-xs text-slate-500">
                    <Clock className="w-3 h-3" />
                    Updated {lastFetched.toLocaleTimeString()}
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => loadData(true)}
            disabled={refreshing}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-800 border border-slate-700 hover:border-emerald-500/50 text-slate-300 hover:text-white text-sm font-medium transition-all disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin text-emerald-400' : ''}`} />
            Refresh
          </button>
          <ContractSelector selectedContractId={contractId} onSelect={handleContractSelect} accentColor="emerald" />
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-5">
        <ExposureCard
          title="Avg Risk Score"
          value={`${(avg_risk * 100).toFixed(0)}%`}
          subtitle="Weighted average"
          icon={Activity}
          color="emerald"
        />
        <ExposureCard
          title="High Risk Countries"
          value={high_risk_countries}
          subtitle="Risk score ≥ 70%"
          icon={AlertTriangle}
          color="red"
        />
        <ExposureCard
          title="Active Sanctions"
          value={sanctions_count}
          subtitle="Trade restrictions"
          icon={Shield}
          color="amber"
        />
        <ExposureCard
          title="Countries Tracked"
          value={countries.length}
          subtitle="Live intel feed"
          icon={Globe}
          color="cyan"
        />
      </div>

      {/* Map + Side Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">

        {/* Map */}
        <div className="lg:col-span-2">
          <div className="relative bg-gradient-to-br from-slate-900/80 to-[#0a1628]/80 backdrop-blur-xl border border-emerald-500/20 rounded-2xl overflow-hidden shadow-[0_0_50px_rgba(16,185,129,0.1)]">
            {/* Terminal bar */}
            <div className="flex items-center justify-between px-5 py-3 border-b border-slate-700/50">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-red-500" />
                <div className="w-3 h-3 rounded-full bg-amber-500" />
                <div className="w-3 h-3 rounded-full bg-emerald-500" />
                <span className="ml-3 text-xs text-slate-500 font-mono">geo-political-risk-map · live feed</span>
              </div>
              <div className="flex items-center gap-4">
                {[
                  { label: 'Low Risk',    color: '#10b981' },
                  { label: 'Medium Risk', color: '#f59e0b' },
                  { label: 'High Risk',   color: '#ef4444' },
                ].map(l => (
                  <div key={l.label} className="hidden sm:flex items-center gap-1.5">
                    <div className="w-3 h-3 rounded-full" style={{ backgroundColor: l.color }} />
                    <span className="text-[10px] text-slate-400">{l.label}</span>
                  </div>
                ))}
                <div className="flex items-center gap-1.5 ml-2">
                  <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                  <span className="text-xs text-emerald-400 font-semibold">LIVE</span>
                </div>
              </div>
            </div>

            {/* Leaflet map with dark CartoDB tiles */}
            <div style={{ height: '520px' }}>
              <MapContainer
                center={[20, 10]}
                zoom={2}
                style={{ height: '100%', width: '100%', background: '#0a1628' }}
                scrollWheelZoom
                zoomControl
              >
                <MapResizer />
                <TileLayer
                  url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
                  attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>'
                  subdomains="abcd"
                  maxZoom={19}
                />
                {countries.map((country, i) => (
                  <CountryMarker
                    key={`${country.name}-${i}`}
                    country={country}
                    onClick={setSelected}
                  />
                ))}
              </MapContainer>
            </div>

            {/* Map footer */}
            <div className="px-5 py-2.5 border-t border-slate-700/50 flex items-center justify-between text-xs text-slate-500">
              <span>Node size ∝ supplier count + exposure · Pulsing = high risk · Red badge = sanctioned</span>
              <span className="flex items-center gap-1 text-emerald-500/70">
                <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                RestCountries API
              </span>
            </div>
          </div>
        </div>

        {/* Right panel: selected country detail OR country list */}
        <div className="lg:col-span-1 space-y-4">

          {/* Selected country card */}
          {selected ? (
            <div className="bg-gradient-to-br from-slate-800/80 to-slate-900/80 backdrop-blur-xl border border-emerald-500/30 rounded-2xl p-5 shadow-[0_0_30px_rgba(16,185,129,0.15)]">
              {/* Header */}
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  {selected.flag && (
                    <img src={selected.flag} alt={selected.name} className="w-10 h-7 rounded object-cover border border-slate-600" />
                  )}
                  <div>
                    <h3 className="text-lg font-black text-white leading-tight">{selected.name}</h3>
                    <p className="text-xs text-slate-400">{selected.region}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`px-2.5 py-1 rounded-lg text-xs font-black border ${riskBg(selected.risk_score)}`}>
                    {riskLabel(selected.risk_score)}
                  </span>
                  <button onClick={() => setSelected(null)} className="text-slate-500 hover:text-white text-lg leading-none">✕</button>
                </div>
              </div>

              {/* Risk bar */}
              <div className="mb-4">
                <div className="flex justify-between mb-1.5">
                  <span className="text-xs text-slate-400">Risk Score</span>
                  <span className="text-xs font-bold" style={{ color: riskColor(selected.risk_score) }}>
                    {(selected.risk_score * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="h-2.5 bg-slate-700 rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all duration-700"
                    style={{ width: `${selected.risk_score * 100}%`, backgroundColor: riskColor(selected.risk_score), boxShadow: `0 0 8px ${riskColor(selected.risk_score)}88` }}
                  />
                </div>
              </div>

              {/* Stats grid */}
              <div className="grid grid-cols-2 gap-2 mb-4">
                {[
                  { label: 'Capital',     val: selected.capital || '—',                   color: 'text-cyan-400' },
                  { label: 'Population',  val: fmtPop(selected.population),                color: 'text-violet-400' },
                  { label: 'Suppliers',   val: selected.supplier_count || 0,               color: 'text-emerald-400' },
                  { label: 'Exposure',    val: `₹${(selected.exposure / 1e6).toFixed(1)}M`, color: 'text-amber-400' },
                  { label: 'GDP Growth',  val: selected.gdp_growth != null ? `${selected.gdp_growth > 0 ? '+' : ''}${selected.gdp_growth}%` : '—', color: selected.gdp_growth > 0 ? 'text-emerald-400' : 'text-red-400' },
                  { label: 'Inflation',   val: selected.inflation != null ? `${selected.inflation}%` : '—', color: selected.inflation > 5 ? 'text-red-400' : 'text-amber-400' },
                  { label: 'Instability', val: `${(selected.instability_index * 100).toFixed(0)}%`, color: 'text-orange-400' },
                  { label: 'Currency',    val: selected.currency ? selected.currency.split('(')[0].trim().substring(0, 18) : '—', color: 'text-slate-300' },
                ].map(({ label, val, color }) => (
                  <div key={label} className="bg-slate-900/60 rounded-xl p-2.5 border border-slate-700/50">
                    <p className="text-[10px] text-slate-500 mb-0.5">{label}</p>
                    <p className={`text-sm font-bold ${color} truncate`}>{val}</p>
                  </div>
                ))}
              </div>

              {/* Sanctions */}
              {selected.has_sanctions && (
                <div className="p-3 bg-red-500/10 rounded-xl border border-red-500/30 mb-3">
                  <div className="flex items-center gap-2 mb-1">
                    <AlertCircle className="w-4 h-4 text-red-400 flex-shrink-0" />
                    <span className="text-sm font-bold text-red-400">Active Sanctions</span>
                  </div>
                  <p className="text-xs text-slate-400">{selected.sanction_details || 'Trade and financial restrictions in effect.'}</p>
                </div>
              )}
            </div>
          ) : (
            <div className="bg-gradient-to-br from-slate-800/60 to-slate-900/60 backdrop-blur-xl border border-slate-700/50 rounded-2xl p-4">
              <div className="flex items-center gap-2 text-slate-400">
                <Globe className="w-5 h-5" />
                <p className="text-sm">Click a country marker on the map to see live details</p>
              </div>
            </div>
          )}

          {/* Country Risk Breakdown list */}
          <div className="bg-gradient-to-br from-slate-800/60 to-slate-900/60 backdrop-blur-xl border border-violet-500/20 rounded-2xl p-5 shadow-[0_0_20px_rgba(139,92,246,0.1)]">
            <h3 className="text-base font-bold text-white mb-4 flex items-center gap-2">
              <Activity className="w-4 h-4 text-violet-400" />
              Country Risk Breakdown
            </h3>
            <div className="space-y-2.5 max-h-[480px] overflow-y-auto pr-1">
              {[...countries].sort((a, b) => b.risk_score - a.risk_score).map((country, i) => (
                <button
                  key={i}
                  onClick={() => setSelected(country)}
                  className={`w-full text-left p-3.5 rounded-xl border transition-all hover:border-emerald-500/40 ${
                    selected?.name === country.name
                      ? 'bg-emerald-500/10 border-emerald-500/30'
                      : 'bg-slate-900/40 border-slate-700/50'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2.5">
                      {country.flag
                        ? <img src={country.flag} alt="" className="w-7 h-5 rounded object-cover border border-slate-600 flex-shrink-0" />
                        : <div className="w-7 h-5 rounded bg-slate-700 flex-shrink-0" />
                      }
                      <div>
                        <p className="text-sm font-bold text-white leading-tight flex items-center gap-1.5">
                          {country.name}
                          {country.has_sanctions && (
                            <span className="px-1.5 py-0.5 text-[9px] bg-red-500/20 text-red-400 border border-red-500/30 rounded font-black">SANC</span>
                          )}
                        </p>
                        <p className="text-[10px] text-slate-500">{country.supplier_count} supplier{country.supplier_count !== 1 ? 's' : ''}</p>
                      </div>
                    </div>
                    <span className={`px-2 py-0.5 rounded text-[11px] font-black border ${riskBg(country.risk_score)}`}>
                      {(country.risk_score * 100).toFixed(0)}%
                    </span>
                  </div>
                  <div className="grid grid-cols-2 gap-x-3 gap-y-0.5 text-[10px] mb-2">
                    <span className="text-slate-500">Instability: <span className="text-slate-300">{(country.instability_index * 100).toFixed(0)}%</span></span>
                    <span className="text-slate-500">Exposure: <span className="text-slate-300">₹{(country.exposure / 1e6).toFixed(1)}M</span></span>
                    {country.gdp_growth != null && (
                      <span className="text-slate-500">GDP: <span className={country.gdp_growth >= 0 ? 'text-emerald-400' : 'text-red-400'}>{country.gdp_growth > 0 ? '+' : ''}{country.gdp_growth}%</span></span>
                    )}
                    {country.inflation != null && (
                      <span className="text-slate-500">Inflation: <span className="text-amber-400">{country.inflation}%</span></span>
                    )}
                  </div>
                  {/* Risk bar */}
                  <div className="h-1.5 bg-slate-700 rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all duration-700"
                      style={{ width: `${country.risk_score * 100}%`, backgroundColor: riskColor(country.risk_score) }}
                    />
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
