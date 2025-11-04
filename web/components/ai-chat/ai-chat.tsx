'use client';

import { useState, useRef, useEffect } from 'react';
import Link from 'next/link';
import { Send, Bot, User, Loader2, X, Minimize2, Maximize2, Brain } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { api } from '@/lib/api';
import { useAuth } from '@/contexts/auth-context';
import { useNotifications } from '@/contexts/notification-context';
import { ChatMessage, ChatSession } from '@/types';
import { ConversationContext } from './conversation-context';

interface AIChatProps {
  isOpen: boolean;
  onClose: () => void;
  initialMessage?: string;
  className?: string;
}

export function AIChat({ isOpen, onClose, initialMessage, className = '' }: AIChatProps) {
  const { user } = useAuth();
  const { addNotification } = useNotifications();
  
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [currentSession, setCurrentSession] = useState<ChatSession | null>(null);
  const [isTyping, setIsTyping] = useState(false);
  const [messagesRemaining, setMessagesRemaining] = useState<number | null>(null);
  const [showRegistrationPrompt, setShowRegistrationPrompt] = useState(false);
  const [isLimitExceeded, setIsLimitExceeded] = useState(false);
  const [showContext, setShowContext] = useState(false);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  // Focus input when chat opens
  useEffect(() => {
    if (isOpen && !isMinimized) {
      inputRef.current?.focus();
    }
  }, [isOpen, isMinimized]);

  // Send initial message if provided
  useEffect(() => {
    if (initialMessage && isOpen && messages.length === 0) {
      handleSendMessage(initialMessage);
    }
  }, [initialMessage, isOpen]);

  const handleSendMessage = async (messageText?: string) => {
    const message = messageText || inputMessage.trim();
    if (!message || isLoading || isLimitExceeded) return;

    setInputMessage('');
    setIsLoading(true);
    setIsTyping(true);

    // Add user message immediately
    const userMessage: ChatMessage = {
      id: `temp-${Date.now()}`,
      role: 'user',
      content: message,
      created_at: new Date().toISOString(),
    };
    setMessages(prev => [...prev, userMessage]);

    try {
      let response;
      
      if (user) {
        // Authenticated user - use regular chat
        response = await api.ai.sendMessage({
          message,
          session_id: currentSession?.id,
        });

        const { session_id, user_message, ai_response } = response.data;

        // Update session if new
        if (!currentSession || currentSession.id !== session_id) {
          setCurrentSession({
            id: session_id,
            title: message.length > 50 ? message.substring(0, 50) + '...' : message,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            is_active: true,
            messages: [],
            message_count: 0,
          });
        }

        // Replace temp user message with real one and add AI response
        setMessages(prev => {
          const filtered = prev.filter(msg => msg.id !== userMessage.id);
          return [...filtered, user_message, ai_response];
        });
      } else {
        // Anonymous user - use anonymous chat
        response = await api.ai.anonymousChat(message, currentSession?.id);

        const { 
          session_id, 
          response: aiResponse, 
          messages_remaining, 
          registration_prompt,
          limit_exceeded 
        } = response.data;

        // Handle limit exceeded
        if (limit_exceeded) {
          setIsLimitExceeded(true);
          setMessages(prev => prev.filter(msg => msg.id !== userMessage.id));
          addNotification({
            type: 'warning',
            title: 'Message Limit Reached',
            message: 'You have reached the maximum of 5 messages. Please register to continue chatting.',
          });
          return;
        }

        // Update session if new
        if (!currentSession || currentSession.id !== session_id) {
          setCurrentSession({
            id: session_id,
            title: message.length > 50 ? message.substring(0, 50) + '...' : message,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            is_active: true,
            messages: [],
            message_count: 0,
          });
        }

        // Update anonymous user state
        setMessagesRemaining(messages_remaining);
        setShowRegistrationPrompt(registration_prompt);

        // Create AI response message
        const aiMessage: ChatMessage = {
          id: `ai-${Date.now()}`,
          role: 'assistant',
          content: aiResponse,
          created_at: new Date().toISOString(),
        };

        // Replace temp user message and add AI response
        setMessages(prev => {
          const filtered = prev.filter(msg => msg.id !== userMessage.id);
          const realUserMessage = { ...userMessage, id: `user-${Date.now()}` };
          return [...filtered, realUserMessage, aiMessage];
        });
      }

    } catch (error: any) {
      console.error('Error sending message:', error);
      
      // Handle rate limiting for anonymous users
      if (error.response?.status === 429) {
        setIsLimitExceeded(true);
        addNotification({
          type: 'warning',
          title: 'Message Limit Reached',
          message: 'You have reached the maximum of 5 messages. Please register to continue chatting.',
        });
      } else {
        addNotification({
          type: 'error',
          title: 'Message Failed',
          message: 'Failed to send message. Please try again.',
        });
      }

      // Remove the temporary user message on error
      setMessages(prev => prev.filter(msg => msg.id !== userMessage.id));
    } finally {
      setIsLoading(false);
      setIsTyping(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleQuickAction = async (action: string) => {
    setIsLoading(true);
    setIsTyping(true);

    try {
      let response;
      switch (action) {
        case 'analyze-cv':
          response = await api.ai.analyzeCVChat(currentSession?.id);
          break;
        case 'generate-portfolio':
          response = await api.ai.generatePortfolioChat(currentSession?.id);
          break;
        case 'job-recommendations':
          response = await api.ai.getJobRecommendationsChat(currentSession?.id);
          break;
        default:
          return;
      }

      const { session_id, ai_response } = response.data;

      // Update session if new
      if (!currentSession || currentSession.id !== session_id) {
        setCurrentSession({
          id: session_id,
          title: `${action.replace('-', ' ')} assistance`,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          is_active: true,
          messages: [],
          message_count: 0,
        });
      }

      // Add AI response
      setMessages(prev => [...prev, ai_response]);

    } catch (error: any) {
      console.error(`Error with ${action}:`, error);
      addNotification({
        type: 'error',
        title: 'Action Failed',
        message: `Failed to ${action.replace('-', ' ')}. Please try again.`,
      });
    } finally {
      setIsLoading(false);
      setIsTyping(false);
    }
  };

  const formatMessageTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  if (!isOpen) return null;

  return (
    <div className={`fixed bottom-4 right-4 z-50 ${className}`}>
      <Card className={`w-96 shadow-2xl border-2 transition-all duration-300 ${
        isMinimized ? 'h-14' : 'h-[600px]'
      }`}>
        {/* Header */}
        <CardHeader className="flex flex-row items-center justify-between p-4 border-b">
          <div className="flex items-center space-x-2">
            <Bot className="h-5 w-5 text-blue-600" />
            <CardTitle className="text-lg">Koroh AI Assistant</CardTitle>
            {currentSession && (
              <Badge variant="secondary" className="text-xs">
                Active
              </Badge>
            )}
            {!user && messagesRemaining !== null && (
              <Badge variant="outline" className="text-xs">
                {messagesRemaining} left
              </Badge>
            )}
          </div>
          <div className="flex items-center space-x-1">
            {user && currentSession && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowContext(!showContext)}
                className="h-8 w-8 p-0"
                title="Show conversation context"
              >
                <Brain className="h-4 w-4" />
              </Button>
            )}
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsMinimized(!isMinimized)}
              className="h-8 w-8 p-0"
            >
              {isMinimized ? <Maximize2 className="h-4 w-4" /> : <Minimize2 className="h-4 w-4" />}
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={onClose}
              className="h-8 w-8 p-0"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        </CardHeader>

        {!isMinimized && (
          <CardContent className="flex flex-col h-[calc(600px-80px)] p-0">
            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.length === 0 && (
                <div className="text-center text-gray-500 mt-8">
                  <Bot className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                  <p className="text-lg font-medium mb-2">Welcome to Koroh AI!</p>
                  <p className="text-sm mb-4">
                    I'm your context-aware career assistant. I remember our conversations and build on them to provide better help.
                    {!user && " Try me out with 5 free messages!"}
                  </p>
                  
                  {user ? (
                    <div className="space-y-2">
                      <div className="text-xs text-green-600 bg-green-50 p-2 rounded mb-3">
                        🧠 I'll remember our conversation and provide contextual assistance
                      </div>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleQuickAction('analyze-cv')}
                        disabled={isLoading}
                        className="w-full"
                      >
                        📄 Analyze my CV
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleQuickAction('generate-portfolio')}
                        disabled={isLoading}
                        className="w-full"
                      >
                        🌐 Generate portfolio
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleQuickAction('job-recommendations')}
                        disabled={isLoading}
                        className="w-full"
                      >
                        💼 Find job opportunities
                      </Button>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      <p className="text-xs text-blue-600 bg-blue-50 p-2 rounded">
                        💡 Ask me about career advice, job searching, or professional development
                      </p>
                      <div className="text-xs text-gray-400">
                        <p>🎯 5 free messages to try our AI</p>
                        <p>🚀 Register for unlimited access</p>
                        <p>🧠 I'll remember our conversation context</p>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {messages.map((message, index) => (
                <div
                  key={message.id}
                  className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[80%] rounded-lg p-3 ${
                      message.role === 'user'
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-100 text-gray-900'
                    }`}
                  >
                    <div className="flex items-start space-x-2">
                      {message.role === 'assistant' && (
                        <div className="flex flex-col items-center">
                          <Bot className="h-4 w-4 mt-0.5 flex-shrink-0" />
                          {index > 2 && (
                            <div className="w-2 h-2 bg-green-400 rounded-full mt-1" title="Context-aware response" />
                          )}
                        </div>
                      )}
                      {message.role === 'user' && (
                        <User className="h-4 w-4 mt-0.5 flex-shrink-0" />
                      )}
                      <div className="flex-1">
                        <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                        <div className="flex items-center justify-between mt-1">
                          <p className={`text-xs ${
                            message.role === 'user' ? 'text-blue-100' : 'text-gray-500'
                          }`}>
                            {formatMessageTime(message.created_at)}
                          </p>
                          {message.role === 'assistant' && index > 2 && (
                            <span className="text-xs text-green-600 bg-green-100 px-1 rounded">
                              Context-aware
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ))}

              {isTyping && (
                <div className="flex justify-start">
                  <div className="bg-gray-100 rounded-lg p-3 max-w-[80%]">
                    <div className="flex items-center space-x-2">
                      <Bot className="h-4 w-4" />
                      <div className="flex space-x-1">
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>

            {/* Registration Prompt for Anonymous Users */}
            {!user && (showRegistrationPrompt || isLimitExceeded) && (
              <div className="border-t border-b bg-blue-50 p-3">
                <div className="text-center">
                  <p className="text-sm text-blue-800 mb-2">
                    {isLimitExceeded 
                      ? "You've reached the 5 message limit!" 
                      : `Only ${messagesRemaining} message${messagesRemaining === 1 ? '' : 's'} remaining!`
                    }
                  </p>
                  <p className="text-xs text-blue-600 mb-3">
                    Register for unlimited chat and access to all features
                  </p>
                  <div className="flex gap-2 justify-center">
                    <Link href="/auth/register">
                      <Button
                        size="sm"
                        className="text-xs"
                      >
                        Register Free
                      </Button>
                    </Link>
                    <Link href="/auth/login">
                      <Button
                        variant="outline"
                        size="sm"
                        className="text-xs"
                      >
                        Login
                      </Button>
                    </Link>
                  </div>
                </div>
              </div>
            )}

            {/* Input Area */}
            <div className="border-t p-4">
              <div className="flex space-x-2">
                <Input
                  ref={inputRef}
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder={isLimitExceeded ? "Register to continue chatting..." : "Type your message..."}
                  disabled={isLoading || isLimitExceeded}
                  className="flex-1"
                />
                <Button
                  onClick={() => handleSendMessage()}
                  disabled={isLoading || !inputMessage.trim() || isLimitExceeded}
                  size="sm"
                  className="px-3"
                >
                  {isLoading ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Send className="h-4 w-4" />
                  )}
                </Button>
              </div>
              
              {/* Quick Actions - Only for authenticated users */}
              {user && messages.length > 0 && (
                <div className="flex flex-wrap gap-2 mt-3">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleQuickAction('analyze-cv')}
                    disabled={isLoading}
                    className="text-xs"
                  >
                    📄 CV Analysis
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleQuickAction('generate-portfolio')}
                    disabled={isLoading}
                    className="text-xs"
                  >
                    🌐 Portfolio
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleQuickAction('job-recommendations')}
                    disabled={isLoading}
                    className="text-xs"
                  >
                    💼 Jobs
                  </Button>
                </div>
              )}

              {/* Anonymous User Info */}
              {!user && !isLimitExceeded && (
                <div className="mt-2 text-center">
                  <p className="text-xs text-gray-500">
                    {messagesRemaining !== null 
                      ? `${messagesRemaining} free messages remaining` 
                      : "Try our AI assistant - 5 free messages"
                    }
                  </p>
                </div>
              )}
            </div>
          </CardContent>
        )}
      </Card>
      
      {/* Conversation Context Component */}
      {user && currentSession && (
        <ConversationContext
          sessionId={currentSession.id}
          isVisible={showContext}
          onToggle={() => setShowContext(!showContext)}
        />
      )}
    </div>
  );
}