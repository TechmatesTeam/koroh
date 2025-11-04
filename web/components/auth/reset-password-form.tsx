'use client';

import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import Link from 'next/link';
import { useNotifications } from '@/contexts/notification-context';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { api } from '@/lib/api';

const resetPasswordSchema = z.object({
  password: z.string()
    .min(8, 'Password must be at least 8 characters')
    .regex(/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/, 'Password must contain at least one uppercase letter, one lowercase letter, and one number'),
  confirmPassword: z.string(),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords don't match",
  path: ["confirmPassword"],
});

type ResetPasswordFormData = z.infer<typeof resetPasswordSchema>;

export function ResetPasswordForm() {
  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [token, setToken] = useState<string>('');
  const router = useRouter();
  const searchParams = useSearchParams();
  const { addNotification } = useNotifications();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ResetPasswordFormData>({
    resolver: zodResolver(resetPasswordSchema),
  });

  useEffect(() => {
    const tokenFromUrl = searchParams.get('token');
    if (tokenFromUrl) {
      setToken(tokenFromUrl);
    } else {
      addNotification({
        type: 'error',
        title: 'Invalid reset link',
        message: 'This reset link is invalid or has expired.',
      });
      router.replace('/auth/forgot-password');
    }
  }, [searchParams, router, addNotification]);

  const onSubmit = async (data: ResetPasswordFormData) => {
    if (!token) {
      addNotification({
        type: 'error',
        title: 'Invalid token',
        message: 'Reset token is missing or invalid.',
      });
      return;
    }

    setIsLoading(true);
    try {
      await api.auth.resetPassword(token, data.password);
      
      setIsSuccess(true);
      addNotification({
        type: 'success',
        title: 'Password reset successful',
        message: 'Your password has been reset successfully. You can now sign in with your new password.',
      });

      // Redirect to login after 3 seconds
      setTimeout(() => {
        router.replace('/auth/login');
      }, 3000);
    } catch (error: any) {
      addNotification({
        type: 'error',
        title: 'Reset failed',
        message: error.message || 'Failed to reset password. Please try again.',
      });
    } finally {
      setIsLoading(false);
    }
  };

  if (isSuccess) {
    return (
      <div className="space-y-6">
        <div className="text-center">
          <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-green-100">
            <svg className="h-6 w-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h3 className="mt-4 text-lg font-medium text-gray-900">Password reset successful</h3>
          <p className="mt-2 text-sm text-gray-600">
            Your password has been reset successfully. You will be redirected to the sign in page shortly.
          </p>
        </div>

        <div className="text-center">
          <Button
            onClick={() => router.replace('/auth/login')}
            className="bg-teal-600 hover:bg-teal-700 font-medium"
          >
            Sign in now
          </Button>
        </div>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <div>
        <Label htmlFor="password">New password</Label>
        <Input
          id="password"
          type="password"
          autoComplete="new-password"
          {...register('password')}
          className="mt-1"
          placeholder="Enter your new password"
        />
        {errors.password && (
          <p className="mt-1 text-sm text-red-600">{errors.password.message}</p>
        )}
        <p className="mt-1 text-xs text-gray-500">
          Password must be at least 8 characters with uppercase, lowercase, and number.
        </p>
      </div>

      <div>
        <Label htmlFor="confirmPassword">Confirm new password</Label>
        <Input
          id="confirmPassword"
          type="password"
          autoComplete="new-password"
          {...register('confirmPassword')}
          className="mt-1"
          placeholder="Confirm your new password"
        />
        {errors.confirmPassword && (
          <p className="mt-1 text-sm text-red-600">{errors.confirmPassword.message}</p>
        )}
      </div>

      <Button
        type="submit"
        disabled={isLoading || !token}
        className="w-full bg-teal-600 hover:bg-teal-700 font-medium"
      >
        {isLoading ? 'Resetting password...' : 'Reset password'}
      </Button>

      <div className="text-center">
        <p className="text-sm text-gray-600">
          Remember your password?{' '}
          <Link href="/auth/login" className="font-medium text-teal-600 hover:text-teal-500 transition-colors">
            Sign in
          </Link>
        </p>
      </div>
    </form>
  );
}