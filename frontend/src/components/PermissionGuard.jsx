import { usePermissions } from '../hooks/usePermissions';
import { Lock } from 'lucide-react';

/**
 * PermissionGuard - Conditionally render children based on permissions
 *
 * Usage:
 * <PermissionGuard permission="useAIFeatures">
 *   <AIComponent />
 * </PermissionGuard>
 *
 * <PermissionGuard anyOf={['exportReports', 'viewProfitability']}>
 *   <ExportButton />
 * </PermissionGuard>
 */
export function PermissionGuard({
  children,
  permission,
  anyOf,
  allOf,
  fallback = null,
  showLocked = false
}) {
  const { hasPermission, hasAnyPermission, hasAllPermissions } = usePermissions();

  let hasAccess = true;

  if (permission) {
    hasAccess = hasPermission(permission);
  } else if (anyOf && anyOf.length > 0) {
    hasAccess = hasAnyPermission(...anyOf);
  } else if (allOf && allOf.length > 0) {
    hasAccess = hasAllPermissions(...allOf);
  }

  if (!hasAccess) {
    if (showLocked) {
      return (
        <div className="relative">
          <div className="pointer-events-none opacity-30 blur-sm">
            {children}
          </div>
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="bg-slate-900/90 backdrop-blur-lg border border-red-500/30 rounded-lg px-4 py-3 flex items-center gap-2">
              <Lock className="w-4 h-4 text-red-400" />
              <span className="text-sm text-red-400 font-medium">Access Restricted</span>
            </div>
          </div>
        </div>
      );
    }
    return fallback;
  }

  return <>{children}</>;
}

/**
 * RoleGuard - Show content only to specific roles
 *
 * Usage:
 * <RoleGuard roles={['admin', 'executive']}>
 *   <AdminPanel />
 * </RoleGuard>
 */
export function RoleGuard({ children, roles, fallback = null }) {
  const { userRole } = usePermissions();

  if (!roles.includes(userRole)) {
    return fallback;
  }

  return <>{children}</>;
}

/**
 * FeatureFlag - Conditional rendering with loading state
 */
export function FeatureFlag({ children, feature, loading = null }) {
  const { hasPermission } = usePermissions();

  if (loading !== null && !hasPermission(feature)) {
    return loading;
  }

  return hasPermission(feature) ? <>{children}</> : null;
}

export default PermissionGuard;
