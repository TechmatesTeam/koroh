import { create } from 'zustand';
import { devtools } from 'zustand/middleware';

interface UIState {
  // Global UI state
  sidebarOpen: boolean;
  mobileMenuOpen: boolean;
  theme: 'light' | 'dark' | 'system';
  
  // Modal states
  modals: {
    cvUpload: boolean;
    portfolioGenerate: boolean;
    jobApplication: boolean;
    groupJoin: boolean;
    companyFollow: boolean;
  };
  
  // Loading states for specific UI elements
  loadingStates: {
    [key: string]: boolean;
  };
  
  // Toast/notification queue (separate from notification context)
  toasts: Array<{
    id: string;
    type: 'success' | 'error' | 'warning' | 'info';
    title: string;
    message: string;
    duration?: number;
  }>;
  
  // Actions
  setSidebarOpen: (open: boolean) => void;
  setMobileMenuOpen: (open: boolean) => void;
  setTheme: (theme: 'light' | 'dark' | 'system') => void;
  openModal: (modal: keyof UIState['modals']) => void;
  closeModal: (modal: keyof UIState['modals']) => void;
  closeAllModals: () => void;
  setLoading: (key: string, loading: boolean) => void;
  addToast: (toast: Omit<UIState['toasts'][0], 'id'>) => void;
  removeToast: (id: string) => void;
  clearToasts: () => void;
}

const initialModals = {
  cvUpload: false,
  portfolioGenerate: false,
  jobApplication: false,
  groupJoin: false,
  companyFollow: false,
};

export const useUIStore = create<UIState>()(
  devtools(
    (set, get) => ({
      // Initial state
      sidebarOpen: true,
      mobileMenuOpen: false,
      theme: 'system',
      modals: initialModals,
      loadingStates: {},
      toasts: [],

      // Actions
      setSidebarOpen: (open: boolean) => {
        set({ sidebarOpen: open });
      },

      setMobileMenuOpen: (open: boolean) => {
        set({ mobileMenuOpen: open });
      },

      setTheme: (theme: 'light' | 'dark' | 'system') => {
        set({ theme });
        
        // Apply theme to document
        if (typeof window !== 'undefined') {
          const root = window.document.documentElement;
          
          if (theme === 'dark') {
            root.classList.add('dark');
          } else if (theme === 'light') {
            root.classList.remove('dark');
          } else {
            // System theme
            const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
            if (mediaQuery.matches) {
              root.classList.add('dark');
            } else {
              root.classList.remove('dark');
            }
          }
          
          // Store preference
          localStorage.setItem('koroh-theme', theme);
        }
      },

      openModal: (modal: keyof UIState['modals']) => {
        set({
          modals: {
            ...get().modals,
            [modal]: true,
          },
        });
      },

      closeModal: (modal: keyof UIState['modals']) => {
        set({
          modals: {
            ...get().modals,
            [modal]: false,
          },
        });
      },

      closeAllModals: () => {
        set({ modals: initialModals });
      },

      setLoading: (key: string, loading: boolean) => {
        const currentLoadingStates = get().loadingStates;
        
        if (loading) {
          set({
            loadingStates: {
              ...currentLoadingStates,
              [key]: true,
            },
          });
        } else {
          const { [key]: removed, ...rest } = currentLoadingStates;
          set({ loadingStates: rest });
        }
      },

      addToast: (toast: Omit<UIState['toasts'][0], 'id'>) => {
        const id = Math.random().toString(36).substr(2, 9);
        const newToast = { ...toast, id };
        
        set({
          toasts: [...get().toasts, newToast],
        });

        // Auto-remove toast after duration
        const duration = toast.duration || 5000;
        if (duration > 0) {
          setTimeout(() => {
            get().removeToast(id);
          }, duration);
        }
      },

      removeToast: (id: string) => {
        set({
          toasts: get().toasts.filter(toast => toast.id !== id),
        });
      },

      clearToasts: () => {
        set({ toasts: [] });
      },
    }),
    {
      name: 'ui-store',
    }
  )
);

// Initialize theme on load
if (typeof window !== 'undefined') {
  const savedTheme = localStorage.getItem('koroh-theme') as 'light' | 'dark' | 'system' | null;
  if (savedTheme) {
    useUIStore.getState().setTheme(savedTheme);
  }
}