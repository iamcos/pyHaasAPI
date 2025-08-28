import React, { useState } from 'react'
import { 
  ArrowLeftIcon,
  DocumentArrowDownIcon,
  ChartBarIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline'
import { Card, CardHeader, CardContent, Button } from '@/components/ui'
import type { StressTestResult, StressTestScenario } from '@/services/stressTestingService'

interface StressTestReportingProps {
  result: StressTestResult
  scenario: StressTestScenario
  onBack: () => void
  onExport: (format: 'json' | 'csv' | 'pdf') => void
}

export function StressTestReporting({ result, scenario, onBack, onExport }: StressTestReportingProps) {
  const [selectedTab, setSelectedTab] = useState<'overview' | 'assets' | 'recommendations' | 'timeseries'>('overview')

  const tabs = [
    { key: 'overview' as const, label: 'Overview' },
    { key: 'assets' as const, label: 'Asset Impact' },
    { key: 'recommendations' as const, label: 'Recommendations' },
    { key: 'timeseries' as const, label: 'Time Series' }
  ]

  const renderOverview = () => (
    <div className="space-y-6">
      {/* Executive Summary */}
      <Card>
        <CardHeader title="Executive Summary" />
        <CardContent>
          <div className="prose max-w-none">
            <p className="text-gray-700">
              The stress test simulation of the <strong>{scenario.name}</strong> scenario 
              revealed a portfolio survivability score of <strong>{(result.results.survivabilityScore * 100).toFixed(0)}%</strong>, 
              indicating {result.results.survivabilityScore >= 0.7 ? 'strong' : result.results.survivabilityScore >= 0.4 ? 'moderate' : 'weak'} resilience 
              under adverse market conditions.
            </p>
            
            <p className="text-gray-700">
              Key findings include a maximum drawdown of <strong>{(result.results.maxDrawdown * 100).toFixed(1)}%</strong> 
              and a total return of <strong>{result.results.totalReturn >= 0 ? '+' : ''}{(result.results.totalReturn * 100).toFixed(1)}%</strong> 
              over the {scenario.duration}-day stress period.
            </p>
            
            <p className="text-gray-700">
              The portfolio's recovery time was <strong>{result.results.recoveryTime} days</strong>, 
              with a Sharpe ratio of <strong>{result.results.sharpeRatio.toFixed(2)}</strong> during the stress period.
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Detailed Metrics */}
      <Card>
        <CardHeader title="Detailed Performance Metrics" />
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-6">
            <div>
              <h4 className="font-medium text-gray-900 mb-3">Return Metrics</h4>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span>Total Return:</span>
                  <span className={result.results.totalReturn >= 0 ? 'text-green-600' : 'text-red-600'}>
                    {result.results.totalReturn >= 0 ? '+' : ''}{(result.results.totalReturn * 100).toFixed(2)}%
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Sharpe Ratio:</span>
                  <span>{result.results.sharpeRatio.toFixed(3)}</span>
                </div>
                <div className="flex justify-between">
                  <span>Volatility:</span>
                  <span>{(result.results.volatility * 100).toFixed(1}}%</span>
                </div>
              </div>
            </div>
            
            <div>
              <h4 className="font-medium text-gray-900 mb-3">Risk Metrics</h4>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span>Max Drawdown:</span>
                  <span className="text-red-600">-{(result.results.maxDrawdown * 100).toFixed(2)}%</span>
                </div>
                <div className="flex justify-between">
                  <span>VaR (95%):</span>
                  <span className="text-red-600">{(result.results.var95 * 100).toFixed(2)}%</span>
                </div>
                <div className="flex justify-between">
                  <span>VaR (99%):</span>
                  <span className="text-red-600">{(result.results.var99 * 100).toFixed(2)}%</span>
                </div>
                <div className="flex justify-between">
                  <span>Expected Shortfall:</span>
                  <span className="text-red-600">{(result.results.expectedShortfall * 100).toFixed(2)}%</span>
                </div>
              </div>
            </div>
            
            <div>
              <h4 className="font-medium text-gray-900 mb-3">Recovery Metrics</h4>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span>Recovery Time:</span>
                  <span>{result.results.recoveryTime} days</span>
                </div>
                <div className="flex justify-between">
                  <span>Survivability:</span>
                  <span className={
                    result.results.survivabilityScore >= 0.7 ? 'text-green-600' :
                    result.results.survivabilityScore >= 0.4 ? 'text-yellow-600' : 'text-red-600'
                  }>
                    {(result.results.survivabilityScore * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )

  const renderAssetImpact = () => (
    <Card>
      <CardHeader title="Asset Impact Analysis" />
      <CardContent>
        <div className="space-y-4">
          {result.portfolioImpact.assetImpacts.map((asset, index) => (
            <div key={index} className="p-4 border border-gray-200 rounded-lg">
              <div className="flex items-center justify-between mb-3">
                <h4 className="font-medium text-gray-900">{asset.asset}</h4>
                <div className={`text-sm font-medium ${
                  asset.pnlPercentage >= 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {asset.pnlPercentage >= 0 ? '+' : ''}{(asset.pnlPercentage * 100).toFixed(1)}%
                </div>
              </div>
              
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <span className="text-gray-500">Initial Weight:</span>
                  <div className="font-medium">{(asset.initialWeight * 100).toFixed(1)}%</div>
                </div>
                <div>
                  <span className="text-gray-500">Final Weight:</span>
                  <div className="font-medium">{(asset.finalWeight * 100).toFixed(1)}%</div>
                </div>
                <div>
                  <span className="text-gray-500">P&L:</span>
                  <div className={`font-medium ${asset.pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    ${asset.pnl.toFixed(2)}
                  </div>
                </div>
                <div>
                  <span className="text-gray-500">Max Drawdown:</span>
                  <div className="font-medium text-red-600">
                    -{(asset.maxDrawdown * 100).toFixed(1)}%
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )

  const renderRecommendations = () => (
    <div className="space-y-4">
      {result.recommendations.map((rec, index) => (
        <Card key={index}>
          <CardContent className="p-4">
            <div className="flex items-start justify-between mb-3">
              <div>
                <h4 className="font-medium text-gray-900">{rec.title}</h4>
                <p className="text-sm text-gray-600 mt-1">{rec.description}</p>
              </div>
              <div className={`px-2 py-1 text-xs font-medium rounded-full ${
                rec.priority === 'high' ? 'bg-red-100 text-red-800' :
                rec.priority === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                'bg-blue-100 text-blue-800'
              }`}>
                {rec.priority}
              </div>
            </div>
            
            <div className="grid grid-cols-3 gap-4 mb-4 text-sm">
              <div>
                <span className="text-gray-500">Expected Benefit:</span>
                <div className="font-medium text-green-600">
                  +{(rec.expectedBenefit * 100).toFixed(1}}%
                </div>
              </div>
              <div>
                <span className="text-gray-500">Implementation Cost:</span>
                <div className="font-medium">
                  {(rec.implementationCost * 100).toFixed(1}}%
                </div>
              </div>
              <div>
                <span className="text-gray-500">Timeframe:</span>
                <div className="font-medium">{rec.timeframe}</div>
              </div>
            </div>
            
            <div>
              <h5 className="text-sm font-medium text-gray-900 mb-2">Action Items:</h5>
              <ul className="space-y-1">
                {rec.actions.map((action, actionIndex) => (
                  <li key={actionIndex} className="text-sm text-gray-600 flex items-start">
                    <span className="w-1.5 h-1.5 bg-gray-400 rounded-full mt-2 mr-2 flex-shrink-0" />
                    {action}
                  </li>
                ))}
              </ul>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  )

  const renderTimeSeries = () => (
    <Card>
      <CardHeader title="Time Series Analysis" />
      <CardContent>
        <div className="space-y-6">
          {/* Chart Placeholder */}
          <div className="h-64 bg-gray-50 rounded-lg flex items-center justify-center">
            <div className="text-center">
              <ChartBarIcon className="h-12 w-12 text-gray-400 mx-auto mb-2" />
              <p className="text-gray-600">Time series chart would be rendered here</p>
              <p className="text-sm text-gray-500 mt-1">
                Showing {result.timeSeriesData.length} data points over {scenario.duration} days
              </p>
            </div>
          </div>
          
          {/* Key Events */}
          <div>
            <h4 className="font-medium text-gray-900 mb-3">Key Events During Stress Period</h4>
            <div className="space-y-2">
              <div className="flex items-center space-x-3 p-2 bg-red-50 rounded">
                <ExclamationTriangleIcon className="h-4 w-4 text-red-600" />
                <span className="text-sm">Maximum drawdown reached: Day {Math.floor(scenario.duration * 0.3)}</span>
              </div>
              <div className="flex items-center space-x-3 p-2 bg-yellow-50 rounded">
                <ExclamationTriangleIcon className="h-4 w-4 text-yellow-600" />
                <span className="text-sm">Highest volatility period: Days {Math.floor(scenario.duration * 0.2)}-{Math.floor(scenario.duration * 0.5)}</span>
              </div>
              <div className="flex items-center space-x-3 p-2 bg-green-50 rounded">
                <ChartBarIcon className="h-4 w-4 text-green-600" />
                <span className="text-sm">Recovery began: Day {Math.floor(scenario.duration * 0.6)}</span>
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div className="flex items-center space-x-3">
          <Button variant="outline" onClick={onBack} size="sm">
            <ArrowLeftIcon className="h-4 w-4" />
          </Button>
          <div>
            <h2 className="text-xl font-bold text-gray-900">Detailed Stress Test Report</h2>
            <p className="text-sm text-gray-600">
              {scenario.name} • {result.executionTime.toLocaleDateString()}
            </p>
          </div>
        </div>
        
        <div className="flex space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => onExport('csv')}
            className="flex items-center space-x-2"
          >
            <DocumentArrowDownIcon className="h-4 w-4" />
            <span>CSV</span>
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => onExport('pdf')}
            className="flex items-center space-x-2"
          >
            <DocumentArrowDownIcon className="h-4 w-4" />
            <span>PDF</span>
          </Button>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-8">
          {tabs.map(tab => (
            <button
              key={tab.key}
              onClick={() => setSelectedTab(tab.key)}
              className={`py-2 px-1 border-b-2 font-medium text-sm transition-colors ${
                selectedTab === tab.key
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="min-h-96">
        {selectedTab === 'overview' && renderOverview()}
        {selectedTab === 'assets' && renderAssetImpact()}
        {selectedTab === 'recommendations' && renderRecommendations()}
        {selectedTab === 'timeseries' && renderTimeSeries()}
      </div>
    </div>
  )
}