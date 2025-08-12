import React, { useState } from 'react'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Alert } from '@/components/ui/Alert'
import { useSyncStatus, useConflictResolution } from '@/hooks/useRealTimeData'
import { realTimeDataSync } from '@/services/realTimeDataSync'
import type { ConflictEntry } from '@/services/realTimeDataSync'

export const RealTimeDataSyncDashboard: React.FC = () => {
  const { syncState, cacheStats, pendingUpdates, conflicts } = useSyncStatus()
  const { conflicts: activeConflicts, resolveConflict } = useConflictResolution()
  const [selectedConflict, setSelectedConflict] = useState<ConflictEntry | null>(null)

  const handleForceSync = () => {
    // Trigger a manual sync
    realTimeDataSync.cleanup()
    window.location.reload() // Simple way to reinitialize
  }

  const handleClearCache = () => {
    realTimeDataSync.cleanup()
  }

  const formatTimestamp = (date: Date) => {
    return new Intl.DateTimeFormat('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      fractionalSecondDigits: 3
    }).format(date)
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">Real-Time Data Sync</h2>
        <div className="flex space-x-2">
          <Button onClick={handleForceSync} variant="outline">
            Force Sync
          </Button>
          <Button onClick={handleClearCache} variant="outline">
            Clear Cache
          </Button>
        </div>
      </div>

      {/* Sync Status Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="text-sm font-medium text-gray-500">Last Sync</div>
          <div className="text-lg font-semibold">
            {formatTimestamp(syncState.lastSync)}
          </div>
        </Card>
        
        <Card className="p-4">
          <div className="text-sm font-medium text-gray-500">Cache Entries</div>
          <div className="text-lg font-semibold">
            {cacheStats.totalEntries}
          </div>
          <div className="text-xs text-gray-400">
            {cacheStats.dirtyEntries} dirty
          </div>
        </Card>
        
        <Card className="p-4">
          <div className="text-sm font-medium text-gray-500">Pending Updates</div>
          <div className="text-lg font-semibold">
            {pendingUpdates.length}
          </div>
        </Card>
        
        <Card className="p-4">
          <div className="text-sm font-medium text-gray-500">Active Conflicts</div>
          <div className="text-lg font-semibold text-red-600">
            {activeConflicts.length}
          </div>
        </Card>
      </div>

      {/* Pending Updates */}
      {pendingUpdates.length > 0 && (
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">Pending Updates</h3>
          <div className="space-y-2">
            {pendingUpdates.map((update) => (
              <div
                key={update.id}
                className="flex items-center justify-between p-3 bg-yellow-50 rounded-lg"
              >
                <div>
                  <div className="font-medium">
                    {update.entityType}:{update.entityId}
                  </div>
                  <div className="text-sm text-gray-500">
                    Type: {update.type} • {formatTimestamp(update.timestamp)}
                  </div>
                </div>
                <div className="flex space-x-2">
                  <Button
                    size="sm"
                    onClick={() => realTimeDataSync.confirmOptimisticUpdate(update.id)}
                  >
                    Confirm
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => realTimeDataSync.rollbackOptimisticUpdate(update.id)}
                  >
                    Rollback
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Conflicts */}
      {activeConflicts.length > 0 && (
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">Data Conflicts</h3>
          <div className="space-y-4">
            {activeConflicts.map((conflict) => (
              <div key={conflict.id} className="border border-red-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <div>
                    <div className="font-medium text-red-800">
                      {conflict.type} Conflict
                    </div>
                    <div className="text-sm text-gray-500">
                      {formatTimestamp(conflict.timestamp)}
                    </div>
                  </div>
                  <Button
                    size="sm"
                    onClick={() => setSelectedConflict(
                      selectedConflict?.id === conflict.id ? null : conflict
                    )}
                  >
                    {selectedConflict?.id === conflict.id ? 'Hide' : 'Show'} Details
                  </Button>
                </div>

                {selectedConflict?.id === conflict.id && (
                  <div className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <h4 className="font-medium text-gray-700 mb-2">Local Data</h4>
                        <pre className="text-xs bg-gray-100 p-2 rounded overflow-auto max-h-32">
                          {JSON.stringify(conflict.localData, null, 2)}
                        </pre>
                      </div>
                      <div>
                        <h4 className="font-medium text-gray-700 mb-2">Remote Data</h4>
                        <pre className="text-xs bg-gray-100 p-2 rounded overflow-auto max-h-32">
                          {JSON.stringify(conflict.remoteData, null, 2)}
                        </pre>
                      </div>
                    </div>

                    <div className="flex space-x-2">
                      <Button
                        size="sm"
                        onClick={() => resolveConflict(conflict.id, 'local')}
                        className="bg-blue-600 hover:bg-blue-700"
                      >
                        Use Local
                      </Button>
                      <Button
                        size="sm"
                        onClick={() => resolveConflict(conflict.id, 'remote')}
                        className="bg-green-600 hover:bg-green-700"
                      >
                        Use Remote
                      </Button>
                      <Button
                        size="sm"
                        onClick={() => resolveConflict(conflict.id, 'merge')}
                        className="bg-purple-600 hover:bg-purple-700"
                      >
                        Merge
                      </Button>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Cache Statistics */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">Cache Statistics</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <div className="text-sm font-medium text-gray-500">Total Entries</div>
            <div className="text-xl font-semibold">{cacheStats.totalEntries}</div>
          </div>
          <div>
            <div className="text-sm font-medium text-gray-500">Dirty Entries</div>
            <div className="text-xl font-semibold">{cacheStats.dirtyEntries}</div>
          </div>
          <div>
            <div className="text-sm font-medium text-gray-500">Subscribers</div>
            <div className="text-xl font-semibold">{cacheStats.totalSubscribers}</div>
          </div>
          <div>
            <div className="text-sm font-medium text-gray-500">Cache Size</div>
            <div className="text-xl font-semibold">
              {(cacheStats.cacheSize / 1024).toFixed(1)}KB
            </div>
          </div>
        </div>
      </Card>

      {/* Status Indicators */}
      <div className="flex space-x-4">
        <Alert
          type={pendingUpdates.length > 0 ? 'warning' : 'success'}
          message={
            pendingUpdates.length > 0
              ? `${pendingUpdates.length} pending updates`
              : 'All updates synchronized'
          }
        />
        
        {activeConflicts.length > 0 && (
          <Alert
            type="error"
            message={`${activeConflicts.length} data conflicts require resolution`}
          />
        )}
      </div>
    </div>
  )
}