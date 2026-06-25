import React, { useRef, useEffect, useState, useCallback } from 'react';
import ForceGraph3D from 'react-force-graph-3d';
import * as THREE from 'three';
import SpriteText from 'three-spritetext';
import {
  Box,
  Paper,
  Typography,
  Chip,
  Card,
  CardContent,
  Grid,
  Slider,
  FormControlLabel,
  Switch,
  Button,
  ButtonGroup,
  IconButton,
  Tooltip,
} from '@mui/material';
import FullscreenIcon from '@mui/icons-material/Fullscreen';
import FullscreenExitIcon from '@mui/icons-material/FullscreenExit';

/**
 * Enterprise 3D Risk Intelligence Graph
 *
 * Advanced Features:
 * - Layered 3D positioning (8 risk layers in concentric spheres)
 * - Glow effects for high-risk nodes
 * - Animated particle flow showing risk propagation
 * - Dynamic node sizing based on criticality
 * - Interactive hover with real-time analytics
 * - Professional color-coded risk visualization
 */
const RiskGraph3D = ({ graphData, onNodeClick, selectedNode }) => {
  const fgRef = useRef();
  const [highlightNodes, setHighlightNodes] = useState(new Set());
  const [highlightLinks, setHighlightLinks] = useState(new Set());
  const [hoverNode, setHoverNode] = useState(null);
  const [particleSpeed, setParticleSpeed] = useState(0.008);
  const [showParticles, setShowParticles] = useState(true);
  const [graphDistance, setGraphDistance] = useState(1200);
  const [layoutMode, setLayoutMode] = useState('spherical'); // spherical, hierarchical, force
  const [showLabels, setShowLabels] = useState(true);
  const [rotationSpeed, setRotationSpeed] = useState(0.002);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [graphKey, setGraphKey] = useState(0);

  // Enhanced color scheme with gradients
  const getRiskColor = (probability) => {
    if (probability >= 0.7) return '#ef4444'; // Red - Critical
    if (probability >= 0.5) return '#f97316'; // Orange - High
    if (probability >= 0.3) return '#f59e0b'; // Amber - Medium-High
    if (probability >= 0.15) return '#eab308'; // Yellow - Medium
    return '#10b981'; // Green - Low
  };

  const getClusterColor = (cluster) => {
    const colors = {
      geopolitical: '#dc2626',
      macroeconomic: '#ea580c',
      market: '#8b5cf6',
      supply_chain: '#0ea5e9',
      financial: '#10b981',
      operational: '#f59e0b',
      contract: '#3b82f6',
      legal_outcome: '#a855f7',
    };
    return colors[cluster] || '#6366f1';
  };

  // Advanced 3D node rendering with glow effects
  const nodeThreeObject = useCallback((node) => {
    const group = new THREE.Group();

    // Main sphere with gradient material
    const radius = 8 + (node.base_probability || 0.1) * 15;
    const geometry = new THREE.SphereGeometry(radius, 32, 32);

    const color = new THREE.Color(getRiskColor(node.base_probability || 0.1));
    const material = new THREE.MeshPhongMaterial({
      color: color,
      emissive: color,
      emissiveIntensity: node.base_probability >= 0.5 ? 0.5 : 0.2,
      shininess: 100,
      transparent: true,
      opacity: 0.9,
    });

    const sphere = new THREE.Mesh(geometry, material);
    group.add(sphere);

    // Glow effect for high-risk nodes
    if (node.base_probability >= 0.5) {
      const glowGeometry = new THREE.SphereGeometry(radius * 1.3, 32, 32);
      const glowMaterial = new THREE.MeshBasicMaterial({
        color: color,
        transparent: true,
        opacity: 0.2,
      });
      const glow = new THREE.Mesh(glowGeometry, glowMaterial);
      group.add(glow);
    }

    // Ring indicator for critical nodes
    if (node.base_probability >= 0.7) {
      const ringGeometry = new THREE.TorusGeometry(radius * 1.5, 1, 16, 100);
      const ringMaterial = new THREE.MeshBasicMaterial({
        color: '#ffffff',
        transparent: true,
        opacity: 0.6,
      });
      const ring = new THREE.Mesh(ringGeometry, ringMaterial);
      ring.rotation.x = Math.PI / 2;
      group.add(ring);
    }

    // Text label
    if (showLabels) {
      const sprite = new SpriteText(node.label);
      sprite.color = '#ffffff';
      sprite.textHeight = 6;
      sprite.backgroundColor = 'rgba(0, 0, 0, 0.8)';
      sprite.padding = 3;
      sprite.borderRadius = 4;
      sprite.position.y = radius + 10;
      group.add(sprite);
    }

    return group;
  }, [showLabels]);

  // Enhanced node positioning based on layout mode
  useEffect(() => {
    if (!fgRef.current || !graphData?.nodes) return;

    const nodes = graphData.nodes;

    if (layoutMode === 'spherical') {
      // Organize nodes in concentric spheres by layer
      nodes.forEach((node) => {
        const layer = node.layer || 1;
        const radius = 200 + (layer - 1) * 150; // Larger spacing between layers

        // Distribute nodes evenly around the sphere for this layer
        const layerNodes = nodes.filter(n => n.layer === layer);
        const index = layerNodes.indexOf(node);
        const phi = Math.acos(-1 + (2 * index) / layerNodes.length);
        const theta = Math.sqrt(layerNodes.length * Math.PI) * phi;

        node.fx = radius * Math.cos(theta) * Math.sin(phi);
        node.fy = radius * Math.sin(theta) * Math.sin(phi);
        node.fz = radius * Math.cos(phi);
      });
    } else if (layoutMode === 'hierarchical') {
      // Vertical layers
      nodes.forEach((node) => {
        const layer = node.layer || 1;
        const layerNodes = nodes.filter(n => n.layer === layer);
        const index = layerNodes.indexOf(node);
        const angleStep = (2 * Math.PI) / layerNodes.length;

        node.fx = 300 * Math.cos(index * angleStep);
        node.fy = (layer - 4.5) * 200; // Center around middle
        node.fz = 300 * Math.sin(index * angleStep);
      });
    } else {
      // Force-directed (release fixed positions)
      nodes.forEach(node => {
        delete node.fx;
        delete node.fy;
        delete node.fz;
      });
    }

    // Refresh the graph to apply new positions
    if (fgRef.current) {
      // Re-heat simulation for force layout
      if (layoutMode === 'force') {
        fgRef.current.d3ReheatSimulation();
      }
    }

    // Force re-render by updating key
    setGraphKey(prev => prev + 1);
  }, [layoutMode, graphData]);

  // Node color with highlight effects
  const nodeColor = useCallback((node) => {
    if (selectedNode && selectedNode.node_id === node.node_id) {
      return '#ffffff';
    }
    if (highlightNodes.has(node.node_id)) {
      return '#fbbf24';
    }
    return getRiskColor(node.base_probability || 0.1);
  }, [selectedNode, highlightNodes]);

  // Enhanced link rendering with clearer visibility
  const linkColor = useCallback((link) => {
    if (highlightLinks.has(`${link.source}-${link.target}`)) {
      return 'rgba(251, 191, 36, 0.9)';
    }
    // Use brighter colors based on conditional probability
    const prob = link.conditional_probability || 0.5;
    if (prob >= 0.7) return 'rgba(239, 68, 68, 0.7)'; // Red for high probability
    if (prob >= 0.5) return 'rgba(249, 115, 22, 0.7)'; // Orange
    if (prob >= 0.3) return 'rgba(6, 182, 212, 0.7)'; // Cyan
    return 'rgba(148, 163, 184, 0.6)'; // Lighter gray
  }, [highlightLinks]);

  const linkWidth = useCallback((link) => {
    const base = highlightLinks.has(`${link.source}-${link.target}`) ? 5 : 2;
    return base * (link.conditional_probability || 0.5);
  }, [highlightLinks]);

  // Animated particles showing risk flow with enhanced visibility
  const linkDirectionalParticles = useCallback((link) => {
    if (!showParticles) return 0;
    return Math.ceil((link.conditional_probability || 0.5) * 6); // More particles
  }, [showParticles]);

  const linkDirectionalParticleSpeed = useCallback((link) => {
    return (link.conditional_probability || 0.5) * particleSpeed;
  }, [particleSpeed]);

  const linkDirectionalParticleWidth = useCallback((link) => {
    // Larger particles with size based on risk probability
    const prob = link.conditional_probability || 0.5;
    return 4 + prob * 4; // Range: 4-8
  }, []);

  const linkDirectionalParticleColor = useCallback((link) => {
    // Color particles based on risk level for clear identification
    const prob = link.conditional_probability || 0.5;
    if (prob >= 0.7) return '#ef4444'; // Red
    if (prob >= 0.5) return '#f97316'; // Orange
    if (prob >= 0.3) return '#06b6d4'; // Cyan
    return '#94a3b8'; // Gray
  }, []);

  // Node click handler with path highlighting
  const handleNodeClick = useCallback((node) => {
    if (onNodeClick) onNodeClick(node);

    const connectedNodeIds = new Set();
    const connectedLinkIds = new Set();

    graphData?.links?.forEach(link => {
      const sourceId = link.source?.node_id || link.source_node_id || link.source;
      const targetId = link.target?.node_id || link.target_node_id || link.target;

      if (sourceId === node.node_id) {
        connectedNodeIds.add(targetId);
        connectedLinkIds.add(`${sourceId}-${targetId}`);
      }
      if (targetId === node.node_id) {
        connectedNodeIds.add(sourceId);
        connectedLinkIds.add(`${sourceId}-${targetId}`);
      }
    });

    setHighlightNodes(connectedNodeIds);
    setHighlightLinks(connectedLinkIds);
  }, [graphData, onNodeClick]);

  const handleNodeHover = useCallback((node) => {
    setHoverNode(node);
  }, []);

  // Fullscreen toggle handler
  const toggleFullscreen = useCallback(() => {
    const element = document.getElementById('risk-graph-3d-container');

    if (!document.fullscreenElement) {
      element.requestFullscreen().then(() => {
        setIsFullscreen(true);
      }).catch(err => {
        console.error('Error attempting to enable fullscreen:', err);
      });
    } else {
      document.exitFullscreen().then(() => {
        setIsFullscreen(false);
      });
    }
  }, []);

  // Listen for fullscreen changes (e.g., user pressing ESC)
  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };

    document.addEventListener('fullscreenchange', handleFullscreenChange);
    return () => document.removeEventListener('fullscreenchange', handleFullscreenChange);
  }, []);

  // Auto-rotation with adjustable speed
  useEffect(() => {
    if (!fgRef.current) return;

    fgRef.current.cameraPosition({ z: graphDistance });

    let angle = 0;
    const interval = setInterval(() => {
      if (fgRef.current && rotationSpeed > 0) {
        angle += rotationSpeed;
        const distance = graphDistance;
        fgRef.current.cameraPosition({
          x: distance * Math.sin(angle),
          z: distance * Math.cos(angle),
        });
      }
    }, 50);

    return () => clearInterval(interval);
  }, [graphDistance, rotationSpeed]);

  return (
    <Box id="risk-graph-3d-container" sx={{ position: 'relative', bgcolor: isFullscreen ? '#020617' : 'transparent' }}>
      {/* Advanced Controls Panel */}
      <Paper
        elevation={0}
        sx={{
          p: 3,
          mb: 2,
          bgcolor: '#0f172a',
          border: '1px solid #1e293b',
          borderRadius: '12px'
        }}
      >
        <Grid container spacing={3} alignItems="center">
          {/* Layout Mode Selector with Fullscreen Button */}
          <Grid container item xs={12} sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Box sx={{ display: 'flex', flexDirection: 'column', flex: 1 }}>
              <Typography variant="body2" sx={{ color: '#94a3b8', fontSize: '13px', mb: 1 }}>
                Layout Mode
              </Typography>
              <ButtonGroup variant="outlined" size="small">
                {['spherical', 'hierarchical', 'force'].map(mode => (
                  <Button
                    key={mode}
                    onClick={() => setLayoutMode(mode)}
                    sx={{
                      bgcolor: layoutMode === mode ? '#06b6d4' : 'transparent',
                      color: layoutMode === mode ? '#fff' : '#94a3b8',
                      borderColor: '#334155',
                      textTransform: 'capitalize',
                      fontSize: '12px',
                      '&:hover': {
                        bgcolor: layoutMode === mode ? '#0891b2' : '#1e293b',
                        borderColor: '#334155',
                      }
                    }}
                  >
                    {mode}
                  </Button>
                ))}
              </ButtonGroup>
            </Box>
            <Tooltip title={isFullscreen ? 'Exit Fullscreen' : 'Enter Fullscreen'}>
              <IconButton
                onClick={toggleFullscreen}
                sx={{
                  bgcolor: '#1e293b',
                  color: '#06b6d4',
                  border: '1px solid #334155',
                  '&:hover': {
                    bgcolor: '#334155',
                    color: '#06b6d4',
                  },
                  ml: 2,
                }}
              >
                {isFullscreen ? <FullscreenExitIcon /> : <FullscreenIcon />}
              </IconButton>
            </Tooltip>
          </Grid>

          <Grid container item xs={12} md={3}>
            <Typography variant="body2" gutterBottom sx={{ color: '#94a3b8', fontSize: '13px' }}>
              Particle Speed: {(particleSpeed * 1000).toFixed(0)}x
            </Typography>
            <Slider
              value={particleSpeed * 1000}
              onChange={(e, val) => setParticleSpeed(val / 1000)}
              min={1}
              max={30}
              step={1}
              valueLabelDisplay="auto"
              valueLabelFormat={(val) => `${val}x`}
              sx={{
                color: '#06b6d4',
                '& .MuiSlider-thumb': { bgcolor: '#06b6d4' },
                '& .MuiSlider-track': { bgcolor: '#06b6d4' },
                '& .MuiSlider-rail': { bgcolor: '#334155' },
              }}
            />
          </Grid>

          <Grid container item xs={12} md={3}>
            <Typography variant="body2" gutterBottom sx={{ color: '#94a3b8', fontSize: '13px' }}>
              Camera Distance: {graphDistance}
            </Typography>
            <Slider
              value={graphDistance}
              onChange={(e, val) => setGraphDistance(val)}
              min={400}
              max={2000}
              step={100}
              valueLabelDisplay="auto"
              sx={{
                color: '#06b6d4',
                '& .MuiSlider-thumb': { bgcolor: '#06b6d4' },
                '& .MuiSlider-track': { bgcolor: '#06b6d4' },
                '& .MuiSlider-rail': { bgcolor: '#334155' },
              }}
            />
          </Grid>

          <Grid container item xs={12} md={3}>
            <Typography variant="body2" gutterBottom sx={{ color: '#94a3b8', fontSize: '13px' }}>
              Rotation Speed: {(rotationSpeed * 1000).toFixed(1)}x
            </Typography>
            <Slider
              value={rotationSpeed * 1000}
              onChange={(e, val) => setRotationSpeed(val / 1000)}
              min={0}
              max={10}
              step={0.5}
              valueLabelDisplay="auto"
              valueLabelFormat={(val) => `${val}x`}
              sx={{
                color: '#06b6d4',
                '& .MuiSlider-thumb': { bgcolor: '#06b6d4' },
                '& .MuiSlider-track': { bgcolor: '#06b6d4' },
                '& .MuiSlider-rail': { bgcolor: '#334155' },
              }}
            />
          </Grid>

          <Grid container item xs={12} md={3}>
            <FormControlLabel
              control={
                <Switch
                  checked={showParticles}
                  onChange={(e) => setShowParticles(e.target.checked)}
                  sx={{
                    '& .MuiSwitch-switchBase.Mui-checked': { color: '#06b6d4' },
                    '& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track': { backgroundColor: '#06b6d4' },
                  }}
                />
              }
              label="Risk Flow Animation"
              sx={{ color: '#e2e8f0', '& .MuiFormControlLabel-label': { fontSize: '13px' } }}
            />
            <FormControlLabel
              control={
                <Switch
                  checked={showLabels}
                  onChange={(e) => setShowLabels(e.target.checked)}
                  sx={{
                    '& .MuiSwitch-switchBase.Mui-checked': { color: '#06b6d4' },
                    '& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track': { backgroundColor: '#06b6d4' },
                  }}
                />
              }
              label="Show Labels"
              sx={{ color: '#e2e8f0', '& .MuiFormControlLabel-label': { fontSize: '13px' } }}
            />
          </Grid>
        </Grid>

        {/* Enhanced Legend */}
        <Box sx={{ mt: 3, pt: 2, borderTop: '1px solid #1e293b' }}>
          <Typography variant="body2" gutterBottom sx={{ color: '#cbd5e1', fontSize: '13px', fontWeight: 600, mb: 1.5 }}>
            Risk Intelligence Legend
          </Typography>
          <Grid container spacing={2}>
            <Grid container item xs={12} md={6}>
              <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                <Chip label="Low (< 15%)" size="small" sx={{ bgcolor: '#10b981', color: 'white', fontSize: '11px', fontWeight: 600 }} />
                <Chip label="Medium (15-30%)" size="small" sx={{ bgcolor: '#eab308', color: 'black', fontSize: '11px', fontWeight: 600 }} />
                <Chip label="Medium-High (30-50%)" size="small" sx={{ bgcolor: '#f59e0b', color: 'white', fontSize: '11px', fontWeight: 600 }} />
                <Chip label="High (50-70%)" size="small" sx={{ bgcolor: '#f97316', color: 'white', fontSize: '11px', fontWeight: 600 }} />
                <Chip label="Critical (> 70%)" size="small" sx={{ bgcolor: '#ef4444', color: 'white', fontSize: '11px', fontWeight: 600 }} />
              </Box>
            </Grid>
            <Grid container item xs={12} md={6}>
              <Typography variant="body2" sx={{ color: '#64748b', fontSize: '11px', mb: 1 }}>
                <strong style={{ color: '#cbd5e1' }}>Nodes:</strong> Size = Risk probability | Glow = High risk (&gt;50%) | Ring = Critical (&gt;70%)
              </Typography>
              <Typography variant="body2" sx={{ color: '#64748b', fontSize: '11px' }}>
                <strong style={{ color: '#cbd5e1' }}>Particles:</strong> Color & size indicate connection strength | Flow shows risk propagation direction
              </Typography>
            </Grid>
          </Grid>
        </Box>
      </Paper>

      {/* 3D Graph Container */}
      <Paper
        elevation={0}
        sx={{
          height: isFullscreen ? '100vh' : '800px',
          position: 'relative',
          overflow: 'hidden',
          bgcolor: '#020617',
          border: '1px solid #1e293b',
          borderRadius: isFullscreen ? '0' : '12px',
          backgroundImage: 'radial-gradient(circle at 50% 50%, rgba(6, 182, 212, 0.05) 0%, transparent 50%)',
        }}
      >
        <ForceGraph3D
          key={graphKey}
          ref={fgRef}
          graphData={graphData}
          nodeThreeObject={nodeThreeObject}
          nodeLabel={(node) => `
            <div style="background: linear-gradient(135deg, rgba(15, 23, 42, 0.95) 0%, rgba(30, 41, 59, 0.95) 100%);
                        padding: 12px; border-radius: 8px; color: white; border: 1px solid #334155;
                        box-shadow: 0 4px 20px rgba(0,0,0,0.5); min-width: 180px;">
              <div style="font-size: 14px; font-weight: 700; color: #f1f5f9; margin-bottom: 6px;">${node.label}</div>
              <div style="font-size: 11px; color: #94a3b8; margin-bottom: 4px;">
                <strong style="color: #cbd5e1;">Cluster:</strong> ${node.cluster}
              </div>
              <div style="font-size: 11px; color: #94a3b8; margin-bottom: 4px;">
                <strong style="color: #cbd5e1;">Layer:</strong> ${node.layer}/8
              </div>
              <div style="font-size: 11px; color: #94a3b8; margin-bottom: 6px;">
                <strong style="color: #cbd5e1;">Risk:</strong> ${((node.base_probability || 0.1) * 100).toFixed(1)}%
              </div>
              <div style="background: ${getRiskColor(node.base_probability || 0.1)};
                          color: white; padding: 3px 8px; border-radius: 4px;
                          font-size: 10px; font-weight: 700; text-align: center;">
                ${node.base_probability >= 0.7 ? 'CRITICAL RISK' : node.base_probability >= 0.5 ? 'HIGH RISK' : node.base_probability >= 0.3 ? 'MEDIUM-HIGH' : node.base_probability >= 0.15 ? 'MEDIUM' : 'LOW RISK'}
              </div>
            </div>
          `}
          linkColor={linkColor}
          linkWidth={linkWidth}
          linkDirectionalParticles={linkDirectionalParticles}
          linkDirectionalParticleSpeed={linkDirectionalParticleSpeed}
          linkDirectionalParticleWidth={linkDirectionalParticleWidth}
          linkDirectionalParticleColor={linkDirectionalParticleColor}
          linkDirectionalArrowLength={6}
          linkDirectionalArrowRelPos={1}
          linkCurvature={0.2}
          linkOpacity={0.8}
          onNodeClick={handleNodeClick}
          onNodeHover={handleNodeHover}
          backgroundColor="#020617"
          showNavInfo={false}
          enableNodeDrag={layoutMode === 'force'}
          enableNavigationControls={true}
          controlType="orbit"
          d3AlphaDecay={0.01}
          d3VelocityDecay={0.2}
          d3Force="charge"
          warmupTicks={100}
          cooldownTicks={0}
        />

        {/* Enhanced Hover Info Card */}
        {hoverNode && (
          <Card
            sx={{
              position: 'absolute',
              top: 16,
              right: 16,
              minWidth: 280,
              maxWidth: 380,
              bgcolor: 'rgba(15, 23, 42, 0.95)',
              color: '#e2e8f0',
              border: '1px solid #334155',
              borderRadius: '12px',
              backdropFilter: 'blur(20px)',
              boxShadow: '0 8px 32px rgba(0, 0, 0, 0.6)',
            }}
          >
            <CardContent sx={{ p: 2.5 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                <Typography variant="h6" sx={{ color: '#f1f5f9', fontSize: '17px', fontWeight: 800 }}>
                  {hoverNode.label}
                </Typography>
                <Box
                  sx={{
                    width: 12,
                    height: 12,
                    borderRadius: '50%',
                    bgcolor: getRiskColor(hoverNode.base_probability || 0.1),
                    boxShadow: `0 0 10px ${getRiskColor(hoverNode.base_probability || 0.1)}`,
                  }}
                />
              </Box>

              <Grid container spacing={1.5}>
                <Grid container item xs={6}>
                  <Typography variant="body2" sx={{ color: '#64748b', fontSize: '11px', mb: 0.5 }}>
                    Cluster
                  </Typography>
                  <Typography variant="body2" sx={{ color: '#cbd5e1', fontSize: '13px', fontWeight: 600 }}>
                    {hoverNode.cluster}
                  </Typography>
                </Grid>
                <Grid container item xs={6}>
                  <Typography variant="body2" sx={{ color: '#64748b', fontSize: '11px', mb: 0.5 }}>
                    Layer
                  </Typography>
                  <Typography variant="body2" sx={{ color: '#cbd5e1', fontSize: '13px', fontWeight: 600 }}>
                    {hoverNode.layer} / 8
                  </Typography>
                </Grid>
                <Grid container item xs={12}>
                  <Typography variant="body2" sx={{ color: '#64748b', fontSize: '11px', mb: 0.5 }}>
                    Risk Probability
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Box sx={{ flex: 1, height: 8, bgcolor: '#1e293b', borderRadius: 4, overflow: 'hidden' }}>
                      <Box
                        sx={{
                          width: `${(hoverNode.base_probability || 0.1) * 100}%`,
                          height: '100%',
                          bgcolor: getRiskColor(hoverNode.base_probability || 0.1),
                          transition: 'width 0.3s ease',
                        }}
                      />
                    </Box>
                    <Typography variant="body2" sx={{ color: '#f1f5f9', fontSize: '14px', fontWeight: 700 }}>
                      {((hoverNode.base_probability || 0.1) * 100).toFixed(1)}%
                    </Typography>
                  </Box>
                </Grid>
              </Grid>

              <Chip
                label={hoverNode.base_probability >= 0.7 ? 'CRITICAL RISK' : hoverNode.base_probability >= 0.5 ? 'HIGH RISK' : hoverNode.base_probability >= 0.3 ? 'MEDIUM-HIGH RISK' : hoverNode.base_probability >= 0.15 ? 'MEDIUM RISK' : 'LOW RISK'}
                size="small"
                sx={{
                  mt: 2,
                  width: '100%',
                  bgcolor: getRiskColor(hoverNode.base_probability || 0.1),
                  color: 'white',
                  fontSize: '11px',
                  fontWeight: 800,
                  letterSpacing: '0.5px',
                }}
              />
            </CardContent>
          </Card>
        )}

        {/* Graph Stats Overlay */}
        <Box
          sx={{
            position: 'absolute',
            bottom: 16,
            left: 16,
            bgcolor: 'rgba(15, 23, 42, 0.9)',
            border: '1px solid #334155',
            borderRadius: '8px',
            p: 1.5,
            backdropFilter: 'blur(10px)',
          }}
        >
          <Typography variant="body2" sx={{ color: '#64748b', fontSize: '10px', mb: 0.5 }}>
            INTELLIGENCE GRAPH
          </Typography>
          <Typography variant="body2" sx={{ color: '#e2e8f0', fontSize: '12px', fontWeight: 600 }}>
            {graphData?.nodes?.length || 0} Nodes • {graphData?.links?.length || 0} Edges
          </Typography>
        </Box>
      </Paper>
    </Box>
  );
};

export default RiskGraph3D;
