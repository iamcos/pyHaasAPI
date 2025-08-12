import React, { useState, useEffect } from 'react';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';
import { Modal } from '../ui/Modal';
import { Alert } from '../ui/Alert';
import { EmergencyControl, EmergencyAction } from '../../types/risk';
import { automatedRiskManager } from '../../services/automatedRiskManager';

interface EmergencyControlsPanelProps {
  className?: string;
}

export const EmergencyControlsPanel: React.FC<EmergencyControlsPanelProps> = ({ className }) => {
  const [controls, setControls] = useState<EmergencyControl[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showTestModal, setShowTestModal] = useState(false);
  const [selectedControl, setSelectedControl] = useState<EmergencyControl | null>(null);
  const [testResults, setTestResults] = useState<any>(null);

  useEffect(() => {
    loadControls();
    
    // Subscribe to emergency control executions
    const unsubscribe = automatedRiskManager.subscribe((data) => {
      if (data.type === 'emergency_control_executed') {
        // Refresh controls and show notification
        loadControls();
        alert(`Emergency control executed: ${data.control.name}`);
      }
    });

    return unsubscribe;
  }, []);

  const loadControls = async () => {
    try {
      setLoading(true);
      const data = await automatedRiskManager.getEmergencyControls();
      setControls(data);
    } catch (error) {
      console.error('Failed to load emergency controls:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleToggleControl = async (controlId: string, enabled: boolean) => {
    try {
      await automatedRiskManager.updateEmergencyControl(controlId, { enabled });
      setControls(prev => prev.map(control => 
        control.id === controlId ? { ...control, enabled } : control
      ));
    } catch (error) {
      console.error('Failed to toggle emergency control:', error);
    }
  };

  const handleTestControl = async (control: EmergencyControl) => {
    try {
      setSelectedControl(control);
      setTestResults(null);
      setShowTestModal(true);
      
      const results = await automatedRiskManager.testEmergencyControl(control.id);
      setTestResults(results);
    } catch (error) {
      console.error('Failed to test emergency control:', error);
      setTestResults({ error: error instanceof Error ? error.message : 'Unknown error' });
    }
  };

  const handleDeleteControl = async (controlId: string) => {
    if (!confirm('Are you sure you want to delete this emergency control?')) {
      return;
    }

    try {
      await automatedRiskManager.removeEmergencyControl(controlId);
      setControls(prev => prev.filter(control => control.id !== controlId));
    } catch (error) {
      console.error('Failed to delete emergency control:', error);
    }
  };

  const getControlTypeIcon = (type: string): string => {
    switch (type) {
      case 'stop_all_bots': return '🛑';
      case 'close_all_positions': return '❌';
      case 'reduce_exposure': return '📉';
      case 'custom': return '⚙️';
      default: return '🔧';
    }
  };

  const getControlTypeColor = (type: string): string => {
    switch (type) {
      case 'stop_all_bots': return 'bg-red-100 text-red-800 border-red-200';
      case 'close_all_positions': return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'reduce_exposure': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'custom': return 'bg-blue-100 text-blue-800 border-blue-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getSeverityColor = (severity: string): string => {
    switch (severity) {
      case 'critical': return 'text-red-600';
      case 'high': return 'text-orange-600';
      case 'medium': return 'text-yellow-600';
      case 'low': return 'text-blue-600';
      default: return 'text-gray-600';
    }
  };

  const formatLastTriggered = (date?: Date): string => {
    if (!date) return 'Never';
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / (1000 * 60));
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (days > 0) return `${days} day${days > 1 ? 's' : ''} ago`;
    if (hours > 0) return `${hours} hour${hours > 1 ? 's' : ''} ago`;
    if (minutes > 0) return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
    return 'Just now';
  };

  if (loading) {
    return (
      <Card className={className}>
        <div className="p-6">
          <div className="animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-1/3 mb-4"></div>
            <div className="space-y-4">
              {[1, 2, 3].map(i => (
                <div key={i} className="h-24 bg-gray-200 rounded"></div>
              ))}
            </div>
          </div>
        </div>
      </Card>
    );
  }

  return (
    <>
      <Card className={className}>
        <div className="p-6">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-semibold">Emergency Controls & Circuit Breakers</h3>
            <div className="flex items-center space-x-2">
              <Button
                onClick={() => setShowCreateModal(true)}
                className="bg-blue-600 hover:bg-blue-700 text-white"
                size="sm"
              >
                Create Control
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={loadControls}
              >
                Refresh
              </Button>
            </div>
          </div>

          {/* System Status */}
          <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                <span className="font-medium text-green-800">Emergency System Active</span>
              </div>
              <div className="text-sm text-green-600">
                {controls.filter(c => c.enabled).length} of {controls.length} controls enabled
              </div>
            </div>
          </div>

          {controls.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <p>No emergency controls configured</p>
              <p className="text-sm">Create emergency controls to automatically manage risk during critical situations</p>
            </div>
          ) : (
            <div className="space-y-4">
              {controls.map((control) => (
                <div
                  key={control.id}
                  className={`border rounded-lg p-4 ${
                    control.enabled ? 'border-green-200 bg-green-50' : 'border-gray-200 bg-gray-50'
                  }`}
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center space-x-3">
                      <span className="text-2xl">{getControlTypeIcon(control.type)}</span>
                      <div>
                        <h4 className="font-semibold">{control.name}</h4>
                        <p className="text-sm text-gray-600">{control.description}</p>
                        <div className="flex items-center space-x-2 mt-1">
                          <span className={`px-2 py-1 rounded-full text-xs font-medium border ${
                            getControlTypeColor(control.type)
                          }`}>
                            {control.type.replace('_', ' ').toUpperCase()}
                          </span>
                          <span className="text-xs text-gray-500">
                            Last triggered: {formatLastTriggered(control.lastTriggered)}
                          </span>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <label className="flex items-center space-x-2">
                        <input
                          type="checkbox"
                          checked={control.enabled}
                          onChange={(e) => handleToggleControl(control.id, e.target.checked)}
                          className="rounded"
                        />
                        <span className="text-sm">Enabled</span>
                      </label>
                    </div>
                  </div>

                  {/* Trigger Conditions */}
                  <div className="mb-3">
                    <h5 className="text-sm font-medium text-gray-700 mb-2">Trigger Conditions:</h5>
                    <div className="space-y-1">
                      {control.triggerConditions.map((condition, index) => (
                        <div key={index} className="text-sm text-gray-600 bg-white rounded px-3 py-2 border">
                          <span className="font-medium">{condition.name}:</span>
                          <span className="ml-2">
                            {condition.metric} {condition.operator} {(condition.threshold * 100).toFixed(1)}%
                          </span>
                          <span className={`ml-2 font-medium ${getSeverityColor(condition.severity)}`}>
                            ({condition.severity})
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="mb-3">
                    <h5 className="text-sm font-medium text-gray-700 mb-2">Actions:</h5>
                    <div className="space-y-1">
                      {control.actions.map((action, index) => (
                        <div key={index} className="text-sm text-gray-600 bg-white rounded px-3 py-2 border">
                          <span className="font-medium">Priority {action.priority}:</span>
                          <span className="ml-2 capitalize">
                            {action.type.replace('_', ' ')}
                          </span>
                          {Object.keys(action.parameters).length > 0 && (
                            <span className="ml-2 text-xs text-gray-500">
                              ({JSON.stringify(action.parameters)})
                            </span>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Control Actions */}
                  <div className="flex items-center justify-end space-x-2 pt-3 border-t border-gray-200">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleTestControl(control)}
                      className="text-xs"
                    >
                      Test
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {/* Edit control */}}
                      className="text-xs"
                    >
                      Edit
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleDeleteControl(control.id)}
                      className="text-xs text-red-600 hover:text-red-700"
                    >
                      Delete
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Warning */}
          <Alert variant="warning" className="mt-6">
            <div>
              <h4 className="font-semibold">Important Notice</h4>
              <p className="text-sm">
                Emergency controls are designed to protect your portfolio during extreme market conditions. 
                Test controls regularly and ensure they align with your risk management strategy.
              </p>
            </div>
          </Alert>
        </div>
      </Card>

      {/* Test Modal */}
      <Modal
        isOpen={showTestModal}
        onClose={() => setShowTestModal(false)}
        title={`Test Emergency Control: ${selectedControl?.name}`}
      >
        <div className="p-6">
          {testResults ? (
            <div>
              {testResults.error ? (
                <Alert variant="error">
                  <div>
                    <h4 className="font-semibold">Test Failed</h4>
                    <p className="text-sm">{testResults.error}</p>
                  </div>
                </Alert>
              ) : (
                <div>
                  <Alert variant="success" className="mb-4">
                    <div>
                      <h4 className="font-semibold">Test Successful</h4>
                      <p className="text-sm">Emergency control test completed successfully</p>
                    </div>
                  </Alert>
                  
                  <div className="space-y-3">
                    <div>
                      <span className="font-medium">Control ID:</span>
                      <span className="ml-2">{testResults.controlId}</span>
                    </div>
                    <div>
                      <span className="font-medium">Test Time:</span>
                      <span className="ml-2">{testResults.triggeredAt.toLocaleString()}</span>
                    </div>
                    <div>
                      <span className="font-medium">Actions Tested:</span>
                      <span className="ml-2">{testResults.actions.length}</span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <p className="text-gray-600">Testing emergency control...</p>
            </div>
          )}
          
          <div className="flex justify-end mt-6">
            <Button
              variant="outline"
              onClick={() => setShowTestModal(false)}
            >
              Close
            </Button>
          </div>
        </div>
      </Modal>

      {/* Create Control Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="Create Emergency Control"
      >
        <div className="p-6">
          <p className="text-gray-600 mb-4">
            Emergency control creation interface would be implemented here.
            This would include forms for defining trigger conditions and actions.
          </p>
          <div className="flex justify-end">
            <Button
              variant="outline"
              onClick={() => setShowCreateModal(false)}
            >
              Close
            </Button>
          </div>
        </div>
      </Modal>
    </>
  );
};