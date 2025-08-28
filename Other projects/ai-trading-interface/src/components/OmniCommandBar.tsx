import React from 'react'
import { MagnifyingGlassIcon, MicrophoneIcon, ExclamationTriangleIcon, CheckCircleIcon, Cog6ToothIcon } from '@heroicons/react/24/outline'
import { useAppStore } from '@/stores/appStore'
import { useAIStore } from '@/stores/aiStore'
import { commandProcessor } from '@/services/commandProcessor'
import { commandValidator } from '@/services/commandValidator'
import { voiceCommandService } from '@/services/voiceCommandService'
import { VoiceSettings } from '@/components/voice/VoiceSettings'
import type { Suggestion, CommandResult } from '@/types'

export function OmniCommandBar() {
  const [query, setQuery] = React.useState('')
  const [isListening, setIsListening] = React.useState(false)
  const [isProcessing, setIsProcessing] = React.useState(false)
  const [suggestions, setSuggestions] = React.useState<Suggestion[]>([])
  const [validationResult, setValidationResult] = React.useState<any>(null)
  const [commandHistory, setCommandHistory] = React.useState<string[]>([])
  const [historyIndex, setHistoryIndex] = React.useState(-1)
  const [showSuggestions, setShowSuggestions] = React.useState(false)
  const [showVoiceSettings, setShowVoiceSettings] = React.useState(false)
  const [voiceError, setVoiceError] = React.useState<string | null>(null)
  const [interimTranscript, setInterimTranscript] = React.useState('')
  
  const { userPreferences, uiContext } = useAppStore()
  const { isProcessing: aiProcessing } = useAIStore()

  // Generate context-aware suggestions
  React.useEffect(() => {
    const generateSuggestions = async () => {
      if (query.length > 1) {
        try {
          const contextSuggestions = await commandProcessor.generateSuggestions(query, uiContext)
          setSuggestions(contextSuggestions)
          setShowSuggestions(true)
        } catch (error) {
          console.error('Failed to generate suggestions:', error)
          setSuggestions([])
        }
      } else {
        setSuggestions([])
        setShowSuggestions(false)
      }
    }

    const debounceTimer = setTimeout(generateSuggestions, 300)
    return () => clearTimeout(debounceTimer)
  }, [query, uiContext])

  // Real-time command validation
  React.useEffect(() => {
    const validateCommand = async () => {
      if (query.length > 3) {
        try {
          // Quick intent classification for validation
          const intent = await commandProcessor['classifyIntent'](query, uiContext)
          const entities = commandProcessor['extractEntities'](query, intent)
          const validation = await commandValidator.validateCommand(query, intent, entities, uiContext)
          setValidationResult(validation)
        } catch (error) {
          console.error('Command validation failed:', error)
          setValidationResult(null)
        }
      } else {
        setValidationResult(null)
      }
    }

    const debounceTimer = setTimeout(validateCommand, 500)
    return () => clearTimeout(debounceTimer)
  }, [query, uiContext])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (query.trim() && !isProcessing) {
      setIsProcessing(true)
      setShowSuggestions(false)
      
      try {
        // Add to command history
        const newHistory = [query, ...commandHistory.slice(0, 19)] // Keep last 20 commands
        setCommandHistory(newHistory)
        setHistoryIndex(-1)

        // Process the command
        const result: CommandResult = await commandProcessor.processCommand(query.trim(), uiContext)
        
        // Handle the result based on type
        await handleCommandResult(result)
        
        // Clear the input
        setQuery('')
        setValidationResult(null)
        
      } catch (error) {
        console.error('Command processing failed:', error)
        // Show error feedback to user
        setValidationResult({
          isValid: false,
          errors: [{ type: 'logic', message: 'Failed to process command', severity: 'error' }],
          warnings: [],
          suggestions: [],
          confidence: 0.1
        })
      } finally {
        setIsProcessing(false)
      }
    }
  }

  // Handle command results
  const handleCommandResult = async (result: CommandResult) => {
    switch (result.type) {
      case 'navigation':
        // Navigation is handled by the command processor updating the store
        console.log('Navigation completed:', result.payload)
        break
        
      case 'ui_generation':
        // Trigger UI generation based on the result
        console.log('UI generation requested:', result.payload)
        // This would integrate with the generative UI engine
        break
        
      case 'data_query':
        // Handle data queries
        console.log('Data query processed:', result.payload)
        break
        
      case 'workflow_trigger':
        // Handle workflow triggers
        console.log('Workflow triggered:', result.payload)
        break
        
      default:
        console.log('Command result:', result)
    }

    // Add proactive actions to AI store if any
    if (result.proactiveActions && result.proactiveActions.length > 0) {
      const aiStore = useAIStore.getState()
      result.proactiveActions.forEach(action => {
        aiStore.addProactiveAction(action)
      })
    }

    // Add chain of thought steps if any
    if (result.chainOfThought && result.chainOfThought.length > 0) {
      const aiStore = useAIStore.getState()
      result.chainOfThought.forEach(step => {
        aiStore.addChainOfThoughtStep(step)
      })
    }
  }

  const handleVoiceInput = async () => {
    if (!userPreferences.accessibility.voiceCommands) {
      setVoiceError('Voice commands not enabled in settings')
      return
    }

    if (!voiceCommandService.isSupported()) {
      setVoiceError('Voice commands not supported in this browser')
      return
    }

    if (isListening) {
      // Stop listening if already active
      voiceCommandService.stopListening()
      setIsListening(false)
      setInterimTranscript('')
      return
    }

    // Clear previous errors
    setVoiceError(null)
    setValidationResult(null)
    setShowSuggestions(false)

    try {
      await voiceCommandService.startListening(
        // onResult callback
        (result) => {
          if (result.success) {
            // Show interim results in real-time
            const displayText = result.transcript
            setQuery(displayText)
            setInterimTranscript(result.transcript)

            // Clear any previous errors
            setVoiceError(null)
          } else {
            setVoiceError(result.error || 'Voice recognition failed')
          }
        },
        // onError callback
        (error) => {
          setIsListening(false)
          setVoiceError(error)
          setInterimTranscript('')
          
          // Show error in validation result for user feedback
          setValidationResult({
            isValid: false,
            errors: [{ type: 'data', message: error, severity: 'error' }],
            warnings: [],
            suggestions: [{ 
              type: 'alternative', 
              message: 'Check microphone permissions and try again', 
              confidence: 0.8 
            }],
            confidence: 0.1
          })
        },
        // onStart callback
        () => {
          setIsListening(true)
          setInterimTranscript('')
          voiceCommandService.provideFeedback('Listening...', 'low')
        },
        // onEnd callback
        () => {
          setIsListening(false)
          setInterimTranscript('')
          
          // Auto-submit if we have a good transcript
          if (query.trim().length > 3) {
            setTimeout(() => {
              const form = document.querySelector('form')
              if (form) {
                form.dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }))
              }
            }, 500) // Small delay to ensure transcript is processed
          }
        }
      )
    } catch (error) {
      setIsListening(false)
      setVoiceError('Failed to start voice recognition')
      console.error('Voice input failed:', error)
    }
  }

  // Handle keyboard navigation
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowUp') {
      e.preventDefault()
      if (commandHistory.length > 0) {
        const newIndex = Math.min(historyIndex + 1, commandHistory.length - 1)
        setHistoryIndex(newIndex)
        setQuery(commandHistory[newIndex])
        setShowSuggestions(false)
      }
    } else if (e.key === 'ArrowDown') {
      e.preventDefault()
      if (historyIndex > 0) {
        const newIndex = historyIndex - 1
        setHistoryIndex(newIndex)
        setQuery(commandHistory[newIndex])
        setShowSuggestions(false)
      } else if (historyIndex === 0) {
        setHistoryIndex(-1)
        setQuery('')
        setShowSuggestions(false)
      }
    } else if (e.key === 'Escape') {
      setShowSuggestions(false)
      setValidationResult(null)
    } else if (e.key === 'Tab' && suggestions.length > 0) {
      e.preventDefault()
      const firstSuggestion = suggestions[0]
      setQuery(firstSuggestion.text)
      setShowSuggestions(false)
    }
  }

  // Handle suggestion selection
  const handleSuggestionClick = (suggestion: Suggestion) => {
    setQuery(suggestion.text)
    setShowSuggestions(false)
    // Auto-submit high-confidence suggestions
    if (suggestion.confidence > 0.8 && suggestion.type === 'command') {
      setTimeout(() => {
        const form = document.querySelector('form')
        if (form) {
          form.dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }))
        }
      }, 100)
    }
  }

  return (
    <div className="bg-white border-b border-neutral-200 px-4 py-3">
      <div className="max-w-4xl mx-auto">
        <form onSubmit={handleSubmit} className="relative">
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <MagnifyingGlassIcon className={`h-5 w-5 ${
                isProcessing || aiProcessing ? 'text-primary-500 animate-pulse' : 'text-neutral-400'
              }`} />
            </div>
            
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={isProcessing || aiProcessing}
              className={`block w-full pl-10 pr-20 py-3 border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent placeholder-neutral-500 text-sm transition-colors ${
                validationResult?.isValid === false 
                  ? 'border-red-300 bg-red-50' 
                  : validationResult?.isValid === true 
                    ? 'border-green-300 bg-green-50'
                    : 'border-neutral-300'
              } ${isProcessing || aiProcessing ? 'opacity-50 cursor-not-allowed' : ''}`}
              placeholder={isListening 
                ? 'Listening...' 
                : "Ask AI anything about your trading... (e.g., 'Create a momentum strategy for BTC' or 'Show my portfolio risk')"
              }
            />
            
            <div className="absolute inset-y-0 right-0 pr-3 flex items-center space-x-2">
              {/* Validation indicator */}
              {validationResult && (
                <div className="flex items-center">
                  {validationResult.isValid ? (
                    <CheckCircleIcon className="h-4 w-4 text-green-500" />
                  ) : (
                    <ExclamationTriangleIcon className="h-4 w-4 text-red-500" />
                  )}
                </div>
              )}
              
              {/* Voice settings button */}
              {userPreferences.accessibility.voiceCommands && (
                <button
                  type="button"
                  onClick={() => setShowVoiceSettings(true)}
                  className="p-1 rounded-md text-neutral-400 hover:text-neutral-600 transition-colors duration-200"
                  title="Voice settings"
                >
                  <span className="sr-only">Voice settings</span>
                  <Cog6ToothIcon className="h-3 w-3" />
                </button>
              )}
              
              {/* Voice input button */}
              {userPreferences.accessibility.voiceCommands && (
                <button
                  type="button"
                  onClick={handleVoiceInput}
                  disabled={isProcessing || aiProcessing}
                  className={`p-2 rounded-md transition-colors duration-200 ${
                    isListening 
                      ? 'text-primary-600 bg-primary-100 animate-pulse' 
                      : voiceError
                        ? 'text-red-500 hover:text-red-600'
                        : 'text-neutral-400 hover:text-neutral-600'
                  } ${isProcessing || aiProcessing ? 'opacity-50 cursor-not-allowed' : ''}`}
                  title={isListening ? 'Stop listening' : 'Start voice input'}
                >
                  <span className="sr-only">{isListening ? 'Stop listening' : 'Voice input'}</span>
                  <MicrophoneIcon className="h-4 w-4" />
                </button>
              )}
            </div>
          </div>

          {/* Voice error feedback */}
          {voiceError && (
            <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded-md">
              <div className="text-sm text-red-700 flex items-start space-x-1">
                <ExclamationTriangleIcon className="h-4 w-4 text-red-500 mt-0.5 flex-shrink-0" />
                <span>{voiceError}</span>
              </div>
            </div>
          )}

          {/* Interim transcript feedback */}
          {isListening && interimTranscript && (
            <div className="mt-2 p-2 bg-blue-50 border border-blue-200 rounded-md">
              <div className="text-sm text-blue-700 flex items-start space-x-1">
                <MicrophoneIcon className="h-4 w-4 text-blue-500 mt-0.5 flex-shrink-0 animate-pulse" />
                <span>Listening: "{interimTranscript}"</span>
              </div>
            </div>
          )}

          {/* Validation feedback */}
          {validationResult && !validationResult.isValid && !voiceError && (
            <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded-md">
              <div className="text-sm text-red-700">
                {validationResult.errors.map((error: any, index: number) => (
                  <div key={index} className="flex items-start space-x-1">
                    <ExclamationTriangleIcon className="h-4 w-4 text-red-500 mt-0.5 flex-shrink-0" />
                    <span>{error.message}</span>
                  </div>
                ))}
              </div>
              {validationResult.suggestions.length > 0 && (
                <div className="mt-1 text-xs text-red-600">
                  Suggestions: {validationResult.suggestions.map((s: any) => s.message).join(', ')}
                </div>
              )}
            </div>
          )}

          {/* Suggestions dropdown */}
          {showSuggestions && suggestions.length > 0 && (
            <div className="absolute z-10 mt-1 w-full bg-white shadow-lg max-h-60 rounded-md py-1 text-base ring-1 ring-black ring-opacity-5 overflow-auto focus:outline-none sm:text-sm">
              {suggestions.map((suggestion, index) => (
                <button
                  key={suggestion.id}
                  type="button"
                  onClick={() => handleSuggestionClick(suggestion)}
                  className="w-full text-left px-4 py-2 text-sm text-neutral-900 hover:bg-neutral-100 focus:bg-neutral-100 focus:outline-none flex items-center justify-between"
                >
                  <div className="flex items-center space-x-2">
                    {suggestion.icon && <span className="text-base">{suggestion.icon}</span>}
                    <span>{suggestion.text}</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="text-xs text-neutral-500 capitalize">{suggestion.type}</span>
                    <div className={`w-2 h-2 rounded-full ${
                      suggestion.confidence > 0.8 ? 'bg-green-400' :
                      suggestion.confidence > 0.6 ? 'bg-yellow-400' : 'bg-red-400'
                    }`} />
                  </div>
                </button>
              ))}
            </div>
          )}
        </form>

        {/* Quick actions */}
        <div className="mt-3 flex flex-wrap gap-2">
          {[
            { text: 'Show Dashboard', icon: '📊' },
            { text: 'Create Strategy', icon: '🚀' },
            { text: 'Market Analysis', icon: '📈' },
            { text: 'Risk Check', icon: '⚠️' },
            { text: 'Bot Status', icon: '🤖' },
          ].map((action) => (
            <button
              key={action.text}
              onClick={() => setQuery(action.text)}
              disabled={isProcessing || aiProcessing}
              className={`inline-flex items-center space-x-1 px-3 py-1 rounded-full text-xs font-medium bg-neutral-100 text-neutral-700 hover:bg-neutral-200 transition-colors duration-200 ${
                isProcessing || aiProcessing ? 'opacity-50 cursor-not-allowed' : ''
              }`}
            >
              <span>{action.icon}</span>
              <span>{action.text}</span>
            </button>
          ))}
        </div>

        {/* Processing indicator */}
        {(isProcessing || aiProcessing) && (
          <div className="mt-2 flex items-center space-x-2 text-sm text-neutral-600">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary-500"></div>
            <span>Processing your command...</span>
          </div>
        )}

        {/* Command history hint */}
        {commandHistory.length > 0 && !isProcessing && !aiProcessing && !isListening && (
          <div className="mt-2 text-xs text-neutral-500">
            Use ↑/↓ arrows to navigate command history • Press Tab to accept first suggestion • Press Esc to clear
            {userPreferences.accessibility.voiceCommands && ' • Click microphone for voice input'}
          </div>
        )}

        {/* Voice listening indicator */}
        {isListening && (
          <div className="mt-2 text-xs text-blue-600 flex items-center space-x-2">
            <div className="flex space-x-1">
              <div className="w-1 h-1 bg-blue-500 rounded-full animate-bounce"></div>
              <div className="w-1 h-1 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
              <div className="w-1 h-1 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
            </div>
            <span>Listening for voice commands... Click microphone to stop</span>
          </div>
        )}
      </div>

      {/* Voice Settings Modal */}
      <VoiceSettings
        isOpen={showVoiceSettings}
        onClose={() => setShowVoiceSettings(false)}
      />
    </div>
  )
}