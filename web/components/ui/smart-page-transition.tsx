'use client';

import { useEffect, useState } from 'react';
import { usePathname } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';

interface SmartPageTransitionProps {
  children: React.ReactNode;
}

// Check if the current page uses AppLayout (has navigation)
function useHasNavigation(pathname: string) {
  const authPages = ['/auth/login', '/auth/register', '/auth/forgot-password', '/auth/reset-password', '/auth/verify-email'];
  const publicPages = ['/', '/about', '/contact', '/privacy', '/terms'];
  
  return !authPages.includes(pathname) && !publicPages.includes(pathname);
}

const pageVariants = {
  initial: {
    opacity: 0,
    y: 10,
  },
  in: {
    opacity: 1,
    y: 0,
  },
  out: {
    opacity: 0,
    y: -10,
  },
};

const pageTransition = {
  type: 'tween' as const,
  ease: [0.25, 0.1, 0.25, 1] as const,
  duration: 0.2,
};

export function SmartPageTransition({ children }: SmartPageTransitionProps) {
  const pathname = usePathname();
  const [isHydrated, setIsHydrated] = useState(false);
  const hasNavigation = useHasNavigation(pathname);

  // Handle hydration
  useEffect(() => {
    setIsHydrated(true);
  }, []);

  // Show loading screen during initial hydration
  if (!isHydrated) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
          className="w-8 h-8 border-3 border-teal-200 border-t-teal-600 rounded-full"
        />
      </div>
    );
  }

  // For pages with navigation (AppLayout), don't animate the whole page
  // The ContentTransition in AppLayout will handle the content animation
  if (hasNavigation) {
    return (
      <div className="min-h-screen bg-gray-50">
        {children}
      </div>
    );
  }

  // For auth pages, no animations to prevent any reload perception
  const isAuthPage = pathname.startsWith('/auth/');
  
  if (isAuthPage) {
    return (
      <div className="min-h-screen bg-gray-50">
        {children}
      </div>
    );
  }

  // For other public pages (landing, about, etc.), use subtle animations
  return (
    <AnimatePresence mode="wait" initial={false}>
      <motion.div
        key={pathname}
        initial="initial"
        animate="in"
        exit="out"
        variants={pageVariants}
        transition={pageTransition}
        className="min-h-screen bg-gray-50"
        style={{ 
          willChange: 'transform, opacity',
          backfaceVisibility: 'hidden',
        }}
      >
        {children}
      </motion.div>
    </AnimatePresence>
  );
}