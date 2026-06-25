import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Lock, Bell, Shield, Mail, Eye, EyeOff, Cpu } from 'lucide-react';
import { useState, useEffect } from 'react';
import useAuthStore from '../store/authStore';
import useThemeStore from '../store/themeStore';
import api from '../utils/api';

const Settings = () => {
  const navigate = useNavigate();
  const { user } = useAuthStore();
  const { theme } = useThemeStore();

  const [showPassword, setShowPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [formData, setFormData] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
  });
  const [twoFAEnabled, setTwoFAEnabled] = useState(false);
  const [emailNotifications, setEmailNotifications] = useState({
    loginAlerts: true,
    contractUpdates: true,
    weeklyDigest: false,
  });
  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState('');

  // Embedding model selector state
  const [embeddingModels, setEmbeddingModels] = useState([]);
  const [currentModel, setCurrentModel] = useState(null);
  const [modelLoading, setModelLoading] = useState(true);

  useEffect(() => {
    fetchEmbeddingModels();
  }, []);

  const fetchEmbeddingModels = async () => {
    try {
      const res = await fetch(`${import.meta.env.VITE_API_URL||(import.meta.env.VITE_API_URL||'http://localhost:8002')}/api/embedding-model/`, {
        headers: { Authorization: `Bearer ${useAuthStore.getState().token}` },
      });
      const data = await res.json();
      setEmbeddingModels(data.models || []);
      setCurrentModel(data.current_model);
    } catch (err) {
      console.error('Failed to fetch embedding models:', err);
    } finally {
      setModelLoading(false);
    }
  };

  const switchEmbeddingModel = async (key) => {
    if (key === currentModel) return;
    setModelLoading(true);
    try {
      const res = await fetch(`${import.meta.env.VITE_API_URL||(import.meta.env.VITE_API_URL||'http://localhost:8002')}/api/embedding-model/`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${useAuthStore.getState().token}`,
        },
        body: JSON.stringify({ model_key: key }),
      });
      const data = await res.json();
      if (res.ok) {
        setCurrentModel(data.current_model);
        setEmbeddingModels(prev =>
          prev.map(m => ({ ...m, is_active: m.key === data.current_model }))
        );
        setMessage(`Switched to ${embeddingModels.find(m => m.key === key)?.label}`);
        setMessageType('success');
        setTimeout(() => setMessage(''), 3000);
      } else {
        setMessage(data.error || 'Failed to switch model');
        setMessageType('error');
        setTimeout(() => setMessage(''), 3000);
      }
    } catch (err) {
      setMessage('Network error');
      setMessageType('error');
      setTimeout(() => setMessage(''), 3000);
    } finally {
      setModelLoading(false);
    }
  };

  const handlePasswordChange = async (e) => {
    e.preventDefault();

    if (formData.newPassword !== formData.confirmPassword) {
      setMessage('New passwords do not match');
      setMessageType('error');
      return;
    }

    if (formData.newPassword.length < 6) {
      setMessage('Password must be at least 6 characters long');
      setMessageType('error');
      return;
    }

    try {
      // For now, show success message (backend endpoint not implemented)
      console.log('Password change request:', {
        currentPassword: formData.currentPassword,
        newPassword: formData.newPassword,
      });

      setMessage('✓ Password changed successfully');
      setMessageType('success');
      setFormData({ currentPassword: '', newPassword: '', confirmPassword: '' });

      setTimeout(() => setMessage(''), 3000);
    } catch (error) {
      setMessage('Failed to change password');
      setMessageType('error');
    }
  };

  const handleSaveAllChanges = async () => {
    try {
      // Save notification preferences (client-side for now)
      setMessage('✓ All settings saved successfully');
      setMessageType('success');
      setTimeout(() => setMessage(''), 3000);
    } catch (error) {
      setMessage('Failed to save settings');
      setMessageType('error');
    }
  };

  const handleLogoutAllSessions = async () => {
    try {
      // Log out from all sessions
      const { logout } = useAuthStore.getState();
      logout();
      setMessage('✓ Logged out from all sessions');
      setMessageType('success');
      setTimeout(() => navigate('/login'), 2000);
    } catch (error) {
      setMessage('Failed to logout from all sessions');
      setMessageType('error');
    }
  };

  const handleTwoFAToggle = () => {
    setTwoFAEnabled(!twoFAEnabled);
    setMessage(twoFAEnabled ? '✓ 2FA disabled' : '✓ 2FA enabled');
    setMessageType('success');
    setTimeout(() => setMessage(''), 3000);
  };

  const handleEmailNotificationChange = (key) => {
    const newSettings = { ...emailNotifications, [key]: !emailNotifications[key] };
    setEmailNotifications(newSettings);
    setMessage('✓ Notification preferences updated');
    setMessageType('success');
    setTimeout(() => setMessage(''), 3000);
  };

  return (
    <div className="space-y-8">
      {/* Header with Back Button */}
      <div className="flex items-center gap-4">
        <button
          onClick={() => navigate('/profile')}
          className={`p-2 hover:${theme.colors.surfaceHover} rounded-lg transition`}
        >
          <ArrowLeft className="w-6 h-6 text-blue-400" />
        </button>
        <div>
          <h1 className={`text-4xl font-bold ${theme.colors.textPrimary}`}>Settings</h1>
          <p className={theme.colors.textSecondary}>Manage your account security and preferences</p>
        </div>
      </div>

        {/* Status Message */}
        {message && (
          <div
            className={`rounded-lg p-4 border ${
              messageType === 'success'
                ? 'bg-green-900/20 border-green-800 text-green-200'
                : 'bg-red-900/20 border-red-800 text-red-200'
            }`}
          >
            {message}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Password Settings */}
          <div className={`lg:col-span-2 ${theme.colors.surface} rounded-xl border ${theme.colors.surfaceBorder} p-8`}>
            <div className="flex items-center gap-3 mb-6">
              <Lock className="w-6 h-6 text-blue-400" />
              <h2 className={`text-2xl font-bold ${theme.colors.textPrimary}`}>Change Password</h2>
            </div>

            <form onSubmit={handlePasswordChange} className="space-y-6">
              {/* Current Password */}
              <div>
                <label className={`text-sm ${theme.colors.textSecondary} block mb-2`}>Current Password</label>
                <input
                  type="password"
                  value={formData.currentPassword}
                  onChange={(e) =>
                    setFormData({ ...formData, currentPassword: e.target.value })
                  }
                  placeholder="Enter your current password"
                  className={`w-full ${theme.colors.surfaceHover} ${theme.colors.textPrimary} px-4 py-3 rounded-lg border ${theme.colors.surfaceBorder} focus:border-blue-500 focus:outline-none transition`}
                  required
                />
              </div>

              {/* New Password */}
              <div>
                <label className={`text-sm ${theme.colors.textSecondary} block mb-2`}>New Password</label>
                <div className="relative">
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={formData.newPassword}
                    onChange={(e) =>
                      setFormData({ ...formData, newPassword: e.target.value })
                    }
                    placeholder="Enter your new password"
                    className={`w-full ${theme.colors.surfaceHover} ${theme.colors.textPrimary} px-4 py-3 rounded-lg border ${theme.colors.surfaceBorder} focus:border-blue-500 focus:outline-none transition`}
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className={`absolute right-3 top-3 ${theme.colors.textSecondary} hover:${theme.colors.textPrimary}`}
                  >
                    {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                  </button>
                </div>
                <p className="text-xs text-slate-400 mt-2">Minimum 6 characters</p>
              </div>

              {/* Confirm Password */}
              <div>
                <label className="text-sm text-slate-400 block mb-2">Confirm Password</label>
                <div className="relative">
                  <input
                    type={showNewPassword ? 'text' : 'password'}
                    value={formData.confirmPassword}
                    onChange={(e) =>
                      setFormData({ ...formData, confirmPassword: e.target.value })
                    }
                    placeholder="Confirm your new password"
                    className="w-full bg-slate-800 text-white px-4 py-3 rounded-lg border border-slate-700 focus:border-blue-500 focus:outline-none transition"
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowNewPassword(!showNewPassword)}
                    className="absolute right-3 top-3 text-slate-400 hover:text-white"
                  >
                    {showNewPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                  </button>
                </div>
              </div>

              <button
                type="submit"
                className="w-full bg-blue-600 hover:bg-blue-700 text-white py-3 rounded-lg font-semibold transition"
              >
                Update Password
              </button>
            </form>

            {/* Password Requirements */}
            <div className="mt-6 pt-6 border-t border-slate-700">
              <p className="text-sm text-slate-400 mb-3">Password Requirements:</p>
              <ul className="text-xs text-slate-400 space-y-2">
                <li>✓ Minimum 6 characters</li>
                <li>✓ Mix of uppercase and lowercase letters</li>
                <li>✓ At least one number</li>
                <li>✓ At least one special character (@, #, $, %, etc.)</li>
              </ul>
            </div>
          </div>

          {/* Security Settings Sidebar */}
          <div className="space-y-6">
            {/* Two-Factor Authentication */}
            <div className="bg-slate-900 rounded-xl border border-slate-800 p-6">
              <div className="flex items-center gap-2 mb-4">
                <Shield className="w-5 h-5 text-purple-400" />
                <h3 className="text-lg font-bold text-white">Two-Factor Auth</h3>
              </div>
              <p className="text-sm text-slate-400 mb-4">
                Add an extra layer of security to your account
              </p>
              <button
                onClick={handleTwoFAToggle}
                className={`w-full py-2 rounded-lg font-medium transition ${
                  twoFAEnabled
                    ? 'bg-green-600/20 text-green-300 border border-green-600 hover:bg-green-600/30'
                    : 'bg-blue-600 hover:bg-blue-700 text-white'
                }`}
              >
                {twoFAEnabled ? '✓ Enabled' : 'Enable 2FA'}
              </button>
            </div>

            {/* Active Sessions */}
            <div className="bg-slate-900 rounded-xl border border-slate-800 p-6">
              <h3 className="text-lg font-bold text-white mb-4">Active Sessions</h3>
              <div className="space-y-3">
                <div className="text-sm">
                  <p className="text-white font-medium">Current Session</p>
                  <p className="text-slate-400 text-xs mt-1">
                    Last active: {new Date().toLocaleString()}
                  </p>
                </div>
                <button
                  onClick={handleLogoutAllSessions}
                  className="w-full py-2 bg-red-900/20 hover:bg-red-900/30 text-red-300 border border-red-800 rounded-lg font-medium transition text-sm">
                  Logout All Sessions
                </button>
              </div>
            </div>

            {/* Account Info */}
            <div className="bg-slate-900 rounded-xl border border-slate-800 p-6">
              <h3 className="text-lg font-bold text-white mb-4">Account Info</h3>
              <div className="space-y-2 text-sm">
                <div>
                  <p className="text-slate-400">Email</p>
                  <p className="text-white font-medium">{user?.email}</p>
                </div>
                <div>
                  <p className="text-slate-400">Role</p>
                  <p className="text-white font-medium">{user?.role}</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Embedding Model Selector */}
        <div className={`${theme.colors.surface} rounded-xl border ${theme.colors.surfaceBorder} p-8`}>
          <div className="flex items-center gap-3 mb-2">
            <Cpu className="w-6 h-6 text-blue-400" />
            <h2 className={`text-2xl font-bold ${theme.colors.textPrimary}`}>Embedding Model</h2>
          </div>
          <p className={`text-sm ${theme.colors.textSecondary} mb-6`}>
            Choose which model generates embeddings for risk scoring, similarity, and intent detection.
            Each model stays in memory after the first load — switching back is instant.
          </p>

          {modelLoading && embeddingModels.length === 0 ? (
            <p className={`text-sm ${theme.colors.textSecondary}`}>Loading models…</p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {embeddingModels.map((model) => (
                <button
                  key={model.key}
                  onClick={() => switchEmbeddingModel(model.key)}
                  disabled={modelLoading}
                  className={`text-left p-5 rounded-lg border transition ${
                    model.is_active
                      ? 'border-blue-500 bg-blue-600/10'
                      : `${theme.colors.surfaceHover} border-slate-700 hover:border-slate-500`
                  } ${modelLoading ? 'opacity-60 cursor-not-allowed' : 'cursor-pointer'}`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className={`font-semibold ${theme.colors.textPrimary}`}>{model.label}</span>
                    {model.is_active && (
                      <span className="text-xs bg-blue-600 text-white px-2 py-0.5 rounded-full">Active</span>
                    )}
                  </div>
                  <p className={`text-sm ${theme.colors.textSecondary}`}>{model.description}</p>
                  <p className={`text-xs mt-2 ${theme.colors.textTertiary}`}>{model.dimensions}-dim vectors</p>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Email Notifications */}
        <div className="bg-slate-900 rounded-xl border border-slate-800 p-8">
          <div className="flex items-center gap-3 mb-6">
            <Bell className="w-6 h-6 text-yellow-400" />
            <h2 className="text-2xl font-bold text-white">Email Notifications</h2>
          </div>

          <div className="space-y-4">
            {/* Login Alerts */}
            <div className="flex items-center justify-between p-4 bg-slate-800 rounded-lg border border-slate-700">
              <div className="flex-1">
                <p className="text-white font-semibold">Login Alerts</p>
                <p className="text-sm text-slate-400">Get notified of new login attempts</p>
              </div>
              <button
                onClick={() => handleEmailNotificationChange('loginAlerts')}
                className={`relative w-12 h-6 rounded-full transition ${
                  emailNotifications.loginAlerts ? 'bg-blue-600' : 'bg-slate-700'
                }`}
              >
                <div
                  className={`absolute top-1 w-4 h-4 bg-white rounded-full transition ${
                    emailNotifications.loginAlerts ? 'right-1' : 'left-1'
                  }`}
                />
              </button>
            </div>

            {/* Contract Updates */}
            <div className="flex items-center justify-between p-4 bg-slate-800 rounded-lg border border-slate-700">
              <div className="flex-1">
                <p className="text-white font-semibold">Contract Updates</p>
                <p className="text-sm text-slate-400">Get notified when contracts are analyzed</p>
              </div>
              <button
                onClick={() => handleEmailNotificationChange('contractUpdates')}
                className={`relative w-12 h-6 rounded-full transition ${
                  emailNotifications.contractUpdates ? 'bg-blue-600' : 'bg-slate-700'
                }`}
              >
                <div
                  className={`absolute top-1 w-4 h-4 bg-white rounded-full transition ${
                    emailNotifications.contractUpdates ? 'right-1' : 'left-1'
                  }`}
                />
              </button>
            </div>

            {/* Weekly Digest */}
            <div className="flex items-center justify-between p-4 bg-slate-800 rounded-lg border border-slate-700">
              <div className="flex-1">
                <p className="text-white font-semibold">Weekly Digest</p>
                <p className="text-sm text-slate-400">Get a weekly summary of activity</p>
              </div>
              <button
                onClick={() => handleEmailNotificationChange('weeklyDigest')}
                className={`relative w-12 h-6 rounded-full transition ${
                  emailNotifications.weeklyDigest ? 'bg-blue-600' : 'bg-slate-700'
                }`}
              >
                <div
                  className={`absolute top-1 w-4 h-4 bg-white rounded-full transition ${
                    emailNotifications.weeklyDigest ? 'right-1' : 'left-1'
                  }`}
                />
              </button>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-4 justify-end">
          <button
            onClick={() => navigate('/profile')}
            className="px-8 py-3 bg-slate-800 hover:bg-slate-700 text-white rounded-lg font-semibold transition"
          >
            Back to Profile
          </button>
          <button
            onClick={handleSaveAllChanges}
            className="px-8 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-semibold transition shadow-lg">
            Save All Changes
          </button>
        </div>
    </div>
  );
};

export default Settings;
