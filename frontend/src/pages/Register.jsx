import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import useAuthStore from '../store/authStore';
import { Mail, Lock, User, AlertCircle, Eye, EyeOff, CheckCircle, TrendingUp, Users, Award, Sparkles, ArrowRight, CheckCircle2, Rocket } from 'lucide-react';
import PricingModal from '../components/PricingModal';

const Register = () => {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    firstName: '',
    lastName: '',
  });
  const [error, setError] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isVisible, setIsVisible] = useState(false);
  const [showPricingModal, setShowPricingModal] = useState(false);
  const [buttonState, setButtonState] = useState('idle'); // idle, loading, success
  const { register, isLoading, fetchCurrentUser } = useAuthStore();
  const navigate = useNavigate();

  useEffect(() => {
    setIsVisible(true);
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    if (formData.password.length < 6) {
      setError('Password must be at least 6 characters');
      return;
    }

    setButtonState('loading');

    try {
      const result = await register(
        formData.email,
        formData.password,
        formData.firstName,
        formData.lastName
      );

      setButtonState('success');

      // Wait for success animation before showing pricing or navigating
      setTimeout(() => {
        if (result.user.role === 'Admin') {
          navigate('/admin');
        } else {
          setShowPricingModal(true);
        }
      }, 1500);
    } catch (err) {
      setButtonState('idle');
      setError(err.message || 'Registration failed. Please try again.');
    }
  };

  const handlePlanSelected = async (plan) => {
    setShowPricingModal(false);

    try {
      await fetchCurrentUser();
    } catch (error) {
      console.error('Failed to fetch updated user data:', error);
    }

    navigate('/dashboard');
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const benefits = [
    { icon: CheckCircle, title: 'Free to Start', desc: 'No credit card required', color: 'emerald' },
    { icon: TrendingUp, title: 'Scale as You Grow', desc: 'Upgrade anytime', color: 'blue' },
    { icon: Users, title: 'Team Collaboration', desc: 'Work with your team', color: 'purple' }
  ];

  return (
    <div className="min-h-screen flex overflow-hidden bg-slate-950">
      {/* Animated Background Overlay for Success */}
      <div className={`fixed inset-0 z-50 pointer-events-none transition-opacity duration-500 ${buttonState === 'success' ? 'opacity-100' : 'opacity-0'}`}>
        <div className="absolute inset-0 bg-slate-950/80 backdrop-blur-sm"></div>
        <div className="absolute inset-0 flex items-center justify-center">
          <div className={`transform transition-all duration-700 ${buttonState === 'success' ? 'scale-100 opacity-100' : 'scale-50 opacity-0'}`}>
            {/* Success Ring Animation */}
            <div className="relative">
              <div className="absolute inset-0 rounded-full bg-purple-500/20 animate-ping"></div>
              <div className="absolute inset-0 rounded-full bg-purple-500/10 animate-pulse"></div>
              <div className="relative h-32 w-32 rounded-full bg-gradient-to-br from-purple-400 to-emerald-500 flex items-center justify-center shadow-2xl shadow-purple-500/50">
                <Rocket className="h-16 w-16 text-white animate-bounce" />
              </div>
            </div>
            <p className="text-white text-xl font-semibold mt-6 text-center animate-pulse">Account Created!</p>
            <p className="text-slate-400 text-sm mt-2 text-center">Let's choose your plan...</p>
          </div>
        </div>
        {/* Confetti Effects */}
        {buttonState === 'success' && (
          <>
            {[...Array(30)].map((_, i) => (
              <div
                key={i}
                className="absolute animate-confetti"
                style={{
                  left: `${Math.random() * 100}%`,
                  top: '-10px',
                  width: `${Math.random() * 10 + 5}px`,
                  height: `${Math.random() * 10 + 5}px`,
                  backgroundColor: ['#10b981', '#3b82f6', '#8b5cf6', '#f59e0b', '#ec4899'][i % 5],
                  borderRadius: Math.random() > 0.5 ? '50%' : '0',
                  animationDelay: `${i * 0.1}s`,
                  animationDuration: `${Math.random() * 2 + 2}s`,
                }}
              />
            ))}
          </>
        )}
      </div>

      {/* Left Side - Branding & Benefits */}
      <div className="hidden lg:flex lg:w-1/2 xl:w-3/5 relative overflow-hidden">
        {/* Animated background */}
        <div className="absolute inset-0">
          <div className="absolute -top-40 -left-40 w-80 h-80 bg-purple-500/20 rounded-full blur-3xl animate-pulse"></div>
          <div className="absolute top-1/2 -right-20 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }}></div>
          <div className="absolute -bottom-40 left-1/3 w-80 h-80 bg-blue-500/10 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '2s' }}></div>
          {/* Grid pattern */}
          <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:50px_50px]"></div>
        </div>

        {/* Content */}
        <div className={`relative z-10 flex flex-col justify-center px-10 xl:px-16 py-6 transition-all duration-1000 ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`}>
          {/* Logo */}
          <div className="mb-5">
            <Link to="/" className="inline-flex items-center gap-3 px-4 py-2.5 bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700/50 hover:border-emerald-500/50 transition-colors">
              <div className="h-9 w-9 rounded-lg bg-gradient-to-br from-emerald-400 to-emerald-600 flex items-center justify-center shadow-lg shadow-emerald-500/25">
                <span className="text-white font-bold">CA</span>
              </div>
              <span className="text-xl font-bold text-white">ContractAI</span>
            </Link>
          </div>

          {/* Main Heading */}
          <h1 className="text-4xl xl:text-5xl font-bold mb-3 leading-tight text-white">
            Start your journey to<br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-emerald-400">smarter contracts</span>
          </h1>
          <p className="text-lg text-slate-400 mb-6 max-w-lg">
            Join thousands using AI to transform contract management
          </p>

          {/* Benefits */}
          <div className="space-y-2">
            {benefits.map((benefit, index) => (
              <div
                key={index}
                className={`group flex items-center gap-3 p-3 rounded-xl bg-slate-800/30 border border-slate-700/50 hover:border-emerald-500/50 transition-all duration-500 ${isVisible ? 'opacity-100 translate-x-0' : 'opacity-0 -translate-x-8'}`}
                style={{ transitionDelay: `${(index + 1) * 150}ms` }}
              >
                <div className="flex-shrink-0 h-9 w-9 rounded-lg bg-emerald-500/10 flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                  <benefit.icon className="h-4 w-4 text-emerald-400" />
                </div>
                <div>
                  <h3 className="font-semibold text-sm text-white">{benefit.title}</h3>
                  <p className="text-slate-400 text-xs">{benefit.desc}</p>
                </div>
              </div>
            ))}
          </div>

          {/* Stats */}
          <div className={`mt-6 flex gap-6 transition-all duration-1000 ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`} style={{ transitionDelay: '700ms' }}>
            <div className="text-center">
              <div className="text-2xl font-bold text-white">500+</div>
              <div className="text-slate-500 text-xs">Companies</div>
            </div>
            <div className="w-px bg-slate-800"></div>
            <div className="text-center">
              <div className="text-2xl font-bold text-white">50K+</div>
              <div className="text-slate-500 text-xs">Contracts</div>
            </div>
            <div className="w-px bg-slate-800"></div>
            <div className="text-center">
              <div className="text-2xl font-bold text-white">99.9%</div>
              <div className="text-slate-500 text-xs">Accuracy</div>
            </div>
          </div>
        </div>
      </div>

      {/* Right Side - Registration Form */}
      <div className="flex-1 flex items-center justify-center p-4 lg:p-6 overflow-y-auto">
        <div className={`w-full max-w-md transition-all duration-1000 ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`}>
          {/* Mobile Logo */}
          <div className="lg:hidden mb-4 text-center">
            <Link to="/" className="inline-flex items-center gap-3 mb-4">
              <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-emerald-400 to-emerald-600 flex items-center justify-center shadow-lg shadow-emerald-500/25">
                <span className="text-white font-bold text-lg">CA</span>
              </div>
              <span className="text-xl font-bold text-white">ContractAI</span>
            </Link>
          </div>

          {/* Form Card */}
          <div className="bg-slate-900/50 backdrop-blur-sm rounded-2xl border border-slate-800 p-5 lg:p-6 shadow-2xl">
            {/* Badge */}
            <div className="flex justify-center mb-3">
              <div className="inline-flex items-center gap-2 px-3 py-1 bg-purple-500/10 border border-purple-500/20 rounded-full">
                <Sparkles className="w-3 h-3 text-purple-400" />
                <span className="text-purple-400 text-xs font-medium">Free to Start</span>
              </div>
            </div>

            {/* Header */}
            <div className="mb-4 text-center">
              <h2 className="text-2xl font-bold text-white mb-1">Create Account</h2>
              <p className="text-slate-400 text-sm">Get started with your free account</p>
            </div>

            {/* Error Message */}
            {error && (
              <div className="mb-3 p-2.5 bg-red-500/10 border border-red-500/20 rounded-xl flex items-start gap-2 animate-shake">
                <AlertCircle className="h-4 w-4 text-red-400 flex-shrink-0 mt-0.5" />
                <p className="text-red-400 text-xs">{error}</p>
              </div>
            )}

            {/* Form */}
            <form onSubmit={handleSubmit} className="space-y-3">
              {/* Name Fields */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1.5">First Name</label>
                  <div className="relative group">
                    <User className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500 transition-colors group-focus-within:text-emerald-400" />
                    <input
                      type="text"
                      name="firstName"
                      value={formData.firstName}
                      onChange={handleChange}
                      placeholder="John"
                      autoComplete="given-name"
                      className="w-full pl-10 pr-3 py-2.5 bg-slate-800/50 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-all duration-200 text-sm"
                      disabled={buttonState !== 'idle'}
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1.5">Last Name</label>
                  <div className="relative group">
                    <User className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500 transition-colors group-focus-within:text-emerald-400" />
                    <input
                      type="text"
                      name="lastName"
                      value={formData.lastName}
                      onChange={handleChange}
                      placeholder="Doe"
                      autoComplete="family-name"
                      className="w-full pl-10 pr-3 py-2.5 bg-slate-800/50 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-all duration-200 text-sm"
                      disabled={buttonState !== 'idle'}
                    />
                  </div>
                </div>
              </div>

              {/* Email Field */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1.5">Email Address</label>
                <div className="relative group">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500 transition-colors group-focus-within:text-emerald-400" />
                  <input
                    type="email"
                    name="email"
                    value={formData.email}
                    onChange={handleChange}
                    placeholder="you@example.com"
                    autoComplete="email"
                    className="w-full pl-10 pr-3 py-2.5 bg-slate-800/50 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-all duration-200 text-sm"
                    required
                    disabled={buttonState !== 'idle'}
                  />
                </div>
              </div>

              {/* Password Field */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1.5">Password</label>
                <div className="relative group">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500 transition-colors group-focus-within:text-emerald-400" />
                  <input
                    type={showPassword ? 'text' : 'password'}
                    name="password"
                    value={formData.password}
                    onChange={handleChange}
                    placeholder="••••••••"
                    autoComplete="new-password"
                    className="w-full pl-10 pr-10 py-2.5 bg-slate-800/50 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-all duration-200 text-sm"
                    required
                    disabled={buttonState !== 'idle'}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300 transition-colors"
                    tabIndex={-1}
                  >
                    {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
                <p className="mt-1 text-xs text-slate-500">At least 6 characters</p>
              </div>

              {/* Confirm Password Field */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1.5">Confirm Password</label>
                <div className="relative group">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500 transition-colors group-focus-within:text-emerald-400" />
                  <input
                    type={showConfirmPassword ? 'text' : 'password'}
                    name="confirmPassword"
                    value={formData.confirmPassword}
                    onChange={handleChange}
                    placeholder="••••••••"
                    autoComplete="new-password"
                    className="w-full pl-10 pr-10 py-2.5 bg-slate-800/50 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-all duration-200 text-sm"
                    required
                    disabled={buttonState !== 'idle'}
                  />
                  <button
                    type="button"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300 transition-colors"
                    tabIndex={-1}
                  >
                    {showConfirmPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>

              {/* Terms and Conditions */}
              <div className="pt-1">
                <p className="text-xs text-slate-500 leading-relaxed">
                  By creating an account, you agree to our{' '}
                  <Link to="/terms" className="text-emerald-400 hover:text-emerald-300 font-medium">
                    Terms of Service
                  </Link>{' '}
                  and{' '}
                  <Link to="/privacy" className="text-emerald-400 hover:text-emerald-300 font-medium">
                    Privacy Policy
                  </Link>
                </p>
              </div>

              {/* Submit Button */}
              <button
                type="submit"
                disabled={buttonState !== 'idle'}
                className={`group relative w-full mt-3 py-3 px-4 font-semibold rounded-xl transition-all duration-500 overflow-hidden
                  ${buttonState === 'idle'
                    ? 'bg-gradient-to-r from-purple-500 to-emerald-500 hover:from-purple-600 hover:to-emerald-600 text-white shadow-lg shadow-purple-500/25 hover:shadow-purple-500/40'
                    : buttonState === 'loading'
                    ? 'bg-gradient-to-r from-purple-500 to-emerald-500 text-white'
                    : 'bg-gradient-to-r from-emerald-400 to-emerald-500 text-white'}
                  disabled:cursor-not-allowed`}
              >
                {/* Shimmer Effect */}
                <span className="absolute inset-0 overflow-hidden rounded-xl">
                  <span className={`absolute inset-0 -translate-x-full ${buttonState === 'loading' ? 'animate-shimmer bg-gradient-to-r from-transparent via-white/20 to-transparent' : ''}`}></span>
                </span>

                {/* Button Content */}
                <span className="relative flex items-center justify-center gap-2">
                  {buttonState === 'idle' && (
                    <>
                      Create Account
                      <ArrowRight className="h-5 w-5 group-hover:translate-x-1 transition-transform" />
                    </>
                  )}
                  {buttonState === 'loading' && (
                    <span className="flex items-center gap-3">
                      {/* Spinning Ring */}
                      <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                      </svg>
                      <span>Creating your account</span>
                      {/* Animated Dots */}
                      <span className="flex gap-0.5">
                        <span className="w-1 h-1 bg-white rounded-full animate-pulse" style={{ animationDelay: '0ms' }}></span>
                        <span className="w-1 h-1 bg-white rounded-full animate-pulse" style={{ animationDelay: '200ms' }}></span>
                        <span className="w-1 h-1 bg-white rounded-full animate-pulse" style={{ animationDelay: '400ms' }}></span>
                      </span>
                    </span>
                  )}
                  {buttonState === 'success' && (
                    <span className="flex items-center gap-2">
                      <CheckCircle2 className="h-5 w-5 animate-bounce" />
                      Account Created!
                    </span>
                  )}
                </span>

                {/* Progress Bar */}
                {buttonState === 'loading' && (
                  <span className="absolute bottom-0 left-0 h-1 bg-white/30 animate-progress"></span>
                )}
              </button>
            </form>

            {/* Divider */}
            <div className="my-4 flex items-center">
              <div className="flex-grow border-t border-slate-800"></div>
              <span className="px-3 text-xs text-slate-500">Already have an account?</span>
              <div className="flex-grow border-t border-slate-800"></div>
            </div>

            {/* Login Link */}
            <p className="text-center">
              <Link
                to="/login"
                className="text-emerald-400 hover:text-emerald-300 font-semibold transition-colors inline-flex items-center gap-1 hover:gap-2 duration-200 text-sm"
              >
                Sign in instead
                <ArrowRight className="h-4 w-4" />
              </Link>
            </p>
          </div>

          {/* Footer */}
          <p className="text-center text-slate-600 text-xs mt-3">
            © 2025 ContractAI. All rights reserved.
          </p>
        </div>
      </div>

      {/* Custom Animations */}
      <style>{`
        @keyframes shimmer {
          100% { transform: translateX(100%); }
        }
        .animate-shimmer {
          animation: shimmer 1.5s ease-in-out infinite;
        }

        @keyframes progress {
          0% { width: 0%; }
          100% { width: 100%; }
        }
        .animate-progress {
          animation: progress 2s ease-in-out infinite;
        }

        @keyframes confetti {
          0% { transform: translateY(0) rotate(0deg); opacity: 1; }
          100% { transform: translateY(100vh) rotate(720deg); opacity: 0; }
        }
        .animate-confetti {
          animation: confetti 3s ease-out forwards;
        }

        @keyframes shake {
          0%, 100% { transform: translateX(0); }
          25% { transform: translateX(-10px); }
          75% { transform: translateX(10px); }
        }
        .animate-shake {
          animation: shake 0.5s ease-in-out;
        }
      `}</style>

      {/* Pricing Modal */}
      <PricingModal
        show={showPricingModal}
        onPlanSelected={handlePlanSelected}
      />
    </div>
  );
};

export default Register;
