/**
 * Monitoring Hook
 * Provides easy access to monitoring services and utilities
 */

import { useState, useEffect, useCallback } from 'react';
import { logger, LogLevel, LogEntry } from '../services/loggingService';
import { performanceMonitoringService, PerformanceAlert } from '../services/performanceMonitoringService';
import { errorTrackingService } from '../services/errorTrackingService';

export interface MonitoringState {
  logs: LogEntry[];
  alerts: PerformanceAlert[];
  isMonitoring: boolean;
  sessionId: string;
  buildVersion: string;
}

export interface MonitoringActions {
  startTimer: (name: string) => () => void;
  recordMetric: (name: string, value: number, unit?: string) => void;
  logInfo: (category: string, message: string, data?: any) => void;
  logWarn: (category: string, message: string, data?: any) => void;
  logError: (category: string, message: string, data?: any) => void;
  reportError: (error: Error, context?: any) => void;
  setErrorContext: (key: string, context: any) => void;
  clearErrorContext: (key: string) => void;
  exportLogs: () => string;
  clearLogs: () => void;
  refreshData: () => void;
}

export const useMonitoring = (autoRefresh: boolean = false): [MonitoringState, MonitoringActions] => {
  const [state, setState] = useState<MonitoringState>({
    logs: [],
    alerts: [],
    isMonitoring: true,
    sessionId: logger.getSessionId(),
    buildVersion: logger.getBuildVersion()
  });

  const refreshData = useCallback(() => {
    setState(prevState => ({
      ...prevState,
      logs: logger.getLogs(LogLevel.INFO, undefined, 100),
      alerts: performanceMonitoringService.getAlerts(undefined, 50)
    }));
  }, []);

  useEffect(() => {
    refreshData();

    if (autoRefresh) {
      const interval = setInterval(refreshData, 5000); // Refresh every 5 seconds
      return () => clearInterval(interval);
    }
  }, [autoRefresh, refreshData]);

  const actions: MonitoringActions = {
    startTimer: useCallback((name: string) => {
      return logger.startTimer(name);
    }, []),

    recordMetric: useCallback((name: string, value: number, unit: string = 'ms') => {
      logger.recordMetric(name, value, unit);
    }, []),

    logInfo: useCallback((category: string, message: string, data?: any) => {
      logger.info(category, message, data);
      if (autoRefresh) {
        setTimeout(refreshData, 100); // Small delay to ensure log is processed
      }
    }, [autoRefresh, refreshData]),

    logWarn: useCallback((category: string, message: string, data?: any) => {
      logger.warn(category, message, data);
      if (autoRefresh) {
        setTimeout(refreshData, 100);
      }
    }, [autoRefresh, refreshData]),

    logError: useCallback((category: string, message: string, data?: any) => {
      logger.error(category, message, data);
      if (autoRefresh) {
        setTimeout(refreshData, 100);
      }
    }, [autoRefresh, refreshData]),

    reportError: useCallback((error: Error, context?: any) => {
      errorTrackingService.reportError(error, context);
      if (autoRefresh) {
        setTimeout(refreshData, 100);
      }
    }, [autoRefresh, refreshData]),

    setErrorContext: useCallback((key: string, context: any) => {
      errorTrackingService.setErrorContext(key, context);
    }, []),

    clearErrorContext: useCallback((key: string) => {
      errorTrackingService.clearErrorContext(key);
    }, []),

    exportLogs: useCallback(() => {
      return logger.exportLogs();
    }, []),

    clearLogs: useCallback(() => {
      logger.clearLogs();
      refreshData();
    }, [refreshData]),

    refreshData
  };

  return [state, actions];
};

// Hook for component performance monitoring
export const useComponentPerformance = (componentName: string, props?: any) => {
  useEffect(() => {
    const startTime = performance.now();
    
    return () => {
      const endTime = performance.now();
      const renderTime = endTime - startTime;
      performanceMonitoringService.recordComponentPerformance(componentName, renderTime, props);
    };
  });
};

// Hook for API call monitoring
export const useApiMonitoring = () => {
  const monitorApiCall = useCallback(async <T>(
    name: string,
    apiCall: () => Promise<T>,
    context?: any
  ): Promise<T> => {
    const endTimer = logger.startTimer(`api_${name}`);
    
    try {
      errorTrackingService.setErrorContext(`api_${name}`, {
        apiName: name,
        ...context
      });

      const result = await apiCall();
      
      endTimer();
      logger.info('API', `API call successful: ${name}`, { context });
      
      return result;
    } catch (error) {
      endTimer();
      logger.error('API', `API call failed: ${name}`, { error, context });
      errorTrackingService.reportError(error as Error, {
        apiName: name,
        ...context
      });
      throw error;
    } finally {
      errorTrackingService.clearErrorContext(`api_${name}`);
    }
  }, []);

  return { monitorApiCall };
};

// Hook for user action tracking
export const useUserActionTracking = () => {
  const trackAction = useCallback((
    type: 'click' | 'input' | 'navigation' | 'custom',
    target: string,
    data?: any
  ) => {
    errorTrackingService.recordUserAction({
      type,
      target,
      data
    });
  }, []);

  const trackClick = useCallback((target: string, data?: any) => {
    trackAction('click', target, data);
  }, [trackAction]);

  const trackInput = useCallback((target: string, data?: any) => {
    trackAction('input', target, data);
  }, [trackAction]);

  const trackNavigation = useCallback((target: string, data?: any) => {
    trackAction('navigation', target, data);
  }, [trackAction]);

  return {
    trackAction,
    trackClick,
    trackInput,
    trackNavigation
  };
};

// Hook for performance thresholds
export const usePerformanceThresholds = () => {
  const setThreshold = useCallback((
    metric: string,
    warning: number,
    critical: number,
    unit: string = 'ms'
  ) => {
    performanceMonitoringService.setThreshold(metric, {
      metric,
      warning,
      critical,
      unit
    });
  }, []);

  const measureAsync = useCallback(async <T>(
    name: string,
    asyncFn: () => Promise<T>
  ): Promise<T> => {
    return performanceMonitoringService.measureAsync(name, asyncFn);
  }, []);

  const measureSync = useCallback(<T>(
    name: string,
    syncFn: () => T
  ): T => {
    return performanceMonitoringService.measureSync(name, syncFn);
  }, []);

  return {
    setThreshold,
    measureAsync,
    measureSync
  };
};

export default useMonitoring;