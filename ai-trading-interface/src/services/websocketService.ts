import { useTradingStore } from '@/stores/tradingStore'
import type { Market, Position, Bot, MarketDataSubscription, OrderBook, PriceData } from '@/types'

// Enhanced WebSocket message types
interface WSMessage {
  type: 'price_update' | 'bot_status' | 'position_update' | 'trade_executed' | 'system_alert' | 
        'orderbook_update' | 'market_stats' | 'connection_status' | 'subscription_confirmed' | 
        'subscription_error' | 'heartbeat' | 'error'
  data: any
  timestamp: string
  id?: string
  channel?: string
}

interface PriceUpdateData {
  symbol: string
  price: number
  volume: number
  change24h: number
  high24h: number
  low24h: number
  timestamp: string
}

interface BotStatusData {
  botId: string
  status: 'active' | 'inactive' | 'paused' | 'error'
  lastUpdate: string
  performance?: {
    totalReturn: number
    unrealizedPnl: number
    totalTrades: number
  }
}

interface PositionUpdateData {
  symbol: string
  side: 'long' | 'short'
  quantity: number
  entryPrice: number
  currentPrice: number
  unrealizedPnl: number
}

interface TradeExecutedData {
  botId: string
  symbol: string
  side: 'buy' | 'sell'
  quantity: number
  price: number
  timestamp: string
}

interface SystemAlertData {
  level: 'info' | 'warning' | 'error' | 'critical'
  message: string
  source: string
}

interface OrderBookUpdateData {
  symbol: string
  bids: Array<{ price: number; quantity: number }>
  asks: Array<{ price: number; quantity: number }>
  timestamp: string
}

interface MarketStatsData {
  totalVolume24h: number
  marketCount: number
  topGainers: Array<{ symbol: string; change: number }>
  topLosers: Array<{ symbol: string; change: number }>
  timestamp: string
}

// Enhanced WebSocket configuration
interface WSConfig {
  url: string
  reconnectInterval: number
  maxReconnectAttempts: number
  heartbeatInterval: number
  connectionTimeout: number
  maxMessageQueueSize: number
  enableCompression: boolean
  protocols?: string[]
}

const defaultConfig: WSConfig = {
  url: 'ws://localhost:8000/ws',
  reconnectInterval: 5000, // 5 seconds
  maxReconnectAttempts: 10,
  heartbeatInterval: 30000, // 30 seconds
  connectionTimeout: 10000, // 10 seconds
  maxMessageQueueSize: 1000,
  enableCompression: true,
  protocols: ['trading-protocol-v1']
}

// Connection pool management
interface ConnectionPoolEntry {
  id: string
  ws: WebSocket
  isConnected: boolean
  subscriptions: Set<string>
  lastActivity: Date
  reconnectAttempts: number
}

// Data stream subscription management
interface StreamSubscription {
  id: string
  channel: string
  callback: (data: any) => void
  options: SubscriptionOptions
  isActive: boolean
  lastUpdate: Date
}

interface SubscriptionOptions {
  throttle?: number // milliseconds
  buffer?: boolean
  priority?: 'low' | 'normal' | 'high'
  retryOnError?: boolean
}

class WebSocketService {
  private connectionPool = new Map<string, ConnectionPoolEntry>()
  private config: WSConfig
  private primaryConnectionId: string | null = null
  private reconnectTimer: NodeJS.Timeout | null = null
  private heartbeatTimer: NodeJS.Timeout | null = null
  private messageHandlers = new Map<string, (data: any) => void>()
  private streamSubscriptions = new Map<string, StreamSubscription>()
  private messageQueue: WSMessage[] = []
  private connectionListeners = new Set<(status: ConnectionStatus) => void>()
  private errorListeners = new Set<(error: WSError) => void>()
  private throttleTimers = new Map<string, NodeJS.Timeout>()
  private buffers = new Map<string, any[]>()

  constructor(config: Partial<WSConfig> = {}) {
    this.config = { ...defaultConfig, ...config }
    this.setupMessageHandlers()
  }



