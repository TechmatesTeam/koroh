'use client';

import React from 'react';
import { PeerGroup } from '@/types/peer-groups';
import PeerGroupCard from './peer-group-card';
import { LoadingSpinner } from '@/components/ui/loading-spinner';

interface PeerGroupListProps {
  groups: PeerGroup[];
  loading?: boolean;
  error?: string;
  emptyMessage?: string;
  onJoinSuccess?: (group: PeerGroup) => void;
  showJoinButton?: boolean;
  className?: string;
}

const PeerGroupList: React.FC<PeerGroupListProps> = ({
  groups,
  loading = false,
  error,
  emptyMessage = "No peer groups found.",
  onJoinSuccess,
  showJoinButton = true,
  className = ''
}) => {
  if (loading) {
    return (
      <div className={`flex justify-center items-center py-12 ${className}`}>
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (error) {
    return (
      <div className={`text-center py-12 ${className}`}>
        <div className="text-red-600 mb-4">
          <svg className="w-12 h-12 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <h3 className="text-lg font-medium text-gray-900 mb-2">Error Loading Groups</h3>
          <p className="text-gray-600">{error}</p>
        </div>
      </div>
    );
  }

  if (!groups || groups.length === 0) {
    return (
      <div className={`text-center py-12 ${className}`}>
        <div className="text-gray-400 mb-4">
          <svg className="w-12 h-12 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
          </svg>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Groups Found</h3>
          <p className="text-gray-600">{emptyMessage}</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`space-y-4 ${className}`}>
      {groups.map((group) => (
        <PeerGroupCard
          key={group.id}
          group={group}
          onJoinSuccess={onJoinSuccess}
          showJoinButton={showJoinButton}
        />
      ))}
    </div>
  );
};

export default PeerGroupList;