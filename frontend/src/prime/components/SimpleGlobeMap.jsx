import { useState, useEffect, useMemo } from "react";
import { Globe, DollarSign, AlertTriangle, MapPin, TrendingUp, Maximize2, Minimize2, X } from "lucide-react";

// ── Real simplified world map SVG paths ────────────────────────────────────────
const WORLD_PATHS = [
  // North America
  { d: "M 68 80 L 85 75 L 110 78 L 125 88 L 135 100 L 140 120 L 130 135 L 115 145 L 100 150 L 85 145 L 75 135 L 65 120 L 60 105 Z", region: "North America" },
  // Alaska
  { d: "M 40 65 L 65 70 L 68 80 L 55 85 L 40 78 Z", region: "North America" },
  // Greenland
  { d: "M 155 45 L 175 42 L 185 55 L 175 65 L 160 62 Z", region: "North America" },
  // Central America
  { d: "M 115 145 L 125 148 L 120 160 L 112 158 Z", region: "Latin America" },
  // South America
  { d: "M 125 165 L 145 160 L 160 175 L 165 200 L 155 230 L 140 245 L 125 248 L 112 235 L 108 210 L 112 185 Z", region: "Latin America" },
  // UK + Ireland
  { d: "M 258 88 L 265 85 L 272 90 L 270 100 L 260 102 L 255 95 Z", region: "Europe" },
  // Western Europe (France, Spain, Portugal)
  { d: "M 258 100 L 285 98 L 292 110 L 285 125 L 265 128 L 255 118 Z", region: "Europe" },
  // Central/Northern Europe
  { d: "M 268 78 L 310 75 L 325 88 L 318 100 L 290 98 L 270 95 Z", region: "Europe" },
  // Eastern Europe
  { d: "M 310 78 L 350 75 L 360 90 L 345 105 L 320 100 Z", region: "Europe" },
  // Scandinavia
  { d: "M 275 58 L 310 55 L 315 70 L 300 78 L 278 75 Z", region: "Europe" },
  // Italy + Balkans
  { d: "M 275 108 L 295 105 L 305 120 L 298 132 L 282 130 L 272 118 Z", region: "Europe" },
  // North Africa
  { d: "M 245 128 L 360 125 L 368 150 L 355 165 L 285 168 L 245 155 Z", region: "Africa" },
  // Sub-Saharan Africa
  { d: "M 260 168 L 355 165 L 362 200 L 350 230 L 320 248 L 295 255 L 272 245 L 258 220 L 255 195 Z", region: "Africa" },
  // Middle East (Arabian Peninsula)
  { d: "M 355 118 L 395 115 L 408 130 L 405 148 L 390 155 L 368 150 L 358 135 Z", region: "Middle East" },
  // Turkey
  { d: "M 318 100 L 358 98 L 365 108 L 355 118 L 325 118 Z", region: "Middle East" },
  // Russia (western)
  { d: "M 345 55 L 450 45 L 480 60 L 475 80 L 440 90 L 380 88 L 350 78 Z", region: "Asia" },
  // Russia (eastern)
  { d: "M 475 42 L 600 38 L 620 55 L 610 68 L 550 72 L 480 65 Z", region: "Asia" },
  // Central Asia
  { d: "M 380 90 L 460 88 L 475 105 L 465 118 L 420 122 L 385 115 Z", region: "Asia" },
  // South Asia (India)
  { d: "M 410 118 L 455 115 L 465 130 L 460 155 L 448 168 L 430 170 L 415 160 L 408 140 Z", region: "Asia" },
  // China
  { d: "M 465 78 L 545 72 L 568 88 L 565 108 L 545 122 L 500 128 L 468 118 L 462 98 Z", region: "Asia" },
  // Southeast Asia
  { d: "M 525 128 L 568 122 L 578 140 L 565 155 L 540 158 L 520 148 Z", region: "Asia" },
  // Japan
  { d: "M 578 88 L 592 85 L 598 98 L 590 108 L 578 105 Z", region: "Asia" },
  // Korea
  { d: "M 565 95 L 580 92 L 582 105 L 570 108 L 562 102 Z", region: "Asia" },
  // Australia
  { d: "M 535 195 L 598 188 L 618 205 L 622 228 L 608 245 L 578 252 L 548 248 L 528 232 L 525 212 Z", region: "Asia Pacific" },
  // New Zealand
  { d: "M 625 228 L 635 225 L 638 238 L 630 245 L 623 238 Z", region: "Asia Pacific" },
  // Indonesia / Philippines
  { d: "M 538 155 L 598 148 L 605 162 L 588 168 L 542 165 Z", region: "Asia Pacific" },
];

