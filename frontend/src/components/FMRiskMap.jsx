/**
 * FM Risk Map - Geographic Risk Visualization with Mapbox GL
 * Interactive map showing Force Majeure risk levels by region
 */

import React, { useEffect, useRef, useState } from 'react';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';

// Set your Mapbox access token
mapboxgl.accessToken = import.meta.env.VITE_MAPBOX_TOKEN || "";

const FMRiskMap = ({
  riskData = [],
  center = [0, 20],
  zoom = 2,
  height = '600px',
  onRegionClick
}) => {
  const mapContainer = useRef(null);
  const map = useRef(null);
  const [markers, setMarkers] = useState([]);

  useEffect(() => {
    if (map.current) return; // Initialize map only once

    map.current = new mapboxgl.Map({
      container: mapContainer.current,
      style: 'mapbox://styles/mapbox/dark-v11',
      center: center,
      zoom: zoom,
      projection: 'mercator'
    });

    // Add navigation controls
    map.current.addControl(new mapboxgl.NavigationControl(), 'top-right');

    // Add fullscreen control
    map.current.addControl(new mapboxgl.FullscreenControl(), 'top-right');

    map.current.on('load', () => {
      // Add risk heatmap layer
      addRiskHeatmap();
    });

    return () => {
      if (map.current) {
        map.current.remove();
      }
    };
  }, []);

  useEffect(() => {
    if (!map.current || !map.current.loaded()) return;

    // Clear existing markers
    markers.forEach(marker => marker.remove());

    // Add new markers for risk data
    const newMarkers = riskData.map(risk => {
      const el = createMarkerElement(risk.risk_level);

      const marker = new mapboxgl.Marker(el)
        .setLngLat([risk.longitude, risk.latitude])
        .setPopup(
          new mapboxgl.Popup({ offset: 25 })
            .setHTML(`
              <div style="padding: 10px;">
                <h3 style="margin: 0 0 8px 0; color: #333;">${risk.region}</h3>
                <div style="margin-bottom: 5px;">
                  <strong>Risk Level:</strong>
                  <span style="color: ${getRiskColor(risk.risk_level)}; font-weight: bold;">
                    ${(risk.risk_level * 100).toFixed(0)}%
                  </span>
                </div>
                <div style="margin-bottom: 5px;">
                  <strong>Primary Risks:</strong> ${risk.primary_risks?.join(', ') || 'N/A'}
                </div>
                <div style="margin-bottom: 5px;">
                  <strong>Active Events:</strong> ${risk.active_events || 0}
                </div>
                <div>
                  <strong>Affected Contracts:</strong> ${risk.affected_contracts || 0}
                </div>
              </div>
            `)
        )
        .addTo(map.current);

      // Add click handler
      if (onRegionClick) {
        el.addEventListener('click', () => onRegionClick(risk));
      }

      return marker;
    });

    setMarkers(newMarkers);

    // Fit map to show all markers
    if (riskData.length > 0) {
      const bounds = new mapboxgl.LngLatBounds();
      riskData.forEach(risk => {
        bounds.extend([risk.longitude, risk.latitude]);
      });
      map.current.fitBounds(bounds, { padding: 50, maxZoom: 5 });
    }
  }, [riskData]);

  const createMarkerElement = (riskLevel) => {
    const el = document.createElement('div');
    el.className = 'fm-risk-marker';

    const size = 20 + (riskLevel * 30); // Size based on risk level
    const color = getRiskColor(riskLevel);

    el.style.width = `${size}px`;
    el.style.height = `${size}px`;
    el.style.borderRadius = '50%';
    el.style.backgroundColor = color;
    el.style.border = '2px solid white';
    el.style.boxShadow = '0 2px 8px rgba(0,0,0,0.3)';
    el.style.cursor = 'pointer';
    el.style.transition = 'transform 0.2s';

    el.addEventListener('mouseenter', () => {
      el.style.transform = 'scale(1.2)';
    });

    el.addEventListener('mouseleave', () => {
      el.style.transform = 'scale(1)';
    });

    return el;
  };

  const getRiskColor = (riskLevel) => {
    if (riskLevel >= 0.75) return '#DC2626'; // Red (Critical)
    if (riskLevel >= 0.50) return '#EA580C'; // Orange (High)
    if (riskLevel >= 0.30) return '#F59E0B'; // Yellow (Medium)
    return '#10B981'; // Green (Low)
  };

  const addRiskHeatmap = () => {
    // Add heatmap source
    map.current.addSource('risk-heatmap', {
      type: 'geojson',
      data: {
        type: 'FeatureCollection',
        features: riskData.map(risk => ({
          type: 'Feature',
          properties: {
            risk_level: risk.risk_level
          },
          geometry: {
            type: 'Point',
            coordinates: [risk.longitude, risk.latitude]
          }
        }))
      }
    });

    // Add heatmap layer
    map.current.addLayer({
      id: 'risk-heatmap-layer',
      type: 'heatmap',
      source: 'risk-heatmap',
      maxzoom: 9,
      paint: {
        // Increase weight as risk level increases
        'heatmap-weight': [
          'interpolate',
          ['linear'],
          ['get', 'risk_level'],
          0, 0,
          1, 1
        ],
        // Increase intensity as zoom level increases
        'heatmap-intensity': [
          'interpolate',
          ['linear'],
          ['zoom'],
          0, 1,
          9, 3
        ],
        // Color ramp for heatmap
        'heatmap-color': [
          'interpolate',
          ['linear'],
          ['heatmap-density'],
          0, 'rgba(33,102,172,0)',
          0.2, 'rgb(103,169,207)',
          0.4, 'rgb(209,229,240)',
          0.6, 'rgb(253,219,199)',
          0.8, 'rgb(239,138,98)',
          1, 'rgb(178,24,43)'
        ],
        // Adjust radius by zoom level
        'heatmap-radius': [
          'interpolate',
          ['linear'],
          ['zoom'],
          0, 20,
          9, 40
        ],
        // Fade out heatmap as we zoom in
        'heatmap-opacity': [
          'interpolate',
          ['linear'],
          ['zoom'],
          7, 1,
          9, 0
        ]
      }
    });
  };

  return (
    <div style={{ position: 'relative', width: '100%', height }}>
      <div ref={mapContainer} style={{ width: '100%', height: '100%' }} />

      {/* Legend */}
      <div style={{
        position: 'absolute',
        bottom: '30px',
        left: '10px',
        backgroundColor: 'white',
        padding: '15px',
        borderRadius: '8px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.2)',
        zIndex: 1
      }}>
        <h4 style={{ margin: '0 0 10px 0', fontSize: '14px', fontWeight: 'bold' }}>
          Risk Level
        </h4>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{
              width: '20px',
              height: '20px',
              borderRadius: '50%',
              backgroundColor: '#DC2626'
            }} />
            <span style={{ fontSize: '12px' }}>Critical (75-100%)</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{
              width: '20px',
              height: '20px',
              borderRadius: '50%',
              backgroundColor: '#EA580C'
            }} />
            <span style={{ fontSize: '12px' }}>High (50-75%)</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{
              width: '20px',
              height: '20px',
              borderRadius: '50%',
              backgroundColor: '#F59E0B'
            }} />
            <span style={{ fontSize: '12px' }}>Medium (30-50%)</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{
              width: '20px',
              height: '20px',
              borderRadius: '50%',
              backgroundColor: '#10B981'
            }} />
            <span style={{ fontSize: '12px' }}>Low (0-30%)</span>
          </div>
        </div>
      </div>

      {/* Event Counter */}
      {riskData.length > 0 && (
        <div style={{
          position: 'absolute',
          top: '10px',
          left: '10px',
          backgroundColor: 'rgba(0,0,0,0.7)',
          color: 'white',
          padding: '10px 15px',
          borderRadius: '8px',
          fontSize: '14px',
          fontWeight: 'bold'
        }}>
          {riskData.length} Risk Zone{riskData.length !== 1 ? 's' : ''}
        </div>
      )}
    </div>
  );
};

export default FMRiskMap;
