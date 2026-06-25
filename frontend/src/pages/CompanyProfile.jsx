/**
 * Company Profile Page
 * Setup/edit company details used for eligibility checks and proposals
 */
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import tenderService from '../services/tenderService';

const FIELD_GROUPS = [
  {
    title: 'Company Information',
    icon: '🏢',
    fields: [
      { key: 'company_name', label: 'Company Name', type: 'text', required: true, placeholder: 'e.g. Acme Construction Pvt. Ltd.' },
      { key: 'registration_number', label: 'Registration Number', type: 'text', placeholder: 'e.g. U45200MH2010PTC123456' },
      { key: 'years_in_business', label: 'Years in Business', type: 'number', placeholder: 'e.g. 15' },
    ],
  },
  {
    title: 'Financial Credentials',
    icon: '💰',
    fields: [
      { key: 'annual_turnover', label: 'Annual Turnover (₹)', type: 'number', required: true, placeholder: 'e.g. 500000000 (50 Cr)', hint: 'Enter in Rupees (not Crore/Lakh)' },
      { key: 'net_worth', label: 'Net Worth (₹)', type: 'number', required: true, placeholder: 'e.g. 200000000 (20 Cr)', hint: 'As per latest audited balance sheet' },
      { key: 'average_project_margin', label: 'Avg. Project Margin (%)', type: 'number', placeholder: 'e.g. 8.5' },
    ],
  },
  {
    title: 'Project Experience',
    icon: '📊',
    fields: [
      { key: 'total_projects_completed', label: 'Total Projects Completed', type: 'number', placeholder: 'e.g. 45' },
      { key: 'similar_projects_completed', label: 'Similar Projects Completed', type: 'number', required: true, placeholder: 'e.g. 12' },
      { key: 'past_win_rate', label: 'Past Tender Win Rate (0-1)', type: 'number', placeholder: 'e.g. 0.35 means 35%', hint: 'Enter as decimal between 0 and 1' },
    ],
  },
  {
    title: 'Strengths & Advantages',
    icon: '⭐',
    fields: [
      { key: 'company_strengths', label: 'Company Strengths', type: 'textarea', placeholder: 'e.g. 20 years in EPC, ISO 9001 certified, 500+ skilled workforce, in-house design team...' },
      { key: 'competitive_advantages', label: 'Competitive Advantages', type: 'textarea', placeholder: 'e.g. Strong vendor relationships, pan-India presence, pre-qualified with PSUs...' },
    ],
  },
];

