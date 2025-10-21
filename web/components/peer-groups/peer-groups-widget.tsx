'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { PeerGroup, ActivityItem } from '@/types/peer-groups';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Avatar } from '@/components/ui/avatar';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { api } from '@/lib/api';

interface PeerGroupsWidgetProps {
  className?: string;
}

const PeerGroupsWidget: React.FC<PeerGroupsWidgetProps> = ({
  className = ''
}) => {
  const [myGroups, setMyGroups] = useState<PeerGroup[]>([]);
  const [recentActivity, setRecentActivity] = useState<ActivityItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Load user's groups and activity feed in parallel
      const [groupsResponse, activityResponse] = await Promise.all([
        api.peerGroups.myGroups(),
        api.peerGroups.getMyActivityFeed()
      ]);
      
      setMyGroups(groupsResponse.data.slice(0, 3)); // Show top 3 groups
      setRecentActivity(activityResponse.data.activity.slice(0, 5)); // Show 5 recent activities
    } catch (err: any) {
      setError('Failed to load peer groups data');
      console.error('Error loading peer groups data:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatActivityTime = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60);
    
    if (diffInHours < 1) return 'Just now';
    if (diffInHours < 24) return `${Math.floor(diffInHours)}h ago`;
    return `${Math.floor(diffInHours / 24)}d ago`;
  };

  if (loading) {
    return (
      <div className={`bg-white border border-gray-200 rounded-lg p-6 ${className}`}>
        <div className="flex justify-center py-8">
          <LoadingSpinner size="md" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`bg-white border border-gray-200 rounded-lg p-6 ${className}`}>
        <div className="text-center py-8">
          <p className="text-red-600 text-sm">{error}</p>
          <Button size="sm" onClick={loadData} className="mt-2">
            Try Again
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white border border-gray-200 rounded-lg p-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-medium text-gray-900">Peer Groups</h3>
        <Link href="/peer-groups">
          <Button variant="ghost" size="sm">
            View All
          </Button>
        </Link>
      </div>

      {/* My Groups */}
      {myGroups.length > 0 && (
        <div className="mb-6">
          <h4 className="text-sm font-medium text-gray-700 mb-3">My Groups</h4>
          <div className="space-y-3">
            {myGroups.map((group) => (
              <Link
                key={group.id}
                href={`/peer-groups/${group.slug}`}
                className="flex items-center space-x-3 p-2 rounded-lg hover:bg-gray-50 transition-colors"
              >
                {group.image ? (
                  <img
                    src={group.image}
                    alt={group.name}
                    className="w-8 h-8 rounded object-cover"
                  />
                ) : (
                  <div className="w-8 h-8 rounded bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
                    <span className="text-white font-bold text-xs">
                      {group.name.charAt(0).toUpperCase()}
                    </span>
                  </div>
                )}
                
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">
                    {group.name}
                  </p>
                  <p className="text-xs text-gray-500">
                    {group.member_count} members
                  </p>
                </div>
                
                {group.activity_score > 80 && (
                  <Badge variant="secondary" className="text-xs">
                    Active
                  </Badge>
                )}
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* Recent Activity */}
      {recentActivity.length > 0 && (
        <div>
          <h4 className="text-sm font-medium text-gray-700 mb-3">Recent Activity</h4>
          <div className="space-y-3">
            {recentActivity.map((activity) => (
              <div key={activity.id} className="flex items-start space-x-2">
                <Avatar
                  src={activity.user.profile_picture}
                  alt={activity.user.full_name}
                  size="sm"
                />
                
                <div className="flex-1 min-w-0">
                  <div className="text-xs text-gray-600">
                    <span className="font-medium">{activity.user.full_name}</span>
                    {activity.type === 'post' && (
                      <span> posted in </span>
                    )}
                    {activity.type === 'comment' && (
                      <span> commented in </span>
                    )}
                    {activity.type === 'member_joined' && (
                      <span> joined </span>
                    )}
                    {activity.group && (
                      <Link
                        href={`/peer-groups/${activity.group.slug}`}
                        className="font-medium text-blue-600 hover:text-blue-700"
                      >
                        {activity.group.name}
                      </Link>
                    )}
                  </div>
                  
                  {activity.content.title && (
                    <p className="text-xs text-gray-500 mt-1 truncate">
                      "{activity.content.title}"
                    </p>
                  )}
                  
                  <p className="text-xs text-gray-400 mt-1">
                    {formatActivityTime(activity.timestamp)}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Empty State */}
      {myGroups.length === 0 && recentActivity.length === 0 && (
        <div className="text-center py-8">
          <div className="text-gray-400 mb-4">
            <svg className="w-8 h-8 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
            <p className="text-sm text-gray-600">No peer groups yet</p>
          </div>
          <Link href="/peer-groups">
            <Button size="sm">
              Discover Groups
            </Button>
          </Link>
        </div>
      )}
    </div>
  );
};

export default PeerGroupsWidget;