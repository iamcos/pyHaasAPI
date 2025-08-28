import { describe, it, expect, beforeAll, afterAll, vi } from 'vitest'
import { websocketService } from '../../services/websocketService'

// Integration tests for WebSocket real-time data flow
describe('WebSocket Integration Tests', () => {
  let wsAvailable = false
  let testConnection: any

  beforeAll(async () => {
    try {
      // Check if WebSocket server is available
      testConnection = new WebSocket('ws://localhost:8082/ws')
      
      await new Promise((resolve, reject) => {
        const timeout = setTimeout(() => {
          reject(new Error('WebSocket connection timeout'))
        }, 5000)

        testConnection.onopen = () => {
          clearTimeout(timeout)
          wsAvailable = true
          resolve(true)
        }

        testConnection.onerror = () => {
          clearTimeout(timeout)
          wsAvailable = false
          reject(new Error('WebSocket connection failed'))
        }
      })
    } catch (error) {
      console.warn('WebSocket server not available for integration tests')
      wsAvailable = false
    }
  })

  afterAll(async () => {
    if (testConnection && testConnection.readyState === WebSocket.OPEN) {
      testConnection.close()
    }
    
    if (wsAvailable) {
      await websocketService.disconnect()
    }
  })

  describe('Connection Management', () => {
    it('should establish WebSocket connection', async () => {
      if (!wsAvailable) {
        console.log('Skipping test - WebSocket server not available')
        return
      }

      const connected = await websocketService.connect('ws://localhost:8082/ws')
      expect(connected).toBe(true)
      expect(websocketService.isConnected()).toBe(true)
    })

    it('should handle connection failures gracefully', async () => {
      if (!wsAvailable) {
        console.log('Skipping test - WebSocket server not available')
        return
      }

      // Try to connect to invalid endpoint
      const connected = await websocketService.connect('ws://localhost:9999/invalid')
      expect(connected).toBe(false)
    })

    it('should reconnect automatically after disconnection', async () => {
      if (!wsAvailable) {
        console.log('Skipping test - WebSocket server not available')
        return
      }

      await websocketService.connect('ws://localhost:8082/ws')
      expect(websocketService.isConnected()).toBe(true)

      // Simulate disconnection
      websocketService.disconnect()
      expect(websocketService.isConnected()).toBe(false)

      // Wait for automatic reconnection
      await new Promise(resolve => setTimeout(resolve, 2000))
      expect(websocketService.isConnected()).toBe(true)
    })

    it('should maintain connection pool for multiple subscriptions', async () => {
      if (!wsAvailable) {
        console.log('Skipping test - WebSocket server not available')
        return
      }

      const connections = await Promise.all([
        websocketService.connect('ws://localhost:8082/market-data'),
        websocketService.connect('ws://localhost:8082/trade-updates'),
        websocketService.connect('ws://localhost:8082/account-updates'),
      ])

      expect(connections.every(c => c === true)).toBe(true)
      expect(websocketService.getActiveConnections()).toBe(3)
    })
  })

  describe('Real-time Market Data', () => {
    it('should receive real-time price updates', async () => {
      if (!wsAvailable) {
        console.log('Skipping test - WebSocket server not available')
        return
      }

      await websocketService.connect('ws://localhost:8082/market-data')

      const priceUpdates: any[] = []
      const unsubscribe = websocketService.subscribe('price-update', (data) => {
        priceUpdates.push(data)
      })

      // Subscribe to BTC/USD price updates
      await websocketService.send({
        type: 'subscribe',
        channel: 'price',
        symbol: 'BTC/USD',
      })

      // Wait for price updates
      await new Promise(resolve => setTimeout(resolve, 3000))

      expect(priceUpdates.length).toBeGreaterThan(0)
      
      const priceUpdate = priceUpdates[0]
      expect(priceUpdate).toHaveProperty('symbol')
      expect(priceUpdate).toHaveProperty('price')
      expect(priceUpdate).toHaveProperty('timestamp')
      expect(priceUpdate.symbol).toBe('BTC/USD')
      expect(typeof priceUpdate.price).toBe('number')

      unsubscribe()
    })

    it('should receive order book updates', async () => {
      if (!wsAvailable) {
        console.log('Skipping test - WebSocket server not available')
        return
      }

      const orderBookUpdates: any[] = []
      const unsubscribe = websocketService.subscribe('orderbook-update', (data) => {
        orderBookUpdates.push(data)
      })

      await websocketService.send({
        type: 'subscribe',
        channel: 'orderbook',
        symbol: 'ETH/USD',
        depth: 10,
      })

      await new Promise(resolve => setTimeout(resolve, 2000))

      expect(orderBookUpdates.length).toBeGreaterThan(0)
      
      const orderBookUpdate = orderBookUpdates[0]
      expect(orderBookUpdate).toHaveProperty('symbol')
      expect(orderBookUpdate).toHaveProperty('bids')
      expect(orderBookUpdate).toHaveProperty('asks')
      expect(Array.isArray(orderBookUpdate.bids)).toBe(true)
      expect(Array.isArray(orderBookUpdate.asks)).toBe(true)

      unsubscribe()
    })

    it('should receive trade execution updates', async () => {
      if (!wsAvailable) {
        console.log('Skipping test - WebSocket server not available')
        return
      }

      const tradeUpdates: any[] = []
      const unsubscribe = websocketService.subscribe('trade-update', (data) => {
        tradeUpdates.push(data)
      })

      await websocketService.send({
        type: 'subscribe',
        channel: 'trades',
        symbol: 'BTC/USD',
      })

      await new Promise(resolve => setTimeout(resolve, 2000))

      expect(tradeUpdates.length).toBeGreaterThan(0)
      
      const tradeUpdate = tradeUpdates[0]
      expect(tradeUpdate).toHaveProperty('symbol')
      expect(tradeUpdate).toHaveProperty('price')
      expect(tradeUpdate).toHaveProperty('quantity')
      expect(tradeUpdate).toHaveProperty('side')
      expect(tradeUpdate).toHaveProperty('timestamp')

      unsubscribe()
    })
  })

  describe('Bot Status Updates', () => {
    it('should receive bot status changes', async () => {
      if (!wsAvailable) {
        console.log('Skipping test - WebSocket server not available')
        return
      }

      const botUpdates: any[] = []
      const unsubscribe = websocketService.subscribe('bot-status', (data) => {
        botUpdates.push(data)
      })

      await websocketService.send({
        type: 'subscribe',
        channel: 'bot-status',
        botId: 'test-bot-1',
      })

      // Simulate bot status change
      await websocketService.send({
        type: 'bot-action',
        action: 'activate',
        botId: 'test-bot-1',
      })

      await new Promise(resolve => setTimeout(resolve, 1000))

      expect(botUpdates.length).toBeGreaterThan(0)
      
      const statusUpdate = botUpdates[0]
      expect(statusUpdate).toHaveProperty('botId')
      expect(statusUpdate).toHaveProperty('status')
      expect(statusUpdate).toHaveProperty('timestamp')
      expect(statusUpdate.botId).toBe('test-bot-1')

      unsubscribe()
    })

    it('should receive bot performance metrics', async () => {
      if (!wsAvailable) {
        console.log('Skipping test - WebSocket server not available')
        return
      }

      const performanceUpdates: any[] = []
      const unsubscribe = websocketService.subscribe('bot-performance', (data) => {
        performanceUpdates.push(data)
      })

      await websocketService.send({
        type: 'subscribe',
        channel: 'bot-performance',
        botId: 'test-bot-1',
      })

      await new Promise(resolve => setTimeout(resolve, 2000))

      expect(performanceUpdates.length).toBeGreaterThan(0)
      
      const performanceUpdate = performanceUpdates[0]
      expect(performanceUpdate).toHaveProperty('botId')
      expect(performanceUpdate).toHaveProperty('pnl')
      expect(performanceUpdate).toHaveProperty('trades')
      expect(performanceUpdate).toHaveProperty('winRate')
      expect(typeof performanceUpdate.pnl).toBe('number')

      unsubscribe()
    })
  })

  describe('Account Updates', () => {
    it('should receive balance updates', async () => {
      if (!wsAvailable) {
        console.log('Skipping test - WebSocket server not available')
        return
      }

      const balanceUpdates: any[] = []
      const unsubscribe = websocketService.subscribe('balance-update', (data) => {
        balanceUpdates.push(data)
      })

      await websocketService.send({
        type: 'subscribe',
        channel: 'account-balance',
        accountId: 'test-account-1',
      })

      await new Promise(resolve => setTimeout(resolve, 2000))

      expect(balanceUpdates.length).toBeGreaterThan(0)
      
      const balanceUpdate = balanceUpdates[0]
      expect(balanceUpdate).toHaveProperty('accountId')
      expect(balanceUpdate).toHaveProperty('currency')
      expect(balanceUpdate).toHaveProperty('balance')
      expect(balanceUpdate).toHaveProperty('available')
      expect(typeof balanceUpdate.balance).toBe('number')

      unsubscribe()
    })

    it('should receive position updates', async () => {
      if (!wsAvailable) {
        console.log('Skipping test - WebSocket server not available')
        return
      }

      const positionUpdates: any[] = []
      const unsubscribe = websocketService.subscribe('position-update', (data) => {
        positionUpdates.push(data)
      })

      await websocketService.send({
        type: 'subscribe',
        channel: 'positions',
        accountId: 'test-account-1',
      })

      await new Promise(resolve => setTimeout(resolve, 2000))

      if (positionUpdates.length > 0) {
        const positionUpdate = positionUpdates[0]
        expect(positionUpdate).toHaveProperty('accountId')
        expect(positionUpdate).toHaveProperty('symbol')
        expect(positionUpdate).toHaveProperty('quantity')
        expect(positionUpdate).toHaveProperty('averagePrice')
      }

      unsubscribe()
    })
  })

  describe('Data Synchronization', () => {
    it('should handle message ordering correctly', async () => {
      if (!wsAvailable) {
        console.log('Skipping test - WebSocket server not available')
        return
      }

      const messages: any[] = []
      const unsubscribe = websocketService.subscribe('test-ordering', (data) => {
        messages.push(data)
      })

      // Send multiple messages with sequence numbers
      for (let i = 1; i <= 10; i++) {
        await websocketService.send({
          type: 'test-message',
          sequence: i,
          data: `Message ${i}`,
        })
      }

      await new Promise(resolve => setTimeout(resolve, 1000))

      // Messages should be received in order
      expect(messages.length).toBe(10)
      for (let i = 0; i < 10; i++) {
        expect(messages[i].sequence).toBe(i + 1)
      }

      unsubscribe()
    })

    it('should handle duplicate message filtering', async () => {
      if (!wsAvailable) {
        console.log('Skipping test - WebSocket server not available')
        return
      }

      const uniqueMessages: any[] = []
      const unsubscribe = websocketService.subscribe('test-duplicates', (data) => {
        uniqueMessages.push(data)
      })

      // Send duplicate messages
      const message = {
        type: 'test-message',
        id: 'unique-message-1',
        data: 'Test data',
      }

      await websocketService.send(message)
      await websocketService.send(message) // Duplicate
      await websocketService.send(message) // Duplicate

      await new Promise(resolve => setTimeout(resolve, 500))

      // Should only receive one message
      expect(uniqueMessages.length).toBe(1)
      expect(uniqueMessages[0].id).toBe('unique-message-1')

      unsubscribe()
    })

    it('should handle message buffering during disconnection', async () => {
      if (!wsAvailable) {
        console.log('Skipping test - WebSocket server not available')
        return
      }

      const bufferedMessages: any[] = []
      const unsubscribe = websocketService.subscribe('test-buffering', (data) => {
        bufferedMessages.push(data)
      })

      // Disconnect temporarily
      websocketService.disconnect()

      // Send messages while disconnected (should be buffered)
      await websocketService.send({ type: 'buffered-message-1' })
      await websocketService.send({ type: 'buffered-message-2' })

      // Reconnect
      await websocketService.connect('ws://localhost:8082/ws')

      await new Promise(resolve => setTimeout(resolve, 1000))

      // Buffered messages should be sent after reconnection
      expect(bufferedMessages.length).toBe(2)

      unsubscribe()
    })
  })

  describe('Performance and Load Testing', () => {
    it('should handle high-frequency updates efficiently', async () => {
      if (!wsAvailable) {
        console.log('Skipping test - WebSocket server not available')
        return
      }

      const updates: any[] = []
      const startTime = Date.now()
      
      const unsubscribe = websocketService.subscribe('high-frequency', (data) => {
        updates.push(data)
      })

      // Subscribe to high-frequency price updates
      await websocketService.send({
        type: 'subscribe',
        channel: 'high-frequency-prices',
        symbols: ['BTC/USD', 'ETH/USD', 'ADA/USD', 'DOT/USD'],
        interval: 100, // 100ms updates
      })

      // Collect updates for 5 seconds
      await new Promise(resolve => setTimeout(resolve, 5000))
      
      const endTime = Date.now()
      const duration = endTime - startTime

      expect(updates.length).toBeGreaterThan(40) // At least 40 updates in 5 seconds
      
      // Check for reasonable update frequency
      const updatesPerSecond = updates.length / (duration / 1000)
      expect(updatesPerSecond).toBeGreaterThan(8) // At least 8 updates per second

      unsubscribe()
    })

    it('should maintain low latency for critical updates', async () => {
      if (!wsAvailable) {
        console.log('Skipping test - WebSocket server not available')
        return
      }

      const latencies: number[] = []
      
      const unsubscribe = websocketService.subscribe('latency-test', (data) => {
        const receiveTime = Date.now()
        const sendTime = data.timestamp
        const latency = receiveTime - sendTime
        latencies.push(latency)
      })

      // Send timestamped messages
      for (let i = 0; i < 10; i++) {
        await websocketService.send({
          type: 'latency-test',
          timestamp: Date.now(),
        })
        await new Promise(resolve => setTimeout(resolve, 100))
      }

      await new Promise(resolve => setTimeout(resolve, 1000))

      expect(latencies.length).toBeGreaterThan(0)
      
      const averageLatency = latencies.reduce((a, b) => a + b, 0) / latencies.length
      expect(averageLatency).toBeLessThan(100) // Less than 100ms average latency

      unsubscribe()
    })

    it('should handle concurrent subscriptions efficiently', async () => {
      if (!wsAvailable) {
        console.log('Skipping test - WebSocket server not available')
        return
      }

      const subscriptions = []
      const updateCounts: number[] = []

      // Create 20 concurrent subscriptions
      for (let i = 0; i < 20; i++) {
        let count = 0
        const unsubscribe = websocketService.subscribe(`concurrent-${i}`, () => {
          count++
        })
        
        subscriptions.push(unsubscribe)
        updateCounts.push(count)

        await websocketService.send({
          type: 'subscribe',
          channel: `test-channel-${i}`,
        })
      }

      await new Promise(resolve => setTimeout(resolve, 2000))

      // All subscriptions should receive updates
      expect(updateCounts.every(count => count > 0)).toBe(true)

      // Clean up subscriptions
      subscriptions.forEach(unsubscribe => unsubscribe())
    })
  })

  describe('Error Handling and Recovery', () => {
    it('should handle malformed messages gracefully', async () => {
      if (!wsAvailable) {
        console.log('Skipping test - WebSocket server not available')
        return
      }

      const errors: any[] = []
      const unsubscribe = websocketService.subscribe('error', (error) => {
        errors.push(error)
      })

      // Send malformed message
      const malformedMessage = '{"invalid": json syntax'
      await websocketService.sendRaw(malformedMessage)

      await new Promise(resolve => setTimeout(resolve, 500))

      expect(errors.length).toBeGreaterThan(0)
      expect(errors[0]).toHaveProperty('type', 'parse_error')

      unsubscribe()
    })

    it('should recover from server disconnections', async () => {
      if (!wsAvailable) {
        console.log('Skipping test - WebSocket server not available')
        return
      }

      let reconnectCount = 0
      const unsubscribe = websocketService.subscribe('reconnect', () => {
        reconnectCount++
      })

      // Simulate server disconnection
      websocketService.simulateDisconnection()

      // Wait for automatic reconnection
      await new Promise(resolve => setTimeout(resolve, 3000))

      expect(websocketService.isConnected()).toBe(true)
      expect(reconnectCount).toBeGreaterThan(0)

      unsubscribe()
    })

    it('should handle subscription failures gracefully', async () => {
      if (!wsAvailable) {
        console.log('Skipping test - WebSocket server not available')
        return
      }

      const subscriptionErrors: any[] = []
      const unsubscribe = websocketService.subscribe('subscription-error', (error) => {
        subscriptionErrors.push(error)
      })

      // Try to subscribe to invalid channel
      await websocketService.send({
        type: 'subscribe',
        channel: 'invalid-channel-name',
      })

      await new Promise(resolve => setTimeout(resolve, 500))

      expect(subscriptionErrors.length).toBeGreaterThan(0)
      expect(subscriptionErrors[0]).toHaveProperty('type', 'subscription_error')

      unsubscribe()
    })
  })
})