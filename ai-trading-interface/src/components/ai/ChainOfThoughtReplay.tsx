import React, { useState, useEffect, useCallback } from 'react'
import { 
  PlayIcon, 
  PauseIcon, 
  StopIcon, 
  ForwardIcon, 
  BackwardIcon,
  AdjustmentsHorizontalIcon
} from '@heroicons/react/24/outline'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { ChainOfThoughtDisplay } from './ChainOfThoughtDisplay'
import type { ChainOfThoughtStep } from '@/types'

interface ChainOfThoughtReplayProps {
  steps: ChainOfThoughtStep[]
  onStepChange?: (currentStep: number, step: ChainOfThoughtStep) => void
  className?: string
}

export const ChainOfThoughtReplay: React.FC<ChainOfThoughtReplayProps> = ({
  steps,
  onStepChange,
  className = ""
}) => {
  const [currentStepIndex, setCurrentStepIndex] = useState(0)
  const [isPlaying, setIsPlaying] = useState(false)
  const [playbackSpeed, setPlaybackSpeed] = useState(1) // 0.5x, 1x, 2x, 4x
  const [showControls, setShowControls] = useState(true)

  // Auto-advance when playing
  useEffect(() => {
    if (!isPlaying || currentStepIndex >= steps.length - 1) {
      return
    }

    const interval = setInterval(() => {
      setCurrentStepIndex(prev => {
        const next = prev + 1
        if (next >= steps.length) {
          setIsPlaying(false)
          return prev
        }
        return next
      })
    }, 2000 / playbackSpeed) // Base speed: 2 seconds per step

    return () => clearInterval(interval)
  }, [isPlaying, currentStepIndex, steps.length, playbackSpeed])

  // Notify parent of step changes
  useEffect(() => {
    if (steps[currentStepIndex] && onStepChange) {
      onStepChange(currentStepIndex, steps[currentStepIndex])
    }
  }, [currentStepIndex, steps, onStepChange])

  const handlePlay = useCallback(() => {
    if (currentStepIndex >= steps.length - 1) {
      setCurrentStepIndex(0)
    }
    setIsPlaying(true)
  }, [currentStepIndex, steps.length])

  const handlePause = useCallback(() => {
    setIsPlaying(false)
  }, [])

  const handleStop = useCallback(() => {
    setIsPlaying(false)
    setCurrentStepIndex(0)
  }, [])

  const handleNext = useCallback(() => {
    setCurrentStepIndex(prev => Math.min(prev + 1, steps.length - 1))
  }, [steps.length])

  const handlePrevious = useCallback(() => {
    setCurrentStepIndex(prev => Math.max(prev - 1, 0))
  }, [])

  const handleStepClick = useCallback((stepIndex: number) => {
    setCurrentStepIndex(stepIndex)
    setIsPlaying(false)
  }, [])

  const getVisibleSteps = (): ChainOfThoughtStep[] => {
    return steps.slice(0, currentStepIndex + 1)
  }

  const getProgressPercentage = (): number => {
    if (steps.length === 0) return 0
    return ((currentStepIndex + 1) / steps.length) * 100
  }

  if (steps.length === 0) {
    return (
      <Card className={`p-8 text-center ${className}`}>
        <div className="text-gray-500">
          <div className="text-sm">No reasoning steps to replay</div>
        </div>
      </Card>
    )
  }

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Controls */}
      {showControls && (
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              {/* Playback Controls */}
              <div className="flex items-center space-x-1">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handlePrevious}
                  disabled={currentStepIndex === 0}
                >
                  <BackwardIcon className="h-4 w-4" />
                </Button>

                {isPlaying ? (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handlePause}
                  >
                    <PauseIcon className="h-4 w-4" />
                  </Button>
                ) : (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handlePlay}
                    disabled={currentStepIndex >= steps.length - 1}
                  >
                    <PlayIcon className="h-4 w-4" />
                  </Button>
                )}

                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleStop}
                >
                  <StopIcon className="h-4 w-4" />
                </Button>

                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleNext}
                  disabled={currentStepIndex >= steps.length - 1}
                >
                  <ForwardIcon className="h-4 w-4" />
                </Button>
              </div>

              {/* Speed Control */}
              <div className="flex items-center space-x-2 ml-4">
                <AdjustmentsHorizontalIcon className="h-4 w-4 text-gray-500" />
                <select
                  value={playbackSpeed}
                  onChange={(e) => setPlaybackSpeed(parseFloat(e.target.value))}
                  className="text-sm border border-gray-300 rounded px-2 py-1"
                >
                  <option value={0.5}>0.5x</option>
                  <option value={1}>1x</option>
                  <option value={2}>2x</option>
                  <option value={4}>4x</option>
                </select>
              </div>
            </div>

            {/* Progress Info */}
            <div className="flex items-center space-x-4">
              <div className="text-sm text-gray-600">
                Step {currentStepIndex + 1} of {steps.length}
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowControls(false)}
              >
                Hide Controls
              </Button>
            </div>
          </div>

          {/* Progress Bar */}
          <div className="mt-4">
            <div className="flex items-center space-x-2">
              <div className="flex-1 bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${getProgressPercentage()}%` }}
                />
              </div>
              <div className="text-xs text-gray-500 w-12 text-right">
                {getProgressPercentage().toFixed(0)}%
              </div>
            </div>

            {/* Step Markers */}
            <div className="flex justify-between mt-2">
              {steps.map((step, index) => (
                <button
                  key={step.id}
                  onClick={() => handleStepClick(index)}
                  className={`w-3 h-3 rounded-full border-2 transition-colors ${
                    index <= currentStepIndex
                      ? 'bg-blue-500 border-blue-500'
                      : 'bg-white border-gray-300 hover:border-gray-400'
                  }`}
                  title={`Step ${step.step}: ${step.reasoning.substring(0, 50)}...`}
                />
              ))}
            </div>
          </div>
        </Card>
      )}

      {/* Show Controls Button (when hidden) */}
      {!showControls && (
        <div className="flex justify-center">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowControls(true)}
          >
            Show Controls
          </Button>
        </div>
      )}

      {/* Current Step Highlight */}
      <Card className="p-4 bg-blue-50 border-blue-200">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-sm font-medium text-blue-900">
            Current Step ({currentStepIndex + 1}/{steps.length})
          </h3>
          <div className="text-xs text-blue-700">
            {steps[currentStepIndex]?.timestamp.toLocaleTimeString()}
          </div>
        </div>
        
        {steps[currentStepIndex] && (
          <div className="space-y-2">
            <p className="text-sm text-blue-800">
              {steps[currentStepIndex].reasoning}
            </p>
            
            <div className="flex items-center space-x-4">
              <div className="text-xs text-blue-600">
                Confidence: {(steps[currentStepIndex].confidence * 100).toFixed(0)}%
              </div>
              
              {steps[currentStepIndex].data && (
                <div className="text-xs text-blue-600">
                  Has supporting data
                </div>
              )}
              
              {steps[currentStepIndex].alternatives && steps[currentStepIndex].alternatives!.length > 0 && (
                <div className="text-xs text-blue-600">
                  {steps[currentStepIndex].alternatives!.length} alternatives considered
                </div>
              )}
            </div>
          </div>
        )}
      </Card>

      {/* Chain of Thought Display */}
      <ChainOfThoughtDisplay
        steps={getVisibleSteps()}
        title={`Reasoning Replay (${getVisibleSteps().length}/${steps.length} steps)`}
        showConfidence={true}
        showAlternatives={true}
        onStepClick={(step) => {
          const index = steps.findIndex(s => s.id === step.id)
          if (index !== -1) {
            handleStepClick(index)
          }
        }}
      />

      {/* Replay Statistics */}
      <Card className="p-4">
        <h3 className="text-sm font-medium text-gray-900 mb-3">Replay Statistics</h3>
        
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <div className="text-gray-500">Total Steps</div>
            <div className="font-medium">{steps.length}</div>
          </div>
          
          <div>
            <div className="text-gray-500">Avg Confidence</div>
            <div className="font-medium">
              {steps.length > 0 
                ? (steps.reduce((sum, s) => sum + s.confidence, 0) / steps.length * 100).toFixed(0) + '%'
                : '0%'
              }
            </div>
          </div>
          
          <div>
            <div className="text-gray-500">Duration</div>
            <div className="font-medium">
              {steps.length > 1 
                ? Math.round((new Date(steps[steps.length - 1].timestamp).getTime() - 
                             new Date(steps[0].timestamp).getTime()) / 1000) + 's'
                : '0s'
              }
            </div>
          </div>
          
          <div>
            <div className="text-gray-500">With Alternatives</div>
            <div className="font-medium">
              {steps.filter(s => s.alternatives && s.alternatives.length > 0).length}
            </div>
          </div>
        </div>
      </Card>
    </div>
  )
}

export default ChainOfThoughtReplay