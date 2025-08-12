import type { 
  Persona, 
  PersonaPreferences,
  StrategyAnalysis,
  MarketAnalysis,
  ProactiveAction,
  ChainOfThoughtStep,
  RiskAssessment 
} from '@/types'

export interface PersonaInfluence {
  riskAdjustment: number
  timeframePreference: string[]
  optimizationWeight: {
    return: number
    risk: number
    consistency: number
  }
  alertThreshold: number
  decisionConfidenceRequired: number
}

export interface DecisionContext {
  type: 'strategy_creation' | 'risk_assessment' | 'optimization' | 'market_analysis'
  data: any
  currentConditions: {
    marketVolatility: number
    portfolioRisk: number
    recentPerformance: number
  }
}

export interface PersonaDecision {
  recommendation: string
  confidence: number
  reasoning: ChainOfThoughtStep[]
  adjustments: any
  proactiveActions: ProactiveAction[]
}

export interface PersonaAdaptationData {
  userActions: UserAction[]
  performanceMetrics: PerformanceMetric[]
  feedbackHistory: UserFeedback[]
  timeframe: string
}

export interface UserAction {
  id: string
  type: 'accept_suggestion' | 'reject_suggestion' | 'modify_parameters' | 'override_decision'
  timestamp: Date
  context: string
  personaRecommendation: string
  userChoice: string
  outcome?: 'positive' | 'negative' | 'neutral'
}

export interface PerformanceMetric {
  id: string
  timestamp: Date
  personaId: string
  metric: 'return' | 'drawdown' | 'sharpe_ratio' | 'win_rate'
  value: number
  benchmark: number
}

export interface UserFeedback {
  id: string
  timestamp: Date
  personaId: string
  rating: number // 1-5
  category: 'risk_management' | 'strategy_suggestions' | 'market_analysis' | 'overall'
  comment?: string
}

export class PersonaService {
  private static instance: PersonaService
  
  public static getInstance(): PersonaService {
    if (!PersonaService.instance) {
      PersonaService.instance = new PersonaService()
    }
    return PersonaService.instance
  }

  /**
   * Calculate persona influence on decision-making
   */
  calculatePersonaInfluence(persona: Persona): PersonaInfluence {
    const baseInfluence: PersonaInfluence = {
      riskAdjustment: persona.riskTolerance,
      timeframePreference: persona.preferences.preferredTimeframes,
      optimizationWeight: this.calculateOptimizationWeights(persona),
      alertThreshold: this.calculateAlertThreshold(persona),
      decisionConfidenceRequired: this.calculateConfidenceThreshold(persona)
    }

    return baseInfluence
  }

  /**
   * Apply persona influence to strategy analysis
   */
  influenceStrategyAnalysis(
    analysis: StrategyAnalysis, 
    persona: Persona
  ): StrategyAnalysis {
    const influence = this.calculatePersonaInfluence(persona)
    
    // Adjust risk assessments based on persona
    const adjustedRisks = analysis.risks.map(risk => ({
      ...risk,
      level: this.adjustRiskLevel(risk.level, persona.riskTolerance),
      impact: risk.impact * (2 - persona.riskTolerance) // More risk-averse = higher impact
    }))

    // Adjust performance estimates
    const adjustedPerformance = {
      ...analysis.estimatedPerformance,
      expectedReturn: analysis.estimatedPerformance.expectedReturn * influence.optimizationWeight.return,
      expectedDrawdown: analysis.estimatedPerformance.expectedDrawdown * (2 - persona.riskTolerance),
      confidence: Math.min(analysis.estimatedPerformance.confidence, influence.decisionConfidenceRequired)
    }

    // Add persona-specific recommendations
    const personaRecommendations = this.generatePersonaRecommendations(analysis, persona)

    return {
      ...analysis,
      risks: adjustedRisks,
      estimatedPerformance: adjustedPerformance,
      recommendations: [...analysis.recommendations, ...personaRecommendations],
      chainOfThought: [
        ...analysis.chainOfThought,
        {
          id: `persona-influence-${Date.now()}`,
          step: analysis.chainOfThought.length + 1,
          reasoning: `Applied ${persona.name} persona influence: Risk tolerance ${persona.riskTolerance}, Focus on ${persona.preferences.optimizationFocus}`,
          confidence: 0.9,
          alternatives: [],
          timestamp: new Date()
        }
      ]
    }
  }

