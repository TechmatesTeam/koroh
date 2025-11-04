'use client';

import { ReactNode } from 'react';
import { motion, isMotionAvailable } from '@/lib/utils/motion';

interface MotionWrapperProps {
  children: ReactNode;
  className?: string;
  initial?: any;
  animate?: any;
  transition?: any;
  whileHover?: any;
  whileTap?: any;
  variants?: any;
  style?: React.CSSProperties;
  fallbackClassName?: string;
}

export function MotionDiv({
  children,
  className = '',
  initial,
  animate,
  transition,
  whileHover,
  whileTap,
  variants,
  style,
  fallbackClassName = 'animate-fade-in',
  ...props
}: MotionWrapperProps) {
  if (!isMotionAvailable()) {
    return (
      <div 
        className={`${className} ${fallbackClassName}`} 
        style={style}
        {...props}
      >
        {children}
      </div>
    );
  }

  return (
    <motion.div
      className={className}
      initial={initial}
      animate={animate}
      transition={transition}
      whileHover={whileHover}
      whileTap={whileTap}
      variants={variants}
      style={style}
      {...props}
    >
      {children}
    </motion.div>
  );
}

export function MotionSpan({
  children,
  className = '',
  initial,
  animate,
  transition,
  whileHover,
  variants,
  style,
  fallbackClassName = '',
  ...props
}: MotionWrapperProps) {
  if (!isMotionAvailable()) {
    return (
      <span 
        className={`${className} ${fallbackClassName}`} 
        style={style}
        {...props}
      >
        {children}
      </span>
    );
  }

  return (
    <motion.span
      className={className}
      initial={initial}
      animate={animate}
      transition={transition}
      whileHover={whileHover}
      variants={variants}
      style={style}
      {...props}
    >
      {children}
    </motion.span>
  );
}