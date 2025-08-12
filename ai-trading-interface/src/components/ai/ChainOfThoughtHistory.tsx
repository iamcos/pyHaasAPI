import React, { useState, useMemo } from 'react'
import { MagnifyingGlassIcon, FunnelIcon, ClockIcon, TrashIcon } from '@heroicons/react/24/outline'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { ChainOfThoughtDisplay } from './ChainOfThoughtDisplay'
import { useAIStore } from '@/stores/aiStore'
import type { ChainOfThoughtStep } from '@/types'

interface ChainOfThoughtHistoryProps {
  className?: string
}

export const ChainOfThoughtHistory: React.FC<ChainOfThoughtHistoryProps> = ({
  className = ""
}) => {
  const { chainOfThoughtHistory, clearChainOfThought } = useAIStore()
  const [searchTerm, setSearchTerm] = useState('')
  const [confidenceFilter, setConfidenceFilter] = useState<'all' | 'high' | 'medium' | 'low'>('all')
  const [timeFilter, setTimeFilter] = useState<'all' | 'today' | 'week' | 'month'>('all')
  const [selectedSession, setSelectedSession] = useState<string | null>(null)

  // Group steps by session (based on timestamp proximity)
  const sessionGroups = useMemo(() => {
    const groups: { [key: string]: ChainOfThoughtStep[] } = {}
    const sortedSteps = [...chainOfThoughtHistory].sort((a, b) => 
      new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
    )

    let currentSession = ''
    let lastTimestamp: Date | null = null

    sortedSteps.forEach(step => {
      const stepTime = new Date(step.timestamp)
      
      // Create new session if more than 30 minutes gap
      if (!lastTimestamp || stepTime.getTime() - lastTimestamp.getTime() > 30 * 60 * 1000) {
        currentSession = `session-${stepTime.getTime()}`
      }
      
      if (!groups[currentSession]) {
        groups[currentSession] = []
      }
      
      groups[currentSession].push(step)
      lastTimestamp = stepTime
    })

    return groups
  }, [chainOfThoughtHistory])

  // Filter steps based on search and filters
  const filteredSessions = useMemo(() => {
    const filtered: { [key: string]: ChainOfThoughtStep[] } = {}

    Object.entries(sessionGroups).forEach(([sessionId, steps]) => {
      const filteredSteps = steps.filter(step => {
        // Search filter
        if (searchTerm && !step.reasoning.toLowerCase().includes(searchTerm.toLowerCase())) {
          return false
        }

        // Confidence filter
        if (confidenceFilter !== 'all') {
          const confidence = step.confidence
          if (confidenceFilter === 'high' && confidence < 0.8) return false
          if (confidenceFilter === 'medium' && (confidence < 0.5 || confidence >= 0.8)) return false
          if (confidenceFilter === 'low' && confidence >= 0.5) return false
        }

        // Time filter
        if (timeFilter !== 'all') {
          const stepTime = new Date(step.timestamp)
          const now = new Date()
          const dayMs = 24 * 60 * 60 * 1000

          if (timeFilter === 'today' && now.getTime() - stepTime.getTime() > dayMs) return false
          if (timeFilter === 'week' && now.getTime() - stepTime.getTime() > 7 * dayMs) return false
          if (timeFilter === 'month' && now.getTime() - stepTime.getTime() > 30 * dayMs) return false
        }

        return true
      })

      if (filteredSteps.length > 0) {
        filtered[sessionId] = filteredSteps
      }
    })

    return filtered
  }, [sessionGroups, searchTerm, confidenceFilter, timeFilter])

  const getSessionTitle = (sessionId: string, steps: ChainOfThoughtStep[]): string => {
    if (steps.length === 0) return 'Empty Session'
    
    const firstStep = steps[steps.length - 1] // Steps are in reverse chronological order
    const timestamp = new Date(firstStep.timestamp)
    const timeStr = timestamp.toLocaleString()
    
    // Try to extract a meaningful title from the first step
    const reasoning = firstStep.reasoning
    const shortReasoning = reasoning.length > 50 ? reasoning.substring(0, 50) + '...' : reasoning
    
    return `${timeStr} - ${shortReasoning}`
  }

  const getSessionSummary = (steps: ChainOfThoughtStep[]): {
    avgConfidence: number
    duration: string
    stepCount: number
  } => {
    if (steps.length === 0) {
      return { avgConfidence: 0, duration: '0s', stepCount: 0 }
    }

    const avgConfidence = steps.reduce((sum, step) => sum + step.confidence, 0) / steps.length
    
    const timestamps = steps.map(s => new Date(s.timestamp).getTime())
    const minTime = Math.min(...timestamps)
    const maxTime = Math.max(...timestamps)
    const durationMs = maxTime - minTime
    
    let duration = '0s'
    if (durationMs > 60000) {
      duration = `${Math.round(durationMs / 60000)}m`
    } else if (durationMs > 1000) {
      duration = `${Math.round(durationMs / 1000)}s`
    }

    return {
      avgConfidence,
      duration,
      stepCount: steps.length
    }
  }

  if (chainOfThoughtHistory.length === 0) {
    return (
      <Card className={`p-8 text-center ${className}`}>
        <ClockIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">No Reasoning History</h3>
        <p className="text-gray-500">
          Chain-of-thought reasoning steps will appear here as you interact with the AI.
        </p>
      </Card>
    )
  }

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Filters */}
      <Card className="p-4">
        <div className="flex flex-col sm:flex-row gap-4">
          {/* Search */}
          <div className="flex-1">
            <div className="relative">
              <MagnifyingGlassIcon className="h-5 w-5 text-gray-400 absolute left-3 top-1/2 transform -translate-y-1/2" />
              <input
                type="text"
                placeholder="Search reasoning steps..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>

          {/* Confidence Filter */}
          <div className="flex items-center space-x-2">
            <FunnelIcon className="h-5 w-5 text-gray-400" />
            <select
              value={confidenceFilter}
              onChange={(e) => setConfidenceFilter(e.target.value as any)}
              className="border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="all">All Confidence</option>
              <option value="high">High (80%+)</option>
              <option value="medium">Medium (50-80%)</option>
              <option value="low">Low (&lt;50%)</option>
            </select>
          </div>

          {/* Time Filter */}
          <div className="flex items-center space-x-2">
            <ClockIcon className="h-5 w-5 text-gray-400" />
            <select
              value={timeFilter}
              onChange={(e) => setTimeFilter(e.target.value as any)}
              className="border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="all">All Time</option>
              <option value="today">Today</option>
              <option value="week">This Week</option>
              <option value="month">This Month</option>
            </select>
          </div>

          {/* Clear History */}
          <Button
            variant="outline"
            onClick={clearChainOfThought}
            className="flex items-center space-x-2"
          >
            <TrashIcon className="h-4 w-4" />
            <span>Clear</span>
          </Button>
        </div>
      </Card>

      {/* Session List */}
      <div className="space-y-4">
        {Object.entries(filteredSessions).map(([sessionId, steps]) => {
          const summary = getSessionSummary(steps)
          const isSelected = selectedSession === sessionId

          return (
            <Card key={sessionId} className="overflow-hidden">
              <div 
                className="p-4 cursor-pointer hover:bg-gray-50 transition-colors border-b border-gray-200"
                onClick={() => setSelectedSession(isSelected ? null : sessionId)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <h3 className="text-sm font-medium text-gray-900">
                      {getSessionTitle(sessionId, steps)}
                    </h3>
                    <div className="flex items-center space-x-4 mt-1 text-xs text-gray-500">
                      <span>{summary.stepCount} steps</span>
                      <span>{summary.duration} duration</span>
                      <span>{(summary.avgConfidence * 100).toFixed(0)}% avg confidence</span>
                    </div>
                  </div>
                  <div className="text-xs text-gray-400">
                    {isSelected ? 'Click to collapse' : 'Click to expand'}
                  </div>
                </div>
              </div>

              {isSelected && (
                <div className="p-4">
                  <ChainOfThoughtDisplay
                    steps={steps.reverse()} // Show in chronological order when expanded
                    title={`Reasoning Session (${steps.length} steps)`}
                    showConfidence={true}
                    showAlternatives={true}
                  />
                </div>
              )}
            </Card>
          )
        })}
      </div>

      {Object.keys(filteredSessions).length === 0 && (
        <Card className="p-8 text-center">
          <div className="text-gray-500">
            No reasoning sessions match your current filters.
          </div>
        </Card>
      )}
    </div>
  )
}

export default ChainOfThoughtHistory