  private setupMessageHandlers(): void {
    this.messageHandlers.set('price_update', this.handlePriceUpdate.bind(this))
    this.messageHandlers.set('bot_status', this.handleBotStatus.bind(this))
    this.messageHandlers.set('position_update', this.handlePositionUpdate.bind(this))
    this.messageHandlers.set('trade_executed', this.handleTradeExecuted.bind(this))
    this.messageHandlers.set('system_alert', this.handleSystemAlert.bind(this))
    this.messageHandlers.set('orderbook_update', this.handleOrderBookUpdate.bind(this))
    this.messageHandlers.set('market_stats', this.handleMarketStats.bind(this))
    this.messageHandlers.set('connection_status', this.handleConnectionStatus.bind(this))
    this.messageHandlers.set('subscription_confirmed', this.handleSubscriptionConfirmed.bind(this))
    this.messageHandlers.set('subscription_error', this.handleSubscriptionError.bind(this))
    this.messageHandlers.set('heartbeat', this.handleHeartbeat.bind(this))
    this.messageHandlers.set('error', this.handleError.bind(this))
  }

  // Enhanced connection management with pooling
  async connect(connectionId?: string): Promise<string> {
    const id = connectionId || this.generateConnectionId()
    
    return new Promise((resolve, reject) => {
      try {
        const ws = new WebSocket(this.config.url, this.config.protocols)
        const connectionTimeout = setTimeout(() => {
          ws.close()
          this.emitError({
            type: 'timeout',
            message: `Connection timeout after ${this.config.connectionTimeout}ms`,
            timestamp: new Date()
          })
          reject(new Error('Connection timeout'))
        }, this.config.connectionTimeout)

        const poolEntry: ConnectionPoolEntry = {
          id,
          ws,
          isConnected: false,
          subscriptions: new Set(),
          lastActivity: new Date(),
          reconnectAttempts: 0
        }

        ws.onopen = () => {
          clearTimeout(connectionTimeout)
          console.log(`WebSocket connected: ${id}`)
          
          poolEntry.isConnected = true
          poolEntry.lastActivity = new Date()
          this.connectionPool.set(id, poolEntry)
          
          if (!this.primaryConnectionId) {
            this.primaryConnectionId = id
          }
          
          this.startHeartbeat()
          this.processMessageQueue()
          this.resubscribeAll(id)
          this.emitConnectionStatus()
          
          resolve(id)
        }

        ws.onmessage = (event) => {
          poolEntry.lastActivity = new Date()
          try {
            const message: WSMessage = JSON.parse(event.data)
            this.handleMessage(message, id)
          } catch (error) {
            console.error('Failed to parse WebSocket message:', error)
            this.emitError({
              type: 'message',
              message: 'Failed to parse message',
              timestamp: new Date()
            })
          }
        }

        ws.onclose = (event) => {
          clearTimeout(connectionTimeout)
          console.log(`WebSocket disconnected: ${id}`, event.code, event.reason)
          
          poolEntry.isConnected = false
          
          if (id === this.primaryConnectionId) {
            this.primaryConnectionId = this.findAlternativePrimaryConnection()
            if (!this.primaryConnectionId) {
              this.stopHeartbeat()
            }
          }
          
          if (!event.wasClean && poolEntry.reconnectAttempts < this.config.maxReconnectAttempts) {
            this.scheduleReconnect(id)
          } else {
            this.connectionPool.delete(id)
          }
          
          this.emitConnectionStatus()
        }

        ws.onerror = (error) => {
          clearTimeout(connectionTimeout)
          console.error(`WebSocket error: ${id}`, error)
          this.emitError({
            type: 'connection',
            message: `Connection error: ${error}`,
            timestamp: new Date()
          })
          reject(error)
        }

        this.connectionPool.set(id, poolEntry)
      } catch (error) {
        reject(error)
      }
    })
  }

  disconnect(connectionId?: string): void {
    if (connectionId) {
      const connection = this.connectionPool.get(connectionId)
      if (connection) {
        connection.ws.close(1000, 'Client disconnect')
        this.connectionPool.delete(connectionId)
        
        if (connectionId === this.primaryConnectionId) {
          this.primaryConnectionId = this.findAlternativePrimaryConnection()
        }
      }
    } else {
      // Disconnect all connections
      this.connectionPool.forEach((connection, id) => {
        connection.ws.close(1000, 'Client disconnect')
      })
      this.connectionPool.clear()
      this.primaryConnectionId = null
      this.stopHeartbeat()
    }
    
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
    
    this.emitConnectionStatus()
  }

