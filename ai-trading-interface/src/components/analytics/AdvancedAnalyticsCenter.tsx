import React, { useState, useEffect } from 'react'
import { 
  ChartBarIcon,
  ArrowTrendingUpIcon,
  ScaleIcon,
  CpuChipIcon,
  MagnifyingGlassIcon,
  Cog6ToothIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline'
import { Card, CardHeader, CardContent, Button } from '@/components/ui'
import { PerformanceAnalysisPanel } from './PerformanceAnalysisPanel'
import { CorrelationAnalysisPanel } from './CorrelationAnalysisPanel'
import { PatternRecognitionPanel } from './PatternRecognitionPanel'
import { RiskAdjustedReturnsPanel } from './RiskAdjustedReturnsPanel'
import { DrawdownAnalysisPanel } from './DrawdownAnalysisPanel'
import { PortfolioOptimizationPanel } from './PortfolioOptimizationPanel'
import { useTradingStore } from '@/stores/tradingStore'
import { analyticsService } from '@/services/analyticsService'
import type { AnalyticsMetrics } from '@/services/analyticsService'

interface AdvancedAnalyticsCenterProps {
  className?: string
}

export function AdvancedAnalyticsCenter({ className = '' }: AdvancedAnalyticsCenterProps) {
  const { bots, positions, markets } = useTradingStore()
  const [analytics, setAnalytics] = useState<AnalyticsMetrics | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'performance' | 'correlation' | 'patterns' | 'risk' | 'drawdown' | 'optimization'>('performance')
  const [autoRefresh, setAutoRefresh] = useState(true)
  const [refreshInterval, setRefreshInterval] = useState(60000) // 1 minute

  // Load analytics data
  const loadAnalytics = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const analyticsData = await analyticsService.generateAnalytics(bots, positions, markets)
      setAnalytics(analyticsData)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load analytics')
      console.error('Analytics loading error:', err)
    } finally {
      setLoading(false)
    }
  }

  // Initial load and auto-refresh setup
  useEffect(() => {
    loadAnalytics()

    if (autoRefresh) {
      const interval = setInterval(loadAnalytics, refreshInterval)
      return () => clearInterval(interval)
    }
  }, [bots, positions, markets, autoRefresh, refreshInterval])

  // Manual refresh
  const handleRefresh = () => {
    analyticsService.clearCache()
    loadAnalytics()
  }

  const tabs = [
    { 
      key: 'performance' as const, 
      label: 'Performance', 
      icon: ChartBarIcon,
      description: 'Multi-dimensional performance analysis'
    },
    { 
      key: 'correlation' as const, 
      label: 'Correlation', 
      icon: ScaleIcon,
      description: 'Asset correlation and clustering analysis'
    },
    { 
      key: 'patterns' as const, 
      label: 'Patterns', 
      icon: MagnifyingGlassIcon,
      description: 'Pattern recognition and predictive signals'
    },
    { 
      key: 'risk' as const, 
      label: 'Risk Metrics', 
      icon: ExclamationTriangleIcon,
      description: 'Risk-adjusted return calculations'
    },
    { 
      key: 'drawdown' as const, 
      label: 'Drawdown', 
      icon: ArrowTrendingUpIcon,
      description: 'Drawdown analysis and recovery metrics'
    },
    { 
      key: 'optimization' as const, 
      label: 'Optimization', 
      icon: CpuChipIcon,
      description: 'Portfolio optimization suggestions'
    }
  ]

  if (loading && !analytics) {
    return (
      <div className={`p-6 ${className}`}>
        <div className="animate-pulse space-y-6">
          <div className="h-8 bg-gray-200 rounded w-1/3"></div>
          <div className="flex space-x-2">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="h-10 w-24 bg-gray-200 rounded"></div>
            ))}
          </div>
          <div className="h-96 bg-gray-200 rounded"></div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className={`p-6 ${className}`}>
        <Card>
          <CardContent>
            <div className="text-center py-8">
              <ExclamationTriangleIcon className="h-12 w-12 text-red-500 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                Failed to Load Analytics
              </h3>
              <p className="text-gray-600 mb-4">{error}</p>
              <Button onClick={handleRefresh}>
                Try Again
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className={`p-6 space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Advanced Analytics Center
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Multi-dimensional performance analysis and portfolio optimization
          </p>
        </div>
        
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2">
            <label className="text-sm text-gray-600">Auto-refresh:</label>
            <button
              onClick={() => setAutoRefresh(!autoRefresh)}
              className={`w-10 h-6 rounded-full transition-colors ${
                autoRefresh ? 'bg-primary-600' : 'bg-gray-300'
              }`}
            >
              <div className={`w-4 h-4 bg-white rounded-full transition-transform ${
                autoRefresh ? 'translate-x-5' : 'translate-x-1'
              }`} />
            </button>
          </div>
          
          <select
            value={refreshInterval}
            onChange={(e) => setRefreshInterval(Number(e.target.value))}
            className="text-sm border border-gray-300 rounded px-2 py-1"
          >
            <option value={30000}>30s</option>
            <option value={60000}>1m</option>
            <option value={300000}>5m</option>
            <option value={900000}>15m</option>
          </select>
          
          <Button
            onClick={handleRefresh}
            variant="outline"
            size="sm"
            disabled={loading}
          >
            <Cog6ToothIcon className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          </Button>
        </div>
      </div>

      {/* Analytics Summary Cards */}
      {analytics && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card hover>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Sharpe Ratio</p>
                  <p className="text-xl font-bold text-gray-900">
                    {analytics.riskAdjustedReturns.sharpeRatio.toFixed(2)}
                  </p>
                </div>
                <ChartBarIcon className="h-8 w-8 text-blue-500" />
              </div>
            </CardContent>
          </Card>
          
          <Card hover>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Max Drawdown</p>
                  <p className="text-xl font-bold text-red-600">
                    -{(analytics.drawdownAnalysis.maxDrawdown * 100).toFixed(1)}%
                  </p>
                </div>
                <ArrowTrendingUpIcon className="h-8 w-8 text-red-500" />
              </div>
            </CardContent>
          </Card>
          
          <Card hover>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Portfolio Efficiency</p>
                  <p className="text-xl font-bold text-green-600">
                    {(analytics.portfolioOptimization.portfolioEfficiency * 100).toFixed(0)}%
                  </p>
                </div>
                <CpuChipIcon className="h-8 w-8 text-green-500" />
              </div>
            </CardContent>
          </Card>
          
          <Card hover>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Diversification</p>
                  <p className="text-xl font-bold text-purple-600">
                    {(analytics.correlationMatrix.diversificationRatio * 100).toFixed(0)}%
                  </p>
                </div>
                <ScaleIcon className="h-8 w-8 text-purple-500" />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Tab Navigation */}
      <div className="border-b border-gray-200 dark:border-gray-700">
        <nav className="flex space-x-8 overflow-x-auto">
          {tabs.map(tab => {
            const Icon = tab.icon
            return (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm whitespace-nowrap transition-colors ${
                  activeTab === tab.key
                    ? 'border-primary-500 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <Icon className="h-5 w-5" />
                <span>{tab.label}</span>
              </button>
            )
          })}
        </nav>
      </div>

      {/* Tab Content */}
      {analytics && (
        <div className="min-h-96">
          {activeTab === 'performance' && (
            <PerformanceAnalysisPanel 
              analysis={analytics.performanceAnalysis}
              loading={loading}
            />
          )}
          
          {activeTab === 'correlation' && (
            <CorrelationAnalysisPanel 
              correlationMatrix={analytics.correlationMatrix}
              loading={loading}
            />
          )}
          
          {activeTab === 'patterns' && (
            <PatternRecognitionPanel 
              patternAnalysis={analytics.patternRecognition}
              loading={loading}
            />
          )}
          
          {activeTab === 'risk' && (
            <RiskAdjustedReturnsPanel 
              riskMetrics={analytics.riskAdjustedReturns}
              loading={loading}
            />
          )}
          
          {activeTab === 'drawdown' && (
            <DrawdownAnalysisPanel 
              drawdownAnalysis={analytics.drawdownAnalysis}
              loading={loading}
            />
          )}
          
          {activeTab === 'optimization' && (
            <PortfolioOptimizationPanel 
              optimization={analytics.portfolioOptimization}
              loading={loading}
            />
          )}
        </div>
      )}
    </div>
  )
}