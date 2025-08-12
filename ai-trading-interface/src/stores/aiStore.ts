import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { personaService } from '@/services/personaService'
import { personalizationService } from '@/services/personalizationService'
import type { 
  ChainOfThoughtStep,
  ProactiveAction,
  InsightCard,
  Persona,
  AIResponse,
  StrategyAnalysis,
  MarketAnalysis 
} from '@/types'

interface AIState {
  // AI interaction data
  conversationHistory: AIResponse[]
  chainOfThoughtHistory: ChainOfThoughtStep[]
  proactiveActions: ProactiveAction[]
  insightCards: InsightCard[]
  
  // Current AI state
  currentPersona: Persona
  availablePersonas: Persona[]
  isProcessing: boolean
  lastQuery: string
  
  // AI analysis results
  currentStrategyAnalysis: StrategyAnalysis | null
  currentMarketAnalysis: MarketAnalysis | null
  
  // UI state
  showChainOfThought: boolean
  showInsightCards: boolean
  autoGenerateInsights: boolean
  
  // Settings
  aiSettings: {
    responseStyle: 'concise' | 'detailed' | 'technical'
    confidenceThreshold: number
    enableProactiveActions: boolean
    maxConversationHistory: number
  }
  
  // Actions
  addConversationEntry: (response: AIResponse) => void
  clearConversationHistory: () => void
  
  addChainOfThoughtStep: (step: ChainOfThoughtStep) => void
  clearChainOfThought: () => void
  
  addProactiveAction: (action: ProactiveAction) => void
  dismissProactiveAction: (id: string) => void
  executeProactiveAction: (id: string) => Promise<void>
  clearProactiveActions: () => void
  
  addInsightCard: (card: InsightCard) => void
  dismissInsightCard: (id: string) => void
  clearInsightCards: () => void
  
  setCurrentPersona: (persona: Persona) => void
  addPersona: (persona: Persona) => void
  updatePersona: (id: string, updates: Partial<Persona>) => void
  removePersona: (id: string) => void
  
  setStrategyAnalysis: (analysis: StrategyAnalysis | null) => void
  setMarketAnalysis: (analysis: MarketAnalysis | null) => void
  
  setProcessing: (processing: boolean) => void
  setLastQuery: (query: string) => void
  
  setShowChainOfThought: (show: boolean) => void
  setShowInsightCards: (show: boolean) => void
  setAutoGenerateInsights: (auto: boolean) => void
  
  updateAISettings: (settings: Partial<AIState['aiSettings']>) => void
  
  // AI interaction helpers
  processQuery: (query: string) => Promise<AIResponse>
  generateInsights: () => Promise<InsightCard[]>
  analyzeStrategy: (strategyDescription: string) => Promise<StrategyAnalysis>
  analyzeMarket: (symbols: string[]) => Promise<MarketAnalysis>
}

// Default personas
const defaultPersonas: Persona[] = [
  {
    id: 'conservative',
    name: 'Conservative Trader',
    type: 'conservative',
    description: 'Risk-averse approach with focus on capital preservation',
    riskTolerance: 0.3,
    optimizationStyle: 'safety_first',
    decisionSpeed: 'deliberate',
    preferences: {
      preferredTimeframes: ['4h', '1d', '1w'],
      riskLimits: {
        maxDrawdown: 0.1,
        maxPositionSize: 0.05,
        maxCorrelation: 0.5,
      },
      optimizationFocus: 'consistency',
      alertFrequency: 'frequent',
    },
  },
  {
    id: 'balanced',
    name: 'Balanced Trader',
    type: 'balanced',
    description: 'Balanced approach between risk and reward',
    riskTolerance: 0.5,
    optimizationStyle: 'balanced',
    decisionSpeed: 'moderate',
    preferences: {
      preferredTimeframes: ['1h', '4h', '1d'],
      riskLimits: {
        maxDrawdown: 0.15,
        maxPositionSize: 0.1,
        maxCorrelation: 0.7,
      },
      optimizationFocus: 'risk_adjusted',
      alertFrequency: 'moderate',
    },
  },
  {
    id: 'aggressive',
    name: 'Aggressive Trader',
    type: 'aggressive',
    description: 'High-risk, high-reward trading approach',
    riskTolerance: 0.8,
    optimizationStyle: 'performance_focused',
    decisionSpeed: 'quick',
    preferences: {
      preferredTimeframes: ['15m', '1h', '4h'],
      riskLimits: {
        maxDrawdown: 0.25,
        maxPositionSize: 0.2,
        maxCorrelation: 0.9,
      },
      optimizationFocus: 'return',
      alertFrequency: 'minimal',
    },
  },
]

