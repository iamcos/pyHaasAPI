import React, { useState, useEffect } from 'react'
import { 
  TrendingUpIcon, 
  TrendingDownIcon,
  MinusIcon,
  ChartBarIcon
} from '@heroicons/react/24/outline'
import { Card, CardHeader, CardContent } from '@/components/ui'
import type { PortfolioSummary } from '@/services/dashboardService'

interface RealTimePnLTrackerProps {
  portfolioSummary: PortfolioSummary
  loading?: boolean
}

interface PnLDataPoint {
  timestamp: Date
  value: number
  change: number
}

export function RealTimePnLTracker({ portfolioSummary, loading = false }: RealTimePnLTrackerProps) {
  const [pnlHistory, setPnlHistory] = useState<PnLDataPoint[]>([])
  const [selectedTimeframe, setSelectedTimeframe] = useState<'1h' | '4h' | '1d' | '1w'>('1h')

  // Simulate real-time P&L updates
  useEffect(() => {
    const interval = setInterval(() => {
      const now = new Date()
      const change = (Math.random() - 0.5) * 100 // Random change for demo
      const newPoint: PnLDataPoint = {
        timestamp: now,
        value: portfolioSummary.unrealizedPnL + change,
        change: change
      }
      
      setPnlHistory(prev => {
        const updated = [...prev, newPoint]
        // Keep only last 100 points
        return updated.slice(-100)
      })
    }, 5000) // Update every 5 seconds

    return () => clearInterval(interval)
  }, [portfolioSummary.unrealizedPnL])

  const timeframes = [
    { key: '1h' as const, label: '1H', duration: 3600000 },
    { key: '4h' as const, label: '4H', duration: 14400000 },
    { key: '1d' as const, label: '1D', duration: 86400000 },
    { key: '1w' as const, label: '1W', duration: 604800000 }
  ]

  const currentTimeframe = timeframes.find(t => t.key === selectedTimeframe)!
  const cutoffTime = new Date(Date.now() - currentTimeframe.duration)
  const filteredHistory = pnlHistory.filter(point => point.timestamp >= cutoffTime)

  const totalChange = filteredHistory.length > 1 
    ? filteredHistory[filteredHistory.length - 1].value - filteredHistory[0].value
    : 0

  const changePercentage = portfolioSummary.totalValue > 0 
    ? (totalChange / portfolioSummary.totalValue) * 100 
    : 0

  const getTrendIcon = () => {
    if (totalChange > 0) return TrendingUpIcon
    if (totalChange < 0) return TrendingDownIcon
    return MinusIcon
  }

  const getTrendColor = () => {
    if (totalChange > 0) return 'text-green-500'
    if (totalChange < 0) return 'text-red-500'
    return 'text-gray-500'
  }

  const TrendIcon = getTrendIcon()

  return (
    <Card className="relative overflow-hidden">
      <CardHeader 
        title="Real-time P&L Tracker"
        action={
          <div className="flex space-x-1">
            {timeframes.map(timeframe => (
              <button
                key={timeframe.key}
                onClick={() => setSelectedTimeframe(timeframe.key)}
                className={`px-3 py-1 text-xs font-medium rounded transition-colors ${
                  selectedTimeframe === timeframe.key
                    ? 'bg-primary-100 text-primary-700'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                {timeframe.label}
              </button>
            ))}
          </div>
        }
      />
      
      <CardContent>
        {loading ? (
          <div className="animate-pulse">
            <div className="h-8 bg-gray-200 rounded w-1/3 mb-4"></div>
            <div className="h-32 bg-gray-200 rounded"></div>
          </div>
        ) : (
          <div className="space-y-4">
            {/* Current P&L Display */}
            <div className="flex items-center justify-between">
              <div>
                <div className="flex items-center space-x-2">
                  <span className="text-2xl font-bold text-gray-900 dark:text-white">
                    {portfolioSummary.unrealizedPnL >= 0 ? '+' : ''}
                    ${portfolioSummary.unrealizedPnL.toFixed(2)}
                  </span>
                  <TrendIcon className={`h-6 w-6 ${getTrendColor()}`} />
                </div>
                <div className="flex items-center space-x-4 mt-1">
                  <span className={`text-sm font-medium ${getTrendColor()}`}>
                    {totalChange >= 0 ? '+' : ''}${totalChange.toFixed(2)} ({changePercentage >= 0 ? '+' : ''}{changePercentage.toFixed(2)}%)
                  </span>
                  <span className="text-xs text-gray-500">
                    {selectedTimeframe.toUpperCase()}
                  </span>
                </div>
              </div>
              
              <div className="text-right">
                <div className="text-sm text-gray-600">Total Value</div>
                <div className="text-lg font-semibold text-gray-900 dark:text-white">
                  ${portfolioSummary.totalValue.toLocaleString()}
                </div>
              </div>
            </div>

            {/* Mini Chart */}
            <div className="relative h-32 bg-gray-50 dark:bg-gray-800 rounded-lg overflow-hidden">
              {filteredHistory.length > 1 ? (
                <svg className="w-full h-full" viewBox="0 0 400 128">
                  <defs>
                    <linearGradient id="pnlGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                      <stop offset="0%" stopColor={totalChange >= 0 ? "#10b981" : "#ef4444"} stopOpacity="0.3" />
                      <stop offset="100%" stopColor={totalChange >= 0 ? "#10b981" : "#ef4444"} stopOpacity="0.1" />
                    </linearGradient>
                  </defs>
                  
                  {/* Generate path for P&L line */}
                  <path
                    d={filteredHistory.map((point, index) => {
                      const x = (index / (filteredHistory.length - 1)) * 400
                      const minValue = Math.min(...filteredHistory.map(p => p.value))
                      const maxValue = Math.max(...filteredHistory.map(p => p.value))
                      const range = maxValue - minValue || 1
                      const y = 128 - ((point.value - minValue) / range) * 128
                      return `${index === 0 ? 'M' : 'L'} ${x} ${y}`
                    }).join(' ')}
                    stroke={totalChange >= 0 ? "#10b981" : "#ef4444"}
                    strokeWidth="2"
                    fill="none"
                  />
                  
                  {/* Fill area under curve */}
                  <path
                    d={[
                      ...filteredHistory.map((point, index) => {
                        const x = (index / (filteredHistory.length - 1)) * 400
                        const minValue = Math.min(...filteredHistory.map(p => p.value))
                        const maxValue = Math.max(...filteredHistory.map(p => p.value))
                        const range = maxValue - minValue || 1
                        const y = 128 - ((point.value - minValue) / range) * 128
                        return `${index === 0 ? 'M' : 'L'} ${x} ${y}`
                      }),
                      'L 400 128',
                      'L 0 128',
                      'Z'
                    ].join(' ')}
                    fill="url(#pnlGradient)"
                  />
                </svg>
              ) : (
                <div className="flex items-center justify-center h-full text-gray-500">
                  <ChartBarIcon className="h-8 w-8 mr-2" />
                  <span className="text-sm">Collecting data...</span>
                </div>
              )}
            </div>

            {/* Period Breakdown */}
            <div className="grid grid-cols-3 gap-4 pt-4 border-t border-gray-200 dark:border-gray-700">
              <div className="text-center">
                <div className="text-xs text-gray-500 mb-1">Daily</div>
                <div className={`text-sm font-medium ${
                  portfolioSummary.dailyPnL >= 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {portfolioSummary.dailyPnL >= 0 ? '+' : ''}${portfolioSummary.dailyPnL.toFixed(2)}
                </div>
              </div>
              
              <div className="text-center">
                <div className="text-xs text-gray-500 mb-1">Weekly</div>
                <div className={`text-sm font-medium ${
                  portfolioSummary.weeklyPnL >= 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {portfolioSummary.weeklyPnL >= 0 ? '+' : ''}${portfolioSummary.weeklyPnL.toFixed(2)}
                </div>
              </div>
              
              <div className="text-center">
                <div className="text-xs text-gray-500 mb-1">Monthly</div>
                <div className={`text-sm font-medium ${
                  portfolioSummary.monthlyPnL >= 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {portfolioSummary.monthlyPnL >= 0 ? '+' : ''}${portfolioSummary.monthlyPnL.toFixed(2)}
                </div>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}