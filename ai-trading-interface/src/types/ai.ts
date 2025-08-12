// AI-Specific Data Models
export interface ChainOfThoughtStep {
  id: string
  step: number
  reasoning: string
  data?: any
  confidence: number
  alternatives?: Alternative[]
  timestamp: Date
}

export interface Alternative {
  id: string
  description: string
  confidence: number
  reasoning: string
}

export interface ProactiveAction {
  id: string
  type: 'suggestion' | 'alert' | 'optimization' | 'risk_warning'
  title: string
  description: string
  action: () => Promise<void>
  priority: 'low' | 'medium' | 'high' | 'critical'
  chainOfThought: ChainOfThoughtStep[]
  timestamp: Date
  dismissed?: boolean
}

export interface InsightCard {
  id: string
  type: 'opportunity' | 'risk' | 'performance' | 'market_analysis'
  title: string
  content: string
  data: any
  actions: ProactiveAction[]
  confidence: number
  chainOfThought: ChainOfThoughtStep[]
  timestamp: Date
  dismissed?: boolean
}

export interface GenerativeComponent {
  id: string
  type: 'chart' | 'table' | 'card' | 'form' | 'dashboard'
  props: ComponentProps
  data: any
  interactions: Interaction[]
  adaptations: Adaptation[]
}

export interface ComponentProps {
  [key: string]: any
}

export interface Interaction {
  type: 'click' | 'hover' | 'drag' | 'zoom' | 'filter'
  handler: (event: any) => void
  description: string
}

export interface Adaptation {
  trigger: string
  modification: string
  description: string
}

// AI Persona System
export interface Persona {
  id: string
  name: string
  type: 'conservative' | 'balanced' | 'aggressive' | 'custom'
  description: string
  riskTolerance: number
  optimizationStyle: 'safety_first' | 'balanced' | 'performance_focused'
  decisionSpeed: 'deliberate' | 'moderate' | 'quick'
  preferences: PersonaPreferences
}

export interface PersonaPreferences {
  preferredTimeframes: string[]
  riskLimits: {
    maxDrawdown: number
    maxPositionSize: number
    maxCorrelation: number
  }
  optimizationFocus: 'return' | 'risk_adjusted' | 'consistency'
  alertFrequency: 'minimal' | 'moderate' | 'frequent'
}

// AI Engine Interfaces
export interface AIResponse {
  content: string
  confidence: number
  chainOfThought: ChainOfThoughtStep[]
  proactiveActions: ProactiveAction[]
  metadata: {
    model: string
    tokens: number
    processingTime: number
  }
}

export interface StrategyAnalysis {
  feasibility: number
  complexity: 'simple' | 'moderate' | 'complex' | 'advanced'
  estimatedPerformance: PerformanceEstimate
  requiredParameters: any[] // Will be properly typed when trading.ts is imported
  marketSuitability: any[] // Will be properly typed when trading.ts is imported
  risks: RiskAssessment[]
  recommendations: string[]
  chainOfThought: ChainOfThoughtStep[]
}

export interface PerformanceEstimate {
  expectedReturn: number
  expectedDrawdown: number
  confidence: number
  timeframe: string
}

export interface RiskAssessment {
  type: 'market' | 'liquidity' | 'technical' | 'operational'
  level: 'low' | 'medium' | 'high' | 'critical'
  description: string
  mitigation: string
  impact: number
}

export interface HaasScriptResult {
  script: string
  parameters: any[] // Will be properly typed when trading.ts is imported
  validation: ValidationResult
  optimization: OptimizationSuggestion[]
  chainOfThought: ChainOfThoughtStep[]
}

export interface ValidationResult {
  isValid: boolean
  errors: ValidationError[]
  warnings: ValidationWarning[]
  suggestions: string[]
}

export interface ValidationError {
  line: number
  column: number
  message: string
  severity: 'error' | 'warning' | 'info'
}

export interface ValidationWarning {
  line: number
  column: number
  message: string
  suggestion: string
}

export interface OptimizationSuggestion {
  type: 'parameter' | 'logic' | 'performance' | 'risk'
  description: string
  impact: 'low' | 'medium' | 'high'
  implementation: string
  confidence: number
}

export interface MarketAnalysis {
  sentiment: 'bullish' | 'bearish' | 'neutral'
  confidence: number
  trends: TrendAnalysis[]
  opportunities: OpportunityAnalysis[]
  risks: RiskAnalysis[]
  recommendations: string[]
  chainOfThought: ChainOfThoughtStep[]
}

export interface TrendAnalysis {
  timeframe: string
  direction: 'up' | 'down' | 'sideways'
  strength: number
  confidence: number
  description: string
}

export interface OpportunityAnalysis {
  type: 'arbitrage' | 'momentum' | 'mean_reversion' | 'breakout'
  description: string
  potential: number
  timeframe: string
  confidence: number
}

export interface RiskAnalysis {
  type: 'volatility' | 'liquidity' | 'correlation' | 'drawdown'
  level: number
  description: string
  mitigation: string
}

// Re-export persona service types for convenience
export type {
  PersonaInfluence,
  DecisionContext,
  PersonaDecision,
  PersonaAdaptationData,
  UserAction,
  PerformanceMetric,
  UserFeedback
} from '@/services/personaService'

export type {
  BehaviorPattern,
  AdaptationSuggestion,
  PersonalizationMetrics,
  LearningContext
} from '@/services/personalizationService'