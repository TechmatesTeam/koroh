import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';
import Cookies from 'js-cookie';
import { parseApiError, logError } from './error-handler';
import { mockApi } from './mock-api';

// API Configuration
// In Docker, use the Next.js proxy. Otherwise use explicit URL.
const getApiBaseUrl = () => {
  if (process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL;
  }
  // Check if we're in Docker environment - use the Next.js rewrite proxy
  if (process.env.DOCKER_CONTAINER === 'true') {
    return '/api/v1';
  }
  // Default to localhost for local development
  return 'http://localhost:8000/api/v1';
};

const API_BASE_URL = getApiBaseUrl();
const USE_MOCK_API = process.env.NEXT_PUBLIC_USE_MOCK_API === 'true';

// Create axios instance
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = Cookies.get('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle token refresh and errors (only for real API)
if (!USE_MOCK_API) {
  apiClient.interceptors.response.use(
    (response: AxiosResponse) => {
      return response;
    },
    async (error) => {
      const originalRequest = error.config;

      // Log error for debugging
      logError(error, `API ${originalRequest?.method?.toUpperCase()} ${originalRequest?.url}`);

      // Handle 401 errors with token refresh
      if (error.response?.status === 401 && !originalRequest._retry) {
        originalRequest._retry = true;

        try {
          const refreshToken = Cookies.get('refresh_token');
          if (refreshToken) {
            const response = await axios.post(`${API_BASE_URL}/auth/refresh/`, {
              refresh: refreshToken,
            });

            const { access } = response.data;
            Cookies.set('access_token', access, {
              secure: process.env.NODE_ENV === 'production',
              sameSite: 'lax'
            });

            // Retry original request with new token
            originalRequest.headers.Authorization = `Bearer ${access}`;
            return apiClient(originalRequest);
          }
        } catch (refreshError) {
          // Refresh failed, clear tokens and redirect to login
          Cookies.remove('access_token');
          Cookies.remove('refresh_token');
          
          // Store current path for redirect after login
          if (typeof window !== 'undefined') {
            sessionStorage.setItem('redirectAfterLogin', window.location.pathname);
            window.location.href = '/auth/login';
          }
        }
      }

      // Return parsed error for consistent error handling
      return Promise.reject(parseApiError(error));
    }
  );
}

// API methods
export const api = {
  // Auth endpoints
  auth: {
    login: (credentials: { email: string; password: string }) =>
      USE_MOCK_API ? mockApi.auth.login(credentials) : apiClient.post('/auth/login/', credentials),
    register: (userData: { email: string; password: string; password_confirm: string; first_name: string; last_name: string }) =>
      USE_MOCK_API ? mockApi.auth.register(userData) : apiClient.post('/auth/register/', userData),
    logout: () =>
      USE_MOCK_API ? mockApi.auth.logout() : apiClient.post('/auth/logout/'),
    refresh: (refreshToken: string) =>
      USE_MOCK_API ? mockApi.auth.refresh(refreshToken) : apiClient.post('/auth/refresh/', { refresh: refreshToken }),
    requestPasswordReset: (email: string) =>
      USE_MOCK_API ? mockApi.auth.requestPasswordReset(email) : apiClient.post('/auth/password-reset/', { email }),
    resetPassword: (token: string, password: string) =>
      USE_MOCK_API ? mockApi.auth.resetPassword(token, password) : apiClient.post('/auth/password-reset/confirm/', { token, password }),
  },

  // Profile endpoints
  profiles: {
    getMe: () => USE_MOCK_API ? mockApi.profiles.getMe() : apiClient.get('/profiles/me/'),
    updateMe: (data: any) => USE_MOCK_API ? mockApi.profiles.updateMe(data) : apiClient.patch('/profiles/me/', data),
    uploadCV: (file: FormData) =>
      USE_MOCK_API 
        ? Promise.reject(new Error('CV upload not available in mock mode'))
        : apiClient.post('/profiles/upload-cv/', file, {
            headers: { 'Content-Type': 'multipart/form-data' },
          }),
    generatePortfolio: (data?: { template?: string; portfolioName?: string }) => 
      USE_MOCK_API ? mockApi.profiles.generatePortfolio(data) : apiClient.post('/profiles/generate-portfolio/', data),
    getPortfolios: () => 
      USE_MOCK_API ? mockApi.profiles.getPortfolios() : apiClient.get('/profiles/portfolios/'),
    updatePortfolio: (portfolioId: string, data: any) => 
      USE_MOCK_API 
        ? mockApi.profiles.updatePortfolio(portfolioId, data)
        : apiClient.patch(`/profiles/portfolios/${portfolioId}/`, data),
  },

  // Jobs endpoints
  jobs: {
    search: (params: any) => 
      USE_MOCK_API ? mockApi.jobs.search(params) : apiClient.get('/jobs/search/', { params }),
    getRecommendations: () => 
      USE_MOCK_API ? mockApi.jobs.getRecommendations() : apiClient.get('/jobs/recommendations/'),
    apply: (jobId: string) => 
      USE_MOCK_API ? mockApi.jobs.apply(jobId) : apiClient.post(`/jobs/${jobId}/apply/`),
  },

  // Companies endpoints
  companies: {
    search: (params: any) => 
      USE_MOCK_API ? mockApi.companies.search(params) : apiClient.get('/companies/search/', { params }),
    follow: (companyId: string) => 
      USE_MOCK_API ? mockApi.companies.follow(companyId) : apiClient.post(`/companies/${companyId}/follow/`),
    unfollow: (companyId: string) => 
      USE_MOCK_API ? mockApi.companies.unfollow(companyId) : apiClient.delete(`/companies/${companyId}/follow/`),
    getInsights: (companyId: string) => 
      USE_MOCK_API ? mockApi.companies.getInsights(companyId) : apiClient.get(`/companies/${companyId}/insights/`),
  },

  // Peer Groups endpoints
  peerGroups: {
    // Group discovery and search
    discover: (params?: any) => 
      USE_MOCK_API ? mockApi.peerGroups.discover(params) : apiClient.get('/peer_groups/groups/discover/', { params }),
    search: (params: any) => 
      USE_MOCK_API ? mockApi.peerGroups.search(params) : apiClient.get('/peer_groups/groups/search/', { params }),
    trending: (params?: any) => 
      USE_MOCK_API ? mockApi.peerGroups.trending(params) : apiClient.get('/peer_groups/groups/trending/', { params }),
    
    // Group CRUD
    list: (params?: any) => 
      USE_MOCK_API ? mockApi.peerGroups.list(params) : apiClient.get('/peer_groups/groups/', { params }),
    get: (slug: string) => 
      USE_MOCK_API ? mockApi.peerGroups.get(slug) : apiClient.get(`/peer_groups/groups/${slug}/`),
    create: (data: any) => 
      USE_MOCK_API ? mockApi.peerGroups.create(data) : apiClient.post('/peer_groups/groups/', data),
    update: (slug: string, data: any) => 
      USE_MOCK_API ? mockApi.peerGroups.update(slug, data) : apiClient.patch(`/peer_groups/groups/${slug}/`, data),
    delete: (slug: string) => 
      USE_MOCK_API ? mockApi.peerGroups.delete(slug) : apiClient.delete(`/peer_groups/groups/${slug}/`),
    
    // Group membership
    myGroups: () => 
      USE_MOCK_API ? mockApi.peerGroups.myGroups() : apiClient.get('/peer_groups/groups/my_groups/'),
    join: (slug: string, data?: any) => 
      USE_MOCK_API ? mockApi.peerGroups.join(slug, data) : apiClient.post(`/peer_groups/groups/${slug}/join/`, data),
    leave: (slug: string) => 
      USE_MOCK_API ? mockApi.peerGroups.leave(slug) : apiClient.post(`/peer_groups/groups/${slug}/leave/`),
    
    // Group members
    getMembers: (slug: string) => 
      USE_MOCK_API ? mockApi.peerGroups.getMembers(slug) : apiClient.get(`/peer_groups/groups/${slug}/members/`),
    getPendingMembers: (slug: string) => 
      USE_MOCK_API ? mockApi.peerGroups.getPendingMembers(slug) : apiClient.get(`/peer_groups/groups/${slug}/pending_members/`),
    inviteMember: (slug: string, data: any) => 
      USE_MOCK_API ? mockApi.peerGroups.inviteMember(slug, data) : apiClient.post(`/peer_groups/groups/${slug}/invite_member/`, data),
    manageMember: (slug: string, data: any) => 
      USE_MOCK_API ? mockApi.peerGroups.manageMember(slug, data) : apiClient.post(`/peer_groups/groups/${slug}/manage_member/`, data),
    
    // Group activity
    getActivityFeed: (slug: string) => 
      USE_MOCK_API ? mockApi.peerGroups.getActivityFeed(slug) : apiClient.get(`/peer_groups/groups/${slug}/activity_feed/`),
    getMyActivityFeed: () => 
      USE_MOCK_API ? mockApi.peerGroups.getMyActivityFeed() : apiClient.get('/peer_groups/groups/my_activity_feed/'),
    
    // Similar groups
    getSimilar: (slug: string, params?: any) => 
      USE_MOCK_API ? mockApi.peerGroups.getSimilar(slug, params) : apiClient.get(`/peer_groups/groups/${slug}/similar/`, { params }),
    
    // Group posts
    getPosts: (slug: string, params?: any) => 
      USE_MOCK_API ? mockApi.peerGroups.getPosts(slug, params) : apiClient.get(`/peer_groups/groups/${slug}/posts/`, { params }),
    createPost: (slug: string, data: any) => 
      USE_MOCK_API ? mockApi.peerGroups.createPost(slug, data) : apiClient.post(`/peer_groups/groups/${slug}/posts/`, data),
    updatePost: (slug: string, postId: string, data: any) => 
      USE_MOCK_API ? mockApi.peerGroups.updatePost(slug, postId, data) : apiClient.patch(`/peer_groups/groups/${slug}/posts/${postId}/`, data),
    deletePost: (slug: string, postId: string) => 
      USE_MOCK_API ? mockApi.peerGroups.deletePost(slug, postId) : apiClient.delete(`/peer_groups/groups/${slug}/posts/${postId}/`),
    likePost: (slug: string, postId: string, action: 'like' | 'unlike') => 
      USE_MOCK_API ? mockApi.peerGroups.likePost(slug, postId, action) : apiClient.post(`/peer_groups/groups/${slug}/posts/${postId}/like/`, { action }),
    
    // Post comments
    getComments: (slug: string, postId: string, params?: any) => 
      USE_MOCK_API ? mockApi.peerGroups.getComments(slug, postId, params) : apiClient.get(`/peer_groups/groups/${slug}/posts/${postId}/comments/`, { params }),
    createComment: (slug: string, postId: string, data: any) => 
      USE_MOCK_API ? mockApi.peerGroups.createComment(slug, postId, data) : apiClient.post(`/peer_groups/groups/${slug}/posts/${postId}/comments/`, data),
    updateComment: (slug: string, postId: string, commentId: string, data: any) => 
      USE_MOCK_API ? mockApi.peerGroups.updateComment(slug, postId, commentId, data) : apiClient.patch(`/peer_groups/groups/${slug}/posts/${postId}/comments/${commentId}/`, data),
    deleteComment: (slug: string, postId: string, commentId: string) => 
      USE_MOCK_API ? mockApi.peerGroups.deleteComment(slug, postId, commentId) : apiClient.delete(`/peer_groups/groups/${slug}/posts/${postId}/comments/${commentId}/`),
    likeComment: (slug: string, postId: string, commentId: string, action: 'like' | 'unlike') => 
      USE_MOCK_API ? mockApi.peerGroups.likeComment(slug, postId, commentId, action) : apiClient.post(`/peer_groups/groups/${slug}/posts/${postId}/comments/${commentId}/like/`, { action }),
  },

  // AI Chat endpoints
  ai: {
    // Session management
    getSessions: () => 
      USE_MOCK_API ? Promise.resolve({ data: { sessions: [], count: 0 } }) : apiClient.get('/ai/sessions/'),
    createSession: () => 
      USE_MOCK_API ? Promise.resolve({ data: { id: 'mock-session', title: '', messages: [] } }) : apiClient.post('/ai/sessions/'),
    getSession: (sessionId: string) => 
      USE_MOCK_API ? Promise.resolve({ data: { id: sessionId, title: '', messages: [] } }) : apiClient.get(`/ai/sessions/${sessionId}/`),
    updateSession: (sessionId: string, data: any) => 
      USE_MOCK_API ? Promise.resolve({ data: { id: sessionId, ...data } }) : apiClient.patch(`/ai/sessions/${sessionId}/`, data),
    deleteSession: (sessionId: string) => 
      USE_MOCK_API ? Promise.resolve({ data: { message: 'Session deleted' } }) : apiClient.delete(`/ai/sessions/${sessionId}/`),
    
    // Message sending
    sendMessage: (data: { message: string; session_id?: string; context?: any }) =>
      USE_MOCK_API ? Promise.resolve({ 
        data: { 
          session_id: 'mock-session',
          user_message: { id: '1', role: 'user', content: data.message, created_at: new Date().toISOString() },
          ai_response: { id: '2', role: 'assistant', content: 'This is a mock AI response.', created_at: new Date().toISOString() }
        }
      }) : apiClient.post('/ai/send/', data),
    quickChat: (message: string) =>
      USE_MOCK_API ? Promise.resolve({ 
        data: { 
          message,
          response: 'This is a mock AI response.',
          session_id: 'mock-session'
        }
      }) : apiClient.post('/ai/quick/', { message }),
    
    // Anonymous chat (no auth required)
    anonymousChat: (message: string, sessionId?: string) => {
      if (USE_MOCK_API) {
        return Promise.resolve({ 
          data: { 
            message,
            response: 'This is a mock AI response for anonymous users. You have 4 messages remaining.',
            session_id: 'mock-anonymous-session',
            is_authenticated: false,
            messages_remaining: 4,
            max_messages: 5,
            registration_prompt: false
          }
        });
      }
      
      const axiosInstance = axios.create({
        baseURL: API_BASE_URL,
        timeout: 10000,
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      return axiosInstance.post('/ai/anonymous/', { message, session_id: sessionId });
    },
    
    // Platform integration
    analyzeCVChat: (sessionId?: string) =>
      USE_MOCK_API ? Promise.resolve({ 
        data: { 
          session_id: 'mock-session',
          analysis_result: { success: true, message: 'Mock CV analysis complete' },
          ai_response: { id: '3', role: 'assistant', content: 'I\'ve analyzed your CV!', created_at: new Date().toISOString() }
        }
      }) : apiClient.post('/ai/analyze-cv/', { session_id: sessionId }),
    generatePortfolioChat: (sessionId?: string) =>
      USE_MOCK_API ? Promise.resolve({ 
        data: { 
          session_id: 'mock-session',
          generation_result: { success: true, message: 'Mock portfolio generation ready' },
          ai_response: { id: '4', role: 'assistant', content: 'I can help you generate a portfolio!', created_at: new Date().toISOString() }
        }
      }) : apiClient.post('/ai/generate-portfolio/', { session_id: sessionId }),
    getJobRecommendationsChat: (sessionId?: string) =>
      USE_MOCK_API ? Promise.resolve({ 
        data: { 
          session_id: 'mock-session',
          recommendations_result: { success: true, message: 'Mock job recommendations ready' },
          ai_response: { id: '5', role: 'assistant', content: 'Here are some job recommendations for you!', created_at: new Date().toISOString() }
        }
      }) : apiClient.post('/ai/job-recommendations/', { session_id: sessionId }),
  },
};

export default apiClient;