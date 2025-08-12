import React, { useState, useEffect } from 'react'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Modal } from '@/components/ui/Modal'
import { Alert } from '@/components/ui/Alert'
import { batchWorkflowManager } from '@/services/batchWorkflowManager'
import { batchMonitoringService } from '@/services/batchMonitoringService'
import type { WorkflowConfig } from '@/types'

export const BatchProcessingDashboard: React.FC = () => {
  const [activeBatches, setActiveBatches] = useState<any[]>([])
  const [systemStats, setSystemStats] = useState<any>(null)
  const [selectedBatch, setSelectedBatch] = useState<any>(null)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showReportModal, setShowReportModal] = useState(false)
  const [batchReport, setBatchReport] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Form state for creating new batch
  const [batchForm, setBatchForm] = useState({
    name: '',
    description: '',
    concurrencyLimit: 3,
    workflows: [] as WorkflowConfig[]
  })

  useEffect(() => {
    loadActiveBatches()
    loadSystemStats()
    
    // Set up periodic updates
    const interval = setInterval(() => {
      loadActiveBatches()
      loadSystemStats()
    }, 5000)

    return () => clearInterval(interval)
  }, [])

  const loadActiveBatches = () => {
    const batches = batchWorkflowManager.getActiveBatches()
    setActiveBatches(batches)
  }

  const loadSystemStats = () => {
    const stats = batchMonitoringService.getSystemBatchStats()
    setSystemStats(stats)
  }

  const handleCreateBatch = async () => {
    if (!batchForm.name || batchForm.workflows.length === 0) {
      setError('Please provide a name and at least one workflow')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const batchConfig = {
        name: batchForm.name,
        description: batchForm.description,
        workflows: batchForm.workflows,
        concurrencyLimit: batchForm.concurrencyLimit
      }

      const batch = await batchWorkflowManager.executeBatch(batchConfig)
      
      // Start monitoring
      batchMonitoringService.startMonitoring(batch.id)
      
      setShowCreateModal(false)
      setBatchForm({
        name: '',
        description: '',
        concurrencyLimit: 3,
        workflows: []
      })
      
      loadActiveBatches()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create batch')
    } finally {
      setLoading(false)
    }
  }

  const handlePauseBatch = async (batchId: string) => {
    try {
      await batchWorkflowManager.pauseBatch(batchId)
      loadActiveBatches()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to pause batch')
    }
  }

  const handleResumeBatch = async (batchId: string) => {
    try {
      await batchWorkflowManager.resumeBatch(batchId)
      loadActiveBatches()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to resume batch')
    }
  }

  const handleCancelBatch = async (batchId: string) => {
    try {
      await batchWorkflowManager.cancelBatch(batchId)
      loadActiveBatches()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to cancel batch')
    }
  }

  const handleViewReport = async (batchId: string) => {
    try {
      const report = batchMonitoringService.generateBatchReport(batchId)
      setBatchReport(report)
      setShowReportModal(true)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate report')
    }
  }

  const formatDuration = (ms: number) => {
    const minutes = Math.floor(ms / 60000)
    const seconds = Math.floor((ms % 60000) / 1000)
    return `${minutes}m ${seconds}s`
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
      case 'cancelled':
        return 'text-gray-600 bg-gray-100'
      case 'partial':
        return 'text-orange-600 bg-orange-100'
      default:
        return 'text-gray-600 bg-gray-100'
    }
  }

  const addSampleWorkflow = () => {
    const sampleWorkflow: WorkflowConfig = {
      templateId: 'basic_optimization',
      labId: `sample_lab_${Date.now()}`,
      persona: { type: 'balanced', settings: {} },
      parameters: {
        timeframes: ['1h'],
        numericalParams: [],
        structuralParams: [],
        constraints: []
      },
      resumable: true,
      priority: 'normal'
    }

    setBatchForm(prev => ({
      ...prev,
      workflows: [...prev.workflows, sampleWorkflow]
    }))
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">Batch Processing</h2>
        <Button onClick={() => setShowCreateModal(true)}>
          Create New Batch
        </Button>
      </div>

      {/* Error Display */}
      {error && (
        <Alert type="error" title="Error">
          {error}
        </Alert>
      )}

      {/* System Statistics */}
      {systemStats && (
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">System Overview</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">{systemStats.totalBatches}</div>
              <div className="text-sm text-gray-600">Total Batches</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">{systemStats.runningBatches}</div>
              <div className="text-sm text-gray-600">Running</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">{systemStats.totalWorkflows}</div>
              <div className="text-sm text-gray-600">Total Workflows</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">
                {Math.round(systemStats.systemResourceUtilization.overall * 100)}%
              </div>
              <div className="text-sm text-gray-600">Resource Usage</div>
            </div>
          </div>
        </Card>
      )}

      {/* Active Batches */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">Active Batches</h3>
        
        {activeBatches.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            No active batches. Create a new batch to get started.
          </div>
        ) : (
          <div className="space-y-4">
            {activeBatches.map((batch) => (
              <div key={batch.id} className="border rounded-lg p-4">
                <div className="flex justify-between items-start mb-3">
                  <div>
                    <h4 className="font-medium text-lg">{batch.name}</h4>
                    <p className="text-sm text-gray-600">{batch.description}</p>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className={`px-2 py-1 text-xs rounded-full capitalize ${getStatusColor(batch.status)}`}>
                      {batch.status}
                    </span>
                    <div className="flex space-x-1">
                      {batch.status === 'running' && (
                        <Button size="sm" variant="outline" onClick={() => handlePauseBatch(batch.id)}>
                          Pause
                        </Button>
                      )}
                      {batch.status === 'paused' && (
                        <Button size="sm" onClick={() => handleResumeBatch(batch.id)}>
                          Resume
                        </Button>
                      )}
                      {(batch.status === 'running' || batch.status === 'paused') && (
                        <Button size="sm" variant="outline" onClick={() => handleCancelBatch(batch.id)}>
                          Cancel
                        </Button>
                      )}
                      <Button size="sm" variant="outline" onClick={() => handleViewReport(batch.id)}>
                        Report
                      </Button>
                    </div>
                  </div>
                </div>

                {/* Progress Bar */}
                <div className="mb-3">
                  <div className="flex justify-between text-sm text-gray-600 mb-1">
                    <span>Progress</span>
                    <span>{Math.round(batch.progress)}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${batch.progress}%` }}
                    />
                  </div>
                </div>

                {/* Batch Statistics */}
                <div className="grid grid-cols-2 md:grid-cols-5 gap-4 text-sm">
                  <div>
                    <span className="text-gray-600">Total:</span>
                    <span className="ml-2 font-medium">{batch.totalWorkflows}</span>
                  </div>
                  <div>
                    <span className="text-gray-600">Completed:</span>
                    <span className="ml-2 font-medium text-green-600">{batch.completedWorkflows}</span>
                  </div>
                  <div>
                    <span className="text-gray-600">Failed:</span>
                    <span className="ml-2 font-medium text-red-600">{batch.failedWorkflows}</span>
                  </div>
                  <div>
                    <span className="text-gray-600">Running:</span>
                    <span className="ml-2 font-medium text-blue-600">
                      {batch.workflows.filter((w: any) => w.status === 'running').length}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-600">Duration:</span>
                    <span className="ml-2 font-medium">
                      {formatDuration(batch.endTime 
                        ? batch.endTime.getTime() - batch.startTime.getTime()
                        : Date.now() - batch.startTime.getTime()
                      )}
                    </span>
                  </div>
                </div>

                {/* Error Summary */}
                {batch.errors.length > 0 && (
                  <div className="mt-3 p-2 bg-red-50 border border-red-200 rounded text-sm">
                    <span className="text-red-800 font-medium">
                      {batch.errors.length} error(s) occurred
                    </span>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* Create Batch Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="Create New Batch"
        size="large"
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Batch Name
            </label>
            <input
              type="text"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={batchForm.name}
              onChange={(e) => setBatchForm(prev => ({ ...prev, name: e.target.value }))}
              placeholder="Enter batch name"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Description
            </label>
            <textarea
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows={3}
              value={batchForm.description}
              onChange={(e) => setBatchForm(prev => ({ ...prev, description: e.target.value }))}
              placeholder="Enter batch description"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Concurrency Limit
            </label>
            <input
              type="number"
              min="1"
              max="10"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={batchForm.concurrencyLimit}
              onChange={(e) => setBatchForm(prev => ({ ...prev, concurrencyLimit: parseInt(e.target.value) }))}
            />
          </div>

          <div>
            <div className="flex justify-between items-center mb-2">
              <label className="block text-sm font-medium text-gray-700">
                Workflows ({batchForm.workflows.length})
              </label>
              <Button size="sm" variant="outline" onClick={addSampleWorkflow}>
                Add Sample Workflow
              </Button>
            </div>
            
            {batchForm.workflows.length === 0 ? (
              <div className="text-sm text-gray-500 text-center py-4 border-2 border-dashed border-gray-300 rounded">
                No workflows added. Click "Add Sample Workflow" to get started.
              </div>
            ) : (
              <div className="space-y-2 max-h-40 overflow-y-auto">
                {batchForm.workflows.map((workflow, index) => (
                  <div key={index} className="flex justify-between items-center p-2 border rounded">
                    <div className="text-sm">
                      <div className="font-medium">Workflow {index + 1}</div>
                      <div className="text-gray-600">Template: {workflow.templateId}</div>
                    </div>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => setBatchForm(prev => ({
                        ...prev,
                        workflows: prev.workflows.filter((_, i) => i !== index)
                      }))}
                    >
                      Remove
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="flex justify-end space-x-3">
            <Button variant="outline" onClick={() => setShowCreateModal(false)}>
              Cancel
            </Button>
            <Button onClick={handleCreateBatch} disabled={loading}>
              {loading ? 'Creating...' : 'Create Batch'}
            </Button>
          </div>
        </div>
      </Modal>

      {/* Batch Report Modal */}
      <Modal
        isOpen={showReportModal}
        onClose={() => setShowReportModal(false)}
        title="Batch Report"
        size="large"
      >
        {batchReport && (
          <div className="space-y-6">
            {/* Summary */}
            <div>
              <h4 className="font-medium mb-2">Summary</h4>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-600">Status:</span>
                  <span className={`ml-2 capitalize ${getStatusColor(batchReport.summary.status)}`}>
                    {batchReport.summary.status}
                  </span>
                </div>
                <div>
                  <span className="text-gray-600">Success Rate:</span>
                  <span className="ml-2 font-medium">
                    {Math.round(batchReport.summary.successRate * 100)}%
                  </span>
                </div>
                <div>
                  <span className="text-gray-600">Duration:</span>
                  <span className="ml-2 font-medium">
                    {formatDuration(batchReport.summary.duration)}
                  </span>
                </div>
                <div>
                  <span className="text-gray-600">Throughput:</span>
                  <span className="ml-2 font-medium">
                    {batchReport.summary.throughput.toFixed(2)} workflows/hour
                  </span>
                </div>
              </div>
            </div>

            {/* Alerts */}
            {batchReport.alerts.length > 0 && (
              <div>
                <h4 className="font-medium mb-2">Alerts</h4>
                <div className="space-y-2">
                  {batchReport.alerts.map((alert: any, index: number) => (
                    <div key={index} className={`p-2 rounded text-sm ${
                      alert.severity === 'high' ? 'bg-red-50 text-red-800' :
                      alert.severity === 'medium' ? 'bg-yellow-50 text-yellow-800' :
                      'bg-blue-50 text-blue-800'
                    }`}>
                      <div className="flex justify-between">
                        <span>{alert.message}</span>
                        <span className="capitalize">{alert.severity}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Recommendations */}
            {batchReport.recommendations.length > 0 && (
              <div>
                <h4 className="font-medium mb-2">Recommendations</h4>
                <ul className="list-disc list-inside text-sm text-gray-700 space-y-1">
                  {batchReport.recommendations.map((rec: string, index: number) => (
                    <li key={index}>{rec}</li>
                  ))}
                </ul>
              </div>
            )}

            <div className="flex justify-end">
              <Button variant="outline" onClick={() => setShowReportModal(false)}>
                Close
              </Button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}

export default BatchProcessingDashboard