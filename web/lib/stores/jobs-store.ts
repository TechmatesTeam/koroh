import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { api } from '@/lib/api';
import { logError } from '@/lib/error-handler';
import { LoadingState, PaginationState, SearchState, StoreActions } from './types';
import { Job, JobSearchParams } from '@/types';

interface JobsState extends LoadingState, StoreActions {
  // Data
  jobs: Job[];
  recommendations: Job[];
  savedJobs: Job[];
  appliedJobs: string[]; // Job IDs
  
  // Search and pagination
  searchParams: JobSearchParams;
  pagination: PaginationState;
  
  // Actions
  searchJobs: (params?: Partial<JobSearchParams>) => Promise<void>;
  loadRecommendations: () => Promise<void>;
  applyToJob: (jobId: string) => Promise<void>;
  saveJob: (jobId: string) => Promise<void>;
  unsaveJob: (jobId: string) => Promise<void>;
  loadSavedJobs: () => Promise<void>;
  updateSearchParams: (params: Partial<JobSearchParams>) => void;
  setPage: (page: number) => void;
  clearSearch: () => void;
}

const initialSearchParams: JobSearchParams = {
  query: '',
  location: '',
  job_type: '',
  salary_min: undefined,
  salary_max: undefined,
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

export const useJobsStore = create<JobsState>()(
  devtools(
    (set, get) => ({
      // Initial state
      jobs: [],
      recommendations: [],
      savedJobs: [],
      appliedJobs: [],
      searchParams: initialSearchParams,
      pagination: initialPagination,
      isLoading: false,
      error: null,

      // Actions
      searchJobs: async (params?: Partial<JobSearchParams>) => {
        try {
          set({ isLoading: true, error: null });

          const currentParams = get().searchParams;
          const searchParams = { ...currentParams, ...params };

          const response = await api.jobs.search(searchParams);
          const { results, count, next, previous } = response.data;

          const page = searchParams.page || 1;
          const limit = searchParams.limit || 20;

          set({
            jobs: results,
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
          logError(error, 'Job search');
          set({
            isLoading: false,
            error: 'Failed to search jobs',
          });
        }
      },

      loadRecommendations: async () => {
        try {
          const response = await api.jobs.getRecommendations();
          set({
            recommendations: response.data.recommendations || response.data,
          });
        } catch (error) {
          logError(error, 'Job recommendations');
          // Don't set error for recommendations as it's not critical
        }
      },

      applyToJob: async (jobId: string) => {
        try {
          await api.jobs.apply(jobId);
          
          const currentAppliedJobs = get().appliedJobs;
          set({
            appliedJobs: [...currentAppliedJobs, jobId],
          });
        } catch (error) {
          logError(error, 'Job application');
          throw error;
        }
      },

      saveJob: async (jobId: string) => {
        try {
          // TODO: Implement save job API endpoint
          // For now, just add to local saved jobs
          const currentJobs = get().jobs;
          const currentRecommendations = get().recommendations;
          const jobToSave = currentJobs.find(job => job.id === jobId) || 
                           currentRecommendations.find(job => job.id === jobId);
          
          if (jobToSave) {
            const currentSavedJobs = get().savedJobs;
            set({
              savedJobs: [...currentSavedJobs, jobToSave],
            });
          }
        } catch (error) {
          logError(error, 'Save job');
          throw error;
        }
      },

      unsaveJob: async (jobId: string) => {
        try {
          // TODO: Implement unsave job API endpoint
          // For now, just remove from local saved jobs
          const currentSavedJobs = get().savedJobs;
          set({
            savedJobs: currentSavedJobs.filter(job => job.id !== jobId),
          });
        } catch (error) {
          logError(error, 'Unsave job');
          throw error;
        }
      },

      loadSavedJobs: async () => {
        try {
          // TODO: Implement get saved jobs API endpoint
          // For now, return empty array
          set({
            savedJobs: [],
          });
        } catch (error) {
          logError(error, 'Load saved jobs');
          // Don't set error as saved jobs are not critical
        }
      },

      updateSearchParams: (params: Partial<JobSearchParams>) => {
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
        get().searchJobs({ page });
      },

      clearSearch: () => {
        set({
          jobs: [],
          searchParams: initialSearchParams,
          pagination: initialPagination,
          error: null,
        });
      },

      // Store actions
      setLoading: (loading: boolean) => set({ isLoading: loading }),
      setError: (error: string | null) => set({ error }),
      reset: () => set({
        jobs: [],
        recommendations: [],
        savedJobs: [],
        appliedJobs: [],
        searchParams: initialSearchParams,
        pagination: initialPagination,
        isLoading: false,
        error: null,
      }),
    }),
    {
      name: 'jobs-store',
    }
  )
);