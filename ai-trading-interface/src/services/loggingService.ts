/**
 * Comprehensive Logging Service
 * Handles application logging, error tracking, and performance monitoring
 */

export enum LogLevel {
  DEBUG = 0,
  INFO = 1,
  WARN = 2,
  ERROR = 3,
  CRITICAL = 4
}

export interface LogEntry {
  id: string;
  timestamp: Date;
  level: LogLevel;
  category: string;
  message: string;
  data?: any;
  userId?: string;
  sessionId: string;
  buildVersion: string;
  platform: string;
  stackTrace?: string;
  context?: Record<string, any>;
}

export interface PerformanceMetric {
  id: string;
  timestamp: Date;
  name: string;
  value: number;
  unit: string;
  category: 'response_time' | 'memory_usage' | 'cpu_usage' | 'network' | 'custom';
  context?: Record<string, any>;
}

export interface ErrorReport {
  id: string;
  timestamp: Date;
  error: Error;
  level: LogLevel;
  category: string;
  userId?: string;
  sessionId: string;
  buildVersion: string;
  platform: string;
  userAgent: string;
  url: string;
  context?: Record<string, any>;
  stackTrace: string;
  breadcrumbs: LogEntry[];
}

class LoggingService {
  private logs: LogEntry[] = [];
  private performanceMetrics: PerformanceMetric[] = [];
  private errorReports: ErrorReport[] = [];
  private sessionId: string;
  private buildVersion: string;
  private platform: string;
  private currentLogLevel: LogLevel;
  private maxLogEntries: number = 1000;
  private maxPerformanceMetrics: number = 500;
  private maxErrorReports: number = 100;
  private breadcrumbs: LogEntry[] = [];
  private maxBreadcrumbs: number = 50;

  constructor() {
    this.sessionId = this.generateSessionId();
    this.buildVersion = this.getBuildVersion();
    this.platform = this.getPlatform();
    this.currentLogLevel = this.getLogLevelFromEnv();
    
    // Set up global error handlers
    this.setupGlobalErrorHandlers();
    
    // Set up performance monitoring
    this.setupPerformanceMonitoring();
    
    // Initialize with startup log
    this.info('LoggingService', 'Logging service initialized', {
      sessionId: this.sessionId,
      buildVersion: this.buildVersion,
      platform: this.platform,
      logLevel: LogLevel[this.currentLogLevel]
    });
  }

