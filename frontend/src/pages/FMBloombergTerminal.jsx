/**
 * Force Majeure Bloomberg Terminal
 * ===================================
 * 5-panel live dashboard:
 *   Panel 1 — Global FM Risk Map (world map with risk markers)
 *   Panel 2 — Live Event Stream (Bloomberg ticker)
 *   Panel 3 — War Intelligence (live geopolitical data)
 *   Panel 4 — Portfolio Alerts (contracts at risk)
 *   Panel 5 — FM Radar (all live events by type)
 *
 * Keyboard shortcuts: FMAP, CRISK, CLAUSE, SUPPLY, SIM
 * Auto-refreshes every 60 seconds.
 */
import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  Globe, Zap, AlertTriangle, Activity, Shield, RefreshCw,
  Sword, TrendingUp, Radio, Eye, BarChart2, Clock,
  ChevronRight, ExternalLink,
} from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  LineChart, Line, CartesianGrid,
} from 'recharts';
import {
  getLiveEvents, getRiskMapData, getEventStream,
  getWarIntelligence, getPortfolioAlerts,
} from '../services/forceMajeureService';

// ─── Helpers ──────────────────────────────────────────────────────────────────
const severityColor = { CRITICAL: '#9d1b1b', HIGH: '#F16667', MEDIUM: '#F79767', LOW: '#68BC00' };
const eventTypeIcon = {
  war: '⚔️', sanctions: '🚫', pandemic: '🦠', port_closure: '⚓',
  supply_chain_disruption: '🔗', energy_shortage: '⚡', political_coup: '🏛️',
  natural_disaster: '🌊', cyber_attack: '💻', terrorism: '💣', unknown: '❓',
};

const RiskBadge = ({ score }) => {
  const color = score > 0.7 ? '#F16667' : score > 0.4 ? '#F79767' : '#68BC00';
  const label = score > 0.7 ? 'HIGH' : score > 0.4 ? 'MED' : 'LOW';
  return (
    <span className="text-xs font-bold px-1.5 py-0.5 rounded" style={{ background: color + '33', color }}>
      {label}
    </span>
  );
};

const LiveDot = () => (
  <span className="relative flex h-2 w-2">
    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75" />
    <span className="relative inline-flex rounded-full h-2 w-2 bg-red-500" />
  </span>
);

// ─── Panel: Live Event Stream ─────────────────────────────────────────────────
const EventStreamPanel = ({ data, loading }) => (
  <div className="bg-gray-900 border border-gray-700 rounded-xl flex flex-col h-full">
    <div className="flex items-center justify-between px-3 py-2 border-b border-gray-700">
      <div className="flex items-center gap-2 text-xs font-bold text-yellow-400">
        <Radio size={11} /> LIVE EVENT STREAM
      </div>
      <LiveDot />
    </div>
    <div className="flex-1 overflow-y-auto p-2 space-y-1.5">
      {loading ? (
        <div className="text-gray-500 text-xs text-center py-4">Fetching live events…</div>
      ) : (data?.ticker || []).length === 0 ? (
        <div className="text-gray-500 text-xs text-center py-4">No live events detected</div>
      ) : (
        (data?.ticker || []).map((ev, i) => (
          <div key={i} className="flex items-start gap-2 p-1.5 rounded hover:bg-gray-800 transition">
            <span className="text-gray-500 text-xs w-10 shrink-0 font-mono">
              {ev.time?.slice(11, 16) || '--:--'}
            </span>
            <span className="text-xs">{eventTypeIcon[ev.event_type] || '📌'}</span>
            <div className="flex-1 min-w-0">
              <div className="text-gray-200 text-xs leading-tight truncate">{ev.title}</div>
              <div className="text-gray-500 text-xs">{ev.location} · {ev.source}</div>
            </div>
            <RiskBadge score={ev.risk_score} />
          </div>
        ))
      )}
    </div>
    <div className="px-3 py-1.5 border-t border-gray-700 text-gray-600 text-xs">
      {data?.total || 0} events · Updated {data?.last_updated?.slice(11, 19) || '--'}
    </div>
  </div>
);

