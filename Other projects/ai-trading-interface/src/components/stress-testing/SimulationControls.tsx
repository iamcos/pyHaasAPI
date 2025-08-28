import React from 'react'
import { StopIcon, ClockIcon } from '@heroicons/react/24/outline'
import { Card, CardHeader, CardContent, Button } from '@/components/ui'
import type { StressTestScenario } from '@/services/stressTestingService'

interface SimulationControlsProps {
  scenario: StressTestScenario
  progress: number
  isRunning: boolean
  onStop: () => void
  estimatedTimeRemaining: number
}

export function SimulationControls({ 
  scenario, 
  progress, 
  isRunning, 
  onStop, 
  estimatedTimeRemaining 
}: SimulationControlsProps) {
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader title={`Running: ${scenario.name}`} />
        <CardContent>
          <div className="space-y-6">
            {/* Progress Bar */}
            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium text-gray-700">
                  Simulation Progress
                </span>
                <span className="text-sm text-gray-600">
                  {progress.toFixed(1)}%
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3">
                <div 
                  className="bg-primary-600 h-3 rounded-full transition-all duration-300"
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>

            {/* Status Information */}
            <div className="grid grid-cols-2 gap-4">
              <div className="text-center p-4 bg-blue-50 rounded-lg">
                <ClockIcon className="h-8 w-8 text-blue-600 mx-auto mb-2" />
                <div className="text-lg font-semibold text-blue-900">
                  {formatTime(estimatedTimeRemaining)}
                </div>
                <div className="text-sm text-blue-600">Time Remaining</div>
              </div>
              
              <div className="text-center p-4 bg-green-50 rounded-lg">
                <div className="text-lg font-semibold text-green-900">
                  {scenario.duration} days
                </div>
                <div className="text-sm text-green-600">Scenario Duration</div>
              </div>
            </div>

            {/* Current Phase */}
            <div className="p-4 bg-gray-50 rounded-lg">
              <h4 className="font-medium text-gray-900 mb-2">Current Phase</h4>
              <div className="text-sm text-gray-600">
                {progress < 20 ? 'Initializing portfolio and market conditions...' :
                 progress < 50 ? 'Applying stress parameters to market data...' :
                 progress < 80 ? 'Running portfolio simulation under stress...' :
                 progress < 95 ? 'Calculating risk metrics and performance...' :
                 'Finalizing results and generating recommendations...'}
              </div>
            </div>

            {/* Active Parameters */}
            <div>
              <h4 className="font-medium text-gray-900 mb-3">Active Stress Parameters</h4>
              <div className="grid grid-cols-2 gap-3">
                {scenario.parameters.marketShock.enabled && (
                  <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                    <div className="text-sm font-medium text-red-800">Market Shock</div>
                    <div className="text-xs text-red-600 mt-1">
                      {(scenario.parameters.marketShock.magnitude * 100).toFixed(1)}% decline
                    </div>
                  </div>
                )}
                
                {scenario.parameters.volatilityChange.enabled && (
                  <div className="p-3 bg-orange-50 border border-orange-200 rounded-lg">
                    <div className="text-sm font-medium text-orange-800">Volatility Spike</div>
                    <div className="text-xs text-orange-600 mt-1">
                      {scenario.parameters.volatilityChange.multiplier}x increase
                    </div>
                  </div>
                )}
                
                {scenario.parameters.correlationChange.enabled && (
                  <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                    <div className="text-sm font-medium text-yellow-800">Correlation Change</div>
                    <div className="text-xs text-yellow-600 mt-1">
                      Target: {(scenario.parameters.correlationChange.newCorrelation * 100).toFixed(0)}%
                    </div>
                  </div>
                )}
                
                {scenario.parameters.liquidityImpact.enabled && (
                  <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                    <div className="text-sm font-medium text-blue-800">Liquidity Crisis</div>
                    <div className="text-xs text-blue-600 mt-1">
                      {(scenario.parameters.liquidityImpact.liquidityReduction * 100).toFixed(0)}% reduction
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Control Buttons */}
            <div className="flex justify-center">
              <Button
                onClick={onStop}
                variant="outline"
                className="flex items-center space-x-2 text-red-600 border-red-300 hover:bg-red-50"
                disabled={!isRunning}
              >
                <StopIcon className="h-4 w-4" />
                <span>Stop Simulation</span>
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}