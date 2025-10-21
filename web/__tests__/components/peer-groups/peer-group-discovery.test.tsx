import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { jest } from '@jest/globals';
import PeerGroupDiscovery from '@/components/peer-groups/peer-group-discovery';
import { api } from '@/lib/api';
import { useNotification } from '@/contexts/notification-context';

// Mock dependencies
jest.mock('@/lib/api');
jest.mock('@/contexts/notification-context');
jest.mock('@/components/peer-groups/peer-group-search', () => {
  return function MockPeerGroupSearch({ onSearch, loading }: any) {
    return (
      <div data-testid="peer-group-search">
        <input
          data-testid="search-input"
          onChange={(e) => onSearch({ query: e.target.value })}
          disabled={loading}
        />
      </div>
    );
  };
});
jest.mock('@/components/peer-groups/peer-group-filters', () => {
  return function MockPeerGroupFilters({ onFiltersChange }: any) {
    return (
      <div data-testid="peer-group-filters">
        <button
          data-testid="filter-industry"
          onClick={() => onFiltersChange({ industry: 'Technology' })}
        >
          Filter by Technology
        </button>
      </div>
    );
  };
});
jest.mock('@/components/peer-groups/peer-group-list', () => {
  return function MockPeerGroupList({ groups, loading, error, emptyMessage, onJoinSuccess }: any) {
    if (loading) return <div data-testid="loading">Loading...</div>;
    if (error) return <div data-testid="error">{error}</div>;
    if (groups.length === 0) return <div data-testid="empty">{emptyMessage}</div>;
    
    return (
      <div data-testid="peer-group-list">
        {groups.map((group: any) => (
          <div key={group.id} data-testid={`group-${group.id}`}>
            {group.name}
            <button
              data-testid={`join-${group.id}`}
              onClick={() => onJoinSuccess({ ...group, is_member: true })}
            >
              Join
            </button>
          </div>
        ))}
      </div>
    );
  };
});

// Mock PeerGroupCard component used in discovery
function PeerGroupCard({ group, onJoinSuccess }: any) {
  return (
    <div data-testid={`group-card-${group.id}`}>
      <h3>{group.name}</h3>
      <button
        data-testid={`join-${group.id}`}
        onClick={() => onJoinSuccess({ ...group, is_member: true })}
      >
        Join
      </button>
    </div>
  );
}

// Make PeerGroupCard available globally for the component
(global as any).PeerGroupCard = PeerGroupCard;

const mockApi = api as jest.Mocked<typeof api>;
const mockUseNotification = useNotification as jest.MockedFunction<typeof useNotification>;

const mockAddNotification = jest.fn();

