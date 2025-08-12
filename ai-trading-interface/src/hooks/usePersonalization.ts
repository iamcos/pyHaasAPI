import { useState, useEffect, useCallback } from 'react'
import { useAIStore } from '@/stores/aiStore'
import { 
  personalizationService,
  type BehaviorPattern,
  type AdaptationSuggestion,
  type PersonalizationMetrics,
  type LearningContext
} from '@/services/personalizationService'
import type { UserAction, PerformanceMetric, UserFeedback } from '@/services/personaService'

interface UsePersonalizationOptions {
  userId: string
  autoLoadData?: boolean
  trackingEnabled?: boolean
}

interface PersonalizationState {
  patterns: BehaviorPattern[]
  suggestions: AdaptationSuggestion[]
  metrics: PersonalizationMetrics | null
  trends: any[]
  isLoading: boolean
  error: string | null
}

export const usePersonalization = ({
  userId,
  autoLoadData = true,
  trackingEnabled = true
}: UsePersonalizationOptions) => {
  const { currentPersona } = useAIStore()
  const [state, setState] = useState<PersonalizationState>({
    patterns: [],
    suggestions: [],
    metrics: null,
    trends: [],
    isLoading: false,
    error: null
  })

  // Load personalization data
  const loadData = useCallback(async () => {
    if (!userId) return

    setState(prev => ({ ...prev, isLoading: true, error: null }))

    try {
      await personalizationService.loadUserData(userId)
      const insights = personalizationService.getLearningInsights(userId)
      
      setState(prev => ({
        ...prev,
        patterns: insights.patterns,
        suggestions: insights.suggestions,
        metrics: insights.metrics,
        trends: insights.trends,
        isLoading: false
      }))
    } catch (error) {
      setState(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : 'Failed to load personalization data',
        isLoading: false
      }))
    }
  }, [userId])

  // Track user action
  const trackAction = useCallback((
    action: Omit<UserAction, 'id' | 'timestamp'>,
    context?: Partial<LearningContext>
  ) => {
    if (!trackingEnabled || !userId) return

    const defaultContext: LearningContext = {
      userId,
      sessionId: `session-${Date.now()}`,
      timestamp: new Date(),
      marketConditions: {
        volatility: 0.5,
        trend: 'neutral',
        volume: 1.0
      },
      portfolioState: {
        totalValue: 10000,
        riskExposure: 0.1,
        activeStrategies: 1
      },
      ...context
    }

    personalizationService.trackUserAction(userId, action, defaultContext)
    
    // Reload data after tracking to get updated insights
    setTimeout(() => loadData(), 100)
  }, [userId, trackingEnabled, loadData])

  // Track performance metric
  const trackPerformance = useCallback((
    metric: Omit<PerformanceMetric, 'id' | 'timestamp'>
  ) => {
    if (!trackingEnabled || !userId) return

    personalizationService.trackPerformance(userId, metric)
    setTimeout(() => loadData(), 100)
  }, [userId, trackingEnabled, loadData])

  // Track user feedback
  const trackFeedback = useCallback((
    feedback: Omit<UserFeedback, 'id' | 'timestamp'>
  ) => {
    if (!trackingEnabled || !userId) return

    personalizationService.trackFeedback(userId, feedback)
    setTimeout(() => loadData(), 100)
  }, [userId, trackingEnabled, loadData])

  // Generate new adaptation suggestions
  const generateSuggestions = useCallback(async () => {
    if (!userId || !currentPersona) return []

    try {
      const suggestions = personalizationService.generateAdaptationSuggestions(userId, currentPersona)
      setState(prev => ({ ...prev, suggestions }))
      return suggestions
    } catch (error) {
      console.error('Failed to generate suggestions:', error)
      return []
    }
  }, [userId, currentPersona])

  // Apply adaptation suggestion
  const applySuggestion = useCallback(async (suggestion: AdaptationSuggestion) => {
    if (!currentPersona) return null

    try {
      const adaptedPersona = personalizationService.adaptPersona(currentPersona, suggestion)
      
      // Track that user accepted the suggestion
      trackAction({
        type: 'accept_suggestion',
        context: `adaptation_${suggestion.type}`,
        personaRecommendation: suggestion.description,
        userChoice: 'accepted',
        outcome: 'positive'
      })

      return adaptedPersona
    } catch (error) {
      console.error('Failed to apply suggestion:', error)
      return null
    }
  }, [currentPersona, trackAction])

  // Reject adaptation suggestion
  const rejectSuggestion = useCallback(async (suggestion: AdaptationSuggestion) => {
    trackAction({
      type: 'reject_suggestion',
      context: `adaptation_${suggestion.type}`,
      personaRecommendation: suggestion.description,
      userChoice: 'rejected',
      outcome: 'neutral'
    })
  }, [trackAction])

  // Analyze current behavior patterns
  const analyzePatterns = useCallback(() => {
    if (!userId) return []

    const patterns = personalizationService.analyzeUserBehavior(userId)
    setState(prev => ({ ...prev, patterns }))
    return patterns
  }, [userId])

  // Get personalization metrics
  const getMetrics = useCallback(() => {
    if (!userId) return null

    const metrics = personalizationService.calculatePersonalizationMetrics(userId)
    setState(prev => ({ ...prev, metrics }))
    return metrics
  }, [userId])

  // Convenience methods for common tracking scenarios
  const trackStrategyInteraction = useCallback((
    action: 'create' | 'modify' | 'delete' | 'backtest',
    strategyName: string,
    parameters?: any
  ) => {
    trackAction({
      type: action === 'create' ? 'accept_suggestion' : 'modify_parameters',
      context: `strategy_${action}`,
      personaRecommendation: `${action} strategy: ${strategyName}`,
      userChoice: JSON.stringify(parameters || {}),
      outcome: 'positive'
    })
  }, [trackAction])

  const trackRiskDecision = useCallback((
    decision: 'increase' | 'decrease' | 'maintain',
    currentRisk: number,
    newRisk: number
  ) => {
    trackAction({
      type: 'modify_parameters',
      context: 'risk_management',
      personaRecommendation: `Current risk: ${currentRisk}`,
      userChoice: `${decision} risk to ${newRisk}`,
      outcome: decision === 'decrease' ? 'positive' : 'neutral'
    })
  }, [trackAction])

  const trackOptimizationChoice = useCallback((
    focus: 'return' | 'risk' | 'consistency',
    parameters: any
  ) => {
    trackAction({
      type: 'accept_suggestion',
      context: 'optimization_focus',
      personaRecommendation: 'Optimize strategy parameters',
      userChoice: `Focus on ${focus}: ${JSON.stringify(parameters)}`,
      outcome: 'positive'
    })
  }, [trackAction])

  const trackMarketAnalysisInteraction = useCallback((
    action: 'view' | 'filter' | 'export',
    markets: string[],
    filters?: any
  ) => {
    trackAction({
      type: 'accept_suggestion',
      context: 'market_analysis',
      personaRecommendation: `Analyze markets: ${markets.join(', ')}`,
      userChoice: `${action} with filters: ${JSON.stringify(filters || {})}`,
      outcome: 'positive'
    })
  }, [trackAction])

  // Load data on mount if enabled
  useEffect(() => {
    if (autoLoadData && userId) {
      loadData()
    }
  }, [autoLoadData, userId, loadData])

  // Auto-generate suggestions when persona changes
  useEffect(() => {
    if (currentPersona && userId && state.patterns.length > 0) {
      generateSuggestions()
    }
  }, [currentPersona, userId, state.patterns.length, generateSuggestions])

  return {
    // State
    patterns: state.patterns,
    suggestions: state.suggestions,
    metrics: state.metrics,
    trends: state.trends,
    isLoading: state.isLoading,
    error: state.error,

    // Actions
    loadData,
    trackAction,
    trackPerformance,
    trackFeedback,
    generateSuggestions,
    applySuggestion,
    rejectSuggestion,
    analyzePatterns,
    getMetrics,

    // Convenience methods
    trackStrategyInteraction,
    trackRiskDecision,
    trackOptimizationChoice,
    trackMarketAnalysisInteraction
  }
}

