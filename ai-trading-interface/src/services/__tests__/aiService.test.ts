import { describe, it, expect, vi, beforeEach } from 'vitest'
import { aiService } from '../aiService'
import { createMockAIResponse, createMockChainOfThoughtStep } from '../../test/mocks/aiService'

// Mock fetch
global.fetch = vi.fn()

describe('AIService', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(fetch).mockResolvedValue({
      ok: true,
      json: vi.fn().mockResolvedValue({
        choices: [{
          message: {
            content: 'Mock AI response',
          },
        }],
        usage: {
          total_tokens: 100,
        },
      }),
    } as any)
  })

  describe('generateResponse', () => {
    it('generates AI response successfully', async () => {
      const prompt = 'Analyze this trading strategy'
      const context = { market: 'BTC/USD', timeframe: '1h' }

      const response = await aiService.generateResponse(prompt, context)

      expect(response).toBeDefined()
      expect(response.content).toBe('Mock AI response')
      expect(response.confidence).toBeGreaterThan(0)
      expect(response.metadata).toBeDefined()
    })

    it('handles API errors gracefully', async () => {
      vi.mocked(fetch).mockResolvedValue({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
      } as any)

      const prompt = 'Test prompt'

      await expect(aiService.generateResponse(prompt))
        .rejects.toThrow('AI service error: 500 Internal Server Error')
    })

    it('includes chain of thought in response', async () => {
      vi.mocked(fetch).mockResolvedValue({
        ok: true,
        json: vi.fn().mockResolvedValue({
          choices: [{
            message: {
              content: JSON.stringify({
                response: 'AI response',
                chainOfThought: [
                  { step: 1, reasoning: 'First step', confidence: 0.9 },
                  { step: 2, reasoning: 'Second step', confidence: 0.8 },
                ],
              }),
            },
          }],
          usage: { total_tokens: 150 },
        }),
      } as any)

      const response = await aiService.generateResponse('Test prompt', {}, true)

      expect(response.chainOfThought).toHaveLength(2)
      expect(response.chainOfThought[0].reasoning).toBe('First step')
    })

    it('respects rate limiting', async () => {
      const promises = Array.from({ length: 10 }, () => 
        aiService.generateResponse('Test prompt')
      )

      await Promise.all(promises)

      // Should not exceed rate limit
      expect(fetch).toHaveBeenCalledTimes(10)
    })
  })

  describe('analyzeStrategy', () => {
    it('analyzes trading strategy successfully', async () => {
      const strategyDescription = 'RSI-based scalping strategy'
      const marketContext = { symbol: 'BTC/USD', volatility: 0.05 }

      vi.mocked(fetch).mockResolvedValue({
        ok: true,
        json: vi.fn().mockResolvedValue({
          choices: [{
            message: {
              content: JSON.stringify({
                analysis: 'Strategy analysis result',
                suggestions: ['Optimize RSI period', 'Add stop loss'],
                riskAssessment: {
                  level: 'medium',
                  factors: ['Market volatility', 'Position size'],
                },
                confidence: 0.85,
              }),
            },
          }],
        }),
      } as any)

      const analysis = await aiService.analyzeStrategy(strategyDescription, marketContext)

      expect(analysis.analysis).toBe('Strategy analysis result')
      expect(analysis.suggestions).toHaveLength(2)
      expect(analysis.riskAssessment.level).toBe('medium')
      expect(analysis.confidence).toBe(0.85)
    })

    it('handles invalid strategy descriptions', async () => {
      const invalidStrategy = ''

      await expect(aiService.analyzeStrategy(invalidStrategy))
        .rejects.toThrow('Strategy description cannot be empty')
    })
  })

  describe('generateHaasScript', () => {
    it('generates HaasScript code successfully', async () => {
      const strategyDescription = 'Simple moving average crossover'
      const parameters = { fastPeriod: 10, slowPeriod: 20 }

      vi.mocked(fetch).mockResolvedValue({
        ok: true,
        json: vi.fn().mockResolvedValue({
          choices: [{
            message: {
              content: JSON.stringify({
                script: 'var fastMA = MA(Close, 10);\nvar slowMA = MA(Close, 20);',
                parameters: [
                  { name: 'fastPeriod', value: 10, type: 'number' },
                  { name: 'slowPeriod', value: 20, type: 'number' },
                ],
                explanation: 'Moving average crossover strategy implementation',
              }),
            },
          }],
        }),
      } as any)

      const result = await aiService.generateHaasScript(strategyDescription, parameters)

      expect(result.script).toContain('MA(Close')
      expect(result.parameters).toHaveLength(2)
      expect(result.explanation).toBeDefined()
    })

    it('validates generated script syntax', async () => {
      const strategyDescription = 'Invalid strategy'

      vi.mocked(fetch).mockResolvedValue({
        ok: true,
        json: vi.fn().mockResolvedValue({
          choices: [{
            message: {
              content: JSON.stringify({
                script: 'invalid syntax here',
                parameters: [],
                explanation: 'Invalid script',
              }),
            },
          }],
        }),
      } as any)

      await expect(aiService.generateHaasScript(strategyDescription))
        .rejects.toThrow('Generated script contains syntax errors')
    })
  })

  describe('explainDecision', () => {
    it('provides decision explanation with chain of thought', async () => {
      const decision = { action: 'buy', confidence: 0.8 }
      const context = { market: 'BTC/USD', indicators: { rsi: 30 } }

      vi.mocked(fetch).mockResolvedValue({
        ok: true,
        json: vi.fn().mockResolvedValue({
          choices: [{
            message: {
              content: JSON.stringify({
                chainOfThought: [
                  {
                    step: 1,
                    reasoning: 'RSI indicates oversold condition',
                    confidence: 0.9,
                  },
                  {
                    step: 2,
                    reasoning: 'Market trend supports buy signal',
                    confidence: 0.7,
                  },
                ],
              }),
            },
          }],
        }),
      } as any)

      const explanation = await aiService.explainDecision(decision, context)

      expect(explanation).toHaveLength(2)
      expect(explanation[0].reasoning).toContain('RSI indicates')
      expect(explanation[1].reasoning).toContain('Market trend')
    })
  })

  describe('caching and optimization', () => {
    it('caches similar requests', async () => {
      const prompt = 'Test caching'

      await aiService.generateResponse(prompt)
      await aiService.generateResponse(prompt)

      // Second request should use cache
      expect(fetch).toHaveBeenCalledTimes(1)
    })

    it('invalidates cache after timeout', async () => {
      const prompt = 'Test cache timeout'

      await aiService.generateResponse(prompt)
      
      // Mock time passage
      vi.advanceTimersByTime(60000) // 1 minute
      
      await aiService.generateResponse(prompt)

      expect(fetch).toHaveBeenCalledTimes(2)
    })

    it('batches multiple requests', async () => {
      const prompts = ['Prompt 1', 'Prompt 2', 'Prompt 3']

      const promises = prompts.map(prompt => 
        aiService.generateResponse(prompt)
      )

      await Promise.all(promises)

      // Should batch requests to reduce API calls
      expect(fetch).toHaveBeenCalledTimes(1)
    })
  })

  describe('error handling and retries', () => {
    it('retries failed requests', async () => {
      vi.mocked(fetch)
        .mockResolvedValueOnce({
          ok: false,
          status: 429,
          statusText: 'Too Many Requests',
        } as any)
        .mockResolvedValueOnce({
          ok: true,
          json: vi.fn().mockResolvedValue({
            choices: [{ message: { content: 'Success after retry' } }],
            usage: { total_tokens: 50 },
          }),
        } as any)

      const response = await aiService.generateResponse('Test retry')

      expect(response.content).toBe('Success after retry')
      expect(fetch).toHaveBeenCalledTimes(2)
    })

    it('handles network errors', async () => {
      vi.mocked(fetch).mockRejectedValue(new Error('Network error'))

      await expect(aiService.generateResponse('Test network error'))
        .rejects.toThrow('Network error')
    })

    it('provides fallback responses', async () => {
      vi.mocked(fetch).mockRejectedValue(new Error('Service unavailable'))

      const response = await aiService.generateResponse('Test fallback', {}, false, true)

      expect(response.content).toContain('AI service temporarily unavailable')
      expect(response.confidence).toBe(0)
    })
  })

  describe('context management', () => {
    it('maintains conversation context', async () => {
      const context = { conversationId: 'conv-1' }

      await aiService.generateResponse('First message', context)
      await aiService.generateResponse('Follow up message', context)

      const calls = vi.mocked(fetch).mock.calls
      expect(calls[1][1]?.body).toContain('First message')
    })

    it('limits context window size', async () => {
      const context = { conversationId: 'conv-2' }

      // Send many messages to exceed context window
      for (let i = 0; i < 100; i++) {
        await aiService.generateResponse(`Message ${i}`, context)
      }

      const lastCall = vi.mocked(fetch).mock.calls.slice(-1)[0]
      const requestBody = JSON.parse(lastCall[1]?.body as string)
      
      // Should not exceed maximum context length
      expect(requestBody.messages.length).toBeLessThanOrEqual(20)
    })
  })
})