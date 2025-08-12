import { websocketService } from './websocketService'
import type { 
  Market, 
  Position, 
  Bot, 
  OrderBook, 
  PriceData,
  MarketDataSubscription 
} from '@/types'

// Data synchronization interfaces
interface SyncState {
  lastSync: Date
  version: number
  conflicts: ConflictEntry[]
  pendingUpdates: PendingUpdate[]
}

interface ConflictEntry {
  id: string
  type: 'market' | 'position' | 'bot' | 'orderbook'
  localData: any
  remoteData: any
  timestamp: Date
  resolved: boolean
  resolution?: 'local' | 'remote' | 'merge'
}

interface PendingUpdate {
  id: string
  type: 'optimistic' | 'confirmed' | 'rollback'
  entityType: 'market' | 'position' | 'bot' | 'orderbook'
  entityId: string
  data: any
  timestamp: Date
  timeout?: NodeJS.Timeout
}

interface CacheEntry<T> {
  data: T
  timestamp: Date
  version: number
  dirty: boolean
  subscribers: Set<string>
}

interface SyncOptions {
  enableOptimisticUpdates: boolean
  conflictResolution: 'local' | 'remote' | 'merge' | 'manual'
  cacheTimeout: number
  maxRetries: number
  batchSize: number
  syncInterval: number
}

const defaultSyncOptions: SyncOptions = {
  enableOptimisticUpdates: true,
  conflictResolution: 'remote',
  cacheTimeout: 300000, // 5 minutes
  maxRetries: 3,
  batchSize: 50,
  syncInterval: 30000 // 30 seconds
}

class RealTimeDataSyncService {
  private cache = new Map<string, CacheEntry<any>>()
  private syncState: SyncState = {
    lastSync: new Date(),
    version: 0,
    conflicts: [],
    pendingUpdates: []
  }
  private options: SyncOptions
  private syncTimer: NodeJS.Timeout | null = null
  private subscriptions = new Map<string, string>() // entityId -> subscriptionId
  private conflictListeners = new Set<(conflict: ConflictEntry) => void>()
  private syncListeners = new Set<(state: SyncState) => void>()
  private isOnline = true
  private offlineQueue: Array<{ action: string; data: any; timestamp: Date }> = []

  constructor(options: Partial<SyncOptions> = {}) {
    this.options = { ...defaultSyncOptions, ...options }
    this.setupWebSocketListeners()
    this.startSyncTimer()
    this.setupOnlineOfflineHandlers()
  }

  private setupWebSocketListeners(): void {
    // Listen for connection status changes
    websocketService.onConnectionStatusChange((status) => {
      this.isOnline = status.connected
      if (status.connected && this.offlineQueue.length > 0) {
        this.processOfflineQueue()
      }
    })

    // Listen for WebSocket errors
    websocketService.onError((error) => {
      console.error('WebSocket error in sync service:', error)
      if (error.type === 'connection') {
        this.isOnline = false
      }
    })
  }

  private setupOnlineOfflineHandlers(): void {
    window.addEventListener('online', () => {
      this.isOnline = true
      this.processOfflineQueue()
      this.performFullSync()
    })

    window.addEventListener('offline', () => {
      this.isOnline = false
    })
  }

  private startSyncTimer(): void {
    this.syncTimer = setInterval(() => {
      this.performIncrementalSync()
    }, this.options.syncInterval)
  }

  private stopSyncTimer(): void {
    if (this.syncTimer) {
      clearInterval(this.syncTimer)
      this.syncTimer = null
    }
  }

  // Cache management
  private getCacheKey(entityType: string, entityId: string): string {
    return `${entityType}:${entityId}`
  }

  private setCache<T>(entityType: string, entityId: string, data: T, version?: number): void {
    const key = this.getCacheKey(entityType, entityId)
    const existing = this.cache.get(key)
    
    const entry: CacheEntry<T> = {
      data,
      timestamp: new Date(),
      version: version || (existing?.version || 0) + 1,
      dirty: false,
      subscribers: existing?.subscribers || new Set()
    }
    
    this.cache.set(key, entry)
    this.notifySubscribers(key, data)
  }