  private generateConnectionId(): string {
    return `ws_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  }

  private findAlternativePrimaryConnection(): string | null {
    for (const [id, connection] of this.connectionPool) {
      if (connection.isConnected) {
        return id
      }
    }
    return null
  }

  private processMessageQueue(): void {
    if (this.messageQueue.length === 0) return
    
    const connection = this.getPrimaryConnection()
    if (!connection) return
    
    while (this.messageQueue.length > 0) {
      const message = this.messageQueue.shift()
      if (message) {
        this.sendToConnection(connection.id, message)
      }
    }
  }

  private resubscribeAll(connectionId: string): void {
    this.streamSubscriptions.forEach((subscription) => {
      if (subscription.isActive) {
        this.sendToConnection(connectionId, {
          type: 'subscribe',
          data: { channel: subscription.channel, options: subscription.options },
          timestamp: new Date().toISOString()
        })
      }
    })
  }

  private scheduleReconnect(connectionId: string): void {
    const connection = this.connectionPool.get(connectionId)
    if (!connection) return
    
    connection.reconnectAttempts++
    const delay = this.config.reconnectInterval * Math.pow(1.5, connection.reconnectAttempts - 1)
    
    console.log(`Scheduling reconnect attempt ${connection.reconnectAttempts} for ${connectionId} in ${delay}ms`)
    
    this.reconnectTimer = setTimeout(async () => {
      try {
        await this.connect(connectionId)
      } catch (error) {
        console.error(`Reconnect failed for ${connectionId}:`, error)
        this.emitError({
          type: 'connection',
          message: `Reconnect failed: ${error}`,
          timestamp: new Date()
        })
      }
    }, delay)
  }

  private startHeartbeat(): void {
    if (this.heartbeatTimer) return // Already running
    
    this.heartbeatTimer = setInterval(() => {
      this.connectionPool.forEach((connection, id) => {
        if (connection.isConnected) {
          this.sendToConnection(id, {
            type: 'heartbeat',
            data: { timestamp: new Date().toISOString() },
            timestamp: new Date().toISOString()
          })
        }
      })
    }, this.config.heartbeatInterval)
  }

  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer)
      this.heartbeatTimer = null
    }
  }

  private sendToConnection(connectionId: string, data: any): boolean {
    const connection = this.connectionPool.get(connectionId)
    if (!connection || !connection.isConnected || connection.ws.readyState !== WebSocket.OPEN) {
      return false
    }
    
    try {
      connection.ws.send(JSON.stringify(data))
      connection.lastActivity = new Date()
      return true
    } catch (error) {
      console.error(`Failed to send message to ${connectionId}:`, error)
      this.emitError({
        type: 'message',
        message: `Failed to send message: ${error}`,
        timestamp: new Date()
      })
      return false
    }
  }

  private send(data: any): boolean {
    const connection = this.getPrimaryConnection()
    if (!connection) {
      // Queue message if no connection available
      if (this.messageQueue.length < this.config.maxMessageQueueSize) {
        this.messageQueue.push(data)
      }
      return false
    }
    
    return this.sendToConnection(connection.id, data)
  }

  private getPrimaryConnection(): ConnectionPoolEntry | null {
    if (this.primaryConnectionId) {
      const connection = this.connectionPool.get(this.primaryConnectionId)
      if (connection && connection.isConnected) {
        return connection
      }
    }
    
    // Find any connected connection
    for (const connection of this.connectionPool.values()) {
      if (connection.isConnected) {
        this.primaryConnectionId = connection.id
        return connection
      }
    }
    
    return null
  }

  // Enhanced subscription management with data stream support
  subscribe(
    channel: string, 
    callback: (data: any) => void, 
    options: SubscriptionOptions = {}
  ): string {
    const subscriptionId = this.generateSubscriptionId()
    
    const subscription: StreamSubscription = {
      id: subscriptionId,
      channel,
      callback,
      options: {
        throttle: 0,
        buffer: false,
        priority: 'normal',
        retryOnError: true,
        ...options
      },
      isActive: true,
      lastUpdate: new Date()
    }
    
    this.streamSubscriptions.set(subscriptionId, subscription)
    
    // Send subscription request
    const success = this.send({
      type: 'subscribe',
      data: { 
        channel, 
        subscriptionId,
        options: subscription.options 
      },
      timestamp: new Date().toISOString()
    })
    
    if (!success) {
      console.warn(`Failed to send subscription for ${channel}, will retry when connected`)
    }
    
    return subscriptionId
  }

  unsubscribe(subscriptionId: string): void {
    const subscription = this.streamSubscriptions.get(subscriptionId)
    if (!subscription) return
    
    subscription.isActive = false
    
    this.send({
      type: 'unsubscribe',
      data: { 
        channel: subscription.channel,
        subscriptionId 
      },
      timestamp: new Date().toISOString()
    })
    
    // Clean up throttle timers and buffers
    if (this.throttleTimers.has(subscriptionId)) {
      clearTimeout(this.throttleTimers.get(subscriptionId)!)
      this.throttleTimers.delete(subscriptionId)
    }
    
    this.buffers.delete(subscriptionId)
    this.streamSubscriptions.delete(subscriptionId)
  }

  private generateSubscriptionId(): string {
    return `sub_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  }

