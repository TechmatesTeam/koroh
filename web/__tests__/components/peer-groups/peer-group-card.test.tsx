import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { jest } from '@jest/globals';
import PeerGroupCard from '@/components/peer-groups/peer-group-card';
import { api } from '@/lib/api';
import { useNotification } from '@/contexts/notification-context';

// Mock dependencies
jest.mock('@/lib/api');
jest.mock('@/contexts/notification-context');
jest.mock('next/link', () => {
  return function MockLink({ children, href }: any) {
    return <a href={href}>{children}</a>;
  };
});

const mockApi = api as jest.Mocked<typeof api>;
const mockUseNotification = useNotification as jest.MockedFunction<typeof useNotification>;

const mockAddNotification = jest.fn();

const mockGroup = {
  id: 1,
  name: 'Tech Professionals',
  slug: 'tech-professionals',
  description: 'A group for technology professionals to connect and share knowledge',
  tagline: 'Connecting tech minds',
  image: 'https://example.com/group-image.jpg',
  privacy_level: 'public',
  group_type: 'industry',
  industry: 'Technology',
  member_count: 150,
  post_count: 45,
  activity_score: 85,
  is_member: false,
  membership_status: null,
  skills: ['JavaScript', 'Python', 'React', 'Node.js', 'AI'],
  recent_members: [
    {
      id: 1,
      full_name: 'John Doe',
      profile_picture: 'https://example.com/john.jpg'
    },
    {
      id: 2,
      full_name: 'Jane Smith',
      profile_picture: 'https://example.com/jane.jpg'
    },
    {
      id: 3,
      full_name: 'Bob Johnson',
      profile_picture: null
    },
    {
      id: 4,
      full_name: 'Alice Brown',
      profile_picture: 'https://example.com/alice.jpg'
    }
  ]
};