  private getCache<T>(entityType: string, entityId: string): T | null {
    const key = this.getCacheKey(entityType, entityId)
    const entry = this.cache.get(key)
    
    if (!entry) return null
    
    // Check if cache is expired
    const age = Date.now() - entry.timestamp.getTime()
    if (age > this.options.cacheTimeout) {
      this.cache.delete(key)
      return null
    }
    
    return entry.data
  }

  private markCacheDirty(entityType: string, entityId: string): void {
    const key = this.getCacheKey(entityType, entityId)
    const entry = this.cache.get(key)
    if (entry) {
      entry.dirty = true
    }
  }

  private notifySubscribers(cacheKey: string, data: any): void {
    const entry = this.cache.get(cacheKey)
    if (!entry) return
    
    entry.subscribers.forEach(subscriberId => {
      // Emit custom event for subscribers
      window.dispatchEvent(new CustomEvent(`cache-update-${subscriberId}`, {
        detail: { cacheKey, data }
      }))
    })
  }

  // Subscription management
  subscribeToEntity<T>(
    entityType: string, 
    entityId: string, 
    callback: (data: T) => void
  ): string {
    const subscriberId = `sub_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    const cacheKey = this.getCacheKey(entityType, entityId)
    
    // Add to cache subscribers
    let entry = this.cache.get(cacheKey)
    if (!entry) {
      entry = {
        data: null,
        timestamp: new Date(),
        version: 0,
        dirty: false,
        subscribers: new Set()
      }
      this.cache.set(cacheKey, entry)
    }
    entry.subscribers.add(subscriberId)
    
    // Set up event listener
    const eventHandler = (event: CustomEvent) => {
      callback(event.detail.data)
    }
    window.addEventListener(`cache-update-${subscriberId}`, eventHandler as EventListener)
    
    // Subscribe to WebSocket updates if not already subscribed
    if (!this.subscriptions.has(entityId)) {
      const wsSubscriptionId = this.subscribeToWebSocketUpdates(entityType, entityId)
      this.subscriptions.set(entityId, wsSubscriptionId)
    }
    
    // Return cached data immediately if available
    if (entry.data) {
      setTimeout(() => callback(entry.data), 0)
    }
    
    return subscriberId
  }

  unsubscribeFromEntity(subscriberId: string): void {
    // Remove event listener
    window.removeEventListener(`cache-update-${subscriberId}`, () => {})
    
    // Remove from cache subscribers
    this.cache.forEach((entry, key) => {
      entry.subscribers.delete(subscriberId)
      
      // Clean up empty subscriptions
      if (entry.subscribers.size === 0) {
        const [entityType, entityId] = key.split(':')
        const wsSubscriptionId = this.subscriptions.get(entityId)
        if (wsSubscriptionId) {
          websocketService.unsubscribe(wsSubscriptionId)
          this.subscriptions.delete(entityId)
        }
      }
    })
  }

  private subscribeToWebSocketUpdates(entityType: string, entityId: string): string {
    switch (entityType) {
      case 'market':
        return websocketService.subscribeToMarketData(
          [entityId],
          (data) => this.handleMarketUpdate(entityId, data),
          { throttle: 100 } // Throttle market updates to 100ms
        )[0]
      
      case 'bot':
        return websocketService.subscribeToBotUpdates(
          [entityId],
          (data) => this.handleBotUpdate(entityId, data)
        )[0]
      
      case 'orderbook':
        return websocketService.subscribeToOrderBooks(
          [entityId],
          (data) => this.handleOrderBookUpdate(entityId, data),
          { buffer: true } // Buffer orderbook updates
        )[0]
      
      default:
        throw new Error(`Unsupported entity type: ${entityType}`)
    }
  }

  // Real-time update handlers
  private handleMarketUpdate(marketId: string, data: any): void {
    const cached = this.getCache<Market>('market', marketId)
    
    if (this.options.enableOptimisticUpdates || !cached) {
      // Apply update immediately
      const updatedMarket: Market = {
        ...cached,
        id: marketId,
        price: data.price,
        volume24h: data.volume,
        change24h: data.change24h,
        high24h: data.high24h,
        low24h: data.low24h,
        lastUpdated: new Date(data.timestamp)
      } as Market
      
      this.setCache('market', marketId, updatedMarket)
    }
    
    // Check for conflicts
    if (cached && this.hasConflict(cached, data)) {
      this.handleConflict('market', marketId, cached, data)
    }
  }

  private handleBotUpdate(botId: string, data: any): void {
    const cached = this.getCache<Bot>('bot', botId)
    
    if (this.options.enableOptimisticUpdates || !cached) {
      const updatedBot: Partial<Bot> = {
        ...cached,
        id: botId,
        status: data.status,
        performance: data.performance
      }
      
      this.setCache('bot', botId, updatedBot)
    }
    
    if (cached && this.hasConflict(cached, data)) {
      this.handleConflict('bot', botId, cached, data)
    }
  }

  private handleOrderBookUpdate(marketId: string, data: any): void {
    const cached = this.getCache<OrderBook>('orderbook', marketId)
    
    const updatedOrderBook: OrderBook = {
      marketId,
      timestamp: new Date(data.timestamp),
      bids: data.bids.map((bid: any) => ({
        price: bid.price,
        quantity: bid.quantity,
        total: bid.price * bid.quantity
      })),
      asks: data.asks.map((ask: any) => ({
        price: ask.price,
        quantity: ask.quantity,
        total: ask.price * ask.quantity
      })),
      spread: data.asks[0]?.price - data.bids[0]?.price || 0,
      spreadPercent: data.bids[0]?.price ? 
        ((data.asks[0]?.price - data.bids[0]?.price) / data.bids[0]?.price) * 100 : 0
    }
    
    this.setCache('orderbook', marketId, updatedOrderBook)
  }

  // Optimistic updates
  applyOptimisticUpdate<T>(
    entityType: string, 
    entityId: string, 
    updateData: Partial<T>,
    timeout: number = 5000
  ): string {
    const updateId = `opt_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    const cached = this.getCache<T>(entityType, entityId)
    
    if (!cached) {
      throw new Error(`No cached data found for ${entityType}:${entityId}`)
    }
    
    // Apply optimistic update
    const optimisticData = { ...cached, ...updateData }
    this.setCache(entityType, entityId, optimisticData)
    this.markCacheDirty(entityType, entityId)
    
    // Track pending update
    const pendingUpdate: PendingUpdate = {
      id: updateId,
      type: 'optimistic',
      entityType,
      entityId,
      data: updateData,
      timestamp: new Date(),
      timeout: setTimeout(() => {
        this.rollbackOptimisticUpdate(updateId)
      }, timeout)
    }
    
    this.syncState.pendingUpdates.push(pendingUpdate)
    
    // Queue for offline processing if needed
    if (!this.isOnline) {
      this.offlineQueue.push({
        action: 'optimistic_update',
        data: { entityType, entityId, updateData, updateId },
        timestamp: new Date()
      })
    }
    
    return updateId
  }

