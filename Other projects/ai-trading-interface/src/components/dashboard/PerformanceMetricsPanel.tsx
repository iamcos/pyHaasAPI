import React, { useState } from 'react'
import { 
  TrophyIcon,
  ExclamationTriangleIcon,
  ChartBarIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon
} from '@heroicons/react/24/outline'
import { Card, CardHeader, CardContent, Button } from '@/components/ui'
import type { StrategyPerformance } from '@/services/dashboardService'

interface PerformanceMetricsPanelProps {
  topPerformers: StrategyPerformance[]
  worstPerformers: StrategyPerformance[]
  loading?: boolean
}

export function PerformanceMetricsPanel({ 
  topPerformers, 
  worstPerformers, 
  loading = false 
}: PerformanceMetricsPanelProps) {
  const [activeTab, setActiveTab] = useState<'top' | 'worst' | 'all'>('top')

  if (loading) {
    return (
      <Card>
        <CardHeader title="Strategy Performance" />
        <CardContent>
          <div className="animate-pulse space-y-4">
            <div className="flex space-x-2">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="h-8 w-16 bg-gray-200 rounded"></div>
              ))}
            </div>
            <div className="space-y-3">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="h-16 bg-gray-200 rounded"></div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>
    )
  }

  const allStrategies = [...topPerformers, ...worstPerformers]
    .sort((a, b) => b.pnl - a.pnl)

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'text-green-600 bg-green-100'
      case 'paused': return 'text-yellow-600 bg-yellow-100'
      case 'inactive': return 'text-gray-600 bg-gray-100'
      default: return 'text-gray-600 bg-gray-100'
    }
  }

  const getPerformanceColor = (pnl: number) => {
    if (pnl > 0) return 'text-green-600'
    if (pnl < 0) return 'text-red-600'
    return 'text-gray-600'
  }

  const renderStrategyList = (strategies: StrategyPerformance[], showRank = false) => (
    <div className="space-y-3">
      {strategies.map((strategy, index) => (
        <div 
          key={strategy.strategyId}
          className="flex items-center justify-between p-3 border border-gray-200 dark:border-gray-700 rounded-lg hover:shadow-sm transition-shadow"
        >
          <div className="flex items-center space-x-3 flex-1">
            {showRank && (
              <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                index < 3 ? 'bg-yellow-100 text-yellow-800' : 'bg-gray-100 text-gray-600'
              }`}>
                {index + 1}
              </div>
            )}
            
            <div className="flex-1 min-w-0">
              <div className="flex items-center space-x-2 mb-1">
                <h4 className="text-sm font-medium text-gray-900 dark:text-white truncate">
                  {strategy.strategyName}
                </h4>
                <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${getStatusColor(strategy.status)}`}>
                  {strategy.status}
                </span>
              </div>
              
              <div className="flex items-center space-x-4 text-xs text-gray-500">
                <span>{strategy.trades} trades</span>
                <span>{strategy.winRate.toFixed(1)}% win rate</span>
                {strategy.botId && (
                  <span className="text-blue-600">Bot: {strategy.botId.slice(0, 8)}...</span>
                )}
              </div>
            </div>
          </div>
          
          <div className="text-right ml-3">
            <div className={`text-sm font-medium ${getPerformanceColor(strategy.pnl)}`}>
              {strategy.pnl >= 0 ? '+' : ''}${strategy.pnl.toFixed(2)}
            </div>
            <div className={`text-xs ${getPerformanceColor(strategy.pnlPercentage)}`}>
              {strategy.pnlPercentage >= 0 ? '+' : ''}{strategy.pnlPercentage.toFixed(2)}%
            </div>
          </div>
        </div>
      ))}
    </div>
  )

  const tabs = [
    { 
      key: 'top' as const, 
      label: 'Top Performers', 
      icon: TrophyIcon, 
      count: topPerformers.length,
      color: 'text-green-600'
    },
    { 
      key: 'worst' as const, 
      label: 'Needs Attention', 
      icon: ExclamationTriangleIcon, 
      count: worstPerformers.length,
      color: 'text-red-600'
    },
    { 
      key: 'all' as const, 
      label: 'All Strategies', 
      icon: ChartBarIcon, 
      count: allStrategies.length,
      color: 'text-blue-600'
    }
  ]

  return (
    <Card>
      <CardHeader 
        title="Strategy Performance Analytics"
        subtitle="Performance breakdown across all trading strategies"
      />
      
      <CardContent>
        {/* Tab Navigation */}
        <div className="flex space-x-1 mb-6 bg-gray-100 dark:bg-gray-800 rounded-lg p-1">
          {tabs.map(tab => {
            const Icon = tab.icon
            return (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`flex items-center space-x-2 px-3 py-2 text-sm font-medium rounded-md transition-colors flex-1 justify-center ${
                  activeTab === tab.key
                    ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm'
                    : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
                }`}
              >
                <Icon className="h-4 w-4" />
                <span>{tab.label}</span>
                <span className={`px-1.5 py-0.5 text-xs rounded-full ${
                  activeTab === tab.key ? 'bg-gray-100 text-gray-600' : 'bg-gray-200 text-gray-500'
                }`}>
                  {tab.count}
                </span>
              </button>
            )
          })}
        </div>

        {/* Performance Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="text-center p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
            <ArrowTrendingUpIcon className="h-6 w-6 text-green-600 mx-auto mb-2" />
            <div className="text-lg font-semibold text-green-600">
              {topPerformers.length}
            </div>
            <div className="text-xs text-green-700 dark:text-green-400">
              Profitable Strategies
            </div>
          </div>
          
          <div className="text-center p-4 bg-red-50 dark:bg-red-900/20 rounded-lg">
            <ArrowTrendingDownIcon className="h-6 w-6 text-red-600 mx-auto mb-2" />
            <div className="text-lg font-semibold text-red-600">
              {worstPerformers.length}
            </div>
            <div className="text-xs text-red-700 dark:text-red-400">
              Underperforming
            </div>
          </div>
          
          <div className="text-center p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
            <ChartBarIcon className="h-6 w-6 text-blue-600 mx-auto mb-2" />
            <div className="text-lg font-semibold text-blue-600">
              {allStrategies.reduce((sum, s) => sum + s.trades, 0)}
            </div>
            <div className="text-xs text-blue-700 dark:text-blue-400">
              Total Trades
            </div>
          </div>
        </div>

        {/* Strategy Lists */}
        <div className="space-y-4">
          {activeTab === 'top' && (
            <div>
              {topPerformers.length > 0 ? (
                <>
                  <div className="flex items-center space-x-2 mb-4">
                    <TrophyIcon className="h-5 w-5 text-green-600" />
                    <h3 className="text-sm font-medium text-gray-900 dark:text-white">
                      Top Performing Strategies
                    </h3>
                  </div>
                  {renderStrategyList(topPerformers, true)}
                </>
              ) : (
                <div className="text-center py-8">
                  <TrophyIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-sm text-gray-600">No profitable strategies yet</p>
                </div>
              )}
            </div>
          )}

          {activeTab === 'worst' && (
            <div>
              {worstPerformers.length > 0 ? (
                <>
                  <div className="flex items-center space-x-2 mb-4">
                    <ExclamationTriangleIcon className="h-5 w-5 text-red-600" />
                    <h3 className="text-sm font-medium text-gray-900 dark:text-white">
                      Strategies Needing Attention
                    </h3>
                  </div>
                  {renderStrategyList(worstPerformers)}
                  
                  {worstPerformers.length > 0 && (
                    <div className="mt-4 p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
                      <div className="flex items-center space-x-2">
                        <ExclamationTriangleIcon className="h-4 w-4 text-yellow-600" />
                        <span className="text-sm font-medium text-yellow-800 dark:text-yellow-200">
                          Optimization Recommended
                        </span>
                      </div>
                      <p className="text-xs text-yellow-700 dark:text-yellow-300 mt-1">
                        Consider reviewing parameters or pausing underperforming strategies.
                      </p>
                    </div>
                  )}
                </>
              ) : (
                <div className="text-center py-8">
                  <ExclamationTriangleIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-sm text-gray-600">All strategies performing well</p>
                </div>
              )}
            </div>
          )}

          {activeTab === 'all' && (
            <div>
              {allStrategies.length > 0 ? (
                <>
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center space-x-2">
                      <ChartBarIcon className="h-5 w-5 text-blue-600" />
                      <h3 className="text-sm font-medium text-gray-900 dark:text-white">
                        All Trading Strategies
                      </h3>
                    </div>
                    <div className="text-xs text-gray-500">
                      Sorted by performance
                    </div>
                  </div>
                  {renderStrategyList(allStrategies, true)}
                </>
              ) : (
                <div className="text-center py-8">
                  <ChartBarIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-sm text-gray-600">No strategies found</p>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Performance Insights */}
        {allStrategies.length > 0 && (
          <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
            <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
              Performance Insights
            </h4>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
              <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <div className="font-medium text-gray-900 dark:text-white mb-1">
                  Average Win Rate
                </div>
                <div className="text-lg font-semibold text-blue-600">
                  {allStrategies.length > 0 
                    ? (allStrategies.reduce((sum, s) => sum + s.winRate, 0) / allStrategies.length).toFixed(1)
                    : '0.0'
                  }%
                </div>
              </div>
              
              <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <div className="font-medium text-gray-900 dark:text-white mb-1">
                  Total P&L
                </div>
                <div className={`text-lg font-semibold ${
                  allStrategies.reduce((sum, s) => sum + s.pnl, 0) >= 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {allStrategies.reduce((sum, s) => sum + s.pnl, 0) >= 0 ? '+' : ''}
                  ${allStrategies.reduce((sum, s) => sum + s.pnl, 0).toFixed(2)}
                </div>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}