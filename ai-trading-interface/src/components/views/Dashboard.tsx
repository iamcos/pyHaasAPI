import { useState } from 'react'
import { SparklesIcon } from '@heroicons/react/24/outline'
import { Button } from '@/components/ui'
import { GenerativeUIDemo } from '@/components/generative/GenerativeUIDemo'
import { UnifiedDashboard } from '@/components/dashboard'
import { useStores } from '@/hooks/useStores'
import type { UIContext } from '@/types'

export function Dashboard() {
  const [showGenerativeDemo, setShowGenerativeDemo] = useState(false)
  const { appStore } = useStores()

  // Create UI context for the generative demo
  const uiContext: UIContext = {
    currentView: 'dashboard',
    selectedAssets: ['BTC/USDT', 'ETH/USDT'],
    activeStrategies: ['momentum-scalper', 'grid-trading'],
    userPreferences: {
      theme: appStore.theme,
      language: 'en',
      timezone: 'UTC',
      currency: 'USD',
      notifications: {
        enabled: true,
        types: [
          { type: 'trade', enabled: true, priority: 'medium' },
          { type: 'alert', enabled: true, priority: 'high' }
        ],
        frequency: 'immediate',
        channels: [
          { type: 'in_app', enabled: true, settings: {} }
        ]
      },
      dashboard: {
        layout: 'grid',
        widgets: [],
        refreshInterval: 30000,
        autoRefresh: true
      },
      accessibility: {
        highContrast: false,
        largeText: false,
        screenReader: false,
        keyboardNavigation: true,
        voiceCommands: false,
        reducedMotion: false
      }
    },
    marketConditions: [
      { type: 'trending', confidence: 0.8, timeframe: '1h', description: 'BTC showing strong upward trend' },
      { type: 'volatile', confidence: 0.7, timeframe: '1h', description: 'ETH experiencing high volatility' }
    ],
    riskTolerance: {
      level: 'moderate',
      maxDrawdown: 0.15,
      maxPositionSize: 0.1,
      diversificationRequirement: 0.3,
      stopLossRequirement: true
    },
    persona: {
      id: 'balanced-trader',
      name: 'Balanced Trader',
      type: 'balanced',
      description: 'Balanced approach to risk and return',
      riskTolerance: 0.5,
      optimizationStyle: 'balanced',
      decisionSpeed: 'moderate',
      preferences: {
        preferredTimeframes: ['1h', '4h', '1d'],
        riskLimits: {
          maxDrawdown: 0.15,
          maxPositionSize: 0.1,
          maxCorrelation: 0.7
        },
        optimizationFocus: 'risk_adjusted',
        alertFrequency: 'moderate'
      }
    }
  }

  if (showGenerativeDemo) {
    return (
      <div className="p-6 space-y-6">
        <div className="flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Generative UI Engine Demo
          </h1>
          <Button
            onClick={() => setShowGenerativeDemo(false)}
            variant="outline"
          >
            Back to Dashboard
          </Button>
        </div>
        <GenerativeUIDemo context={uiContext} />
      </div>
    )
  }

  return (
    <div className="relative">
      {/* Generative UI Demo Button */}
      <div className="absolute top-6 right-6 z-10">
        <Button
          onClick={() => setShowGenerativeDemo(true)}
          className="bg-primary-600 hover:bg-primary-700 text-white"
          size="sm"
        >
          <SparklesIcon className="h-4 w-4 mr-2" />
          Try Generative UI
        </Button>
      </div>

      {/* Unified Dashboard */}
      <UnifiedDashboard />
    </div>
  )
}