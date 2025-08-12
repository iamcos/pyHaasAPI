import React, { useState, useEffect } from 'react'
import { 
  ChartBarIcon, 
  ClockIcon, 
  CheckCircleIcon, 
  ExclamationTriangleIcon,
  PlayIcon,
  DocumentTextIcon,
  Cog6ToothIcon
} from '@heroicons/react/24/outline'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { ChainOfThoughtDisplay } from './ChainOfThoughtDisplay'
import { ChainOfThoughtHistory } from './ChainOfThoughtHistory'
import { ChainOfThoughtReplay } from './ChainOfThoughtReplay'
import { chainOfThoughtManager, type ChainOfThoughtSession } from '@/services/chainOfThoughtManager'
import { chainOfThoughtValidator } from '@/services/chainOfThoughtValidator'
import { useAIStore } from '@/stores/aiStore'
import type { ChainOfThoughtStep } from '@/types'

interface ChainOfThoughtDashboardProps {
  className?: string
}

export const ChainOfThoughtDashboard: React.FC<ChainOfThoughtDashboardProps> = ({
  className = ""
}) => {
  const { chainOfThoughtHistory, showChainOfThought, setShowChainOfThought } = useAIStore()
  const [activeTab, setActiveTab] = useState<'current' | 'history' | 'replay' | 'analytics'>('current')
  const [selectedSession, setSelectedSession] = useState<ChainOfThoughtSession | null>(null)
  const [sessions, setSessions] = useState<ChainOfThoughtSession[]>([])
  const [analytics, setAnalytics] = useState<any>(null)
  const [validationSettings, setValidationSettings] = useState({
    confidenceThreshold: 0.5,
    showValidation: true,
    autoValidate: true
  })

  // Load sessions and analytics
  useEffect(() => {
    const loadedSessions = chainOfThoughtManager.getAllSessions()
    setSessions(loadedSessions)
    
    const analyticsData = chainOfThoughtManager.getOverallAnalytics()
    setAnalytics(analyticsData)
  }, [chainOfThoughtHistory])

  // Auto-create session for current reasoning
  useEffect(() => {
    if (chainOfThoughtHistory.length > 0 && !selectedSession) {
      const sessionId = chainOfThoughtManager.createSession(
        'Current Reasoning Session',
        'Active reasoning session',
        'dashboard',
        ['current', 'active']
      )
      
      // Add current steps to session
      chainOfThoughtManager.addStepsToSession(sessionId, chainOfThoughtHistory)
      
      const session = chainOfThoughtManager.getSession(sessionId)
      if (session) {
        setSelectedSession(session)
      }
    }
  }, [chainOfThoughtHistory, selectedSession])

  const getCurrentValidation = () => {
    if (chainOfThoughtHistory.length === 0) return null
    return chainOfThoughtValidator.validateChainOfThought(chainOfThoughtHistory)
  }

  const getValidationStatusIcon = (validation: any) => {
    if (!validation) return null
    
    if (validation.isValid && validation.score > 0.8) {
      return <CheckCircleIcon className="h-5 w-5 text-green-500" />
    }
    
    return <ExclamationTriangleIcon className="h-5 w-5 text-yellow-500" />
  }

  const getValidationStatusText = (validation: any) => {
    if (!validation) return 'No validation available'
    
    if (validation.isValid && validation.score > 0.8) {
      return 'High quality reasoning'
    } else if (validation.isValid) {
      return 'Valid reasoning with room for improvement'
    } else {
      return 'Reasoning has issues that need attention'
    }
  }

  const currentValidation = getCurrentValidation()

  const tabs = [
    { id: 'current', label: 'Current Reasoning', icon: DocumentTextIcon },
    { id: 'history', label: 'History', icon: ClockIcon },
    { id: 'replay', label: 'Replay', icon: PlayIcon },
    { id: 'analytics', label: 'Analytics', icon: ChartBarIcon }
  ]

  if (!showChainOfThought) {
    return (
      <Card className={`p-4 ${className}`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <DocumentTextIcon className="h-5 w-5 text-gray-400" />
            <span className="text-sm text-gray-600">Chain-of-Thought Reasoning</span>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowChainOfThought(true)}
          >
            Show Reasoning
          </Button>
        </div>
      </Card>
    )
  }

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Header */}
      <Card className="p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <DocumentTextIcon className="h-6 w-6 text-blue-600" />
            <div>
              <h2 className="text-lg font-semibold text-gray-900">Chain-of-Thought Dashboard</h2>
              <p className="text-sm text-gray-600">
                Monitor and analyze AI reasoning processes
              </p>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            {/* Validation Status */}
            {currentValidation && (
              <div className="flex items-center space-x-2 px-3 py-1 bg-gray-50 rounded-lg">
                {getValidationStatusIcon(currentValidation)}
                <span className="text-sm text-gray-700">
                  {getValidationStatusText(currentValidation)}
                </span>
                <span className="text-xs text-gray-500">
                  ({(currentValidation.score * 100).toFixed(0)}%)
                </span>
              </div>
            )}
            
            {/* Settings */}
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                // Toggle settings modal or panel
              }}
            >
              <Cog6ToothIcon className="h-4 w-4" />
            </Button>
            
            {/* Hide Button */}
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowChainOfThought(false)}
            >
              Hide
            </Button>
          </div>
        </div>
      </Card>

      {/* Quick Stats */}
      {analytics && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card className="p-4">
            <div className="flex items-center space-x-2">
              <DocumentTextIcon className="h-5 w-5 text-blue-500" />
              <div>
                <div className="text-sm text-gray-600">Total Sessions</div>
                <div className="text-lg font-semibold">{analytics.totalSessions}</div>
              </div>
            </div>
          </Card>
          
          <Card className="p-4">
            <div className="flex items-center space-x-2">
              <ChartBarIcon className="h-5 w-5 text-green-500" />
              <div>
                <div className="text-sm text-gray-600">Avg Confidence</div>
                <div className="text-lg font-semibold">
                  {(analytics.avgConfidence * 100).toFixed(0)}%
                </div>
              </div>
            </div>
          </Card>
          
          <Card className="p-4">
            <div className="flex items-center space-x-2">
              <CheckCircleIcon className="h-5 w-5 text-purple-500" />
              <div>
                <div className="text-sm text-gray-600">Avg Quality</div>
                <div className="text-lg font-semibold">
                  {(analytics.avgValidationScore * 100).toFixed(0)}%
                </div>
              </div>
            </div>
          </Card>
          
          <Card className="p-4">
            <div className="flex items-center space-x-2">
              <ClockIcon className="h-5 w-5 text-orange-500" />
              <div>
                <div className="text-sm text-gray-600">Avg Steps</div>
                <div className="text-lg font-semibold">
                  {analytics.avgSessionLength.toFixed(1)}
                </div>
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* Tab Navigation */}
      <Card className="p-1">
        <div className="flex space-x-1">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                activeTab === tab.id
                  ? 'bg-blue-100 text-blue-700'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
              }`}
            >
              <tab.icon className="h-4 w-4" />
              <span>{tab.label}</span>
            </button>
          ))}
        </div>
      </Card>

      {/* Tab Content */}
      <div className="min-h-[400px]">
        {activeTab === 'current' && (
          <div className="space-y-4">
            {chainOfThoughtHistory.length > 0 ? (
              <>
                <ChainOfThoughtDisplay
                  steps={chainOfThoughtHistory}
                  title="Current Reasoning Chain"
                  showConfidence={true}
                  showAlternatives={true}
                />
                
                {currentValidation && validationSettings.showValidation && (
                  <Card className="p-4">
                    <h3 className="text-lg font-semibold mb-3">Validation Results</h3>
                    
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                      <div className="text-center">
                        <div className="text-2xl font-bold text-blue-600">
                          {(currentValidation.score * 100).toFixed(0)}%
                        </div>
                        <div className="text-sm text-gray-600">Overall Score</div>
                      </div>
                      
                      <div className="text-center">
                        <div className="text-2xl font-bold text-green-600">
                          {currentValidation.issues.filter(i => i.severity !== 'high').length}
                        </div>
                        <div className="text-sm text-gray-600">Minor Issues</div>
                      </div>
                      
                      <div className="text-center">
                        <div className="text-2xl font-bold text-red-600">
                          {currentValidation.issues.filter(i => i.severity === 'high').length}
                        </div>
                        <div className="text-sm text-gray-600">Major Issues</div>
                      </div>
                    </div>
                    
                    {currentValidation.issues.length > 0 && (
                      <div className="space-y-2">
                        <h4 className="font-medium text-gray-900">Issues Found:</h4>
                        {currentValidation.issues.map((issue, index) => (
                          <div 
                            key={index}
                            className={`p-3 rounded-lg border-l-4 ${
                              issue.severity === 'high' 
                                ? 'bg-red-50 border-red-400'
                                : issue.severity === 'medium'
                                ? 'bg-yellow-50 border-yellow-400'
                                : 'bg-blue-50 border-blue-400'
                            }`}
                          >
                            <div className="flex items-start justify-between">
                              <div>
                                <div className="font-medium text-sm">{issue.description}</div>
                                <div className="text-xs text-gray-600 mt-1">{issue.suggestion}</div>
                              </div>
                              <span className={`text-xs px-2 py-1 rounded ${
                                issue.severity === 'high' 
                                  ? 'bg-red-100 text-red-800'
                                  : issue.severity === 'medium'
                                  ? 'bg-yellow-100 text-yellow-800'
                                  : 'bg-blue-100 text-blue-800'
                              }`}>
                                {issue.severity}
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                    
                    {currentValidation.suggestions.length > 0 && (
                      <div className="mt-4">
                        <h4 className="font-medium text-gray-900 mb-2">Suggestions:</h4>
                        <ul className="space-y-1">
                          {currentValidation.suggestions.map((suggestion, index) => (
                            <li key={index} className="text-sm text-gray-700 flex items-start">
                              <span className="text-blue-500 mr-2">•</span>
                              {suggestion}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </Card>
                )}
              </>
            ) : (
              <Card className="p-8 text-center">
                <DocumentTextIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No Active Reasoning</h3>
                <p className="text-gray-500">
                  Start interacting with the AI to see chain-of-thought reasoning appear here.
                </p>
              </Card>
            )}
          </div>
        )}

        {activeTab === 'history' && (
          <ChainOfThoughtHistory />
        )}

        {activeTab === 'replay' && (
          <div>
            {chainOfThoughtHistory.length > 0 ? (
              <ChainOfThoughtReplay
                steps={chainOfThoughtHistory}
                onStepChange={(index, step) => {
                  console.log(`Replay at step ${index}:`, step)
                }}
              />
            ) : (
              <Card className="p-8 text-center">
                <PlayIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No Reasoning to Replay</h3>
                <p className="text-gray-500">
                  Reasoning steps will be available for replay once you start interacting with the AI.
                </p>
              </Card>
            )}
          </div>
        )}

        {activeTab === 'analytics' && (
          <div className="space-y-6">
            {analytics ? (
              <>
                {/* Issue Distribution */}
                {analytics.commonIssues.length > 0 && (
                  <Card className="p-4">
                    <h3 className="text-lg font-semibold mb-4">Common Issues</h3>
                    <div className="space-y-3">
                      {analytics.commonIssues.slice(0, 5).map((issue: any, index: number) => (
                        <div key={index} className="flex items-center justify-between">
                          <div className="flex items-center space-x-3">
                            <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                            <span className="text-sm font-medium capitalize">
                              {issue.type.replace('_', ' ')}
                            </span>
                          </div>
                          <div className="flex items-center space-x-2">
                            <span className="text-sm text-gray-600">{issue.count}</span>
                            <span className="text-xs text-gray-500">
                              ({issue.percentage.toFixed(1)}%)
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </Card>
                )}

                {/* Confidence Distribution */}
                <Card className="p-4">
                  <h3 className="text-lg font-semibold mb-4">Confidence Distribution</h3>
                  <div className="space-y-3">
                    {analytics.confidenceDistribution.map((range: any, index: number) => (
                      <div key={index} className="flex items-center justify-between">
                        <span className="text-sm font-medium">{range.range}</span>
                        <div className="flex items-center space-x-2">
                          <div className="w-32 bg-gray-200 rounded-full h-2">
                            <div 
                              className="bg-blue-500 h-2 rounded-full"
                              style={{ width: `${range.percentage}%` }}
                            />
                          </div>
                          <span className="text-sm text-gray-600 w-12 text-right">
                            {range.count}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </Card>

                {/* Time Distribution */}
                <Card className="p-4">
                  <h3 className="text-lg font-semibold mb-4">Recent Activity</h3>
                  <div className="space-y-3">
                    {analytics.timeDistribution.map((period: any, index: number) => (
                      <div key={index} className="flex items-center justify-between">
                        <span className="text-sm font-medium">{period.period}</span>
                        <span className="text-sm text-gray-600">{period.count} sessions</span>
                      </div>
                    ))}
                  </div>
                </Card>
              </>
            ) : (
              <Card className="p-8 text-center">
                <ChartBarIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No Analytics Available</h3>
                <p className="text-gray-500">
                  Analytics will be generated as you use the chain-of-thought reasoning system.
                </p>
              </Card>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default ChainOfThoughtDashboard