import { Metadata } from 'next';
import Link from 'next/link';
import { RedirectIfAuthenticated } from '@/components/auth/redirect-if-authenticated';
import { ResetPasswordForm } from '@/components/auth/reset-password-form';
import { PublicNavigation } from '@/components/layout/public-navigation';
import { PublicFooter } from '@/components/layout/public-footer';
import { cssClasses } from '@/lib/design-system';

export const metadata: Metadata = {
  title: 'Reset Password - Koroh',
  description: 'Set a new password for your Koroh account',
};

export default function ResetPasswordPage() {
  return (
    <RedirectIfAuthenticated>
      <div className="min-h-screen bg-gradient-to-br from-teal-50 to-blue-50 flex flex-col">
        <PublicNavigation />
        
        <div className="flex-1 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
          <div className="sm:mx-auto sm:w-full sm:max-w-md">
            <div className="text-center">
              <h2 className={`mt-6 text-3xl ${cssClasses.text.heading}`}>
                Reset your password
              </h2>
              <p className={`mt-2 text-sm ${cssClasses.text.body}`}>
                Enter your new password below.
              </p>
              <p className={`mt-4 text-sm ${cssClasses.text.body}`}>
                Remember your password?{' '}
                <Link href="/auth/login" className={`font-medium ${cssClasses.text.accent} hover:text-teal-500 transition-colors`}>
                  Sign in here
                </Link>
              </p>
            </div>
          </div>

          <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
            <div className="bg-white py-8 px-4 shadow-lg sm:rounded-xl sm:px-10 border border-gray-100">
              <ResetPasswordForm />
            </div>
          </div>
        </div>
        
        <PublicFooter />
      </div>
    </RedirectIfAuthenticated>
  );
}