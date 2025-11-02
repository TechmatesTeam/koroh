'use client';

import { ProtectedRoute } from '@/components/auth/protected-route';
import { AppLayout } from '@/components/layout/app-layout';
import { FullScreenAIChat } from '@/components/ai-chat';

export default function AIChatPage() {
  return (
    <ProtectedRoute>
      <AppLayout>
        <div className="min-h-screen bg-gray-50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            {/* Page Header */}
            <div className="mb-8">
              <h1 className="text-3xl font-bold text-gray-900">
                Koroh AI Assistant
              </h1>
              <p className="mt-2 text-lg text-gray-600">
                Your intelligent career companion - get personalized advice, analyze your CV, and discover opportunities
              </p>
            </div>

            {/* Main Content */}
            <FullScreenAIChat />
          </div>
        </div>
      </AppLayout>
    </ProtectedRoute>
  );
}
