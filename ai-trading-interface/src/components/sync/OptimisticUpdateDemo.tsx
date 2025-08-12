import React, { useState } from 'react'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { useRealTimeData } from '@/hooks/useRealTimeData'
import type { Market } from '@/types'

interface OptimisticUpdateDemoProps {
  marketId: string
}

export const OptimisticUpdateDemo: React.FC<OptimisticUpdateDemoProps> = ({
  marketId
}) => {
  const { data: market, loading, error, updateOptimistically } = useRealTimeData<Market>(
    'market',
    marketId
  )
  const [pendingUpdates, setPendingUpdates] = useState<string[]>([])

  const handleOptimisticPriceUpdate = () => {
    if (!market) return

    const newPrice = market.price * (1 + (Math.random() - 0.5) * 0.02) // ±1% change
    const updateId = updateOptimistically({
      price: newPrice,
      lastUpdated: new Date()
    }, 3000) // 3 second timeout

    if (updateId) {
      setPendingUpdates(prev => [...prev, updateId])
      
      // Simulate confirmation after 1.5 seconds
      setTimeout(() => {
        setPendingUpdates(prev => prev.filter(id => id !== updateId))
      }, 1500)
    }
  }

  const handleOptimisticVolumeUpdate = () => {
    if (!market) return

    const newVolume = market.volume24h * (1 + Math.random() * 0.1) // +10% increase
    const updateId = updateOptimistically({
      volume24h: newVolume,
      lastUpdated: new Date()
    }, 3000)

    if (updateId) {
      setPendingUpdates(prev => [...prev, updateId])
      
      // Simulate confirmation after 2 seconds
      setTimeout(() => {
        setPendingUpdates(prev => prev.filter(id => id !== updateId))
      }, 2000)
    }
  }

  const handleOptimisticStatusUpdate = () => {
    if (!market) return

    const newStatus = market.status === 'active' ? 'inactive' : 'active'
    const updateId = updateOptimistically({
      status: newStatus,
      lastUpdated: new Date()
    }, 5000) // 5 second timeout

    if (updateId) {
      setPendingUpdates(prev => [...prev, updateId])
      
      // This one will timeout to demonstrate rollback
      setTimeout(() => {
        setPendingUpdates(prev => prev.filter(id => id !== updateId))
      }, 5500)
    }
  }

  if (loading) {
    return (
      <Card className="p-6">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="space-y-2">
            <div className="h-3 bg-gray-200 rounded"></div>
            <div className="h-3 bg-gray-200 rounded w-5/6"></div>
          </div>
        </div>
      </Card>
    )
  }

  if (error) {
    return (
      <Card className="p-6">
        <div className="text-red-600">Error: {error}</div>
      </Card>
    )
  }

  if (!market) {
    return (
      <Card className="p-6">
        <div className="text-gray-500">No market data available</div>
      </Card>
    )
  }

  return (
    <Card className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold">Optimistic Updates Demo</h3>
        <div className="flex items-center space-x-2">
          {pendingUpdates.length > 0 && (
            <div className="flex items-center space-x-1">
              <div className="w-2 h-2 bg-yellow-400 rounded-full animate-pulse"></div>
              <span className="text-sm text-yellow-600">
                {pendingUpdates.length} pending
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Market Data Display */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-gray-50 p-4 rounded-lg">
          <div className="text-sm font-medium text-gray-500">Symbol</div>
          <div className="text-lg font-semibold">{market.symbol}</div>
        </div>
        
        <div className="bg-gray-50 p-4 rounded-lg">
          <div className="text-sm font-medium text-gray-500">Price</div>
          <div className="text-lg font-semibold">
            ${market.price.toFixed(4)}
          </div>
          <div className="text-xs text-gray-400">
            {market.changePercent24h > 0 ? '+' : ''}
            {market.changePercent24h.toFixed(2)}%
          </div>
        </div>
        
        <div className="bg-gray-50 p-4 rounded-lg">
          <div className="text-sm font-medium text-gray-500">24h Volume</div>
          <div className="text-lg font-semibold">
            ${(market.volume24h / 1000000).toFixed(2)}M
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <div className="bg-gray-50 p-4 rounded-lg">
          <div className="text-sm font-medium text-gray-500">Status</div>
          <div className="flex items-center space-x-2">
            <div
              className={`w-2 h-2 rounded-full ${
                market.status === 'active' ? 'bg-green-400' : 'bg-red-400'
              }`}
            ></div>
            <span className="text-lg font-semibold capitalize">
              {market.status}
            </span>
          </div>
        </div>
        
        <div className="bg-gray-50 p-4 rounded-lg">
          <div className="text-sm font-medium text-gray-500">Last Updated</div>
          <div className="text-lg font-semibold">
            {new Intl.DateTimeFormat('en-US', {
              hour: '2-digit',
              minute: '2-digit',
              second: '2-digit'
            }).format(market.lastUpdated)}
          </div>
        </div>
      </div>

      {/* Optimistic Update Controls */}
      <div className="space-y-4">
        <h4 className="font-medium text-gray-700">Try Optimistic Updates:</h4>
        
        <div className="flex flex-wrap gap-2">
          <Button
            onClick={handleOptimisticPriceUpdate}
            disabled={pendingUpdates.length > 0}
            className="bg-blue-600 hover:bg-blue-700"
          >
            Update Price (Confirms in 1.5s)
          </Button>
          
          <Button
            onClick={handleOptimisticVolumeUpdate}
            disabled={pendingUpdates.length > 0}
            className="bg-green-600 hover:bg-green-700"
          >
            Update Volume (Confirms in 2s)
          </Button>
          
          <Button
            onClick={handleOptimisticStatusUpdate}
            disabled={pendingUpdates.length > 0}
            className="bg-red-600 hover:bg-red-700"
          >
            Toggle Status (Will Rollback)
          </Button>
        </div>

        <div className="text-sm text-gray-500">
          <p>
            • Price and Volume updates will be confirmed and persist
          </p>
          <p>
            • Status update will timeout and rollback after 5 seconds
          </p>
          <p>
            • Updates are applied immediately for responsive UI
          </p>
        </div>
      </div>

      {/* Pending Updates Display */}
      {pendingUpdates.length > 0 && (
        <div className="mt-6 p-4 bg-yellow-50 rounded-lg">
          <h5 className="font-medium text-yellow-800 mb-2">Pending Updates:</h5>
          <div className="space-y-1">
            {pendingUpdates.map((updateId, index) => (
              <div key={updateId} className="text-sm text-yellow-700">
                Update {index + 1}: {updateId.substring(0, 8)}...
              </div>
            ))}
          </div>
        </div>
      )}
    </Card>
  )
}