'use client';

import { useEffect, useState } from 'react';
import { useAuth } from '@/contexts/auth-context';
import { usePeerGroupRealtime } from '@/lib/hooks/use-realtime';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Avatar } from '@/components/ui/avatar';
import { Button } from '@/components/ui/button';
import { 
  MessageSquare, 
  Users, 
  FileText, 
  Clock, 
  Eye,
  ChevronRight,
  Activity
} from 'lucide-react';
import Link from 'next/link';

interface ActivityItem {
  id: string;
  type: 'new_post' | 'new_comment' | 'member_joined';
  timestamp: string;
  author?: {
    id: number;
    name: string;
    profile_picture?: string;
  };
  group?: {
    slug: string;
    name: string;
  };
  content?: {
    title?: string;
    excerpt?: string;
    post_title?: string;
  };
}

interface RealtimeActivityFeedProps {
  groupSlug?: string;
  maxItems?: number;
  showHeader?: boolean;
  className?: string;
}

export function RealtimeActivityFeed({ 
  groupSlug, 
  maxItems = 10, 
  showHeader = true,
  className = '' 
}: RealtimeActivityFeedProps) {
  const { user } = useAuth();
  const [activities, setActivities] = useState<ActivityItem[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [isVisible, setIsVisible] = useState(true);

  const peerGroupRealtime = usePeerGroupRealtime(groupSlug || '', {
    autoConnect: !!user && !!groupSlug,
    onConnect: () => {
      console.log(`Connected to peer group ${groupSlug} real-time updates`);
    }
  });

  useEffect(() => {
    if (!peerGroupRealtime.connection) return;

    const handleNewPost = (postData: any) => {
      const activity: ActivityItem = {
        id: `post-${postData.id}-${Date.now()}`,
        type: 'new_post',
        timestamp: postData.created_at,
        author: postData.author,
        group: {
          slug: groupSlug || '',
          name: postData.group_name || 'Unknown Group'
        },
        content: {
          title: postData.title,
          excerpt: postData.content
        }
      };

      setActivities(prev => [activity, ...prev].slice(0, maxItems));
      setUnreadCount(prev => prev + 1);
    };

    const handleNewComment = (commentData: any) => {
      const activity: ActivityItem = {
        id: `comment-${commentData.id}-${Date.now()}`,
        type: 'new_comment',
        timestamp: commentData.created_at,
        author: commentData.author,
        group: {
          slug: groupSlug || '',
          name: commentData.group_name || 'Unknown Group'
        },
        content: {
          title: commentData.content,
          post_title: commentData.post_title
        }
      };

      setActivities(prev => [activity, ...prev].slice(0, maxItems));
      setUnreadCount(prev => prev + 1);
    };

    const handleMemberJoined = (memberData: any) => {
      const activity: ActivityItem = {
        id: `member-${memberData.id}-${Date.now()}`,
        type: 'member_joined',
        timestamp: memberData.joined_at,
        author: {
          id: memberData.id,
          name: memberData.name,
          profile_picture: memberData.profile_picture
        },
        group: {
          slug: groupSlug || '',
          name: memberData.group_name || 'Unknown Group'
        }
      };

      setActivities(prev => [activity, ...prev].slice(0, maxItems));
      setUnreadCount(prev => prev + 1);
    };

    peerGroupRealtime.on('new_post', handleNewPost);
    peerGroupRealtime.on('new_comment', handleNewComment);
    peerGroupRealtime.on('member_joined', handleMemberJoined);

    return () => {
      peerGroupRealtime.off('new_post', handleNewPost);
      peerGroupRealtime.off('new_comment', handleNewComment);
      peerGroupRealtime.off('member_joined', handleMemberJoined);
    };
  }, [peerGroupRealtime, groupSlug, maxItems]);

  const markAsRead = () => {
    setUnreadCount(0);
  };

  const toggleVisibility = () => {
    setIsVisible(!isVisible);
    if (!isVisible) {
      markAsRead();
    }
  };

  const formatTimeAgo = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffInMinutes = Math.floor((now.getTime() - date.getTime()) / (1000 * 60));
    
    if (diffInMinutes < 1) return 'Just now';
    if (diffInMinutes < 60) return `${diffInMinutes}m ago`;
    if (diffInMinutes < 1440) return `${Math.floor(diffInMinutes / 60)}h ago`;
    return `${Math.floor(diffInMinutes / 1440)}d ago`;
  };

  const getActivityIcon = (type: string) => {
    switch (type) {
      case 'new_post':
        return <FileText className="w-4 h-4 text-blue-600" />;
      case 'new_comment':
        return <MessageSquare className="w-4 h-4 text-green-600" />;
      case 'member_joined':
        return <Users className="w-4 h-4 text-purple-600" />;
      default:
        return <Activity className="w-4 h-4 text-gray-600" />;
    }
  };

  const getActivityText = (activity: ActivityItem) => {
    switch (activity.type) {
      case 'new_post':
        return (
          <span>
            <span className="font-medium">{activity.author?.name}</span> posted{' '}
            <span className="font-medium">"{activity.content?.title}"</span>
          </span>
        );
      case 'new_comment':
        return (
          <span>
            <span className="font-medium">{activity.author?.name}</span> commented on{' '}
            <span className="font-medium">"{activity.content?.post_title}"</span>
          </span>
        );
      case 'member_joined':
        return (
          <span>
            <span className="font-medium">{activity.author?.name}</span> joined the group
          </span>
        );
      default:
        return 'Unknown activity';
    }
  };

  if (!user || !groupSlug) {
    return null;
  }

  return (
    <Card className={className}>
      {showHeader && (
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg flex items-center">
              <Activity className="w-5 h-5 mr-2 text-teal-600" />
              Live Activity
              {unreadCount > 0 && (
                <Badge className="ml-2 bg-red-500 text-white">
                  {unreadCount}
                </Badge>
              )}
            </CardTitle>
            <Button
              variant="ghost"
              size="sm"
              onClick={toggleVisibility}
              className="text-gray-500 hover:text-gray-700"
            >
              {isVisible ? <Eye className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </Button>
          </div>
        </CardHeader>
      )}

      {isVisible && (
        <CardContent className="pt-0">
          {activities.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <Activity className="w-8 h-8 mx-auto mb-2 text-gray-400" />
              <p className="text-sm">No recent activity</p>
              <p className="text-xs">New posts and comments will appear here</p>
            </div>
          ) : (
            <div className="space-y-3">
              {activities.map((activity) => (
                <div
                  key={activity.id}
                  className="flex items-start space-x-3 p-3 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  <div className="flex-shrink-0">
                    {activity.author?.profile_picture ? (
                      <Avatar
                        src={activity.author.profile_picture}
                        alt={activity.author.name}
                        size="sm"
                      />
                    ) : (
                      <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center">
                        {getActivityIcon(activity.type)}
                      </div>
                    )}
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="text-sm text-gray-900">
                      {getActivityText(activity)}
                    </div>
                    
                    {activity.content?.excerpt && (
                      <p className="text-xs text-gray-600 mt-1 line-clamp-2">
                        {activity.content.excerpt}
                      </p>
                    )}
                    
                    <div className="flex items-center justify-between mt-2">
                      <div className="flex items-center text-xs text-gray-500">
                        <Clock className="w-3 h-3 mr-1" />
                        {formatTimeAgo(activity.timestamp)}
                      </div>
                      
                      {groupSlug && (
                        <Link
                          href={`/peer-groups/${groupSlug}`}
                          className="text-xs text-teal-600 hover:text-teal-700 flex items-center"
                        >
                          View
                          <ChevronRight className="w-3 h-3 ml-1" />
                        </Link>
                      )}
                    </div>
                  </div>
                </div>
              ))}

              {unreadCount > 0 && (
                <div className="text-center pt-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={markAsRead}
                    className="text-teal-600 hover:text-teal-700"
                  >
                    Mark all as read
                  </Button>
                </div>
              )}
            </div>
          )}
        </CardContent>
      )}
    </Card>
  );
}

interface ActivitySummaryProps {
  activities: ActivityItem[];
  className?: string;
}

export function ActivitySummary({ activities, className = '' }: ActivitySummaryProps) {
  const postCount = activities.filter(a => a.type === 'new_post').length;
  const commentCount = activities.filter(a => a.type === 'new_comment').length;
  const memberCount = activities.filter(a => a.type === 'member_joined').length;

  return (
    <div className={`flex items-center space-x-4 text-sm text-gray-600 ${className}`}>
      {postCount > 0 && (
        <div className="flex items-center">
          <FileText className="w-4 h-4 mr-1 text-blue-600" />
          {postCount} post{postCount !== 1 ? 's' : ''}
        </div>
      )}
      {commentCount > 0 && (
        <div className="flex items-center">
          <MessageSquare className="w-4 h-4 mr-1 text-green-600" />
          {commentCount} comment{commentCount !== 1 ? 's' : ''}
        </div>
      )}
      {memberCount > 0 && (
        <div className="flex items-center">
          <Users className="w-4 h-4 mr-1 text-purple-600" />
          {memberCount} new member{memberCount !== 1 ? 's' : ''}
        </div>
      )}
    </div>
  );
}