  confirmOptimisticUpdate(updateId: string): void {
    const updateIndex = this.syncState.pendingUpdates.findIndex(u => u.id === updateId)
    if (updateIndex === -1) return
    
    const update = this.syncState.pendingUpdates[updateIndex]
    
    // Clear timeout
    if (update.timeout) {
      clearTimeout(update.timeout)
    }
    
    // Mark as confirmed
    update.type = 'confirmed'
    
    // Remove dirty flag
    const cacheKey = this.getCacheKey(update.entityType, update.entityId)
    const entry = this.cache.get(cacheKey)
    if (entry) {
      entry.dirty = false
    }
    
    // Remove from pending updates
    this.syncState.pendingUpdates.splice(updateIndex, 1)
  }

  rollbackOptimisticUpdate(updateId: string): void {
    const updateIndex = this.syncState.pendingUpdates.findIndex(u => u.id === updateId)
    if (updateIndex === -1) return
    
    const update = this.syncState.pendingUpdates[updateIndex]
    
    // Clear timeout
    if (update.timeout) {
      clearTimeout(update.timeout)
    }
    
    // Rollback to previous state (would need to store previous state)
    // For now, mark for refresh
    this.markCacheDirty(update.entityType, update.entityId)
    
    // Remove from pending updates
    this.syncState.pendingUpdates.splice(updateIndex, 1)
    
    console.warn(`Rolled back optimistic update ${updateId}`)
  }

