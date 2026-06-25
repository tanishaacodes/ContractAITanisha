import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { ArrowLeft, Shield, CheckCircle, XCircle, Clock, TrendingDown } from 'lucide-react';
import ExposureCard from '../../components/enterprise/metrics/ExposureCard';

export default function InsurancePolicyDashboard() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const contractId = searchParams.get('contractId') || 'CONTRACT_X';

  const [loading, setLoading] = useState(true);
  const [policies, setPolicies] = useState([]);
  const [summary, setSummary] = useState({
    totalCoverage: 0,
    activePolicies: 0,
    annualPremium: 0,
    netCoverage: 0
  });

  useEffect(() => {
    // TODO: Create API endpoint to fetch insurance policies
    // For now, using mock data
    loadPolicies();
  }, [contractId]);

  const loadPolicies = () => {
    // Mock data - replace with actual API call
    const mockPolicies = [
      {
        id: '1',
        policyNumber: 'POL-2024-001',
        policyType: 'GENERAL_LIABILITY',
        insurerName: "Lloyd's of London",
        coverageAmount: 50000000,
        deductible: 1000000,
        premiumAnnual: 500000,
        effectiveDate: '2024-01-01',
        expiryDate: '2025-01-01',
        status: 'ACTIVE',
        coversUnlimitedLiability: true,
        coversGeoPoliticalRisk: false,
        coversSupplyChainDisruption: true
      },
      {
        id: '2',
        policyNumber: 'POL-2024-002',
        policyType: 'PROFESSIONAL_INDEMNITY',
        insurerName: 'AIG Insurance',
        coverageAmount: 25000000,
        deductible: 500000,
        premiumAnnual: 300000,
        effectiveDate: '2024-01-01',
        expiryDate: '2025-01-01',
        status: 'ACTIVE',
        coversUnlimitedLiability: false,
        coversGeoPoliticalRisk: true,
        coversSupplyChainDisruption: false
      }
    ];

    const totalCoverage = mockPolicies.reduce((sum, p) => sum + p.coverageAmount, 0);
    const totalDeductible = mockPolicies.reduce((sum, p) => sum + p.deductible, 0);
    const activePolicies = mockPolicies.filter(p => p.status === 'ACTIVE').length;
    const annualPremium = mockPolicies.reduce((sum, p) => sum + p.premiumAnnual, 0);

    setSummary({
      totalCoverage,
      activePolicies,
      annualPremium,
      netCoverage: totalCoverage - totalDeductible
    });

    setPolicies(mockPolicies);
    setLoading(false);
  };

  const getPolicyTypeLabel = (type) => {
    const labels = {
      'GENERAL_LIABILITY': 'General Liability',
      'PROFESSIONAL_INDEMNITY': 'Professional Indemnity',
      'PRODUCT_LIABILITY': 'Product Liability',
      'CYBER_LIABILITY': 'Cyber Liability',
      'POLITICAL_RISK': 'Political Risk',
      'TRADE_CREDIT': 'Trade Credit'
    };
    return labels[type] || type;
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'ACTIVE':
        return <CheckCircle className="w-5 h-5 text-green-400" />;
      case 'EXPIRED':
        return <XCircle className="w-5 h-5 text-red-400" />;
      case 'PENDING':
        return <Clock className="w-5 h-5 text-yellow-400" />;
      default:
        return <XCircle className="w-5 h-5 text-gray-400" />;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
        <div className="text-white">Loading insurance policies...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/enterprise/risk-dashboard')}
            className="p-3 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 hover:border-violet-500/50 transition-all"
          >
            <ArrowLeft className="w-5 h-5 text-slate-400" />
          </button>
          <div className="flex items-center gap-3">
            <div className="p-3 rounded-xl bg-gradient-to-br from-emerald-500/20 to-teal-500/20 border border-emerald-500/30">
              <Shield className="w-8 h-8 text-emerald-400" />
            </div>
            <div>
              <h1 className="text-3xl font-black text-transparent bg-clip-text bg-gradient-to-r from-white via-emerald-200 to-teal-300">
                Insurance Policy Dashboard
              </h1>
              <p className="text-slate-400 text-sm">
                Liability Coverage & Risk Transfer
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <ExposureCard
          title="Total Coverage"
          value={`₹${(summary.totalCoverage / 1000000).toFixed(1)}M`}
          subtitle="Maximum protection"
          icon={Shield}
          color="emerald"
        />

        <ExposureCard
          title="Net Coverage"
          value={`₹${(summary.netCoverage / 1000000).toFixed(1)}M`}
          subtitle="After deductibles"
          icon={CheckCircle}
          color="teal"
        />

        <ExposureCard
          title="Active Policies"
          value={summary.activePolicies}
          subtitle="Currently in force"
          icon={CheckCircle}
          color="cyan"
        />

        <ExposureCard
          title="Annual Premium"
          value={`₹${(summary.annualPremium / 1000000).toFixed(2)}M`}
          subtitle="Total cost"
          icon={TrendingDown}
          color="blue"
        />
      </div>

      {/* Policies List */}
      <div className="bg-gradient-to-br from-slate-800/60 to-slate-900/60 backdrop-blur-xl border border-emerald-500/20 rounded-2xl p-6 shadow-[0_0_30px_rgba(16,185,129,0.15)]">
        <h3 className="text-xl font-bold text-white mb-6">Active Insurance Policies</h3>

        <div className="space-y-4">
          {policies.map((policy) => (
            <div
              key={policy.id}
              className="bg-slate-800/50 rounded-xl p-6 border border-slate-700 hover:border-emerald-500/50 transition-all"
            >
              <div className="flex items-start justify-between mb-4">
                <div>
                  <div className="flex items-center gap-3 mb-2">
                    {getStatusIcon(policy.status)}
                    <h4 className="text-lg font-bold text-white">{policy.policyNumber}</h4>
                    <span className="px-3 py-1 rounded-full bg-emerald-500/20 text-emerald-300 text-xs font-semibold">
                      {getPolicyTypeLabel(policy.policyType)}
                    </span>
                  </div>
                  <p className="text-slate-400 text-sm">{policy.insurerName}</p>
                </div>

                <div className="text-right">
                  <p className="text-2xl font-bold text-emerald-400">
                    ₹{(policy.coverageAmount / 1000000).toFixed(1)}M
                  </p>
                  <p className="text-xs text-slate-500">Coverage Amount</p>
                </div>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                <div>
                  <p className="text-xs text-slate-500">Deductible</p>
                  <p className="text-sm font-semibold text-white">
                    ₹{(policy.deductible / 1000000).toFixed(2)}M
                  </p>
                </div>

                <div>
                  <p className="text-xs text-slate-500">Annual Premium</p>
                  <p className="text-sm font-semibold text-white">
                    ₹{(policy.premiumAnnual / 1000000).toFixed(2)}M
                  </p>
                </div>

                <div>
                  <p className="text-xs text-slate-500">Effective Date</p>
                  <p className="text-sm font-semibold text-white">{policy.effectiveDate}</p>
                </div>

                <div>
                  <p className="text-xs text-slate-500">Expiry Date</p>
                  <p className="text-sm font-semibold text-white">{policy.expiryDate}</p>
                </div>
              </div>

              {/* Coverage Flags */}
              <div className="flex flex-wrap gap-2">
                {policy.coversUnlimitedLiability && (
                  <span className="px-2 py-1 rounded bg-red-500/20 text-red-300 text-xs">
                    ✓ Unlimited Liability
                  </span>
                )}
                {policy.coversGeoPoliticalRisk && (
                  <span className="px-2 py-1 rounded bg-amber-500/20 text-amber-300 text-xs">
                    ✓ Geo-Political Risk
                  </span>
                )}
                {policy.coversSupplyChainDisruption && (
                  <span className="px-2 py-1 rounded bg-cyan-500/20 text-cyan-300 text-xs">
                    ✓ Supply Chain Disruption
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>

        {policies.length === 0 && (
          <div className="text-center py-12">
            <Shield className="w-16 h-16 text-slate-600 mx-auto mb-4" />
            <p className="text-slate-400">No insurance policies found for this contract</p>
          </div>
        )}
      </div>
    </div>
  );
}
