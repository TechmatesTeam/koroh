/**
 * React hooks for real-time WebSocket functionality.
 * 
 * This module provides React hooks for connecting to WebSocket services
 * and handling real-time updates in components.
 */

import { useEffect, useRef, useState, useCallback } from 'react';
import { wsManager, WebSocketClient } from '../websocket';
import { useAuth } from '@/contexts/auth-context';
import { useNotifications } from '@/contexts/notification-context';

export interface UseRealtimeOptions {
  autoConnect?: boolean;
  onConnect?: () => void;
  onDisconnect?: (event: CloseEvent) => void;
  onError?: (error: Event) => void;
}

/**
 * Base hook for WebSocket connections.
 */
export function useWebSocket(
  connectionName: string,
  getConnection: () => WebSocketClient,
  options: UseRealtimeOptions = {}
) {
  const { user } = useAuth();
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const connectionRef = useRef<WebSocketClient | null>(null);
  const { autoConnect = true, onConnect, onDisconnect, onError } = options;

  const connect = useCallback(async () => {
    if (!user || isConnecting || isConnected) return;

    setIsConnecting(true);
    try {
      const connection = getConnection();
      connectionRef.current = connection;

      // Set up event handlers
      connection.onConnect(() => {
        setIsConnected(true);
        setIsConnecting(false);
        onConnect?.();
      });

      connection.onDisconnect((event) => {
        setIsConnected(false);
        setIsConnecting(false);
        onDisconnect?.(event);
      });

      connection.onError((error) => {
        setIsConnecting(false);
        onError?.(error);
      });

      await connection.connect();
    } catch (error) {
      console.error(`Failed to connect to ${connectionName}:`, error);
      setIsConnecting(false);
    }
  }, [user, isConnecting, isConnected, getConnection, connectionName, onConnect, onDisconnect, onError]);

  const disconnect = useCallback(() => {
    if (connectionRef.current) {
      connectionRef.current.disconnect();
      connectionRef.current = null;
    }
    setIsConnected(false);
    setIsConnecting(false);
  }, []);

  const send = useCallback((type: string, data: any) => {
    if (connectionRef.current && isConnected) {
      connectionRef.current.send(type, data);
    }
  }, [isConnected]);

  const on = useCallback((messageType: string, handler: (data: any) => void) => {
    if (connectionRef.current) {
      connectionRef.current.on(messageType, handler);
    }
  }, []);

  const off = useCallback((messageType: string, handler: (data: any) => void) => {
    if (connectionRef.current) {
      connectionRef.current.off(messageType, handler);
    }
  }, []);

  // Auto-connect when user is available
  useEffect(() => {
    if (user && autoConnect) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [user, autoConnect, connect, disconnect]);

  return {
    isConnected,
    isConnecting,
    connect,
    disconnect,
    send,
    on,
    off,
    connection: connectionRef.current
  };
}

/**
 * Hook for AI chat real-time functionality.
 */
export function useAIChat(sessionId?: string, options: UseRealtimeOptions = {}) {
  const [messages, setMessages] = useState<any[]>([]);
  const [isTyping, setIsTyping] = useState(false);

  const websocket = useWebSocket(
    'ai-chat',
    () => wsManager.getAIChatConnection(sessionId),
    options
  );

  // Handle incoming messages
  useEffect(() => {
    if (!websocket.connection) return;

    const handleMessageResponse = (data: any) => {
      setMessages(prev => [
        ...prev,
        data.user_message,
        data.ai_response
      ]);
    };

    const handleTyping = (data: any) => {
      setIsTyping(data.is_typing);
    };

    websocket.on('message_response', handleMessageResponse);
    websocket.on('typing', handleTyping);

    return () => {
      websocket.off('message_response', handleMessageResponse);
      websocket.off('typing', handleTyping);
    };
  }, [websocket]);

  const sendMessage = useCallback((message: string) => {
    websocket.send('send_message', { message });
  }, [websocket]);

  const sendTyping = useCallback((isTyping: boolean) => {
    websocket.send(isTyping ? 'typing' : 'stop_typing', {});
  }, [websocket]);

  return {
    ...websocket,
    messages,
    isTyping,
    sendMessage,
    sendTyping
  };
}

/**
 * Hook for notifications real-time functionality.
 */
export function useRealtimeNotifications(options: UseRealtimeOptions = {}) {
  const { addNotification } = useNotifications();
  const [unreadCount, setUnreadCount] = useState(0);

  const websocket = useWebSocket(
    'notifications',
    () => wsManager.getNotificationsConnection(),
    options
  );

  // Handle incoming notifications
  useEffect(() => {
    if (!websocket.connection) return;

    const handleNewNotification = (data: any) => {
      addNotification({
        type: data.type || 'info',
        title: data.title,
        message: data.message,
        duration: data.duration
      });
      setUnreadCount(prev => prev + 1);
    };

    const handleNotificationUpdate = (data: any) => {
      if (data.unread_count !== undefined) {
        setUnreadCount(data.unread_count);
      }
    };

    websocket.on('new_notification', handleNewNotification);
    websocket.on('notification_update', handleNotificationUpdate);

    return () => {
      websocket.off('new_notification', handleNewNotification);
      websocket.off('notification_update', handleNotificationUpdate);
    };
  }, [websocket, addNotification]);

  const markAsRead = useCallback((notificationIds: string[]) => {
    websocket.send('mark_read', { notification_ids: notificationIds });
  }, [websocket]);

  return {
    ...websocket,
    unreadCount,
    markAsRead
  };
}

/**
 * Hook for peer group real-time functionality.
 */
export function usePeerGroupRealtime(groupSlug: string, options: UseRealtimeOptions = {}) {
  const [newPosts, setNewPosts] = useState<any[]>([]);
  const [newComments, setNewComments] = useState<any[]>([]);
  const [newMembers, setNewMembers] = useState<any[]>([]);
  const [typingUsers, setTypingUsers] = useState<string[]>([]);

  const websocket = useWebSocket(
    `peer-group-${groupSlug}`,
    () => wsManager.getPeerGroupConnection(groupSlug),
    options
  );

  // Handle incoming updates
  useEffect(() => {
    if (!websocket.connection) return;

    const handleNewPost = (data: any) => {
      setNewPosts(prev => [data, ...prev]);
    };

    const handleNewComment = (data: any) => {
      setNewComments(prev => [data, ...prev]);
    };

    const handleMemberJoined = (data: any) => {
      setNewMembers(prev => [data, ...prev]);
    };

    const handleUserTyping = (data: any) => {
      setTypingUsers(prev => {
        if (data.is_typing) {
          return prev.includes(data.user_name) ? prev : [...prev, data.user_name];
        } else {
          return prev.filter(name => name !== data.user_name);
        }
      });
    };

    websocket.on('new_post', handleNewPost);
    websocket.on('new_comment', handleNewComment);
    websocket.on('member_joined', handleMemberJoined);
    websocket.on('user_typing', handleUserTyping);

    return () => {
      websocket.off('new_post', handleNewPost);
      websocket.off('new_comment', handleNewComment);
      websocket.off('member_joined', handleMemberJoined);
      websocket.off('user_typing', handleUserTyping);
    };
  }, [websocket]);

  const sendTyping = useCallback((isTyping: boolean) => {
    websocket.send('user_typing', { is_typing: isTyping });
  }, [websocket]);

  const clearNewPosts = useCallback(() => {
    setNewPosts([]);
  }, []);

  const clearNewComments = useCallback(() => {
    setNewComments([]);
  }, []);

  const clearNewMembers = useCallback(() => {
    setNewMembers([]);
  }, []);

  return {
    ...websocket,
    newPosts,
    newComments,
    newMembers,
    typingUsers,
    sendTyping,
    clearNewPosts,
    clearNewComments,
    clearNewMembers
  };
}

/**
 * Hook for dashboard real-time functionality.
 */
export function useDashboardRealtime(options: UseRealtimeOptions = {}) {
  const [jobRecommendations, setJobRecommendations] = useState<any[]>([]);
  const [companyUpdates, setCompanyUpdates] = useState<any[]>([]);
  const [shouldRefresh, setShouldRefresh] = useState(false);

  const websocket = useWebSocket(
    'dashboard',
    () => wsManager.getDashboardConnection(),
    options
  );

  // Handle incoming updates
  useEffect(() => {
    if (!websocket.connection) return;

    const handleJobRecommendationUpdate = (data: any) => {
      setJobRecommendations(prev => [data, ...prev]);
    };

    const handleCompanyUpdate = (data: any) => {
      setCompanyUpdates(prev => [data, ...prev]);
    };

    const handleDashboardRefresh = (data: any) => {
      setShouldRefresh(true);
    };

    websocket.on('job_recommendation_update', handleJobRecommendationUpdate);
    websocket.on('company_update', handleCompanyUpdate);
    websocket.on('dashboard_refresh', handleDashboardRefresh);

    return () => {
      websocket.off('job_recommendation_update', handleJobRecommendationUpdate);
      websocket.off('company_update', handleCompanyUpdate);
      websocket.off('dashboard_refresh', handleDashboardRefresh);
    };
  }, [websocket]);

  const refreshData = useCallback(() => {
    websocket.send('refresh_data', {});
    setShouldRefresh(false);
  }, [websocket]);

  const clearUpdates = useCallback(() => {
    setJobRecommendations([]);
    setCompanyUpdates([]);
    setShouldRefresh(false);
  }, []);

  return {
    ...websocket,
    jobRecommendations,
    companyUpdates,
    shouldRefresh,
    refreshData,
    clearUpdates
  };
}