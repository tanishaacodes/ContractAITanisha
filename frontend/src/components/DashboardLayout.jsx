import { useState } from 'react';
import { useLocation } from 'react-router-dom';
import Sidebar from './Sidebar';
import useAuthStore from '../store/authStore';
import useThemeStore from '../store/themeStore';
import ThemeToggle from './ThemeToggle';

const DashboardLayout = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { user } = useAuthStore();
  const { theme } = useThemeStore();
  const location = useLocation();
  const isFirstLogin = localStorage.getItem('isFirstLogin') === 'true';

  // Hide the generic "Dashboard" header on contract-scoped pages
  // (any route under /contracts/<uuid>…)
  const hideHeader = /^\/contracts\/[0-9a-f]{8}-/i.test(location.pathname);

  return (
    <div className={`flex h-screen bg-gradient-to-br ${theme.colors.bgPrimary}`}>
      {/* Sidebar */}
      <Sidebar isOpen={sidebarOpen} setIsOpen={setSidebarOpen} />

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top Navigation Bar – hidden on contract-scoped pages */}
        {!hideHeader && (
          <header className={`${theme.colors.surface} border-b ${theme.colors.surfaceBorder} px-6 py-4 lg:px-8`}>
            <div className="flex items-center justify-between">
              <div className="hidden lg:block">
                <h2 className={`text-2xl font-bold ${theme.colors.textPrimary}`}>Dashboard</h2>
                <p className={`${theme.colors.textSecondary} text-sm`}>
                  {isFirstLogin ? `Welcome, ${user?.firstName}! 🎉` : `Welcome back, ${user?.firstName}!`}
                </p>
              </div>

              <div className="flex items-center gap-4 ml-auto">
                <ThemeToggle />
                <div className={`hidden md:flex items-center gap-3 px-4 py-2 rounded-lg ${theme.colors.surfaceHover}`}>
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center">
                    <span className="text-white text-xs font-bold">
                      {user?.firstName?.charAt(0)}{user?.lastName?.charAt(0)}
                    </span>
                  </div>
                  <div className="text-right">
                    <p className={`text-sm font-medium ${theme.colors.textPrimary}`}>
                      {user?.firstName}
                    </p>
                    <p className={`text-xs ${theme.colors.textSecondary}`}>{user?.role}</p>
                  </div>
                </div>
              </div>
            </div>
          </header>
        )}

        {/* Page Content */}
        <main className={`flex-1 overflow-auto bg-gradient-to-br ${theme.colors.bgPrimary}`}>
          {hideHeader ? children : (
            <div className="px-4 lg:px-8 py-6">
              {children}
            </div>
          )}
        </main>
      </div>
    </div>
  );
};

export default DashboardLayout;
