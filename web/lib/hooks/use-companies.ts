import { useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useCompaniesStore } from '@/lib/stores';
import { useAuth } from '@/contexts/auth-context';
import { useNotifications } from '@/contexts/notification-context';

interface CompanySearchParams {
  query?: string;
  industry?: string;
  size?: string;
  location?: string;
  page?: number;
  limit?: number;
  following?: boolean;
}

export function useCompanies() {
  const { user } = useAuth();
  const { addNotification } = useNotifications();
  const queryClient = useQueryClient();
  
  const {
    companies,
    followedCompanies,
    companyInsights,
    searchParams,
    pagination,
    isLoading,
    error,
    searchCompanies,
    loadFollowedCompanies,
    loadCompanyInsights,
    updateSearchParams,
    setPage,
    clearSearch,
  } = useCompaniesStore();

  // Company search query
  const companySearchQuery = useQuery(
    ['companies', 'search', searchParams],
    async () => {
      await searchCompanies(searchParams);
    },
    {
      enabled: !!(searchParams.query || searchParams.industry || searchParams.size || searchParams.location),
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
    }
  );

  // Followed companies query
  const followedCompaniesQuery = useQuery(
    ['companies', 'followed', user?.id],
    async () => {
      await loadFollowedCompanies();
    },
    {
      enabled: !!user,
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
    }
  );

  // Company insights query
  const insightsQuery = useQuery(
    ['companies', 'insights', user?.id],
    async () => {
      await loadCompanyInsights();
    },
    {
      enabled: !!user,
      staleTime: 15 * 60 * 1000, // 15 minutes
      cacheTime: 30 * 60 * 1000, // 30 minutes
    }
  );

  // Follow company mutation
  const followMutation = useMutation({
    mutationFn: async (companyId: string) => {
      await useCompaniesStore.getState().followCompany(companyId);
    },
    onSuccess: () => {
      addNotification({
        type: 'success',
        title: 'Company followed',
        message: 'You will receive updates about this company.',
      });
      // Invalidate related queries
      queryClient.invalidateQueries({ queryKey: ['companies', 'followed'] });
      queryClient.invalidateQueries({ queryKey: ['companies', 'insights'] });
    },
    onError: () => {
      addNotification({
        type: 'error',
        title: 'Follow failed',
        message: 'Failed to follow company. Please try again.',
      });
    },
  });

  // Unfollow company mutation
  const unfollowMutation = useMutation({
    mutationFn: async (companyId: string) => {
      await useCompaniesStore.getState().unfollowCompany(companyId);
    },
    onSuccess: () => {
      addNotification({
        type: 'success',
        title: 'Company unfollowed',
        message: 'You will no longer receive updates about this company.',
      });
      // Invalidate related queries
      queryClient.invalidateQueries({ queryKey: ['companies', 'followed'] });
      queryClient.invalidateQueries({ queryKey: ['companies', 'insights'] });
    },
    onError: () => {
      addNotification({
        type: 'error',
        title: 'Unfollow failed',
        message: 'Failed to unfollow company. Please try again.',
      });
    },
  });

  // Enhanced search function
  const handleSearch = (params: Partial<CompanySearchParams>) => {
    updateSearchParams(params);
    // The query will automatically refetch due to key change
  };

  // Enhanced page change function
  const handlePageChange = (page: number) => {
    setPage(page);
    // The query will automatically refetch due to key change
  };

  // Enhanced follow/unfollow function
  const handleCompanyFollow = async (companyId: string, isFollowing: boolean) => {
    if (isFollowing) {
      unfollowMutation.mutate(companyId);
    } else {
      followMutation.mutate(companyId);
    }
  };

  // Utility functions
  const isCompanyFollowed = (companyId: string) => {
    return followedCompanies.some(company => company.id === companyId) ||
           companies.some(company => company.id === companyId && company.is_following);
  };

  const getCompanyById = (companyId: string) => {
    return companies.find(company => company.id === companyId) ||
           followedCompanies.find(company => company.id === companyId);
  };

  const refreshFollowedCompanies = () => {
    queryClient.invalidateQueries({ queryKey: ['companies', 'followed'] });
  };

  const refreshInsights = () => {
    queryClient.invalidateQueries({ queryKey: ['companies', 'insights'] });
  };

  return {
    // Data
    companies,
    followedCompanies,
    companyInsights,
    searchParams,
    pagination,
    
    // Loading states
    isLoading: companySearchQuery.isLoading || isLoading,
    isLoadingFollowed: followedCompaniesQuery.isLoading,
    isLoadingInsights: insightsQuery.isLoading,
    isFollowing: followMutation.isPending,
    isUnfollowing: unfollowMutation.isPending,
    
    // Error states
    error: companySearchQuery.error || error,
    followedError: followedCompaniesQuery.error,
    insightsError: insightsQuery.error,
    
    // Actions
    search: handleSearch,
    setPage: handlePageChange,
    clearSearch,
    followCompany: handleCompanyFollow,
    
    // Utilities
    isCompanyFollowed,
    getCompanyById,
    refreshFollowedCompanies,
    refreshInsights,
    
    // Raw queries for advanced usage
    queries: {
      search: companySearchQuery,
      followed: followedCompaniesQuery,
      insights: insightsQuery,
    },
  };
}