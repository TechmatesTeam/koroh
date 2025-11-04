// Export all stores for easy importing
export { useDashboardStore } from './dashboard-store';
export { useJobsStore } from './jobs-store';
export { useCompaniesStore } from './companies-store';
export { usePeerGroupsStore } from './peer-groups-store';
export { useUIStore } from './ui-store';

// Export types
export type * from './types';

// Import stores for reset utility
import { useDashboardStore } from './dashboard-store';
import { useJobsStore } from './jobs-store';
import { useCompaniesStore } from './companies-store';
import { usePeerGroupsStore } from './peer-groups-store';

// Store reset utility for testing and logout
export const resetAllStores = () => {
  useDashboardStore.getState().reset();
  useJobsStore.getState().reset();
  useCompaniesStore.getState().reset();
  usePeerGroupsStore.getState().reset();
  // Note: UI store is not reset as it contains user preferences
};