'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import Link from 'next/link';
import { useAuth } from '@/contexts/auth-context';
import { useNotifications } from '@/contexts/notification-context';
import { getErrorMessage, logError, isAuthError } from '@/lib/error-handler';
import { LoadingButton } from '@/components/ui/loading-spinner';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { AlertCircle } from 'lucide-react';

const loginSchema = z.object({
  email: z.string().email('Please enter a valid email address'),
  password: z.string().min(1, 'Password is required'),
});

type LoginFormData = z.infer<typeof loginSchema>;

export function LoginForm() {
  const [isLoading, setIsLoading] = useState(false);
  const [serverError, setServerError] = useState<string | null>(null);
  const { login, error: authError, clearError } = useAuth();
  const { addNotification } = useNotifications();

  const {
    register,
    handleSubmit,
    formState: { errors },
    setError,
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  });

  const onSubmit = async (data: LoginFormData) => {
    setIsLoading(true);
    setServerError(null);
    clearError();
    
    try {
      await login(data);
      addNotification({
        type: 'success',
        title: 'Welcome back!',
        message: 'You have successfully signed in.',
      });
    } catch (error: any) {
      logError(error, 'Login form');
      const errorMessage = getErrorMessage(error);
      
      // Handle verification required error
      if (error.verification_required) {
        setServerError(`Please verify your email address before logging in. Check your inbox at ${error.email || 'your email'}.`);
        addNotification({
          type: 'warning',
          title: 'Email verification required',
          message: 'Please check your email and click the verification link to activate your account.',
        });
        return;
      }
      
      // Handle specific error types
      if (error.code === 'INVALID_CREDENTIALS') {
        setError('email', { message: 'Invalid email or password' });
        setError('password', { message: 'Invalid email or password' });
      } else if (error.code === 'ACCOUNT_NOT_VERIFIED') {
        setServerError('Your account is not verified. Please check your email for verification instructions.');
      } else if (error.code === 'VALIDATION_ERROR') {
        // Handle field-specific validation errors
        if (error.details?.email) {
          setError('email', { message: Array.isArray(error.details.email) ? error.details.email[0] : error.details.email });
        }
        if (error.details?.password) {
          setError('password', { message: Array.isArray(error.details.password) ? error.details.password[0] : error.details.password });
        }
      } else {
        setServerError(errorMessage);
      }
      
      addNotification({
        type: 'error',
        title: 'Sign in failed',
        message: errorMessage,
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      {/* Server Error Display */}
      {(serverError || authError) && (
        <div className="rounded-md bg-red-50 p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <AlertCircle className="h-5 w-5 text-red-400" />
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">
                Sign in failed
              </h3>
              <div className="mt-2 text-sm text-red-700">
                {serverError || authError}
              </div>
            </div>
          </div>
        </div>
      )}

      <div>
        <Label htmlFor="email">Email address</Label>
        <Input
          id="email"
          type="email"
          autoComplete="email"
          {...register('email')}
          className={`mt-1 ${errors.email ? 'border-red-300 focus:border-red-500 focus:ring-red-500' : ''}`}
          disabled={isLoading}
        />
        {errors.email && (
          <p className="mt-1 text-sm text-red-600 flex items-center">
            <AlertCircle className="h-4 w-4 mr-1" />
            {errors.email.message}
          </p>
        )}
      </div>

      <div>
        <Label htmlFor="password">Password</Label>
        <Input
          id="password"
          type="password"
          autoComplete="current-password"
          {...register('password')}
          className={`mt-1 ${errors.password ? 'border-red-300 focus:border-red-500 focus:ring-red-500' : ''}`}
          disabled={isLoading}
        />
        {errors.password && (
          <p className="mt-1 text-sm text-red-600 flex items-center">
            <AlertCircle className="h-4 w-4 mr-1" />
            {errors.password.message}
          </p>
        )}
      </div>

      <div className="flex items-center justify-between">
        <div className="flex items-center">
          <input
            id="remember-me"
            name="remember-me"
            type="checkbox"
            className="h-4 w-4 text-teal-600 focus:ring-teal-500 border-gray-300 rounded"
            disabled={isLoading}
          />
          <label htmlFor="remember-me" className="ml-2 block text-sm text-gray-900">
            Remember me
          </label>
        </div>

        <div className="text-sm">
          <Link 
            href="/auth/forgot-password" 
            className="font-medium text-teal-600 hover:text-teal-500 transition-colors"
            tabIndex={isLoading ? -1 : 0}
          >
            Forgot your password?
          </Link>
        </div>
      </div>

      <LoadingButton
        type="submit"
        loading={isLoading}
        className="w-full bg-teal-600 hover:bg-teal-700 font-medium py-2 px-4 rounded-md text-white"
      >
        Sign in
      </LoadingButton>
    </form>
  );
}