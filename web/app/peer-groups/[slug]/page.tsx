'use client';

import React, { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { ProtectedRoute } from '@/components/auth/protected-route';
import { AppLayout } from '@/components/layout/app-layout';
import GroupProfile from '@/components/peer-groups/group-profile';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { PeerGroup } from '@/types/peer-groups';
import { api } from '@/lib/api';
import { useNotifications } from '@/contexts/notification-context';

export default function GroupPage() {
  const params = useParams();
  const router = useRouter();
  const slug = params.slug as string;
  const [group, setGroup] = useState<PeerGroup | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { addNotification } = useNotifications();

  useEffect(() => {
    if (slug) {
      loadGroup();
    }
  }, [slug]);

  const loadGroup = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await api.peerGroups.get(slug);
      setGroup(response.data);
    } catch (err: any) {
      const errorMessage = err.response?.data?.error || 'Failed to load group';
      setError(errorMessage);
      
      if (err.response?.status === 404) {
        addNotification({
          type: 'error',
          title: 'Group Not Found',
          message: 'The requested group could not be found.'
        });
        router.push('/peer-groups');
      } else if (err.response?.status === 403) {
        addNotification({
          type: 'error',
          title: 'Access Denied',
          message: 'You do not have permission to view this group.'
        });
        router.push('/peer-groups');
      } else {
        addNotification({
          type: 'error',
          title: 'Error',
          message: errorMessage
        });
      }
    } finally {
      setLoading(false);
    }
  };

  const handleGroupUpdate = (updatedGroup: PeerGroup) => {
    setGroup(updatedGroup);
  };

  if (loading) {
    return (
      <ProtectedRoute>
        <AppLayout>
          <div className="min-h-screen bg-gray-50 flex items-center justify-center">
            <LoadingSpinner size="lg" />
          </div>
        </AppLayout>
      </ProtectedRoute>
    );
  }

  if (error || !group) {
    return (
      <ProtectedRoute>
        <AppLayout>
          <div className="min-h-screen bg-gray-50 flex items-center justify-center">
            <div className="text-center">
              <div className="text-red-600 mb-4">
                <svg className="w-12 h-12 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  {error || 'Group Not Found'}
                </h3>
                <p className="text-gray-600">
                  The group you're looking for doesn't exist or you don't have access to it.
                </p>
              </div>
              <button
                onClick={() => router.push('/peer-groups')}
                className="text-blue-600 hover:text-blue-700 font-medium"
              >
                ← Back to Peer Groups
              </button>
            </div>
          </div>
        </AppLayout>
      </ProtectedRoute>
    );
  }

  return (
    <ProtectedRoute>
      <AppLayout>
        <div className="min-h-screen bg-gray-50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            {/* Breadcrumb */}
            <nav className="mb-6">
              <ol className="flex items-center space-x-2 text-sm text-gray-500">
                <li>
                  <button
                    onClick={() => router.push('/peer-groups')}
                    className="hover:text-gray-700"
                  >
                    Peer Groups
                  </button>
                </li>
                <li>
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
                  </svg>
                </li>
                <li className="text-gray-900 font-medium">
                  {group.name}
                </li>
              </ol>
            </nav>

            {/* Group Profile */}
            <GroupProfile
              group={group}
              onGroupUpdate={handleGroupUpdate}
            />
          </div>
        </div>
      </AppLayout>
    </ProtectedRoute>
  );
}