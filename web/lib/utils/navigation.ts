/**
 * Navigation utilities to prevent page refreshes and handle client-side routing
 */

import { AppRouterInstance } from 'next/dist/shared/lib/app-router-context.shared-runtime';

export interface NavigationOptions {
  replace?: boolean;
  scroll?: boolean;
  shallow?: boolean;
}

/**
 * Safe navigation that prevents page refreshes
 */
export function navigateTo(
  router: AppRouterInstance,
  path: string,
  options: NavigationOptions = {}
) {
  const { replace = false, scroll = true } = options;
  
  try {
    if (replace) {
      router.replace(path, { scroll });
    } else {
      router.push(path, { scroll });
    }
  } catch (error) {
    console.error('Navigation error:', error);
    // Fallback to window.location only if router fails
    if (typeof window !== 'undefined') {
      window.location.href = path;
    }
  }
}

/**
 * Handle form submission without page refresh
 */
export function handleFormSubmit<T = any>(
  callback: (data: T) => void | Promise<void>
) {
  return async (e: React.FormEvent<HTMLFormElement>, data?: T) => {
    e.preventDefault();
    e.stopPropagation();
    
    try {
      await callback(data as T);
    } catch (error) {
      console.error('Form submission error:', error);
      throw error;
    }
  };
}

/**
 * Handle button click without page refresh
 */
export function handleButtonClick(
  callback: () => void | Promise<void>
) {
  return async (e: React.MouseEvent<HTMLButtonElement>) => {
    e.preventDefault();
    e.stopPropagation();
    
    try {
      await callback();
    } catch (error) {
      console.error('Button click error:', error);
      throw error;
    }
  };
}

/**
 * Handle link click for programmatic navigation
 */
export function handleLinkClick(
  router: AppRouterInstance,
  path: string,
  options: NavigationOptions = {}
) {
  return (e: React.MouseEvent<HTMLAnchorElement>) => {
    // Allow default behavior for external links or when modifier keys are pressed
    if (
      path.startsWith('http') ||
      path.startsWith('mailto:') ||
      path.startsWith('tel:') ||
      e.ctrlKey ||
      e.metaKey ||
      e.shiftKey ||
      e.altKey
    ) {
      return;
    }
    
    e.preventDefault();
    navigateTo(router, path, options);
  };
}

/**
 * Debounced navigation to prevent rapid successive calls
 */
let navigationTimeout: NodeJS.Timeout | null = null;

export function debouncedNavigate(
  router: AppRouterInstance,
  path: string,
  options: NavigationOptions = {},
  delay: number = 100
) {
  if (navigationTimeout) {
    clearTimeout(navigationTimeout);
  }
  
  navigationTimeout = setTimeout(() => {
    navigateTo(router, path, options);
  }, delay);
}

/**
 * Check if a path is external
 */
export function isExternalLink(path: string): boolean {
  return (
    path.startsWith('http://') ||
    path.startsWith('https://') ||
    path.startsWith('mailto:') ||
    path.startsWith('tel:') ||
    path.startsWith('ftp://')
  );
}

/**
 * Get the current path without query parameters
 */
export function getCurrentPath(): string {
  if (typeof window === 'undefined') return '';
  return window.location.pathname;
}

/**
 * Check if the current path matches a given path
 */
export function isCurrentPath(path: string): boolean {
  return getCurrentPath() === path;
}