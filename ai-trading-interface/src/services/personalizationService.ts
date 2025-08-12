import type { 
  UserAction,
  PerformanceMetric,
  UserFeedback,
  PersonaAdaptationData 
} from '@/services/personaService'
import type { Persona, PersonaPreferences } from '@/types'

export interface BehaviorPattern {
  id: string
  type: 'risk_preference' | 'timeframe_preference' | 'decision_speed' | 'optimization_focus'
  pattern: string
  confidence: number
  frequency: number
  lastObserved: Date
  impact: 'low' | 'medium' | 'high'
}

export interface AdaptationSuggestion {
  id: string
  type: 'persona_adjustment' | 'new_persona' | 'parameter_change'
  description: string
  confidence: number
  expectedImprovement: number
  changes: Partial<Persona>
  reasoning: string[]
}

export interface PersonalizationMetrics {
  adaptationAccuracy: number
  userSatisfaction: number
  performanceImprovement: number
  engagementLevel: number
  lastUpdated: Date
}

export interface LearningContext {
  userId: string
  sessionId: string
  timestamp: Date
  marketConditions: {
    volatility: number
    trend: 'bullish' | 'bearish' | 'neutral'
    volume: number
  }
  portfolioState: {
    totalValue: number
    riskExposure: number
    activeStrategies: number
  }
}

export class PersonalizationService {
  private static instance: PersonalizationService
  private behaviorHistory: Map<string, UserAction[]> = new Map()
  private performanceHistory: Map<string, PerformanceMetric[]> = new Map()
  private feedbackHistory: Map<string, UserFeedback[]> = new Map()
  private behaviorPatterns: Map<string, BehaviorPattern[]> = new Map()
  private adaptationHistory: Map<string, AdaptationSuggestion[]> = new Map()

  public static getInstance(): PersonalizationService {
    if (!PersonalizationService.instance) {
      PersonalizationService.instance = new PersonalizationService()
    }
    return PersonalizationService.instance
  }

  /**
   * Track user action for learning
   */
  trackUserAction(
    userId: string,
    action: Omit<UserAction, 'id' | 'timestamp'>,
    context: LearningContext
  ): void {
    const userAction: UserAction = {
      id: `action-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date(),
      ...action
    }

    // Store action
    const userActions = this.behaviorHistory.get(userId) || []
    userActions.push(userAction)
    
    // Keep only last 1000 actions per user
    if (userActions.length > 1000) {
      userActions.splice(0, userActions.length - 1000)
    }
    
    this.behaviorHistory.set(userId, userActions)

    // Analyze patterns in real-time
    this.analyzeUserBehavior(userId)
    
    // Store in IndexedDB for persistence
    this.persistUserData(userId)
  }

  /**
   * Track performance metrics
   */
  trackPerformance(
    userId: string,
    metric: Omit<PerformanceMetric, 'id' | 'timestamp'>
  ): void {
    const performanceMetric: PerformanceMetric = {
      id: `perf-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date(),
      ...metric
    }

    const userMetrics = this.performanceHistory.get(userId) || []
    userMetrics.push(performanceMetric)
    
    // Keep only last 500 metrics per user
    if (userMetrics.length > 500) {
      userMetrics.splice(0, userMetrics.length - 500)
    }
    
    this.performanceHistory.set(userId, userMetrics)
    this.persistUserData(userId)
  }

