/**
 * Enhanced Link component that ensures client-side navigation
 */

import { forwardRef } from 'react';
import Link from 'next/link';
import { useClientNavigation } from '@/lib/hooks/use-client-navigation';

interface ClientLinkProps {
  href: string;
  children: React.ReactNode;
  className?: string;
  replace?: boolean;
  prefetch?: boolean;
  onClick?: (e: React.MouseEvent<HTMLAnchorElement>) => void;
  [key: string]: any;
}

export const ClientLink = forwardRef<HTMLAnchorElement, ClientLinkProps>(
  ({ href, children, className, replace = false, prefetch = true, onClick, ...props }, ref) => {
    const { handleLinkClick } = useClientNavigation();

    const handleClick = (e: React.MouseEvent<HTMLAnchorElement>) => {
      // Call custom onClick if provided
      if (onClick) {
        onClick(e);
      }

      // Handle client-side navigation
      if (!e.defaultPrevented) {
        handleLinkClick(href, { replace })(e);
      }
    };

    return (
      <Link
        href={href}
        className={className}
        prefetch={prefetch}
        ref={ref}
        onClick={handleClick}
        {...props}
      >
        {children}
      </Link>
    );
  }
);

ClientLink.displayName = 'ClientLink';