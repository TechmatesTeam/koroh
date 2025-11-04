/**
 * Hook to prevent page refreshes and handle component-based updates
 */

import { useCallback } from 'react';

export function usePreventRefresh() {
  const handleClick = useCallback((callback: () => void | Promise<void>) => {
    return (e: React.MouseEvent) => {
      e.preventDefault();
      e.stopPropagation();
      
      if (callback) {
        callback();
      }
    };
  }, []);

  const handleSubmit = useCallback((callback: (data?: any) => void | Promise<void>) => {
    return (e: React.FormEvent, data?: any) => {
      e.preventDefault();
      e.stopPropagation();
      
      if (callback) {
        callback(data);
      }
    };
  }, []);

  const handleKeyPress = useCallback((callback: () => void | Promise<void>) => {
    return (e: React.KeyboardEvent) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        e.stopPropagation();
        
        if (callback) {
          callback();
        }
      }
    };
  }, []);

  return {
    handleClick,
    handleSubmit,
    handleKeyPress,
  };
}