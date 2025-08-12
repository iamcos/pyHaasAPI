/**
 * Error Tracking Service
 * Advanced error tracking and reporting with context and user journey tracking
 */

import { logger, LogLevel } from './loggingService';

export interface ErrorContext {
  userId?: string;
  userAction?: string;
  componentName?: string;
  props?: Record<string, any>;
  state?: Record<string, any>;
  route?: string;
  timestamp: Date;
  sessionId: string;
  buildVersion: string;
}

export interface UserAction {
  id: string;
  timestamp: Date;
  type: 'click' | 'input' | 'navigation' | 'api_call' | 'custom';
  target?: string;
  data?: any;
  route?: string;
}

export interface ErrorBoundaryInfo {
  componentStack: string;
  errorBoundary?: string;
  errorInfo?: any;
}

export interface NetworkError {
  url: string;
  method: string;
  status?: number;
  statusText?: string;
  responseTime?: number;
  requestData?: any;
  responseData?: any;
}

export interface PerformanceIssue {
  type: 'slow_render' | 'memory_leak' | 'large_bundle' | 'slow_api' | 'custom';
  component?: string;
  metric: string;
  value: number;
  threshold: number;
  impact: 'low' | 'medium' | 'high' | 'critical';
}

class ErrorTrackingService {
  private userActions: UserAction[] = [];
  private maxUserActions: number = 100;
  private errorContexts: Map<string, ErrorContext> = new Map();
  private performanceObserver?: PerformanceObserver;
  private isInitialized: boolean = false;

  constructor() {
    this.initialize();
  }

  private initialize(): void {
    if (this.isInitialized) return;

    // Set up performance monitoring
    this.setupPerformanceMonitoring();
    
    // Set up user action tracking
    this.setupUserActionTracking();
    
    // Set up network error tracking
    this.setupNetworkErrorTracking();

    this.isInitialized = true;
    logger.info('ErrorTracking', 'Error tracking service initialized');
  }

