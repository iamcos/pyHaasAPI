import { describe, it, expect, beforeAll, afterAll, vi } from 'vitest'
import { mcpClient } from '../../services/mcpClient'

// Integration tests for MCP Server
// These tests require a running MCP server instance
describe('MCP Server Integration Tests', () => {
  let serverAvailable = false

  beforeAll(async () => {
    try {
      // Check if MCP server is available
      const response = await fetch('http://localhost:8080/health', {
        method: 'GET',
        timeout: 5000,
      })
      serverAvailable = response.ok
    } catch (error) {
      console.warn('MCP Server not available for integration tests')
      serverAvailable = false
    }
  })

  describe('Lab Management', () => {
    it('should fetch all labs', async () => {
      if (!serverAvailable) {
        console.log('Skipping test - MCP server not available')
        return
      }

      const labs = await mcpClient.labs.getAll()
      
      expect(Array.isArray(labs)).toBe(true)
      if (labs.length > 0) {
        expect(labs[0]).toHaveProperty('id')
        expect(labs[0]).toHaveProperty('name')
        expect(labs[0]).toHaveProperty('status')
      }
    })

    it('should create a new lab', async () => {
      if (!serverAvailable) {
        console.log('Skipping test - MCP server not available')
        return
      }

      const labConfig = {
        name: 'Integration Test Lab',
        script: 'Simple RSI Strategy',
        market: 'BTC/USD',
        parameters: {
          rsiPeriod: 14,
          overbought: 70,
          oversold: 30,
        },
      }

      const newLab = await mcpClient.labs.create(labConfig)
      
      expect(newLab).toHaveProperty('id')
      expect(newLab.name).toBe(labConfig.name)
      expect(newLab.status).toBe('created')

      // Clean up - delete the created lab
      await mcpClient.labs.delete(newLab.id)
    })

    it('should clone an existing lab', async () => {
      if (!serverAvailable) {
        console.log('Skipping test - MCP server not available')
        return
      }

      // First create a lab to clone
      const originalLab = await mcpClient.labs.create({
        name: 'Original Lab',
        script: 'Test Strategy',
        market: 'ETH/USD',
        parameters: { period: 20 },
      })

      const cloneConfig = {
        name: 'Cloned Lab',
        market: 'BTC/USD',
      }

      const clonedLab = await mcpClient.labs.clone(originalLab.id, cloneConfig)
      
      expect(clonedLab).toHaveProperty('id')
      expect(clonedLab.id).not.toBe(originalLab.id)
      expect(clonedLab.name).toBe(cloneConfig.name)
      expect(clonedLab.market).toBe(cloneConfig.market)

      // Clean up
      await mcpClient.labs.delete(originalLab.id)
      await mcpClient.labs.delete(clonedLab.id)
    })

    it('should run backtest on lab', async () => {
      if (!serverAvailable) {
        console.log('Skipping test - MCP server not available')
        return
      }

      // Create a lab for backtesting
      const lab = await mcpClient.labs.create({
        name: 'Backtest Lab',
        script: 'Simple MA Strategy',
        market: 'BTC/USD',
        parameters: { period: 10 },
      })

      const backtestConfig = {
        startDate: '2024-01-01',
        endDate: '2024-01-31',
        initialBalance: 10000,
      }

      const backtestResult = await mcpClient.labs.backtest(lab.id, backtestConfig)
      
      expect(backtestResult).toHaveProperty('id')
      expect(backtestResult).toHaveProperty('status')
      expect(backtestResult).toHaveProperty('results')

      // Clean up
      await mcpClient.labs.delete(lab.id)
    })
  })

  describe('Bot Management', () => {
    it('should fetch all bots', async () => {
      if (!serverAvailable) {
        console.log('Skipping test - MCP server not available')
        return
      }

      const bots = await mcpClient.bots.getAll()
      
      expect(Array.isArray(bots)).toBe(true)
      if (bots.length > 0) {
        expect(bots[0]).toHaveProperty('id')
        expect(bots[0]).toHaveProperty('name')
        expect(bots[0]).toHaveProperty('status')
      }
    })

    it('should create bot from lab', async () => {
      if (!serverAvailable) {
        console.log('Skipping test - MCP server not available')
        return
      }

      // First create a lab
      const lab = await mcpClient.labs.create({
        name: 'Bot Source Lab',
        script: 'Trading Strategy',
        market: 'BTC/USD',
        parameters: { period: 14 },
      })

      const botConfig = {
        name: 'Integration Test Bot',
        accountId: 'test-account',
        riskLevel: 'medium',
      }

      const bot = await mcpClient.bots.createFromLab(lab.id, botConfig)
      
      expect(bot).toHaveProperty('id')
      expect(bot.name).toBe(botConfig.name)
      expect(bot.status).toBe('created')

      // Clean up
      await mcpClient.bots.delete(bot.id)
      await mcpClient.labs.delete(lab.id)
    })

    it('should activate and deactivate bot', async () => {
      if (!serverAvailable) {
        console.log('Skipping test - MCP server not available')
        return
      }

      // Create lab and bot
      const lab = await mcpClient.labs.create({
        name: 'Activation Test Lab',
        script: 'Test Strategy',
        market: 'ETH/USD',
        parameters: {},
      })

      const bot = await mcpClient.bots.createFromLab(lab.id, {
        name: 'Activation Test Bot',
        accountId: 'test-account',
      })

      // Activate bot
      await mcpClient.bots.activate(bot.id)
      const activatedBot = await mcpClient.bots.getById(bot.id)
      expect(activatedBot.status).toBe('active')

      // Deactivate bot
      await mcpClient.bots.deactivate(bot.id)
      const deactivatedBot = await mcpClient.bots.getById(bot.id)
      expect(deactivatedBot.status).toBe('inactive')

      // Clean up
      await mcpClient.bots.delete(bot.id)
      await mcpClient.labs.delete(lab.id)
    })
  })

  describe('Market Data', () => {
    it('should fetch all markets', async () => {
      if (!serverAvailable) {
        console.log('Skipping test - MCP server not available')
        return
      }

      const markets = await mcpClient.markets.getAll()
      
      expect(Array.isArray(markets)).toBe(true)
      expect(markets.length).toBeGreaterThan(0)
      
      const market = markets[0]
      expect(market).toHaveProperty('id')
      expect(market).toHaveProperty('symbol')
      expect(market).toHaveProperty('exchange')
      expect(market).toHaveProperty('price')
    })

    it('should fetch price data for specific market', async () => {
      if (!serverAvailable) {
        console.log('Skipping test - MCP server not available')
        return
      }

      const markets = await mcpClient.markets.getAll()
      if (markets.length === 0) {
        console.log('No markets available for testing')
        return
      }

      const marketId = markets[0].id
      const priceData = await mcpClient.markets.getPriceData(marketId)
      
      expect(priceData).toHaveProperty('symbol')
      expect(priceData).toHaveProperty('price')
      expect(priceData).toHaveProperty('timestamp')
      expect(typeof priceData.price).toBe('number')
    })

    it('should fetch order book data', async () => {
      if (!serverAvailable) {
        console.log('Skipping test - MCP server not available')
        return
      }

      const markets = await mcpClient.markets.getAll()
      if (markets.length === 0) {
        console.log('No markets available for testing')
        return
      }

      const marketId = markets[0].id
      const orderBook = await mcpClient.markets.getOrderBook(marketId, 10)
      
      expect(orderBook).toHaveProperty('bids')
      expect(orderBook).toHaveProperty('asks')
      expect(Array.isArray(orderBook.bids)).toBe(true)
      expect(Array.isArray(orderBook.asks)).toBe(true)
      
      if (orderBook.bids.length > 0) {
        expect(orderBook.bids[0]).toHaveProperty('price')
        expect(orderBook.bids[0]).toHaveProperty('quantity')
      }
    })
  })

  describe('Account Management', () => {
    it('should fetch all accounts', async () => {
      if (!serverAvailable) {
        console.log('Skipping test - MCP server not available')
        return
      }

      const accounts = await mcpClient.accounts.getAll()
      
      expect(Array.isArray(accounts)).toBe(true)
      if (accounts.length > 0) {
        expect(accounts[0]).toHaveProperty('id')
        expect(accounts[0]).toHaveProperty('name')
        expect(accounts[0]).toHaveProperty('exchange')
      }
    })

    it('should get account balance', async () => {
      if (!serverAvailable) {
        console.log('Skipping test - MCP server not available')
        return
      }

      const accounts = await mcpClient.accounts.getAll()
      if (accounts.length === 0) {
        console.log('No accounts available for testing')
        return
      }

      const accountId = accounts[0].id
      const balance = await mcpClient.accounts.getBalance(accountId)
      
      expect(balance).toHaveProperty('total')
      expect(balance).toHaveProperty('available')
      expect(balance).toHaveProperty('currency')
      expect(typeof balance.total).toBe('number')
    })

    it('should create simulated account', async () => {
      if (!serverAvailable) {
        console.log('Skipping test - MCP server not available')
        return
      }

      const accountConfig = {
        name: 'Integration Test Account',
        exchange: 'Binance',
        type: 'simulated',
        initialBalance: 10000,
        currency: 'USD',
      }

      const account = await mcpClient.accounts.createSimulated(accountConfig)
      
      expect(account).toHaveProperty('id')
      expect(account.name).toBe(accountConfig.name)
      expect(account.type).toBe('simulated')

      // Clean up
      await mcpClient.accounts.delete(account.id)
    })
  })

  describe('Error Handling', () => {
    it('should handle invalid lab ID gracefully', async () => {
      if (!serverAvailable) {
        console.log('Skipping test - MCP server not available')
        return
      }

      await expect(mcpClient.labs.getById('invalid-lab-id'))
        .rejects.toThrow('Lab not found')
    })

    it('should handle network timeouts', async () => {
      if (!serverAvailable) {
        console.log('Skipping test - MCP server not available')
        return
      }

      // Mock a slow request
      const originalTimeout = mcpClient.timeout
      mcpClient.timeout = 100 // Very short timeout

      await expect(mcpClient.markets.getAll())
        .rejects.toThrow(/timeout/i)

      // Restore original timeout
      mcpClient.timeout = originalTimeout
    })

    it('should retry failed requests', async () => {
      if (!serverAvailable) {
        console.log('Skipping test - MCP server not available')
        return
      }

      // Mock intermittent failures
      let callCount = 0
      const originalFetch = global.fetch
      global.fetch = vi.fn().mockImplementation((...args) => {
        callCount++
        if (callCount < 3) {
          return Promise.reject(new Error('Network error'))
        }
        return originalFetch(...args)
      })

      const markets = await mcpClient.markets.getAll()
      expect(Array.isArray(markets)).toBe(true)
      expect(callCount).toBe(3) // Should have retried twice

      // Restore original fetch
      global.fetch = originalFetch
    })
  })

  describe('Performance', () => {
    it('should handle concurrent requests efficiently', async () => {
      if (!serverAvailable) {
        console.log('Skipping test - MCP server not available')
        return
      }

      const startTime = Date.now()
      
      // Make 10 concurrent requests
      const promises = Array.from({ length: 10 }, () => 
        mcpClient.markets.getAll()
      )

      const results = await Promise.all(promises)
      const endTime = Date.now()
      const duration = endTime - startTime

      // All requests should succeed
      results.forEach(markets => {
        expect(Array.isArray(markets)).toBe(true)
      })

      // Should complete within reasonable time (adjust based on server performance)
      expect(duration).toBeLessThan(10000) // 10 seconds
    })

    it('should cache frequently requested data', async () => {
      if (!serverAvailable) {
        console.log('Skipping test - MCP server not available')
        return
      }

      // First request
      const startTime1 = Date.now()
      const markets1 = await mcpClient.markets.getAll()
      const duration1 = Date.now() - startTime1

      // Second request (should be cached)
      const startTime2 = Date.now()
      const markets2 = await mcpClient.markets.getAll()
      const duration2 = Date.now() - startTime2

      expect(markets1).toEqual(markets2)
      expect(duration2).toBeLessThan(duration1) // Cached request should be faster
    })
  })
})