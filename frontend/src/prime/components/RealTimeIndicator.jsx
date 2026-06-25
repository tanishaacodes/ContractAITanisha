import { useState, useEffect } from 'react';
import { Wifi, WifiOff, RefreshCw, Bell } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export default function RealTimeIndicator({ isConnected, lastUpdate, onRefresh }) {
  const [showNotification, setShowNotification] = useState(false);

  useEffect(() => {
    if (lastUpdate) {
      setShowNotification(true);
      const timer = setTimeout(() => setShowNotification(false), 3000);
      return () => clearTimeout(timer);
    }
  }, [lastUpdate]);

  const getTimeAgo = (timestamp) => {
    if (!timestamp) return 'Never';
    const seconds = Math.floor((new Date() - new Date(timestamp)) / 1000);
    if (seconds < 60) return 'Just now';
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    return `${Math.floor(seconds / 86400)}d ago`;
  };

  return (
    <>
      {/* Inline status bar - no fixed positioning */}
      <div className="flex items-center gap-2">
        <div className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border text-xs font-medium transition-all duration-300 ${
          isConnected
            ? 'bg-green-500/10 border-green-500/30 text-green-400'
            : 'bg-red-500/10 border-red-500/30 text-red-400'
        }`}>
          {isConnected
            ? <Wifi className="w-3.5 h-3.5 animate-pulse" />
            : <WifiOff className="w-3.5 h-3.5" />
          }
          {isConnected ? 'Live' : 'Offline'}
        </div>

        <button
          onClick={onRefresh}
          className="p-1.5 rounded-lg bg-white/10 hover:bg-white/20 border border-white/10 transition-colors"
          title="Refresh Dashboard"
        >
          <RefreshCw className="w-3.5 h-3.5 text-white" />
        </button>

        {lastUpdate && (
          <span className="text-xs text-gray-400 px-2 py-1.5 rounded-lg bg-white/5 border border-white/10">
            Updated {getTimeAgo(lastUpdate)}
          </span>
        )}
      </div>

      {/* Toast notification - fixed bottom-right, away from header */}
      <AnimatePresence>
        {showNotification && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 10 }}
            className="fixed bottom-6 right-6 z-50"
          >
            <div className="flex items-center gap-3 px-4 py-3 rounded-lg bg-blue-500/10 backdrop-blur-lg border border-blue-500/30 shadow-2xl">
              <Bell className="w-4 h-4 text-blue-400 animate-bounce" />
              <div>
                <p className="text-sm font-semibold text-blue-400">Dashboard updated</p>
                <p className="text-xs text-gray-400">Data refreshed</p>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
