import { useState, useEffect, useCallback, useRef } from 'react'
import { realTimeDataSync } from '@/services/realTimeDataSync'
import type { ConflictEntry, SyncState } from '@/services/realTimeDataSync'

// Hook for subscribing to real-time entity data
export function useRealTimeData<T>(
  entityType: string,
  entityId: string,
  initialData?: T
) {
  const [data, setData] = useState<T | null>(initialData || null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const subscriptionRef = useRef<string | null>(null)

  useEffect(() => {
    if (!entityId) return

    setLoading(true)
    setError(null)

    // Subscribe to real-time updates
    subscriptionRef.current = realTimeDataSync.subscribeToEntity<T>(
      entityType,
      entityId,
      (updatedData) => {
        setData(updatedData)
        setLoading(false)
      }
    )

    // Cleanup subscription on unmount
    return () => {
      if (subscriptionRef.current) {
        realTimeDataSync.unsubscribeFromEntity(subscriptionRef.current)
      }
    }
  }, [entityType, entityId])

  // Optimistic update function
  const updateOptimistically = useCallback(
    (updateData: Partial<T>, timeout?: number) => {
      if (!entityId) return null
      
      try {
        return realTimeDataSync.applyOptimisticUpdate(
          entityType,
          entityId,
          updateData,
          timeout
        )
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Update failed')
        return null
      }
    },
    [entityType, entityId]
  )

  return {
    data,
    loading,
    error,
    updateOptimistically
  }
}

// Hook for managing conflicts
export function useConflictResolution() {
  const [conflicts, setConflicts] = useState<ConflictEntry[]>([])

  useEffect(() => {
    // Subscribe to conflicts
    const unsubscribe = realTimeDataSync.onConflict((conflict) => {
      setConflicts(prev => [...prev, conflict])
    })

    // Load existing conflicts
    setConflicts(realTimeDataSync.getConflicts())

    return unsubscribe
  }, [])

  const resolveConflict = useCallback(
    (conflictId: string, resolution: 'local' | 'remote' | 'merge') => {
      realTimeDataSync.resolveConflict(conflictId, resolution)
      setConflicts(prev => prev.filter(c => c.id !== conflictId))
    },
    []
  )

  return {
    conflicts,
    resolveConflict
  }
}// H
ook for sync status monitoring
export function useSyncStatus() {
  const [syncState, setSyncState] = useState<SyncState>(
    realTimeDataSync.getSyncState()
  )
  const [cacheStats, setCacheStats] = useState(
    realTimeDataSync.getCacheStats()
  )

  useEffect(() => {
    // Subscribe to sync state changes
    const unsubscribe = realTimeDataSync.onSync((state) => {
      setSyncState(state)
    })

    // Update cache stats periodically
    const statsInterval = setInterval(() => {
      setCacheStats(realTimeDataSync.getCacheStats())
    }, 5000)

    return () => {
      unsubscribe()
      clearInterval(statsInterval)
    }
  }, [])

  return {
    syncState,
    cacheStats,
    pendingUpdates: syncState.pendingUpdates,
    conflicts: syncState.conflicts
  }
}

// Hook for batch real-time data subscriptions
export function useBatchRealTimeData<T>(
  subscriptions: Array<{
    entityType: string
    entityId: string
    initialData?: T
  }>
) {
  const [dataMap, setDataMap] = useState<Map<string, T>>(new Map())
  const [loadingMap, setLoadingMap] = useState<Map<string, boolean>>(new Map())
  const [errorMap, setErrorMap] = useState<Map<string, string>>(new Map())
  const subscriptionRefs = useRef<Map<string, string>>(new Map())

  useEffect(() => {
    // Clear existing subscriptions
    subscriptionRefs.current.forEach(subscriptionId => {
      realTimeDataSync.unsubscribeFromEntity(subscriptionId)
    })
    subscriptionRefs.current.clear()

    // Set up new subscriptions
    subscriptions.forEach(({ entityType, entityId, initialData }) => {
      const key = `${entityType}:${entityId}`
      
      // Set initial state
      if (initialData) {
        setDataMap(prev => new Map(prev).set(key, initialData))
      }
      setLoadingMap(prev => new Map(prev).set(key, true))
      setErrorMap(prev => new Map(prev).set(key, ''))

      // Subscribe to updates
      const subscriptionId = realTimeDataSync.subscribeToEntity<T>(
        entityType,
        entityId,
        (updatedData) => {
          setDataMap(prev => new Map(prev).set(key, updatedData))
          setLoadingMap(prev => new Map(prev).set(key, false))
        }
      )

      subscriptionRefs.current.set(key, subscriptionId)
    })

    // Cleanup on unmount
    return () => {
      subscriptionRefs.current.forEach(subscriptionId => {
        realTimeDataSync.unsubscribeFromEntity(subscriptionId)
      })
      subscriptionRefs.current.clear()
    }
  }, [subscriptions])

  const getData = useCallback((entityType: string, entityId: string): T | null => {
    const key = `${entityType}:${entityId}`
    return dataMap.get(key) || null
  }, [dataMap])

  const isLoading = useCallback((entityType: string, entityId: string): boolean => {
    const key = `${entityType}:${entityId}`
    return loadingMap.get(key) || false
  }, [loadingMap])

  const getError = useCallback((entityType: string, entityId: string): string | null => {
    const key = `${entityType}:${entityId}`
    return errorMap.get(key) || null
  }, [errorMap])

  return {
    getData,
    isLoading,
    getError,
    dataMap,
    loadingMap,
    errorMap
  }
}