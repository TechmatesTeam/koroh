import { Metadata } from 'next';
import Link from 'next/link';
import { PublicRoute } from '@/components/auth/protected-route';
import { LoginForm } from '@/components/auth/login-form';
import { PublicNavigation } from '@/components/layout/public-navigation';
import { PublicFooter } from '@/components/layout/public-footer';
import { cssClasses } from '@/lib/design-system';

export const metadata: Metadata = {
  title: 'Sign In - Koroh',
  description: 'Sign in to your Koroh account',
};

export default function LoginPage() {
  return (
    <PublicRoute>
      <div className="min-h-screen bg-gradient-to-br from-teal-50 to-blue-50 flex flex-col">
        <PublicNavigation currentPage="login" />
        
        <div className="flex-1 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
          <div className="sm:mx-auto sm:w-full sm:max-w-md">
            <div className="text-center">
              <h2 className={`mt-6 text-3xl ${cssClasses.text.heading}`}>
                Welcome back
              </h2>
              <p className={`mt-2 text-sm ${cssClasses.text.body}`}>
                Sign in to your account to continue
              </p>
              <p className={`mt-4 text-sm ${cssClasses.text.body}`}>
                Don't have an account?{' '}
                <Link href="/auth/register" className={`font-medium ${cssClasses.text.accent} hover:text-teal-500 transition-colors`}>
                  Create one now
                </Link>
              </p>
            </div>
          </div>

          <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
            <div className="bg-white py-8 px-4 shadow-lg sm:rounded-xl sm:px-10 border border-gray-100">
              <LoginForm />
            </div>
          </div>
        </div>
        
        <PublicFooter />
      </div>
    </PublicRoute>
  );
}