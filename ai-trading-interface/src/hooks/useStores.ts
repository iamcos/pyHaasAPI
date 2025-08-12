import { useAppStore, useTradingStore, useWorkflowStore, useAIStore } from '@/stores'

// Custom hooks for common store combinations and computed values

export function useStores() {
  return {
    appStore: useAppStore(),
    tradingStore: useTradingStore(),
    workflowStore: useWorkflowStore(),
    aiStore: useAIStore()
  }
}

export function useCurrentStrategy() {
  const { strategies, selectedStrategy } = useTradingStore()
  return strategies.find(s => s.id === selectedStrategy) || null
}

export function useCurrentLab() {
  const { labs, selectedLab } = useTradingStore()
  return labs.find(l => l.id === selectedLab) || null
}

export function useCurrentBot() {
  const { bots, selectedBot } = useTradingStore()
  return bots.find(b => b.id === selectedBot) || null
}

export function useActiveWorkflow() {
  const { executions, activeExecution } = useWorkflowStore()
  return executions.find(e => e.id === activeExecution) || null
}

export function usePortfolioSummary() {
  const { accounts, positions, bots } = useTradingStore()
  
  const totalBalance = accounts.reduce((sum, account) => sum + account.balance, 0)
  const totalEquity = accounts.reduce((sum, account) => sum + account.equity, 0)
  const activeBots = bots.filter(bot => bot.status === 'active').length
  const totalPositions = positions.length
  
  const unrealizedPnL = positions.reduce((sum, position) => sum + position.unrealizedPnl, 0)
  
  return {
    totalBalance,
    totalEquity,
    activeBots,
    totalPositions,
    unrealizedPnL,
    totalValue: totalEquity + unrealizedPnL,
  }
}

export function useActiveInsights() {
  const { insightCards } = useAIStore()
  return insightCards.filter(card => !card.dismissed)
}

export function usePendingActions() {
  const { proactiveActions } = useAIStore()
  return proactiveActions.filter(action => !action.dismissed)
}

export function useWorkflowProgress() {
  const { getExecutionProgress, activeExecution } = useWorkflowStore()
  
  if (!activeExecution) return null
  
  return getExecutionProgress(activeExecution)
}

export function usePersonaSettings() {
  const { currentPersona } = useAIStore()
  const { updateUIContext } = useAppStore()
  
  const applyPersonaToUI = () => {
    updateUIContext({
      riskTolerance: {
        level: currentPersona.type === 'balanced' ? 'moderate' : 
               currentPersona.type === 'custom' ? 'moderate' : 
               currentPersona.type,
        maxDrawdown: currentPersona.preferences.riskLimits.maxDrawdown,
        maxPositionSize: currentPersona.preferences.riskLimits.maxPositionSize,
        diversificationRequirement: 1 - currentPersona.preferences.riskLimits.maxCorrelation,
        stopLossRequirement: currentPersona.type !== 'aggressive',
      }
    })
  }
  
  return {
    currentPersona,
    applyPersonaToUI,
  }
}

export function useRealTimeData() {
  const { markets, positions } = useTradingStore()
  const { bots } = useTradingStore()
  
  // This would typically connect to WebSocket feeds
  const isConnected = true // Mock connection status
  const lastUpdate = new Date()
  
  return {
    markets,
    positions,
    bots,
    isConnected,
    lastUpdate,
  }
}

export function useErrorHandling() {
  const tradingErrors = useTradingStore(state => state.errors)
  const workflowErrors = useWorkflowStore(state => state.errors)
  
  const clearAllErrors = () => {
    useTradingStore.getState().clearErrors()
    useWorkflowStore.getState().clearErrors()
  }
  
  const hasErrors = Object.values(tradingErrors).some(error => error !== null) ||
                   Object.values(workflowErrors).some(error => error !== null)
  
  const allErrors = [
    ...Object.entries(tradingErrors).filter(([_, error]) => error !== null),
    ...Object.entries(workflowErrors).filter(([_, error]) => error !== null),
  ]
  
  return {
    hasErrors,
    allErrors,
    clearAllErrors,
    tradingErrors,
    workflowErrors,
  }
}

export function useLoadingStates() {
  const tradingLoading = useTradingStore(state => state.loading)
  const workflowLoading = useWorkflowStore(state => state.loading)
  const aiProcessing = useAIStore(state => state.isProcessing)
  
  const isAnyLoading = Object.values(tradingLoading).some(loading => loading) ||
                      Object.values(workflowLoading).some(loading => loading) ||
                      aiProcessing
  
  return {
    isAnyLoading,
    tradingLoading,
    workflowLoading,
    aiProcessing,
  }
}