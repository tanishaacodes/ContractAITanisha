import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import PaymentSelection from '../components/payments/PaymentSelection';
import { Check, Crown, Zap, TrendingUp, AlertCircle, CheckCircle, Sparkles, ArrowRight, ArrowLeft, Star, Calendar, Clock } from 'lucide-react';
import useAuthStore from '../store/authStore';
import useThemeStore from '../store/themeStore';
import { config } from '../config/api.config';

export default function MyPlan() {
  const [plans, setPlans] = useState([]);
  const [currentSubscription, setCurrentSubscription] = useState(null);
  const [selectedPlan, setSelectedPlan] = useState(null);
  const [billingCycle, setBillingCycle] = useState('MONTHLY');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [contractsCount, setContractsCount] = useState(0);
  const { user } = useAuthStore();
  const { theme } = useThemeStore();
  const navigate = useNavigate();

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const token = localStorage.getItem('token');
      const headers = { 'Authorization': `Bearer ${token}` };

      // Fetch pricing plans
      const plansRes = await axios.get(config.PRICING_PLANS_URL, { headers });
      setPlans(plansRes.data.plans || []);

      // Try to fetch current subscription
      try {
        const subscriptionRes = await axios.get(config.CURRENT_SUBSCRIPTION_URL, { headers });
        setCurrentSubscription(subscriptionRes.data.subscription);
      } catch (subErr) {
        console.log('Subscription endpoint not available yet');
        setCurrentSubscription(null);
      }

      // Fetch actual contracts count
      try {
        const contractsRes = await axios.get(config.CONTRACTS_LIST_URL, { headers });
        console.log('Contracts API Response:', contractsRes.data);
        // API returns { count: number, contracts: [] }
        const count = contractsRes.data?.count || contractsRes.data?.contracts?.length || 0;
        console.log('Setting contracts count to:', count);
        setContractsCount(count);
      } catch (contractErr) {
        console.error('Could not fetch contracts count:', contractErr);
        console.log('User data:', user);
        // Fallback to user data if available
        const fallbackCount = user?.totalContractsUploaded || user?.total_contracts_uploaded || 0;
        console.log('Using fallback count:', fallbackCount);
        setContractsCount(fallbackCount);
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

  const handlePaymentSuccess = async () => {
    // Refresh user data from auth store to get updated plan
    await useAuthStore.getState().fetchCurrentUser();
    // Also fetch subscription data
    await fetchData();
    // Clear selected plan to go back to main page
    setSelectedPlan(null);
    // Show success message
    alert('Payment successful! Your plan has been upgraded.');
  };

  // Get current plan usage info
  const getUsagePercentage = () => {
    if (!user?.currentPlan || user.currentPlan.contractLimit === -1) return 0;
    return (contractsCount / user.currentPlan.contractLimit) * 100;
  };

  const isLimitReached = () => {
    if (!user?.currentPlan || user.currentPlan.contractLimit === -1) return false;
    return contractsCount >= user.currentPlan.contractLimit;
  };

  if (loading) {
    return (
      <div className={`flex items-center justify-center min-h-screen ${theme.colors.background}`}>
        <div>
          <div className={`animate-spin rounded-full h-16 w-16 border-t-4 border-b-4 ${theme.colors.primaryBorder} mx-auto mb-4`}></div>
          <p className={`${theme.colors.textSecondary} text-center`}>Loading plans...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`flex items-center justify-center min-h-screen ${theme.colors.background}`}>
        <div className={`text-center ${theme.colors.surface} p-8 rounded-xl ${theme.colors.shadow} max-w-md`}>
          <AlertCircle className={`w-16 h-16 ${theme.colors.dangerText} mx-auto mb-4`} />
          <p className={`${theme.colors.textPrimary} mb-4`}>{error}</p>
          <button
            onClick={fetchData}
            className={`${theme.colors.primarySolid} text-white px-8 py-3 rounded-lg font-semibold transition-all hover:opacity-90 hover:scale-105`}
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
      <div className={`min-h-screen ${theme.colors.background} py-12 px-4`}>
        <div className="max-w-4xl mx-auto">
          {/* Back Button */}
          <button
            onClick={() => setSelectedPlan(null)}
            className={`flex items-center gap-2 mb-6 ${theme.colors.textSecondary} hover:${theme.colors.textPrimary} transition-colors group`}
          >
            <ArrowLeft className="w-5 h-5 group-hover:-translate-x-1 transition-transform" />
            <span className="font-medium">Back to Plans</span>
          </button>

          <div className="mb-8">
            <h1 className={`text-3xl font-bold ${theme.colors.textPrimary}`}>Complete Your Purchase</h1>
            <p className={`${theme.colors.textSecondary} mt-2`}>
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

  // Main Your Plan page
  return (
    <div className={`min-h-screen ${theme.colors.background} py-8 px-4`}>
      <div className="max-w-7xl mx-auto">
        {/* Back Button */}
        <button
          onClick={() => navigate(-1)}
          className={`flex items-center gap-2 mb-6 ${theme.colors.textSecondary} hover:${theme.colors.textPrimary} transition`}
        >
          <ArrowLeft size={20} />
          <span>Back</span>
        </button>

        {/* Header */}
        <div className="text-center mb-10">
          <div className="flex items-center justify-center gap-3 mb-3">
            <Crown className={`w-10 h-10 ${theme.colors.primaryText}`} />
            <h1 className={`text-4xl font-bold ${theme.colors.textPrimary}`}>
              Your Plan
            </h1>
          </div>
          <p className={`text-lg ${theme.colors.textSecondary}`}>
            Manage your subscription and unlock premium features
          </p>
        </div>

        {/* Current Plan Details Card - ENHANCED */}
        {user?.currentPlan && (
          <div className={`mb-8 ${theme.colors.surface} rounded-3xl ${theme.colors.shadow} overflow-hidden border-2 border-green-500/50 relative`}>
            {/* Decorative Background Gradient */}
            <div className="absolute inset-0 bg-gradient-to-br from-green-500/5 via-emerald-500/5 to-blue-500/5 pointer-events-none"></div>

            {/* Active Plan Header */}
            <div className="relative bg-gradient-to-r from-green-600 via-emerald-600 to-green-500 px-8 py-5">
              <div className="flex items-center justify-between flex-wrap gap-4">
                <div className="flex items-center gap-3">
                  <div className="p-2.5 bg-white/20 backdrop-blur-sm rounded-xl">
                    <CheckCircle className="h-6 w-6 text-white" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2 mb-0.5">
                      <span className="text-white/90 font-bold text-xs uppercase tracking-wider">Active Subscription</span>
                      <div className="h-2 w-2 rounded-full bg-white animate-pulse"></div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Star className="h-5 w-5 text-yellow-300 fill-yellow-300" />
                      <span className="text-white font-bold text-xl">
                        {user.currentPlan.displayName}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Billing Cycle Badge */}
                <div className="flex items-center gap-3">
                  <div className="bg-white/20 backdrop-blur-sm px-4 py-2 rounded-xl border border-white/30">
                    <div className="flex items-center gap-2">
                      <Clock className="h-4 w-4 text-white" />
                      <span className="text-white font-semibold text-sm">
                        {currentSubscription?.billing_cycle || currentSubscription?.billingCycle || 'Monthly'} Billing
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className={`p-8 ${theme.colors.surface} relative`}>
              {/* Top Stats - 4 Column Grid */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-5 mb-6">
                {/* Price */}
                <div className="relative overflow-hidden bg-gradient-to-br from-blue-600/20 via-blue-500/10 to-transparent rounded-2xl p-5 border border-blue-500/30 backdrop-blur-sm hover:scale-105 transition-transform duration-300">
                  <div className="absolute top-0 right-0 w-20 h-20 bg-blue-500/10 rounded-full blur-2xl"></div>
                  <div className="relative">
                    <p className={`${theme.colors.textSecondary} font-semibold text-xs mb-2 uppercase tracking-wide`}>Monthly Cost</p>
                    <p className="text-3xl font-extrabold bg-gradient-to-r from-blue-400 to-blue-600 bg-clip-text text-transparent">
                      {user.currentPlan.priceMonthly === 0
                        ? 'Free'
                        : user.currentPlan.isContactSales
                        ? 'Custom'
                        : `$${user.currentPlan.priceMonthly}`
                      }
                    </p>
                    {user.currentPlan.priceMonthly > 0 && !user.currentPlan.isContactSales && (
                      <p className={`${theme.colors.textTertiary} text-xs font-medium mt-1`}>per month</p>
                    )}
                  </div>
                </div>

                {/* Contract Usage */}
                <div className="relative overflow-hidden bg-gradient-to-br from-purple-600/20 via-purple-500/10 to-transparent rounded-2xl p-5 border border-purple-500/30 backdrop-blur-sm hover:scale-105 transition-transform duration-300">
                  <div className="absolute top-0 right-0 w-20 h-20 bg-purple-500/10 rounded-full blur-2xl"></div>
                  <div className="relative">
                    <p className={`${theme.colors.textSecondary} font-semibold text-xs mb-2 uppercase tracking-wide`}>Contracts Used</p>
                    <p className="text-3xl font-extrabold bg-gradient-to-r from-purple-400 to-purple-600 bg-clip-text text-transparent">
                      {contractsCount}
                      <span className={`text-lg ${theme.colors.textSecondary}`}>
                        {user.currentPlan.contractLimit === -1 ? ' / ∞' : ` / ${user.currentPlan.contractLimit}`}
                      </span>
                    </p>
                    {user.currentPlan.contractLimit !== -1 && (
                      <div className="mt-2.5 bg-gray-700/50 rounded-full h-2.5 overflow-hidden backdrop-blur-sm">
                        <div
                          className={`h-full transition-all duration-500 rounded-full ${
                            isLimitReached() ? 'bg-gradient-to-r from-red-500 to-red-600' : 'bg-gradient-to-r from-purple-500 to-purple-600'
                          }`}
                          style={{ width: `${Math.min(getUsagePercentage(), 100)}%` }}
                        ></div>
                      </div>
                    )}
                  </div>
                </div>

                {/* Renewal Date */}
                <div className="relative overflow-hidden bg-gradient-to-br from-orange-600/20 via-orange-500/10 to-transparent rounded-2xl p-5 border border-orange-500/30 backdrop-blur-sm hover:scale-105 transition-transform duration-300">
                  <div className="absolute top-0 right-0 w-20 h-20 bg-orange-500/10 rounded-full blur-2xl"></div>
                  <div className="relative">
                    <p className={`${theme.colors.textSecondary} font-semibold text-xs mb-2 uppercase tracking-wide flex items-center gap-1.5`}>
                      <Calendar className="w-3.5 h-3.5" />
                      {user.currentPlan.priceMonthly === 0 ? 'Plan Type' : 'Renews On'}
                    </p>
                    {user.currentPlan.priceMonthly === 0 ? (
                      <p className="text-2xl font-extrabold bg-gradient-to-r from-orange-400 to-orange-600 bg-clip-text text-transparent">
                        Forever
                      </p>
                    ) : currentSubscription?.end_date || currentSubscription?.endDate ? (
                      <>
                        <p className="text-2xl font-extrabold bg-gradient-to-r from-orange-400 to-orange-600 bg-clip-text text-transparent">
                          {new Date(currentSubscription.end_date || currentSubscription.endDate).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                        </p>
                        <p className={`${theme.colors.textTertiary} text-xs font-medium mt-1`}>
                          {new Date(currentSubscription.end_date || currentSubscription.endDate).getFullYear()}
                        </p>
                      </>
                    ) : (
                      <>
                        <p className="text-2xl font-extrabold bg-gradient-to-r from-orange-400 to-orange-600 bg-clip-text text-transparent">
                          {new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                        </p>
                        <p className={`${theme.colors.textTertiary} text-xs font-medium mt-1`}>
                          {new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).getFullYear()}
                        </p>
                      </>
                    )}
                  </div>
                </div>

                {/* Status */}
                <div className="relative overflow-hidden bg-gradient-to-br from-green-600/20 via-green-500/10 to-transparent rounded-2xl p-5 border border-green-500/30 backdrop-blur-sm hover:scale-105 transition-transform duration-300">
                  <div className="absolute top-0 right-0 w-20 h-20 bg-green-500/10 rounded-full blur-2xl"></div>
                  <div className="relative">
                    <p className={`${theme.colors.textSecondary} font-semibold text-xs mb-2 uppercase tracking-wide`}>Status</p>
                    <div className="flex items-center gap-2.5 mb-1">
                      <div className="h-3 w-3 rounded-full bg-green-500 animate-pulse shadow-lg shadow-green-500/50"></div>
                      <p className="text-2xl font-extrabold bg-gradient-to-r from-green-400 to-green-600 bg-clip-text text-transparent">
                        Active
                      </p>
                    </div>
                    <p className={`${theme.colors.textTertiary} text-xs font-medium`}>
                      {isLimitReached() ? '⚠️ Limit Reached' : '✓ All Systems Go'}
                    </p>
                  </div>
                </div>
              </div>

              {/* Limit Reached Warning */}
              {isLimitReached() && (
                <div className="bg-gradient-to-r from-red-900/30 to-red-800/20 border-2 border-red-500/50 rounded-2xl p-5 mb-6 backdrop-blur-sm">
                  <div className="flex items-start gap-3.5">
                    <div className="p-2 bg-red-500/20 rounded-xl">
                      <AlertCircle className="h-6 w-6 text-red-400" />
                    </div>
                    <div>
                      <p className="text-red-400 font-bold text-base mb-1">Contract Limit Reached!</p>
                      <p className="text-red-300/90 text-sm leading-relaxed">
                        You've reached your {user.currentPlan.contractLimit} contract limit. Upgrade to a higher plan to upload more contracts and unlock premium features.
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Features */}
              {user.currentPlan.features && user.currentPlan.features.length > 0 && (
                <div className="relative overflow-hidden bg-gradient-to-br from-indigo-600/10 via-blue-500/5 to-transparent rounded-2xl p-6 border border-indigo-500/20 backdrop-blur-sm">
                  <div className="absolute top-0 right-0 w-32 h-32 bg-indigo-500/5 rounded-full blur-3xl"></div>
                  <div className="relative">
                    <h3 className={`${theme.colors.textPrimary} font-bold text-base mb-4 flex items-center gap-2.5`}>
                      <div className="p-2 bg-indigo-500/20 rounded-lg">
                        <Sparkles className="h-5 w-5 text-indigo-400" />
                      </div>
                      <span>Included Features</span>
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {user.currentPlan.features.map((feature, index) => (
                        <div key={index} className="flex items-start gap-3 group">
                          <div className="mt-0.5 flex-shrink-0 w-6 h-6 rounded-lg bg-green-500/15 flex items-center justify-center group-hover:scale-110 transition-transform">
                            <Check className="h-4 w-4 text-green-400 font-bold" />
                          </div>
                          <span className={`${theme.colors.textPrimary} text-sm leading-relaxed`}>{feature}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Billing Cycle Toggle */}
        <div className="flex justify-center mb-12">
          <div className={`${theme.colors.surface} rounded-xl p-1.5 inline-flex ${theme.colors.shadow} border ${theme.colors.surfaceBorder}`}>
            <button
              onClick={() => setBillingCycle('MONTHLY')}
              className={`px-8 py-3 rounded-lg transition-all duration-300 font-semibold ${
                billingCycle === 'MONTHLY'
                  ? `${theme.colors.primarySolid} text-white shadow-lg scale-105`
                  : `${theme.colors.textSecondary} hover:${theme.colors.textPrimary}`
              }`}
            >
              Monthly
            </button>
            <button
              onClick={() => setBillingCycle('YEARLY')}
              className={`px-8 py-3 rounded-lg transition-all duration-300 relative font-semibold ${
                billingCycle === 'YEARLY'
                  ? `${theme.colors.primarySolid} text-white shadow-lg scale-105`
                  : `${theme.colors.textSecondary} hover:${theme.colors.textPrimary}`
              }`}
            >
              Yearly
              <span className="absolute -top-2 -right-2 bg-gradient-to-r from-green-500 to-emerald-500 text-white text-[10px] font-bold px-2 py-1 rounded-full shadow-lg">
                Save 20%
              </span>
            </button>
          </div>
        </div>

        {/* Upgrade Options Header */}
        <div className="text-center mb-10">
          <h2 className={`text-3xl font-bold ${theme.colors.textPrimary} mb-2`}>
            {user?.currentPlan ? 'Upgrade Options' : 'Choose Your Plan'}
          </h2>
          <p className={`text-base ${theme.colors.textSecondary}`}>
            {user?.currentPlan
              ? 'Unlock more features and increase your contract limits'
              : 'Select the perfect plan for your needs'}
          </p>
        </div>

        {/* Pricing Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {plans.map((plan) => {
            const priceMonthly = plan.priceMonthly || plan.price_monthly || 0;
            const price = billingCycle === 'YEARLY'
              ? priceMonthly * 12 * 0.8 // 20% discount for yearly
              : priceMonthly;

            // Check if this is the current plan AND billing cycle matches
            const currentSubBillingCycle = currentSubscription?.billing_cycle || currentSubscription?.billingCycle || 'MONTHLY';
            const isCurrentPlan = user?.currentPlan?.id === plan.id && currentSubBillingCycle === billingCycle;
            const planType = (plan.planType || plan.plan_type || '').toUpperCase();
            const isProfessional = planType === 'PROFESSIONAL';

            return (
              <div
                key={plan.id}
                className={`${theme.colors.surface} rounded-2xl overflow-hidden transform transition-all duration-500 hover:scale-105 ${theme.colors.shadow} flex flex-col ${
                  isProfessional ? `border-2 ${theme.colors.primaryBorder} relative ring-4 ring-blue-500/20` : `border ${theme.colors.surfaceBorder}`
                }`}
              >
                {/* Current Plan Badge */}
                {isCurrentPlan && (
                  <div className="absolute top-4 right-4 bg-gradient-to-r from-green-500 to-emerald-500 text-white px-4 py-2 text-xs font-bold uppercase tracking-wide rounded-full z-10 shadow-lg">
                    ✓ Active
                  </div>
                )}

                {/* Popular Badge */}
                {isProfessional && !isCurrentPlan && (
                  <div className="absolute top-4 right-4 bg-gradient-to-r from-blue-500 to-indigo-500 text-white px-4 py-2 text-xs font-bold uppercase tracking-wide rounded-full flex items-center gap-1.5 shadow-lg">
                    <Star className="w-3 h-3 fill-white" />
                    Most Popular
                  </div>
                )}

                {/* Plan Header */}
                <div className={`p-8 ${isProfessional ? 'bg-gradient-to-br from-blue-600 via-indigo-600 to-purple-600 text-white' : theme.colors.surfaceHover}`}>
                  <div className="flex items-center gap-3 mb-5">
                    <div className={`p-3 rounded-xl ${isProfessional ? 'bg-white/20 text-white' : `${theme.colors.primarySolid} text-white`}`}>
                      {getPlanIcon(planType)}
                    </div>
                    <h3 className={`text-2xl font-bold ${isProfessional ? 'text-white' : theme.colors.textPrimary}`}>
                      {plan.displayName || plan.display_name}
                    </h3>
                  </div>
                  <div className="mb-4">
                    {(plan.isContactSales || plan.is_contact_sales) ? (
                      <div className={`text-2xl font-semibold ${isProfessional ? 'text-white' : theme.colors.textPrimary}`}>
                        Talk to sales
                      </div>
                    ) : (
                      <div className="flex items-baseline gap-2">
                        <span className={`text-5xl font-extrabold ${isProfessional ? 'text-white' : theme.colors.textPrimary}`}>
                          ${price.toFixed(0)}
                        </span>
                        <span className={`text-lg ${isProfessional ? 'text-blue-100' : theme.colors.textSecondary}`}>
                          /{billingCycle === 'YEARLY' ? 'year' : 'month'}
                        </span>
                      </div>
                    )}
                  </div>
                  <p className={`text-sm ${isProfessional ? 'text-blue-100' : theme.colors.textSecondary}`}>
                    {plan.description || 'Perfect for your needs'}
                  </p>
                </div>

                {/* Features */}
                <div className={`p-8 ${theme.colors.surface} flex flex-col flex-grow`}>
                  <div className={`mb-6 p-4 rounded-xl ${theme.colors.surfaceHover} border ${theme.colors.surfaceBorder}`}>
                    <div className={`text-xs font-bold ${theme.colors.textSecondary} uppercase tracking-wider mb-2`}>Contract Limit</div>
                    <div className={`text-3xl font-extrabold ${theme.colors.primaryText}`}>
                      {(plan.contractLimit ?? plan.contract_limit) === -1 ? '∞' : (plan.contractLimit ?? plan.contract_limit)}
                      <span className={`text-lg font-normal ${theme.colors.textSecondary} ml-2`}>
                        {(plan.contractLimit ?? plan.contract_limit) === -1 ? 'Unlimited' : 'contracts'}
                      </span>
                    </div>
                  </div>

                  <ul className="space-y-3.5 mb-8 flex-grow">
                    {plan.features && plan.features.map((feature, idx) => (
                      <li key={idx} className="flex items-start gap-3">
                        <div className="mt-0.5 flex-shrink-0 w-5 h-5 rounded-full bg-green-500/10 flex items-center justify-center">
                          <Check className="w-3.5 h-3.5 text-green-500 font-bold" />
                        </div>
                        <span className={`text-sm ${theme.colors.textPrimary} leading-relaxed`}>{feature}</span>
                      </li>
                    ))}
                  </ul>

                  {/* CTA Button - FIXED LAYOUT */}
                  <button
                    onClick={() => handleSelectPlan(plan)}
                    disabled={isCurrentPlan}
                    className={`w-full py-4 px-6 rounded-xl font-bold text-base transition-all duration-300 flex items-center justify-center gap-2 ${
                      isCurrentPlan
                        ? `${theme.colors.surface} ${theme.colors.textTertiary} cursor-not-allowed border ${theme.colors.surfaceBorder}`
                        : isProfessional
                        ? 'bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 text-white hover:shadow-2xl hover:scale-105'
                        : `${theme.colors.primarySolid} text-white hover:shadow-xl hover:scale-105`
                    }`}
                  >
                    {isCurrentPlan ? (
                      <>
                        <CheckCircle className="w-5 h-5" />
                        Current Plan
                      </>
                    ) : planType === 'FREE' ? (
                      <>
                        Select Plan
                        <ArrowRight className="w-5 h-5" />
                      </>
                    ) : (plan.isContactSales || plan.is_contact_sales) ? (
                      <>
                        Contact
                        <ArrowRight className="w-5 h-5" />
                      </>
                    ) : (
                      <>
                        Upgrade Now
                        <ArrowRight className="w-5 h-5" />
                      </>
                    )}
                  </button>
                </div>
              </div>
            );
          })}
        </div>

        {/* FAQ or Additional Info */}
        <div className={`mt-16 ${theme.colors.surface} rounded-2xl ${theme.colors.shadow} p-8 border ${theme.colors.surfaceBorder}`}>
          <div className="flex items-center gap-3 mb-6">
            <Sparkles className={`w-6 h-6 ${theme.colors.primaryText}`} />
            <h2 className={`text-2xl font-bold ${theme.colors.textPrimary}`}>Frequently Asked Questions</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className={`p-6 rounded-xl ${theme.colors.surfaceHover} border ${theme.colors.surfaceBorder}`}>
              <h3 className={`font-bold ${theme.colors.textPrimary} text-base mb-2`}>Can I change my plan later?</h3>
              <p className={`${theme.colors.textSecondary} text-sm leading-relaxed`}>Yes, you can upgrade or downgrade your plan at any time from this page.</p>
            </div>
            <div className={`p-6 rounded-xl ${theme.colors.surfaceHover} border ${theme.colors.surfaceBorder}`}>
              <h3 className={`font-bold ${theme.colors.textPrimary} text-base mb-2`}>What payment methods do you accept?</h3>
              <p className={`${theme.colors.textSecondary} text-sm leading-relaxed`}>We accept all major credit cards (Visa, Mastercard, Amex) via Stripe and PayPal payments.</p>
            </div>
            <div className={`p-6 rounded-xl ${theme.colors.surfaceHover} border ${theme.colors.surfaceBorder}`}>
              <h3 className={`font-bold ${theme.colors.textPrimary} text-base mb-2`}>Is there a free trial?</h3>
              <p className={`${theme.colors.textSecondary} text-sm leading-relaxed`}>Yes! Our Free plan allows you to try ContractAI with up to 5 contracts at no cost.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
