import React from 'react'
import { 
  ChartBarIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  ArrowPathIcon,
  DocumentTextIcon
} from '@heroicons/react/24/outline'
import { Card, CardHeader, CardContent, Button } from '@/components/ui'
import type { StressTestResult, StressTestScenario } from '@/services/stressTestingService'

interface StressTestResultsProps {
  result: StressTestResult
  scenario: StressTestScenario
  onViewDetails: () => void
  onRunAnother: () => void
}

export function StressTestResults({ result, scenario, onViewDetails, onRunAnother }: StressTestResultsProps) {
  const getSurvivabilityColor = (score: number) => {
    if (score >= 0.7) return 'text-green-600 bg-green-50'
    if (score >= 0.4) return 'text-yellow-600 bg-yellow-50'
    return 'text-red-600 bg-red-50'
  }

  const getSurvivabilityLabel = (score: number) => {
    if (score >= 0.7) return 'Strong'
    if (score >= 0.4) return 'Moderate'
    return 'Weak'
  }

  const getResultIcon = (score: number) => {
    if (score >= 0.7) return CheckCircleIcon
    if (score >= 0.4) return ExclamationTriangleIcon
    return ExclamationTriangleIcon
  }

  const ResultIcon = getResultIcon(result.results.survivabilityScore)

  return (
    <div className="space-y-6">
      {/* Overall Result */}
      <Card>
        <CardHeader title="Stress Test Results" />
        <CardContent>
          <div className="text-center py-6">
            <ResultIcon className={`h-16 w-16 mx-auto mb-4 ${
              result.results.survivabilityScore >= 0.7 ? 'text-green-500' :
              result.results.survivabilityScore >= 0.4 ? 'text-yellow-500' : 'text-red-500'
            }`} />
            
            <h3 className="text-2xl font-bold text-gray-900 mb-2">
              {getSurvivabilityLabel(result.results.survivabilityScore)} Portfolio Resilience
            </h3>
            
            <div className={`inline-flex items-center px-4 py-2 rounded-full text-lg font-medium ${getSurvivabilityColor(result.results.survivabilityScore)}`}>
              Survivability Score: {(result.results.survivabilityScore * 100).toFixed(0)}%
            </div>
            
            <p className="text-gray-600 mt-4 max-w-2xl mx-auto">
              Your portfolio showed {getSurvivabilityLabel(result.results.survivabilityScore).toLowerCase()} resilience 
              under the {scenario.name} stress scenario. 
              {result.results.survivabilityScore >= 0.7 
                ? ' The portfolio maintained good performance despite adverse conditions.'
                : result.results.survivabilityScore >= 0.4
                ? ' There are opportunities to improve risk management.'
                : ' Significant improvements to risk management are recommended.'
              }
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4 text-center">
            <div className={`text-2xl font-bold ${
              result.results.totalReturn >= 0 ? 'text-green-600' : 'text-red-600'
            }`}>
              {result.results.totalReturn >= 0 ? '+' : ''}{(result.results.totalReturn * 100).toFixed(1)}%
            </div>
            <div className="text-sm text-gray-600 mt-1">Total Return</div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold text-red-600">
              -{(result.results.maxDrawdown * 100).toFixed(1)}%
            </div>
            <div className="text-sm text-gray-600 mt-1">Max Drawdown</div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold text-gray-900">
              {result.results.sharpeRatio.toFixed(2)}
            </div>
            <div className="text-sm text-gray-600 mt-1">Sharpe Ratio</div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold text-gray-900">
              {result.results.recoveryTime}
            </div>
            <div className="text-sm text-gray-600 mt-1">Recovery Days</div>
          </CardContent>
        </Card>
      </div>

      {/* Portfolio Impact Summary */}
      <Card>
        <CardHeader title="Portfolio Impact" />
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center">
              <div className="text-lg font-semibold text-gray-900">
                ${result.portfolioImpact.initialValue.toLocaleString()}
              </div>
              <div className="text-sm text-gray-600">Initial Value</div>
            </div>
            
            <div className="text-center">
              <div className="text-lg font-semibold text-gray-900">
                ${result.portfolioImpact.worstValue.toLocaleString()}
              </div>
              <div className="text-sm text-gray-600">Worst Value</div>
            </div>
            
            <div className="text-center">
              <div className="text-lg font-semibold text-gray-900">
                ${result.portfolioImpact.finalValue.toLocaleString()}
              </div>
              <div className="text-sm text-gray-600">Final Value</div>
            </div>
          </div>
          
          <div className="mt-6">
            <div className="flex justify-between text-sm mb-2">
              <span>Peak-to-Trough Impact</span>
              <span className="font-medium">
                -{(result.portfolioImpact.peakToTrough * 100).toFixed(1)}%
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-red-500 h-2 rounded-full"
                style={{ width: `${result.portfolioImpact.peakToTrough * 100}%` }}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Top Recommendations */}
      <Card>
        <CardHeader title="Key Recommendations" />
        <CardContent>
          <div className="space-y-3">
            {result.recommendations.slice(0, 3).map((rec, index) => (
              <div key={index} className={`p-4 rounded-lg border ${
                rec.priority === 'high' ? 'bg-red-50 border-red-200' :
                rec.priority === 'medium' ? 'bg-yellow-50 border-yellow-200' :
                'bg-blue-50 border-blue-200'
              }`}>
                <div className="flex items-start justify-between">
                  <div>
                    <h4 className={`font-medium ${
                      rec.priority === 'high' ? 'text-red-800' :
                      rec.priority === 'medium' ? 'text-yellow-800' :
                      'text-blue-800'
                    }`}>
                      {rec.title}
                    </h4>
                    <p className={`text-sm mt-1 ${
                      rec.priority === 'high' ? 'text-red-700' :
                      rec.priority === 'medium' ? 'text-yellow-700' :
                      'text-blue-700'
                    }`}>
                      {rec.description}
                    </p>
                  </div>
                  <div className={`px-2 py-1 text-xs font-medium rounded-full ${
                    rec.priority === 'high' ? 'bg-red-100 text-red-800' :
                    rec.priority === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-blue-100 text-blue-800'
                  }`}>
                    {rec.priority}
                  </div>
                </div>
              </div>
            ))}
          </div>
          
          {result.recommendations.length > 3 && (
            <div className="mt-4 text-center">
              <Button variant="outline" onClick={onViewDetails}>
                View All {result.recommendations.length} Recommendations
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Risk Metrics Summary */}
      <Card>
        <CardHeader title="Risk Metrics" />
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            <div className="text-center p-3 bg-gray-50 rounded-lg">
              <div className="text-lg font-semibold text-gray-900">
                {(result.riskMetrics.concentrationRisk * 100).toFixed(0)}%
              </div>
              <div className="text-xs text-gray-600">Concentration Risk</div>
            </div>
            
            <div className="text-center p-3 bg-gray-50 rounded-lg">
              <div className="text-lg font-semibold text-gray-900">
                {(result.riskMetrics.correlationRisk * 100).toFixed(0)}%
              </div>
              <div className="text-xs text-gray-600">Correlation Risk</div>
            </div>
            
            <div className="text-center p-3 bg-gray-50 rounded-lg">
              <div className="text-lg font-semibold text-gray-900">
                {(result.riskMetrics.liquidityRisk * 100).toFixed(0)}%
              </div>
              <div className="text-xs text-gray-600">Liquidity Risk</div>
            </div>
            
            <div className="text-center p-3 bg-gray-50 rounded-lg">
              <div className="text-lg font-semibold text-gray-900">
                {(result.riskMetrics.tailRisk * 100).toFixed(1)}%
              </div>
              <div className="text-xs text-gray-600">Tail Risk (VaR)</div>
            </div>
            
            <div className="text-center p-3 bg-gray-50 rounded-lg">
              <div className="text-lg font-semibold text-gray-900">
                {(result.riskMetrics.leverageRisk * 100).toFixed(0)}%
              </div>
              <div className="text-xs text-gray-600">Leverage Risk</div>
            </div>
            
            <div className="text-center p-3 bg-gray-50 rounded-lg">
              <div className="text-lg font-semibold text-gray-900">
                {(result.riskMetrics.systemicRisk * 100).toFixed(0)}%
              </div>
              <div className="text-xs text-gray-600">Systemic Risk</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Action Buttons */}
      <div className="flex justify-center space-x-4">
        <Button
          onClick={onViewDetails}
          className="flex items-center space-x-2"
        >
          <DocumentTextIcon className="h-4 w-4" />
          <span>View Detailed Report</span>
        </Button>
        
        <Button
          onClick={onRunAnother}
          variant="outline"
          className="flex items-center space-x-2"
        >
          <ArrowPathIcon className="h-4 w-4" />
          <span>Run Another Test</span>
        </Button>
      </div>
    </div>
  )
}