  /**
   * Apply persona influence to market analysis
   */
  influenceMarketAnalysis(
    analysis: MarketAnalysis, 
    persona: Persona
  ): MarketAnalysis {
    const influence = this.calculatePersonaInfluence(persona)
    
    // Adjust confidence based on persona decision speed
    const confidenceMultiplier = persona.decisionSpeed === 'quick' ? 0.9 : 
                                persona.decisionSpeed === 'deliberate' ? 1.1 : 1.0

    // Filter opportunities based on risk tolerance
    const filteredOpportunities = analysis.opportunities.filter(opp => {
      const riskLevel = this.getOpportunityRiskLevel(opp.type)
      return riskLevel <= persona.riskTolerance
    })

    // Adjust risk analysis based on persona
    const adjustedRisks = analysis.risks.map(risk => ({
      ...risk,
      level: risk.level * (2 - persona.riskTolerance)
    }))

    return {
      ...analysis,
      confidence: Math.min(analysis.confidence * confidenceMultiplier, 1.0),
      opportunities: filteredOpportunities,
      risks: adjustedRisks,
      recommendations: [
        ...analysis.recommendations,
        ...this.generateMarketRecommendations(analysis, persona)
      ],
      chainOfThought: [
        ...analysis.chainOfThought,
        {
          id: `persona-market-influence-${Date.now()}`,
          step: analysis.chainOfThought.length + 1,
          reasoning: `Applied ${persona.name} market analysis adjustments: Filtered ${analysis.opportunities.length - filteredOpportunities.length} high-risk opportunities`,
          confidence: 0.85,
          alternatives: [],
          timestamp: new Date()
        }
      ]
    }
  }

  /**
   * Make persona-influenced decisions
   */
  makePersonaDecision(
    context: DecisionContext, 
    persona: Persona
  ): PersonaDecision {
    const influence = this.calculatePersonaInfluence(persona)
    const chainOfThought: ChainOfThoughtStep[] = []
    
    // Step 1: Analyze context with persona lens
    chainOfThought.push({
      id: `decision-context-${Date.now()}`,
      step: 1,
      reasoning: `Analyzing ${context.type} decision through ${persona.name} persona lens. Risk tolerance: ${persona.riskTolerance}, Decision speed: ${persona.decisionSpeed}`,
      data: { context: context.type, persona: persona.name },
      confidence: 0.9,
      alternatives: [],
      timestamp: new Date()
    })

    // Step 2: Apply persona-specific logic
    let recommendation: string
    let confidence: number
    let adjustments: any = {}
    let proactiveActions: ProactiveAction[] = []

    switch (context.type) {
      case 'strategy_creation':
        const strategyDecision = this.makeStrategyDecision(context, persona, influence)
        recommendation = strategyDecision.recommendation
        confidence = strategyDecision.confidence
        adjustments = strategyDecision.adjustments
        proactiveActions = strategyDecision.proactiveActions
        break

      case 'risk_assessment':
        const riskDecision = this.makeRiskDecision(context, persona, influence)
        recommendation = riskDecision.recommendation
        confidence = riskDecision.confidence
        adjustments = riskDecision.adjustments
        proactiveActions = riskDecision.proactiveActions
        break

      case 'optimization':
        const optimizationDecision = this.makeOptimizationDecision(context, persona, influence)
        recommendation = optimizationDecision.recommendation
        confidence = optimizationDecision.confidence
        adjustments = optimizationDecision.adjustments
        proactiveActions = optimizationDecision.proactiveActions
        break

      case 'market_analysis':
        const marketDecision = this.makeMarketDecision(context, persona, influence)
        recommendation = marketDecision.recommendation
        confidence = marketDecision.confidence
        adjustments = marketDecision.adjustments
        proactiveActions = marketDecision.proactiveActions
        break

      default:
        recommendation = 'Unable to process decision with current persona configuration'
        confidence = 0.1
    }

    // Step 3: Final reasoning
    chainOfThought.push({
      id: `decision-final-${Date.now()}`,
      step: 2,
      reasoning: `Final decision: ${recommendation}. Confidence adjusted for ${persona.decisionSpeed} decision speed and ${persona.preferences.optimizationFocus} focus.`,
      data: { recommendation, confidence, adjustments },
      confidence,
      alternatives: [],
      timestamp: new Date()
    })

    return {
      recommendation,
      confidence,
      reasoning: chainOfThought,
      adjustments,
      proactiveActions
    }
  }

