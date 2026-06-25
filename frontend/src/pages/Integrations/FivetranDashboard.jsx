import { useState, useEffect } from 'react';
import { Database, RefreshCw, CheckCircle, XCircle, Clock, Webhook } from 'lucide-react';
import useAuthStore from '../../store/authStore';
import useThemeStore from '../../store/themeStore';

const FivetranDashboard = () => {
  const { theme } = useThemeStore();
  const { token } = useAuthStore();
  const [status, setStatus] = useState(null);
  const [connectors, setConnectors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);

  useEffect(() => {
    fetchStatus();
    fetchConnectors();
  }, []);

  const fetchStatus = async () => {
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL||(import.meta.env.VITE_API_URL||'http://localhost:8002')}/api/integrations/fivetran/status/`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await response.json();
      setStatus(data);
    } catch (error) {
      console.error('Failed to fetch Fivetran status:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchConnectors = async () => {
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL||(import.meta.env.VITE_API_URL||'http://localhost:8002')}/api/integrations/fivetran/connectors/`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await response.json();
      setConnectors(data.connectors || []);
    } catch (error) {
      console.error('Failed to fetch connectors:', error);
    }
  };

  const handleSync = async (connectorId) => {
    setSyncing(true);
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL||(import.meta.env.VITE_API_URL||'http://localhost:8002')}/api/integrations/fivetran/sync/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ connectorId }),
      });

      if (response.ok) {
        const data = await response.json();
        alert(data.message);
        fetchStatus();
        fetchConnectors();
      }
    } catch (error) {
      alert('Failed to trigger sync');
      console.error(error);
    } finally {
      setSyncing(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-xl">Loading Fivetran Dashboard...</div>
      </div>
    );
  }

  return (
    <div className={`min-h-screen ${theme.colors.background} ${theme.colors.textPrimary} p-8`}>
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-4 mb-4">
          <div className="p-4 bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl">
            <Database size={32} className="text-white" />
          </div>
          <div>
            <h1 className="text-4xl font-bold">Fivetran Connector</h1>
            <p className={theme.colors.textSecondary}>
              Sync data from DocuSign, SAP, and Salesforce
            </p>
          </div>
        </div>
      </div>

      {/* Status Card */}
      {status && (
        <div className={`${theme.colors.surface} p-6 rounded-xl border ${theme.colors.surfaceBorder} mb-8`}>
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-semibold mb-2">Connection Status</h2>
              <div className="flex items-center gap-3">
                {status.status === 'connected' ? (
                  <>
                    <CheckCircle className="text-green-500" size={24} />
                    <span className="text-green-500 font-semibold">Connected</span>
                  </>
                ) : (
                  <>
                    <XCircle className="text-red-500" size={24} />
                    <span className="text-red-500 font-semibold">Disconnected</span>
                  </>
                )}
              </div>
              {status.lastSync && (
                <p className={`text-sm ${theme.colors.textSecondary} mt-2`}>
                  Last sync: {new Date(status.lastSync).toLocaleString()}
                </p>
              )}
            </div>

            <div className="text-right">
              <p className={`text-sm ${theme.colors.textSecondary}`}>Total Connectors</p>
              <p className="text-3xl font-bold">{connectors.length}</p>
            </div>
          </div>
        </div>
      )}

      {/* Connectors Grid */}
      <div className="mb-6">
        <h2 className="text-2xl font-bold mb-4">Active Connectors</h2>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {connectors.map((connector) => (
          <div
            key={connector.id}
            className={`${theme.colors.surface} p-6 rounded-xl border ${theme.colors.surfaceBorder} hover:border-purple-500 transition`}
          >
            {/* Connector Header */}
            <div className="flex items-start justify-between mb-4">
              <div>
                <h3 className="text-lg font-semibold">{connector.name}</h3>
                <p className={`text-sm ${theme.colors.textSecondary}`}>{connector.source}</p>
              </div>
              <div className={`p-2 rounded-lg ${connector.status === 'active' ? 'bg-green-500/20' : 'bg-gray-500/20'}`}>
                {connector.status === 'active' ? (
                  <CheckCircle className="text-green-500" size={20} />
                ) : (
                  <Clock className="text-gray-400" size={20} />
                )}
              </div>
            </div>

            {/* Connector Stats */}
            <div className="space-y-2 mb-4">
              <div className="flex justify-between text-sm">
                <span className={theme.colors.textSecondary}>Status:</span>
                <span className={connector.status === 'active' ? 'text-green-500' : 'text-gray-400'}>
                  {connector.status}
                </span>
              </div>
              <div className="flex justify-between text-sm">
                <span className={theme.colors.textSecondary}>Records Synced:</span>
                <span>{connector.recordsSynced?.toLocaleString() || 0}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className={theme.colors.textSecondary}>Last Sync:</span>
                <span>{connector.lastSync || 'Never'}</span>
              </div>
            </div>

            {/* Sync Button */}
            <button
              onClick={() => handleSync(connector.id)}
              disabled={syncing}
              className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-gradient-to-r from-purple-500 to-purple-600 text-white rounded-lg hover:from-purple-600 hover:to-purple-700 transition disabled:opacity-50"
            >
              <RefreshCw size={18} className={syncing ? 'animate-spin' : ''} />
              {syncing ? 'Syncing...' : 'Trigger Sync'}
            </button>
          </div>
        ))}
      </div>

      {/* Webhook Info */}
      <div className={`${theme.colors.surface} p-6 rounded-xl border ${theme.colors.surfaceBorder} mt-8`}>
        <div className="flex items-start gap-4">
          <Webhook className="text-purple-500" size={24} />
          <div>
            <h3 className="text-lg font-semibold mb-2">Webhook Configuration</h3>
            <p className={`text-sm ${theme.colors.textSecondary} mb-2`}>
              Configure Fivetran to send webhook notifications to:
            </p>
            <code className={`block px-4 py-2 ${theme.colors.surfaceHover} rounded-lg text-sm`}>
              http://localhost:8002/api/integrations/fivetran/webhook/
            </code>
          </div>
        </div>
      </div>

      {/* Data Sources Info */}
      <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className={`${theme.colors.surface} p-6 rounded-xl border ${theme.colors.surfaceBorder}`}>
          <h3 className="font-semibold mb-2">DocuSign</h3>
          <p className={`text-sm ${theme.colors.textSecondary}`}>
            Sync contracts, envelopes, and signatures from DocuSign
          </p>
        </div>

        <div className={`${theme.colors.surface} p-6 rounded-xl border ${theme.colors.surfaceBorder}`}>
          <h3 className="font-semibold mb-2">SAP</h3>
          <p className={`text-sm ${theme.colors.textSecondary}`}>
            Import procurement data and vendor contracts from SAP
          </p>
        </div>

        <div className={`${theme.colors.surface} p-6 rounded-xl border ${theme.colors.surfaceBorder}`}>
          <h3 className="font-semibold mb-2">Salesforce</h3>
          <p className={`text-sm ${theme.colors.textSecondary}`}>
            Pull customer agreements and deal data from Salesforce
          </p>
        </div>
      </div>
    </div>
  );
};

export default FivetranDashboard;