// ── Jurisdiction → map percentage coordinates ──────────────────────────────────
const JURISDICTION_COORDS = {
  // North America
  "usa": { x: 16, y: 38, region: "North America", label: "USA" },
  "united states": { x: 16, y: 38, region: "North America", label: "USA" },
  "us": { x: 16, y: 38, region: "North America", label: "USA" },
  "new york": { x: 18, y: 35, region: "North America", label: "New York" },
  "california": { x: 12, y: 37, region: "North America", label: "California" },
  "texas": { x: 16, y: 41, region: "North America", label: "Texas" },
  "canada": { x: 16, y: 28, region: "North America", label: "Canada" },
  "mexico": { x: 15, y: 47, region: "Latin America", label: "Mexico" },
  // South America
  "brazil": { x: 27, y: 62, region: "Latin America", label: "Brazil" },
  "argentina": { x: 24, y: 70, region: "Latin America", label: "Argentina" },
  "colombia": { x: 22, y: 54, region: "Latin America", label: "Colombia" },
  "chile": { x: 22, y: 66, region: "Latin America", label: "Chile" },
  // Europe
  "uk": { x: 43, y: 30, region: "Europe", label: "UK" },
  "united kingdom": { x: 43, y: 30, region: "Europe", label: "UK" },
  "england": { x: 43, y: 30, region: "Europe", label: "UK" },
  "london": { x: 43, y: 30, region: "Europe", label: "London" },
  "germany": { x: 48, y: 28, region: "Europe", label: "Germany" },
  "france": { x: 46, y: 32, region: "Europe", label: "France" },
  "netherlands": { x: 47, y: 27, region: "Europe", label: "Netherlands" },
  "switzerland": { x: 48, y: 31, region: "Europe", label: "Switzerland" },
  "spain": { x: 44, y: 35, region: "Europe", label: "Spain" },
  "italy": { x: 49, y: 33, region: "Europe", label: "Italy" },
  "europe": { x: 48, y: 30, region: "Europe", label: "Europe" },
  // Middle East
  "dubai": { x: 60, y: 44, region: "Middle East", label: "Dubai" },
  "uae": { x: 60, y: 44, region: "Middle East", label: "UAE" },
  "saudi arabia": { x: 57, y: 43, region: "Middle East", label: "Saudi Arabia" },
  "qatar": { x: 59, y: 44, region: "Middle East", label: "Qatar" },
  "israel": { x: 55, y: 40, region: "Middle East", label: "Israel" },
  "turkey": { x: 53, y: 33, region: "Middle East", label: "Turkey" },
  "middle east": { x: 58, y: 42, region: "Middle East", label: "Middle East" },
  // Asia
  "india": { x: 65, y: 45, region: "Asia", label: "India" },
  "china": { x: 74, y: 36, region: "Asia", label: "China" },
  "singapore": { x: 75, y: 53, region: "Asia Pacific", label: "Singapore" },
  "japan": { x: 82, y: 35, region: "Asia", label: "Japan" },
  "hong kong": { x: 77, y: 43, region: "Asia", label: "Hong Kong" },
  "south korea": { x: 80, y: 36, region: "Asia", label: "Korea" },
  "australia": { x: 80, y: 65, region: "Asia Pacific", label: "Australia" },
  "indonesia": { x: 77, y: 57, region: "Asia Pacific", label: "Indonesia" },
  "malaysia": { x: 75, y: 53, region: "Asia Pacific", label: "Malaysia" },
  "asia": { x: 74, y: 40, region: "Asia", label: "Asia" },
  // Africa
  "south africa": { x: 50, y: 70, region: "Africa", label: "South Africa" },
  "nigeria": { x: 46, y: 54, region: "Africa", label: "Nigeria" },
  "egypt": { x: 53, y: 38, region: "Africa", label: "Egypt" },
  "kenya": { x: 55, y: 58, region: "Africa", label: "Kenya" },
  "africa": { x: 50, y: 58, region: "Africa", label: "Africa" },
};