  /**
   * Track user feedback
   */
  trackFeedback(
    userId: string,
    feedback: Omit<UserFeedback, 'id' | 'timestamp'>
  ): void {
    const userFeedback: UserFeedback = {
      id: `feedback-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date(),
      ...feedback
    }

    const userFeedbacks = this.feedbackHistory.get(userId) || []
    userFeedbacks.push(userFeedback)
    
    // Keep only last 200 feedback entries per user
    if (userFeedbacks.length > 200) {
      userFeedbacks.splice(0, userFeedbacks.length - 200)
    }
    
    this.feedbackHistory.set(userId, userFeedbacks)
    this.persistUserData(userId)
  }

  /**
   * Analyze user behavior patterns
   */
  analyzeUserBehavior(userId: string): BehaviorPattern[] {
    const actions = this.behaviorHistory.get(userId) || []
    const patterns: BehaviorPattern[] = []

    if (actions.length < 10) {
      return patterns // Need minimum data for analysis
    }

    // Analyze risk preference patterns
    const riskPattern = this.analyzeRiskPreference(actions)
    if (riskPattern) patterns.push(riskPattern)

    // Analyze timeframe preferences
    const timeframePattern = this.analyzeTimeframePreference(actions)
    if (timeframePattern) patterns.push(timeframePattern)

    // Analyze decision speed patterns
    const decisionSpeedPattern = this.analyzeDecisionSpeed(actions)
    if (decisionSpeedPattern) patterns.push(decisionSpeedPattern)

    // Analyze optimization focus patterns
    const optimizationPattern = this.analyzeOptimizationFocus(actions)
    if (optimizationPattern) patterns.push(optimizationPattern)

    this.behaviorPatterns.set(userId, patterns)
    return patterns
  }

  /**
   * Generate persona adaptation suggestions
   */
  generateAdaptationSuggestions(
    userId: string,
    currentPersona: Persona
  ): AdaptationSuggestion[] {
    const patterns = this.behaviorPatterns.get(userId) || []
    const performance = this.performanceHistory.get(userId) || []
    const feedback = this.feedbackHistory.get(userId) || []
    
    if (patterns.length === 0) {
      return []
    }

    const suggestions: AdaptationSuggestion[] = []

    // Analyze each pattern for adaptation opportunities
    for (const pattern of patterns) {
      const suggestion = this.createAdaptationSuggestion(
        pattern,
        currentPersona,
        performance,
        feedback
      )
      
      if (suggestion && suggestion.confidence > 0.6) {
        suggestions.push(suggestion)
      }
    }

    // Sort by confidence and expected improvement
    suggestions.sort((a, b) => 
      (b.confidence * b.expectedImprovement) - (a.confidence * a.expectedImprovement)
    )

    this.adaptationHistory.set(userId, suggestions)
    return suggestions.slice(0, 5) // Return top 5 suggestions
  }

  /**
   * Apply adaptation to persona
   */
  adaptPersona(
    currentPersona: Persona,
    adaptationSuggestion: AdaptationSuggestion
  ): Persona {
    const adaptedPersona: Persona = {
      ...currentPersona,
      ...adaptationSuggestion.changes,
      id: `adapted-${currentPersona.id}-${Date.now()}`,
      name: `${currentPersona.name} (Adapted)`,
      description: `${currentPersona.description} - Adapted based on user behavior`
    }

    return adaptedPersona
  }

  /**
   * Calculate personalization metrics
   */
  calculatePersonalizationMetrics(userId: string): PersonalizationMetrics {
    const actions = this.behaviorHistory.get(userId) || []
    const performance = this.performanceHistory.get(userId) || []
    const feedback = this.feedbackHistory.get(userId) || []
    const adaptations = this.adaptationHistory.get(userId) || []

    // Calculate adaptation accuracy (how often user accepts suggestions)
    const acceptedAdaptations = actions.filter(a => 
      a.type === 'accept_suggestion' && a.outcome === 'positive'
    ).length
    const totalSuggestions = adaptations.length
    const adaptationAccuracy = totalSuggestions > 0 ? acceptedAdaptations / totalSuggestions : 0

    // Calculate user satisfaction from feedback
    const recentFeedback = feedback.filter(f => 
      Date.now() - f.timestamp.getTime() < 30 * 24 * 60 * 60 * 1000 // Last 30 days
    )
    const userSatisfaction = recentFeedback.length > 0 
      ? recentFeedback.reduce((sum, f) => sum + f.rating, 0) / (recentFeedback.length * 5)
      : 0

    // Calculate performance improvement
    const recentPerformance = performance.filter(p => 
      Date.now() - p.timestamp.getTime() < 30 * 24 * 60 * 60 * 1000
    )
    const performanceImprovement = this.calculatePerformanceImprovement(recentPerformance)

    // Calculate engagement level
    const recentActions = actions.filter(a => 
      Date.now() - a.timestamp.getTime() < 7 * 24 * 60 * 60 * 1000 // Last 7 days
    )
    const engagementLevel = Math.min(recentActions.length / 50, 1) // Normalize to 0-1

    return {
      adaptationAccuracy,
      userSatisfaction,
      performanceImprovement,
      engagementLevel,
      lastUpdated: new Date()
    }
  }

  /**
   * Get learning insights for user
   */
  getLearningInsights(userId: string): {
    patterns: BehaviorPattern[]
    suggestions: AdaptationSuggestion[]
    metrics: PersonalizationMetrics
    trends: any[]
  } {
    const patterns = this.behaviorPatterns.get(userId) || []
    const suggestions = this.adaptationHistory.get(userId) || []
    const metrics = this.calculatePersonalizationMetrics(userId)
    const trends = this.calculateTrends(userId)

    return {
      patterns,
      suggestions,
      metrics,
      trends
    }
  }

  // Private helper methods

  private analyzeRiskPreference(actions: UserAction[]): BehaviorPattern | null {
    const riskActions = actions.filter(a => 
      a.context.includes('risk') || a.type === 'modify_parameters'
    )

    if (riskActions.length < 5) return null

    // Analyze if user consistently chooses higher or lower risk
    let riskTrend = 0
    for (const action of riskActions) {
      if (action.userChoice.includes('increase') || action.userChoice.includes('higher')) {
        riskTrend += 1
      } else if (action.userChoice.includes('decrease') || action.userChoice.includes('lower')) {
        riskTrend -= 1
      }
    }

    const confidence = Math.abs(riskTrend) / riskActions.length
    if (confidence < 0.3) return null

    return {
      id: `risk-pattern-${Date.now()}`,
      type: 'risk_preference',
      pattern: riskTrend > 0 ? 'prefers_higher_risk' : 'prefers_lower_risk',
      confidence,
      frequency: riskActions.length,
      lastObserved: new Date(),
      impact: confidence > 0.7 ? 'high' : confidence > 0.4 ? 'medium' : 'low'
    }
  }

  private analyzeTimeframePreference(actions: UserAction[]): BehaviorPattern | null {
    const timeframeActions = actions.filter(a => 
      a.context.includes('timeframe') || a.userChoice.includes('m') || a.userChoice.includes('h') || a.userChoice.includes('d')
    )

    if (timeframeActions.length < 3) return null

    // Extract timeframes from user choices
    const timeframes = timeframeActions.map(a => {
      const match = a.userChoice.match(/(\d+[mhd])/g)
      return match ? match[0] : null
    }).filter(Boolean)

    if (timeframes.length === 0) return null

    // Find most common timeframe category
    const shortTerm = timeframes.filter(tf => tf?.includes('m') || tf === '1h').length
    const mediumTerm = timeframes.filter(tf => tf?.includes('4h') || tf?.includes('1d')).length
    const longTerm = timeframes.filter(tf => tf?.includes('1w') || tf?.includes('1M')).length

    const total = shortTerm + mediumTerm + longTerm
    const maxCategory = Math.max(shortTerm, mediumTerm, longTerm)
    const confidence = maxCategory / total

    if (confidence < 0.4) return null

    let pattern: string
    if (maxCategory === shortTerm) pattern = 'prefers_short_term'
    else if (maxCategory === mediumTerm) pattern = 'prefers_medium_term'
    else pattern = 'prefers_long_term'

    return {
      id: `timeframe-pattern-${Date.now()}`,
      type: 'timeframe_preference',
      pattern,
      confidence,
      frequency: timeframeActions.length,
      lastObserved: new Date(),
      impact: confidence > 0.7 ? 'high' : confidence > 0.5 ? 'medium' : 'low'
    }
  }

  private analyzeDecisionSpeed(actions: UserAction[]): BehaviorPattern | null {
    // Analyze time between suggestion and user action
    const decisionTimes: number[] = []
    
    for (let i = 1; i < actions.length; i++) {
      const current = actions[i]
      const previous = actions[i - 1]
      
      if (current.type === 'accept_suggestion' || current.type === 'reject_suggestion') {
        const timeDiff = current.timestamp.getTime() - previous.timestamp.getTime()
        decisionTimes.push(timeDiff)
      }
    }

    if (decisionTimes.length < 5) return null

    const avgDecisionTime = decisionTimes.reduce((sum, time) => sum + time, 0) / decisionTimes.length
    const minutes = avgDecisionTime / (1000 * 60)

    let pattern: string
    let confidence: number

    if (minutes < 2) {
      pattern = 'quick_decision_maker'
      confidence = 0.8
    } else if (minutes < 10) {
      pattern = 'moderate_decision_maker'
      confidence = 0.6
    } else {
      pattern = 'deliberate_decision_maker'
      confidence = 0.7
    }

    return {
      id: `decision-speed-pattern-${Date.now()}`,
      type: 'decision_speed',
      pattern,
      confidence,
      frequency: decisionTimes.length,
      lastObserved: new Date(),
      impact: 'medium'
    }
  }

  private analyzeOptimizationFocus(actions: UserAction[]): BehaviorPattern | null {
    const optimizationActions = actions.filter(a => 
      a.context.includes('optimization') || a.context.includes('performance')
    )

    if (optimizationActions.length < 3) return null

    // Analyze what user optimizes for
    let returnFocus = 0
    let riskFocus = 0
    let consistencyFocus = 0

    for (const action of optimizationActions) {
      if (action.userChoice.includes('return') || action.userChoice.includes('profit')) {
        returnFocus += 1
      } else if (action.userChoice.includes('risk') || action.userChoice.includes('drawdown')) {
        riskFocus += 1
      } else if (action.userChoice.includes('consistent') || action.userChoice.includes('stable')) {
        consistencyFocus += 1
      }
    }

    const total = returnFocus + riskFocus + consistencyFocus
    if (total === 0) return null

    const maxFocus = Math.max(returnFocus, riskFocus, consistencyFocus)
    const confidence = maxFocus / total

    if (confidence < 0.4) return null

    let pattern: string
    if (maxFocus === returnFocus) pattern = 'return_focused'
    else if (maxFocus === riskFocus) pattern = 'risk_focused'
    else pattern = 'consistency_focused'

    return {
      id: `optimization-pattern-${Date.now()}`,
      type: 'optimization_focus',
      pattern,
      confidence,
      frequency: optimizationActions.length,
      lastObserved: new Date(),
      impact: confidence > 0.6 ? 'high' : 'medium'
    }
  }

  private createAdaptationSuggestion(
    pattern: BehaviorPattern,
    currentPersona: Persona,
    performance: PerformanceMetric[],
    feedback: UserFeedback[]
  ): AdaptationSuggestion | null {
    const changes: Partial<Persona> = {}
    const reasoning: string[] = []
    let expectedImprovement = 0

    switch (pattern.type) {
      case 'risk_preference':
        if (pattern.pattern === 'prefers_higher_risk' && currentPersona.riskTolerance < 0.8) {
          changes.riskTolerance = Math.min(currentPersona.riskTolerance + 0.2, 1.0)
          changes.preferences = {
            ...currentPersona.preferences,
            riskLimits: {
              ...currentPersona.preferences.riskLimits,
              maxDrawdown: Math.min(currentPersona.preferences.riskLimits.maxDrawdown + 0.05, 0.3),
              maxPositionSize: Math.min(currentPersona.preferences.riskLimits.maxPositionSize + 0.05, 0.25)
            }
          }
          reasoning.push(`User consistently chooses higher risk options (${pattern.frequency} times)`)
          expectedImprovement = 0.15
        } else if (pattern.pattern === 'prefers_lower_risk' && currentPersona.riskTolerance > 0.2) {
          changes.riskTolerance = Math.max(currentPersona.riskTolerance - 0.2, 0.1)
          changes.preferences = {
            ...currentPersona.preferences,
            riskLimits: {
              ...currentPersona.preferences.riskLimits,
              maxDrawdown: Math.max(currentPersona.preferences.riskLimits.maxDrawdown - 0.05, 0.05),
              maxPositionSize: Math.max(currentPersona.preferences.riskLimits.maxPositionSize - 0.05, 0.01)
            }
          }
          reasoning.push(`User consistently chooses lower risk options (${pattern.frequency} times)`)
          expectedImprovement = 0.12
        }
        break

      case 'decision_speed':
        if (pattern.pattern === 'quick_decision_maker' && currentPersona.decisionSpeed !== 'quick') {
          changes.decisionSpeed = 'quick'
          reasoning.push(`User makes decisions quickly (avg < 2 minutes)`)
          expectedImprovement = 0.08
        } else if (pattern.pattern === 'deliberate_decision_maker' && currentPersona.decisionSpeed !== 'deliberate') {
          changes.decisionSpeed = 'deliberate'
          reasoning.push(`User takes time for decisions (avg > 10 minutes)`)
          expectedImprovement = 0.08
        }
        break

      case 'optimization_focus':
        const currentFocus = currentPersona.preferences.optimizationFocus
        if (pattern.pattern === 'return_focused' && currentFocus !== 'return') {
          changes.preferences = {
            ...currentPersona.preferences,
            optimizationFocus: 'return'
          }
          reasoning.push(`User consistently optimizes for returns`)
          expectedImprovement = 0.1
        } else if (pattern.pattern === 'risk_focused' && currentFocus !== 'risk_adjusted') {
          changes.preferences = {
            ...currentPersona.preferences,
            optimizationFocus: 'risk_adjusted'
          }
          reasoning.push(`User consistently focuses on risk management`)
          expectedImprovement = 0.1
        } else if (pattern.pattern === 'consistency_focused' && currentFocus !== 'consistency') {
          changes.preferences = {
            ...currentPersona.preferences,
            optimizationFocus: 'consistency'
          }
          reasoning.push(`User consistently values stable performance`)
          expectedImprovement = 0.1
        }
        break
    }

    if (Object.keys(changes).length === 0) {
      return null
    }

    return {
      id: `adaptation-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      type: 'persona_adjustment',
      description: `Adjust persona based on observed ${pattern.type.replace('_', ' ')} pattern`,
      confidence: pattern.confidence,
      expectedImprovement,
      changes,
      reasoning
    }
  }

