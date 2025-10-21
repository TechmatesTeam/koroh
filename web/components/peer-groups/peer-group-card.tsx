'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { PeerGroup } from '@/types/peer-groups';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Avatar } from '@/components/ui/avatar';
import { api } from '@/lib/api';
import { useNotifications } from '@/contexts/notification-context';

interface PeerGroupCardProps {
  group: PeerGroup;
  onJoinSuccess?: (group: PeerGroup) => void;
  showJoinButton?: boolean;
  className?: string;
}

const PeerGroupCard: React.FC<PeerGroupCardProps> = ({
  group,
  onJoinSuccess,
  showJoinButton = true,
  className = ''
}) => {
  const [isJoining, setIsJoining] = useState(false);
  const [membershipStatus, setMembershipStatus] = useState(group.membership_status);
  const [isMember, setIsMember] = useState(group.is_member);
  const { addNotification } = useNotifications();

  const handleJoinGroup = async () => {
    if (isJoining || isMember) return;

    setIsJoining(true);
    try {
      const response = await api.peerGroups.join(group.slug);
      const newStatus = response.data.status;
      
      setMembershipStatus(newStatus);
      setIsMember(newStatus === 'active');
      
      addNotification({
        type: 'success',
        title: 'Success',
        message: response.data.message
      });

      if (onJoinSuccess) {
        onJoinSuccess({ ...group, membership_status: newStatus, is_member: newStatus === 'active' });
      }
    } catch (error: any) {
      addNotification({
        type: 'error',
        title: 'Error',
        message: error.response?.data?.error || 'Failed to join group'
      });
    } finally {
      setIsJoining(false);
    }
  };

  const getPrivacyBadgeColor = (privacy: string) => {
    switch (privacy) {
      case 'public': return 'bg-green-100 text-green-800';
      case 'private': return 'bg-red-100 text-red-800';
      case 'restricted': return 'bg-yellow-100 text-yellow-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getGroupTypeBadgeColor = (type: string) => {
    switch (type) {
      case 'industry': return 'bg-blue-100 text-blue-800';
      case 'skill': return 'bg-purple-100 text-purple-800';
      case 'location': return 'bg-orange-100 text-orange-800';
      case 'experience': return 'bg-indigo-100 text-indigo-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getJoinButtonText = () => {
    if (isMember) return 'Joined';
    if (membershipStatus === 'pending') return 'Pending Approval';
    if (membershipStatus === 'invited') return 'Accept Invitation';
    if (group.privacy_level === 'public') return 'Join Group';
    return 'Request to Join';
  };

  const getJoinButtonVariant = () => {
    if (isMember) return 'outline';
    if (membershipStatus === 'pending') return 'outline';
    return 'default';
  };

  return (
    <Card className={`p-6 hover:shadow-lg transition-shadow duration-200 ${className}`}>
      <div className="flex items-start space-x-4">
        {/* Group Image */}
        <div className="flex-shrink-0">
          {group.image ? (
            <img
              src={group.image}
              alt={group.name}
              className="w-16 h-16 rounded-lg object-cover"
            />
          ) : (
            <div className="w-16 h-16 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
              <span className="text-white font-bold text-xl">
                {group.name.charAt(0).toUpperCase()}
              </span>
            </div>
          )}
        </div>

        {/* Group Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <Link 
                href={`/peer-groups/${group.slug}`}
                className="block hover:text-blue-600 transition-colors"
              >
                <h3 className="text-lg font-semibold text-gray-900 truncate">
                  {group.name}
                </h3>
              </Link>
              
              {group.tagline && (
                <p className="text-sm text-gray-600 mt-1">
                  {group.tagline}
                </p>
              )}
            </div>

            {/* Join Button */}
            {showJoinButton && (
              <Button
                onClick={handleJoinGroup}
                disabled={isJoining || isMember || membershipStatus === 'pending'}
                variant={getJoinButtonVariant()}
                size="sm"
                className="ml-4 flex-shrink-0"
              >
                {isJoining ? 'Joining...' : getJoinButtonText()}
              </Button>
            )}
          </div>

          {/* Description */}
          <p className="text-sm text-gray-700 mt-2 line-clamp-2">
            {group.description}
          </p>

          {/* Badges */}
          <div className="flex flex-wrap gap-2 mt-3">
            <Badge className={getPrivacyBadgeColor(group.privacy_level)}>
              {group.privacy_level}
            </Badge>
            <Badge className={getGroupTypeBadgeColor(group.group_type)}>
              {group.group_type.replace('_', ' ')}
            </Badge>
            {group.industry && (
              <Badge variant="outline">
                {group.industry}
              </Badge>
            )}
          </div>

          {/* Stats and Meta */}
          <div className="flex items-center justify-between mt-4">
            <div className="flex items-center space-x-4 text-sm text-gray-500">
              <span className="flex items-center">
                <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M13 6a3 3 0 11-6 0 3 3 0 016 0zM18 8a2 2 0 11-4 0 2 2 0 014 0zM14 15a4 4 0 00-8 0v3h8v-3z" />
                </svg>
                {group.member_count} members
              </span>
              
              <span className="flex items-center">
                <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9H5v2h2V9zm8 0h-2v2h2V9zM9 9h2v2H9V9z" clipRule="evenodd" />
                </svg>
                {group.post_count} posts
              </span>

              {group.activity_score > 0 && (
                <span className="flex items-center">
                  <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M12.395 2.553a1 1 0 00-1.45-.385c-.345.23-.614.558-.822.88-.214.33-.403.713-.57 1.116-.334.804-.614 1.768-.84 2.734a31.365 31.365 0 00-.613 3.58 2.64 2.64 0 01-.945-1.067c-.328-.68-.398-1.534-.398-2.654A1 1 0 005.05 6.05 6.981 6.981 0 003 11a7 7 0 1011.95-4.95c-.592-.591-.98-.985-1.348-1.467-.363-.476-.724-1.063-1.207-2.03zM12.12 15.12A3 3 0 017 13s.879.5 2.5.5c0-1 .5-4 1.25-4.5.5 1 .786 1.293 1.371 1.879A2.99 2.99 0 0113 13a2.99 2.99 0 01-.879 2.121z" clipRule="evenodd" />
                  </svg>
                  Active
                </span>
              )}
            </div>

            {/* Recent Members */}
            {group.recent_members && group.recent_members.length > 0 && (
              <div className="flex -space-x-2">
                {group.recent_members.slice(0, 3).map((member, index) => (
                  <Avatar
                    key={member.id}
                    src={member.profile_picture}
                    alt={member.full_name}
                    size="sm"
                    className="border-2 border-white"
                  />
                ))}
                {group.recent_members.length > 3 && (
                  <div className="w-8 h-8 rounded-full bg-gray-200 border-2 border-white flex items-center justify-center">
                    <span className="text-xs text-gray-600 font-medium">
                      +{group.recent_members.length - 3}
                    </span>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Skills */}
          {group.skills && group.skills.length > 0 && (
            <div className="mt-3">
              <div className="flex flex-wrap gap-1">
                {group.skills.slice(0, 3).map((skill, index) => (
                  <Badge key={index} variant="secondary" className="text-xs">
                    {skill}
                  </Badge>
                ))}
                {group.skills.length > 3 && (
                  <Badge variant="secondary" className="text-xs">
                    +{group.skills.length - 3} more
                  </Badge>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </Card>
  );
};

export default PeerGroupCard;