'use client';

import React, { useState, useEffect } from 'react';
import { ActivityItem } from '@/types/peer-groups';
import { Avatar } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { Button } from '@/components/ui/button';
import { api } from '@/lib/api';
import { useNotifications } from '@/contexts/notification-context';

interface GroupActivityFeedProps {
  groupSlug?: string; // If provided, shows activity for specific group
  showMyFeed?: boolean; // If true, shows user's activity feed across all groups
  className?: string;
}

const GroupActivityFeed: React.FC<GroupActivityFeedProps> = ({
  groupSlug,
  showMyFeed = false,
  className = ''
}) => {
  const [activities, setActivities] = useState<ActivityItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { addNotification } = useNotifications();

  useEffect(() => {
    loadActivityFeed();
  }, [groupSlug, showMyFeed]);

  const loadActivityFeed = async () => {
    setLoading(true);
    setError(null);
    
    try {
      let response;
      
      if (showMyFeed) {
        response = await api.peerGroups.getMyActivityFeed();
        setActivities(response.data.activity);
      } else if (groupSlug) {
        response = await api.peerGroups.getActivityFeed(groupSlug);
        setActivities(response.data.activity);
      } else {
        setActivities([]);
      }
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to load activity feed');
      addNotification({
        type: 'error',
        title: 'Error',
        message: 'Failed to load activity feed'
      });
    } finally {
      setLoading(false);
    }
  };

  const formatActivityTime = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInMinutes = (now.getTime() - date.getTime()) / (1000 * 60);
    
    if (diffInMinutes < 1) return 'Just now';
    if (diffInMinutes < 60) return `${Math.floor(diffInMinutes)}m ago`;
    
    const diffInHours = diffInMinutes / 60;
    if (diffInHours < 24) return `${Math.floor(diffInHours)}h ago`;
    
    const diffInDays = diffInHours / 24;
    if (diffInDays < 7) return `${Math.floor(diffInDays)}d ago`;
    
    return date.toLocaleDateString();
  };

  const getActivityIcon = (type: string) => {
    switch (type) {
      case 'post':
        return (
          <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
            <svg className="w-4 h-4 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9H5v2h2V9zm8 0h-2v2h2V9zM9 9h2v2H9V9z" clipRule="evenodd" />
            </svg>
          </div>
        );
      case 'comment':
        return (
          <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
            <svg className="w-4 h-4 text-green-600" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 5v8a2 2 0 01-2 2h-5l-5 4v-4H4a2 2 0 01-2-2V5a2 2 0 012-2h12a2 2 0 012 2zM7 8H5v2h2V8zm2 0h2v2H9V8zm6 0h-2v2h2V8z" clipRule="evenodd" />
            </svg>
          </div>
        );
      case 'member_joined':
        return (
          <div className="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center">
            <svg className="w-4 h-4 text-purple-600" fill="currentColor" viewBox="0 0 20 20">
              <path d="M8 9a3 3 0 100-6 3 3 0 000 6zM8 11a6 6 0 016 6H2a6 6 0 016-6zM16 7a1 1 0 10-2 0v1h-1a1 1 0 100 2h1v1a1 1 0 102 0v-1h1a1 1 0 100-2h-1V7z" />
            </svg>
          </div>
        );
      default:
        return (
          <div className="w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center">
            <svg className="w-4 h-4 text-gray-600" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
            </svg>
          </div>
        );
    }
  };

  const getActivityDescription = (activity: ActivityItem) => {
    switch (activity.type) {
      case 'post':
        return (
          <div>
            <span className="font-medium">posted</span> "{activity.content.title}"
            {activity.content.content && (
              <p className="text-sm text-gray-600 mt-1 line-clamp-2">
                {activity.content.content}
              </p>
            )}
            <div className="flex items-center space-x-4 mt-2 text-xs text-gray-500">
              {activity.content.like_count !== undefined && (
                <span>{activity.content.like_count} likes</span>
              )}
              {activity.content.comment_count !== undefined && (
                <span>{activity.content.comment_count} comments</span>
              )}
              {activity.content.post_type && (
                <Badge variant="outline" className="text-xs">
                  {activity.content.post_type}
                </Badge>
              )}
            </div>
          </div>
        );
      
      case 'comment':
        return (
          <div>
            <span className="font-medium">commented on</span> "{activity.content.post_title}"
            {activity.content.comment && (
              <p className="text-sm text-gray-600 mt-1 line-clamp-2">
                {activity.content.comment}
              </p>
            )}
            {activity.content.like_count !== undefined && (
              <div className="mt-2 text-xs text-gray-500">
                {activity.content.like_count} likes
              </div>
            )}
          </div>
        );
      
      case 'member_joined':
        return (
          <div>
            <span className="font-medium">{activity.content.message}</span>
          </div>
        );
      
      default:
        return (
          <div>
            <span className="text-gray-600">Unknown activity</span>
          </div>
        );
    }
  };

  if (loading) {
    return (
      <div className={`flex justify-center py-8 ${className}`}>
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (error) {
    return (
      <div className={`text-center py-8 ${className}`}>
        <p className="text-red-600 mb-4">{error}</p>
        <Button onClick={loadActivityFeed}>
          Try Again
        </Button>
      </div>
    );
  }

  if (activities.length === 0) {
    return (
      <div className={`text-center py-12 ${className}`}>
        <div className="text-gray-400 mb-4">
          <svg className="w-12 h-12 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Activity Yet</h3>
          <p className="text-gray-600">
            {showMyFeed 
              ? "Join some groups and start participating to see activity here."
              : "No recent activity in this group."
            }
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className={className}>
      <div className="space-y-4">
        {activities.map((activity) => (
          <div key={activity.id} className="flex items-start space-x-3 p-4 bg-white border border-gray-200 rounded-lg hover:shadow-sm transition-shadow">
            {/* Activity Icon */}
            <div className="flex-shrink-0">
              {getActivityIcon(activity.type)}
            </div>
            
            {/* Activity Content */}
            <div className="flex-1 min-w-0">
              <div className="flex items-start justify-between">
                <div className="flex items-center space-x-2">
                  <Avatar
                    src={activity.user.profile_picture}
                    alt={activity.user.full_name}
                    size="sm"
                  />
                  <div>
                    <span className="font-medium text-gray-900">
                      {activity.user.full_name}
                    </span>
                    {showMyFeed && activity.group && (
                      <span className="text-sm text-gray-500 ml-2">
                        in {activity.group.name}
                      </span>
                    )}
                  </div>
                </div>
                
                <span className="text-sm text-gray-500 flex-shrink-0">
                  {formatActivityTime(activity.timestamp)}
                </span>
              </div>
              
              <div className="mt-2">
                {getActivityDescription(activity)}
              </div>
            </div>
          </div>
        ))}
      </div>
      
      {/* Load More Button */}
      {activities.length >= 20 && (
        <div className="text-center mt-6">
          <Button variant="outline" onClick={loadActivityFeed}>
            Load More Activity
          </Button>
        </div>
      )}
    </div>
  );
};

export default GroupActivityFeed;