  private generateSessionId(): string {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private getBuildVersion(): string {
    return (import.meta.env.VITE_APP_VERSION as string) || '1.0.0';
  }

  private getPlatform(): string {
    return navigator.platform || 'unknown';
  }

  private getLogLevelFromEnv(): LogLevel {
    const envLevel = import.meta.env.VITE_LOG_LEVEL as string;
    switch (envLevel?.toLowerCase()) {
      case 'debug': return LogLevel.DEBUG;
      case 'info': return LogLevel.INFO;
      case 'warn': return LogLevel.WARN;
      case 'error': return LogLevel.ERROR;
      case 'critical': return LogLevel.CRITICAL;
      default: return LogLevel.INFO;
    }
  }

  private setupGlobalErrorHandlers(): void {
    // Handle unhandled promise rejections
    window.addEventListener('unhandledrejection', (event) => {
      this.error('UnhandledPromiseRejection', 'Unhandled promise rejection', {
        reason: event.reason,
        promise: event.promise
      });
    });

    // Handle global errors
    window.addEventListener('error', (event) => {
      this.error('GlobalError', 'Global error occurred', {
        message: event.message,
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno,
        error: event.error
      });
    });

    // Handle resource loading errors
    window.addEventListener('error', (event) => {
      if (event.target !== window) {
        this.warn('ResourceError', 'Resource loading error', {
          tagName: (event.target as any)?.tagName,
          src: (event.target as any)?.src || (event.target as any)?.href,
          type: event.type
        });
      }
    }, true);
  }

  private setupPerformanceMonitoring(): void {
    // Monitor page load performance
    if (typeof window !== 'undefined' && 'performance' in window) {
      window.addEventListener('load', () => {
        setTimeout(() => {
          const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
          if (navigation) {
            this.recordPerformanceMetric('page_load_time', navigation.loadEventEnd - navigation.fetchStart, 'ms');
            this.recordPerformanceMetric('dom_content_loaded', navigation.domContentLoadedEventEnd - navigation.fetchStart, 'ms');
            this.recordPerformanceMetric('first_paint', navigation.responseEnd - navigation.fetchStart, 'ms');
          }
        }, 0);
      });
    }

    // Monitor memory usage (if available)
    if ('memory' in performance) {
      setInterval(() => {
        const memory = (performance as any).memory;
        this.recordPerformanceMetric('memory_used', memory.usedJSHeapSize, 'bytes', 'memory_usage');
        this.recordPerformanceMetric('memory_total', memory.totalJSHeapSize, 'bytes', 'memory_usage');
        this.recordPerformanceMetric('memory_limit', memory.jsHeapSizeLimit, 'bytes', 'memory_usage');
      }, 30000); // Every 30 seconds
    }
  }

  private createLogEntry(level: LogLevel, category: string, message: string, data?: any, context?: Record<string, any>): LogEntry {
    const entry: LogEntry = {
      id: `log_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date(),
      level,
      category,
      message,
      data,
      sessionId: this.sessionId,
      buildVersion: this.buildVersion,
      platform: this.platform,
      context
    };

    // Add stack trace for errors
    if (level >= LogLevel.ERROR) {
      entry.stackTrace = new Error().stack;
    }

    return entry;
  }

  private shouldLog(level: LogLevel): boolean {
    return level >= this.currentLogLevel;
  }

  private addLogEntry(entry: LogEntry): void {
    if (!this.shouldLog(entry.level)) {
      return;
    }

    // Add to logs
    this.logs.push(entry);
    
    // Add to breadcrumbs for error reporting
    this.breadcrumbs.push(entry);
    if (this.breadcrumbs.length > this.maxBreadcrumbs) {
      this.breadcrumbs.shift();
    }

    // Maintain log size limit
    if (this.logs.length > this.maxLogEntries) {
      this.logs.shift();
    }

    // Console output in development
    if (import.meta.env.DEV) {
      this.outputToConsole(entry);
    }

    // Send to external logging service if configured
    this.sendToExternalService(entry);
  }

  private outputToConsole(entry: LogEntry): void {
    const timestamp = entry.timestamp.toISOString();
    const prefix = `[${timestamp}] [${LogLevel[entry.level]}] [${entry.category}]`;
    
    switch (entry.level) {
      case LogLevel.DEBUG:
        console.debug(prefix, entry.message, entry.data);
        break;
      case LogLevel.INFO:
        console.info(prefix, entry.message, entry.data);
        break;
      case LogLevel.WARN:
        console.warn(prefix, entry.message, entry.data);
        break;
      case LogLevel.ERROR:
      case LogLevel.CRITICAL:
        console.error(prefix, entry.message, entry.data);
        if (entry.stackTrace) {
          console.error('Stack trace:', entry.stackTrace);
        }
        break;
    }
  }

  private async sendToExternalService(entry: LogEntry): Promise<void> {
    // Only send errors and critical logs to external service in production
    if (!import.meta.env.PROD || entry.level < LogLevel.ERROR) {
      return;
    }

    try {
      // This would be replaced with actual external logging service
      // For now, we'll store in localStorage as a fallback
      const externalLogs = JSON.parse(localStorage.getItem('external_logs') || '[]');
      externalLogs.push(entry);
      
      // Keep only last 100 external logs
      if (externalLogs.length > 100) {
        externalLogs.splice(0, externalLogs.length - 100);
      }
      
      localStorage.setItem('external_logs', JSON.stringify(externalLogs));
    } catch (error) {
      console.error('Failed to send log to external service:', error);
    }
  }

  // Public logging methods
  debug(category: string, message: string, data?: any, context?: Record<string, any>): void {
    const entry = this.createLogEntry(LogLevel.DEBUG, category, message, data, context);
    this.addLogEntry(entry);
  }

  info(category: string, message: string, data?: any, context?: Record<string, any>): void {
    const entry = this.createLogEntry(LogLevel.INFO, category, message, data, context);
    this.addLogEntry(entry);
  }

  warn(category: string, message: string, data?: any, context?: Record<string, any>): void {
    const entry = this.createLogEntry(LogLevel.WARN, category, message, data, context);
    this.addLogEntry(entry);
  }

  error(category: string, message: string, data?: any, context?: Record<string, any>): void {
    const entry = this.createLogEntry(LogLevel.ERROR, category, message, data, context);
    this.addLogEntry(entry);
    
    // Create error report
    if (data instanceof Error) {
      this.createErrorReport(data, LogLevel.ERROR, category, context);
    }
  }

  critical(category: string, message: string, data?: any, context?: Record<string, any>): void {
    const entry = this.createLogEntry(LogLevel.CRITICAL, category, message, data, context);
    this.addLogEntry(entry);
    
    // Create error report
    if (data instanceof Error) {
      this.createErrorReport(data, LogLevel.CRITICAL, category, context);
    }
  }

  // Performance monitoring
  recordPerformanceMetric(
    name: string, 
    value: number, 
    unit: string = 'ms', 
    category: PerformanceMetric['category'] = 'custom',
    context?: Record<string, any>
  ): void {
    const metric: PerformanceMetric = {
      id: `perf_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date(),
      name,
      value,
      unit,
      category,
      context
    };

    this.performanceMetrics.push(metric);

    // Maintain metrics size limit
    if (this.performanceMetrics.length > this.maxPerformanceMetrics) {
      this.performanceMetrics.shift();
    }

    // Log significant performance issues
    if (category === 'response_time' && value > 5000) { // 5 seconds
      this.warn('Performance', `Slow response time detected: ${name}`, { value, unit });
    }

    this.debug('Performance', `Recorded metric: ${name}`, { value, unit, category });
  }

  // Error reporting
  private createErrorReport(error: Error, level: LogLevel, category: string, context?: Record<string, any>): void {
    const report: ErrorReport = {
      id: `error_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date(),
      error,
      level,
      category,
      sessionId: this.sessionId,
      buildVersion: this.buildVersion,
      platform: this.platform,
      userAgent: navigator.userAgent,
      url: window.location.href,
      context,
      stackTrace: error.stack || new Error().stack || '',
      breadcrumbs: [...this.breadcrumbs]
    };

    this.errorReports.push(report);

    // Maintain error reports size limit
    if (this.errorReports.length > this.maxErrorReports) {
      this.errorReports.shift();
    }

    // Send critical errors immediately
    if (level === LogLevel.CRITICAL) {
      this.sendErrorReport(report);
    }
  }

  private async sendErrorReport(report: ErrorReport): Promise<void> {
    try {
      // This would be replaced with actual error reporting service
      // For now, we'll store in localStorage
      const errorReports = JSON.parse(localStorage.getItem('error_reports') || '[]');
      errorReports.push({
        ...report,
        error: {
          name: report.error.name,
          message: report.error.message,
          stack: report.error.stack
        }
      });
      
      // Keep only last 50 error reports
      if (errorReports.length > 50) {
        errorReports.splice(0, errorReports.length - 50);
      }
      
      localStorage.setItem('error_reports', JSON.stringify(errorReports));
    } catch (error) {
      console.error('Failed to send error report:', error);
    }
  }

  // Timing utilities
  startTimer(name: string): () => void {
    const startTime = performance.now();
    return () => {
      const endTime = performance.now();
      const duration = endTime - startTime;
      this.recordPerformanceMetric(name, duration, 'ms', 'response_time');
    };
  }

  // Data retrieval methods
  getLogs(level?: LogLevel, category?: string, limit?: number): LogEntry[] {
    let filteredLogs = this.logs;

    if (level !== undefined) {
      filteredLogs = filteredLogs.filter(log => log.level >= level);
    }

    if (category) {
      filteredLogs = filteredLogs.filter(log => log.category === category);
    }

    if (limit) {
      filteredLogs = filteredLogs.slice(-limit);
    }

    return filteredLogs;
  }

  getPerformanceMetrics(category?: PerformanceMetric['category'], limit?: number): PerformanceMetric[] {
    let filteredMetrics = this.performanceMetrics;

    if (category) {
      filteredMetrics = filteredMetrics.filter(metric => metric.category === category);
    }

    if (limit) {
      filteredMetrics = filteredMetrics.slice(-limit);
    }

    return filteredMetrics;
  }

  getErrorReports(level?: LogLevel, limit?: number): ErrorReport[] {
    let filteredReports = this.errorReports;

    if (level !== undefined) {
      filteredReports = filteredReports.filter(report => report.level >= level);
    }

    if (limit) {
      filteredReports = filteredReports.slice(-limit);
    }

    return filteredReports;
  }

  // Export data for debugging
  exportLogs(): string {
    return JSON.stringify({
      sessionId: this.sessionId,
      buildVersion: this.buildVersion,
      platform: this.platform,
      timestamp: new Date().toISOString(),
      logs: this.logs,
      performanceMetrics: this.performanceMetrics,
      errorReports: this.errorReports.map(report => ({
        ...report,
        error: {
          name: report.error.name,
          message: report.error.message,
          stack: report.error.stack
        }
      }))
    }, null, 2);
  }

  // Clear data
  clearLogs(): void {
    this.logs = [];
    this.performanceMetrics = [];
    this.errorReports = [];
    this.breadcrumbs = [];
    this.info('LoggingService', 'Logs cleared');
  }

  // Configuration
  setLogLevel(level: LogLevel): void {
    this.currentLogLevel = level;
    this.info('LoggingService', `Log level changed to ${LogLevel[level]}`);
  }

  getSessionId(): string {
    return this.sessionId;
  }

  getBuildVersion(): string {
    return this.buildVersion;
  }
}

// Create singleton instance
export const loggingService = new LoggingService();

// Export convenience functions
export const logger = {
  debug: (category: string, message: string, data?: any, context?: Record<string, any>) => 
    loggingService.debug(category, message, data, context),
  info: (category: string, message: string, data?: any, context?: Record<string, any>) => 
    loggingService.info(category, message, data, context),
  warn: (category: string, message: string, data?: any, context?: Record<string, any>) => 
    loggingService.warn(category, message, data, context),
  error: (category: string, message: string, data?: any, context?: Record<string, any>) => 
    loggingService.error(category, message, data, context),
  critical: (category: string, message: string, data?: any, context?: Record<string, any>) => 
    loggingService.critical(category, message, data, context),
  startTimer: (name: string) => loggingService.startTimer(name),
  recordMetric: (name: string, value: number, unit?: string, category?: PerformanceMetric['category']) => 
    loggingService.recordPerformanceMetric(name, value, unit, category)
};