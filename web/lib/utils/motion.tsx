import React from 'react';

// Conditional motion import with fallback
let motion: any;
let AnimatePresence: any;
let motionAvailable = false;

try {
  const framerMotion = require('framer-motion');
  motion = framerMotion.motion;
  AnimatePresence = framerMotion.AnimatePresence;
  motionAvailable = true;
} catch (error) {
  // Fallback when framer-motion is not available
  console.warn('framer-motion not available, using fallback components');
  
  const FallbackDiv = ({ children, className, style, ...props }: any) => (
    <div className={className} style={style} {...props}>{children}</div>
  );
  
  const FallbackSpan = ({ children, className, style, ...props }: any) => (
    <span className={className} style={style} {...props}>{children}</span>
  );

  motion = {
    div: FallbackDiv,
    span: FallbackSpan,
    button: FallbackDiv,
  };

  AnimatePresence = ({ children }: { children: React.ReactNode }) => <>{children}</>;
}

export { motion, AnimatePresence };

// Animation variants that work with or without framer-motion
export const fadeInUp = {
  hidden: { opacity: 0, y: 60 },
  visible: { opacity: 1, y: 0 },
};

export const fadeIn = {
  hidden: { opacity: 0 },
  visible: { opacity: 1 },
};

export const scaleIn = {
  hidden: { opacity: 0, scale: 0.8 },
  visible: { opacity: 1, scale: 1 },
};

export const slideInUp = {
  hidden: { opacity: 0, y: 100 },
  visible: { opacity: 1, y: 0 },
};

// Check if framer-motion is available
export const isMotionAvailable = () => motionAvailable;