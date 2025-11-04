import { useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { usePeerGroupsStore } from '@/lib/stores';
import { useAuth } from '@/contexts/auth-context';
import { useNotifications } from '@/contexts/notification-context';

interface PeerGroupSearchParams {
  query?: string;
  industry?: string;
  experience_level?: string;
  page?: number;
  limit?: number;
}

export function usePeerGroups() {
  const { user } = useAuth();
  const { addNotification } = useNotifications();
  const queryClient = useQueryClient();
  
  const {
    allGroups,
    joinedGroups,
    recommendations,
    currentGroup,
    groupMessages,
    searchParams,
    pagination,
    isLoading,
    error,
    searchGroups,
    loadRecommendations,
    loadJoinedGroups,
    loadGroupDetails,
    loadGroupMessages,
    updateSearchParams,
    setPage,
    clearSearch,
    setCurrentGroup,
  } = usePeerGroupsStore();

  // Group search query
  const groupSearchQuery = useQuery(
    ['peer-groups', 'search', searchParams],
    async () => {
      await searchGroups(searchParams);
    },
    {
      enabled: !!(searchParams.query || searchParams.industry || searchParams.experience_level),
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
    }
  );

  // Group recommendations query
  const recommendationsQuery = useQuery(
    ['peer-groups', 'recommendations', user?.id],
    async () => {
      await loadRecommendations();
    },
    {
      enabled: !!user,
      staleTime: 10 * 60 * 1000, // 10 minutes
      cacheTime: 15 * 60 * 1000, // 15 minutes
    }
  );

  // Joined groups query
  const joinedGroupsQuery = useQuery(
    ['peer-groups', 'joined', user?.id],
    async () => {
      await loadJoinedGroups();
    },
    {
      enabled: !!user,
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
    }
  );

  // Current group details query
  const currentGroupQuery = useQuery(
    ['peer-groups', 'details', currentGroup?.slug],
    async () => {
      if (currentGroup) {
        await loadGroupDetails(currentGroup.slug);
      }
    },
    {
      enabled: !!currentGroup?.slug,
      staleTime: 2 * 60 * 1000, // 2 minutes
      cacheTime: 5 * 60 * 1000, // 5 minutes
    }
  );

  // Group messages query
  const messagesQuery = useQuery(
    ['peer-groups', 'messages', currentGroup?.slug],
    async () => {
      if (currentGroup) {
        await loadGroupMessages(currentGroup.slug);
      }
    },
    {
      enabled: !!currentGroup?.slug,
      staleTime: 30 * 1000, // 30 seconds
      cacheTime: 2 * 60 * 1000, // 2 minutes
      refetchInterval: 30 * 1000, // Refetch every 30 seconds for real-time feel
    }
  );

  // Join group mutation
  const joinMutation = useMutation({
    mutationFn: async (groupSlug: string) => {
      await usePeerGroupsStore.getState().joinGroup(groupSlug);
    },
    onSuccess: () => {
      addNotification({
        type: 'success',
        title: 'Joined group',
        message: 'You have successfully joined the peer group.',
      });
      // Invalidate related queries
      queryClient.invalidateQueries({ queryKey: ['peer-groups', 'joined'] });
      queryClient.invalidateQueries({ queryKey: ['peer-groups', 'recommendations'] });
    },
    onError: () => {
      addNotification({
        type: 'error',
        title: 'Join failed',
        message: 'Failed to join group. Please try again.',
      });
    },
  });

  // Leave group mutation
  const leaveMutation = useMutation({
    mutationFn: async (groupSlug: string) => {
      await usePeerGroupsStore.getState().leaveGroup(groupSlug);
    },
    onSuccess: () => {
      addNotification({
        type: 'success',
        title: 'Left group',
        message: 'You have successfully left the peer group.',
      });
      // Invalidate related queries
      queryClient.invalidateQueries({ queryKey: ['peer-groups', 'joined'] });
    },
    onError: () => {
      addNotification({
        type: 'error',
        title: 'Leave failed',
        message: 'Failed to leave group. Please try again.',
      });
    },
  });

  // Send message mutation
  const sendMessageMutation = useMutation({
    mutationFn: async ({ groupSlug, content }: { groupSlug: string; content: string }) => {
      await usePeerGroupsStore.getState().sendMessage(groupSlug, content);
    },
    onSuccess: () => {
      // Invalidate messages query to refresh
      queryClient.invalidateQueries({ queryKey: ['peer-groups', 'messages', currentGroup?.slug] });
    },
    onError: () => {
      addNotification({
        type: 'error',
        title: 'Message failed',
        message: 'Failed to send message. Please try again.',
      });
    },
  });

  // Enhanced search function
  const handleSearch = (params: Partial<PeerGroupSearchParams>) => {
    updateSearchParams(params);
    // The query will automatically refetch due to key change
  };

  // Enhanced page change function
  const handlePageChange = (page: number) => {
    setPage(page);
    // The query will automatically refetch due to key change
  };

  // Enhanced group join/leave function
  const handleGroupMembership = async (groupSlug: string, isMember: boolean) => {
    if (isMember) {
      leaveMutation.mutate(groupSlug);
    } else {
      joinMutation.mutate(groupSlug);
    }
  };

  // Enhanced send message function
  const handleSendMessage = (content: string) => {
    if (currentGroup) {
      sendMessageMutation.mutate({ groupSlug: currentGroup.slug, content });
    }
  };

  // Utility functions
  const isGroupMember = (groupSlug: string) => {
    return joinedGroups.some(group => group.slug === groupSlug) ||
           allGroups.some(group => group.slug === groupSlug && group.is_member) ||
           recommendations.some(group => group.slug === groupSlug && group.is_member);
  };

  const getGroupBySlug = (groupSlug: string) => {
    return allGroups.find(group => group.slug === groupSlug) ||
           joinedGroups.find(group => group.slug === groupSlug) ||
           recommendations.find(group => group.slug === groupSlug);
  };

  const getCurrentGroupMessages = () => {
    return currentGroup ? groupMessages[currentGroup.slug] || [] : [];
  };

  const refreshRecommendations = () => {
    queryClient.invalidateQueries({ queryKey: ['peer-groups', 'recommendations'] });
  };

  const refreshJoinedGroups = () => {
    queryClient.invalidateQueries({ queryKey: ['peer-groups', 'joined'] });
  };

  const refreshMessages = () => {
    if (currentGroup) {
      queryClient.invalidateQueries({ queryKey: ['peer-groups', 'messages', currentGroup.slug] });
    }
  };

  return {
    // Data
    allGroups,
    joinedGroups,
    recommendations,
    currentGroup,
    messages: getCurrentGroupMessages(),
    searchParams,
    pagination,
    
    // Loading states
    isLoading: groupSearchQuery.isLoading || isLoading,
    isLoadingRecommendations: recommendationsQuery.isLoading,
    isLoadingJoined: joinedGroupsQuery.isLoading,
    isLoadingCurrentGroup: currentGroupQuery.isLoading,
    isLoadingMessages: messagesQuery.isLoading,
    isJoining: joinMutation.isPending,
    isLeaving: leaveMutation.isPending,
    isSendingMessage: sendMessageMutation.isPending,
    
    // Error states
    error: groupSearchQuery.error || error,
    recommendationsError: recommendationsQuery.error,
    joinedError: joinedGroupsQuery.error,
    currentGroupError: currentGroupQuery.error,
    messagesError: messagesQuery.error,
    
    // Actions
    search: handleSearch,
    setPage: handlePageChange,
    clearSearch,
    setCurrentGroup,
    joinGroup: handleGroupMembership,
    sendMessage: handleSendMessage,
    
    // Utilities
    isGroupMember,
    getGroupBySlug,
    refreshRecommendations,
    refreshJoinedGroups,
    refreshMessages,
    
    // Raw queries for advanced usage
    queries: {
      search: groupSearchQuery,
      recommendations: recommendationsQuery,
      joined: joinedGroupsQuery,
      currentGroup: currentGroupQuery,
      messages: messagesQuery,
    },
  };
}