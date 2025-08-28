import React from 'react'
import { 
  ArrowTrendingDownIcon,
  ClockIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon
} from '@heroicons/react/24/outline'
import { Card, CardHeader, CardContent } from '@/components/ui'
import type { DrawdownAnalysis } from '@/services/analyticsService'

interface DrawdownAnalysisPanelProps {
  drawdownAnalysis: DrawdownAnalysis
  loading?: boolean
}

export function DrawdownAnalysisPanel({ drawdownAnalysis, loading = false }: DrawdownAnalysisPanelProps) {
  if (loading) {
    return (
      <div className="animate-pulse space-y-6">
        <div className="h-8 bg-gray-200 rounded w-1/4"></div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="h-64 bg-gray-200 rounded"></div>
          <div className="h-64 bg-gray-200 rounded"></div>
        </div>
      </div>
    )
  }

  const getDrawdownColor = (drawdown: number) => {
    if (drawdown >= 0.15) return 'text-red-600'
    if (drawdown >= 0.1) return 'text-orange-600'
    if (drawdown >= 0.05) return 'text-yellow-600'
    return 'text-green-600'
  }

  const drawdownMetrics = [
    {
      label: 'Current Drawdown',
      value: drawdownAnalysis.currentDrawdown,
      format: 'percentage',
      icon: ArrowTrendingDownIcon,
      description: 'Current portfolio drawdown from peak'
    },
    {
      label: 'Maximum Drawdown',
      value: drawdownAnalysis.maxDrawdown,
      format: 'percentage',
      icon: ArrowTrendingDownIcon,
      description: 'Largest peak-to-trough decline'
    },
    {
      label: 'Average Drawdown',
      value: drawdownAnalysis.avgDrawdown,
      format: 'percentage',
      icon: ArrowTrendingDownIcon,
      description: 'Average of all drawdown periods'
    },
    {
      label: 'Drawdown Frequency',
      value: drawdownAnalysis.drawdownFrequency,
      format: 'percentage',
      icon: ClockIcon,
      description: 'Percentage of time in drawdown'
    }
  ]

  const durationMetrics = [
    {
      label: 'Current Duration',
      value: drawdownAnalysis.drawdownDuration,
      format: 'days',
      description: 'Days in current drawdown'
    },
    {
      label: 'Max Duration',
      value: drawdownAnalysis.maxDrawdownDuration,
      format: 'days',
      description: 'Longest drawdown period'
    },
    {
      label: 'Avg Duration',
      value: drawdownAnalysis.avgDrawdownDuration,
      format: 'days',
      description: 'Average drawdown duration'
    },
    {
      label: 'Recovery Time',
      value: drawdownAnalysis.recoveryTime,
      format: 'days',
      description: 'Time to recover from current drawdown'
    },
    {
      label: 'Avg Recovery',
      value: drawdownAnalysis.avgRecoveryTime,
      format: 'days',
      description: 'Average recovery time'
    }
  ]

  const formatValue = (value: number, format: string) => {
    switch (format) {
      case 'percentage':
        return `${(value * 100).toFixed(2)}%`
      case 'days':
        return `${value} days`
      default:
        return value.toString()
    }
  }

  return (
    <div className="space-y-6">
      {/* Drawdown Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {drawdownMetrics.map((metric, index) => {
          const Icon = metric.icon
          return (
            <Card key={index} hover>
              <CardContent className="p-4">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-medium text-gray-900">{metric.label}</h4>
                  <Icon className="h-5 w-5 text-gray-400" />
                </div>
                <div className={`text-2xl font-bold ${getDrawdownColor(metric.value)}`}>
                  -{formatValue(metric.value, metric.format)}
                </div>
                <p className="text-xs text-gray-500 mt-2">
                  {metric.description}
                </p>
              </CardContent>
            </Card>
          )
        })}
      </div>

      {/* Underwater Curve */}
      <Card>
        <CardHeader 
          title="Underwater Curve"
          subtitle="Portfolio drawdown over time"
        />
        <CardContent>
          <div className="h-64 bg-gray-50 rounded-lg flex items-center justify-center mb-6">
            <div className="text-center">
              <ArrowTrendingDownIcon className="h-12 w-12 text-gray-400 mx-auto mb-2" />
              <p className="text-gray-600">Underwater curve chart would be rendered here</p>
              <p className="text-sm text-gray-500 mt-1">
                Showing {drawdownAnalysis.underwaterCurve.length} data points
              </p>
            </div>
          </div>

          {/* Recent Drawdown Points */}
          <div className="space-y-2">
            <h4 className="font-medium text-gray-900 mb-3">Recent Drawdown History</h4>
            {drawdownAnalysis.underwaterCurve.slice(-10).map((point, index) => (
              <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                <div className="flex items-center space-x-3">
                  <div className={`w-3 h-3 rounded-full ${
                    point.inDrawdown ? 'bg-red-500' : 'bg-green-500'
                  }`} />
                  <span className="text-sm text-gray-600">
                    {point.timestamp.toLocaleDateString()}
                  </span>
                </div>
                <div className="text-right">
                  <div className={`text-sm font-medium ${
                    point.drawdown > 0 ? 'text-red-600' : 'text-green-600'
                  }`}>
                    {point.drawdown > 0 ? '-' : ''}{(point.drawdown * 100).toFixed(2)}%
                  </div>
                  {point.duration > 0 && (
                    <div className="text-xs text-gray-500">
                      {point.duration} days
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Duration Analysis */}
      <Card>
        <CardHeader title="Drawdown Duration Analysis" />
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
            {durationMetrics.map((metric, index) => (
              <div key={index} className="text-center p-4 bg-gray-50 rounded-lg">
                <div className="text-lg font-semibold text-gray-900">
                  {formatValue(metric.value, metric.format)}
                </div>
                <div className="text-sm font-medium text-gray-700 mt-1">
                  {metric.label}
                </div>
                <div className="text-xs text-gray-500 mt-2">
                  {metric.description}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Risk Assessment */}
      <Card>
        <CardHeader title="Drawdown Risk Assessment" />
        <CardContent>
          <div className="space-y-4">
            {/* Current Drawdown Warning */}
            {drawdownAnalysis.currentDrawdown > 0.1 && (
              <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                <div className="flex items-start space-x-3">
                  <ExclamationTriangleIcon className="h-5 w-5 text-red-600 mt-0.5" />
                  <div>
                    <h4 className="font-medium text-red-800">Significant Current Drawdown</h4>
                    <p className="text-sm text-red-700 mt-1">
                      Current drawdown of {(drawdownAnalysis.currentDrawdown * 100).toFixed(1)}% 
                      is above the 10% threshold. Consider reviewing risk management strategies 
                      and position sizing.
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Max Drawdown Assessment */}
            {drawdownAnalysis.maxDrawdown > 0.2 && (
              <div className="p-4 bg-orange-50 border border-orange-200 rounded-lg">
                <div className="flex items-start space-x-3">
                  <ExclamationTriangleIcon className="h-5 w-5 text-orange-600 mt-0.5" />
                  <div>
                    <h4 className="font-medium text-orange-800">High Maximum Drawdown</h4>
                    <p className="text-sm text-orange-700 mt-1">
                      Maximum drawdown of {(drawdownAnalysis.maxDrawdown * 100).toFixed(1)}% 
                      indicates high portfolio volatility. Consider implementing stop-loss 
                      mechanisms or reducing leverage.
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Long Duration Warning */}
            {drawdownAnalysis.maxDrawdownDuration > 30 && (
              <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                <div className="flex items-start space-x-3">
                  <ClockIcon className="h-5 w-5 text-yellow-600 mt-0.5" />
                  <div>
                    <h4 className="font-medium text-yellow-800">Extended Drawdown Periods</h4>
                    <p className="text-sm text-yellow-700 mt-1">
                      Maximum drawdown duration of {drawdownAnalysis.maxDrawdownDuration} days 
                      suggests prolonged recovery periods. Consider strategies that can adapt 
                      to different market conditions.
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Positive Assessment */}
            {drawdownAnalysis.maxDrawdown < 0.1 && drawdownAnalysis.avgRecoveryTime < 10 && (
              <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                <div className="flex items-start space-x-3">
                  <InformationCircleIcon className="h-5 w-5 text-green-600 mt-0.5" />
                  <div>
                    <h4 className="font-medium text-green-800">Good Drawdown Control</h4>
                    <p className="text-sm text-green-700 mt-1">
                      Maximum drawdown of {(drawdownAnalysis.maxDrawdown * 100).toFixed(1)}% 
                      and average recovery time of {drawdownAnalysis.avgRecoveryTime} days 
                      indicate good risk management and portfolio resilience.
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* General Guidelines */}
            <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <div className="flex items-start space-x-3">
                <InformationCircleIcon className="h-5 w-5 text-blue-600 mt-0.5" />
                <div>
                  <h4 className="font-medium text-blue-800">Drawdown Management Guidelines</h4>
                  <ul className="text-sm text-blue-700 mt-1 space-y-1">
                    <li>• Maximum drawdown should typically stay below 15-20%</li>
                    <li>• Frequent small drawdowns are preferable to rare large ones</li>
                    <li>• Recovery time should be reasonable relative to holding periods</li>
                    <li>• Consider position sizing and stop-loss rules to limit drawdowns</li>
                    <li>• Monitor correlation during stress periods as it tends to increase</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Drawdown Statistics */}
      <Card>
        <CardHeader title="Statistical Summary" />
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center p-3 bg-gray-50 rounded-lg">
              <div className="text-lg font-semibold text-gray-900">
                {((1 - drawdownAnalysis.drawdownFrequency) * 100).toFixed(1)}%
              </div>
              <div className="text-xs text-gray-500">Time Above Water</div>
            </div>
            
            <div className="text-center p-3 bg-gray-50 rounded-lg">
              <div className="text-lg font-semibold text-gray-900">
                {(drawdownAnalysis.maxDrawdown / drawdownAnalysis.avgDrawdown).toFixed(1)}x
              </div>
              <div className="text-xs text-gray-500">Max/Avg Ratio</div>
            </div>
            
            <div className="text-center p-3 bg-gray-50 rounded-lg">
              <div className="text-lg font-semibold text-gray-900">
                {(drawdownAnalysis.avgRecoveryTime / drawdownAnalysis.avgDrawdownDuration).toFixed(1)}x
              </div>
              <div className="text-xs text-gray-500">Recovery/Duration Ratio</div>
            </div>
            
            <div className="text-center p-3 bg-gray-50 rounded-lg">
              <div className="text-lg font-semibold text-gray-900">
                {Math.round(365 * drawdownAnalysis.drawdownFrequency / drawdownAnalysis.avgDrawdownDuration)}
              </div>
              <div className="text-xs text-gray-500">Est. Annual Drawdowns</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}