export const useAIStore = create<AIState>()(
  persist(
    (set, get) => ({
      // Initial state
      conversationHistory: [],
      chainOfThoughtHistory: [],
      proactiveActions: [],
      insightCards: [],
      
      currentPersona: defaultPersonas[1], // Balanced by default
      availablePersonas: defaultPersonas,
      isProcessing: false,
      lastQuery: '',
      
      currentStrategyAnalysis: null,
      currentMarketAnalysis: null,
      
      showChainOfThought: true,
      showInsightCards: true,
      autoGenerateInsights: true,
      
      aiSettings: {
        responseStyle: 'detailed',
        confidenceThreshold: 0.7,
        enableProactiveActions: true,
        maxConversationHistory: 50,
      },
      
      // Conversation actions
      addConversationEntry: (response) => set((state) => {
        const newHistory = [...state.conversationHistory, response]
        // Limit history size
        if (newHistory.length > state.aiSettings.maxConversationHistory) {
          newHistory.splice(0, newHistory.length - state.aiSettings.maxConversationHistory)
        }
        return { conversationHistory: newHistory }
      }),
      
      clearConversationHistory: () => set({ conversationHistory: [] }),
      
      // Chain of thought actions
      addChainOfThoughtStep: (step) => set((state) => ({
        chainOfThoughtHistory: [...state.chainOfThoughtHistory, step]
      })),
      
      clearChainOfThought: () => set({ chainOfThoughtHistory: [] }),
      
      // Proactive actions
      addProactiveAction: (action) => set((state) => ({
        proactiveActions: [...state.proactiveActions, action]
      })),
      
      dismissProactiveAction: (id) => set((state) => ({
        proactiveActions: state.proactiveActions.filter(action => action.id !== id)
      })),
      
      executeProactiveAction: async (id) => {
        const action = get().proactiveActions.find(a => a.id === id)
        if (action) {
          try {
            await action.action()
            // Remove action after successful execution
            get().dismissProactiveAction(id)
          } catch (error) {
            console.error('Failed to execute proactive action:', error)
          }
        }
      },
      
      clearProactiveActions: () => set({ proactiveActions: [] }),
      
      // Insight cards
      addInsightCard: (card) => set((state) => ({
        insightCards: [...state.insightCards, card]
      })),
      
      dismissInsightCard: (id) => set((state) => ({
        insightCards: state.insightCards.map(card =>
          card.id === id ? { ...card, dismissed: true } : card
        )
      })),
      
      clearInsightCards: () => set({ insightCards: [] }),
      
      // Persona management
      setCurrentPersona: (persona) => {
        set({ currentPersona: persona })
        
        // Track persona change for personalization
        const userId = 'default-user' // In real app, get from auth
        personalizationService.trackUserAction(userId, {
          type: 'override_decision',
          context: 'persona_selection',
          personaRecommendation: get().currentPersona.name,
          userChoice: persona.name,
          outcome: 'neutral'
        }, {
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
          }
        })
      },
      
      addPersona: (persona) => set((state) => ({
        availablePersonas: [...state.availablePersonas, persona]
      })),
      
      updatePersona: (id, updates) => set((state) => ({
        availablePersonas: state.availablePersonas.map(persona =>
          persona.id === id ? { ...persona, ...updates } : persona
        ),
        currentPersona: state.currentPersona.id === id 
          ? { ...state.currentPersona, ...updates }
          : state.currentPersona
      })),
      
      removePersona: (id) => set((state) => ({
        availablePersonas: state.availablePersonas.filter(persona => persona.id !== id),
        currentPersona: state.currentPersona.id === id 
          ? defaultPersonas[1] // Fallback to balanced
          : state.currentPersona
      })),
      
      // Analysis results
      setStrategyAnalysis: (analysis) => set({ currentStrategyAnalysis: analysis }),
      setMarketAnalysis: (analysis) => set({ currentMarketAnalysis: analysis }),
      
      // UI state
      setProcessing: (processing) => set({ isProcessing: processing }),
      setLastQuery: (query) => set({ lastQuery: query }),
      setShowChainOfThought: (show) => set({ showChainOfThought: show }),
      setShowInsightCards: (show) => set({ showInsightCards: show }),
      setAutoGenerateInsights: (auto) => set({ autoGenerateInsights: auto }),
      
      updateAISettings: (settings) => set((state) => ({
        aiSettings: { ...state.aiSettings, ...settings }
      })),
      
      // AI interaction methods (these would integrate with actual AI services)
      processQuery: async (query) => {
        set({ isProcessing: true, lastQuery: query })
        
        try {
          // Mock AI response - in real implementation, this would call GPT-5/Claude
          const mockResponse: AIResponse = {
            content: `I understand you want to ${query}. Let me help you with that.`,
            confidence: 0.85,
            chainOfThought: [
              {
                id: `cot-${Date.now()}`,
                step: 1,
                reasoning: `Analyzing the query: "${query}"`,
                confidence: 0.9,
                alternatives: [],
                timestamp: new Date(),
              }
            ],
            proactiveActions: [],
            metadata: {
              model: 'gpt-5',
              tokens: 150,
              processingTime: 1200,
            }
          }
          
          get().addConversationEntry(mockResponse)
          
          // Add chain of thought steps
          mockResponse.chainOfThought.forEach(step => {
            get().addChainOfThoughtStep(step)
          })
          
          return mockResponse
        } finally {
          set({ isProcessing: false })
        }
      },
      
      generateInsights: async () => {
        // Mock insight generation
        const mockInsights: InsightCard[] = [
          {
            id: `insight-${Date.now()}`,
            type: 'opportunity',
            title: 'Market Opportunity Detected',
            content: 'BTC showing strong momentum signals',
            data: { symbol: 'BTC/USD', signal: 'bullish' },
            actions: [],
            confidence: 0.8,
            chainOfThought: [],
            timestamp: new Date(),
          }
        ]
        
        mockInsights.forEach(insight => {
          get().addInsightCard(insight)
        })
        
        return mockInsights
      },
      
      analyzeStrategy: async (strategyDescription) => {
        set({ isProcessing: true })
        
        try {
          // Mock strategy analysis
          const mockAnalysis: StrategyAnalysis = {
            feasibility: 0.8,
            complexity: 'moderate',
            estimatedPerformance: {
              expectedReturn: 0.15,
              expectedDrawdown: 0.08,
              confidence: 0.75,
              timeframe: '1 year',
            },
            requiredParameters: [],
            marketSuitability: [],
            risks: [
              {
                type: 'market',
                level: 'medium',
                description: 'Strategy may underperform in ranging markets',
                mitigation: 'Add trend filter',
                impact: 0.3,
              }
            ],
            recommendations: [
              'Consider adding a trend filter',
              'Test on multiple timeframes',
              'Implement proper risk management',
            ],
            chainOfThought: [],
          }
          
          // Apply persona influence to the analysis
          const currentPersona = get().currentPersona
          const influencedAnalysis = personaService.influenceStrategyAnalysis(mockAnalysis, currentPersona)
          
          set({ currentStrategyAnalysis: influencedAnalysis })
          return influencedAnalysis
        } finally {
          set({ isProcessing: false })
        }
      },
      
      analyzeMarket: async (symbols) => {
        set({ isProcessing: true })
        
        try {
          // Mock market analysis
          const mockAnalysis: MarketAnalysis = {
            sentiment: 'bullish',
            confidence: 0.75,
            trends: [
              {
                timeframe: '1d',
                direction: 'up',
                strength: 0.8,
                confidence: 0.85,
                description: 'Strong upward trend on daily timeframe',
              }
            ],
            opportunities: [
              {
                type: 'momentum',
                description: 'Momentum breakout opportunity',
                potential: 0.12,
                timeframe: '4h',
                confidence: 0.7,
              }
            ],
            risks: [
              {
                type: 'volatility',
                level: 0.6,
                description: 'Increased volatility expected',
                mitigation: 'Reduce position sizes',
              }
            ],
            recommendations: [
              'Consider momentum strategies',
              'Monitor for breakout confirmation',
              'Manage position sizes carefully',
            ],
            chainOfThought: [],
          }
          
          // Apply persona influence to the analysis
          const currentPersona = get().currentPersona
          const influencedAnalysis = personaService.influenceMarketAnalysis(mockAnalysis, currentPersona)
          
          set({ currentMarketAnalysis: influencedAnalysis })
          return influencedAnalysis
        } finally {
          set({ isProcessing: false })
        }
      },
    }),
    {
      name: 'ai-store',
      partialize: (state) => ({
        // Persist user preferences and personas
        currentPersona: state.currentPersona,
        availablePersonas: state.availablePersonas,
        showChainOfThought: state.showChainOfThought,
        showInsightCards: state.showInsightCards,
        autoGenerateInsights: state.autoGenerateInsights,
        aiSettings: state.aiSettings,
        // Don't persist conversation history or real-time data
      }),
    }
  )
)