  // Bulk subscription management
  subscribeToMultiple(
    subscriptions: Array<{
      channel: string
      callback: (data: any) => void
      options?: SubscriptionOptions
    }>
  ): string[] {
    return subscriptions.map(sub => 
      this.subscribe(sub.channel, sub.callback, sub.options)
    )
  }

  unsubscribeFromMultiple(subscriptionIds: string[]): void {
    subscriptionIds.forEach(id => this.unsubscribe(id))
  }

  // Get active subscriptions
  getActiveSubscriptions(): Array<{
    id: string
    channel: string
    options: SubscriptionOptions
    lastUpdate: Date
  }> {
    return Array.from(this.streamSubscriptions.values())
      .filter(sub => sub.isActive)
      .map(sub => ({
        id: sub.id,
        channel: sub.channel,
        options: sub.options,
        lastUpdate: sub.lastUpdate
      }))
  }

  // Enhanced message handling with throttling and buffering
  private handleMessage(message: WSMessage, connectionId: string): void {
    // Update connection activity
    const connection = this.connectionPool.get(connectionId)
    if (connection) {
      connection.lastActivity = new Date()
    }
    
    // Handle system messages first
    const handler = this.messageHandlers.get(message.type)
    if (handler) {
      handler(message.data, message)
    }
    
    // Route to subscription callbacks
    if (message.channel) {
      this.routeToSubscriptions(message)
    }
    
    if (!handler && !message.channel) {
      console.warn('Unknown message type:', message.type)
    }
  }

  private routeToSubscriptions(message: WSMessage): void {
    this.streamSubscriptions.forEach((subscription) => {
      if (subscription.isActive && subscription.channel === message.channel) {
        this.processSubscriptionMessage(subscription, message.data)
      }
    })
  }

  private processSubscriptionMessage(subscription: StreamSubscription, data: any): void {
    subscription.lastUpdate = new Date()
    
    // Handle throttling
    if (subscription.options.throttle && subscription.options.throttle > 0) {
      this.handleThrottledMessage(subscription, data)
      return
    }
    
    // Handle buffering
    if (subscription.options.buffer) {
      this.handleBufferedMessage(subscription, data)
      return
    }
    
    // Direct callback
    try {
      subscription.callback(data)
    } catch (error) {
      console.error(`Error in subscription callback for ${subscription.channel}:`, error)
      if (subscription.options.retryOnError) {
        // Could implement retry logic here
      }
    }
  }

  private handleThrottledMessage(subscription: StreamSubscription, data: any): void {
    const timerId = this.throttleTimers.get(subscription.id)
    
    if (!timerId) {
      // First message or timer expired, process immediately
      try {
        subscription.callback(data)
      } catch (error) {
        console.error(`Error in throttled callback for ${subscription.channel}:`, error)
      }
      
      // Set throttle timer
      const newTimer = setTimeout(() => {
        this.throttleTimers.delete(subscription.id)
      }, subscription.options.throttle!)
      
      this.throttleTimers.set(subscription.id, newTimer)
    }
    // If timer exists, message is dropped (throttled)
  }

  private handleBufferedMessage(subscription: StreamSubscription, data: any): void {
    if (!this.buffers.has(subscription.id)) {
      this.buffers.set(subscription.id, [])
    }
    
    const buffer = this.buffers.get(subscription.id)!
    buffer.push(data)
    
    // Process buffer periodically or when it reaches a certain size
    if (buffer.length >= 10) { // Configurable buffer size
      this.flushBuffer(subscription.id)
    }
  }

