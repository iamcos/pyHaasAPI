import React from 'react'
import { voiceCommandService } from '@/services/voiceCommandService'
import { useAppStore } from '@/stores/appStore'
import type { VoiceCommand } from '@/types'

// Voice command hook for managing voice input state
export function useVoiceCommands() {
  const [isSupported, setIsSupported] = React.useState(false)
  const [isListening, setIsListening] = React.useState(false)
  const [lastCommand, setLastCommand] = React.useState<VoiceCommand | null>(null)
  const [error, setError] = React.useState<string | null>(null)
  const [statistics, setStatistics] = React.useState<any>(null)

  const { userPreferences } = useAppStore()

  // Check voice support on mount
  React.useEffect(() => {
    const checkSupport = async () => {
      const supported = voiceCommandService.isSupported()
      setIsSupported(supported)

      if (supported) {
        // Test voice services
        try {
          const testResult = await voiceCommandService.testVoiceServices()
          if (!testResult.recognition || !testResult.synthesis) {
            setError('Some voice features may not work properly')
          }
        } catch (error) {
          console.warn('Voice service test failed:', error)
        }
      }
    }

    checkSupport()
  }, [])

  // Update statistics periodically
  React.useEffect(() => {
    const updateStats = () => {
      const stats = voiceCommandService.getStatistics()
      setStatistics(stats)
    }

    updateStats()
    const interval = setInterval(updateStats, 30000) // Update every 30 seconds

    return () => clearInterval(interval)
  }, [])

  // Monitor listening state
  React.useEffect(() => {
    const checkListening = () => {
      setIsListening(voiceCommandService.isCurrentlyListening())
    }

    const interval = setInterval(checkListening, 100)
    return () => clearInterval(interval)
  }, [])

  // Start voice recognition
  const startListening = React.useCallback(async (
    onResult?: (transcript: string, confidence: number) => void,
    onError?: (error: string) => void
  ) => {
    if (!isSupported) {
      const errorMsg = 'Voice commands not supported'
      setError(errorMsg)
      onError?.(errorMsg)
      return false
    }

    if (!userPreferences.accessibility.voiceCommands) {
      const errorMsg = 'Voice commands not enabled in settings'
      setError(errorMsg)
      onError?.(errorMsg)
      return false
    }

    try {
      setError(null)
      
      await voiceCommandService.startListening(
        (result) => {
          if (result.success) {
            setLastCommand({
              id: `voice-${Date.now()}`,
              transcript: result.transcript,
              confidence: result.confidence,
              intent: result.intent || 'unknown',
              entities: [],
              timestamp: new Date()
            })
            onResult?.(result.transcript, result.confidence)
          }
        },
        (error) => {
          setError(error)
          onError?.(error)
        },
        () => setIsListening(true),
        () => setIsListening(false)
      )

      return true
    } catch (error) {
      const errorMsg = 'Failed to start voice recognition'
      setError(errorMsg)
      onError?.(errorMsg)
      return false
    }
  }, [isSupported, userPreferences.accessibility.voiceCommands])

  // Stop voice recognition
  const stopListening = React.useCallback(() => {
    voiceCommandService.stopListening()
    setIsListening(false)
  }, [])

  // Toggle voice recognition
  const toggleListening = React.useCallback(async (
    onResult?: (transcript: string, confidence: number) => void,
    onError?: (error: string) => void
  ) => {
    if (isListening) {
      stopListening()
      return false
    } else {
      return await startListening(onResult, onError)
    }
  }, [isListening, startListening, stopListening])

  // Provide voice feedback
  const speak = React.useCallback((
    message: string, 
    priority: 'low' | 'normal' | 'high' = 'normal'
  ) => {
    if (isSupported && userPreferences.accessibility.voiceCommands) {
      voiceCommandService.provideFeedback(message, priority)
    }
  }, [isSupported, userPreferences.accessibility.voiceCommands])

  // Get command history
  const getHistory = React.useCallback(() => {
    return voiceCommandService.getCommandHistory()
  }, [])

  // Clear command history
  const clearHistory = React.useCallback(() => {
    voiceCommandService.clearHistory()
    setStatistics(voiceCommandService.getStatistics())
  }, [])

  // Test voice services
  const testVoiceServices = React.useCallback(async () => {
    try {
      const result = await voiceCommandService.testVoiceServices()
      
      if (result.recognition && result.synthesis && result.microphone) {
        speak('Voice services test successful', 'normal')
        setError(null)
      } else {
        const issues = []
        if (!result.recognition) issues.push('speech recognition')
        if (!result.synthesis) issues.push('speech synthesis')
        if (!result.microphone) issues.push('microphone access')
        
        const errorMsg = `Voice test failed: ${issues.join(', ')} not available`
        setError(errorMsg)
      }
      
      return result
    } catch (error) {
      const errorMsg = 'Voice service test failed'
      setError(errorMsg)
      return { recognition: false, synthesis: false, microphone: false }
    }
  }, [speak])

  // Configure voice settings
  const configureVoice = React.useCallback((config: {
    enabled?: boolean
    rate?: number
    pitch?: number
    volume?: number
    voice?: SpeechSynthesisVoice
  }) => {
    if (config.enabled !== undefined) {
      voiceCommandService.setEnabled(config.enabled)
    }

    const feedbackConfig: any = {}
    if (config.rate !== undefined) feedbackConfig.rate = config.rate
    if (config.pitch !== undefined) feedbackConfig.pitch = config.pitch
    if (config.volume !== undefined) feedbackConfig.volume = config.volume

    if (Object.keys(feedbackConfig).length > 0) {
      voiceCommandService.configureFeedback(feedbackConfig)
    }

    if (config.voice) {
      voiceCommandService.setFeedbackVoice(config.voice)
    }
  }, [])

  // Get available voices
  const getAvailableVoices = React.useCallback(() => {
    return voiceCommandService.getAvailableVoices()
  }, [])

  // Cleanup on unmount
  React.useEffect(() => {
    return () => {
      voiceCommandService.cleanup()
    }
  }, [])

  return {
    // State
    isSupported,
    isListening,
    lastCommand,
    error,
    statistics,
    
    // Actions
    startListening,
    stopListening,
    toggleListening,
    speak,
    
    // History
    getHistory,
    clearHistory,
    
    // Configuration
    testVoiceServices,
    configureVoice,
    getAvailableVoices,
    
    // Utilities
    clearError: () => setError(null)
  }
}