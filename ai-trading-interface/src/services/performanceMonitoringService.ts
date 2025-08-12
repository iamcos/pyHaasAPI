/**
 * Performance Monitoring Service
 * Comprehensive performance monitoring and alerting system
 */

import { logger } from './loggingService';

export interface PerformanceThreshold {
  metric: string;
  warning: number;
  critical: number;
  unit: string;
}

export interface PerformanceAlert {
  id: string;
  timestamp: Date;
  metric: string;
  value: number;
  threshold: number;
  severity: 'warning' | 'critical';
  component?: string;
  context?: Record<string, any>;
}

export interface ResourceUsage {
  timestamp: Date;
  memory: {
    used: number;
    total: number;
    limit: number;
  };
  cpu?: {
    usage: number;
  };
  network: {
    downlink?: number;
    effectiveType?: string;
    rtt?: number;
  };
}

export interface ComponentPerformance {
  componentName: string;
  renderTime: number;
  renderCount: number;
  averageRenderTime: number;
  lastRender: Date;
  props?: Record<string, any>;
}

class PerformanceMonitoringService {
  private thresholds: Map<string, PerformanceThreshold> = new Map();
  private alerts: PerformanceAlert[] = [];
  private resourceUsageHistory: ResourceUsage[] = [];
  private componentPerformance: Map<string, ComponentPerformance> = new Map();
  private performanceObserver?: PerformanceObserver;
  private resourceMonitorInterval?: number;
  private isMonitoring: boolean = false;
  private maxAlerts: number = 100;
  private maxResourceHistory: number = 1000;

  constructor() {
    this.setupDefaultThresholds();
    this.initialize();
  }

  private setupDefaultThresholds(): void {
    // Default performance thresholds
    this.thresholds.set('response_time', {
      metric: 'response_time',
      warning: 1000, // 1 second
      critical: 5000, // 5 seconds
      unit: 'ms'
    });

    this.thresholds.set('memory_usage', {
      metric: 'memory_usage',
      warning: 100 * 1024 * 1024, // 100MB
      critical: 500 * 1024 * 1024, // 500MB
      unit: 'bytes'
    });

    this.thresholds.set('render_time', {
      metric: 'render_time',
      warning: 16, // 16ms (60fps)
      critical: 33, // 33ms (30fps)
      unit: 'ms'
    });

    this.thresholds.set('bundle_size', {
      metric: 'bundle_size',
      warning: 1024 * 1024, // 1MB
      critical: 5 * 1024 * 1024, // 5MB
      unit: 'bytes'
    });

    this.thresholds.set('api_response_time', {
      metric: 'api_response_time',
      warning: 2000, // 2 seconds
      critical: 10000, // 10 seconds
      unit: 'ms'
    });
  }

  private initialize(): void {
    if (typeof window === 'undefined') return;

    this.setupPerformanceObserver();
    this.setupResourceMonitoring();
    this.setupNavigationTiming();
    this.setupNetworkMonitoring();

    this.isMonitoring = true;
    logger.info('PerformanceMonitoring', 'Performance monitoring service initialized');
  }

