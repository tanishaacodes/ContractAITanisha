/**
 * Supply Chain Route Map - Interactive Supply Chain Visualization
 * Shows ports, routes, disruptions, and alternative paths
 */

import React, { useEffect, useRef, useState } from 'react';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';

mapboxgl.accessToken = import.meta.env.VITE_MAPBOX_TOKEN || "";

const SupplyChainRouteMap = ({
  ports = [],
  routes = [],
  disruptions = [],
  suppliers = [],
  center = [20, 20],
  zoom = 2,
  height = '600px',
  showAlternatives = true
}) => {
  const mapContainer = useRef(null);
  const map = useRef(null);
  const [selectedRoute, setSelectedRoute] = useState(null);

  useEffect(() => {
    if (map.current) return;

    map.current = new mapboxgl.Map({
      container: mapContainer.current,
      style: 'mapbox://styles/mapbox/light-v11',
      center: center,
      zoom: zoom,
      projection: 'mercator'
    });

    map.current.addControl(new mapboxgl.NavigationControl(), 'top-right');
    map.current.addControl(new mapboxgl.FullscreenControl(), 'top-right');

    map.current.on('load', () => {
      addSupplyChainLayers();
    });

    return () => {
      if (map.current) {
        map.current.remove();
      }
    };
  }, []);

  useEffect(() => {
    if (!map.current || !map.current.loaded()) return;

    updateSupplyChainData();
  }, [ports, routes, disruptions, suppliers]);

  const addSupplyChainLayers = () => {
    // Add route lines source
    map.current.addSource('routes', {
      type: 'geojson',
      data: createRoutesGeoJSON()
    });

    // Add primary routes layer
    map.current.addLayer({
      id: 'primary-routes',
      type: 'line',
      source: 'routes',
      filter: ['==', ['get', 'type'], 'primary'],
      paint: {
        'line-color': [
          'case',
          ['==', ['get', 'status'], 'disrupted'],
          '#DC2626',
          ['==', ['get', 'status'], 'warning'],
          '#F59E0B',
          '#3B82F6'
        ],
        'line-width': 4,
        'line-opacity': 0.8
      }
    });

    // Add alternative routes layer
    if (showAlternatives) {
      map.current.addLayer({
        id: 'alternative-routes',
        type: 'line',
        source: 'routes',
        filter: ['==', ['get', 'type'], 'alternative'],
        paint: {
          'line-color': '#10B981',
          'line-width': 2,
          'line-dasharray': [2, 2],
          'line-opacity': 0.6
        }
      });
    }

    // Add click handlers
    map.current.on('click', 'primary-routes', handleRouteClick);
    map.current.on('click', 'alternative-routes', handleRouteClick);

    // Change cursor on hover
    map.current.on('mouseenter', 'primary-routes', () => {
      map.current.getCanvas().style.cursor = 'pointer';
    });
    map.current.on('mouseleave', 'primary-routes', () => {
      map.current.getCanvas().style.cursor = '';
    });

    // Add ports as markers
    addPortMarkers();

    // Add disruption markers
    addDisruptionMarkers();

    // Add supplier markers
    addSupplierMarkers();
  };

  const createRoutesGeoJSON = () => {
    const features = routes.map(route => ({
      type: 'Feature',
      properties: {
        id: route.id,
        name: route.name,
        type: route.is_alternative ? 'alternative' : 'primary',
        status: route.status || 'normal',
        distance_km: route.distance_km,
        transit_time_days: route.transit_time_days,
        cost_factor: route.cost_factor
      },
      geometry: {
        type: 'LineString',
        coordinates: route.coordinates
      }
    }));

    return {
      type: 'FeatureCollection',
      features
    };
  };

  const updateSupplyChainData = () => {
    if (!map.current || !map.current.getSource('routes')) return;

    map.current.getSource('routes').setData(createRoutesGeoJSON());
  };

  const addPortMarkers = () => {
    ports.forEach(port => {
      const el = document.createElement('div');
      el.className = 'port-marker';
      el.style.width = '30px';
      el.style.height = '30px';
      el.style.backgroundImage = 'url(/icons/port-icon.png)';
      el.style.backgroundSize = 'contain';
      el.style.cursor = 'pointer';

      // If no icon, use colored circle
      if (!el.style.backgroundImage) {
        el.style.backgroundColor = '#3B82F6';
        el.style.borderRadius = '50%';
        el.style.border = '3px solid white';
        el.style.boxShadow = '0 2px 6px rgba(0,0,0,0.3)';
      }

      const marker = new mapboxgl.Marker(el)
        .setLngLat([port.longitude, port.latitude])
        .setPopup(
          new mapboxgl.Popup({ offset: 25 })
            .setHTML(`
              <div style="padding: 10px; min-width: 200px;">
                <h3 style="margin: 0 0 8px 0; color: #1F2937;">⚓ ${port.name}</h3>
                <div style="font-size: 12px; color: #6B7280; margin-bottom: 5px;">
                  <strong>Country:</strong> ${port.country}
                </div>
                <div style="font-size: 12px; color: #6B7280; margin-bottom: 5px;">
                  <strong>Status:</strong>
                  <span style="color: ${port.status === 'operational' ? '#10B981' : '#DC2626'}; font-weight: bold;">
                    ${port.status || 'operational'}
                  </span>
                </div>
                ${port.congestion_level ? `
                  <div style="font-size: 12px; color: #6B7280; margin-bottom: 5px;">
                    <strong>Congestion:</strong> ${(port.congestion_level * 100).toFixed(0)}%
                  </div>
                ` : ''}
                ${port.routes_count ? `
                  <div style="font-size: 12px; color: #6B7280;">
                    <strong>Active Routes:</strong> ${port.routes_count}
                  </div>
                ` : ''}
              </div>
            `)
        )
        .addTo(map.current);
    });
  };

  const addDisruptionMarkers = () => {
    disruptions.forEach(disruption => {
      const el = document.createElement('div');
      el.className = 'disruption-marker';
      el.innerHTML = '⚠️';
      el.style.fontSize = '24px';
      el.style.cursor = 'pointer';
      el.style.animation = 'pulse 2s infinite';

      const marker = new mapboxgl.Marker(el)
        .setLngLat([disruption.longitude, disruption.latitude])
        .setPopup(
          new mapboxgl.Popup({ offset: 25 })
            .setHTML(`
              <div style="padding: 10px; min-width: 220px;">
                <h3 style="margin: 0 0 8px 0; color: #DC2626;">⚠️ ${disruption.type}</h3>
                <div style="font-size: 12px; color: #6B7280; margin-bottom: 5px;">
                  <strong>Location:</strong> ${disruption.location}
                </div>
                <div style="font-size: 12px; color: #6B7280; margin-bottom: 5px;">
                  <strong>Severity:</strong>
                  <span style="color: #DC2626; font-weight: bold;">
                    ${(disruption.severity * 100).toFixed(0)}%
                  </span>
                </div>
                <div style="font-size: 12px; color: #6B7280; margin-bottom: 5px;">
                  <strong>Impact:</strong> ${disruption.impact || 'Unknown'}
                </div>
                ${disruption.duration_estimate ? `
                  <div style="font-size: 12px; color: #6B7280;">
                    <strong>Est. Duration:</strong> ${disruption.duration_estimate}
                  </div>
                ` : ''}
              </div>
            `)
        )
        .addTo(map.current);
    });

    // Add pulsing animation CSS
    const style = document.createElement('style');
    style.textContent = `
      @keyframes pulse {
        0%, 100% { transform: scale(1); opacity: 1; }
        50% { transform: scale(1.2); opacity: 0.8; }
      }
    `;
    document.head.appendChild(style);
  };

  const addSupplierMarkers = () => {
    suppliers.forEach(supplier => {
      const el = document.createElement('div');
      el.className = 'supplier-marker';
      el.innerHTML = '🏭';
      el.style.fontSize = '20px';
      el.style.cursor = 'pointer';

      const marker = new mapboxgl.Marker(el)
        .setLngLat([supplier.longitude, supplier.latitude])
        .setPopup(
          new mapboxgl.Popup({ offset: 25 })
            .setHTML(`
              <div style="padding: 10px; min-width: 200px;">
                <h3 style="margin: 0 0 8px 0; color: #1F2937;">🏭 ${supplier.name}</h3>
                <div style="font-size: 12px; color: #6B7280; margin-bottom: 5px;">
                  <strong>Type:</strong> ${supplier.type || 'Supplier'}
                </div>
                <div style="font-size: 12px; color: #6B7280; margin-bottom: 5px;">
                  <strong>Criticality:</strong>
                  <span style="color: ${supplier.criticality >= 0.7 ? '#DC2626' : '#F59E0B'}; font-weight: bold;">
                    ${(supplier.criticality * 100).toFixed(0)}%
                  </span>
                </div>
                ${supplier.alternatives_count ? `
                  <div style="font-size: 12px; color: #6B7280;">
                    <strong>Alternatives:</strong> ${supplier.alternatives_count}
                  </div>
                ` : ''}
              </div>
            `)
        )
        .addTo(map.current);
    });
  };

  const handleRouteClick = (e) => {
    const feature = e.features[0];
    const route = feature.properties;

    setSelectedRoute(route);

    // Highlight selected route
    map.current.setPaintProperty('primary-routes', 'line-width', [
      'case',
      ['==', ['get', 'id'], route.id],
      6,
      4
    ]);

    // Show route details popup
    new mapboxgl.Popup()
      .setLngLat(e.lngLat)
      .setHTML(`
        <div style="padding: 10px; min-width: 220px;">
          <h3 style="margin: 0 0 8px 0; color: #1F2937;">
            ${route.type === 'alternative' ? '🔄 Alternative Route' : '🚢 Primary Route'}
          </h3>
          <div style="font-size: 12px; color: #6B7280; margin-bottom: 5px;">
            <strong>Name:</strong> ${route.name}
          </div>
          <div style="font-size: 12px; color: #6B7280; margin-bottom: 5px;">
            <strong>Distance:</strong> ${route.distance_km?.toLocaleString() || 'N/A'} km
          </div>
          <div style="font-size: 12px; color: #6B7280; margin-bottom: 5px;">
            <strong>Transit Time:</strong> ${route.transit_time_days || 'N/A'} days
          </div>
          <div style="font-size: 12px; color: #6B7280; margin-bottom: 5px;">
            <strong>Cost Factor:</strong> ${route.cost_factor ? `${route.cost_factor}x` : 'Standard'}
          </div>
          <div style="font-size: 12px; margin-top: 8px;">
            <strong>Status:</strong>
            <span style="color: ${
              route.status === 'disrupted' ? '#DC2626' :
              route.status === 'warning' ? '#F59E0B' :
              '#10B981'
            }; font-weight: bold; text-transform: capitalize;">
              ${route.status || 'normal'}
            </span>
          </div>
        </div>
      `)
      .addTo(map.current);
  };

  return (
    <div style={{ position: 'relative', width: '100%', height }}>
      <div ref={mapContainer} style={{ width: '100%', height: '100%' }} />

      {/* Legend */}
      <div style={{
        position: 'absolute',
        bottom: '20px',
        right: '10px',
        backgroundColor: 'white',
        padding: '15px',
        borderRadius: '8px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.2)',
        zIndex: 1,
        maxWidth: '200px'
      }}>
        <h4 style={{ margin: '0 0 10px 0', fontSize: '14px', fontWeight: 'bold' }}>
          Legend
        </h4>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{ width: '20px', height: '3px', backgroundColor: '#3B82F6' }} />
            <span>Primary Route</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{ width: '20px', height: '3px', backgroundColor: '#DC2626' }} />
            <span>Disrupted</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{ width: '20px', height: '2px', backgroundColor: '#10B981', borderTop: '2px dashed #10B981' }} />
            <span>Alternative</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span>⚓</span>
            <span>Port</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span>🏭</span>
            <span>Supplier</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span>⚠️</span>
            <span>Disruption</span>
          </div>
        </div>
      </div>

      {/* Statistics */}
      <div style={{
        position: 'absolute',
        top: '10px',
        left: '10px',
        backgroundColor: 'rgba(255,255,255,0.95)',
        padding: '15px',
        borderRadius: '8px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
        fontSize: '12px'
      }}>
        <div style={{ marginBottom: '8px' }}>
          <strong>Routes:</strong> {routes.length}
        </div>
        <div style={{ marginBottom: '8px' }}>
          <strong>Ports:</strong> {ports.length}
        </div>
        <div style={{ marginBottom: '8px' }}>
          <strong>Suppliers:</strong> {suppliers.length}
        </div>
        <div style={{ color: '#DC2626', fontWeight: 'bold' }}>
          <strong>Disruptions:</strong> {disruptions.length}
        </div>
      </div>
    </div>
  );
};

export default SupplyChainRouteMap;