  private flushBuffer(subscriptionId: string): void {
    const subscription = this.streamSubscriptions.get(subscriptionId)
    const buffer = this.buffers.get(subscriptionId)
    
    if (!subscription || !buffer || buffer.length === 0) return
    
    try {
      subscription.callback(buffer.splice(0)) // Pass all buffered data and clear buffer
    } catch (error) {
      console.error(`Error in buffered callback for ${subscription.channel}:`, error)
    }
  }

  // Flush all buffers (useful for cleanup or forced processing)
  flushAllBuffers(): void {
    this.buffers.forEach((_, subscriptionId) => {
      this.flushBuffer(subscriptionId)
    })
  }

  private handlePriceUpdate(data: PriceUpdateData): void {
    const tradingStore = useTradingStore.getState()
    tradingStore.updateMarketPrice(data.symbol, data.price)
  }

  private handleBotStatus(data: BotStatusData): void {
    const tradingStore = useTradingStore.getState()
    const updates: Partial<Bot> = {
      status: data.status,
    }
    
    if (data.performance) {
      updates.performance = {
        totalReturn: data.performance.totalReturn,
        sharpeRatio: 0, // Would need to be calculated
        maxDrawdown: 0, // Would need to be calculated
        winRate: 0, // Would need to be calculated
        profitFactor: 0, // Would need to be calculated
        totalTrades: data.performance.totalTrades,
        avgTradeReturn: 0, // Would need to be calculated
        volatility: 0, // Would need to be calculated
        calmarRatio: 0, // Would need to be calculated
        sortinoRatio: 0, // Would need to be calculated
      }
    }
    
    tradingStore.updateBot(data.botId, updates)
  }

  private handlePositionUpdate(data: PositionUpdateData): void {
    const tradingStore = useTradingStore.getState()
    tradingStore.updatePosition(data.symbol, {
      side: data.side,
      quantity: data.quantity,
      entryPrice: data.entryPrice,
      currentPrice: data.currentPrice,
      unrealizedPnl: data.unrealizedPnl,
      timestamp: new Date(),
    })
  }

  private handleTradeExecuted(data: TradeExecutedData): void {
    // This could trigger notifications, update trade history, etc.
    console.log('Trade executed:', data)
    
    // You could emit custom events here for other parts of the app to listen to
    window.dispatchEvent(new CustomEvent('trade-executed', { detail: data }))
  }

  private handleSystemAlert(data: SystemAlertData): void {
    // Handle system alerts - could show notifications, update UI, etc.
    console.log('System alert:', data)
    
    // Emit custom event for alert handling
    window.dispatchEvent(new CustomEvent('system-alert', { detail: data }))
  }

  private handleOrderBookUpdate(data: OrderBookUpdateData): void {
    const tradingStore = useTradingStore.getState()
    
    // Update order book data in store
    const orderBook: OrderBook = {
      marketId: data.symbol,
      timestamp: new Date(data.timestamp),
      bids: data.bids.map(bid => ({
        price: bid.price,
        quantity: bid.quantity,
        total: bid.price * bid.quantity
      })),
      asks: data.asks.map(ask => ({
        price: ask.price,
        quantity: ask.quantity,
        total: ask.price * ask.quantity
      })),
      spread: data.asks[0]?.price - data.bids[0]?.price || 0,
      spreadPercent: data.bids[0]?.price ? 
        ((data.asks[0]?.price - data.bids[0]?.price) / data.bids[0]?.price) * 100 : 0
    }
    
    // Emit custom event for order book updates
    window.dispatchEvent(new CustomEvent('orderbook-update', { 
      detail: { symbol: data.symbol, orderBook } 
    }))
  }

  private handleMarketStats(data: MarketStatsData): void {
    console.log('Market stats update:', data)
    
    // Emit custom event for market stats
    window.dispatchEvent(new CustomEvent('market-stats-update', { detail: data }))
  }

  private handleConnectionStatus(data: any, message: WSMessage): void {
    console.log('Connection status update:', data)
    this.emitConnectionStatus()
  }

  private handleSubscriptionConfirmed(data: any, message: WSMessage): void {
    console.log('Subscription confirmed:', data)
    
    // Update subscription status if needed
    if (data.subscriptionId) {
      const subscription = this.streamSubscriptions.get(data.subscriptionId)
      if (subscription) {
        subscription.isActive = true
      }
    }
  }

