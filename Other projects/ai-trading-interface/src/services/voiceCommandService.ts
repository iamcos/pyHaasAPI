import { commandProcessor } from './commandProcessor'
import { useAppStore } from '@/stores/appStore'
import type { VoiceCommand, UIContext } from '@/types'

// Voice recognition configuration
interface VoiceConfig {
  language: string
  continuous: boolean
  interimResults: boolean
  maxAlternatives: number
  grammars?: any // SpeechGrammarList
}

// Voice command processing result
interface VoiceProcessingResult {
  success: boolean
  transcript: string
  confidence: number
  alternatives: string[]
  intent?: string
  error?: string
}

// Voice feedback configuration
interface VoiceFeedback {
  enabled: boolean
  voice?: SpeechSynthesisVoice
  rate: number
  pitch: number
  volume: number
}

// Enhanced voice command service
class VoiceCommandService {
  private recognition: any | null = null // SpeechRecognition
  private synthesis: SpeechSynthesis | null = null
  private isListening = false
  private config: VoiceConfig
  private feedback: VoiceFeedback
  private commandHistory: VoiceCommand[] = []
  private grammarList: any | null = null // SpeechGrammarList

  constructor() {
    this.config = this.getDefaultConfig()
    this.feedback = this.getDefaultFeedback()
    this.initializeSpeechServices()
    this.setupGrammar()
  }

  // Initialize speech recognition and synthesis
  private initializeSpeechServices(): void {
    // Initialize speech recognition
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = (window as any).webkitSpeechRecognition || (window as any).SpeechRecognition
      this.recognition = new SpeechRecognition()
      this.setupRecognition()
    }

