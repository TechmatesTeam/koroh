/**
 * Enhanced navigation link that ensures no page reloads
 */

'use client';

import { forwardRef } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

interface NavLinkProps {
  href: string;
  children: React.ReactNode;
  className?: string;
  onClick?: (e: React.MouseEvent<HTMLAnchorElement>) => void;
  [key: string]: any;
}

export const NavLink = forwardRef<HTMLAnchorElement, NavLinkProps>(
  ({ href, children, className, onClick, ...props }, ref) => {
    const router = useRouter();

    const handleClick = (e: React.MouseEvent<HTMLAnchorElement>) => {
      // Call custom onClick if provided
      if (onClick) {
        onClick(e);
      }

      // For internal links, ensure client-side navigation
      if (href.startsWith('/') && !href.startsWith('//')) {
        e.preventDefault();
        
        // Use requestAnimationFrame for smoother navigation
        requestAnimationFrame(() => {
          router.push(href);
        });
      }
    };

    return (
      <Link
        href={href}
        className={className}
        ref={ref}
        onClick={handleClick}
        {...props}
      >
        {children}
      </Link>
    );
  }
);

NavLink.displayName = 'NavLink';