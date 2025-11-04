import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { api } from '@/lib/api';
import { logError } from '@/lib/error-handler';
import { LoadingState, PaginationState, StoreActions } from './types';

interface PeerGroup {
  id: string;
  name: string;
  slug: string;
  description: string;
  member_count: number;
  activity_score: number;
  is_member: boolean;
  is_private: boolean;
  industry?: string;
  experience_level?: string;
  created_at: string;
}

interface GroupMessage {
  id: string;
  content: string;
  author: {
    id: string;
    name: string;
    avatar?: string;
  };
  created_at: string;
  group_id: string;
}

interface PeerGroupSearchParams {
  query?: string;
  industry?: string;
  experience_level?: string;
  page?: number;
  limit?: number;
}

interface PeerGroupsState extends LoadingState, StoreActions {
  // Data
  allGroups: PeerGroup[];
  joinedGroups: PeerGroup[];
  recommendations: PeerGroup[];
  currentGroup: PeerGroup | null;
  groupMessages: Record<string, GroupMessage[]>; // groupId -> messages
  
  // Search and pagination
  searchParams: PeerGroupSearchParams;
  pagination: PaginationState;
  
  // Actions
  searchGroups: (params?: Partial<PeerGroupSearchParams>) => Promise<void>;
  loadRecommendations: () => Promise<void>;
  loadJoinedGroups: () => Promise<void>;
  joinGroup: (groupSlug: string) => Promise<void>;
  leaveGroup: (groupSlug: string) => Promise<void>;
  loadGroupDetails: (groupSlug: string) => Promise<void>;
  loadGroupMessages: (groupSlug: string) => Promise<void>;
  sendMessage: (groupSlug: string, content: string) => Promise<void>;
  updateSearchParams: (params: Partial<PeerGroupSearchParams>) => void;
  setPage: (page: number) => void;
  clearSearch: () => void;
  setCurrentGroup: (group: PeerGroup | null) => void;
}

