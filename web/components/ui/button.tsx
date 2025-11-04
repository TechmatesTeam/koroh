'use client';

import { ButtonHTMLAttributes, forwardRef } from 'react';
import { clsx } from 'clsx';
import { motion, isMotionAvailable } from '@/lib/utils/motion';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'default' | 'outline' | 'ghost' | 'destructive';
  size?: 'sm' | 'default' | 'lg';
  animated?: boolean;
  loading?: boolean;
}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'default', size = 'default', animated = true, loading = false, children, ...props }, ref) => {
    const buttonContent = (
      <button
        type={props.type || 'button'}
        className={clsx(
          // Base styles with enhanced transitions
          'inline-flex items-center justify-center rounded-md font-medium focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none ring-offset-background relative overflow-hidden',
          
          // Enhanced transitions
          'transition-all duration-300 ease-out',
          'transform-gpu',
          
          // Hover effects
          animated && 'hover:scale-[1.02] hover:shadow-lg active:scale-[0.98]',
          
          // Variants with enhanced colors
          {
            'bg-gradient-to-r from-indigo-600 to-blue-600 text-white hover:from-indigo-700 hover:to-blue-700 shadow-md hover:shadow-xl': variant === 'default',
            'border border-gray-300 bg-white text-gray-700 hover:bg-gray-50 hover:border-gray-400 hover:shadow-md': variant === 'outline',
            'hover:bg-gray-100 text-gray-700 hover:shadow-sm': variant === 'ghost',
            'bg-gradient-to-r from-red-600 to-red-700 text-white hover:from-red-700 hover:to-red-800 shadow-md hover:shadow-xl': variant === 'destructive',
          },
          
          // Sizes
          {
            'h-9 px-3 text-sm': size === 'sm',
            'h-10 py-2 px-4': size === 'default',
            'h-11 px-8 text-lg': size === 'lg',
          },
          
          // Loading state
          loading && 'cursor-not-allowed',
          
          className
        )}
        ref={ref}
        disabled={loading || props.disabled}
        {...props}
      >
        {/* Ripple effect overlay */}
        {animated && (
          <span className="absolute inset-0 overflow-hidden rounded-md">
            <span className="absolute inset-0 bg-white opacity-0 transition-opacity duration-300 hover:opacity-10" />
          </span>
        )}
        
        {/* Loading spinner */}
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
          </div>
        )}
        
        {/* Content */}
        <span className={clsx('flex items-center gap-2', loading && 'opacity-0')}>
          {children}
        </span>
      </button>
    );

    if (animated && !loading && isMotionAvailable()) {
      return (
        <motion.div
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          transition={{ type: 'spring', stiffness: 400, damping: 25 }}
        >
          {buttonContent}
        </motion.div>
      );
    }

    return buttonContent;
  }
);

Button.displayName = 'Button';

export { Button };