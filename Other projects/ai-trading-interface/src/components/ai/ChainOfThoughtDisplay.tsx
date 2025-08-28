import React, { useState } from 'react'
import { ChevronDownIcon, ChevronRightIcon, CheckCircleIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import type { ChainOfThoughtStep, Alternative } from '@/types'

interface ChainOfThoughtDisplayProps {
  steps: ChainOfThoughtStep[]
  title?: string
  showConfidence?: boolean
  showAlternatives?: boolean
  onStepClick?: (step: ChainOfThoughtStep) => void
  className?: string
}

export const ChainOfThoughtDisplay: React.FC<ChainOfThoughtDisplayProps> = ({
  steps,
  title = "Chain of Thought",
  showConfidence = true,
  showAlternatives = true,
  onStepClick,
  className = ""
}) => {
  const [expandedSteps, setExpandedSteps] = useState<Set<string>>(new Set())
  const [showAllSteps, setShowAllSteps] = useState(false)

  const toggleStep = (stepId: string) => {
    const newExpanded = new Set(expandedSteps)
    if (newExpanded.has(stepId)) {
      newExpanded.delete(stepId)
    } else {
      newExpanded.add(stepId)
    }
    setExpandedSteps(newExpanded)
  }

  const getConfidenceColor = (confidence: number): string => {
    if (confidence >= 0.8) return 'text-green-600 bg-green-50'
    if (confidence >= 0.6) return 'text-yellow-600 bg-yellow-50'
    return 'text-red-600 bg-red-50'
  }

  const getConfidenceIcon = (confidence: number) => {
    if (confidence >= 0.7) {
      return <CheckCircleIcon className="h-4 w-4 text-green-500" />
    }
    return <ExclamationTriangleIcon className="h-4 w-4 text-yellow-500" />
  }

  const displaySteps = showAllSteps ? steps : steps.slice(0, 3)

  if (steps.length === 0) {
    return (
      <Card className={`p-4 ${className}`}>
        <div className="text-center text-gray-500">
          <div className="text-sm">No reasoning steps available</div>
        </div>
      </Card>
    )
  }

  return (
    <Card className={`${className}`}>
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
          <div className="flex items-center space-x-2">
            {steps.length > 3 && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowAllSteps(!showAllSteps)}
              >
                {showAllSteps ? `Show Less` : `Show All (${steps.length})`}
              </Button>
            )}
            <div className="text-sm text-gray-500">
              {steps.length} step{steps.length !== 1 ? 's' : ''}
            </div>
          </div>
        </div>
      </div>

      <div className="p-4 space-y-3">
        {displaySteps.map((step, index) => (
          <ChainOfThoughtStep
            key={step.id}
            step={step}
            index={index}
            isExpanded={expandedSteps.has(step.id)}
            onToggle={() => toggleStep(step.id)}
            onClick={() => onStepClick?.(step)}
            showConfidence={showConfidence}
            showAlternatives={showAlternatives}
            getConfidenceColor={getConfidenceColor}
            getConfidenceIcon={getConfidenceIcon}
          />
        ))}

        {!showAllSteps && steps.length > 3 && (
          <div className="text-center pt-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowAllSteps(true)}
              className="text-blue-600 hover:text-blue-800"
            >
              Show {steps.length - 3} more steps
            </Button>
          </div>
        )}
      </div>
    </Card>
  )
}

interface ChainOfThoughtStepProps {
  step: ChainOfThoughtStep
  index: number
  isExpanded: boolean
  onToggle: () => void
  onClick?: () => void
  showConfidence: boolean
  showAlternatives: boolean
  getConfidenceColor: (confidence: number) => string
  getConfidenceIcon: (confidence: number) => React.ReactNode
}

const ChainOfThoughtStep: React.FC<ChainOfThoughtStepProps> = ({
  step,
  index,
  isExpanded,
  onToggle,
  onClick,
  showConfidence,
  showAlternatives,
  getConfidenceColor,
  getConfidenceIcon
}) => {
  const hasDetails = step.data || (step.alternatives && step.alternatives.length > 0)

  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden">
      <div 
        className={`p-3 cursor-pointer hover:bg-gray-50 transition-colors ${
          onClick ? 'cursor-pointer' : ''
        }`}
        onClick={onClick}
      >
        <div className="flex items-start space-x-3">
          <div className="flex-shrink-0">
            <div className="flex items-center justify-center w-6 h-6 bg-blue-100 text-blue-800 rounded-full text-sm font-medium">
              {step.step}
            </div>
          </div>

          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <p className="text-sm text-gray-900 leading-relaxed">
                  {step.reasoning}
                </p>
                
                <div className="flex items-center space-x-4 mt-2">
                  {showConfidence && (
                    <div className="flex items-center space-x-1">
                      {getConfidenceIcon(step.confidence)}
                      <span className={`text-xs px-2 py-1 rounded-full ${getConfidenceColor(step.confidence)}`}>
                        {(step.confidence * 100).toFixed(0)}% confidence
                      </span>
                    </div>
                  )}
                  
                  <div className="text-xs text-gray-500">
                    {step.timestamp.toLocaleTimeString()}
                  </div>
                </div>
              </div>

              {hasDetails && (
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    onToggle()
                  }}
                  className="ml-2 p-1 hover:bg-gray-100 rounded"
                >
                  {isExpanded ? (
                    <ChevronDownIcon className="h-4 w-4 text-gray-500" />
                  ) : (
                    <ChevronRightIcon className="h-4 w-4 text-gray-500" />
                  )}
                </button>
              )}
            </div>
          </div>
        </div>
      </div>

      {isExpanded && hasDetails && (
        <div className="border-t border-gray-200 bg-gray-50 p-3">
          {step.data && (
            <div className="mb-3">
              <h4 className="text-sm font-medium text-gray-700 mb-2">Supporting Data</h4>
              <div className="bg-white rounded border p-2">
                <pre className="text-xs text-gray-600 whitespace-pre-wrap overflow-x-auto">
                  {typeof step.data === 'string' ? step.data : JSON.stringify(step.data, null, 2)}
                </pre>
              </div>
            </div>
          )}

          {showAlternatives && step.alternatives && step.alternatives.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-2">
                Alternative Considerations ({step.alternatives.length})
              </h4>
              <div className="space-y-2">
                {step.alternatives.map((alt) => (
                  <AlternativeDisplay key={alt.id} alternative={alt} />
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

interface AlternativeDisplayProps {
  alternative: Alternative
}

const AlternativeDisplay: React.FC<AlternativeDisplayProps> = ({ alternative }) => {
  return (
    <div className="bg-white border border-gray-200 rounded p-2">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm text-gray-800">{alternative.description}</p>
          <p className="text-xs text-gray-600 mt-1">{alternative.reasoning}</p>
        </div>
        <div className="ml-2 flex-shrink-0">
          <span className="text-xs px-2 py-1 bg-gray-100 text-gray-600 rounded">
            {(alternative.confidence * 100).toFixed(0)}%
          </span>
        </div>
      </div>
    </div>
  )
}

export default ChainOfThoughtDisplay