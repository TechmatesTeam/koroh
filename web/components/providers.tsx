'use client';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { AuthProvider } from '@/contexts/auth-context';
import { NotificationProvider } from '@/contexts/notification-context';
import { LoadingProvider } from '@/contexts/loading-context';
import { ChatButton } from '@/components/ai-chat';
import { useState, useEffect } from 'react';
import { useUIStore } from '@/lib/stores/ui-store';

function ThemeInitializer() {
  useEffect(() => {
    // Initialize theme on client side
    const savedTheme = localStorage.getItem('koroh-theme') as 'light' | 'dark' | 'system' | null;
    if (savedTheme) {
      useUIStore.getState().setTheme(savedTheme);
    }
  }, []);

  return null;
}

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 5 * 60 * 1000, // 5 minutes
            cacheTime: 10 * 60 * 1000, // 10 minutes
            retry: (failureCount, error: any) => {
              // Don't retry on 4xx errors
              if (error?.response?.status >= 400 && error?.response?.status < 500) {
                return false;
              }
              return failureCount < 3;
            },
          },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>
      <LoadingProvider>
        <AuthProvider>
          <NotificationProvider>
            <ThemeInitializer />
            {children}
            <ChatButton />
          </NotificationProvider>
        </AuthProvider>
      </LoadingProvider>
      {process.env.NODE_ENV === 'development' && <ReactQueryDevtools />}
    </QueryClientProvider>
  );
}