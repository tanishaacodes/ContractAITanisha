/**
 * Tender Dashboard — Premium Redesign
 */
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import tenderService from '../../services/tenderService';
import TenderOverview from './TenderOverview';
import BOQTable from './BOQTable';
import RiskAnalysis from './RiskAnalysis';
import EligibilityCheck from './EligibilityCheck';
import WinSimulation from './WinSimulation';
import MarginOptimization from './MarginOptimization';
import ProposalBuilder from './ProposalBuilder';
import NegotiationPanel from './NegotiationPanel';
import PreBidQuestions from './PreBidQuestions';
import AmendmentPanel from './AmendmentPanel';

const STATUS_META = {
  DRAFT:     { bg: 'bg-slate-700/60 text-slate-300 border-slate-600',        dot: 'bg-slate-400' },
  ANALYZING: { bg: 'bg-amber-900/40 text-amber-300 border-amber-700/50',     dot: 'bg-amber-400 animate-pulse' },
  ANALYZED:  { bg: 'bg-emerald-900/40 text-emerald-300 border-emerald-700/50', dot: 'bg-emerald-400' },
  BIDDING:   { bg: 'bg-blue-900/40 text-blue-300 border-blue-700/50',        dot: 'bg-blue-400' },
  SUBMITTED: { bg: 'bg-purple-900/40 text-purple-300 border-purple-700/50',  dot: 'bg-purple-400' },
  WON:       { bg: 'bg-green-900/40 text-green-300 border-green-700/50',     dot: 'bg-green-400' },
  LOST:      { bg: 'bg-red-900/40 text-red-300 border-red-700/50',           dot: 'bg-red-400' },
};

const TABS = [
  { id: 'overview',     label: 'Overview',          icon: (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zm10 0a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zm10 0a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" /></svg>
  )},
  { id: 'boq',          label: 'BOQ Analysis',      icon: (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" /></svg>
  )},
  { id: 'risks',        label: 'Risks & Conflicts',  icon: (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
  )},
  { id: 'eligibility',  label: 'Eligibility',        icon: (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
  )},
  { id: 'winsim',       label: 'Win Simulation',     icon: (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
  )},
  { id: 'margin',       label: 'Margin',             icon: (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
  )},
  { id: 'proposal',     label: 'Proposal',           icon: (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" /></svg>
  )},
  { id: 'negotiation',  label: 'Negotiation',        icon: (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8h2a2 2 0 012 2v6a2 2 0 01-2 2h-2v4l-4-4H9a1.994 1.994 0 01-1.414-.586m0 0L11 14h4a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2v4l.586-.586z" /></svg>
  )},
  { id: 'prebid',       label: 'Pre-Bid Q&A',        icon: (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
  )},
  { id: 'amendments',   label: 'Amendments',         icon: (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg>
  )},
];

