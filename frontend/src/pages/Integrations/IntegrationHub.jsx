import { useState, useEffect } from 'react';
import useThemeStore from '../../store/themeStore';
import useAuthStore from '../../store/authStore';
import {
  Globe,
  Zap,
  RefreshCw,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Send,
  Activity,
  Database,
  FileCode,
  ChevronDown,
  ChevronUp,
  Shield,
  Cpu,
  ArrowRight,
  Clock,
  Info,
} from 'lucide-react';

const API_BASE = (import.meta.env.VITE_API_URL||(import.meta.env.VITE_API_URL||'http://localhost:8002'));

const ERP_OPTIONS = [
  { value: 'SAP', label: 'SAP S/4HANA', color: 'text-blue-400', bg: 'bg-blue-500/10 border-blue-500/30' },
  { value: 'INFOR', label: 'Infor ERP LN', color: 'text-orange-400', bg: 'bg-orange-500/10 border-orange-500/30' },
  { value: 'ORACLE', label: 'Oracle Fusion', color: 'text-red-400', bg: 'bg-red-500/10 border-red-500/30' },
  { value: 'DYNAMICS', label: 'Microsoft Dynamics', color: 'text-purple-400', bg: 'bg-purple-500/10 border-purple-500/30' },
];

const SAMPLE_PAYLOADS = {
  SAP: {
    d: {
      PurchaseContract: '4600001234',
      PurchaseContractType: 'MK',
      PurchaseContractTargetAmount: '2500000',
      DocumentCurrency: 'USD',
      Supplier: 'V-10042',
      PurchaseContractDesc: 'Annual IT Services with unlimited indemnity clause',
      CompanyCode: '1000',
      PurchasingOrganization: 'US00',
      ValidityStartDate: '2025-01-01',
      ValidityEndDate: '2025-12-31',
    }
  },
  INFOR: {
    contractId: 'CNT-001',
    contractType: 'SERVICE',
    netAmount: 2500000,
    currency: 'USD',
    vendorId: 'V-10042',
    vendorName: 'TechSolutions Pvt Ltd',
    description: 'Annual IT Infrastructure Services with auto-renewal clause',
    paymentTerms: 'Net 60',
    startDate: '2025-01-01',
    endDate: '2025-12-31',
  },
  ORACLE: {
    contractNumber: 'ORC-2025-00123',
    contractType: 'PROCUREMENT',
    totalValue: 1800000,
    currency: 'USD',
    supplierId: 'SUPP-442',
    supplierName: 'Global Supply Corp',
    description: 'Raw material supply with exclusive sourcing rights',
    startDate: '2025-03-01',
    endDate: '2026-02-28',
  },
  DYNAMICS: {
    contractId: 'DYN-C-2025-0042',
    contractType: 'VENDOR_AGREEMENT',
    amount: 950000,
    currency: 'USD',
    vendorId: 'VEND-099',
    vendorName: 'Precision Parts Ltd',
    description: 'Component manufacturing agreement',
    startDate: '2025-06-01',
    endDate: '2026-05-31',
  },
};