  private setupPerformanceMonitoring(): void {
    if (typeof window === 'undefined' || !('PerformanceObserver' in window)) {
      return;
    }

    try {
      // Monitor long tasks
      this.performanceObserver = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          if (entry.entryType === 'longtask') {
            this.reportPerformanceIssue({
              type: 'slow_render',
              metric: 'task_duration',
              value: entry.duration,
              threshold: 50, // 50ms threshold
              impact: entry.duration > 100 ? 'high' : 'medium'
            });
          }
        }
      });

      this.performanceObserver.observe({ entryTypes: ['longtask'] });

      // Monitor largest contentful paint
      const lcpObserver = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          const lcp = entry as PerformanceEventTiming;
          if (lcp.startTime > 2500) { // 2.5s threshold
            this.reportPerformanceIssue({
              type: 'slow_render',
              metric: 'largest_contentful_paint',
              value: lcp.startTime,
              threshold: 2500,
              impact: lcp.startTime > 4000 ? 'critical' : 'high'
            });
          }
        }
      });

      lcpObserver.observe({ entryTypes: ['largest-contentful-paint'] });

    } catch (error) {
      logger.warn('ErrorTracking', 'Failed to setup performance monitoring', error);
    }
  }

  private setupUserActionTracking(): void {
    if (typeof window === 'undefined') return;

    // Track clicks
    document.addEventListener('click', (event) => {
      this.recordUserAction({
        type: 'click',
        target: this.getElementSelector(event.target as Element),
        data: {
          x: event.clientX,
          y: event.clientY,
          button: event.button
        }
      });
    }, { passive: true });

    // Track form inputs
    document.addEventListener('input', (event) => {
      const target = event.target as HTMLInputElement;
      if (target.type !== 'password') { // Don't track password inputs
        this.recordUserAction({
          type: 'input',
          target: this.getElementSelector(target),
          data: {
            inputType: target.type,
            valueLength: target.value?.length || 0
          }
        });
      }
    }, { passive: true });

    // Track navigation
    window.addEventListener('popstate', () => {
      this.recordUserAction({
        type: 'navigation',
        target: 'browser_back_forward',
        data: { url: window.location.href }
      });
    });
  }

  private setupNetworkErrorTracking(): void {
    if (typeof window === 'undefined') return;

    // Intercept fetch requests
    const originalFetch = window.fetch;
    window.fetch = async (...args) => {
      const startTime = performance.now();
      const url = typeof args[0] === 'string' ? args[0] : args[0].url;
      const method = args[1]?.method || 'GET';

      try {
        const response = await originalFetch(...args);
        const endTime = performance.now();
        const responseTime = endTime - startTime;

        // Log slow API calls
        if (responseTime > 5000) { // 5 second threshold
          this.reportPerformanceIssue({
            type: 'slow_api',
            metric: 'response_time',
            value: responseTime,
            threshold: 5000,
            impact: responseTime > 10000 ? 'critical' : 'high'
          });
        }

        // Log HTTP errors
        if (!response.ok) {
          this.reportNetworkError({
            url,
            method,
            status: response.status,
            statusText: response.statusText,
            responseTime,
            requestData: this.sanitizeRequestData(args[1])
          });
        }

        return response;
      } catch (error) {
        const endTime = performance.now();
        const responseTime = endTime - startTime;

        this.reportNetworkError({
          url,
          method,
          responseTime,
          requestData: this.sanitizeRequestData(args[1])
        });

        throw error;
      }
    };
  }

  private getElementSelector(element: Element): string {
    if (!element) return 'unknown';

    // Try to get a meaningful selector
    if (element.id) {
      return `#${element.id}`;
    }

    if (element.className) {
      const classes = element.className.split(' ').filter(c => c.length > 0);
      if (classes.length > 0) {
        return `.${classes[0]}`;
      }
    }

    return element.tagName.toLowerCase();
  }

  private sanitizeRequestData(requestInit?: RequestInit): any {
    if (!requestInit) return undefined;

    const sanitized: any = {
      method: requestInit.method,
      headers: requestInit.headers,
      mode: requestInit.mode,
      credentials: requestInit.credentials
    };

    // Don't include sensitive data
    if (requestInit.body && typeof requestInit.body === 'string') {
      try {
        const parsed = JSON.parse(requestInit.body);
        // Remove potential sensitive fields
        const sensitiveFields = ['password', 'token', 'apiKey', 'secret', 'authorization'];
        for (const field of sensitiveFields) {
          if (parsed[field]) {
            parsed[field] = '[REDACTED]';
          }
        }
        sanitized.body = parsed;
      } catch {
        sanitized.body = '[NON_JSON_BODY]';
      }
    }

    return sanitized;
  }

  // Public methods
  recordUserAction(action: Omit<UserAction, 'id' | 'timestamp' | 'route'>): void {
    const userAction: UserAction = {
      id: `action_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date(),
      route: window.location.pathname,
      ...action
    };

    this.userActions.push(userAction);

    // Maintain size limit
    if (this.userActions.length > this.maxUserActions) {
      this.userActions.shift();
    }

    logger.debug('ErrorTracking', 'User action recorded', userAction);
  }

  setErrorContext(key: string, context: Partial<ErrorContext>): void {
    const fullContext: ErrorContext = {
      timestamp: new Date(),
      sessionId: logger.getSessionId?.() || 'unknown',
      buildVersion: logger.getBuildVersion?.() || 'unknown',
      route: window.location.pathname,
      ...context
    };

    this.errorContexts.set(key, fullContext);
    logger.debug('ErrorTracking', 'Error context set', { key, context: fullContext });
  }

  clearErrorContext(key: string): void {
    this.errorContexts.delete(key);
    logger.debug('ErrorTracking', 'Error context cleared', { key });
  }

  reportError(
    error: Error, 
    context?: Partial<ErrorContext>, 
    boundaryInfo?: ErrorBoundaryInfo
  ): void {
    const errorId = `error_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    const fullContext: ErrorContext = {
      timestamp: new Date(),
      sessionId: logger.getSessionId?.() || 'unknown',
      buildVersion: logger.getBuildVersion?.() || 'unknown',
      route: window.location.pathname,
      ...context
    };

    // Gather all current contexts
    const allContexts = Array.from(this.errorContexts.values());
    
    // Get recent user actions
    const recentActions = this.userActions.slice(-10); // Last 10 actions

    const errorReport = {
      id: errorId,
      error: {
        name: error.name,
        message: error.message,
        stack: error.stack
      },
      context: fullContext,
      allContexts,
      recentActions,
      boundaryInfo,
      userAgent: navigator.userAgent,
      url: window.location.href,
      timestamp: new Date().toISOString()
    };

    // Log the error
    logger.error('ErrorTracking', `Error reported: ${error.message}`, errorReport);

    // Send to external error tracking service if configured
    this.sendToErrorTrackingService(errorReport);
  }

  reportNetworkError(networkError: NetworkError): void {
    const errorId = `network_error_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    const errorReport = {
      id: errorId,
      type: 'network_error',
      networkError,
      recentActions: this.userActions.slice(-5), // Last 5 actions
      timestamp: new Date().toISOString(),
      url: window.location.href
    };

    logger.error('ErrorTracking', `Network error: ${networkError.url}`, errorReport);
    this.sendToErrorTrackingService(errorReport);
  }

  reportPerformanceIssue(issue: PerformanceIssue): void {
    const issueId = `perf_issue_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    const issueReport = {
      id: issueId,
      type: 'performance_issue',
      issue,
      timestamp: new Date().toISOString(),
      url: window.location.href,
      userAgent: navigator.userAgent
    };

    const logLevel = issue.impact === 'critical' ? LogLevel.ERROR : LogLevel.WARN;
    logger.warn('ErrorTracking', `Performance issue: ${issue.type}`, issueReport);

    if (issue.impact === 'critical' || issue.impact === 'high') {
      this.sendToErrorTrackingService(issueReport);
    }
  }

  private async sendToErrorTrackingService(report: any): Promise<void> {
    try {
      // In a real implementation, this would send to services like Sentry, Bugsnag, etc.
      // For now, we'll store in localStorage and optionally send to a custom endpoint
      
      const errorReports = JSON.parse(localStorage.getItem('error_tracking_reports') || '[]');
      errorReports.push(report);
      
      // Keep only last 100 reports
      if (errorReports.length > 100) {
        errorReports.splice(0, errorReports.length - 100);
      }
      
      localStorage.setItem('error_tracking_reports', JSON.stringify(errorReports));

      // If external error tracking is enabled, send to endpoint
      const errorTrackingUrl = import.meta.env.VITE_ERROR_TRACKING_URL;
      if (errorTrackingUrl && import.meta.env.PROD) {
        await fetch(errorTrackingUrl, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(report)
        });
      }
    } catch (error) {
      logger.warn('ErrorTracking', 'Failed to send error report to external service', error);
    }
  }

  // Data retrieval methods
  getUserActions(limit?: number): UserAction[] {
    return limit ? this.userActions.slice(-limit) : [...this.userActions];
  }

  getErrorContexts(): Record<string, ErrorContext> {
    return Object.fromEntries(this.errorContexts);
  }

  // Export data for debugging
  exportErrorTrackingData(): string {
    return JSON.stringify({
      userActions: this.userActions,
      errorContexts: Object.fromEntries(this.errorContexts),
      timestamp: new Date().toISOString(),
      sessionId: logger.getSessionId?.() || 'unknown',
      buildVersion: logger.getBuildVersion?.() || 'unknown'
    }, null, 2);
  }

  // Cleanup
  cleanup(): void {
    if (this.performanceObserver) {
      this.performanceObserver.disconnect();
    }
    
    this.userActions = [];
    this.errorContexts.clear();
    
    logger.info('ErrorTracking', 'Error tracking service cleaned up');
  }
}

// Create singleton instance
export const errorTrackingService = new ErrorTrackingService();

// React Error Boundary helper
export const withErrorTracking = (Component: React.ComponentType<any>) => {
  return class ErrorTrackingWrapper extends React.Component<any, { hasError: boolean }> {
    constructor(props: any) {
      super(props);
      this.state = { hasError: false };
    }

    static getDerivedStateFromError(error: Error) {
      return { hasError: true };
    }

    componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
      errorTrackingService.reportError(error, {
        componentName: Component.name || 'Unknown',
        props: this.props
      }, {
        componentStack: errorInfo.componentStack,
        errorInfo
      });
    }

    render() {
      if (this.state.hasError) {
        return (
          <div className="error-boundary">
            <h2>Something went wrong.</h2>
            <p>An error occurred in this component. The error has been reported.</p>
          </div>
        );
      }

      return <Component {...this.props} />;
    }
  };
};

export default errorTrackingService;