  /**
   * Select optimal persona based on user profile and market conditions
   */
  selectOptimalPersona(
    availablePersonas: Persona[],
    userProfile: {
      experienceLevel: 'beginner' | 'intermediate' | 'advanced' | 'expert'
      riskPreference: number
      tradingGoals: string[]
      timeAvailable: 'low' | 'medium' | 'high'
    },
    marketConditions: {
      volatility: number
      trend: 'bullish' | 'bearish' | 'neutral'
      uncertainty: number
    }
  ): Persona {
    let bestPersona = availablePersonas[0]
    let bestScore = 0

    for (const persona of availablePersonas) {
      const score = this.calculatePersonaScore(persona, userProfile, marketConditions)
      if (score > bestScore) {
        bestScore = score
        bestPersona = persona
      }
    }

    return bestPersona
  }

  /**
   * Create custom persona based on user preferences
   */
  createCustomPersona(
    name: string,
    preferences: {
      riskTolerance: number
      tradingStyle: 'scalping' | 'day_trading' | 'swing_trading' | 'position_trading'
      focusArea: 'growth' | 'income' | 'preservation'
      timeCommitment: 'minimal' | 'moderate' | 'intensive'
    }
  ): Persona {
    const customPreferences: PersonaPreferences = {
      preferredTimeframes: this.getTimeframesForStyle(preferences.tradingStyle),
      riskLimits: {
        maxDrawdown: 0.05 + (preferences.riskTolerance * 0.2),
        maxPositionSize: 0.02 + (preferences.riskTolerance * 0.18),
        maxCorrelation: 0.3 + (preferences.riskTolerance * 0.6)
      },
      optimizationFocus: preferences.focusArea === 'growth' ? 'return' : 
                        preferences.focusArea === 'income' ? 'risk_adjusted' : 'consistency',
      alertFrequency: preferences.timeCommitment === 'minimal' ? 'minimal' :
                     preferences.timeCommitment === 'moderate' ? 'moderate' : 'frequent'
    }

    return {
      id: `custom-${Date.now()}`,
      name,
      type: 'custom',
      description: `Custom persona: ${preferences.tradingStyle} with ${preferences.focusArea} focus`,
      riskTolerance: preferences.riskTolerance,
      optimizationStyle: preferences.focusArea === 'growth' ? 'performance_focused' :
                        preferences.focusArea === 'preservation' ? 'safety_first' : 'balanced',
      decisionSpeed: preferences.timeCommitment === 'intensive' ? 'quick' :
                    preferences.timeCommitment === 'minimal' ? 'deliberate' : 'moderate',
      preferences: customPreferences
    }
  }

  // Private helper methods

  private calculateOptimizationWeights(persona: Persona): { return: number; risk: number; consistency: number } {
    switch (persona.preferences.optimizationFocus) {
      case 'return':
        return { return: 0.7, risk: 0.2, consistency: 0.1 }
      case 'risk_adjusted':
        return { return: 0.4, risk: 0.4, consistency: 0.2 }
      case 'consistency':
        return { return: 0.2, risk: 0.3, consistency: 0.5 }
      default:
        return { return: 0.33, risk: 0.33, consistency: 0.34 }
    }
  }

  private calculateAlertThreshold(persona: Persona): number {
    const baseThreshold = 0.5
    const frequencyMultiplier = persona.preferences.alertFrequency === 'frequent' ? 0.7 :
                               persona.preferences.alertFrequency === 'moderate' ? 1.0 : 1.3
    return baseThreshold * frequencyMultiplier
  }

  private calculateConfidenceThreshold(persona: Persona): number {
    const baseConfidence = 0.7
    const speedMultiplier = persona.decisionSpeed === 'quick' ? 0.8 :
                           persona.decisionSpeed === 'deliberate' ? 1.2 : 1.0
    return Math.min(baseConfidence * speedMultiplier, 0.95)
  }

