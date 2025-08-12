import { vi } from 'vitest'
import type { AIResponse, ChainOfThoughtStep, StrategyAnalysis } from '../../types/ai'

export const mockAIService = {
  generateResponse: vi.fn().mockResolvedValue({
    content: 'Mock AI response',
    confidence: 0.85,
    chainOfThought: [
      {
        id: '1',
        step: 1,
        reasoning: 'Mock reasoning step',
        confidence: 0.85,
        timestamp: new Date(),
      }
    ] as ChainOfThoughtStep[],
    metadata: {
      model: 'gpt-4',
      tokens: 100,
      processingTime: 500,
    }
  } as AIResponse),

  analyzeStrategy: vi.fn().mockResolvedValue({
    analysis: 'Mock strategy analysis',
    suggestions: ['Suggestion 1', 'Suggestion 2'],
    riskAssessment: {
      level: 'medium',
      factors: ['Market volatility', 'Position size'],
    },
    confidence: 0.8,
  } as StrategyAnalysis),

  generateHaasScript: vi.fn().mockResolvedValue({
    script: 'Mock HaasScript code',
    parameters: [
      { name: 'period', value: 14, type: 'number' },
      { name: 'threshold', value: 0.02, type: 'number' },
    ],
    explanation: 'Mock script explanation',
  }),

  explainDecision: vi.fn().mockResolvedValue([
    {
      id: '1',
      step: 1,
      reasoning: 'Mock decision explanation',
      confidence: 0.9,
      timestamp: new Date(),
    }
  ] as ChainOfThoughtStep[]),
}

export const createMockAIResponse = (overrides?: Partial<AIResponse>): AIResponse => ({
  content: 'Mock response',
  confidence: 0.85,
  chainOfThought: [],
  metadata: {
    model: 'gpt-4',
    tokens: 100,
    processingTime: 500,
  },
  ...overrides,
})

export const createMockChainOfThoughtStep = (overrides?: Partial<ChainOfThoughtStep>): ChainOfThoughtStep => ({
  id: '1',
  step: 1,
  reasoning: 'Mock reasoning',
  confidence: 0.85,
  timestamp: new Date(),
  ...overrides,
})