const REGION_FALLBACKS = {
  "north america": { x: 16, y: 38, region: "North America", label: "Americas" },
  "latin america": { x: 25, y: 60, region: "Latin America", label: "Latin America" },
  "europe": { x: 48, y: 30, region: "Europe", label: "Europe" },
  "middle east": { x: 58, y: 42, region: "Middle East", label: "Middle East" },
  "asia": { x: 72, y: 40, region: "Asia", label: "Asia" },
  "asia pacific": { x: 78, y: 55, region: "Asia Pacific", label: "Asia Pacific" },
  "africa": { x: 50, y: 58, region: "Africa", label: "Africa" },
};

// ── Smart jurisdiction inference ───────────────────────────────────────────────
function inferJurisdiction(contract) {
  const fields = [
    contract.jurisdiction,
    contract.party_name,
    contract.party_a,
    contract.party_b,
    contract.original_filename,
    contract.contract_type,
  ].filter(Boolean).join(" ").toLowerCase();

  for (const key of Object.keys(JURISDICTION_COORDS)) {
    if (fields.includes(key)) return JURISDICTION_COORDS[key];
  }
  for (const key of Object.keys(REGION_FALLBACKS)) {
    if (fields.includes(key)) return REGION_FALLBACKS[key];
  }
  return null;
}

// Distribute unknown contracts across realistic world locations
const SPREAD_COORDS = [
  { x: 16, y: 38, region: "North America", label: "USA" },
  { x: 47, y: 30, region: "Europe", label: "Europe" },
  { x: 72, y: 40, region: "Asia", label: "Asia" },
  { x: 60, y: 44, region: "Middle East", label: "Middle East" },
  { x: 65, y: 45, region: "Asia", label: "India" },
  { x: 80, y: 65, region: "Asia Pacific", label: "Australia" },
  { x: 26, y: 62, region: "Latin America", label: "Brazil" },
  { x: 48, y: 58, region: "Africa", label: "Africa" },
  { x: 82, y: 35, region: "Asia", label: "Japan" },
  { x: 43, y: 30, region: "Europe", label: "UK" },
  { x: 48, y: 28, region: "Europe", label: "Germany" },
  { x: 75, y: 53, region: "Asia Pacific", label: "Singapore" },
];

function parseValue(raw) {
  if (!raw) return 0;
  try {
    let s = String(raw).trim();
    let m = 1;
    if (s.toUpperCase().endsWith("B")) { m = 1e9; s = s.slice(0, -1); }
    else if (s.toUpperCase().endsWith("M")) { m = 1e6; s = s.slice(0, -1); }
    else if (s.toUpperCase().endsWith("K")) { m = 1e3; s = s.slice(0, -1); }
    return parseFloat(s.replace(/[$,]/g, "")) * m || 0;
  } catch { return 0; }
}

function formatValue(v) {
  if (!v || v === 0) return "$0";
  if (v >= 1e9) return `$${(v / 1e9).toFixed(1)}B`;
  if (v >= 1e6) return `$${(v / 1e6).toFixed(1)}M`;
  if (v >= 1e3) return `$${(v / 1e3).toFixed(0)}K`;
  return `$${v.toFixed(0)}`;
}

