import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AIChat } from '@/components/ai-chat/ai-chat';
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

describe('AIChat Component', () => {
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
  const mockOnClose = jest.fn();

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
  });

  describe('Chat Interface', () => {
    it('renders welcome message when no messages exist', () => {
      render(<AIChat isOpen={true} onClose={mockOnClose} />);
      
      expect(screen.getByText('Welcome to Koroh AI!')).toBeInTheDocument();
      expect(screen.getByText(/I'm here to help you with your career journey/)).toBeInTheDocument();
    });

    it('displays quick action buttons in welcome state', () => {
      render(<AIChat isOpen={true} onClose={mockOnClose} />);
      
      expect(screen.getByText('📄 Analyze my CV')).toBeInTheDocument();
      expect(screen.getByText('🌐 Generate portfolio')).toBeInTheDocument();
      expect(screen.getByText('💼 Find job opportunities')).toBeInTheDocument();
    });

    it('does not render when isOpen is false', () => {
      render(<AIChat isOpen={false} onClose={mockOnClose} />);
      
      expect(screen.queryByText('Welcome to Koroh AI!')).not.toBeInTheDocument();
    });

    it('can be minimized and maximized', async () => {
      const user = userEvent.setup();
      render(<AIChat isOpen={true} onClose={mockOnClose} />);
      
      const minimizeButton = screen.getByRole('button', { name: /minimize/i });
      await user.click(minimizeButton);
      
      // Check if chat content is hidden when minimized
      expect(screen.queryByText('Welcome to Koroh AI!')).not.toBeInTheDocument();
      
      const maximizeButton = screen.getByRole('button', { name: /maximize/i });
      await user.click(maximizeButton);
      
      // Check if chat content is visible when maximized
      expect(screen.getByText('Welcome to Koroh AI!')).toBeInTheDocument();
    });

    it('calls onClose when close button is clicked', async () => {
      const user = userEvent.setup();
      render(<AIChat isOpen={true} onClose={mockOnClose} />);
      
      const closeButton = screen.getByRole('button', { name: /close/i });
      await user.click(closeButton);
      
      expect(mockOnClose).toHaveBeenCalledTimes(1);
    });
  });

  describe('Message Sending', () => {
    const mockSendMessageResponse = {
      data: {
        session_id: 'test-session-id',
        user_message: {
          id: 'user-msg-1',
          role: 'user',
          content: 'Hello AI',
          created_at: '2024-01-01T00:00:00Z',
        },
        ai_response: {
          id: 'ai-msg-1',
          role: 'assistant',
          content: 'Hello! How can I help you today?',
          created_at: '2024-01-01T00:00:01Z',
        },
      },
    };

    beforeEach(() => {
      mockApi.ai.sendMessage.mockResolvedValue(mockSendMessageResponse);
    });

    it('sends message when send button is clicked', async () => {
      const user = userEvent.setup();
      render(<AIChat isOpen={true} onClose={mockOnClose} />);
      
      const input = screen.getByPlaceholderText('Type your message...');
      const sendButton = screen.getByRole('button', { name: /send/i });
      
      await user.type(input, 'Hello AI');
      await user.click(sendButton);
      
      expect(mockApi.ai.sendMessage).toHaveBeenCalledWith({
        message: 'Hello AI',
        session_id: undefined,
      });
    });

    it('sends message when Enter key is pressed', async () => {
      const user = userEvent.setup();
      render(<AIChat isOpen={true} onClose={mockOnClose} />);
      
      const input = screen.getByPlaceholderText('Type your message...');
      
      await user.type(input, 'Hello AI');
      await user.keyboard('{Enter}');
      
      expect(mockApi.ai.sendMessage).toHaveBeenCalledWith({
        message: 'Hello AI',
        session_id: undefined,
      });
    });

    it('does not send empty messages', async () => {
      const user = userEvent.setup();
      render(<AIChat isOpen={true} onClose={mockOnClose} />);
      
      const sendButton = screen.getByRole('button', { name: /send/i });
      
      await user.click(sendButton);
      
      expect(mockApi.ai.sendMessage).not.toHaveBeenCalled();
    });

    it('displays messages after successful send', async () => {
      const user = userEvent.setup();
      render(<AIChat isOpen={true} onClose={mockOnClose} />);
      
      const input = screen.getByPlaceholderText('Type your message...');
      
      await user.type(input, 'Hello AI');
      await user.keyboard('{Enter}');
      
      await waitFor(() => {
        expect(screen.getByText('Hello AI')).toBeInTheDocument();
        expect(screen.getByText('Hello! How can I help you today?')).toBeInTheDocument();
      });
    });

    it('shows loading state while sending message', async () => {
      const user = userEvent.setup();
      
      // Mock a delayed response
      mockApi.ai.sendMessage.mockImplementation(() => 
        new Promise(resolve => setTimeout(() => resolve(mockSendMessageResponse), 100))
      );
      
      render(<AIChat isOpen={true} onClose={mockOnClose} />);
      
      const input = screen.getByPlaceholderText('Type your message...');
      
      await user.type(input, 'Hello AI');
      await user.keyboard('{Enter}');
      
      // Check for loading indicator
      expect(screen.getByRole('button', { name: /send/i })).toBeDisabled();
      
      await waitFor(() => {
        expect(screen.getByText('Hello! How can I help you today?')).toBeInTheDocument();
      });
    });

    it('handles message send errors gracefully', async () => {
      const user = userEvent.setup();
      
      mockApi.ai.sendMessage.mockRejectedValue(new Error('Network error'));
      
      render(<AIChat isOpen={true} onClose={mockOnClose} />);
      
      const input = screen.getByPlaceholderText('Type your message...');
      
      await user.type(input, 'Hello AI');
      await user.keyboard('{Enter}');
      
      await waitFor(() => {
        expect(mockAddNotification).toHaveBeenCalledWith({
          type: 'error',
          message: 'Failed to send message. Please try again.',
        });
      });
    });
  });

  describe('Quick Actions', () => {
    const mockQuickActionResponse = {
      data: {
        session_id: 'test-session-id',
        ai_response: {
          id: 'ai-msg-1',
          role: 'assistant',
          content: 'I can help you analyze your CV!',
          created_at: '2024-01-01T00:00:01Z',
        },
      },
    };

    beforeEach(() => {
      mockApi.ai.analyzeCVChat.mockResolvedValue(mockQuickActionResponse);
      mockApi.ai.generatePortfolioChat.mockResolvedValue(mockQuickActionResponse);
      mockApi.ai.getJobRecommendationsChat.mockResolvedValue(mockQuickActionResponse);
    });

    it('handles CV analysis quick action', async () => {
      const user = userEvent.setup();
      render(<AIChat isOpen={true} onClose={mockOnClose} />);
      
      const cvAnalysisButton = screen.getByText('📄 Analyze my CV');
      await user.click(cvAnalysisButton);
      
      expect(mockApi.ai.analyzeCVChat).toHaveBeenCalledWith(undefined);
      
      await waitFor(() => {
        expect(screen.getByText('I can help you analyze your CV!')).toBeInTheDocument();
      });
    });

    it('handles portfolio generation quick action', async () => {
      const user = userEvent.setup();
      render(<AIChat isOpen={true} onClose={mockOnClose} />);
      
      const portfolioButton = screen.getByText('🌐 Generate portfolio');
      await user.click(portfolioButton);
      
      expect(mockApi.ai.generatePortfolioChat).toHaveBeenCalledWith(undefined);
      
      await waitFor(() => {
        expect(screen.getByText('I can help you analyze your CV!')).toBeInTheDocument();
      });
    });

    it('handles job recommendations quick action', async () => {
      const user = userEvent.setup();
      render(<AIChat isOpen={true} onClose={mockOnClose} />);
      
      const jobsButton = screen.getByText('💼 Find job opportunities');
      await user.click(jobsButton);
      
      expect(mockApi.ai.getJobRecommendationsChat).toHaveBeenCalledWith(undefined);
      
      await waitFor(() => {
        expect(screen.getByText('I can help you analyze your CV!')).toBeInTheDocument();
      });
    });

    it('handles quick action errors gracefully', async () => {
      const user = userEvent.setup();
      
      mockApi.ai.analyzeCVChat.mockRejectedValue(new Error('Service error'));
      
      render(<AIChat isOpen={true} onClose={mockOnClose} />);
      
      const cvAnalysisButton = screen.getByText('📄 Analyze my CV');
      await user.click(cvAnalysisButton);
      
      await waitFor(() => {
        expect(mockAddNotification).toHaveBeenCalledWith({
          type: 'error',
          message: 'Failed to analyze cv. Please try again.',
        });
      });
    });
  });

  describe('Context Management', () => {
    it('maintains session context across messages', async () => {
      const user = userEvent.setup();
      
      const firstResponse = {
        data: {
          session_id: 'test-session-id',
          user_message: {
            id: 'user-msg-1',
            role: 'user',
            content: 'Hello',
            created_at: '2024-01-01T00:00:00Z',
          },
          ai_response: {
            id: 'ai-msg-1',
            role: 'assistant',
            content: 'Hello! How can I help?',
            created_at: '2024-01-01T00:00:01Z',
          },
        },
      };

      const secondResponse = {
        data: {
          session_id: 'test-session-id',
          user_message: {
            id: 'user-msg-2',
            role: 'user',
            content: 'Tell me about jobs',
            created_at: '2024-01-01T00:00:02Z',
          },
          ai_response: {
            id: 'ai-msg-2',
            role: 'assistant',
            content: 'I can help you find jobs!',
            created_at: '2024-01-01T00:00:03Z',
          },
        },
      };

      mockApi.ai.sendMessage
        .mockResolvedValueOnce(firstResponse)
        .mockResolvedValueOnce(secondResponse);
      
      render(<AIChat isOpen={true} onClose={mockOnClose} />);
      
      const input = screen.getByPlaceholderText('Type your message...');
      
      // Send first message
      await user.type(input, 'Hello');
      await user.keyboard('{Enter}');
      
      await waitFor(() => {
        expect(screen.getByText('Hello! How can I help?')).toBeInTheDocument();
      });
      
      // Send second message
      await user.type(input, 'Tell me about jobs');
      await user.keyboard('{Enter}');
      
      // Verify session ID is maintained
      expect(mockApi.ai.sendMessage).toHaveBeenLastCalledWith({
        message: 'Tell me about jobs',
        session_id: 'test-session-id',
      });
      
      await waitFor(() => {
        expect(screen.getByText('I can help you find jobs!')).toBeInTheDocument();
      });
    });

    it('sends initial message when provided', async () => {
      const initialMessage = 'Help me with my career';
      
      mockApi.ai.sendMessage.mockResolvedValue({
        data: {
          session_id: 'test-session-id',
          user_message: {
            id: 'user-msg-1',
            role: 'user',
            content: initialMessage,
            created_at: '2024-01-01T00:00:00Z',
          },
          ai_response: {
            id: 'ai-msg-1',
            role: 'assistant',
            content: 'I\'d be happy to help with your career!',
            created_at: '2024-01-01T00:00:01Z',
          },
        },
      });
      
      render(<AIChat isOpen={true} onClose={mockOnClose} initialMessage={initialMessage} />);
      
      await waitFor(() => {
        expect(mockApi.ai.sendMessage).toHaveBeenCalledWith({
          message: initialMessage,
          session_id: undefined,
        });
      });
    });
  });

  describe('Accessibility', () => {
    it('has proper ARIA labels and roles', () => {
      render(<AIChat isOpen={true} onClose={mockOnClose} />);
      
      expect(screen.getByPlaceholderText('Type your message...')).toHaveAttribute('type', 'text');
      expect(screen.getByRole('button', { name: /send/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /close/i })).toBeInTheDocument();
    });

    it('focuses input when chat opens', () => {
      render(<AIChat isOpen={true} onClose={mockOnClose} />);
      
      const input = screen.getByPlaceholderText('Type your message...');
      expect(input).toHaveFocus();
    });

    it('supports keyboard navigation', async () => {
      const user = userEvent.setup();
      render(<AIChat isOpen={true} onClose={mockOnClose} />);
      
      // Tab through interactive elements
      await user.tab();
      expect(screen.getByText('📄 Analyze my CV')).toHaveFocus();
      
      await user.tab();
      expect(screen.getByText('🌐 Generate portfolio')).toHaveFocus();
      
      await user.tab();
      expect(screen.getByText('💼 Find job opportunities')).toHaveFocus();
    });
  });
});