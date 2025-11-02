/**
 * Prometheus metrics for Next.js frontend
 * 
 * This module provides client-side and server-side metrics collection
 * for the Koroh platform frontend application.
 */

import { register, Counter, Histogram, Gauge } from 'prom-client';

// Only initialize metrics on server side
const isServer = typeof window === 'undefined';

// Page view metrics
export const pageViews = isServer ? new Counter({
  name: 'koroh_web_page_views_total',
  help: 'Total number of page views',
  labelNames: ['page', 'user_type'],
  registers: [register]
}) : null;

// API request metrics
export const apiRequests = isServer ? new Counter({
  name: 'koroh_web_api_requests_total',
  help: 'Total number of API requests from frontend',
  labelNames: ['endpoint', 'method', 'status'],
  registers: [register]
}) : null;

export const apiRequestDuration = isServer ? new Histogram({
  name: 'koroh_web_api_request_duration_seconds',
  help: 'Duration of API requests from frontend',
  labelNames: ['endpoint', 'method'],
  buckets: [0.1, 0.5, 1.0, 2.5, 5.0, 10.0],
  registers: [register]
}) : null;

// User interaction metrics
export const userInteractions = isServer ? new Counter({
  name: 'koroh_web_user_interactions_total',
  help: 'Total number of user interactions',
  labelNames: ['interaction_type', 'component'],
  registers: [register]
}) : null;

// Feature usage metrics
export const featureUsage = isServer ? new Counter({
  name: 'koroh_web_feature_usage_total',
  help: 'Feature usage statistics',
  labelNames: ['feature_name', 'user_type'],
  registers: [register]
}) : null;

// Performance metrics
export const renderTime = isServer ? new Histogram({
  name: 'koroh_web_render_time_seconds',
  help: 'Component render time',
  labelNames: ['component_name'],
  buckets: [0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0],
  registers: [register]
}) : null;

// Error metrics
export const clientErrors = isServer ? new Counter({
  name: 'koroh_web_client_errors_total',
  help: 'Total number of client-side errors',
  labelNames: ['error_type', 'component'],
  registers: [register]
}) : null;

// Active sessions
export const activeSessions = isServer ? new Gauge({
  name: 'koroh_web_active_sessions',
  help: 'Number of active user sessions',
  registers: [register]
}) : null;

// Bundle size metrics
export const bundleSize = isServer ? new Gauge({
  name: 'koroh_web_bundle_size_bytes',
  help: 'Size of JavaScript bundles',
  labelNames: ['bundle_name'],
  registers: [register]
}) : null;

/**
 * Track page view
 */
export function trackPageView(page: string, userType: string = 'anonymous') {
  if (isServer && pageViews) {
    pageViews.labels(page, userType).inc();
  }
}

/**
 * Track API request
 */
export function trackApiRequest(
  endpoint: string, 
  method: string, 
  status: number, 
  duration?: number
) {
  if (isServer) {
    if (apiRequests) {
      apiRequests.labels(endpoint, method, status.toString()).inc();
    }
    
    if (duration && apiRequestDuration) {
      apiRequestDuration.labels(endpoint, method).observe(duration / 1000);
    }
  }
}

/**
 * Track user interaction
 */
export function trackUserInteraction(interactionType: string, component: string) {
  if (isServer && userInteractions) {
    userInteractions.labels(interactionType, component).inc();
  }
}

/**
 * Track feature usage
 */
export function trackFeatureUsage(featureName: string, userType: string = 'regular') {
  if (isServer && featureUsage) {
    featureUsage.labels(featureName, userType).inc();
  }
}

/**
 * Track component render time
 */
export function trackRenderTime(componentName: string, duration: number) {
  if (isServer && renderTime) {
    renderTime.labels(componentName).observe(duration / 1000);
  }
}

/**
 * Track client error
 */
export function trackClientError(errorType: string, component: string) {
  if (isServer && clientErrors) {
    clientErrors.labels(errorType, component).inc();
  }
}

/**
 * Update active sessions count
 */
export function updateActiveSessions(count: number) {
  if (isServer && activeSessions) {
    activeSessions.set(count);
  }
}

/**
 * Update bundle size
 */
export function updateBundleSize(bundleName: string, size: number) {
  if (isServer && bundleSize) {
    bundleSize.labels(bundleName).set(size);
  }
}

/**
 * Client-side metrics collection
 * These functions can be called from browser code
 */
export const clientMetrics = {
  /**
   * Track page view on client side
   */
  trackPageView: (page: string, userType: string = 'anonymous') => {
    if (typeof window !== 'undefined') {
      // Send to metrics endpoint
      fetch('/api/metrics/track', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          type: 'page_view',
          data: { page, userType }
        })
      }).catch(console.error);
    }
  },

  /**
   * Track user interaction on client side
   */
  trackInteraction: (interactionType: string, component: string) => {
    if (typeof window !== 'undefined') {
      fetch('/api/metrics/track', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          type: 'user_interaction',
          data: { interactionType, component }
        })
      }).catch(console.error);
    }
  },

  /**
   * Track feature usage on client side
   */
  trackFeature: (featureName: string, userType: string = 'regular') => {
    if (typeof window !== 'undefined') {
      fetch('/api/metrics/track', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          type: 'feature_usage',
          data: { featureName, userType }
        })
      }).catch(console.error);
    }
  },

  /**
   * Track client error on client side
   */
  trackError: (errorType: string, component: string, errorMessage?: string) => {
    if (typeof window !== 'undefined') {
      fetch('/api/metrics/track', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          type: 'client_error',
          data: { errorType, component, errorMessage }
        })
      }).catch(console.error);
    }
  }
};

/**
 * Performance monitoring hook
 */
export function usePerformanceMonitoring(componentName: string) {
  if (typeof window !== 'undefined') {
    const startTime = performance.now();
    
    return {
      end: () => {
        const duration = performance.now() - startTime;
        clientMetrics.trackFeature(`render_time_${componentName}`, 'performance');
      }
    };
  }
  
  return { end: () => {} };
}