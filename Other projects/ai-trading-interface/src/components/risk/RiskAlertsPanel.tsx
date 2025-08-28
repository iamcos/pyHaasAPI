import React, { useState, useEffect } from 'react';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';
import { Alert } from '../ui/Alert';
import { RiskAlert, RiskThreshold } from '../../types/risk';
import { riskMonitoringService } from '../../services/riskMonitoringService';

interface RiskAlertsPanelProps {
  className?: string;
}

export const RiskAlertsPanel: React.FC<RiskAlertsPanelProps> = ({ className }) => {
  const [alerts, setAlerts] = useState<RiskAlert[]>([]);
  const [thresholds, setThresholds] = useState<RiskThreshold[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'critical' | 'high' | 'medium' | 'low'>('all');
  const [showAcknowledged, setShowAcknowledged] = useState(false);

  useEffect(() => {
    const unsubscribe = riskMonitoringService.subscribe((data) => {
      if (data.type === 'risk_update') {
        setAlerts(data.alerts);
      } else if (data.type === 'critical_alert') {
        // Handle critical alerts immediately
        setAlerts(prev => {
          const existing = prev.find(a => a.id === data.alert.id);
          if (existing) return prev;
          return [...prev, data.alert];
        });
        
        // Show browser notification for critical alerts
        if (Notification.permission === 'granted') {
          new Notification('Critical Risk Alert', {
            body: data.alert.message,
            icon: '/risk-icon.png'
          });
        }
      }
    });

    loadData();

    return unsubscribe;
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [alertsData, config] = await Promise.all([
        riskMonitoringService.getActiveAlerts(),
        riskMonitoringService.getRiskConfiguration()
      ]);
      
      setAlerts(alertsData);
      setThresholds(config.thresholds);
    } catch (error) {
      console.error('Failed to load risk alerts:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAcknowledgeAlert = async (alertId: string) => {
    try {
      await riskMonitoringService.acknowledgeAlert(alertId);
      setAlerts(prev => prev.map(alert => 
        alert.id === alertId ? { ...alert, acknowledged: true } : alert
      ));
    } catch (error) {
      console.error('Failed to acknowledge alert:', error);
    }
  };

  const getSeverityColor = (severity: string): string => {
    switch (severity) {
      case 'critical': return 'border-red-500 bg-red-50';
      case 'high': return 'border-orange-500 bg-orange-50';
      case 'medium': return 'border-yellow-500 bg-yellow-50';
      case 'low': return 'border-blue-500 bg-blue-50';
      default: return 'border-gray-500 bg-gray-50';
    }
  };

  const getSeverityIcon = (severity: string): string => {
    switch (severity) {
      case 'critical': return '🚨';
      case 'high': return '⚠️';
      case 'medium': return '⚡';
      case 'low': return 'ℹ️';
      default: return '📊';
    }
  };

  const filteredAlerts = alerts.filter(alert => {
    if (!showAcknowledged && alert.acknowledged) return false;
    if (filter !== 'all' && alert.severity !== filter) return false;
    return true;
  });

  const alertCounts = {
    critical: alerts.filter(a => a.severity === 'critical' && !a.acknowledged).length,
    high: alerts.filter(a => a.severity === 'high' && !a.acknowledged).length,
    medium: alerts.filter(a => a.severity === 'medium' && !a.acknowledged).length,
    low: alerts.filter(a => a.severity === 'low' && !a.acknowledged).length
  };

  if (loading) {
    return (
      <Card className={className}>
        <div className="p-6">
          <div className="animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-1/3 mb-4"></div>
            <div className="space-y-3">
              {[1, 2, 3].map(i => (
                <div key={i} className="h-16 bg-gray-200 rounded"></div>
              ))}
            </div>
          </div>
        </div>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <div className="p-6">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold">Risk Alerts & Notifications</h3>
          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={loadData}
              className="text-xs"
            >
              Refresh
            </Button>
          </div>
        </div>

        {/* Alert Summary */}
        <div className="grid grid-cols-4 gap-4 mb-6">
          <div className="text-center p-3 bg-red-50 rounded-lg border border-red-200">
            <div className="text-2xl font-bold text-red-600">{alertCounts.critical}</div>
            <div className="text-sm text-red-600">Critical</div>
          </div>
          <div className="text-center p-3 bg-orange-50 rounded-lg border border-orange-200">
            <div className="text-2xl font-bold text-orange-600">{alertCounts.high}</div>
            <div className="text-sm text-orange-600">High</div>
          </div>
          <div className="text-center p-3 bg-yellow-50 rounded-lg border border-yellow-200">
            <div className="text-2xl font-bold text-yellow-600">{alertCounts.medium}</div>
            <div className="text-sm text-yellow-600">Medium</div>
          </div>
          <div className="text-center p-3 bg-blue-50 rounded-lg border border-blue-200">
            <div className="text-2xl font-bold text-blue-600">{alertCounts.low}</div>
            <div className="text-sm text-blue-600">Low</div>
          </div>
        </div>

        {/* Filters */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
            <label className="text-sm font-medium">Filter:</label>
            <select
              value={filter}
              onChange={(e) => setFilter(e.target.value as any)}
              className="text-sm border border-gray-300 rounded px-2 py-1"
            >
              <option value="all">All Severities</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </div>
          <div className="flex items-center space-x-2">
            <input
              type="checkbox"
              id="showAcknowledged"
              checked={showAcknowledged}
              onChange={(e) => setShowAcknowledged(e.target.checked)}
              className="rounded"
            />
            <label htmlFor="showAcknowledged" className="text-sm">
              Show acknowledged
            </label>
          </div>
        </div>

        {/* Alerts List */}
        <div className="space-y-3 max-h-96 overflow-y-auto">
          {filteredAlerts.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <p>No alerts match the current filter</p>
            </div>
          ) : (
            filteredAlerts.map((alert) => (
              <div
                key={alert.id}
                className={`border-l-4 p-4 rounded-r-lg ${getSeverityColor(alert.severity)} ${
                  alert.acknowledged ? 'opacity-60' : ''
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-2">
                      <span className="text-lg">{getSeverityIcon(alert.severity)}</span>
                      <span className="font-medium capitalize">{alert.severity}</span>
                      <span className="text-sm text-gray-500">
                        {alert.timestamp.toLocaleString()}
                      </span>
                      {alert.acknowledged && (
                        <span className="text-xs bg-gray-200 text-gray-600 px-2 py-1 rounded">
                          Acknowledged
                        </span>
                      )}
                    </div>
                    <p className="text-sm mb-2">{alert.message}</p>
                    <div className="text-xs text-gray-600 space-x-4">
                      <span>Account: {alert.accountId}</span>
                      {alert.symbol && <span>Symbol: {alert.symbol}</span>}
                      <span>
                        Current: {(alert.currentValue * 100).toFixed(2)}% | 
                        Threshold: {(alert.thresholdValue * 100).toFixed(2)}%
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2 ml-4">
                    {!alert.acknowledged && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleAcknowledgeAlert(alert.id)}
                        className="text-xs"
                      >
                        Acknowledge
                      </Button>
                    )}
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {/* Navigate to detailed view */}}
                      className="text-xs"
                    >
                      Details
                    </Button>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Request notification permission */}
        {Notification.permission === 'default' && (
          <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-blue-800">Enable Browser Notifications</p>
                <p className="text-xs text-blue-600">Get instant alerts for critical risk events</p>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => Notification.requestPermission()}
                className="text-xs"
              >
                Enable
              </Button>
            </div>
          </div>
        )}
      </div>
    </Card>
  );
};