  private setupPerformanceObserver(): void {
    if (!('PerformanceObserver' in window)) {
      logger.warn('PerformanceMonitoring', 'PerformanceObserver not supported');
      return;
    }

    try {
      this.performanceObserver = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          this.processPerformanceEntry(entry);
        }
      });

      // Observe different types of performance entries
      const entryTypes = ['measure', 'navigation', 'resource', 'paint', 'largest-contentful-paint'];
      
      for (const entryType of entryTypes) {
        try {
          this.performanceObserver.observe({ entryTypes: [entryType] });
        } catch (error) {
          logger.debug('PerformanceMonitoring', `Entry type ${entryType} not supported`, error);
        }
      }

      // Observe long tasks if supported
      try {
        this.performanceObserver.observe({ entryTypes: ['longtask'] });
      } catch (error) {
        logger.debug('PerformanceMonitoring', 'Long task monitoring not supported', error);
      }

    } catch (error) {
      logger.warn('PerformanceMonitoring', 'Failed to setup performance observer', error);
    }
  }

  private setupResourceMonitoring(): void {
    // Monitor resource usage every 30 seconds
    this.resourceMonitorInterval = window.setInterval(() => {
      this.collectResourceUsage();
    }, 30000);

    // Initial collection
    this.collectResourceUsage();
  }

  private setupNavigationTiming(): void {
    window.addEventListener('load', () => {
      setTimeout(() => {
        this.analyzeNavigationTiming();
      }, 0);
    });
  }

  private setupNetworkMonitoring(): void {
    // Monitor network information if available
    if ('connection' in navigator) {
      const connection = (navigator as any).connection;
      
      const logNetworkInfo = () => {
        logger.info('PerformanceMonitoring', 'Network information', {
          effectiveType: connection.effectiveType,
          downlink: connection.downlink,
          rtt: connection.rtt,
          saveData: connection.saveData
        });
      };

      connection.addEventListener('change', logNetworkInfo);
      logNetworkInfo(); // Initial log
    }
  }

  private processPerformanceEntry(entry: PerformanceEntry): void {
    switch (entry.entryType) {
      case 'measure':
        this.processMeasureEntry(entry as PerformanceMeasure);
        break;
      case 'navigation':
        this.processNavigationEntry(entry as PerformanceNavigationTiming);
        break;
      case 'resource':
        this.processResourceEntry(entry as PerformanceResourceTiming);
        break;
      case 'paint':
        this.processPaintEntry(entry as PerformancePaintTiming);
        break;
      case 'largest-contentful-paint':
        this.processLCPEntry(entry as PerformanceEventTiming);
        break;
      case 'longtask':
        this.processLongTaskEntry(entry);
        break;
    }
  }

  private processMeasureEntry(entry: PerformanceMeasure): void {
    const duration = entry.duration;
    
    // Check if this is a component render measurement
    if (entry.name.startsWith('component:')) {
      const componentName = entry.name.replace('component:', '');
      this.recordComponentPerformance(componentName, duration);
    }

    this.checkThreshold('render_time', duration, { measureName: entry.name });
    
    logger.debug('PerformanceMonitoring', `Measure: ${entry.name}`, {
      duration,
      startTime: entry.startTime
    });
  }

  private processNavigationEntry(entry: PerformanceNavigationTiming): void {
    const metrics = {
      dns: entry.domainLookupEnd - entry.domainLookupStart,
      tcp: entry.connectEnd - entry.connectStart,
      request: entry.responseStart - entry.requestStart,
      response: entry.responseEnd - entry.responseStart,
      dom: entry.domContentLoadedEventEnd - entry.domContentLoadedEventStart,
      load: entry.loadEventEnd - entry.loadEventStart,
      total: entry.loadEventEnd - entry.fetchStart
    };

    logger.info('PerformanceMonitoring', 'Navigation timing', metrics);

    // Check thresholds
    this.checkThreshold('response_time', metrics.total, { type: 'navigation' });
  }

  private processResourceEntry(entry: PerformanceResourceTiming): void {
    const duration = entry.responseEnd - entry.requestStart;
    
    // Check for slow resource loading
    if (duration > 5000) { // 5 seconds
      this.checkThreshold('api_response_time', duration, {
        resource: entry.name,
        type: 'resource'
      });
    }

    logger.debug('PerformanceMonitoring', `Resource: ${entry.name}`, {
      duration,
      size: entry.transferSize,
      type: entry.initiatorType
    });
  }

  private processPaintEntry(entry: PerformancePaintTiming): void {
    logger.info('PerformanceMonitoring', `Paint: ${entry.name}`, {
      startTime: entry.startTime
    });

    // Check paint timing thresholds
    if (entry.name === 'first-contentful-paint' && entry.startTime > 3000) {
      this.checkThreshold('response_time', entry.startTime, {
        type: 'first-contentful-paint'
      });
    }
  }

  private processLCPEntry(entry: PerformanceEventTiming): void {
    logger.info('PerformanceMonitoring', 'Largest Contentful Paint', {
      startTime: entry.startTime,
      element: (entry as any).element?.tagName
    });

    // Check LCP threshold
    if (entry.startTime > 2500) { // 2.5 seconds
      this.checkThreshold('response_time', entry.startTime, {
        type: 'largest-contentful-paint'
      });
    }
  }

  private processLongTaskEntry(entry: PerformanceEntry): void {
    logger.warn('PerformanceMonitoring', 'Long task detected', {
      duration: entry.duration,
      startTime: entry.startTime
    });

    this.checkThreshold('render_time', entry.duration, {
      type: 'long-task'
    });
  }

  private collectResourceUsage(): void {
    const usage: ResourceUsage = {
      timestamp: new Date(),
      memory: {
        used: 0,
        total: 0,
        limit: 0
      },
      network: {}
    };

    // Collect memory information if available
    if ('memory' in performance) {
      const memory = (performance as any).memory;
      usage.memory = {
        used: memory.usedJSHeapSize,
        total: memory.totalJSHeapSize,
        limit: memory.jsHeapSizeLimit
      };

      // Check memory threshold
      this.checkThreshold('memory_usage', memory.usedJSHeapSize, {
        type: 'memory'
      });
    }

    // Collect network information if available
    if ('connection' in navigator) {
      const connection = (navigator as any).connection;
      usage.network = {
        downlink: connection.downlink,
        effectiveType: connection.effectiveType,
        rtt: connection.rtt
      };
    }

    this.resourceUsageHistory.push(usage);

    // Maintain history size limit
    if (this.resourceUsageHistory.length > this.maxResourceHistory) {
      this.resourceUsageHistory.shift();
    }

    logger.debug('PerformanceMonitoring', 'Resource usage collected', usage);
  }

  private analyzeNavigationTiming(): void {
    const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
    if (!navigation) return;

    const analysis = {
      redirectTime: navigation.redirectEnd - navigation.redirectStart,
      dnsTime: navigation.domainLookupEnd - navigation.domainLookupStart,
      tcpTime: navigation.connectEnd - navigation.connectStart,
      requestTime: navigation.responseStart - navigation.requestStart,
      responseTime: navigation.responseEnd - navigation.responseStart,
      domProcessingTime: navigation.domContentLoadedEventStart - navigation.responseEnd,
      loadEventTime: navigation.loadEventEnd - navigation.loadEventStart,
      totalTime: navigation.loadEventEnd - navigation.fetchStart
    };

    logger.info('PerformanceMonitoring', 'Navigation timing analysis', analysis);

    // Record metrics
    Object.entries(analysis).forEach(([key, value]) => {
      if (value > 0) {
        logger.recordMetric(`navigation_${key}`, value, 'ms', 'response_time');
      }
    });
  }

  // Public methods
  recordComponentPerformance(componentName: string, renderTime: number, props?: Record<string, any>): void {
    const existing = this.componentPerformance.get(componentName);
    
    if (existing) {
      existing.renderCount++;
      existing.renderTime += renderTime;
      existing.averageRenderTime = existing.renderTime / existing.renderCount;
      existing.lastRender = new Date();
      existing.props = props;
    } else {
      this.componentPerformance.set(componentName, {
        componentName,
        renderTime,
        renderCount: 1,
        averageRenderTime: renderTime,
        lastRender: new Date(),
        props
      });
    }

    // Check render time threshold
    this.checkThreshold('render_time', renderTime, {
      component: componentName,
      props
    });

    logger.debug('PerformanceMonitoring', `Component render: ${componentName}`, {
      renderTime,
      props
    });
  }

  measureAsync<T>(name: string, asyncFn: () => Promise<T>): Promise<T> {
    const startTime = performance.now();
    
    return asyncFn().then(
      (result) => {
        const endTime = performance.now();
        const duration = endTime - startTime;
        
        performance.mark(`${name}-start`);
        performance.mark(`${name}-end`);
        performance.measure(name, `${name}-start`, `${name}-end`);
        
        logger.recordMetric(name, duration, 'ms', 'response_time');
        
        return result;
      },
      (error) => {
        const endTime = performance.now();
        const duration = endTime - startTime;
        
        logger.recordMetric(`${name}-error`, duration, 'ms', 'response_time');
        
        throw error;
      }
    );
  }

  measureSync<T>(name: string, syncFn: () => T): T {
    const startTime = performance.now();
    
    try {
      const result = syncFn();
      const endTime = performance.now();
      const duration = endTime - startTime;
      
      performance.mark(`${name}-start`);
      performance.mark(`${name}-end`);
      performance.measure(name, `${name}-start`, `${name}-end`);
      
      logger.recordMetric(name, duration, 'ms', 'response_time');
      
      return result;
    } catch (error) {
      const endTime = performance.now();
      const duration = endTime - startTime;
      
      logger.recordMetric(`${name}-error`, duration, 'ms', 'response_time');
      
      throw error;
    }
  }

  setThreshold(metric: string, threshold: PerformanceThreshold): void {
    this.thresholds.set(metric, threshold);
    logger.info('PerformanceMonitoring', `Threshold set for ${metric}`, threshold);
  }

  private checkThreshold(
    metric: string, 
    value: number, 
    context?: Record<string, any>
  ): void {
    const threshold = this.thresholds.get(metric);
    if (!threshold) return;

    let severity: 'warning' | 'critical' | null = null;
    let thresholdValue: number;

    if (value >= threshold.critical) {
      severity = 'critical';
      thresholdValue = threshold.critical;
    } else if (value >= threshold.warning) {
      severity = 'warning';
      thresholdValue = threshold.warning;
    }

    if (severity) {
      const alert: PerformanceAlert = {
        id: `alert_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        timestamp: new Date(),
        metric,
        value,
        threshold: thresholdValue,
        severity,
        component: context?.component,
        context
      };

      this.alerts.push(alert);

      // Maintain alerts size limit
      if (this.alerts.length > this.maxAlerts) {
        this.alerts.shift();
      }

      // Log the alert
      const logLevel = severity === 'critical' ? 'error' : 'warn';
      logger[logLevel]('PerformanceMonitoring', `Performance alert: ${metric}`, alert);

      // Trigger alert callback if configured
      this.triggerAlert(alert);
    }
  }

  private triggerAlert(alert: PerformanceAlert): void {
    // In a real implementation, this could send notifications, emails, etc.
    logger.info('PerformanceMonitoring', 'Performance alert triggered', alert);
  }

  // Data retrieval methods
  getAlerts(severity?: 'warning' | 'critical', limit?: number): PerformanceAlert[] {
    let filteredAlerts = this.alerts;

    if (severity) {
      filteredAlerts = filteredAlerts.filter(alert => alert.severity === severity);
    }

    if (limit) {
      filteredAlerts = filteredAlerts.slice(-limit);
    }

    return filteredAlerts;
  }

  getResourceUsageHistory(limit?: number): ResourceUsage[] {
    return limit ? this.resourceUsageHistory.slice(-limit) : [...this.resourceUsageHistory];
  }

  getComponentPerformance(): ComponentPerformance[] {
    return Array.from(this.componentPerformance.values());
  }

  getPerformanceReport(): any {
    return {
      timestamp: new Date().toISOString(),
      alerts: this.alerts,
      resourceUsage: this.resourceUsageHistory.slice(-10), // Last 10 entries
      componentPerformance: this.getComponentPerformance(),
      thresholds: Object.fromEntries(this.thresholds),
      isMonitoring: this.isMonitoring
    };
  }

  // Cleanup
  cleanup(): void {
    if (this.performanceObserver) {
      this.performanceObserver.disconnect();
    }

    if (this.resourceMonitorInterval) {
      clearInterval(this.resourceMonitorInterval);
    }

    this.alerts = [];
    this.resourceUsageHistory = [];
    this.componentPerformance.clear();
    this.isMonitoring = false;

    logger.info('PerformanceMonitoring', 'Performance monitoring service cleaned up');
  }
}

// Create singleton instance
export const performanceMonitoringService = new PerformanceMonitoringService();

// React HOC for component performance monitoring
export const withPerformanceMonitoring = (Component: React.ComponentType<any>) => {
  return React.memo((props: any) => {
    const componentName = Component.displayName || Component.name || 'Unknown';
    
    React.useEffect(() => {
      const startTime = performance.now();
      
      return () => {
        const endTime = performance.now();
        const renderTime = endTime - startTime;
        performanceMonitoringService.recordComponentPerformance(componentName, renderTime, props);
      };
    });

    return <Component {...props} />;
  });
};

export default performanceMonitoringService;