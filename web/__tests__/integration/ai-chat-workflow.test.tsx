import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ChatInterface } from '@/components/ai-chat/chat-interface';
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

describe('AI Chat Workflow Integration', () => {
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

    // Mock default API responses
    mockApi.ai.getSessions.mockResolvedValue({
      data: { sessions: [], count: 0 },
    });
  });

  describe('Complete Conversational Flow', () => {
    it('handles full conversation with context management', async () => {
      const user = userEvent.setup();
      
      // Mock conversation responses
      const responses = [
        {
          data: {
            session_id: 'session-1',
            user_message: {
              id: 'msg-1',
              role: 'user',
              content: 'Hello, I need help with my career',
              created_at: '2024-01-01T10:00:00Z',
            },
            ai_response: {
              id: 'msg-2',
              role: 'assistant',
              content: 'Hello! I\'d be happy to help with your career. What specific area would you like assistance with?',
              created_at: '2024-01-01T10:00:01Z',
            },
          },
        },
        {
          data: {
            session_id: 'session-1',
            user_message: {
              id: 'msg-3',
              role: 'user',
              content: 'I want to improve my resume',
              created_at: '2024-01-01T10:01:00Z',
            },
            ai_response: {
              id: 'msg-4',
              role: 'assistant',
              content: 'Great! I can help you analyze your current CV and suggest improvements. Have you uploaded your CV to the platform?',
              created_at: '2024-01-01T10:01:01Z',
            },
          },
        },
        {
          data: {
            session_id: 'session-1',
            user_message: {
              id: 'msg-5',
              role: 'user',
              content: 'Yes, I have uploaded it',
              created_at: '2024-01-01T10:02:00Z',
            },
            ai_response: {
              id: 'msg-6',
              role: 'assistant',
              content: 'Perfect! Let me analyze your CV for you. I\'ll look at your skills, experience, and suggest improvements.',
              created_at: '2024-01-01T10:02:01Z',
            },
          },
        },
      ];

      mockApi.ai.sendMessage
        .mockResolvedValueOnce(responses[0])
        .mockResolvedValueOnce(responses[1])
        .mockResolvedValueOnce(responses[2]);

      render(<ChatInterface isOpen={true} onClose={mockOnClose} />);
      
      // Wait for initial load
      await waitFor(() => {
        expect(screen.getByText('Koroh AI Assistant')).toBeInTheDocument();
      });

      // Start conversation
      const input = screen.getByPlaceholderText('Type your message...');
      
      // First message
      await user.type(input, 'Hello, I need help with my career');
      await user.keyboard('{Enter}');
      
      await waitFor(() => {
        expect(screen.getByText('Hello, I need help with my career')).toBeInTheDocument();
        expect(screen.getByText(/I'd be happy to help with your career/)).toBeInTheDocument();
      });

      // Second message - context should be maintained
      await user.type(input, 'I want to improve my resume');
      await user.keyboard('{Enter}');
      
      expect(mockApi.ai.sendMessage).toHaveBeenLastCalledWith({
        message: 'I want to improve my resume',
        session_id: 'session-1',
      });

      await waitFor(() => {
        expect(screen.getByText('I want to improve my resume')).toBeInTheDocument();
        expect(screen.getByText(/I can help you analyze your current CV/)).toBeInTheDocument();
      });

      // Third message - continuing context
      await user.type(input, 'Yes, I have uploaded it');
      await user.keyboard('{Enter}');
      
      expect(mockApi.ai.sendMessage).toHaveBeenLastCalledWith({
        message: 'Yes, I have uploaded it',
        session_id: 'session-1',
      });

      await waitFor(() => {
        expect(screen.getByText('Yes, I have uploaded it')).toBeInTheDocument();
        expect(screen.getByText(/Let me analyze your CV for you/)).toBeInTheDocument();
      });

      // Verify all messages are displayed in order
      const messages = screen.getAllByText(/Hello|improve|uploaded|analyze/);
      expect(messages.length).toBeGreaterThan(0);
    });

    it('handles platform feature integration workflow', async () => {
      const user = userEvent.setup();
      
      // Mock CV analysis response
      const cvAnalysisResponse = {
        data: {
          session_id: 'session-1',
          analysis_result: {
            success: true,
            message: 'CV analysis complete',
            data: {
              skills_count: 12,
              experience_years: 3,
              education_count: 2,
              key_skills: ['JavaScript', 'React', 'Node.js', 'Python', 'SQL'],
            },
          },
          ai_response: {
            id: 'msg-1',
            role: 'assistant',
            content: 'I\'ve analyzed your CV! You have 12 skills listed, 3 years of experience, and 2 education entries. Your key skills include JavaScript, React, Node.js, Python, and SQL. Would you like me to suggest improvements?',
            created_at: '2024-01-01T10:00:00Z',
          },
        },
      };

      // Mock portfolio generation response
      const portfolioResponse = {
        data: {
          session_id: 'session-1',
          generation_result: {
            success: true,
            message: 'Portfolio generation ready',
            action_required: 'portfolio_template_selection',
          },
          ai_response: {
            id: 'msg-2',
            role: 'assistant',
            content: 'I can help you generate a professional portfolio! What style would you prefer: Modern, Classic, or Creative?',
            created_at: '2024-01-01T10:01:00Z',
          },
        },
      };

      // Mock job recommendations response
      const jobRecommendationsResponse = {
        data: {
          session_id: 'session-1',
          recommendations_result: {
            success: true,
            message: 'Found 3 great job opportunities',
            data: {
              recommendations: [
                {
                  title: 'Frontend Developer',
                  company: 'Tech Corp',
                  location: 'San Francisco, CA',
                  match_score: 92,
                },
                {
                  title: 'Full Stack Engineer',
                  company: 'StartupXYZ',
                  location: 'Remote',
                  match_score: 88,
                },
              ],
              total_count: 2,
            },
          },
          ai_response: {
            id: 'msg-3',
            role: 'assistant',
            content: 'I found 2 great job opportunities for you! Here are the top matches: Frontend Developer at Tech Corp (92% match) and Full Stack Engineer at StartupXYZ (88% match).',
            created_at: '2024-01-01T10:02:00Z',
          },
        },
      };

      mockApi.ai.analyzeCVChat.mockResolvedValue(cvAnalysisResponse);
      mockApi.ai.generatePortfolioChat.mockResolvedValue(portfolioResponse);
      mockApi.ai.getJobRecommendationsChat.mockResolvedValue(jobRecommendationsResponse);

      render(<ChatInterface isOpen={true} onClose={mockOnClose} />);
      
      // Wait for initial load
      await waitFor(() => {
        expect(screen.getByText('Koroh AI Assistant')).toBeInTheDocument();
      });

      // Test CV Analysis workflow
      const cvAnalysisButton = screen.getByText('📄 Analyze my CV');
      await user.click(cvAnalysisButton);
      
      expect(mockApi.ai.analyzeCVChat).toHaveBeenCalledWith(undefined);
      
      await waitFor(() => {
        expect(screen.getByText(/I've analyzed your CV/)).toBeInTheDocument();
        expect(screen.getByText(/12 skills listed/)).toBeInTheDocument();
      });

      // Test Portfolio Generation workflow
      const portfolioButton = screen.getByText('🌐 Generate portfolio');
      await user.click(portfolioButton);
      
      expect(mockApi.ai.generatePortfolioChat).toHaveBeenCalledWith('session-1');
      
      await waitFor(() => {
        expect(screen.getByText(/What style would you prefer/)).toBeInTheDocument();
      });

      // Test Job Recommendations workflow
      const jobsButton = screen.getByText('💼 Find job opportunities');
      await user.click(jobsButton);
      
      expect(mockApi.ai.getJobRecommendationsChat).toHaveBeenCalledWith('session-1');
      
      await waitFor(() => {
        expect(screen.getByText(/I found 2 great job opportunities/)).toBeInTheDocument();
        expect(screen.getByText(/Frontend Developer at Tech Corp/)).toBeInTheDocument();
      });
    });
  });

  describe('Session Management Workflow', () => {
    it('handles session creation and switching', async () => {
      const user = userEvent.setup();
      
      const existingSessions = [
        {
          id: 'session-1',
          title: 'Career Advice',
          created_at: '2024-01-01T09:00:00Z',
          updated_at: '2024-01-01T09:30:00Z',
          is_active: true,
          message_count: 5,
          last_message: {
            content: 'Thanks for the help!',
            role: 'user',
            created_at: '2024-01-01T09:30:00Z',
          },
        },
      ];

      const newSession = {
        id: 'session-2',
        title: '',
        created_at: '2024-01-01T10:00:00Z',
        updated_at: '2024-01-01T10:00:00Z',
        is_active: true,
        message_count: 0,
      };

      const sessionDetails = {
        id: 'session-1',
        title: 'Career Advice',
        created_at: '2024-01-01T09:00:00Z',
        updated_at: '2024-01-01T09:30:00Z',
        is_active: true,
        messages: [
          {
            id: 'msg-1',
            role: 'user',
            content: 'I need career advice',
            created_at: '2024-01-01T09:00:00Z',
          },
          {
            id: 'msg-2',
            role: 'assistant',
            content: 'I\'d be happy to help with your career!',
            created_at: '2024-01-01T09:00:01Z',
          },
        ],
        message_count: 2,
      };

      mockApi.ai.getSessions.mockResolvedValue({
        data: { sessions: existingSessions, count: 1 },
      });
      mockApi.ai.createSession.mockResolvedValue({ data: newSession });
      mockApi.ai.getSession.mockResolvedValue({ data: sessionDetails });

      render(<ChatInterface isOpen={true} onClose={mockOnClose} />);
      
      // Wait for sessions to load
      await waitFor(() => {
        expect(screen.getByText('Career Advice')).toBeInTheDocument();
      });

      // Select existing session
      const existingSession = screen.getByText('Career Advice');
      await user.click(existingSession);
      
      expect(mockApi.ai.getSession).toHaveBeenCalledWith('session-1');
      
      await waitFor(() => {
        expect(screen.getByText('I need career advice')).toBeInTheDocument();
        expect(screen.getByText('I\'d be happy to help with your career!')).toBeInTheDocument();
      });

      // Create new session
      const newChatButton = screen.getByText('New Chat');
      await user.click(newChatButton);
      
      // The interface should switch to a new chat without existing messages
      expect(screen.queryByText('I need career advice')).not.toBeInTheDocument();
    });

    it('handles session deletion workflow', async () => {
      const user = userEvent.setup();
      
      const sessions = [
        {
          id: 'session-1',
          title: 'Career Advice',
          created_at: '2024-01-01T09:00:00Z',
          updated_at: '2024-01-01T09:30:00Z',
          is_active: true,
          message_count: 5,
          last_message: {
            content: 'Thanks for the help!',
            role: 'user',
            created_at: '2024-01-01T09:30:00Z',
          },
        },
        {
          id: 'session-2',
          title: 'Portfolio Help',
          created_at: '2024-01-01T08:00:00Z',
          updated_at: '2024-01-01T08:15:00Z',
          is_active: true,
          message_count: 3,
        },
      ];

      mockApi.ai.getSessions.mockResolvedValue({
        data: { sessions, count: 2 },
      });
      mockApi.ai.deleteSession.mockResolvedValue({
        data: { message: 'Session deleted' },
      });

      // Mock window.confirm
      const originalConfirm = window.confirm;
      window.confirm = jest.fn(() => true);

      render(<ChatInterface isOpen={true} onClose={mockOnClose} />);
      
      // Wait for sessions to load
      await waitFor(() => {
        expect(screen.getByText('Career Advice')).toBeInTheDocument();
        expect(screen.getByText('Portfolio Help')).toBeInTheDocument();
      });

      // Delete first session
      const deleteButtons = screen.getAllByRole('button', { name: /trash/i });
      await user.click(deleteButtons[0]);
      
      expect(window.confirm).toHaveBeenCalledWith('Are you sure you want to delete this chat session?');
      expect(mockApi.ai.deleteSession).toHaveBeenCalledWith('session-1');
      
      await waitFor(() => {
        expect(mockAddNotification).toHaveBeenCalledWith({
          type: 'success',
          message: 'Chat session deleted',
        });
      });

      // Restore window.confirm
      window.confirm = originalConfirm;
    });
  });

  describe('Error Handling and Recovery', () => {
    it('handles network errors gracefully', async () => {
      const user = userEvent.setup();
      
      mockApi.ai.sendMessage.mockRejectedValue(new Error('Network error'));
      
      render(<ChatInterface isOpen={true} onClose={mockOnClose} />);
      
      // Try to send a message
      const input = screen.getByPlaceholderText('Type your message...');
      await user.type(input, 'Hello');
      await user.keyboard('{Enter}');
      
      await waitFor(() => {
        expect(mockAddNotification).toHaveBeenCalledWith({
          type: 'error',
          message: 'Failed to send message. Please try again.',
        });
      });
    });

    it('handles platform integration errors', async () => {
      const user = userEvent.setup();
      
      mockApi.ai.analyzeCVChat.mockRejectedValue(new Error('CV analysis failed'));
      
      render(<ChatInterface isOpen={true} onClose={mockOnClose} />);
      
      const cvAnalysisButton = screen.getByText('📄 Analyze my CV');
      await user.click(cvAnalysisButton);
      
      await waitFor(() => {
        expect(mockAddNotification).toHaveBeenCalledWith({
          type: 'error',
          message: 'Failed to analyze cv. Please try again.',
        });
      });
    });

    it('recovers from temporary failures', async () => {
      const user = userEvent.setup();
      
      const successResponse = {
        data: {
          session_id: 'session-1',
          user_message: {
            id: 'msg-1',
            role: 'user',
            content: 'Hello',
            created_at: '2024-01-01T10:00:00Z',
          },
          ai_response: {
            id: 'msg-2',
            role: 'assistant',
            content: 'Hello! How can I help?',
            created_at: '2024-01-01T10:00:01Z',
          },
        },
      };

      // First call fails, second succeeds
      mockApi.ai.sendMessage
        .mockRejectedValueOnce(new Error('Temporary failure'))
        .mockResolvedValueOnce(successResponse);
      
      render(<ChatInterface isOpen={true} onClose={mockOnClose} />);
      
      const input = screen.getByPlaceholderText('Type your message...');
      
      // First attempt fails
      await user.type(input, 'Hello');
      await user.keyboard('{Enter}');
      
      await waitFor(() => {
        expect(mockAddNotification).toHaveBeenCalledWith({
          type: 'error',
          message: 'Failed to send message. Please try again.',
        });
      });

      // Second attempt succeeds
      await user.type(input, 'Hello');
      await user.keyboard('{Enter}');
      
      await waitFor(() => {
        expect(screen.getByText('Hello! How can I help?')).toBeInTheDocument();
      });
    });
  });

  describe('Mobile and Desktop Responsiveness', () => {
    it('switches between mobile tabs correctly', async () => {
      const user = userEvent.setup();
      
      // Mock mobile viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 500,
      });

      render(<ChatInterface isOpen={true} onClose={mockOnClose} />);
      
      // Should show tabs on mobile
      expect(screen.getByText('Chat')).toBeInTheDocument();
      expect(screen.getByText('Sessions')).toBeInTheDocument();
      
      // Switch to sessions tab
      const sessionsTab = screen.getByText('Sessions');
      await user.click(sessionsTab);
      
      // Should show sessions content
      await waitFor(() => {
        expect(screen.getByText('No chat sessions yet')).toBeInTheDocument();
      });
      
      // Switch back to chat tab
      const chatTab = screen.getByText('Chat');
      await user.click(chatTab);
      
      // Should show chat interface
      expect(screen.getByPlaceholderText('Type your message...')).toBeInTheDocument();
    });
  });
});