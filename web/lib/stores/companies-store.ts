import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { api } from '@/lib/api';
import { logError } from '@/lib/error-handler';
import { LoadingState, PaginationState, StoreActions } from './types';
import { Company } from '@/types';

interface CompanySearchParams {
  query?: string;
  industry?: string;
  size?: string;
  location?: string;
  page?: number;
  limit?: number;
  following?: boolean;
}

interface CompaniesState extends LoadingState, StoreActions {
  // Data
  companies: Company[];
  followedCompanies: Company[];
  companyInsights: {
    totalFollowed: number;
    newJobsThisWeek: number;
    topIndustries: string[];
    averageRating: number;
  };
  
  // Search and pagination
  searchParams: CompanySearchParams;
  pagination: PaginationState;
  
  // Actions
  searchCompanies: (params?: Partial<CompanySearchParams>) => Promise<void>;
  loadFollowedCompanies: () => Promise<void>;
  followCompany: (companyId: string) => Promise<void>;
  unfollowCompany: (companyId: string) => Promise<void>;
  loadCompanyInsights: () => Promise<void>;
  updateSearchParams: (params: Partial<CompanySearchParams>) => void;
  setPage: (page: number) => void;
  clearSearch: () => void;
}

const initialSearchParams: CompanySearchParams = {
  query: '',
  industry: '',
  size: '',
  location: '',
  page: 1,
  limit: 20,
};

const initialPagination: PaginationState = {
  page: 1,
  limit: 20,
  totalCount: 0,
  hasNextPage: false,
  hasPreviousPage: false,
};

const initialInsights = {
  totalFollowed: 0,
  newJobsThisWeek: 0,
  topIndustries: [],
  averageRating: 0,
};

export const useCompaniesStore = create<CompaniesState>()(
  devtools(
    (set, get) => ({
      // Initial state
      companies: [],
      followedCompanies: [],
      companyInsights: initialInsights,
      searchParams: initialSearchParams,
      pagination: initialPagination,
      isLoading: false,
      error: null,

      // Actions
      searchCompanies: async (params?: Partial<CompanySearchParams>) => {
        try {
          set({ isLoading: true, error: null });

          const currentParams = get().searchParams;
          const searchParams = { ...currentParams, ...params };

          const response = await api.companies.search(searchParams);
          const { results, count, next, previous } = response.data;

          const page = searchParams.page || 1;
          const limit = searchParams.limit || 20;

          set({
            companies: results,
            searchParams,
            pagination: {
              page,
              limit,
              totalCount: count,
              hasNextPage: !!next,
              hasPreviousPage: !!previous,
            },
            isLoading: false,
          });
        } catch (error) {
          logError(error, 'Company search');
          set({
            isLoading: false,
            error: 'Failed to search companies',
          });
        }
      },

      loadFollowedCompanies: async () => {
        try {
          const response = await api.companies.search({ following: true });
          const followedCompanies = response.data.results || [];
          
          set({
            followedCompanies,
            companyInsights: {
              ...get().companyInsights,
              totalFollowed: followedCompanies.length,
            },
          });
        } catch (error) {
          logError(error, 'Load followed companies');
          // Don't set error as this is not critical
        }
      },

      followCompany: async (companyId: string) => {
        try {
          await api.companies.follow(companyId);
          
          // Update the company in both lists
          const updateCompanyFollowStatus = (companies: Company[]) =>
            companies.map(company =>
              company.id === companyId
                ? { ...company, is_following: true }
                : company
            );

          const currentCompanies = get().companies;
          const currentFollowed = get().followedCompanies;
          
          // Find the company to add to followed list
          const companyToFollow = currentCompanies.find(c => c.id === companyId);
          
          set({
            companies: updateCompanyFollowStatus(currentCompanies),
            followedCompanies: companyToFollow 
              ? [...currentFollowed, { ...companyToFollow, is_following: true }]
              : currentFollowed,
          });

          // Update insights
          const insights = get().companyInsights;
          set({
            companyInsights: {
              ...insights,
              totalFollowed: insights.totalFollowed + 1,
            },
          });
        } catch (error) {
          logError(error, 'Follow company');
          throw error;
        }
      },

      unfollowCompany: async (companyId: string) => {
        try {
          await api.companies.unfollow(companyId);
          
          // Update the company in both lists
          const updateCompanyFollowStatus = (companies: Company[]) =>
            companies.map(company =>
              company.id === companyId
                ? { ...company, is_following: false }
                : company
            );

          set({
            companies: updateCompanyFollowStatus(get().companies),
            followedCompanies: get().followedCompanies.filter(c => c.id !== companyId),
          });

          // Update insights
          const insights = get().companyInsights;
          set({
            companyInsights: {
              ...insights,
              totalFollowed: Math.max(0, insights.totalFollowed - 1),
            },
          });
        } catch (error) {
          logError(error, 'Unfollow company');
          throw error;
        }
      },

      loadCompanyInsights: async () => {
        try {
          // Calculate insights from followed companies
          const followedCompanies = get().followedCompanies;
          const insights = {
            totalFollowed: followedCompanies.length,
            newJobsThisWeek: 0, // This would come from a real API
            topIndustries: [...new Set(followedCompanies.map(c => c.industry))].slice(0, 5),
            averageRating: followedCompanies.reduce((sum, c) => sum + (c.rating || 0), 0) / followedCompanies.length || 0,
          };
          
          set({
            companyInsights: insights,
          });
        } catch (error) {
          logError(error, 'Load company insights');
          // Don't set error as insights are not critical
        }
      },

      updateSearchParams: (params: Partial<CompanySearchParams>) => {
        const currentParams = get().searchParams;
        const newParams = { ...currentParams, ...params, page: 1 }; // Reset page on param change
        set({ searchParams: newParams });
      },

      setPage: (page: number) => {
        const currentParams = get().searchParams;
        set({
          searchParams: { ...currentParams, page },
        });
        // Trigger search with new page
        get().searchCompanies({ page });
      },

      clearSearch: () => {
        set({
          companies: [],
          searchParams: initialSearchParams,
          pagination: initialPagination,
          error: null,
        });
      },

      // Store actions
      setLoading: (loading: boolean) => set({ isLoading: loading }),
      setError: (error: string | null) => set({ error }),
      reset: () => set({
        companies: [],
        followedCompanies: [],
        companyInsights: initialInsights,
        searchParams: initialSearchParams,
        pagination: initialPagination,
        isLoading: false,
        error: null,
      }),
    }),
    {
      name: 'companies-store',
    }
  )
);