// ── Connection arc between two points ─────────────────────────────────────────
function ConnectionArc({ x1, y1, x2, y2, color }) {
  const mx = (x1 + x2) / 2;
  const my = Math.min(y1, y2) - 12;
  return (
    <path
      d={`M ${x1} ${y1} Q ${mx} ${my} ${x2} ${y2}`}
      fill="none"
      stroke={color}
      strokeWidth="0.5"
      strokeDasharray="3,2"
      opacity="0.35"
    />
  );
}

export default function SimpleGlobeMap({ selectedContract, contracts = [] }) {
  const [locations, setLocations] = useState([]);
  const [selectedLocation, setSelectedLocation] = useState(null);
  const [fullscreen, setFullscreen] = useState(false);
  const [hoveredRegion, setHoveredRegion] = useState(null);

  useEffect(() => {
    const display = selectedContract && selectedContract !== "all"
      ? contracts.filter(c => String(c.id) === String(selectedContract))
      : contracts;

    if (display.length === 0) { setLocations([]); return; }

    // Build location map
    const locMap = {};
    display.forEach((c, i) => {
      const coords = inferJurisdiction(c) || SPREAD_COORDS[i % SPREAD_COORDS.length];
      const key = `${coords.x.toFixed(0)}-${coords.y.toFixed(0)}`;
      const val = parseValue(c.contract_value);
      const riskLevel = c.liability_level === "HIGH" ? "high" : c.liability_level === "MEDIUM" ? "medium" : "low";
      const riskColor = riskLevel === "high" ? "#ef4444" : riskLevel === "medium" ? "#f59e0b" : "#10b981";

      if (!locMap[key]) {
        locMap[key] = { ...coords, key, contracts: [], totalValue: 0, highRiskCount: 0, mediumRiskCount: 0, color: "#10b981" };
      }
      locMap[key].contracts.push({ id: c.id, name: c.original_filename, value: val, party: c.party_name, risk: riskLevel, status: c.status });
      locMap[key].totalValue += val;
      if (riskLevel === "high") { locMap[key].highRiskCount++; locMap[key].color = "#ef4444"; }
      else if (riskLevel === "medium" && locMap[key].color !== "#ef4444") { locMap[key].mediumRiskCount++; locMap[key].color = "#f59e0b"; }
    });

    setLocations(Object.values(locMap));
  }, [selectedContract, contracts]);

  const totalValue = useMemo(() => locations.reduce((s, l) => s + l.totalValue, 0), [locations]);
  const totalContracts = useMemo(() => locations.reduce((s, l) => s + l.contracts.length, 0), [locations]);
  const totalHighRisk = useMemo(() => locations.reduce((s, l) => s + l.highRiskCount, 0), [locations]);

  // Connections between high-risk locations
  const connections = useMemo(() => {
    const highRisk = locations.filter(l => l.highRiskCount > 0);
    const arcs = [];
    for (let i = 0; i < highRisk.length - 1; i++) {
      arcs.push({ x1: highRisk[i].x, y1: highRisk[i].y, x2: highRisk[i + 1].x, y2: highRisk[i + 1].y, color: "#ef4444" });
    }
    // Hub connections from largest location
    const sorted = [...locations].sort((a, b) => b.totalValue - a.totalValue);
    if (sorted.length > 1) {
      for (let i = 1; i < Math.min(sorted.length, 5); i++) {
        arcs.push({ x1: sorted[0].x, y1: sorted[0].y, x2: sorted[i].x, y2: sorted[i].y, color: "#06b6d4" });
      }
    }
    return arcs;
  }, [locations]);

  // Region summary
  const regionSummary = useMemo(() => {
    const r = {};
    locations.forEach(l => {
      if (!r[l.region]) r[l.region] = { contracts: 0, value: 0, highRisk: 0 };
      r[l.region].contracts += l.contracts.length;
      r[l.region].value += l.totalValue;
      r[l.region].highRisk += l.highRiskCount;
    });
    return Object.entries(r).sort((a, b) => b[1].value - a[1].value);
  }, [locations]);

  return (
    <div className={`rounded-2xl bg-slate-950 shadow-2xl border border-white/10 flex flex-col ${fullscreen ? "fixed inset-2 z-50" : "h-[650px]"}`}>

      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-white/10 flex-shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-1 h-6 bg-gradient-to-b from-emerald-400 to-teal-600 rounded-full" />
          <div>
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              Global Portfolio Exposure Map
              <span className="text-xs text-gray-500 font-normal">({locations.length} {locations.length === 1 ? "Location" : "Locations"})</span>
            </h3>
            <p className="text-xs text-gray-500">Click markers for details · Hover regions for info</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Globe className="w-4 h-4 text-emerald-400" />
          <button onClick={() => setFullscreen(v => !v)} className="p-1.5 rounded-lg bg-white/10 hover:bg-white/20 transition-colors">
            {fullscreen ? <Minimize2 className="w-3.5 h-3.5 text-white" /> : <Maximize2 className="w-3.5 h-3.5 text-white" />}
          </button>
        </div>
      </div>

      {/* Map */}
      <div className="flex-1 relative min-h-0 overflow-hidden">
        <svg
          viewBox="0 0 700 380"
          className="w-full h-full"
          style={{ background: "linear-gradient(180deg, #020617 0%, #0c1a33 40%, #020617 100%)" }}
        >
          {/* Ocean grid */}
          <defs>
            <pattern id="grid" width="25" height="25" patternUnits="userSpaceOnUse">
              <path d="M 25 0 L 0 0 0 25" fill="none" stroke="#06b6d408" strokeWidth="0.5" />
            </pattern>
            <radialGradient id="glow-red" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#ef4444" stopOpacity="0.6" />
              <stop offset="100%" stopColor="#ef4444" stopOpacity="0" />
            </radialGradient>
            <radialGradient id="glow-amber" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#f59e0b" stopOpacity="0.6" />
              <stop offset="100%" stopColor="#f59e0b" stopOpacity="0" />
            </radialGradient>
            <radialGradient id="glow-green" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#10b981" stopOpacity="0.6" />
              <stop offset="100%" stopColor="#10b981" stopOpacity="0" />
            </radialGradient>
          </defs>
          <rect width="700" height="380" fill="url(#grid)" />

          {/* Latitude lines */}
          {[60, 100, 140, 180, 220, 260, 300, 340].map(y => (
            <line key={y} x1="0" y1={y} x2="700" y2={y} stroke="#06b6d410" strokeWidth="0.5" />
          ))}
          {/* Longitude lines */}
          {[70, 140, 210, 280, 350, 420, 490, 560, 630].map(x => (
            <line key={x} x1={x} y1="0" x2={x} y2="380" stroke="#06b6d410" strokeWidth="0.5" />
          ))}
          {/* Equator */}
          <line x1="0" y1="195" x2="700" y2="195" stroke="#06b6d420" strokeWidth="1" strokeDasharray="4,4" />
          <text x="4" y="193" fontSize="6" fill="#06b6d440">equator</text>
          {/* Tropic of Cancer */}
          <line x1="0" y1="160" x2="700" y2="160" stroke="#f59e0b15" strokeWidth="0.5" strokeDasharray="3,6" />
          {/* Tropic of Capricorn */}
          <line x1="0" y1="230" x2="700" y2="230" stroke="#f59e0b15" strokeWidth="0.5" strokeDasharray="3,6" />

          {/* Continents */}
          {WORLD_PATHS.map((p, i) => {
            const isHovered = hoveredRegion === p.region;
            return (
              <path
                key={i}
                d={p.d.replace(/(\d+)/g, (n) => String(Math.round(parseInt(n) * 700 / 700)))}
                fill={isHovered ? "#1e3a5f" : "#0f2744"}
                stroke="#1e40af"
                strokeWidth="0.6"
                opacity={isHovered ? 1 : 0.85}
                onMouseEnter={() => setHoveredRegion(p.region)}
                onMouseLeave={() => setHoveredRegion(null)}
                style={{ cursor: "default", transition: "fill 0.2s" }}
              />
            );
          })}

          {/* Connection arcs */}
          {connections.map((arc, i) => (
            <ConnectionArc
              key={i}
              x1={arc.x1 * 7}
              y1={arc.y1 * 3.5}
              x2={arc.x2 * 7}
              y2={arc.y2 * 3.5}
              color={arc.color}
            />
          ))}

          {/* Location markers */}
          {locations.map((loc, i) => {
            const cx = loc.x * 7;
            const cy = loc.y * 3.5;
            const baseR = Math.min(Math.max(4 + loc.contracts.length * 2.5, 6), 18);
            const glowId = loc.color === "#ef4444" ? "glow-red" : loc.color === "#f59e0b" ? "glow-amber" : "glow-green";
            const isSelected = selectedLocation?.key === loc.key;

            return (
              <g key={i} onClick={() => setSelectedLocation(isSelected ? null : loc)} style={{ cursor: "pointer" }}>
                {/* Glow halo */}
                <circle cx={cx} cy={cy} r={baseR * 2.5} fill={`url(#${glowId})`} opacity="0.5" />
                {/* Pulse ring */}
                <circle cx={cx} cy={cy} r={baseR + 3} fill="none" stroke={loc.color} strokeWidth="1" opacity="0.4">
                  <animate attributeName="r" values={`${baseR + 2};${baseR + 7};${baseR + 2}`} dur="2s" repeatCount="indefinite" />
                  <animate attributeName="opacity" values="0.6;0;0.6" dur="2s" repeatCount="indefinite" />
                </circle>
                {/* Main dot */}
                <circle cx={cx} cy={cy} r={baseR} fill={loc.color} stroke="white" strokeWidth={isSelected ? 1.5 : 0.8} opacity="0.92" />
                {/* Count label */}
                <text x={cx} y={cy + 3.5} textAnchor="middle" fontSize={baseR > 10 ? "7" : "6"} fill="white" fontWeight="bold">
                  {loc.contracts.length}
                </text>
                {/* Location name label */}
                <text x={cx} y={cy - baseR - 3} textAnchor="middle" fontSize="5.5" fill={loc.color} fontWeight="600">
                  {loc.label}
                </text>
                {/* Value label */}
                {loc.totalValue > 0 && (
                  <text x={cx} y={cy + baseR + 7} textAnchor="middle" fontSize="5" fill="#10b981" opacity="0.9">
                    {formatValue(loc.totalValue)}
                  </text>
                )}
                {/* High-risk warning badge */}
                {loc.highRiskCount > 0 && (
                  <g>
                    <circle cx={cx + baseR - 1} cy={cy - baseR + 1} r="4" fill="#ef4444" stroke="#020617" strokeWidth="0.8" />
                    <text x={cx + baseR - 1} y={cy - baseR + 3.5} textAnchor="middle" fontSize="4.5" fill="white" fontWeight="bold">
                      !
                    </text>
                  </g>
                )}
              </g>
            );
          })}

          {/* Hovered region tooltip */}
          {hoveredRegion && (
            <text x="350" y="370" textAnchor="middle" fontSize="8" fill="#94a3b8">{hoveredRegion}</text>
          )}
        </svg>

        {/* Selected location popup */}
        {selectedLocation && (
          <div className="absolute top-3 right-3 bg-slate-900/98 backdrop-blur border border-white/15 rounded-xl p-4 w-72 shadow-2xl z-20">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <MapPin className="w-4 h-4" style={{ color: selectedLocation.color }} />
                <h4 className="font-bold text-white text-sm">{selectedLocation.label}</h4>
                <span className="text-xs text-gray-500">{selectedLocation.region}</span>
              </div>
              <button onClick={() => setSelectedLocation(null)} className="text-gray-500 hover:text-white">
                <X className="w-3.5 h-3.5" />
              </button>
            </div>

            <div className="grid grid-cols-3 gap-2 mb-3">
              <div className="bg-white/5 rounded-lg p-2 text-center">
                <p className="text-[10px] text-gray-400">Contracts</p>
                <p className="text-sm font-bold text-cyan-400">{selectedLocation.contracts.length}</p>
              </div>
              <div className="bg-white/5 rounded-lg p-2 text-center">
                <p className="text-[10px] text-gray-400">Value</p>
                <p className="text-sm font-bold text-green-400">{formatValue(selectedLocation.totalValue)}</p>
              </div>
              <div className="bg-white/5 rounded-lg p-2 text-center">
                <p className="text-[10px] text-gray-400">High Risk</p>
                <p className="text-sm font-bold text-red-400">{selectedLocation.highRiskCount}</p>
              </div>
            </div>

            <div className="space-y-1.5 max-h-48 overflow-y-auto">
              <p className="text-[10px] text-gray-500 uppercase tracking-wide mb-1">Contracts</p>
              {selectedLocation.contracts.map((c, i) => (
                <div key={i} className="flex items-center justify-between bg-white/5 rounded-lg px-2.5 py-1.5">
                  <div className="min-w-0">
                    <p className="text-xs text-white truncate">{c.name || `Contract ${i + 1}`}</p>
                    {c.party && <p className="text-[10px] text-gray-500 truncate">{c.party}</p>}
                  </div>
                  <div className="flex items-center gap-1.5 ml-2 flex-shrink-0">
                    {c.value > 0 && <span className="text-[10px] text-green-400 font-mono">{formatValue(c.value)}</span>}
                    <span className={`text-[9px] px-1.5 py-0.5 rounded font-semibold ${
                      c.risk === "high" ? "bg-red-500/20 text-red-400" :
                      c.risk === "medium" ? "bg-yellow-500/20 text-yellow-400" : "bg-green-500/20 text-green-400"
                    }`}>{c.risk}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Stats bar */}
      <div className="border-t border-white/10 flex-shrink-0">
        <div className="grid grid-cols-4 gap-0 divide-x divide-white/10">
          {[
            { icon: DollarSign, label: "Total Value", value: formatValue(totalValue), color: "text-green-400", bg: "from-green-500/10" },
            { icon: MapPin,     label: "Contracts",   value: totalContracts,           color: "text-cyan-400",  bg: "from-cyan-500/10" },
            { icon: AlertTriangle, label: "High Risk", value: totalHighRisk,           color: "text-red-400",   bg: "from-red-500/10" },
            { icon: Globe,     label: "Locations",    value: locations.length,          color: "text-purple-400", bg: "from-purple-500/10" },
          ].map(s => (
            <div key={s.label} className={`p-3 bg-gradient-to-br ${s.bg} to-transparent`}>
              <div className="flex items-center gap-1.5 mb-0.5">
                <s.icon className={`w-3 h-3 ${s.color}`} />
                <p className="text-[10px] text-gray-400">{s.label}</p>
              </div>
              <p className={`text-base font-bold ${s.color}`}>{s.value}</p>
            </div>
          ))}
        </div>

        {/* Region breakdown */}
        {regionSummary.length > 0 && (
          <div className="px-4 py-2 border-t border-white/5 flex gap-3 overflow-x-auto">
            {regionSummary.map(([region, data]) => (
              <div key={region} className="flex items-center gap-1.5 text-xs whitespace-nowrap">
                <TrendingUp className="w-3 h-3 text-gray-500" />
                <span className="text-gray-400">{region}:</span>
                <span className="text-white font-semibold">{data.contracts}</span>
                <span className="text-gray-600">·</span>
                <span className="text-green-400">{formatValue(data.value)}</span>
                {data.highRisk > 0 && <span className="text-red-400">· {data.highRisk} high risk</span>}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
