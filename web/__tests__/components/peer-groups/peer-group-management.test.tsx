import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { jest } from '@jest/globals';
import GroupManagement from '@/components/peer-groups/group-management';
import { api } from '@/lib/api';
import { useNotification } from '@/contexts/notification-context';

// Mock dependencies
jest.mock('@/lib/api');
jest.mock('@/contexts/notification-context');

const mockApi = api as jest.Mocked<typeof api>;
const mockUseNotification = useNotification as jest.MockedFunction<typeof useNotification>;

const mockAddNotification = jest.fn();

const mockGroup = {
  id: 1,
  name: 'Tech Professionals',
  slug: 'tech-professionals',
  description: 'A group for technology professionals',
  privacy_level: 'public',
  group_type: 'industry',
  industry: 'Technology',
  member_count: 150,
  is_admin: true,
  created_by: {
    id: 1,
    full_name: 'John Doe',
    email: 'john@example.com'
  }
};

const mockMembers = [
  {
    id: 1,
    user: {
      id: 1,
      full_name: 'John Doe',
      email: 'john@example.com',
      profile_picture: 'https://example.com/john.jpg'
    },
    role: 'admin',
    status: 'active',
    joined_at: '2024-01-01T00:00:00Z'
  },
  {
    id: 2,
    user: {
      id: 2,
      full_name: 'Jane Smith',
      email: 'jane@example.com',
      profile_picture: null
    },
    role: 'member',
    status: 'active',
    joined_at: '2024-01-02T00:00:00Z'
  },
  {
    id: 3,
    user: {
      id: 3,
      full_name: 'Bob Johnson',
      email: 'bob@example.com',
      profile_picture: 'https://example.com/bob.jpg'
    },
    role: 'member',
    status: 'pending',
    joined_at: '2024-01-03T00:00:00Z'
  }
];

const mockPendingRequests = [
  {
    id: 4,
    user: {
      id: 4,
      full_name: 'Alice Brown',
      email: 'alice@example.com',
      profile_picture: 'https://example.com/alice.jpg'
    },
    role: 'member',
    status: 'pending',
    requested_at: '2024-01-04T00:00:00Z'
  }
];