const initialSearchParams: PeerGroupSearchParams = {
  query: '',
  industry: '',
  experience_level: '',
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

export const usePeerGroupsStore = create<PeerGroupsState>()(
  devtools(
    (set, get) => ({
      // Initial state
      allGroups: [],
      joinedGroups: [],
      recommendations: [],
      currentGroup: null,
      groupMessages: {},
      searchParams: initialSearchParams,
      pagination: initialPagination,
      isLoading: false,
      error: null,

      // Actions
      searchGroups: async (params?: Partial<PeerGroupSearchParams>) => {
        try {
          set({ isLoading: true, error: null });

          const currentParams = get().searchParams;
          const searchParams = { ...currentParams, ...params };

          const response = await api.peerGroups.search(searchParams);
          const { results, count, next, previous } = response.data;

          const page = searchParams.page || 1;
          const limit = searchParams.limit || 20;

          set({
            allGroups: results,
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
          logError(error, 'Peer group search');
          set({
            isLoading: false,
            error: 'Failed to search peer groups',
          });
        }
      },

      loadRecommendations: async () => {
        try {
          const response = await api.peerGroups.discover({ limit: 10 });
          const recommendations = response.data.recommendations?.map((r: any) => r.group) || response.data;
          
          set({
            recommendations,
          });
        } catch (error) {
          logError(error, 'Load peer group recommendations');
          // Don't set error as recommendations are not critical
        }
      },

      loadJoinedGroups: async () => {
        try {
          const response = await api.peerGroups.myGroups();
          set({
            joinedGroups: response.data.results || response.data,
          });
        } catch (error) {
          logError(error, 'Load joined groups');
          // Don't set error as this is not critical
        }
      },

      joinGroup: async (groupSlug: string) => {
        try {
          await api.peerGroups.join(groupSlug);
          
          // Update the group in all relevant lists
          const updateGroupMembership = (groups: PeerGroup[]) =>
            groups.map(group =>
              group.slug === groupSlug
                ? { ...group, is_member: true, member_count: group.member_count + 1 }
                : group
            );

          const currentAllGroups = get().allGroups;
          const currentRecommendations = get().recommendations;
          const currentJoined = get().joinedGroups;
          
          // Find the group to add to joined list
          const groupToJoin = currentAllGroups.find(g => g.slug === groupSlug) ||
                             currentRecommendations.find(g => g.slug === groupSlug);
          
          set({
            allGroups: updateGroupMembership(currentAllGroups),
            recommendations: updateGroupMembership(currentRecommendations),
            joinedGroups: groupToJoin && !currentJoined.find(g => g.slug === groupSlug)
              ? [...currentJoined, { ...groupToJoin, is_member: true }]
              : updateGroupMembership(currentJoined),
          });

          // Update current group if it's the one being joined
          const currentGroup = get().currentGroup;
          if (currentGroup && currentGroup.slug === groupSlug) {
            set({
              currentGroup: {
                ...currentGroup,
                is_member: true,
                member_count: currentGroup.member_count + 1,
              },
            });
          }
        } catch (error) {
          logError(error, 'Join group');
          throw error;
        }
      },

      leaveGroup: async (groupSlug: string) => {
        try {
          await api.peerGroups.leave(groupSlug);
          
          // Update the group in all relevant lists
          const updateGroupMembership = (groups: PeerGroup[]) =>
            groups.map(group =>
              group.slug === groupSlug
                ? { ...group, is_member: false, member_count: Math.max(0, group.member_count - 1) }
                : group
            );

          set({
            allGroups: updateGroupMembership(get().allGroups),
            recommendations: updateGroupMembership(get().recommendations),
            joinedGroups: get().joinedGroups.filter(g => g.slug !== groupSlug),
          });

          // Update current group if it's the one being left
          const currentGroup = get().currentGroup;
          if (currentGroup && currentGroup.slug === groupSlug) {
            set({
              currentGroup: {
                ...currentGroup,
                is_member: false,
                member_count: Math.max(0, currentGroup.member_count - 1),
              },
            });
          }
        } catch (error) {
          logError(error, 'Leave group');
          throw error;
        }
      },

      loadGroupDetails: async (groupSlug: string) => {
        try {
          const response = await api.peerGroups.get(groupSlug);
          set({
            currentGroup: response.data,
          });
        } catch (error) {
          logError(error, 'Load group details');
          set({
            error: 'Failed to load group details',
          });
        }
      },

      loadGroupMessages: async (groupSlug: string) => {
        try {
          // TODO: Implement get messages API endpoint
          // For now, return empty array
          set({
            groupMessages: {
              ...get().groupMessages,
              [groupSlug]: [],
            },
          });
        } catch (error) {
          logError(error, 'Load group messages');
          // Don't set error as messages are not critical for group viewing
        }
      },

      sendMessage: async (groupSlug: string, content: string) => {
        try {
          // TODO: Implement send message API endpoint
          // For now, just add to local messages
          const newMessage = {
            id: Date.now().toString(),
            content,
            author: {
              id: 'current-user',
              name: 'Current User',
              avatar: undefined,
            },
            created_at: new Date().toISOString(),
            group_id: groupSlug,
          };
          
          const currentMessages = get().groupMessages[groupSlug] || [];
          set({
            groupMessages: {
              ...get().groupMessages,
              [groupSlug]: [...currentMessages, newMessage],
            },
          });
        } catch (error) {
          logError(error, 'Send message');
          throw error;
        }
      },

      updateSearchParams: (params: Partial<PeerGroupSearchParams>) => {
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
        get().searchGroups({ page });
      },

      clearSearch: () => {
        set({
          allGroups: [],
          searchParams: initialSearchParams,
          pagination: initialPagination,
          error: null,
        });
      },

      setCurrentGroup: (group: PeerGroup | null) => {
        set({ currentGroup: group });
      },

      // Store actions
      setLoading: (loading: boolean) => set({ isLoading: loading }),
      setError: (error: string | null) => set({ error }),
      reset: () => set({
        allGroups: [],
        joinedGroups: [],
        recommendations: [],
        currentGroup: null,
        groupMessages: {},
        searchParams: initialSearchParams,
        pagination: initialPagination,
        isLoading: false,
        error: null,
      }),
    }),
    {
      name: 'peer-groups-store',
    }
  )
);