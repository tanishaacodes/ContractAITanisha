import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import useAuthStore from '../store/authStore';
import { Mail, Lock, AlertCircle, Eye, EyeOff, FileText, Shield, Zap, Sparkles, ArrowRight, CheckCircle2 } from 'lucide-react';

const Login = () => {
  const [formData, setFormData] = useState({ email: '', password: '' });
  const [error, setError] = useState('');
  const [rememberMe, setRememberMe] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [isVisible, setIsVisible] = useState(false);
  const [buttonState, setButtonState] = useState('idle'); // idle, loading, success
  const { login, isLoading } = useAuthStore();
  const navigate = useNavigate();

  useEffect(() => {
    setIsVisible(true);
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setButtonState('loading');

    try {
      const result = await login(formData.email, formData.password);
      setButtonState('success');

      // Wait for success animation before navigating
      setTimeout(() => {
        if (result.user.role === 'Admin') {
          navigate('/admin');
        } else {
          navigate('/dashboard');
        }
      }, 1500);
    } catch (err) {
      setButtonState('idle');
      setError(err.message || 'Login failed. Please try again.');
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const features = [
    { icon: FileText, title: 'Smart Extraction', desc: 'Extract key clauses & metadata automatically', color: 'emerald' },
    { icon: Shield, title: 'Risk Analysis', desc: 'AI-driven risk scoring and deviation detection', color: 'blue' },
    { icon: Zap, title: 'Fast Processing', desc: 'Process contracts in seconds, not hours', color: 'purple' }
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
              <div className="absolute inset-0 rounded-full bg-emerald-500/20 animate-ping"></div>
              <div className="absolute inset-0 rounded-full bg-emerald-500/10 animate-pulse"></div>
              <div className="relative h-32 w-32 rounded-full bg-gradient-to-br from-emerald-400 to-emerald-600 flex items-center justify-center shadow-2xl shadow-emerald-500/50">
                <CheckCircle2 className="h-16 w-16 text-white animate-bounce" />
              </div>
            </div>
            <p className="text-white text-xl font-semibold mt-6 text-center animate-pulse">Welcome back!</p>
          </div>
        </div>
        {/* Particle Effects */}
        {buttonState === 'success' && (
          <>
            {[...Array(20)].map((_, i) => (
              <div
                key={i}
                className="absolute w-2 h-2 rounded-full animate-particle"
                style={{
                  left: '50%',
                  top: '50%',
                  backgroundColor: ['#10b981', '#3b82f6', '#8b5cf6', '#f59e0b'][i % 4],
                  animationDelay: `${i * 0.05}s`,
                  '--tx': `${(Math.random() - 0.5) * 400}px`,
                  '--ty': `${(Math.random() - 0.5) * 400}px`,
                }}
              />
            ))}
          </>
        )}
      </div>

      {/* Left Side - Branding & Features */}
      <div className="hidden lg:flex lg:w-1/2 xl:w-3/5 relative overflow-hidden">
        {/* Animated background */}
        <div className="absolute inset-0">
          <div className="absolute -top-40 -left-40 w-80 h-80 bg-emerald-500/20 rounded-full blur-3xl animate-pulse"></div>
          <div className="absolute top-1/2 -right-20 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }}></div>
          <div className="absolute -bottom-40 left-1/3 w-80 h-80 bg-purple-500/10 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '2s' }}></div>
          {/* Grid pattern */}
          <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:50px_50px]"></div>
        </div>

        {/* Content */}
        <div className={`relative z-10 flex flex-col justify-center px-10 xl:px-16 py-8 transition-all duration-1000 ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`}>
          {/* Logo */}
          <div className="mb-6">
            <Link to="/" className="inline-flex items-center gap-3 px-4 py-2.5 bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700/50 hover:border-emerald-500/50 transition-colors">
              <div className="h-9 w-9 rounded-lg bg-gradient-to-br from-emerald-400 to-emerald-600 flex items-center justify-center shadow-lg shadow-emerald-500/25">
                <span className="text-white font-bold">CA</span>
              </div>
              <span className="text-xl font-bold text-white">ContractAI</span>
            </Link>
          </div>

          {/* Main Heading */}
          <h1 className="text-4xl xl:text-5xl font-bold mb-4 leading-tight text-white">
            Welcome back to<br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-cyan-400">your command center</span>
          </h1>
          <p className="text-lg text-slate-400 mb-8 max-w-lg">
            Intelligent Contract Intelligence Platform for modern enterprises
          </p>

          {/* Features */}
          <div className="space-y-3">
            {features.map((feature, index) => (
              <div
                key={index}
                className={`group flex items-center gap-3 p-3 rounded-xl bg-slate-800/30 border border-slate-700/50 hover:border-emerald-500/50 transition-all duration-500 ${isVisible ? 'opacity-100 translate-x-0' : 'opacity-0 -translate-x-8'}`}
                style={{ transitionDelay: `${(index + 1) * 150}ms` }}
              >
                <div className="flex-shrink-0 h-10 w-10 rounded-lg bg-emerald-500/10 flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                  <feature.icon className="h-5 w-5 text-emerald-400" />
                </div>
                <div>
                  <h3 className="font-semibold text-base text-white">{feature.title}</h3>
                  <p className="text-slate-400 text-xs">{feature.desc}</p>
                </div>
              </div>
            ))}
          </div>

          {/* Stats */}
          <div className={`mt-8 flex gap-6 transition-all duration-1000 ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`} style={{ transitionDelay: '600ms' }}>
            <div className="text-center">
              <div className="text-2xl font-bold text-white">500+</div>
              <div className="text-slate-500 text-xs">Enterprises</div>
            </div>
            <div className="w-px bg-slate-800"></div>
            <div className="text-center">
              <div className="text-2xl font-bold text-white">99.9%</div>
              <div className="text-slate-500 text-xs">Accuracy</div>
            </div>
            <div className="w-px bg-slate-800"></div>
            <div className="text-center">
              <div className="text-2xl font-bold text-white">24/7</div>
              <div className="text-slate-500 text-xs">Available</div>
            </div>
          </div>
        </div>
      </div>

      {/* Right Side - Login Form */}
      <div className="flex-1 flex items-center justify-center p-4 lg:p-8">
        <div className={`w-full max-w-md transition-all duration-1000 ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`}>
          {/* Mobile Logo */}
          <div className="lg:hidden mb-6 text-center">
            <Link to="/" className="inline-flex items-center gap-3 mb-4">
              <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-emerald-400 to-emerald-600 flex items-center justify-center shadow-lg shadow-emerald-500/25">
                <span className="text-white font-bold text-lg">CA</span>
              </div>
              <span className="text-xl font-bold text-white">ContractAI</span>
            </Link>
          </div>

          {/* Form Card */}
          <div className="bg-slate-900/50 backdrop-blur-sm rounded-2xl border border-slate-800 p-6 lg:p-8 shadow-2xl">
            {/* Badge */}
            <div className="flex justify-center mb-4">
              <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-emerald-500/10 border border-emerald-500/20 rounded-full">
                <Sparkles className="w-3.5 h-3.5 text-emerald-400" />
                <span className="text-emerald-400 text-xs font-medium">Secure Login</span>
              </div>
            </div>

            {/* Header */}
            <div className="mb-6 text-center">
              <h2 className="text-2xl font-bold text-white mb-1">Sign in</h2>
              <p className="text-slate-400 text-sm">Access your contract intelligence dashboard</p>
            </div>

            {/* Error Message */}
            {error && (
              <div className="mb-4 p-3 bg-red-500/10 border border-red-500/20 rounded-xl flex items-start gap-2 animate-shake">
                <AlertCircle className="h-4 w-4 text-red-400 flex-shrink-0 mt-0.5" />
                <p className="text-red-400 text-xs">{error}</p>
              </div>
            )}

            {/* Form */}
            <form onSubmit={handleSubmit} className="space-y-4">
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
                    className="w-full pl-10 pr-4 py-3 bg-slate-800/50 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-all duration-200 text-sm"
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
                    autoComplete="current-password"
                    className="w-full pl-10 pr-10 py-3 bg-slate-800/50 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-all duration-200 text-sm"
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
              </div>

              {/* Remember Me & Forgot Password */}
              <div className="flex items-center justify-between">
                <label className="flex items-center gap-2 cursor-pointer group">
                  <input
                    type="checkbox"
                    checked={rememberMe}
                    onChange={(e) => setRememberMe(e.target.checked)}
                    className="w-4 h-4 rounded border-slate-600 bg-slate-800 text-emerald-500 focus:ring-emerald-500 focus:ring-offset-0 focus:ring-offset-slate-900 cursor-pointer"
                  />
                  <span className="text-sm text-slate-400 group-hover:text-slate-300 transition-colors">Remember me</span>
                </label>
                <Link
                  to="/forgot-password"
                  className="text-sm text-emerald-400 hover:text-emerald-300 font-medium transition-colors"
                >
                  Forgot password?
                </Link>
              </div>

              {/* Submit Button */}
              <button
                type="submit"
                disabled={buttonState !== 'idle'}
                className={`group relative w-full mt-4 py-3.5 px-4 font-semibold rounded-xl transition-all duration-500 overflow-hidden
                  ${buttonState === 'idle'
                    ? 'bg-gradient-to-r from-emerald-500 to-emerald-600 hover:from-emerald-600 hover:to-emerald-700 text-white shadow-lg shadow-emerald-500/25 hover:shadow-emerald-500/40'
                    : buttonState === 'loading'
                    ? 'bg-gradient-to-r from-emerald-500 to-emerald-600 text-white'
                    : 'bg-gradient-to-r from-emerald-400 to-emerald-500 text-white'}
                  disabled:cursor-not-allowed`}
              >
                {/* Ripple Effect */}
                <span className="absolute inset-0 overflow-hidden rounded-xl">
                  <span className={`absolute inset-0 rounded-xl ${buttonState === 'loading' ? 'animate-ripple bg-white/20' : ''}`}></span>
                </span>

                {/* Button Content */}
                <span className="relative flex items-center justify-center gap-2">
                  {buttonState === 'idle' && (
                    <>
                      Sign In
                      <ArrowRight className="h-5 w-5 group-hover:translate-x-1 transition-transform" />
                    </>
                  )}
                  {buttonState === 'loading' && (
                    <span className="flex items-center gap-3">
                      {/* Animated Dots */}
                      <span className="flex gap-1">
                        <span className="w-2 h-2 bg-white rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
                        <span className="w-2 h-2 bg-white rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
                        <span className="w-2 h-2 bg-white rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
                      </span>
                      <span className="animate-pulse">Signing in</span>
                    </span>
                  )}
                  {buttonState === 'success' && (
                    <span className="flex items-center gap-2 animate-bounce">
                      <CheckCircle2 className="h-5 w-5" />
                      Success!
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
            <div className="my-5 flex items-center">
              <div className="flex-grow border-t border-slate-800"></div>
              <span className="px-3 text-xs text-slate-500">New to ContractAI?</span>
              <div className="flex-grow border-t border-slate-800"></div>
            </div>

            {/* Sign Up Link */}
            <p className="text-center">
              <Link
                to="/register"
                className="text-emerald-400 hover:text-emerald-300 font-semibold transition-colors inline-flex items-center gap-1 hover:gap-2 duration-200 text-sm"
              >
                Create an account
                <ArrowRight className="h-4 w-4" />
              </Link>
            </p>
          </div>

          {/* Footer */}
          <p className="text-center text-slate-600 text-xs mt-4">
            © 2025 ContractAI. All rights reserved.
          </p>
        </div>
      </div>

      {/* Custom Animations */}
      <style>{`
        @keyframes ripple {
          0% { transform: scale(0); opacity: 0.5; }
          100% { transform: scale(4); opacity: 0; }
        }
        .animate-ripple {
          animation: ripple 1.5s ease-out infinite;
        }

        @keyframes progress {
          0% { width: 0%; }
          100% { width: 100%; }
        }
        .animate-progress {
          animation: progress 2s ease-in-out infinite;
        }

        @keyframes particle {
          0% { transform: translate(-50%, -50%) scale(1); opacity: 1; }
          100% { transform: translate(calc(-50% + var(--tx)), calc(-50% + var(--ty))) scale(0); opacity: 0; }
        }
        .animate-particle {
          animation: particle 1s ease-out forwards;
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
    </div>
  );
};

export default Login;
