/**
 * Hook for smooth navigation transitions
 */

import { useRouter } from 'next/navigation';
import { useCallback } from 'react';

export function useSmoothNavigation() {
  const router = useRouter();

  const navigate = useCallback((path: string, options?: { replace?: boolean }) => {
    // Add a small delay to allow for smooth transitions
    requestAnimationFrame(() => {
      if (options?.replace) {
        router.replace(path);
      } else {
        router.push(path);
      }
    });
  }, [router]);

  const navigateWithDelay = useCallback((path: string, delay: number = 100, options?: { replace?: boolean }) => {
    setTimeout(() => {
      navigate(path, options);
    }, delay);
  }, [navigate]);

  return {
    navigate,
    navigateWithDelay,
    router,
  };
}