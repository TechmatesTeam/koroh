'use client';

import { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Loader2, History, Plus, Settings } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { api } from '@/lib/api';
import { useAuth } from '@/contexts/auth-context';
import { useNotifications } from '@/contexts/notification-context';
import { ChatMessage, ChatSession } from '@/types';
import { ChatSessions } from './chat-sessions';

export function FullScreenAIChat() {
  const { user } = useAuth();
  const { addNotification } = useNotifications();
  
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [currentSession, setCurrentSession] = useState<ChatSession | null>(null);
  const [isTyping, setIsTyping] = useState(false);
  const [messagesRemaining, setMessagesRemaining] = useState<number | null>(null);
  const [showRegistrationPrompt, setShowRegistrationPrompt] = useState(false);
  const [isLimitExceeded, setIsLimitExceeded] = useState(false);
  const [selectedSessionId, setSelectedSessionId] = useState<string>('');
  const [activeTab, setActiveTab] = useState<'chat' | 'sessions'>('chat');
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  // Focus input when component mounts
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

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
          setSelectedSessionId(session_id);
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
          setSelectedSessionId(session_id);
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
        setSelectedSessionId(session_id);
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

  const handleSessionSelect = (sessionId: string) => {
    setSelectedSessionId(sessionId);
    setActiveTab('chat');
    loadSession(sessionId);
  };

  const loadSession = async (sessionId: string) => {
    try {
      const response = await api.ai.getSession(sessionId);
      setCurrentSession(response.data);
      setMessages(response.data.messages || []);
    } catch (error) {
      console.error('Error loading session:', error);
    }
  };

  const handleNewSession = () => {
    setSelectedSessionId('');
    setCurrentSession(null);
    setMessages([]);
    setActiveTab('chat');
  };

  const formatMessageTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  return (
    <div className="h-[calc(100vh-200px)]">
      <Card className="h-full flex flex-col">
        {/* Header */}
        <CardHeader className="flex flex-row items-center justify-between p-4 border-b">
          <div className="flex items-center space-x-2">
            <Bot className="h-6 w-6 text-blue-600" />
            <CardTitle className="text-xl">Koroh AI Assistant</CardTitle>
            {currentSession && (
              <Badge variant="secondary" className="text-xs">
                Active Session
              </Badge>
            )}
            {!user && messagesRemaining !== null && (
              <Badge variant="outline" className="text-xs">
                {messagesRemaining} messages left
              </Badge>
            )}
          </div>
          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleNewSession}
              className="flex items-center space-x-1"
            >
              <Plus className="h-4 w-4" />
              <span>New Chat</span>
            </Button>
          </div>
        </CardHeader>

        {/* Content */}
        <CardContent className="flex-1 p-0 overflow-hidden">
          <div className="flex h-full">
            {/* Desktop Layout */}
            <div className="hidden md:flex w-full">
              {/* Sessions Sidebar */}
              <div className="w-80 border-r">
                <ChatSessions
                  onSessionSelect={handleSessionSelect}
                  selectedSessionId={selectedSessionId}
                  className="h-full border-0 rounded-none"
                />
              </div>

              {/* Chat Area */}
              <div className="flex-1 flex flex-col">
                {/* Messages Area */}
                <div className="flex-1 overflow-y-auto p-6 space-y-4">
                  {messages.length === 0 && (
                    <div className="text-center text-gray-500 mt-12">
                      <Bot className="h-16 w-16 mx-auto mb-6 text-gray-400" />
                      <p className="text-2xl font-medium mb-4">Welcome to Koroh AI!</p>
                      <p className="text-lg mb-8 max-w-2xl mx-auto">
                        I'm here to help you with your career journey. 
                        {!user && " Try me out with 5 free messages!"}
                      </p>
                      
                      {user ? (
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 max-w-4xl mx-auto">
                          <Button
                            variant="outline"
                            size="lg"
                            onClick={() => handleQuickAction('analyze-cv')}
                            disabled={isLoading}
                            className="h-20 flex flex-col space-y-2"
                          >
                            <span className="text-2xl">📄</span>
                            <span>Analyze my CV</span>
                          </Button>
                          <Button
                            variant="outline"
                            size="lg"
                            onClick={() => handleQuickAction('generate-portfolio')}
                            disabled={isLoading}
                            className="h-20 flex flex-col space-y-2"
                          >
                            <span className="text-2xl">🌐</span>
                            <span>Generate portfolio</span>
                          </Button>
                          <Button
                            variant="outline"
                            size="lg"
                            onClick={() => handleQuickAction('job-recommendations')}
                            disabled={isLoading}
                            className="h-20 flex flex-col space-y-2"
                          >
                            <span className="text-2xl">💼</span>
                            <span>Find job opportunities</span>
                          </Button>
                        </div>
                      ) : (
                        <div className="space-y-4 max-w-2xl mx-auto">
                          <div className="bg-blue-50 p-6 rounded-lg">
                            <p className="text-blue-800 text-lg mb-4">
                              💡 Ask me about career advice, job searching, or professional development
                            </p>
                            <div className="text-blue-600 space-y-2">
                              <p>🎯 5 free messages to try our AI</p>
                              <p>🚀 Register for unlimited access</p>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {messages.map((message) => (
                    <div
                      key={message.id}
                      className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                      <div
                        className={`max-w-[70%] rounded-lg p-4 ${
                          message.role === 'user'
                            ? 'bg-blue-600 text-white'
                            : 'bg-gray-100 text-gray-900'
                        }`}
                      >
                        <div className="flex items-start space-x-3">
                          {message.role === 'assistant' && (
                            <Bot className="h-5 w-5 mt-0.5 flex-shrink-0" />
                          )}
                          {message.role === 'user' && (
                            <User className="h-5 w-5 mt-0.5 flex-shrink-0" />
                          )}
                          <div className="flex-1">
                            <p className="text-sm whitespace-pre-wrap leading-relaxed">{message.content}</p>
                            <p className={`text-xs mt-2 ${
                              message.role === 'user' ? 'text-blue-100' : 'text-gray-500'
                            }`}>
                              {formatMessageTime(message.created_at)}
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}

                  {isTyping && (
                    <div className="flex justify-start">
                      <div className="bg-gray-100 rounded-lg p-4 max-w-[70%]">
                        <div className="flex items-center space-x-3">
                          <Bot className="h-5 w-5" />
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
                  <div className="border-t border-b bg-blue-50 p-4">
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
                        <Button
                          size="sm"
                          onClick={() => window.location.href = '/auth/register'}
                          className="text-xs"
                        >
                          Register Free
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => window.location.href = '/auth/login'}
                          className="text-xs"
                        >
                          Login
                        </Button>
                      </div>
                    </div>
                  </div>
                )}

                {/* Input Area */}
                <div className="border-t p-6">
                  <div className="flex space-x-3">
                    <Input
                      ref={inputRef}
                      value={inputMessage}
                      onChange={(e) => setInputMessage(e.target.value)}
                      onKeyPress={handleKeyPress}
                      placeholder={isLimitExceeded ? "Register to continue chatting..." : "Type your message..."}
                      disabled={isLoading || isLimitExceeded}
                      className="flex-1 h-12 text-base"
                    />
                    <Button
                      onClick={() => handleSendMessage()}
                      disabled={isLoading || !inputMessage.trim() || isLimitExceeded}
                      size="lg"
                      className="px-6 h-12"
                    >
                      {isLoading ? (
                        <Loader2 className="h-5 w-5 animate-spin" />
                      ) : (
                        <Send className="h-5 w-5" />
                      )}
                    </Button>
                  </div>
                  
                  {/* Quick Actions - Only for authenticated users */}
                  {user && messages.length > 0 && (
                    <div className="flex flex-wrap gap-2 mt-4">
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
                    <div className="mt-3 text-center">
                      <p className="text-sm text-gray-500">
                        {messagesRemaining !== null 
                          ? `${messagesRemaining} free messages remaining` 
                          : "Try our AI assistant - 5 free messages"
                        }
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Mobile Layout */}
            <div className="md:hidden w-full">
              <Tabs value={activeTab} onValueChange={(value) => setActiveTab(value as 'chat' | 'sessions')}>
                <TabsList className="grid w-full grid-cols-2">
                  <TabsTrigger value="chat" className="flex items-center space-x-2">
                    <span>Chat</span>
                  </TabsTrigger>
                  <TabsTrigger value="sessions" className="flex items-center space-x-2">
                    <History className="h-4 w-4" />
                    <span>Sessions</span>
                  </TabsTrigger>
                </TabsList>

                <TabsContent value="chat" className="h-[calc(100vh-300px)] flex flex-col">
                  {/* Messages Area */}
                  <div className="flex-1 overflow-y-auto p-4 space-y-4">
                    {messages.length === 0 && (
                      <div className="text-center text-gray-500 mt-8">
                        <Bot className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                        <p className="text-lg font-medium mb-2">Welcome to Koroh AI!</p>
                        <p className="text-sm mb-4">
                          I'm here to help you with your career journey. 
                          {!user && " Try me out with 5 free messages!"}
                        </p>
                        
                        {user ? (
                          <div className="space-y-2">
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
                            </div>
                          </div>
                        )}
                      </div>
                    )}

                    {messages.map((message) => (
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
                              <Bot className="h-4 w-4 mt-0.5 flex-shrink-0" />
                            )}
                            {message.role === 'user' && (
                              <User className="h-4 w-4 mt-0.5 flex-shrink-0" />
                            )}
                            <div className="flex-1">
                              <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                              <p className={`text-xs mt-1 ${
                                message.role === 'user' ? 'text-blue-100' : 'text-gray-500'
                              }`}>
                                {formatMessageTime(message.created_at)}
                              </p>
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
                          <Button
                            size="sm"
                            onClick={() => window.location.href = '/auth/register'}
                            className="text-xs"
                          >
                            Register Free
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => window.location.href = '/auth/login'}
                            className="text-xs"
                          >
                            Login
                          </Button>
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
                </TabsContent>

                <TabsContent value="sessions" className="h-[calc(100vh-300px)]">
                  <ChatSessions
                    onSessionSelect={handleSessionSelect}
                    selectedSessionId={selectedSessionId}
                    className="h-full border-0"
                  />
                </TabsContent>
              </Tabs>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
