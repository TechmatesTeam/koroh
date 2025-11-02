/**
 * Comprehensive error handling system for the Koroh platform
 * Provides user-friendly error messages and proper error categorization
 */

export interface ApiError {
  message: string;
  code?: string;
  status?: number;
  details?: any;
}

export interface ErrorResponse {
  error: string;
  message: string;
  code?: string;
  details?: any;
}

export class KorohError extends Error {
  public code?: string;
  public status?: number;
  public details?: any;

  constructor(message: string, code?: string, status?: number, details?: any) {
    super(message);
    this.name = 'KorohError';
    this.code = code;
    this.status = status;
    this.details = details;
  }
}

// Error categories
export const ERROR_CODES = {
  // Authentication errors
  INVALID_CREDENTIALS: 'INVALID_CREDENTIALS',
  ACCOUNT_NOT_VERIFIED: 'ACCOUNT_NOT_VERIFIED',
  TOKEN_EXPIRED: 'TOKEN_EXPIRED',
  UNAUTHORIZED: 'UNAUTHORIZED',
  
  // Validation errors
  VALIDATION_ERROR: 'VALIDATION_ERROR',
  EMAIL_ALREADY_EXISTS: 'EMAIL_ALREADY_EXISTS',
  WEAK_PASSWORD: 'WEAK_PASSWORD',
  
  // Network errors
  NETWORK_ERROR: 'NETWORK_ERROR',
  SERVER_ERROR: 'SERVER_ERROR',
  TIMEOUT_ERROR: 'TIMEOUT_ERROR',
  
  // Feature errors
  FILE_UPLOAD_ERROR: 'FILE_UPLOAD_ERROR',
  AI_SERVICE_ERROR: 'AI_SERVICE_ERROR',
  RATE_LIMIT_EXCEEDED: 'RATE_LIMIT_EXCEEDED',
  
  // Generic errors
  UNKNOWN_ERROR: 'UNKNOWN_ERROR',
} as const;

// User-friendly error messages
export const ERROR_MESSAGES = {
  [ERROR_CODES.INVALID_CREDENTIALS]: 'Invalid email or password. Please check your credentials and try again.',
  [ERROR_CODES.ACCOUNT_NOT_VERIFIED]: 'Your account is not verified. Please check your email for verification instructions.',
  [ERROR_CODES.TOKEN_EXPIRED]: 'Your session has expired. Please log in again.',
  [ERROR_CODES.UNAUTHORIZED]: 'You are not authorized to access this resource. Please log in.',
  
  [ERROR_CODES.VALIDATION_ERROR]: 'Please check your input and try again.',
  [ERROR_CODES.EMAIL_ALREADY_EXISTS]: 'An account with this email already exists. Try logging in instead.',
  [ERROR_CODES.WEAK_PASSWORD]: 'Password must be at least 8 characters with uppercase, lowercase, and numbers.',
  
  [ERROR_CODES.NETWORK_ERROR]: 'Network connection error. Please check your internet connection.',
  [ERROR_CODES.SERVER_ERROR]: 'Server error occurred. Please try again later.',
  [ERROR_CODES.TIMEOUT_ERROR]: 'Request timed out. Please try again.',
  
  [ERROR_CODES.FILE_UPLOAD_ERROR]: 'File upload failed. Please check file size and format.',
  [ERROR_CODES.AI_SERVICE_ERROR]: 'AI service is temporarily unavailable. Please try again later.',
  [ERROR_CODES.RATE_LIMIT_EXCEEDED]: 'Too many requests. Please wait a moment before trying again.',
  
  [ERROR_CODES.UNKNOWN_ERROR]: 'An unexpected error occurred. Please try again.',
} as const;

/**
 * Parse API error response and return standardized error
 */
