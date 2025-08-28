// Store exports
export { useAppStore } from './appStore'
export { useTradingStore } from './tradingStore'
export { useWorkflowStore } from './workflowStore'
export { useAIStore } from './aiStore'
export { useStrategyStore } from './strategyStore'

// Re-export store types for convenience
export type { 
  TradingStrategy, 
  Lab, 
  Bot, 
  Account, 
  Market,
  WorkflowExecution,
  WorkflowTemplate,
  Persona,
  InsightCard,
  ProactiveAction,
  HaasScriptStrategy,
  HaasScriptValidationError,
  StrategyTemplate,
} from '@/types'