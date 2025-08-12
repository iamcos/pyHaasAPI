import React from 'react'
import { 
  BanknotesIcon,
  ScaleIcon,
  BoltIcon,
  ChartBarIcon
} from '@heroicons/react/24/outline'
import { Card, CardHeader, CardContent } from '@/components/ui'
import type { AccountSummary } from '@/services/dashboardService'

interface AccountSummaryGridProps {
  accountSummaries: AccountSummary[]
  loading?: boolean
}

export function AccountSummaryGrid({ accountSummaries, loading = false }: AccountSummaryGridProps) {
  if (loading) {
    return (
      <Card>
        <CardHeader title="Account Summary" />
        <CardContent>
          <div className="animate-pulse grid grid-cols-1 md:grid-cols-2 gap-4">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-32 bg-gray-200 rounded"></div>
            ))}
          </div>
        </CardContent>
      </Card>
    )
  }

  const getRiskColor = (score: number) => {
    if (score <= 3) return 'text-green-600 bg-green-50'
    if (score <= 6) return 'text-yellow-600 bg-yellow-50'
    return 'text-red-600 bg-red-50'
  }

  const getRiskLabel = (score: number) => {
    if (score <= 3) return 'Low'
    if (score <= 6) return 'Moderate'
    return 'High'
  }

  return (
    <Card>
      <CardHeader 
        title="Multi-Account Overview"
        subtitle={`${accountSummaries.length} trading accounts`}
      />
      
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {accountSummaries.map((account) => (
            <div 
              key={account.accountId}
              className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 hover:shadow-md transition-shadow"
            >
              {/* Account Header */}
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="font-medium text-gray-900 dark:text-white">
                    {account.accountName}
                  </h3>
                  <p className="text-xs text-gray-500">
                    Account ID: {account.accountId.slice(0, 8)}...
                  </p>
                </div>
                <div className={`px-2 py-1 rounded-full text-xs font-medium ${getRiskColor(account.riskScore)}`}>
                  {getRiskLabel(account.riskScore)} Risk
                </div>
              </div>

              {/* Account Metrics */}
              <div className="grid grid-cols-2 gap-4 mb-4">
                <div className="text-center">
                  <div className="flex items-center justify-center mb-1">
                    <BanknotesIcon className="h-4 w-4 text-gray-400 mr-1" />
                    <span className="text-xs text-gray-500">Balance</span>
                  </div>
                  <div className="text-lg font-semibold text-gray-900 dark:text-white">
                    ${account.balance.toLocaleString()}
                  </div>
                </div>
                
                <div className="text-center">
                  <div className="flex items-center justify-center mb-1">
                    <ScaleIcon className="h-4 w-4 text-gray-400 mr-1" />
                    <span className="text-xs text-gray-500">Equity</span>
                  </div>
                  <div className="text-lg font-semibold text-gray-900 dark:text-white">
                    ${account.equity.toLocaleString()}
                  </div>
                </div>
              </div>

              {/* P&L Display */}
              <div className="mb-4">
                <div className="flex items-center justify-center mb-1">
                  <ChartBarIcon className="h-4 w-4 text-gray-400 mr-1" />
                  <span className="text-xs text-gray-500">Unrealized P&L</span>
                </div>
                <div className={`text-xl font-bold text-center ${
                  account.unrealizedPnL >= 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {account.unrealizedPnL >= 0 ? '+' : ''}${account.unrealizedPnL.toFixed(2)}
                </div>
                <div className={`text-xs text-center ${
                  account.unrealizedPnL >= 0 ? 'text-green-500' : 'text-red-500'
                }`}>
                  {account.equity > 0 ? 
                    `${((account.unrealizedPnL / account.equity) * 100).toFixed(2)}%` : 
                    '0.00%'
                  }
                </div>
              </div>

              {/* Activity Summary */}
              <div className="grid grid-cols-2 gap-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                <div className="text-center">
                  <div className="flex items-center justify-center mb-1">
                    <BoltIcon className="h-3 w-3 text-gray-400 mr-1" />
                    <span className="text-xs text-gray-500">Active Bots</span>
                  </div>
                  <div className="text-sm font-medium text-gray-900 dark:text-white">
                    {account.activeBots}
                  </div>
                </div>
                
                <div className="text-center">
                  <div className="flex items-center justify-center mb-1">
                    <ChartBarIcon className="h-3 w-3 text-gray-400 mr-1" />
                    <span className="text-xs text-gray-500">Positions</span>
                  </div>
                  <div className="text-sm font-medium text-gray-900 dark:text-white">
                    {account.positionCount}
                  </div>
                </div>
              </div>

              {/* Risk Score Visualization */}
              <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs text-gray-500">Risk Score</span>
                  <span className={`text-xs font-medium ${getRiskColor(account.riskScore).split(' ')[0]}`}>
                    {account.riskScore.toFixed(1)}/10
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className={`h-2 rounded-full transition-all duration-300 ${
                      account.riskScore <= 3 ? 'bg-green-500' :
                      account.riskScore <= 6 ? 'bg-yellow-500' : 'bg-red-500'
                    }`}
                    style={{ width: `${(account.riskScore / 10) * 100}%` }}
                  />
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Summary Statistics */}
        {accountSummaries.length > 1 && (
          <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
            <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-4">
              Portfolio Summary
            </h4>
            
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <div className="text-lg font-semibold text-gray-900 dark:text-white">
                  ${accountSummaries.reduce((sum, acc) => sum + acc.balance, 0).toLocaleString()}
                </div>
                <div className="text-xs text-gray-500">Total Balance</div>
              </div>
              
              <div className="text-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <div className="text-lg font-semibold text-gray-900 dark:text-white">
                  ${accountSummaries.reduce((sum, acc) => sum + acc.equity, 0).toLocaleString()}
                </div>
                <div className="text-xs text-gray-500">Total Equity</div>
              </div>
              
              <div className="text-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <div className={`text-lg font-semibold ${
                  accountSummaries.reduce((sum, acc) => sum + acc.unrealizedPnL, 0) >= 0 
                    ? 'text-green-600' : 'text-red-600'
                }`}>
                  {accountSummaries.reduce((sum, acc) => sum + acc.unrealizedPnL, 0) >= 0 ? '+' : ''}
                  ${accountSummaries.reduce((sum, acc) => sum + acc.unrealizedPnL, 0).toFixed(2)}
                </div>
                <div className="text-xs text-gray-500">Total P&L</div>
              </div>
              
              <div className="text-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <div className="text-lg font-semibold text-gray-900 dark:text-white">
                  {accountSummaries.reduce((sum, acc) => sum + acc.activeBots, 0)}
                </div>
                <div className="text-xs text-gray-500">Active Bots</div>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}