// ─── Panel: War Intelligence ──────────────────────────────────────────────────
const WarIntelPanel = ({ data, loading }) => (
  <div className="bg-gray-900 border border-red-900 rounded-xl flex flex-col h-full">
    <div className="flex items-center justify-between px-3 py-2 border-b border-red-900">
      <div className="flex items-center gap-2 text-xs font-bold text-red-400">
        <Sword size={11} /> WAR INTELLIGENCE
      </div>
      <span className="text-xs text-red-600">
        GWI: {data?.global_war_risk_index ? `${Math.round(data.global_war_risk_index * 100)}%` : '--'}
      </span>
    </div>
    <div className="flex-1 overflow-y-auto p-2 space-y-1">
      {loading ? (
        <div className="text-gray-500 text-xs text-center py-4">Loading war intelligence…</div>
      ) : (
        <>
          {/* Top war zones */}
          <div className="text-gray-500 text-xs px-1 mb-1">TOP WAR ZONES</div>
          {(data?.top_war_zones || []).slice(0, 6).map((zone, i) => (
            <div key={i} className="flex items-center gap-2 px-1 py-0.5">
              <span className="text-gray-400 text-xs w-3">{i + 1}.</span>
              <span className="text-gray-200 text-xs flex-1">{zone.country}</span>
              <div className="w-16 bg-gray-700 rounded-full h-1.5">
                <div className="h-1.5 rounded-full bg-red-500"
                  style={{ width: `${Math.round(zone.war_risk * 100)}%` }} />
              </div>
              <span className="text-red-400 text-xs w-8 text-right">
                {Math.round(zone.war_risk * 100)}%
              </span>
            </div>
          ))}

          {/* Shipping disruptions */}
          <div className="text-gray-500 text-xs px-1 mt-2 mb-1">SHIPPING DISRUPTIONS</div>
          {(data?.active_shipping_disruptions || []).map((route, i) => (
            <div key={i} className="px-1 py-0.5">
              <div className="flex items-center justify-between">
                <span className="text-yellow-400 text-xs font-medium">{route.route}</span>
                <RiskBadge score={route.risk} />
              </div>
              <div className="text-gray-500 text-xs truncate">{route.cause}</div>
            </div>
          ))}
        </>
      )}
    </div>
    <div className="px-3 py-1.5 border-t border-red-900 text-gray-600 text-xs">
      {data?.war_events_detected || 0} war events · {data?.sanctions_count || 0} sanctions
    </div>
  </div>
);

// ─── Panel: Risk Map (text-based heatmap) ─────────────────────────────────────
const RiskMapPanel = ({ data, loading }) => {
  const regions = (data?.risk_regions || []).slice(0, 14);
  return (
    <div className="bg-gray-900 border border-gray-700 rounded-xl flex flex-col h-full">
      <div className="flex items-center justify-between px-3 py-2 border-b border-gray-700">
        <div className="flex items-center gap-2 text-xs font-bold text-blue-400">
          <Globe size={11} /> GLOBAL FM RISK MAP
        </div>
        <span className="text-xs text-gray-500">
          {data?.high_risk_regions || 0} high-risk regions
        </span>
      </div>
      <div className="flex-1 overflow-y-auto p-2">
        {loading ? (
          <div className="text-gray-500 text-xs text-center py-4">Loading map data…</div>
        ) : (
          <>
            <div className="grid grid-cols-2 gap-1 mb-2">
              {regions.map((r, i) => (
                <div key={i}
                  className="flex items-center justify-between px-2 py-1 rounded text-xs"
                  style={{ background: (r.color || '#374151') + '22', border: `1px solid ${r.color || '#374151'}44` }}
                >
                  <span className="text-gray-300 truncate max-w-20">{r.country}</span>
                  <span className="font-bold ml-1" style={{ color: r.color || '#9ca3af' }}>
                    {Math.round((r.risk_score || 0) * 100)}%
                  </span>
                </div>
              ))}
            </div>
            {/* Shipping routes */}
            <div className="text-gray-500 text-xs mb-1">CRITICAL SHIPPING ROUTES</div>
            {(data?.shipping_routes || []).map((route, i) => (
              <div key={i} className="flex items-center gap-2 px-1 py-0.5">
                <span className="text-xs">⚓</span>
                <span className="text-gray-300 text-xs flex-1 truncate">{route.name}</span>
                <span className="text-xs font-bold" style={{ color: route.color }}>
                  {Math.round(route.disruption_risk * 100)}%
                </span>
              </div>
            ))}
          </>
        )}
      </div>
    </div>
  );
};

