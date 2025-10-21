'use client';

import React, { useState, useEffect } from 'react';
import { PeerGroup, GroupMembership, InviteUserRequest } from '@/types/peer-groups';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Modal } from '@/components/ui/modal';
import { Badge } from '@/components/ui/badge';
import { Avatar } from '@/components/ui/avatar';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { Tabs } from '@/components/ui/tabs';
import { api } from '@/lib/api';
import { useNotifications } from '@/contexts/notification-context';

interface GroupManagementProps {
  group: PeerGroup;
  onGroupUpdate?: (group: PeerGroup) => void;
  className?: string;
}

const GroupManagement: React.FC<GroupManagementProps> = ({
  group: initialGroup,
  onGroupUpdate,
  className = ''
}) => {
  const [group, setGroup] = useState(initialGroup);
  const [activeTab, setActiveTab] = useState<'settings' | 'members' | 'invites'>('settings');
  const [loading, setLoading] = useState(false);
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [pendingMembers, setPendingMembers] = useState<GroupMembership[]>([]);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const { addNotification } = useNotifications();

  // Form states
  const [groupSettings, setGroupSettings] = useState({
    name: group.name,
    tagline: group.tagline || '',
    description: group.description,
    rules: group.rules || '',
    welcome_message: group.welcome_message || '',
    privacy_level: group.privacy_level,
    max_members: group.max_members || '',
    industry: group.industry || '',
    location: group.location || '',
    skills: group.skills.join(', ')
  });

  const [inviteForm, setInviteForm] = useState({
    user_email: '',
    message: ''
  });

  useEffect(() => {
    if (activeTab === 'members') {
      loadPendingMembers();
    }
  }, [activeTab]);

  const loadPendingMembers = async () => {
    try {
      const response = await api.peerGroups.getPendingMembers(group.slug);
      setPendingMembers(response.data);
    } catch (err: any) {
      console.error('Failed to load pending members:', err);
    }
  };

  const handleUpdateGroup = async () => {
    setLoading(true);
    
    try {
      const updateData = {
        ...groupSettings,
        skills: groupSettings.skills.split(',').map(s => s.trim()).filter(s => s),
        max_members: groupSettings.max_members ? parseInt(groupSettings.max_members.toString()) : null
      };
      
      const response = await api.peerGroups.update(group.slug, updateData);
      const updatedGroup = { ...group, ...response.data };
      
      setGroup(updatedGroup);
      if (onGroupUpdate) {
        onGroupUpdate(updatedGroup);
      }
      
      addNotification({
        type: 'success',
        title: 'Success',
        message: 'Group settings updated successfully'
      });
    } catch (err: any) {
      addNotification({
        type: 'error',
        title: 'Error',
        message: err.response?.data?.error || 'Failed to update group settings'
      });
    } finally {
      setLoading(false);
    }
  };

  const handleInviteMember = async () => {
    if (!inviteForm.user_email.trim()) {
      addNotification({
        type: 'error',
        title: 'Validation Error',
        message: 'Email address is required'
      });
      return;
    }

    setLoading(true);
    
    try {
      await api.peerGroups.inviteMember(group.slug, inviteForm);
      
      addNotification({
        type: 'success',
        title: 'Success',
        message: 'Invitation sent successfully'
      });
      
      setShowInviteModal(false);
      setInviteForm({ user_email: '', message: '' });
    } catch (err: any) {
      addNotification({
        type: 'error',
        title: 'Error',
        message: err.response?.data?.error || 'Failed to send invitation'
      });
    } finally {
      setLoading(false);
    }
  };

  const handleMemberAction = async (memberId: string, action: string) => {
    setActionLoading(memberId);
    
    try {
      await api.peerGroups.manageMember(group.slug, {
        member_id: memberId,
        action
      });
      
      addNotification({
        type: 'success',
        title: 'Success',
        message: `Member ${action} successfully`
      });
      
      // Reload pending members
      await loadPendingMembers();
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

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  return (
    <div className={`max-w-4xl mx-auto ${className}`}>
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">
          Manage Group: {group.name}
        </h1>
        <p className="text-gray-600">
          Configure group settings, manage members, and send invitations
        </p>
      </div>

      {/* Tab Navigation */}
      <div className="mb-6">
        <nav className="flex space-x-8">
          <button
            onClick={() => setActiveTab('settings')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'settings'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            Settings
          </button>
          <button
            onClick={() => setActiveTab('members')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'members'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            Member Requests
            {pendingMembers.length > 0 && (
              <Badge className="ml-2 bg-red-100 text-red-800">
                {pendingMembers.length}
              </Badge>
            )}
          </button>
          <button
            onClick={() => setActiveTab('invites')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'invites'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            Invite Members
          </button>
        </nav>
      </div>

      {/* Tab Content */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        {activeTab === 'settings' && (
          <div className="space-y-6">
            <h3 className="text-lg font-medium text-gray-900">Group Settings</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <Label htmlFor="group-name">Group Name</Label>
                <Input
                  id="group-name"
                  value={groupSettings.name}
                  onChange={(e) => setGroupSettings({ ...groupSettings, name: e.target.value })}
                  className="mt-1"
                />
              </div>
              
              <div>
                <Label htmlFor="group-tagline">Tagline</Label>
                <Input
                  id="group-tagline"
                  value={groupSettings.tagline}
                  onChange={(e) => setGroupSettings({ ...groupSettings, tagline: e.target.value })}
                  placeholder="Short group tagline..."
                  className="mt-1"
                />
              </div>
            </div>

            <div>
              <Label htmlFor="group-description">Description</Label>
              <Textarea
                id="group-description"
                value={groupSettings.description}
                onChange={(e) => setGroupSettings({ ...groupSettings, description: e.target.value })}
                rows={4}
                className="mt-1"
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <Label htmlFor="privacy-level">Privacy Level</Label>
                <select
                  id="privacy-level"
                  value={groupSettings.privacy_level}
                  onChange={(e) => setGroupSettings({ ...groupSettings, privacy_level: e.target.value as any })}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                >
                  <option value="public">Public - Anyone can join</option>
                  <option value="restricted">Restricted - Request to join</option>
                  <option value="private">Private - Invitation only</option>
                </select>
              </div>
              
              <div>
                <Label htmlFor="max-members">Maximum Members (optional)</Label>
                <Input
                  id="max-members"
                  type="number"
                  value={groupSettings.max_members}
                  onChange={(e) => setGroupSettings({ ...groupSettings, max_members: e.target.value })}
                  placeholder="No limit"
                  className="mt-1"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <Label htmlFor="industry">Industry</Label>
                <Input
                  id="industry"
                  value={groupSettings.industry}
                  onChange={(e) => setGroupSettings({ ...groupSettings, industry: e.target.value })}
                  placeholder="e.g., Technology, Healthcare"
                  className="mt-1"
                />
              </div>
              
              <div>
                <Label htmlFor="location">Location</Label>
                <Input
                  id="location"
                  value={groupSettings.location}
                  onChange={(e) => setGroupSettings({ ...groupSettings, location: e.target.value })}
                  placeholder="e.g., Global, San Francisco"
                  className="mt-1"
                />
              </div>
            </div>

            <div>
              <Label htmlFor="skills">Relevant Skills (comma-separated)</Label>
              <Input
                id="skills"
                value={groupSettings.skills}
                onChange={(e) => setGroupSettings({ ...groupSettings, skills: e.target.value })}
                placeholder="e.g., React, JavaScript, Node.js"
                className="mt-1"
              />
            </div>

            <div>
              <Label htmlFor="welcome-message">Welcome Message</Label>
              <Textarea
                id="welcome-message"
                value={groupSettings.welcome_message}
                onChange={(e) => setGroupSettings({ ...groupSettings, welcome_message: e.target.value })}
                placeholder="Message shown to new members..."
                rows={3}
                className="mt-1"
              />
            </div>

            <div>
              <Label htmlFor="group-rules">Group Rules</Label>
              <Textarea
                id="group-rules"
                value={groupSettings.rules}
                onChange={(e) => setGroupSettings({ ...groupSettings, rules: e.target.value })}
                placeholder="Group rules and guidelines..."
                rows={4}
                className="mt-1"
              />
            </div>

            <div className="flex justify-end">
              <Button onClick={handleUpdateGroup} disabled={loading}>
                {loading ? 'Updating...' : 'Update Group Settings'}
              </Button>
            </div>
          </div>
        )}

        {activeTab === 'members' && (
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-4">
              Pending Member Requests
            </h3>
            
            {pendingMembers.length === 0 ? (
              <p className="text-gray-500 text-center py-8">
                No pending membership requests.
              </p>
            ) : (
              <div className="space-y-4">
                {pendingMembers.map((membership) => (
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
                        <p className="text-xs text-gray-400">
                          Requested {formatDate(membership.joined_at)}
                        </p>
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
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === 'invites' && (
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-900">
                Invite New Members
              </h3>
              <Button onClick={() => setShowInviteModal(true)}>
                Send Invitation
              </Button>
            </div>
            
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h4 className="font-medium text-blue-800 mb-2">
                How to invite members
              </h4>
              <ul className="text-sm text-blue-700 space-y-1">
                <li>• Enter the email address of the person you want to invite</li>
                <li>• Add a personal message explaining why they should join</li>
                <li>• They'll receive an email invitation with a link to join the group</li>
                <li>• For private groups, invitations bypass the approval process</li>
              </ul>
            </div>
          </div>
        )}
      </div>

      {/* Invite Member Modal */}
      <Modal
        isOpen={showInviteModal}
        onClose={() => setShowInviteModal(false)}
        title="Invite Member to Group"
      >
        <div className="space-y-4">
          <div>
            <Label htmlFor="invite-email">Email Address</Label>
            <Input
              id="invite-email"
              type="email"
              value={inviteForm.user_email}
              onChange={(e) => setInviteForm({ ...inviteForm, user_email: e.target.value })}
              placeholder="Enter email address..."
              className="mt-1"
            />
          </div>

          <div>
            <Label htmlFor="invite-message">Personal Message (optional)</Label>
            <Textarea
              id="invite-message"
              value={inviteForm.message}
              onChange={(e) => setInviteForm({ ...inviteForm, message: e.target.value })}
              placeholder="Add a personal message to your invitation..."
              rows={3}
              className="mt-1"
            />
          </div>

          <div className="flex justify-end space-x-3">
            <Button
              variant="outline"
              onClick={() => setShowInviteModal(false)}
              disabled={loading}
            >
              Cancel
            </Button>
            <Button
              onClick={handleInviteMember}
              disabled={loading || !inviteForm.user_email.trim()}
            >
              {loading ? 'Sending...' : 'Send Invitation'}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};

export default GroupManagement;