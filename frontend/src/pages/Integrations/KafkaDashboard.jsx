import { useState, useEffect } from 'react';
import { Activity, Send, CheckCircle, XCircle, Users, BarChart3 } from 'lucide-react';
import useAuthStore from '../../store/authStore';
import useThemeStore from '../../store/themeStore';

const KafkaDashboard = () => {
  const { theme } = useThemeStore();
  const { token } = useAuthStore();
  const [status, setStatus] = useState(null);
  const [topics, setTopics] = useState([]);
  const [consumerGroups, setConsumerGroups] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [publishing, setPublishing] = useState(false);

  const [messageForm, setMessageForm] = useState({
    topic: '',
    message: '',
  });

  useEffect(() => {
    fetchStatus();
    fetchTopics();
    fetchConsumerGroups();
    fetchMetrics();
  }, []);

  const fetchStatus = async () => {
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL||(import.meta.env.VITE_API_URL||'http://localhost:8002')}/api/integrations/kafka/status/`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await response.json();
      setStatus(data);
    } catch (error) {
      console.error('Failed to fetch Kafka status:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchTopics = async () => {
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL||(import.meta.env.VITE_API_URL||'http://localhost:8002')}/api/integrations/kafka/topics/`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await response.json();
      setTopics(data.topics || []);
    } catch (error) {
      console.error('Failed to fetch topics:', error);
    }
  };

  const fetchConsumerGroups = async () => {
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL||(import.meta.env.VITE_API_URL||'http://localhost:8002')}/api/integrations/kafka/consumer-groups/`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await response.json();
      setConsumerGroups(data.consumerGroups || []);
    } catch (error) {
      console.error('Failed to fetch consumer groups:', error);
    }
  };

  const fetchMetrics = async () => {
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL||(import.meta.env.VITE_API_URL||'http://localhost:8002')}/api/integrations/kafka/metrics/`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await response.json();
      setMetrics(data);
    } catch (error) {
      console.error('Failed to fetch metrics:', error);
    }
  };

  const handlePublish = async (e) => {
    e.preventDefault();
    setPublishing(true);

    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL||(import.meta.env.VITE_API_URL||'http://localhost:8002')}/api/integrations/kafka/publish/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          topic: messageForm.topic,
          payload: JSON.parse(messageForm.message),
        }),
      });

      if (response.ok) {
        const data = await response.json();
        alert(data.message);
        setMessageForm({ topic: '', message: '' });
        fetchMetrics();
      }
    } catch (error) {
      alert('Failed to publish message');
      console.error(error);
    } finally {
      setPublishing(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-xl">Loading Kafka Dashboard...</div>
      </div>
    );
  }

  return (
    <div className={`min-h-screen ${theme.colors.background} ${theme.colors.textPrimary} p-8`}>
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-4 mb-4">
          <div className="p-4 bg-gradient-to-br from-orange-500 to-orange-600 rounded-xl">
            <Activity size={32} className="text-white" />
          </div>
          <div>
            <h1 className="text-4xl font-bold">Kafka Connector</h1>
            <p className={theme.colors.textSecondary}>
              Event streaming and microservices integration
            </p>
          </div>
        </div>
      </div>

      {/* Status Card */}
      {status && (
        <div className={`${theme.colors.surface} p-6 rounded-xl border ${theme.colors.surfaceBorder} mb-8`}>
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-semibold mb-2">Broker Status</h2>
              <div className="flex items-center gap-3">
                {status.status === 'connected' ? (
                  <>
                    <CheckCircle className="text-green-500" size={24} />
                    <span className="text-green-500 font-semibold">Connected</span>
                  </>
                ) : (
                  <>
                    <XCircle className="text-red-500" size={24} />
                    <span className="text-red-500 font-semibold">Disconnected</span>
                  </>
                )}
              </div>
              <p className={`text-sm ${theme.colors.textSecondary} mt-2`}>
                Broker: {status.broker}
              </p>
            </div>

            <div className="text-right">
              <p className={`text-sm ${theme.colors.textSecondary}`}>Active Topics</p>
              <p className="text-3xl font-bold">{topics.length}</p>
            </div>
          </div>
        </div>
      )}

      {/* Metrics */}
      {metrics && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className={`${theme.colors.surface} p-6 rounded-xl border ${theme.colors.surfaceBorder}`}>
            <div className="flex items-center justify-between">
              <div>
                <p className={`text-sm ${theme.colors.textSecondary}`}>Messages/Sec</p>
                <p className="text-2xl font-bold mt-1">{metrics.messagesPerSecond}</p>
              </div>
              <Activity className="text-orange-500" size={32} />
            </div>
          </div>

          <div className={`${theme.colors.surface} p-6 rounded-xl border ${theme.colors.surfaceBorder}`}>
            <div className="flex items-center justify-between">
              <div>
                <p className={`text-sm ${theme.colors.textSecondary}`}>Total Partitions</p>
                <p className="text-2xl font-bold mt-1">{metrics.totalPartitions}</p>
              </div>
              <BarChart3 className="text-blue-500" size={32} />
            </div>
          </div>

          <div className={`${theme.colors.surface} p-6 rounded-xl border ${theme.colors.surfaceBorder}`}>
            <div className="flex items-center justify-between">
              <div>
                <p className={`text-sm ${theme.colors.textSecondary}`}>Consumer Groups</p>
                <p className="text-2xl font-bold mt-1">{consumerGroups.length}</p>
              </div>
              <Users className="text-green-500" size={32} />
            </div>
          </div>

          <div className={`${theme.colors.surface} p-6 rounded-xl border ${theme.colors.surfaceBorder}`}>
            <div className="flex items-center justify-between">
              <div>
                <p className={`text-sm ${theme.colors.textSecondary}`}>Lag</p>
                <p className="text-2xl font-bold mt-1">{metrics.consumerLag}</p>
              </div>
              <Activity className="text-purple-500" size={32} />
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Topics */}
        <div>
          <h2 className="text-2xl font-bold mb-4">Topics</h2>
          <div className={`${theme.colors.surface} rounded-xl border ${theme.colors.surfaceBorder} overflow-hidden`}>
            <table className="w-full">
              <thead className={`${theme.colors.surfaceHover}`}>
                <tr>
                  <th className="px-4 py-3 text-left">Topic Name</th>
                  <th className="px-4 py-3 text-center">Partitions</th>
                  <th className="px-4 py-3 text-center">Replicas</th>
                </tr>
              </thead>
              <tbody>
                {topics.map((topic) => (
                  <tr key={topic.name} className={`border-t ${theme.colors.surfaceBorder}`}>
                    <td className="px-4 py-3">{topic.name}</td>
                    <td className="px-4 py-3 text-center">{topic.partitions}</td>
                    <td className="px-4 py-3 text-center">{topic.replicas}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Publish Message */}
        <div>
          <h2 className="text-2xl font-bold mb-4">Publish Message</h2>
          <div className={`${theme.colors.surface} p-6 rounded-xl border ${theme.colors.surfaceBorder}`}>
            <form onSubmit={handlePublish} className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Topic</label>
                <select
                  required
                  value={messageForm.topic}
                  onChange={(e) => setMessageForm({ ...messageForm, topic: e.target.value })}
                  className={`w-full px-4 py-2 rounded-lg ${theme.colors.surfaceHover} border ${theme.colors.surfaceBorder}`}
                >
                  <option value="">Select Topic</option>
                  {topics.map((topic) => (
                    <option key={topic.name} value={topic.name}>
                      {topic.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Message (JSON)</label>
                <textarea
                  required
                  value={messageForm.message}
                  onChange={(e) => setMessageForm({ ...messageForm, message: e.target.value })}
                  placeholder='{"event": "contract_signed", "contractId": "123"}'
                  rows={6}
                  className={`w-full px-4 py-2 rounded-lg ${theme.colors.surfaceHover} border ${theme.colors.surfaceBorder} font-mono text-sm`}
                />
              </div>

              <button
                type="submit"
                disabled={publishing}
                className="w-full flex items-center justify-center gap-2 px-6 py-3 bg-gradient-to-r from-orange-500 to-orange-600 text-white rounded-lg hover:from-orange-600 hover:to-orange-700 transition disabled:opacity-50"
              >
                <Send size={20} />
                {publishing ? 'Publishing...' : 'Publish Message'}
              </button>
            </form>
          </div>
        </div>
      </div>

      {/* Consumer Groups */}
      <div className="mt-8">
        <h2 className="text-2xl font-bold mb-4">Consumer Groups</h2>
        <div className={`${theme.colors.surface} rounded-xl border ${theme.colors.surfaceBorder} overflow-hidden`}>
          <table className="w-full">
            <thead className={`${theme.colors.surfaceHover}`}>
              <tr>
                <th className="px-6 py-3 text-left">Group ID</th>
                <th className="px-6 py-3 text-center">Members</th>
                <th className="px-6 py-3 text-center">State</th>
                <th className="px-6 py-3 text-center">Lag</th>
              </tr>
            </thead>
            <tbody>
              {consumerGroups.map((group) => (
                <tr key={group.groupId} className={`border-t ${theme.colors.surfaceBorder}`}>
                  <td className="px-6 py-3">{group.groupId}</td>
                  <td className="px-6 py-3 text-center">{group.members}</td>
                  <td className="px-6 py-3 text-center">
                    <span className={`px-3 py-1 rounded-full text-sm ${
                      group.state === 'Stable' ? 'bg-green-500/20 text-green-400' : 'bg-yellow-500/20 text-yellow-400'
                    }`}>
                      {group.state}
                    </span>
                  </td>
                  <td className="px-6 py-3 text-center">{group.lag}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Use Cases */}
      <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className={`${theme.colors.surface} p-6 rounded-xl border ${theme.colors.surfaceBorder}`}>
          <h3 className="font-semibold mb-2">Contract Events</h3>
          <p className={`text-sm ${theme.colors.textSecondary}`}>
            Stream contract lifecycle events to microservices for real-time processing
          </p>
        </div>

        <div className={`${theme.colors.surface} p-6 rounded-xl border ${theme.colors.surfaceBorder}`}>
          <h3 className="font-semibold mb-2">AI Analysis Queue</h3>
          <p className={`text-sm ${theme.colors.textSecondary}`}>
            Queue contracts for AI analysis using agentic workflows with LangGraph
          </p>
        </div>

        <div className={`${theme.colors.surface} p-6 rounded-xl border ${theme.colors.surfaceBorder}`}>
          <h3 className="font-semibold mb-2">Audit Trail</h3>
          <p className={`text-sm ${theme.colors.textSecondary}`}>
            Maintain immutable audit logs of all contract modifications
          </p>
        </div>
      </div>
    </div>
  );
};

export default KafkaDashboard;
