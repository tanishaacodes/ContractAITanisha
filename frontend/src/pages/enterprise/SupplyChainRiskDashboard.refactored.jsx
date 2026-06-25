/**
 * REFACTORED VERSION - Supply Chain Risk Dashboard
 * Demonstrates using shared hooks, components, and utilities
 *
 * BENEFITS:
 * - 50+ lines of boilerplate removed
 * - Consistent behavior across all enterprise pages
 * - Easier to maintain and test
 * - Clear separation of concerns
 */
import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Users, Package, AlertCircle, Globe, Shield,
  TrendingUp, TrendingDown, Zap, ChevronDown, ChevronUp, X
} from 'lucide-react';
import CytoscapeComponent from 'react-cytoscapejs';

// Shared hooks
import { useContractSelector } from '../../hooks/useContractSelector';
import { useEnterpriseData } from '../../hooks/useEnterpriseData';

// Shared components
import LoadingScreen from '../../components/shared/LoadingScreen';
import ErrorScreen from '../../components/shared/ErrorScreen';
import PageContainer from '../../components/shared/PageContainer';
import ExposureCard from '../../components/enterprise/metrics/ExposureCard';

// Services & Utils
import enterpriseRiskService from '../../services/enterpriseRiskService';
import { getRiskColor, getRiskLabel, getRiskBadgeClasses } from '../../utils/riskUtils';

const TIER_COLOR  = { 1: '#06b6d4', 2: '#8b5cf6', 3: '#f59e0b' };
const TIER_LABEL  = { 1: 'Direct', 2: 'Indirect', 3: 'Deep-tier' };

