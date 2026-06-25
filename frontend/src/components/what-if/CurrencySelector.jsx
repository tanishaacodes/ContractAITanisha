import { useState, useEffect } from 'react';
import { DollarSign, RefreshCw } from 'lucide-react';
import useThemeStore from '../../store/themeStore';
import api from '../../utils/api';

/**
 * Currency Selector with Real-Time Conversion
 * Allows users to view exposure in different currencies
 */
export default function CurrencySelector({ onCurrencyChange, defaultCurrency = 'INR' }) {
  const { currentTheme } = useThemeStore();
  const theme = currentTheme;

  const [selectedCurrency, setSelectedCurrency] = useState(defaultCurrency);
  const [currencies, setCurrencies] = useState({});
  const [loading, setLoading] = useState(false);
  const [exchangeRate, setExchangeRate] = useState(null);

  // Load supported currencies
  useEffect(() => {
    loadCurrencies();
  }, []);

  // Update exchange rate when currency changes
  useEffect(() => {
    if (selectedCurrency !== defaultCurrency) {
      fetchExchangeRate();
    }
  }, [selectedCurrency, defaultCurrency]);

  const loadCurrencies = async () => {
    try {
      const response = await api.get('/currency/supported');
      if (response.data.success) {
        setCurrencies(response.data.currencies || {});
      }
    } catch (err) {
      console.error('Failed to load currencies:', err);
      // Fallback currencies
      setCurrencies({
        'USD': 'US Dollar',
        'INR': 'Indian Rupee',
        'EUR': 'Euro',
        'GBP': 'British Pound'
      });
    }
  };

  const fetchExchangeRate = async () => {
    if (selectedCurrency === defaultCurrency) {
      setExchangeRate(null);
      return;
    }

    setLoading(true);
    try {
      const response = await api.get(
        `/currency/rate/${defaultCurrency}/${selectedCurrency}`
      );
      if (response.data.success) {
        setExchangeRate(response.data.rate);
      }
    } catch (err) {
      console.error('Failed to fetch exchange rate:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCurrencyChange = (currency) => {
    setSelectedCurrency(currency);
    if (onCurrencyChange) {
      onCurrencyChange(currency);
    }
  };

  return (
    <div className={`rounded-lg p-4 border ${
      theme === 'dark'
        ? 'bg-gray-800 border-gray-700'
        : 'bg-white border-gray-200'
    }`}>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-2">
          <DollarSign className="w-5 h-5 text-green-500" />
          <label className={`text-sm font-medium ${
            theme === 'dark' ? 'text-gray-300' : 'text-gray-700'
          }`}>
            Display Currency
          </label>
        </div>

        {loading && (
          <RefreshCw className="w-4 h-4 text-blue-500 animate-spin" />
        )}
      </div>

      <select
        value={selectedCurrency}
        onChange={(e) => handleCurrencyChange(e.target.value)}
        className={`w-full px-3 py-2 rounded-lg border ${
          theme === 'dark'
            ? 'bg-gray-700 border-gray-600 text-white'
            : 'bg-white border-gray-300 text-gray-900'
        } focus:outline-none focus:ring-2 focus:ring-blue-500`}
      >
        {Object.entries(currencies).map(([code, name]) => (
          <option key={code} value={code}>
            {code} - {name}
          </option>
        ))}
      </select>

      {exchangeRate && (
        <div className={`mt-2 text-xs ${
          theme === 'dark' ? 'text-gray-400' : 'text-gray-600'
        }`}>
          Exchange Rate: 1 {defaultCurrency} = {exchangeRate.toFixed(4)} {selectedCurrency}
        </div>
      )}

      <p className={`mt-2 text-xs ${
        theme === 'dark' ? 'text-gray-500' : 'text-gray-500'
      }`}>
        Real-time exchange rates updated hourly
      </p>
    </div>
  );
}
