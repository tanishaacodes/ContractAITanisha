import { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, RefreshCw, Activity } from 'lucide-react';
import api from '../../utils/api';

export default function RealTimeCommodityPrices() {
  const [prices, setPrices] = useState([]);
  const [loading, setLoading] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(null);

  const commodities = ['Steel', 'Copper', 'Oil', 'Aluminum', 'Gold'];

  useEffect(() => {
    fetchPrices();
    // Auto-refresh every 5 minutes
    const interval = setInterval(fetchPrices, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  const fetchPrices = async () => {
    setLoading(true);
    const priceData = [];

    for (const commodity of commodities) {
      try {
        const response = await api.get(`/enterprise/commodity-prices/${commodity}/`);
        priceData.push({
          name: commodity,
          ...response.data
        });
      } catch (error) {
        console.error(`Failed to fetch price for ${commodity}:`, error);
        // Use fallback data
        priceData.push({
          name: commodity,
          price: 0,
          change: 0,
          change_percent: '0%',
          source: 'unavailable'
        });
      }
    }

    setPrices(priceData);
    setLastUpdated(new Date());
    setLoading(false);
  };

  const handleRefresh = () => {
    fetchPrices();
  };

  const formatPrice = (price, commodity) => {
    if (price >= 1000) {
      return `$${price.toLocaleString()}`;
    }
    return `$${price.toFixed(2)}`;
  };

  const getPriceChangeColor = (change) => {
    if (change > 0) return 'text-green-400';
    if (change < 0) return 'text-red-400';
    return 'text-slate-400';
  };

  const getPriceChangeIcon = (change) => {
    if (change > 0) return <TrendingUp className="w-4 h-4" />;
    if (change < 0) return <TrendingDown className="w-4 h-4" />;
    return <Activity className="w-4 h-4" />;
  };

  return (
    <div className="bg-gradient-to-br from-slate-800/60 to-slate-900/60 backdrop-blur-xl border border-amber-500/20 rounded-2xl p-6 shadow-[0_0_30px_rgba(251,191,36,0.15)]">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <Activity className="w-6 h-6 text-amber-400" />
          <div>
            <h3 className="text-xl font-bold text-white">Live Commodity Prices</h3>
            {lastUpdated && (
              <p className="text-xs text-slate-400">
                Updated: {lastUpdated.toLocaleTimeString()}
              </p>
            )}
          </div>
        </div>

        <button
          onClick={handleRefresh}
          disabled={loading}
          className="p-2 rounded-lg bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 transition-all disabled:opacity-50"
        >
          <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      <div className="space-y-3">
        {prices.map((commodity) => (
          <div
            key={commodity.name}
            className="flex items-center justify-between p-4 bg-slate-800/50 rounded-xl border border-slate-700 hover:border-amber-500/50 transition-all"
          >
            <div className="flex items-center gap-4">
              <div className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
              <div>
                <p className="font-semibold text-white">{commodity.name}</p>
                <p className="text-xs text-slate-500">
                  {commodity.source === 'database' && '(Cached)'}
                  {commodity.source === 'alpha_vantage' && '(Live - Alpha Vantage)'}
                  {commodity.source === 'finnhub' && '(Live - Finnhub)'}
                  {commodity.source === 'unavailable' && '(Unavailable)'}
                </p>
              </div>
            </div>

            <div className="text-right">
              <p className="text-lg font-bold text-white">
                {formatPrice(commodity.price, commodity.name)}
              </p>
              <div className={`flex items-center gap-1 text-sm ${getPriceChangeColor(commodity.change)}`}>
                {getPriceChangeIcon(commodity.change)}
                <span>{commodity.change_percent}</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {loading && prices.length === 0 && (
        <div className="text-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-amber-400 mx-auto"></div>
          <p className="text-slate-400 mt-4">Fetching live prices...</p>
        </div>
      )}
    </div>
  );
}
