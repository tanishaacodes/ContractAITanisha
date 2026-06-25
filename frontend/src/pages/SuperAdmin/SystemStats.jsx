import { useState, useEffect } from 'react';
import { Users, UserCheck, Database, Activity, BarChart3 } from 'lucide-react';
import useAuthStore from '../../store/authStore';
import useThemeStore from '../../store/themeStore';

const SystemStats = () => {
  const { theme } = useThemeStore();
  const { token } = useAuthStore();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL||(import.meta.env.VITE_API_URL||'http://localhost:8002')}/api/superadmin/stats/`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await response.json();
      setStats(data);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-xl">Loading Statistics...</div>
      </div>
    );
  }

  return (
    <div className={`min-h-screen ${theme.colors.background} ${theme.colors.textPrimary} p-8`}>
      <div className="mb-8">
        <h1 className="text-4xl font-bold mb-2">System Statistics</h1>
        <p className={theme.colors.textSecondary}>Overview of users and connector access</p>
      </div>

      {stats && (
        <>
          {/* Main Stats */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <div className={`${theme.colors.surface} p-6 rounded-xl border ${theme.colors.surfaceBorder}`}>
              <div className="flex items-center justify-between">
                <div>
                  <p className={`text-sm ${theme.colors.textSecondary}`}>Total Users</p>
                  <p className="text-4xl font-bold mt-2">{stats.totalUsers}</p>
                </div>
                <Users className="text-blue-500" size={48} />
              </div>
            </div>

            <div className={`${theme.colors.surface} p-6 rounded-xl border ${theme.colors.surfaceBorder}`}>
              <div className="flex items-center justify-between">
                <div>
                  <p className={`text-sm ${theme.colors.textSecondary}`}>Active Users</p>
                  <p className="text-4xl font-bold mt-2 text-green-500">{stats.activeUsers}</p>
                </div>
                <UserCheck className="text-green-500" size={48} />
              </div>
            </div>

            <div className={`${theme.colors.surface} p-6 rounded-xl border ${theme.colors.surfaceBorder}`}>
              <div className="flex items-center justify-between">
                <div>
                  <p className={`text-sm ${theme.colors.textSecondary}`}>Fivetran Users</p>
                  <p className="text-4xl font-bold mt-2 text-purple-500">{stats.fivetranUsers}</p>
                </div>
                <Database className="text-purple-500" size={48} />
              </div>
            </div>

            <div className={`${theme.colors.surface} p-6 rounded-xl border ${theme.colors.surfaceBorder}`}>
              <div className="flex items-center justify-between">
                <div>
                  <p className={`text-sm ${theme.colors.textSecondary}`}>Kafka Users</p>
                  <p className="text-4xl font-bold mt-2 text-orange-500">{stats.kafkaUsers}</p>
                </div>
                <Activity className="text-orange-500" size={48} />
              </div>
            </div>
          </div>

          {/* Users by Role */}
          <div className={`${theme.colors.surface} p-6 rounded-xl border ${theme.colors.surfaceBorder}`}>
            <h2 className="text-2xl font-bold mb-6">Users by Role</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
              {Object.entries(stats.usersByRole || {}).map(([role, count]) => (
                <div key={role} className={`p-4 ${theme.colors.surfaceHover} rounded-lg`}>
                  <p className={`text-sm ${theme.colors.textSecondary} mb-1`}>{role}</p>
                  <p className="text-3xl font-bold">{count}</p>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default SystemStats;
