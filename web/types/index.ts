// User and Authentication Types
export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  profile_picture?: string;
  is_verified: boolean;
  role?: string;
  created_at: string;
  updated_at: string;
}

export interface AuthTokens {
  access: string;
  refresh: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
  password_confirm: string;
  first_name: string;
  last_name: string;
}

// Profile Types
export interface Profile {
  id: string;
  user: User;
  headline: string;
  summary: string;
  location: string;
  industry: string;
  experience_level: string;
  skills: string[];
  cv_file?: string;
  portfolio_url?: string;
  preferences: Record<string, any>;
}

// Job Types
export interface Job {
  id: string;
  title: string;
  company: Company;
  description: string;
  requirements: string[];
  location: string;
  salary_range: string;
  job_type: string;
  posted_date: string;
  is_active: boolean;
}

export interface JobSearchParams {
  query?: string;
  location?: string;
  job_type?: string;
  salary_min?: number;
  salary_max?: number;
  remote?: boolean;
  page?: number;
  limit?: number;
}

// Company Types
export interface Company {
  id: string;
  name: string;
  description: string;
  industry: string;
  size: string;
  location: string;
  website: string;
  logo?: string;
  followers_count: number;
  is_following: boolean;
  rating?: number;
}

// Re-export peer group types
export * from './peer-groups';

// Portfolio Types
export interface Portfolio {
  id: string;
  user: string;
  title: string;
  template: string;
  content: Record<string, any>;
  url: string;
  is_public: boolean;
  created_at: string;
  updated_at: string;
}

// AI Chat Types
export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  metadata?: Record<string, any>;
  status?: 'pending' | 'processing' | 'completed' | 'failed';
  created_at: string;
}

export interface ChatSession {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  is_active: boolean;
  messages: ChatMessage[];
  message_count: number;
}

export interface ChatSessionListItem {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  is_active: boolean;
  message_count: number;
  last_message?: {
    content: string;
    role: string;
    created_at: string;
  };
}

export interface CVAnalysis {
  id: string;
  cv_file: string;
  extracted_data: {
    personal_info: Record<string, any>;
    skills: string[];
    experience: Record<string, any>[];
    education: Record<string, any>[];
  };
  analysis_status: 'pending' | 'completed' | 'failed';
  created_at: string;
}

// API Response Types
export interface ApiResponse<T> {
  data: T;
  message?: string;
  status: number;
}

export interface PaginatedResponse<T> {
  results: T[];
  count: number;
  next?: string;
  previous?: string;
}

export interface ApiError {
  error: {
    code: string;
    message: string;
    details?: Record<string, string[]>;
    timestamp: string;
  };
}

// Form Types
export interface FormField {
  name: string;
  label: string;
  type: 'text' | 'email' | 'password' | 'textarea' | 'select' | 'file';
  placeholder?: string;
  required?: boolean;
  options?: { value: string; label: string }[];
}

// Navigation Types
export interface NavItem {
  name: string;
  href: string;
  icon?: string;
  current?: boolean;
}

// Notification Types
export interface Notification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title?: string;
  message: string;
  timestamp: string;
  read: boolean;
}