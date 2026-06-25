import { useState, useEffect } from 'react';
import axios from 'axios';
import PaymentSelection from '../../components/payments/PaymentSelection';
import { Check, Crown, Zap, TrendingUp } from 'lucide-react';
import { config } from '../../config/api.config';

/**
 * Subscription & Pricing Page
 * Displays pricing plans and handles subscription upgrades
 */
export default function SubscriptionPage() {
  const [plans, setPlans] = useState([]);
  const [currentSubscription, setCurrentSubscription] = useState(null);
  const [selectedPlan, setSelectedPlan] = useState(null);
  const [billingCycle, setBillingCycle] = useState('MONTHLY');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const token = localStorage.getItem('token');
      const headers = { 'Authorization': `Bearer ${token}` };

      // Fetch pricing plans (required)
      const plansRes = await axios.get(config.PRICING_PLANS_URL, { headers });
      setPlans(plansRes.data.plans || []);

      // Try to fetch current subscription (optional - may fail if endpoint doesn't exist yet)
      try {
        const subscriptionRes = await axios.get(config.CURRENT_SUBSCRIPTION_URL, { headers });
        setCurrentSubscription(subscriptionRes.data.subscription);
      } catch (subErr) {
        console.log('Subscription endpoint not available yet - using user plan from auth');
        // Subscription endpoint doesn't exist, will use current plan from user object
        setCurrentSubscription(null);
      }

      setLoading(false);
    } catch (err) {
      console.error('Error fetching data:', err);
      setError(err.response?.data?.error || 'Failed to load subscription data');
      setLoading(false);
    }
  };

  const getPlanIcon = (planType) => {
    const type = (planType || '').toUpperCase();
    switch (type) {
      case 'FREE':
        return <Zap className="w-6 h-6" />;
      case 'STANDARD':
        return <TrendingUp className="w-6 h-6" />;
      case 'PROFESSIONAL':
        return <Crown className="w-6 h-6" />;
      default:
        return <Check className="w-6 h-6" />;
    }
  };

  const handleSelectPlan = (plan) => {
    const planType = (plan.planType || plan.plan_type || '').toUpperCase();
    if (planType === 'FREE') {
      // Handle free plan selection (no payment needed)
      upgradeToFreePlan(plan);
    } else {
      setSelectedPlan(plan);
    }
  };

  const upgradeToFreePlan = async (plan) => {
    try {
      const token = localStorage.getItem('token');
      await axios.post(
        config.SELECT_PLAN_URL,
        { planId: plan.id },
        { headers: { 'Authorization': `Bearer ${token}` } }
      );
      alert('Plan updated successfully!');
      fetchData();
    } catch (err) {
      alert(err.response?.data?.error || err.response?.data?.message || 'Failed to update plan');
    }
  };

  const handlePaymentSuccess = () => {
    setSelectedPlan(null);
    fetchData();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <p className="text-red-600 mb-4">{error}</p>
          <button
            onClick={fetchData}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  // If a plan is selected, show payment page
  if (selectedPlan) {
    return (
      <div className="min-h-screen bg-gray-50 py-12 px-4">
        <div className="max-w-4xl mx-auto">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900">Complete Your Purchase</h1>
            <p className="text-gray-600 mt-2">
              You're upgrading to {selectedPlan.displayName || selectedPlan.display_name}
            </p>
          </div>
          <PaymentSelection
            plan={selectedPlan}
            billingCycle={billingCycle}
            onSuccess={handlePaymentSuccess}
            onCancel={() => setSelectedPlan(null)}
          />
        </div>
      </div>
    );
  }

  // Main pricing page
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 py-12 px-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Choose Your Plan
          </h1>
          <p className="text-lg text-gray-600 mb-8">
            Unlock more features and increase your contract limits
          </p>

          {/* Current Plan Badge */}
          {currentSubscription && (
            <div className="inline-block bg-green-100 text-green-800 px-6 py-2 rounded-full">
              Current Plan: <strong>{currentSubscription.plan.name}</strong>
            </div>
          )}
        </div>

        {/* Billing Cycle Toggle */}
        <div className="flex justify-center mb-12">
          <div className="bg-white rounded-lg p-1 inline-flex shadow-md">
            <button
              onClick={() => setBillingCycle('MONTHLY')}
              className={`px-6 py-2 rounded-md transition-colors ${
                billingCycle === 'MONTHLY'
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-700 hover:text-gray-900'
              }`}
            >
              Monthly
            </button>
            <button
              onClick={() => setBillingCycle('YEARLY')}
              className={`px-6 py-2 rounded-md transition-colors relative ${
                billingCycle === 'YEARLY'
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-700 hover:text-gray-900'
              }`}
            >
              Yearly
              <span className="absolute -top-2 -right-2 bg-green-500 text-white text-xs px-2 py-0.5 rounded-full">
                Save 20%
              </span>
            </button>
          </div>
        </div>

        {/* Pricing Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {plans.map((plan) => {
            const priceMonthly = plan.priceMonthly || plan.price_monthly || 0;
            const price = billingCycle === 'YEARLY'
              ? priceMonthly * 12 * 0.8 // 20% discount for yearly
              : priceMonthly;

            const isCurrentPlan = currentSubscription?.plan.id === plan.id;
            const planType = (plan.planType || plan.plan_type || '').toUpperCase();
            const isProfessional = planType === 'PROFESSIONAL';

            return (
              <div
                key={plan.id}
                className={`bg-white rounded-xl shadow-lg overflow-hidden transform transition-all duration-300 hover:scale-105 ${
                  isProfessional ? 'border-4 border-blue-600 relative' : 'border border-gray-200'
                }`}
              >
                {/* Current Plan Badge */}
                {isProfessional && (
                  <div className="absolute top-0 right-0 bg-blue-600 text-white px-4 py-1 text-xs font-semibold">
                    CURRENT PLAN
                  </div>
                )}

                {/* Plan Header */}
                <div className={`p-8 ${isProfessional ? 'bg-gradient-to-br from-blue-600 to-indigo-600 text-white' : 'bg-gray-50'}`}>
                  <div className="flex items-center mb-4">
                    <div className={isProfessional ? 'text-white' : 'text-blue-600'}>
                      {getPlanIcon(planType)}
                    </div>
                    <h3 className={`ml-3 text-2xl font-bold ${isProfessional ? 'text-white' : 'text-gray-900'}`}>
                      {plan.displayName || plan.display_name}
                    </h3>
                  </div>
                  <div className="mb-4">
                    <span className={`text-4xl font-bold ${isProfessional ? 'text-white' : 'text-gray-900'}`}>
                      ${price.toFixed(0)}
                    </span>
                    <span className={`ml-2 ${isProfessional ? 'text-blue-100' : 'text-gray-600'}`}>
                      /{billingCycle === 'YEARLY' ? 'year' : 'month'}
                    </span>
                  </div>
                  <p className={`text-sm ${isProfessional ? 'text-blue-100' : 'text-gray-600'}`}>
                    {plan.description || 'Perfect for your needs'}
                  </p>
                </div>

                {/* Features */}
                <div className="p-8">
                  <div className="mb-6">
                    <div className="text-sm font-semibold text-gray-700 mb-2">Contract Limit:</div>
                    <div className="text-2xl font-bold text-blue-600">
                      {(plan.contractLimit ?? plan.contract_limit) === -1 ? 'Unlimited' : (plan.contractLimit ?? plan.contract_limit)} contracts
                    </div>
                  </div>

                  <ul className="space-y-3 mb-8">
                    {plan.features && plan.features.map((feature, idx) => (
                      <li key={idx} className="flex items-start">
                        <Check className="w-5 h-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" />
                        <span className="text-gray-700">{feature}</span>
                      </li>
                    ))}
                  </ul>

                  {/* CTA Button */}
                  <button
                    onClick={() => handleSelectPlan(plan)}
                    disabled={isCurrentPlan}
                    className={`w-full py-3 px-6 rounded-lg font-semibold transition-colors ${
                      isCurrentPlan
                        ? 'bg-gray-200 text-gray-500 cursor-not-allowed'
                        : isProfessional
                        ? 'bg-blue-600 text-white hover:bg-blue-700'
                        : 'bg-gray-900 text-white hover:bg-gray-800'
                    }`}
                  >
                    {isCurrentPlan ? 'Current Plan' : planType === 'FREE' ? 'Select Plan' : 'Upgrade Now'}
                  </button>
                </div>
              </div>
            );
          })}
        </div>

        {/* FAQ or Additional Info */}
        <div className="mt-16 bg-white rounded-xl shadow-lg p-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Frequently Asked Questions</h2>
          <div className="space-y-4">
            <div>
              <h3 className="font-semibold text-gray-900 mb-2">Can I change my plan later?</h3>
              <p className="text-gray-600">Yes, you can upgrade or downgrade your plan at any time from this page.</p>
            </div>
            <div>
              <h3 className="font-semibold text-gray-900 mb-2">What payment methods do you accept?</h3>
              <p className="text-gray-600">We accept all major credit cards (Visa, Mastercard, Amex) via Stripe and PayPal payments.</p>
            </div>
            <div>
              <h3 className="font-semibold text-gray-900 mb-2">Is there a free trial?</h3>
              <p className="text-gray-600">Yes! Our Free plan allows you to try ContractAI with up to 5 contracts at no cost.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
