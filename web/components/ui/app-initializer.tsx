'use client';

import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Sparkles } from 'lucide-react';

interface AppInitializerProps {
  children: React.ReactNode;
}

export function AppInitializer({ children }: AppInitializerProps) {
  const [isInitialized, setIsInitialized] = useState(false);
  const [showSplash, setShowSplash] = useState(false); // Start with false
  const [hasShownSplash, setHasShownSplash] = useState(false);

  useEffect(() => {
    // Only show splash on very first app load
    const hasLoaded = sessionStorage.getItem('koroh-app-loaded');
    
    if (!hasLoaded) {
      setShowSplash(true);
      setHasShownSplash(true);
      sessionStorage.setItem('koroh-app-loaded', 'true');
      
      // Quick initialization
      const initTimer = setTimeout(() => {
        setIsInitialized(true);
      }, 50);

      // Hide splash screen quickly
      const splashTimer = setTimeout(() => {
        setShowSplash(false);
      }, 600);

      return () => {
        clearTimeout(initTimer);
        clearTimeout(splashTimer);
      };
    } else {
      // App already loaded, skip splash
      setIsInitialized(true);
      setShowSplash(false);
    }
  }, []);

  return (
    <>
      <AnimatePresence>
        {showSplash && (
          <motion.div
            initial={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3, ease: 'easeOut' }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-white"
          >
            <motion.div
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 1.1, opacity: 0 }}
              transition={{ duration: 0.4, ease: 'easeOut' }}
              className="text-center"
            >
              <motion.div
                animate={{ 
                  rotate: [0, 360],
                  scale: [1, 1.1, 1]
                }}
                transition={{ 
                  rotate: { duration: 2, repeat: Infinity, ease: "linear" },
                  scale: { duration: 1, repeat: Infinity, ease: "easeInOut" }
                }}
                className="mb-4"
              >
                <Sparkles className="w-12 h-12 text-teal-600 mx-auto" />
              </motion.div>
              <motion.h1 
                initial={{ y: 20, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ delay: 0.2, duration: 0.3 }}
                className="text-2xl font-bold text-gray-900"
              >
                Koroh
              </motion.h1>
              <motion.p
                initial={{ y: 20, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ delay: 0.3, duration: 0.3 }}
                className="text-gray-600 text-sm mt-1"
              >
                AI-Powered Professional Networking
              </motion.p>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: isInitialized ? 1 : 0 }}
        transition={{ duration: 0.3, delay: showSplash ? 0.5 : 0 }}
        className="min-h-screen"
      >
        {isInitialized && children}
      </motion.div>
    </>
  );
}