  private calculatePerformanceImprovement(metrics: PerformanceMetric[]): number {
    if (metrics.length < 2) return 0

    // Sort by timestamp
    metrics.sort((a, b) => a.timestamp.getTime() - b.timestamp.getTime())
    
    const firstHalf = metrics.slice(0, Math.floor(metrics.length / 2))
    const secondHalf = metrics.slice(Math.floor(metrics.length / 2))

    const firstAvg = firstHalf.reduce((sum, m) => sum + m.value, 0) / firstHalf.length
    const secondAvg = secondHalf.reduce((sum, m) => sum + m.value, 0) / secondHalf.length

    return (secondAvg - firstAvg) / Math.abs(firstAvg)
  }

  private calculateTrends(userId: string): any[] {
    // Calculate various trends from user data
    const actions = this.behaviorHistory.get(userId) || []
    const performance = this.performanceHistory.get(userId) || []
    
    return [
      {
        type: 'activity_trend',
        direction: this.calculateActivityTrend(actions),
        confidence: 0.8
      },
      {
        type: 'performance_trend',
        direction: this.calculatePerformanceTrend(performance),
        confidence: 0.7
      }
    ]
  }

  private calculateActivityTrend(actions: UserAction[]): 'increasing' | 'decreasing' | 'stable' {
    if (actions.length < 10) return 'stable'

    const recentActions = actions.filter(a => 
      Date.now() - a.timestamp.getTime() < 7 * 24 * 60 * 60 * 1000
    ).length

    const olderActions = actions.filter(a => {
      const daysDiff = (Date.now() - a.timestamp.getTime()) / (24 * 60 * 60 * 1000)
      return daysDiff >= 7 && daysDiff < 14
    }).length

    if (recentActions > olderActions * 1.2) return 'increasing'
    if (recentActions < olderActions * 0.8) return 'decreasing'
    return 'stable'
  }

