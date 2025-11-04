// Shared types for state management
export interface LoadingState {
  isLoading: boolean;
  error: string | null;
}

export interface PaginationState {
  page: number;
  limit: number;
  totalCount: number;
  hasNextPage: boolean;
  hasPreviousPage: boolean;
}

export interface SearchState {
  query: string;
  filters: Record<string, any>;
  sortBy: string;
  sortOrder: 'asc' | 'desc';
}

export interface AsyncAction<T = any> {
  (...args: any[]): Promise<T>;
}

export interface StoreActions {
  reset: () => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}