  private handleSubscriptionError(data: any, message: WSMessage): void {
    console.error('Subscription error:', data)
    
    this.emitError({
      type: 'subscription',
      message: data.message || 'Subscription failed',
      channel: data.channel,
      timestamp: new Date()
    })
    
    // Deactivate subscription if needed
    if (data.subscriptionId) {
      const subscription = this.streamSubscriptions.get(data.subscriptionId)
      if (subscription && data.retryable !== false) {
        // Could implement retry logic here
      }
    }
  }

  private handleHeartbeat(data: any): void {
    // Heartbeat received, connection is alive
    // Could update connection health metrics here
  }

  private handleError(data: any, message: WSMessage): void {
    console.error('WebSocket error message:', data)
    
    this.emitError({
      type: 'message',
      message: data.message || 'Unknown error',
      code: data.code,
      channel: message.channel,
      timestamp: new Date()
    })
  }

  // Event emission and listener management
  private emitConnectionStatus(): void {
    const status = this.getConnectionStatus()
    this.connectionListeners.forEach(listener => {
      try {
        listener(status)
      } catch (error) {
        console.error('Error in connection status listener:', error)
      }
    })
  }

  private emitError(error: WSError): void {
    this.errorListeners.forEach(listener => {
      try {
        listener(error)
      } catch (listenerError) {
        console.error('Error in error listener:', listenerError)
      }
    })
  }

  // Public listener management
  onConnectionStatusChange(listener: (status: ConnectionStatus) => void): () => void {
    this.connectionListeners.add(listener)
    
    // Return unsubscribe function
    return () => {
      this.connectionListeners.delete(listener)
    }
  }

  onError(listener: (error: WSError) => void): () => void {
    this.errorListeners.add(listener)
    
    // Return unsubscribe function
    return () => {
      this.errorListeners.delete(listener)
    }
  }

  // Enhanced public methods for subscription management
  subscribeToMarketData(
    symbols: string[], 
    callback: (data: PriceUpdateData) => void,
    options?: SubscriptionOptions
  ): string[] {
    return symbols.map(symbol => 
      this.subscribe(`market:${symbol}`, callback, options)
    )
  }

  subscribeToBotUpdates(
    botIds: string[], 
    callback: (data: BotStatusData) => void,
    options?: SubscriptionOptions
  ): string[] {
    return botIds.map(botId => 
      this.subscribe(`bot:${botId}`, callback, options)
    )
  }

  subscribeToAccountUpdates(
    accountIds: string[], 
    callback: (data: any) => void,
    options?: SubscriptionOptions
  ): string[] {
    return accountIds.map(accountId => 
      this.subscribe(`account:${accountId}`, callback, options)
    )
  }

  subscribeToOrderBooks(
    symbols: string[], 
    callback: (data: OrderBookUpdateData) => void,
    options?: SubscriptionOptions
  ): string[] {
    return symbols.map(symbol => 
      this.subscribe(`orderbook:${symbol}`, callback, options)
    )
  }

  subscribeToSystemAlerts(
    callback: (data: SystemAlertData) => void,
    options?: SubscriptionOptions
  ): string {
    return this.subscribe('system:alerts', callback, options)
  }

  subscribeToMarketStats(
    callback: (data: MarketStatsData) => void,
    options?: SubscriptionOptions
  ): string {
    return this.subscribe('market:stats', callback, options)
  }

  // Enhanced status methods
  getConnectionStatus(): ConnectionStatus {
    const connectedCount = Array.from(this.connectionPool.values())
      .filter(conn => conn.isConnected).length
    
    const totalReconnectAttempts = Array.from(this.connectionPool.values())
      .reduce((sum, conn) => sum + conn.reconnectAttempts, 0)
    
    const uptime = this.primaryConnectionId ? 
      Date.now() - (this.connectionPool.get(this.primaryConnectionId)?.lastActivity.getTime() || Date.now()) : 0
    
    return {
      connected: connectedCount > 0,
      activeConnections: connectedCount,
      totalSubscriptions: this.streamSubscriptions.size,
      reconnectAttempts: totalReconnectAttempts,
      uptime
    }
  }

