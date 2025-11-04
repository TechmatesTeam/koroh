/**
 * Robust JWT token management for the Koroh platform
 * Handles token storage, refresh, and validation
 */

import Cookies from 'js-cookie';
import { jwtDecode } from 'jwt-decode';

interface TokenPayload {
  exp: number;
  iat: number;
  user_id: string;
  email: string;
  [key: string]: any;
}

interface TokenPair {
  access: string;
  refresh: string;
}

class TokenManager {
  private static instance: TokenManager;
  private refreshPromise: Promise<string> | null = null;

  private constructor() {}

  static getInstance(): TokenManager {
    if (!TokenManager.instance) {
      TokenManager.instance = new TokenManager();
    }
    return TokenManager.instance;
  }

  /**
   * Store tokens securely
   */
  setTokens(tokens: TokenPair): void {
    const isProduction = process.env.NODE_ENV === 'production';
    
    // Store access token (shorter expiry)
    Cookies.set('access_token', tokens.access, {
      expires: 1, // 1 day
      secure: isProduction,
      sameSite: 'lax',
      httpOnly: false, // Need to access from JS
    });

    // Store refresh token (longer expiry)
    Cookies.set('refresh_token', tokens.refresh, {
      expires: 7, // 7 days
      secure: isProduction,
      sameSite: 'lax',
      httpOnly: false,
    });
  }

  /**
   * Get access token
   */
  getAccessToken(): string | null {
    return Cookies.get('access_token') || null;
  }

  /**
   * Get refresh token
   */
  getRefreshToken(): string | null {
    return Cookies.get('refresh_token') || null;
  }

  /**
   * Clear all tokens
   */
  clearTokens(): void {
    Cookies.remove('access_token');
    Cookies.remove('refresh_token');
    this.refreshPromise = null;
  }

  /**
   * Check if access token is valid and not expired
   */
  isAccessTokenValid(): boolean {
    const token = this.getAccessToken();
    if (!token) return false;

    try {
      const payload = jwtDecode<TokenPayload>(token);
      const currentTime = Math.floor(Date.now() / 1000);
      
      // Check if token expires in the next 5 minutes (300 seconds)
      return payload.exp > currentTime + 300;
    } catch (error) {
      console.error('Invalid token format:', error);
      return false;
    }
  }

  /**
   * Check if refresh token is valid and not expired
   */
  isRefreshTokenValid(): boolean {
    const token = this.getRefreshToken();
    if (!token) return false;

    try {
      const payload = jwtDecode<TokenPayload>(token);
      const currentTime = Math.floor(Date.now() / 1000);
      
      return payload.exp > currentTime;
    } catch (error) {
      console.error('Invalid refresh token format:', error);
      return false;
    }
  }

  /**
   * Get token payload without verification
   */
  getTokenPayload(token?: string): TokenPayload | null {
    const tokenToUse = token || this.getAccessToken();
    if (!tokenToUse) return null;

    try {
      return jwtDecode<TokenPayload>(tokenToUse);
    } catch (error) {
      console.error('Failed to decode token:', error);
      return null;
    }
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    return this.isAccessTokenValid() || this.isRefreshTokenValid();
  }

  /**
   * Get time until token expires (in seconds)
   */
  getTimeUntilExpiry(): number | null {
    const token = this.getAccessToken();
    if (!token) return null;

    try {
      const payload = jwtDecode<TokenPayload>(token);
      const currentTime = Math.floor(Date.now() / 1000);
      return Math.max(0, payload.exp - currentTime);
    } catch (error) {
      return null;
    }
  }

  /**
   * Refresh access token using refresh token
   */
  async refreshAccessToken(): Promise<string> {
    // If there's already a refresh in progress, return that promise
    if (this.refreshPromise) {
      return this.refreshPromise;
    }

    const refreshToken = this.getRefreshToken();
    if (!refreshToken || !this.isRefreshTokenValid()) {
      throw new Error('No valid refresh token available');
    }

    this.refreshPromise = this.performTokenRefresh(refreshToken);

    try {
      const newAccessToken = await this.refreshPromise;
      return newAccessToken;
    } finally {
      this.refreshPromise = null;
    }
  }

  /**
   * Perform the actual token refresh API call
   */
  private async performTokenRefresh(refreshToken: string): Promise<string> {
    const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
    
    try {
      const response = await fetch(`${API_BASE_URL}/auth/refresh/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refresh: refreshToken }),
      });

      if (!response.ok) {
        throw new Error(`Token refresh failed: ${response.status}`);
      }

      const data = await response.json();
      const newAccessToken = data.access;

      if (!newAccessToken) {
        throw new Error('No access token in refresh response');
      }

      // Update the access token
      Cookies.set('access_token', newAccessToken, {
        expires: 1,
        secure: process.env.NODE_ENV === 'production',
        sameSite: 'lax',
      });

      return newAccessToken;
    } catch (error) {
      // Clear tokens on refresh failure
      this.clearTokens();
      throw error;
    }
  }

  /**
   * Get a valid access token, refreshing if necessary
   */
  async getValidAccessToken(): Promise<string | null> {
    // If access token is valid, return it
    if (this.isAccessTokenValid()) {
      return this.getAccessToken();
    }

    // If refresh token is valid, try to refresh
    if (this.isRefreshTokenValid()) {
      try {
        return await this.refreshAccessToken();
      } catch (error) {
        console.error('Token refresh failed:', error);
        return null;
      }
    }

    // No valid tokens
    return null;
  }

  /**
   * Schedule automatic token refresh
   */
  scheduleTokenRefresh(): void {
    const timeUntilExpiry = this.getTimeUntilExpiry();
    
    if (timeUntilExpiry && timeUntilExpiry > 300) { // More than 5 minutes
      // Schedule refresh 5 minutes before expiry
      const refreshTime = (timeUntilExpiry - 300) * 1000;
      
      setTimeout(async () => {
        try {
          await this.refreshAccessToken();
          // Schedule next refresh
          this.scheduleTokenRefresh();
        } catch (error) {
          console.error('Scheduled token refresh failed:', error);
        }
      }, refreshTime);
    }
  }

  /**
   * Initialize token manager
   */
  initialize(): void {
    // Schedule token refresh if we have valid tokens
    if (this.isAuthenticated()) {
      this.scheduleTokenRefresh();
    }

    // Listen for storage events (token changes in other tabs)
    if (typeof window !== 'undefined') {
      window.addEventListener('storage', (event) => {
        if (event.key === 'access_token' || event.key === 'refresh_token') {
          // Token changed in another tab, update our state
          if (!event.newValue) {
            // Token was removed
            this.clearTokens();
          }
        }
      });
    }
  }
}

// Export singleton instance
export const tokenManager = TokenManager.getInstance();

// Auto-initialize when module is loaded
if (typeof window !== 'undefined') {
  tokenManager.initialize();
}