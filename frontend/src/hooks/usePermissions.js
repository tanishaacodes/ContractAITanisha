import { useMemo } from 'react';
import useAuthStore from '../store/authStore';

/**
 * User Roles
 */
export const UserRole = {
  ADMIN: 'admin',
  EXECUTIVE: 'executive',
  ANALYST: 'analyst',
  VIEWER: 'viewer',
};

/**
 * Permission Matrix - Frontend version matching backend
 */
const PERMISSIONS = {
  [UserRole.ADMIN]: {
    viewPrimeDashboard: true,
    useAIFeatures: true,
    viewProfitability: true,
    runSimulations: true,
    exportReports: true,
    manageContracts: true,
    viewAnalytics: true,
    configureSystem: true,
  },
  [UserRole.EXECUTIVE]: {
    viewPrimeDashboard: true,
    useAIFeatures: true,
    viewProfitability: true,
    runSimulations: true,
    exportReports: true,
    manageContracts: false,
    viewAnalytics: true,
    configureSystem: false,
  },
  [UserRole.ANALYST]: {
    viewPrimeDashboard: true,
    useAIFeatures: true,
    viewProfitability: true,
    runSimulations: true,
    exportReports: true,
    manageContracts: true,
    viewAnalytics: true,
    configureSystem: false,
  },
  [UserRole.VIEWER]: {
    viewPrimeDashboard: true,
    useAIFeatures: false,
    viewProfitability: false,
    runSimulations: false,
    exportReports: false,
    manageContracts: false,
    viewAnalytics: true,
    configureSystem: false,
  },
};

/**
 * Hook for permission checks
 */
export function usePermissions() {
  const { user } = useAuthStore();

  const userRole = useMemo(() => {
    return user?.role || UserRole.VIEWER;
  }, [user]);

  const permissions = useMemo(() => {
    return PERMISSIONS[userRole] || PERMISSIONS[UserRole.VIEWER];
  }, [userRole]);

  const hasPermission = (permissionName) => {
    if (user?.is_superuser) return true;
    return permissions[permissionName] || false;
  };

  const hasAnyPermission = (...permissionNames) => {
    return permissionNames.some(name => hasPermission(name));
  };

  const hasAllPermissions = (...permissionNames) => {
    return permissionNames.every(name => hasPermission(name));
  };

  const canAccessPrimeDashboard = () => hasPermission('viewPrimeDashboard');
  const canUseAIFeatures = () => hasPermission('useAIFeatures');
  const canExportReports = () => hasPermission('exportReports');
  const canManageContracts = () => hasPermission('manageContracts');
  const canRunSimulations = () => hasPermission('runSimulations');
  const canViewProfitability = () => hasPermission('viewProfitability');

  return {
    userRole,
    permissions,
    hasPermission,
    hasAnyPermission,
    hasAllPermissions,
    canAccessPrimeDashboard,
    canUseAIFeatures,
    canExportReports,
    canManageContracts,
    canRunSimulations,
    canViewProfitability,
  };
}

/**
 * Role Badge Component Helper
 */
export function getRoleBadgeColor(role) {
  switch (role) {
    case UserRole.ADMIN:
      return 'bg-red-500/20 text-red-400 border-red-500/30';
    case UserRole.EXECUTIVE:
      return 'bg-purple-500/20 text-purple-400 border-purple-500/30';
    case UserRole.ANALYST:
      return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
    case UserRole.VIEWER:
      return 'bg-gray-500/20 text-gray-400 border-gray-500/30';
    default:
      return 'bg-gray-500/20 text-gray-400 border-gray-500/30';
  }
}

/**
 * Role Display Name
 */
export function getRoleDisplayName(role) {
  const names = {
    [UserRole.ADMIN]: 'Administrator',
    [UserRole.EXECUTIVE]: 'Executive',
    [UserRole.ANALYST]: 'Analyst',
    [UserRole.VIEWER]: 'Viewer',
  };
  return names[role] || 'Unknown';
}

export default usePermissions;
