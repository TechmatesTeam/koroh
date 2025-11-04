'use client';

import { ReactNode } from 'react';
import { Navigation } from './navigation';
import { NotificationToast } from '@/components/ui/notification-toast';
import { ContentTransition } from '@/components/ui/content-transition';

interface AppLayoutProps {
  children: ReactNode;
}

export function AppLayout({ children }: AppLayoutProps) {
  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation />
      <main className="relative">
        <ContentTransition>
          {children}
        </ContentTransition>
      </main>
      <NotificationToast />
    </div>
  );
}