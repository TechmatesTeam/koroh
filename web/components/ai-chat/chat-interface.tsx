'use client';

import { useState, useEffect } from 'react';
import { X, Settings, History } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { AIChat } from './ai-chat';
import { ChatSessions } from './chat-sessions';
import { api } from '@/lib/api';
import { ChatSession } from '@/types';

interface ChatInterfaceProps {
  isOpen: boolean;
  onClose: () => void;
  className?: string;
}

export function ChatInterface({ isOpen, onClose, className = '' }: ChatInterfaceProps) {
  const [selectedSessionId, setSelectedSessionId] = useState<string>('');
  const [currentSession, setCurrentSession] = useState<ChatSession | null>(null);
  const [activeTab, setActiveTab] = useState<'chat' | 'sessions'>('chat');

  useEffect(() => {
    if (selectedSessionId) {
      loadSession(selectedSessionId);
      setActiveTab('chat');
    }
  }, [selectedSessionId]);

  const loadSession = async (sessionId: string) => {
    try {
      const response = await api.ai.getSession(sessionId);
      setCurrentSession(response.data);
    } catch (error) {
      console.error('Error loading session:', error);
    }
  };

  const handleSessionSelect = (sessionId: string) => {
    setSelectedSessionId(sessionId);
  };

  const handleNewSession = () => {
    setSelectedSessionId('');
    setCurrentSession(null);
    setActiveTab('chat');
  };

  if (!isOpen) return null;

  return (
    <div className={`fixed inset-0 z-50 bg-black bg-opacity-50 flex items-center justify-center p-4 ${className}`}>
      <Card className="w-full max-w-6xl h-[80vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b">
          <h2 className="text-xl font-semibold">Koroh AI Assistant</h2>
          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleNewSession}
            >
              New Chat
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={onClose}
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        </div>

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
              <div className="flex-1">
                <AIChat
                  isOpen={true}
                  onClose={() => {}}
                  className="relative inset-0 w-full h-full"
                />
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

                <TabsContent value="chat" className="h-[calc(80vh-120px)]">
                  <AIChat
                    isOpen={true}
                    onClose={() => {}}
                    className="relative inset-0 w-full h-full"
                  />
                </TabsContent>

                <TabsContent value="sessions" className="h-[calc(80vh-120px)]">
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