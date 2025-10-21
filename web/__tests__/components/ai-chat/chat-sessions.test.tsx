import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ChatSessions } from '@/components/ai-chat/chat-sessions';
import { useAuth } from '@/contexts/auth-context';
import { useNotifications } from '@/contexts/notification-context';
import { api } from '@/lib/api';

// Mock dependencies
jest.mock('@/contexts/auth-context');
jest.mock('@/contexts/notification-context');
jest.mock('@/lib/api');

const mockUseAuth = useAuth as jest.MockedFunction<typeof useAuth>;
const mockUseNotifications = useNotifications as jest.MockedFunction<typeof useNotifications>;
const mockApi = api as jest.Mocked<typeof api>;

describe('ChatSessions Component', () => {
  const mockUser = {
    id: '1',
    email: 'test@example.com',
    first_name: 'Test',
    last_name: 'User',
    is_verified: true,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  };

  const mockAddNotification = jest.fn();
  const mockOnSessionSelect = jest.fn();

  const mockSessions = [
    {
      id: 'session-1',
      title: 'Career Advice Chat',
      created_at: '2024-01-01T10:00:00Z',
      updated_at: '2024-01-01T10:30:00Z',
      is_active: true,
      message_count: 5,
      last_message: {
        content: 'Thank you for the advice!',
        role: 'user',
        created_at: '2024-01-01T10:30:00Z',
      },
    },
    {
      id: 'session-2',
      title: 'Portfolio Generation',
      created_at: '2024-01-01T09:00:00Z',
      updated_at: '2024-01-01T09:15:00Z',
      is_active: true,
      message_count: 3,
      last_message: {
        content: 'I can help you create a portfolio!',
        role: 'assistant',
        created_at: '2024-01-01T09:15:00Z',
      },
    },
  ];

  beforeEach(() => {
    jest.clearAllMocks();
    
    mockUseAuth.mockReturnValue({
      user: mockUser,
      login: jest.fn(),
      logout: jest.fn(),
      register: jest.fn(),
      isLoading: false,
      error: null,
    });

    mockUseNotifications.mockReturnValue({
      notifications: [],
      addNotification: mockAddNotification,
      removeNotification: jest.fn(),
      clearNotifications: jest.fn(),
    });

    mockApi.ai.getSessions.mockResolvedValue({
      data: { sessions: mockSessions, count: mockSessions.length },
    });
  });

  describe('Session List Display', () => {
    it('renders loading state initially', () => {
      render(<ChatSessions onSessionSelect={mockOnSessionSelect} />);
      
      expect(screen.getByText('Chat Sessions')).toBeInTheDocument();
      // Check for loading skeletons
      expect(screen.getAllByRole('generic')).toHaveLength(expect.any(Number));
    });

    it('displays sessions after loading', async () => {
      render(<ChatSessions onSessionSelect={mockOnSessionSelect} />);
      
      await waitFor(() => {
        expect(screen.getByText('Career Advice Chat')).toBeInTheDocument();
        expect(screen.getByText('Portfolio Generation')).toBeInTheDocument();
      });
    });

    it('shows session details correctly', async () => {
      render(<ChatSessions onSessionSelect={mockOnSessionSelect} />);
      
      await waitFor(() => {
        expect(screen.getByText('Career Advice Chat')).toBeInTheDocument();
        expect(screen.getByText('Thank you for the advice!')).toBeInTheDocument();
        expect(screen.getByText('5 messages')).toBeInTheDocument();
      });
    });

    it('displays empty state when no sessions exist', async () => {
      mockApi.ai.getSessions.mockResolvedValue({
        data: { sessions: [], count: 0 },
      });
      
      render(<ChatSessions onSessionSelect={mockOnSessionSelect} />);
      
      await waitFor(() => {
        expect(screen.getByText('No chat sessions yet')).toBeInTheDocument();
        expect(screen.getByText('Start a conversation with Koroh AI!')).toBeInTheDocument();
      });
    });

    it('handles loading error gracefully', async () => {
      mockApi.ai.getSessions.mockRejectedValue(new Error('Network error'));
      
      render(<ChatSessions onSessionSelect={mockOnSessionSelect} />);
      
      await waitFor(() => {
        expect(mockAddNotification).toHaveBeenCalledWith({
          type: 'error',
          message: 'Failed to load chat sessions',
        });
      });
    });
  });

  describe('Session Selection', () => {
    it('calls onSessionSelect when session is clicked', async () => {
      const user = userEvent.setup();
      render(<ChatSessions onSessionSelect={mockOnSessionSelect} />);
      
      await waitFor(() => {
        expect(screen.getByText('Career Advice Chat')).toBeInTheDocument();
      });
      
      const sessionCard = screen.getByText('Career Advice Chat').closest('div');
      await user.click(sessionCard!);
      
      expect(mockOnSessionSelect).toHaveBeenCalledWith('session-1');
    });

    it('highlights selected session', async () => {
      render(<ChatSessions onSessionSelect={mockOnSessionSelect} selectedSessionId="session-1" />);
      
      await waitFor(() => {
        const selectedSession = screen.getByText('Career Advice Chat').closest('div');
        expect(selectedSession).toHaveClass('border-blue-500', 'bg-blue-50');
      });
    });

    it('does not highlight unselected sessions', async () => {
      render(<ChatSessions onSessionSelect={mockOnSessionSelect} selectedSessionId="session-1" />);
      
      await waitFor(() => {
        const unselectedSession = screen.getByText('Portfolio Generation').closest('div');
        expect(unselectedSession).toHaveClass('border-gray-200');
        expect(unselectedSession).not.toHaveClass('border-blue-500');
      });
    });
  });

  describe('Session Management', () => {
    it('creates new session when button is clicked', async () => {
      const user = userEvent.setup();
      const newSession = {
        id: 'new-session',
        title: '',
        created_at: '2024-01-01T11:00:00Z',
        updated_at: '2024-01-01T11:00:00Z',
        is_active: true,
        message_count: 0,
      };

      mockApi.ai.createSession.mockResolvedValue({ data: newSession });
      
      render(<ChatSessions onSessionSelect={mockOnSessionSelect} />);
      
      await waitFor(() => {
        expect(screen.getByText('Career Advice Chat')).toBeInTheDocument();
      });
      
      const createButton = screen.getByRole('button', { name: /plus/i });
      await user.click(createButton);
      
      expect(mockApi.ai.createSession).toHaveBeenCalled();
      
      await waitFor(() => {
        expect(mockOnSessionSelect).toHaveBeenCalledWith('new-session');
        expect(mockAddNotification).toHaveBeenCalledWith({
          type: 'success',
          message: 'New chat session created',
        });
      });
    });

    it('handles session creation error', async () => {
      const user = userEvent.setup();
      
      mockApi.ai.createSession.mockRejectedValue(new Error('Creation failed'));
      
      render(<ChatSessions onSessionSelect={mockOnSessionSelect} />);
      
      await waitFor(() => {
        expect(screen.getByText('Career Advice Chat')).toBeInTheDocument();
      });
      
      const createButton = screen.getByRole('button', { name: /plus/i });
      await user.click(createButton);
      
      await waitFor(() => {
        expect(mockAddNotification).toHaveBeenCalledWith({
          type: 'error',
          message: 'Failed to create new session',
        });
      });
    });

    it('deletes session when delete button is clicked', async () => {
      const user = userEvent.setup();
      
      // Mock window.confirm
      const originalConfirm = window.confirm;
      window.confirm = jest.fn(() => true);
      
      mockApi.ai.deleteSession.mockResolvedValue({ data: { message: 'Deleted' } });
      
      render(<ChatSessions onSessionSelect={mockOnSessionSelect} selectedSessionId="session-1" />);
      
      await waitFor(() => {
        expect(screen.getByText('Career Advice Chat')).toBeInTheDocument();
      });
      
      const deleteButtons = screen.getAllByRole('button', { name: /trash/i });
      await user.click(deleteButtons[0]);
      
      expect(window.confirm).toHaveBeenCalledWith('Are you sure you want to delete this chat session?');
      expect(mockApi.ai.deleteSession).toHaveBeenCalledWith('session-1');
      
      await waitFor(() => {
        expect(mockOnSessionSelect).toHaveBeenCalledWith('');
        expect(mockAddNotification).toHaveBeenCalledWith({
          type: 'success',
          message: 'Chat session deleted',
        });
      });
      
      // Restore window.confirm
      window.confirm = originalConfirm;
    });

    it('does not delete session when user cancels confirmation', async () => {
      const user = userEvent.setup();
      
      // Mock window.confirm to return false
      const originalConfirm = window.confirm;
      window.confirm = jest.fn(() => false);
      
      render(<ChatSessions onSessionSelect={mockOnSessionSelect} />);
      
      await waitFor(() => {
        expect(screen.getByText('Career Advice Chat')).toBeInTheDocument();
      });
      
      const deleteButtons = screen.getAllByRole('button', { name: /trash/i });
      await user.click(deleteButtons[0]);
      
      expect(window.confirm).toHaveBeenCalled();
      expect(mockApi.ai.deleteSession).not.toHaveBeenCalled();
      
      // Restore window.confirm
      window.confirm = originalConfirm;
    });

    it('handles session deletion error', async () => {
      const user = userEvent.setup();
      
      // Mock window.confirm
      const originalConfirm = window.confirm;
      window.confirm = jest.fn(() => true);
      
      mockApi.ai.deleteSession.mockRejectedValue(new Error('Deletion failed'));
      
      render(<ChatSessions onSessionSelect={mockOnSessionSelect} />);
      
      await waitFor(() => {
        expect(screen.getByText('Career Advice Chat')).toBeInTheDocument();
      });
      
      const deleteButtons = screen.getAllByRole('button', { name: /trash/i });
      await user.click(deleteButtons[0]);
      
      await waitFor(() => {
        expect(mockAddNotification).toHaveBeenCalledWith({
          type: 'error',
          message: 'Failed to delete session',
        });
      });
      
      // Restore window.confirm
      window.confirm = originalConfirm;
    });
  });

  describe('Date Formatting', () => {
    it('formats recent dates correctly', async () => {
      const recentSession = {
        ...mockSessions[0],
        updated_at: new Date(Date.now() - 30 * 60 * 1000).toISOString(), // 30 minutes ago
      };

      mockApi.ai.getSessions.mockResolvedValue({
        data: { sessions: [recentSession], count: 1 },
      });
      
      render(<ChatSessions onSessionSelect={mockOnSessionSelect} />);
      
      await waitFor(() => {
        expect(screen.getByText('Just now')).toBeInTheDocument();
      });
    });

    it('formats older dates correctly', async () => {
      const oldSession = {
        ...mockSessions[0],
        updated_at: new Date(Date.now() - 25 * 60 * 60 * 1000).toISOString(), // 25 hours ago
      };

      mockApi.ai.getSessions.mockResolvedValue({
        data: { sessions: [oldSession], count: 1 },
      });
      
      render(<ChatSessions onSessionSelect={mockOnSessionSelect} />);
      
      await waitFor(() => {
        expect(screen.getByText('1d ago')).toBeInTheDocument();
      });
    });
  });

  describe('Empty State Actions', () => {
    it('shows start new chat button in empty state', async () => {
      mockApi.ai.getSessions.mockResolvedValue({
        data: { sessions: [], count: 0 },
      });
      
      render(<ChatSessions onSessionSelect={mockOnSessionSelect} />);
      
      await waitFor(() => {
        expect(screen.getByText('Start New Chat')).toBeInTheDocument();
      });
    });

    it('creates session from empty state button', async () => {
      const user = userEvent.setup();
      const newSession = {
        id: 'new-session',
        title: '',
        created_at: '2024-01-01T11:00:00Z',
        updated_at: '2024-01-01T11:00:00Z',
        is_active: true,
        message_count: 0,
      };

      mockApi.ai.getSessions.mockResolvedValue({
        data: { sessions: [], count: 0 },
      });
      mockApi.ai.createSession.mockResolvedValue({ data: newSession });
      
      render(<ChatSessions onSessionSelect={mockOnSessionSelect} />);
      
      await waitFor(() => {
        expect(screen.getByText('Start New Chat')).toBeInTheDocument();
      });
      
      const startButton = screen.getByText('Start New Chat');
      await user.click(startButton);
      
      expect(mockApi.ai.createSession).toHaveBeenCalled();
    });
  });

  describe('Accessibility', () => {
    it('has proper ARIA labels and roles', async () => {
      render(<ChatSessions onSessionSelect={mockOnSessionSelect} />);
      
      await waitFor(() => {
        expect(screen.getByText('Chat Sessions')).toBeInTheDocument();
      });
      
      const createButton = screen.getByRole('button', { name: /plus/i });
      expect(createButton).toBeInTheDocument();
      
      const deleteButtons = screen.getAllByRole('button', { name: /trash/i });
      expect(deleteButtons.length).toBeGreaterThan(0);
    });

    it('supports keyboard navigation', async () => {
      const user = userEvent.setup();
      render(<ChatSessions onSessionSelect={mockOnSessionSelect} />);
      
      await waitFor(() => {
        expect(screen.getByText('Career Advice Chat')).toBeInTheDocument();
      });
      
      // Tab to create button
      await user.tab();
      expect(screen.getByRole('button', { name: /plus/i })).toHaveFocus();
      
      // Tab to first session
      await user.tab();
      const firstSession = screen.getByText('Career Advice Chat').closest('div');
      expect(firstSession).toHaveFocus();
    });
  });
});