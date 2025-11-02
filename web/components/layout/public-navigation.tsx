'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Menu, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cssClasses } from '@/lib/design-system';

interface PublicNavigationProps {
  showAuthButtons?: boolean;
  currentPage?: 'home' | 'login' | 'register';
}

export function PublicNavigation({ 
  showAuthButtons = true, 
  currentPage = 'home' 
}: PublicNavigationProps) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navigationLinks = [
    { name: 'AI Chat', href: '/ai-chat' },
    { name: 'Jobs', href: '/#jobs' },
    { name: 'Companies', href: '/#companies' },
    { name: 'Networking', href: '/#networking' },
    { name: 'Demo', href: '/demo' },
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
          <div className="hidden md:flex items-center space-x-8">
            {navigationLinks.map((link) => (
              <Link
                key={link.name}
                href={link.href}
                className={cssClasses.nav.link}
              >
                {link.name}
              </Link>
            ))}
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
            {navigationLinks.map((link) => (
              <Link
                key={link.name}
                href={link.href}
                className="block px-3 py-2 text-gray-700 hover:text-teal-600 hover:bg-teal-50 rounded-md font-medium"
                onClick={() => setMobileMenuOpen(false)}
              >
                {link.name}
              </Link>
            ))}
            
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