const TenderDashboard = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [tender, setTender]     = useState(null);
  const [loading, setLoading]   = useState(true);
  const [error, setError]       = useState(null);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => { loadTenderDetails(); }, [id]);

  const loadTenderDetails = async () => {
    try {
      setLoading(true);
      const data = await tenderService.getTenderDetails(id);
      setTender(data);
      setError(null);
    } catch (err) {
      setError('Failed to load tender details');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!window.confirm('Delete this tender? This cannot be undone.')) return;
    try {
      await tenderService.deleteTender(id);
      navigate('/tenders');
    } catch {
      alert('Failed to delete tender.');
    }
  };

  /* ── Loading ── */
  if (loading) return (
    <div className="flex items-center justify-center min-h-screen bg-slate-950">
      <div className="text-center">
        <div className="relative w-16 h-16 mx-auto mb-4">
          <div className="absolute inset-0 rounded-full border-2 border-blue-500/20" />
          <div className="absolute inset-0 rounded-full border-t-2 border-blue-500 animate-spin" />
        </div>
        <p className="text-slate-500 text-sm">Loading tender intelligence…</p>
      </div>
    </div>
  );

  /* ── Error ── */
  if (error) return (
    <div className="flex items-center justify-center min-h-screen bg-slate-950">
      <div className="bg-red-900/20 border border-red-700/30 rounded-2xl p-8 text-center max-w-md">
        <div className="text-4xl mb-4">⚠️</div>
        <p className="text-red-400 mb-4">{error}</p>
        <button onClick={() => navigate('/tenders')} className="px-5 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-xl text-sm">
          Back to Tenders
        </button>
      </div>
    </div>
  );

  if (!tender) return null;

  const statusMeta = STATUS_META[tender.status] || STATUS_META.DRAFT;
  const value = tender.estimated_value
    ? `₹${(parseFloat(tender.estimated_value) / 10000000).toFixed(2)} Cr`
    : 'N/A';
  const deadline = tender.submission_deadline
    ? new Date(tender.submission_deadline).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })
    : 'N/A';
  const daysLeft = tender.submission_deadline
    ? Math.ceil((new Date(tender.submission_deadline) - new Date()) / 86400000)
    : null;

  return (
    <div className="min-h-screen bg-slate-950">

      {/* ══ Hero Header ══════════════════════════════════════════════ */}
      <div className="relative overflow-hidden bg-gradient-to-b from-slate-900 via-slate-900 to-slate-950 border-b border-slate-800/60">
        {/* ambient glow */}
        <div className="absolute -top-24 -left-24 w-96 h-96 bg-blue-600/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -top-12 right-0 w-72 h-72 bg-indigo-600/8 rounded-full blur-3xl pointer-events-none" />

        <div className="relative max-w-7xl mx-auto px-6 pt-5 pb-0">
          {/* Breadcrumb */}
          <button
            onClick={() => navigate('/tenders')}
            className="flex items-center gap-1.5 text-slate-500 hover:text-blue-400 text-sm mb-4 transition-colors"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Tender Intelligence
          </button>

          {/* Title row */}
          <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4 mb-5">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-3 mb-2 flex-wrap">
                <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold border ${statusMeta.bg}`}>
                  <span className={`w-1.5 h-1.5 rounded-full ${statusMeta.dot}`} />
                  {tender.status}
                </span>
                {tender.reference_number && (
                  <span className="text-xs text-slate-500 font-mono bg-slate-800/60 border border-slate-700/40 px-2.5 py-1 rounded-lg">
                    {tender.reference_number}
                  </span>
                )}
              </div>
              <h1 className="text-xl lg:text-2xl font-bold text-white leading-tight line-clamp-2 mb-1">
                {tender.title}
              </h1>
              {tender.organization && (
                <p className="text-slate-500 text-sm">{tender.organization}</p>
              )}
            </div>

            {/* Right: value + actions */}
            <div className="flex flex-col items-end gap-3 shrink-0">
              <div className="text-right">
                <div className="text-3xl font-bold text-white leading-none">{value}</div>
                <div className="flex items-center gap-1.5 justify-end mt-1">
                  <svg className="w-3.5 h-3.5 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                      d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                  <span className="text-xs text-slate-500">Deadline: {deadline}</span>
                  {daysLeft !== null && (
                    <span className={`text-xs font-semibold px-1.5 py-0.5 rounded ${
                      daysLeft < 0 ? 'bg-red-900/40 text-red-400' :
                      daysLeft <= 7 ? 'bg-orange-900/40 text-orange-400' :
                      daysLeft <= 30 ? 'bg-yellow-900/40 text-yellow-400' :
                      'bg-emerald-900/40 text-emerald-400'
                    }`}>
                      {daysLeft < 0 ? `${Math.abs(daysLeft)}d overdue` : `${daysLeft}d left`}
                    </span>
                  )}
                </div>
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => navigate(`/tenders/${id}/bid-management`)}
                  className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-violet-600 to-purple-600
                             hover:from-violet-500 hover:to-purple-500 text-white rounded-xl text-sm font-semibold
                             transition-all shadow-md shadow-purple-900/40"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                      d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  </svg>
                  Bid Management
                </button>
                <button
                  onClick={() => navigate(`/tenders/${id}/buyer`)}
                  className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-indigo-600 to-blue-600
                             hover:from-indigo-500 hover:to-blue-500 text-white rounded-xl text-sm font-semibold
                             transition-all shadow-md shadow-indigo-900/40"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                      d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                  Buyer Evaluation
                </button>
                <button
                  onClick={handleDelete}
                  className="flex items-center gap-1.5 px-3 py-2 bg-slate-800/60 hover:bg-red-900/30 border border-slate-700/40
                             hover:border-red-700/40 text-slate-400 hover:text-red-400 rounded-xl text-sm transition-all"
                  title="Delete Tender"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                      d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                  Delete
                </button>
              </div>
            </div>
          </div>

          {/* ── Tabs ── */}
          <div className="flex items-center gap-1 overflow-x-auto pb-0 scrollbar-none">
            {TABS.map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-4 py-2.5 rounded-t-xl text-sm font-medium whitespace-nowrap transition-all relative
                  ${activeTab === tab.id
                    ? 'bg-slate-950 text-white border-t border-l border-r border-slate-700/60 -mb-px z-10'
                    : 'text-slate-500 hover:text-slate-300 hover:bg-slate-800/40'
                  }`}
              >
                <span className={activeTab === tab.id ? 'text-blue-400' : ''}>{tab.icon}</span>
                {tab.label}
                {tab.id === 'risks' && (tender.risks?.length > 0) && (
                  <span className="w-5 h-5 rounded-full bg-red-500/20 text-red-400 text-[10px] font-bold flex items-center justify-center">
                    {tender.risks.length}
                  </span>
                )}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* ══ Tab Content ══════════════════════════════════════════════ */}
      <div className="max-w-7xl mx-auto px-6 py-6">
        {activeTab === 'overview'    && <TenderOverview tender={tender} />}
        {activeTab === 'boq'         && <BOQTable workItems={tender.work_items} tenderId={tender.id} onReanalyzed={setTender} />}
        {activeTab === 'risks'       && <RiskAnalysis risks={tender.risks} conflicts={tender.conflicts} tenderId={tender.id} onReanalyzed={setTender} />}
        {activeTab === 'eligibility' && <EligibilityCheck tenderId={tender.id} eligibility={tender.eligibility} />}
        {activeTab === 'winsim'      && <WinSimulation tenderId={tender.id} />}
        {activeTab === 'margin'      && <MarginOptimization tenderId={tender.id} scenarios={tender.bid_scenarios} />}
        {activeTab === 'proposal'    && <ProposalBuilder tenderId={tender.id} proposal={tender.proposal} />}
        {activeTab === 'negotiation' && <NegotiationPanel tenderId={tender.id} negotiations={tender.negotiations} risks={tender.risks} />}
        {activeTab === 'prebid'      && <PreBidQuestions questions={tender.prebid_questions} />}
        {activeTab === 'amendments'  && <AmendmentPanel tenderId={tender.id} amendments={tender.amendments || []} onAmendmentUploaded={u => u && setTender(u)} />}
      </div>
    </div>
  );
};

export default TenderDashboard;
