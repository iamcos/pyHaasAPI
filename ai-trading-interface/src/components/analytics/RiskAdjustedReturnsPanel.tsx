import React from 'react'
import { 
  ScaleIcon,
  ShieldCheckIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon
} from '@heroicons/react/24/outline'
import { Card, CardHeader, CardContent } from '@/components/ui'
import type { RiskAdjustedMetrics } from '@/services/analyticsService'

interface RiskAdjustedReturnsPanelProps {
  riskMetrics: RiskAdjustedMetrics
  loading?: boolean
}

export function RiskAdjustedReturnsPanel({ riskMetrics, loading = false }: RiskAdjustedReturnsPanelProps) {
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

  const getMetricColor = (value: number, type: 'ratio' | 'var' | 'alpha') => {
    if (type === 'var') {
      // VaR is negative, so more negative is worse
      if (value <= -0.1) return 'text-red-600'
      if (value <= -0.05) return 'text-orange-600'
      return 'text-green-600'
    } else if (type === 'alpha') {
      if (value >= 0.02) return 'text-green-600'
      if (value >= 0) return 'text-yellow-600'
      return 'text-red-600'
    } else {
      // Ratios - higher is better
      if (value >= 1.5) return 'text-green-600'
      if (value >= 1.0) return 'text-yellow-600'
      return 'text-red-600'
    }
  }

  const getMetricDescription = (metric: string) => {
    const descriptions: Record<string, string> = {
      sharpeRatio: 'Risk-adjusted return per unit of volatility',
      sortinoRatio: 'Return per unit of downside deviation',
      calmarRatio: 'Annual return divided by maximum drawdown',
      omegaRatio: 'Probability weighted ratio of gains vs losses',
      informationRatio: 'Active return per unit of tracking error',
      treynorRatio: 'Excess return per unit of systematic risk',
      jensenAlpha: 'Risk-adjusted excess return over benchmark',
      modigliani: 'Risk-adjusted performance measure',
      var95: '95% confidence Value at Risk',
      var99: '99% confidence Value at Risk',
      cvar95: '95% confidence Conditional Value at Risk',
      cvar99: '99% confidence Conditional Value at Risk'
    }
    return descriptions[metric] || ''
  }

  const riskAdjustedRatios = [
    { key: 'sharpeRatio', label: 'Sharpe Ratio', value: riskMetrics.sharpeRatio, type: 'ratio' as const },
    { key: 'sortinoRatio', label: 'Sortino Ratio', value: riskMetrics.sortinoRatio, type: 'ratio' as const },
    { key: 'calmarRatio', label: 'Calmar Ratio', value: riskMetrics.calmarRatio, type: 'ratio' as const },
    { key: 'omegaRatio', label: 'Omega Ratio', value: riskMetrics.omegaRatio, type: 'ratio' as const },
    { key: 'informationRatio', label: 'Information Ratio', value: riskMetrics.informationRatio, type: 'ratio' as const },
    { key: 'treynorRatio', label: 'Treynor Ratio', value: riskMetrics.treynorRatio, type: 'ratio' as const }
  ]

  const performanceMetrics = [
    { key: 'jensenAlpha', label: 'Jensen Alpha', value: riskMetrics.jensenAlpha, type: 'alpha' as const },
    { key: 'modigliani', label: 'Modigliani M²', value: riskMetrics.modigliani, type: 'ratio' as const }
  ]

  const riskMetricsData = [
    { key: 'var95', label: 'VaR (95%)', value: riskMetrics.var95, type: 'var' as const },
    { key: 'var99', label: 'VaR (99%)', value: riskMetrics.var99, type: 'var' as const },
    { key: 'cvar95', label: 'CVaR (95%)', value: riskMetrics.cvar95, type: 'var' as const },
    { key: 'cvar99', label: 'CVaR (99%)', value: riskMetrics.cvar99, type: 'var' as const }
  ]

  const formatValue = (value: number, type: 'ratio' | 'var' | 'alpha') => {
    if (type === 'var' || type === 'alpha') {
      return `${(value * 100).toFixed(2)}%`
    }
    return value.toFixed(2)
  }

  return (
    <div className="space-y-6">
      {/* Risk-Adjusted Ratios */}
      <Card>
        <CardHeader 
          title="Risk-Adjusted Performance Ratios"
          subtitle="Higher values indicate better risk-adjusted performance"
        />
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {riskAdjustedRatios.map((metric) => (
              <div key={metric.key} className="p-4 border border-gray-200 rounded-lg hover:shadow-sm transition-shadow">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-medium text-gray-900">{metric.label}</h4>
                  <ScaleIcon className="h-5 w-5 text-gray-400" />
                </div>
                <div className={`text-2xl font-bold ${getMetricColor(metric.value, metric.type)}`}>
                  {formatValue(metric.value, metric.type)}
                </div>
                <p className="text-xs text-gray-500 mt-2">
                  {getMetricDescription(metric.key)}
                </p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Performance Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader title="Alpha & Performance Measures" />
          <CardContent>
            <div className="space-y-4">
              {performanceMetrics.map((metric) => (
                <div key={metric.key} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div>
                    <div className="font-medium text-gray-900">{metric.label}</div>
                    <div className="text-xs text-gray-500 mt-1">
                      {getMetricDescription(metric.key)}
                    </div>
                  </div>
                  <div className={`text-lg font-semibold ${getMetricColor(metric.value, metric.type)}`}>
                    {formatValue(metric.value, metric.type)}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader title="Value at Risk (VaR) Metrics" />
          <CardContent>
            <div className="space-y-4">
              {riskMetricsData.map((metric) => (
                <div key={metric.key} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div>
                    <div className="font-medium text-gray-900">{metric.label}</div>
                    <div className="text-xs text-gray-500 mt-1">
                      {getMetricDescription(metric.key)}
                    </div>
                  </div>
                  <div className={`text-lg font-semibold ${getMetricColor(metric.value, metric.type)}`}>
                    {formatValue(metric.value, metric.type)}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Risk Assessment */}
      <Card>
        <CardHeader title="Risk Assessment Summary" />
        <CardContent>
          <div className="space-y-4">
            {/* Sharpe Ratio Assessment */}
            {riskMetrics.sharpeRatio >= 1.5 && (
              <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                <div className="flex items-start space-x-3">
                  <ShieldCheckIcon className="h-5 w-5 text-green-600 mt-0.5" />
                  <div>
                    <h4 className="font-medium text-green-800">Excellent Risk-Adjusted Performance</h4>
                    <p className="text-sm text-green-700 mt-1">
                      Sharpe ratio of {riskMetrics.sharpeRatio.toFixed(2)} indicates strong risk-adjusted returns. 
                      The portfolio is generating good returns relative to the risk taken.
                    </p>
                  </div>
                </div>
              </div>
            )}

            {riskMetrics.sharpeRatio < 1.0 && (
              <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                <div className="flex items-start space-x-3">
                  <ExclamationTriangleIcon className="h-5 w-5 text-yellow-600 mt-0.5" />
                  <div>
                    <h4 className="font-medium text-yellow-800">Below Average Risk-Adjusted Performance</h4>
                    <p className="text-sm text-yellow-700 mt-1">
                      Sharpe ratio of {riskMetrics.sharpeRatio.toFixed(2)} suggests room for improvement. 
                      Consider optimizing the risk-return profile of your portfolio.
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* VaR Assessment */}
            {Math.abs(riskMetrics.var95) > 0.1 && (
              <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                <div className="flex items-start space-x-3">
                  <ExclamationTriangleIcon className="h-5 w-5 text-red-600 mt-0.5" />
                  <div>
                    <h4 className="font-medium text-red-800">High Value at Risk</h4>
                    <p className="text-sm text-red-700 mt-1">
                      95% VaR of {(riskMetrics.var95 * 100).toFixed(1)}% indicates significant potential losses. 
                      Consider reducing position sizes or improving diversification.
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Alpha Assessment */}
            {riskMetrics.jensenAlpha > 0.02 && (
              <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                <div className="flex items-start space-x-3">
                  <InformationCircleIcon className="h-5 w-5 text-green-600 mt-0.5" />
                  <div>
                    <h4 className="font-medium text-green-800">Positive Alpha Generation</h4>
                    <p className="text-sm text-green-700 mt-1">
                      Jensen Alpha of {(riskMetrics.jensenAlpha * 100).toFixed(2)}% shows the portfolio is 
                      generating excess returns above what would be expected given its risk level.
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* General Risk Guidance */}
            <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <div className="flex items-start space-x-3">
                <InformationCircleIcon className="h-5 w-5 text-blue-600 mt-0.5" />
                <div>
                  <h4 className="font-medium text-blue-800">Risk Management Guidelines</h4>
                  <ul className="text-sm text-blue-700 mt-1 space-y-1">
                    <li>• Sharpe ratio above 1.0 is generally considered good</li>
                    <li>• Sortino ratio focuses on downside risk and should be higher than Sharpe</li>
                    <li>• VaR represents potential losses at given confidence levels</li>
                    <li>• Positive alpha indicates outperformance relative to systematic risk</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Metric Comparison Chart Placeholder */}
      <Card>
        <CardHeader title="Risk-Return Profile Visualization" />
        <CardContent>
          <div className="h-64 bg-gray-50 rounded-lg flex items-center justify-center">
            <div className="text-center">
              <ScaleIcon className="h-12 w-12 text-gray-400 mx-auto mb-2" />
              <p className="text-gray-600">Risk-return scatter plot would be rendered here</p>
              <p className="text-sm text-gray-500 mt-1">
                Showing portfolio position relative to efficient frontier
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}