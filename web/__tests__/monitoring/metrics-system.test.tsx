/**
 * Test frontend metrics collection and monitoring system
 * 
 * This test suite validates the client-side metrics collection,
 * API endpoint functionality, and integration with Prometheus.
 */

// Mock Next.js server components
jest.mock('next/server', () => ({
  NextRequest: jest.fn(),
  NextResponse: {
    json: jest.fn((data, init) => ({
      json: () => Promise.resolve(data),
      status: init?.status || 200,
    })),
    text: jest.fn((text, init) => ({
      text: () => Promise.resolve(text),
      status: init?.status || 200,
    })),
  },
}));

// Mock prometheus client
jest.mock('prom-client', () => ({
  register: {
    metrics: jest.fn(() => Promise.resolve('# Mock metrics\ntest_metric 1.0')),
    contentType: 'text/plain; version=0.0.4; charset=utf-8',
  },
  Counter: jest.fn(),
  Histogram: jest.fn(),
  Gauge: jest.fn(),
}));

import { NextRequest } from 'next/server';
import { GET, POST } from '@/app/api/metrics/route';
import { clientMetrics } from '@/lib/metrics';

// Mock fetch for client-side tests
global.fetch = jest.fn();

// Mock performance API
Object.defineProperty(window, 'performance', {
  value: {
    now: jest.fn(() => Date.now()),
  },
  writable: true,
});

