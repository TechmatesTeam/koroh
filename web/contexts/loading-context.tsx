'use client';

import { createContext, useContext, useState, ReactNode, useEffect } from 'react';
import { usePathname, useSearchParams } from 'next/navigation';
import { LoadingScreen } from '@/components/ui/loading-screen';

interface LoadingContextType {
  isLoading: boolean;
  setLoading: (loading: boolean) => void;
  showPageLoading: (message?: string) => void;
  hidePageLoading: () => void;
}

const LoadingContext = createContext<LoadingContextType | undefined>(undefined);

export function LoadingProvider({ children }: { children: ReactNode }) {
  const [isLoading, setIsLoading] = useState(false);
  const [pageLoadingMessage, setPageLoadingMessage] = useState<string>('');
  const [showPageLoader, setShowPageLoader] = useState(false);
  const pathname = usePathname();
  const searchParams = useSearchParams();

  // Handle route changes - disabled automatic loading for smooth navigation
  useEffect(() => {
    // Only show loading for initial page load, not for client-side navigation
    // This prevents the loading screen from showing on every route change
    // which was causing the perception of page reloads
  }, [pathname, searchParams]);

  const setLoading = (loading: boolean) => {
    setIsLoading(loading);
  };

  const showPageLoading = (message: string = 'Loading...') => {
    setPageLoadingMessage(message);
    setShowPageLoader(true);
  };

  const hidePageLoading = () => {
    setShowPageLoader(false);
    setPageLoadingMessage('');
  };

  const value = {
    isLoading,
    setLoading,
    showPageLoading,
    hidePageLoading,
  };

  return (
    <LoadingContext.Provider value={value}>
      {children}
      <LoadingScreen 
        isLoading={showPageLoader} 
        message={pageLoadingMessage}
        showLogo={false}
      />
    </LoadingContext.Provider>
  );
}

export function useLoading() {
  const context = useContext(LoadingContext);
  if (context === undefined) {
    throw new Error('useLoading must be used within a LoadingProvider');
  }
  return context;
}