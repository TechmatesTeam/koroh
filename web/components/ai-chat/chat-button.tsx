'use client';

import { useState } from 'react';
import { MessageCircle, Bot, Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { AIChat } from './ai-chat';
import { useAuth } from '@/contexts/auth-context';

interface ChatButtonProps {
  className?: string;
  initialMessage?: string;
  showBadge?: boolean;
}

export function ChatButton({ className = '', initialMessage, showBadge = true }: ChatButtonProps) {
  const [isChatOpen, setIsChatOpen] = useState(false);
  const { user } = useAuth();

  return (
    <>
      <div className={`fixed bottom-4 right-4 z-40 ${className}`}>
        <Button
          onClick={() => setIsChatOpen(true)}
          className="relative h-14 w-14 rounded-full shadow-lg hover:shadow-xl transition-all duration-300 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700"
          size="lg"
        >
          <Bot className="h-6 w-6" />
          {!user && (
            <Badge className="absolute -top-2 -right-2 bg-green-500 text-white text-xs px-1.5 py-0.5 animate-pulse">
              Free
            </Badge>
          )}
          {user && showBadge && (
            <Badge 
              variant="destructive" 
              className="absolute -top-2 -right-2 h-5 w-5 rounded-full p-0 flex items-center justify-center text-xs"
            >
              AI
            </Badge>
          )}
        </Button>
        
        {!user && !isChatOpen && (
          <div className="absolute bottom-16 right-0 bg-white rounded-lg shadow-lg p-3 max-w-xs animate-bounce">
            <div className="flex items-center space-x-2">
              <Sparkles className="h-4 w-4 text-yellow-500" />
              <p className="text-sm font-medium">Try Koroh AI!</p>
            </div>
            <p className="text-xs text-gray-600 mt-1">
              5 free messages to get career advice
            </p>
            <div className="absolute bottom-0 right-4 transform translate-y-1/2 rotate-45 w-2 h-2 bg-white border-r border-b border-gray-200"></div>
          </div>
        )}
      </div>

      <AIChat
        isOpen={isChatOpen}
        onClose={() => setIsChatOpen(false)}
        initialMessage={initialMessage}
      />
    </>
  );
}