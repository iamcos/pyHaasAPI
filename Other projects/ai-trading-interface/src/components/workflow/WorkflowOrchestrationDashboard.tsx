import React, { useState, useEffect } from 'react'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Modal } from '@/components/ui/Modal'
import { Alert } from '@/components/ui/Alert'
import { useWorkflowStore } from '@/stores/workflowStore'
import { workflowOrchestrator } from '@/services/workflowOrchestrator'
import { workflowTemplateManager } from '@/services/workflowTemplateManager'
import { workflowProgressTracker } from '@/services/workflowProgressTracker'
import { workflowConfigManager } from '@/services/workflowConfigManager'
import type { 
  WorkflowExecution, 
  WorkflowTemplate, 
  WorkflowConfig,
  WorkflowProgress 
} from '@/types'

export const WorkflowOrchestrationDashboard: React.FC = () => {
  const {
    templates,
    executions,
    activeExecution,
    selectedTemplate,
    loading,
    errors,
    setTemplates,
    selectTemplate,
    setActiveExecution
  } = useWorkflowStore()

  const [showTemplateModal, setShowTemplateModal] = useState(false)
  const [showConfigModal, setShowConfigModal] = useState(false)
  const [currentProgress, setCurrentProgress] = useState<WorkflowProgress | null>(null)
  const [selectedExecution, setSelectedExecution] = useState<string | null>(null)

  useEffect(() => {
    loadTemplates()
  }, [])

  useEffect(() => {
    if (activeExecution) {
      workflowProgressTracker.startTracking(activeExecution)
      workflowProgressTracker.addProgressListener(activeExecution, setCurrentProgress)
      
      return () => {
        workflowProgressTracker.stopTracking(activeExecution)
        workflowProgressTracker.removeProgressListener(activeExecution, setCurrentProgress)
      }
    }
  }, [activeExecution])

  const loadTemplates = async () => {
    try {
      const availableTemplates = await workflowTemplateManager.getTemplates()
      setTemplates(availableTemplates)
    } catch (error) {
      console.error('Failed to load templates:', error)
    }
  }

  const handleStartWorkflow = async (templateId: string) => {
    try {
      // This would typically come from a form or configuration modal
      const config: WorkflowConfig = await workflowConfigManager.createConfigFromTemplate(
        templateId,
        'sample_lab_id', // This should come from user selection
        { type: 'balanced', settings: {} }, // This should come from persona selection
      )

      const execution = await workflowOrchestrator.executeWorkflow(config)
      setActiveExecution(execution.id)
    } catch (error) {
      console.error('Failed to start workflow:', error)
    }
  }

  const handlePauseWorkflow = async (executionId: string) => {
    // Implementation for pausing workflow
    console.log('Pausing workflow:', executionId)
  }

  const handleResumeWorkflow = async (executionId: string) => {
    // Implementation for resuming workflow
    console.log('Resuming workflow:', executionId)
  }

  const handleStopWorkflow = async (executionId: string) => {
    // Implementation for stopping workflow
    console.log('Stopping workflow:', executionId)
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">Workflow Orchestration</h2>
        <div className="flex space-x-3">
          <Button
            onClick={() => setShowTemplateModal(true)}
            variant="outline"
          >
            Manage Templates
          </Button>
          <Button
            onClick={() => setShowConfigModal(true)}
            disabled={!selectedTemplate}
          >
            Start Workflow
          </Button>
        </div>
      </div>

      {/* Error Display */}
      {errors.execution && (
        <Alert type="error" title="Workflow Error">
          {errors.execution}
        </Alert>
      )}

      {/* Active Workflow Progress */}
      {activeExecution && currentProgress && (
        <Card className="p-6">
          <div className="flex justify-between items-start mb-4">
            <div>
              <h3 className="text-lg font-semibold">Active Workflow</h3>
              <p className="text-sm text-gray-600">
                Step {currentProgress.currentStep} of {currentProgress.totalSteps}
              </p>
            </div>
            <div className="flex space-x-2">
              <Button
                size="sm"
                variant="outline"
                onClick={() => handlePauseWorkflow(activeExecution)}
              >
                Pause
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => handleStopWorkflow(activeExecution)}
              >
                Stop
              </Button>
            </div>
          </div>

          {/* Progress Bar */}
          <div className="mb-4">
            <div className="flex justify-between text-sm text-gray-600 mb-1">
              <span>Overall Progress</span>
              <span>{Math.round(currentProgress.overallProgress)}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${currentProgress.overallProgress}%` }}
              />
            </div>
          </div>

          {/* Current Step Progress */}
          {currentProgress.stepProgress > 0 && (
            <div className="mb-4">
              <div className="flex justify-between text-sm text-gray-600 mb-1">
                <span>Current Step</span>
                <span>{Math.round(currentProgress.stepProgress)}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-1">
                <div
                  className="bg-green-500 h-1 rounded-full transition-all duration-300"
                  style={{ width: `${currentProgress.stepProgress}%` }}
                />
              </div>
            </div>
          )}

          {/* Workflow Details */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <span className="text-gray-600">Status:</span>
              <span className="ml-2 font-medium capitalize">{currentProgress.status}</span>
            </div>
            <div>
              <span className="text-gray-600">Time Remaining:</span>
              <span className="ml-2 font-medium">
                {Math.round(currentProgress.estimatedTimeRemaining / 1000 / 60)}m
              </span>
            </div>
            <div>
              <span className="text-gray-600">Completed:</span>
              <span className="ml-2 font-medium">
                {executions.find(e => e.id === activeExecution)?.steps.filter(s => s.status === 'completed').length || 0}
              </span>
            </div>
            <div>
              <span className="text-gray-600">Failed:</span>
              <span className="ml-2 font-medium">
                {executions.find(e => e.id === activeExecution)?.steps.filter(s => s.status === 'failed').length || 0}
              </span>
            </div>
          </div>
        </Card>
      )}

      {/* Workflow Templates */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">Available Templates</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {templates.map((template) => (
            <div
              key={template.id}
              className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                selectedTemplate === template.id
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
              onClick={() => selectTemplate(template.id)}
            >
              <div className="flex justify-between items-start mb-2">
                <h4 className="font-medium">{template.name}</h4>
                <span className={`px-2 py-1 text-xs rounded-full ${
                  template.complexity === 'simple' ? 'bg-green-100 text-green-800' :
                  template.complexity === 'moderate' ? 'bg-yellow-100 text-yellow-800' :
                  template.complexity === 'complex' ? 'bg-orange-100 text-orange-800' :
                  'bg-red-100 text-red-800'
                }`}>
                  {template.complexity}
                </span>
              </div>
              <p className="text-sm text-gray-600 mb-3">{template.description}</p>
              <div className="flex justify-between items-center text-xs text-gray-500">
                <span>{template.steps.length} steps</span>
                <span>{Math.round(template.estimatedDuration / 1000 / 60)}m</span>
              </div>
              <div className="mt-2">
                <Button
                  size="sm"
                  onClick={(e) => {
                    e.stopPropagation()
                    handleStartWorkflow(template.id)
                  }}
                  disabled={loading.executing}
                >
                  Start Workflow
                </Button>
              </div>
            </div>
          ))}
        </div>
      </Card>

      {/* Recent Executions */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">Recent Executions</h3>
        <div className="space-y-3">
          {executions.slice(0, 5).map((execution) => (
            <div
              key={execution.id}
              className="flex justify-between items-center p-3 border rounded-lg"
            >
              <div>
                <div className="font-medium">
                  {templates.find(t => t.id === execution.templateId)?.name || 'Custom Workflow'}
                </div>
                <div className="text-sm text-gray-600">
                  Started: {execution.startTime.toLocaleString()}
                </div>
              </div>
              <div className="flex items-center space-x-3">
                <span className={`px-2 py-1 text-xs rounded-full ${
                  execution.status === 'completed' ? 'bg-green-100 text-green-800' :
                  execution.status === 'running' ? 'bg-blue-100 text-blue-800' :
                  execution.status === 'paused' ? 'bg-yellow-100 text-yellow-800' :
                  'bg-red-100 text-red-800'
                }`}>
                  {execution.status}
                </span>
                <div className="text-sm text-gray-600">
                  {execution.currentStep}/{execution.totalSteps}
                </div>
                {execution.status === 'paused' && (
                  <Button
                    size="sm"
                    onClick={() => handleResumeWorkflow(execution.id)}
                  >
                    Resume
                  </Button>
                )}
              </div>
            </div>
          ))}
        </div>
      </Card>

      {/* Template Management Modal */}
      <Modal
        isOpen={showTemplateModal}
        onClose={() => setShowTemplateModal(false)}
        title="Manage Workflow Templates"
      >
        <div className="space-y-4">
          <p className="text-gray-600">
            Template management functionality would go here, including:
          </p>
          <ul className="list-disc list-inside text-sm text-gray-600 space-y-1">
            <li>Create new templates</li>
            <li>Edit existing templates</li>
            <li>Clone templates</li>
            <li>Import/export templates</li>
            <li>Template versioning</li>
          </ul>
          <div className="flex justify-end space-x-3">
            <Button variant="outline" onClick={() => setShowTemplateModal(false)}>
              Close
            </Button>
          </div>
        </div>
      </Modal>

      {/* Configuration Modal */}
      <Modal
        isOpen={showConfigModal}
        onClose={() => setShowConfigModal(false)}
        title="Configure Workflow"
      >
        <div className="space-y-4">
          <p className="text-gray-600">
            Workflow configuration interface would go here, including:
          </p>
          <ul className="list-disc list-inside text-sm text-gray-600 space-y-1">
            <li>Lab selection</li>
            <li>Persona selection</li>
            <li>Parameter configuration</li>
            <li>Constraint settings</li>
            <li>Retry policy configuration</li>
          </ul>
          <div className="flex justify-end space-x-3">
            <Button variant="outline" onClick={() => setShowConfigModal(false)}>
              Cancel
            </Button>
            <Button onClick={() => setShowConfigModal(false)}>
              Start Workflow
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}

export default WorkflowOrchestrationDashboard