  private calculatePerformanceTrend(metrics: PerformanceMetric[]): 'improving' | 'declining' | 'stable' {
    if (metrics.length < 5) return 'stable'

    const recent = metrics.slice(-5)
    const older = metrics.slice(-10, -5)

    if (older.length === 0) return 'stable'

    const recentAvg = recent.reduce((sum, m) => sum + m.value, 0) / recent.length
    const olderAvg = older.reduce((sum, m) => sum + m.value, 0) / older.length

    const improvement = (recentAvg - olderAvg) / Math.abs(olderAvg)

    if (improvement > 0.1) return 'improving'
    if (improvement < -0.1) return 'declining'
    return 'stable'
  }

  private async persistUserData(userId: string): Promise<void> {
    // In a real implementation, this would save to IndexedDB
    // For now, we'll just store in memory
    try {
      const data = {
        behaviorHistory: this.behaviorHistory.get(userId) || [],
        performanceHistory: this.performanceHistory.get(userId) || [],
        feedbackHistory: this.feedbackHistory.get(userId) || [],
        behaviorPatterns: this.behaviorPatterns.get(userId) || [],
        adaptationHistory: this.adaptationHistory.get(userId) || [],
        lastUpdated: new Date()
      }

      // Store in localStorage as fallback
      localStorage.setItem(`personalization-${userId}`, JSON.stringify(data))
    } catch (error) {
      console.error('Failed to persist user data:', error)
    }
  }

  /**
   * Load user data from storage
   */
  async loadUserData(userId: string): Promise<void> {
    try {
      const stored = localStorage.getItem(`personalization-${userId}`)
      if (stored) {
        const data = JSON.parse(stored)
        
        // Convert date strings back to Date objects
        const convertDates = (items: any[]) => items.map(item => ({
          ...item,
          timestamp: new Date(item.timestamp),
          lastObserved: item.lastObserved ? new Date(item.lastObserved) : undefined
        }))

        this.behaviorHistory.set(userId, convertDates(data.behaviorHistory || []))
        this.performanceHistory.set(userId, convertDates(data.performanceHistory || []))
        this.feedbackHistory.set(userId, convertDates(data.feedbackHistory || []))
        this.behaviorPatterns.set(userId, convertDates(data.behaviorPatterns || []))
        this.adaptationHistory.set(userId, data.adaptationHistory || [])
      }
    } catch (error) {
      console.error('Failed to load user data:', error)
    }
  }
}

export const personalizationService = PersonalizationService.getInstance()