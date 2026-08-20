import { createContext, useState, useEffect, useContext, type ReactNode } from 'react';
import { apiFetch, setLocalAccessToken } from '../api/client';

export interface UserProfile {
  id: string;
  email: string;
  full_name: string;
  role: string;
  department_id: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

interface AuthContextType {
  user: UserProfile | null;
  accessToken: string | null;
  loading: boolean;
  login: (email: string, password: string, requestedRole?: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshAccessToken: () => Promise<string | null>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  // Sync access token to local storage only if required, but task specifies: "DO NOT store the access token in localStorage."
  // So the access token is strictly kept in memory (React state).
  // On page refresh, the AuthProvider calls refreshAccessToken() to restore the session.

  const refreshAccessToken = async (): Promise<string | null> => {
    try {
      const data = await apiFetch<{ access_token: string; user: UserProfile }>('/auth/refresh', {
        method: 'POST',
      });
      setAccessToken(data.access_token);
      setUser(data.user);
      // Store token in memory/state and update authorization header
      setLocalAccessToken(data.access_token);
      return data.access_token;
    } catch {
      // Refresh token expired or absent: clear state
      setAccessToken(null);
      setUser(null);
      setLocalAccessToken(null);
      return null;
    }
  };

  const login = async (email: string, password: string, requestedRole?: string) => {
    const data = await apiFetch<{ access_token: string; user: UserProfile }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password, requested_role: requestedRole }),
    });
    setAccessToken(data.access_token);
    setUser(data.user);
    setLocalAccessToken(data.access_token);
  };

  const logout = async () => {
    try {
      await apiFetch('/auth/logout', { method: 'POST' });
    } catch {
      // Proceed with local logout regardless of server response
    } finally {
      setAccessToken(null);
      setUser(null);
      setLocalAccessToken(null);
    }
  };

  useEffect(() => {
    // Attempt session restoration on mount
    refreshAccessToken().finally(() => {
      setLoading(false);
    });

    // Auto-refresh token every 28 minutes to keep it valid (access token life: 30m)
    const interval = setInterval(() => {
      refreshAccessToken();
    }, 28 * 60 * 1000);

    return () => clearInterval(interval);
  }, []);

  return (
    <AuthContext.Provider value={{ user, accessToken, loading, login, logout, refreshAccessToken }}>
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
