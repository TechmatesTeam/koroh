/**
 * WebSocket client for real-time features in Koroh Platform.
 * 
 * This module provides WebSocket connections for AI chat, notifications,
 * peer group activities, and dashboard updates.
 */

import { tokenManager } from './token-manager';

export interface WebSocketMessage {
  type: string;
  data: any;
  timestamp: string;
}

export interface WebSocketConfig {
  url: string;
  protocols?: string[];
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  heartbeatInterval?: number;
}

export class WebSocketClient {
  private ws: WebSocket | null = null;
  private config: WebSocketConfig;
  private reconnectAttempts = 0;
  private reconnectTimer: NodeJS.Timeout | null = null;
  private heartbeatTimer: NodeJS.Timeout | null = null;
  private isConnecting = false;
  private isManualClose = false;
  private messageHandlers: Map<string, ((data: any) => void)[]> = new Map();
  private connectionHandlers: (() => void)[] = [];
  private disconnectionHandlers: ((event: CloseEvent) => void)[] = [];
  private errorHandlers: ((error: Event) => void)[] = [];

  constructor(config: WebSocketConfig) {
    this.config = {
      reconnectInterval: 3000,
      maxReconnectAttempts: 5,
      heartbeatInterval: 30000,
      ...config
    };
  }

  /**
   * Connect to the WebSocket server.
   */
  async connect(): Promise<void> {
    if (this.isConnecting || (this.ws && this.ws.readyState === WebSocket.OPEN)) {
      return;
    }

    this.isConnecting = true;
    this.isManualClose = false;

    try {
      // Get authentication token
      const token = await tokenManager.getValidAccessToken();
      
      // Build WebSocket URL
      const wsUrl = this.buildWebSocketUrl(token || undefined);
      
      // Create WebSocket connection
      this.ws = new WebSocket(wsUrl, this.config.protocols);
      
      this.ws.onopen = this.handleOpen.bind(this);
      this.ws.onmessage = this.handleMessage.bind(this);
      this.ws.onclose = this.handleClose.bind(this);
      this.ws.onerror = this.handleError.bind(this);

    } catch (error) {
      console.error('Failed to connect to WebSocket:', error);
      this.isConnecting = false;
      this.scheduleReconnect();
    }
  }

  /**
   * Disconnect from the WebSocket server.
   */
  disconnect(): void {
    this.isManualClose = true;
    this.clearTimers();
    
    if (this.ws) {
      this.ws.close(1000, 'Manual disconnect');
      this.ws = null;
    }
  }

