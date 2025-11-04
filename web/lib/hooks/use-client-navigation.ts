/**
 * Hook for ensuring client-side navigation without page reloads
 */

import { useRouter } from 'next/navigation';
import { useCallback } from 'react';

export function useClientNavigation() {
  const router = useRouter();

  const navigate = useCallback((href: string, options?: { replace?: boolean }) => {
    // Ensure we're doing client-side navigation
    if (typeof window !== 'undefined') {
      // Prevent any potential page reload
      if (options?.replace) {
        router.replace(href);
      } else {
        router.push(href);
      }
    }
  }, [router]);

  const handleLinkClick = useCallback((href: string, options?: { replace?: boolean }) => {
    return (e: React.MouseEvent<HTMLAnchorElement>) => {
      // Only prevent default for internal links
      if (href.startsWith('/') && !href.startsWith('//')) {
        e.preventDefault();
        navigate(href, options);
      }
    };
  }, [navigate]);

  return {
    navigate,
    handleLinkClick,
    router,
  };
}

/**
 * Prefetch pages for faster navigation
 */
export function usePrefetch() {
  const router = useRouter();

  const prefetch = useCallback((href: string) => {
    if (typeof window !== 'undefined' && href.startsWith('/')) {
      router.prefetch(href);
    }
  }, [router]);

  return { prefetch };
}