import React, { createContext, useContext, useState, useEffect } from 'react';
import { User, Organization } from '../types';
import { authApi } from '../services/api';

interface AuthContextType {
  user: User | null;
  organization: Organization | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (payload: {
    full_name: string;
    email: string;
    password: string;
    organization_name: string;
  }) => Promise<void>;
  logout: () => void;
}

const DEFAULT_USER: User = {
  id: 'usr-demo-1',
  organization_id: 'org-demo-lexflow',
  email: 'alexander@hamiltonlegal.com',
  full_name: 'Alexander Hamilton',
  role: 'owner',
  is_active: true,
  created_at: '2026-01-01T00:00:00Z',
};

const DEFAULT_ORG: Organization = {
  id: 'org-demo-lexflow',
  name: 'Hamilton Legal Group',
  slug: 'hamilton-legal-group',
  is_active: true,
  created_at: '2026-01-01T00:00:00Z',
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [organization, setOrganization] = useState<Organization | null>(null);
  const [token, setToken] = useState<string | null>(localStorage.getItem('lexflow_token'));
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    const initAuth = async () => {
      const storedToken = localStorage.getItem('lexflow_token');
      if (storedToken && storedToken.startsWith('eyJ')) {
        try {
          const res = await authApi.getCurrentUser();
          setUser(res.user || res);
          if (res.organization) setOrganization(res.organization);
          setToken(storedToken);
        } catch (err) {
          console.warn('Stored token is invalid or expired, resetting session.');
          localStorage.removeItem('lexflow_token');
          setToken(null);
          setUser(null);
          setOrganization(null);
        }
      } else {
        localStorage.removeItem('lexflow_token');
        setToken(null);
        setUser(null);
        setOrganization(null);
      }
      setIsLoading(false);
    };

    initAuth();
  }, []);

  const login = async (email: string, password: string) => {
    setIsLoading(true);
    try {
      const data = await authApi.login(email, password);
      localStorage.setItem('lexflow_token', data.access_token);
      setToken(data.access_token);
      setUser(data.user);
      if (data.organization) setOrganization(data.organization);
    } catch (err: any) {
      console.error('Backend login error:', err);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (payload: {
    full_name: string;
    email: string;
    password: string;
    organization_name: string;
  }) => {
    setIsLoading(true);
    try {
      const data = await authApi.register(payload);
      localStorage.setItem('lexflow_token', data.access_token);
      setToken(data.access_token);
      setUser(data.user);
      if (data.organization) setOrganization(data.organization);
    } catch (err: any) {
      console.error('Backend registration error:', err);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem('lexflow_token');
    setToken(null);
    setUser(null);
    setOrganization(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        organization,
        token,
        isAuthenticated: !!user,
        isLoading,
        login,
        register,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