export function parseApiError(error: any): KorohError {
  // Handle axios errors
  if (error.response) {
    const { status, data } = error.response;
    
    // Handle specific HTTP status codes
    switch (status) {
      case 400:
        if (data?.email && Array.isArray(data.email) && data.email.includes('user with this email already exists.')) {
          return new KorohError(
            ERROR_MESSAGES[ERROR_CODES.EMAIL_ALREADY_EXISTS],
            ERROR_CODES.EMAIL_ALREADY_EXISTS,
            status,
            data
          );
        }
        if (data?.password) {
          return new KorohError(
            ERROR_MESSAGES[ERROR_CODES.WEAK_PASSWORD],
            ERROR_CODES.WEAK_PASSWORD,
            status,
            data
          );
        }
        return new KorohError(
          data?.message || data?.detail || ERROR_MESSAGES[ERROR_CODES.VALIDATION_ERROR],
          ERROR_CODES.VALIDATION_ERROR,
          status,
          data
        );
        
      case 401:
        if (data?.detail?.includes('credentials') || data?.message?.includes('credentials')) {
          return new KorohError(
            ERROR_MESSAGES[ERROR_CODES.INVALID_CREDENTIALS],
            ERROR_CODES.INVALID_CREDENTIALS,
            status,
            data
          );
        }
        return new KorohError(
          ERROR_MESSAGES[ERROR_CODES.UNAUTHORIZED],
          ERROR_CODES.UNAUTHORIZED,
          status,
          data
        );
        
      case 403:
        return new KorohError(
          data?.message || 'Access forbidden. You do not have permission to perform this action.',
          ERROR_CODES.UNAUTHORIZED,
          status,
          data
        );
        
      case 404:
        return new KorohError(
          data?.message || 'The requested resource was not found.',
          'NOT_FOUND',
          status,
          data
        );
        
      case 429:
        return new KorohError(
          ERROR_MESSAGES[ERROR_CODES.RATE_LIMIT_EXCEEDED],
          ERROR_CODES.RATE_LIMIT_EXCEEDED,
          status,
          data
        );
        
      case 500:
      case 502:
      case 503:
      case 504:
        return new KorohError(
          ERROR_MESSAGES[ERROR_CODES.SERVER_ERROR],
          ERROR_CODES.SERVER_ERROR,
          status,
          data
        );
        
      default:
        return new KorohError(
          data?.message || data?.detail || ERROR_MESSAGES[ERROR_CODES.UNKNOWN_ERROR],
          ERROR_CODES.UNKNOWN_ERROR,
          status,
          data
        );
    }
  }
  
  // Handle network errors
  if (error.request) {
    if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
      return new KorohError(
        ERROR_MESSAGES[ERROR_CODES.TIMEOUT_ERROR],
        ERROR_CODES.TIMEOUT_ERROR,
        0
      );
    }
    
    return new KorohError(
      ERROR_MESSAGES[ERROR_CODES.NETWORK_ERROR],
      ERROR_CODES.NETWORK_ERROR,
      0
    );
  }
  
  // Handle other errors
  if (error instanceof KorohError) {
    return error;
  }
  
  return new KorohError(
    error.message || ERROR_MESSAGES[ERROR_CODES.UNKNOWN_ERROR],
    ERROR_CODES.UNKNOWN_ERROR
  );
}

/**
 * Get user-friendly error message
 */
export function getErrorMessage(error: any): string {
  const parsedError = parseApiError(error);
  return parsedError.message;
}

/**
 * Check if error is authentication related
 */
export function isAuthError(error: any): boolean {
  const parsedError = parseApiError(error);
  return [
    ERROR_CODES.INVALID_CREDENTIALS,
    ERROR_CODES.TOKEN_EXPIRED,
    ERROR_CODES.UNAUTHORIZED,
    ERROR_CODES.ACCOUNT_NOT_VERIFIED,
  ].includes(parsedError.code as any);
}

/**
 * Check if error requires user action
 */
export function requiresUserAction(error: any): boolean {
  const parsedError = parseApiError(error);
  return [
    ERROR_CODES.INVALID_CREDENTIALS,
    ERROR_CODES.VALIDATION_ERROR,
    ERROR_CODES.EMAIL_ALREADY_EXISTS,
    ERROR_CODES.WEAK_PASSWORD,
    ERROR_CODES.ACCOUNT_NOT_VERIFIED,
  ].includes(parsedError.code as any);
}

/**
 * Log error for debugging (in development)
 */
export function logError(error: any, context?: string): void {
  if (process.env.NODE_ENV === 'development' || process.env.NEXT_PUBLIC_SHOW_ERROR_DETAILS === 'true') {
    console.group(`🚨 Error${context ? ` in ${context}` : ''}`);
    console.error('Original error:', error);
    console.error('Parsed error:', parseApiError(error));
    console.groupEnd();
  }
}