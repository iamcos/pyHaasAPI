import { useState, useEffect } from 'react'
import { useTradingStore } from '@/stores/tradingStore'
import { useAIStore } from '@/stores/aiStore'
import type { PortfolioSummary } from '@/services/dashboardService'
import type { InsightCard, ProactiveAction } from '@/types/ai'

// Mock portfolio summary hook
export function usePortfolioSummary() {
  const { accounts, bots, positions } = useTradingStore()
  
  const totalValue = accounts.reduce((sum, account) => sum + account.equity, 0)
  const unrealizedPnL = positions.reduce((sum, position) => sum + position.unrealizedPnl, 0)
  const activeBots = bots.filter(bot => bot.status === 'active').length
  const totalPositions = positions.length

  return {
    totalValue,
    unrealizedPnL,
    activeBots,
    totalPositions
  }
}

// Mock active insights hook
export function useActiveInsights(): InsightCard[] {
  const { insights } = useAIStore()
  return insights.filter(insight => 
    insight.type === 'opportunity' || 
    insight.type === 'risk' || 
    insight.type === 'performance'
  )
}

// Mock pending actions hook
export function usePendingActions(): ProactiveAction[] {
  const { insights } = useAIStore()
  return insights.flatMap(insight => insight.actions || [])
}