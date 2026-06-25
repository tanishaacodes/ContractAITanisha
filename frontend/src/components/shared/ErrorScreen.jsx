/**
 * Reusable error screen component for enterprise pages
 */
import { AlertTriangle } from 'lucide-react';

export default function ErrorScreen({
  error,
  onRetry,
  title = 'Error Loading Data'
}) {
  return (
    <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      <div className="text-center max-w-md">
        <AlertTriangle className="w-16 h-16 text-red-400 mx-auto mb-4" />
        <h2 className="text-2xl font-bold text-white mb-2">{title}</h2>
        <p className="text-slate-400 mb-6">{error}</p>
        {onRetry && (
          <button
            onClick={onRetry}
            className="px-6 py-3 bg-cyan-500 hover:bg-cyan-600 text-white rounded-xl font-semibold transition-all"
          >
            Retry
          </button>
        )}
      </div>
    </div>
  );
}
