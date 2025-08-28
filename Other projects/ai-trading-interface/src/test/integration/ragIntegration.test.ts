import { describe, it, expect, beforeAll, afterAll, vi } from 'vitest'
import { ragClient } from '../../services/ragClient'

// Integration tests for HaasScript RAG system with MongoDB
describe('RAG System Integration Tests', () => {
  let ragAvailable = false
  const testProjectId = 'integration-test-project'

  beforeAll(async () => {
    try {
      // Check if RAG service is available
      const response = await fetch('http://localhost:8081/health', {
        method: 'GET',
        timeout: 5000,
      })
      ragAvailable = response.ok

      if (ragAvailable) {
        // Clean up any existing test data
        await ragClient.clearProject(testProjectId)
      }
    } catch (error) {
      console.warn('RAG Service not available for integration tests')
      ragAvailable = false
    }
  })

  afterAll(async () => {
    if (ragAvailable) {
      // Clean up test data
      await ragClient.clearProject(testProjectId)
    }
  })

  describe('Memory Management', () => {
    it('should add trading memory to project', async () => {
      if (!ragAvailable) {
        console.log('Skipping test - RAG service not available')
        return
      }

      const memory = {
        type: 'strategy_analysis',
        content: 'RSI strategy with 14-period lookback shows good performance on BTC/USD',
        metadata: {
          strategy: 'RSI',
          market: 'BTC/USD',
          performance: {
            winRate: 0.65,
            sharpeRatio: 1.8,
            maxDrawdown: 0.12,
          },
          timestamp: new Date().toISOString(),
        },
        tags: ['RSI', 'BTC', 'strategy', 'analysis'],
      }

      await ragClient.addMemory(testProjectId, memory)

      // Verify memory was added by searching for it
      const searchResults = await ragClient.searchMemories(testProjectId, 'RSI strategy')
      
      expect(searchResults.length).toBeGreaterThan(0)
      const foundMemory = searchResults.find(m => m.content.includes('14-period'))
      expect(foundMemory).toBeDefined()
      expect(foundMemory?.metadata.strategy).toBe('RSI')
    })

    it('should search memories by content', async () => {
      if (!ragAvailable) {
        console.log('Skipping test - RAG service not available')
        return
      }

      // Add multiple memories
      const memories = [
        {
          type: 'strategy_analysis',
          content: 'Moving Average crossover strategy works well in trending markets',
          metadata: { strategy: 'MA_Crossover', market: 'ETH/USD' },
          tags: ['MA', 'crossover', 'trending'],
        },
        {
          type: 'market_insight',
          content: 'Bitcoin shows strong correlation with traditional markets during volatility',
          metadata: { asset: 'BTC', correlation: 0.8 },
          tags: ['BTC', 'correlation', 'volatility'],
        },
        {
          type: 'risk_analysis',
          content: 'High frequency strategies require careful position sizing',
          metadata: { strategy_type: 'HFT', risk_level: 'high' },
          tags: ['HFT', 'risk', 'position_sizing'],
        },
      ]

      for (const memory of memories) {
        await ragClient.addMemory(testProjectId, memory)
      }

      // Search for specific content
      const maResults = await ragClient.searchMemories(testProjectId, 'Moving Average')
      expect(maResults.length).toBeGreaterThan(0)
      expect(maResults[0].content).toContain('Moving Average')

      const btcResults = await ragClient.searchMemories(testProjectId, 'Bitcoin correlation')
      expect(btcResults.length).toBeGreaterThan(0)
      expect(btcResults[0].content).toContain('Bitcoin')

      const riskResults = await ragClient.searchMemories(testProjectId, 'position sizing')
      expect(riskResults.length).toBeGreaterThan(0)
      expect(riskResults[0].content).toContain('position sizing')
    })

    it('should search memories by tags', async () => {
      if (!ragAvailable) {
        console.log('Skipping test - RAG service not available')
        return
      }

      const tagResults = await ragClient.searchMemoriesByTags(testProjectId, ['BTC'])
      expect(tagResults.length).toBeGreaterThan(0)
      
      const btcMemory = tagResults.find(m => m.tags.includes('BTC'))
      expect(btcMemory).toBeDefined()
    })

    it('should search memories by metadata', async () => {
      if (!ragAvailable) {
        console.log('Skipping test - RAG service not available')
        return
      }

      const metadataResults = await ragClient.searchMemoriesByMetadata(testProjectId, {
        strategy: 'RSI'
      })
      
      expect(metadataResults.length).toBeGreaterThan(0)
      expect(metadataResults[0].metadata.strategy).toBe('RSI')
    })
  })

  describe('Script Intelligence', () => {
    it('should analyze HaasScript code', async () => {
      if (!ragAvailable) {
        console.log('Skipping test - RAG service not available')
        return
      }

      const haasScript = `
        var rsiPeriod = 14;
        var overbought = 70;
        var oversold = 30;
        
        var rsi = RSI(Close, rsiPeriod);
        
        if (rsi < oversold) {
          Buy();
        } else if (rsi > overbought) {
          Sell();
        }
      `

      const analysis = await ragClient.analyzeScript(haasScript)
      
      expect(analysis).toHaveProperty('indicators')
      expect(analysis).toHaveProperty('signals')
      expect(analysis).toHaveProperty('complexity')
      expect(analysis).toHaveProperty('suggestions')
      
      expect(analysis.indicators).toContain('RSI')
      expect(analysis.signals.length).toBeGreaterThan(0)
      expect(typeof analysis.complexity).toBe('number')
    })

    it('should suggest script improvements', async () => {
      if (!ragAvailable) {
        console.log('Skipping test - RAG service not available')
        return
      }

      const basicScript = `
        var ma = MA(Close, 20);
        if (Close > ma) {
          Buy();
        } else {
          Sell();
        }
      `

      const performanceData = {
        winRate: 0.45,
        sharpeRatio: 0.8,
        maxDrawdown: 0.25,
        totalTrades: 100,
      }

      const improvements = await ragClient.suggestImprovements(basicScript, performanceData)
      
      expect(Array.isArray(improvements)).toBe(true)
      expect(improvements.length).toBeGreaterThan(0)
      
      const improvement = improvements[0]
      expect(improvement).toHaveProperty('type')
      expect(improvement).toHaveProperty('description')
      expect(improvement).toHaveProperty('priority')
      expect(improvement).toHaveProperty('expectedImpact')
    })

    it('should translate external strategies to HaasScript', async () => {
      if (!ragAvailable) {
        console.log('Skipping test - RAG service not available')
        return
      }

      const pineScript = `
        //@version=5
        indicator("Simple RSI", overlay=false)
        
        length = input.int(14, title="RSI Length")
        src = input(close, title="Source")
        
        rsi_value = ta.rsi(src, length)
        
        plot(rsi_value, title="RSI", color=color.blue)
        hline(70, "Overbought", color=color.red)
        hline(30, "Oversold", color=color.green)
      `

      const externalStrategy = {
        type: 'pine_script',
        code: pineScript,
        description: 'Simple RSI indicator with overbought/oversold levels',
      }

      const translation = await ragClient.translateStrategy(externalStrategy, 'haasscript')
      
      expect(translation).toHaveProperty('haasScript')
      expect(translation).toHaveProperty('parameters')
      expect(translation).toHaveProperty('explanation')
      expect(translation).toHaveProperty('confidence')
      
      expect(translation.haasScript).toContain('RSI')
      expect(translation.parameters.length).toBeGreaterThan(0)
      expect(translation.confidence).toBeGreaterThan(0.5)
    })
  })

  describe('Knowledge Retrieval', () => {
    it('should retrieve relevant context for strategy development', async () => {
      if (!ragAvailable) {
        console.log('Skipping test - RAG service not available')
        return
      }

      const query = 'How to implement a momentum strategy for cryptocurrency trading?'
      
      const context = await ragClient.getRelevantContext(testProjectId, query)
      
      expect(context).toHaveProperty('memories')
      expect(context).toHaveProperty('suggestions')
      expect(context).toHaveProperty('relevanceScore')
      
      expect(Array.isArray(context.memories)).toBe(true)
      expect(Array.isArray(context.suggestions)).toBe(true)
      expect(typeof context.relevanceScore).toBe('number')
    })

    it('should provide strategy recommendations based on market conditions', async () => {
      if (!ragAvailable) {
        console.log('Skipping test - RAG service not available')
        return
      }

      const marketConditions = {
        volatility: 'high',
        trend: 'bullish',
        volume: 'above_average',
        market: 'BTC/USD',
      }

      const recommendations = await ragClient.getStrategyRecommendations(
        testProjectId, 
        marketConditions
      )
      
      expect(Array.isArray(recommendations)).toBe(true)
      expect(recommendations.length).toBeGreaterThan(0)
      
      const recommendation = recommendations[0]
      expect(recommendation).toHaveProperty('strategy')
      expect(recommendation).toHaveProperty('confidence')
      expect(recommendation).toHaveProperty('reasoning')
      expect(recommendation).toHaveProperty('parameters')
    })

    it('should learn from trading performance feedback', async () => {
      if (!ragAvailable) {
        console.log('Skipping test - RAG service not available')
        return
      }

      const performanceFeedback = {
        strategyId: 'rsi-strategy-1',
        period: '2024-01-01 to 2024-01-31',
        metrics: {
          totalReturn: 0.15,
          sharpeRatio: 1.8,
          maxDrawdown: 0.08,
          winRate: 0.68,
          totalTrades: 45,
        },
        marketConditions: {
          volatility: 'medium',
          trend: 'sideways',
          market: 'BTC/USD',
        },
        notes: 'Strategy performed well in sideways market conditions',
      }

      await ragClient.addPerformanceFeedback(testProjectId, performanceFeedback)
      
      // Verify the feedback was stored and can be retrieved
      const searchResults = await ragClient.searchMemories(testProjectId, 'sideways market')
      expect(searchResults.length).toBeGreaterThan(0)
      
      const feedbackMemory = searchResults.find(m => 
        m.content.includes('performed well in sideways')
      )
      expect(feedbackMemory).toBeDefined()
    })
  })

  describe('Vector Search and Similarity', () => {
    it('should find similar strategies', async () => {
      if (!ragAvailable) {
        console.log('Skipping test - RAG service not available')
        return
      }

      const targetStrategy = {
        description: 'RSI-based mean reversion strategy with dynamic thresholds',
        parameters: {
          rsiPeriod: 14,
          overboughtThreshold: 70,
          oversoldThreshold: 30,
        },
        market: 'BTC/USD',
      }

      const similarStrategies = await ragClient.findSimilarStrategies(
        testProjectId, 
        targetStrategy
      )
      
      expect(Array.isArray(similarStrategies)).toBe(true)
      if (similarStrategies.length > 0) {
        const similar = similarStrategies[0]
        expect(similar).toHaveProperty('strategy')
        expect(similar).toHaveProperty('similarity')
        expect(similar).toHaveProperty('commonFeatures')
        expect(similar.similarity).toBeGreaterThan(0)
        expect(similar.similarity).toBeLessThanOrEqual(1)
      }
    })

    it('should cluster related trading concepts', async () => {
      if (!ragAvailable) {
        console.log('Skipping test - RAG service not available')
        return
      }

      const concepts = await ragClient.getConceptClusters(testProjectId)
      
      expect(Array.isArray(concepts)).toBe(true)
      if (concepts.length > 0) {
        const cluster = concepts[0]
        expect(cluster).toHaveProperty('name')
        expect(cluster).toHaveProperty('memories')
        expect(cluster).toHaveProperty('centroid')
        expect(Array.isArray(cluster.memories)).toBe(true)
      }
    })
  })

  describe('Performance and Scalability', () => {
    it('should handle large memory datasets efficiently', async () => {
      if (!ragAvailable) {
        console.log('Skipping test - RAG service not available')
        return
      }

      const startTime = Date.now()
      
      // Add many memories
      const memories = Array.from({ length: 100 }, (_, i) => ({
        type: 'performance_test',
        content: `Test memory ${i} with trading insights and market analysis`,
        metadata: { index: i, category: `category_${i % 10}` },
        tags: [`tag_${i % 5}`, 'performance_test'],
      }))

      await Promise.all(
        memories.map(memory => ragClient.addMemory(testProjectId, memory))
      )

      const addTime = Date.now() - startTime

      // Search through the large dataset
      const searchStartTime = Date.now()
      const results = await ragClient.searchMemories(testProjectId, 'trading insights')
      const searchTime = Date.now() - searchStartTime

      expect(results.length).toBeGreaterThan(0)
      expect(addTime).toBeLessThan(30000) // 30 seconds for 100 memories
      expect(searchTime).toBeLessThan(5000) // 5 seconds for search
    })

    it('should maintain search accuracy with diverse content', async () => {
      if (!ragAvailable) {
        console.log('Skipping test - RAG service not available')
        return
      }

      // Search for specific content that should have high relevance
      const preciseResults = await ragClient.searchMemories(
        testProjectId, 
        'RSI strategy 14-period BTC/USD'
      )
      
      expect(preciseResults.length).toBeGreaterThan(0)
      
      // The most relevant result should be the RSI strategy we added earlier
      const topResult = preciseResults[0]
      expect(topResult.content).toContain('RSI')
      expect(topResult.content).toContain('14-period')
    })
  })

  describe('Error Handling and Resilience', () => {
    it('should handle invalid project IDs gracefully', async () => {
      if (!ragAvailable) {
        console.log('Skipping test - RAG service not available')
        return
      }

      await expect(ragClient.searchMemories('invalid-project-id', 'test'))
        .rejects.toThrow('Project not found')
    })

    it('should handle malformed memory data', async () => {
      if (!ragAvailable) {
        console.log('Skipping test - RAG service not available')
        return
      }

      const invalidMemory = {
        // Missing required fields
        content: null,
        metadata: 'invalid-metadata-format',
      }

      await expect(ragClient.addMemory(testProjectId, invalidMemory as any))
        .rejects.toThrow('Invalid memory format')
    })

    it('should recover from temporary database connection issues', async () => {
      if (!ragAvailable) {
        console.log('Skipping test - RAG service not available')
        return
      }

      // Mock temporary connection failure
      const originalFetch = global.fetch
      let callCount = 0
      
      global.fetch = vi.fn().mockImplementation((...args) => {
        callCount++
        if (callCount === 1) {
          return Promise.reject(new Error('Connection timeout'))
        }
        return originalFetch(...args)
      })

      // Should retry and succeed
      const results = await ragClient.searchMemories(testProjectId, 'test')
      expect(Array.isArray(results)).toBe(true)
      expect(callCount).toBe(2)

      // Restore original fetch
      global.fetch = originalFetch
    })
  })
})