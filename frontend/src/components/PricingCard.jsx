import React from 'react';
import { Check, ArrowRight, Phone, Sparkles } from 'lucide-react';
import useThemeStore from '../store/themeStore';

const PricingCard = ({ plan, isSelected, onSelect, isPopular = false }) => {
  const { theme, currentTheme } = useThemeStore();
  const isDark = currentTheme === 'dark';
  const handleClick = () => {
    if (!plan.isContactSales) {
      onSelect(plan);
    } else {
      // Open email client for Enterprise/On-premise plans
      window.location.href = `mailto:sales@contractai.com?subject=Interested in ${plan.displayName}&body=Hi, I'm interested in learning more about the ${plan.displayName}. Please contact me.`;
    }
  };

  const formatPrice = () => {
    if (plan.isContactSales) {
      return 'Custom';
    }
    if (plan.priceMonthly === 0) {
      return 'Free';
    }
    return `$${plan.priceMonthly}`;
  };

  const formatContractLimit = () => {
    if (plan.contractLimit === -1) {
      return 'Unlimited contracts';
    }
    return `${plan.contractLimit} contracts`;
  };

  return (
    <div
      className={`
        relative flex flex-col rounded-2xl transition-all duration-300 h-full
        ${isSelected
          ? 'transform scale-105 shadow-2xl ring-4 ring-blue-400 ring-opacity-50'
          : 'shadow-lg hover:shadow-2xl hover:-translate-y-2'
        }
        ${isDark
          ? isPopular
            ? 'bg-gradient-to-br from-slate-800 via-slate-700 to-slate-800 border-2 border-blue-500'
            : `${theme.colors.surface} border-2 ${theme.colors.surfaceBorder} hover:border-blue-400`
          : isPopular
            ? 'bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 border-2 border-blue-500'
            : 'bg-white border-2 border-gray-200 hover:border-blue-400'
        }
      `}
    >
      {/* Popular Badge */}
      {isPopular && (
        <div className="absolute -top-4 left-1/2 transform -translate-x-1/2 z-10">
          <div className="flex items-center gap-1.5 px-5 py-2 rounded-full text-xs font-extrabold bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 text-white shadow-xl border-2 border-white">
            <Sparkles className="h-4 w-4" />
            <span>MOST POPULAR</span>
          </div>
        </div>
      )}

      {/* Card Content - with flex-1 to make all cards equal height */}
      <div className="p-8 flex flex-col flex-1">

        {/* Plan Header */}
        <div className="text-center mb-6">
          <h3 className={`text-2xl font-extrabold mb-4 ${
            isDark
              ? isPopular ? 'text-blue-300' : `${theme.colors.textPrimary}`
              : isPopular ? 'text-blue-900' : 'text-gray-900'
          }`}>
            {plan.displayName}
          </h3>

          {/* Price */}
          <div className="mb-4">
            <div className="flex items-baseline justify-center gap-1">
              <span className={`text-5xl font-black ${
                isDark
                  ? isPopular
                    ? 'bg-gradient-to-r from-blue-400 via-indigo-400 to-purple-400 bg-clip-text text-transparent'
                    : 'text-blue-400'
                  : isPopular
                    ? 'bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 bg-clip-text text-transparent'
                    : 'text-gray-900'
              }`}>
                {formatPrice()}
              </span>
              {!plan.isContactSales && plan.priceMonthly > 0 && (
                <span className={`text-lg font-semibold ${isDark ? `${theme.colors.textSecondary}` : 'text-gray-500'}`}>/mo</span>
              )}
            </div>
            {!plan.isContactSales && plan.priceMonthly > 0 && (
              <p className={`text-sm mt-1 font-medium ${isDark ? `${theme.colors.textSecondary}` : 'text-gray-500'}`}>per month</p>
            )}
          </div>

          {/* Description */}
          {plan.description && (
            <p className={`text-sm leading-relaxed px-2 font-medium ${isDark ? `${theme.colors.textSecondary}` : 'text-gray-600'}`}>
              {plan.description}
            </p>
          )}
        </div>

        {/* Contract Limit */}
        <div className={`mb-6 pb-6 ${isDark ? `border-b ${theme.colors.surfaceBorder}` : 'border-b border-gray-200'}`}>
          <div className={`text-center px-4 py-3 rounded-xl ${
            isDark
              ? isPopular
                ? 'bg-gradient-to-r from-blue-900/40 to-indigo-900/40'
                : `${theme.colors.surfaceHover}`
              : isPopular
                ? 'bg-gradient-to-r from-blue-100 to-indigo-100'
                : 'bg-gray-100'
          }`}>
            <p className={`text-base font-extrabold ${
              isDark
                ? isPopular ? 'text-blue-300' : `${theme.colors.textPrimary}`
                : isPopular ? 'text-blue-900' : 'text-gray-900'
            }`}>
              {formatContractLimit()}
            </p>
          </div>
        </div>

        {/* Features List - flex-1 to push button to bottom */}
        <ul className="space-y-4 mb-8 flex-1">
          {plan.features && plan.features.map((feature, index) => (
            <li key={index} className="flex items-start">
              <div className={`rounded-full p-1 mr-3 flex-shrink-0 mt-0.5 ${isPopular ? 'bg-gradient-to-r from-blue-500 to-purple-500' : 'bg-green-500'}`}>
                <Check className="h-3.5 w-3.5 text-white" strokeWidth={3} />
              </div>
              <span className={`text-sm font-semibold leading-relaxed ${isDark ? `${theme.colors.textSecondary}` : 'text-gray-700'}`}>{feature}</span>
            </li>
          ))}
        </ul>

        {/* CTA Button - at bottom */}
        <div className="mt-auto">
          <button
            onClick={handleClick}
            className={`
              w-full py-4 px-6 rounded-xl font-bold text-base transition-all duration-300
              flex items-center justify-center gap-2 transform
              ${isSelected
                ? 'bg-gradient-to-r from-green-600 to-green-700 text-white shadow-xl hover:shadow-2xl hover:scale-105 ring-4 ring-green-300'
                : isPopular
                ? 'bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 text-white hover:from-blue-700 hover:via-indigo-700 hover:to-purple-700 shadow-xl hover:shadow-2xl hover:scale-105'
                : plan.isContactSales
                ? 'bg-gradient-to-r from-gray-800 to-gray-900 text-white hover:from-gray-900 hover:to-black shadow-lg hover:shadow-xl hover:scale-105'
                : isDark
                ? `${theme.colors.surfaceHover} text-blue-300 border-2 border-blue-500 hover:${theme.colors.surface} hover:border-blue-400 shadow-lg hover:shadow-xl hover:scale-105`
                : 'bg-white text-blue-600 border-2 border-blue-600 hover:bg-blue-50 hover:border-blue-700 shadow-lg hover:shadow-xl hover:scale-105'
              }
            `}
          >
            {plan.isContactSales ? (
              <>
                <Phone className="h-5 w-5" />
                <span>Contact Sales</span>
              </>
            ) : isSelected ? (
              <>
                <Check className="h-5 w-5" />
                <span>Selected</span>
              </>
            ) : (
              <>
                <span>Select {plan.name}</span>
                <ArrowRight className="h-5 w-5" />
              </>
            )}
          </button>

          {/* Enterprise Note */}
          {plan.isContactSales && (
            <p className={`mt-4 text-center text-xs leading-relaxed font-medium ${isDark ? `${theme.colors.textSecondary}` : 'text-gray-500'}`}>
              Custom pricing and features tailored to your needs
            </p>
          )}
        </div>
      </div>
    </div>
  );
};

export default PricingCard;
