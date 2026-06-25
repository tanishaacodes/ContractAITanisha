import { useState, useEffect } from 'react';
import { Users, Plus, Edit, Trash2, UserCheck, UserX, Database, Activity } from 'lucide-react';
import useAuthStore from '../../store/authStore';
import useThemeStore from '../../store/themeStore';

const UserManagement = () => {
  const { theme } = useThemeStore();
  const { token } = useAuthStore();
  const [users, setUsers] = useState([]);
  const [roles, setRoles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [stats, setStats] = useState(null);

  const [newUser, setNewUser] = useState({
    email: '',
    password: '',
    firstName: '',
    lastName: '',
    roleId: '',
    fivetranAccess: false,
    kafkaAccess: false,
  });

  useEffect(() => {
    fetchUsers();
    fetchRoles();
    fetchStats();
  }, []);

  const fetchUsers = async () => {
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL||(import.meta.env.VITE_API_URL||'http://localhost:8002')}/api/superadmin/users/`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await response.json();
      setUsers(data.users || []);
    } catch (error) {
      console.error('Failed to fetch users:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchRoles = async () => {
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL||(import.meta.env.VITE_API_URL||'http://localhost:8002')}/api/superadmin/roles/`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await response.json();
      setRoles(data.roles || []);
    } catch (error) {
      console.error('Failed to fetch roles:', error);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL||(import.meta.env.VITE_API_URL||'http://localhost:8002')}/api/superadmin/stats/`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await response.json();
      setStats(data);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  };

  const handleCreateUser = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL||(import.meta.env.VITE_API_URL||'http://localhost:8002')}/api/superadmin/users/create/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(newUser),
      });

      if (response.ok) {
        alert('User created successfully!');
        setShowCreateModal(false);
        setNewUser({
          email: '',
          password: '',
          firstName: '',
          lastName: '',
          roleId: '',
          fivetranAccess: false,
          kafkaAccess: false,
        });
        fetchUsers();
        fetchStats();
      } else {
        const error = await response.json();
        alert(`Error: ${error.error || 'Failed to create user'}`);
      }
    } catch (error) {
      alert('Failed to create user');
      console.error(error);
    }
  };

  const handleToggleStatus = async (userId, currentStatus) => {
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL||(import.meta.env.VITE_API_URL||'http://localhost:8002')}/api/superadmin/users/${userId}/toggle-status/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ isActive: !currentStatus }),
      });

      if (response.ok) {
        fetchUsers();
        fetchStats();
      }
    } catch (error) {
      console.error('Failed to toggle status:', error);
    }
  };

  const handleDeleteUser = async (userId) => {
    if (!confirm('Are you sure you want to delete this user?')) return;

    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL||(import.meta.env.VITE_API_URL||'http://localhost:8002')}/api/superadmin/users/${userId}/delete/`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      });

      if (response.ok) {
        alert('User deleted successfully!');
        fetchUsers();
        fetchStats();
      } else {
        const error = await response.json();
        alert(`Error: ${error.error || 'Failed to delete user'}`);
      }
    } catch (error) {
      alert('Failed to delete user');
      console.error(error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-xl">Loading...</div>
      </div>
    );
  }

  return (
    <div className={`min-h-screen ${theme.colors.background} ${theme.colors.textPrimary} p-8`}>
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-4xl font-bold mb-2">User Management</h1>
        <p className={theme.colors.textSecondary}>Manage users and assign connector permissions</p>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className={`${theme.colors.surface} p-6 rounded-xl border ${theme.colors.surfaceBorder}`}>
            <div className="flex items-center justify-between">
              <div>
                <p className={`text-sm ${theme.colors.textSecondary}`}>Total Users</p>
                <p className="text-3xl font-bold mt-1">{stats.totalUsers}</p>
              </div>
              <Users className="text-blue-500" size={40} />
            </div>
          </div>

          <div className={`${theme.colors.surface} p-6 rounded-xl border ${theme.colors.surfaceBorder}`}>
            <div className="flex items-center justify-between">
              <div>
                <p className={`text-sm ${theme.colors.textSecondary}`}>Active Users</p>
                <p className="text-3xl font-bold mt-1 text-green-500">{stats.activeUsers}</p>
              </div>
              <UserCheck className="text-green-500" size={40} />
            </div>
          </div>

          <div className={`${theme.colors.surface} p-6 rounded-xl border ${theme.colors.surfaceBorder}`}>
            <div className="flex items-center justify-between">
              <div>
                <p className={`text-sm ${theme.colors.textSecondary}`}>Fivetran Users</p>
                <p className="text-3xl font-bold mt-1 text-purple-500">{stats.fivetranUsers}</p>
              </div>
              <Database className="text-purple-500" size={40} />
            </div>
          </div>

          <div className={`${theme.colors.surface} p-6 rounded-xl border ${theme.colors.surfaceBorder}`}>
            <div className="flex items-center justify-between">
              <div>
                <p className={`text-sm ${theme.colors.textSecondary}`}>Kafka Users</p>
                <p className="text-3xl font-bold mt-1 text-orange-500">{stats.kafkaUsers}</p>
              </div>
              <Activity className="text-orange-500" size={40} />
            </div>
          </div>
        </div>
      )}

      {/* Create User Button */}
      <div className="mb-6">
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-lg hover:from-blue-600 hover:to-blue-700 transition"
        >
          <Plus size={20} />
          Create New User
        </button>
      </div>

      {/* Users Table */}
      <div className={`${theme.colors.surface} rounded-xl border ${theme.colors.surfaceBorder} overflow-hidden`}>
        <table className="w-full">
          <thead className={`${theme.colors.surfaceHover}`}>
            <tr>
              <th className="px-6 py-4 text-left">Email</th>
              <th className="px-6 py-4 text-left">Name</th>
              <th className="px-6 py-4 text-left">Role</th>
              <th className="px-6 py-4 text-center">Fivetran</th>
              <th className="px-6 py-4 text-center">Kafka</th>
              <th className="px-6 py-4 text-center">Status</th>
              <th className="px-6 py-4 text-center">Actions</th>
            </tr>
          </thead>
          <tbody>
            {users.map((user) => (
              <tr key={user.id} className={`border-t ${theme.colors.surfaceBorder} hover:${theme.colors.surfaceHover}`}>
                <td className="px-6 py-4">{user.email}</td>
                <td className="px-6 py-4">{user.firstName} {user.lastName}</td>
                <td className="px-6 py-4">
                  <span className="px-3 py-1 bg-blue-500/20 text-blue-400 rounded-full text-sm">
                    {user.roleName}
                  </span>
                </td>
                <td className="px-6 py-4 text-center">
                  {user.fivetranAccess ? (
                    <span className="text-green-500">✓</span>
                  ) : (
                    <span className="text-gray-500">-</span>
                  )}
                </td>
                <td className="px-6 py-4 text-center">
                  {user.kafkaAccess ? (
                    <span className="text-green-500">✓</span>
                  ) : (
                    <span className="text-gray-500">-</span>
                  )}
                </td>
                <td className="px-6 py-4 text-center">
                  {user.isActive ? (
                    <span className="px-3 py-1 bg-green-500/20 text-green-400 rounded-full text-sm">
                      Active
                    </span>
                  ) : (
                    <span className="px-3 py-1 bg-red-500/20 text-red-400 rounded-full text-sm">
                      Inactive
                    </span>
                  )}
                </td>
                <td className="px-6 py-4">
                  <div className="flex items-center justify-center gap-2">
                    <button
                      onClick={() => handleToggleStatus(user.id, user.isActive)}
                      className="p-2 hover:bg-gray-700 rounded"
                      title={user.isActive ? 'Deactivate' : 'Activate'}
                    >
                      {user.isActive ? <UserX size={18} /> : <UserCheck size={18} />}
                    </button>
                    <button
                      onClick={() => handleDeleteUser(user.id)}
                      className="p-2 hover:bg-red-900/20 text-red-400 rounded"
                      title="Delete"
                    >
                      <Trash2 size={18} />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Create User Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className={`${theme.colors.surface} rounded-xl p-8 max-w-md w-full mx-4`}>
            <h2 className="text-2xl font-bold mb-6">Create New User</h2>
            <form onSubmit={handleCreateUser} className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Email</label>
                <input
                  type="email"
                  required
                  value={newUser.email}
                  onChange={(e) => setNewUser({ ...newUser, email: e.target.value })}
                  className={`w-full px-4 py-2 rounded-lg ${theme.colors.surfaceHover} border ${theme.colors.surfaceBorder}`}
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Password</label>
                <input
                  type="password"
                  required
                  value={newUser.password}
                  onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
                  className={`w-full px-4 py-2 rounded-lg ${theme.colors.surfaceHover} border ${theme.colors.surfaceBorder}`}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-2">First Name</label>
                  <input
                    type="text"
                    required
                    value={newUser.firstName}
                    onChange={(e) => setNewUser({ ...newUser, firstName: e.target.value })}
                    className={`w-full px-4 py-2 rounded-lg ${theme.colors.surfaceHover} border ${theme.colors.surfaceBorder}`}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Last Name</label>
                  <input
                    type="text"
                    required
                    value={newUser.lastName}
                    onChange={(e) => setNewUser({ ...newUser, lastName: e.target.value })}
                    className={`w-full px-4 py-2 rounded-lg ${theme.colors.surfaceHover} border ${theme.colors.surfaceBorder}`}
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Role</label>
                <select
                  required
                  value={newUser.roleId}
                  onChange={(e) => setNewUser({ ...newUser, roleId: e.target.value })}
                  className={`w-full px-4 py-2 rounded-lg ${theme.colors.surfaceHover} border ${theme.colors.surfaceBorder}`}
                >
                  <option value="">Select Role</option>
                  {roles.map((role) => (
                    <option key={role.id} value={role.id}>
                      {role.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="space-y-3">
                <label className="flex items-center gap-3">
                  <input
                    type="checkbox"
                    checked={newUser.fivetranAccess}
                    onChange={(e) => setNewUser({ ...newUser, fivetranAccess: e.target.checked })}
                    className="w-5 h-5"
                  />
                  <span className="flex items-center gap-2">
                    <Database size={18} className="text-purple-500" />
                    Grant Fivetran Access
                  </span>
                </label>

                <label className="flex items-center gap-3">
                  <input
                    type="checkbox"
                    checked={newUser.kafkaAccess}
                    onChange={(e) => setNewUser({ ...newUser, kafkaAccess: e.target.checked })}
                    className="w-5 h-5"
                  />
                  <span className="flex items-center gap-2">
                    <Activity size={18} className="text-orange-500" />
                    Grant Kafka Access
                  </span>
                </label>
              </div>

              <div className="flex gap-3 mt-6">
                <button
                  type="submit"
                  className="flex-1 px-6 py-3 bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-lg hover:from-blue-600 hover:to-blue-700 transition"
                >
                  Create User
                </button>
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className={`flex-1 px-6 py-3 ${theme.colors.surfaceHover} rounded-lg hover:${theme.colors.surface} transition`}
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default UserManagement;