describe('Frontend Metrics System', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (fetch as jest.Mock).mockClear();
  });

  describe('Metrics API Endpoint', () => {
    it('should return Prometheus metrics in GET request', async () => {
      const response = await GET();
      
      expect(response.status).toBe(200);
      
      const text = await response.text();
      expect(text).toContain('# HELP');
      expect(text).toContain('# TYPE');
    });

    it('should handle POST requests for client metrics tracking', async () => {
      const mockRequest = {
        json: jest.fn().mockResolvedValue({
          type: 'page_view',
          data: {
            page: '/dashboard',
            userType: 'authenticated'
          }
        })
      } as unknown as NextRequest;

      const response = await POST(mockRequest);
      
      expect(response.status).toBe(200);
      
      const data = await response.json();
      expect(data.success).toBe(true);
    });

    it('should handle invalid metric types in POST requests', async () => {
      const mockRequest = {
        json: jest.fn().mockResolvedValue({
          type: 'invalid_type',
          data: {}
        })
      } as unknown as NextRequest;

      const response = await POST(mockRequest);
      
      expect(response.status).toBe(400);
      
      const data = await response.json();
      expect(data.error).toBe('Unknown metric type');
    });

    it('should handle malformed POST requests', async () => {
      const mockRequest = {
        json: jest.fn().mockRejectedValue(new Error('Invalid JSON'))
      } as unknown as NextRequest;

      const response = await POST(mockRequest);
      
      expect(response.status).toBe(500);
      
      const data = await response.json();
      expect(data.error).toBe('Failed to track metric');
    });
  });

  describe('Client-side Metrics Tracking', () => {
    it('should track page views', async () => {
      (fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ success: true })
      });

      await clientMetrics.trackPageView('/dashboard', 'authenticated');

      expect(fetch).toHaveBeenCalledWith('/api/metrics/track', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          type: 'page_view',
          data: { page: '/dashboard', userType: 'authenticated' }
        })
      });
    });

    it('should track user interactions', async () => {
      (fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ success: true })
      });

      await clientMetrics.trackInteraction('click', 'cv-upload-button');

      expect(fetch).toHaveBeenCalledWith('/api/metrics/track', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          type: 'user_interaction',
          data: { interactionType: 'click', component: 'cv-upload-button' }
        })
      });
    });

    it('should track feature usage', async () => {
      (fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ success: true })
      });

      await clientMetrics.trackFeature('portfolio-generation', 'premium');

      expect(fetch).toHaveBeenCalledWith('/api/metrics/track', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          type: 'feature_usage',
          data: { featureName: 'portfolio-generation', userType: 'premium' }
        })
      });
    });

    it('should track client errors', async () => {
      (fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ success: true })
      });

      await clientMetrics.trackError('javascript_error', 'ai-chat', 'Network timeout');

      expect(fetch).toHaveBeenCalledWith('/api/metrics/track', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          type: 'client_error',
          data: { 
            errorType: 'javascript_error', 
            component: 'ai-chat',
            errorMessage: 'Network timeout'
          }
        })
      });
    });

    it('should handle fetch errors gracefully', async () => {
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();
      (fetch as jest.Mock).mockRejectedValue(new Error('Network error'));

      // Should not throw
      await expect(clientMetrics.trackPageView('/test')).resolves.toBeUndefined();

      expect(consoleSpy).toHaveBeenCalledWith(expect.any(Error));
      consoleSpy.mockRestore();
    });

    it('should not track metrics on server side', () => {
      // Mock server environment
      const originalWindow = global.window;
      delete (global as any).window;

      // Should not make fetch calls
      clientMetrics.trackPageView('/test');
      expect(fetch).not.toHaveBeenCalled();

      // Restore window
      global.window = originalWindow;
    });
  });

  describe('Performance Monitoring', () => {
    it('should track component render times', () => {
      const mockPerformance = {
        now: jest.fn()
          .mockReturnValueOnce(1000) // Start time
          .mockReturnValueOnce(1050) // End time
      };

      Object.defineProperty(window, 'performance', {
        value: mockPerformance,
        writable: true,
      });

      (fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ success: true })
      });

      // Import after mocking performance
      const { usePerformanceMonitoring } = require('@/lib/metrics');
      
      const monitor = usePerformanceMonitoring('TestComponent');
      monitor.end();

      expect(mockPerformance.now).toHaveBeenCalledTimes(2);
    });

    it('should handle missing performance API', () => {
      const originalPerformance = window.performance;
      delete (window as any).performance;

      const { usePerformanceMonitoring } = require('@/lib/metrics');
      
      // Should not throw
      expect(() => {
        const monitor = usePerformanceMonitoring('TestComponent');
        monitor.end();
      }).not.toThrow();

      window.performance = originalPerformance;
    });
  });

  describe('Metrics Data Validation', () => {
    it('should validate page view data', async () => {
      const mockRequest = {
        json: jest.fn().mockResolvedValue({
          type: 'page_view',
          data: {
            page: '/dashboard',
            userType: 'authenticated'
          }
        })
      } as unknown as NextRequest;

      const response = await POST(mockRequest);
      expect(response.status).toBe(200);
    });

    it('should handle missing data fields', async () => {
      const mockRequest = {
        json: jest.fn().mockResolvedValue({
          type: 'page_view',
          data: {} // Missing required fields
        })
      } as unknown as NextRequest;

      // Should still process but may have undefined values
      const response = await POST(mockRequest);
      expect(response.status).toBe(200);
    });

    it('should handle null data', async () => {
      const mockRequest = {
        json: jest.fn().mockResolvedValue({
          type: 'page_view',
          data: null
        })
      } as unknown as NextRequest;

      // Should handle gracefully
      const response = await POST(mockRequest);
      expect(response.status).toBe(500); // Will fail when trying to access data properties
    });
  });

  describe('Metrics Integration', () => {
    it('should format metrics for Prometheus consumption', async () => {
      const response = await GET();
      const metricsText = await response.text();

      // Check Prometheus format requirements
      expect(metricsText).toMatch(/# HELP \w+ .+/);
      expect(metricsText).toMatch(/# TYPE \w+ (counter|gauge|histogram|summary)/);
      
      // Check for specific Koroh metrics
      expect(metricsText).toContain('koroh_web_');
    });

    it('should include proper metric labels', async () => {
      // Track some metrics first
      const mockRequest = {
        json: jest.fn().mockResolvedValue({
          type: 'user_interaction',
          data: {
            interactionType: 'click',
            component: 'navigation'
          }
        })
      } as unknown as NextRequest;

      await POST(mockRequest);

      const response = await GET();
      const metricsText = await response.text();

      // Should include label information in metrics output
      expect(metricsText).toContain('koroh_web_');
    });

    it('should handle concurrent metric updates', async () => {
      const requests = Array.from({ length: 10 }, (_, i) => ({
        json: jest.fn().mockResolvedValue({
          type: 'page_view',
          data: {
            page: `/page-${i}`,
            userType: 'authenticated'
          }
        })
      })) as unknown as NextRequest[];

      // Process multiple requests concurrently
      const responses = await Promise.all(
        requests.map(request => POST(request))
      );

      // All should succeed
      for (const response of responses) {
        expect(response.status).toBe(200);
      }
    });
  });

  describe('Error Handling and Resilience', () => {
    it('should handle metrics collection failures gracefully', async () => {
      // Mock register.metrics to throw an error
      const originalMetrics = require('prom-client').register.metrics;
      require('prom-client').register.metrics = jest.fn().mockRejectedValue(
        new Error('Metrics collection failed')
      );

      const response = await GET();
      expect(response.status).toBe(500);

      const data = await response.json();
      expect(data.error).toBe('Failed to generate metrics');

      // Restore original function
      require('prom-client').register.metrics = originalMetrics;
    });

    it('should continue functioning when tracking fails', async () => {
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();
      
      // Mock fetch to fail
      (fetch as jest.Mock).mockRejectedValue(new Error('Network failure'));

      // Should not throw and should continue execution
      await expect(clientMetrics.trackPageView('/test')).resolves.toBeUndefined();
      
      expect(consoleSpy).toHaveBeenCalled();
      consoleSpy.mockRestore();
    });

    it('should validate metric types', async () => {
      const validTypes = ['page_view', 'user_interaction', 'feature_usage', 'client_error'];
      
      for (const type of validTypes) {
        const mockRequest = {
          json: jest.fn().mockResolvedValue({
            type,
            data: { test: 'data' }
          })
        } as unknown as NextRequest;

        const response = await POST(mockRequest);
        expect(response.status).toBe(200);
      }

      // Test invalid type
      const invalidRequest = {
        json: jest.fn().mockResolvedValue({
          type: 'invalid_type',
          data: { test: 'data' }
        })
      } as unknown as NextRequest;

      const response = await POST(invalidRequest);
      expect(response.status).toBe(400);
    });
  });
});