// ─── Panel: Portfolio Alerts ───────────────────────────────────────────────────
const PortfolioAlertsPanel = ({ data, loading }) => (
  <div className="bg-gray-900 border border-yellow-900 rounded-xl flex flex-col h-full">
    <div className="flex items-center justify-between px-3 py-2 border-b border-yellow-900">
      <div className="flex items-center gap-2 text-xs font-bold text-yellow-400">
        <AlertTriangle size={11} /> PORTFOLIO ALERTS
      </div>
      <span className="text-xs text-yellow-600">
        {data?.critical_alerts || 0} CRITICAL
      </span>
    </div>
    <div className="flex-1 overflow-y-auto p-2 space-y-1.5">
      {loading ? (
        <div className="text-gray-500 text-xs text-center py-4">Scanning portfolio…</div>
      ) : (data?.portfolio_alerts || []).length === 0 ? (
        <div className="text-green-500 text-xs text-center py-4">✓ No critical alerts</div>
      ) : (
        (data?.portfolio_alerts || []).slice(0, 8).map((alert, i) => (
          <div key={i} className="p-2 rounded bg-gray-800 border border-gray-700">
            <div className="flex items-center justify-between mb-1">
              <span className="text-gray-200 text-xs truncate max-w-36">
                {alert.contract_title || alert.contract_id?.slice(0, 8) + '…'}
              </span>
              <RiskBadge score={alert.fm_trigger_probability} />
            </div>
            <div className="flex gap-1 flex-wrap">
              {(alert.triggered_by || []).slice(0, 3).map((t, j) => (
                <span key={j} className="text-xs px-1 bg-gray-700 text-gray-400 rounded">
                  {t?.replace(/_/g, ' ')}
                </span>
              ))}
            </div>
          </div>
        ))
      )}
    </div>
    <div className="px-3 py-1.5 border-t border-yellow-900 text-gray-600 text-xs">
      {data?.total_alerts || 0} alerts · {data?.live_events_analyzed || 0} events scanned
    </div>
  </div>
);

