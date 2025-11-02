/**
 * Frontend performance monitoring and optimization utilities.
 * 
 * Requirements: 4.3, 4.4
 */

// Performance monitoring
export class PerformanceMonitor {
  private static instance: PerformanceMonitor;
  private metrics: Map<string, number[]> = new Map();
  
  static getInstance(): PerformanceMonitor {
    if (!PerformanceMonitor.instance) {
      PerformanceMonitor.instance = new PerformanceMonitor();
    }
    return PerformanceMonitor.instance;
  }
  
  // Measure component render time
  measureRender(componentName: string, renderFn: () => void): void {
    const startTime = performance.now();
    renderFn();
    const endTime = performance.now();
    
    this.recordMetric(`render_${componentName}`, endTime - startTime);
  }
  
  // Measure API call time
  async measureApiCall<T>(
    endpoint: string, 
    apiCall: () => Promise<T>
  ): Promise<T> {
    const startTime = performance.now();
    try {
      const result = await apiCall();
      const endTime = performance.now();
      this.recordMetric(`api_${endpoint}`, endTime - startTime);
      return result;
    } catch (error) {
      const endTime = performance.now();
      this.recordMetric(`api_${endpoint}_error`, endTime - startTime);
      throw error;
    }
  }
  
  // Record custom metric
  recordMetric(name: string, value: number): void {
    if (!this.metrics.has(name)) {
      this.metrics.set(name, []);
    }
    
    const values = this.metrics.get(name)!;
    values.push(value);
    
    // Keep only last 100 measurements
    if (values.length > 100) {
      values.shift();
    }
    
    // Log slow operations
    if (value > 1000) { // More than 1 second
      console.warn(`Slow operation detected: ${name} took ${value.toFixed(2)}ms`);
    }
  }
  
  // Get performance statistics
  getStats(metricName: string): {
    avg: number;
    min: number;
    max: number;
    count: number;
  } | null {
    const values = this.metrics.get(metricName);
    if (!values || values.length === 0) {
      return null;
    }
    
    const sum = values.reduce((a, b) => a + b, 0);
    return {
      avg: sum / values.length,
      min: Math.min(...values),
      max: Math.max(...values),
      count: values.length,
    };
  }
  
  // Get all metrics
  getAllStats(): Record<string, any> {
    const stats: Record<string, any> = {};
    
    for (const [name, values] of this.metrics.entries()) {
      if (values.length > 0) {
        const sum = values.reduce((a, b) => a + b, 0);
        stats[name] = {
          avg: sum / values.length,
          min: Math.min(...values),
          max: Math.max(...values),
          count: values.length,
        };
      }
    }
    
    return stats;
  }
  
  // Clear metrics
  clearMetrics(): void {
    this.metrics.clear();
  }
}

// Web Vitals monitoring
export class WebVitalsMonitor {
  private static vitals: Record<string, number> = {};
  
  static recordVital(name: string, value: number): void {
    WebVitalsMonitor.vitals[name] = value;
    
    // Log poor performance
    const thresholds = {
      CLS: 0.1,
      FID: 100,
      FCP: 1800,
      LCP: 2500,
      TTFB: 800,
    };
    
    if (thresholds[name as keyof typeof thresholds] && 
        value > thresholds[name as keyof typeof thresholds]) {
      console.warn(`Poor ${name}: ${value}`);
    }
  }
  
  static getVitals(): Record<string, number> {
    return { ...WebVitalsMonitor.vitals };
  }
  
  static reportVitals(): void {
    // Send vitals to analytics service
    if (typeof window !== 'undefined' && WebVitalsMonitor.vitals) {
      // In a real app, you'd send this to your analytics service
      console.log('Web Vitals:', WebVitalsMonitor.vitals);
    }
  }
}

// Cache management
export class CacheManager {
  private static cache = new Map<string, { data: any; timestamp: number; ttl: number }>();
  
  static set(key: string, data: any, ttlMs: number = 300000): void { // 5 minutes default
    CacheManager.cache.set(key, {
      data,
      timestamp: Date.now(),
      ttl: ttlMs,
    });
  }
  
  static get<T>(key: string): T | null {
    const item = CacheManager.cache.get(key);
    
    if (!item) {
      return null;
    }
    
    // Check if expired
    if (Date.now() - item.timestamp > item.ttl) {
      CacheManager.cache.delete(key);
      return null;
    }
    
    return item.data as T;
  }
  
  static has(key: string): boolean {
    const item = CacheManager.cache.get(key);
    
    if (!item) {
      return false;
    }
    
    // Check if expired
    if (Date.now() - item.timestamp > item.ttl) {
      CacheManager.cache.delete(key);
      return false;
    }
    
    return true;
  }
  
  static delete(key: string): void {
    CacheManager.cache.delete(key);
  }
  
  static clear(): void {
    CacheManager.cache.clear();
  }
  
