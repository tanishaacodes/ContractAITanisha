import { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import AlfrescoContractGrid from '../components/AlfrescoContractGrid';
import {
  CloudUpload,
  Loader2,
  CheckCircle,
  XCircle,
  AlertCircle,
  RefreshCw,
  Database,
  FileText
} from 'lucide-react';
import { config } from '../config/api.config';

const API_BASE_URL = config.API_BASE_URL;

const AlfrescoSync = () => {
  const [syncing, setSyncing] = useState(false);
  const [syncResults, setSyncResults] = useState(null);
  const [healthStatus, setHealthStatus] = useState(null);
  const [error, setError] = useState(null);
  const [syncedContracts, setSyncedContracts] = useState([]);
  const [loadingContracts, setLoadingContracts] = useState(false);
  const [syncProgress, setSyncProgress] = useState(null);
  const [taskId, setTaskId] = useState(null);

  useEffect(() => {
    checkHealth();

    // Restore sync results from sessionStorage on page load
    const savedResults = sessionStorage.getItem('alfrescoSyncResults');
    const savedContracts = sessionStorage.getItem('alfrescoSyncedContracts');

    if (savedResults && savedContracts) {
      try {
        setSyncResults(JSON.parse(savedResults));
        setSyncedContracts(JSON.parse(savedContracts));
      } catch (e) {
        console.error('Failed to restore sync results:', e);
      }
    }
  }, []);

  const getAuthHeader = () => {
    const token = localStorage.getItem('token');
    return { Authorization: `Bearer ${token}` };
  };

  const fetchSyncedContractsFromResults = async (syncResults) => {
    // Extract contract IDs from sync results
    const successfulSyncs = syncResults.results.filter(r => r.status === 'success' && r.contract_id);

    if (successfulSyncs.length === 0) {
      setSyncedContracts([]);
      sessionStorage.removeItem('alfrescoSyncedContracts');
      return;
    }

    setLoadingContracts(true);
    try {
      // Fetch all contracts and filter by IDs from sync results
      const response = await axios.get(`${API_BASE_URL}/contracts/list`, {
        headers: getAuthHeader()
      });

      const allContracts = response.data.contracts || [];
      const contractIds = successfulSyncs.map(s => s.contract_id);

      // Filter to show only contracts from this sync
      const justSyncedContracts = allContracts.filter(c => contractIds.includes(c.id));
      setSyncedContracts(justSyncedContracts);

      // Save to sessionStorage so it persists across navigation
      sessionStorage.setItem('alfrescoSyncedContracts', JSON.stringify(justSyncedContracts));
    } catch (err) {
      console.error('Failed to fetch synced contracts:', err);
      setSyncedContracts([]);
      sessionStorage.removeItem('alfrescoSyncedContracts');
    } finally {
      setLoadingContracts(false);
    }
  };

  const checkHealth = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/alfresco/health`, {
        timeout: 5000  // 5 second timeout
      });
      setHealthStatus(response.data.alfresco);
      setError(null);
    } catch (err) {
      console.error('Health check failed:', err);
      setHealthStatus({
        status: 'error',
        method: 'none',
        message: err.code === 'ECONNABORTED'
          ? 'Health check timed out - backend may not be running'
          : err.response?.data?.message || 'Failed to connect to backend'
      });
      setError('Unable to check Alfresco connection. Please ensure the backend is running.');
    }
  };

  const pollSyncStatus = async (taskId) => {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/alfresco/sync/status/${taskId}`,
        { headers: getAuthHeader() }
      );

      const status = response.data;
      setSyncProgress(status);

      if (status.status === 'completed') {
        setSyncing(false);
        setSyncResults({
          status: 'completed',
          message: `Sync completed. ${status.synced} successful, ${status.failed} failed`,
          synced_count: status.synced,
          failed_count: status.failed,
          total_count: status.total,
          results: status.results || []
        });
        sessionStorage.setItem('alfrescoSyncResults', JSON.stringify({
          status: 'completed',
          synced_count: status.synced,
          failed_count: status.failed,
          total_count: status.total,
          results: status.results || []
        }));
        if (status.results && status.results.length > 0) {
          fetchSyncedContractsFromResults({ results: status.results });
        }
        setSyncProgress(null);
        setTaskId(null);
      } else if (status.status === 'error') {
        setSyncing(false);
        setError(status.error || 'Sync failed');
        setSyncProgress(null);
        setTaskId(null);
      } else {
        setTimeout(() => pollSyncStatus(taskId), 2000);
      }
    } catch (err) {
      console.error('Failed to poll sync status:', err);
      setError('Failed to check sync status');
      setSyncing(false);
      setSyncProgress(null);
      setTaskId(null);
    }
  };

  const syncFromAlfresco = async () => {
    setSyncing(true);
    setError(null);
    setSyncResults(null);
    setSyncProgress(null);

    try {
      const response = await axios.post(
        `${API_BASE_URL}/alfresco/sync`,
        {
          extract_intelligence: true,
          use_openai: false,
          async: true
        },
        { headers: getAuthHeader() }
      );

      if (response.data.status === 'started') {
        const newTaskId = response.data.task_id;
        setTaskId(newTaskId);
        setSyncProgress({
          status: 'processing',
          progress: 0,
          total: response.data.total_count,
          synced: 0,
          failed: 0,
          current: null
        });
        setTimeout(() => pollSyncStatus(newTaskId), 2000);
      } else if (response.data.status === 'completed') {
        setSyncResults(response.data);
        sessionStorage.setItem('alfrescoSyncResults', JSON.stringify(response.data));
        fetchSyncedContractsFromResults(response.data);
        setSyncing(false);
      } else {
        setError('Unexpected response from server');
        setSyncing(false);
      }
    } catch (err) {
      setError(err.response?.data?.message || 'Sync failed');
      setSyncing(false);
    }
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <CloudUpload className="h-8 w-8" />
            Alfresco Integration
          </h1>
          <p className="text-muted-foreground mt-1">
            Sync contracts from Alfresco CMS and extract intelligence
          </p>
        </div>
        <Button
          onClick={checkHealth}
          variant="outline"
          size="sm"
        >
          <RefreshCw className="mr-2 h-4 w-4" />
          Refresh Status
        </Button>
      </div>

      {/* Health Status */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Database className="h-5 w-5" />
            Connection Status
          </CardTitle>
        </CardHeader>
        <CardContent>
          {healthStatus ? (
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                {healthStatus.status === 'healthy' ? (
                  <>
                    <CheckCircle className="h-6 w-6 text-green-500" />
                    <div>
                      <p className="font-medium">Connected to Alfresco</p>
                      <p className="text-sm text-muted-foreground">
                        Method: {healthStatus.method}
                      </p>
                    </div>
                  </>
                ) : healthStatus.status === 'error' ? (
                  <>
                    <XCircle className="h-6 w-6 text-red-500" />
                    <div>
                      <p className="font-medium">Connection Error</p>
                      <p className="text-sm text-muted-foreground">
                        {healthStatus.message}
                      </p>
                    </div>
                  </>
                ) : (
                  <>
                    <AlertCircle className="h-6 w-6 text-yellow-500" />
                    <div>
                      <p className="font-medium">Alfresco Not Connected</p>
                      <p className="text-sm text-muted-foreground">
                        {healthStatus.message}
                      </p>
                    </div>
                  </>
                )}
              </div>
              <Badge variant={healthStatus.status === 'healthy' ? 'default' : healthStatus.status === 'error' ? 'destructive' : 'outline'}>
                {healthStatus.status}
              </Badge>
            </div>
          ) : (
            <div className="flex items-center gap-2 text-muted-foreground">
              <Loader2 className="h-5 w-5 animate-spin" />
              <span>Checking connection...</span>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Sync Action */}
      <Card>
        <CardHeader>
          <CardTitle>Sync Contracts</CardTitle>
          <CardDescription>
            Import contracts from Alfresco and extract legal intelligence using AI
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div className="flex items-start gap-2">
              <CheckCircle className="h-5 w-5 text-green-500 mt-0.5" />
              <div>
                <p className="font-medium">Document Extraction</p>
                <p className="text-muted-foreground">Fetch from Alfresco CMS</p>
              </div>
            </div>
            <div className="flex items-start gap-2">
              <CheckCircle className="h-5 w-5 text-green-500 mt-0.5" />
              <div>
                <p className="font-medium">Vector Embedding</p>
                <p className="text-muted-foreground">Store in ChromaDB</p>
              </div>
            </div>
            <div className="flex items-start gap-2">
              <CheckCircle className="h-5 w-5 text-green-500 mt-0.5" />
              <div>
                <p className="font-medium">AI Analysis</p>
                <p className="text-muted-foreground">Extract legal clauses</p>
              </div>
            </div>
          </div>

          <Button
            onClick={syncFromAlfresco}
            disabled={syncing || healthStatus?.status !== 'healthy'}
            className="w-full"
            size="lg"
          >
            {syncing ? (
              <>
                <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                Syncing from Alfresco...
              </>
            ) : (
              <>
                <CloudUpload className="mr-2 h-5 w-5" />
                Start Sync
              </>
            )}
          </Button>

          {/* Progress Indicator */}
          {syncProgress && (
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="font-medium">
                  {syncProgress.current ? `Processing: ${syncProgress.current}` : 'Processing contracts...'}
                </span>
                <span className="text-muted-foreground">
                  {syncProgress.progress} / {syncProgress.total}
                </span>
              </div>
              <div className="w-full bg-secondary rounded-full h-2">
                <div
                  className="bg-primary h-2 rounded-full transition-all duration-300"
                  style={{ width: `${(syncProgress.progress / syncProgress.total) * 100}%` }}
                />
              </div>
              <div className="flex items-center justify-between text-xs text-muted-foreground">
                <span>{syncProgress.synced} synced</span>
                {syncProgress.failed > 0 && <span className="text-destructive">{syncProgress.failed} failed</span>}
              </div>
            </div>
          )}

          {healthStatus?.status !== 'healthy' && (
            <p className="text-sm text-yellow-600 flex items-center gap-2">
              <AlertCircle className="h-4 w-4" />
              Alfresco connection required to sync contracts
            </p>
          )}
        </CardContent>
      </Card>

      {/* Error */}
      {error && (
        <Card className="border-destructive">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 text-destructive">
              <XCircle className="h-5 w-5" />
              <p>{error}</p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Sync Results */}
      {syncResults && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CheckCircle className="h-5 w-5 text-green-500" />
              Sync Complete
            </CardTitle>
            <CardDescription>
              {syncResults.message}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Summary Stats */}
            <div className="grid grid-cols-3 gap-4">
              <StatCard
                label="Total Contracts"
                value={syncResults.total_count}
                icon={<FileText className="h-5 w-5" />}
              />
              <StatCard
                label="Successfully Synced"
                value={syncResults.synced_count}
                icon={<CheckCircle className="h-5 w-5 text-green-500" />}
                className="text-green-600"
              />
              <StatCard
                label="Failed"
                value={syncResults.failed_count}
                icon={<XCircle className="h-5 w-5 text-red-500" />}
                className="text-red-600"
              />
            </div>

            {/* Individual Results */}
            {syncResults.results && syncResults.results.length > 0 && (
              <div className="space-y-2">
                <h4 className="font-semibold text-sm">Sync Details:</h4>
                <div className="max-h-96 overflow-y-auto space-y-2">
                  {syncResults.results.map((result, idx) => (
                    <ResultCard key={idx} result={result} />
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Synced Contracts Grid - Only shown after sync */}
      {syncResults && syncResults.synced_count > 0 && (
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-2xl font-bold">Synced Contracts from This Session</h2>
            <Button
              onClick={() => {
                setSyncResults(null);
                setSyncedContracts([]);
                sessionStorage.removeItem('alfrescoSyncResults');
                sessionStorage.removeItem('alfrescoSyncedContracts');
              }}
              variant="outline"
              size="sm"
            >
              <XCircle className="mr-2 h-4 w-4" />
              Clear Results
            </Button>
          </div>

          {loadingContracts ? (
            <div className="bg-slate-900 border border-slate-700 rounded-xl p-12 text-center">
              <Loader2 className="w-12 h-12 text-blue-500 animate-spin mx-auto mb-4" />
              <p className="text-slate-400">Loading contracts...</p>
            </div>
          ) : (
            <AlfrescoContractGrid
              contracts={syncedContracts}
              onRefresh={() => fetchSyncedContractsFromResults(syncResults)}
            />
          )}
        </div>
      )}
    </div>
  );
};

const StatCard = ({ label, value, icon, className = '' }) => (
  <Card>
    <CardContent className="p-4">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-muted-foreground">{label}</p>
          <p className={`text-2xl font-bold ${className}`}>{value}</p>
        </div>
        {icon}
      </div>
    </CardContent>
  </Card>
);

const ResultCard = ({ result }) => (
  <div className="p-3 border rounded-lg bg-muted/50">
    <div className="flex items-start justify-between">
      <div className="flex-1">
        <div className="flex items-center gap-2 mb-1">
          {result.status === 'success' ? (
            <CheckCircle className="h-4 w-4 text-green-500" />
          ) : (
            <XCircle className="h-4 w-4 text-red-500" />
          )}
          <span className="font-medium text-sm">{result.name}</span>
        </div>
        {result.status === 'success' && (
          <div className="text-xs text-muted-foreground space-y-1 ml-6">
            <p>Chunks created: {result.chunks_created}</p>
            {result.intelligence_extracted && (
              <div className="flex items-center gap-1 text-green-600">
                <CheckCircle className="h-3 w-3" />
                <span>Intelligence extracted</span>
              </div>
            )}
          </div>
        )}
        {result.error && (
          <p className="text-xs text-destructive ml-6">{result.error}</p>
        )}
      </div>
      <Badge variant={result.status === 'success' ? 'default' : 'destructive'}>
        {result.status}
      </Badge>
    </div>
  </div>
);

export default AlfrescoSync;
