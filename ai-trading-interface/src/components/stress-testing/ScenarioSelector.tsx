import React, { useState } from 'react'
import { 
  ExclamationTriangleIcon,
  PlusIcon,
  InformationCircleIcon,
  ChartBarIcon
} from '@heroicons/react/24/outline'
import { Card, CardHeader, CardContent, Button } from '@/components/ui'
import { CustomScenarioModal } from './CustomScenarioModal'
import type { StressTestScenario } from '@/services/stressTestingService'

interface ScenarioSelectorProps {
  scenarios: StressTestScenario[]
  selectedScenario: StressTestScenario | null
  onScenarioSelect: (scenario: StressTestScenario) => void
  onCreateCustom: (scenario: StressTestScenario) => void
}

export function ScenarioSelector({ 
  scenarios, 
  selectedScenario, 
  onScenarioSelect, 
  onCreateCustom 
}: ScenarioSelectorProps) {
  const [showCustomModal, setShowCustomModal] = useState(false)
  const [selectedCategory, setSelectedCategory] = useState<string>('all')

  const categories = [
    { key: 'all', label: 'All Scenarios' },
    { key: 'market_crash', label: 'Market Crash' },
    { key: 'volatility_spike', label: 'Volatility Spike' },
    { key: 'correlation_breakdown', label: 'Correlation Breakdown' },
    { key: 'liquidity_crisis', label: 'Liquidity Crisis' },
    { key: 'custom', label: 'Custom' }
  ]

  const filteredScenarios = selectedCategory === 'all' 
    ? scenarios 
    : scenarios.filter(s => s.category === selectedCategory)

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'mild': return 'text-green-600 bg-green-50 border-green-200'
      case 'moderate': return 'text-yellow-600 bg-yellow-50 border-yellow-200'
      case 'severe': return 'text-orange-600 bg-orange-50 border-orange-200'
      case 'extreme': return 'text-red-600 bg-red-50 border-red-200'
      default: return 'text-gray-600 bg-gray-50 border-gray-200'
    }
  }

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'extreme':
      case 'severe':
        return ExclamationTriangleIcon
      default:
        return ChartBarIcon
    }
  }

  return (
    <div className="space-y-6">
      {/* Category Filter */}
      <div className="flex flex-wrap gap-2">
        {categories.map(category => (
          <button
            key={category.key}
            onClick={() => setSelectedCategory(category.key)}
            className={`px-3 py-1 text-sm font-medium rounded-full transition-colors ${
              selectedCategory === category.key
                ? 'bg-primary-100 text-primary-700'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            {category.label}
          </button>
        ))}
      </div>

      {/* Scenario Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {filteredScenarios.map((scenario) => {
          const SeverityIcon = getSeverityIcon(scenario.severity)
          const isSelected = selectedScenario?.id === scenario.id
          
          return (
            <Card 
              key={scenario.id}
              className={`cursor-pointer transition-all ${
                isSelected 
                  ? 'ring-2 ring-primary-500 bg-primary-50' 
                  : 'hover:shadow-md'
              }`}
              onClick={() => onScenarioSelect(scenario)}
            >
              <CardContent className="p-4">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-start space-x-3">
                    <SeverityIcon className="h-6 w-6 text-gray-400 mt-1" />
                    <div>
                      <h3 className="font-medium text-gray-900">{scenario.name}</h3>
                      <p className="text-sm text-gray-600 mt-1">{scenario.description}</p>
                    </div>
                  </div>
                  
                  <div className={`px-2 py-1 text-xs font-medium rounded-full border ${getSeverityColor(scenario.severity)}`}>
                    {scenario.severity}
                  </div>
                </div>

                {/* Scenario Details */}
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-gray-500">Duration:</span>
                    <span className="ml-2 font-medium">{scenario.duration} days</span>
                  </div>
                  <div>
                    <span className="text-gray-500">Probability:</span>
                    <span className="ml-2 font-medium">{(scenario.probability * 100).toFixed(1)}%</span>
                  </div>
                </div>

                {/* Historical Examples */}
                {scenario.historicalExamples.length > 0 && (
                  <div className="mt-3">
                    <div className="text-xs text-gray-500 mb-1">Historical Examples:</div>
                    <div className="flex flex-wrap gap-1">
                      {scenario.historicalExamples.slice(0, 2).map((example, index) => (
                        <span key={index} className="px-2 py-1 text-xs bg-gray-100 rounded">
                          {example}
                        </span>
                      ))}
                      {scenario.historicalExamples.length > 2 && (
                        <span className="px-2 py-1 text-xs bg-gray-100 rounded">
                          +{scenario.historicalExamples.length - 2} more
                        </span>
                      )}
                    </div>
                  </div>
                )}

                {/* Active Parameters Preview */}
                <div className="mt-3 pt-3 border-t border-gray-200">
                  <div className="text-xs text-gray-500 mb-2">Active Parameters:</div>
                  <div className="flex flex-wrap gap-1">
                    {scenario.parameters.marketShock.enabled && (
                      <span className="px-2 py-1 text-xs bg-red-100 text-red-700 rounded">
                        Market Shock
                      </span>
                    )}
                    {scenario.parameters.volatilityChange.enabled && (
                      <span className="px-2 py-1 text-xs bg-orange-100 text-orange-700 rounded">
                        Volatility
                      </span>
                    )}
                    {scenario.parameters.correlationChange.enabled && (
                      <span className="px-2 py-1 text-xs bg-yellow-100 text-yellow-700 rounded">
                        Correlation
                      </span>
                    )}
                    {scenario.parameters.liquidityImpact.enabled && (
                      <span className="px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded">
                        Liquidity
                      </span>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          )
        })}

        {/* Create Custom Scenario Card */}
        <Card 
          className="cursor-pointer border-2 border-dashed border-gray-300 hover:border-primary-400 hover:bg-primary-50 transition-colors"
          onClick={() => setShowCustomModal(true)}
        >
          <CardContent className="p-4 flex flex-col items-center justify-center h-full min-h-48">
            <PlusIcon className="h-12 w-12 text-gray-400 mb-3" />
            <h3 className="font-medium text-gray-900 mb-2">Create Custom Scenario</h3>
            <p className="text-sm text-gray-600 text-center">
              Build your own stress test scenario with custom parameters
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Selected Scenario Details */}
      {selectedScenario && (
        <Card>
          <CardHeader 
            title={`Selected: ${selectedScenario.name}`}
            subtitle="Scenario details and parameters"
          />
          <CardContent>
            <div className="space-y-4">
              {/* Description */}
              <div>
                <h4 className="font-medium text-gray-900 mb-2">Description</h4>
                <p className="text-sm text-gray-600">{selectedScenario.description}</p>
              </div>

              {/* Key Parameters */}
              <div>
                <h4 className="font-medium text-gray-900 mb-2">Key Parameters</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {selectedScenario.parameters.marketShock.enabled && (
                    <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                      <div className="font-medium text-red-800">Market Shock</div>
                      <div className="text-sm text-red-700 mt-1">
                        {(selectedScenario.parameters.marketShock.magnitude * 100).toFixed(1)}% decline
                      </div>
                    </div>
                  )}
                  
                  {selectedScenario.parameters.volatilityChange.enabled && (
                    <div className="p-3 bg-orange-50 border border-orange-200 rounded-lg">
                      <div className="font-medium text-orange-800">Volatility Increase</div>
                      <div className="text-sm text-orange-700 mt-1">
                        {selectedScenario.parameters.volatilityChange.multiplier}x multiplier
                      </div>
                    </div>
                  )}
                  
                  {selectedScenario.parameters.correlationChange.enabled && (
                    <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                      <div className="font-medium text-yellow-800">Correlation Change</div>
                      <div className="text-sm text-yellow-700 mt-1">
                        Target: {(selectedScenario.parameters.correlationChange.newCorrelation * 100).toFixed(0)}%
                      </div>
                    </div>
                  )}
                  
                  {selectedScenario.parameters.liquidityImpact.enabled && (
                    <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                      <div className="font-medium text-blue-800">Liquidity Impact</div>
                      <div className="text-sm text-blue-700 mt-1">
                        {(selectedScenario.parameters.liquidityImpact.liquidityReduction * 100).toFixed(0)}% reduction
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Historical Context */}
              {selectedScenario.historicalExamples.length > 0 && (
                <div>
                  <h4 className="font-medium text-gray-900 mb-2">Historical Context</h4>
                  <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                    <div className="flex items-start space-x-2">
                      <InformationCircleIcon className="h-5 w-5 text-blue-600 mt-0.5" />
                      <div>
                        <div className="text-sm text-blue-800">
                          Similar events have occurred {selectedScenario.historicalExamples.length} times in recent history:
                        </div>
                        <ul className="text-sm text-blue-700 mt-1 space-y-1">
                          {selectedScenario.historicalExamples.map((example, index) => (
                            <li key={index}>• {example}</li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Custom Scenario Modal */}
      {showCustomModal && (
        <CustomScenarioModal
          onClose={() => setShowCustomModal(false)}
          onSave={(scenario) => {
            onCreateCustom(scenario)
            setShowCustomModal(false)
          }}
        />
      )}
    </div>
  )
}