import React from 'react'
import { useAppStore } from '@/stores/appStore'
import { Dashboard } from './views/Dashboard'
import { MarketIntelligence } from './views/MarketIntelligence'
import { StrategyDevelopmentStudio } from './strategy/StrategyDevelopmentStudio'

export function MainContent() {
  const { uiContext } = useAppStore()

  const renderView = () => {
    switch (uiContext.currentView) {
      case 'dashboard':
        return <Dashboard />
      case 'strategy_studio':
        return <StrategyDevelopmentStudio />
      case 'analytics':
        return <div className="p-6">Analytics - Coming Soon</div>
      case 'market_intelligence':
      case 'market-intelligence':
        return <MarketIntelligence />
      case 'risk_management':
        return <div className="p-6">Risk Management - Coming Soon</div>
      case 'workflows':
        return <div className="p-6">Workflows - Coming Soon</div>
      case 'settings':
        return <div className="p-6">Settings - Coming Soon</div>
      default:
        return <Dashboard />
    }
  }

  return (
    <main className="flex-1 overflow-y-auto lg:pl-64">
      <div className="h-full">
        {renderView()}
      </div>
    </main>
  )
}