'use client';

import React, { useState } from 'react';
import { PeerGroup, JoinGroupRequest } from '@/types/peer-groups';
import { Modal } from '@/components/ui/modal';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { api } from '@/lib/api';
import { useNotifications } from '@/contexts/notification-context';

interface JoinGroupModalProps {
  group: PeerGroup | null;
  isOpen: boolean;
  onClose: () => void;
  onJoinSuccess: (group: PeerGroup) => void;
}

const JoinGroupModal: React.FC<JoinGroupModalProps> = ({
  group,
  isOpen,
  onClose,
  onJoinSuccess
}) => {
  const [message, setMessage] = useState('');
  const [isJoining, setIsJoining] = useState(false);
  const { addNotification } = useNotifications();

  const handleJoin = async () => {
    if (!group || isJoining) return;

    setIsJoining(true);
    try {
      const requestData: JoinGroupRequest = {};
      if (message.trim()) {
        requestData.message = message.trim();
      }

      const response = await api.peerGroups.join(group.slug, requestData);
      const newStatus = response.data.status;
      
      addNotification({
        type: 'success',
        title: 'Success',
        message: response.data.message
      });

      onJoinSuccess({
        ...group,
        membership_status: newStatus,
        is_member: newStatus === 'active'
      });
      
      onClose();
      setMessage('');
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

  const handleClose = () => {
    if (!isJoining) {
      onClose();
      setMessage('');
    }
  };

  if (!group) return null;

  const requiresApproval = group.privacy_level !== 'public';
  const isInviteOnly = group.privacy_level === 'private';

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title="Join Group">
      <div className="space-y-6">
        {/* Group Info */}
        <div className="flex items-start space-x-4">
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
          
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-gray-900">
              {group.name}
            </h3>
            {group.tagline && (
              <p className="text-sm text-gray-600 mt-1">
                {group.tagline}
              </p>
            )}
            
            <div className="flex flex-wrap gap-2 mt-2">
              <Badge className={
                group.privacy_level === 'public' ? 'bg-green-100 text-green-800' :
                group.privacy_level === 'private' ? 'bg-red-100 text-red-800' :
                'bg-yellow-100 text-yellow-800'
              }>
                {group.privacy_level}
              </Badge>
              <Badge variant="outline">
                {group.member_count} members
              </Badge>
            </div>
          </div>
        </div>

        {/* Group Description */}
        <div>
          <p className="text-sm text-gray-700">
            {group.description}
          </p>
        </div>

        {/* Join Requirements Info */}
        {requiresApproval && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <div className="flex">
              <svg className="w-5 h-5 text-yellow-400 mr-2 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
              <div>
                <h4 className="text-sm font-medium text-yellow-800">
                  {isInviteOnly ? 'Invitation Required' : 'Approval Required'}
                </h4>
                <p className="text-sm text-yellow-700 mt-1">
                  {isInviteOnly 
                    ? 'This is a private group. You need an invitation from a group admin to join.'
                    : 'Your request to join will be reviewed by group administrators.'
                  }
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Welcome Message */}
        {group.welcome_message && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h4 className="text-sm font-medium text-blue-800 mb-2">
              Welcome Message
            </h4>
            <p className="text-sm text-blue-700">
              {group.welcome_message}
            </p>
          </div>
        )}

        {/* Group Rules */}
        {group.rules && (
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
            <h4 className="text-sm font-medium text-gray-800 mb-2">
              Group Rules
            </h4>
            <p className="text-sm text-gray-700 whitespace-pre-wrap">
              {group.rules}
            </p>
          </div>
        )}

        {/* Message Input */}
        {requiresApproval && !isInviteOnly && (
          <div>
            <Label htmlFor="join-message">
              Message to Administrators {requiresApproval ? '(Optional)' : ''}
            </Label>
            <Textarea
              id="join-message"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Tell the administrators why you'd like to join this group..."
              rows={3}
              className="mt-1"
              maxLength={500}
            />
            <p className="text-xs text-gray-500 mt-1">
              {message.length}/500 characters
            </p>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex justify-end space-x-3">
          <Button
            variant="outline"
            onClick={handleClose}
            disabled={isJoining}
          >
            Cancel
          </Button>
          <Button
            onClick={handleJoin}
            disabled={isJoining || isInviteOnly}
            className="min-w-[120px]"
          >
            {isJoining ? 'Joining...' : 
             isInviteOnly ? 'Invitation Required' :
             requiresApproval ? 'Request to Join' : 'Join Group'}
          </Button>
        </div>
      </div>
    </Modal>
  );
};

export default JoinGroupModal;