const mockGroups = [
  {
    id: 1,
    name: 'Tech Professionals',
    slug: 'tech-professionals',
    description: 'A group for technology professionals',
    is_member: false,
    membership_status: null
  },
  {
    id: 2,
    name: 'AI Enthusiasts',
    slug: 'ai-enthusiasts',
    description: 'Discussing AI and machine learning',
    is_member: false,
    membership_status: null
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

describe('PeerGroupDiscovery', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockUseNotification.mockReturnValue({
      addNotification: mockAddNotification,
      notifications: [],
      removeNotification: jest.fn()
    });
  });

  describe('Tab Navigation', () => {
    it('should render all tabs', () => {
      render(<PeerGroupDiscovery />);
      
      expect(screen.getByText('Discover')).toBeInTheDocument();
      expect(screen.getByText('Search')).toBeInTheDocument();
      expect(screen.getByText('Trending')).toBeInTheDocument();
    });

    it('should switch between tabs', async () => {
      mockApi.peerGroups = {
        discover: jest.fn().mockResolvedValue({
          data: { ai_powered: true, recommendations: mockRecommendations }
        }),
        search: jest.fn().mockResolvedValue({
          data: { results: mockGroups }
        }),
        trending: jest.fn().mockResolvedValue({
          data: mockGroups
        })
      } as any;

      render(<PeerGroupDiscovery />);

      // Click search tab
      fireEvent.click(screen.getByText('Search'));
      await waitFor(() => {
        expect(screen.getByText('Search Groups')).toBeInTheDocument();
      });

      // Click trending tab
      fireEvent.click(screen.getByText('Trending'));
      await waitFor(() => {
        expect(screen.getByText('Trending Groups')).toBeInTheDocument();
      });
    });
  });

  describe('Discover Tab', () => {
    it('should load AI-powered recommendations', async () => {
      mockApi.peerGroups = {
        discover: jest.fn().mockResolvedValue({
          data: { ai_powered: true, recommendations: mockRecommendations }
        })
      } as any;

      render(<PeerGroupDiscovery />);

      await waitFor(() => {
        expect(screen.getByText('Discover Groups for You')).toBeInTheDocument();
        expect(screen.getByText('Based on your technology background')).toBeInTheDocument();
        expect(screen.getByText('Matches your AI interests')).toBeInTheDocument();
      });

      expect(mockApi.peerGroups.discover).toHaveBeenCalledWith({ limit: 20 });
    });

    it('should handle non-AI recommendations', async () => {
      mockApi.peerGroups = {
        discover: jest.fn().mockResolvedValue({
          data: { 
            ai_powered: false, 
            recommendations: mockGroups.map(group => ({ group }))
          }
        })
      } as any;

      render(<PeerGroupDiscovery />);

      await waitFor(() => {
        expect(screen.getByTestId('peer-group-list')).toBeInTheDocument();
      });
    });

    it('should handle discover API errors', async () => {
      mockApi.peerGroups = {
        discover: jest.fn().mockRejectedValue({
          response: { data: { error: 'Failed to load recommendations' } }
        })
      } as any;

      render(<PeerGroupDiscovery />);

      await waitFor(() => {
        expect(mockAddNotification).toHaveBeenCalledWith({
          type: 'error',
          title: 'Error',
          message: 'Failed to load peer groups'
        });
      });
    });
  });

  describe('Search Tab', () => {
    beforeEach(() => {
      mockApi.peerGroups = {
        discover: jest.fn().mockResolvedValue({
          data: { ai_powered: false, recommendations: [] }
        }),
        search: jest.fn().mockResolvedValue({
          data: { results: mockGroups }
        })
      } as any;
    });

    it('should perform search when query is entered', async () => {
      render(<PeerGroupDiscovery />);

      // Switch to search tab
      fireEvent.click(screen.getByText('Search'));

      await waitFor(() => {
        expect(screen.getByTestId('search-input')).toBeInTheDocument();
      });

      // Enter search query
      fireEvent.change(screen.getByTestId('search-input'), {
        target: { value: 'technology' }
      });

      await waitFor(() => {
        expect(mockApi.peerGroups.search).toHaveBeenCalledWith({
          query: 'technology',
          limit: 20
        });
      });
    });

    it('should apply filters', async () => {
      render(<PeerGroupDiscovery />);

      // Switch to search tab
      fireEvent.click(screen.getByText('Search'));

      await waitFor(() => {
        expect(screen.getByTestId('filter-industry')).toBeInTheDocument();
      });

      // Apply filter
      fireEvent.click(screen.getByTestId('filter-industry'));

      await waitFor(() => {
        expect(mockApi.peerGroups.search).toHaveBeenCalledWith({
          industry: 'Technology',
          limit: 20
        });
      });
    });

    it('should handle search errors', async () => {
      mockApi.peerGroups.search = jest.fn().mockRejectedValue({
        response: { data: { error: 'Search failed' } }
      });

      render(<PeerGroupDiscovery />);

      // Switch to search tab and search
      fireEvent.click(screen.getByText('Search'));
      
      await waitFor(() => {
        fireEvent.change(screen.getByTestId('search-input'), {
          target: { value: 'test' }
        });
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

  describe('Trending Tab', () => {
    it('should load trending groups', async () => {
      mockApi.peerGroups = {
        discover: jest.fn().mockResolvedValue({
          data: { ai_powered: false, recommendations: [] }
        }),
        trending: jest.fn().mockResolvedValue({
          data: mockGroups
        })
      } as any;

      render(<PeerGroupDiscovery />);

      // Switch to trending tab
      fireEvent.click(screen.getByText('Trending'));

      await waitFor(() => {
        expect(screen.getByText('Trending Groups')).toBeInTheDocument();
        expect(mockApi.peerGroups.trending).toHaveBeenCalledWith({ limit: 20 });
      });
    });
  });

  describe('Group Joining', () => {
    it('should handle successful group joining', async () => {
      mockApi.peerGroups = {
        discover: jest.fn().mockResolvedValue({
          data: { ai_powered: false, recommendations: mockGroups.map(g => ({ group: g })) }
        })
      } as any;

      render(<PeerGroupDiscovery />);

      await waitFor(() => {
        expect(screen.getByTestId('join-1')).toBeInTheDocument();
      });

      // Join a group
      fireEvent.click(screen.getByTestId('join-1'));

      await waitFor(() => {
        // Verify the group state was updated
        expect(screen.getByTestId('group-1')).toBeInTheDocument();
      });
    });
  });

  describe('Loading States', () => {
    it('should show loading state during API calls', async () => {
      let resolvePromise: (value: any) => void;
      const promise = new Promise(resolve => {
        resolvePromise = resolve;
      });

      mockApi.peerGroups = {
        discover: jest.fn().mockReturnValue(promise)
      } as any;

      render(<PeerGroupDiscovery />);

      // Should show loading initially
      expect(screen.getByTestId('loading')).toBeInTheDocument();

      // Resolve the promise
      resolvePromise!({
        data: { ai_powered: false, recommendations: [] }
      });

      await waitFor(() => {
        expect(screen.queryByTestId('loading')).not.toBeInTheDocument();
      });
    });
  });
});