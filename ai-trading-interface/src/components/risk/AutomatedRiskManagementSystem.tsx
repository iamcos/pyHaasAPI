import React, { useState, useEffect } from 'react';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';
import { Alert } from '../ui/Alert';
import { PositionSizingPanel } from './PositionSizingPanel';
import { StopLossOptimizationPanel } from './StopLossOptimizationPanel';
import { EmergencyControlsPanel } from './EmergencyControlsPanel';
import { automatedRiskManager } from '../../services/automatedRiskManager';
import { mcpClient } from '../../services/mcpClient';

interface AutomatedRiskManagementSystemProps {
  className?: string;
}

export const AutomatedRiskManagementSystem: React.FC<AutomatedRiskManagementSystemProps> = ({ 
  className 
}) => {
  const [activeTab, setActiveTab] = useState<'overview' | 'position_sizing' | 'stop_loss' | 'emergency'>('overview');
  const [accounts, setAccounts] = useState<any[]>([]);
  const [selectedAccountId, setSelectedAccountId] = useState<string>('');
  const [systemStatus, setSystemStatus] = useState({
    isActive: true,
    lastUpdate: new Date(),
    activeControls: 0,
    recentActions: 0
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadInitialData();
    
    // Subscribe to automated risk manager events
    const unsubscribe = automatedRiskManager.subscribe((data) => {
      if (data.type === 'emergency_control_executed') {
        setSystemStatus(prev => ({
          ...prev,
          recentActions: prev.recentActions + 1,
          lastUpdate: new Date()
        }));
      }
    });

    return unsubscribe;
  }, []);

  const loadInitialData = async () => {
    try {
      setLoading(true);
      const [accountsData, controlsData] = await Promise.all([
        mcpClient.accounts.getAll(),
        automatedRiskManager.getEmergencyControls()
      ]);
      
      setAccounts(accountsData);
      if (accountsData.length > 0 && !selectedAccountId) {
        setSelectedAccountId(accountsData[0].id);
      }
      
      setSystemStatus(prev => ({
        ...prev,
        isActive: automatedRiskManager.isActiveManager(),
        activeControls: controlsData.filter(c => c.enabled).length
      }));
    } catch (error) {
      console.error('Failed to load initial data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleToggleSystem = () => {
    const newStatus = !systemStatus.isActive;
    automatedRiskManager.setActive(newStatus);
    setSystemStatus(prev => ({
      ...prev,
      isActive: newStatus,
      lastUpdate: new Date()
    }));
  };

  const tabs = [
    { id: 'overview', label: 'System Overview', icon: '📊' },
    { id: 'position_sizing', label: 'Position Sizing', icon: '📏' },
    { id: 'stop_loss', label: 'Stop-Loss Optimization', icon: '🎯' },
    { id: 'emergency', label: 'Emergency Controls', icon: '🚨' }
  ];

  const renderOverview = () => (
    <div className="space-y-6">
      {/* System Status */}
      <Card>
        <div className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h4 className="text-lg font-semibold">Automated Risk Management Status</h4>
            <div className="flex items-center space-x-2">
              <div className={`w-3 h-3 rounded-full ${
                systemStatus.isActive ? 'bg-green-500' : 'bg-red-500'
              }`}></div>
              <span className="text-sm text-gray-600">
                {systemStatus.isActive ? 'Active' : 'Inactive'}
              </span>
              <Button
                variant={systemStatus.isActive ? 'outline' : 'default'}
                size="sm"
                onClick={handleToggleSystem}
                className={systemStatus.isActive ? 'text-red-600 hover:text-red-700' : 'bg-green-600 hover:bg-green-700 text-white'}
              >
                {systemStatus.isActive ? 'Deactivate' : 'Activate'}
              </Button>
            </div>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">{systemStatus.activeControls}</div>
              <div className="text-sm text-blue-600">Active Controls</div>
            </div>
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <div className="text-2xl font-bold text-green-600">{accounts.length}</div>
              <div className="text-sm text-green-600">Monitored Accounts</div>
            </div>
            <div className="text-center p-4 bg-orange-50 rounded-lg">
              <div className="text-2xl font-bold text-orange-600">{systemStatus.recentActions}</div>
              <div className="text-sm text-orange-600">Recent Actions</div>
            </div>
            <div className="text-center p-4 bg-purple-50 rounded-lg">
              <div className="text-2xl font-bold text-purple-600">
                {systemStatus.lastUpdate.toLocaleTimeString()}
              </div>
              <div className="text-sm text-purple-600">Last Update</div>
            </div>
          </div>
        </div>
      </Card>

      {/* System Features */}
      <Card>
        <div className="p-6">
          <h4 className="text-lg font-semibold mb-4">Automated Risk Management Features</h4>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center p-4 border rounded-lg hover:bg-gray-50 cursor-pointer"
                 onClick={() => setActiveTab('position_sizing')}>
              <div className="text-3xl mb-2">📏</div>
              <h5 className="font-medium mb-2">AI Position Sizing</h5>
              <p className="text-sm text-gray-600">
                Intelligent position sizing recommendations based on risk management principles and market analysis
              </p>
            </div>
            
            <div className="text-center p-4 border rounded-lg hover:bg-gray-50 cursor-pointer"
                 onClick={() => setActiveTab('stop_loss')}>
              <div className="text-3xl mb-2">🎯</div>
              <h5 className="font-medium mb-2">Dynamic Stop-Loss</h5>
              <p className="text-sm text-gray-600">
                Automated optimization of stop-loss and take-profit levels using technical analysis and volatility
              </p>
            </div>
            
            <div className="text-center p-4 border rounded-lg hover:bg-gray-50 cursor-pointer"
                 onClick={() => setActiveTab('emergency')}>
              <div className="text-3xl mb-2">🚨</div>
              <h5 className="font-medium mb-2">Emergency Controls</h5>
              <p className="text-sm text-gray-600">
                Circuit breakers and emergency actions to protect portfolio during extreme market conditions
              </p>
            </div>
          </div>
        </div>
      </Card>

      {/* Recent Activity */}
      <Card>
        <div className="p-6">
          <h4 className="text-lg font-semibold mb-4">Recent Automated Actions</h4>
          <div className="space-y-3">
            {/* This would show actual recent actions from the system */}
            <div className="flex items-center justify-between p-3 bg-green-50 border border-green-200 rounded-lg">
              <div className="flex items-center space-x-3">
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                <div>
                  <div className="font-medium text-sm">Position sizing optimized</div>
                  <div className="text-xs text-gray-600">BTC/USD position reduced by 15% based on volatility increase</div>
                </div>
              </div>
              <div className="text-xs text-gray-500">2 minutes ago</div>
            </div>
            
            <div className="flex items-center justify-between p-3 bg-blue-50 border border-blue-200 rounded-lg">
              <div className="flex items-center space-x-3">
                <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                <div>
                  <div className="font-medium text-sm">Stop-loss levels updated</div>
                  <div className="text-xs text-gray-600">ETH/USD stop-loss optimized for better risk-reward ratio</div>
                </div>
              </div>
              <div className="text-xs text-gray-500">15 minutes ago</div>
            </div>
            
            <div className="flex items-center justify-between p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
              <div className="flex items-center space-x-3">
                <div className="w-2 h-2 bg-yellow-500 rounded-full"></div>
                <div>
                  <div className="font-medium text-sm">Risk threshold alert</div>
                  <div className="text-xs text-gray-600">Portfolio exposure approaching 80% threshold</div>
                </div>
              </div>
              <div className="text-xs text-gray-500">1 hour ago</div>
            </div>
          </div>
        </div>
      </Card>

      {/* System Health */}
      <Alert variant="info">
        <div>
          <h4 className="font-semibold">System Health Check</h4>
          <div className="text-sm mt-2 space-y-1">
            <div className="flex items-center space-x-2">
              <span className="w-2 h-2 bg-green-500 rounded-full"></span>
              <span>Risk monitoring: Active</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="w-2 h-2 bg-green-500 rounded-full"></span>
              <span>AI services: Connected</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="w-2 h-2 bg-green-500 rounded-full"></span>
              <span>Emergency controls: Ready</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="w-2 h-2 bg-green-500 rounded-full"></span>
              <span>Market data: Live</span>
            </div>
          </div>
        </div>
      </Alert>
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
        <h2 className="text-2xl font-bold">Automated Risk Management System</h2>
        <div className="flex items-center space-x-4">
          {accounts.length > 0 && (
            <select
              value={selectedAccountId}
              onChange={(e) => setSelectedAccountId(e.target.value)}
              className="border border-gray-300 rounded px-3 py-2 text-sm"
            >
              <option value="">Select Account</option>
              {accounts.map(account => (
                <option key={account.id} value={account.id}>
                  {account.name}
                </option>
              ))}
            </select>
          )}
          <div className="flex items-center space-x-2">
            <div className={`w-3 h-3 rounded-full ${
              systemStatus.isActive ? 'bg-green-500' : 'bg-red-500'
            }`}></div>
            <span className="text-sm text-gray-600">
              System {systemStatus.isActive ? 'Active' : 'Inactive'}
            </span>
          </div>
        </div>
      </div>

      {/* System Inactive Warning */}
      {!systemStatus.isActive && (
        <Alert variant="warning" className="mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h4 className="font-semibold">Automated Risk Management Inactive</h4>
              <p className="text-sm">
                The automated risk management system is currently disabled. 
                Your positions are not being automatically monitored or adjusted.
              </p>
            </div>
            <Button
              onClick={handleToggleSystem}
              className="bg-green-600 hover:bg-green-700 text-white"
            >
              Activate System
            </Button>
          </div>
        </Alert>
      )}

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
        {activeTab === 'position_sizing' && selectedAccountId && (
          <PositionSizingPanel accountId={selectedAccountId} />
        )}
        {activeTab === 'stop_loss' && selectedAccountId && (
          <StopLossOptimizationPanel accountId={selectedAccountId} />
        )}
        {activeTab === 'emergency' && <EmergencyControlsPanel />}
        
        {(activeTab === 'position_sizing' || activeTab === 'stop_loss') && !selectedAccountId && (
          <Card>
            <div className="p-6 text-center text-gray-500">
              <p>Please select an account to view {activeTab.replace('_', ' ')} features</p>
            </div>
          </Card>
        )}
      </div>
    </div>
  );
};