describe('PeerGroupCard', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockUseNotification.mockReturnValue({
      addNotification: mockAddNotification,
      notifications: [],
      removeNotification: jest.fn()
    });
  });

  describe('Group Information Display', () => {
    it('should display group basic information', () => {
      render(<PeerGroupCard group={mockGroup} />);

      expect(screen.getByText('Tech Professionals')).toBeInTheDocument();
      expect(screen.getByText('Connecting tech minds')).toBeInTheDocument();
      expect(screen.getByText('A group for technology professionals to connect and share knowledge')).toBeInTheDocument();
    });

    it('should display group image when available', () => {
      render(<PeerGroupCard group={mockGroup} />);

      const image = screen.getByAltText('Tech Professionals');
      expect(image).toBeInTheDocument();
      expect(image).toHaveAttribute('src', 'https://example.com/group-image.jpg');
    });

    it('should display group initial when no image available', () => {
      const groupWithoutImage = { ...mockGroup, image: null };
      render(<PeerGroupCard group={groupWithoutImage} />);

      expect(screen.getByText('T')).toBeInTheDocument();
    });

    it('should display privacy and type badges', () => {
      render(<PeerGroupCard group={mockGroup} />);

      expect(screen.getByText('public')).toBeInTheDocument();
      expect(screen.getByText('industry')).toBeInTheDocument();
      expect(screen.getByText('Technology')).toBeInTheDocument();
    });

    it('should display member and post counts', () => {
      render(<PeerGroupCard group={mockGroup} />);

      expect(screen.getByText('150 members')).toBeInTheDocument();
      expect(screen.getByText('45 posts')).toBeInTheDocument();
    });

    it('should display activity indicator for active groups', () => {
      render(<PeerGroupCard group={mockGroup} />);

      expect(screen.getByText('Active')).toBeInTheDocument();
    });

    it('should display skills with overflow handling', () => {
      render(<PeerGroupCard group={mockGroup} />);

      expect(screen.getByText('JavaScript')).toBeInTheDocument();
      expect(screen.getByText('Python')).toBeInTheDocument();
      expect(screen.getByText('React')).toBeInTheDocument();
      expect(screen.getByText('+2 more')).toBeInTheDocument();
    });

    it('should display recent members with overflow', () => {
      render(<PeerGroupCard group={mockGroup} />);

      // Should show first 3 members and +1 indicator
      const avatars = screen.getAllByRole('img');
      const memberAvatars = avatars.filter(img => 
        img.getAttribute('alt')?.includes('John Doe') ||
        img.getAttribute('alt')?.includes('Jane Smith') ||
        img.getAttribute('alt')?.includes('Bob Johnson')
      );
      
      expect(memberAvatars).toHaveLength(2); // Only those with images
      expect(screen.getByText('+1')).toBeInTheDocument();
    });
  });

  describe('Group Link', () => {
    it('should link to group page', () => {
      render(<PeerGroupCard group={mockGroup} />);

      const link = screen.getByRole('link');
      expect(link).toHaveAttribute('href', '/peer-groups/tech-professionals');
    });
  });

  describe('Join Functionality', () => {
    beforeEach(() => {
      mockApi.peerGroups = {
        join: jest.fn()
      } as any;
    });

    it('should show join button for non-members', () => {
      render(<PeerGroupCard group={mockGroup} />);

      expect(screen.getByText('Join Group')).toBeInTheDocument();
    });

    it('should show joined status for members', () => {
      const memberGroup = { ...mockGroup, is_member: true };
      render(<PeerGroupCard group={memberGroup} />);

      expect(screen.getByText('Joined')).toBeInTheDocument();
    });

    it('should show pending status for pending requests', () => {
      const pendingGroup = { ...mockGroup, membership_status: 'pending' };
      render(<PeerGroupCard group={pendingGroup} />);

      expect(screen.getByText('Pending Approval')).toBeInTheDocument();
    });

    it('should show request to join for private groups', () => {
      const privateGroup = { ...mockGroup, privacy_level: 'private' };
      render(<PeerGroupCard group={privateGroup} />);

      expect(screen.getByText('Request to Join')).toBeInTheDocument();
    });

    it('should handle successful group joining', async () => {
      mockApi.peerGroups.join = jest.fn().mockResolvedValue({
        data: {
          status: 'active',
          message: 'Successfully joined the group!'
        }
      });

      const onJoinSuccess = jest.fn();
      render(<PeerGroupCard group={mockGroup} onJoinSuccess={onJoinSuccess} />);

      const joinButton = screen.getByText('Join Group');
      fireEvent.click(joinButton);

      await waitFor(() => {
        expect(mockApi.peerGroups.join).toHaveBeenCalledWith('tech-professionals');
        expect(mockAddNotification).toHaveBeenCalledWith({
          type: 'success',
          title: 'Success',
          message: 'Successfully joined the group!'
        });
        expect(onJoinSuccess).toHaveBeenCalledWith({
          ...mockGroup,
          membership_status: 'active',
          is_member: true
        });
      });

      // Button should now show "Joined"
      expect(screen.getByText('Joined')).toBeInTheDocument();
    });

    it('should handle pending approval for private groups', async () => {
      mockApi.peerGroups.join = jest.fn().mockResolvedValue({
        data: {
          status: 'pending',
          message: 'Your request has been sent for approval'
        }
      });

      const privateGroup = { ...mockGroup, privacy_level: 'private' };
      render(<PeerGroupCard group={privateGroup} />);

      const joinButton = screen.getByText('Request to Join');
      fireEvent.click(joinButton);

      await waitFor(() => {
        expect(mockApi.peerGroups.join).toHaveBeenCalledWith('tech-professionals');
        expect(mockAddNotification).toHaveBeenCalledWith({
          type: 'success',
          title: 'Success',
          message: 'Your request has been sent for approval'
        });
      });

      // Button should now show "Pending Approval"
      expect(screen.getByText('Pending Approval')).toBeInTheDocument();
    });

    it('should handle join errors', async () => {
      mockApi.peerGroups.join = jest.fn().mockRejectedValue({
        response: {
          data: {
            error: 'Group is full'
          }
        }
      });

      render(<PeerGroupCard group={mockGroup} />);

      const joinButton = screen.getByText('Join Group');
      fireEvent.click(joinButton);

      await waitFor(() => {
        expect(mockAddNotification).toHaveBeenCalledWith({
          type: 'error',
          title: 'Error',
          message: 'Group is full'
        });
      });

      // Button should still show "Join Group"
      expect(screen.getByText('Join Group')).toBeInTheDocument();
    });

    it('should show loading state during join request', async () => {
      let resolvePromise: (value: any) => void;
      const promise = new Promise(resolve => {
        resolvePromise = resolve;
      });

      mockApi.peerGroups.join = jest.fn().mockReturnValue(promise);

      render(<PeerGroupCard group={mockGroup} />);

      const joinButton = screen.getByText('Join Group');
      fireEvent.click(joinButton);

      // Should show loading state
      expect(screen.getByText('Joining...')).toBeInTheDocument();

      // Resolve the promise
      resolvePromise!({
        data: {
          status: 'active',
          message: 'Successfully joined!'
        }
      });

      await waitFor(() => {
        expect(screen.getByText('Joined')).toBeInTheDocument();
      });
    });

    it('should disable join button when already member', () => {
      const memberGroup = { ...mockGroup, is_member: true };
      render(<PeerGroupCard group={memberGroup} />);

      const joinButton = screen.getByText('Joined');
      expect(joinButton).toBeDisabled();
    });

    it('should disable join button when request is pending', () => {
      const pendingGroup = { ...mockGroup, membership_status: 'pending' };
      render(<PeerGroupCard group={pendingGroup} />);

      const joinButton = screen.getByText('Pending Approval');
      expect(joinButton).toBeDisabled();
    });

    it('should hide join button when showJoinButton is false', () => {
      render(<PeerGroupCard group={mockGroup} showJoinButton={false} />);

      expect(screen.queryByText('Join Group')).not.toBeInTheDocument();
    });
  });

  describe('Badge Colors', () => {
    it('should apply correct colors for privacy levels', () => {
      const publicGroup = { ...mockGroup, privacy_level: 'public' };
      const privateGroup = { ...mockGroup, privacy_level: 'private' };
      const restrictedGroup = { ...mockGroup, privacy_level: 'restricted' };

      const { rerender } = render(<PeerGroupCard group={publicGroup} />);
      expect(screen.getByText('public')).toHaveClass('bg-green-100', 'text-green-800');

      rerender(<PeerGroupCard group={privateGroup} />);
      expect(screen.getByText('private')).toHaveClass('bg-red-100', 'text-red-800');

      rerender(<PeerGroupCard group={restrictedGroup} />);
      expect(screen.getByText('restricted')).toHaveClass('bg-yellow-100', 'text-yellow-800');
    });

    it('should apply correct colors for group types', () => {
      const industryGroup = { ...mockGroup, group_type: 'industry' };
      const skillGroup = { ...mockGroup, group_type: 'skill' };
      const locationGroup = { ...mockGroup, group_type: 'location' };
      const experienceGroup = { ...mockGroup, group_type: 'experience' };

      const { rerender } = render(<PeerGroupCard group={industryGroup} />);
      expect(screen.getByText('industry')).toHaveClass('bg-blue-100', 'text-blue-800');

      rerender(<PeerGroupCard group={skillGroup} />);
      expect(screen.getByText('skill')).toHaveClass('bg-purple-100', 'text-purple-800');

      rerender(<PeerGroupCard group={locationGroup} />);
      expect(screen.getByText('location')).toHaveClass('bg-orange-100', 'text-orange-800');

      rerender(<PeerGroupCard group={experienceGroup} />);
      expect(screen.getByText('experience')).toHaveClass('bg-indigo-100', 'text-indigo-800');
    });
  });

  describe('Edge Cases', () => {
    it('should handle group without tagline', () => {
      const groupWithoutTagline = { ...mockGroup, tagline: null };
      render(<PeerGroupCard group={groupWithoutTagline} />);

      expect(screen.getByText('Tech Professionals')).toBeInTheDocument();
      expect(screen.queryByText('Connecting tech minds')).not.toBeInTheDocument();
    });

    it('should handle group without industry', () => {
      const groupWithoutIndustry = { ...mockGroup, industry: null };
      render(<PeerGroupCard group={groupWithoutIndustry} />);

      expect(screen.queryByText('Technology')).not.toBeInTheDocument();
    });

    it('should handle group without skills', () => {
      const groupWithoutSkills = { ...mockGroup, skills: [] };
      render(<PeerGroupCard group={groupWithoutSkills} />);

      expect(screen.queryByText('JavaScript')).not.toBeInTheDocument();
    });

    it('should handle group without recent members', () => {
      const groupWithoutMembers = { ...mockGroup, recent_members: [] };
      render(<PeerGroupCard group={groupWithoutMembers} />);

      expect(screen.queryByText('+1')).not.toBeInTheDocument();
    });

    it('should handle low activity score', () => {
      const inactiveGroup = { ...mockGroup, activity_score: 0 };
      render(<PeerGroupCard group={inactiveGroup} />);

      expect(screen.queryByText('Active')).not.toBeInTheDocument();
    });
  });
});