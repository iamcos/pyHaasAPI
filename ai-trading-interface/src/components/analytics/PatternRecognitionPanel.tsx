import React, { useState } from 'react'
import { 
  MagnifyingGlassIcon,
  TrendingUpIcon,
  CalendarIcon,
  ExclamationTriangleIcon,
  LightBulbIcon,
  ChartBarIcon
} from '@heroicons/react/24/outline'
import { Card, CardHeader, CardContent } from '@/components/ui'
import type { PatternAnalysis } from '@/services/analyticsService'

interface PatternRecognitionPanelProps {
  patternAnalysis: PatternAnalysis
  loading?: boolean
}

export function PatternRecognitionPanel({ patternAnalysis, loading = false }: PatternRecognitionPanelProps) {
  const [selectedView, setSelectedView] = useState<'trends' | 'seasonal' | 'volatility' | 'anomalies' | 'signals'>('trends')

  if (loading) {
    return (
      <div className="animate-pulse space-y-6">
        <div className="h-8 bg-gray-200 rounded w-1/4"></div>
        <div className="h-64 bg-gray-200 rounded"></div>
      </div>
    )
  }

  const getTrendColor = (type: string) => {
    switch (type) {
      case 'uptrend': return 'text-green-600 bg-green-50 border-green-200'
      case 'downtrend': return 'text-red-600 bg-red-50 border-red-200'
      default: return 'text-gray-600 bg-gray-50 border-gray-200'
    }
  }

  const getTrendIcon = (type: string) => {
    switch (type) {
      case 'uptrend': return TrendingUpIcon
      case 'downtrend': return TrendingUpIcon // Will be rotated
      default: return ChartBarIcon
    }
  }

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600'
    if (confidence >= 0.6) return 'text-yellow-600'
    return 'text-red-600'
  }

  const renderTrendsView = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader title="Identified Trend Patterns" />
        <CardContent>
          <div className="space-y-4">
            {patternAnalysis.trendPatterns.map((pattern, index) => {
              const TrendIcon = getTrendIcon(pattern.type)
              return (
                <div key={index} className={`p-4 border rounded-lg ${getTrendColor(pattern.type)}`}>
                  <div className="flex items-start justify-between">
                    <div className="flex items-start space-x-3">
                      <TrendIcon className={`h-6 w-6 mt-1 ${
                        pattern.type === 'downtrend' ? 'transform rotate-180' : ''
                      }`} />
                      <div>
                        <h4 className="font-medium capitalize">
                          {pattern.type.replace('_', ' ')} Pattern
                        </h4>
                        <p className="text-sm opacity-80 mt-1">
                          Duration: {pattern.duration} days • Strength: {(pattern.strength * 100).toFixed(0)}%
                        </p>
                        <div className="flex flex-wrap gap-1 mt-2">
                          {pattern.assets.map((asset, assetIndex) => (
                            <span key={assetIndex} className="px-2 py-1 text-xs rounded-full bg-white bg-opacity-50">
                              {asset.split('/')[0]}
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className={`text-sm font-medium ${getConfidenceColor(pattern.confidence)}`}>
                        {(pattern.confidence * 100).toFixed(0)}% confidence
                      </div>
                      <div className="text-xs opacity-75 mt-1">
                        {pattern.startDate.toLocaleDateString()} - {pattern.endDate.toLocaleDateString()}
                      </div>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  )

  const renderSeasonalView = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader title="Seasonal Patterns" />
        <CardContent>
          <div className="space-y-4">
            {patternAnalysis.seasonalPatterns.map((pattern, index) => (
              <div key={index} className="p-4 border border-blue-200 bg-blue-50 rounded-lg">
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-3">
                    <CalendarIcon className="h-6 w-6 text-blue-600 mt-1" />
                    <div>
                      <h4 className="font-medium text-blue-900">{pattern.pattern}</h4>
                      <p className="text-sm text-blue-700 mt-1">{pattern.description}</p>
                      <div className="flex items-center space-x-4 mt-2 text-xs text-blue-600">
                        <span>Frequency: {pattern.frequency}</span>
                        <span>Occurrences: {pattern.historicalOccurrences}</span>
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className={`text-sm font-medium ${getConfidenceColor(pattern.confidence)}`}>
                      {(pattern.confidence * 100).toFixed(0)}% confidence
                    </div>
                    <div className="text-xs text-blue-600 mt-1">
                      Strength: {(pattern.strength * 100).toFixed(0)}%
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )

  const renderVolatilityView = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader title="Volatility Regime Analysis" />
        <CardContent>
          <div className="space-y-4">
            {patternAnalysis.volatilityRegimes.map((regime, index) => {
              const getRegimeColor = (regimeType: string) => {
                switch (regimeType) {
                  case 'low': return 'text-green-600 bg-green-50 border-green-200'
                  case 'medium': return 'text-yellow-600 bg-yellow-50 border-yellow-200'
                  case 'high': return 'text-orange-600 bg-orange-50 border-orange-200'
                  case 'extreme': return 'text-red-600 bg-red-50 border-red-200'
                  default: return 'text-gray-600 bg-gray-50 border-gray-200'
                }
              }

              return (
                <div key={index} className={`p-4 border rounded-lg ${getRegimeColor(regime.regime)}`}>
                  <div className="flex items-start justify-between">
                    <div>
                      <h4 className="font-medium capitalize">{regime.regime} Volatility Regime</h4>
                      <div className="mt-2 space-y-1 text-sm">
                        <div>Current Level: {(regime.currentLevel * 100).toFixed(1)}%</div>
                        <div>Threshold: {(regime.threshold * 100).toFixed(1)}%</div>
                        <div>Duration: {regime.duration} days</div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-medium">
                        {(regime.probability * 100).toFixed(0)}% probability
                      </div>
                      <div className="text-xs opacity-75 mt-1">
                        Expected: {regime.expectedDuration} days
                      </div>
                    </div>
                  </div>
                  
                  {/* Volatility Level Bar */}
                  <div className="mt-4">
                    <div className="flex justify-between text-xs mb-1">
                      <span>Volatility Level</span>
                      <span>{(regime.currentLevel * 100).toFixed(1)}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className={`h-2 rounded-full ${
                          regime.regime === 'low' ? 'bg-green-500' :
                          regime.regime === 'medium' ? 'bg-yellow-500' :
                          regime.regime === 'high' ? 'bg-orange-500' : 'bg-red-500'
                        }`}
                        style={{ width: `${Math.min(100, (regime.currentLevel / regime.threshold) * 100)}%` }}
                      />
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  )

  const renderAnomaliesView = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader title="Market Anomalies" />
        <CardContent>
          <div className="space-y-4">
            {patternAnalysis.anomalies.map((anomaly, index) => {
              const getSeverityColor = (severity: number) => {
                if (severity >= 0.8) return 'text-red-600 bg-red-50 border-red-200'
                if (severity >= 0.6) return 'text-orange-600 bg-orange-50 border-orange-200'
                return 'text-yellow-600 bg-yellow-50 border-yellow-200'
              }

              return (
                <div key={index} className={`p-4 border rounded-lg ${getSeverityColor(anomaly.severity)}`}>
                  <div className="flex items-start justify-between">
                    <div className="flex items-start space-x-3">
                      <ExclamationTriangleIcon className="h-6 w-6 mt-1" />
                      <div>
                        <h4 className="font-medium capitalize">
                          {anomaly.type.replace('_', ' ')}
                        </h4>
                        <p className="text-sm opacity-90 mt-1">{anomaly.description}</p>
                        <div className="flex flex-wrap gap-1 mt-2">
                          {anomaly.affectedAssets.map((asset, assetIndex) => (
                            <span key={assetIndex} className="px-2 py-1 text-xs rounded-full bg-white bg-opacity-50">
                              {asset.split('/')[0]}
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-medium">
                        Severity: {(anomaly.severity * 100).toFixed(0)}%
                      </div>
                      <div className="text-xs opacity-75 mt-1">
                        {anomaly.timestamp.toLocaleDateString()}
                      </div>
                      <div className="text-xs opacity-75">
                        Impact: {(anomaly.impact * 100).toFixed(1)}%
                      </div>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  )

  const renderSignalsView = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader title="Predictive Signals" />
        <CardContent>
          <div className="space-y-4">
            {patternAnalysis.predictiveSignals.map((signal, index) => {
              const getSignalColor = (type: string) => {
                switch (type) {
                  case 'momentum': return 'text-blue-600 bg-blue-50 border-blue-200'
                  case 'mean_reversion': return 'text-purple-600 bg-purple-50 border-purple-200'
                  case 'volatility': return 'text-orange-600 bg-orange-50 border-orange-200'
                  case 'correlation': return 'text-green-600 bg-green-50 border-green-200'
                  default: return 'text-gray-600 bg-gray-50 border-gray-200'
                }
              }

              return (
                <div key={index} className={`p-4 border rounded-lg ${getSignalColor(signal.type)}`}>
                  <div className="flex items-start justify-between">
                    <div className="flex items-start space-x-3">
                      <LightBulbIcon className="h-6 w-6 mt-1" />
                      <div>
                        <h4 className="font-medium">{signal.signal}</h4>
                        <p className="text-sm opacity-90 mt-1 capitalize">
                          {signal.type.replace('_', ' ')} signal
                        </p>
                        <div className="mt-2 space-y-1 text-xs">
                          <div>Time Horizon: {signal.timeHorizon}</div>
                          <div>Expected Return: {(signal.expectedReturn * 100).toFixed(1)}%</div>
                          <div>Risk Level: {(signal.riskLevel * 100).toFixed(0)}%</div>
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-medium">
                        Strength: {(signal.strength * 100).toFixed(0)}%
                      </div>
                      <div className={`text-xs mt-1 ${getConfidenceColor(signal.confidence)}`}>
                        {(signal.confidence * 100).toFixed(0)}% confidence
                      </div>
                    </div>
                  </div>
                  
                  {/* Signal Strength Bar */}
                  <div className="mt-4">
                    <div className="flex justify-between text-xs mb-1">
                      <span>Signal Strength</span>
                      <span>{(signal.strength * 100).toFixed(0)}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className="h-2 rounded-full bg-current opacity-60"
                        style={{ width: `${signal.strength * 100}%` }}
                      />
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  )

  const viewOptions = [
    { key: 'trends' as const, label: 'Trend Patterns', icon: TrendingUpIcon },
    { key: 'seasonal' as const, label: 'Seasonal', icon: CalendarIcon },
    { key: 'volatility' as const, label: 'Volatility', icon: ChartBarIcon },
    { key: 'anomalies' as const, label: 'Anomalies', icon: ExclamationTriangleIcon },
    { key: 'signals' as const, label: 'Predictive Signals', icon: LightBulbIcon }
  ]

  return (
    <div className="space-y-6">
      {/* View Selector */}
      <div className="flex space-x-1 bg-gray-100 rounded-lg p-1 overflow-x-auto">
        {viewOptions.map(option => {
          const Icon = option.icon
          return (
            <button
              key={option.key}
              onClick={() => setSelectedView(option.key)}
              className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors whitespace-nowrap ${
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
      {selectedView === 'trends' && renderTrendsView()}
      {selectedView === 'seasonal' && renderSeasonalView()}
      {selectedView === 'volatility' && renderVolatilityView()}
      {selectedView === 'anomalies' && renderAnomaliesView()}
      {selectedView === 'signals' && renderSignalsView()}
    </div>
  )
}