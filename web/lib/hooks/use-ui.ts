import { useUIStore } from '@/lib/stores/ui-store';

export function useUI() {
  const {
    sidebarOpen,
    mobileMenuOpen,
    theme,
    modals,
    loadingStates,
    toasts,
    setSidebarOpen,
    setMobileMenuOpen,
    setTheme,
    openModal,
    closeModal,
    closeAllModals,
    setLoading,
    addToast,
    removeToast,
    clearToasts,
  } = useUIStore();

  // Helper functions for common UI operations
  const toggleSidebar = () => setSidebarOpen(!sidebarOpen);
  const toggleMobileMenu = () => setMobileMenuOpen(!mobileMenuOpen);

  const isModalOpen = (modal: keyof typeof modals) => modals[modal];
  const isLoading = (key: string) => loadingStates[key] || false;

  // Enhanced toast function with better defaults
  const showToast = (
    type: 'success' | 'error' | 'warning' | 'info',
    title: string,
    message: string,
    duration?: number
  ) => {
    addToast({ type, title, message, duration });
  };

  // Specific toast helpers
  const showSuccess = (title: string, message: string, duration?: number) => 
    showToast('success', title, message, duration);
  
  const showError = (title: string, message: string, duration?: number) => 
    showToast('error', title, message, duration);
  
  const showWarning = (title: string, message: string, duration?: number) => 
    showToast('warning', title, message, duration);
  
  const showInfo = (title: string, message: string, duration?: number) => 
    showToast('info', title, message, duration);

  return {
    // State
    sidebarOpen,
    mobileMenuOpen,
    theme,
    modals,
    toasts,
    
    // Actions
    setSidebarOpen,
    setMobileMenuOpen,
    setTheme,
    toggleSidebar,
    toggleMobileMenu,
    
    // Modal management
    openModal,
    closeModal,
    closeAllModals,
    isModalOpen,
    
    // Loading management
    setLoading,
    isLoading,
    
    // Toast management
    showToast,
    showSuccess,
    showError,
    showWarning,
    showInfo,
    removeToast,
    clearToasts,
  };
}