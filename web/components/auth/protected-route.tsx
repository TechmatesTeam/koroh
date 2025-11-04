'use client';

import { useEffect, ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/auth-context';
import { LoadingSpinner } from '@/components/ui/loading-spinner';

interface ProtectedRouteProps {
  children: ReactNode;
  requireAuth?: boolean;
  redirectTo?: string;
  fallback?: ReactNode;
}

/**
 * Protected Route Component
 * 
 * Protects routes that require authentication.
 * Redirects unauthenticated users to login page.
 */
export function ProtectedRoute({ 
  children, 
  requireAuth = true, 
  redirectTo = '/auth/login',
  fallback 
}: ProtectedRouteProps) {
  const { user, loading, isAuthenticated } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && requireAuth && !isAuthenticated) {
      // Store the current path to redirect back after login
      const currentPath = window.location.pathname + window.location.search;
      sessionStorage.setItem('redirectAfterLogin', currentPath);
      
      router.push(redirectTo);
    }
  }, [loading, isAuthenticated, requireAuth, redirectTo, router]);

  // Show loading spinner while checking authentication
  if (loading) {
    return fallback || (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  // If authentication is required but user is not authenticated, don't render children
  if (requireAuth && !isAuthenticated) {
    return fallback || null; // Let the redirect handle it
  }

  return <>{children}</>;
}

/**
 * Public Route Component
 * 
 * For routes that should redirect authenticated users away (like login/register pages)
 */
interface PublicRouteProps {
  children: ReactNode;
  redirectTo?: string;
}

export function PublicRoute({ children, redirectTo = '/dashboard' }: PublicRouteProps) {
  const { loading, isAuthenticated } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && isAuthenticated) {
      // Check if there's a stored redirect path
      const storedRedirect = sessionStorage.getItem('redirectAfterLogin');
      if (storedRedirect) {
        sessionStorage.removeItem('redirectAfterLogin');
        router.push(storedRedirect);
      } else {
        router.push(redirectTo);
      }
    }
  }, [loading, isAuthenticated, redirectTo, router]);

  // Show loading while checking authentication
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  // If user is authenticated, don't render the public route content
  if (isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return <>{children}</>;
}

/**
 * Role-based Route Protection
 */
interface RoleProtectedRouteProps {
  children: ReactNode;
  allowedRoles?: string[];
  userRole?: string;
  fallback?: ReactNode;
}

export function RoleProtectedRoute({ 
  children, 
  allowedRoles = [], 
  userRole,
  fallback 
}: RoleProtectedRouteProps) {
  const { user, loading, isAuthenticated } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !isAuthenticated) {
      router.push('/auth/login');
    }
  }, [loading, isAuthenticated, router]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  // Check role permissions
  const currentUserRole = userRole || user?.role || 'user';
  const hasPermission = allowedRoles.length === 0 || allowedRoles.includes(currentUserRole);

  if (!hasPermission) {
    // Redirect to forbidden page
    router.push('/forbidden');
    return null;
  }

  return <>{children}</>;
}