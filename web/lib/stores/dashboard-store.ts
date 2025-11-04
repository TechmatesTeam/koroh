import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { api } from '@/lib/api';
import { logError } from '@/lib/error-handler';
import { LoadingState, StoreActions } from './types';

interface JobRecommendation {
  id: string;
  title: string;
  company: {
    id: string;
    name: string;
    logo?: string;
    industry: string;
  };
  location: string;
  type: string;
  remote: boolean;
  salary_range?: string;
  match_score?: number;
  match_reasons?: string[];
  posted_date: string;
}

interface Company {
  id: string;
  name: string;
  logo?: string;
  industry: string;
  size: string;
  location: string;
  description: string;
  is_following: boolean;
  open_positions: number;
  rating?: number;
}

interface PeerGroup {
  id: string;
  name: string;
  slug: string;
  description: string;
  member_count: number;
  activity_score: number;
  is_member: boolean;
}

interface DashboardData {
  jobRecommendations: JobRecommendation[];
  companies: Company[];
  peerGroups: PeerGroup[];
  profileCompletion: number;
  stats: {
    profileViews: number;
    connections: number;
    groupsJoined: number;
    jobApplications: number;
  };
}

interface DashboardState extends LoadingState, StoreActions {
  data: DashboardData;
  lastUpdated: Date | null;
  
  // Actions
  fetchDashboardData: () => Promise<void>;
  updateJobRecommendations: (jobs: JobRecommendation[]) => void;
  updateCompanies: (companies: Company[]) => void;
  updatePeerGroups: (groups: PeerGroup[]) => void;
  followCompany: (companyId: string) => Promise<void>;
  joinPeerGroup: (groupSlug: string) => Promise<void>;
  applyToJob: (jobId: string) => Promise<void>;
  refreshData: () => Promise<void>;
}

const initialData: DashboardData = {
  jobRecommendations: [],
  companies: [],
  peerGroups: [],
  profileCompletion: 0,
  stats: {
    profileViews: 0,
    connections: 0,
    groupsJoined: 0,
    jobApplications: 0,
  },
};

export const useDashboardStore = create<DashboardState>()(
  devtools(
    (set, get) => ({
      // Initial state
      data: initialData,
      isLoading: false,
      error: null,
      lastUpdated: null,

      // Actions
      fetchDashboardData: async () => {
        try {
          set({ isLoading: true, error: null });

          const [jobsResponse, companiesResponse, peerGroupsResponse] = await Promise.all([
            api.jobs.getRecommendations(),
            api.companies.search({ page_size: 4 }),
            api.peerGroups.discover({ limit: 3 }),
          ]);

          const newData: DashboardData = {
            jobRecommendations: jobsResponse.data.recommendations || [],
            companies: companiesResponse.data.results || [],
            peerGroups: peerGroupsResponse.data.recommendations?.map((r: any) => r.group) || [],
            profileCompletion: 75, // This would come from profile analysis
            stats: {
              profileViews: 127,
              connections: 45,
              groupsJoined: 3,
              jobApplications: 12,
            },
          };

          set({
            data: newData,
            isLoading: false,
            lastUpdated: new Date(),
          });
        } catch (error) {
          logError(error, 'Dashboard data fetch');
          set({
            isLoading: false,
            error: 'Failed to load dashboard data',
          });
        }
      },

      updateJobRecommendations: (jobs: JobRecommendation[]) => {
        const currentData = get().data;
        set({
          data: {
            ...currentData,
            jobRecommendations: jobs,
          },
          lastUpdated: new Date(),
        });
      },

      updateCompanies: (companies: Company[]) => {
        const currentData = get().data;
        set({
          data: {
            ...currentData,
            companies,
          },
          lastUpdated: new Date(),
        });
      },

      updatePeerGroups: (groups: PeerGroup[]) => {
        const currentData = get().data;
        set({
          data: {
            ...currentData,
            peerGroups: groups,
          },
          lastUpdated: new Date(),
        });
      },

      followCompany: async (companyId: string) => {
        try {
          await api.companies.follow(companyId);
          
          const currentData = get().data;
          const updatedCompanies = currentData.companies.map(company =>
            company.id === companyId
              ? { ...company, is_following: true }
              : company
          );

          set({
            data: {
              ...currentData,
              companies: updatedCompanies,
            },
            lastUpdated: new Date(),
          });
        } catch (error) {
          logError(error, 'Company follow');
          throw error;
        }
      },

      joinPeerGroup: async (groupSlug: string) => {
        try {
          await api.peerGroups.join(groupSlug);
          
          const currentData = get().data;
          const updatedGroups = currentData.peerGroups.map(group =>
            group.slug === groupSlug
              ? { ...group, is_member: true }
              : group
          );

          set({
            data: {
              ...currentData,
              peerGroups: updatedGroups,
            },
            lastUpdated: new Date(),
          });
        } catch (error) {
          logError(error, 'Group join');
          throw error;
        }
      },

      applyToJob: async (jobId: string) => {
        try {
          await api.jobs.apply(jobId);
          
          // Update stats
          const currentData = get().data;
          set({
            data: {
              ...currentData,
              stats: {
                ...currentData.stats,
                jobApplications: currentData.stats.jobApplications + 1,
              },
            },
            lastUpdated: new Date(),
          });
        } catch (error) {
          logError(error, 'Job application');
          throw error;
        }
      },

      refreshData: async () => {
        await get().fetchDashboardData();
      },

      // Store actions
      setLoading: (loading: boolean) => set({ isLoading: loading }),
      setError: (error: string | null) => set({ error }),
      reset: () => set({ data: initialData, isLoading: false, error: null, lastUpdated: null }),
    }),
    {
      name: 'dashboard-store',
    }
  )
);