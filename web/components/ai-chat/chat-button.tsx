'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { MessageCircle, Bot, Sparkles, ArrowRight } from 'lucide-react';
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
  const [showTooltip, setShowTooltip] = useState(true);
  const { user } = useAuth();
  const router = useRouter();

  const handleContinueChat = () => {
    router.push('/ai-chat');
  };

  const handleCloseTooltip = () => {
    setShowTooltip(false);
  };

  return (
    <>
      <div className={`fixed bottom-4 right-4 z-40 ${className}`}>
        <Button
          onClick={() => setIsChatOpen(true)}
          className="chat-button-hover relative h-12 w-12 sm:h-14 sm:w-14 rounded-full shadow-lg hover:shadow-xl bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700"
          size="lg"
        >
          <Bot className="h-5 w-5 sm:h-6 sm:w-6" />
          {!user && (
            <Badge className="absolute -top-1 -right-1 sm:-top-2 sm:-right-2 bg-green-500 text-white text-xs px-1 py-0.5 sm:px-1.5 sm:py-0.5 animate-pulse">
              Free
            </Badge>
          )}
          {user && showBadge && (
            <Badge 
              variant="destructive" 
              className="absolute -top-1 -right-1 sm:-top-2 sm:-right-2 h-4 w-4 sm:h-5 sm:w-5 rounded-full p-0 flex items-center justify-center text-xs"
            >
              AI
            </Badge>
          )}
        </Button>
        
        {!user && !isChatOpen && showTooltip && (
          <div className="chat-tooltip absolute bottom-16 sm:bottom-18 right-0 bg-white rounded-xl shadow-xl border border-gray-200 p-4 sm:p-5 w-72 sm:w-80">
            <button
              onClick={handleCloseTooltip}
              className="absolute top-3 right-3 text-gray-400 hover:text-gray-600 transition-colors p-1.5 rounded-full hover:bg-gray-100"
              aria-label="Close tooltip"
            >
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
              </svg>
            </button>
            
            <div className="flex items-start space-x-3 mb-4">
              <div className="flex-shrink-0 w-10 h-10 bg-gradient-to-r from-yellow-400 to-orange-500 rounded-full flex items-center justify-center shadow-sm">
                <Sparkles className="h-5 w-5 text-white" />
              </div>
              <div className="flex-1 min-w-0 pt-1">
                <h3 className="text-base font-semibold text-gray-900 mb-1">Try Koroh AI!</h3>
                <p className="text-sm text-gray-600 leading-relaxed">
                  Get 5 free messages for personalized career advice
                </p>
              </div>
            </div>
            
            <div className="bg-gray-50 rounded-lg p-3 mb-4">
              <div className="flex items-center justify-between text-sm">
                <span className="text-green-600 font-medium flex items-center">
                  <span className="w-2 h-2 bg-green-500 rounded-full mr-2"></span>
                  No signup required
                </span>
                <span className="text-gray-500 font-medium">5 messages free</span>
              </div>
            </div>
            
            <Button
              size="sm"
              onClick={() => setIsChatOpen(true)}
              className="w-full text-sm h-10 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 shadow-sm font-medium"
            >
              Start Free Chat
            </Button>
            
            <div className="absolute bottom-0 right-6 transform translate-y-1/2 rotate-45 w-3 h-3 bg-white border-r border-b border-gray-200"></div>
          </div>
        )}

        {user && !isChatOpen && showTooltip && (
          <div className="chat-tooltip absolute bottom-16 sm:bottom-18 right-0 bg-white rounded-xl shadow-xl border border-gray-200 p-4 sm:p-5 w-72 sm:w-80">
            <button
              onClick={handleCloseTooltip}
              className="absolute top-3 right-3 text-gray-400 hover:text-gray-600 transition-colors p-1.5 rounded-full hover:bg-gray-100"
              aria-label="Close tooltip"
            >
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
              </svg>
            </button>
            
            <div className="flex items-start space-x-3 mb-5">
              <div className="flex-shrink-0 w-10 h-10 bg-gradient-to-r from-blue-600 to-purple-600 rounded-full flex items-center justify-center shadow-sm">
                <Bot className="h-5 w-5 text-white" />
              </div>
              <div className="flex-1 min-w-0 pt-1">
                <h3 className="text-base font-semibold text-gray-900 mb-1">Koroh AI Assistant</h3>
                <p className="text-sm text-gray-600 leading-relaxed">
                  Get personalized career guidance and insights
                </p>
              </div>
            </div>
            
            <div className="space-y-3">
              <Button
                size="sm"
                onClick={() => setIsChatOpen(true)}
                className="w-full text-sm h-10 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 shadow-sm font-medium"
              >
                <MessageCircle className="h-4 w-4 mr-2" />
                Quick Chat
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={handleContinueChat}
                className="w-full text-sm h-10 flex items-center justify-center space-x-2 hover:bg-gray-50 border-gray-300"
              >
                <span>Open Full Chat</span>
                <ArrowRight className="h-4 w-4" />
              </Button>
            </div>
            
            <div className="absolute bottom-0 right-6 transform translate-y-1/2 rotate-45 w-3 h-3 bg-white border-r border-b border-gray-200"></div>
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