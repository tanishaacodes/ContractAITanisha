import { useState, useEffect } from 'react';
import { BarChart3, TrendingUp, Zap, Clock, FileText, MessageSquare, ArrowLeft } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import Sidebar from '../components/Sidebar';
import api from '../utils/api';

export default function ChatAnalytics() {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [days, setDays] = useState(7);
  const navigate = useNavigate();

  useEffect(() => {
    loadAnalytics();
  }, [days]);

  const loadAnalytics = async () => {
    try {
      setLoading(true);
      const response = await api.get(`/chat/analytics?days=${days}`);
      setAnalytics(response.data);
    } catch (error) {
      console.error('Failed to load analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex h-screen bg-slate-900">
        <Sidebar />
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-slate-400">Loading analytics...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-slate-900">
      <Sidebar />

      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header - matching UnifiedChat style */}
        <div className="bg-slate-800 border-b border-slate-700 px-8 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <button
              onClick={() => navigate('/chat')}
              className="p-2 hover:bg-slate-700 rounded-lg transition"
              title="Back to AI Chat"
            >
              <ArrowLeft className="w-5 h-5 text-slate-300" />
            </button>
            <div className="bg-purple-600 p-2 rounded-lg">
              <BarChart3 className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white">Chat Analytics</h1>
              <p className="text-slate-400 text-xs">Insights into your contract queries and AI chat usage</p>
            </div>
          </div>
        </div>

        <div className="flex-1 overflow-auto p-8">
          {/* Time Range Selector */}
          <div className="mb-6 flex gap-2">
            {[7, 14, 30].map((d) => (
              <button
                key={d}
                onClick={() => setDays(d)}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  days === d
                    ? 'bg-blue-600 text-white'
                    : 'bg-slate-800 text-slate-300 hover:bg-slate-700 border border-slate-700'
                }`}
              >
                Last {d} days
              </button>
            ))}
          </div>

          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <div className="bg-slate-800 p-6 rounded-lg border border-slate-700">
              <div className="flex items-center justify-between mb-2">
                <span className="text-slate-400 text-sm">Total Queries</span>
                <MessageSquare className="w-5 h-5 text-blue-500" />
              </div>
              <div className="text-3xl font-bold text-white">
                {analytics?.stats?.total_queries || 0}
              </div>
            </div>

            <div className="bg-slate-800 p-6 rounded-lg border border-slate-700">
              <div className="flex items-center justify-between mb-2">
                <span className="text-slate-400 text-sm">Avg Response Time</span>
                <Clock className="w-5 h-5 text-green-500" />
              </div>
              <div className="text-3xl font-bold text-white">
                {analytics?.stats?.avg_response_time || 0}ms
              </div>
            </div>

            <div className="bg-slate-800 p-6 rounded-lg border border-slate-700">
              <div className="flex items-center justify-between mb-2">
                <span className="text-slate-400 text-sm">Cache Hit Rate</span>
                <Zap className="w-5 h-5 text-yellow-500" />
              </div>
              <div className="text-3xl font-bold text-white">
                {analytics?.stats?.cache_hit_rate || 0}%
              </div>
            </div>

            <div className="bg-slate-800 p-6 rounded-lg border border-slate-700">
              <div className="flex items-center justify-between mb-2">
                <span className="text-slate-400 text-sm">Cached Responses</span>
                <TrendingUp className="w-5 h-5 text-purple-500" />
              </div>
              <div className="text-3xl font-bold text-white">
                {analytics?.stats?.cached_responses || 0}
              </div>
            </div>
          </div>

          {/* Top Questions */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-slate-800 p-6 rounded-lg border border-slate-700">
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <MessageSquare className="w-5 h-5 text-blue-500" />
                Top Questions
              </h3>
              {analytics?.top_questions && analytics.top_questions.length > 0 ? (
                <div className="space-y-3">
                  {analytics.top_questions.map((q, idx) => (
                    <div key={idx} className="flex items-center justify-between p-3 bg-slate-700/50 rounded-lg">
                      <span className="text-sm text-slate-300 flex-1 truncate">{q.query}</span>
                      <span className="ml-3 px-3 py-1 bg-blue-600 text-white rounded-full text-xs font-medium">
                        {q.count}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-slate-500 text-center py-8">No questions yet</p>
              )}
            </div>

            {/* Most Queried Contracts */}
            <div className="bg-slate-800 p-6 rounded-lg border border-slate-700">
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <FileText className="w-5 h-5 text-green-500" />
                Most Queried Contracts
              </h3>
              {analytics?.top_contracts && analytics.top_contracts.length > 0 ? (
                <div className="space-y-3">
                  {analytics.top_contracts.map((c, idx) => (
                    <div key={idx} className="flex items-center justify-between p-3 bg-slate-700/50 rounded-lg">
                      <span className="text-sm text-slate-300 flex-1 truncate">{c.filename}</span>
                      <span className="ml-3 px-3 py-1 bg-green-600 text-white rounded-full text-xs font-medium">
                        {c.count}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-slate-500 text-center py-8">No contracts queried yet</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
