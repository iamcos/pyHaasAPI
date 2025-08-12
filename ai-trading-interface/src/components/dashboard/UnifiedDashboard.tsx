import React, { useState, useEffect } from 'react'
import { 
  CurrencyDollarIcon,
  ChartBarIcon,
  ExclamationTriangleIcon,
  BoltIcon,
  TrendingUpIcon,
  TrendingDownIcon,
  EyeIcon,
  Cog6ToothIcon
} from '@heroicons/react/24/outline'
import { Card, CardHeader, CardContent, Button } from '@/components/ui'
import { PortfolioOverview } from './PortfolioOverview'
import { MarketSentimentPanel } from './MarketSentimentPanel'
import { OpportunityAlertsPanel } from './OpportunityAlertsPanel'
import { RealTimePnLTracker } from './RealTimePnLTracker'
import { AccountSummaryGrid } from './AccountSummaryGrid'
import { PerformanceMetricsPanel } from './PerformanceMetricsPanel'
import { useTradingStore } from '@/stores/tradingStore'
import { useStores } from '@/hooks/useStores'
import { dashboardService } from '@/services/dashboardService'
import type { PortfolioSummary, MarketSentiment, OpportunityAlert } from '@/services/dashboardService'

interface UnifiedDashboardProps {
  className?: string
}

