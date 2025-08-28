import React, { useState, useEffect } from 'react'
import { generativeUIEngine } from '@/services/generativeUIEngine'
import { insightCardSystem } from '@/services/insightCardSystem'
import { interactiveVisualizationEngine } from '@/services/interactiveVisualizationEngine'
import type { UIContext, InsightCard } from '@/types'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'

interface GenerativeUIDemoProps {
  context: UIContext
}

export const GenerativeUIDemo: React.FC<GenerativeUIDemoProps> = ({ context }) => {
  const [generatedComponent, setGeneratedComponent] = useState<React.ComponentType<any> | null>(null)
  const [insightCards, setInsightCards] = useState<InsightCard[]>([])
  const [chartInstance, setChartInstance] = useState<any>(null)
  const [description, setDescription] = useState('')
  const [isGenerating, setIsGenerating] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Sample descriptions for testing
  const sampleDescriptions = [
    "Show me a price chart for BTC/USDT with 1h timeframe",
    "Create a performance card showing my portfolio metrics",
    "Display a table of my active trading strategies",
    "Show a risk indicator for my current portfolio",
    "Create a market dashboard with top 9 cryptocurrencies"
  ]

  // Sample data for demonstrations
  const sampleData = {
    priceData: Array.from({ length: 50 }, (_, i) => ({
      timestamp: Date.now() - (50 - i) * 3600000,
      open: 45000 + Math.random() * 5000,
      high: 46000 + Math.random() * 5000,
      low: 44000 + Math.random() * 5000,
      close: 45000 + Math.random() * 5000,
      volume: Math.random() * 1000000
    })),
    performanceData: {
      pnl: 1250.75,
      return: 0.125,
      drawdown: -0.08,
      winRate: 0.68,
      sharpe: 1.45
    },
    strategies: [
      { name: 'Momentum Scalper', performance: 0.15, risk: 0.3, status: 'active' },
      { name: 'Mean Reversion', performance: 0.08, risk: 0.2, status: 'paused' },
      { name: 'Arbitrage Bot', performance: 0.22, risk: 0.1, status: 'active' },
      { name: 'Grid Trading', performance: 0.12, risk: 0.25, status: 'active' }
    ],
    riskMetrics: {
      riskScore: 0.35,
      maxDrawdown: 0.15,
      var95: 0.08,
      correlation: 0.45
    },
    markets: [
      { symbol: 'BTC/USDT', price: 45234.56, change: 0.025 },
      { symbol: 'ETH/USDT', price: 2834.12, change: -0.012 },
      { symbol: 'ADA/USDT', price: 0.456, change: 0.034 },
      { symbol: 'SOL/USDT', price: 98.76, change: 0.018 },
      { symbol: 'DOT/USDT', price: 6.78, change: -0.008 },
      { symbol: 'LINK/USDT', price: 14.23, change: 0.045 },
      { symbol: 'AVAX/USDT', price: 23.45, change: 0.012 },
      { symbol: 'MATIC/USDT', price: 0.89, change: -0.025 },
      { symbol: 'UNI/USDT', price: 7.65, change: 0.031 }
    ]
  }

  // Generate component from description
  const handleGenerateComponent = async () => {
    if (!description.trim()) {
      setError('Please enter a description')
      return
    }

    setIsGenerating(true)
    setError(null)

    try {
      // Determine appropriate sample data based on description
      let componentData = null
      const lowerDesc = description.toLowerCase()
      
      if (lowerDesc.includes('chart') || lowerDesc.includes('price')) {
        componentData = sampleData.priceData
      } else if (lowerDesc.includes('performance')) {
        componentData = sampleData.performanceData
      } else if (lowerDesc.includes('strategies') || lowerDesc.includes('table')) {
        componentData = sampleData.strategies
      } else if (lowerDesc.includes('risk')) {
        componentData = { value: 35, maxValue: 100, ...sampleData.riskMetrics }
      } else if (lowerDesc.includes('dashboard') || lowerDesc.includes('market')) {
        componentData = { markets: sampleData.markets }
      }

      const component = await generativeUIEngine.generateComponent(
        description,
        context,
        componentData
      )

      setGeneratedComponent(() => component)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate component')
      console.error('Component generation error:', err)
    } finally {
      setIsGenerating(false)
    }
  }

  // Generate insight cards
  const handleGenerateInsights = async () => {
    setIsGenerating(true)
    setError(null)

    try {
      const insightContext = {
        userContext: context,
        marketData: sampleData.markets,
        portfolioData: {
          positions: sampleData.strategies,
          totalValue: 125000,
          peakValue: 135000
        },
        performanceData: {
          returns: [0.02, 0.015, -0.008, 0.025, 0.012],
          trades: Array.from({ length: 20 }, (_, i) => ({
            id: i,
            symbol: 'BTC/USDT',
            side: Math.random() > 0.5 ? 'buy' : 'sell',
            size: Math.random() * 10,
            pnl: (Math.random() - 0.5) * 1000
          }))
        },
        riskData: sampleData.riskMetrics,
        timeframe: '1d',
        symbols: ['BTC/USDT', 'ETH/USDT', 'ADA/USDT']
      }

      const cards = await insightCardSystem.generateInsightCards(insightContext)
      setInsightCards(cards)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate insights')
      console.error('Insight generation error:', err)
    } finally {
      setIsGenerating(false)
    }
  }

  // Create interactive chart
  const handleCreateChart = async () => {
    setIsGenerating(true)
    setError(null)

    try {
      const chartId = 'demo-chart-' + Date.now()
      
      const chart = await interactiveVisualizationEngine.createChart(
        chartId,
        'candlestick',
        sampleData.priceData,
        {
          theme: context.userPreferences.theme === 'auto' ? 'dark' : context.userPreferences.theme,
          zoom: true,
          pan: true,
          crosshair: true,
          indicators: [
            { type: 'sma', period: 20, parameters: {}, visible: true },
            { type: 'rsi', period: 14, parameters: {}, visible: true }
          ]
        },
        context
      )

      setChartInstance(chart)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create chart')
      console.error('Chart creation error:', err)
    } finally {
      setIsGenerating(false)
    }
  }

  // Use sample description
  const handleUseSample = (sample: string) => {
    setDescription(sample)
  }

  // Clear generated content
  const handleClear = () => {
    setGeneratedComponent(null)
    setInsightCards([])
    setChartInstance(null)
    setError(null)
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
          Generative UI Engine Demo
        </h2>
        <p className="text-gray-600 dark:text-gray-300 mb-6">
          Demonstrate dynamic component generation, AI-powered insight cards, and interactive visualizations.
        </p>

        {/* Input Section */}
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Describe the component you want to generate:
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="e.g., Show me a price chart for BTC/USDT with technical indicators"
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
              rows={3}
            />
          </div>

          {/* Sample Descriptions */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Or try these examples:
            </label>
            <div className="flex flex-wrap gap-2">
              {sampleDescriptions.map((sample, index) => (
                <Button
                  key={index}
                  variant="outline"
                  size="sm"
                  onClick={() => handleUseSample(sample)}
                  className="text-xs"
                >
                  {sample.substring(0, 30)}...
                </Button>
              ))}
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-wrap gap-3">
            <Button
              onClick={handleGenerateComponent}
              disabled={isGenerating || !description.trim()}
              className="bg-blue-600 hover:bg-blue-700"
            >
              {isGenerating ? 'Generating...' : 'Generate Component'}
            </Button>
            <Button
              onClick={handleGenerateInsights}
              disabled={isGenerating}
              className="bg-green-600 hover:bg-green-700"
            >
              Generate Insights
            </Button>
            <Button
              onClick={handleCreateChart}
              disabled={isGenerating}
              className="bg-purple-600 hover:bg-purple-700"
            >
              Create Interactive Chart
            </Button>
            <Button
              onClick={handleClear}
              variant="outline"
            >
              Clear All
            </Button>
          </div>

          {/* Error Display */}
          {error && (
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md p-4">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <p className="text-sm text-red-800 dark:text-red-200">{error}</p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Generated Component Display */}
      {generatedComponent && (
        <Card className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Generated Component
          </h3>
          <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
            {React.createElement(generatedComponent)}
          </div>
        </Card>
      )}

      {/* Insight Cards Display */}
      {insightCards.length > 0 && (
        <Card className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            AI-Generated Insight Cards ({insightCards.length})
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {insightCards.map((card) => (
              <InsightCardComponent key={card.id} card={card} />
            ))}
          </div>
        </Card>
      )}

      {/* Interactive Chart Display */}
      {chartInstance && (
        <Card className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Interactive Visualization
          </h3>
          <div className="bg-gray-900 rounded-lg p-4" style={{ height: 400 }}>
            <div className="text-white text-center mt-20">
              <h4 className="text-xl font-semibold mb-2">Interactive Chart Created</h4>
              <p className="text-gray-300">Chart ID: {chartInstance.id}</p>
              <p className="text-gray-300">Type: {chartInstance.config.type}</p>
              <p className="text-gray-300">Data Points: {chartInstance.config.data.length || 0}</p>
              <div className="mt-4 space-x-2">
                <Button
                  size="sm"
                  onClick={() => interactiveVisualizationEngine.updateChart(chartInstance.id, {
                    timestamp: Date.now(),
                    open: 45000 + Math.random() * 5000,
                    high: 46000 + Math.random() * 5000,
                    low: 44000 + Math.random() * 5000,
                    close: 45000 + Math.random() * 5000,
                    volume: Math.random() * 1000000
                  })}
                >
                  Add Data Point
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => interactiveVisualizationEngine.resizeChart(chartInstance.id)}
                >
                  Resize Chart
                </Button>
              </div>
            </div>
          </div>
        </Card>
      )}

      {/* Engine Statistics */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Engine Statistics
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
            <h4 className="font-medium text-blue-900 dark:text-blue-100">Component Templates</h4>
            <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">
              {generativeUIEngine.getAvailableTemplates().length}
            </p>
            <p className="text-sm text-blue-700 dark:text-blue-300">Available templates</p>
          </div>
          <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-4">
            <h4 className="font-medium text-green-900 dark:text-green-100">Insight Templates</h4>
            <p className="text-2xl font-bold text-green-600 dark:text-green-400">
              {insightCardSystem.getAvailableTemplates().length}
            </p>
            <p className="text-sm text-green-700 dark:text-green-300">Insight card types</p>
          </div>
          <div className="bg-purple-50 dark:bg-purple-900/20 rounded-lg p-4">
            <h4 className="font-medium text-purple-900 dark:text-purple-100">Active Charts</h4>
            <p className="text-2xl font-bold text-purple-600 dark:text-purple-400">
              {interactiveVisualizationEngine.getChartStats().activeCharts}
            </p>
            <p className="text-sm text-purple-700 dark:text-purple-300">Chart instances</p>
          </div>
        </div>
      </Card>
    </div>
  )
}

// Insight Card Component
const InsightCardComponent: React.FC<{ card: InsightCard }> = ({ card }) => {
  const getCardIcon = (type: string) => {
    switch (type) {
      case 'opportunity':
        return '🚀'
      case 'risk':
        return '⚠️'
      case 'performance':
        return '📈'
      case 'market_analysis':
        return '🔍'
      default:
        return '💡'
    }
  }

  const getCardColor = (type: string) => {
    switch (type) {
      case 'opportunity':
        return 'border-green-200 dark:border-green-800 bg-green-50 dark:bg-green-900/20'
      case 'risk':
        return 'border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/20'
      case 'performance':
        return 'border-blue-200 dark:border-blue-800 bg-blue-50 dark:bg-blue-900/20'
      case 'market_analysis':
        return 'border-purple-200 dark:border-purple-800 bg-purple-50 dark:bg-purple-900/20'
      default:
        return 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800'
    }
  }

  return (
    <div className={`border rounded-lg p-4 ${getCardColor(card.type)}`}>
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center space-x-2">
          <span className="text-lg">{getCardIcon(card.type)}</span>
          <h4 className="font-semibold text-gray-900 dark:text-white">{card.title}</h4>
        </div>
        <span className="text-xs bg-gray-200 dark:bg-gray-700 px-2 py-1 rounded">
          {Math.round(card.confidence * 100)}%
        </span>
      </div>
      
      <p className="text-sm text-gray-600 dark:text-gray-300 mb-3 line-clamp-3">
        {card.content}
      </p>
      
      {card.actions.length > 0 && (
        <div className="space-y-2">
          {card.actions.slice(0, 2).map((action) => (
            <Button
              key={action.id}
              size="sm"
              variant="outline"
              onClick={action.action}
              className="w-full text-xs"
            >
              {action.title}
            </Button>
          ))}
        </div>
      )}
      
      <div className="mt-3 text-xs text-gray-500 dark:text-gray-400">
        {new Date(card.timestamp).toLocaleTimeString()}
      </div>
    </div>
  )
}