  // Conflict resolution
  private hasConflict(localData: any, remoteData: any): boolean {
    // Simple conflict detection based on timestamps or versions
    if (localData.lastUpdated && remoteData.timestamp) {
      const localTime = new Date(localData.lastUpdated).getTime()
      const remoteTime = new Date(remoteData.timestamp).getTime()
      
      // Consider it a conflict if local data is newer than remote
      return localTime > remoteTime
    }
    
    return false
  }

  private handleConflict(
    entityType: string, 
    entityId: string, 
    localData: any, 
    remoteData: any
  ): void {
    const conflict: ConflictEntry = {
      id: `conflict_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      type: entityType as any,
      localData,
      remoteData,
      timestamp: new Date(),
      resolved: false
    }
    
    this.syncState.conflicts.push(conflict)
    
    // Auto-resolve based on strategy
    switch (this.options.conflictResolution) {
      case 'local':
        this.resolveConflict(conflict.id, 'local')
        break
      case 'remote':
        this.resolveConflict(conflict.id, 'remote')
        break
      case 'merge':
        this.resolveConflict(conflict.id, 'merge')
        break
      case 'manual':
        this.notifyConflictListeners(conflict)
        break
    }
  }

  resolveConflict(conflictId: string, resolution: 'local' | 'remote' | 'merge'): void {
    const conflict = this.syncState.conflicts.find(c => c.id === conflictId)
    if (!conflict || conflict.resolved) return
    
    let resolvedData: any
    
    switch (resolution) {
      case 'local':
        resolvedData = conflict.localData
        break
      case 'remote':
        resolvedData = conflict.remoteData
        break
      case 'merge':
        resolvedData = this.mergeData(conflict.localData, conflict.remoteData)
        break
    }
    
    // Apply resolution
    const [entityType, entityId] = this.extractEntityInfo(conflict)
    this.setCache(entityType, entityId, resolvedData)
    
    // Mark conflict as resolved
    conflict.resolved = true
    conflict.resolution = resolution
    
    console.log(`Resolved conflict ${conflictId} using ${resolution} strategy`)
  }

  private mergeData(localData: any, remoteData: any): any {
    // Simple merge strategy - prefer remote for most fields, keep local for user-modified fields
    return {
      ...remoteData,
      ...localData,
      // Prefer remote timestamps
      lastUpdated: remoteData.timestamp || remoteData.lastUpdated || localData.lastUpdated
    }
  }

  private extractEntityInfo(conflict: ConflictEntry): [string, string] {
    // Extract entity type and ID from conflict data
    const entityType = conflict.type
    const entityId = conflict.localData.id || conflict.remoteData.id
    return [entityType, entityId]
  }

  private notifyConflictListeners(conflict: ConflictEntry): void {
    this.conflictListeners.forEach(listener => {
      try {
        listener(conflict)
      } catch (error) {
        console.error('Error in conflict listener:', error)
      }
    })
  }

  // Synchronization
  private async performFullSync(): Promise<void> {
    console.log('Performing full synchronization...')
    
    try {
      // Sync all cached entities
      const syncPromises: Promise<void>[] = []
      
      this.cache.forEach((entry, key) => {
        const [entityType, entityId] = key.split(':')
        syncPromises.push(this.syncEntity(entityType, entityId))
      })
      
      await Promise.all(syncPromises)
      
      this.syncState.lastSync = new Date()
      this.syncState.version++
      
      this.notifySyncListeners()
      console.log('Full synchronization completed')
    } catch (error) {
      console.error('Full synchronization failed:', error)
    }
  }

  private async performIncrementalSync(): Promise<void> {
    // Only sync dirty entries
    const dirtyEntries: Array<[string, string]> = []
    
    this.cache.forEach((entry, key) => {
      if (entry.dirty) {
        const [entityType, entityId] = key.split(':')
        dirtyEntries.push([entityType, entityId])
      }
    })
    
    if (dirtyEntries.length === 0) return
    
    console.log(`Performing incremental sync for ${dirtyEntries.length} entities`)
    
    try {
      const syncPromises = dirtyEntries.map(([entityType, entityId]) => 
        this.syncEntity(entityType, entityId)
      )
      
      await Promise.all(syncPromises)
      
      this.syncState.lastSync = new Date()
      this.notifySyncListeners()
    } catch (error) {
      console.error('Incremental synchronization failed:', error)
    }
  }

  private async syncEntity(entityType: string, entityId: string): Promise<void> {
    // This would typically make an API call to get the latest data
    // For now, we'll simulate it
    return new Promise((resolve) => {
      setTimeout(() => {
        // Mark as clean
        const key = this.getCacheKey(entityType, entityId)
        const entry = this.cache.get(key)
        if (entry) {
          entry.dirty = false
        }
        resolve()
      }, 100)
    })
  }

  private processOfflineQueue(): void {
    console.log(`Processing ${this.offlineQueue.length} offline actions`)
    
    while (this.offlineQueue.length > 0) {
      const action = this.offlineQueue.shift()
      if (!action) continue
      
      try {
        switch (action.action) {
          case 'optimistic_update':
            // Re-apply optimistic update
            const { entityType, entityId, updateData, updateId } = action.data
            this.applyOptimisticUpdate(entityType, entityId, updateData)
            break
          // Handle other offline actions
        }
      } catch (error) {
        console.error('Error processing offline action:', error)
      }
    }
  }

  private notifySyncListeners(): void {
    this.syncListeners.forEach(listener => {
      try {
        listener(this.syncState)
      } catch (error) {
        console.error('Error in sync listener:', error)
      }
    })
  }

  // Public API
  onConflict(listener: (conflict: ConflictEntry) => void): () => void {
    this.conflictListeners.add(listener)
    return () => this.conflictListeners.delete(listener)
  }

  onSync(listener: (state: SyncState) => void): () => void {
    this.syncListeners.add(listener)
    return () => this.syncListeners.delete(listener)
  }

  getSyncState(): SyncState {
    return { ...this.syncState }
  }

  getConflicts(): ConflictEntry[] {
    return this.syncState.conflicts.filter(c => !c.resolved)
  }

  getPendingUpdates(): PendingUpdate[] {
    return [...this.syncState.pendingUpdates]
  }

  getCacheStats(): {
    totalEntries: number
    dirtyEntries: number
    totalSubscribers: number
    cacheSize: number
  } {
    let dirtyCount = 0
    let totalSubscribers = 0
    
    this.cache.forEach(entry => {
      if (entry.dirty) dirtyCount++
      totalSubscribers += entry.subscribers.size
    })
    
    return {
      totalEntries: this.cache.size,
      dirtyEntries: dirtyCount,
      totalSubscribers,
      cacheSize: JSON.stringify(Array.from(this.cache.entries())).length
    }
  }

  updateOptions(newOptions: Partial<SyncOptions>): void {
    const oldOptions = { ...this.options }
    this.options = { ...this.options, ...newOptions }
    
    // Restart sync timer if interval changed
    if (oldOptions.syncInterval !== this.options.syncInterval) {
      this.stopSyncTimer()
      this.startSyncTimer()
    }
    
    console.log('Sync options updated:', newOptions)
  }

  // Cleanup
  cleanup(): void {
    this.stopSyncTimer()
    
    // Clear all timeouts
    this.syncState.pendingUpdates.forEach(update => {
      if (update.timeout) {
        clearTimeout(update.timeout)
      }
    })
    
    // Clear cache
    this.cache.clear()
    
    // Clear subscriptions
    this.subscriptions.forEach(subscriptionId => {
      websocketService.unsubscribe(subscriptionId)
    })
    this.subscriptions.clear()
    
    // Clear listeners
    this.conflictListeners.clear()
    this.syncListeners.clear()
    
    // Clear offline queue
    this.offlineQueue.length = 0
    
    console.log('Real-time data sync service cleaned up')
  }
}

// Create singleton instance
export const realTimeDataSync = new RealTimeDataSyncService()

// Export types and service
export type {
  SyncState,
  ConflictEntry,
  PendingUpdate,
  SyncOptions
}
export { RealTimeDataSyncService }