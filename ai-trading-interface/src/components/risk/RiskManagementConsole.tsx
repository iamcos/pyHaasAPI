import React, { useState, useEffect } from 'react';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';
import { RiskExposureTracker } from './RiskExposureTracker';
import { RiskAlertsPanel } from './RiskAlertsPanel';
import { PortfolioCorrelationAnalysis } from './PortfolioCorrelationAnalysis';
import { AutomatedRiskManagementSystem } from './AutomatedRiskManagementSystem';
import { RiskMetrics, RiskVisualizationData } from '../../types/risk';
import { riskMonitoringService } from '../../services/riskMonitoringService';

interface RiskManagementConsoleProps {
  className?: string;
}

export const RiskManagementConsole: React.FC<RiskManagementConsoleProps> = ({ className }) => {
  const [activeTab, setActiveTab] = useState<'overview' | 'exposure' | 'alerts' | 'correlations' | 'automated' | 'visualization'>('overview');
  const [riskMetrics, setRiskMetrics] = useState<RiskMetrics | null>(null);
  const [visualizationData, setVisualizationData] = useState<RiskVisualizationData | null>(null);
  const [loading, setLoading] = useState(true);
  const [isMonitoring, setIsMonitoring] = useState(true);

  useEffect(() => {
    loadRiskData();
    
    const unsubscribe = riskMonitoringService.subscribe((data) => {
      if (data.type === 'risk_update') {
        // Refresh metrics when risk data updates
        loadRiskMetrics();
      }
    });

    return unsubscribe;
  }, []);

  const loadRiskData = async () => {
    try {
      setLoading(true);
      await Promise.all([
        loadRiskMetrics(),
        loadVisualizationData()
      ]);
    } catch (error) {
      console.error('Failed to load risk data:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadRiskMetrics = async () => {
    try {
      const metrics = await riskMonitoringService.getRiskMetrics();
      setRiskMetrics(metrics);
    } catch (error) {
      console.error('Failed to load risk metrics:', error);
    }
  };

  const loadVisualizationData = async () => {
    try {
      const data = await riskMonitoringService.getRiskVisualizationData();
      setVisualizationData(data);
    } catch (error) {
      console.error('Failed to load visualization data:', error);
    }
  };

  const toggleMonitoring = () => {
    if (isMonitoring) {
      riskMonitoringService.stopRealTimeMonitoring();
    } else {
      riskMonitoringService.startRealTimeMonitoring();
    }
    setIsMonitoring(!isMonitoring);
  };

  const formatCurrency = (value: number): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  };

  const formatPercentage = (value: number): string => {
    return `${(value * 100).toFixed(2)}%`;
  };

  const getRiskLevel = (value: number, thresholds: { low: number; medium: number; high: number }): string => {
    if (value >= thresholds.high) return 'High';
    if (value >= thresholds.medium) return 'Medium';
    return 'Low';
  };

  const getRiskColor = (level: string): string => {
    switch (level) {
      case 'High': return 'text-red-600 bg-red-50 border-red-200';
      case 'Medium': return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'Low': return 'text-green-600 bg-green-50 border-green-200';
      default: return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const tabs = [
    { id: 'overview', label: 'Overview', icon: '📊' },
    { id: 'exposure', label: 'Exposure Tracking', icon: '📈' },
    { id: 'alerts', label: 'Alerts', icon: '🚨' },
    { id: 'correlations', label: 'Correlations', icon: '🔗' },
    { id: 'automated', label: 'Automated Risk Mgmt', icon: '🤖' },
    { id: 'visualization', label: 'Visualization', icon: '📉' }
  ];

  const renderOverview = () => (
    <div className="space-y-6">
      {/* Risk Metrics Summary */}
      {riskMetrics && (
        <Card>
          <div className="p-6">
            <h4 className="text-lg font-semibold mb-4">Portfolio Risk Metrics</h4>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center p-4 bg-blue-50 rounded-lg">
                <div className="text-2xl font-bold text-blue-600">
                  {formatCurrency(riskMetrics.totalPortfolioValue)}
                </div>
                <div className="text-sm text-blue-600">Total Portfolio Value</div>
              </div>
              <div className="text-center p-4 bg-purple-50 rounded-lg">
                <div className="text-2xl font-bold text-purple-600">
                  {formatCurrency(riskMetrics.var95)}
                </div>
                <div className="text-sm text-purple-600">Value at Risk (95%)</div>
              </div>
              <div className="text-center p-4 bg-orange-50 rounded-lg">
                <div className="text-2xl font-bold text-orange-600">
                  {formatPercentage(riskMetrics.maxDrawdown)}
                </div>
                <div className="text-sm text-orange-600">Max Drawdown</div>
              </div>
              <div className="text-center p-4 bg-green-50 rounded-lg">
                <div className="text-2xl font-bold text-green-600">
                  {riskMetrics.sharpeRatio.toFixed(2)}
                </div>
                <div className="text-sm text-green-600">Sharpe Ratio</div>
              </div>
            </div>
          </div>
        </Card>
      )}

      {/* Risk Assessment */}
      {riskMetrics && (
        <Card>
          <div className="p-6">
            <h4 className="text-lg font-semibold mb-4">Risk Assessment</h4>
            <div className="space-y-4">
              <div className="flex items-center justify-between p-3 border rounded-lg">
                <div>
                  <span className="font-medium">Correlation Risk</span>
                  <p className="text-sm text-gray-600">Portfolio concentration in correlated assets</p>
                </div>
                <div className={`px-3 py-1 rounded-full text-sm font-medium border ${
                  getRiskColor(getRiskLevel(riskMetrics.correlationRisk, { low: 0.3, medium: 0.6, high: 0.8 }))
                }`}>
                  {getRiskLevel(riskMetrics.correlationRisk, { low: 0.3, medium: 0.6, high: 0.8 })}
                </div>
              </div>
              
              <div className="flex items-center justify-between p-3 border rounded-lg">
                <div>
                  <span className="font-medium">Concentration Risk</span>
                  <p className="text-sm text-gray-600">Single position exposure relative to portfolio</p>
                </div>
                <div className={`px-3 py-1 rounded-full text-sm font-medium border ${
                  getRiskColor(getRiskLevel(riskMetrics.concentrationRisk, { low: 0.2, medium: 0.4, high: 0.6 }))
                }`}>
                  {getRiskLevel(riskMetrics.concentrationRisk, { low: 0.2, medium: 0.4, high: 0.6 })}
                </div>
              </div>
              
              <div className="flex items-center justify-between p-3 border rounded-lg">
                <div>
                  <span className="font-medium">Liquidity Risk</span>
                  <p className="text-sm text-gray-600">Ability to exit positions quickly</p>
                </div>
                <div className={`px-3 py-1 rounded-full text-sm font-medium border ${
                  getRiskColor(getRiskLevel(riskMetrics.liquidityRisk, { low: 0.2, medium: 0.5, high: 0.8 }))
                }`}>
                  {getRiskLevel(riskMetrics.liquidityRisk, { low: 0.2, medium: 0.5, high: 0.8 })}
                </div>
              </div>
              
              <div className="flex items-center justify-between p-3 border rounded-lg">
                <div>
                  <span className="font-medium">Volatility Risk</span>
                  <p className="text-sm text-gray-600">Portfolio price volatility</p>
                </div>
                <div className={`px-3 py-1 rounded-full text-sm font-medium border ${
                  getRiskColor(getRiskLevel(riskMetrics.volatility, { low: 0.15, medium: 0.25, high: 0.4 }))
                }`}>
                  {getRiskLevel(riskMetrics.volatility, { low: 0.15, medium: 0.25, high: 0.4 })}
                </div>
              </div>
            </div>
          </div>
        </Card>
      )}

      {/* Quick Actions */}
      <Card>
        <div className="p-6">
          <h4 className="text-lg font-semibold mb-4">Quick Actions</h4>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Button
              variant="outline"
              onClick={() => setActiveTab('alerts')}
              className="h-16 flex flex-col items-center justify-center"
            >
              <span className="text-2xl mb-1">🚨</span>
              <span className="text-sm">View Alerts</span>
            </Button>
            <Button
              variant="outline"
              onClick={() => setActiveTab('exposure')}
              className="h-16 flex flex-col items-center justify-center"
            >
              <span className="text-2xl mb-1">📈</span>
              <span className="text-sm">Check Exposure</span>
            </Button>
            <Button
              variant="outline"
              onClick={() => setActiveTab('correlations')}
              className="h-16 flex flex-col items-center justify-center"
            >
              <span className="text-2xl mb-1">🔗</span>
              <span className="text-sm">Analyze Correlations</span>
            </Button>
            <Button
              variant="outline"
              onClick={loadRiskData}
              className="h-16 flex flex-col items-center justify-center"
            >
              <span className="text-2xl mb-1">🔄</span>
              <span className="text-sm">Refresh Data</span>
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );

  const renderVisualization = () => (
    <div className="space-y-6">
      {visualizationData && (
        <>
          {/* Exposure by Account */}
          <Card>
            <div className="p-6">
              <h4 className="text-lg font-semibold mb-4">Exposure by Account</h4>
              <div className="space-y-3">
                {visualizationData.exposureByAccount.map((item, index) => (
                  <div key={index} className="flex items-center justify-between">
                    <span className="font-medium">{item.account}</span>
                    <div className="flex items-center space-x-4">
                      <div className="w-32 bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-blue-500 h-2 rounded-full"
                          style={{ width: `${Math.min(100, item.percentage)}%` }}
                        ></div>
                      </div>
                      <span className="text-sm text-gray-600 w-16 text-right">
                        {item.percentage.toFixed(1)}%
                      </span>
                      <span className="text-sm font-medium w-24 text-right">
                        {formatCurrency(item.exposure)}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </Card>

          {/* Exposure by Asset */}
          <Card>
            <div className="p-6">
              <h4 className="text-lg font-semibold mb-4">Top Asset Exposures</h4>
              <div className="space-y-3">
                {visualizationData.exposureByAsset
                  .sort((a, b) => b.exposure - a.exposure)
                  .slice(0, 10)
                  .map((item, index) => (
                    <div key={index} className="flex items-center justify-between">
                      <span className="font-medium">{item.asset}</span>
                      <div className="flex items-center space-x-4">
                        <div className="w-32 bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-green-500 h-2 rounded-full"
                            style={{ width: `${Math.min(100, item.percentage)}%` }}
                          ></div>
                        </div>
                        <span className="text-sm text-gray-600 w-16 text-right">
                          {item.percentage.toFixed(1)}%
                        </span>
                        <span className="text-sm font-medium w-24 text-right">
                          {formatCurrency(item.exposure)}
                        </span>
                      </div>
                    </div>
                  ))}
              </div>
            </div>
          </Card>
        </>
      )}
    </div>
  );

  if (loading) {
    return (
      <div className={className}>
        <Card>
          <div className="p-6">
            <div className="animate-pulse">
              <div className="h-6 bg-gray-200 rounded w-1/3 mb-6"></div>
              <div className="grid grid-cols-4 gap-4 mb-6">
                {[1, 2, 3, 4].map(i => (
                  <div key={i} className="h-20 bg-gray-200 rounded"></div>
                ))}
              </div>
              <div className="space-y-4">
                {[1, 2, 3].map(i => (
                  <div key={i} className="h-16 bg-gray-200 rounded"></div>
                ))}
              </div>
            </div>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className={className}>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold">Risk Management Console</h2>
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <div className={`w-3 h-3 rounded-full ${isMonitoring ? 'bg-green-500' : 'bg-red-500'}`}></div>
            <span className="text-sm text-gray-600">
              {isMonitoring ? 'Monitoring Active' : 'Monitoring Paused'}
            </span>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={toggleMonitoring}
          >
            {isMonitoring ? 'Pause' : 'Resume'} Monitoring
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={loadRiskData}
          >
            Refresh
          </Button>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="-mb-px flex space-x-8">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`py-2 px-1 border-b-2 font-medium text-sm flex items-center space-x-2 ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <span>{tab.icon}</span>
              <span>{tab.label}</span>
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div>
        {activeTab === 'overview' && renderOverview()}
        {activeTab === 'exposure' && <RiskExposureTracker />}
        {activeTab === 'alerts' && <RiskAlertsPanel />}
        {activeTab === 'correlations' && <PortfolioCorrelationAnalysis />}
        {activeTab === 'automated' && <AutomatedRiskManagementSystem />}
        {activeTab === 'visualization' && renderVisualization()}
      </div>
    </div>
  );
};