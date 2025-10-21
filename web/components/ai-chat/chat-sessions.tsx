'use client';

import { useState, useEffect } from 'react';
import { Clock, MessageCircle, Trash2, Plus } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { api } from '@/lib/api';
import { useAuth } from '@/contexts/auth-context';
import { useNotifications } from '@/contexts/notification-context';
import { ChatSessionListItem } from '@/types';

interface ChatSessionsProps {
  onSessionSelect: (sessionId: string) => void;
  selectedSessionId?: string;
  className?: string;
}

export function ChatSessions({ onSessionSelect, selectedSessionId, className = '' }: ChatSessionsProps) {
  const { user } = useAuth();
  const { addNotification } = useNotifications();
  
  const [sessions, setSessions] = useState<ChatSessionListItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (user) {
      loadSessions();
    }
  }, [user]);

  const loadSessions = async () => {
    try {
      setIsLoading(true);
      const response = await api.ai.getSessions();
      setSessions(response.data.sessions || []);
    } catch (error: any) {
      console.error('Error loading chat sessions:', error);
      addNotification({
        type: 'error',
        title: 'Load Failed',
        message: 'Failed to load chat sessions',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const createNewSession = async () => {
    try {
      const response = await api.ai.createSession();
      const newSession = response.data;
      
      // Add to sessions list
      setSessions(prev => [newSession, ...prev]);
      
      // Select the new session
      onSessionSelect(newSession.id);
      
      addNotification({
        type: 'success',
        title: 'Session Created',
        message: 'New chat session created',
      });
    } catch (error: any) {
      console.error('Error creating session:', error);
      addNotification({
        type: 'error',
        title: 'Creation Failed',
        message: 'Failed to create new session',
      });
    }
  };

  const deleteSession = async (sessionId: string, event: React.MouseEvent) => {
    event.stopPropagation();
    
    if (!confirm('Are you sure you want to delete this chat session?')) {
      return;
    }

    try {
      await api.ai.deleteSession(sessionId);
      setSessions(prev => prev.filter(session => session.id !== sessionId));
      
      // If deleted session was selected, clear selection
      if (selectedSessionId === sessionId) {
        onSessionSelect('');
      }
      
      addNotification({
        type: 'success',
        title: 'Session Deleted',
        message: 'Chat session deleted',
      });
    } catch (error: any) {
      console.error('Error deleting session:', error);
      addNotification({
        type: 'error',
        title: 'Deletion Failed',
        message: 'Failed to delete session',
      });
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60);

    if (diffInHours < 1) {
      return 'Just now';
    } else if (diffInHours < 24) {
      return `${Math.floor(diffInHours)}h ago`;
    } else if (diffInHours < 168) { // 7 days
      return `${Math.floor(diffInHours / 24)}d ago`;
    } else {
      return date.toLocaleDateString();
    }
  };

  if (isLoading) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            Chat Sessions
            <Button size="sm" disabled>
              <Plus className="h-4 w-4" />
            </Button>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="animate-pulse">
                <div className="h-16 bg-gray-200 rounded-lg"></div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          Chat Sessions
          <Button size="sm" onClick={createNewSession}>
            <Plus className="h-4 w-4" />
          </Button>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {sessions.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <MessageCircle className="h-12 w-12 mx-auto mb-4 text-gray-400" />
            <p className="text-lg font-medium mb-2">No chat sessions yet</p>
            <p className="text-sm mb-4">Start a conversation with Koroh AI!</p>
            <Button onClick={createNewSession}>
              Start New Chat
            </Button>
          </div>
        ) : (
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {sessions.map((session) => (
              <div
                key={session.id}
                onClick={() => onSessionSelect(session.id)}
                className={`p-3 rounded-lg border cursor-pointer transition-all hover:bg-gray-50 ${
                  selectedSessionId === session.id 
                    ? 'border-blue-500 bg-blue-50' 
                    : 'border-gray-200'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <h4 className="font-medium text-sm truncate">
                      {session.title || 'Untitled Chat'}
                    </h4>
                    {session.last_message && (
                      <p className="text-xs text-gray-500 mt-1 truncate">
                        {session.last_message.content}
                      </p>
                    )}
                    <div className="flex items-center space-x-2 mt-2">
                      <Badge variant="secondary" className="text-xs">
                        {session.message_count} messages
                      </Badge>
                      <div className="flex items-center text-xs text-gray-400">
                        <Clock className="h-3 w-3 mr-1" />
                        {formatDate(session.updated_at)}
                      </div>
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={(e) => deleteSession(session.id, e)}
                    className="h-8 w-8 p-0 text-gray-400 hover:text-red-500"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}