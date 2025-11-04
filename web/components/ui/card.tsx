import { HTMLAttributes, forwardRef } from 'react';
import { clsx } from 'clsx';
import { motion, isMotionAvailable } from '@/lib/utils/motion';

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  animated?: boolean;
  hoverEffect?: 'lift' | 'scale' | 'glow' | 'none';
}

const Card = forwardRef<HTMLDivElement, CardProps>(
  ({ className, animated = true, hoverEffect = 'lift', children, ...props }, ref) => {
    const cardContent = (
      <div
        ref={ref}
        className={clsx(
          'rounded-lg border border-gray-200 bg-white text-gray-950 shadow-sm',
          'transition-all duration-300 ease-out',
          
          // Hover effects
          {
            'hover:shadow-lg hover:-translate-y-1': hoverEffect === 'lift' && animated,
            'hover:scale-[1.02] hover:shadow-lg': hoverEffect === 'scale' && animated,
            'hover:shadow-xl hover:shadow-blue-500/10 hover:border-blue-300': hoverEffect === 'glow' && animated,
          },
          
          className
        )}
        {...props}
      >
        {children}
      </div>
    );

    if (animated && hoverEffect !== 'none' && isMotionAvailable()) {
      return (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, ease: 'easeOut' }}
          whileHover={
            hoverEffect === 'lift' 
              ? { y: -4, boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.1)', transition: { type: 'spring', stiffness: 300, damping: 25 } }
              : hoverEffect === 'scale'
              ? { scale: 1.02, transition: { type: 'spring', stiffness: 300, damping: 25 } }
              : hoverEffect === 'glow'
              ? { boxShadow: '0 0 20px rgba(59, 130, 246, 0.2)', transition: { type: 'spring', stiffness: 300, damping: 25 } }
              : {}
          }
        >
          {cardContent}
        </motion.div>
      );
    }

    return cardContent;
  }
);
Card.displayName = 'Card';

const CardHeader = forwardRef<HTMLDivElement, CardProps>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={clsx('flex flex-col space-y-1.5 p-6', className)}
      {...props}
    />
  )
);
CardHeader.displayName = 'CardHeader';

const CardTitle = forwardRef<HTMLParagraphElement, HTMLAttributes<HTMLHeadingElement>>(
  ({ className, ...props }, ref) => (
    <h3
      ref={ref}
      className={clsx('text-2xl font-semibold leading-none tracking-tight', className)}
      {...props}
    />
  )
);
CardTitle.displayName = 'CardTitle';

const CardDescription = forwardRef<HTMLParagraphElement, HTMLAttributes<HTMLParagraphElement>>(
  ({ className, ...props }, ref) => (
    <p
      ref={ref}
      className={clsx('text-sm text-gray-500', className)}
      {...props}
    />
  )
);
CardDescription.displayName = 'CardDescription';

const CardContent = forwardRef<HTMLDivElement, CardProps>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={clsx('p-6 pt-0', className)} {...props} />
  )
);
CardContent.displayName = 'CardContent';

const CardFooter = forwardRef<HTMLDivElement, CardProps>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={clsx('flex items-center p-6 pt-0', className)}
      {...props}
    />
  )
);
CardFooter.displayName = 'CardFooter';

export { Card, CardHeader, CardFooter, CardTitle, CardDescription, CardContent };