'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { apiClient } from '@/lib/api-client';

interface User {
  id: string;
  email: string;
  name: string;
  role: string;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (user: User, token: string, refresh: string) => void;
  logout: () => void;
  apiKey: string | null;
  saveApiKey: (key: string | null) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [apiKey, setApiKey] = useState<string | null>(null);
  const router = useRouter();

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    const savedApiKey = localStorage.getItem('api_key');
    const savedUser = localStorage.getItem('tides_user');
    
    if (savedApiKey) {
      setApiKey(savedApiKey);
    }

    if (token && savedUser) {
      try {
        setUser(JSON.parse(savedUser));
      } catch (e) {
        setUser(null);
      }
    }
    setIsLoading(false);
  }, []);

  const login = (userData: User, token: string, refresh: string) => {
    localStorage.setItem('access_token', token);
    localStorage.setItem('refresh_token', refresh);
    localStorage.setItem('tides_user', JSON.stringify(userData));
    setUser(userData);
    router.push('/dashboard');
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('tides_user');
    setUser(null);
    router.push('/login');
  };

  const saveApiKey = (key: string | null) => {
    if (key) {
      localStorage.setItem('api_key', key);
      setApiKey(key);
    } else {
      localStorage.removeItem('api_key');
      setApiKey(null);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        login,
        logout,
        apiKey,
        saveApiKey,
      }}
    >
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
