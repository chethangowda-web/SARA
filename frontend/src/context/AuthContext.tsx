import { createContext, useState, useEffect, useContext, useRef, type ReactNode } from 'react';
import {
  apiFetch,
  setAuthTokens,
  clearAuthTokens,
  setUnauthorizedHandler,
  restoreSession,
} from '../api/client';

export interface UserProfile {
  id: string;
  email: string;
  full_name: string;
  role: string;
  department_id: string | null;
  department_name?: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

interface AuthContextType {
  user: UserProfile | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (fullName: string, email: string, password: string, preferredLanguage?: string) => Promise<void>;
  logout: () => Promise<void>;
}

export function getDashboardRoute(role: string): string {
  if (role === 'CITIZEN') return '/citizen';
  if (role === 'OFFICER') return '/officer';
  if (role === 'SUPERVISOR') return '/supervisor';
  if (role === 'ADMIN') return '/admin';
  return '/login';
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const handledUnauthorizedRef = useRef(false);

  // Global 401 handling: clear auth state so ProtectedRoute redirects to /login.
  useEffect(() => {
    handledUnauthorizedRef.current = false;
    setUnauthorizedHandler(() => {
      handledUnauthorizedRef.current = true;
      setUser(null);
    });
    return () => setUnauthorizedHandler(null);
  }, []);

  // Session restoration on app load
  useEffect(() => {
    let cancelled = false;
    (async () => {
      const result = await restoreSession();
      if (cancelled) return;
      if (result) {
        setUser(result.user as UserProfile);
        setLoading(false);
      } else {
        if (!handledUnauthorizedRef.current) {
          setUser(null);
        }
        setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const login = async (email: string, password: string) => {
    const data = await apiFetch<{ access_token: string; user: UserProfile }>(
      '/auth/login',
      { method: 'POST', body: JSON.stringify({ email, password }) }
    );
    setAuthTokens(data.access_token);
    setUser(data.user);
  };

  const signup = async (fullName: string, email: string, password: string, preferredLanguage: string = 'en') => {
    await apiFetch<{ message: string; user: UserProfile }>(
      '/auth/signup',
      {
        method: 'POST',
        body: JSON.stringify({
          email,
          password,
          full_name: fullName,
          preferred_language: preferredLanguage
        })
      }
    );
  };

  const logout = async () => {
    try {
      await apiFetch('/auth/logout', {
        method: 'POST',
      });
    } catch {
      // Proceed with local logout regardless of server response
    } finally {
      clearAuthTokens();
      setUser(null);
    }
  };

  const isAuthenticated = !!user;

  return (
    <AuthContext.Provider value={{ user, isAuthenticated, isLoading: loading, login, signup, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}