describe('GroupManagement', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockUseNotification.mockReturnValue({
      addNotification: mockAddNotification,
      notifications: [],
      removeNotification: jest.fn()
    });

    mockApi.peerGroups = {
      getMembers: jest.fn().mockResolvedValue({ data: mockMembers }),
      getPendingMembers: jest.fn().mockResolvedValue({ data: mockPendingRequests }),
      manageMember: jest.fn(),
      update: jest.fn()
    } as any;
  });

  describe('Component Rendering', () => {
    it('should render group management interface for admin', async () => {
      render(<GroupManagement group={mockGroup} />);

      await waitFor(() => {
        expect(screen.getByText('Group Management')).toBeInTheDocument();
        expect(screen.getByText('Members')).toBeInTheDocument();
        expect(screen.getByText('Pending Requests')).toBeInTheDocument();
        expect(screen.getByText('Group Settings')).toBeInTheDocument();
      });
    });

    it('should not render for non-admin users', () => {
      const nonAdminGroup = { ...mockGroup, is_admin: false };
      render(<GroupManagement group={nonAdminGroup} />);

      expect(screen.getByText('Access Denied')).toBeInTheDocument();
      expect(screen.getByText('You do not have permission to manage this group.')).toBeInTheDocument();
    });
  });

  describe('Members Management', () => {
    it('should load and display group members', async () => {
      render(<GroupManagement group={mockGroup} />);

      await waitFor(() => {
        expect(screen.getByText('John Doe')).toBeInTheDocument();
        expect(screen.getByText('jane@example.com')).toBeInTheDocument();
        expect(screen.getByText('Bob Johnson')).toBeInTheDocument();
      });

      expect(mockApi.peerGroups.getMembers).toHaveBeenCalledWith('tech-professionals');
    });

    it('should display member roles and statuses', async () => {
      render(<GroupManagement group={mockGroup} />);

      await waitFor(() => {
        expect(screen.getByText('Admin')).toBeInTheDocument();
        expect(screen.getAllByText('Member')).toHaveLength(2);
        expect(screen.getByText('Pending')).toBeInTheDocument();
      });
    });

    it('should promote member to admin', async () => {
      mockApi.peerGroups.manageMember = jest.fn().mockResolvedValue({
        data: { message: 'Member promoted to admin' }
      });

      render(<GroupManagement group={mockGroup} />);

      await waitFor(() => {
        const promoteButtons = screen.getAllByText('Promote to Admin');
        fireEvent.click(promoteButtons[0]);
      });

      await waitFor(() => {
        expect(mockApi.peerGroups.manageMember).toHaveBeenCalledWith(
          'tech-professionals',
          { user_id: 2, action: 'promote' }
        );
        expect(mockAddNotification).toHaveBeenCalledWith({
          type: 'success',
          title: 'Success',
          message: 'Member promoted to admin'
        });
      });
    });

    it('should remove member from group', async () => {
      mockApi.peerGroups.manageMember = jest.fn().mockResolvedValue({
        data: { message: 'Member removed from group' }
      });

      render(<GroupManagement group={mockGroup} />);

      await waitFor(() => {
        const removeButtons = screen.getAllByText('Remove');
        fireEvent.click(removeButtons[0]);
      });

      // Confirm removal
      const confirmButton = screen.getByText('Confirm Remove');
      fireEvent.click(confirmButton);

      await waitFor(() => {
        expect(mockApi.peerGroups.manageMember).toHaveBeenCalledWith(
          'tech-professionals',
          { user_id: 2, action: 'remove' }
        );
        expect(mockAddNotification).toHaveBeenCalledWith({
          type: 'success',
          title: 'Success',
          message: 'Member removed from group'
        });
      });
    });

    it('should handle member management errors', async () => {
      mockApi.peerGroups.manageMember = jest.fn().mockRejectedValue({
        response: { data: { error: 'Permission denied' } }
      });

      render(<GroupManagement group={mockGroup} />);

      await waitFor(() => {
        const promoteButtons = screen.getAllByText('Promote to Admin');
        fireEvent.click(promoteButtons[0]);
      });

      await waitFor(() => {
        expect(mockAddNotification).toHaveBeenCalledWith({
          type: 'error',
          title: 'Error',
          message: 'Permission denied'
        });
      });
    });
  });

  describe('Pending Requests Management', () => {
    it('should load and display pending requests', async () => {
      render(<GroupManagement group={mockGroup} />);

      // Switch to pending requests tab
      fireEvent.click(screen.getByText('Pending Requests'));

      await waitFor(() => {
        expect(screen.getByText('Alice Brown')).toBeInTheDocument();
        expect(screen.getByText('alice@example.com')).toBeInTheDocument();
      });

      expect(mockApi.peerGroups.getPendingMembers).toHaveBeenCalledWith('tech-professionals');
    });

    it('should approve pending request', async () => {
      mockApi.peerGroups.manageMember = jest.fn().mockResolvedValue({
        data: { message: 'Member request approved' }
      });

      render(<GroupManagement group={mockGroup} />);

      // Switch to pending requests tab
      fireEvent.click(screen.getByText('Pending Requests'));

      await waitFor(() => {
        const approveButton = screen.getByText('Approve');
        fireEvent.click(approveButton);
      });

      await waitFor(() => {
        expect(mockApi.peerGroups.manageMember).toHaveBeenCalledWith(
          'tech-professionals',
          { user_id: 4, action: 'approve' }
        );
        expect(mockAddNotification).toHaveBeenCalledWith({
          type: 'success',
          title: 'Success',
          message: 'Member request approved'
        });
      });
    });

    it('should reject pending request', async () => {
      mockApi.peerGroups.manageMember = jest.fn().mockResolvedValue({
        data: { message: 'Member request rejected' }
      });

      render(<GroupManagement group={mockGroup} />);

      // Switch to pending requests tab
      fireEvent.click(screen.getByText('Pending Requests'));

      await waitFor(() => {
        const rejectButton = screen.getByText('Reject');
        fireEvent.click(rejectButton);
      });

      await waitFor(() => {
        expect(mockApi.peerGroups.manageMember).toHaveBeenCalledWith(
          'tech-professionals',
          { user_id: 4, action: 'reject' }
        );
        expect(mockAddNotification).toHaveBeenCalledWith({
          type: 'success',
          title: 'Success',
          message: 'Member request rejected'
        });
      });
    });

    it('should show empty state when no pending requests', async () => {
      mockApi.peerGroups.getPendingMembers = jest.fn().mockResolvedValue({
        data: []
      });

      render(<GroupManagement group={mockGroup} />);

      // Switch to pending requests tab
      fireEvent.click(screen.getByText('Pending Requests'));

      await waitFor(() => {
        expect(screen.getByText('No pending requests')).toBeInTheDocument();
      });
    });
  });

  describe('Group Settings', () => {
    it('should display group settings form', async () => {
      render(<GroupManagement group={mockGroup} />);

      // Switch to group settings tab
      fireEvent.click(screen.getByText('Group Settings'));

      await waitFor(() => {
        expect(screen.getByDisplayValue('Tech Professionals')).toBeInTheDocument();
        expect(screen.getByDisplayValue('A group for technology professionals')).toBeInTheDocument();
        expect(screen.getByDisplayValue('public')).toBeInTheDocument();
      });
    });

    it('should update group settings', async () => {
      mockApi.peerGroups.update = jest.fn().mockResolvedValue({
        data: { message: 'Group settings updated' }
      });

      render(<GroupManagement group={mockGroup} />);

      // Switch to group settings tab
      fireEvent.click(screen.getByText('Group Settings'));

      await waitFor(() => {
        // Update group name
        const nameInput = screen.getByDisplayValue('Tech Professionals');
        fireEvent.change(nameInput, { target: { value: 'Updated Tech Group' } });

        // Update description
        const descInput = screen.getByDisplayValue('A group for technology professionals');
        fireEvent.change(descInput, { target: { value: 'Updated description' } });

        // Save changes
        const saveButton = screen.getByText('Save Changes');
        fireEvent.click(saveButton);
      });

      await waitFor(() => {
        expect(mockApi.peerGroups.update).toHaveBeenCalledWith(
          'tech-professionals',
          {
            name: 'Updated Tech Group',
            description: 'Updated description',
            privacy_level: 'public',
            group_type: 'industry',
            industry: 'Technology'
          }
        );
        expect(mockAddNotification).toHaveBeenCalledWith({
          type: 'success',
          title: 'Success',
          message: 'Group settings updated'
        });
      });
    });

    it('should handle group settings update errors', async () => {
      mockApi.peerGroups.update = jest.fn().mockRejectedValue({
        response: { data: { error: 'Invalid group name' } }
      });

      render(<GroupManagement group={mockGroup} />);

      // Switch to group settings tab
      fireEvent.click(screen.getByText('Group Settings'));

      await waitFor(() => {
        const saveButton = screen.getByText('Save Changes');
        fireEvent.click(saveButton);
      });

      await waitFor(() => {
        expect(mockAddNotification).toHaveBeenCalledWith({
          type: 'error',
          title: 'Error',
          message: 'Invalid group name'
        });
      });
    });
  });

  describe('Loading States', () => {
    it('should show loading state while fetching members', () => {
      let resolvePromise: (value: any) => void;
      const promise = new Promise(resolve => {
        resolvePromise = resolve;
      });

      mockApi.peerGroups.getMembers = jest.fn().mockReturnValue(promise);

      render(<GroupManagement group={mockGroup} />);

      expect(screen.getByText('Loading members...')).toBeInTheDocument();

      // Resolve the promise
      resolvePromise!({ data: mockMembers });
    });

    it('should show loading state during member actions', async () => {
      let resolvePromise: (value: any) => void;
      const promise = new Promise(resolve => {
        resolvePromise = resolve;
      });

      mockApi.peerGroups.manageMember = jest.fn().mockReturnValue(promise);

      render(<GroupManagement group={mockGroup} />);

      await waitFor(() => {
        const promoteButtons = screen.getAllByText('Promote to Admin');
        fireEvent.click(promoteButtons[0]);
      });

      expect(screen.getByText('Promoting...')).toBeInTheDocument();

      // Resolve the promise
      resolvePromise!({ data: { message: 'Success' } });
    });
  });

  describe('Error Handling', () => {
    it('should handle API errors when loading members', async () => {
      mockApi.peerGroups.getMembers = jest.fn().mockRejectedValue({
        response: { data: { error: 'Failed to load members' } }
      });

      render(<GroupManagement group={mockGroup} />);

      await waitFor(() => {
        expect(mockAddNotification).toHaveBeenCalledWith({
          type: 'error',
          title: 'Error',
          message: 'Failed to load members'
        });
      });
    });

    it('should handle API errors when loading pending requests', async () => {
      mockApi.peerGroups.getPendingMembers = jest.fn().mockRejectedValue({
        response: { data: { error: 'Failed to load requests' } }
      });

      render(<GroupManagement group={mockGroup} />);

      // Switch to pending requests tab
      fireEvent.click(screen.getByText('Pending Requests'));

      await waitFor(() => {
        expect(mockAddNotification).toHaveBeenCalledWith({
          type: 'error',
          title: 'Error',
          message: 'Failed to load requests'
        });
      });
    });
  });

  describe('Tab Navigation', () => {
    it('should switch between tabs correctly', async () => {
      render(<GroupManagement group={mockGroup} />);

      // Initially on Members tab
      await waitFor(() => {
        expect(screen.getByText('John Doe')).toBeInTheDocument();
      });

      // Switch to Pending Requests
      fireEvent.click(screen.getByText('Pending Requests'));
      await waitFor(() => {
        expect(screen.getByText('Alice Brown')).toBeInTheDocument();
      });

      // Switch to Group Settings
      fireEvent.click(screen.getByText('Group Settings'));
      await waitFor(() => {
        expect(screen.getByDisplayValue('Tech Professionals')).toBeInTheDocument();
      });

      // Switch back to Members
      fireEvent.click(screen.getByText('Members'));
      await waitFor(() => {
        expect(screen.getByText('John Doe')).toBeInTheDocument();
      });
    });
  });
});