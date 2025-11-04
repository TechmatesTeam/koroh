'use client';

import { useState, useEffect } from 'react';
import { Brain, Target, Lightbulb, MessageSquare, TrendingUp } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { api } from '@/lib/api';

interface ConversationContextProps {
  sessionId: string;
  isVisible: boolean;
  onToggle: () => void;
}

interface ContextData {
  conversation_stage: string;
  active_topics: string[];
  recent_intents: string[];
  key_entities: Record<string, string[]>;
  user_goals: string[];
  key_insights: string[];
  context_confidence: number;
  active_features: string[];
  conversation_summary: string;
  context_version: number;
}

export function ConversationContext({ sessionId, isVisible, onToggle }: ConversationContextProps) {
  const [contextData, setContextData] = useState<ContextData | null>(null);
  const [loading, setLoading] = useState(false);
  const [messageCount, setMessageCount] = useState(0);

  useEffect(() => {
    if (isVisible && sessionId) {
      fetchContext();
    }
  }, [isVisible, sessionId]);

  const fetchContext = async () => {
    if (!sessionId) return;
    
    setLoading(true);
    try {
      const response = await api.ai.getConversationContext(sessionId);
      setContextData(response.data.context);
      setMessageCount(response.data.message_count);
    } catch (error) {
      console.error('Error fetching conversation context:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStageColor = (stage: string) => {
    const colors = {
      greeting: 'bg-blue-100 text-blue-800',
      initial: 'bg-gray-100 text-gray-800',
      exploration: 'bg-green-100 text-green-800',
      task_focused: 'bg-purple-100 text-purple-800',
      follow_up: 'bg-orange-100 text-orange-800'
    };
    return colors[stage as keyof typeof colors] || 'bg-gray-100 text-gray-800';
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.7) return 'text-green-600';
    if (confidence >= 0.4) return 'text-yellow-600';
    return 'text-red-600';
  };

  if (!isVisible) {
    return (
      <Button
        variant="outline"
        size="sm"
        onClick={onToggle}
        className="fixed bottom-20 right-4 z-40"
      >
        <Brain className="h-4 w-4 mr-1" />
        Context
      </Button>
    );
  }

  return (
    <Card className="fixed bottom-20 right-4 w-80 max-h-96 overflow-y-auto z-40 shadow-lg">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm flex items-center">
            <Brain className="h-4 w-4 mr-2" />
            Conversation Context
          </CardTitle>
          <Button variant="ghost" size="sm" onClick={onToggle} className="h-6 w-6 p-0">
            ×
          </Button>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-3 text-xs">
        {loading ? (
          <div className="text-center py-4">Loading context...</div>
        ) : contextData ? (
          <>
            {/* Basic Info */}
            <div className="flex items-center justify-between">
              <span className="text-gray-600">Messages:</span>
              <Badge variant="secondary">{messageCount}</Badge>
            </div>
            
            <div className="flex items-center justify-between">
              <span className="text-gray-600">Stage:</span>
              <Badge className={getStageColor(contextData.conversation_stage)}>
                {contextData.conversation_stage.replace('_', ' ')}
              </Badge>
            </div>
            
            <div className="flex items-center justify-between">
              <span className="text-gray-600">Confidence:</span>
              <span className={`font-medium ${getConfidenceColor(contextData.context_confidence)}`}>
                {(contextData.context_confidence * 100).toFixed(0)}%
              </span>
            </div>

            {/* Active Topics */}
            {contextData.active_topics.length > 0 && (
              <div>
                <div className="flex items-center mb-1">
                  <MessageSquare className="h-3 w-3 mr-1" />
                  <span className="font-medium">Active Topics</span>
                </div>
                <div className="flex flex-wrap gap-1">
                  {contextData.active_topics.map((topic, index) => (
                    <Badge key={index} variant="outline" className="text-xs">
                      {topic.replace('_', ' ')}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {/* User Goals */}
            {contextData.user_goals.length > 0 && (
              <div>
                <div className="flex items-center mb-1">
                  <Target className="h-3 w-3 mr-1" />
                  <span className="font-medium">User Goals</span>
                </div>
                <div className="space-y-1">
                  {contextData.user_goals.map((goal, index) => (
                    <div key={index} className="text-xs text-gray-600">
                      • {goal}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Key Insights */}
            {contextData.key_insights.length > 0 && (
              <div>
                <div className="flex items-center mb-1">
                  <Lightbulb className="h-3 w-3 mr-1" />
                  <span className="font-medium">Key Insights</span>
                </div>
                <div className="space-y-1">
                  {contextData.key_insights.map((insight, index) => (
                    <div key={index} className="text-xs text-gray-600">
                      • {insight}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Entities */}
            {Object.keys(contextData.key_entities).length > 0 && (
              <div>
                <div className="flex items-center mb-1">
                  <TrendingUp className="h-3 w-3 mr-1" />
                  <span className="font-medium">Mentioned</span>
                </div>
                <div className="space-y-1">
                  {Object.entries(contextData.key_entities).map(([type, entities]) => (
                    <div key={type} className="text-xs">
                      <span className="font-medium text-gray-700 capitalize">
                        {type.replace('_', ' ')}:
                      </span>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {entities.map((entity, index) => (
                          <Badge key={index} variant="outline" className="text-xs">
                            {entity}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Recent Intents */}
            {contextData.recent_intents.length > 0 && (
              <div>
                <div className="flex items-center mb-1">
                  <span className="font-medium text-xs">Recent Intents</span>
                </div>
                <div className="flex flex-wrap gap-1">
                  {contextData.recent_intents.map((intent, index) => (
                    <Badge key={index} variant="secondary" className="text-xs">
                      {intent.replace('_', ' ')}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {/* Summary */}
            {contextData.conversation_summary && (
              <div>
                <div className="font-medium text-xs mb-1">Summary</div>
                <div className="text-xs text-gray-600 bg-gray-50 p-2 rounded">
                  {contextData.conversation_summary}
                </div>
              </div>
            )}

            {/* Refresh Button */}
            <Button
              variant="outline"
              size="sm"
              onClick={fetchContext}
              disabled={loading}
              className="w-full text-xs"
            >
              Refresh Context
            </Button>
          </>
        ) : (
          <div className="text-center py-4 text-gray-500">
            No context data available
          </div>
        )}
      </CardContent>
    </Card>
  );
}