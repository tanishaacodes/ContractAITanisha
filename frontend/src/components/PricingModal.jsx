import React, { useState, useEffect } from 'react';
import { X } from 'lucide-react';
import PricingCard from './PricingCard';
import api from '../utils/api';
import useThemeStore from '../store/themeStore';

const PricingModal = ({ show, onPlanSelected }) => {
  const { theme, currentTheme } = useThemeStore();
  const isDark = currentTheme === 'dark';
  const [plans, setPlans] = useState([]);
  const [selectedPlan, setSelectedPlan] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (show) {
      fetchPricingPlans();
    }
  }, [show]);

  const fetchPricingPlans = async () => {
    try {
      setLoading(true);
      const response = await api.get('/pricing/plans');
      setPlans(response.data.plans);
    } catch (err) {
      setError('Failed to load pricing plans');
      console.error('Error fetching pricing plans:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectPlan = (plan) => {
    if (plan.isContactSales) {
      // Contact sales plans open email client (handled in PricingCard)
      return;
    }
    setSelectedPlan(plan);
  };

  const handleConfirmSelection = async () => {
    if (!selectedPlan || selectedPlan.isContactSales) {
      return;
    }

    try {
      setSubmitting(true);
      await api.post('/user/select-plan', {
        planId: selectedPlan.id
      });

      // Notify parent component that plan was selected
      onPlanSelected(selectedPlan);
    } catch (err) {
      setError('Failed to select plan. Please try again.');
      console.error('Error selecting plan:', err);
      setSubmitting(false);
    }
  };

  // Get non-contact-sales plans for the grid
  const standardPlans = plans.filter(p => !p.isContactSales);
  const contactSalesPlans = plans.filter(p => p.isContactSales);

  if (!show) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-gradient-to-br from-gray-900/97 via-blue-900/97 to-purple-900/97 backdrop-blur-md flex items-center justify-center p-4">
      <div className={`${isDark ? theme.colors.surface : 'bg-white'} rounded-3xl shadow-2xl max-w-7xl w-full max-h-[95vh] overflow-y-auto border ${isDark ? theme.colors.surfaceBorder : 'border-gray-200'}`}>
        {/* Header - Cannot close until plan selected */}
        <div className="sticky top-0 bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 px-8 py-10 rounded-t-3xl z-10 shadow-2xl">
          <div className="text-center">
            <h2 className="text-5xl font-black text-white mb-3 tracking-tight">
              Choose Your Plan
            </h2>
            <p className="text-blue-50 text-xl font-semibold">
              Select a plan to get started with Contract AI
            </p>
          </div>
        </div>

        {/* Content */}
        <div className={`px-8 py-12 ${isDark ? theme.colors.background : 'bg-gradient-to-br from-slate-50 via-white to-blue-50'}`}>
          {loading ? (
            <div className="flex items-center justify-center py-24">
              <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-blue-600 shadow-lg"></div>
            </div>
          ) : error ? (
            <div className="bg-gradient-to-r from-red-50 to-rose-50 border-2 border-red-300 rounded-2xl p-8 text-center shadow-lg">
              <p className="text-red-700 font-bold text-lg">{error}</p>
              <button
                onClick={fetchPricingPlans}
                className="mt-5 px-8 py-3 bg-red-600 text-white rounded-xl hover:bg-red-700 font-bold shadow-md hover:shadow-lg transition-all duration-200 transform hover:scale-105"
              >
                Retry
              </button>
            </div>
          ) : (
            <>
              {/* Standard Plans Grid */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-8">
                {standardPlans.map((plan, index) => (
                  <PricingCard
                    key={plan.id}
                    plan={plan}
                    isSelected={selectedPlan?.id === plan.id}
                    onSelect={handleSelectPlan}
                    isPopular={plan.planType === 'PROFESSIONAL'}
                  />
                ))}
              </div>

              {/* Contact Sales Plans */}
              {contactSalesPlans.length > 0 && (
                <>
                  <div className={`border-t-2 ${isDark ? theme.colors.surfaceBorder : 'border-gray-300'} my-12`}></div>
                  <div className="text-center mb-10">
                    <h3 className={`text-3xl font-extrabold ${isDark ? theme.colors.textPrimary : 'text-gray-900'} mb-3`}>
                      Enterprise Solutions
                    </h3>
                    <p className={`${isDark ? theme.colors.textSecondary : 'text-gray-600'} text-lg font-medium`}>
                      For large organizations with custom requirements
                    </p>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-4xl mx-auto">
                    {contactSalesPlans.map((plan) => (
                      <PricingCard
                        key={plan.id}
                        plan={plan}
                        isSelected={false}
                        onSelect={handleSelectPlan}
                      />
                    ))}
                  </div>
                </>
              )}

              {/* Confirm Button */}
              {selectedPlan && !selectedPlan.isContactSales && (
                <div className="mt-12 flex justify-center">
                  <button
                    onClick={handleConfirmSelection}
                    disabled={submitting}
                    className="px-16 py-5 bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 text-white text-xl font-extrabold rounded-xl shadow-2xl hover:from-blue-700 hover:via-indigo-700 hover:to-purple-700 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed transform hover:scale-105"
                  >
                    {submitting ? (
                      <span className="flex items-center space-x-3">
                        <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-white"></div>
                        <span>Processing...</span>
                      </span>
                    ) : (
                      `Continue with ${selectedPlan.displayName}`
                    )}
                  </button>
                </div>
              )}

              {/* Note */}
              <div className="mt-12 text-center">
                <p className={`${isDark ? theme.colors.textSecondary : 'text-gray-600'} text-base font-medium`}>
                  You can upgrade or downgrade your plan anytime from your profile settings
                </p>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default PricingModal;