// Hook for tracking specific interaction types
export const usePersonalizationTracking = (userId: string) => {
  const { trackAction } = usePersonalization({ userId, autoLoadData: false })

  return {
    // Strategy interactions
    onStrategyCreate: (name: string, params: any) => 
      trackAction({
        type: 'accept_suggestion',
        context: 'strategy_creation',
        personaRecommendation: 'Create new strategy',
        userChoice: `Created ${name} with params: ${JSON.stringify(params)}`,
        outcome: 'positive'
      }),

    onStrategyModify: (name: string, oldParams: any, newParams: any) =>
      trackAction({
        type: 'modify_parameters',
        context: 'strategy_modification',
        personaRecommendation: `Modify ${name}`,
        userChoice: `Changed from ${JSON.stringify(oldParams)} to ${JSON.stringify(newParams)}`,
        outcome: 'positive'
      }),

    // Risk management interactions
    onRiskAdjustment: (oldRisk: number, newRisk: number, reason: string) =>
      trackAction({
        type: 'modify_parameters',
        context: 'risk_adjustment',
        personaRecommendation: `Current risk: ${oldRisk}`,
        userChoice: `Adjusted to ${newRisk} because: ${reason}`,
        outcome: newRisk < oldRisk ? 'positive' : 'neutral'
      }),

    // UI interactions
    onPersonaSwitch: (fromPersona: string, toPersona: string) =>
      trackAction({
        type: 'override_decision',
        context: 'persona_selection',
        personaRecommendation: `Continue with ${fromPersona}`,
        userChoice: `Switched to ${toPersona}`,
        outcome: 'neutral'
      }),

    onSuggestionDismiss: (suggestionType: string, reason: string) =>
      trackAction({
        type: 'reject_suggestion',
        context: `suggestion_${suggestionType}`,
        personaRecommendation: 'Apply suggested changes',
        userChoice: `Dismissed: ${reason}`,
        outcome: 'negative'
      })
  }
}