export function UnifiedDashboard({ className = '' }: UnifiedDashboardProps) {
  const { accounts, bots, positions, markets } = useTradingStore()
  const { appStore } = useStores()
  
  const [portfolioSummary, setPortfolioSummary] = useState<PortfolioSummary | null>(null)
  const [marketSentiment, setMarketSentiment] = useState<MarketSentiment | null>(null)
  const [opportunities, setOpportunities] = useState<OpportunityAlert[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [refreshInterval, setRefreshInterval] = useState(30000) // 30 seconds
  const [autoRefresh, setAutoRefresh] = useState(true)

  // Load dashboard data
  const loadDashboardData = async () => {
    try {
      setLoading(true)
      setError(null)

      const [portfolio, sentiment, alerts] = await Promise.all([
        dashboardService.getPortfolioSummary(accounts, bots, positions),
        dashboardService.getMarketSentiment(markets),
        dashboardService.getOpportunityAlerts(markets, positions)
      ])

      setPortfolioSummary(portfolio)
      setMarketSentiment(sentiment)
      setOpportunities(alerts)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load dashboard data')
      console.error('Dashboard data loading error:', err)
    } finally {
      setLoading(false)
    }
  }

  // Initial load and auto-refresh setup
  useEffect(() => {
    loadDashboardData()

    if (autoRefresh) {
      const interval = setInterval(loadDashboardData, refreshInterval)
      return () => clearInterval(interval)
    }
  }, [accounts, bots, positions, markets, autoRefresh, refreshInterval])

  // Manual refresh
  const handleRefresh = () => {
    dashboardService.invalidateCache()
    loadDashboardData()
  }

  // Toggle auto-refresh
  const toggleAutoRefresh = () => {
    setAutoRefresh(!autoRefresh)
  }

  // Update refresh interval
  const updateRefreshInterval = (interval: number) => {
    setRefreshInterval(interval)
    dashboardService.setUpdateInterval(interval)
  }

  if (loading && !portfolioSummary) {
    return (
      <div className={`p-6 ${className}`}>
        <div className="animate-pulse space-y-6">
          <div className="h-8 bg-gray-200 rounded w-1/4"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-32 bg-gray-200 rounded"></div>
            ))}
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 h-96 bg-gray-200 rounded"></div>
            <div className="h-96 bg-gray-200 rounded"></div>
          </div>
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
                Failed to Load Dashboard
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

  const quickStats = portfolioSummary ? [
    {
      name: 'Total Portfolio Value',
      value: `$${portfolioSummary.totalValue.toLocaleString('en-US', { 
        minimumFractionDigits: 2, 
        maximumFractionDigits: 2 
      })}`,
      change: portfolioSummary.dailyPnL >= 0 
        ? `+$${portfolioSummary.dailyPnL.toFixed(2)}` 
        : `-$${Math.abs(portfolioSummary.dailyPnL).toFixed(2)}`,
      changeType: portfolioSummary.dailyPnL >= 0 ? 'profit' as const : 'loss' as const,
      icon: CurrencyDollarIcon,
      trend: portfolioSummary.dailyPnL >= 0 ? TrendingUpIcon : TrendingDownIcon
    },
    {
      name: 'Unrealized P&L',
      value: portfolioSummary.unrealizedPnL >= 0 
        ? `+$${portfolioSummary.unrealizedPnL.toFixed(2)}`
        : `-$${Math.abs(portfolioSummary.unrealizedPnL).toFixed(2)}`,
      change: `${portfolioSummary.totalPositions} positions`,
      changeType: portfolioSummary.unrealizedPnL >= 0 ? 'profit' as const : 'loss' as const,
      icon: ChartBarIcon,
      trend: portfolioSummary.unrealizedPnL >= 0 ? TrendingUpIcon : TrendingDownIcon
    },
    {
      name: 'Active Strategies',
      value: portfolioSummary.activeBots.toString(),
      change: `${accounts.length} accounts`,
      changeType: 'neutral' as const,
      icon: BoltIcon,
      trend: null
    },
    {
      name: 'Opportunities',
      value: opportunities.length.toString(),
      change: marketSentiment?.overall.sentiment || 'neutral',
      changeType: 'neutral' as const,
      icon: EyeIcon,
      trend: null
    }
  ] : []

  return (
    <div className={`p-6 space-y-6 ${className}`}>
      {/* Header with controls */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Trading Dashboard
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Real-time portfolio overview and market intelligence
          </p>
        </div>
        
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2">
            <label className="text-sm text-gray-600">Auto-refresh:</label>
            <button
              onClick={toggleAutoRefresh}
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
            onChange={(e) => updateRefreshInterval(Number(e.target.value))}
            className="text-sm border border-gray-300 rounded px-2 py-1"
          >
            <option value={10000}>10s</option>
            <option value={30000}>30s</option>
            <option value={60000}>1m</option>
            <option value={300000}>5m</option>
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

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {quickStats.map((stat) => (
          <Card key={stat.name} hover className="relative overflow-hidden">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                    {stat.name}
                  </p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
                    {stat.value}
                  </p>
                  <div className="flex items-center mt-2">
                    {stat.trend && (
                      <stat.trend className={`h-4 w-4 mr-1 ${
                        stat.changeType === 'profit' ? 'text-green-500' : 
                        stat.changeType === 'loss' ? 'text-red-500' : 'text-gray-500'
                      }`} />
                    )}
                    <p className={`text-sm ${
                      stat.changeType === 'profit' ? 'text-green-600' : 
                      stat.changeType === 'loss' ? 'text-red-600' : 'text-gray-600'
                    }`}>
                      {stat.change}
                    </p>
                  </div>
                </div>
                <div className="flex-shrink-0">
                  <stat.icon className="h-8 w-8 text-gray-400" />
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Real-time P&L Tracker */}
      {portfolioSummary && (
        <RealTimePnLTracker 
          portfolioSummary={portfolioSummary}
          loading={loading}
        />
      )}

      {/* Main Dashboard Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Portfolio Overview - Takes 2 columns */}
        <div className="lg:col-span-2 space-y-6">
          {portfolioSummary && (
            <PortfolioOverview 
              portfolioSummary={portfolioSummary}
              loading={loading}
            />
          )}
          
          {portfolioSummary && (
            <AccountSummaryGrid 
              accountSummaries={portfolioSummary.accountBreakdown}
              loading={loading}
            />
          )}
          
          {portfolioSummary && (
            <PerformanceMetricsPanel 
              topPerformers={portfolioSummary.topPerformers}
              worstPerformers={portfolioSummary.worstPerformers}
              loading={loading}
            />
          )}
        </div>

        {/* Side Panel - Market Intelligence */}
        <div className="space-y-6">
          {marketSentiment && (
            <MarketSentimentPanel 
              sentiment={marketSentiment}
              loading={loading}
            />
          )}
          
          <OpportunityAlertsPanel 
            opportunities={opportunities}
            loading={loading}
          />
        </div>
      </div>
    </div>
  )
}