import React from 'react';
import { X, AlertCircle, ArrowUpCircle, Crown } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import useThemeStore from '../store/themeStore';

const UpgradePlanModal = ({ isOpen, onClose, limitData }) => {
  const navigate = useNavigate();
  const { theme } = useThemeStore();

  if (!isOpen) return null;

  const handleUpgrade = () => {
    onClose();
    navigate('/my-plan');
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className={`${theme.colors.surface} rounded-2xl shadow-2xl max-w-md w-full border-2 border-red-500/30 animate-fadeIn`}>
        {/* Header */}
        <div className="bg-gradient-to-r from-red-600 to-red-700 px-6 py-4 rounded-t-2xl flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="bg-white/20 p-2 rounded-lg">
              <AlertCircle className="h-6 w-6 text-white" />
            </div>
            <h2 className={`text-2xl font-black ${theme.colors.textPrimary}`}>Contract Limit Reached</h2>
          </div>
          <button
            onClick={onClose}
            className={`${theme.colors.textPrimary} opacity-80 hover:opacity-100 transition-opacity`}
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        {/* Content */}
        <div className="p-8">
          {/* Limit Info */}
          <div className={`${theme.colors.surfaceHover} rounded-xl p-6 mb-6 border ${theme.colors.surfaceBorder}`}>
            <div className="flex items-center justify-between mb-4">
              <div>
                <p className={`${theme.colors.textSecondary} text-sm font-semibold mb-1`}>Current Plan</p>
                <p className={`${theme.colors.textPrimary} text-xl font-bold flex items-center gap-2`}>
                  <Crown className="h-5 w-5 text-yellow-400" />
                  {limitData?.planName || 'Free Plan'}
                </p>
              </div>
              <div className="text-right">
                <p className={`${theme.colors.textSecondary} text-sm font-semibold mb-1`}>Contracts Uploaded</p>
                <p className="text-red-400 text-3xl font-black">
                  {limitData?.totalUploaded || 0} / {limitData?.limit || 0}
                </p>
              </div>
            </div>

            {/* Progress Bar */}
            <div className={`${theme.colors.surface} rounded-full h-3 overflow-hidden`}>
              <div
                className="h-full bg-gradient-to-r from-red-500 to-red-600 transition-all"
                style={{ width: '100%' }}
              ></div>
            </div>
          </div>

          {/* Message */}
          <div className="mb-6">
            <p className={`${theme.colors.textPrimary} text-base leading-relaxed`}>
              {limitData?.message || 'You have reached your contract upload limit.'}
            </p>
            <p className={`${theme.colors.primaryText} text-sm mt-3 font-semibold`}>
              {limitData?.suggestion || 'Upgrade your plan to upload more contracts.'}
            </p>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-3">
            <button
              onClick={onClose}
              className={`flex-1 px-6 py-3 ${theme.colors.surfaceHover} hover:opacity-80 ${theme.colors.textPrimary} font-bold rounded-xl transition-all duration-200 border ${theme.colors.surfaceBorder}`}
            >
              Cancel
            </button>
            <button
              onClick={handleUpgrade}
              className={`flex-1 px-6 py-3 ${theme.colors.primarySolid} hover:${theme.colors.primaryHover} ${theme.colors.textPrimary} font-bold rounded-xl transition-all duration-200 shadow-lg hover:shadow-xl flex items-center justify-center gap-2`}
            >
              <ArrowUpCircle className="h-5 w-5" />
              Upgrade Plan
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default UpgradePlanModal;
