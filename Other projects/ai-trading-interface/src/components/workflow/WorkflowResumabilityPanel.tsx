import React, { useState, useEffect } from 'react'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Modal } from '@/components/ui/Modal'
import { Alert } from '@/components/ui/Alert'
import { useWorkflowStore } from '@/stores/workflowStore'
import { workflowCheckpointManager } from '@/services/workflowCheckpointManager'
import { workflowRecoveryService } from '@/services/workflowRecoveryService'
import { workflowStatusMonitor } from '@/services/workflowStatusMonitor'
import type { WorkflowExecution } from '@/types'

interface WorkflowResumabilityPanelProps {
  execution: WorkflowExecution
}

export const WorkflowResumabilityPanel: React.FC<WorkflowResumabilityPanelProps> = ({
  execution
}) => {
  const [checkpoints, setCheckpoints] = useState<any[]>([])
  const [recoveryHistory, setRecoveryHistory] = useState<any[]>([])
  const [workflowStatus, setWorkflowStatus] = useState<any>(null)
  const [showCheckpointModal, setShowCheckpointModal] = useState(false)
  const [showRecoveryModal, setShowRecoveryModal] = useState(false)
  const [selectedCheckpoint, setSelectedCheckpoint] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const { updateExecution } = useWorkflowStore()

  useEffect(() => {
    loadCheckpoints()
    loadRecoveryHistory()
    loadWorkflowStatus()
    
    // Start monitoring
    workflowStatusMonitor.startMonitoring(execution.id)
    workflowStatusMonitor.addStatusListener(execution.id, setWorkflowStatus)
    
    return () => {
      workflowStatusMonitor.removeStatusListener(execution.id, setWorkflowStatus)
    }
  }, [execution.id])

  const loadCheckpoints = async () => {
    try {
      const checkpointList = await workflowCheckpointManager.getCheckpointsForExecution(execution.id)
      setCheckpoints(checkpointList)
    } catch (err) {
      console.error('Failed to load checkpoints:', err)
    }
  }

  const loadRecoveryHistory = () => {
    const history = workflowRecoveryService.getRecoveryHistory(execution.id)
    setRecoveryHistory(history)
  }

  const loadWorkflowStatus = () => {
    const status = workflowStatusMonitor.getWorkflowStatus(execution.id)
    setWorkflowStatus(status)
  }

  const handleCreateCheckpoint = async () => {
    setLoading(true)
    setError(null)
    
    try {
      await workflowCheckpointManager.createCheckpoint(execution.id)
      await loadCheckpoints()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create checkpoint')
    } finally {
      setLoading(false)
    }
  }

  const handleResumeFromCheckpoint = async (checkpointId: string) => {
    setLoading(true)
    setError(null)
    
    try {
      const resumedExecution = await workflowCheckpointManager.resumeFromCheckpoint(checkpointId)
      updateExecution(execution.id, resumedExecution)
      setShowCheckpointModal(false)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to resume from checkpoint')
    } finally {
      setLoading(false)
    }
  }

  const handleResumeWorkflow = async () => {
    setLoading(true)
    setError(null)
    
    try {
      await workflowRecoveryService.resumeAfterRecovery(execution.id)
      updateExecution(execution.id, { status: 'running' })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to resume workflow')
    } finally {
      setLoading(false)
    }
  }

  const handleDeleteCheckpoint = async (checkpointId: string) => {
    try {
      await workflowCheckpointManager.deleteCheckpoint(checkpointId)
      await loadCheckpoints()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete checkpoint')
    }
  }

  const formatTimestamp = (timestamp: Date) => {
    return new Intl.DateTimeFormat('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    }).format(timestamp)
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'text-green-600 bg-green-100'
      case 'running':
        return 'text-blue-600 bg-blue-100'
      case 'paused':
        return 'text-yellow-600 bg-yellow-100'
      case 'failed':
        return 'text-red-600 bg-red-100'
      default:
        return 'text-gray-600 bg-gray-100'
    }
  }

  const getHealthColor = (status: string) => {
    switch (status) {
      case 'excellent':
        return 'text-green-600'
      case 'good':
        return 'text-blue-600'
      case 'fair':
        return 'text-yellow-600'
      case 'poor':
        return 'text-orange-600'
      case 'critical':
        return 'text-red-600'
      default:
        return 'text-gray-600'
    }
  }

  return (
    <div className="space-y-6">
      {/* Error Display */}
      {error && (
        <Alert type="error" title="Error">
          {error}
        </Alert>
      )}

      {/* Workflow Status Overview */}
      {workflowStatus && (
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">Workflow Status</h3>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
            <div>
              <span className="text-sm text-gray-600">Overall Status:</span>
              <div className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium capitalize ml-2 ${
                getStatusColor(workflowStatus.overall)
              }`}>
                {workflowStatus.overall}
              </div>
            </div>
            <div>
              <span className="text-sm text-gray-600">Progress:</span>
              <span className="ml-2 font-medium">
                {workflowStatus.progress.completed}/{workflowStatus.progress.total} steps
              </span>
            </div>
            <div>
              <span className="text-sm text-gray-600">Health:</span>
              <span className={`ml-2 font-medium ${getHealthColor(workflowStatus.health.status)}`}>
                {workflowStatus.health.status} ({workflowStatus.health.score}%)
              </span>
            </div>
            <div>
              <span className="text-sm text-gray-600">Issues:</span>
              <span className={`ml-2 font-medium ${
                workflowStatus.issues.length > 0 ? 'text-red-600' : 'text-green-600'
              }`}>
                {workflowStatus.issues.length}
              </span>
            </div>
          </div>

          {/* Issues */}
          {workflowStatus.issues.length > 0 && (
            <div className="mt-4">
              <h4 className="text-sm font-medium text-gray-700 mb-2">Active Issues</h4>
              <div className="space-y-2">
                {workflowStatus.issues.slice(0, 3).map((issue: any, index: number) => (
                  <div key={index} className={`p-2 rounded text-sm ${
                    issue.severity === 'high' ? 'bg-red-50 text-red-800' :
                    issue.severity === 'medium' ? 'bg-yellow-50 text-yellow-800' :
                    'bg-blue-50 text-blue-800'
                  }`}>
                    <div className="flex justify-between items-start">
                      <span>{issue.message}</span>
                      <span className="text-xs opacity-75 capitalize">{issue.severity}</span>
                    </div>
                  </div>
                ))}
                {workflowStatus.issues.length > 3 && (
                  <div className="text-xs text-gray-500">
                    +{workflowStatus.issues.length - 3} more issues
                  </div>
                )}
              </div>
            </div>
          )}
        </Card>
      )}

      {/* Resumability Controls */}
      <Card className="p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold">Resumability Controls</h3>
          <div className="flex space-x-2">
            <Button
              size="sm"
              variant="outline"
              onClick={handleCreateCheckpoint}
              disabled={loading || execution.status === 'completed'}
            >
              Create Checkpoint
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => setShowCheckpointModal(true)}
              disabled={checkpoints.length === 0}
            >
              View Checkpoints
            </Button>
            {(execution.status === 'paused' || execution.status === 'failed') && (
              <Button
                size="sm"
                onClick={handleResumeWorkflow}
                disabled={loading}
              >
                Resume Workflow
              </Button>
            )}
          </div>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-3 gap-4 text-sm">
          <div>
            <span className="text-gray-600">Checkpoints:</span>
            <span className="ml-2 font-medium">{checkpoints.length}</span>
          </div>
          <div>
            <span className="text-gray-600">Recovery Attempts:</span>
            <span className="ml-2 font-medium">{recoveryHistory.length}</span>
          </div>
          <div>
            <span className="text-gray-600">Last Checkpoint:</span>
            <span className="ml-2 font-medium">
              {checkpoints.length > 0 ? formatTimestamp(checkpoints[0].timestamp) : 'None'}
            </span>
          </div>
        </div>
      </Card>

      {/* Recovery History */}
      {recoveryHistory.length > 0 && (
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">Recovery History</h3>
          <div className="space-y-3">
            {recoveryHistory.slice(0, 5).map((attempt) => (
              <div key={attempt.id} className="flex justify-between items-center p-3 border rounded-lg">
                <div>
                  <div className="font-medium">{attempt.strategy}</div>
                  <div className="text-sm text-gray-600">
                    {attempt.errorCode} • {formatTimestamp(attempt.timestamp)}
                  </div>
                </div>
                <div className={`px-2 py-1 text-xs rounded-full ${
                  attempt.status === 'success' ? 'bg-green-100 text-green-800' :
                  attempt.status === 'failed' ? 'bg-red-100 text-red-800' :
                  'bg-yellow-100 text-yellow-800'
                }`}>
                  {attempt.status}
                </div>
              </div>
            ))}
            {recoveryHistory.length > 5 && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowRecoveryModal(true)}
              >
                View All Recovery History
              </Button>
            )}
          </div>
        </Card>
      )}

      {/* Checkpoints Modal */}
      <Modal
        isOpen={showCheckpointModal}
        onClose={() => setShowCheckpointModal(false)}
        title="Workflow Checkpoints"
        size="large"
      >
        <div className="space-y-4">
          {checkpoints.length === 0 ? (
            <p className="text-gray-600">No checkpoints available for this workflow.</p>
          ) : (
            <div className="space-y-3">
              {checkpoints.map((checkpoint) => (
                <div key={checkpoint.id} className="border rounded-lg p-4">
                  <div className="flex justify-between items-start mb-2">
                    <div>
                      <div className="font-medium">
                        Checkpoint {checkpoint.id.split('_').pop()}
                      </div>
                      <div className="text-sm text-gray-600">
                        {formatTimestamp(checkpoint.timestamp)}
                      </div>
                    </div>
                    <div className="flex space-x-2">
                      <Button
                        size="sm"
                        onClick={() => handleResumeFromCheckpoint(checkpoint.id)}
                        disabled={loading}
                      >
                        Resume
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleDeleteCheckpoint(checkpoint.id)}
                      >
                        Delete
                      </Button>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-gray-600">Step:</span>
                      <span className="ml-2">
                        {checkpoint.metadata.currentStep}/{checkpoint.metadata.totalSteps}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-600">Status:</span>
                      <span className={`ml-2 capitalize ${getStatusColor(checkpoint.metadata.status)}`}>
                        {checkpoint.metadata.status}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-600">Completed:</span>
                      <span className="ml-2">{checkpoint.metadata.completedSteps}</span>
                    </div>
                    <div>
                      <span className="text-gray-600">Failed:</span>
                      <span className="ml-2">{checkpoint.metadata.failedSteps}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
          
          <div className="flex justify-end space-x-3">
            <Button variant="outline" onClick={() => setShowCheckpointModal(false)}>
              Close
            </Button>
          </div>
        </div>
      </Modal>

      {/* Recovery History Modal */}
      <Modal
        isOpen={showRecoveryModal}
        onClose={() => setShowRecoveryModal(false)}
        title="Recovery History"
        size="large"
      >
        <div className="space-y-4">
          {recoveryHistory.length === 0 ? (
            <p className="text-gray-600">No recovery attempts recorded for this workflow.</p>
          ) : (
            <div className="space-y-3">
              {recoveryHistory.map((attempt) => (
                <div key={attempt.id} className="border rounded-lg p-4">
                  <div className="flex justify-between items-start mb-2">
                    <div>
                      <div className="font-medium">{attempt.strategy}</div>
                      <div className="text-sm text-gray-600">
                        Error: {attempt.errorCode}
                      </div>
                    </div>
                    <div className={`px-2 py-1 text-xs rounded-full ${
                      attempt.status === 'success' ? 'bg-green-100 text-green-800' :
                      attempt.status === 'failed' ? 'bg-red-100 text-red-800' :
                      'bg-yellow-100 text-yellow-800'
                    }`}>
                      {attempt.status}
                    </div>
                  </div>
                  
                  <div className="text-sm text-gray-600 mb-2">
                    {formatTimestamp(attempt.timestamp)}
                    {attempt.endTime && (
                      <span> • Duration: {Math.round((attempt.endTime.getTime() - attempt.timestamp.getTime()) / 1000)}s</span>
                    )}
                  </div>
                  
                  {attempt.result && (
                    <div className="text-sm">
                      <div className="font-medium">Result:</div>
                      <div className="text-gray-600">{attempt.result.message}</div>
                      {attempt.result.actions.length > 0 && (
                        <div className="mt-1">
                          <div className="font-medium">Actions:</div>
                          <ul className="list-disc list-inside text-gray-600">
                            {attempt.result.actions.map((action, index) => (
                              <li key={index}>{action}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  )}
                  
                  {attempt.error && (
                    <div className="text-sm text-red-600 mt-2">
                      Error: {attempt.error}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
          
          <div className="flex justify-end space-x-3">
            <Button variant="outline" onClick={() => setShowRecoveryModal(false)}>
              Close
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}

export default WorkflowResumabilityPanel