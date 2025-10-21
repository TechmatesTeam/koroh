'use client';

import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import Cookies from 'js-cookie';
import { api } from '@/lib/api';
import { parseApiError, logError, isAuthError } from '@/lib/error-handler';
import { User, AuthTokens, LoginCredentials, RegisterData } from '@/types';

interface AuthContextType {
  user: User | null;
  loading: boolean;
  error: string | null;
  login: (credentials: LoginCredentials) => Promise<void>;
  register: (userData: RegisterData) => Promise<void>;
  logout: () => void;
  requestPasswordReset: (email: string) => Promise<{ message: string; resetToken?: string }>;
  resetPassword: (token: string, password: string) => Promise<void>;
  clearError: () => void;
  refreshUser: () => Promise<void>;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  const isAuthenticated = !!user;

  const clearError = () => setError(null);

  // Check if user is authenticated on mount
  useEffect(() => {
    const checkAuth = async () => {
      try {
        // For mock API, check localStorage directly
        if (process.env.NEXT_PUBLIC_USE_MOCK_API === 'true') {
          const currentUser = localStorage.getItem('koroh_current_user');
          if (currentUser) {
            setUser(JSON.parse(currentUser));
          }
        } else {
          // For real API, check with server
          const token = Cookies.get('access_token');
          
          if (token) {
            const response = await api.profiles.getMe();
            setUser(response.data.user);
          }
        }
      } catch (error) {
        logError(error, 'Auth check');
        
        // If it's an auth error, clear tokens
        if (isAuthError(error)) {
          Cookies.remove('access_token');
          Cookies.remove('refresh_token');
        }
      } finally {
        setLoading(false);
      }
    };

    checkAuth();
  }, []);

  const login = async (credentials: LoginCredentials) => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await api.auth.login(credentials);
      
      // Handle different response structures
      const responseData = response.data;
      let access, refresh, userData;
      
      if (responseData.tokens) {
        // New format with tokens object
        access = responseData.tokens.access;
        refresh = responseData.tokens.refresh;
        userData = responseData.user;
      } else {
        // Legacy format
        access = responseData.access;
        refresh = responseData.refresh;
        userData = responseData.user;
      }

      if (!access || !userData) {
        throw new Error('Invalid response format from server');
      }

      // Store tokens securely
      Cookies.set('access_token', access, { 
        expires: 1, // 1 day
        secure: process.env.NODE_ENV === 'production',
        sameSite: 'lax'
      });
      
      if (refresh) {
        Cookies.set('refresh_token', refresh, { 
          expires: 7, // 7 days
          secure: process.env.NODE_ENV === 'production',
          sameSite: 'lax'
        });
      }

      setUser(userData);
      
      // Check for stored redirect path
      const redirectPath = sessionStorage.getItem('redirectAfterLogin');
      if (redirectPath) {
        sessionStorage.removeItem('redirectAfterLogin');
        router.push(redirectPath);
      } else {
        router.push('/dashboard');
      }
    } catch (error: any) {
      const parsedError = parseApiError(error);
      setError(parsedError.message);
      logError(error, 'Login');
      throw parsedError;
    } finally {
      setLoading(false);
    }
  };

  const register = async (userData: RegisterData) => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await api.auth.register(userData);
      
      // Handle different response structures
      const responseData = response.data;
      let access, refresh, newUser;
      
      if (responseData.tokens) {
        // New format with tokens object
        access = responseData.tokens.access;
        refresh = responseData.tokens.refresh;
        newUser = responseData.user;
      } else {
        // Legacy format
        access = responseData.access;
        refresh = responseData.refresh;
        newUser = responseData.user;
      }

      if (!access || !newUser) {
        throw new Error('Invalid response format from server');
      }

      // Store tokens securely
      Cookies.set('access_token', access, { 
        expires: 1,
        secure: process.env.NODE_ENV === 'production',
        sameSite: 'lax'
      });
      
      if (refresh) {
        Cookies.set('refresh_token', refresh, { 
          expires: 7,
          secure: process.env.NODE_ENV === 'production',
          sameSite: 'lax'
        });
      }

      setUser(newUser);
      router.push('/dashboard');
    } catch (error: any) {
      const parsedError = parseApiError(error);
      setError(parsedError.message);
      logError(error, 'Registration');
      throw parsedError;
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    try {
      // Call logout endpoint
      await api.auth.logout();
    } catch (error) {
      // Ignore logout errors - we'll clear local state anyway
      logError(error, 'Logout');
    } finally {
      // Always clear local state
      Cookies.remove('access_token');
      Cookies.remove('refresh_token');
      
      // For mock API, also clear localStorage
      if (process.env.NEXT_PUBLIC_USE_MOCK_API === 'true') {
        localStorage.removeItem('koroh_current_user');
      }
      
      setUser(null);
      setError(null);
      
      // Clear any stored redirect paths
      sessionStorage.removeItem('redirectAfterLogin');
      
      router.push('/');
    }
  };

  const requestPasswordReset = async (email: string) => {
    try {
      setError(null);
      const response = await api.auth.requestPasswordReset(email);
      return response.data;
    } catch (error: any) {
      const parsedError = parseApiError(error);
      setError(parsedError.message);
      logError(error, 'Password reset request');
      throw parsedError;
    }
  };

  const resetPassword = async (token: string, password: string) => {
    try {
      setError(null);
      await api.auth.resetPassword(token, password);
    } catch (error: any) {
      const parsedError = parseApiError(error);
      setError(parsedError.message);
      logError(error, 'Password reset');
      throw parsedError;
    }
  };

  const refreshUser = async () => {
    try {
      const response = await api.profiles.getMe();
      setUser(response.data.user);
    } catch (error) {
      logError(error, 'User refresh');
      
      if (isAuthError(error)) {
        // If refresh fails due to auth, logout user
        await logout();
      }
    }
  };

  const value = {
    user,
    loading,
    error,
    login,
    register,
    logout,
    requestPasswordReset,
    resetPassword,
    clearError,
    refreshUser,
    isAuthenticated,
  };

  return (
    <AuthContext.Provider value={value}>
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