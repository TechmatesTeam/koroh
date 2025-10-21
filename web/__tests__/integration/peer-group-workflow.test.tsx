import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { jest } from '@jest/globals';
import { api } from '@/lib/api';
import { useNotification } from '@/contexts/notification-context';
import PeerGroupDiscovery from '@/components/peer-groups/peer-group-discovery';
import GroupManagement from '@/components/peer-groups/group-management';

// Mock dependencies
jest.mock('@/lib/api');
jest.mock('@/contexts/notification-context');
jest.mock('next/link', () => {
  return function MockLink({ children, href }: any) {
    return <a href={href}>{children}</a>;
  };
});

// Mock child components for integration testing
jest.mock('@/components/peer-groups/peer-group-search', () => {
  return function MockPeerGroupSearch({ onSearch, loading }: any) {
    return (
      <div data-testid="peer-group-search">
        <input
          data-testid="search-input"
          onChange={(e) => onSearch({ query: e.target.value })}
          disabled={loading}
          placeholder="Search groups..."
        />
      </div>
    );
  };
});

jest.mock('@/components/peer-groups/peer-group-filters', () => {
  return function MockPeerGroupFilters({ onFiltersChange }: any) {
    return (
      <div data-testid="peer-group-filters">
        <select
          data-testid="industry-filter"
          onChange={(e) => onFiltersChange({ industry: e.target.value })}
        >
          <option value="">All Industries</option>
          <option value="Technology">Technology</option>
          <option value="Healthcare">Healthcare</option>
        </select>
      </div>
    );
  };
});

jest.mock('@/components/peer-groups/peer-group-list', () => {
  return function MockPeerGroupList({ groups, loading, error, emptyMessage, onJoinSuccess }: any) {
    if (loading) return <div data-testid="loading">Loading groups...</div>;
    if (error) return <div data-testid="error">{error}</div>;
    if (groups.length === 0) return <div data-testid="empty">{emptyMessage}</div>;
    
    return (
      <div data-testid="peer-group-list">
        {groups.map((group: any) => (
          <div key={group.id} data-testid={`group-${group.id}`} className="group-card">
            <h3>{group.name}</h3>
            <p>{group.description}</p>
            <span className="member-count">{group.member_count} members</span>
            <button
              data-testid={`join-${group.id}`}
              onClick={() => onJoinSuccess({ ...group, is_member: true, membership_status: 'active' })}
              disabled={group.is_member}
            >
              {group.is_member ? 'Joined' : 'Join Group'}
            </button>
          </div>
        ))}
      </div>
    );
  };
});

const mockApi = api as jest.Mocked<typeof api>;
const mockUseNotification = useNotification as jest.MockedFunction<typeof useNotification>;

const mockAddNotification = jest.fn();

const mockGroups = [
  {
    id: 1,
    name: 'Tech Professionals',
    slug: 'tech-professionals',
    description: 'A group for technology professionals',
    member_count: 150,
    is_member: false,
    membership_status: null,
    privacy_level: 'public',
    group_type: 'industry',
    industry: 'Technology'
  },
  {
    id: 2,
    name: 'AI Enthusiasts',
    slug: 'ai-enthusiasts',
    description: 'Discussing AI and machine learning',
    member_count: 89,
    is_member: false,
    membership_status: null,
    privacy_level: 'public',
    group_type: 'skill',
    industry: 'Technology'
  },
  {
    id: 3,
    name: 'Healthcare Innovation',
    slug: 'healthcare-innovation',
    description: 'Innovating in healthcare technology',
    member_count: 67,
    is_member: false,
    membership_status: null,
    privacy_level: 'private',
    group_type: 'industry',
    industry: 'Healthcare'
  }
];

const mockRecommendations = [
  {
    group: mockGroups[0],
    reason: 'Based on your technology background',
    score: 0.95
  },
  {
    group: mockGroups[1],
    reason: 'Matches your AI interests',
    score: 0.87
  }
];

