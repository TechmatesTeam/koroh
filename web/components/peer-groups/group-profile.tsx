'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { PeerGroup, ActivityItem } from '@/types/peer-groups';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Avatar } from '@/components/ui/avatar';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { api } from '@/lib/api';
import { useNotifications } from '@/contexts/notification-context';
import GroupMemberList from './group-member-list';
import GroupPosts from './group-posts';
import GroupActivityFeed from './group-activity-feed';

interface GroupProfileProps {
  group: PeerGroup;
  onGroupUpdate?: (group: PeerGroup) => void;
  className?: string;
}

const GroupProfile: React.FC<GroupProfileProps> = ({
  group: initialGroup,
  onGroupUpdate,
  className = ''
}) => {
  const [group, setGroup] = useState(initialGroup);
  const [activeTab, setActiveTab] = useState<'about' | 'posts' | 'members' | 'activity'>('about');
  const [activityFeed, setActivityFeed] = useState<ActivityItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [joinLoading, setJoinLoading] = useState(false);
  const { addNotification } = useNotifications();

  useEffect(() => {
    if (activeTab === 'activity') {
      loadActivityFeed();
    }
  }, [activeTab, group.slug]);

  const loadActivityFeed = async () => {
    setLoading(true);
    try {
      const response = await api.peerGroups.getActivityFeed(group.slug);
      setActivityFeed(response.data.activity);
    } catch (err: any) {
      console.error('Failed to load activity feed:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleJoinGroup = async () => {
    setJoinLoading(true);
    try {
      const response = await api.peerGroups.join(group.slug);
      const newStatus = response.data.status;
      
      const updatedGroup = {
        ...group,
        membership_status: newStatus,
        is_member: newStatus === 'active',
        member_count: newStatus === 'active' ? group.member_count + 1 : group.member_count
      };
      
      setGroup(updatedGroup);
      if (onGroupUpdate) {
        onGroupUpdate(updatedGroup);
      }
      
      addNotification({
        type: 'success',
        title: 'Success',
        message: response.data.message
      });
    } catch (error: any) {
      addNotification({
        type: 'error',
        title: 'Error',
        message: error.response?.data?.error || 'Failed to join group'
      });
    } finally {
      setJoinLoading(false);
    }
  };

  const handleLeaveGroup = async () => {
    if (!confirm('Are you sure you want to leave this group?')) return;
    
    setJoinLoading(true);
    try {
      await api.peerGroups.leave(group.slug);
      
      const updatedGroup = {
        ...group,
        membership_status: 'left' as const,
        is_member: false,
        member_count: group.member_count - 1
      };
      
      setGroup(updatedGroup);
      if (onGroupUpdate) {
        onGroupUpdate(updatedGroup);
      }
      
      addNotification({
        type: 'success',
        title: 'Success',
        message: 'Successfully left the group'
      });
    } catch (error: any) {
      addNotification({
        type: 'error',
        title: 'Error',
        message: error.response?.data?.error || 'Failed to leave group'
      });
    } finally {
      setJoinLoading(false);
    }
  };

  const getJoinButtonText = () => {
    if (group.is_member) return 'Leave Group';
    if (group.membership_status === 'pending') return 'Pending Approval';
    if (group.membership_status === 'invited') return 'Accept Invitation';
    if (group.privacy_level === 'public') return 'Join Group';
    return 'Request to Join';
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  const formatActivityTime = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60);
    
    if (diffInHours < 1) return 'Just now';
    if (diffInHours < 24) return `${Math.floor(diffInHours)}h ago`;
    if (diffInHours < 168) return `${Math.floor(diffInHours / 24)}d ago`;
    return date.toLocaleDateString();
  };

  return (
    <div className={`max-w-4xl mx-auto ${className}`}>
      {/* Header */}
      <div className="bg-white border border-gray-200 rounded-lg overflow-hidden mb-6">
        {/* Cover Image */}
        {group.cover_image && (
          <div className="h-48 bg-gradient-to-r from-blue-500 to-purple-600">
            <img
              src={group.cover_image}
              alt={`${group.name} cover`}
              className="w-full h-full object-cover"
            />
          </div>
        )}
        
        <div className="p-6">
          <div className="flex items-start justify-between">
            <div className="flex items-start space-x-4">
              {/* Group Image */}
              <div className="flex-shrink-0">
                {group.image ? (
                  <img
                    src={group.image}
                    alt={group.name}
                    className="w-20 h-20 rounded-lg object-cover border-4 border-white -mt-10 relative z-10"
                  />
                ) : (
                  <div className="w-20 h-20 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center border-4 border-white -mt-10 relative z-10">
                    <span className="text-white font-bold text-2xl">
                      {group.name.charAt(0).toUpperCase()}
                    </span>
                  </div>
                )}
              </div>
              
              {/* Group Info */}
              <div className="flex-1">
                <h1 className="text-2xl font-bold text-gray-900">
                  {group.name}
                </h1>
                {group.tagline && (
                  <p className="text-gray-600 mt-1">
                    {group.tagline}
                  </p>
                )}
                
                <div className="flex flex-wrap gap-2 mt-3">
                  <Badge className={
                    group.privacy_level === 'public' ? 'bg-green-100 text-green-800' :
                    group.privacy_level === 'private' ? 'bg-red-100 text-red-800' :
                    'bg-yellow-100 text-yellow-800'
                  }>
                    {group.privacy_level}
                  </Badge>
                  <Badge className="bg-blue-100 text-blue-800">
                    {group.group_type.replace('_', ' ')}
                  </Badge>
                  {group.industry && (
                    <Badge variant="outline">
                      {group.industry}
                    </Badge>
                  )}
                </div>
                
                <div className="flex items-center space-x-4 mt-3 text-sm text-gray-500">
                  <span>{group.member_count} members</span>
                  <span>{group.post_count} posts</span>
                  <span>Created {formatDate(group.created_at)}</span>
                </div>
              </div>
            </div>
            
            {/* Action Buttons */}
            <div className="flex space-x-2">
              {!group.is_member ? (
                <Button
                  onClick={handleJoinGroup}
                  disabled={joinLoading || group.membership_status === 'pending'}
                  className="min-w-[120px]"
                >
                  {joinLoading ? 'Processing...' : getJoinButtonText()}
                </Button>
              ) : (
                <Button
                  variant="outline"
                  onClick={handleLeaveGroup}
                  disabled={joinLoading}
                  className="text-red-600 hover:text-red-700"
                >
                  {joinLoading ? 'Processing...' : 'Leave Group'}
                </Button>
              )}
              
              {group.is_admin && (
                <Link href={`/peer-groups/${group.slug}/manage`}>
                  <Button variant="outline">
                    Manage Group
                  </Button>
                </Link>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="mb-6">
        <nav className="flex space-x-8">
          <button
            onClick={() => setActiveTab('about')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'about'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            About
          </button>
          <button
            onClick={() => setActiveTab('posts')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'posts'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            Posts ({group.post_count})
          </button>
          <button
            onClick={() => setActiveTab('members')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'members'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            Members ({group.member_count})
          </button>
          <button
            onClick={() => setActiveTab('activity')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'activity'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            Activity
          </button>
        </nav>
      </div>

      {/* Tab Content */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        {activeTab === 'about' && (
          <div className="space-y-6">
            {/* Description */}
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-3">About</h3>
              <p className="text-gray-700 whitespace-pre-wrap">
                {group.description}
              </p>
            </div>

            {/* Skills */}
            {group.skills && group.skills.length > 0 && (
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-3">Relevant Skills</h3>
                <div className="flex flex-wrap gap-2">
                  {group.skills.map((skill, index) => (
                    <Badge key={index} variant="secondary">
                      {skill}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {/* Group Details */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h4 className="font-medium text-gray-900 mb-2">Group Details</h4>
                <dl className="space-y-2 text-sm">
                  {group.industry && (
                    <>
                      <dt className="text-gray-500">Industry</dt>
                      <dd className="text-gray-900">{group.industry}</dd>
                    </>
                  )}
                  {group.experience_level && (
                    <>
                      <dt className="text-gray-500">Experience Level</dt>
                      <dd className="text-gray-900">{group.experience_level}</dd>
                    </>
                  )}
                  {group.location && (
                    <>
                      <dt className="text-gray-500">Location</dt>
                      <dd className="text-gray-900">{group.location}</dd>
                    </>
                  )}
                  {group.max_members && (
                    <>
                      <dt className="text-gray-500">Maximum Members</dt>
                      <dd className="text-gray-900">{group.max_members}</dd>
                    </>
                  )}
                </dl>
              </div>

              <div>
                <h4 className="font-medium text-gray-900 mb-2">Created By</h4>
                <div className="flex items-center space-x-3">
                  <Avatar
                    src={group.created_by.profile_picture}
                    alt={group.created_by.full_name}
                    size="sm"
                  />
                  <div>
                    <p className="text-sm font-medium text-gray-900">
                      {group.created_by.full_name}
                    </p>
                    <p className="text-xs text-gray-500">
                      {formatDate(group.created_at)}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Rules */}
            {group.rules && (
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-3">Group Rules</h3>
                <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                  <p className="text-gray-700 whitespace-pre-wrap">
                    {group.rules}
                  </p>
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'posts' && (
          <GroupPosts
            groupSlug={group.slug}
            canPost={group.is_member}
          />
        )}

        {activeTab === 'members' && (
          <GroupMemberList
            groupSlug={group.slug}
            isAdmin={group.is_admin}
          />
        )}

        {activeTab === 'activity' && (
          <GroupActivityFeed groupSlug={group.slug} />
        )}
      </div>
    </div>
  );
};

export default GroupProfile;