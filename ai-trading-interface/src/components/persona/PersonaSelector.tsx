import React, { useState } from 'react'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Modal } from '@/components/ui/Modal'
import { useAIStore } from '@/stores/aiStore'
import { personaService } from '@/services/personaService'
import type { Persona } from '@/types'

interface PersonaSelectorProps {
  onPersonaSelect?: (persona: Persona) => void
  showCreateCustom?: boolean
}

export const PersonaSelector: React.FC<PersonaSelectorProps> = ({
  onPersonaSelect,
  showCreateCustom = true
}) => {
  const {
    currentPersona,
    availablePersonas,
    setCurrentPersona,
    addPersona
  } = useAIStore()

  const [showCustomModal, setShowCustomModal] = useState(false)
  const [customPersonaData, setCustomPersonaData] = useState({
    name: '',
    riskTolerance: 0.5,
    tradingStyle: 'swing_trading' as const,
    focusArea: 'growth' as const,
    timeCommitment: 'moderate' as const
  })

  const handlePersonaSelect = (persona: Persona) => {
    setCurrentPersona(persona)
    onPersonaSelect?.(persona)
  }

  const handleCreateCustomPersona = () => {
    if (!customPersonaData.name.trim()) return

    const customPersona = personaService.createCustomPersona(
      customPersonaData.name,
      {
        riskTolerance: customPersonaData.riskTolerance,
        tradingStyle: customPersonaData.tradingStyle,
        focusArea: customPersonaData.focusArea,
        timeCommitment: customPersonaData.timeCommitment
      }
    )

    addPersona(customPersona)
    handlePersonaSelect(customPersona)
    setShowCustomModal(false)
    
    // Reset form
    setCustomPersonaData({
      name: '',
      riskTolerance: 0.5,
      tradingStyle: 'swing_trading',
      focusArea: 'growth',
      timeCommitment: 'moderate'
    })
  }

  const getPersonaIcon = (type: Persona['type']) => {
    switch (type) {
      case 'conservative':
        return '🛡️'
      case 'balanced':
        return '⚖️'
      case 'aggressive':
        return '🚀'
      case 'custom':
        return '⚙️'
      default:
        return '👤'
    }
  }

  const getPersonaColor = (type: Persona['type']) => {
    switch (type) {
      case 'conservative':
        return 'border-green-500 bg-green-50'
      case 'balanced':
        return 'border-blue-500 bg-blue-50'
      case 'aggressive':
        return 'border-red-500 bg-red-50'
      case 'custom':
        return 'border-purple-500 bg-purple-50'
      default:
        return 'border-gray-500 bg-gray-50'
    }
  }

  const getRiskLabel = (riskTolerance: number) => {
    if (riskTolerance < 0.3) return 'Low Risk'
    if (riskTolerance < 0.7) return 'Medium Risk'
    return 'High Risk'
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">Trading Persona</h3>
        {showCreateCustom && (
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowCustomModal(true)}
          >
            Create Custom
          </Button>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {availablePersonas.map((persona) => (
          <Card
            key={persona.id}
            className={`cursor-pointer transition-all duration-200 hover:shadow-md ${
              currentPersona.id === persona.id
                ? `ring-2 ring-offset-2 ${getPersonaColor(persona.type)} ring-opacity-50`
                : 'hover:shadow-lg'
            } ${getPersonaColor(persona.type)}`}
            onClick={() => handlePersonaSelect(persona)}
          >
            <div className="p-4">
              <div className="flex items-center space-x-3 mb-3">
                <span className="text-2xl">{getPersonaIcon(persona.type)}</span>
                <div>
                  <h4 className="font-semibold text-gray-900">{persona.name}</h4>
                  <p className="text-sm text-gray-600">{getRiskLabel(persona.riskTolerance)}</p>
                </div>
              </div>
              
              <p className="text-sm text-gray-700 mb-3">{persona.description}</p>
              
              <div className="space-y-2">
                <div className="flex justify-between text-xs">
                  <span className="text-gray-600">Risk Tolerance:</span>
                  <span className="font-medium">{(persona.riskTolerance * 100).toFixed(0)}%</span>
                </div>
                
                <div className="flex justify-between text-xs">
                  <span className="text-gray-600">Decision Speed:</span>
                  <span className="font-medium capitalize">{persona.decisionSpeed}</span>
                </div>
                
                <div className="flex justify-between text-xs">
                  <span className="text-gray-600">Focus:</span>
                  <span className="font-medium capitalize">
                    {persona.preferences.optimizationFocus.replace('_', ' ')}
                  </span>
                </div>
                
                <div className="text-xs">
                  <span className="text-gray-600">Timeframes:</span>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {persona.preferences.preferredTimeframes.map((tf) => (
                      <span
                        key={tf}
                        className="px-2 py-1 bg-white rounded text-xs font-medium"
                      >
                        {tf}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </Card>
        ))}
      </div>

      {/* Custom Persona Creation Modal */}
      <Modal
        open={showCustomModal}
        onClose={() => setShowCustomModal(false)}
        title="Create Custom Persona"
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Persona Name
            </label>
            <input
              type="text"
              value={customPersonaData.name}
              onChange={(e) => setCustomPersonaData(prev => ({ ...prev, name: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="My Trading Persona"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Risk Tolerance: {(customPersonaData.riskTolerance * 100).toFixed(0)}%
            </label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              value={customPersonaData.riskTolerance}
              onChange={(e) => setCustomPersonaData(prev => ({ 
                ...prev, 
                riskTolerance: parseFloat(e.target.value) 
              }))}
              className="w-full"
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>Conservative</span>
              <span>Aggressive</span>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Trading Style
            </label>
            <select
              value={customPersonaData.tradingStyle}
              onChange={(e) => setCustomPersonaData(prev => ({ 
                ...prev, 
                tradingStyle: e.target.value as any 
              }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="scalping">Scalping (1m-15m)</option>
              <option value="day_trading">Day Trading (15m-4h)</option>
              <option value="swing_trading">Swing Trading (4h-3d)</option>
              <option value="position_trading">Position Trading (1d-1M)</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Focus Area
            </label>
            <select
              value={customPersonaData.focusArea}
              onChange={(e) => setCustomPersonaData(prev => ({ 
                ...prev, 
                focusArea: e.target.value as any 
              }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="growth">Growth (Maximum Returns)</option>
              <option value="income">Income (Risk-Adjusted Returns)</option>
              <option value="preservation">Preservation (Capital Safety)</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Time Commitment
            </label>
            <select
              value={customPersonaData.timeCommitment}
              onChange={(e) => setCustomPersonaData(prev => ({ 
                ...prev, 
                timeCommitment: e.target.value as any 
              }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="minimal">Minimal (Few alerts)</option>
              <option value="moderate">Moderate (Balanced alerts)</option>
              <option value="intensive">Intensive (Frequent monitoring)</option>
            </select>
          </div>

          <div className="flex space-x-3 pt-4">
            <Button
              variant="outline"
              onClick={() => setShowCustomModal(false)}
              className="flex-1"
            >
              Cancel
            </Button>
            <Button
              onClick={handleCreateCustomPersona}
              disabled={!customPersonaData.name.trim()}
              className="flex-1"
            >
              Create Persona
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}