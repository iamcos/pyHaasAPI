import React, { useState } from 'react'
import { 
  ChartBarIcon,
  TrophyIcon,
  ClockIcon,
  CurrencyDollarIcon
} from '@heroicons/react/24/outline'
import { Card, CardHeader, CardContent } from '@/components/ui'
import type { PerformanceAnalysis } from '@/services/analyticsService'

interface PerformanceAnalysisPanelProps {
  analysis: PerformanceAnalysis
  loading?: boolean
}

export function PerformanceAnalysisPanel({ analysis, loading = false }: PerformanceAnalysisPanelProps) {
  const [selectedView, setSelectedView] = useState<'timeseries' | 'attribution' | 'benchmark' | 'rolling'>('timeseries')

  if (loading) {
    return (
      <div className="animate-pulse space-y-6">
        <div className="h-8 bg-gray-200 rounded w-1/4"></div>
        <div className="h-64 bg-gray-200 rounded"></div>
      </div>
    )
  }

  const viewOptions = [
    { key: 'timeseries' as const, label: 'Time Series', icon: ChartBarIcon },
    { key: 'attribution' as const, label: 'Attribution', icon: TrophyIcon },
    { key: 'benchmark' as const, label: 'Benchmark', icon: CurrencyDollarIcon },
    { key: 'rolling' as const, label: 'Rolling Metrics', icon: ClockIcon }
  ]

  const renderTimeSeriesView = () => (
    <div className="space-y-6">
      {/* Time Series Chart */}
      <Card>
        <CardHeader title="Portfolio Performance Over Time" />
        <CardContent>
          <div className="h-64 bg-gray-50 rounded-lg flex items-center justify-center">
            <div className="text-center">
              <ChartBarIcon className="h-12 w-12 text-gray-400 mx-auto mb-2" />
              <p className="text-gray-600">Interactive time series chart would be rendered here</p>
              <p className="text-sm text-gray-500 mt-1">
                Showing {analysis.timeSeriesData.length} data points
              </p>
            </div>
          </div>
          
          {/* Key Metrics */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
            <div className="text-center p-3 bg-gray-50 rounded-lg">
              <div className="text-lg font-semibold text-gray-900">
                {(analysis.periodReturns.inception * 100).toFixed(1)}%
              </div>
              <div className="text-xs text-gray-500">Total Return</div>
            </div>
            <div className="text-center p-3 bg-gray-50 rounded-lg">
              <div className="text-lg font-semibold text-gray-900">
                {(analysis.periodReturns.yearly * 100).toFixed(1)}%
              </div>
              <div className="text-xs text-gray-500">Annualized</div>
            </div>
            <div className="text-center p-3 bg-gray-50 rounded-lg">
              <div className="text-lg font-semibold text-gray-900">
                {(analysis.periodReturns.monthly * 100).toFixed(1)}%
              </div>
              <div className="text-xs text-gray-500">Monthly</div>
            </div>
            <div className="text-center p-3 bg-gray-50 rounded-lg">
              <div className="text-lg font-semibold text-gray-900">
                {(analysis.periodReturns.daily * 100).toFixed(2)}%
              </div>
              <div className="text-xs text-gray-500">Daily Avg</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )

  const renderAttributionView = () => (
    <div className="space-y-6">
      {/* Asset Attribution */}
      <Card>
        <CardHeader title="Performance Attribution by Asset" />
        <CardContent>
          <div className="space-y-3">
            {analysis.performanceAttribution.assetContribution.map((asset, index) => (
              <div key={index} className="flex items-center justify-between p-3 border border-gray-200 rounded-lg">
                <div className="flex items-center space-x-3">
                  <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                  <div>
                    <div className="font-medium text-gray-900">{asset.asset}</div>
                    <div className="text-sm text-gray-500">
                      Weight: {(asset.weight * 100).toFixed(1)}%
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <div className={`font-medium ${
                    asset.contribution >= 0 ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {asset.contribution >= 0 ? '+' : ''}{(asset.contribution * 100).toFixed(2)}%
                  </div>
                  <div className="text-sm text-gray-500">
                    Return: {(asset.return * 100).toFixed(1)}%
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Strategy Attribution */}
      <Card>
        <CardHeader title="Performance Attribution by Strategy" />
        <CardContent>
          <div className="space-y-3">
            {analysis.performanceAttribution.strategyContribution.map((strategy, index) => (
              <div key={index} className="flex items-center justify-between p-3 border border-gray-200 rounded-lg">
                <div className="flex items-center space-x-3">
                  <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                  <div>
                    <div className="font-medium text-gray-900">{strategy.strategyName}</div>
                    <div className="text-sm text-gray-500">
                      Allocation: {(strategy.allocation * 100).toFixed(1)}%
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <div className={`font-medium ${
                    strategy.contribution >= 0 ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {strategy.contribution >= 0 ? '+' : ''}{(strategy.contribution * 100).toFixed(2)}%
                  </div>
                  <div className="text-sm text-gray-500">
                    Sharpe: {strategy.sharpeRatio.toFixed(2)}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )

  const renderBenchmarkView = () => (
    <Card>
      <CardHeader title="Benchmark Comparison" />
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Performance Comparison */}
          <div className="space-y-4">
            <h4 className="font-medium text-gray-900">Performance Metrics</h4>
            
            <div className="space-y-3">
              <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                <span className="text-sm text-gray-600">Portfolio Return</span>
                <span className="font-medium text-green-600">
                  {(analysis.benchmarkComparison.portfolioReturn * 100).toFixed(1)}%
                </span>
              </div>
              
              <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                <span className="text-sm text-gray-600">{analysis.benchmarkComparison.benchmarkName}</span>
                <span className="font-medium text-gray-900">
                  {(analysis.benchmarkComparison.benchmarkReturn * 100).toFixed(1)}%
                </span>
              </div>
              
              <div className="flex justify-between items-center p-3 bg-green-50 rounded-lg border border-green-200">
                <span className="text-sm text-green-700">Alpha (Excess Return)</span>
                <span className="font-medium text-green-700">
                  +{(analysis.benchmarkComparison.alpha * 100).toFixed(1)}%
                </span>
              </div>
            </div>
          </div>

          {/* Risk Metrics */}
          <div className="space-y-4">
            <h4 className="font-medium text-gray-900">Risk Metrics</h4>
            
            <div className="space-y-3">
              <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                <span className="text-sm text-gray-600">Beta</span>
                <span className="font-medium text-gray-900">
                  {analysis.benchmarkComparison.beta.toFixed(2)}
                </span>
              </div>
              
              <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                <span className="text-sm text-gray-600">Tracking Error</span>
                <span className="font-medium text-gray-900">
                  {(analysis.benchmarkComparison.trackingError * 100).toFixed(1)}%
                </span>
              </div>
              
              <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                <span className="text-sm text-gray-600">Information Ratio</span>
                <span className="font-medium text-gray-900">
                  {analysis.benchmarkComparison.informationRatio.toFixed(2)}
                </span>
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )

  const renderRollingView = () => (
    <Card>
      <CardHeader title="Rolling Performance Metrics" />
      <CardContent>
        <div className="space-y-6">
          {/* Rolling Charts Placeholder */}
          <div className="h-48 bg-gray-50 rounded-lg flex items-center justify-center">
            <div className="text-center">
              <ClockIcon className="h-12 w-12 text-gray-400 mx-auto mb-2" />
              <p className="text-gray-600">Rolling metrics charts would be rendered here</p>
              <p className="text-sm text-gray-500 mt-1">
                {analysis.rollingMetrics.window}-day rolling window
              </p>
            </div>
          </div>

          {/* Current Rolling Metrics */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center p-3 bg-gray-50 rounded-lg">
              <div className="text-lg font-semibold text-gray-900">
                {analysis.rollingMetrics.sharpeRatio[analysis.rollingMetrics.sharpeRatio.length - 1]?.toFixed(2) || 'N/A'}
              </div>
              <div className="text-xs text-gray-500">Current Sharpe</div>
            </div>
            
            <div className="text-center p-3 bg-gray-50 rounded-lg">
              <div className="text-lg font-semibold text-gray-900">
                {((analysis.rollingMetrics.volatility[analysis.rollingMetrics.volatility.length - 1] || 0) * 100).toFixed(1)}%
              </div>
              <div className="text-xs text-gray-500">Current Volatility</div>
            </div>
            
            <div className="text-center p-3 bg-gray-50 rounded-lg">
              <div className="text-lg font-semibold text-red-600">
                -{((analysis.rollingMetrics.maxDrawdown[analysis.rollingMetrics.maxDrawdown.length - 1] || 0) * 100).toFixed(1)}%
              </div>
              <div className="text-xs text-gray-500">Current Drawdown</div>
            </div>
            
            <div className="text-center p-3 bg-gray-50 rounded-lg">
              <div className="text-lg font-semibold text-gray-900">
                {analysis.rollingMetrics.calmarRatio[analysis.rollingMetrics.calmarRatio.length - 1]?.toFixed(2) || 'N/A'}
              </div>
              <div className="text-xs text-gray-500">Current Calmar</div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )

  return (
    <div className="space-y-6">
      {/* View Selector */}
      <div className="flex space-x-1 bg-gray-100 rounded-lg p-1">
        {viewOptions.map(option => {
          const Icon = option.icon
          return (
            <button
              key={option.key}
              onClick={() => setSelectedView(option.key)}
              className={`flex items-center space-x-2 px-4 py-2 rounded-md text-sm font-medium transition-colors flex-1 justify-center ${
                selectedView === option.key
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              <Icon className="h-4 w-4" />
              <span>{option.label}</span>
            </button>
          )
        })}
      </div>

      {/* View Content */}
      {selectedView === 'timeseries' && renderTimeSeriesView()}
      {selectedView === 'attribution' && renderAttributionView()}
      {selectedView === 'benchmark' && renderBenchmarkView()}
      {selectedView === 'rolling' && renderRollingView()}
    </div>
  )
}