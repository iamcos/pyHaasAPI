import React, { useState, useEffect } from 'react'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { useAIStore } from '@/stores/aiStore'
import { personaService, type PersonaInfluence, type DecisionContext } from '@/services/personaService'
import type { Persona } from '@/types'

interface PersonaDashboardProps {
  className?: string
}

export const PersonaDashboard: React.FC<PersonaDashboardProps> = ({ className = '' }) => {
  const { currentPersona, currentStrategyAnalysis, currentMarketAnalysis } = useAIStore()
  const [personaInfluence, setPersonaInfluence] = useState<PersonaInfluence | null>(null)
  const [recentDecisions, setRecentDecisions] = useState<any[]>([])

  useEffect(() => {
    if (currentPersona) {
      const influence = personaService.calculatePersonaInfluence(currentPersona)
      setPersonaInfluence(influence)
    }
  }, [currentPersona])

  const handleTestDecision = async (type: DecisionContext['type']) => {
    const mockContext: DecisionContext = {
      type,
      data: type === 'strategy_creation' ? { description: 'Test strategy' } : {},
      currentConditions: {
        marketVolatility: 0.6,
        portfolioRisk: 0.12,
        recentPerformance: 0.08
      }
    }

    const decision = personaService.makePersonaDecision(mockContext, currentPersona)
    
    setRecentDecisions(prev => [
      {
        id: Date.now(),
        type,
        decision,
        timestamp: new Date()
      },
      ...prev.slice(0, 4) // Keep only last 5 decisions
    ])
  }

  const getPersonaIcon = (type: Persona['type']) => {
    switch (type) {
      case 'conservative': return '🛡️'
      case 'balanced': return '⚖️'
      case 'aggressive': return '🚀'
      case 'custom': return '⚙️'
      default: return '👤'
    }
  }

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600'
    if (confidence >= 0.6) return 'text-yellow-600'
    return 'text-red-600'
  }

  const formatDecisionType = (type: string) => {
    return type.split('_').map(word => 
      word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ')
  }

  if (!currentPersona || !personaInfluence) {
    return (
      <Card className={`p-6 ${className}`}>
        <div className="text-center text-gray-500">
          <p>No persona selected</p>
        </div>
      </Card>
    )
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Current Persona Overview */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <span className="text-3xl">{getPersonaIcon(currentPersona.type)}</span>
            <div>
              <h3 className="text-xl font-semibold text-gray-900">{currentPersona.name}</h3>
              <p className="text-sm text-gray-600">{currentPersona.description}</p>
            </div>
          </div>
          <div className="text-right">
            <div className="text-sm text-gray-600">Risk Tolerance</div>
            <div className="text-2xl font-bold text-blue-600">
              {(currentPersona.riskTolerance * 100).toFixed(0)}%
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-gray-50 p-4 rounded-lg">
            <h4 className="font-medium text-gray-900 mb-2">Decision Style</h4>
            <p className="text-sm text-gray-600 capitalize">{currentPersona.decisionSpeed}</p>
            <p className="text-sm text-gray-600 capitalize">{currentPersona.optimizationStyle.replace('_', ' ')}</p>
          </div>
          
          <div className="bg-gray-50 p-4 rounded-lg">
            <h4 className="font-medium text-gray-900 mb-2">Optimization Focus</h4>
            <p className="text-sm text-gray-600 capitalize">
              {currentPersona.preferences.optimizationFocus.replace('_', ' ')}
            </p>
            <p className="text-sm text-gray-600">
              Alerts: {currentPersona.preferences.alertFrequency}
            </p>
          </div>
          
          <div className="bg-gray-50 p-4 rounded-lg">
            <h4 className="font-medium text-gray-900 mb-2">Risk Limits</h4>
            <p className="text-xs text-gray-600">
              Max Drawdown: {(currentPersona.preferences.riskLimits.maxDrawdown * 100).toFixed(1)}%
            </p>
            <p className="text-xs text-gray-600">
              Max Position: {(currentPersona.preferences.riskLimits.maxPositionSize * 100).toFixed(1)}%
            </p>
            <p className="text-xs text-gray-600">
              Max Correlation: {(currentPersona.preferences.riskLimits.maxCorrelation * 100).toFixed(0)}%
            </p>
          </div>
        </div>
      </Card>

      {/* Persona Influence Metrics */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Decision Influence</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h4 className="font-medium text-gray-900 mb-3">Optimization Weights</h4>
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Return Focus</span>
                <div className="flex items-center space-x-2">
                  <div className="w-20 bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-blue-600 h-2 rounded-full" 
                      style={{ width: `${personaInfluence.optimizationWeight.return * 100}%` }}
                    />
                  </div>
                  <span className="text-sm font-medium">
                    {(personaInfluence.optimizationWeight.return * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
              
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Risk Focus</span>
                <div className="flex items-center space-x-2">
                  <div className="w-20 bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-yellow-600 h-2 rounded-full" 
                      style={{ width: `${personaInfluence.optimizationWeight.risk * 100}%` }}
                    />
                  </div>
                  <span className="text-sm font-medium">
                    {(personaInfluence.optimizationWeight.risk * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
              
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Consistency Focus</span>
                <div className="flex items-center space-x-2">
                  <div className="w-20 bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-green-600 h-2 rounded-full" 
                      style={{ width: `${personaInfluence.optimizationWeight.consistency * 100}%` }}
                    />
                  </div>
                  <span className="text-sm font-medium">
                    {(personaInfluence.optimizationWeight.consistency * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
            </div>
          </div>

          <div>
            <h4 className="font-medium text-gray-900 mb-3">Decision Thresholds</h4>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Alert Threshold</span>
                <span className="text-sm font-medium">
                  {(personaInfluence.alertThreshold * 100).toFixed(0)}%
                </span>
              </div>
              
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Confidence Required</span>
                <span className="text-sm font-medium">
                  {(personaInfluence.decisionConfidenceRequired * 100).toFixed(0)}%
                </span>
              </div>
              
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Preferred Timeframes</span>
                <div className="flex space-x-1">
                  {personaInfluence.timeframePreference.slice(0, 3).map((tf) => (
                    <span key={tf} className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                      {tf}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </Card>

      {/* Decision Testing */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Test Persona Decisions</h3>
        
        <div className="flex flex-wrap gap-2 mb-4">
          <Button
            size="sm"
            variant="outline"
            onClick={() => handleTestDecision('strategy_creation')}
          >
            Test Strategy Decision
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={() => handleTestDecision('risk_assessment')}
          >
            Test Risk Assessment
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={() => handleTestDecision('optimization')}
          >
            Test Optimization
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={() => handleTestDecision('market_analysis')}
          >
            Test Market Analysis
          </Button>
        </div>

        {recentDecisions.length > 0 && (
          <div className="space-y-3">
            <h4 className="font-medium text-gray-900">Recent Decisions</h4>
            {recentDecisions.map((item) => (
              <div key={item.id} className="bg-gray-50 p-4 rounded-lg">
                <div className="flex justify-between items-start mb-2">
                  <span className="font-medium text-sm">
                    {formatDecisionType(item.type)}
                  </span>
                  <span className={`text-sm font-medium ${getConfidenceColor(item.decision.confidence)}`}>
                    {(item.decision.confidence * 100).toFixed(0)}% confidence
                  </span>
                </div>
                <p className="text-sm text-gray-700 mb-2">{item.decision.recommendation}</p>
                
                {item.decision.reasoning.length > 0 && (
                  <details className="text-xs text-gray-600">
                    <summary className="cursor-pointer hover:text-gray-800">
                      View reasoning ({item.decision.reasoning.length} steps)
                    </summary>
                    <div className="mt-2 space-y-1 pl-4">
                      {item.decision.reasoning.map((step: any) => (
                        <div key={step.id} className="border-l-2 border-gray-300 pl-2">
                          <span className="font-medium">Step {step.step}:</span> {step.reasoning}
                        </div>
                      ))}
                    </div>
                  </details>
                )}
                
                <div className="text-xs text-gray-500 mt-2">
                  {item.timestamp.toLocaleTimeString()}
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* Current Analysis Influence */}
      {(currentStrategyAnalysis || currentMarketAnalysis) && (
        <Card className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Active Analysis Influence</h3>
          
          {currentStrategyAnalysis && (
            <div className="mb-4">
              <h4 className="font-medium text-gray-900 mb-2">Strategy Analysis</h4>
              <div className="bg-blue-50 p-3 rounded-lg">
                <p className="text-sm text-gray-700">
                  Persona has adjusted risk assessment and recommendations based on {currentPersona.name} preferences.
                </p>
                <div className="mt-2 text-xs text-gray-600">
                  Expected return adjusted by {(personaInfluence.optimizationWeight.return * 100).toFixed(0)}% weight
                </div>
              </div>
            </div>
          )}
          
          {currentMarketAnalysis && (
            <div>
              <h4 className="font-medium text-gray-900 mb-2">Market Analysis</h4>
              <div className="bg-green-50 p-3 rounded-lg">
                <p className="text-sm text-gray-700">
                  Market opportunities filtered based on {currentPersona.name} risk tolerance of {(currentPersona.riskTolerance * 100).toFixed(0)}%.
                </p>
                <div className="mt-2 text-xs text-gray-600">
                  Confidence adjusted for {currentPersona.decisionSpeed} decision speed
                </div>
              </div>
            </div>
          )}
        </Card>
      )}
    </div>
  )
}