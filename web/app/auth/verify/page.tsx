'use client';

import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { useAuth } from '@/contexts/auth-context';
import { useNotifications } from '@/contexts/notification-context';

export default function VerifyEmailPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { login } = useAuth();
  const { addNotification } = useNotifications();
  
  const [isVerifying, setIsVerifying] = useState(false);
  const [verificationStatus, setVerificationStatus] = useState<'pending' | 'success' | 'error'>('pending');
  const [errorMessage, setErrorMessage] = useState('');
  const [isExpired, setIsExpired] = useState(false);
  const [userEmail, setUserEmail] = useState('');

  const token = searchParams.get('token');

  useEffect(() => {
    if (token) {
      verifyEmail(token);
    } else {
      setVerificationStatus('error');
      setErrorMessage('Invalid verification link. No token provided.');
    }
  }, [token]);

  const verifyEmail = async (verificationToken: string) => {
    setIsVerifying(true);
    
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/verify-email/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          token: verificationToken,
        }),
      });

      const data = await response.json();

      if (response.ok) {
        setVerificationStatus('success');
        
        // Auto-login the user with the returned tokens
        if (data.tokens) {
          localStorage.setItem('access_token', data.tokens.access);
          localStorage.setItem('refresh_token', data.tokens.refresh);
          
          // Update auth context
          login(data.user, data.tokens);
          
          addNotification({
            type: 'success',
            title: 'Email Verified',
            message: 'Email verified successfully! Welcome to Koroh.'
          });
          
          // Redirect to dashboard after a short delay
          setTimeout(() => {
            router.replace('/dashboard');
          }, 2000);
        }
      } else {
        setVerificationStatus('error');
        setErrorMessage(data.error || 'Email verification failed.');
        setIsExpired(data.expired || false);
      }
    } catch (error) {
      console.error('Email verification error:', error);
      setVerificationStatus('error');
      setErrorMessage('Network error. Please try again.');
    } finally {
      setIsVerifying(false);
    }
  };

  const resendVerification = async () => {
    if (!userEmail) {
      const email = prompt('Please enter your email address:');
      if (!email) return;
      setUserEmail(email);
    }

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/resend-verification/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: userEmail,
        }),
      });

      const data = await response.json();

      if (response.ok) {
        addNotification({
          type: 'success',
          title: 'Email Sent',
          message: 'Verification email sent! Please check your inbox.'
        });
      } else {
        addNotification({
          type: 'error',
          title: 'Error',
          message: data.error || 'Failed to resend verification email.'
        });
      }
    } catch (error) {
      console.error('Resend verification error:', error);
      addNotification({
        type: 'error',
        title: 'Network Error',
        message: 'Network error. Please try again.'
      });
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <h2 className="mt-6 text-3xl font-extrabold text-gray-900">
            Email Verification
          </h2>
        </div>

        <Card className="p-8">
          {verificationStatus === 'pending' && (
            <div className="text-center">
              <LoadingSpinner size="lg" />
              <p className="mt-4 text-gray-600">
                {isVerifying ? 'Verifying your email...' : 'Processing verification...'}
              </p>
            </div>
          )}

          {verificationStatus === 'success' && (
            <div className="text-center">
              <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-green-100 mb-4">
                <svg
                  className="h-6 w-6 text-green-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M5 13l4 4L19 7"
                  />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                Email Verified Successfully!
              </h3>
              <p className="text-gray-600 mb-4">
                Your email has been verified. You're being redirected to your dashboard...
              </p>
              <LoadingSpinner size="sm" />
            </div>
          )}

          {verificationStatus === 'error' && (
            <div className="text-center">
              <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100 mb-4">
                <svg
                  className="h-6 w-6 text-red-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                Verification Failed
              </h3>
              <p className="text-red-600 mb-4">{errorMessage}</p>
              
              {isExpired && (
                <div className="space-y-4">
                  <p className="text-gray-600">
                    Your verification link has expired. Click below to request a new one.
                  </p>
                  <Button
                    onClick={resendVerification}
                    className="w-full"
                  >
                    Resend Verification Email
                  </Button>
                </div>
              )}
              
              <div className="mt-4 space-y-2">
                <Button
                  onClick={() => router.push('/auth/login')}
                  variant="outline"
                  className="w-full"
                >
                  Go to Login
                </Button>
                <Button
                  onClick={() => router.push('/')}
                  variant="ghost"
                  className="w-full"
                >
                  Back to Home
                </Button>
              </div>
            </div>
          )}
        </Card>

        <div className="text-center">
          <p className="text-sm text-gray-600">
            Need help?{' '}
            <a
              href="mailto:support@koroh.com"
              className="font-medium text-indigo-600 hover:text-indigo-500"
            >
              Contact Support
            </a>
          </p>
        </div>
      </div>
    </div>
  );
}