  /**
   * Send a message to the WebSocket server.
   */
  send(type: string, data: any): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      console.warn('WebSocket not connected, cannot send message');
      return;
    }

    const message = {
      type,
      data,
      timestamp: new Date().toISOString()
    };

    this.ws.send(JSON.stringify(message));
  }

  /**
   * Add a message handler for a specific message type.
   */
  on(messageType: string, handler: (data: any) => void): void {
    if (!this.messageHandlers.has(messageType)) {
      this.messageHandlers.set(messageType, []);
    }
    this.messageHandlers.get(messageType)!.push(handler);
  }

  /**
   * Remove a message handler.
   */
  off(messageType: string, handler: (data: any) => void): void {
    const handlers = this.messageHandlers.get(messageType);
    if (handlers) {
      const index = handlers.indexOf(handler);
      if (index > -1) {
        handlers.splice(index, 1);
      }
    }
  }

  /**
   * Add a connection handler.
   */
  onConnect(handler: () => void): void {
    this.connectionHandlers.push(handler);
  }

  /**
   * Add a disconnection handler.
   */
  onDisconnect(handler: (event: CloseEvent) => void): void {
    this.disconnectionHandlers.push(handler);
  }

  /**
   * Add an error handler.
   */
  onError(handler: (error: Event) => void): void {
    this.errorHandlers.push(handler);
  }

  /**
   * Get the current connection state.
   */
  get readyState(): number {
    return this.ws ? this.ws.readyState : WebSocket.CLOSED;
  }

  /**
   * Check if the WebSocket is connected.
   */
  get isConnected(): boolean {
    return this.ws ? this.ws.readyState === WebSocket.OPEN : false;
  }

  private buildWebSocketUrl(token?: string): string {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = process.env.NEXT_PUBLIC_WS_HOST || window.location.host;
    let url = `${protocol}//${host}${this.config.url}`;
    
    // Add authentication token as query parameter for WebSocket
    if (token) {
      const separator = url.includes('?') ? '&' : '?';
      url += `${separator}token=${encodeURIComponent(token)}`;
    }
    
    return url;
  }

  private handleOpen(event: Event): void {
    console.log('WebSocket connected:', this.config.url);
    this.isConnecting = false;
    this.reconnectAttempts = 0;
    
    // Start heartbeat
    this.startHeartbeat();
    
    // Notify connection handlers
    this.connectionHandlers.forEach(handler => handler());
  }

  private handleMessage(event: MessageEvent): void {
    try {
      const message: WebSocketMessage = JSON.parse(event.data);
      
      // Handle heartbeat response
      if (message.type === 'pong') {
        return;
      }
      
      // Dispatch to message handlers
      const handlers = this.messageHandlers.get(message.type);
      if (handlers) {
        handlers.forEach(handler => handler(message.data));
      }
      
      // Also dispatch to 'message' handlers for all messages
      const allHandlers = this.messageHandlers.get('message');
      if (allHandlers) {
        allHandlers.forEach(handler => handler(message));
      }
      
    } catch (error) {
      console.error('Failed to parse WebSocket message:', error);
    }
  }

  private handleClose(event: CloseEvent): void {
    console.log('WebSocket disconnected:', event.code, event.reason);
    this.isConnecting = false;
    this.clearTimers();
    
    // Notify disconnection handlers
    this.disconnectionHandlers.forEach(handler => handler(event));
    
    // Attempt to reconnect if not manually closed
    if (!this.isManualClose && event.code !== 1000) {
      this.scheduleReconnect();
    }
  }

  private handleError(event: Event): void {
    console.error('WebSocket error:', event);
    this.isConnecting = false;
    
    // Notify error handlers
    this.errorHandlers.forEach(handler => handler(event));
  }

  private scheduleReconnect(): void {
    if (this.isManualClose || this.reconnectAttempts >= this.config.maxReconnectAttempts!) {
      return;
    }

    this.reconnectAttempts++;
    const delay = this.config.reconnectInterval! * Math.pow(2, this.reconnectAttempts - 1);
    
    console.log(`Scheduling WebSocket reconnect attempt ${this.reconnectAttempts} in ${delay}ms`);
    
    this.reconnectTimer = setTimeout(() => {
      this.connect();
    }, delay);
  }

  private startHeartbeat(): void {
    if (this.config.heartbeatInterval! > 0) {
      this.heartbeatTimer = setInterval(() => {
        if (this.isConnected) {
          this.send('ping', {});
        }
      }, this.config.heartbeatInterval!);
    }
  }

  private clearTimers(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }
}

/**
 * WebSocket manager for different types of connections.
 */
class WebSocketManager {
  private connections: Map<string, WebSocketClient> = new Map();

  /**
   * Get or create a WebSocket connection.
   */
  getConnection(name: string, config: WebSocketConfig): WebSocketClient {
    if (!this.connections.has(name)) {
      this.connections.set(name, new WebSocketClient(config));
    }
    return this.connections.get(name)!;
  }

  /**
   * Close a specific connection.
   */
  closeConnection(name: string): void {
    const connection = this.connections.get(name);
    if (connection) {
      connection.disconnect();
      this.connections.delete(name);
    }
  }

  /**
   * Close all connections.
   */
  closeAllConnections(): void {
    this.connections.forEach((connection, name) => {
      connection.disconnect();
    });
    this.connections.clear();
  }

  /**
   * Get AI chat WebSocket connection.
   */
  getAIChatConnection(sessionId?: string): WebSocketClient {
    const url = sessionId ? `/ws/ai-chat/${sessionId}/` : '/ws/ai-chat/';
    return this.getConnection('ai-chat', { url });
  }

  /**
   * Get notifications WebSocket connection.
   */
  getNotificationsConnection(): WebSocketClient {
    return this.getConnection('notifications', { url: '/ws/notifications/' });
  }

  /**
   * Get peer group WebSocket connection.
   */
  getPeerGroupConnection(groupSlug: string): WebSocketClient {
    return this.getConnection(`peer-group-${groupSlug}`, { 
      url: `/ws/peer-groups/${groupSlug}/` 
    });
  }

  /**
   * Get peer group activity WebSocket connection.
   */
  getPeerGroupActivityConnection(): WebSocketClient {
    return this.getConnection('peer-group-activity', { 
      url: '/ws/peer-groups/activity/' 
    });
  }

  /**
   * Get dashboard WebSocket connection.
   */
  getDashboardConnection(): WebSocketClient {
    return this.getConnection('dashboard', { url: '/ws/dashboard/' });
  }
}

// Export singleton instance
export const wsManager = new WebSocketManager();

// Cleanup on page unload
if (typeof window !== 'undefined') {
  window.addEventListener('beforeunload', () => {
    wsManager.closeAllConnections();
  });
}