  static cleanup(): void {
    const now = Date.now();
    
    for (const [key, item] of CacheManager.cache.entries()) {
      if (now - item.timestamp > item.ttl) {
        CacheManager.cache.delete(key);
      }
    }
  }
}

// Image optimization utilities
export class ImageOptimizer {
  static getOptimizedImageProps(
    src: string,
    alt: string,
    width?: number,
    height?: number
  ) {
    return {
      src,
      alt,
      width,
      height,
      loading: 'lazy' as const,
      placeholder: 'blur' as const,
      blurDataURL: 'data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCdABmX/9k=',
      quality: 85,
      sizes: width && height 
        ? `(max-width: 768px) 100vw, ${width}px`
        : '(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw',
    };
  }
  
  static preloadImage(src: string): Promise<void> {
    return new Promise((resolve, reject) => {
      const img = new Image();
      img.onload = () => resolve();
      img.onerror = reject;
      img.src = src;
    });
  }
  
  static preloadImages(sources: string[]): Promise<void[]> {
    return Promise.all(sources.map(src => ImageOptimizer.preloadImage(src)));
  }
}

// Bundle size monitoring
export class BundleMonitor {
  static logBundleSize(): void {
    if (typeof window !== 'undefined' && 'performance' in window) {
      const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
      
      if (navigation) {
        const transferSize = navigation.transferSize;
        const encodedBodySize = navigation.encodedBodySize;
        const decodedBodySize = navigation.decodedBodySize;
        
        console.log('Bundle metrics:', {
          transferSize: `${(transferSize / 1024).toFixed(2)} KB`,
          encodedBodySize: `${(encodedBodySize / 1024).toFixed(2)} KB`,
          decodedBodySize: `${(decodedBodySize / 1024).toFixed(2)} KB`,
          compressionRatio: encodedBodySize > 0 ? (decodedBodySize / encodedBodySize).toFixed(2) : 'N/A',
        });
      }
    }
  }
}

// Resource loading optimization
export class ResourceLoader {
  private static loadedResources = new Set<string>();
  
  static async loadScript(src: string): Promise<void> {
    if (ResourceLoader.loadedResources.has(src)) {
      return Promise.resolve();
    }
    
    return new Promise((resolve, reject) => {
      const script = document.createElement('script');
      script.src = src;
      script.async = true;
      
      script.onload = () => {
        ResourceLoader.loadedResources.add(src);
        resolve();
      };
      
      script.onerror = reject;
      
      document.head.appendChild(script);
    });
  }
  
  static async loadStylesheet(href: string): Promise<void> {
    if (ResourceLoader.loadedResources.has(href)) {
      return Promise.resolve();
    }
    
    return new Promise((resolve, reject) => {
      const link = document.createElement('link');
      link.rel = 'stylesheet';
      link.href = href;
      
      link.onload = () => {
        ResourceLoader.loadedResources.add(href);
        resolve();
      };
      
      link.onerror = reject;
      
      document.head.appendChild(link);
    });
  }
  
  static preloadResource(href: string, as: string): void {
    if (typeof document !== 'undefined') {
      const link = document.createElement('link');
      link.rel = 'preload';
      link.href = href;
      link.as = as;
      document.head.appendChild(link);
    }
  }
}

// Performance hooks for React components
export function usePerformanceMonitor(componentName: string) {
  const monitor = PerformanceMonitor.getInstance();
  
  return {
    measureRender: (renderFn: () => void) => {
      monitor.measureRender(componentName, renderFn);
    },
    measureApiCall: <T>(endpoint: string, apiCall: () => Promise<T>) => {
      return monitor.measureApiCall(endpoint, apiCall);
    },
    recordMetric: (name: string, value: number) => {
      monitor.recordMetric(`${componentName}_${name}`, value);
    },
  };
}

// Debounce utility for performance
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout;
  
  return (...args: Parameters<T>) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
}

// Throttle utility for performance
export function throttle<T extends (...args: any[]) => any>(
  func: T,
  limit: number
): (...args: Parameters<T>) => void {
  let inThrottle: boolean;
  
  return (...args: Parameters<T>) => {
    if (!inThrottle) {
      func(...args);
      inThrottle = true;
      setTimeout(() => inThrottle = false, limit);
    }
  };
}

// Initialize performance monitoring
if (typeof window !== 'undefined') {
  // Clean up cache periodically
  setInterval(() => {
    CacheManager.cleanup();
  }, 60000); // Every minute
  
  // Report web vitals on page unload
  window.addEventListener('beforeunload', () => {
    WebVitalsMonitor.reportVitals();
  });
  
  // Log bundle size in development
  if (process.env.NODE_ENV === 'development') {
    window.addEventListener('load', () => {
      setTimeout(() => {
        BundleMonitor.logBundleSize();
      }, 1000);
    });
  }
}