export default function SupplyChainRiskDashboard() {
  const navigate = useNavigate();

  // ✅ Use shared hook for contract selection (replaces 10 lines)
  const { contractId, handleContractSelect } = useContractSelector();

  // Component state
  const [selectedNode, setSelectedNode] = useState(null);
  const [sortBy, setSortBy] = useState('risk');
  const [sortAsc, setSortAsc] = useState(false);
  const [filterRisk, setFilterRisk] = useState('ALL');
  const cyRef = useRef(null);

  // ✅ Use shared hook for data fetching (replaces 30+ lines of loading/error logic)
  const { loading, data, error, refetch, setData } = useEnterpriseData(
    () => loadSupplyChainData(),
    [contractId]
  );

  // Cleanup Cytoscape on unmount
  useEffect(() => () => {
    if (cyRef.current && !cyRef.current.destroyed()) {
      try { cyRef.current.destroy(); } catch {}
    }
  }, []);

  const loadSupplyChainData = async () => {
    const api = await enterpriseRiskService.getSupplyChainRisk(contractId);

    const rawSuppliers = (api.nodes || [])
      .filter(n => n.type === 'supplier')
      .map(n => ({
        ...n,
        risk_score: n.risk === 'CRITICAL' ? 0.95
                  : n.risk === 'HIGH'     ? 0.78
                  : n.risk === 'MEDIUM'   ? 0.48
                  : 0.2,
        dependency_score: n.dependency_level === 'CRITICAL' ? 0.9
                        : n.dependency_level === 'HIGH'     ? 0.7
                        : 0.4,
        tier_num: n.tier || 1,
      }));

    const td = api.tier_distribution || {};

    return {
      total_suppliers: api.total_suppliers || rawSuppliers.length,
      high_risk: rawSuppliers.filter(s => s.risk_score >= 0.7).length,
      single_source: api.single_source_count || 0,
      avg_risk: rawSuppliers.length
        ? rawSuppliers.reduce((s, x) => s + x.risk_score, 0) / rawSuppliers.length
        : 0,
      total_exposure: rawSuppliers.reduce((s, x) => s + (x.exposure || 0), 0),
      tier_breakdown: { tier1: td.tier_1 || 0, tier2: td.tier_2 || 0, tier3: td.tier_3 || 0 },
      single_source_list: api.single_source_suppliers || [],
      suppliers: rawSuppliers,
      contract_node: (api.nodes || []).find(n => n.type === 'contract') || null,
      links: api.links || [],
    };
  };

  const buildElements = () => {
    if (!data) return [];
    const elems = [];

    const hubId = data.contract_node ? data.contract_node.id : '__hub__';
    const hubLabel = data.contract_node
      ? (data.contract_node.name || 'Contract').substring(0, 16)
      : (contractId ? 'Hub' : 'Portfolio');
    elems.push({ data: { id: hubId, label: hubLabel, type: 'contract', _color: '#a78bfa', _size: 70 }});

    data.suppliers.forEach(s => {
      const color = getRiskColor(s.risk_score); // ✅ Use shared utility
      const tier  = s.tier_num || 1;
      const sz    = Math.round(32 + s.risk_score * 20);
      elems.push({ data: {
        id: s.id,
        label: (s.name || '').substring(0, 14),
        type: 'supplier',
        tier,
        risk: s.risk_score,
        exposure: s.exposure || 0,
        country: s.country || '',
        single: s.is_single_source || false,
        _color: color,
        _size: sz,
      }});
      elems.push({ data: { id: `hub-${s.id}`, source: hubId, target: s.id, _tier: tier }});
    });

    data.links.forEach((l, i) => {
      if (l.source !== hubId && l.target !== hubId) {
        elems.push({ data: { id: `link-${i}`, source: l.source, target: l.target, _tier: 0 }});
      }
    });

    return elems;
  };

  const cytoscapeStylesheet = [
    { selector: 'node', style: { opacity: 1 } },
    { selector: 'node:selected', style: { opacity: 1 } },
    { selector: 'node:unselected', style: { opacity: 1 } },
    { selector: 'edge', style: { opacity: 1 } },
    { selector: 'edge:selected', style: { opacity: 1 } },
    { selector: 'edge:unselected', style: { opacity: 1 } },
    {
      selector: 'node',
      style: {
        'background-color': 'data(_color)',
        'width': 'data(_size)',
        'height': 'data(_size)',
        'label': 'data(label)',
        'color': '#e2e8f0',
        'text-valign': 'bottom',
        'text-halign': 'center',
        'text-margin-y': 8,
        'font-size': 11,
        'font-weight': 600,
        'text-background-color': '#1e293b',
        'text-background-opacity': 0.85,
        'text-background-padding': 3,
        'border-width': 2,
        'border-color': '#475569'
      }
    },
    {
      selector: 'edge',
      style: {
        'width': 2,
        'line-color': ele => {
          const t = ele.data('_tier');
          return t === 1 ? '#06b6d4' : t === 2 ? '#8b5cf6' : '#64748b';
        },
        'target-arrow-color': ele => {
          const t = ele.data('_tier');
          return t === 1 ? '#06b6d4' : t === 2 ? '#8b5cf6' : '#64748b';
        },
        'target-arrow-shape': 'triangle',
        'curve-style': 'bezier',
        'opacity': 0.6
      }
    }
  ];

  const filteredSuppliers = data?.suppliers.filter(s => {
    if (filterRisk === 'ALL') return true;
    if (filterRisk === 'HIGH') return s.risk_score >= 0.7;
    if (filterRisk === 'MEDIUM') return s.risk_score >= 0.4 && s.risk_score < 0.7;
    if (filterRisk === 'LOW') return s.risk_score < 0.4;
    return true;
  }).sort((a, b) => {
    const field = sortBy === 'risk' ? 'risk_score' : sortBy === 'exposure' ? 'exposure' : 'tier_num';
    const aVal = a[field] || 0;
    const bVal = b[field] || 0;
    return sortAsc ? aVal - bVal : bVal - aVal;
  }) || [];

  // ✅ Use shared LoadingScreen component (replaces 15 lines)
  if (loading) {
    return <LoadingScreen message="Loading Supply Chain Risk Data..." />;
  }

  // ✅ Use shared ErrorScreen component (replaces 20 lines)
  if (error) {
    return <ErrorScreen error={error} onRetry={refetch} title="Error Loading Supply Chain Data" />;
  }

  // ✅ Use PageContainer for consistent layout (replaces 30 lines)
  return (
    <PageContainer
      title="Supply Chain Risk Intelligence"
      subtitle="Multi-tier supplier risk & dependency analysis"
      icon={Package}
      contractId={contractId}
      onContractSelect={handleContractSelect}
    >
      {/* Summary Cards */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <ExposureCard
          title="Total Suppliers"
          value={data.total_suppliers}
          icon={Users}
          trend={0}
          color="cyan"
        />
        <ExposureCard
          title="High Risk"
          value={data.high_risk}
          icon={AlertCircle}
          trend={0}
          color="red"
        />
        <ExposureCard
          title="Single Source"
          value={data.single_source}
          icon={Zap}
          trend={0}
          color="amber"
        />
        <ExposureCard
          title="Avg Risk Score"
          value={(data.avg_risk * 100).toFixed(1) + '%'}
          icon={Shield}
          trend={0}
          color="purple"
        />
      </div>

      {/* Network Graph */}
      <div className="bg-slate-800/50 backdrop-blur-sm rounded-2xl p-6 border border-slate-700/50 mb-6">
        <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
          <Globe className="w-5 h-5 text-cyan-400" />
          Supply Chain Network
        </h3>
        <div className="relative">
          <CytoscapeComponent
            elements={buildElements()}
            stylesheet={cytoscapeStylesheet}
            style={{ width: '100%', height: '500px', background: '#0f172a', borderRadius: '12px' }}
            cy={cy => { cyRef.current = cy; }}
            layout={{ name: 'cose', animate: true, animationDuration: 500 }}
          />
        </div>
      </div>

      {/* Supplier Table */}
      <div className="bg-slate-800/50 backdrop-blur-sm rounded-2xl p-6 border border-slate-700/50">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xl font-bold">Supplier Details</h3>
          <div className="flex gap-2">
            <select
              value={filterRisk}
              onChange={e => setFilterRisk(e.target.value)}
              className="px-3 py-1.5 bg-slate-700 rounded-lg text-sm"
            >
              <option value="ALL">All Risk Levels</option>
              <option value="HIGH">High Risk</option>
              <option value="MEDIUM">Medium Risk</option>
              <option value="LOW">Low Risk</option>
            </select>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-700">
                <th className="text-left py-3 px-4 text-slate-400 font-semibold">Supplier</th>
                <th className="text-left py-3 px-4 text-slate-400 font-semibold">Risk</th>
                <th className="text-left py-3 px-4 text-slate-400 font-semibold">Tier</th>
                <th className="text-left py-3 px-4 text-slate-400 font-semibold">Exposure</th>
                <th className="text-left py-3 px-4 text-slate-400 font-semibold">Country</th>
              </tr>
            </thead>
            <tbody>
              {filteredSuppliers.map(s => (
                <tr key={s.id} className="border-b border-slate-700/50 hover:bg-slate-700/30">
                  <td className="py-3 px-4">{s.name}</td>
                  <td className="py-3 px-4">
                    <span className={`px-2 py-1 rounded-lg text-xs font-semibold border ${getRiskBadgeClasses(s.risk_score)}`}>
                      {getRiskLabel(s.risk_score)}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <span className="text-sm" style={{ color: TIER_COLOR[s.tier_num] }}>
                      {TIER_LABEL[s.tier_num]}
                    </span>
                  </td>
                  <td className="py-3 px-4">${(s.exposure || 0).toLocaleString()}</td>
                  <td className="py-3 px-4 text-slate-400">{s.country}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </PageContainer>
  );
}
