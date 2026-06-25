import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Mail, Phone, Calendar, Shield, Clock, CheckCircle, Edit2, Loader } from 'lucide-react';
import useAuthStore from '../store/authStore';
import api from '../utils/api';

const UserProfile = () => {
  const navigate = useNavigate();
  const { user, setUser } = useAuthStore();

  // Edit mode state
  const [isEditing, setIsEditing] = useState(false);
  const [firstName, setFirstName] = useState(user?.firstName || '');
  const [lastName, setLastName] = useState(user?.lastName || '');
  const [updating, setUpdating] = useState(false);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  const getMemberSinceDate = () => {
    if (user?.createdAt) {
      return new Date(user.createdAt).toLocaleDateString('en-US', {
        month: 'short',
        year: 'numeric'
      });
    }
    return 'Unknown';
  };

  const getLastLoginDate = () => {
    if (user?.lastLogin) {
      const lastLoginDate = new Date(user.lastLogin);
      const today = new Date();
      const yesterday = new Date(today);
      yesterday.setDate(yesterday.getDate() - 1);

      if (lastLoginDate.toDateString() === today.toDateString()) {
        return 'Today';
      } else if (lastLoginDate.toDateString() === yesterday.toDateString()) {
        return 'Yesterday';
      } else {
        return lastLoginDate.toLocaleDateString('en-US', {
          month: 'short',
          day: 'numeric',
          year: 'numeric'
        });
      }
    }
    return 'Never';
  };

  const handleEditClick = () => {
    setIsEditing(true);
    setFirstName(user?.firstName || '');
    setLastName(user?.lastName || '');
    setError('');
    setSuccessMessage('');
  };

  const handleCancelEdit = () => {
    setIsEditing(false);
    setFirstName(user?.firstName || '');
    setLastName(user?.lastName || '');
    setError('');
    setSuccessMessage('');
  };

  const handleUpdateProfile = async () => {
    if (!firstName.trim() || !lastName.trim()) {
      setError('First name and last name are required');
      return;
    }

    try {
      setUpdating(true);
      setError('');
      setSuccessMessage('');

      const response = await api.put('/auth/update-profile', {
        firstName: firstName.trim(),
        lastName: lastName.trim()
      });

      // Update user in store
      setUser(response.data.user);
      setSuccessMessage('Profile updated successfully!');
      setIsEditing(false);

      // Clear success message after 3 seconds
      setTimeout(() => setSuccessMessage(''), 3000);
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to update profile');
      console.error('Update profile error:', err);
    } finally {
      setUpdating(false);
    }
  };

  const profileStats = [
    { label: 'Account Status', value: user?.isActive ? 'Active' : 'Inactive', icon: CheckCircle, color: user?.isActive ? 'green' : 'red' },
    { label: 'Member Since', value: getMemberSinceDate(), icon: Calendar, color: 'blue' },
    { label: 'Last Login', value: getLastLoginDate(), icon: Clock, color: 'purple' },
    { label: 'Account Type', value: user?.role || 'User', icon: Shield, color: 'yellow' },
  ];

  return (
    <div className="space-y-8">
      {/* Header with Back Button */}
      <div className="flex items-center gap-4">
        <button
          onClick={() => navigate('/dashboard')}
          className="p-2 hover:bg-slate-800 rounded-lg transition"
        >
          <ArrowLeft className="w-6 h-6 text-blue-400" />
        </button>
        <div>
          <h1 className="text-4xl font-bold text-white">User Profile</h1>
          <p className="text-slate-400">Manage your profile information and account settings</p>
        </div>
      </div>

        {/* Profile Header Card */}
        <div className="bg-gradient-to-r from-blue-600 to-blue-700 rounded-2xl p-8 shadow-xl">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-6">
              {/* Avatar */}
              <div className="h-24 w-24 rounded-full bg-white flex items-center justify-center shadow-lg">
                <span className="text-4xl font-bold text-blue-600">
                  {user?.firstName?.charAt(0)}{user?.lastName?.charAt(0)}
                </span>
              </div>
              {/* User Info */}
              <div>
                <h2 className="text-3xl font-bold text-white">
                  {user?.firstName} {user?.lastName}
                </h2>
                <p className="text-blue-100 text-lg mt-1">{user?.email}</p>
                <p className="text-blue-200 text-sm mt-2">Role: {user?.role}</p>
              </div>
            </div>
            <div className="text-right">
              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/20 backdrop-blur">
                <span className="h-3 w-3 rounded-full bg-green-400"></span>
                <span className="text-white font-semibold">Active</span>
              </div>
            </div>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {profileStats.map((stat, index) => {
            const Icon = stat.icon;
            const colorMap = {
              green: 'from-green-600 to-green-400',
              blue: 'from-blue-600 to-blue-400',
              purple: 'from-purple-600 to-purple-400',
              yellow: 'from-yellow-600 to-yellow-400'
            };

            return (
              <div key={index} className="bg-slate-900 rounded-xl border border-slate-800 p-6 hover:border-slate-700 transition">
                <div className={`inline-flex items-center justify-center w-12 h-12 rounded-lg bg-gradient-to-br ${colorMap[stat.color]} mb-4`}>
                  <Icon className="h-6 w-6 text-white" />
                </div>
                <p className="text-slate-400 text-sm mb-1">{stat.label}</p>
                <p className="text-2xl font-bold text-white">{stat.value}</p>
              </div>
            );
          })}
        </div>

        {/* Error and Success Messages */}
        {error && (
          <div className="bg-red-900/20 border border-red-800 rounded-lg p-4 flex items-center gap-3">
            <Mail className="w-5 h-5 text-red-400 flex-shrink-0" />
            <p className="text-red-200">{error}</p>
          </div>
        )}

        {successMessage && (
          <div className="bg-green-900/20 border border-green-800 rounded-lg p-4 flex items-center gap-3">
            <CheckCircle className="w-5 h-5 text-green-400 flex-shrink-0" />
            <p className="text-green-200">{successMessage}</p>
          </div>
        )}

        {/* Profile Information Sections */}
        <div className="grid grid-cols-1 gap-8">
          {/* Personal Information */}
          <div className="bg-slate-900 rounded-xl border border-slate-800 p-8">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-bold text-white">Personal Information</h3>
              {!isEditing && (
                <button
                  onClick={handleEditClick}
                  className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition"
                >
                  <Edit2 className="w-4 h-4" />
                  Edit
                </button>
              )}
            </div>
            <div className="space-y-6">
              <div>
                <label className="text-sm text-slate-400 block mb-2">First Name</label>
                {isEditing ? (
                  <input
                    type="text"
                    value={firstName}
                    onChange={(e) => setFirstName(e.target.value)}
                    className="w-full bg-slate-800 rounded-lg px-4 py-3 text-white border border-slate-700 focus:border-blue-500 focus:outline-none"
                    placeholder="Enter first name"
                  />
                ) : (
                  <div className="bg-slate-800 rounded-lg px-4 py-3 text-white border border-slate-700">
                    {user?.firstName}
                  </div>
                )}
              </div>
              <div>
                <label className="text-sm text-slate-400 block mb-2">Last Name</label>
                {isEditing ? (
                  <input
                    type="text"
                    value={lastName}
                    onChange={(e) => setLastName(e.target.value)}
                    className="w-full bg-slate-800 rounded-lg px-4 py-3 text-white border border-slate-700 focus:border-blue-500 focus:outline-none"
                    placeholder="Enter last name"
                  />
                ) : (
                  <div className="bg-slate-800 rounded-lg px-4 py-3 text-white border border-slate-700">
                    {user?.lastName}
                  </div>
                )}
              </div>
              <div>
                <label className="text-sm text-slate-400 block mb-2 flex items-center gap-2">
                  <Mail size={16} />
                  Email Address
                </label>
                <div className="bg-slate-800 rounded-lg px-4 py-3 text-white border border-slate-700 opacity-60">
                  {user?.email} <span className="text-slate-500 text-xs ml-2">(Cannot be changed)</span>
                </div>
              </div>
              <div>
                <label className="text-sm text-slate-400 block mb-2 flex items-center gap-2">
                  <Shield size={16} />
                  Account Role
                </label>
                <div className="bg-slate-800 rounded-lg px-4 py-3 text-white border border-slate-700 opacity-60">
                  {user?.role} <span className="text-slate-500 text-xs ml-2">(Cannot be changed)</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Activity Section */}
        <div className="bg-slate-900 rounded-xl border border-slate-800 p-8">
          <h3 className="text-xl font-bold text-white mb-6">Recent Activity</h3>
          <div className="space-y-4">
            <div className="flex items-center gap-4 pb-4 border-b border-slate-700">
              <div className="h-10 w-10 rounded-full bg-blue-600 flex items-center justify-center">
                <CheckCircle className="h-6 w-6 text-white" />
              </div>
              <div className="flex-1">
                <p className="text-white font-semibold">Logged in successfully</p>
                <p className="text-sm text-slate-400">Today at {new Date().toLocaleTimeString()}</p>
              </div>
            </div>
            <div className="flex items-center gap-4 pb-4 border-b border-slate-700">
              <div className="h-10 w-10 rounded-full bg-green-600 flex items-center justify-center">
                <CheckCircle className="h-6 w-6 text-white" />
              </div>
              <div className="flex-1">
                <p className="text-white font-semibold">Account created</p>
                <p className="text-sm text-slate-400">
                  {user?.createdAt
                    ? new Date(user.createdAt).toLocaleDateString('en-US', {
                        month: 'long',
                        day: 'numeric',
                        year: 'numeric'
                      })
                    : 'Unknown date'}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-4 justify-end">
          {isEditing ? (
            <>
              <button
                onClick={handleCancelEdit}
                disabled={updating}
                className="px-8 py-3 bg-slate-800 hover:bg-slate-700 disabled:bg-slate-700 disabled:cursor-not-allowed text-white rounded-lg font-semibold transition"
              >
                Cancel
              </button>
              <button
                onClick={handleUpdateProfile}
                disabled={updating}
                className="px-8 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-500 disabled:cursor-not-allowed text-white rounded-lg font-semibold transition shadow-lg flex items-center gap-2"
              >
                {updating ? (
                  <>
                    <Loader className="w-5 h-5 animate-spin" />
                    Updating...
                  </>
                ) : (
                  'Update Information'
                )}
              </button>
            </>
          ) : (
            <button
              onClick={() => navigate('/dashboard')}
              className="px-8 py-3 bg-slate-800 hover:bg-slate-700 text-white rounded-lg font-semibold transition"
            >
              Back to Dashboard
            </button>
          )}
        </div>
    </div>
  );
};

export default UserProfile;
