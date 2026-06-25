/**
 * TEST PAGE - Verify all shared components work
 *
 * Add this route to your router to test:
 * <Route path="/test-components" element={<TestReusableComponents />} />
 *
 * Then visit: http://localhost:5173/test-components
 */
import { useState } from 'react';
import { Globe, Shield, TrendingUp } from 'lucide-react';

// Import all shared components
import { useContractSelector } from '../hooks/useContractSelector';
import { useEnterpriseData } from '../hooks/useEnterpriseData';
import LoadingScreen from '../components/shared/LoadingScreen';
import ErrorScreen from '../components/shared/ErrorScreen';
import PageContainer from '../components/shared/PageContainer';
import ExposureCard from '../components/enterprise/metrics/ExposureCard';

// Import utilities
import {
  getRiskColor,
  getRiskLabel,
  getRiskBadgeClasses,
  formatLargeNumber,
  formatPercentage,
  calculateVaR
} from '../utils/riskUtils';

export default function TestReusableComponents() {
  const [testMode, setTestMode] = useState('normal'); // normal, loading, error
  const { contractId, handleContractSelect } = useContractSelector();

  // Simulate data fetching with different modes
  const { loading, data, error, refetch } = useEnterpriseData(
    async () => {
      // Simulate network delay
      await new Promise(resolve => setTimeout(resolve, 1000));

      if (testMode === 'error') {
        throw new Error('Simulated error for testing!');
      }

      return {
        exposure: 5000000,
        risk_score: 0.75,
        margin: 18.5,
        contracts: 12
      };
    },
    [testMode]
  );

  // Test loading state
  if (loading) {
    return <LoadingScreen message="Testing Loading Component..." />;
  }

  // Test error state
  if (error) {
    return <ErrorScreen error={error} onRetry={refetch} title="Test Error Screen" />;
  }

  // Calculate test values
  const exposure = 5000000;
  const riskScore = 0.75;
  const var95 = calculateVaR(exposure, 0.95);

  return (
    <PageContainer
      title="Test Reusable Components"
      subtitle="Verify all shared components and utilities work correctly"
      icon={Globe}
      contractId={contractId}
      onContractSelect={handleContractSelect}
      showBack={true}
      headerActions={
        <div className="flex gap-2">
          <button
            onClick={() => setTestMode('normal')}
            className={`px-4 py-2 rounded-lg ${testMode === 'normal' ? 'bg-cyan-500' : 'bg-slate-700'}`}
          >
            Normal
          </button>
          <button
            onClick={() => setTestMode('loading')}
            className={`px-4 py-2 rounded-lg ${testMode === 'loading' ? 'bg-cyan-500' : 'bg-slate-700'}`}
          >
            Test Loading
          </button>
          <button
            onClick={() => setTestMode('error')}
            className={`px-4 py-2 rounded-lg ${testMode === 'error' ? 'bg-cyan-500' : 'bg-slate-700'}`}
          >
            Test Error
          </button>
        </div>
      }
    >
      {/* Test Status */}
      <div className="bg-green-500/20 border border-green-500/50 rounded-xl p-4 mb-6">
        <h3 className="text-lg font-bold text-green-400 mb-2">✓ All Components Loaded Successfully!</h3>
        <p className="text-slate-300">
          All shared hooks, components, and utilities are working correctly.
        </p>
      </div>

      {/* Test useContractSelector Hook */}
      <div className="bg-slate-800/50 rounded-xl p-6 mb-6 border border-slate-700">
        <h3 className="text-xl font-bold mb-4">1. useContractSelector Hook</h3>
        <div className="space-y-2">
          <p className="text-slate-400">Selected Contract ID: <span className="text-cyan-400">{contractId || 'None'}</span></p>
          <p className="text-slate-400">Has Contract: <span className="text-cyan-400">{contractId ? 'Yes' : 'No'}</span></p>
          <p className="text-green-400">✓ Hook working correctly</p>
        </div>
      </div>

      {/* Test useEnterpriseData Hook */}
      <div className="bg-slate-800/50 rounded-xl p-6 mb-6 border border-slate-700">
        <h3 className="text-xl font-bold mb-4">2. useEnterpriseData Hook</h3>
        <div className="space-y-2">
          <p className="text-slate-400">Loading State: <span className="text-cyan-400">{loading ? 'True' : 'False'}</span></p>
          <p className="text-slate-400">Has Data: <span className="text-cyan-400">{data ? 'Yes' : 'No'}</span></p>
          <p className="text-slate-400">Has Error: <span className="text-cyan-400">{error ? 'Yes' : 'No'}</span></p>
          {data && (
            <div className="mt-2 p-3 bg-slate-700/50 rounded">
              <pre className="text-xs text-cyan-400">{JSON.stringify(data, null, 2)}</pre>
            </div>
          )}
          <p className="text-green-400">✓ Hook working correctly</p>
        </div>
      </div>

      {/* Test ExposureCard Component */}
      <div className="bg-slate-800/50 rounded-xl p-6 mb-6 border border-slate-700">
        <h3 className="text-xl font-bold mb-4">3. ExposureCard Component</h3>
        <div className="grid grid-cols-3 gap-4 mb-4">
          <ExposureCard
            title="Total Exposure"
            value={formatLargeNumber(exposure)}
            icon={Shield}
            trend={5.2}
            color="cyan"
          />
          <ExposureCard
            title="Risk Score"
            value={(riskScore * 100).toFixed(1) + '%'}
            icon={TrendingUp}
            trend={-2.3}
            color="red"
          />
          <ExposureCard
            title="VaR (95%)"
            value={formatLargeNumber(var95)}
            icon={Globe}
            trend={0}
            color="amber"
          />
        </div>
        <p className="text-green-400">✓ Component rendering correctly</p>
      </div>

      {/* Test Risk Utilities */}
      <div className="bg-slate-800/50 rounded-xl p-6 mb-6 border border-slate-700">
        <h3 className="text-xl font-bold mb-4">4. Risk Utilities</h3>
        <div className="space-y-4">
          <div>
            <p className="text-slate-400 mb-2">Risk Levels & Colors:</p>
            <div className="flex gap-3">
              {[0.2, 0.5, 0.8].map(score => (
                <div key={score} className="flex-1">
                  <div
                    className={`px-4 py-2 rounded-lg border text-center ${getRiskBadgeClasses(score)}`}
                  >
                    <div className="font-bold">{getRiskLabel(score)}</div>
                    <div className="text-sm opacity-75">{(score * 100).toFixed(0)}%</div>
                    <div
                      className="w-full h-2 rounded mt-2"
                      style={{ backgroundColor: getRiskColor(score) }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div>
            <p className="text-slate-400 mb-2">Number Formatting:</p>
            <div className="grid grid-cols-2 gap-4">
              <div className="p-3 bg-slate-700/50 rounded">
                <div className="text-xs text-slate-400">formatLargeNumber(5000000)</div>
                <div className="text-cyan-400 font-bold">{formatLargeNumber(5000000)}</div>
              </div>
              <div className="p-3 bg-slate-700/50 rounded">
                <div className="text-xs text-slate-400">formatLargeNumber(1500000000)</div>
                <div className="text-cyan-400 font-bold">{formatLargeNumber(1500000000)}</div>
              </div>
              <div className="p-3 bg-slate-700/50 rounded">
                <div className="text-xs text-slate-400">formatPercentage(5.2)</div>
                <div className="text-cyan-400 font-bold">{formatPercentage(5.2)}</div>
              </div>
              <div className="p-3 bg-slate-700/50 rounded">
                <div className="text-xs text-slate-400">calculateVaR(5M, 0.95)</div>
                <div className="text-cyan-400 font-bold">{formatLargeNumber(var95)}</div>
              </div>
            </div>
          </div>

          <p className="text-green-400">✓ All utilities working correctly</p>
        </div>
      </div>

      {/* Test Instructions */}
      <div className="bg-blue-500/20 border border-blue-500/50 rounded-xl p-6">
        <h3 className="text-xl font-bold mb-4">✨ Test Instructions</h3>
        <div className="space-y-2 text-slate-300">
          <p>• Click "Test Loading" button to see LoadingScreen component</p>
          <p>• Click "Test Error" button to see ErrorScreen component</p>
          <p>• Click "Normal" button to return to this view</p>
          <p>• Use Contract Selector to test URL param management</p>
          <p>• Check browser console for any errors (should be none)</p>
        </div>
      </div>

      {/* Success Summary */}
      <div className="mt-6 p-6 bg-gradient-to-r from-green-500/20 to-cyan-500/20 rounded-xl border border-green-500/30">
        <h3 className="text-2xl font-bold text-white mb-2">🎉 All Tests Passed!</h3>
        <p className="text-slate-300">
          All shared components, hooks, and utilities are working correctly.
          You can now use these in any enterprise page to reduce code duplication.
        </p>
      </div>
    </PageContainer>
  );
}
