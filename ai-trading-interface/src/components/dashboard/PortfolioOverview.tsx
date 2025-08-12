import React, { useState } from 'react'
import { 
  PieChartIcon,
  ChartBarIcon,
  CurrencyDollarIcon,
  ScaleIcon
} from '@heroicons/react/24/outline'
import { Card, CardHeader, CardContent, Button } from '@/components/ui'
import type { PortfolioSummary } from '@/services/dashboardService'

interface PortfolioOverviewProps {
  portfolioSummary: PortfolioSummary
  loading?: boolean
}

export function PortfolioOverview({ portfolioSummary, loading = false }: PortfolioOverviewProps) {
  const [viewMode, setViewMode] = useState<'allocation' | 'performance' | 'risk'>('allocation')

  if (loading) {
    return (
      <Card>
        <CardHeader title="Portfolio Overview" />
        <CardContent>
          <div className="animate-pulse space-y-4">
            <div className="h-8 bg-gray-200 rounded w-1/3"></div>
            <div className="h-64 bg-gray-200 rounded"></div>
          </div>
        </CardContent>
      </Card>
    )
  }

  const viewModes = [
    { key: 'allocation' as const, label: 'Allocation', icon: PieChartIcon },
    { key: 'performance' as const, label: 'Performance', icon: ChartBarIcon },
    { key: 'risk' as const, label: 'Risk', icon: ScaleIcon }
  ]

  const renderAllocationView = () => {
    const totalEquity = portfolioSummary.totalEquity
    
    return (
      <div className="space-y-6">
        {/* Account Allocation */}
        <div>
          <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
            Account Allocation
          </h4>
          <div className="space-y-3">
            {portfolioSummary.accountBreakdown.map((account, index) => {
              const percentage = totalEquity > 0 ? (account.equity / totalEquity) * 100 : 0
              const colors = [
                'bg-blue-500',
                'bg-green-500', 
                'bg-purple-500',
                'bg-orange-500',
                'bg-pink-500'
              ]
              const color = colors[index % colors.length]
              
              return (
                <div key={account.accountId} className="flex items-center space-x-3">
                  <div className={`w-3 h-3 rounded-full ${color}`} />
                  <div className="flex-1">
                    <div className="flex justify-between items-center">
                      <span className="text-sm font-medium text-gray-900 dark:text-white">
                        {account.accountName}
                      </span>
                      <span className="text-sm text-gray-600 dark:text-gray-400">
                        {percentage.toFixed(1)}%
                      </span>
                    </div>
                    <div className="flex justify-between items-center mt-1">
                      <span className="text-xs text-gray-500">
                        ${account.equity.toLocaleString()}
                      </span>
                      <span className={`text-xs ${
                        account.unrealizedPnL >= 0 ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {account.unrealizedPnL >= 0 ? '+' : ''}${account.unrealizedPnL.toFixed(2)}
                      </span>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Visual Allocation Chart */}
        <div className="relative">
          <div className="flex h-4 bg-gray-200 rounded-full overflow-hidden">
            {portfolioSummary.accountBreakdown.map((account, index) => {
              const percentage = totalEquity > 0 ? (account.equity / totalEquity) * 100 : 0
              const colors = [
                'bg-blue-500',
                'bg-green-500', 
                'bg-purple-500',
                'bg-orange-500',
                'bg-pink-500'
              ]
              const color = colors[index % colors.length]
              
              return (
                <div
                  key={account.accountId}
                  className={color}
                  style={{ width: `${percentage}%` }}
                  title={`${account.accountName}: ${percentage.toFixed(1)}%`}
                />
              )
            })}
          </div>
        </div>
      </div>
    )
  }

  const renderPerformanceView = () => (
    <div className="space-y-6">
      {/* Top Performers */}
      <div>
        <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
          Top Performers
        </h4>
        <div className="space-y-2">
          {portfolioSummary.topPerformers.slice(0, 5).map((performer, index) => (
            <div key={performer.strategyId} className="flex items-center justify-between p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
              <div className="flex items-center space-x-3">
                <div className="w-6 h-6 bg-green-500 text-white rounded-full flex items-center justify-center text-xs font-bold">
                  {index + 1}
                </div>
                <div>
                  <div className="text-sm font-medium text-gray-900 dark:text-white">
                    {performer.strategyName}
                  </div>
                  <div className="text-xs text-gray-500">
                    {performer.trades} trades • {performer.winRate.toFixed(1)}% win rate
                  </div>
                </div>
              </div>
              <div className="text-right">
                <div className="text-sm font-medium text-green-600">
                  +${performer.pnl.toFixed(2)}
                </div>
                <div className="text-xs text-green-500">
                  +{performer.pnlPercentage.toFixed(2)}%
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Worst Performers */}
      <div>
        <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
          Needs Attention
        </h4>
        <div className="space-y-2">
          {portfolioSummary.worstPerformers.slice(0, 3).map((performer, index) => (
            <div key={performer.strategyId} className="flex items-center justify-between p-3 bg-red-50 dark:bg-red-900/20 rounded-lg">
              <div className="flex items-center space-x-3">
                <div className="w-6 h-6 bg-red-500 text-white rounded-full flex items-center justify-center text-xs font-bold">
                  !
                </div>
                <div>
                  <div className="text-sm font-medium text-gray-900 dark:text-white">
                    {performer.strategyName}
                  </div>
                  <div className="text-xs text-gray-500">
                    {performer.trades} trades • {performer.winRate.toFixed(1)}% win rate
                  </div>
                </div>
              </div>
              <div className="text-right">
                <div className="text-sm font-medium text-red-600">
                  ${performer.pnl.toFixed(2)}
                </div>
                <div className="text-xs text-red-500">
                  {performer.pnlPercentage.toFixed(2)}%
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )

  const renderRiskView = () => {
    const avgRiskScore = portfolioSummary.accountBreakdown.reduce(
      (sum, account) => sum + account.riskScore, 0
    ) / portfolioSummary.accountBreakdown.length

    const getRiskColor = (score: number) => {
      if (score <= 3) return 'text-green-600'
      if (score <= 6) return 'text-yellow-600'
      return 'text-red-600'
    }

    const getRiskLabel = (score: number) => {
      if (score <= 3) return 'Low Risk'
      if (score <= 6) return 'Moderate Risk'
      return 'High Risk'
    }

    return (
      <div className="space-y-6">
        {/* Overall Risk Score */}
        <div className="text-center p-6 bg-gray-50 dark:bg-gray-800 rounded-lg">
          <div className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
            {avgRiskScore.toFixed(1)}/10
          </div>
          <div className={`text-sm font-medium ${getRiskColor(avgRiskScore)}`}>
            {getRiskLabel(avgRiskScore)}
          </div>
          <div className="text-xs text-gray-500 mt-1">
            Portfolio Risk Score
          </div>
        </div>

        {/* Risk Breakdown by Account */}
        <div>
          <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
            Risk by Account
          </h4>
          <div className="space-y-3">
            {portfolioSummary.accountBreakdown.map((account) => (
              <div key={account.accountId} className="flex items-center justify-between p-3 border border-gray-200 dark:border-gray-700 rounded-lg">
                <div>
                  <div className="text-sm font-medium text-gray-900 dark:text-white">
                    {account.accountName}
                  </div>
                  <div className="text-xs text-gray-500">
                    {account.positionCount} positions • {account.activeBots} active bots
                  </div>
                </div>
                <div className="text-right">
                  <div className={`text-sm font-medium ${getRiskColor(account.riskScore)}`}>
                    {account.riskScore.toFixed(1)}/10
                  </div>
                  <div className={`text-xs ${getRiskColor(account.riskScore)}`}>
                    {getRiskLabel(account.riskScore)}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Risk Metrics */}
        <div className="grid grid-cols-2 gap-4">
          <div className="text-center p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
            <div className="text-lg font-semibold text-gray-900 dark:text-white">
              {portfolioSummary.totalPositions}
            </div>
            <div className="text-xs text-gray-500">Open Positions</div>
          </div>
          <div className="text-center p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
            <div className="text-lg font-semibold text-gray-900 dark:text-white">
              {portfolioSummary.activeBots}
            </div>
            <div className="text-xs text-gray-500">Active Strategies</div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <Card>
      <CardHeader 
        title="Portfolio Overview"
        action={
          <div className="flex space-x-1">
            {viewModes.map(mode => {
              const Icon = mode.icon
              return (
                <button
                  key={mode.key}
                  onClick={() => setViewMode(mode.key)}
                  className={`flex items-center space-x-1 px-3 py-1 text-xs font-medium rounded transition-colors ${
                    viewMode === mode.key
                      ? 'bg-primary-100 text-primary-700'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  <Icon className="h-3 w-3" />
                  <span>{mode.label}</span>
                </button>
              )
            })}
          </div>
        }
      />
      
      <CardContent>
        {viewMode === 'allocation' && renderAllocationView()}
        {viewMode === 'performance' && renderPerformanceView()}
        {viewMode === 'risk' && renderRiskView()}
      </CardContent>
    </Card>
  )
}