  private adjustRiskLevel(level: string, riskTolerance: number): 'low' | 'medium' | 'high' | 'critical' {
    const riskLevels: ('low' | 'medium' | 'high' | 'critical')[] = ['low', 'medium', 'high', 'critical']
    const currentIndex = riskLevels.indexOf(level as any)
    
    if (currentIndex === -1) return 'medium' // Default fallback
    
    if (riskTolerance < 0.3) {
      // Conservative: increase perceived risk
      return riskLevels[Math.min(currentIndex + 1, riskLevels.length - 1)]
    } else if (riskTolerance > 0.7) {
      // Aggressive: decrease perceived risk
      return riskLevels[Math.max(currentIndex - 1, 0)]
    }
    
    return level as 'low' | 'medium' | 'high' | 'critical'
  }

  private generatePersonaRecommendations(analysis: StrategyAnalysis, persona: Persona): string[] {
    const recommendations: string[] = []
    
    if (persona.type === 'conservative') {
      recommendations.push('Consider adding additional stop-loss mechanisms')
      recommendations.push('Test with smaller position sizes initially')
      if (analysis.estimatedPerformance.expectedDrawdown > persona.preferences.riskLimits.maxDrawdown) {
        recommendations.push('Reduce risk parameters to align with conservative approach')
      }
    } else if (persona.type === 'aggressive') {
      recommendations.push('Consider increasing position sizes for higher returns')
      recommendations.push('Explore shorter timeframes for more opportunities')
      if (analysis.complexity === 'simple') {
        recommendations.push('Add complexity to capture more market inefficiencies')
      }
    } else {
      recommendations.push('Balance risk and reward according to current market conditions')
      recommendations.push('Monitor performance and adjust parameters as needed')
    }

    return recommendations
  }

  private generateMarketRecommendations(analysis: MarketAnalysis, persona: Persona): string[] {
    const recommendations: string[] = []
    
    if (persona.decisionSpeed === 'quick' && analysis.opportunities.length > 0) {
      recommendations.push('Act quickly on identified opportunities')
    } else if (persona.decisionSpeed === 'deliberate') {
      recommendations.push('Take time to validate signals before acting')
      recommendations.push('Consider waiting for stronger confirmation')
    }

    if (persona.preferences.alertFrequency === 'frequent') {
      recommendations.push('Monitor for additional market signals')
    }

    return recommendations
  }

  private getOpportunityRiskLevel(type: string): number {
    const riskLevels = {
      'arbitrage': 0.2,
      'mean_reversion': 0.4,
      'momentum': 0.6,
      'breakout': 0.8
    }
    return riskLevels[type as keyof typeof riskLevels] || 0.5
  }

  private makeStrategyDecision(
    context: DecisionContext, 
    persona: Persona, 
    influence: PersonaInfluence
  ): Omit<PersonaDecision, 'reasoning'> {
    // Strategy-specific decision logic
    const recommendation = `Create strategy with ${persona.preferences.optimizationFocus} focus and ${persona.riskTolerance * 100}% risk tolerance`
    const confidence = influence.decisionConfidenceRequired
    const adjustments = {
      riskParameters: {
        maxDrawdown: persona.preferences.riskLimits.maxDrawdown,
        positionSize: persona.preferences.riskLimits.maxPositionSize
      },
      timeframes: persona.preferences.preferredTimeframes
    }
    
    const proactiveActions: ProactiveAction[] = [{
      id: `strategy-action-${Date.now()}`,
      type: 'suggestion',
      title: 'Optimize Strategy Parameters',
      description: `Adjust parameters based on ${persona.name} preferences`,
      action: async () => {
        console.log('Applying persona-based parameter optimization')
      },
      priority: 'medium',
      chainOfThought: [],
      timestamp: new Date()
    }]

    return { recommendation, confidence, adjustments, proactiveActions }
  }

