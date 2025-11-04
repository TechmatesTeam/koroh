import { useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useDashboardStore } from '@/lib/stores';
import { useAuth } from '@/contexts/auth-context';
import { useNotifications } from '@/contexts/notification-context';

export function useDashboard() {
  const { user } = useAuth();
  const { addNotification } = useNotifications();
  const {
    data,
    isLoading,
    error,
    lastUpdated,
    fetchDashboardData,
    followCompany,
    joinPeerGroup,
    applyToJob,
    refreshData,
  } = useDashboardStore();

  // Use React Query for caching and background refetching
  const dashboardQuery = useQuery(
    ['dashboard', user?.id],
    async () => {
      await fetchDashboardData();
    },
    {
      enabled: !!user,
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
      refetchOnWindowFocus: true,
      refetchInterval: 5 * 60 * 1000, // Refetch every 5 minutes
    }
  );

  // Sync React Query loading state with store
  useEffect(() => {
    if (dashboardQuery.isLoading !== isLoading) {
      useDashboardStore.getState().setLoading(dashboardQuery.isLoading);
    }
  }, [dashboardQuery.isLoading, isLoading]);

  // Sync React Query error state with store
  useEffect(() => {
    if (dashboardQuery.error && !error) {
      const errorMessage = dashboardQuery.error instanceof Error 
        ? dashboardQuery.error.message 
        : 'Failed to load dashboard data';
      useDashboardStore.getState().setError(errorMessage);
    }
  }, [dashboardQuery.error, error]);

  // Enhanced actions with notifications
  const handleFollowCompany = async (companyId: string) => {
    try {
      await followCompany(companyId);
      addNotification({
        type: 'success',
        title: 'Company followed',
        message: 'You will receive updates about this company.',
      });
    } catch (error) {
      addNotification({
        type: 'error',
        title: 'Follow failed',
        message: 'Failed to follow company. Please try again.',
      });
      throw error;
    }
  };

  const handleJoinPeerGroup = async (groupSlug: string) => {
    try {
      await joinPeerGroup(groupSlug);
      addNotification({
        type: 'success',
        title: 'Joined group',
        message: 'You have successfully joined the peer group.',
      });
    } catch (error) {
      addNotification({
        type: 'error',
        title: 'Join failed',
        message: 'Failed to join group. Please try again.',
      });
      throw error;
    }
  };

  const handleApplyToJob = async (jobId: string) => {
    try {
      await applyToJob(jobId);
      addNotification({
        type: 'success',
        title: 'Application submitted',
        message: 'Your job application has been submitted successfully.',
      });
    } catch (error) {
      addNotification({
        type: 'error',
        title: 'Application failed',
        message: 'Failed to submit job application. Please try again.',
      });
      throw error;
    }
  };

  const handleRefresh = async () => {
    try {
      await refreshData();
      dashboardQuery.refetch();
    } catch (error) {
      addNotification({
        type: 'error',
        title: 'Refresh failed',
        message: 'Failed to refresh dashboard data.',
      });
    }
  };

  return {
    // Data
    data,
    isLoading: dashboardQuery.isLoading || isLoading,
    error: dashboardQuery.error || error,
    lastUpdated,
    
    // Query state
    isRefetching: dashboardQuery.isRefetching,
    isFetching: dashboardQuery.isFetching,
    
    // Actions
    followCompany: handleFollowCompany,
    joinPeerGroup: handleJoinPeerGroup,
    applyToJob: handleApplyToJob,
    refresh: handleRefresh,
    
    // Raw query for advanced usage
    query: dashboardQuery,
  };
}