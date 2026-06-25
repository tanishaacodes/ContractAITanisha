import { DollarSign, TrendingDown, AlertCircle } from 'lucide-react';
import useThemeStore from '../../store/themeStore';

/**
 * Executive Exposure KPI Cards (Rupees/Dollars)
 * Shows financial exposure before/after and reduction
 */
export default function ExposureKPIs({ exposure }) {
  const { currentTheme } = useThemeStore();
  const theme = currentTheme;

  if (!exposure || !exposure.exposure) return null;

  // Show warning banner when contract value is missing
  if (exposure.warning) {
    return (
      <div className="flex items-start gap-2 bg-amber-900/30 border border-amber-700 rounded-lg p-4">
        <AlertCircle size={18} className="text-amber-400 mt-0.5 shrink-0" />
        <p className="text-amber-300 text-sm">{exposure.warning}</p>
      </div>
    );
  }

  const { before, after, delta, reduction_pct } = exposure.exposure;
  const currency = exposure.currency || 'INR';
  const currencySymbol = currency === 'INR' ? '\u20B9' : '$';

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

  const kpis = [
    {
      label: 'Exposure Before',
      value: formatAmount(before),
      color: 'bg-red-50 border-red-200',
      darkColor: 'bg-red-900 bg-opacity-30 border-red-800',
      textColor: 'text-red-600'
    },
    {
      label: 'Exposure After',
      value: formatAmount(after),
      color: 'bg-green-50 border-green-200',
      darkColor: 'bg-green-900 bg-opacity-30 border-green-800',
      textColor: 'text-green-600'
    },
    {
      label: 'Exposure Reduced',
      value: formatAmount(delta),
      subValue: `${(reduction_pct || 0).toFixed(1)}%`,
      color: 'bg-blue-50 border-blue-200',
      darkColor: 'bg-blue-900 bg-opacity-30 border-blue-800',
      textColor: 'text-blue-600',
      highlight: true
    }
  ];

  return (
    <div className="mb-6">
      <div className="flex items-center space-x-2 mb-4">
        <DollarSign className="w-5 h-5 text-green-600" />
        <h3 className={`text-lg font-semibold ${
          theme === 'dark' ? 'text-white' : 'text-gray-900'
        }`}>
          Financial Exposure Impact
        </h3>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {kpis.map((kpi, index) => (
          <div
            key={index}
            className={`rounded-lg p-5 border ${
              theme === 'dark' ? kpi.darkColor : kpi.color
            } ${kpi.highlight ? 'border-l-4 border-l-blue-500' : ''}`}
          >
            <p className={`text-sm font-medium mb-1 ${
              theme === 'dark' ? 'text-gray-400' : 'text-gray-600'
            }`}>
              {kpi.label}
            </p>
            <p className={`text-2xl font-bold ${kpi.textColor}`}>
              {currencySymbol}{kpi.value}
            </p>
            {kpi.subValue && (
              <p className={`text-sm mt-1 ${
                theme === 'dark' ? 'text-gray-400' : 'text-gray-500'
              }`}>
                ({kpi.subValue} reduction)
              </p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
