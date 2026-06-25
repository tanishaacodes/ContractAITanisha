import { useState, useEffect, useCallback, useRef } from "react";
import mapboxgl from "mapbox-gl";
import { Globe, DollarSign, Maximize2, Minimize2, TrendingUp } from "lucide-react";
import "mapbox-gl/dist/mapbox-gl.css";

// Mapbox token - using public token for demo (replace with your token)
const MAPBOX_TOKEN = import.meta.env.VITE_MAPBOX_TOKEN;

mapboxgl.accessToken = MAPBOX_TOKEN;

export default function PortfolioGlobe({ selectedContract, contracts = [] }) {
  const mapContainerRef = useRef(null);
  const mapRef = useRef(null);
  const markersRef = useRef([]);
  const popupRef = useRef(null);

  const [selectedRegion, setSelectedRegion] = useState(null);
  const [regions, setRegions] = useState([]);
  const [fullscreen, setFullscreen] = useState(false);
  const [mapLoaded, setMapLoaded] = useState(false);

  // Initialize regions
  useEffect(() => {
    const baseRegions = [
      {
        name: "North America",
        var: 1200,
        exposure: 2400,
        risk: "high",
        coordinates: [-98.5795, 39.8283],
        color: "#ef4444"
      },
      {
        name: "Europe",
        var: 900,
        exposure: 1800,
        risk: "medium",
        coordinates: [10.4515, 51.1657],
        color: "#f59e0b"
      },
      {
        name: "Asia Pacific",
        var: 850,
        exposure: 1600,
        risk: "high",
        coordinates: [103.8198, 1.3521],
        color: "#ef4444"
      },
      {
        name: "Latin America",
        var: 320,
        exposure: 680,
        risk: "medium",
        coordinates: [-47.9292, -15.7801],
        color: "#f59e0b"
      },
      {
        name: "Middle East",
        var: 450,
        exposure: 920,
        risk: "low",
        coordinates: [55.2708, 25.2048],
        color: "#10b981"
      }
    ];

    if (selectedContract === "all" && contracts.length > 0) {
      setRegions(baseRegions.map((r, i) => ({
        ...r,
        contracts: Math.floor(contracts.length * [0.35, 0.25, 0.28, 0.07, 0.05][i])
      })));
    } else {
      setRegions(baseRegions.map((r, i) => ({
        ...r,
        contracts: [145, 98, 112, 42, 38][i]
      })));
    }
  }, [selectedContract, contracts]);

  // Initialize map
  useEffect(() => {
    if (!mapContainerRef.current) return;

    const map = new mapboxgl.Map({
      container: mapContainerRef.current,
      style: 'mapbox://styles/mapbox/dark-v11',
      projection: 'globe',
      center: [0, 20],
      zoom: 1.2,
      pitch: 0
    });

    mapRef.current = map;

    map.on('load', () => {
      setMapLoaded(true);
    });

    return () => {
      setMapLoaded(false);
      map.remove();
    };
  }, []);

  // Update markers when regions change
  useEffect(() => {
    if (!mapRef.current || !mapLoaded || regions.length === 0) return;

    // Clear existing markers
    markersRef.current.forEach(marker => marker.remove());
    markersRef.current = [];

    // Add heatmap source and layer
    if (!mapRef.current.getSource('var-heatmap')) {
      mapRef.current.addSource('var-heatmap', {
        type: 'geojson',
        data: {
          type: 'FeatureCollection',
          features: regions.map(region => ({
            type: 'Feature',
            properties: {
              var: region.var,
              exposure: region.exposure,
              intensity: region.var / 100
            },
            geometry: {
              type: 'Point',
              coordinates: region.coordinates
            }
          }))
        }
      });

      mapRef.current.addLayer({
        id: 'heatmap-layer',
        type: 'heatmap',
        source: 'var-heatmap',
        paint: {
          'heatmap-weight': ['interpolate', ['linear'], ['get', 'intensity'], 0, 0, 20, 1],
          'heatmap-intensity': ['interpolate', ['linear'], ['zoom'], 0, 1, 9, 3],
          'heatmap-color': [
            'interpolate',
            ['linear'],
            ['heatmap-density'],
            0, 'rgba(0, 0, 255, 0)',
            0.2, 'rgb(34, 211, 238)',
            0.4, 'rgb(168, 85, 247)',
            0.6, 'rgb(251, 191, 36)',
            0.8, 'rgb(239, 68, 68)',
            1, 'rgb(220, 38, 38)'
          ],
          'heatmap-radius': ['interpolate', ['linear'], ['zoom'], 0, 30, 9, 60],
          'heatmap-opacity': 0.8
        }
      });
    }

    // Add markers
    regions.forEach(region => {
      const markerEl = document.createElement('div');
      markerEl.className = 'custom-marker';
      markerEl.style.cssText = `
        width: ${Math.min(region.var / 30, 30)}px;
        height: ${Math.min(region.var / 30, 30)}px;
        background-color: ${region.color};
        border-radius: 50%;
        cursor: pointer;
        box-shadow: 0 0 20px ${region.color};
        animation: pulse 2s infinite;
      `;

      const marker = new mapboxgl.Marker(markerEl)
        .setLngLat(region.coordinates)
        .addTo(mapRef.current);

      markerEl.addEventListener('click', () => {
        setSelectedRegion(region);
        mapRef.current.flyTo({
          center: region.coordinates,
          zoom: 4,
          duration: 1000
        });

        // Show popup
        if (!popupRef.current) {
          popupRef.current = new mapboxgl.Popup({ closeButton: true, closeOnClick: false });
        }

        popupRef.current
          .setLngLat(region.coordinates)
          .setHTML(`
            <div style="background: #0f172a; padding: 16px; border-radius: 8px; min-width: 200px;">
              <h4 style="font-weight: bold; color: white; margin-bottom: 8px; display: flex; align-items: center; gap: 8px;">
                ${region.name}
              </h4>
              <div style="color: #d1d5db; font-size: 14px; line-height: 1.8;">
                <p>VaR: <span style="font-weight: 600; color: #f87171;">$${region.var}M</span></p>
                <p>Exposure: <span style="font-weight: 600; color: #fbbf24;">$${region.exposure}M</span></p>
                <p>Contracts: <span style="font-weight: 600; color: #22d3ee;">${region.contracts}</span></p>
                <div style="display: flex; align-items: center; gap: 8px; margin-top: 8px; padding-top: 8px; border-top: 1px solid #374151;">
                  <div style="width: 8px; height: 8px; border-radius: 50%; background-color: ${region.color};"></div>
                  <span style="font-size: 12px; color: #9ca3af; text-transform: capitalize;">${region.risk} Risk</span>
                </div>
              </div>
            </div>
          `)
          .addTo(mapRef.current);
      });

      markersRef.current.push(marker);
    });
  }, [regions, mapLoaded]);

  return (
    <div className={`rounded-2xl bg-gradient-to-br from-white/5 to-white/10 shadow-2xl backdrop-blur-lg border border-white/10 ${fullscreen ? 'fixed inset-4 z-50' : 'h-[600px]'}`}>
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-white/10">
        <h3 className="text-xl font-bold text-white flex items-center gap-2">
          <div className="w-1 h-6 bg-gradient-to-b from-emerald-500 to-teal-600 rounded-full" />
          Global Portfolio Exposure Map
          <span className="text-xs text-gray-400 font-normal">
            ({selectedContract === "all" ? "All Regions" : "Distribution"})
          </span>
        </h3>

        <div className="flex items-center gap-2">
          <Globe className="w-5 h-5 text-emerald-400" />
          <button
            onClick={() => setFullscreen(!fullscreen)}
            className="p-2 rounded-lg bg-white/10 hover:bg-white/20 transition-colors"
            title={fullscreen ? "Exit Fullscreen" : "Fullscreen"}
          >
            {fullscreen ? (
              <Minimize2 className="w-4 h-4 text-white" />
            ) : (
              <Maximize2 className="w-4 h-4 text-white" />
            )}
          </button>
        </div>
      </div>

      {/* Mapbox Globe */}
      <div
        ref={mapContainerRef}
        className={`relative ${fullscreen ? 'h-[calc(100%-140px)]' : 'h-[400px]'} rounded-xl overflow-hidden`}
      />

      <style>{`
        @keyframes pulse {
          0%, 100% {
            opacity: 1;
            transform: scale(1);
          }
          50% {
            opacity: 0.5;
            transform: scale(1.1);
          }
        }
      `}</style>

      {/* Summary Stats */}
      <div className="grid grid-cols-4 gap-3 p-4">
        <div className="bg-gradient-to-br from-red-500/10 to-red-600/5 border border-red-500/20 rounded-lg p-3">
          <div className="flex items-center gap-2 mb-1">
            <DollarSign className="w-3 h-3 text-red-400" />
            <p className="text-xs text-gray-400">Total VaR</p>
          </div>
          <p className="text-lg font-bold text-red-400">
            ${regions.reduce((sum, r) => sum + r.var, 0)}M
          </p>
        </div>
        <div className="bg-gradient-to-br from-yellow-500/10 to-yellow-600/5 border border-yellow-500/20 rounded-lg p-3">
          <p className="text-xs text-gray-400 mb-1">Exposure</p>
          <p className="text-lg font-bold text-yellow-400">
            ${regions.reduce((sum, r) => sum + r.exposure, 0)}M
          </p>
        </div>
        <div className="bg-gradient-to-br from-cyan-500/10 to-cyan-600/5 border border-cyan-500/20 rounded-lg p-3">
          <p className="text-xs text-gray-400 mb-1">Contracts</p>
          <p className="text-lg font-bold text-cyan-400">
            {regions.reduce((sum, r) => sum + r.contracts, 0)}
          </p>
        </div>
        <div className="bg-gradient-to-br from-purple-500/10 to-purple-600/5 border border-purple-500/20 rounded-lg p-3">
          <p className="text-xs text-gray-400 mb-1">Regions</p>
          <p className="text-lg font-bold text-purple-400">{regions.length}</p>
        </div>
      </div>
    </div>
  );
}
