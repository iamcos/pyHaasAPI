import React from 'react'
import { MicrophoneIcon, SpeakerWaveIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline'
import { useVoiceCommands } from '@/hooks/useVoiceCommands'
import { useAppStore } from '@/stores/appStore'

interface VoiceIndicatorProps {
  className?: string
  showDetails?: boolean
}

export function VoiceIndicator({ className = '', showDetails = false }: VoiceIndicatorProps) {
  const { 
    isSupported, 
    isListening, 
    error, 
    statistics,
    testVoiceServices,
    clearError 
  } = useVoiceCommands()
  
  const { userPreferences } = useAppStore()
  const [showTooltip, setShowTooltip] = React.useState(false)

  // Don't render if voice commands are disabled
  if (!userPreferences.accessibility.voiceCommands) {
    return null
  }

  const getStatusColor = () => {
    if (error) return 'text-red-500'
    if (isListening) return 'text-primary-500'
    if (isSupported) return 'text-green-500'
    return 'text-neutral-400'
  }

  const getStatusText = () => {
    if (error) return 'Voice Error'
    if (isListening) return 'Listening'
    if (isSupported) return 'Voice Ready'
    return 'Voice Unavailable'
  }

  const handleClick = () => {
    if (error) {
      clearError()
      testVoiceServices()
    }
  }

  return (
    <div 
      className={`relative ${className}`}
      onMouseEnter={() => setShowTooltip(true)}
      onMouseLeave={() => setShowTooltip(false)}
    >
      <div 
        className={`flex items-center space-x-2 ${error ? 'cursor-pointer' : ''}`}
        onClick={handleClick}
      >
        {/* Voice status icon */}
        <div className={`relative ${getStatusColor()}`}>
          {isListening ? (
            <MicrophoneIcon className="h-4 w-4 animate-pulse" />
          ) : error ? (
            <ExclamationTriangleIcon className="h-4 w-4" />
          ) : (
            <SpeakerWaveIcon className="h-4 w-4" />
          )}
          
          {/* Listening animation */}
          {isListening && (
            <div className="absolute -inset-1 rounded-full border-2 border-primary-500 animate-ping opacity-75" />
          )}
        </div>

        {/* Status text (if details enabled) */}
        {showDetails && (
          <span className={`text-xs font-medium ${getStatusColor()}`}>
            {getStatusText()}
          </span>
        )}
      </div>

      {/* Tooltip */}
      {showTooltip && (
        <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 z-50">
          <div className="bg-neutral-900 text-white text-xs rounded-lg px-3 py-2 whitespace-nowrap">
            <div className="font-medium">{getStatusText()}</div>
            
            {error && (
              <div className="text-red-300 mt-1">{error}</div>
            )}
            
            {statistics && statistics.totalCommands > 0 && (
              <div className="text-neutral-300 mt-1">
                {statistics.totalCommands} commands • {Math.round(statistics.successRate * 100)}% success
              </div>
            )}
            
            {isSupported && !error && (
              <div className="text-neutral-300 mt-1">
                {isListening ? 'Click microphone to stop' : 'Voice commands ready'}
              </div>
            )}
            
            {error && (
              <div className="text-yellow-300 mt-1">
                Click to retry
              </div>
            )}
            
            {/* Tooltip arrow */}
            <div className="absolute top-full left-1/2 transform -translate-x-1/2">
              <div className="border-4 border-transparent border-t-neutral-900"></div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

// Compact version for header/status bar
export function VoiceStatusDot({ className = '' }: { className?: string }) {
  const { isSupported, isListening, error } = useVoiceCommands()
  const { userPreferences } = useAppStore()

  if (!userPreferences.accessibility.voiceCommands) {
    return null
  }

  const getStatusColor = () => {
    if (error) return 'bg-red-500'
    if (isListening) return 'bg-primary-500'
    if (isSupported) return 'bg-green-500'
    return 'bg-neutral-400'
  }

  return (
    <div className={`relative ${className}`}>
      <div className={`w-2 h-2 rounded-full ${getStatusColor()}`}>
        {isListening && (
          <div className="absolute inset-0 rounded-full bg-primary-500 animate-ping opacity-75" />
        )}
      </div>
    </div>
  )
}

// Voice command help overlay
export function VoiceCommandHelp({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) {
  if (!isOpen) return null

  const voiceCommands = [
    { command: 'Create strategy', description: 'Start building a new trading strategy' },
    { command: 'Show dashboard', description: 'Navigate to the main dashboard' },
    { command: 'Analyze Bitcoin', description: 'Perform market analysis on BTC' },
    { command: 'Check portfolio risk', description: 'Display risk assessment' },
    { command: 'Start optimization', description: 'Begin strategy optimization workflow' },
    { command: 'Show active bots', description: 'Display currently running trading bots' },
    { command: 'Market sentiment', description: 'Get current market sentiment analysis' },
    { command: 'Generate report', description: 'Create performance or analysis report' }
  ]

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
        <div className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-neutral-900 flex items-center space-x-2">
              <MicrophoneIcon className="h-5 w-5" />
              <span>Voice Commands</span>
            </h3>
            <button
              onClick={onClose}
              className="text-neutral-400 hover:text-neutral-600"
            >
              <span className="sr-only">Close</span>
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <div className="space-y-3">
            <p className="text-sm text-neutral-600">
              Try these voice commands to interact with the trading interface:
            </p>
            
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {voiceCommands.map((item, index) => (
                <div key={index} className="flex flex-col space-y-1 p-2 bg-neutral-50 rounded-md">
                  <div className="font-medium text-sm text-neutral-900">
                    "{item.command}"
                  </div>
                  <div className="text-xs text-neutral-600">
                    {item.description}
                  </div>
                </div>
              ))}
            </div>

            <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-md">
              <div className="text-sm text-blue-800">
                <strong>Tips:</strong>
                <ul className="mt-1 space-y-1 text-xs">
                  <li>• Speak clearly and at normal pace</li>
                  <li>• Use specific terms like "BTC", "strategy", "analyze"</li>
                  <li>• Wait for the listening indicator before speaking</li>
                  <li>• Commands are processed automatically when you finish</li>
                </ul>
              </div>
            </div>
          </div>

          <div className="mt-6 flex justify-end">
            <button
              onClick={onClose}
              className="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 transition-colors"
            >
              Got it
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}