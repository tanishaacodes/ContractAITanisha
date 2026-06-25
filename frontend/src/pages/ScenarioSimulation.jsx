import { useState } from 'react';
import { Play, RefreshCw, AlertTriangle, TrendingUp, TrendingDown, Info } from 'lucide-react';
import axios from 'axios';
import useAuthStore from '../store/authStore';

const ScenarioSimulation = () => {
  const { token } = useAuthStore();

  const [scenarioType, setScenarioType] = useState('vendor_loss');
  const [parameters, setParameters] = useState({
    vendor_name: '',
    region: 'APAC',
    risk_multiplier: 1.5
  });
  const [jobId, setJobId] = useState(null);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const runSimulation = async () => {
    setLoading(true);
    setError(null);
    setResults(null);

    try {
      const payload = {
        scenario_type: scenarioType,
        ...parameters
      };

      // Start simulation
      const response = await axios.post(
        `${import.meta.env.VITE_API_URL||(import.meta.env.VITE_API_URL||'http://localhost:8002')}/api/risk/scenario-simulation`,
        payload,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );

      if (response.data.success) {
        setJobId(response.data.job_id);
        // Poll for results
        pollJobStatus(response.data.job_id);
      }
    } catch (err) {
      console.error('Error running simulation:', err);
      setError(err.response?.data?.error || 'Failed to run simulation');
      setLoading(false);
    }
  };

  const pollJobStatus = async (jid) => {
    const maxAttempts = 30;
    let attempts = 0;

    const poll = setInterval(async () => {
      attempts++;

      try {
        const response = await axios.get(
          `${import.meta.env.VITE_API_URL||(import.meta.env.VITE_API_URL||'http://localhost:8002')}/api/risk/jobs/${jid}/status`,
          {
            headers: { Authorization: `Bearer ${token}` }
          }
        );

        if (response.data.success) {
          const jobData = response.data.data;

          if (jobData.status === 'SUCCESS') {
            setResults(jobData.result);
            setLoading(false);
            clearInterval(poll);
          } else if (jobData.status === 'FAILURE') {
            setError(jobData.error || 'Simulation failed');
            setLoading(false);
            clearInterval(poll);
          }
        }

        if (attempts >= maxAttempts) {
          setError('Simulation timed out');
          setLoading(false);
          clearInterval(poll);
        }
      } catch (err) {
        console.error('Error polling job status:', err);
        setError('Failed to get simulation results');
        setLoading(false);
        clearInterval(poll);
      }
    }, 2000);
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center space-x-3 mb-2">
          <div className="bg-purple-600 p-3 rounded-lg">
            <Play className="w-8 h-8 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Risk Scenario Simulation</h1>
            <p className="text-gray-600">Perform what-if analysis on your contract portfolio</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Configuration Panel */}
        <div className="lg:col-span-1 bg-white rounded-lg shadow-lg p-6">
          <h3 className="text-lg font-semibold mb-4">Scenario Configuration</h3>

          {/* Scenario Type */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Scenario Type
            </label>
            <select
              value={scenarioType}
              onChange={(e) => setScenarioType(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2"
              disabled={loading}
            >
              <option value="vendor_loss">Vendor Loss / Disruption</option>
              <option value="risk_multiplier">Risk Multiplier (Regional)</option>
            </select>
          </div>

          {/* Scenario-specific parameters */}
          {scenarioType === 'vendor_loss' && (
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Vendor Name
              </label>
              <input
                type="text"
                value={parameters.vendor_name}
                onChange={(e) => setParameters({ ...parameters, vendor_name: e.target.value })}
                placeholder="e.g., VendorABC"
                className="w-full border border-gray-300 rounded-lg px-3 py-2"
                disabled={loading}
              />
              <p className="text-xs text-gray-500 mt-1">
                Simulate the impact if this vendor becomes unavailable
              </p>
            </div>
          )}

          {scenarioType === 'risk_multiplier' && (
            <>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Region
                </label>
                <select
                  value={parameters.region}
                  onChange={(e) => setParameters({ ...parameters, region: e.target.value })}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2"
                  disabled={loading}
                >
                  <option value="APAC">APAC</option>
                  <option value="EMEA">EMEA</option>
                  <option value="US">US</option>
                  <option value="LATAM">LATAM</option>
                </select>
              </div>

              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Risk Multiplier: {parameters.risk_multiplier}x
                </label>
                <input
                  type="range"
                  min="0.5"
                  max="3"
                  step="0.1"
                  value={parameters.risk_multiplier}
                  onChange={(e) => setParameters({ ...parameters, risk_multiplier: parseFloat(e.target.value) })}
                  className="w-full"
                  disabled={loading}
                />
                <div className="flex justify-between text-xs text-gray-500 mt-1">
                  <span>0.5x (Decrease)</span>
                  <span>3x (Increase)</span>
                </div>
                <p className="text-xs text-gray-500 mt-2">
                  Simulate the impact of increasing/decreasing risk in this region
                </p>
              </div>
            </>
          )}

          {/* Action Button */}
          <button
            onClick={runSimulation}
            disabled={loading || (scenarioType === 'vendor_loss' && !parameters.vendor_name)}
            className={`w-full flex items-center justify-center space-x-2 px-4 py-3 rounded-lg font-semibold ${
              loading
                ? 'bg-gray-400 cursor-not-allowed'
                : 'bg-purple-600 hover:bg-purple-700 text-white'
            }`}
          >
            {loading ? (
              <>
                <RefreshCw className="w-5 h-5 animate-spin" />
                <span>Running Simulation...</span>
              </>
            ) : (
              <>
                <Play className="w-5 h-5" />
                <span>Run Simulation</span>
              </>
            )}
          </button>

          {error && (
            <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-sm text-red-800">{error}</p>
            </div>
          )}
        </div>

        {/* Results Panel */}
        <div className="lg:col-span-2 bg-white rounded-lg shadow-lg p-6">
          <h3 className="text-lg font-semibold mb-4">Simulation Results</h3>

          {!results && !loading && !error && (
            <div className="text-center py-12 text-gray-500">
              <Info className="w-16 h-16 mx-auto mb-4 opacity-20" />
              <p className="text-lg mb-2">No simulation results yet</p>
              <p className="text-sm">Configure a scenario and click "Run Simulation" to see results</p>
            </div>
          )}

          {loading && (
            <div className="text-center py-12">
              <RefreshCw className="w-12 h-12 text-purple-600 animate-spin mx-auto mb-4" />
              <p className="text-gray-600">Processing simulation...</p>
            </div>
          )}

          {results && results.status === 'completed' && (
            <div className="space-y-6">
              {/* Results Header */}
              <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                <h4 className="font-semibold text-purple-900 mb-2">
                  Scenario: {scenarioType.replace('_', ' ').toUpperCase()}
                </h4>
                <p className="text-sm text-purple-700">
                  {scenarioType === 'vendor_loss' && `Vendor: ${parameters.vendor_name}`}
                  {scenarioType === 'risk_multiplier' && `Region: ${parameters.region}, Multiplier: ${parameters.risk_multiplier}x`}
                </p>
              </div>

              {/* Results Data */}
              {results.results && results.results.length > 0 && (
                <div className="space-y-4">
                  {results.results.map((result, index) => (
                    <div key={index} className="border border-gray-200 rounded-lg p-4">
                      {scenarioType === 'vendor_loss' && (
                        <>
                          <div className="grid grid-cols-2 gap-4 mb-4">
                            <div>
                              <label className="text-sm text-gray-600">Affected Contracts</label>
                              <p className="text-2xl font-bold text-gray-900">
                                {result.affected_contracts || 0}
                              </p>
                            </div>
                            <div>
                              <label className="text-sm text-gray-600">Total Exposure</label>
                              <p className="text-2xl font-bold text-red-600">
                                ${(result.total_exposure || 0).toLocaleString()}
                              </p>
                            </div>
                          </div>

                          <div className="bg-red-50 border border-red-200 rounded p-3">
                            <div className="flex items-start space-x-2">
                              <AlertTriangle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                              <div>
                                <p className="text-sm font-semibold text-red-900">Impact Assessment</p>
                                <p className="text-sm text-red-700 mt-1">
                                  Loss of this vendor would impact {result.affected_contracts || 0} contracts with
                                  a total risk exposure of ${(result.total_exposure || 0).toLocaleString()}.
                                </p>
                              </div>
                            </div>
                          </div>
                        </>
                      )}

                      {scenarioType === 'risk_multiplier' && (
                        <>
                          <div className="grid grid-cols-2 gap-4 mb-4">
                            <div>
                              <label className="text-sm text-gray-600">Affected Contracts</label>
                              <p className="text-2xl font-bold text-gray-900">
                                {result.affected_contracts || 0}
                              </p>
                            </div>
                            <div>
                              <label className="text-sm text-gray-600">Current Exposure</label>
                              <p className="text-2xl font-bold text-gray-900">
                                ${(result.current_exposure || 0).toLocaleString()}
                              </p>
                            </div>
                          </div>

                          <div className="grid grid-cols-2 gap-4 mb-4">
                            <div>
                              <label className="text-sm text-gray-600">Projected Exposure</label>
                              <p className="text-2xl font-bold text-orange-600">
                                ${(result.projected_exposure || 0).toLocaleString()}
                              </p>
                            </div>
                            <div>
                              <label className="text-sm text-gray-600">Change</label>
                              <div className="flex items-center space-x-2">
                                {result.projected_exposure > result.current_exposure ? (
                                  <TrendingUp className="w-6 h-6 text-red-600" />
                                ) : (
                                  <TrendingDown className="w-6 h-6 text-green-600" />
                                )}
                                <p className={`text-2xl font-bold ${
                                  result.projected_exposure > result.current_exposure
                                    ? 'text-red-600'
                                    : 'text-green-600'
                                }`}>
                                  {(((result.projected_exposure - result.current_exposure) / result.current_exposure) * 100).toFixed(1)}%
                                </p>
                              </div>
                            </div>
                          </div>

                          <div className={`border rounded p-3 ${
                            result.projected_exposure > result.current_exposure
                              ? 'bg-orange-50 border-orange-200'
                              : 'bg-green-50 border-green-200'
                          }`}>
                            <div className="flex items-start space-x-2">
                              {result.projected_exposure > result.current_exposure ? (
                                <AlertTriangle className="w-5 h-5 text-orange-600 flex-shrink-0 mt-0.5" />
                              ) : (
                                <Info className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                              )}
                              <div>
                                <p className={`text-sm font-semibold ${
                                  result.projected_exposure > result.current_exposure
                                    ? 'text-orange-900'
                                    : 'text-green-900'
                                }`}>
                                  Impact Assessment
                                </p>
                                <p className={`text-sm mt-1 ${
                                  result.projected_exposure > result.current_exposure
                                    ? 'text-orange-700'
                                    : 'text-green-700'
                                }`}>
                                  Applying a {parameters.risk_multiplier}x multiplier to {parameters.region} contracts
                                  would {result.projected_exposure > result.current_exposure ? 'increase' : 'decrease'} exposure
                                  by ${Math.abs(result.projected_exposure - result.current_exposure).toLocaleString()}.
                                </p>
                              </div>
                            </div>
                          </div>
                        </>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ScenarioSimulation;
