import { useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useJobsStore } from '@/lib/stores';
import { useAuth } from '@/contexts/auth-context';
import { useNotifications } from '@/contexts/notification-context';
import { JobSearchParams } from '@/types';

export function useJobs() {
  const { user } = useAuth();
  const { addNotification } = useNotifications();
  const queryClient = useQueryClient();
  
  const {
    jobs,
    recommendations,
    savedJobs,
    appliedJobs,
    searchParams,
    pagination,
    isLoading,
    error,
    searchJobs,
    loadRecommendations,
    loadSavedJobs,
    updateSearchParams,
    setPage,
    clearSearch,
  } = useJobsStore();

  // Job search query
  const jobSearchQuery = useQuery(
    ['jobs', 'search', searchParams],
    async () => {
      await searchJobs(searchParams);
    },
    {
      enabled: !!(searchParams.query || searchParams.location || searchParams.job_type),
      staleTime: 2 * 60 * 1000, // 2 minutes
      cacheTime: 5 * 60 * 1000, // 5 minutes
    }
  );

  // Job recommendations query
  const recommendationsQuery = useQuery(
    ['jobs', 'recommendations', user?.id],
    async () => {
      await loadRecommendations();
    },
    {
      enabled: !!user,
      staleTime: 10 * 60 * 1000, // 10 minutes
      cacheTime: 15 * 60 * 1000, // 15 minutes
    }
  );

  // Saved jobs query
  const savedJobsQuery = useQuery(
    ['jobs', 'saved', user?.id],
    async () => {
      await loadSavedJobs();
    },
    {
      enabled: !!user,
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
    }
  );

  // Job application mutation
  const applyMutation = useMutation({
    mutationFn: async (jobId: string) => {
      await useJobsStore.getState().applyToJob(jobId);
    },
    onSuccess: () => {
      addNotification({
        type: 'success',
        title: 'Application submitted',
        message: 'Your job application has been submitted successfully.',
      });
      // Invalidate related queries
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
    },
    onError: () => {
      addNotification({
        type: 'error',
        title: 'Application failed',
        message: 'Failed to submit job application. Please try again.',
      });
    },
  });

  // Save job mutation
  const saveJobMutation = useMutation({
    mutationFn: async (jobId: string) => {
      await useJobsStore.getState().saveJob(jobId);
    },
    onSuccess: () => {
      addNotification({
        type: 'success',
        title: 'Job saved',
        message: 'Job has been added to your saved list.',
      });
      queryClient.invalidateQueries({ queryKey: ['jobs', 'saved'] });
    },
    onError: () => {
      addNotification({
        type: 'error',
        title: 'Save failed',
        message: 'Failed to save job. Please try again.',
      });
    },
  });

  // Unsave job mutation
  const unsaveJobMutation = useMutation({
    mutationFn: async (jobId: string) => {
      await useJobsStore.getState().unsaveJob(jobId);
    },
    onSuccess: () => {
      addNotification({
        type: 'success',
        title: 'Job removed',
        message: 'Job has been removed from your saved list.',
      });
      queryClient.invalidateQueries({ queryKey: ['jobs', 'saved'] });
    },
    onError: () => {
      addNotification({
        type: 'error',
        title: 'Remove failed',
        message: 'Failed to remove job. Please try again.',
      });
    },
  });

  // Enhanced search function
  const handleSearch = (params: Partial<JobSearchParams>) => {
    updateSearchParams(params);
    // The query will automatically refetch due to key change
  };

  // Enhanced page change function
  const handlePageChange = (page: number) => {
    setPage(page);
    // The query will automatically refetch due to key change
  };

  // Utility functions
  const isJobSaved = (jobId: string) => {
    return savedJobs.some(job => job.id === jobId);
  };

  const isJobApplied = (jobId: string) => {
    return appliedJobs.includes(jobId);
  };

  const refreshRecommendations = () => {
    queryClient.invalidateQueries({ queryKey: ['jobs', 'recommendations'] });
  };

  const refreshSavedJobs = () => {
    queryClient.invalidateQueries({ queryKey: ['jobs', 'saved'] });
  };

  return {
    // Data
    jobs,
    recommendations,
    savedJobs,
    appliedJobs,
    searchParams,
    pagination,
    
    // Loading states
    isLoading: jobSearchQuery.isLoading || isLoading,
    isLoadingRecommendations: recommendationsQuery.isLoading,
    isLoadingSavedJobs: savedJobsQuery.isLoading,
    isApplying: applyMutation.isPending,
    isSaving: saveJobMutation.isPending,
    isUnsaving: unsaveJobMutation.isPending,
    
    // Error states
    error: jobSearchQuery.error || error,
    recommendationsError: recommendationsQuery.error,
    savedJobsError: savedJobsQuery.error,
    
    // Actions
    search: handleSearch,
    setPage: handlePageChange,
    clearSearch,
    applyToJob: applyMutation.mutate,
    saveJob: saveJobMutation.mutate,
    unsaveJob: unsaveJobMutation.mutate,
    
    // Utilities
    isJobSaved,
    isJobApplied,
    refreshRecommendations,
    refreshSavedJobs,
    
    // Raw queries for advanced usage
    queries: {
      search: jobSearchQuery,
      recommendations: recommendationsQuery,
      savedJobs: savedJobsQuery,
    },
  };
}