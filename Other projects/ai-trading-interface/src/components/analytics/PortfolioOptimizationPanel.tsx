import React, { useState } from 'react'
import { 
  CpuChipIcon,
  ScaleIcon,
  TrendingUpIcon,
  ShieldCheckIcon,
  LightBulbIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline'
import { Card, CardHeader, CardContent, Button } from '@/components/ui'
import type { OptimizationSuggestions } from '@/services/analyticsService'

interface PortfolioOptimizationPanelProps {
  optimization: OptimizationSuggestions
  loading?: boolean
}

export function PortfolioOptimizationPanel({ optimization, loading = false }: PortfolioOptimizationPanelProps) {
  const [selectedView, setSelectedView] = useState<'allocations' | 'risk' | 'returns' | 'diversification'>('allocations')

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

  const getEfficiencyColor = (efficiency: number) => {
    if (efficiency >= 0.8) return 'text-green-600'
    if (efficiency >= 0.6) return 'text-yellow-600'
    return 'text-red-600'
  }

  const getImpactColor = (impact: number) => {
    if (impact > 0.02) return 'text-green-600'
    if (impact > 0) return 'text-yellow-600'
    return 'text-red-600'
  }

  const renderAllocationsView = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader 
          title="Suggested Asset Allocations"
          subtitle="Optimized weights based on risk-return analysis"
        />
        <CardContent>
          <div className="space-y-4">
            {optimization.suggestedAllocations.map((allocation, index) => (
              <div key={index} className="p-4 border border-gray-200 rounded-lg">
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <h4 className="font-medium text-gray-900">{allocation.asset}</h4>
                    <p className="text-sm text-gray-600 mt-1">{allocation.rationale}</p>
                  </div>
                  <div className="text-right">
                    <div className={`text-sm font-medium ${getImpactColor(allocation.expectedImpact)}`}>
                      {allocation.expectedImpact >= 0 ? '+' : ''}{(allocation.expectedImpact * 100).toFixed(2)}%
                    </div>
                    <div className="text-xs text-gray-500">Expected Impact</div>
                  </div>
                </div>
                
                {/* Weight Comparison */}
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>Current Weight</span>
                    <span>{(allocation.currentWeight * 100).toFixed(1)}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="h-2 bg-blue-500 rounded-full"
                      style={{ width: `${allocation.currentWeight * 100}%` }}
                    />
                  </div>
                  
                  <div className="flex justify-between text-sm">
                    <span>Suggested Weight</span>
                    <span>{(allocation.suggestedWeight * 100).toFixed(1)}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="h-2 bg-green-500 rounded-full"
                      style={{ width: `${allocation.suggestedWeight * 100}%` }}
                    />
                  </div>
                </div>
                
                {/* Confidence */}
                <div className="mt-3 flex items-center justify-between">
                  <span className="text-sm text-gray-600">Confidence</span>
                  <div className="flex items-center space-x-2">
                    <div className="w-20 bg-gray-200 rounded-full h-2">
                      <div 
                        className="h-2 bg-blue-500 rounded-full"
                        style={{ width: `${allocation.confidence * 100}%` }}
                      />
                    </div>
                    <span className="text-sm font-medium">{(allocation.confidence * 100).toFixed(0)}%</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )

  const renderRiskView = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader title="Risk Reduction Opportunities" />
        <CardContent>
          <div className="space-y-4">
            {optimization.riskReduction.map((risk, index) => (
              <div key={index} className="p-4 border border-orange-200 bg-orange-50 rounded-lg">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-start space-x-3">
                    <ShieldCheckIcon className="h-6 w-6 text-orange-600 mt-1" />
                    <div>
                      <h4 className="font-medium text-orange-900 capitalize">
                        {risk.type.replace('_', ' ')} Risk Reduction
                      </h4>
                      <p className="text-sm text-orange-700 mt-1">{risk.description}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-medium text-orange-900">
                      -{(risk.expectedReduction * 100).toFixed(1)}%
                    </div>
                    <div className="text-xs text-orange-600">Expected Reduction</div>
                  </div>
                </div>
                
                {/* Current vs Target */}
                <div className="grid grid-cols-2 gap-4 mb-3">
                  <div className="text-center p-2 bg-white bg-opacity-50 rounded">
                    <div className="text-lg font-semibold text-orange-900">
                      {(risk.currentLevel * 100).toFixed(1)}%
                    </div>
                    <div className="text-xs text-orange-600">Current Level</div>
                  </div>
                  <div className="text-center p-2 bg-white bg-opacity-50 rounded">
                    <div className="text-lg font-semibold text-green-700">
                      {(risk.targetLevel * 100).toFixed(1)}%
                    </div>
                    <div className="text-xs text-green-600">Target Level</div>
                  </div>
                </div>
                
                {/* Actions */}
                <div>
                  <div className="text-sm font-medium text-orange-900 mb-2">Recommended Actions:</div>
                  <ul className="space-y-1">
                    {risk.actions.map((action, actionIndex) => (
                      <li key={actionIndex} className="text-sm text-orange-700 flex items-center space-x-2">
                        <div className="w-1.5 h-1.5 bg-orange-600 rounded-full" />
                        <span>{action}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )

  const renderReturnsView = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader title="Return Enhancement Opportunities" />
        <CardContent>
          <div className="space-y-4">
            {optimization.returnEnhancement.map((enhancement, index) => (
              <div key={index} className="p-4 border border-green-200 bg-green-50 rounded-lg">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-start space-x-3">
                    <TrendingUpIcon className="h-6 w-6 text-green-600 mt-1" />
                    <div>
                      <h4 className="font-medium text-green-900 capitalize">
                        {enhancement.type.replace('_', ' ')} Strategy
                      </h4>
                      <p className="text-sm text-green-700 mt-1">{enhancement.description}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-medium text-green-900">
                      +{(enhancement.expectedReturn * 100).toFixed(1}}%
                    </div>
                    <div className="text-xs text-green-600">Expected Return</div>
                  </div>
                </div>
                
                {/* Risk and Time Horizon */}
                <div className="grid grid-cols-2 gap-4 mb-3">
                  <div className="text-center p-2 bg-white bg-opacity-50 rounded">
                    <div className="text-lg font-semibold text-green-900">
                      {(enhancement.riskLevel * 100).toFixed(0)}%
                    </div>
                    <div className="text-xs text-green-600">Risk Level</div>
                  </div>
                  <div className="text-center p-2 bg-white bg-opacity-50 rounded">
                    <div className="text-sm font-semibold text-green-900">
                      {enhancement.timeHorizon}
                    </div>
                    <div className="text-xs text-green-600">Time Horizon</div>
                  </div>
                </div>
                
                {/* Implementation */}
                <div>
                  <div className="text-sm font-medium text-green-900 mb-2">Implementation Steps:</div>
                  <ul className="space-y-1">
                    {enhancement.implementation.map((step, stepIndex) => (
                      <li key={stepIndex} className="text-sm text-green-700 flex items-center space-x-2">
                        <div className="w-1.5 h-1.5 bg-green-600 rounded-full" />
                        <span>{step}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )

  const renderDiversificationView = () => (
    <div className="space-y-6">
      {optimization.diversificationOpportunities.map((opportunity, index) => (
        <Card key={index}>
          <CardHeader title="Diversification Opportunities" />
          <CardContent>
            <div className="space-y-6">
              {/* Current vs Target Diversification */}
              <div className="grid grid-cols-2 gap-6">
                <div className="text-center p-6 bg-gray-50 rounded-lg">
                  <div className="text-3xl font-bold text-gray-900">
                    {(opportunity.currentDiversification * 100).toFixed(0)}%
                  </div>
                  <div className="text-sm text-gray-600 mt-1">Current Diversification</div>
                </div>
                <div className="text-center p-6 bg-green-50 rounded-lg">
                  <div className="text-3xl font-bold text-green-600">
                    {(opportunity.targetDiversification * 100).toFixed(0)}%
                  </div>
                  <div className="text-sm text-green-600 mt-1">Target Diversification</div>
                </div>
              </div>
              
              {/* Suggested Assets */}
              <div>
                <h4 className="font-medium text-gray-900 mb-3">Suggested Assets for Diversification</h4>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                  {opportunity.suggestedAssets.map((asset, assetIndex) => (
                    <div key={assetIndex} className="p-3 bg-blue-50 border border-blue-200 rounded-lg text-center">
                      <div className="font-medium text-blue-900">{asset}</div>
                    </div>
                  ))}
                </div>
              </div>
              
              {/* Rationale and Benefit */}
              <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <h4 className="font-medium text-blue-900 mb-2">Rationale</h4>
                <p className="text-sm text-blue-700 mb-3">{opportunity.rationale}</p>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-blue-700">Expected Benefit:</span>
                  <span className="font-medium text-blue-900">
                    +{(opportunity.expectedBenefit * 100).toFixed(1}}% improvement
                  </span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  )

  const viewOptions = [
    { key: 'allocations' as const, label: 'Asset Allocation', icon: ScaleIcon },
    { key: 'risk' as const, label: 'Risk Reduction', icon: ShieldCheckIcon },
    { key: 'returns' as const, label: 'Return Enhancement', icon: TrendingUpIcon },
    { key: 'diversification' as const, label: 'Diversification', icon: LightBulbIcon }
  ]

  return (
    <div className="space-y-6">
      {/* Portfolio Efficiency Overview */}
      <Card>
        <CardHeader title="Portfolio Efficiency Score" />
        <CardContent>
          <div className="text-center py-6">
            <div className={`text-6xl font-bold ${getEfficiencyColor(optimization.portfolioEfficiency)}`}>
              {(optimization.portfolioEfficiency * 100).toFixed(0)}%
            </div>
            <div className="text-lg text-gray-600 mt-2">Overall Efficiency</div>
            <div className="mt-4 max-w-md mx-auto">
              <div className="w-full bg-gray-200 rounded-full h-3">
                <div 
                  className={`h-3 rounded-full ${
                    optimization.portfolioEfficiency >= 0.8 ? 'bg-green-500' :
                    optimization.portfolioEfficiency >= 0.6 ? 'bg-yellow-500' : 'bg-red-500'
                  }`}
                  style={{ width: `${optimization.portfolioEfficiency * 100}%` }}
                />
              </div>
            </div>
            <p className="text-sm text-gray-600 mt-3">
              {optimization.portfolioEfficiency >= 0.8 ? 'Highly efficient portfolio' :
               optimization.portfolioEfficiency >= 0.6 ? 'Moderately efficient, room for improvement' :
               'Significant optimization opportunities available'}
            </p>
          </div>
        </CardContent>
      </Card>

      {/* View Selector */}
      <div className="flex space-x-1 bg-gray-100 rounded-lg p-1 overflow-x-auto">
        {viewOptions.map(option => {
          const Icon = option.icon
          return (
            <button
              key={option.key}
              onClick={() => setSelectedView(option.key)}
              className={`flex items-center space-x-2 px-4 py-2 rounded-md text-sm font-medium transition-colors whitespace-nowrap ${
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
      {selectedView === 'allocations' && renderAllocationsView()}
      {selectedView === 'risk' && renderRiskView()}
      {selectedView === 'returns' && renderReturnsView()}
      {selectedView === 'diversification' && renderDiversificationView()}

      {/* Action Buttons */}
      <Card>
        <CardHeader title="Optimization Actions" />
        <CardContent>
          <div className="flex flex-wrap gap-3">
            <Button className="flex items-center space-x-2">
              <ArrowPathIcon className="h-4 w-4" />
              <span>Apply Suggested Allocations</span>
            </Button>
            <Button variant="outline" className="flex items-center space-x-2">
              <CpuChipIcon className="h-4 w-4" />
              <span>Run Full Optimization</span>
            </Button>
            <Button variant="outline" className="flex items-center space-x-2">
              <LightBulbIcon className="h-4 w-4" />
              <span>Generate Custom Strategy</span>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}