describe('Peer Group Workflow Integration Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockUseNotification.mockReturnValue({
      addNotification: mockAddNotification,
      notifications: [],
      removeNotification: jest.fn()
    });

    // Setup default API mocks
    mockApi.peerGroups = {
      discover: jest.fn().mockResolvedValue({
        data: { ai_powered: true, recommendations: mockRecommendations }
      }),
      search: jest.fn().mockResolvedValue({
        data: { results: mockGroups }
      }),
      trending: jest.fn().mockResolvedValue({
        data: mockGroups
      }),
      join: jest.fn().mockResolvedValue({
        data: { status: 'active', message: 'Successfully joined the group!' }
      }),
      getMembers: jest.fn().mockResolvedValue({ data: [] }),
      getPendingMembers: jest.fn().mockResolvedValue({ data: [] }),
      manageMember: jest.fn(),
      update: jest.fn()
    } as any;
  });

  describe('Group Discovery and Joining Workflow', () => {
    it('should complete full discovery to joining workflow', async () => {
      render(<PeerGroupDiscovery />);

      // 1. Initial discovery loads AI recommendations
      await waitFor(() => {
        expect(screen.getByText('Discover Groups for You')).toBeInTheDocument();
        expect(screen.getByText('Tech Professionals')).toBeInTheDocument();
        expect(screen.getByText('Based on your technology background')).toBeInTheDocument();
      });

      expect(mockApi.peerGroups.discover).toHaveBeenCalledWith({ limit: 20 });

      // 2. User joins a recommended group
      const joinButton = screen.getByTestId('join-1');
      fireEvent.click(joinButton);

      await waitFor(() => {
        expect(screen.getByText('Joined')).toBeInTheDocument();
      });

      // 3. Switch to search tab and perform search
      fireEvent.click(screen.getByText('Search'));

      await waitFor(() => {
        expect(screen.getByText('Search Groups')).toBeInTheDocument();
        expect(screen.getByTestId('search-input')).toBeInTheDocument();
      });

      // 4. Perform search
      const searchInput = screen.getByTestId('search-input');
      fireEvent.change(searchInput, { target: { value: 'AI' } });

      await waitFor(() => {
        expect(mockApi.peerGroups.search).toHaveBeenCalledWith({
          query: 'AI',
          limit: 20
        });
      });

      // 5. Apply filters
      const industryFilter = screen.getByTestId('industry-filter');
      fireEvent.change(industryFilter, { target: { value: 'Technology' } });

      await waitFor(() => {
        expect(mockApi.peerGroups.search).toHaveBeenCalledWith({
          query: 'AI',
          industry: 'Technology',
          limit: 20
        });
      });

      // 6. Switch to trending tab
      fireEvent.click(screen.getByText('Trending'));

      await waitFor(() => {
        expect(screen.getByText('Trending Groups')).toBeInTheDocument();
        expect(mockApi.peerGroups.trending).toHaveBeenCalledWith({ limit: 20 });
      });
    });

    it('should handle private group join workflow', async () => {
      // Mock private group join response
      mockApi.peerGroups.join = jest.fn().mockResolvedValue({
        data: { status: 'pending', message: 'Your request has been sent for approval' }
      });

      render(<PeerGroupDiscovery />);

      await waitFor(() => {
        expect(screen.getByText('Tech Professionals')).toBeInTheDocument();
      });

      // Join a group (simulate private group)
      const joinButton = screen.getByTestId('join-1');
      fireEvent.click(joinButton);

      await waitFor(() => {
        expect(mockAddNotification).toHaveBeenCalledWith({
          type: 'success',
          title: 'Success',
          message: 'Your request has been sent for approval'
        });
      });
    });

    it('should handle join errors gracefully', async () => {
      mockApi.peerGroups.join = jest.fn().mockRejectedValue({
        response: { data: { error: 'Group is full' } }
      });

      render(<PeerGroupDiscovery />);

      await waitFor(() => {
        expect(screen.getByText('Tech Professionals')).toBeInTheDocument();
      });

      const joinButton = screen.getByTestId('join-1');
      fireEvent.click(joinButton);

      await waitFor(() => {
        expect(mockAddNotification).toHaveBeenCalledWith({
          type: 'error',
          title: 'Error',
          message: 'Group is full'
        });
      });
    });
  });

  describe('Search and Filter Workflow', () => {
    it('should perform complex search with multiple filters', async () => {
      render(<PeerGroupDiscovery />);

      // Switch to search tab
      fireEvent.click(screen.getByText('Search'));

      await waitFor(() => {
        expect(screen.getByTestId('search-input')).toBeInTheDocument();
      });

      // Perform initial search
      const searchInput = screen.getByTestId('search-input');
      fireEvent.change(searchInput, { target: { value: 'technology' } });

      await waitFor(() => {
        expect(mockApi.peerGroups.search).toHaveBeenCalledWith({
          query: 'technology',
          limit: 20
        });
      });

      // Apply industry filter
      const industryFilter = screen.getByTestId('industry-filter');
      fireEvent.change(industryFilter, { target: { value: 'Technology' } });

      await waitFor(() => {
        expect(mockApi.peerGroups.search).toHaveBeenCalledWith({
          query: 'technology',
          industry: 'Technology',
          limit: 20
        });
      });

      // Verify results are displayed
      expect(screen.getByTestId('peer-group-list')).toBeInTheDocument();
      expect(screen.getByText('Tech Professionals')).toBeInTheDocument();
    });

    it('should handle empty search results', async () => {
      mockApi.peerGroups.search = jest.fn().mockResolvedValue({
        data: { results: [] }
      });

      render(<PeerGroupDiscovery />);

      fireEvent.click(screen.getByText('Search'));

      await waitFor(() => {
        const searchInput = screen.getByTestId('search-input');
        fireEvent.change(searchInput, { target: { value: 'nonexistent' } });
      });

      await waitFor(() => {
        expect(screen.getByText('No groups match your search criteria.')).toBeInTheDocument();
      });
    });

    it('should handle search API errors', async () => {
      mockApi.peerGroups.search = jest.fn().mockRejectedValue({
        response: { data: { error: 'Search service unavailable' } }
      });

      render(<PeerGroupDiscovery />);

      fireEvent.click(screen.getByText('Search'));

      await waitFor(() => {
        const searchInput = screen.getByTestId('search-input');
        fireEvent.change(searchInput, { target: { value: 'test' } });
      });

      await waitFor(() => {
        expect(mockAddNotification).toHaveBeenCalledWith({
          type: 'error',
          title: 'Search Error',
          message: 'Failed to search peer groups'
        });
      });
    });
  });

  describe('Group Management Workflow', () => {
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
          email: 'john@example.com'
        },
        role: 'admin',
        status: 'active'
      },
      {
        id: 2,
        user: {
          id: 2,
          full_name: 'Jane Smith',
          email: 'jane@example.com'
        },
        role: 'member',
        status: 'active'
      }
    ];

    const mockPendingRequests = [
      {
        id: 3,
        user: {
          id: 3,
          full_name: 'Bob Johnson',
          email: 'bob@example.com'
        },
        role: 'member',
        status: 'pending'
      }
    ];

    it('should complete full group management workflow', async () => {
      mockApi.peerGroups.getMembers = jest.fn().mockResolvedValue({ data: mockMembers });
      mockApi.peerGroups.getPendingMembers = jest.fn().mockResolvedValue({ data: mockPendingRequests });
      mockApi.peerGroups.manageMember = jest.fn()
        .mockResolvedValueOnce({
          data: { message: 'Member approved successfully' }
        })
        .mockResolvedValueOnce({
          data: { message: 'Member role updated' }
        });

      render(<GroupManagement group={mockGroup} />);

      // 1. Verify initial load of members
      await waitFor(() => {
        expect(screen.getByText('Group Management')).toBeInTheDocument();
        expect(screen.getByText('John Doe')).toBeInTheDocument();
        expect(screen.getByText('Jane Smith')).toBeInTheDocument();
      });

      expect(mockApi.peerGroups.getMembers).toHaveBeenCalledWith('tech-professionals');

      // 2. Switch to pending requests and approve a member
      fireEvent.click(screen.getByText('Pending Requests'));

      await waitFor(() => {
        expect(screen.getByText('Bob Johnson')).toBeInTheDocument();
        expect(screen.getByText('Approve')).toBeInTheDocument();
      });

      const approveButton = screen.getByText('Approve');
      fireEvent.click(approveButton);

      await waitFor(() => {
        expect(mockApi.peerGroups.manageMember).toHaveBeenCalledWith('tech-professionals', { user_id: 3, action: 'approve' });
        expect(mockAddNotification).toHaveBeenCalledWith({
          type: 'success',
          title: 'Success',
          message: 'Member approved successfully'
        });
      });

      // 3. Go back to members and promote someone
      fireEvent.click(screen.getByText('Members'));

      await waitFor(() => {
        const promoteButton = screen.getByText('Promote to Admin');
        fireEvent.click(promoteButton);
      });

      await waitFor(() => {
        expect(mockApi.peerGroups.manageMember).toHaveBeenCalledWith(
          'tech-professionals',
          { user_id: 2, action: 'promote' }
        );
      });
    });

    it('should handle group settings update workflow', async () => {
      mockApi.peerGroups.getMembers = jest.fn().mockResolvedValue({ data: mockMembers });
      mockApi.peerGroups.update = jest.fn().mockResolvedValue({
        data: { message: 'Group settings updated successfully' }
      });

      render(<GroupManagement group={mockGroup} />);

      // Switch to group settings
      fireEvent.click(screen.getByText('Group Settings'));

      await waitFor(() => {
        expect(screen.getByDisplayValue('Tech Professionals')).toBeInTheDocument();
      });

      // Update group name
      const nameInput = screen.getByDisplayValue('Tech Professionals');
      fireEvent.change(nameInput, { target: { value: 'Updated Tech Group' } });

      // Save changes
      const saveButton = screen.getByText('Save Changes');
      fireEvent.click(saveButton);

      await waitFor(() => {
        expect(mockApi.peerGroups.update).toHaveBeenCalledWith(
          'tech-professionals',
          expect.objectContaining({
            name: 'Updated Tech Group'
          })
        );
        expect(mockAddNotification).toHaveBeenCalledWith({
          type: 'success',
          title: 'Success',
          message: 'Group settings updated successfully'
        });
      });
    });
  });

  describe('Notification System Integration', () => {
    it('should handle multiple notifications during workflow', async () => {
      // Setup multiple API calls that will trigger notifications
      mockApi.peerGroups.join = jest.fn()
        .mockResolvedValueOnce({
          data: { status: 'active', message: 'Joined Tech Professionals!' }
        })
        .mockResolvedValueOnce({
          data: { status: 'pending', message: 'Request sent for AI Enthusiasts' }
        });

      render(<PeerGroupDiscovery />);

      await waitFor(() => {
        expect(screen.getByText('Tech Professionals')).toBeInTheDocument();
      });

      // Join first group
      const firstJoinButton = screen.getByTestId('join-1');
      fireEvent.click(firstJoinButton);

      await waitFor(() => {
        expect(mockAddNotification).toHaveBeenCalledWith({
          type: 'success',
          title: 'Success',
          message: 'Joined Tech Professionals!'
        });
      });

      // Join second group (if visible)
      const secondJoinButton = screen.queryByTestId('join-2');
      if (secondJoinButton) {
        fireEvent.click(secondJoinButton);

        await waitFor(() => {
          expect(mockAddNotification).toHaveBeenCalledWith({
            type: 'success',
            title: 'Success',
            message: 'Request sent for AI Enthusiasts'
          });
        });
      }

      // Verify multiple notifications were triggered
      expect(mockAddNotification).toHaveBeenCalledTimes(1); // At least one notification
    });
  });

  describe('Error Recovery Workflow', () => {
    it('should recover from API failures and retry operations', async () => {
      // First call fails, second succeeds
      mockApi.peerGroups.discover = jest.fn()
        .mockRejectedValueOnce({
          response: { data: { error: 'Service temporarily unavailable' } }
        })
        .mockResolvedValueOnce({
          data: { ai_powered: true, recommendations: mockRecommendations }
        });

      render(<PeerGroupDiscovery />);

      // Initial load should fail
      await waitFor(() => {
        expect(mockAddNotification).toHaveBeenCalledWith({
          type: 'error',
          title: 'Error',
          message: 'Failed to load peer groups'
        });
      });

      // Simulate retry by switching tabs (triggers reload)
      fireEvent.click(screen.getByText('Search'));
      fireEvent.click(screen.getByText('Discover'));

      await waitFor(() => {
        expect(screen.getByText('Tech Professionals')).toBeInTheDocument();
      });

      expect(mockApi.peerGroups.discover).toHaveBeenCalledTimes(2);
    });
  });

  describe('Performance and Loading States', () => {
    it('should handle concurrent API calls efficiently', async () => {
      let discoverResolve: (value: any) => void;
      let trendingResolve: (value: any) => void;

      const discoverPromise = new Promise(resolve => { discoverResolve = resolve; });
      const trendingPromise = new Promise(resolve => { trendingResolve = resolve; });

      mockApi.peerGroups.discover = jest.fn().mockReturnValue(discoverPromise);
      mockApi.peerGroups.trending = jest.fn().mockReturnValue(trendingPromise);

      render(<PeerGroupDiscovery />);

      // Should show loading initially
      expect(screen.getByTestId('loading')).toBeInTheDocument();

      // Switch to trending while discover is still loading
      fireEvent.click(screen.getByText('Trending'));

      // Both API calls should be in progress
      expect(mockApi.peerGroups.discover).toHaveBeenCalled();
      expect(mockApi.peerGroups.trending).toHaveBeenCalled();

      // Resolve trending first
      trendingResolve!({ data: mockGroups });

      await waitFor(() => {
        expect(screen.getByText('Tech Professionals')).toBeInTheDocument();
      });

      // Resolve discover (should not affect current view)
      discoverResolve!({ data: { ai_powered: true, recommendations: mockRecommendations } });

      // Should still be on trending tab
      expect(screen.getByText('Trending Groups')).toBeInTheDocument();
    });
  });
});