    // Initialize speech synthesis
    if ('speechSynthesis' in window) {
      this.synthesis = window.speechSynthesis
    }
  }

  // Setup speech recognition configuration
  private setupRecognition(): void {
    if (!this.recognition) return

    this.recognition.continuous = this.config.continuous
    this.recognition.interimResults = this.config.interimResults
    this.recognition.lang = this.config.language
    this.recognition.maxAlternatives = this.config.maxAlternatives

    if (this.grammarList) {
      this.recognition.grammars = this.grammarList
    }
  }

  // Setup grammar for better recognition of trading terms
  private setupGrammar(): void {
    if ('webkitSpeechGrammarList' in window || 'SpeechGrammarList' in window) {
      const SpeechGrammarList = (window as any).webkitSpeechGrammarList || (window as any).SpeechGrammarList
      this.grammarList = new SpeechGrammarList()

      // Define trading-specific grammar
      const tradingGrammar = `
        #JSGF V1.0; grammar trading;
        public <command> = <action> <target> | <query> <subject>;
        <action> = create | build | generate | start | stop | activate | deactivate | analyze | show | optimize;
        <target> = strategy | bot | analysis | report | chart | dashboard;
        <query> = what is | show me | how is | analyze;
        <subject> = performance | risk | market | portfolio | balance;
        <symbol> = bitcoin | BTC | ethereum | ETH | cardano | ADA | polkadot | DOT;
        <timeframe> = hourly | daily | weekly | one hour | four hours | one day;
      `

      this.grammarList.addFromString(tradingGrammar, 1)
    }
  }

  // Get default voice configuration
  private getDefaultConfig(): VoiceConfig {
    const userPrefs = useAppStore.getState().userPreferences
    return {
      language: userPrefs.language || 'en-US',
      continuous: false,
      interimResults: true,
      maxAlternatives: 3
    }
  }

  // Get default voice feedback configuration
  private getDefaultFeedback(): VoiceFeedback {
    return {
      enabled: true,
      rate: 1.0,
      pitch: 1.0,
      volume: 0.8
    }
  }

  // Check if voice commands are supported
  isSupported(): boolean {
    return !!(this.recognition && this.synthesis)
  }

  // Check if currently listening
  isCurrentlyListening(): boolean {
    return this.isListening
  }

  // Start voice recognition
  async startListening(
    onResult: (result: VoiceProcessingResult) => void,
    onError: (error: string) => void,
    onStart?: () => void,
    onEnd?: () => void
  ): Promise<void> {
    if (!this.recognition) {
      onError('Speech recognition not supported')
      return
    }

    if (this.isListening) {
      onError('Already listening')
      return
    }

    // Update configuration from user preferences
    this.updateConfigFromPreferences()

    // Setup event handlers
    this.recognition.onstart = () => {
      this.isListening = true
      onStart?.()
      this.provideFeedback('Listening...')
    }

    this.recognition.onresult = (event: any) => {
      const result = this.processRecognitionResult(event)
      onResult(result)

      // If we have a final result, process it
      if (result.success && event.results[event.resultIndex].isFinal) {
        this.processVoiceCommand(result)
      }
    }

    this.recognition.onerror = (event: any) => {
      this.isListening = false
      const errorMessage = this.getErrorMessage(event.error)
      onError(errorMessage)
      this.provideFeedback(`Error: ${errorMessage}`)
    }

    this.recognition.onend = () => {
      this.isListening = false
      onEnd?.()
    }

    // Start recognition
    try {
      this.recognition.start()
    } catch (error) {
      this.isListening = false
      onError('Failed to start voice recognition')
    }
  }

  // Stop voice recognition
  stopListening(): void {
    if (this.recognition && this.isListening) {
      this.recognition.stop()
      this.isListening = false
    }
  }

  // Process speech recognition result
  private processRecognitionResult(event: any): VoiceProcessingResult {
    let finalTranscript = ''
    let interimTranscript = ''
    const alternatives: string[] = []

    for (let i = event.resultIndex; i < event.results.length; i++) {
      const result = event.results[i]
      const transcript = result[0].transcript

      if (result.isFinal) {
        finalTranscript += transcript
        
        // Collect alternatives
        for (let j = 0; j < Math.min(result.length, this.config.maxAlternatives); j++) {
          alternatives.push(result[j].transcript)
        }
      } else {
        interimTranscript += transcript
      }
    }

    const fullTranscript = finalTranscript + interimTranscript
    const confidence = event.results[event.resultIndex]?.[0]?.confidence || 0

    return {
      success: true,
      transcript: fullTranscript,
      confidence,
      alternatives,
      intent: this.extractIntent(fullTranscript)
    }
  }

  // Extract intent from voice command
  private extractIntent(transcript: string): string {
    const lowerTranscript = transcript.toLowerCase()
    
    // Simple intent extraction based on keywords
    if (lowerTranscript.includes('create') || lowerTranscript.includes('build') || lowerTranscript.includes('generate')) {
      return 'create'
    } else if (lowerTranscript.includes('show') || lowerTranscript.includes('display') || lowerTranscript.includes('view')) {
      return 'show'
    } else if (lowerTranscript.includes('analyze') || lowerTranscript.includes('analysis')) {
      return 'analyze'
    } else if (lowerTranscript.includes('start') || lowerTranscript.includes('activate')) {
      return 'start'
    } else if (lowerTranscript.includes('stop') || lowerTranscript.includes('deactivate')) {
      return 'stop'
    } else if (lowerTranscript.includes('optimize') || lowerTranscript.includes('improve')) {
      return 'optimize'
    }
    
    return 'unknown'
  }

  // Process voice command through the command processor
  private async processVoiceCommand(result: VoiceProcessingResult): Promise<void> {
    try {
      // Create voice command record
      const voiceCommand: VoiceCommand = {
        id: `voice-${Date.now()}`,
        transcript: result.transcript,
        confidence: result.confidence,
        intent: result.intent || 'unknown',
        entities: [],
        timestamp: new Date()
      }

      // Add to history
      this.commandHistory.push(voiceCommand)
      if (this.commandHistory.length > 50) {
        this.commandHistory.shift()
      }

      // Get current UI context
      const uiContext = useAppStore.getState().uiContext

      // Process through command processor
      const commandResult = await commandProcessor.processCommand(result.transcript, uiContext)

      // Provide voice feedback on result
      if (commandResult.success) {
        this.provideFeedback(`Command processed: ${commandResult.message || 'Done'}`)
      } else {
        this.provideFeedback(`Error: ${commandResult.message || 'Command failed'}`)
      }

    } catch (error) {
      console.error('Voice command processing failed:', error)
      this.provideFeedback('Sorry, I could not process that command')
    }
  }

  // Provide voice feedback to user
  provideFeedback(message: string, priority: 'low' | 'normal' | 'high' = 'normal'): void {
    if (!this.feedback.enabled || !this.synthesis) return

    // Cancel any ongoing speech
    this.synthesis.cancel()

    const utterance = new SpeechSynthesisUtterance(message)
    
    // Configure utterance
    utterance.rate = this.feedback.rate
    utterance.pitch = this.feedback.pitch
    utterance.volume = this.feedback.volume

    // Set voice if available
    if (this.feedback.voice) {
      utterance.voice = this.feedback.voice
    }

    // Adjust properties based on priority
    switch (priority) {
      case 'high':
        utterance.rate = Math.min(this.feedback.rate * 0.8, 1.0) // Slower for important messages
        utterance.volume = Math.min(this.feedback.volume * 1.2, 1.0)
        break
      case 'low':
        utterance.rate = Math.min(this.feedback.rate * 1.2, 2.0) // Faster for less important
        utterance.volume = this.feedback.volume * 0.8
        break
    }

    // Speak the message
    this.synthesis.speak(utterance)
  }

  // Update configuration from user preferences
  private updateConfigFromPreferences(): void {
    const userPrefs = useAppStore.getState().userPreferences
    
    this.config.language = userPrefs.language || 'en-US'
    
    if (this.recognition) {
      this.recognition.lang = this.config.language
    }
  }

  // Get available voices for speech synthesis
  getAvailableVoices(): SpeechSynthesisVoice[] {
    if (!this.synthesis) return []
    return this.synthesis.getVoices()
  }

  // Set voice for feedback
  setFeedbackVoice(voice: SpeechSynthesisVoice): void {
    this.feedback.voice = voice
  }

  // Configure voice feedback settings
  configureFeedback(config: Partial<VoiceFeedback>): void {
    this.feedback = { ...this.feedback, ...config }
  }

  // Get error message for speech recognition errors
  private getErrorMessage(error: string): string {
    switch (error) {
      case 'no-speech':
        return 'No speech detected. Please try speaking more clearly.'
      case 'audio-capture':
        return 'Microphone access denied or not available.'
      case 'not-allowed':
        return 'Microphone permission denied. Please allow microphone access.'
      case 'network':
        return 'Network error occurred during speech recognition.'
      case 'service-not-allowed':
        return 'Speech recognition service not allowed.'
      case 'bad-grammar':
        return 'Grammar error in speech recognition.'
      case 'language-not-supported':
        return 'Selected language not supported for speech recognition.'
      default:
        return `Speech recognition error: ${error}`
    }
  }

  // Get command history
  getCommandHistory(): VoiceCommand[] {
    return [...this.commandHistory]
  }

  // Clear command history
  clearHistory(): void {
    this.commandHistory = []
  }

  // Test voice recognition and synthesis
  async testVoiceServices(): Promise<{
    recognition: boolean
    synthesis: boolean
    microphone: boolean
  }> {
    const result = {
      recognition: !!this.recognition,
      synthesis: !!this.synthesis,
      microphone: false
    }

    // Test microphone access
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      result.microphone = true
      stream.getTracks().forEach(track => track.stop()) // Clean up
    } catch (error) {
      console.warn('Microphone test failed:', error)
    }

    return result
  }

  // Enable/disable voice commands
  setEnabled(enabled: boolean): void {
    if (!enabled && this.isListening) {
      this.stopListening()
    }
  }

  // Get voice command statistics
  getStatistics(): {
    totalCommands: number
    averageConfidence: number
    mostCommonIntent: string
    successRate: number
  } {
    if (this.commandHistory.length === 0) {
      return {
        totalCommands: 0,
        averageConfidence: 0,
        mostCommonIntent: 'none',
        successRate: 0
      }
    }

    const totalCommands = this.commandHistory.length
    const averageConfidence = this.commandHistory.reduce((sum, cmd) => sum + cmd.confidence, 0) / totalCommands
    
    // Find most common intent
    const intentCounts: Record<string, number> = {}
    this.commandHistory.forEach(cmd => {
      intentCounts[cmd.intent] = (intentCounts[cmd.intent] || 0) + 1
    })
    
    const mostCommonIntent = Object.entries(intentCounts)
      .sort(([,a], [,b]) => b - a)[0]?.[0] || 'unknown'

    // Calculate success rate (commands with confidence > 0.7)
    const successfulCommands = this.commandHistory.filter(cmd => cmd.confidence > 0.7).length
    const successRate = successfulCommands / totalCommands

    return {
      totalCommands,
      averageConfidence,
      mostCommonIntent,
      successRate
    }
  }

  // Cleanup resources
  cleanup(): void {
    this.stopListening()
    if (this.synthesis) {
      this.synthesis.cancel()
    }
  }
}

// Export singleton instance
export const voiceCommandService = new VoiceCommandService()