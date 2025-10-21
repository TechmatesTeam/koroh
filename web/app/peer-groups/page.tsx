'use client';

import React from 'react';
import { ProtectedRoute } from '@/components/auth/protected-route';
import { AppLayout } from '@/components/layout/app-layout';
import PeerGroupDiscovery from '@/components/peer-groups/peer-group-discovery';

export default function PeerGroupsPage() {
  return (
    <ProtectedRoute>
      <AppLayout>
        <div className="min-h-screen bg-gray-50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            {/* Page Header */}
            <div className="mb-8">
              <h1 className="text-3xl font-bold text-gray-900">
                Peer Groups
              </h1>
              <p className="mt-2 text-lg text-gray-600">
                Connect with like-minded professionals and expand your network
              </p>
            </div>

            {/* Main Content */}
            <PeerGroupDiscovery />
          </div>
        </div>
      </AppLayout>
    </ProtectedRoute>
  );
}