const CompanyProfilePage = () => {
  const navigate = useNavigate();
  const [profile, setProfile] = useState(null);
  const [profileId, setProfileId] = useState(null);
  const [form, setForm] = useState({
    company_name: '',
    registration_number: '',
    annual_turnover: '',
    net_worth: '',
    years_in_business: '',
    total_projects_completed: '',
    similar_projects_completed: '',
    past_win_rate: '',
    average_project_margin: '',
    company_strengths: '',
    competitive_advantages: '',
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadProfile();
  }, []);

  const loadProfile = async () => {
    try {
      setLoading(true);
      const data = await tenderService.getCompanyProfile();
      const profiles = Array.isArray(data) ? data : (data.results || [data]);
      if (profiles.length > 0) {
        const p = profiles[0];
        setProfile(p);
        setProfileId(p.id);
        setForm({
          company_name: p.company_name || '',
          registration_number: p.registration_number || '',
          annual_turnover: p.annual_turnover || '',
          net_worth: p.net_worth || '',
          years_in_business: p.years_in_business || '',
          total_projects_completed: p.total_projects_completed || '',
          similar_projects_completed: p.similar_projects_completed || '',
          past_win_rate: p.past_win_rate || '',
          average_project_margin: p.average_project_margin || '',
          company_strengths: p.company_strengths || '',
          competitive_advantages: p.competitive_advantages || '',
        });
      }
    } catch (err) {
      // No profile yet — fresh form
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (key, value) => {
    setForm(prev => ({ ...prev, [key]: value }));
    setSaved(false);
  };

  const handleSave = async () => {
    if (!form.company_name) {
      setError('Company name is required');
      return;
    }
    setSaving(true);
    setError(null);
    try {
      if (profileId) {
        await tenderService.updateCompanyProfile(profileId, form);
      } else {
        const result = await tenderService.createCompanyProfile(form);
        setProfileId(result.id);
      }
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (err) {
      console.error('Save error:', err);
      setError(err.response?.data?.detail || 'Failed to save profile');
    } finally {
      setSaving(false);
    }
  };

  // Computed metrics for display
  const turnoverCr = form.annual_turnover ? (parseFloat(form.annual_turnover) / 10000000).toFixed(2) : null;
  const netWorthCr = form.net_worth ? (parseFloat(form.net_worth) / 10000000).toFixed(2) : null;

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-slate-400">Loading profile...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-900 p-6">
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={() => navigate('/tenders')}
            className="text-blue-400 hover:text-blue-300 text-sm flex items-center mb-3"
          >
            <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Back to Tenders
          </button>
          <h1 className="text-3xl font-bold text-white">Company Profile</h1>
          <p className="text-slate-400 mt-1">
            This information is used for eligibility checks, bid proposals, and win simulations
          </p>
        </div>

        {/* Profile completeness card */}
        {(turnoverCr || netWorthCr) && (
          <div className="bg-gradient-to-r from-blue-900/40 to-purple-900/40 border border-blue-700/50 rounded-lg p-5 mb-6">
            <h3 className="text-sm font-medium text-blue-300 mb-3">Your Financial Profile</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {turnoverCr && (
                <div>
                  <div className="text-xl font-bold text-white">₹{turnoverCr} Cr</div>
                  <div className="text-xs text-slate-400">Annual Turnover</div>
                </div>
              )}
              {netWorthCr && (
                <div>
                  <div className="text-xl font-bold text-white">₹{netWorthCr} Cr</div>
                  <div className="text-xs text-slate-400">Net Worth</div>
                </div>
              )}
              {form.similar_projects_completed && (
                <div>
                  <div className="text-xl font-bold text-white">{form.similar_projects_completed}</div>
                  <div className="text-xs text-slate-400">Similar Projects</div>
                </div>
              )}
              {form.past_win_rate && (
                <div>
                  <div className="text-xl font-bold text-white">{(parseFloat(form.past_win_rate) * 100).toFixed(0)}%</div>
                  <div className="text-xs text-slate-400">Win Rate</div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Form */}
        <div className="space-y-6">
          {FIELD_GROUPS.map(group => (
            <div key={group.title} className="bg-slate-800 border border-slate-700 rounded-lg p-6">
              <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <span>{group.icon}</span>
                {group.title}
              </h2>
              <div className="space-y-4">
                {group.fields.map(field => (
                  <div key={field.key}>
                    <label className="block text-sm font-medium text-slate-300 mb-1">
                      {field.label}
                      {field.required && <span className="text-red-400 ml-1">*</span>}
                    </label>
                    {field.type === 'textarea' ? (
                      <textarea
                        rows={3}
                        value={form[field.key]}
                        onChange={e => handleChange(field.key, e.target.value)}
                        placeholder={field.placeholder}
                        className="w-full px-3 py-2 bg-slate-700 border border-slate-600 text-white placeholder-slate-400 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                      />
                    ) : (
                      <input
                        type={field.type}
                        value={form[field.key]}
                        onChange={e => handleChange(field.key, e.target.value)}
                        placeholder={field.placeholder}
                        className="w-full px-3 py-2 bg-slate-700 border border-slate-600 text-white placeholder-slate-400 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      />
                    )}
                    {field.hint && (
                      <p className="text-xs text-slate-500 mt-1">{field.hint}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>

        {/* Error */}
        {error && (
          <div className="mt-4 p-4 bg-red-900/30 border border-red-700/50 rounded-lg">
            <p className="text-red-300 text-sm">{error}</p>
          </div>
        )}

        {/* Actions */}
        <div className="mt-6 flex justify-between items-center">
          <button
            onClick={() => navigate('/tenders')}
            className="px-5 py-2.5 border border-slate-600 text-slate-300 rounded-lg hover:bg-slate-700 transition-colors"
          >
            Cancel
          </button>

          <button
            onClick={handleSave}
            disabled={saving}
            className={`px-6 py-2.5 rounded-lg text-white font-medium transition-colors flex items-center gap-2 ${
              saved
                ? 'bg-green-600 hover:bg-green-700'
                : saving
                ? 'bg-slate-600 cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-700'
            }`}
          >
            {saving ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                Saving...
              </>
            ) : saved ? (
              <>
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                Saved!
              </>
            ) : (
              profileId ? 'Update Profile' : 'Save Profile'
            )}
          </button>
        </div>

        {/* Info box */}
        <div className="mt-6 p-4 bg-slate-800/50 border border-slate-700/50 rounded-lg">
          <h4 className="text-sm font-medium text-slate-300 mb-2">How this is used</h4>
          <ul className="text-xs text-slate-400 space-y-1">
            <li>• <span className="text-slate-300">Eligibility Check</span> — turnover, net worth &amp; project count vs tender requirements</li>
            <li>• <span className="text-slate-300">Proposal Builder</span> — company strengths auto-inserted into proposal sections</li>
            <li>• <span className="text-slate-300">Win Simulation</span> — past win rate and competitiveness factor used in probability model</li>
            <li>• <span className="text-slate-300">Margin Optimizer</span> — average margin history informs optimal bid price recommendation</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default CompanyProfilePage;