  getDetailedStatus(): {
    connections: Array<{
      id: string
      connected: boolean
      lastActivity: Date
      reconnectAttempts: number
      subscriptions: number
    }>
    subscriptions: Array<{
      id: string
      channel: string
      active: boolean
      lastUpdate: Date
      options: SubscriptionOptions
    }>
    messageQueue: number
    config: WSConfig
  } {
    return {
      connections: Array.from(this.connectionPool.entries()).map(([id, conn]) => ({
        id,
        connected: conn.isConnected,
        lastActivity: conn.lastActivity,
        reconnectAttempts: conn.reconnectAttempts,
        subscriptions: conn.subscriptions.size
      })),
      subscriptions: Array.from(this.streamSubscriptions.values()).map(sub => ({
        id: sub.id,
        channel: sub.channel,
        active: sub.isActive,
        lastUpdate: sub.lastUpdate,
        options: sub.options
      })),
      messageQueue: this.messageQueue.length,
      config: this.config
    }
  }

  // Configuration management
  updateConfig(newConfig: Partial<WSConfig>): void {
    const oldConfig = { ...this.config }
    this.config = { ...this.config, ...newConfig }
    
    // Restart heartbeat if interval changed
    if (oldConfig.heartbeatInterval !== this.config.heartbeatInterval) {
      this.stopHeartbeat()
      if (this.connectionPool.size > 0) {
        this.startHeartbeat()
      }
    }
    
    console.log('WebSocket configuration updated:', newConfig)
  }

  getConfig(): WSConfig {
    return { ...this.config }
  }

  // Health check and maintenance
  performHealthCheck(): Promise<{
    healthy: boolean
    issues: string[]
    recommendations: string[]
  }> {
    return new Promise((resolve) => {
      const issues: string[] = []
      const recommendations: string[] = []
      
      // Check connection health
      const connectedCount = Array.from(this.connectionPool.values())
        .filter(conn => conn.isConnected).length
      
      if (connectedCount === 0) {
        issues.push('No active connections')
        recommendations.push('Establish at least one WebSocket connection')
      }
      
      // Check for stale connections
      const now = Date.now()
      this.connectionPool.forEach((conn, id) => {
        const timeSinceActivity = now - conn.lastActivity.getTime()
        if (timeSinceActivity > this.config.heartbeatInterval * 2) {
          issues.push(`Connection ${id} appears stale (${timeSinceActivity}ms since last activity)`)
          recommendations.push(`Consider reconnecting ${id}`)
        }
      })
      
      // Check message queue size
      if (this.messageQueue.length > this.config.maxMessageQueueSize * 0.8) {
        issues.push('Message queue is nearly full')
        recommendations.push('Process queued messages or increase queue size')
      }
      
      // Check subscription health
      const inactiveSubscriptions = Array.from(this.streamSubscriptions.values())
        .filter(sub => !sub.isActive).length
      
      if (inactiveSubscriptions > 0) {
        issues.push(`${inactiveSubscriptions} inactive subscriptions`)
        recommendations.push('Clean up inactive subscriptions')
      }
      
      resolve({
        healthy: issues.length === 0,
        issues,
        recommendations
      })
    })
  }

  // Cleanup and maintenance
  cleanup(): void {
    // Clear all timers
    this.throttleTimers.forEach(timer => clearTimeout(timer))
    this.throttleTimers.clear()
    
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
    
    this.stopHeartbeat()
    
    // Clear buffers
    this.buffers.clear()
    
    // Clear message queue
    this.messageQueue.length = 0
    
    // Disconnect all connections
    this.disconnect()
    
    // Clear listeners
    this.connectionListeners.clear()
    this.errorListeners.clear()
    
    console.log('WebSocket service cleaned up')
  }
}

// Move interfaces outside the class
interface ConnectionStatus {
  connected: boolean
  activeConnections: number
  totalSubscriptions: number
  reconnectAttempts: number
  lastError?: string
  uptime: number
}

interface WSError {
  type: 'connection' | 'subscription' | 'message' | 'timeout'
  message: string
  code?: number
  channel?: string
  timestamp: Date
}

// Create singleton instance
export const websocketService = new WebSocketService()

// Export types and service
export type { 
  WSMessage, 
  PriceUpdateData, 
  BotStatusData, 
  PositionUpdateData, 
  TradeExecutedData, 
  SystemAlertData,
  OrderBookUpdateData,
  MarketStatsData,
  WSConfig,
  ConnectionStatus,
  WSError,
  StreamSubscription,
  SubscriptionOptions
}
export { WebSocketService }