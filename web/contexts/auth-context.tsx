'use client';

import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import Cookies from 'js-cookie';
import { api } from '@/lib/api';
import { parseApiError, logError, isAuthError } from '@/lib/error-handler';
import { tokenManager } from '@/lib/token-manager';
import { resetAllStores } from '@/lib/stores';
import { User, AuthTokens, LoginCredentials, RegisterData } from '@/types';

interface AuthContextType {
  user: User | null;
  loading: boolean;
  error: string | null;
  login: (credentials: LoginCredentials, userData?: User, tokens?: AuthTokens) => Promise<void>;
  register: (userData: RegisterData) => Promise<any>;
  logout: () => void;
  requestPasswordReset: (email: string) => Promise<{ message: string; resetToken?: string }>;
  resetPassword: (token: string, password: string) => Promise<void>;
  verifyEmail: (token: string) => Promise<{ user: User; tokens: AuthTokens }>;
  resendVerification: (email: string) => Promise<{ message: string }>;
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
          // For real API, check if we have valid tokens
          if (tokenManager.isAuthenticated()) {
            try {
              const response = await api.profiles.getMe();
              setUser(response.data.user);
            } catch (error) {
              // If profile fetch fails, clear tokens
              tokenManager.clearTokens();
            }
          }
        }
      } catch (error) {
        logError(error, 'Auth check');
        
        // If it's an auth error, clear tokens
        if (isAuthError(error)) {
          tokenManager.clearTokens();
        }
      } finally {
        setLoading(false);
      }
    };

    checkAuth();
  }, []);

  const login = async (credentials: LoginCredentials, userData?: User, tokens?: AuthTokens) => {
    // If userData and tokens are provided, use them directly (for post-verification login)
    if (userData && tokens) {
      tokenManager.setTokens(tokens);
      setUser(userData);
      
      setTimeout(() => {
        const redirectPath = sessionStorage.getItem('redirectAfterLogin');
        if (redirectPath) {
          sessionStorage.removeItem('redirectAfterLogin');
          router.push(redirectPath);
        } else {
          router.push('/dashboard');
        }
      }, 100);
      return;
    }
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

      // Store tokens using token manager
      tokenManager.setTokens({ access, refresh });

      setUser(userData);
      
      // Use requestAnimationFrame for smoother transitions
      requestAnimationFrame(() => {
        setTimeout(() => {
          const redirectPath = sessionStorage.getItem('redirectAfterLogin');
          if (redirectPath) {
            sessionStorage.removeItem('redirectAfterLogin');
            router.replace(redirectPath);
          } else {
            router.replace('/dashboard');
          }
        }, 50);
      });
    } catch (error: any) {
      const parsedError = parseApiError(error);
      
      // Check if it's a verification required error
      if (error.response?.status === 403 && error.response?.data?.verification_required) {
        const verificationError = new Error(error.response.data.error || 'Email verification required');
        (verificationError as any).verification_required = true;
        (verificationError as any).email = error.response.data.email;
        throw verificationError;
      }
      
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
      
      // Check if verification is required
      if (responseData.verification_required) {
        // Registration successful but verification required
        // Don't set user or tokens, just return success
        return {
          success: true,
          verification_required: true,
          email: responseData.email,
          message: responseData.message
        };
      }
      
      // Legacy flow - immediate login (for backward compatibility)
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

      // Store tokens using token manager
      tokenManager.setTokens({ access, refresh });

      setUser(newUser);
      requestAnimationFrame(() => {
        setTimeout(() => {
          router.replace('/dashboard');
        }, 50);
      });
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
      tokenManager.clearTokens();
      
      // For mock API, also clear localStorage
      if (process.env.NEXT_PUBLIC_USE_MOCK_API === 'true') {
        localStorage.removeItem('koroh_current_user');
      }
      
      // Reset all Zustand stores
      resetAllStores();
      
      setUser(null);
      setError(null);
      
      // Clear any stored redirect paths
      sessionStorage.removeItem('redirectAfterLogin');
      
      router.replace('/');
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

  const verifyEmail = async (token: string) => {
    try {
      setError(null);
      const response = await api.auth.verifyEmail(token);
      return response.data;
    } catch (error: any) {
      const parsedError = parseApiError(error);
      setError(parsedError.message);
      logError(error, 'Email verification');
      throw parsedError;
    }
  };

  const resendVerification = async (email: string) => {
    try {
      setError(null);
      const response = await api.auth.resendVerification(email);
      return response.data;
    } catch (error: any) {
      const parsedError = parseApiError(error);
      setError(parsedError.message);
      logError(error, 'Resend verification');
      throw parsedError;
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
    verifyEmail,
    resendVerification,
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