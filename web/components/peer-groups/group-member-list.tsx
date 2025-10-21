'use client';

import React, { useState, useEffect } from 'react';
import { GroupMembership, User } from '@/types/peer-groups';
import { Avatar } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { api } from '@/lib/api';
import { useNotifications } from '@/contexts/notification-context';

interface GroupMemberListProps {
  groupSlug: string;
  isAdmin?: boolean;
  className?: string;
}

const GroupMemberList: React.FC<GroupMemberListProps> = ({
  groupSlug,
  isAdmin = false,
  className = ''
}) => {
  const [members, setMembers] = useState<GroupMembership[]>([]);
  const [pendingMembers, setPendingMembers] = useState<GroupMembership[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'active' | 'pending'>('active');
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const { addNotification } = useNotifications();

  useEffect(() => {
    loadMembers();
    if (isAdmin) {
      loadPendingMembers();
    }
  }, [groupSlug, isAdmin]);

  const loadMembers = async () => {
    try {
      const response = await api.peerGroups.getMembers(groupSlug);
      setMembers(response.data);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to load members');
    }
  };

  const loadPendingMembers = async () => {
    if (!isAdmin) return;
    
    try {
      const response = await api.peerGroups.getPendingMembers(groupSlug);
      setPendingMembers(response.data);
    } catch (err: any) {
      console.error('Failed to load pending members:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleMemberAction = async (memberId: string, action: string, reason?: string) => {
    setActionLoading(memberId);
    
    try {
      await api.peerGroups.manageMember(groupSlug, {
        member_id: memberId,
        action,
        reason
      });
      
      addNotification({
        type: 'success',
        title: 'Success',
        message: `Member ${action} successfully`
      });
      
      // Reload data
      await loadMembers();
      if (isAdmin) {
        await loadPendingMembers();
      }
    } catch (err: any) {
      addNotification({
        type: 'error',
        title: 'Error',
        message: err.response?.data?.error || `Failed to ${action} member`
      });
    } finally {
      setActionLoading(null);
    }
  };

  const getRoleBadgeColor = (role: string) => {
    switch (role) {
      case 'admin': return 'bg-red-100 text-red-800';
      case 'moderator': return 'bg-orange-100 text-orange-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
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
        <p className="text-red-600">{error}</p>
      </div>
    );
  }

  return (
    <div className={className}>
      {/* Tab Navigation */}
      {isAdmin && pendingMembers.length > 0 && (
        <div className="mb-6">
          <nav className="flex space-x-8">
            <button
              onClick={() => setActiveTab('active')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'active'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              Members ({members.length})
            </button>
            <button
              onClick={() => setActiveTab('pending')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'pending'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              Pending ({pendingMembers.length})
            </button>
          </nav>
        </div>
      )}

      {/* Member List */}
      <div className="space-y-4">
        {activeTab === 'active' && (
          <>
            {members.length === 0 ? (
              <p className="text-gray-500 text-center py-8">No members found.</p>
            ) : (
              members.map((membership) => (
                <div key={membership.id} className="flex items-center justify-between p-4 bg-white border border-gray-200 rounded-lg">
                  <div className="flex items-center space-x-4">
                    <Avatar
                      src={membership.user.profile_picture}
                      alt={membership.user.full_name}
                      size="md"
                    />
                    
                    <div>
                      <h4 className="font-medium text-gray-900">
                        {membership.user.full_name}
                      </h4>
                      <p className="text-sm text-gray-500">
                        {membership.user.email}
                      </p>
                      <div className="flex items-center space-x-2 mt-1">
                        <Badge className={getRoleBadgeColor(membership.role)}>
                          {membership.role}
                        </Badge>
                        <span className="text-xs text-gray-400">
                          Joined {formatDate(membership.joined_at)}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center space-x-2">
                    <div className="text-right text-sm text-gray-500">
                      <div>{membership.post_count} posts</div>
                      <div>{membership.comment_count} comments</div>
                    </div>
                    
                    {isAdmin && membership.role !== 'admin' && (
                      <div className="flex space-x-2">
                        {membership.role === 'member' && (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleMemberAction(membership.user.id, 'promote')}
                            disabled={actionLoading === membership.user.id}
                          >
                            Promote
                          </Button>
                        )}
                        {membership.role === 'moderator' && (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleMemberAction(membership.user.id, 'demote')}
                            disabled={actionLoading === membership.user.id}
                          >
                            Demote
                          </Button>
                        )}
                        <Button
                          size="sm"
                          variant="outline"
                          className="text-red-600 hover:text-red-700"
                          onClick={() => handleMemberAction(membership.user.id, 'remove')}
                          disabled={actionLoading === membership.user.id}
                        >
                          Remove
                        </Button>
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}
          </>
        )}

        {activeTab === 'pending' && isAdmin && (
          <>
            {pendingMembers.length === 0 ? (
              <p className="text-gray-500 text-center py-8">No pending requests.</p>
            ) : (
              pendingMembers.map((membership) => (
                <div key={membership.id} className="flex items-center justify-between p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                  <div className="flex items-center space-x-4">
                    <Avatar
                      src={membership.user.profile_picture}
                      alt={membership.user.full_name}
                      size="md"
                    />
                    
                    <div>
                      <h4 className="font-medium text-gray-900">
                        {membership.user.full_name}
                      </h4>
                      <p className="text-sm text-gray-500">
                        {membership.user.email}
                      </p>
                      <div className="flex items-center space-x-2 mt-1">
                        <Badge className="bg-yellow-100 text-yellow-800">
                          Pending Approval
                        </Badge>
                        <span className="text-xs text-gray-400">
                          Requested {formatDate(membership.joined_at)}
                        </span>
                      </div>
                      {membership.invitation_message && (
                        <p className="text-sm text-gray-600 mt-2 italic">
                          "{membership.invitation_message}"
                        </p>
                      )}
                    </div>
                  </div>

                  <div className="flex space-x-2">
                    <Button
                      size="sm"
                      variant="default"
                      onClick={() => handleMemberAction(membership.user.id, 'approve')}
                      disabled={actionLoading === membership.user.id}
                    >
                      {actionLoading === membership.user.id ? 'Processing...' : 'Approve'}
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      className="text-red-600 hover:text-red-700"
                      onClick={() => handleMemberAction(membership.user.id, 'reject')}
                      disabled={actionLoading === membership.user.id}
                    >
                      Reject
                    </Button>
                  </div>
                </div>
              ))
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default GroupMemberList;