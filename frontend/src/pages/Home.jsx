import { Link } from 'react-router-dom';
import { ArrowRight, LogOut, FileText, Shield, Zap, CheckCircle, Sparkles, BarChart3, Lock, ChevronDown, ChevronLeft, ChevronRight, Phone } from 'lucide-react';
import useAuthStore from '../store/authStore';
import { useState, useEffect, useRef } from 'react';

const Home = () => {
  const { isAuthenticated, logout } = useAuthStore();
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });
  const [cursorVariant, setCursorVariant] = useState('default');
  const [scrollY, setScrollY] = useState(0);
  const [isVisible, setIsVisible] = useState({});
  const [pricingIndex, setPricingIndex] = useState(0);
  const heroRef = useRef(null);
  const featuresRef = useRef(null);

  // Actual pricing plans
  const pricingPlans = [
    {
      name: 'Free',
      price: 'Free',
      period: '',
      description: 'Perfect for trying out Contract AI',
      features: ['Analyse Risks', 'Clauses Library', '5 Contracts'],
      cta: 'Get Started',
      popular: false,
      isContactSales: false,
    },
    {
      name: 'Standard',
      price: '$10',
      period: '/month',
      description: 'Great for small teams and growing businesses',
      features: ['Everything in Free', 'Analyse Risks', 'Clauses Library', '30 Contracts'],
      cta: 'Get Started',
      popular: false,
      isContactSales: false,
    },
    {
      name: 'Professional',
      price: '$30',
      period: '/month',
      description: 'Advanced features for legal teams',
      features: ['Everything in Standard', 'Analyse Intents', 'Contract Clustering', 'Comprehensive Risk Management', '120 Contracts'],
      cta: 'Start Free Trial',
      popular: true,
      isContactSales: false,
    },
    {
      name: 'Enterprise',
      price: 'Custom',
      period: '',
      description: 'Unlimited contracts with dedicated support',
      features: ['Everything in Professional', 'Unlimited Contracts', 'Dedicated Account Manager', 'Priority Support', 'Custom Integrations'],
      cta: 'Contact Sales',
      popular: false,
      isContactSales: true,
    },
    {
      name: 'On-Premise',
      price: 'Custom',
      period: '',
      description: 'Full deployment with DMS and SAP integration',
      features: ['Everything in Enterprise', 'DMS Integration', 'SAP Integration', 'On-Premise Deployment', 'Full Data Control'],
      cta: 'Contact Sales',
      popular: false,
      isContactSales: true,
    },
  ];

  const canScrollLeft = pricingIndex > 0;
  const canScrollRight = pricingIndex < pricingPlans.length - 3;

  const handleLogout = () => {
    logout();
    window.location.reload();
  };

  // Mouse tracking for custom cursor
  useEffect(() => {
    const handleMouseMove = (e) => {
      setMousePosition({ x: e.clientX, y: e.clientY });
    };

    const handleScroll = () => {
      setScrollY(window.scrollY);
    };

    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('scroll', handleScroll);

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('scroll', handleScroll);
    };
  }, []);

  // Intersection Observer for scroll animations
  useEffect(() => {
    const observerOptions = {
      threshold: 0.1,
      rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          setIsVisible((prev) => ({ ...prev, [entry.target.id]: true }));
        }
      });
    }, observerOptions);

    const elements = document.querySelectorAll('[data-animate]');
    elements.forEach((el) => observer.observe(el));

    return () => observer.disconnect();
  }, []);

  // Text animation for hero
  const heroText = "ContractAI";
  const [displayedText, setDisplayedText] = useState('');

  useEffect(() => {
    let index = 0;
    const timer = setInterval(() => {
      if (index <= heroText.length) {
        setDisplayedText(heroText.slice(0, index));
        index++;
      } else {
        clearInterval(timer);
      }
    }, 100);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 overflow-x-hidden">
      {/* Custom Cursor */}
      <div
        className={`fixed w-4 h-4 rounded-full pointer-events-none z-[9999] mix-blend-difference transition-transform duration-150 ease-out ${
          cursorVariant === 'hover' ? 'scale-[2.5] bg-white' : 'bg-emerald-400'
        }`}
        style={{
          left: mousePosition.x - 8,
          top: mousePosition.y - 8,
        }}
      />
      <div
        className="fixed w-1 h-1 rounded-full bg-white pointer-events-none z-[9999]"
        style={{
          left: mousePosition.x - 2,
          top: mousePosition.y - 2,
        }}
      />

      {/* Animated Background Mesh */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        {/* Gradient Orbs with Parallax */}
        <div
          className="absolute w-[800px] h-[800px] rounded-full opacity-30 blur-[120px]"
          style={{
            background: 'radial-gradient(circle, rgba(16, 185, 129, 0.4) 0%, transparent 70%)',
            top: -200 + scrollY * 0.1,
            right: -200,
            transform: `translate(${mousePosition.x * 0.02}px, ${mousePosition.y * 0.02}px)`,
          }}
        />
        <div
          className="absolute w-[600px] h-[600px] rounded-full opacity-20 blur-[100px]"
          style={{
            background: 'radial-gradient(circle, rgba(59, 130, 246, 0.4) 0%, transparent 70%)',
            bottom: -100 + scrollY * 0.05,
            left: -150,
            transform: `translate(${mousePosition.x * -0.015}px, ${mousePosition.y * -0.015}px)`,
          }}
        />
        <div
          className="absolute w-[500px] h-[500px] rounded-full opacity-20 blur-[80px]"
          style={{
            background: 'radial-gradient(circle, rgba(139, 92, 246, 0.3) 0%, transparent 70%)',
            top: '50%',
            left: '50%',
            transform: `translate(-50%, -50%) translate(${mousePosition.x * 0.01}px, ${mousePosition.y * 0.01}px)`,
          }}
        />

        {/* Animated Grid */}
        <div
          className="absolute inset-0 opacity-[0.03]"
          style={{
            backgroundImage: `
              linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px),
              linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)
            `,
            backgroundSize: '100px 100px',
            transform: `translateY(${scrollY * 0.1}px)`,
          }}
        />

        {/* Floating Particles */}
        {[...Array(20)].map((_, i) => (
          <div
            key={i}
            className="absolute w-1 h-1 bg-emerald-400/30 rounded-full animate-float"
            style={{
              left: `${Math.random() * 100}%`,
              top: `${Math.random() * 100}%`,
              animationDelay: `${Math.random() * 5}s`,
              animationDuration: `${Math.random() * 10 + 10}s`,
            }}
          />
        ))}
      </div>

      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div
            className="flex items-center gap-3 group cursor-pointer"
            onMouseEnter={() => setCursorVariant('hover')}
            onMouseLeave={() => setCursorVariant('default')}
          >
            <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-emerald-400 to-emerald-600 flex items-center justify-center shadow-lg shadow-emerald-500/25 group-hover:scale-110 transition-transform duration-300">
              <span className="text-white font-bold text-lg">CA</span>
            </div>
            <span className="text-xl font-bold text-white">ContractAI</span>
          </div>

          <div className="hidden md:flex items-center gap-8">
            {['Features', 'Pricing', 'About'].map((item) => (
              <a
                key={item}
                href={`#${item.toLowerCase()}`}
                className="text-slate-400 hover:text-white transition-colors duration-300 text-sm font-medium relative group"
                onMouseEnter={() => setCursorVariant('hover')}
                onMouseLeave={() => setCursorVariant('default')}
              >
                {item}
                <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-emerald-400 group-hover:w-full transition-all duration-300" />
              </a>
            ))}
          </div>

          <div className="flex items-center gap-4">
            {isAuthenticated ? (
              <>
                <Link
                  to="/dashboard"
                  className="px-4 py-2 text-sm font-medium text-white hover:text-emerald-400 transition-colors"
                  onMouseEnter={() => setCursorVariant('hover')}
                  onMouseLeave={() => setCursorVariant('default')}
                >
                  Dashboard
                </Link>
                <button
                  onClick={handleLogout}
                  className="px-4 py-2 text-sm font-medium text-slate-400 hover:text-white transition-colors"
                >
                  <LogOut className="h-4 w-4" />
                </button>
              </>
            ) : (
              <>
                <Link
                  to="/login"
                  className="px-4 py-2 text-sm font-medium text-slate-300 hover:text-white transition-colors"
                  onMouseEnter={() => setCursorVariant('hover')}
                  onMouseLeave={() => setCursorVariant('default')}
                >
                  Sign In
                </Link>
                <Link
                  to="/register"
                  className="magnetic-btn px-5 py-2.5 text-sm font-medium text-white bg-gradient-to-r from-emerald-500 to-emerald-600 rounded-lg hover:shadow-lg hover:shadow-emerald-500/25 transition-all duration-300"
                  onMouseEnter={() => setCursorVariant('hover')}
                  onMouseLeave={() => setCursorVariant('default')}
                >
                  Get Started
                </Link>
              </>
            )}
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section ref={heroRef} className="relative min-h-[85vh] flex flex-col items-center justify-center px-6 pt-20">
        {/* Badge */}
        <div
          className="animate-fade-in-up mb-8"
          style={{ animationDelay: '0.2s' }}
        >
          <div
            className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-500/10 border border-emerald-500/20 rounded-full hover:bg-emerald-500/20 transition-colors cursor-pointer"
            onMouseEnter={() => setCursorVariant('hover')}
            onMouseLeave={() => setCursorVariant('default')}
          >
            <Sparkles className="w-4 h-4 text-emerald-400 animate-pulse" />
            <span className="text-emerald-400 text-sm font-medium">AI-Powered Contract Intelligence</span>
            <ArrowRight className="w-3 h-3 text-emerald-400" />
          </div>
        </div>

        {/* Main Title with Text Animation */}
        <div className="text-center mb-6 animate-fade-in-up" style={{ animationDelay: '0.4s' }}>
          <h1 className="text-6xl md:text-8xl font-bold text-white mb-4 tracking-tight">
            {displayedText.split('').map((char, i) => (
              <span
                key={i}
                className={`inline-block ${i >= 8 ? 'text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-cyan-400' : ''}`}
                style={{
                  animation: 'letterPop 0.5s ease forwards',
                  animationDelay: `${i * 0.05}s`,
                  opacity: 0,
                }}
              >
                {char}
              </span>
            ))}
            <span className="animate-blink text-emerald-400">|</span>
          </h1>
        </div>

        {/* Subtitle */}
        <p
          className="text-xl md:text-2xl text-slate-400 font-light max-w-2xl mx-auto text-center leading-relaxed mb-8 animate-fade-in-up"
          style={{ animationDelay: '0.6s' }}
        >
          Transform how your enterprise manages contracts with{' '}
          <span className="text-white font-medium">intelligent automation</span>
        </p>

        {/* Stats Row with Counter Animation */}
        <div
          className="flex flex-wrap justify-center gap-10 mb-10 animate-fade-in-up"
          style={{ animationDelay: '0.8s' }}
        >
          {[
            { value: '90%', label: 'Faster Review' },
            { value: '99%', label: 'Accuracy' },
            { value: '24/7', label: 'Processing' },
          ].map((stat, i) => (
            <div key={i} className="text-center group cursor-default">
              <div className="text-4xl md:text-5xl font-bold text-white mb-1 group-hover:text-emerald-400 transition-colors duration-300">
                {stat.value}
              </div>
              <div className="text-slate-500 text-sm">{stat.label}</div>
            </div>
          ))}
        </div>

        {/* CTA Buttons */}
        <div
          className="flex flex-col sm:flex-row gap-4 animate-fade-in-up"
          style={{ animationDelay: '1s' }}
        >
          <Link
            to={isAuthenticated ? "/dashboard" : "/register"}
            className="group relative px-8 py-4 bg-gradient-to-r from-emerald-500 to-emerald-600 text-white font-semibold rounded-xl overflow-hidden"
            onMouseEnter={() => setCursorVariant('hover')}
            onMouseLeave={() => setCursorVariant('default')}
          >
            <span className="relative z-10 flex items-center justify-center gap-2">
              {isAuthenticated ? 'Go to Dashboard' : 'Start Free Trial'}
              <ArrowRight className="h-5 w-5 group-hover:translate-x-1 transition-transform" />
            </span>
            <div className="absolute inset-0 bg-gradient-to-r from-emerald-600 to-emerald-700 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
            <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500">
              <div className="absolute inset-0 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000 bg-gradient-to-r from-transparent via-white/20 to-transparent" />
            </div>
          </Link>
        </div>

        {/* Scroll Indicator */}
        <div className="absolute bottom-8 left-1/2 -translate-x-1/2 animate-bounce">
          <ChevronDown className="w-6 h-6 text-slate-500" />
        </div>
      </section>

      {/* Features Section */}
      <section id="features" ref={featuresRef} className="relative py-16 px-6">
        <div className="max-w-7xl mx-auto">
          {/* Section Header */}
          <div
            id="features-header"
            data-animate
            className={`text-center mb-12 transition-all duration-1000 ${
              isVisible['features-header'] ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'
            }`}
          >
            <span className="text-emerald-400 text-sm font-semibold tracking-wider uppercase mb-4 block">Features</span>
            <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
              Everything you need to{' '}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-cyan-400">
                manage contracts
              </span>
            </h2>
            <p className="text-slate-400 text-lg max-w-2xl mx-auto">
              Powerful AI-driven tools to streamline your contract lifecycle from creation to compliance
            </p>
          </div>

          {/* Features Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[
              {
                icon: FileText,
                title: 'Smart Extraction',
                description: 'Extract key clauses, dates, parties & metadata automatically using advanced NLP models',
                color: 'emerald',
                gradient: 'from-emerald-500/20 to-emerald-600/20',
              },
              {
                icon: Shield,
                title: 'Risk Analysis',
                description: 'AI-driven risk scoring, deviation detection & real-time compliance monitoring',
                color: 'blue',
                gradient: 'from-blue-500/20 to-blue-600/20',
              },
              {
                icon: Zap,
                title: 'Fast Processing',
                description: 'Process thousands of contracts in seconds. Scale effortlessly with your business',
                color: 'purple',
                gradient: 'from-purple-500/20 to-purple-600/20',
              },
            ].map((feature, i) => (
              <div
                key={i}
                id={`feature-${i}`}
                data-animate
                className={`group relative p-8 rounded-2xl bg-slate-900/50 border border-slate-800 hover:border-${feature.color}-500/50 transition-all duration-500 cursor-pointer overflow-hidden ${
                  isVisible[`feature-${i}`] ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'
                }`}
                style={{ transitionDelay: `${i * 150}ms` }}
                onMouseEnter={() => setCursorVariant('hover')}
                onMouseLeave={() => setCursorVariant('default')}
              >
                {/* Hover Gradient */}
                <div className={`absolute inset-0 bg-gradient-to-br ${feature.gradient} opacity-0 group-hover:opacity-100 transition-opacity duration-500`} />

                {/* Icon */}
                <div className={`relative h-14 w-14 rounded-xl bg-${feature.color}-500/10 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300`}>
                  <feature.icon className={`h-7 w-7 text-${feature.color}-400`} />
                </div>

                {/* Content */}
                <h3 className="relative text-xl font-semibold text-white mb-3 group-hover:text-emerald-400 transition-colors">
                  {feature.title}
                </h3>
                <p className="relative text-slate-400 leading-relaxed">
                  {feature.description}
                </p>

                {/* Arrow */}
                <div className="relative mt-6 flex items-center text-slate-500 group-hover:text-emerald-400 transition-colors">
                  <span className="text-sm font-medium">Learn more</span>
                  <ArrowRight className="w-4 h-4 ml-2 group-hover:translate-x-2 transition-transform" />
                </div>
              </div>
            ))}
          </div>

          {/* Additional Features Pills */}
          <div
            id="features-pills"
            data-animate
            className={`flex flex-wrap justify-center gap-4 mt-10 transition-all duration-1000 ${
              isVisible['features-pills'] ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'
            }`}
          >
            {[
              { icon: CheckCircle, text: 'Clause Library' },
              { icon: BarChart3, text: 'Analytics Dashboard' },
              { icon: Lock, text: 'Enterprise Security' },
            ].map((item, i) => (
              <div
                key={i}
                className="flex items-center gap-2 px-5 py-2.5 bg-slate-800/50 border border-slate-700 rounded-full hover:border-emerald-500/50 hover:bg-slate-800 transition-all duration-300 cursor-pointer"
                onMouseEnter={() => setCursorVariant('hover')}
                onMouseLeave={() => setCursorVariant('default')}
              >
                <item.icon className="w-4 h-4 text-emerald-400" />
                <span className="text-slate-300 text-sm font-medium">{item.text}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="relative py-16 px-6">
        <div className="max-w-7xl mx-auto">
          {/* Section Header */}
          <div
            id="pricing-header"
            data-animate
            className={`text-center mb-12 transition-all duration-1000 ${
              isVisible['pricing-header'] ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'
            }`}
          >
            <span className="text-emerald-400 text-sm font-semibold tracking-wider uppercase mb-4 block">Pricing</span>
            <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
              Simple, transparent{' '}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-cyan-400">
                pricing
              </span>
            </h2>
            <p className="text-slate-400 text-lg max-w-2xl mx-auto">
              Choose the plan that fits your needs. Start free and scale as you grow.
            </p>
          </div>

          {/* Pricing Cards with Navigation */}
          <div className="relative">
            {/* Left Arrow */}
            <button
              onClick={() => setPricingIndex(Math.max(0, pricingIndex - 1))}
              className={`absolute left-0 top-1/2 -translate-y-1/2 -translate-x-4 z-10 w-12 h-12 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center transition-all duration-300 ${
                canScrollLeft
                  ? 'opacity-100 hover:bg-slate-700 hover:border-emerald-500 cursor-pointer'
                  : 'opacity-30 cursor-not-allowed'
              }`}
              disabled={!canScrollLeft}
              onMouseEnter={() => canScrollLeft && setCursorVariant('hover')}
              onMouseLeave={() => setCursorVariant('default')}
            >
              <ChevronLeft className="w-6 h-6 text-white" />
            </button>

            {/* Right Arrow */}
            <button
              onClick={() => setPricingIndex(Math.min(pricingPlans.length - 3, pricingIndex + 1))}
              className={`absolute right-0 top-1/2 -translate-y-1/2 translate-x-4 z-10 w-12 h-12 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center transition-all duration-300 ${
                canScrollRight
                  ? 'opacity-100 hover:bg-slate-700 hover:border-emerald-500 cursor-pointer'
                  : 'opacity-30 cursor-not-allowed'
              }`}
              disabled={!canScrollRight}
              onMouseEnter={() => canScrollRight && setCursorVariant('hover')}
              onMouseLeave={() => setCursorVariant('default')}
            >
              <ChevronRight className="w-6 h-6 text-white" />
            </button>

            {/* Cards Container with Smooth Slide */}
            <div className="overflow-hidden px-8 pt-6">
              <div
                className="flex gap-6 transition-transform duration-500 ease-out"
                style={{ transform: `translateX(-${pricingIndex * (100 / 3 + 2)}%)` }}
              >
                {pricingPlans.map((plan, i) => (
                  <div
                    key={i}
                    className={`relative p-8 rounded-2xl transition-all duration-300 flex-shrink-0 w-full md:w-[calc(33.333%-1rem)] ${
                      plan.popular
                        ? 'bg-gradient-to-b from-emerald-500/20 to-slate-900/50 border-2 border-emerald-500/50'
                        : 'bg-slate-900/50 border border-slate-800 hover:border-slate-700'
                    }`}
                    onMouseEnter={() => setCursorVariant('hover')}
                    onMouseLeave={() => setCursorVariant('default')}
                  >
                    {plan.popular && (
                      <div className="absolute -top-4 left-1/2 -translate-x-1/2 px-4 py-1 bg-emerald-500 text-white text-sm font-medium rounded-full">
                        Most Popular
                      </div>
                    )}
                    <h3 className="text-xl font-semibold text-white mb-2">{plan.name}</h3>
                    <div className="flex items-baseline gap-1 mb-2">
                      <span className="text-4xl font-bold text-white">{plan.price}</span>
                      <span className="text-slate-400">{plan.period}</span>
                    </div>
                    <p className="text-slate-400 text-sm mb-6">{plan.description}</p>
                    <ul className="space-y-3 mb-8">
                      {plan.features.map((feature, j) => (
                        <li key={j} className="flex items-center gap-3 text-slate-300 text-sm">
                          <CheckCircle className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                          {feature}
                        </li>
                      ))}
                    </ul>
                    {plan.isContactSales ? (
                      <a
                        href={`mailto:sales@contractai.com?subject=Interested in ${plan.name} Plan`}
                        className="flex items-center justify-center gap-2 w-full py-3 text-center font-semibold rounded-xl bg-slate-800 text-white hover:bg-slate-700 transition-all duration-300"
                      >
                        <Phone className="w-4 h-4" />
                        {plan.cta}
                      </a>
                    ) : (
                      <Link
                        to="/register"
                        className={`block w-full py-3 text-center font-semibold rounded-xl transition-all duration-300 ${
                          plan.popular
                            ? 'bg-emerald-500 text-white hover:bg-emerald-600'
                            : 'bg-slate-800 text-white hover:bg-slate-700'
                        }`}
                      >
                        {plan.cta}
                      </Link>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Pagination Dots */}
            <div className="flex justify-center gap-2 mt-8">
              {[0, 1, 2].map((idx) => (
                <button
                  key={idx}
                  onClick={() => setPricingIndex(idx)}
                  className={`h-2 rounded-full transition-all duration-500 ${
                    pricingIndex === idx ? 'bg-emerald-400 w-8' : 'bg-slate-600 hover:bg-slate-500 w-2'
                  }`}
                  onMouseEnter={() => setCursorVariant('hover')}
                  onMouseLeave={() => setCursorVariant('default')}
                />
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* About Section */}
      <section id="about" className="relative py-16 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-12 items-center">
            {/* Left Content */}
            <div
              id="about-content"
              data-animate
              className={`transition-all duration-1000 ${
                isVisible['about-content'] ? 'opacity-100 translate-x-0' : 'opacity-0 -translate-x-10'
              }`}
            >
              <span className="text-emerald-400 text-sm font-semibold tracking-wider uppercase mb-4 block">About Us</span>
              <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
                Built by lawyers,{' '}
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-cyan-400">
                  powered by AI
                </span>
              </h2>
              <p className="text-slate-400 text-lg mb-6 leading-relaxed">
                ContractAI was founded with a simple mission: make contract management effortless for everyone. We combine cutting-edge AI technology with deep legal expertise to help businesses manage contracts smarter.
              </p>
              <p className="text-slate-400 text-lg mb-8 leading-relaxed">
                Our team includes former legal professionals, AI researchers, and enterprise software experts who understand the real challenges of contract management.
              </p>
              <div className="flex gap-8">
                {[
                  { value: '500+', label: 'Enterprises' },
                  { value: '1M+', label: 'Contracts Analyzed' },
                  { value: '50+', label: 'Countries' },
                ].map((stat, i) => (
                  <div key={i} className="text-center">
                    <div className="text-2xl font-bold text-white">{stat.value}</div>
                    <div className="text-slate-500 text-sm">{stat.label}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* Right Visual */}
            <div
              id="about-visual"
              data-animate
              className={`relative transition-all duration-1000 ${
                isVisible['about-visual'] ? 'opacity-100 translate-x-0' : 'opacity-0 translate-x-10'
              }`}
            >
              <div className="relative p-8 rounded-2xl bg-slate-900/50 border border-slate-800">
                <div className="grid grid-cols-2 gap-4">
                  {[
                    { icon: Shield, label: 'Bank-grade Security', desc: 'SOC 2 Type II Certified' },
                    { icon: Zap, label: 'Lightning Fast', desc: 'Process in milliseconds' },
                    { icon: Lock, label: 'Privacy First', desc: 'Your data stays yours' },
                    { icon: BarChart3, label: 'Actionable Insights', desc: 'Data-driven decisions' },
                  ].map((item, i) => (
                    <div key={i} className="p-4 rounded-xl bg-slate-800/50 hover:bg-slate-800 transition-colors">
                      <item.icon className="w-8 h-8 text-emerald-400 mb-3" />
                      <h4 className="text-white font-medium mb-1">{item.label}</h4>
                      <p className="text-slate-500 text-sm">{item.desc}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="relative py-16 px-6">
        <div
          id="cta-section"
          data-animate
          className={`max-w-4xl mx-auto text-center transition-all duration-1000 ${
            isVisible['cta-section'] ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'
          }`}
        >
          <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
            Ready to transform your<br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 via-cyan-400 to-blue-400 animate-gradient">
              contract management?
            </span>
          </h2>
          <p className="text-slate-400 text-lg mb-8 max-w-2xl mx-auto">
            Join thousands of enterprises already using ContractAI to save time, reduce risk, and gain insights from their contracts.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              to={isAuthenticated ? "/dashboard" : "/register"}
              className="group relative px-8 py-4 bg-white text-slate-900 font-semibold rounded-xl overflow-hidden hover:shadow-2xl hover:shadow-white/20 transition-all duration-300"
              onMouseEnter={() => setCursorVariant('hover')}
              onMouseLeave={() => setCursorVariant('default')}
            >
              <span className="relative z-10 flex items-center justify-center gap-2">
                Get Started Free
                <ArrowRight className="h-5 w-5 group-hover:translate-x-1 transition-transform" />
              </span>
            </Link>
            <Link
              to="/pricing"
              className="px-8 py-4 text-white font-semibold rounded-xl border border-slate-700 hover:border-slate-500 hover:bg-slate-800/50 transition-all duration-300"
              onMouseEnter={() => setCursorVariant('hover')}
              onMouseLeave={() => setCursorVariant('default')}
            >
              View Pricing
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="relative py-12 px-6 border-t border-slate-800">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <p className="text-slate-500 text-sm">
            © 2025 ContractAI. All rights reserved.
          </p>
          <div className="flex items-center gap-6">
            {['Privacy', 'Terms', 'Contact'].map((item) => (
              <a
                key={item}
                href="#"
                className="text-slate-500 hover:text-white text-sm transition-colors"
                onMouseEnter={() => setCursorVariant('hover')}
                onMouseLeave={() => setCursorVariant('default')}
              >
                {item}
              </a>
            ))}
          </div>
        </div>
      </footer>

      {/* Custom Styles */}
      <style>{`
        @keyframes fade-in-up {
          from {
            opacity: 0;
            transform: translateY(30px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        .animate-fade-in-up {
          animation: fade-in-up 0.8s ease forwards;
          opacity: 0;
        }

        @keyframes letterPop {
          0% {
            opacity: 0;
            transform: translateY(20px) scale(0.9);
          }
          100% {
            opacity: 1;
            transform: translateY(0) scale(1);
          }
        }

        @keyframes blink {
          0%, 50% { opacity: 1; }
          51%, 100% { opacity: 0; }
        }
        .animate-blink {
          animation: blink 1s infinite;
        }

        @keyframes float {
          0%, 100% {
            transform: translateY(0) translateX(0);
          }
          25% {
            transform: translateY(-20px) translateX(10px);
          }
          50% {
            transform: translateY(-10px) translateX(-10px);
          }
          75% {
            transform: translateY(-30px) translateX(5px);
          }
        }
        .animate-float {
          animation: float 15s ease-in-out infinite;
        }

        @keyframes gradient {
          0%, 100% {
            background-position: 0% 50%;
          }
          50% {
            background-position: 100% 50%;
          }
        }
        .animate-gradient {
          background-size: 200% 200%;
          animation: gradient 3s ease infinite;
        }

        .magnetic-btn {
          transition: transform 0.3s ease;
        }
        .magnetic-btn:hover {
          transform: scale(1.05);
        }
      `}</style>
    </div>
  );
};

export default Home;
