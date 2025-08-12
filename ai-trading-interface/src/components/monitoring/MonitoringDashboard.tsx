/**
 * Monitoring Dashboard Component
 * Displays real-time monitoring data, logs, and performance metrics
 */

import React, { useState, useEffect } from 'react';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';
import { logger, LogLevel, LogEntry } from '../../services/loggingService';
import { performanceMonitoringService, PerformanceAlert } from '../../services/performanceMonitoringService';
import { errorTrackingService } from '../../services/errorTrackingService';

interface MonitoringDashboardProps {
  isOpen: boolean;
  onClose: () => void;
}

export const MonitoringDashboard: React.FC<MonitoringDashboardProps> = ({
  isOpen,
  onClose
}) => {
  const [activeTab, setActiveTab] = useState<'logs' | 'performance' | 'errors' | 'system'>('logs');
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [alerts, setAlerts] = useState<PerformanceAlert[]>([]);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [logLevel, setLogLevel] = useState<LogLevel>(LogLevel.INFO);

  useEffect(() => {
    if (!isOpen) return;

    const refreshData = () => {
      setLogs(logger.getLogs(logLevel, undefined, 100));
      setAlerts(performanceMonitoringService.getAlerts(undefined, 50));
    };

    refreshData();

    let interval: number | undefined;
    if (autoRefresh) {
      interval = window.setInterval(refreshData, 2000); // Refresh every 2 seconds
    }

    return () => {
      if (interval) {
        clearInterval(interval);
      }
    };
  }, [isOpen, autoRefresh, logLevel]);

  if (!isOpen) return null;

  const renderLogsTab = () => (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <select
            value={logLevel}
            onChange={(e) => setLogLevel(Number(e.target.value) as LogLevel)}
            className="px-3 py-1 border border-gray-300 rounded-md text-sm"
          >
            <option value={LogLevel.DEBUG}>Debug</option>
            <option value={LogLevel.INFO}>Info</option>
            <option value={LogLevel.WARN}>Warning</option>
            <option value={LogLevel.ERROR}>Error</option>
            <option value={LogLevel.CRITICAL}>Critical</option>
          </select>
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="rounded"
            />
            <span className="text-sm">Auto refresh</span>
          </label>
        </div>
        <div className="flex space-x-2">
          <Button
            onClick={() => setLogs(logger.getLogs(logLevel, undefined, 100))}
            size="sm"
            variant="outline"
          >
            Refresh
          </Button>
          <Button
            onClick={() => {
              logger.clearLogs();
              setLogs([]);
            }}
            size="sm"
            variant="outline"
          >
            Clear
          </Button>
        </div>
      </div>

      <div className="bg-black text-green-400 p-4 rounded-lg font-mono text-xs max-h-96 overflow-y-auto">
        {logs.length === 0 ? (
          <div className="text-gray-500">No logs available</div>
        ) : (
          logs.slice(-50).map((log) => (
            <div key={log.id} className="mb-1">
              <span className="text-gray-400">
                {log.timestamp.toLocaleTimeString()}
              </span>
              <span className={`ml-2 ${getLogLevelColor(log.level)}`}>
                [{LogLevel[log.level]}]
              </span>
              <span className="ml-2 text-blue-400">[{log.category}]</span>
              <span className="ml-2">{log.message}</span>
              {log.data && (
                <div className="ml-8 text-gray-300">
                  {JSON.stringify(log.data, null, 2)}
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );

  const renderPerformanceTab = () => {
    const resourceUsage = performanceMonitoringService.getResourceUsageHistory(10);
    const componentPerformance = performanceMonitoringService.getComponentPerformance();

    return (
      <div className="space-y-6">
        {/* Performance Alerts */}
        <Card>
          <div className="p-4">
            <h3 className="text-lg font-semibold mb-4">Performance Alerts</h3>
            {alerts.length === 0 ? (
              <div className="text-gray-500">No performance alerts</div>
            ) : (
              <div className="space-y-2">
                {alerts.slice(-10).map((alert) => (
                  <div
                    key={alert.id}
                    className={`p-3 rounded-lg ${
                      alert.severity === 'critical'
                        ? 'bg-red-50 border border-red-200'
                        : 'bg-yellow-50 border border-yellow-200'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <span className={`font-semibold ${
                          alert.severity === 'critical' ? 'text-red-800' : 'text-yellow-800'
                        }`}>
                          {alert.metric}
                        </span>
                        <span className="ml-2 text-sm text-gray-600">
                          {alert.value.toFixed(2)} (threshold: {alert.threshold})
                        </span>
                      </div>
                      <span className="text-xs text-gray-500">
                        {alert.timestamp.toLocaleTimeString()}
                      </span>
                    </div>
                    {alert.component && (
                      <div className="text-sm text-gray-600 mt-1">
                        Component: {alert.component}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </Card>

        {/* Resource Usage */}
        <Card>
          <div className="p-4">
            <h3 className="text-lg font-semibold mb-4">Resource Usage</h3>
            {resourceUsage.length === 0 ? (
              <div className="text-gray-500">No resource usage data</div>
            ) : (
              <div className="space-y-4">
                {resourceUsage.slice(-5).map((usage, index) => (
                  <div key={index} className="border-b border-gray-200 pb-2">
                    <div className="text-sm text-gray-600 mb-2">
                      {usage.timestamp.toLocaleString()}
                    </div>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <div className="font-medium">Memory</div>
                        <div>Used: {formatBytes(usage.memory.used)}</div>
                        <div>Total: {formatBytes(usage.memory.total)}</div>
                        <div>Limit: {formatBytes(usage.memory.limit)}</div>
                      </div>
                      <div>
                        <div className="font-medium">Network</div>
                        <div>Type: {usage.network.effectiveType || 'Unknown'}</div>
                        <div>Downlink: {usage.network.downlink || 'Unknown'} Mbps</div>
                        <div>RTT: {usage.network.rtt || 'Unknown'} ms</div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </Card>

        {/* Component Performance */}
        <Card>
          <div className="p-4">
            <h3 className="text-lg font-semibold mb-4">Component Performance</h3>
            {componentPerformance.length === 0 ? (
              <div className="text-gray-500">No component performance data</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-200">
                      <th className="text-left py-2">Component</th>
                      <th className="text-left py-2">Renders</th>
                      <th className="text-left py-2">Avg Time</th>
                      <th className="text-left py-2">Last Render</th>
                    </tr>
                  </thead>
                  <tbody>
                    {componentPerformance
                      .sort((a, b) => b.averageRenderTime - a.averageRenderTime)
                      .slice(0, 20)
                      .map((comp) => (
                        <tr key={comp.componentName} className="border-b border-gray-100">
                          <td className="py-2">{comp.componentName}</td>
                          <td className="py-2">{comp.renderCount}</td>
                          <td className="py-2">
                            <span className={
                              comp.averageRenderTime > 16 ? 'text-red-600' :
                              comp.averageRenderTime > 8 ? 'text-yellow-600' : 'text-green-600'
                            }>
                              {comp.averageRenderTime.toFixed(2)}ms
                            </span>
                          </td>
                          <td className="py-2">{comp.lastRender.toLocaleTimeString()}</td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </Card>
      </div>
    );
  };

  const renderErrorsTab = () => {
    const errorReports = logger.getErrorReports(undefined, 50);
    const userActions = errorTrackingService.getUserActions(20);

    return (
      <div className="space-y-6">
        {/* Error Reports */}
        <Card>
          <div className="p-4">
            <h3 className="text-lg font-semibold mb-4">Error Reports</h3>
            {errorReports.length === 0 ? (
              <div className="text-gray-500">No error reports</div>
            ) : (
              <div className="space-y-4">
                {errorReports.slice(-10).map((report) => (
                  <div key={report.id} className="border border-red-200 rounded-lg p-4 bg-red-50">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-semibold text-red-800">
                        {report.error.name}: {report.error.message}
                      </span>
                      <span className="text-xs text-gray-500">
                        {report.timestamp.toLocaleString()}
                      </span>
                    </div>
                    <div className="text-sm text-gray-600 mb-2">
                      URL: {report.url}
                    </div>
                    {report.stackTrace && (
                      <details className="text-xs">
                        <summary className="cursor-pointer text-gray-600">Stack Trace</summary>
                        <pre className="mt-2 p-2 bg-gray-100 rounded overflow-x-auto">
                          {report.stackTrace}
                        </pre>
                      </details>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </Card>

        {/* User Actions */}
        <Card>
          <div className="p-4">
            <h3 className="text-lg font-semibold mb-4">Recent User Actions</h3>
            {userActions.length === 0 ? (
              <div className="text-gray-500">No user actions recorded</div>
            ) : (
              <div className="space-y-2">
                {userActions.slice(-15).map((action) => (
                  <div key={action.id} className="flex items-center justify-between text-sm">
                    <div>
                      <span className="font-medium">{action.type}</span>
                      <span className="ml-2 text-gray-600">{action.target}</span>
                    </div>
                    <span className="text-xs text-gray-500">
                      {action.timestamp.toLocaleTimeString()}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </Card>
      </div>
    );
  };

  const renderSystemTab = () => {
    const performanceReport = performanceMonitoringService.getPerformanceReport();
    const sessionId = logger.getSessionId();
    const buildVersion = logger.getBuildVersion();

    return (
      <div className="space-y-6">
        {/* System Information */}
        <Card>
          <div className="p-4">
            <h3 className="text-lg font-semibold mb-4">System Information</h3>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <div className="font-medium">Session ID</div>
                <div className="text-gray-600">{sessionId}</div>
              </div>
              <div>
                <div className="font-medium">Build Version</div>
                <div className="text-gray-600">{buildVersion}</div>
              </div>
              <div>
                <div className="font-medium">Platform</div>
                <div className="text-gray-600">{navigator.platform}</div>
              </div>
              <div>
                <div className="font-medium">User Agent</div>
                <div className="text-gray-600 truncate">{navigator.userAgent}</div>
              </div>
            </div>
          </div>
        </Card>

        {/* Export Data */}
        <Card>
          <div className="p-4">
            <h3 className="text-lg font-semibold mb-4">Export Data</h3>
            <div className="space-y-2">
              <Button
                onClick={() => {
                  const data = logger.exportLogs();
                  downloadData(data, `logs-${Date.now()}.json`);
                }}
                variant="outline"
                size="sm"
              >
                Export Logs
              </Button>
              <Button
                onClick={() => {
                  const data = errorTrackingService.exportErrorTrackingData();
                  downloadData(data, `error-tracking-${Date.now()}.json`);
                }}
                variant="outline"
                size="sm"
              >
                Export Error Tracking Data
              </Button>
              <Button
                onClick={() => {
                  const data = JSON.stringify(performanceReport, null, 2);
                  downloadData(data, `performance-report-${Date.now()}.json`);
                }}
                variant="outline"
                size="sm"
              >
                Export Performance Report
              </Button>
            </div>
          </div>
        </Card>
      </div>
    );
  };

  const getLogLevelColor = (level: LogLevel): string => {
    switch (level) {
      case LogLevel.DEBUG: return 'text-gray-400';
      case LogLevel.INFO: return 'text-blue-400';
      case LogLevel.WARN: return 'text-yellow-400';
      case LogLevel.ERROR: return 'text-red-400';
      case LogLevel.CRITICAL: return 'text-red-600';
      default: return 'text-gray-400';
    }
  };

  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const downloadData = (data: string, filename: string): void => {
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-6xl h-5/6 flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <h2 className="text-xl font-semibold">Monitoring Dashboard</h2>
          <Button onClick={onClose} variant="outline" size="sm">
            Close
          </Button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-gray-200">
          {[
            { key: 'logs', label: 'Logs' },
            { key: 'performance', label: 'Performance' },
            { key: 'errors', label: 'Errors' },
            { key: 'system', label: 'System' }
          ].map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key as any)}
              className={`px-4 py-2 text-sm font-medium ${
                activeTab === tab.key
                  ? 'text-blue-600 border-b-2 border-blue-600'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4">
          {activeTab === 'logs' && renderLogsTab()}
          {activeTab === 'performance' && renderPerformanceTab()}
          {activeTab === 'errors' && renderErrorsTab()}
          {activeTab === 'system' && renderSystemTab()}
        </div>
      </div>
    </div>
  );
};

export default MonitoringDashboard;