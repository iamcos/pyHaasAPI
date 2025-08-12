import React, { useState } from 'react'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Modal } from '@/components/ui/Modal'
import type { WorkflowStep, WorkflowExecution, ChainOfThoughtStep } from '@/types'

interface WorkflowStepVisualizationProps {
  execution: WorkflowExecution
  onStepClick?: (step: WorkflowStep) => void
}

export const WorkflowStepVisualization: React.FC<WorkflowStepVisualizationProps> = ({
  execution,
  onStepClick
}) => {
  const [selectedStep, setSelectedStep] = useState<WorkflowStep | null>(null)
  const [showStepDetails, setShowStepDetails] = useState(false)

  const getStepStatusColor = (status: WorkflowStep['status']) => {
    switch (status) {
      case 'completed':
        return 'bg-green-500'
      case 'running':
        return 'bg-blue-500'
      case 'failed':
        return 'bg-red-500'
      case 'pending':
        return 'bg-gray-300'
      case 'skipped':
        return 'bg-yellow-500'
      default:
        return 'bg-gray-300'
    }
  }

  const getStepStatusIcon = (status: WorkflowStep['status']) => {
    switch (status) {
      case 'completed':
        return '✓'
      case 'running':
        return '⟳'
      case 'failed':
        return '✗'
      case 'pending':
        return '○'
      case 'skipped':
        return '⊘'
      default:
        return '○'
    }
  }

  const handleStepClick = (step: WorkflowStep) => {
    setSelectedStep(step)
    setShowStepDetails(true)
    onStepClick?.(step)
  }

  const formatDuration = (startTime?: Date, endTime?: Date) => {
    if (!startTime) return 'Not started'
    if (!endTime) return 'In progress'
    
    const duration = endTime.getTime() - startTime.getTime()
    const minutes = Math.floor(duration / 60000)
    const seconds = Math.floor((duration % 60000) / 1000)
    
    return `${minutes}m ${seconds}s`
  }

  const buildDependencyGraph = () => {
    // Create a simple dependency visualization
    const stepMap = new Map(execution.steps.map(step => [step.id, step]))
    const dependencies: { from: string; to: string }[] = []
    
    // This would need to be enhanced with actual dependency information
    // For now, we'll show a simple linear flow
    for (let i = 0; i < execution.steps.length - 1; i++) {
      dependencies.push({
        from: execution.steps[i].id,
        to: execution.steps[i + 1].id
      })
    }
    
    return dependencies
  }

  return (
    <div className="space-y-6">
      {/* Workflow Overview */}
      <Card className="p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold">Workflow Steps</h3>
          <div className="text-sm text-gray-600">
            {execution.steps.filter(s => s.status === 'completed').length} of {execution.steps.length} completed
          </div>
        </div>

        {/* Progress Timeline */}
        <div className="relative">
          <div className="absolute left-6 top-0 bottom-0 w-0.5 bg-gray-200"></div>
          
          <div className="space-y-4">
            {execution.steps.map((step, index) => (
              <div
                key={step.id}
                className="relative flex items-start cursor-pointer hover:bg-gray-50 p-3 rounded-lg transition-colors"
                onClick={() => handleStepClick(step)}
              >
                {/* Step Icon */}
                <div className={`
                  relative z-10 flex items-center justify-center w-12 h-12 rounded-full text-white font-bold
                  ${getStepStatusColor(step.status)}
                `}>
                  {getStepStatusIcon(step.status)}
                </div>

                {/* Step Content */}
                <div className="ml-4 flex-1 min-w-0">
                  <div className="flex justify-between items-start">
                    <div>
                      <h4 className="font-medium text-gray-900">{step.name}</h4>
                      <p className="text-sm text-gray-600 capitalize">{step.type} step</p>
                    </div>
                    <div className="text-right text-sm text-gray-500">
                      <div>{formatDuration(step.startTime, step.endTime)}</div>
                      {step.status === 'running' && (
                        <div className="text-blue-600">{step.progress}%</div>
                      )}
                    </div>
                  </div>

                  {/* Progress Bar for Running Steps */}
                  {step.status === 'running' && (
                    <div className="mt-2">
                      <div className="w-full bg-gray-200 rounded-full h-1">
                        <div
                          className="bg-blue-600 h-1 rounded-full transition-all duration-300"
                          style={{ width: `${step.progress}%` }}
                        />
                      </div>
                    </div>
                  )}

                  {/* Error Message */}
                  {step.status === 'failed' && step.error && (
                    <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-sm text-red-700">
                      {step.error.message}
                    </div>
                  )}

                  {/* Chain of Thought Preview */}
                  {step.chainOfThought.length > 0 && (
                    <div className="mt-2 text-xs text-gray-500">
                      Latest reasoning: {step.chainOfThought[step.chainOfThought.length - 1]?.reasoning.substring(0, 100)}...
                    </div>
                  )}
                </div>

                {/* Connection Line to Next Step */}
                {index < execution.steps.length - 1 && (
                  <div className="absolute left-6 top-12 w-0.5 h-8 bg-gray-200"></div>
                )}
              </div>
            ))}
          </div>
        </div>
      </Card>

      {/* Step Details Modal */}
      <Modal
        isOpen={showStepDetails}
        onClose={() => setShowStepDetails(false)}
        title={selectedStep ? `Step Details: ${selectedStep.name}` : 'Step Details'}
        size="large"
      >
        {selectedStep && (
          <div className="space-y-6">
            {/* Step Overview */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Status</label>
                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium capitalize ${
                  selectedStep.status === 'completed' ? 'bg-green-100 text-green-800' :
                  selectedStep.status === 'running' ? 'bg-blue-100 text-blue-800' :
                  selectedStep.status === 'failed' ? 'bg-red-100 text-red-800' :
                  selectedStep.status === 'pending' ? 'bg-gray-100 text-gray-800' :
                  'bg-yellow-100 text-yellow-800'
                }`}>
                  {selectedStep.status}
                </span>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Type</label>
                <span className="text-sm text-gray-900 capitalize">{selectedStep.type}</span>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Progress</label>
                <span className="text-sm text-gray-900">{selectedStep.progress}%</span>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Duration</label>
                <span className="text-sm text-gray-900">
                  {formatDuration(selectedStep.startTime, selectedStep.endTime)}
                </span>
              </div>
            </div>

            {/* Parameters */}
            {selectedStep.parameters && Object.keys(selectedStep.parameters).length > 0 && (
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-2">Parameters</h4>
                <div className="bg-gray-50 rounded-lg p-3">
                  <pre className="text-xs text-gray-800 whitespace-pre-wrap">
                    {JSON.stringify(selectedStep.parameters, null, 2)}
                  </pre>
                </div>
              </div>
            )}

            {/* Results */}
            {selectedStep.result && (
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-2">Results</h4>
                <div className="space-y-3">
                  <div className="grid grid-cols-3 gap-4 text-sm">
                    <div>
                      <span className="text-gray-600">Success:</span>
                      <span className={`ml-2 font-medium ${
                        selectedStep.result.success ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {selectedStep.result.success ? 'Yes' : 'No'}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-600">Duration:</span>
                      <span className="ml-2 font-medium">
                        {Math.round(selectedStep.result.metrics.duration / 1000)}s
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-600">Quality:</span>
                      <span className="ml-2 font-medium">
                        {Math.round(selectedStep.result.metrics.quality.accuracy * 100)}%
                      </span>
                    </div>
                  </div>
                  
                  {selectedStep.result.data && (
                    <div>
                      <h5 className="text-xs font-medium text-gray-600 mb-1">Data</h5>
                      <div className="bg-gray-50 rounded-lg p-3 max-h-40 overflow-y-auto">
                        <pre className="text-xs text-gray-800 whitespace-pre-wrap">
                          {JSON.stringify(selectedStep.result.data, null, 2)}
                        </pre>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Chain of Thought */}
            {selectedStep.chainOfThought.length > 0 && (
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-2">Chain of Thought</h4>
                <div className="space-y-3 max-h-60 overflow-y-auto">
                  {selectedStep.chainOfThought.map((thought, index) => (
                    <div key={thought.id} className="border-l-2 border-blue-200 pl-3">
                      <div className="flex justify-between items-start mb-1">
                        <span className="text-xs font-medium text-blue-600">
                          Step {thought.step}
                        </span>
                        <span className="text-xs text-gray-500">
                          Confidence: {Math.round(thought.confidence * 100)}%
                        </span>
                      </div>
                      <p className="text-sm text-gray-800">{thought.reasoning}</p>
                      {thought.data && (
                        <div className="mt-1 text-xs text-gray-600">
                          <details>
                            <summary className="cursor-pointer">View data</summary>
                            <pre className="mt-1 bg-gray-50 p-2 rounded text-xs overflow-x-auto">
                              {JSON.stringify(thought.data, null, 2)}
                            </pre>
                          </details>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Error Details */}
            {selectedStep.error && (
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-2">Error Details</h4>
                <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                  <div className="text-sm text-red-800 font-medium mb-1">
                    {selectedStep.error.code}: {selectedStep.error.message}
                  </div>
                  {selectedStep.error.suggestions.length > 0 && (
                    <div className="mt-2">
                      <div className="text-xs text-red-700 font-medium mb-1">Suggestions:</div>
                      <ul className="text-xs text-red-700 list-disc list-inside">
                        {selectedStep.error.suggestions.map((suggestion, index) => (
                          <li key={index}>{suggestion}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Actions */}
            <div className="flex justify-end space-x-3">
              <Button variant="outline" onClick={() => setShowStepDetails(false)}>
                Close
              </Button>
              {selectedStep.status === 'failed' && selectedStep.error?.recoverable && (
                <Button onClick={() => {
                  // Implement retry logic
                  console.log('Retrying step:', selectedStep.id)
                }}>
                  Retry Step
                </Button>
              )}
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}

export default WorkflowStepVisualization