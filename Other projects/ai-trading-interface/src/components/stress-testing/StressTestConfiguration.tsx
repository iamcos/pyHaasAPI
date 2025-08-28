import React from 'react'
import { Card, CardHeader, CardContent } from '@/components/ui'
import type { StressTestScenario, StressTestConfiguration as StressTestConfig } from '@/services/stressTestingService'
import type { Bot, Position, Market } from '@/types/trading'

interface StressTestConfigurationProps {
  scenario: StressTestScenario
  configuration: Partial<StressTestConfig>
  onConfigurationChange: (config: Partial<StressTestConfig>) => void
  portfolioData: {
    bots: Bot[]
    positions: Position[]
    markets: Market[]
  }
}

export function StressTestConfiguration({ 
  scenario, 
  configuration, 
  onConfigurationChange,
  portfolioData 
}: StressTestConfigurationProps) {
  const updateConfig = (updates: Partial<StressTestConfig>) => {
    onConfigurationChange({ ...configuration, ...updates })
  }

  return (
    <div className="space-y-6">
      {/* Scenario Summary */}
      <Card>
        <CardHeader title={`Configuring: ${scenario.name}`} />
        <CardContent>
          <p className="text-sm text-gray-600">{scenario.description}</p>
          <div className="mt-3 flex items-center space-x-4 text-sm">
            <span>Duration: {scenario.duration} days</span>
            <span>Severity: {scenario.severity}</span>
            <span>Probability: {(scenario.probability * 100).toFixed(1)}%</span>
          </div>
        </CardContent>
      </Card>

      {/* Portfolio Settings */}
      <Card>
        <CardHeader title="Portfolio Settings" />
        <CardContent>
          <div className="space-y-4">
            <div>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={configuration.portfolioSettings?.includeAllPositions ?? true}
                  onChange={(e) => updateConfig({
                    portfolioSettings: {
                      ...configuration.portfolioSettings,
                      includeAllPositions: e.target.checked,
                      selectedAssets: [],
                      selectedStrategies: [],
                      rebalancingFrequency: 'none',
                      cashBuffer: 0
                    }
                  })}
                  className="mr-2"
                />
                <span className="text-sm font-medium">Include all positions</span>
              </label>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Cash Buffer (%)
                </label>
                <input
                  type="number"
                  value={(configuration.portfolioSettings?.cashBuffer ?? 0) * 100}
                  onChange={(e) => updateConfig({
                    portfolioSettings: {
                      ...configuration.portfolioSettings,
                      includeAllPositions: true,
                      selectedAssets: [],
                      selectedStrategies: [],
                      rebalancingFrequency: 'none',
                      cashBuffer: Number(e.target.value) / 100
                    }
                  })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  min="0"
                  max="50"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Rebalancing
                </label>
                <select
                  value={configuration.portfolioSettings?.rebalancingFrequency ?? 'none'}
                  onChange={(e) => updateConfig({
                    portfolioSettings: {
                      ...configuration.portfolioSettings,
                      includeAllPositions: true,
                      selectedAssets: [],
                      selectedStrategies: [],
                      rebalancingFrequency: e.target.value as any,
                      cashBuffer: 0
                    }
                  })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                >
                  <option value="none">No Rebalancing</option>
                  <option value="daily">Daily</option>
                  <option value="weekly">Weekly</option>
                  <option value="monthly">Monthly</option>
                </select>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Simulation Settings */}
      <Card>
        <CardHeader title="Simulation Settings" />
        <CardContent>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Time Step (hours)
              </label>
              <select
                value={configuration.simulationSettings?.timeStep ?? 24}
                onChange={(e) => updateConfig({
                  simulationSettings: {
                    ...configuration.simulationSettings,
                    timeStep: Number(e.target.value),
                    monteCarloRuns: 1,
                    confidenceLevel: 0.95,
                    includeTransactionCosts: false,
                    includeSlippage: false
                  }
                })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              >
                <option value={1}>1 hour</option>
                <option value={4}>4 hours</option>
                <option value={24}>1 day</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Confidence Level
              </label>
              <select
                value={configuration.simulationSettings?.confidenceLevel ?? 0.95}
                onChange={(e) => updateConfig({
                  simulationSettings: {
                    ...configuration.simulationSettings,
                    timeStep: 24,
                    monteCarloRuns: 1,
                    confidenceLevel: Number(e.target.value),
                    includeTransactionCosts: false,
                    includeSlippage: false
                  }
                })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              >
                <option value={0.90}>90%</option>
                <option value={0.95}>95%</option>
                <option value={0.99}>99%</option>
              </select>
            </div>
          </div>
          
          <div className="mt-4 space-y-2">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={configuration.simulationSettings?.includeTransactionCosts ?? false}
                onChange={(e) => updateConfig({
                  simulationSettings: {
                    ...configuration.simulationSettings,
                    timeStep: 24,
                    monteCarloRuns: 1,
                    confidenceLevel: 0.95,
                    includeTransactionCosts: e.target.checked,
                    includeSlippage: false
                  }
                })}
                className="mr-2"
              />
              <span className="text-sm">Include transaction costs</span>
            </label>
            
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={configuration.simulationSettings?.includeSlippage ?? false}
                onChange={(e) => updateConfig({
                  simulationSettings: {
                    ...configuration.simulationSettings,
                    timeStep: 24,
                    monteCarloRuns: 1,
                    confidenceLevel: 0.95,
                    includeTransactionCosts: false,
                    includeSlippage: e.target.checked
                  }
                })}
                className="mr-2"
              />
              <span className="text-sm">Include slippage</span>
            </label>
          </div>
        </CardContent>
      </Card>

      {/* Portfolio Summary */}
      <Card>
        <CardHeader title="Portfolio Summary" />
        <CardContent>
          <div className="grid grid-cols-3 gap-4 text-center">
            <div className="p-3 bg-gray-50 rounded-lg">
              <div className="text-lg font-semibold text-gray-900">
                {portfolioData.positions.length}
              </div>
              <div className="text-sm text-gray-600">Positions</div>
            </div>
            
            <div className="p-3 bg-gray-50 rounded-lg">
              <div className="text-lg font-semibold text-gray-900">
                {portfolioData.bots.filter(b => b.status === 'active').length}
              </div>
              <div className="text-sm text-gray-600">Active Bots</div>
            </div>
            
            <div className="p-3 bg-gray-50 rounded-lg">
              <div className="text-lg font-semibold text-gray-900">
                {portfolioData.markets.length}
              </div>
              <div className="text-sm text-gray-600">Markets</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}