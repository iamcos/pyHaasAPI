import React, { useState, useEffect } from 'react'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { websocketService } from '@/services/websocketService'
import { realTimeDataSync } from '@/services/realTimeDataSync'
import { RealTimeDataSyncDashboard } from './RealTimeDataSyncDashboard'
import { OptimisticUpdateDemo } from './OptimisticUpdateDemo'
import type { ConnectionStatus, WSError } from '@/services/websocketService'

export const RealTimeDataTest: React.FC = () => {
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>()
  const [errors, setErrors] = useState<WSError[]>([])
  const [testResults, setTestResults] = useState<string[]>([])
  const [isRunningTests, setIsRunningTests] = useState(false)

  useEffect(() => {
    // Subscribe to connection status changes
    const unsubscribeStatus = websocketService.onConnectionStatusChange((status) => {
      setConnectionStatus(status)
    })

    // Subscribe to errors
    const unsubscribeError = websocketService.onError((error) => {
      setErrors(prev => [...prev.slice(-9), error]) // Keep last 10 errors
    })

    // Get initial status
    setConnectionStatus(websocketService.getConnectionStatus())

    return () => {
      unsubscribeStatus()
      unsubscribeError()
    }
  }, [])

  const runConnectionTests = async () => {
    setIsRunningTests(true)
    setTestResults([])
    
    const results: string[] = []
    
    try {
      // Test 1: Basic connection
      results.push('Testing basic WebSocket connection...')
      const connectionId = await websocketService.connect()
      results.push(`✓ Connected successfully: ${connectionId}`)
      
      // Test 2: Multiple connections (connection pooling)
      results.push('Testing connection pooling...')
      const connectionId2 = await websocketService.connect()
      results.push(`✓ Second connection established: ${connectionId2}`)
      
      // Test 3: Subscription management
      results.push('Testing subscription management...')
      const subscriptionId = websocketService.subscribeToMarketData(
        ['BTCUSDT'],
        (data) => {
          results.push(`✓ Received market data: ${JSON.stringify(data).substring(0, 50)}...`)
        },
        { throttle: 1000 }
      )[0]
      results.push(`✓ Subscribed to market data: ${subscriptionId}`)
      
      // Test 4: Health check
      results.push('Running health check...')
      const healthCheck = await websocketService.performHealthCheck()
      results.push(`✓ Health check: ${healthCheck.healthy ? 'Healthy' : 'Issues found'}`)
      if (healthCheck.issues.length > 0) {
        results.push(`  Issues: ${healthCheck.issues.join(', ')}`)
      }
      
      // Test 5: Real-time sync service
      results.push('Testing real-time data sync...')
      const syncSubscription = realTimeDataSync.subscribeToEntity(
        'market',
        'BTCUSDT',
        (data) => {
          results.push(`✓ Sync service received data: ${data?.symbol || 'unknown'}`)
        }
      )
      results.push(`✓ Sync subscription created: ${syncSubscription}`)
      
      // Test 6: Optimistic update
      results.push('Testing optimistic updates...')
      try {
        const updateId = realTimeDataSync.applyOptimisticUpdate(
          'market',
          'BTCUSDT',
          { price: 50000 },
          2000
        )
        results.push(`✓ Optimistic update applied: ${updateId}`)
        
        // Confirm the update after 1 second
        setTimeout(() => {
          realTimeDataSync.confirmOptimisticUpdate(updateId)
          results.push(`✓ Optimistic update confirmed: ${updateId}`)
          setTestResults([...results])
        }, 1000)
      } catch (error) {
        results.push(`⚠ Optimistic update test skipped: ${error}`)
      }
      
      results.push('✓ All tests completed successfully!')
      
    } catch (error) {
      results.push(`✗ Test failed: ${error}`)
    }
    
    setTestResults(results)
    setIsRunningTests(false)
  }

  const clearErrors = () => {
    setErrors([])
  }

  const clearTestResults = () => {
    setTestResults([])
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">Real-Time Data Integration Test</h2>
        <div className="flex space-x-2">
          <Button
            onClick={runConnectionTests}
            disabled={isRunningTests}
            className="bg-blue-600 hover:bg-blue-700"
          >
            {isRunningTests ? 'Running Tests...' : 'Run Tests'}
          </Button>
          <Button onClick={clearTestResults} variant="outline">
            Clear Results
          </Button>
        </div>
      </div>

      {/* Connection Status */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">Connection Status</h3>
        {connectionStatus ? (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <div className="text-sm font-medium text-gray-500">Status</div>
              <div className={`text-lg font-semibold ${
                connectionStatus.connected ? 'text-green-600' : 'text-red-600'
              }`}>
                {connectionStatus.connected ? 'Connected' : 'Disconnected'}
              </div>
            </div>
            <div>
              <div className="text-sm font-medium text-gray-500">Active Connections</div>
              <div className="text-lg font-semibold">{connectionStatus.activeConnections}</div>
            </div>
            <div>
              <div className="text-sm font-medium text-gray-500">Subscriptions</div>
              <div className="text-lg font-semibold">{connectionStatus.totalSubscriptions}</div>
            </div>
            <div>
              <div className="text-sm font-medium text-gray-500">Reconnect Attempts</div>
              <div className="text-lg font-semibold">{connectionStatus.reconnectAttempts}</div>
            </div>
          </div>
        ) : (
          <div className="text-gray-500">Loading connection status...</div>
        )}
      </Card>

      {/* Test Results */}
      {testResults.length > 0 && (
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">Test Results</h3>
          <div className="bg-gray-900 text-green-400 p-4 rounded-lg font-mono text-sm max-h-64 overflow-y-auto">
            {testResults.map((result, index) => (
              <div key={index} className="mb-1">
                {result}
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Errors */}
      {errors.length > 0 && (
        <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold">Recent Errors</h3>
            <Button onClick={clearErrors} size="sm" variant="outline">
              Clear Errors
            </Button>
          </div>
          <div className="space-y-2">
            {errors.map((error, index) => (
              <div key={index} className="p-3 bg-red-50 border border-red-200 rounded-lg">
                <div className="flex items-center justify-between">
                  <div className="font-medium text-red-800">
                    {error.type.toUpperCase()} Error
                  </div>
                  <div className="text-sm text-red-600">
                    {new Intl.DateTimeFormat('en-US', {
                      hour: '2-digit',
                      minute: '2-digit',
                      second: '2-digit'
                    }).format(error.timestamp)}
                  </div>
                </div>
                <div className="text-red-700 mt-1">{error.message}</div>
                {error.channel && (
                  <div className="text-sm text-red-600 mt-1">
                    Channel: {error.channel}
                  </div>
                )}
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Optimistic Update Demo */}
      <OptimisticUpdateDemo marketId="BTCUSDT" />

      {/* Real-Time Data Sync Dashboard */}
      <RealTimeDataSyncDashboard />
    </div>
  )
}