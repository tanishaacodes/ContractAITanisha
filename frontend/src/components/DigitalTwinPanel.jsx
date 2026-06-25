/**
 * Digital Twin Status Panel - Contract Digital Twin Dashboard
 * Real-time status, health indicators, and simulation results
 */

import React, { useState, useEffect } from 'react';
import { getDigitalTwinStatus, simulateDigitalTwin } from '../services/forceMajeureService';

const DigitalTwinPanel = ({ twinId, autoRefresh = false, refreshInterval = 30000 }) => {
  const [twinData, setTwinData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [simulating, setSimulating] = useState(false);

  useEffect(() => {
    fetchTwinStatus();

    if (autoRefresh) {
      const interval = setInterval(fetchTwinStatus, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [twinId]);

  const fetchTwinStatus = async () => {
    try {
      setLoading(true);
      const data = await getDigitalTwinStatus(twinId);
      setTwinData(data);
      setError(null);
    } catch (err) {
      setError(err.message || 'Failed to fetch twin status');
    } finally {
      setLoading(false);
    }
  };

  const handleSimulate = async (scenario) => {
    try {
      setSimulating(true);
      const result = await simulateDigitalTwin({
        twin_id: twinId,
        fm_scenario: scenario,
        simulation_params: { monte_carlo_runs: 1000 }
      });
      // Handle simulation result
      console.log('Simulation result:', result);
      alert('Simulation completed! Check console for results.');
    } catch (err) {
      alert('Simulation failed: ' + err.message);
    } finally {
      setSimulating(false);
    }
  };

  if (loading) {
    return (
      <div style={{ padding: '20px', textAlign: 'center' }}>
        <div className="spinner">Loading digital twin...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{
        padding: '20px',
        backgroundColor: '#FEE2E2',
        color: '#991B1B',
        borderRadius: '8px',
        border: '1px solid #FECACA'
      }}>
        <strong>Error:</strong> {error}
      </div>
    );
  }

  if (!twinData || !twinData.current_state) {
    return (
      <div style={{ padding: '20px', textAlign: 'center', color: '#6B7280' }}>
        No twin data available
      </div>
    );
  }

  const state = twinData.current_state;
  const healthColor = getHealthColor(state.health_status);

  return (
    <div style={{
      backgroundColor: 'white',
      borderRadius: '12px',
      boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
      overflow: 'hidden'
    }}>
      {/* Header */}
      <div style={{
        padding: '20px',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        color: 'white'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h2 style={{ margin: '0 0 5px 0', fontSize: '20px' }}>
              🤖 Digital Twin: {twinData.contract_name || twinData.contract_id}
            </h2>
            <p style={{ margin: 0, fontSize: '13px', opacity: 0.9 }}>
              Last Updated: {new Date(state.timestamp).toLocaleString()}
            </p>
          </div>
          <div style={{
            backgroundColor: healthColor,
            padding: '8px 16px',
            borderRadius: '20px',
            fontWeight: 'bold',
            fontSize: '14px'
          }}>
            {state.health_status.toUpperCase()}
          </div>
        </div>
      </div>

      {/* Status Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: '15px',
        padding: '20px'
      }}>
        {/* Completion */}
        <StatusCard
          icon="📊"
          title="Completion"
          value={`${state.completion_percentage.toFixed(1)}%`}
          subtitle={`Phase: ${state.phase}`}
          color="#3B82F6"
        />

        {/* Budget */}
        <StatusCard
          icon="💰"
          title="Budget"
          value={`$${(state.budget_spent / 1000000).toFixed(1)}M`}
          subtitle={`Remaining: $${(state.remaining_budget / 1000000).toFixed(1)}M`}
          color="#10B981"
        />

        {/* Schedule */}
        <StatusCard
          icon="📅"
          title="Schedule"
          value={`${state.days_elapsed} days`}
          subtitle={`${state.days_remaining} days remaining`}
          color="#F59E0B"
        />

        {/* Performance */}
        <StatusCard
          icon="⭐"
          title="Performance"
          value={`${(state.performance_score * 100).toFixed(0)}%`}
          subtitle="Overall Score"
          color="#8B5CF6"
        />
      </div>

      {/* Progress Bar */}
      <div style={{ padding: '0 20px 20px' }}>
        <div style={{
          backgroundColor: '#F3F4F6',
          borderRadius: '10px',
          height: '24px',
          position: 'relative',
          overflow: 'hidden'
        }}>
          <div style={{
            width: `${state.completion_percentage}%`,
            height: '100%',
            background: 'linear-gradient(90deg, #3B82F6 0%, #8B5CF6 100%)',
            transition: 'width 0.5s ease',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'white',
            fontSize: '12px',
            fontWeight: 'bold'
          }}>
            {state.completion_percentage >= 10 && `${state.completion_percentage.toFixed(0)}%`}
          </div>
          {state.completion_percentage < 10 && (
            <div style={{
              position: 'absolute',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              fontSize: '12px',
              fontWeight: 'bold',
              color: '#6B7280'
            }}>
              {state.completion_percentage.toFixed(0)}%
            </div>
          )}
        </div>
      </div>

      {/* Active Risks */}
      {state.active_risks && state.active_risks.length > 0 && (
        <div style={{
          margin: '0 20px 20px',
          padding: '15px',
          backgroundColor: '#FEF2F2',
          borderRadius: '8px',
          border: '1px solid #FEE2E2'
        }}>
          <h4 style={{ margin: '0 0 10px 0', fontSize: '14px', fontWeight: 'bold', color: '#991B1B' }}>
            ⚠️ Active Risks ({state.active_risks.length})
          </h4>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
            {state.active_risks.map((risk, index) => (
              <span key={index} style={{
                padding: '4px 12px',
                backgroundColor: 'white',
                color: '#DC2626',
                borderRadius: '12px',
                fontSize: '12px',
                fontWeight: '500'
              }}>
                {risk}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* FM Events */}
      {state.fm_events_occurred && state.fm_events_occurred.length > 0 && (
        <div style={{
          margin: '0 20px 20px',
          padding: '15px',
          backgroundColor: '#FFF7ED',
          borderRadius: '8px',
          border: '1px solid #FED7AA'
        }}>
          <h4 style={{ margin: '0 0 10px 0', fontSize: '14px', fontWeight: 'bold', color: '#9A3412' }}>
            📋 FM Events ({state.fm_events_occurred.length})
          </h4>
          <div style={{ fontSize: '12px', color: '#9A3412' }}>
            {state.fm_events_occurred.map((event, index) => (
              <div key={index} style={{ marginBottom: '4px' }}>
                • {event.type || event} - {event.date || 'Ongoing'}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Quick Actions */}
      <div style={{
        padding: '20px',
        backgroundColor: '#F9FAFB',
        borderTop: '1px solid #E5E7EB'
      }}>
        <h4 style={{ margin: '0 0 12px 0', fontSize: '14px', fontWeight: 'bold', color: '#1F2937' }}>
          Quick Actions
        </h4>
        <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
          <button
            onClick={() => handleSimulate({ type: 'war', severity: 0.7, duration_days: 90 })}
            disabled={simulating}
            style={{
              padding: '8px 16px',
              backgroundColor: '#DC2626',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: simulating ? 'not-allowed' : 'pointer',
              fontSize: '13px',
              fontWeight: '500',
              opacity: simulating ? 0.6 : 1
            }}
          >
            🔴 Simulate War Impact
          </button>
          <button
            onClick={() => handleSimulate({ type: 'pandemic', severity: 0.6, duration_days: 120 })}
            disabled={simulating}
            style={{
              padding: '8px 16px',
              backgroundColor: '#EA580C',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: simulating ? 'not-allowed' : 'pointer',
              fontSize: '13px',
              fontWeight: '500',
              opacity: simulating ? 0.6 : 1
            }}
          >
            🦠 Simulate Pandemic
          </button>
          <button
            onClick={fetchTwinStatus}
            disabled={loading}
            style={{
              padding: '8px 16px',
              backgroundColor: '#3B82F6',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: loading ? 'not-allowed' : 'pointer',
              fontSize: '13px',
              fontWeight: '500',
              opacity: loading ? 0.6 : 1
            }}
          >
            🔄 Refresh Status
          </button>
        </div>
      </div>
    </div>
  );
};

// Status Card Component
const StatusCard = ({ icon, title, value, subtitle, color }) => (
  <div style={{
    padding: '15px',
    backgroundColor: '#F9FAFB',
    borderRadius: '8px',
    border: '1px solid #E5E7EB'
  }}>
    <div style={{ fontSize: '24px', marginBottom: '8px' }}>{icon}</div>
    <div style={{ fontSize: '12px', color: '#6B7280', marginBottom: '4px' }}>{title}</div>
    <div style={{ fontSize: '20px', fontWeight: 'bold', color, marginBottom: '4px' }}>
      {value}
    </div>
    <div style={{ fontSize: '11px', color: '#9CA3AF' }}>{subtitle}</div>
  </div>
);

// Health color helper
const getHealthColor = (status) => {
  switch (status?.toLowerCase()) {
    case 'green':
      return '#10B981';
    case 'yellow':
      return '#F59E0B';
    case 'red':
      return '#DC2626';
    default:
      return '#6B7280';
  }
};

export default DigitalTwinPanel;