// ─── Panel: FM Radar chart ────────────────────────────────────────────────────
const FMRadarPanel = ({ data, loading }) => {
  const chartData = Object.entries(data?.by_event_type || {}).map(([k, v]) => ({
    name: k.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
    count: v,
  })).sort((a, b) => b.count - a.count);

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-xl flex flex-col h-full">
      <div className="flex items-center justify-between px-3 py-2 border-b border-gray-700">
        <div className="flex items-center gap-2 text-xs font-bold text-purple-400">
          <Activity size={11} /> FM RADAR — EVENT BREAKDOWN
        </div>
        <span className="text-xs text-gray-500">
          {data?.total || 0} events · {data?.high_risk_count || 0} high risk
        </span>
      </div>
      <div className="flex-1 p-2">
        {loading ? (
          <div className="text-gray-500 text-xs text-center py-4">Loading radar data…</div>
        ) : chartData.length === 0 ? (
          <div className="text-gray-500 text-xs text-center py-4">No events detected</div>
        ) : (
          <>
            <ResponsiveContainer width="100%" height={130}>
              <BarChart data={chartData} barSize={16}>
                <XAxis dataKey="name" tick={{ fill: '#6b7280', fontSize: 9 }} interval={0}
                  angle={-25} textAnchor="end" height={40} />
                <YAxis tick={{ fill: '#6b7280', fontSize: 9 }} />
                <Tooltip contentStyle={{ background: '#111827', border: '1px solid #374151', color: '#fff', fontSize: 11 }} />
                <Bar dataKey="count" fill="#9063CD" radius={[3, 3, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
            {/* Top events list */}
            <div className="mt-2 space-y-1">
              {(data?.events || []).slice(0, 4).map((ev, i) => (
                <div key={i} className="flex items-center gap-2 text-xs">
                  <span>{eventTypeIcon[ev.event_type] || '📌'}</span>
                  <span className="text-gray-400 truncate flex-1">{ev.title?.slice(0, 55)}</span>
                  <RiskBadge score={ev.risk_score} />
                </div>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
};

// ═══════════════════════════════════════════════════════════════════════════════
// MAIN BLOOMBERG TERMINAL
// ═══════════════════════════════════════════════════════════════════════════════
export default function FMBloombergTerminal() {
  const [eventStream, setEventStream] = useState(null);
  const [warIntel, setWarIntel] = useState(null);
  const [riskMap, setRiskMap] = useState(null);
  const [portfolioAlerts, setPortfolioAlerts] = useState(null);
  const [radarEvents, setRadarEvents] = useState(null);
  const [loading, setLoading] = useState({ stream: true, war: true, map: true, alerts: true, radar: true });
  const [lastRefresh, setLastRefresh] = useState(new Date());
  const [autoRefresh, setAutoRefresh] = useState(true);
  const intervalRef = useRef(null);

  const fetchAll = useCallback(async () => {
    setLoading({ stream: true, war: true, map: true, alerts: true, radar: true });

    // Fetch all in parallel
    const [streamRes, warRes, mapRes, alertsRes, radarRes] = await Promise.allSettled([
      getEventStream(),
      getWarIntelligence(),
      getRiskMapData(),
      getPortfolioAlerts(),
      getLiveEvents(),
    ]);

    if (streamRes.status === 'fulfilled') setEventStream(streamRes.value);
    if (warRes.status === 'fulfilled') setWarIntel(warRes.value);
    if (mapRes.status === 'fulfilled') setRiskMap(mapRes.value);
    if (alertsRes.status === 'fulfilled') setPortfolioAlerts(alertsRes.value);
    if (radarRes.status === 'fulfilled') setRadarEvents(radarRes.value);

    setLoading({ stream: false, war: false, map: false, alerts: false, radar: false });
    setLastRefresh(new Date());
  }, []);

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  useEffect(() => {
    if (autoRefresh) {
      intervalRef.current = setInterval(fetchAll, 60000); // refresh every 60s
    }
    return () => clearInterval(intervalRef.current);
  }, [autoRefresh, fetchAll]);

  // Keyboard shortcuts
  useEffect(() => {
    const handler = (e) => {
      if (e.key === 'F5') { e.preventDefault(); fetchAll(); }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [fetchAll]);

  const totalEvents = radarEvents?.total || 0;
  const highRisk = radarEvents?.high_risk_count || 0;
  const criticalAlerts = portfolioAlerts?.critical_alerts || 0;

  return (
    <div className="min-h-screen bg-gray-950 text-white flex flex-col">
      {/* Terminal header */}
      <div className="bg-gray-900 border-b border-gray-700 px-4 py-2 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-1.5 rounded bg-red-900">
            <Globe size={16} className="text-red-400" />
          </div>
          <div>
            <div className="text-sm font-bold text-white flex items-center gap-2">
              FORCE MAJEURE INTELLIGENCE TERMINAL
              <LiveDot />
            </div>
            <div className="text-xs text-gray-500">
              GDELT · USGS · ReliefWeb · NewsAPI — Live global event monitoring
            </div>
          </div>
        </div>

        {/* Stats bar */}
        <div className="flex items-center gap-4 text-xs">
          <div className="text-center">
            <div className="text-purple-400 font-bold">{totalEvents}</div>
            <div className="text-gray-600">EVENTS</div>
          </div>
          <div className="text-center">
            <div className="text-red-400 font-bold">{highRisk}</div>
            <div className="text-gray-600">HIGH RISK</div>
          </div>
          <div className="text-center">
            <div className="text-yellow-400 font-bold">{criticalAlerts}</div>
            <div className="text-gray-600">ALERTS</div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={fetchAll}
              className="flex items-center gap-1 px-2 py-1 bg-gray-700 hover:bg-gray-600 rounded text-xs transition"
            >
              <RefreshCw size={11} /> Refresh
            </button>
            <button
              onClick={() => setAutoRefresh(a => !a)}
              className={`flex items-center gap-1 px-2 py-1 rounded text-xs transition ${autoRefresh ? 'bg-green-900 text-green-400' : 'bg-gray-700 text-gray-400'}`}
            >
              <Radio size={11} /> {autoRefresh ? 'AUTO ON' : 'AUTO OFF'}
            </button>
          </div>
          <div className="text-gray-600 text-xs flex items-center gap-1">
            <Clock size={10} /> {lastRefresh.toLocaleTimeString()}
          </div>
        </div>
      </div>

      {/* Keyboard shortcut bar */}
      <div className="bg-gray-900 border-b border-gray-800 px-4 py-1 flex gap-4 text-xs text-gray-600">
        {[['FMAP', 'Risk Map'], ['CRISK', 'Contract Risk'], ['CLAUSE', 'Clause Audit'], ['SUPPLY', 'Supply Chain'], ['SIM', 'Simulation']].map(([key, label]) => (
          <span key={key}>
            <span className="text-yellow-500 font-mono font-bold">{key}</span>
            <span className="ml-1 text-gray-600">{label}</span>
          </span>
        ))}
        <span className="ml-auto text-gray-700">F5 = Refresh</span>
      </div>

      {/* 5-panel grid */}
      <div className="flex-1 p-3 grid gap-3" style={{ gridTemplateColumns: '1fr 1fr 1fr', gridTemplateRows: '1fr 1fr', height: 'calc(100vh - 96px)' }}>

        {/* Row 1: Event Stream + War Intel + Risk Map */}
        <div style={{ gridColumn: '1', gridRow: '1' }}>
          <EventStreamPanel data={eventStream} loading={loading.stream} />
        </div>
        <div style={{ gridColumn: '2', gridRow: '1' }}>
          <WarIntelPanel data={warIntel} loading={loading.war} />
        </div>
        <div style={{ gridColumn: '3', gridRow: '1' }}>
          <RiskMapPanel data={riskMap} loading={loading.map} />
        </div>

        {/* Row 2: FM Radar + Portfolio Alerts */}
        <div style={{ gridColumn: '1 / 3', gridRow: '2' }}>
          <FMRadarPanel data={radarEvents} loading={loading.radar} />
        </div>
        <div style={{ gridColumn: '3', gridRow: '2' }}>
          <PortfolioAlertsPanel data={portfolioAlerts} loading={loading.alerts} />
        </div>
      </div>
    </div>
  );
}