  private makeRiskDecision(
    context: DecisionContext, 
    persona: Persona, 
    influence: PersonaInfluence
  ): Omit<PersonaDecision, 'reasoning'> {
    const currentRisk = context.currentConditions.portfolioRisk
    const maxAcceptableRisk = persona.preferences.riskLimits.maxDrawdown
    
    let recommendation: string
    let priority: 'low' | 'medium' | 'high' | 'critical' = 'medium'
    
    if (currentRisk > maxAcceptableRisk) {
      recommendation = `Reduce portfolio risk from ${(currentRisk * 100).toFixed(1)}% to below ${(maxAcceptableRisk * 100).toFixed(1)}%`
      priority = currentRisk > maxAcceptableRisk * 1.5 ? 'critical' : 'high'
    } else {
      recommendation = `Current risk level ${(currentRisk * 100).toFixed(1)}% is acceptable for ${persona.name}`
      priority = 'low'
    }

    const proactiveActions: ProactiveAction[] = currentRisk > maxAcceptableRisk ? [{
      id: `risk-action-${Date.now()}`,
      type: 'risk_warning',
      title: 'Risk Limit Exceeded',
      description: recommendation,
      action: async () => {
        console.log('Implementing risk reduction measures')
      },
      priority,
      chainOfThought: [],
      timestamp: new Date()
    }] : []

    return {
      recommendation,
      confidence: 0.9,
      adjustments: { targetRisk: maxAcceptableRisk },
      proactiveActions
    }
  }

  private makeOptimizationDecision(
    context: DecisionContext, 
    persona: Persona, 
    influence: PersonaInfluence
  ): Omit<PersonaDecision, 'reasoning'> {
    const weights = influence.optimizationWeight
    const recommendation = `Optimize with ${(weights.return * 100).toFixed(0)}% return focus, ${(weights.risk * 100).toFixed(0)}% risk focus, ${(weights.consistency * 100).toFixed(0)}% consistency focus`
    
    return {
      recommendation,
      confidence: influence.decisionConfidenceRequired,
      adjustments: { optimizationWeights: weights },
      proactiveActions: []
    }
  }

  private makeMarketDecision(
    context: DecisionContext, 
    persona: Persona, 
    influence: PersonaInfluence
  ): Omit<PersonaDecision, 'reasoning'> {
    const volatility = context.currentConditions.marketVolatility
    const riskTolerance = persona.riskTolerance
    
    let recommendation: string
    if (volatility > 0.7 && riskTolerance < 0.4) {
      recommendation = 'High volatility detected. Consider reducing exposure or waiting for calmer conditions.'
    } else if (volatility < 0.3 && riskTolerance > 0.6) {
      recommendation = 'Low volatility environment. Consider increasing position sizes or exploring more opportunities.'
    } else {
      recommendation = 'Market conditions are suitable for current persona settings.'
    }

    return {
      recommendation,
      confidence: 0.8,
      adjustments: { volatilityAdjustment: volatility > riskTolerance ? -0.2 : 0.1 },
      proactiveActions: []
    }
  }

  private calculatePersonaScore(
    persona: Persona,
    userProfile: any,
    marketConditions: any
  ): number {
    let score = 0

    // Risk alignment
    const riskDiff = Math.abs(persona.riskTolerance - userProfile.riskPreference)
    score += (1 - riskDiff) * 0.4

    // Experience level alignment
    const experienceScore = this.getExperienceScore(persona, userProfile.experienceLevel)
    score += experienceScore * 0.3

    // Market conditions alignment
    const marketScore = this.getMarketScore(persona, marketConditions)
    score += marketScore * 0.3

    return score
  }

  private getExperienceScore(persona: Persona, experienceLevel: string): number {
    if (experienceLevel === 'beginner' && persona.type === 'conservative') return 1.0
    if (experienceLevel === 'intermediate' && persona.type === 'balanced') return 1.0
    if (experienceLevel === 'advanced' && persona.type === 'aggressive') return 1.0
    if (experienceLevel === 'expert') return 0.9 // Experts can use any persona
    return 0.5
  }

  private getMarketScore(persona: Persona, marketConditions: any): number {
    const volatility = marketConditions.volatility
    const uncertainty = marketConditions.uncertainty

    if (volatility > 0.7 && persona.type === 'conservative') return 1.0
    if (volatility < 0.3 && persona.type === 'aggressive') return 1.0
    if (volatility >= 0.3 && volatility <= 0.7 && persona.type === 'balanced') return 1.0
    
    return 0.6
  }

  private getTimeframesForStyle(style: string): string[] {
    const timeframes = {
      'scalping': ['1m', '5m', '15m'],
      'day_trading': ['15m', '1h', '4h'],
      'swing_trading': ['4h', '1d', '3d'],
      'position_trading': ['1d', '1w', '1M']
    }
    return timeframes[style as keyof typeof timeframes] || ['1h', '4h', '1d']
  }
}

export const personaService = PersonaService.getInstance()