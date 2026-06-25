import { useState, useEffect, useMemo } from 'react';
import api from '../utils/api';
import {
  ScatterChart, Scatter, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Cell, ZAxis
} from 'recharts';
import { DollarSign, Users, AlertTriangle, TrendingUp, ChevronRight } from 'lucide-react';
import '../styles/CounterpartyPortfolioHeatmap.css';

const CounterpartyPortfolioHeatmap = () => {
  const [heatmapData, setHeatmapData] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedQuadrant, setSelectedQuadrant] = useState('ALL');

  useEffect(() => {
    fetchPortfolioHeatmap();
  }, []);

  const fetchPortfolioHeatmap = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await api.get('/counterparty/portfolio-heatmap');

      if (response.data.success) {
        setHeatmapData(response.data.data.heatmap_data);
        setSummary(response.data.data.summary);
      } else {
        throw new Error(response.data.error || 'Failed to load data');
      }
    } catch (err) {
      console.error('Error fetching portfolio heatmap:', err);
      setError(err.response?.data?.error || err.message);
    } finally {
      setLoading(false);
    }
  };

  const getQuadrantColor = (quadrant) => {
    const colors = {
      'IMMEDIATE_ACTION': '#ef4444',
      'MONITOR': '#f59e0b',
      'REVIEW': '#3b82f6',
      'SAFE': '#10b981'
    };
    return colors[quadrant] || '#6b7280';
  };

  const getQuadrantLabel = (quadrant) => {
    const labels = {
      'IMMEDIATE_ACTION': 'Immediate Action',
      'MONITOR': 'Monitor',
      'REVIEW': 'Review',
      'SAFE': 'Safe'
    };
    return labels[quadrant] || quadrant;
  };

  // Add jitter to spread overlapping points with force-based spacing
  const addJitter = (data) => {
    const seededRandom = (seed) => {
      const x = Math.sin(seed++) * 10000;
      return x - Math.floor(x);
    };

    // First pass: apply initial jitter
    let processed = data.map((item, index) => {
      const seed1 = index * 12345;
      const seed2 = index * 67890;

      // Much more aggressive jitter - ±20% horizontal, ±35% vertical
      const jitterX = (seededRandom(seed1) - 0.5) * 0.40;
      const jitterY = (seededRandom(seed2) - 0.5) * 0.70;

      const exposureBase = Math.max(1000, item.financial_exposure);

      return {
        ...item,
        reliability_score_display: Math.max(0, Math.min(1, item.reliability_score + jitterX)),
        financial_exposure_display: Math.max(0, item.financial_exposure + (jitterY * exposureBase))
      };
    });

    // Second pass: push apart points that are too close
    for (let i = 0; i < processed.length; i++) {
      for (let j = i + 1; j < processed.length; j++) {
        const dx = processed[i].reliability_score_display - processed[j].reliability_score_display;
        const dy = (processed[i].financial_exposure_display - processed[j].financial_exposure_display) /
                   Math.max(processed[i].financial_exposure_display, processed[j].financial_exposure_display, 1);

        const distance = Math.sqrt(dx * dx + dy * dy);

        // If points are too close, push them apart
        if (distance < 0.08) {
          const pushX = (dx / distance) * 0.04;
          const pushY = (dy / distance) * 0.04;

          processed[i].reliability_score_display = Math.max(0, Math.min(1,
            processed[i].reliability_score_display + pushX));
          processed[j].reliability_score_display = Math.max(0, Math.min(1,
            processed[j].reliability_score_display - pushX));

          const exposureI = Math.max(1000, processed[i].financial_exposure);
          const exposureJ = Math.max(1000, processed[j].financial_exposure);

          processed[i].financial_exposure_display = Math.max(0,
            processed[i].financial_exposure_display + (pushY * exposureI));
          processed[j].financial_exposure_display = Math.max(0,
            processed[j].financial_exposure_display - (pushY * exposureJ));
        }
      }
    }

    return processed;
  };

  // Memoize jittered data to prevent recalculation on every render (causes shaking)
  const jitteredData = useMemo(() => {
    return addJitter(heatmapData);
  }, [heatmapData]);

  const filteredData = selectedQuadrant === 'ALL'
    ? jitteredData
    : jitteredData.filter(d => d.quadrant === selectedQuadrant);

  const formatCurrency = (value) => {
    if (value >= 10000000) {
      return `Rs ${(value / 10000000).toFixed(2)} Cr`;
    } else if (value >= 100000) {
      return `Rs ${(value / 100000).toFixed(2)} L`;
    } else if (value >= 1000) {
      return `Rs ${(value / 1000).toFixed(1)}K`;
    }
    return `Rs ${value.toFixed(2)}`;
  };

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="custom-tooltip">
          <h4>{data.contract_name}</h4>
          <p><strong>Counterparty:</strong> {data.counterparty_name}</p>
          <p><strong>Reliability:</strong> {(data.reliability_score * 100).toFixed(1)}%</p>
          <p><strong>Exposure:</strong> {formatCurrency(data.financial_exposure)}</p>
          <p><strong>Failure Probability:</strong> {(data.failure_probability * 100).toFixed(1)}%</p>
          <p><strong>Industry:</strong> {data.industry}</p>
          <p className={`quadrant-badge ${data.quadrant.toLowerCase()}`}>
            {getQuadrantLabel(data.quadrant)}
          </p>
        </div>
      );
    }
    return null;
  };

  if (loading) {
    return (
      <div className="portfolio-heatmap-container">
        <div className="loading-state">
          <div className="spinner"></div>
          <p>Loading Portfolio Risk Heatmap...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="portfolio-heatmap-container">
        <div className="error-state">
          <AlertTriangle size={48} />
          <h3>Error Loading Heatmap</h3>
          <p>{error}</p>
          <button onClick={fetchPortfolioHeatmap} className="retry-button">
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="portfolio-heatmap-container">
      <div className="page-header">
        <div>
          <h1>Portfolio-Level Counterparty Risk Heatmap</h1>
          <p className="subtitle">Executive risk intelligence for CFO/CRO decision-making</p>
        </div>
        <button onClick={fetchPortfolioHeatmap} className="refresh-button">
          Refresh Data
        </button>
      </div>

      {summary && (
        <div className="summary-cards">
          <div className="summary-card">
            <div className="card-icon" style={{background: '#3b82f6'}}>
              <Users size={24} />
            </div>
            <div className="card-content">
              <p className="card-label">Total Counterparties</p>
              <h3>{summary.total_counterparties}</h3>
            </div>
          </div>

          <div className="summary-card">
            <div className="card-icon" style={{background: '#10b981'}}>
              <DollarSign size={24} />
            </div>
            <div className="card-content">
              <p className="card-label">Total Exposure</p>
              <h3>{formatCurrency(summary.total_exposure)}</h3>
            </div>
          </div>

          <div className="summary-card">
            <div className="card-icon" style={{background: '#ef4444'}}>
              <AlertTriangle size={24} />
            </div>
            <div className="card-content">
              <p className="card-label">High Risk</p>
              <h3>{summary.high_risk_count}</h3>
            </div>
          </div>

          <div className="summary-card">
            <div className="card-icon" style={{background: '#f59e0b'}}>
              <TrendingUp size={24} />
            </div>
            <div className="card-content">
              <p className="card-label">Avg Reliability</p>
              <h3>{(summary.avg_reliability * 100).toFixed(1)}%</h3>
            </div>
          </div>
        </div>
      )}

      <div className="filter-section">
        <label>Filter by Quadrant:</label>
        <div className="quadrant-filters">
          <button
            className={`filter-btn ${selectedQuadrant === 'ALL' ? 'active' : ''}`}
            onClick={() => setSelectedQuadrant('ALL')}
          >
            All ({heatmapData.length})
          </button>
          <button
            className={`filter-btn ${selectedQuadrant === 'IMMEDIATE_ACTION' ? 'active' : ''}`}
            onClick={() => setSelectedQuadrant('IMMEDIATE_ACTION')}
            style={{borderColor: '#ef4444'}}
          >
            Immediate Action ({heatmapData.filter(d => d.quadrant === 'IMMEDIATE_ACTION').length})
          </button>
          <button
            className={`filter-btn ${selectedQuadrant === 'MONITOR' ? 'active' : ''}`}
            onClick={() => setSelectedQuadrant('MONITOR')}
            style={{borderColor: '#f59e0b'}}
          >
            Monitor ({heatmapData.filter(d => d.quadrant === 'MONITOR').length})
          </button>
          <button
            className={`filter-btn ${selectedQuadrant === 'SAFE' ? 'active' : ''}`}
            onClick={() => setSelectedQuadrant('SAFE')}
            style={{borderColor: '#10b981'}}
          >
            Safe ({heatmapData.filter(d => d.quadrant === 'SAFE').length})
          </button>
        </div>
      </div>

      {heatmapData.length > 0 ? (
        <>
          <div className="chart-section">
            <h2>Risk-Exposure Heatmap</h2>
            <p className="chart-description">
              X-axis: Counterparty Reliability | Y-axis: Financial Exposure | Bubble Size: Failure Probability
            </p>
            <ResponsiveContainer width="100%" height={550}>
              <ScatterChart margin={{ top: 20, right: 40, bottom: 70, left: 110 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.2} />
                <XAxis
                  type="number"
                  dataKey="reliability_score_display"
                  name="Reliability"
                  domain={[0, 1]}
                  label={{
                    value: 'Reliability Score (0 = Unreliable, 1 = Highly Reliable)',
                    position: 'insideBottom',
                    offset: -15,
                    fill: '#94a3b8',
                    fontSize: 12
                  }}
                  tickFormatter={(value) => `${(value * 100).toFixed(0)}%`}
                  stroke="#64748b"
                  tick={{ fill: '#cbd5e1', fontSize: 11 }}
                />
                <YAxis
                  type="number"
                  dataKey="financial_exposure_display"
                  name="Exposure"
                  label={{
                    value: 'Financial Exposure (Rs)',
                    angle: -90,
                    position: 'insideLeft',
                    fill: '#94a3b8',
                    fontSize: 12
                  }}
                  tickFormatter={(value) => formatCurrency(value)}
                  stroke="#64748b"
                  tick={{ fill: '#cbd5e1', fontSize: 11 }}
                />
                <ZAxis
                  type="number"
                  dataKey="failure_probability"
                  range={[200, 350]}
                  name="Failure Probability"
                />
                <Tooltip content={<CustomTooltip />} cursor={{ strokeDasharray: '3 3' }} />
                <Scatter name="Counterparties" data={filteredData} fillOpacity={0.85}>
                  {filteredData.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={getQuadrantColor(entry.quadrant)}
                      stroke="#1e293b"
                      strokeWidth={3}
                    />
                  ))}
                </Scatter>
              </ScatterChart>
            </ResponsiveContainer>
          </div>

          <div className="table-section">
            <h2>Contract Risk Table</h2>
            <div className="risk-table-container">
              <table className="risk-table">
                <thead>
                  <tr>
                    <th>Contract</th>
                    <th>Counterparty</th>
                    <th>Industry</th>
                    <th>Reliability</th>
                    <th>Financial Exposure</th>
                    <th>Failure Probability</th>
                    <th>Risk Status</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredData.map((item, index) => (
                    <tr key={index} className={`risk-row ${item.quadrant.toLowerCase()}`}>
                      <td className="counterparty-name">{item.contract_name}</td>
                      <td>{item.counterparty_name}</td>
                      <td>{item.industry}</td>
                      <td>
                        <div className="reliability-bar">
                          <div
                            className="reliability-fill"
                            style={{width: `${item.reliability_score * 100}%`}}
                          ></div>
                          <span>{(item.reliability_score * 100).toFixed(1)}%</span>
                        </div>
                      </td>
                      <td className="exposure-cell">{formatCurrency(item.financial_exposure)}</td>
                      <td className="failure-cell">{(item.failure_probability * 100).toFixed(1)}%</td>
                      <td>
                        <span className={`status-badge ${item.quadrant.toLowerCase()}`}>
                          {getQuadrantLabel(item.quadrant)}
                        </span>
                      </td>
                      <td>
                        <a
                          href={`/contracts/${item.contract_id}?tab=portfolio-risk`}
                          className="action-button"
                          style={{ textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '0.5rem' }}
                        >
                          View Details <ChevronRight size={16} />
                        </a>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      ) : (
        <div className="empty-state">
          <Users size={64} />
          <h3>No Counterparty Data Available</h3>
          <p>Contracts need to be linked to counterparties to generate portfolio-level risk analysis.</p>
        </div>
      )}
    </div>
  );
};

export default CounterpartyPortfolioHeatmap;
