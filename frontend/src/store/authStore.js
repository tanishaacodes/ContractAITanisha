import { create } from 'zustand';
import { API_BASE_URL } from '../utils/api';

let _initializingAuth = false;

const useAuthStore = create((set) => ({
  user: null,
  token: localStorage.getItem('token'),
  isAuthenticated: false, // Set to false initially, will be validated on app load
  isLoading: false,
  isInitialized: false, // Track if we've validated the token

  login: async (email, password) => {
    set({ isLoading: true });
    try {
      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message);
      }

      const data = await response.json();
      localStorage.setItem('token', data.token);
      set({
        user: data.user,
        token: data.token,
        isAuthenticated: true,
        isLoading: false,
        isInitialized: true,
      });

      return data;
    } catch (error) {
      set({ isLoading: false });
      throw error;
    }
  },

  register: async (email, password, firstName, lastName) => {
    set({ isLoading: true });
    try {
      const response = await fetch(`${API_BASE_URL}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password, firstName, lastName }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message);
      }

      const data = await response.json();
      localStorage.setItem('token', data.token);
      localStorage.setItem('isFirstLogin', 'true'); // Mark as first login
      set({
        user: data.user,
        token: data.token,
        isAuthenticated: true,
        isLoading: false,
        isInitialized: true,
      });
      return data;
    } catch (error) {
      set({ isLoading: false });
      throw error;
    }
  },

  fetchCurrentUser: async () => {
    const token = localStorage.getItem('token');
    if (!token || token === 'null' || token === 'undefined') {
      set({ user: null, token: null, isAuthenticated: false, isInitialized: true });
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/auth/me`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!response.ok) {
        // Only clear auth on 401 (token explicitly expired/invalid)
        if (response.status === 401) {
          localStorage.removeItem('token');
          set({ user: null, token: null, isAuthenticated: false, isInitialized: true });
        } else {
          set({ isAuthenticated: true, isInitialized: true });
        }
        return;
      }

      const data = await response.json();
      set({ user: data.user, isAuthenticated: true, isInitialized: true });
    } catch (error) {
      console.warn('Failed to fetch current user (network):', error.message);
      set({ isAuthenticated: true, isInitialized: true });
    }
  },

  // Initialize auth state by validating token
  initializeAuth: async () => {
    // Prevent duplicate concurrent calls (React StrictMode double-invokes effects)
    if (_initializingAuth) return;
    _initializingAuth = true;

    const token = localStorage.getItem('token');
    if (!token || token === 'null' || token === 'undefined') {
      localStorage.removeItem('token');
      _initializingAuth = false;
      set({ isAuthenticated: false, isInitialized: true });
      return;
    }

    const fetchAuthMe = async (timeoutMs) => {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
      try {
        const response = await fetch(`${API_BASE_URL}/auth/me`, {
          headers: { Authorization: `Bearer ${token}` },
          signal: controller.signal,
        });
        clearTimeout(timeoutId);
        return response;
      } catch (err) {
        clearTimeout(timeoutId);
        throw err;
      }
    };

    const decodeLocalUser = () => {
      const payload = JSON.parse(atob(token.split('.')[1]));
      return {
        id: payload.user_id || payload.id || '',
        email: payload.email || '',
        firstName: payload.first_name || payload.firstName || payload.email?.split('@')[0] || 'User',
        lastName: payload.last_name || payload.lastName || '',
        role: payload.role || 'user',
      };
    };

    // Validate token by fetching current user
    try {
      let response;
      try {
        response = await fetchAuthMe(8000);
      } catch {
        // First attempt timed out — use local JWT immediately so UI is unblocked,
        // then retry in the background to get full server user data.
        try {
          const localUser = decodeLocalUser();
          set({ user: localUser, isAuthenticated: true, isInitialized: true });
        } catch {
          set({ isAuthenticated: true, isInitialized: true });
        }
        _initializingAuth = false;
        // Background retry after 5 seconds
        setTimeout(async () => {
          try {
            const retryResponse = await fetchAuthMe(15000);
            if (retryResponse && retryResponse.ok) {
              const data = await retryResponse.json();
              set({ user: data.user, isAuthenticated: true });
            }
          } catch { /* silent */ }
        }, 5000);
        return;
      }

      if (!response.ok) {
        if (response.status === 401) {
          localStorage.removeItem('token');
          set({ user: null, token: null, isAuthenticated: false, isInitialized: true });
        } else {
          set({ isAuthenticated: true, isInitialized: true });
        }
        _initializingAuth = false;
        return;
      }

      const data = await response.json();
      set({ user: data.user, isAuthenticated: true, isInitialized: true });
    } catch (error) {
      try {
        const localUser = decodeLocalUser();
        set({ user: localUser, isAuthenticated: true, isInitialized: true });
      } catch {
        set({ isAuthenticated: true, isInitialized: true });
      }
    } finally {
      _initializingAuth = false;
    }
  },

  logout: () => {
    localStorage.removeItem('token');
    localStorage.removeItem('isFirstLogin');
    set({ user: null, token: null, isAuthenticated: false, isInitialized: true });
  },

  clearFirstLoginFlag: () => {
    localStorage.removeItem('isFirstLogin');
  },

  setUser: (userData) => {
    set({ user: userData });
  },
}));

export default useAuthStore;
