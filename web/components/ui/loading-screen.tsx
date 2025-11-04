'use client';

import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Sparkles, Loader2 } from 'lucide-react';

interface LoadingScreenProps {
  isLoading: boolean;
  message?: string;
  showLogo?: boolean;
}

export function LoadingScreen({ 
  isLoading, 
  message = "Loading...", 
  showLogo = true 
}: LoadingScreenProps) {
  const [dots, setDots] = useState('');

  useEffect(() => {
    if (!isLoading) return;

    const interval = setInterval(() => {
      setDots(prev => {
        if (prev === '...') return '';
        return prev + '.';
      });
    }, 500);

    return () => clearInterval(interval);
  }, [isLoading]);

  return (
    <AnimatePresence>
      {isLoading && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2 }}
          className="fixed inset-0 z-50 flex items-center justify-center bg-white"
        >
          <div className="text-center">
            {showLogo && (
              <motion.div
                initial={{ scale: 0.8, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ delay: 0.1, duration: 0.3 }}
                className="mb-8"
              >
                <div className="flex items-center justify-center mb-4">
                  <div className="relative">
                    <Sparkles className="w-12 h-12 text-teal-600" />
                    <motion.div
                      animate={{ rotate: 360 }}
                      transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                      className="absolute inset-0"
                    >
                      <Loader2 className="w-12 h-12 text-teal-400 opacity-50" />
                    </motion.div>
                  </div>
                </div>
                <h1 className="text-3xl font-bold text-gray-900 mb-2">Koroh</h1>
                <p className="text-gray-600">AI-Powered Professional Networking</p>
              </motion.div>
            )}
            
            <motion.div
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.2, duration: 0.3 }}
              className="space-y-4"
            >
              {/* Loading spinner */}
              <div className="flex justify-center">
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                  className="w-8 h-8 border-3 border-teal-200 border-t-teal-600 rounded-full"
                />
              </div>
              
              {/* Loading message */}
              <p className="text-gray-600 font-medium">
                {message}
                <span className="inline-block w-6 text-left">{dots}</span>
              </p>
            </motion.div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

// Minimal loading screen for faster transitions
export function MinimalLoadingScreen({ isLoading }: { isLoading: boolean }) {
  return (
    <AnimatePresence>
      {isLoading && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.15 }}
          className="fixed inset-0 z-50 flex items-center justify-center bg-white/80 backdrop-blur-sm"
        >
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
            className="w-8 h-8 border-3 border-teal-200 border-t-teal-600 rounded-full"
          />
        </motion.div>
      )}
    </AnimatePresence>
  );
}

// Page loading overlay
export function PageLoadingOverlay({ isLoading }: { isLoading: boolean }) {
  return (
    <AnimatePresence>
      {isLoading && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 1.05 }}
          transition={{ duration: 0.2 }}
          className="fixed inset-0 z-40 flex items-center justify-center bg-gray-50/90 backdrop-blur-sm"
        >
          <motion.div
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: -20, opacity: 0 }}
            className="bg-white rounded-lg shadow-lg p-6 flex items-center space-x-3"
          >
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
              className="w-5 h-5 border-2 border-teal-200 border-t-teal-600 rounded-full"
            />
            <span className="text-gray-700 font-medium">Loading...</span>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}