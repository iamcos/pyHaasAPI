import React, { useState, useEffect } from 'react'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Alert } from '@/components/ui/Alert'
import { useAIStore } from '@/stores/aiStore'
import { 
  personalizationService, 
  type BehaviorPattern, 
  type AdaptationSuggestion,
  type PersonalizationMetrics 
} from '@/services/personalizationService'
import type { Persona } from '@/types'

interface PersonalizationInsightsProps {
  userId: string
  className?: string
}

export const PersonalizationInsights: React.FC<PersonalizationInsightsProps> = ({
  userId,
  className = ''
}) => {
  const { currentPersona, setCurrentPersona, addPersona } = useAIStore()
  const [insights, setInsights] = useState<{
    patterns: BehaviorPattern[]
    suggestions: AdaptationSuggestion[]
    metrics: PersonalizationMetrics
    trends: any[]
  } | null>(null)
  const [loading, setLoading] = useState(true)
  const [selectedSuggestion, setSelectedSuggestion] = useState<AdaptationSuggestion | null>(null)

  useEffect(() => {
    loadInsights()
  }, [userId])

  const loadInsights = async () => {
    setLoading(true)
    try {
      await personalizationService.loadUserData(userId)
      const userInsights = personalizationService.getLearningInsights(userId)
      setInsights(userInsights)
    } catch (error) {
      console.error('Failed to load personalization insights:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleApplySuggestion = async (suggestion: AdaptationSuggestion) => {
    try {
      const adaptedPersona = personalizationService.adaptPersona(currentPersona, suggestion)
      addPersona(adaptedPersona)
      setCurrentPersona(adaptedPersona)
      
      // Track that user accepted the suggestion
      personalizationService.trackUserAction(userId, {
        type: 'accept_suggestion',
        context: `adaptation_suggestion_${suggestion.type}`,
        personaRecommendation: suggestion.description,
        userChoice: 'accepted',
        outcome: 'positive'
      }, {
        userId,
        sessionId: `session-${Date.now()}`,
        timestamp: new Date(),
        marketConditions: {
          volatility: 0.5,
          trend: 'neutral',
          volume: 1.0
        },
        portfolioState: {
          totalValue: 10000,
          riskExposure: 0.1,
          activeStrategies: 1
        }
      })

      // Reload insights to reflect changes
      await loadInsights()
    } catch (error) {
      console.error('Failed to apply suggestion:', error)
    }
  }

  const handleRejectSuggestion = async (suggestion: AdaptationSuggestion) => {
    personalizationService.trackUserAction(userId, {
      type: 'reject_suggestion',
      context: `adaptation_suggestion_${suggestion.type}`,
      personaRecommendation: suggestion.description,
      userChoice: 'rejected',
      outcome: 'neutral'
    }, {
      userId,
      sessionId: `session-${Date.now()}`,
      timestamp: new Date(),
      marketConditions: {
        volatility: 0.5,
        trend: 'neutral',
        volume: 1.0
      },
      portfolioState: {
        totalValue: 10000,
        riskExposure: 0.1,
        activeStrategies: 1
      }
    })

    await loadInsights()
  }

  const getPatternIcon = (type: string) => {
    switch (type) {
      case 'risk_preference': return '⚖️'
      case 'timeframe_preference': return '⏰'
      case 'decision_speed': return '⚡'
      case 'optimization_focus': return '🎯'
      default: return '📊'
    }
  }

  const getPatternColor = (impact: string) => {
    switch (impact) {
      case 'high': return 'border-red-500 bg-red-50'
      case 'medium': return 'border-yellow-500 bg-yellow-50'
      case 'low': return 'border-green-500 bg-green-50'
      default: return 'border-gray-500 bg-gray-50'
    }
  }

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600'
    if (confidence >= 0.6) return 'text-yellow-600'
    return 'text-red-600'
  }

  const formatPatternType = (type: string) => {
    return type.split('_').map(word => 
      word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ')
  }

  const formatPattern = (pattern: string) => {
    return pattern.split('_').map(word => 
      word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ')
  }

  if (loading) {
    return (
      <Card className={`p-6 ${className}`}>
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-2 text-gray-600">Loading personalization insights...</p>
        </div>
      </Card>
    )
  }

  if (!insights) {
    return (
      <Card className={`p-6 ${className}`}>
        <div className="text-center text-gray-500">
          <p>No personalization data available</p>
          <p className="text-sm mt-1">Start using the system to build your profile</p>
        </div>
      </Card>
    )
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Personalization Metrics */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Personalization Metrics</h3>
        
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">
              {(insights.metrics.adaptationAccuracy * 100).toFixed(0)}%
            </div>
            <div className="text-sm text-gray-600">Adaptation Accuracy</div>
          </div>
          
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">
              {(insights.metrics.userSatisfaction * 100).toFixed(0)}%
            </div>
            <div className="text-sm text-gray-600">User Satisfaction</div>
          </div>
          
          <div className="text-center">
            <div className={`text-2xl font-bold ${
              insights.metrics.performanceImprovement > 0 ? 'text-green-600' : 'text-red-600'
            }`}>
              {insights.metrics.performanceImprovement > 0 ? '+' : ''}
              {(insights.metrics.performanceImprovement * 100).toFixed(1)}%
            </div>
            <div className="text-sm text-gray-600">Performance Change</div>
          </div>
          
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-600">
              {(insights.metrics.engagementLevel * 100).toFixed(0)}%
            </div>
            <div className="text-sm text-gray-600">Engagement Level</div>
          </div>
        </div>
      </Card>

      {/* Behavior Patterns */}
      {insights.patterns.length > 0 && (
        <Card className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Detected Behavior Patterns</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {insights.patterns.map((pattern) => (
              <div
                key={pattern.id}
                className={`p-4 rounded-lg border-2 ${getPatternColor(pattern.impact)}`}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    <span className="text-xl">{getPatternIcon(pattern.type)}</span>
                    <span className="font-medium">{formatPatternType(pattern.type)}</span>
                  </div>
                  <span className={`text-sm font-medium ${getConfidenceColor(pattern.confidence)}`}>
                    {(pattern.confidence * 100).toFixed(0)}%
                  </span>
                </div>
                
                <p className="text-sm text-gray-700 mb-2">
                  {formatPattern(pattern.pattern)}
                </p>
                
                <div className="flex justify-between text-xs text-gray-600">
                  <span>Frequency: {pattern.frequency}</span>
                  <span>Impact: {pattern.impact}</span>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Adaptation Suggestions */}
      {insights.suggestions.length > 0 && (
        <Card className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Adaptation Suggestions</h3>
          
          <div className="space-y-4">
            {insights.suggestions.map((suggestion) => (
              <div key={suggestion.id} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1">
                    <h4 className="font-medium text-gray-900">{suggestion.description}</h4>
                    <div className="flex items-center space-x-4 mt-1 text-sm text-gray-600">
                      <span className={getConfidenceColor(suggestion.confidence)}>
                        {(suggestion.confidence * 100).toFixed(0)}% confidence
                      </span>
                      <span className="text-green-600">
                        +{(suggestion.expectedImprovement * 100).toFixed(1)}% expected improvement
                      </span>
                    </div>
                  </div>
                  
                  <div className="flex space-x-2 ml-4">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleRejectSuggestion(suggestion)}
                    >
                      Reject
                    </Button>
                    <Button
                      size="sm"
                      onClick={() => handleApplySuggestion(suggestion)}
                    >
                      Apply
                    </Button>
                  </div>
                </div>
                
                {suggestion.reasoning.length > 0 && (
                  <div className="bg-gray-50 p-3 rounded text-sm">
                    <div className="font-medium text-gray-700 mb-1">Reasoning:</div>
                    <ul className="list-disc list-inside space-y-1 text-gray-600">
                      {suggestion.reasoning.map((reason, index) => (
                        <li key={index}>{reason}</li>
                      ))}
                    </ul>
                  </div>
                )}
                
                {Object.keys(suggestion.changes).length > 0 && (
                  <details className="mt-3">
                    <summary className="cursor-pointer text-sm font-medium text-gray-700 hover:text-gray-900">
                      View proposed changes
                    </summary>
                    <div className="mt-2 bg-blue-50 p-3 rounded text-sm">
                      <pre className="text-gray-700 whitespace-pre-wrap">
                        {JSON.stringify(suggestion.changes, null, 2)}
                      </pre>
                    </div>
                  </details>
                )}
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Trends */}
      {insights.trends.length > 0 && (
        <Card className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Trends</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {insights.trends.map((trend, index) => (
              <div key={index} className="bg-gray-50 p-4 rounded-lg">
                <div className="flex items-center justify-between">
                  <span className="font-medium text-gray-900">
                    {trend.type.split('_').map((word: string) => 
                      word.charAt(0).toUpperCase() + word.slice(1)
                    ).join(' ')}
                  </span>
                  <div className="flex items-center space-x-2">
                    <span className={`text-sm font-medium ${
                      trend.direction === 'increasing' || trend.direction === 'improving' 
                        ? 'text-green-600' 
                        : trend.direction === 'decreasing' || trend.direction === 'declining'
                        ? 'text-red-600'
                        : 'text-gray-600'
                    }`}>
                      {trend.direction}
                    </span>
                    <span className="text-xs text-gray-500">
                      ({(trend.confidence * 100).toFixed(0)}%)
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* No Data Message */}
      {insights.patterns.length === 0 && insights.suggestions.length === 0 && (
        <Alert 
          title="Building Your Profile"
          message="Continue using the system to generate personalized insights and recommendations. We need at least 10 interactions to start detecting patterns."
        />
      )}
    </div>
  )
}