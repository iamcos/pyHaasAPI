import { useState, useEffect, useCallback } from 'react'

interface IndexedDBConfig {
  dbName: string
  version: number
  stores: {
    name: string
    keyPath: string
    indexes?: { name: string; keyPath: string; unique?: boolean }[]
  }[]
}

const defaultConfig: IndexedDBConfig = {
  dbName: 'ai-trading-interface',
  version: 1,
  stores: [
    {
      name: 'strategies',
      keyPath: 'id',
      indexes: [
        { name: 'name', keyPath: 'name' },
        { name: 'createdAt', keyPath: 'createdAt' },
      ]
    },
    {
      name: 'backtests',
      keyPath: 'id',
      indexes: [
        { name: 'labId', keyPath: 'labId' },
        { name: 'startDate', keyPath: 'startDate' },
      ]
    },
    {
      name: 'workflows',
      keyPath: 'id',
      indexes: [
        { name: 'status', keyPath: 'status' },
        { name: 'startTime', keyPath: 'startTime' },
      ]
    },
    {
      name: 'insights',
      keyPath: 'id',
      indexes: [
        { name: 'type', keyPath: 'type' },
        { name: 'timestamp', keyPath: 'timestamp' },
      ]
    },
  ]
}

export function useIndexedDB(config: IndexedDBConfig = defaultConfig) {
  const [db, setDb] = useState<IDBDatabase | null>(null)
  const [isReady, setIsReady] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Initialize database
  useEffect(() => {
    const initDB = async () => {
      try {
        const request = indexedDB.open(config.dbName, config.version)
        
        request.onerror = () => {
          setError('Failed to open IndexedDB')
        }
        
        request.onsuccess = () => {
          setDb(request.result)
          setIsReady(true)
        }
        
        request.onupgradeneeded = (event) => {
          const database = (event.target as IDBOpenDBRequest).result
          
          // Create object stores
          config.stores.forEach(storeConfig => {
            if (!database.objectStoreNames.contains(storeConfig.name)) {
              const store = database.createObjectStore(storeConfig.name, {
                keyPath: storeConfig.keyPath
              })
              
              // Create indexes
              storeConfig.indexes?.forEach(index => {
                store.createIndex(index.name, index.keyPath, {
                  unique: index.unique || false
                })
              })
            }
          })
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error')
      }
    }
    
    initDB()
  }, [config])

  // Generic CRUD operations
  const add = useCallback(async <T>(storeName: string, data: T): Promise<void> => {
    if (!db) throw new Error('Database not ready')
    
    return new Promise((resolve, reject) => {
      const transaction = db.transaction([storeName], 'readwrite')
      const store = transaction.objectStore(storeName)
      const request = store.add(data)
      
      request.onsuccess = () => resolve()
      request.onerror = () => reject(request.error)
    })
  }, [db])

  const get = useCallback(async <T>(storeName: string, key: string): Promise<T | null> => {
    if (!db) throw new Error('Database not ready')
    
    return new Promise((resolve, reject) => {
      const transaction = db.transaction([storeName], 'readonly')
      const store = transaction.objectStore(storeName)
      const request = store.get(key)
      
      request.onsuccess = () => resolve(request.result || null)
      request.onerror = () => reject(request.error)
    })
  }, [db])

  const getAll = useCallback(async <T>(storeName: string): Promise<T[]> => {
    if (!db) throw new Error('Database not ready')
    
    return new Promise((resolve, reject) => {
      const transaction = db.transaction([storeName], 'readonly')
      const store = transaction.objectStore(storeName)
      const request = store.getAll()
      
      request.onsuccess = () => resolve(request.result)
      request.onerror = () => reject(request.error)
    })
  }, [db])

  const update = useCallback(async <T>(storeName: string, data: T): Promise<void> => {
    if (!db) throw new Error('Database not ready')
    
    return new Promise((resolve, reject) => {
      const transaction = db.transaction([storeName], 'readwrite')
      const store = transaction.objectStore(storeName)
      const request = store.put(data)
      
      request.onsuccess = () => resolve()
      request.onerror = () => reject(request.error)
    })
  }, [db])

  const remove = useCallback(async (storeName: string, key: string): Promise<void> => {
    if (!db) throw new Error('Database not ready')
    
    return new Promise((resolve, reject) => {
      const transaction = db.transaction([storeName], 'readwrite')
      const store = transaction.objectStore(storeName)
      const request = store.delete(key)
      
      request.onsuccess = () => resolve()
      request.onerror = () => reject(request.error)
    })
  }, [db])

  const clear = useCallback(async (storeName: string): Promise<void> => {
    if (!db) throw new Error('Database not ready')
    
    return new Promise((resolve, reject) => {
      const transaction = db.transaction([storeName], 'readwrite')
      const store = transaction.objectStore(storeName)
      const request = store.clear()
      
      request.onsuccess = () => resolve()
      request.onerror = () => reject(request.error)
    })
  }, [db])

  const query = useCallback(async <T>(
    storeName: string, 
    indexName: string, 
    value: any
  ): Promise<T[]> => {
    if (!db) throw new Error('Database not ready')
    
    return new Promise((resolve, reject) => {
      const transaction = db.transaction([storeName], 'readonly')
      const store = transaction.objectStore(storeName)
      const index = store.index(indexName)
      const request = index.getAll(value)
      
      request.onsuccess = () => resolve(request.result)
      request.onerror = () => reject(request.error)
    })
  }, [db])

  return {
    isReady,
    error,
    add,
    get,
    getAll,
    update,
    remove,
    clear,
    query,
  }
}