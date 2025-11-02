'use client';

import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Menu, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cssClasses } from '@/lib/design-system';
import { clsx } from 'clsx';

interface PublicNavigationProps {
  showAuthButtons?: boolean;
  currentPage?: 'home' | 'login' | 'register';
}

export function PublicNavigation({ 
  showAuthButtons = true, 
  currentPage = 'home' 
}: PublicNavigationProps) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const pathname = usePathname();

  const navigationLinks = [
    { name: 'AI Chat', href: '/ai-chat', icon: '🤖' },
    { name: 'Jobs', href: '/#jobs', icon: '💼' },
    { name: 'Companies', href: '/#companies', icon: '🏢' },
    { name: 'Networking', href: '/#networking', icon: '👥' },
    { name: 'Demo', href: '/demo', icon: '🎯' },
  ];

  return (
    <nav className={cssClasses.nav.container}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          {/* Logo */}
          <div className="flex items-center">
            <Link href="/" className={cssClasses.nav.brand}>
              Koroh
            </Link>
          </div>

          {/* Desktop Navigation Links */}
          <div className="hidden md:flex items-center space-x-2">
            {navigationLinks.map((link) => {
              const isActive = pathname === link.href || 
                (link.href.startsWith('/#') && pathname === '/') ||
                (link.href !== '/' && pathname.startsWith(link.href.split('#')[0]));
              
              return (
                <Link
                  key={link.name}
                  href={link.href}
                  className={clsx(
                    'inline-flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200',
                    isActive
                      ? 'bg-teal-50 text-teal-700 shadow-sm border border-teal-200'
                      : 'text-gray-600 hover:text-teal-600 hover:bg-teal-50'
                  )}
                >
                  <span className="mr-2">{link.icon}</span>
                  {link.name}
                </Link>
              );
            })}
          </div>

          {/* Auth Buttons */}
          {showAuthButtons && (
            <div className="hidden md:flex items-center space-x-4">
              {currentPage !== 'login' && (
                <Link href="/auth/login">
                  <Button variant="ghost" className="text-gray-700 hover:text-teal-600 hover:bg-teal-50">
                    Sign In
                  </Button>
                </Link>
              )}
              {currentPage !== 'register' && (
                <Link href="/auth/register">
                  <Button className={cssClasses.button.primary}>
                    Join Now
                  </Button>
                </Link>
              )}
            </div>
          )}

          {/* Mobile menu button */}
          <div className="md:hidden flex items-center">
            <button
              type="button"
              className="text-gray-700 hover:text-teal-600 p-2"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            >
              <span className="sr-only">Open main menu</span>
              {mobileMenuOpen ? (
                <X className="h-6 w-6" />
              ) : (
                <Menu className="h-6 w-6" />
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile menu */}
      {mobileMenuOpen && (
        <div className="md:hidden">
          <div className="px-2 pt-2 pb-3 space-y-1 bg-white border-t border-gray-200">
            {navigationLinks.map((link) => {
              const isActive = pathname === link.href || 
                (link.href.startsWith('/#') && pathname === '/') ||
                (link.href !== '/' && pathname.startsWith(link.href.split('#')[0]));
              
              return (
                <Link
                  key={link.name}
                  href={link.href}
                  className={clsx(
                    'flex items-center px-3 py-3 rounded-lg font-medium transition-all duration-200',
                    isActive
                      ? 'bg-teal-50 text-teal-700 shadow-sm border border-teal-200'
                      : 'text-gray-600 hover:text-teal-600 hover:bg-teal-50'
                  )}
                  onClick={() => setMobileMenuOpen(false)}
                >
                  <span className="mr-3 text-lg">{link.icon}</span>
                  {link.name}
                  {isActive && (
                    <div className="ml-auto w-2 h-2 bg-teal-500 rounded-full"></div>
                  )}
                </Link>
              );
            })}
            
            {showAuthButtons && (
              <div className="pt-4 space-y-2">
                {currentPage !== 'login' && (
                  <Link
                    href="/auth/login"
                    className="block px-3 py-2 text-gray-700 hover:text-teal-600 hover:bg-teal-50 rounded-md font-medium"
                    onClick={() => setMobileMenuOpen(false)}
                  >
                    Sign In
                  </Link>
                )}
                {currentPage !== 'register' && (
                  <Link
                    href="/auth/register"
                    className="block px-3 py-2 bg-teal-600 text-white hover:bg-teal-700 rounded-md font-medium text-center"
                    onClick={() => setMobileMenuOpen(false)}
                  >
                    Join Now
                  </Link>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </nav>
  );
}