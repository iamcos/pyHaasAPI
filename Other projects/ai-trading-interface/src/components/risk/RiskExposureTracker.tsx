import React, { useState, useEffect } from 'react';
import { Card } from '../ui/Card';
import { Alert } from '../ui/Alert';
import { RiskExposure, RiskAlert } from '../../types/risk';
import { riskMonitoringService } from '../../services/riskMonitoringService';

interface RiskExposureTrackerProps {
  className?: string;
}

export const RiskExposureTracker: React.FC<RiskExposureTrackerProps> = ({ className }) => {
  const [exposures, setExposures] = useState<RiskExposure[]>([]);
  const [alerts, setAlerts] = useState<RiskAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  useEffect(() => {
    const unsubscribe = riskMonitoringService.subscribe((data) => {
      if (data.type === 'risk_update') {
        setExposures(data.exposures);
        setAlerts(data.alerts);
        setLastUpdate(data.timestamp);
        setLoading(false);
      }
    });

    // Initial load
    loadRiskData();

    return unsubscribe;
  }, []);

  const loadRiskData = async () => {
    try {
      setLoading(true);
      await riskMonitoringService.performRiskAssessment();
      const activeAlerts = await riskMonitoringService.getActiveAlerts();
      setAlerts(activeAlerts);
    } catch (error) {
      console.error('Failed to load risk data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getExposureColor = (utilizationPercentage: number): string => {
    if (utilizationPercentage >= 0.8) return 'text-red-600';
    if (utilizationPercentage >= 0.6) return 'text-yellow-600';
    return 'text-green-600';
  };

  const getRiskScoreColor = (score: number): string => {
    if (score >= 80) return 'bg-red-500';
    if (score >= 60) return 'bg-yellow-500';
    if (score >= 40) return 'bg-blue-500';
    return 'bg-green-500';
  };

  const formatCurrency = (value: number): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(value);
  };

  const formatPercentage = (value: number): string => {
    return `${(value * 100).toFixed(2)}%`;
  };

  if (loading) {
    return (
      <Card className={className}>
        <div className="p-6">
          <div className="animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
            <div className="space-y-3">
              <div className="h-4 bg-gray-200 rounded"></div>
              <div className="h-4 bg-gray-200 rounded w-5/6"></div>
              <div className="h-4 bg-gray-200 rounded w-4/6"></div>
            </div>
          </div>
        </div>
      </Card>
    );
  }

  return (
    <div className={className}>
      {/* Critical Alerts */}
      {alerts.filter(alert => alert.severity === 'critical' && !alert.acknowledged).length > 0 && (
        <Alert variant="error" className="mb-4">
          <div className="flex items-center justify-between">
            <div>
              <h4 className="font-semibold">Critical Risk Alerts</h4>
              <p className="text-sm">
                {alerts.filter(alert => alert.severity === 'critical' && !alert.acknowledged).length} critical risk threshold(s) exceeded
              </p>
            </div>
            <button
              onClick={() => {/* Navigate to alerts */}}
              className="text-sm underline hover:no-underline"
            >
              View Details
            </button>
          </div>
        </Alert>
      )}

      {/* Risk Exposure Overview */}
      <Card>
        <div className="p-6">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-semibold">Risk Exposure Tracking</h3>
            <div className="text-sm text-gray-500">
              Last updated: {lastUpdate.toLocaleTimeString()}
            </div>
          </div>

          {/* Account Exposures */}
          <div className="space-y-4">
            {exposures.map((exposure) => (
              <div key={exposure.accountId} className="border rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="font-medium">{exposure.accountName}</h4>
                  <div className="flex items-center space-x-4">
                    <span className={`font-semibold ${getExposureColor(exposure.utilizationPercentage)}`}>
                      {formatPercentage(exposure.utilizationPercentage)}
                    </span>
                    <span className="text-sm text-gray-500">
                      {formatCurrency(exposure.totalExposure)} / {formatCurrency(exposure.maxExposure)}
                    </span>
                  </div>
                </div>

                {/* Exposure Bar */}
                <div className="w-full bg-gray-200 rounded-full h-2 mb-3">
                  <div
                    className={`h-2 rounded-full transition-all duration-300 ${
                      exposure.utilizationPercentage >= 0.8 ? 'bg-red-500' :
                      exposure.utilizationPercentage >= 0.6 ? 'bg-yellow-500' : 'bg-green-500'
                    }`}
                    style={{ width: `${Math.min(100, exposure.utilizationPercentage * 100)}%` }}
                  ></div>
                </div>

                {/* Risk Metrics */}
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-gray-500">Correlation Risk:</span>
                    <span className="ml-2 font-medium">{formatPercentage(exposure.correlationRisk)}</span>
                  </div>
                  <div>
                    <span className="text-gray-500">Concentration Risk:</span>
                    <span className="ml-2 font-medium">{formatPercentage(exposure.concentrationRisk)}</span>
                  </div>
                </div>

                {/* Top Positions */}
                {exposure.positions.length > 0 && (
                  <div className="mt-4">
                    <h5 className="text-sm font-medium mb-2">Top Risk Positions</h5>
                    <div className="space-y-2">
                      {exposure.positions
                        .sort((a, b) => b.riskScore - a.riskScore)
                        .slice(0, 3)
                        .map((position, index) => (
                          <div key={`${position.symbol}-${index}`} className="flex items-center justify-between text-sm">
                            <div className="flex items-center space-x-2">
                              <span className="font-medium">{position.symbol}</span>
                              <div className={`w-2 h-2 rounded-full ${getRiskScoreColor(position.riskScore)}`}></div>
                            </div>
                            <div className="flex items-center space-x-4">
                              <span className="text-gray-500">
                                {formatCurrency(position.value)}
                              </span>
                              <span className={position.unrealizedPnL >= 0 ? 'text-green-600' : 'text-red-600'}>
                                {formatCurrency(position.unrealizedPnL)}
                              </span>
                              <span className="text-gray-500">
                                Risk: {position.riskScore.toFixed(0)}
                              </span>
                            </div>
                          </div>
                        ))}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>

          {exposures.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              <p>No risk exposure data available</p>
              <button
                onClick={loadRiskData}
                className="mt-2 text-blue-600 hover:text-blue-800 underline"
              >
                Refresh Data
              </button>
            </div>
          )}
        </div>
      </Card>
    </div>
  );
};