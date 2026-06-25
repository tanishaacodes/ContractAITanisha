import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../utils/api';
import { Users, Settings, Plus, Edit2, Trash2, Lock, AlertCircle, CheckCircle, ArrowLeft } from 'lucide-react';

const AdminDashboard = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('users'); // 'users' or 'roles'
  const [users, setUsers] = useState([]);
  const [roles, setRoles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [selectedUser, setSelectedUser] = useState(null);
  const [selectedRole, setSelectedRole] = useState(null);
  const [roleModalOpen, setRoleModalOpen] = useState(false);
  const [userModalOpen, setUserModalOpen] = useState(false);
  const [createRoleModalOpen, setCreateRoleModalOpen] = useState(false);
  const [formData, setFormData] = useState({ roleId: '', firstName: '', lastName: '', isActive: true });
  const [roleFormData, setRoleFormData] = useState({ name: '', description: '' });
  const defaultRoles = ['Admin', 'Adv. Legal Review', 'Proc Reviewer', 'Viewer'];

  // Fetch users and roles on mount
  useEffect(() => {
    fetchUsers();
    fetchRoles();
  }, []);

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const response = await api.get('/admin/users');
      setUsers(response.data.users);
      setError('');
    } catch (err) {
      setError('Failed to fetch users');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const fetchRoles = async () => {
    try {
      const response = await api.get('/admin/roles');
      setRoles(response.data.roles);
    } catch (err) {
      setError('Failed to fetch roles');
      console.error(err);
    }
  };

  const handleAssignRole = async (userId, roleId) => {
    try {
      // Find the role name from the roleId
      const selectedRole = roles.find(r => r.id === roleId);
      if (!selectedRole) {
        setError('Role not found');
        return;
      }

      await api.post(`/admin/users/${userId}/role`, { role: selectedRole.name });
      fetchUsers();
      setSuccess('User role updated successfully');
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to update role');
    }
  };

  const handleToggleStatus = async (userId) => {
    try {
      await api.post(`/admin/users/${userId}/toggle-status`);
      fetchUsers();
      setSuccess('User status updated');
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to update status');
    }
  };

  const handleDeleteUser = async (userId) => {
    if (window.confirm('Are you sure you want to delete this user?')) {
      try {
        await api.delete(`/admin/users/${userId}`);
        fetchUsers();
        setSuccess('User deleted successfully');
        setTimeout(() => setSuccess(''), 3000);
      } catch (err) {
        setError(err.response?.data?.message || 'Failed to delete user');
      }
    }
  };

  const handleUpdateUser = async (e) => {
    e.preventDefault();
    if (!selectedUser) return;

    try {
      await api.put(`/admin/users/${selectedUser.id}`, {
        firstName: formData.firstName,
        lastName: formData.lastName,
        isActive: formData.isActive,
      });
      fetchUsers();
      setUserModalOpen(false);
      setSelectedUser(null);
      setSuccess('User updated successfully');
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to update user');
    }
  };

  const openUserModal = (user) => {
    setSelectedUser(user);
    setFormData({
      firstName: user.firstName,
      lastName: user.lastName,
      isActive: user.isActive,
      roleId: user.role.id,
    });
    setUserModalOpen(true);
  };

  const handleCreateRole = async (e) => {
    e.preventDefault();
    if (!roleFormData.name.trim()) {
      setError('Role name is required');
      return;
    }

    try {
      await api.post('/admin/roles', {
        name: roleFormData.name,
        description: roleFormData.description,
        permissions: {},
      });
      fetchRoles();
      setCreateRoleModalOpen(false);
      setRoleFormData({ name: '', description: '' });
      setSuccess('Role created successfully');
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to create role');
    }
  };

  const handleUpdateRole = async (e) => {
    e.preventDefault();
    if (!selectedRole) return;

    try {
      await api.put(`/admin/roles/${selectedRole.id}`, {
        description: roleFormData.description,
        permissions: selectedRole.permissions,
      });
      fetchRoles();
      setRoleModalOpen(false);
      setSelectedRole(null);
      setRoleFormData({ name: '', description: '' });
      setSuccess('Role updated successfully');
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to update role');
    }
  };

  const handleDeleteRole = async (roleId) => {
    if (window.confirm('Are you sure you want to delete this role?')) {
      try {
        await api.delete(`/admin/roles/${roleId}`);
        fetchRoles();
        setSuccess('Role deleted successfully');
        setTimeout(() => setSuccess(''), 3000);
      } catch (err) {
        setError(err.response?.data?.message || 'Failed to delete role');
      }
    }
  };

  const openRoleModal = (role) => {
    setSelectedRole(role);
    setRoleFormData({
      name: role.name,
      description: role.description,
    });
    setRoleModalOpen(true);
  };

  return (
    <div className="space-y-8">
      {/* Back Button */}
      <button
        onClick={() => navigate(-1)}
        className="flex items-center gap-2 text-slate-400 hover:text-white transition"
      >
        <ArrowLeft size={20} />
        <span>Back</span>
      </button>

      {/* Header */}
      <div>
        <h1 className="text-4xl font-bold text-white mb-2">Admin Dashboard</h1>
        <p className="text-slate-400">Manage users, roles, and permissions</p>
      </div>

        {/* Error/Success Messages */}
        {error && (
          <div className="mb-6 p-4 bg-red-900/20 border border-red-800 rounded-lg flex items-center gap-3">
            <AlertCircle className="h-5 w-5 text-red-400 flex-shrink-0" />
            <p className="text-red-300 text-sm">{error}</p>
          </div>
        )}

        {success && (
          <div className="mb-6 p-4 bg-green-900/20 border border-green-800 rounded-lg flex items-center gap-3">
            <CheckCircle className="h-5 w-5 text-green-400 flex-shrink-0" />
            <p className="text-green-300 text-sm">{success}</p>
          </div>
        )}

        {/* Tabs */}
        <div className="flex gap-4">
          <button
            onClick={() => setActiveTab('users')}
            className={`flex items-center gap-2 px-6 py-3 rounded-xl font-medium transition ${
              activeTab === 'users'
                ? 'bg-blue-600 border border-blue-500 text-white shadow-lg'
                : 'bg-slate-800 border border-slate-700 text-slate-300 hover:bg-slate-700'
            }`}
          >
            <Users className="h-5 w-5" />
            Users Management
          </button>
          <button
            onClick={() => setActiveTab('roles')}
            className={`flex items-center gap-2 px-6 py-3 rounded-xl font-medium transition ${
              activeTab === 'roles'
                ? 'bg-blue-600 border border-blue-500 text-white shadow-lg'
                : 'bg-slate-800 border border-slate-700 text-slate-300 hover:bg-slate-700'
            }`}
          >
            <Settings className="h-5 w-5" />
            Roles Management
          </button>
        </div>

        {/* Users Tab */}
        {activeTab === 'users' && (
          <div className="bg-slate-900 rounded-xl border border-slate-800 overflow-hidden shadow-sm">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="border-b border-slate-700 bg-slate-800">
                  <tr>
                    <th className="px-6 py-4 text-left text-sm font-semibold text-white">Name</th>
                    <th className="px-6 py-4 text-left text-sm font-semibold text-white">Email</th>
                    <th className="px-6 py-4 text-left text-sm font-semibold text-white">Role</th>
                    <th className="px-6 py-4 text-left text-sm font-semibold text-white">Status</th>
                    <th className="px-6 py-4 text-left text-sm font-semibold text-white">Last Login</th>
                    <th className="px-6 py-4 text-left text-sm font-semibold text-white">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {loading ? (
                    <tr>
                      <td colSpan="6" className="px-6 py-8 text-center text-slate-400">
                        Loading users...
                      </td>
                    </tr>
                  ) : users.length === 0 ? (
                    <tr>
                      <td colSpan="6" className="px-6 py-8 text-center text-slate-400">
                        No users found
                      </td>
                    </tr>
                  ) : (
                    users.map((user) => (
                      <tr key={user.id} className="border-b border-slate-700 hover:bg-slate-800/50 transition">
                        <td className="px-6 py-4 text-white">
                          <span className="font-semibold">{user.firstName} {user.lastName}</span>
                        </td>
                        <td className="px-6 py-4 text-slate-300 text-sm">{user.email}</td>
                        <td className="px-6 py-4">
                          <select
                            value={user.role?.id || ''}
                            onChange={(e) => handleAssignRole(user.id, e.target.value)}
                            className="px-3 py-1.5 bg-slate-800 border border-slate-600 rounded text-sm text-white focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                          >
                            {roles.map((role) => (
                              <option key={role.id} value={role.id}>
                                {role.name}
                              </option>
                            ))}
                          </select>
                        </td>
                        <td className="px-6 py-4">
                          <span
                            className={`px-3 py-1 rounded-full text-xs font-semibold ${
                              user.isActive
                                ? 'bg-green-900/30 text-green-400'
                                : 'bg-red-900/30 text-red-400'
                            }`}
                          >
                            {user.isActive ? 'Active' : 'Inactive'}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-slate-300 text-sm">
                          {user.lastLogin
                            ? new Date(user.lastLogin).toLocaleDateString()
                            : 'Never'}
                        </td>
                        <td className="px-6 py-4">
                          <div className="flex gap-2">
                            <button
                              onClick={() => openUserModal(user)}
                              className="p-2 hover:bg-blue-900/30 rounded transition text-blue-400"
                              title="Edit user"
                            >
                              <Edit2 className="h-4 w-4" />
                            </button>
                            <button
                              onClick={() => handleToggleStatus(user.id)}
                              className="p-2 hover:bg-amber-900/30 rounded transition text-amber-400"
                              title={user.isActive ? 'Deactivate user' : 'Activate user'}
                            >
                              <Lock className="h-4 w-4" />
                            </button>
                            <button
                              onClick={() => handleDeleteUser(user.id)}
                              className="p-2 hover:bg-red-900/30 rounded transition text-red-400"
                              title="Delete user"
                            >
                              <Trash2 className="h-4 w-4" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Roles Tab */}
        {activeTab === 'roles' && (
          <div>
            <div className="mb-6 flex justify-between items-center">
              <h2 className="text-xl font-semibold text-white">Manage Roles</h2>
              <button
                onClick={() => {
                  setCreateRoleModalOpen(true);
                  setRoleFormData({ name: '', description: '' });
                }}
                className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-xl font-medium transition shadow-md"
              >
                <Plus className="h-4 w-4" />
                Create Role
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {roles.map((role) => (
                <div
                  key={role.id}
                  className="bg-slate-900 rounded-xl border border-slate-800 p-6 hover:border-slate-700 transition"
                >
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex-1">
                      <h3 className="text-lg font-bold text-white">{role.name}</h3>
                      <p className="text-slate-400 text-sm mt-1">{role.description || 'No description'}</p>
                    </div>
                    <div className="flex gap-2 ml-4">
                      <button
                        onClick={() => openRoleModal(role)}
                        className="p-2 hover:bg-blue-900/30 rounded transition text-blue-400"
                        title="Edit role"
                      >
                        <Edit2 className="h-4 w-4" />
                      </button>
                      {!defaultRoles.includes(role.name) && (
                        <button
                          onClick={() => handleDeleteRole(role.id)}
                          className="p-2 hover:bg-red-900/30 rounded transition text-red-400"
                          title="Delete role"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      )}
                    </div>
                  </div>
                  <div className="pt-4 border-t border-slate-700">
                    <p className="text-xs text-slate-400 font-semibold mb-2">PERMISSIONS:</p>
                    <div className="space-y-1">
                      {Object.entries(role.permissions).length > 0 ? (
                        Object.entries(role.permissions).map(([key, value]) => (
                          <p key={key} className="text-xs text-slate-400">
                            • {key}: {Array.isArray(value) ? value.join(', ') : 'configured'}
                          </p>
                        ))
                      ) : (
                        <p className="text-xs text-slate-400">No permissions configured</p>
                      )}
                    </div>
                  </div>
                  {defaultRoles.includes(role.name) && (
                    <div className="mt-3 pt-3 border-t border-slate-700">
                      <span className="text-xs bg-blue-900/30 text-blue-400 px-2 py-1 rounded">
                        Default Role
                      </span>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

      {/* User Edit Modal */}
      {userModalOpen && selectedUser && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-slate-900 rounded-xl border border-slate-800 max-w-md w-full p-6 shadow-lg">
            <h2 className="text-xl font-bold text-white mb-4">Edit User</h2>
            <form onSubmit={handleUpdateUser} className="space-y-4">
              <div>
                <label className="block text-sm font-semibold text-white mb-2">First Name</label>
                <input
                  type="text"
                  value={formData.firstName}
                  onChange={(e) => setFormData({ ...formData, firstName: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-semibold text-white mb-2">Last Name</label>
                <input
                  type="text"
                  value={formData.lastName}
                  onChange={(e) => setFormData({ ...formData, lastName: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="flex items-center gap-2 text-white cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.isActive}
                    onChange={(e) => setFormData({ ...formData, isActive: e.target.checked })}
                    className="w-4 h-4 rounded border-slate-600"
                  />
                  <span className="text-sm font-medium">Active</span>
                </label>
              </div>
              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => {
                    setUserModalOpen(false);
                    setSelectedUser(null);
                  }}
                  className="flex-1 px-4 py-2 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-lg text-white font-medium transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-xl text-white font-medium transition shadow-md"
                >
                  Update User
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Create Role Modal */}
      {createRoleModalOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-slate-900 rounded-xl border border-slate-800 max-w-md w-full p-6 shadow-lg">
            <h2 className="text-xl font-bold text-white mb-4">Create New Role</h2>
            <form onSubmit={handleCreateRole} className="space-y-4">
              <div>
                <label className="block text-sm font-semibold text-white mb-2">Role Name</label>
                <input
                  type="text"
                  placeholder="e.g., Content Manager"
                  value={roleFormData.name}
                  onChange={(e) => setRoleFormData({ ...roleFormData, name: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-semibold text-white mb-2">Description</label>
                <textarea
                  placeholder="Describe the purpose of this role"
                  value={roleFormData.description}
                  onChange={(e) => setRoleFormData({ ...roleFormData, description: e.target.value })}
                  rows="3"
                  className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                />
              </div>
              <div className="bg-blue-900/30 border border-blue-800 rounded-lg p-3">
                <p className="text-xs text-blue-300">
                  <strong>ℹ️ Note:</strong> Default roles (Admin, Adv. Legal Review, Proc Reviewer, Viewer) cannot be deleted.
                </p>
              </div>
              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => {
                    setCreateRoleModalOpen(false);
                    setRoleFormData({ name: '', description: '' });
                  }}
                  className="flex-1 px-4 py-2 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-lg text-white font-medium transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-xl text-white font-medium transition shadow-md"
                >
                  Create Role
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Role Modal */}
      {roleModalOpen && selectedRole && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-slate-900 rounded-xl border border-slate-800 max-w-md w-full p-6 shadow-lg">
            <h2 className="text-xl font-bold text-white mb-4">Edit Role</h2>
            <form onSubmit={handleUpdateRole} className="space-y-4">
              <div>
                <label className="block text-sm font-semibold text-white mb-2">Role Name</label>
                <input
                  type="text"
                  value={roleFormData.name}
                  disabled={defaultRoles.includes(selectedRole.name)}
                  className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed"
                />
                {defaultRoles.includes(selectedRole.name) && (
                  <p className="text-xs text-slate-400 mt-1">Cannot modify default role name</p>
                )}
              </div>
              <div>
                <label className="block text-sm font-semibold text-white mb-2">Description</label>
                <textarea
                  value={roleFormData.description}
                  onChange={(e) => setRoleFormData({ ...roleFormData, description: e.target.value })}
                  rows="3"
                  className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                />
              </div>
              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => {
                    setRoleModalOpen(false);
                    setSelectedRole(null);
                    setRoleFormData({ name: '', description: '' });
                  }}
                  className="flex-1 px-4 py-2 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-lg text-white font-medium transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-xl text-white font-medium transition shadow-md"
                >
                  Update Role
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminDashboard;
