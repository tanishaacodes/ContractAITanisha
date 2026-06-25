import { TrendingDown, TrendingUp, AlertTriangle, DollarSign } from 'lucide-react';
import useThemeStore from '../../store/themeStore';

/**
 * Executive KPI Cards for What-If Analysis
 * Shows risk before/after and reduction percentage
 */
export default function WhatIfKPIs({ delta, exposure }) {
  const { currentTheme } = useThemeStore();
  const theme = currentTheme;

  if (!delta) return null;

  const reductionPct = delta.risk_reduction_pct || 0;
  const isReduction = reductionPct > 0;

  const kpis = [
    {
      label: 'Risk Before',
      value: delta.risk_before?.toFixed(3) || '0.000',
      color: 'border-red-500',
      icon: AlertTriangle,
      iconColor: 'text-red-500'
    },
    {
      label: 'Risk After',
      value: delta.risk_after?.toFixed(3) || '0.000',
      color: 'border-blue-500',
      icon: AlertTriangle,
      iconColor: 'text-blue-500'
    },
    {
      label: 'Risk Reduced',
      value: `${isReduction ? '-' : '+'}${Math.abs(reductionPct).toFixed(1)}%`,
      color: isReduction ? 'border-green-500' : 'border-orange-500',
      icon: isReduction ? TrendingDown : TrendingUp,
      iconColor: isReduction ? 'text-green-500' : 'text-orange-500',
      highlight: true
    }
  ];

  // Add exposure KPI if available
  if (exposure?.exposure) {
    const delta = exposure.exposure.delta || 0;
    const currency = exposure.currency || 'INR';

    // Format amount based on currency
    const formatAmount = (amount) => {
      if (!amount) return '0';

      if (currency === 'INR') {
        if (amount >= 10000000) {
          return `${(amount / 10000000).toFixed(1)} Cr`;
        } else if (amount >= 100000) {
          return `${(amount / 100000).toFixed(1)} L`;
        }
      } else {
        if (amount >= 1000000) {
          return `${(amount / 1000000).toFixed(1)}M`;
        }
      }
      return amount.toLocaleString();
    };

    kpis.push({
      label: 'Exposure Reduced',
      value: formatAmount(delta),
      subValue: `(${exposure.exposure.reduction_pct?.toFixed(1) || 0}% reduction)`,
      color: 'border-purple-500',
      icon: DollarSign,
      iconColor: 'text-purple-500',
      prefix: currency === 'INR' ? '\u20B9' : '$'
    });
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
      {kpis.map((kpi, index) => {
        const Icon = kpi.icon;
        return (
          <div
            key={index}
            className={`rounded-lg shadow p-5 border-l-4 ${kpi.color} ${
              kpi.highlight
                ? theme === 'dark'
                  ? 'bg-green-900 bg-opacity-30'
                  : 'bg-green-50'
                : theme === 'dark'
                  ? 'bg-gray-800'
                  : 'bg-white'
            }`}
          >
            <div className="flex items-center justify-between">
              <div>
                <p className={`text-sm font-medium ${
                  theme === 'dark' ? 'text-gray-400' : 'text-gray-500'
                }`}>
                  {kpi.label}
                </p>
                <p className={`text-2xl font-bold mt-1 ${
                  kpi.highlight
                    ? isReduction ? 'text-green-600' : 'text-orange-600'
                    : theme === 'dark' ? 'text-white' : 'text-gray-900'
                }`}>
                  {kpi.prefix}{kpi.value}
                </p>
                {kpi.subValue && (
                  <p className={`text-sm mt-1 ${
                    theme === 'dark' ? 'text-gray-400' : 'text-gray-600'
                  }`}>
                    ({kpi.subValue} reduction)
                  </p>
                )}
              </div>
              <Icon className={`w-10 h-10 ${kpi.iconColor} opacity-50`} />
            </div>
          </div>
        );
      })}
    </div>
  );
}