const IntegrationHub = () => {
  const { theme } = useThemeStore();
  const { token } = useAuthStore();

  const [activeTab, setActiveTab] = useState('ingest');
  const [v1Health, setV1Health] = useState(null);

  // Ingest state
  const [selectedErp, setSelectedErp] = useState('SAP');
  const [ingestPayload, setIngestPayload] = useState(JSON.stringify(SAMPLE_PAYLOADS.SAP, null, 2));
  const [ingestResult, setIngestResult] = useState(null);
  const [ingestLoading, setIngestLoading] = useState(false);
  const [showPayload, setShowPayload] = useState(true);

  // Decision state
  const [decisionContractId, setDecisionContractId] = useState('4600001234');
  const [decisionErp, setDecisionErp] = useState('SAP');
  const [decisionResult, setDecisionResult] = useState(null);
  const [decisionLoading, setDecisionLoading] = useState(false);

  // Amendment state
  const [amendmentPayload, setAmendmentPayload] = useState(JSON.stringify({
    contractId: '4600001234',
    previousRiskScore: 45,
    netAmount: 3200000,
    contractType: 'MK',
    description: 'Amended IT services — added unlimited liability clause',
  }, null, 2));
  const [amendmentResult, setAmendmentResult] = useState(null);
  const [amendmentLoading, setAmendmentLoading] = useState(false);

  // ION BOD state
  const [bodXml, setBodXml] = useState(`<?xml version="1.0" encoding="UTF-8"?>
<BOD>
  <ApplicationArea>
    <Verb>Process</Verb>
    <Target>UniContractAI</Target>
  </ApplicationArea>
  <DataArea>
    <Contract>
      <ContractID>CNT-002</ContractID>
      <NetAmount>4800000</NetAmount>
      <Currency>USD</Currency>
      <VendorID>V-20017</VendorID>
      <VendorName>Global Materials Corp</VendorName>
      <ContractType>PURCHASE</ContractType>
      <Description>Raw Material Supply with Indemnity</Description>
      <ValidFrom>2025-03-01</ValidFrom>
      <ValidTo>2026-02-28</ValidTo>
    </Contract>
  </DataArea>
</BOD>`);
  const [bodResult, setBodResult] = useState(null);
  const [bodLoading, setBodLoading] = useState(false);

  const authHeaders = {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json',
  };

  useEffect(() => {
    fetch(`${API_BASE}/api/v1/health/`, { headers: authHeaders })
      .then(r => r.json())
      .then(d => setV1Health(d))
      .catch(() => setV1Health({ status: 'error' }));
  }, []);

  const handleErpChange = (erp) => {
    setSelectedErp(erp);
    setIngestPayload(JSON.stringify(SAMPLE_PAYLOADS[erp] || SAMPLE_PAYLOADS.SAP, null, 2));
  };

  const runIngest = async () => {
    setIngestLoading(true);
    setIngestResult(null);
    try {
      let body, contentType;
      try {
        body = JSON.stringify(JSON.parse(ingestPayload));
        contentType = 'application/json';
      } catch {
        body = ingestPayload;
        contentType = 'application/xml';
      }

      const res = await fetch(`${API_BASE}/api/v1/contracts/ingest/`, {
        method: 'POST',
        headers: { ...authHeaders, 'Content-Type': contentType, 'X-ERP-System': selectedErp },
        body,
      });
      setIngestResult({ data: await res.json(), ok: res.ok, ts: new Date().toLocaleTimeString() });
    } catch (e) {
      setIngestResult({ data: { error: e.message }, ok: false, ts: new Date().toLocaleTimeString() });
    } finally {
      setIngestLoading(false);
    }
  };

  const runDecision = async () => {
    setDecisionLoading(true);
    setDecisionResult(null);
    try {
      // First get status, then push decision
      const res = await fetch(`${API_BASE}/api/v1/contracts/${decisionContractId}/status/`, {
        headers: { ...authHeaders, 'X-ERP-System': decisionErp },
      });
      const statusData = await res.json();

      // Apply decision
      const decRes = await fetch(`${API_BASE}/api/v1/contracts/${decisionContractId}/decision/`, {
        method: 'POST',
        headers: { ...authHeaders, 'X-ERP-System': decisionErp },
        body: JSON.stringify({
          risk_score: statusData.risk_score,
          risk_category: statusData.risk_category,
          ai_status: statusData.ai_status,
          intent: statusData.intent,
        }),
      });
      setDecisionResult({ status: statusData, decision: await decRes.json(), ok: decRes.ok, ts: new Date().toLocaleTimeString() });
    } catch (e) {
      setDecisionResult({ data: { error: e.message }, ok: false, ts: new Date().toLocaleTimeString() });
    } finally {
      setDecisionLoading(false);
    }
  };

  const runAmendment = async () => {
    setAmendmentLoading(true);
    setAmendmentResult(null);
    try {
      let parsed;
      try { parsed = JSON.parse(amendmentPayload); } catch { parsed = {}; }
      const res = await fetch(`${API_BASE}/api/v1/events/amendment/`, {
        method: 'POST',
        headers: { ...authHeaders, 'X-ERP-System': selectedErp },
        body: JSON.stringify(parsed),
      });
      setAmendmentResult({ data: await res.json(), ok: res.ok, ts: new Date().toLocaleTimeString() });
    } catch (e) {
      setAmendmentResult({ data: { error: e.message }, ok: false, ts: new Date().toLocaleTimeString() });
    } finally {
      setAmendmentLoading(false);
    }
  };

  const runBOD = async () => {
    setBodLoading(true);
    setBodResult(null);
    try {
      const res = await fetch(`${API_BASE}/api/v1/contracts/ingest/`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/xml', 'X-ERP-System': 'INFOR' },
        body: bodXml,
      });
      setBodResult({ data: await res.json(), ok: res.ok, ts: new Date().toLocaleTimeString() });
    } catch (e) {
      setBodResult({ data: { error: e.message }, ok: false, ts: new Date().toLocaleTimeString() });
    } finally {
      setBodLoading(false);
    }
  };

  const getRiskColor = (cat) => {
    const map = { CRITICAL: 'text-red-400', HIGH: 'text-orange-400', MEDIUM: 'text-yellow-400', LOW: 'text-green-400' };
    return map[cat] || 'text-gray-400';
  };

  const tabs = [
    { key: 'ingest', label: 'Contract Ingest', icon: Send },
    { key: 'decision', label: 'Apply Decision', icon: Shield },
    { key: 'amendment', label: 'Amendment Event', icon: Activity },
    { key: 'ion', label: 'Infor ION BOD', icon: FileCode },
  ];

  return (
    <div className="min-h-screen p-6">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div>
            <div className="flex items-center gap-3 mb-1">
              <Globe className="text-blue-400" size={28} />
              <h1 className="text-3xl font-bold">Integration Hub</h1>
              <span className="px-2 py-0.5 rounded text-xs font-bold bg-blue-600 text-white">API v1</span>
            </div>
            <p className={`${theme.colors.textSecondary} text-sm`}>
              Unified multi-ERP contract intelligence — SAP · Infor · Oracle · Dynamics
            </p>
          </div>

          {/* v1 Health Badge */}
          <div className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium border ${
            v1Health?.status === 'healthy'
              ? 'bg-green-500/10 border-green-500/30 text-green-400'
              : 'bg-gray-500/10 border-gray-500/30 text-gray-400'
          }`}>
            {v1Health?.status === 'healthy' ? <CheckCircle size={16} /> : <RefreshCw size={16} className="animate-spin" />}
            {v1Health?.status === 'healthy' ? 'API v1 Online' : 'Connecting…'}
          </div>
        </div>
      </div>

      {/* ERP + Architecture Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-8">
        {ERP_OPTIONS.map(({ value, label, color, bg }) => (
          <div key={value} className={`p-4 rounded-xl border ${bg} cursor-pointer transition ${
            selectedErp === value ? 'ring-2 ring-blue-500' : ''
          }`} onClick={() => handleErpChange(value)}>
            <div className="flex items-center gap-2 mb-1">
              <Database className={color} size={18} />
              <span className={`text-sm font-semibold ${color}`}>{value}</span>
            </div>
            <p className={`text-xs ${theme.colors.textSecondary}`}>{label}</p>
          </div>
        ))}
      </div>

      {/* Architecture Flow */}
      <div className={`${theme.colors.surface} border ${theme.colors.surfaceBorder} rounded-xl p-5 mb-8`}>
        <div className="flex items-center gap-2 mb-4">
          <Cpu className="text-blue-400" size={18} />
          <h2 className="font-semibold text-sm">Bi-Directional Integration Architecture</h2>
        </div>
        <div className="flex items-center gap-2 flex-wrap text-xs">
          {['SAP S/4HANA', 'Infor ION', 'Oracle Fusion'].map((erp, i, arr) => (
            <div key={erp} className="flex items-center gap-2">
              <span className={`px-3 py-1.5 rounded-lg border ${theme.colors.surfaceBorder} font-medium`}>{erp}</span>
              {i < arr.length - 1 && <ArrowRight size={14} className="text-gray-500" />}
            </div>
          ))}
          <ArrowRight size={14} className="text-blue-400" />
          <span className="px-3 py-1.5 rounded-lg bg-blue-600/20 border border-blue-500/40 text-blue-300 font-bold">
            POST /api/v1/contracts/ingest
          </span>
          <ArrowRight size={14} className="text-blue-400" />
          <span className="px-3 py-1.5 rounded-lg bg-purple-600/20 border border-purple-500/40 text-purple-300 font-medium">
            AI Engine
          </span>
          <ArrowRight size={14} className="text-blue-400" />
          <span className="px-3 py-1.5 rounded-lg bg-green-600/20 border border-green-500/40 text-green-300 font-medium">
            CSRF+ETag → SAP Z-Fields
          </span>
        </div>
        <div className="mt-3 flex flex-wrap gap-2">
          {v1Health?.features?.map(f => (
            <span key={f} className={`text-xs px-2 py-0.5 rounded ${theme.colors.surfaceBorder} border ${theme.colors.textSecondary}`}>
              {f}
            </span>
          ))}
        </div>
      </div>

      {/* Tab Bar */}
      <div className="flex gap-2 mb-6 flex-wrap">
        {tabs.map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            onClick={() => setActiveTab(key)}
            className={`flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-medium transition ${
              activeTab === key
                ? 'bg-blue-600 text-white'
                : `${theme.colors.surface} border ${theme.colors.surfaceBorder} ${theme.colors.textSecondary} hover:border-blue-500`
            }`}
          >
            <Icon size={15} />{label}
          </button>
        ))}
      </div>

      {/* ── TAB: INGEST ─────────────────────────────────────────────────── */}
      {activeTab === 'ingest' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className={`${theme.colors.surface} border ${theme.colors.surfaceBorder} rounded-xl p-6`}>
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="font-semibold flex items-center gap-2">
                  <Send size={16} className="text-blue-400" /> Contract Ingest
                </h2>
                <p className={`text-xs mt-1 ${theme.colors.textSecondary}`}>
                  POST /api/v1/contracts/ingest — auto-detects ERP from X-ERP-System header
                </p>
              </div>
            </div>

            {/* ERP selector */}
            <div className="grid grid-cols-2 gap-2 mb-4">
              {ERP_OPTIONS.map(({ value, label, color }) => (
                <button
                  key={value}
                  onClick={() => handleErpChange(value)}
                  className={`py-2 px-3 rounded-lg border text-xs font-medium transition ${
                    selectedErp === value
                      ? 'border-blue-500 bg-blue-500/10 text-white'
                      : `border-gray-700 ${theme.colors.textSecondary} hover:border-gray-500`
                  }`}
                >
                  <span className={color}>{value}</span> — {label}
                </button>
              ))}
            </div>

            {/* Payload editor */}
            <div className="mb-4">
              <button
                onClick={() => setShowPayload(!showPayload)}
                className={`flex items-center gap-2 text-xs ${theme.colors.textSecondary} mb-2`}
              >
                {showPayload ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
                Request Payload (editable)
              </button>
              {showPayload && (
                <textarea
                  value={ingestPayload}
                  onChange={e => setIngestPayload(e.target.value)}
                  rows={12}
                  className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-xs font-mono focus:outline-none focus:border-blue-500"
                />
              )}
            </div>

            <button
              onClick={runIngest}
              disabled={ingestLoading}
              className="w-full py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {ingestLoading ? <><RefreshCw size={15} className="animate-spin" /> Sending…</> : <><Send size={15} /> Send to /api/v1/contracts/ingest</>}
            </button>
          </div>

          {/* Result Panel */}
          <div className={`${theme.colors.surface} border ${theme.colors.surfaceBorder} rounded-xl p-6`}>
            <h2 className="font-semibold mb-4 flex items-center gap-2">
              <Activity className="text-green-400" size={16} /> AI Response
            </h2>
            {!ingestResult ? (
              <div className="text-center py-20">
                <Globe className={`mx-auto mb-3 ${theme.colors.textSecondary}`} size={40} />
                <p className={`text-sm ${theme.colors.textSecondary}`}>Response will appear here</p>
              </div>
            ) : (
              <div className="space-y-4">
                <div className={`flex items-center justify-between p-3 rounded-lg border ${
                  ingestResult.ok ? 'border-green-500/30 bg-green-500/10' : 'border-red-500/30 bg-red-500/10'
                }`}>
                  <div className="flex items-center gap-2">
                    {ingestResult.ok ? <CheckCircle size={16} className="text-green-400" /> : <XCircle size={16} className="text-red-400" />}
                    <span className="font-medium text-sm">{ingestResult.ok ? 'Success' : 'Error'}</span>
                  </div>
                  <span className={`text-xs flex items-center gap-1 ${theme.colors.textSecondary}`}>
                    <Clock size={10} />{ingestResult.ts}
                  </span>
                </div>

                {ingestResult.ok && ingestResult.data && (
                  <div className="space-y-3">
                    {/* Risk summary */}
                    <div className="grid grid-cols-3 gap-2">
                      <div className={`p-3 rounded-lg border ${theme.colors.surfaceBorder} text-center`}>
                        <p className="text-2xl font-bold">{ingestResult.data.risk_score}/100</p>
                        <p className={`text-xs ${theme.colors.textSecondary}`}>Risk Score</p>
                      </div>
                      <div className={`p-3 rounded-lg border ${theme.colors.surfaceBorder} text-center`}>
                        <p className={`text-lg font-bold ${getRiskColor(ingestResult.data.risk_category)}`}>{ingestResult.data.risk_category}</p>
                        <p className={`text-xs ${theme.colors.textSecondary}`}>Category</p>
                      </div>
                      <div className={`p-3 rounded-lg border ${theme.colors.surfaceBorder} text-center`}>
                        <p className="text-sm font-bold text-blue-400">{ingestResult.data.ai_status}</p>
                        <p className={`text-xs ${theme.colors.textSecondary}`}>AI Status</p>
                      </div>
                    </div>

                    {/* ERP detected */}
                    <div className={`p-3 rounded-lg border ${theme.colors.surfaceBorder} text-xs space-y-1`}>
                      <p><span className={theme.colors.textSecondary}>ERP Detected:</span> <strong>{ingestResult.data.erp}</strong></p>
                      <p><span className={theme.colors.textSecondary}>Contract ID:</span> {ingestResult.data.contract_id}</p>
                      <p><span className={theme.colors.textSecondary}>Intent:</span> {ingestResult.data.intent}</p>
                      <p><span className={theme.colors.textSecondary}>Exposure:</span> ${ingestResult.data.exposure?.toLocaleString()}</p>
                      <p><span className={theme.colors.textSecondary}>PrimeContract ID:</span> {ingestResult.data.primeContractId}</p>
                    </div>

                    {/* ERP field updates */}
                    {ingestResult.data.erp_field_updates?.fields && (
                      <div className={`p-3 rounded-lg border ${theme.colors.surfaceBorder} text-xs`}>
                        <p className={`font-medium mb-2 flex items-center gap-1`}>
                          <Shield size={12} className="text-blue-400" />
                          {ingestResult.data.erp_field_updates.erp} Field Updates
                        </p>
                        {Object.entries(ingestResult.data.erp_field_updates.fields).map(([k, v]) => (
                          <div key={k} className="flex justify-between py-0.5">
                            <span className="text-blue-400 font-mono">{k}</span>
                            <span>{String(v)}</span>
                          </div>
                        ))}
                        {ingestResult.data.erp_field_updates.note && (
                          <p className={`mt-2 italic ${theme.colors.textSecondary}`}>
                            <Info size={10} className="inline mr-1" />
                            {ingestResult.data.erp_field_updates.note}
                          </p>
                        )}
                      </div>
                    )}

                    {/* Suggestions */}
                    {ingestResult.data.suggestions?.length > 0 && (
                      <div className={`p-3 rounded-lg border ${theme.colors.surfaceBorder} text-xs`}>
                        <p className={`font-medium mb-1 ${theme.colors.textSecondary}`}>AI Clause Suggestions</p>
                        {ingestResult.data.suggestions.map((s, i) => (
                          <div key={i} className="flex items-start gap-1.5 py-0.5">
                            <AlertTriangle size={11} className="text-yellow-400 mt-0.5 shrink-0" />
                            <span>{s}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {!ingestResult.ok && (
                  <div className="text-red-400 text-sm p-3 bg-red-500/10 rounded-lg">
                    {JSON.stringify(ingestResult.data, null, 2)}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* ── TAB: DECISION ───────────────────────────────────────────────── */}
      {activeTab === 'decision' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className={`${theme.colors.surface} border ${theme.colors.surfaceBorder} rounded-xl p-6`}>
            <h2 className="font-semibold mb-1 flex items-center gap-2">
              <Shield size={16} className="text-purple-400" /> Apply AI Decision to ERP
            </h2>
            <p className={`text-xs ${theme.colors.textSecondary} mb-5`}>
              Fetches AI status then writes back to SAP via CSRF+ETag or Infor via REST
            </p>

            <div className="space-y-4">
              <div>
                <label className={`block text-xs font-medium mb-1 ${theme.colors.textSecondary}`}>Contract ID</label>
                <input
                  value={decisionContractId}
                  onChange={e => setDecisionContractId(e.target.value)}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-purple-500"
                  placeholder="e.g. 4600001234"
                />
              </div>

              <div>
                <label className={`block text-xs font-medium mb-1 ${theme.colors.textSecondary}`}>Target ERP</label>
                <div className="grid grid-cols-2 gap-2">
                  {ERP_OPTIONS.map(({ value, label, color }) => (
                    <button
                      key={value}
                      onClick={() => setDecisionErp(value)}
                      className={`py-2 px-3 rounded-lg border text-xs transition ${
                        decisionErp === value
                          ? 'border-purple-500 bg-purple-500/10'
                          : `border-gray-700 ${theme.colors.textSecondary}`
                      }`}
                    >
                      <span className={color}>{value}</span>
                    </button>
                  ))}
                </div>
              </div>

              <button
                onClick={runDecision}
                disabled={decisionLoading}
                className="w-full py-2.5 bg-purple-600 hover:bg-purple-700 text-white rounded-lg text-sm font-medium flex items-center justify-center gap-2 disabled:opacity-50"
              >
                {decisionLoading ? <><RefreshCw size={15} className="animate-spin" /> Processing…</> : <><Shield size={15} /> Get Status + Write to {decisionErp}</>}
              </button>
            </div>
          </div>

          <div className={`${theme.colors.surface} border ${theme.colors.surfaceBorder} rounded-xl p-6`}>
            <h2 className="font-semibold mb-4">Write-Back Result</h2>
            {!decisionResult ? (
              <div className="text-center py-16">
                <Shield className={`mx-auto mb-3 ${theme.colors.textSecondary}`} size={40} />
                <p className={`text-sm ${theme.colors.textSecondary}`}>Run the decision to see CSRF+ETag write-back</p>
              </div>
            ) : (
              <div className="space-y-3 text-xs">
                {/* AI status */}
                {decisionResult.status && (
                  <div className={`p-3 rounded-lg border ${theme.colors.surfaceBorder}`}>
                    <p className={`font-medium mb-2 ${theme.colors.textSecondary}`}>AI Status (Live)</p>
                    <div className="grid grid-cols-2 gap-1">
                      <p><span className={theme.colors.textSecondary}>Risk:</span> <strong className={getRiskColor(decisionResult.status.risk_category)}>{decisionResult.status.risk_score}/100 {decisionResult.status.risk_category}</strong></p>
                      <p><span className={theme.colors.textSecondary}>Status:</span> <strong>{decisionResult.status.ai_status}</strong></p>
                    </div>
                  </div>
                )}

                {/* Write-back result */}
                {decisionResult.decision?.write_result && (
                  <div className={`p-3 rounded-lg border ${
                    decisionResult.decision.write_result.success
                      ? 'border-green-500/30 bg-green-500/10'
                      : 'border-yellow-500/30 bg-yellow-500/10'
                  }`}>
                    <p className="font-medium mb-2">
                      {decisionResult.decision.write_result.success ? '✅ Write-Back Successful' : '⚠ Write-Back (Sandbox Mode)'}
                    </p>
                    {decisionResult.decision.write_result.fields_written && (
                      <p>{decisionResult.decision.write_result.fields_written.join(', ')}</p>
                    )}
                    {decisionResult.decision.write_result.fields && (
                      <div className="space-y-0.5">
                        {Object.entries(decisionResult.decision.write_result.fields).map(([k, v]) => (
                          <div key={k} className="flex justify-between">
                            <span className="text-blue-400 font-mono">{k}</span>
                            <span>{String(v)}</span>
                          </div>
                        ))}
                      </div>
                    )}
                    {decisionResult.decision.write_result.note && (
                      <p className={`mt-1 italic ${theme.colors.textSecondary}`}>{decisionResult.decision.write_result.note}</p>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* ── TAB: AMENDMENT ─────────────────────────────────────────────── */}
      {activeTab === 'amendment' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className={`${theme.colors.surface} border ${theme.colors.surfaceBorder} rounded-xl p-6`}>
            <h2 className="font-semibold mb-1 flex items-center gap-2">
              <Activity size={16} className="text-yellow-400" /> Amendment Event
            </h2>
            <p className={`text-xs ${theme.colors.textSecondary} mb-5`}>
              POST /api/v1/events/amendment — SAP Event Mesh / Infor ION amendment trigger
            </p>
            <textarea
              value={amendmentPayload}
              onChange={e => setAmendmentPayload(e.target.value)}
              rows={10}
              className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-xs font-mono focus:outline-none focus:border-yellow-500 mb-4"
            />
            <button
              onClick={runAmendment}
              disabled={amendmentLoading}
              className="w-full py-2.5 bg-yellow-600 hover:bg-yellow-700 text-white rounded-lg text-sm font-medium flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {amendmentLoading ? <><RefreshCw size={15} className="animate-spin" /> Processing…</> : <><Zap size={15} /> Send Amendment Event</>}
            </button>
          </div>

          <div className={`${theme.colors.surface} border ${theme.colors.surfaceBorder} rounded-xl p-6`}>
            <h2 className="font-semibold mb-4">Delta Analysis</h2>
            {!amendmentResult ? (
              <div className="text-center py-16">
                <Activity className={`mx-auto mb-3 ${theme.colors.textSecondary}`} size={40} />
                <p className={`text-sm ${theme.colors.textSecondary}`}>Risk delta will appear here</p>
              </div>
            ) : (
              <div className="space-y-3 text-xs">
                <div className={`flex items-center gap-2 p-3 rounded-lg border ${
                  amendmentResult.ok ? 'border-green-500/30 bg-green-500/10' : 'border-red-500/30 bg-red-500/10'
                }`}>
                  {amendmentResult.ok ? <CheckCircle size={14} className="text-green-400" /> : <XCircle size={14} className="text-red-400" />}
                  <span>{amendmentResult.ok ? 'Amendment processed' : 'Error'}</span>
                  <span className={`ml-auto ${theme.colors.textSecondary}`}>{amendmentResult.ts}</span>
                </div>

                {amendmentResult.ok && amendmentResult.data && (
                  <>
                    <div className={`p-3 rounded-lg border ${theme.colors.surfaceBorder}`}>
                      <p className={`font-medium mb-2 ${theme.colors.textSecondary}`}>Risk Delta</p>
                      <div className="flex items-center gap-4">
                        <div className="text-center">
                          <p className="text-xl font-bold text-gray-400">{amendmentResult.data.previous_risk}</p>
                          <p className={theme.colors.textSecondary}>Before</p>
                        </div>
                        <ArrowRight className={amendmentResult.data.risk_delta > 0 ? 'text-red-400' : 'text-green-400'} size={20} />
                        <div className="text-center">
                          <p className={`text-xl font-bold ${getRiskColor(amendmentResult.data.risk_category)}`}>{amendmentResult.data.new_risk_score}</p>
                          <p className={theme.colors.textSecondary}>After</p>
                        </div>
                        <div className="text-center ml-auto">
                          <p className={`text-2xl font-bold ${amendmentResult.data.risk_delta > 0 ? 'text-red-400' : 'text-green-400'}`}>
                            {amendmentResult.data.risk_delta > 0 ? '+' : ''}{amendmentResult.data.risk_delta}
                          </p>
                          <p className={theme.colors.textSecondary}>Delta</p>
                        </div>
                      </div>
                    </div>

                    {amendmentResult.data.alert && (
                      <div className="p-3 rounded-lg border border-red-500/30 bg-red-500/10 flex items-center gap-2">
                        <AlertTriangle size={14} className="text-red-400" />
                        <span className="text-red-300 font-medium">{amendmentResult.data.message}</span>
                      </div>
                    )}

                    <div className={`p-3 rounded-lg border ${theme.colors.surfaceBorder}`}>
                      <p><span className={theme.colors.textSecondary}>New Status:</span> <strong>{amendmentResult.data.status}</strong></p>
                      <p><span className={theme.colors.textSecondary}>Category:</span> <span className={getRiskColor(amendmentResult.data.risk_category)}>{amendmentResult.data.risk_category}</span></p>
                    </div>
                  </>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* ── TAB: ION BOD ────────────────────────────────────────────────── */}
      {activeTab === 'ion' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className={`${theme.colors.surface} border ${theme.colors.surfaceBorder} rounded-xl p-6`}>
            <h2 className="font-semibold mb-1 flex items-center gap-2">
              <FileCode size={16} className="text-orange-400" /> Infor ION BOD Message
            </h2>
            <p className={`text-xs ${theme.colors.textSecondary} mb-4`}>
              XML BOD (Business Object Document) from Infor ION bus — Content-Type: application/xml
            </p>
            <div className={`mb-3 p-2 rounded-lg border text-xs ${theme.colors.surfaceBorder} ${theme.colors.textSecondary} flex items-center gap-2`}>
              <Info size={12} />
              Sent to same endpoint: POST /api/v1/contracts/ingest — auto-detected from Content-Type
            </div>
            <textarea
              value={bodXml}
              onChange={e => setBodXml(e.target.value)}
              rows={16}
              className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-xs font-mono focus:outline-none focus:border-orange-500 mb-4"
            />
            <button
              onClick={runBOD}
              disabled={bodLoading}
              className="w-full py-2.5 bg-orange-600 hover:bg-orange-700 text-white rounded-lg text-sm font-medium flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {bodLoading ? <><RefreshCw size={15} className="animate-spin" /> Parsing BOD…</> : <><Send size={15} /> Send ION BOD</>}
            </button>
          </div>

          <div className={`${theme.colors.surface} border ${theme.colors.surfaceBorder} rounded-xl p-6`}>
            <h2 className="font-semibold mb-4">BOD Parse Result</h2>
            {!bodResult ? (
              <div className="text-center py-16">
                <FileCode className={`mx-auto mb-3 ${theme.colors.textSecondary}`} size={40} />
                <p className={`text-sm ${theme.colors.textSecondary}`}>BOD parse result will appear here</p>
              </div>
            ) : (
              <div className="space-y-3 text-xs">
                <div className={`flex items-center gap-2 p-3 rounded-lg border ${
                  bodResult.ok ? 'border-green-500/30 bg-green-500/10' : 'border-red-500/30 bg-red-500/10'
                }`}>
                  {bodResult.ok ? <CheckCircle size={14} className="text-green-400" /> : <XCircle size={14} className="text-red-400" />}
                  <span>{bodResult.ok ? 'BOD Parsed & Processed' : 'Error'}</span>
                  <span className={`ml-auto ${theme.colors.textSecondary}`}>{bodResult.ts}</span>
                </div>

                {bodResult.data && (
                  <div className={`p-3 rounded-lg border ${theme.colors.surfaceBorder}`}>
                    <p className={`font-medium mb-2 ${theme.colors.textSecondary}`}>ION BOD Parse Details</p>
                    <p><span className={theme.colors.textSecondary}>Source:</span> {bodResult.data.source}</p>
                    <p><span className={theme.colors.textSecondary}>ERP:</span> {bodResult.data.erp}</p>
                    <p><span className={theme.colors.textSecondary}>Verb:</span> {bodResult.data.verb}</p>
                    <p><span className={theme.colors.textSecondary}>Contract ID:</span> {bodResult.data.contract_id}</p>
                    {bodResult.data.result && (
                      <>
                        <hr className="border-gray-700 my-2" />
                        <p><span className={theme.colors.textSecondary}>Risk Score:</span> <strong>{bodResult.data.result.risk_score}/100</strong></p>
                        <p><span className={theme.colors.textSecondary}>Category:</span> <span className={getRiskColor(bodResult.data.result.risk_category)}>{bodResult.data.result.risk_category}</span></p>
                        <p><span className={theme.colors.textSecondary}>AI Status:</span> <strong>{bodResult.data.result.ai_status}</strong></p>
                        <p><span className={theme.colors.textSecondary}>Intent:</span> {bodResult.data.result.intent}</p>
                      </>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default IntegrationHub;
