import React from 'react'
import { MicrophoneIcon, SpeakerWaveIcon, Cog6ToothIcon } from '@heroicons/react/24/outline'
import { voiceCommandService } from '@/services/voiceCommandService'
import { useAppStore } from '@/stores/appStore'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'

interface VoiceSettingsProps {
  isOpen: boolean
  onClose: () => void
}

export function VoiceSettings({ isOpen, onClose }: VoiceSettingsProps) {
  const [voices, setVoices] = React.useState<SpeechSynthesisVoice[]>([])
  const [selectedVoice, setSelectedVoice] = React.useState<string>('')
  const [feedbackEnabled, setFeedbackEnabled] = React.useState(true)
  const [rate, setRate] = React.useState(1.0)
  const [pitch, setPitch] = React.useState(1.0)
  const [volume, setVolume] = React.useState(0.8)
  const [testResult, setTestResult] = React.useState<any>(null)
  const [isTestingVoice, setIsTestingVoice] = React.useState(false)
  const [statistics, setStatistics] = React.useState<any>(null)

  const { userPreferences, updateUserPreferences } = useAppStore()

  // Load available voices
  React.useEffect(() => {
    const loadVoices = () => {
      const availableVoices = voiceCommandService.getAvailableVoices()
      setVoices(availableVoices)
      
      // Set default voice (prefer English voices)
      const englishVoice = availableVoices.find(voice => 
        voice.lang.startsWith('en') && voice.default
      ) || availableVoices.find(voice => 
        voice.lang.startsWith('en')
      ) || availableVoices[0]
      
      if (englishVoice) {
        setSelectedVoice(englishVoice.name)
      }
    }

    loadVoices()
    
    // Voices might not be loaded immediately
    if (voices.length === 0) {
      setTimeout(loadVoices, 100)
    }
  }, [])

  // Load voice command statistics
  React.useEffect(() => {
    if (isOpen) {
      const stats = voiceCommandService.getStatistics()
      setStatistics(stats)
    }
  }, [isOpen])

  // Test voice services
  const handleTestVoice = async () => {
    setIsTestingVoice(true)
    try {
      const result = await voiceCommandService.testVoiceServices()
      setTestResult(result)
      
      if (result.synthesis) {
        voiceCommandService.provideFeedback('Voice test successful. All systems working.', 'normal')
      }
    } catch (error) {
      console.error('Voice test failed:', error)
      setTestResult({ recognition: false, synthesis: false, microphone: false })
    } finally {
      setIsTestingVoice(false)
    }
  }

  // Apply voice settings
  const handleApplySettings = () => {
    // Update voice feedback configuration
    voiceCommandService.configureFeedback({
      enabled: feedbackEnabled,
      rate,
      pitch,
      volume
    })

    // Set selected voice
    const voice = voices.find(v => v.name === selectedVoice)
    if (voice) {
      voiceCommandService.setFeedbackVoice(voice)
    }

    // Update user preferences
    updateUserPreferences({
      accessibility: {
        ...userPreferences.accessibility,
        voiceCommands: userPreferences.accessibility.voiceCommands
      }
    })

    onClose()
  }

  // Test voice feedback with current settings
  const handleTestFeedback = () => {
    voiceCommandService.configureFeedback({
      enabled: feedbackEnabled,
      rate,
      pitch,
      volume
    })

    const voice = voices.find(v => v.name === selectedVoice)
    if (voice) {
      voiceCommandService.setFeedbackVoice(voice)
    }

    voiceCommandService.provideFeedback('This is a test of your voice feedback settings.', 'normal')
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold text-neutral-900 flex items-center space-x-2">
              <MicrophoneIcon className="h-6 w-6" />
              <span>Voice Command Settings</span>
            </h2>
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

          <div className="space-y-6">
            {/* Voice Recognition Status */}
            <Card className="p-4">
              <h3 className="text-lg font-medium text-neutral-900 mb-4 flex items-center space-x-2">
                <Cog6ToothIcon className="h-5 w-5" />
                <span>System Status</span>
              </h3>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                <div className="text-center">
                  <div className={`w-12 h-12 rounded-full mx-auto mb-2 flex items-center justify-center ${
                    testResult?.recognition ? 'bg-green-100 text-green-600' : 'bg-red-100 text-red-600'
                  }`}>
                    <MicrophoneIcon className="h-6 w-6" />
                  </div>
                  <div className="text-sm font-medium">Speech Recognition</div>
                  <div className={`text-xs ${testResult?.recognition ? 'text-green-600' : 'text-red-600'}`}>
                    {testResult?.recognition ? 'Available' : 'Not Available'}
                  </div>
                </div>
                
                <div className="text-center">
                  <div className={`w-12 h-12 rounded-full mx-auto mb-2 flex items-center justify-center ${
                    testResult?.synthesis ? 'bg-green-100 text-green-600' : 'bg-red-100 text-red-600'
                  }`}>
                    <SpeakerWaveIcon className="h-6 w-6" />
                  </div>
                  <div className="text-sm font-medium">Speech Synthesis</div>
                  <div className={`text-xs ${testResult?.synthesis ? 'text-green-600' : 'text-red-600'}`}>
                    {testResult?.synthesis ? 'Available' : 'Not Available'}
                  </div>
                </div>
                
                <div className="text-center">
                  <div className={`w-12 h-12 rounded-full mx-auto mb-2 flex items-center justify-center ${
                    testResult?.microphone ? 'bg-green-100 text-green-600' : 'bg-red-100 text-red-600'
                  }`}>
                    <MicrophoneIcon className="h-6 w-6" />
                  </div>
                  <div className="text-sm font-medium">Microphone</div>
                  <div className={`text-xs ${testResult?.microphone ? 'text-green-600' : 'text-red-600'}`}>
                    {testResult?.microphone ? 'Accessible' : 'No Access'}
                  </div>
                </div>
              </div>

              <Button
                onClick={handleTestVoice}
                disabled={isTestingVoice}
                variant="outline"
                className="w-full"
              >
                {isTestingVoice ? 'Testing...' : 'Test Voice Services'}
              </Button>
            </Card>

            {/* Voice Feedback Settings */}
            <Card className="p-4">
              <h3 className="text-lg font-medium text-neutral-900 mb-4 flex items-center space-x-2">
                <SpeakerWaveIcon className="h-5 w-5" />
                <span>Voice Feedback</span>
              </h3>

              <div className="space-y-4">
                {/* Enable/Disable Feedback */}
                <div className="flex items-center justify-between">
                  <label className="text-sm font-medium text-neutral-700">
                    Enable Voice Feedback
                  </label>
                  <button
                    onClick={() => setFeedbackEnabled(!feedbackEnabled)}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                      feedbackEnabled ? 'bg-primary-600' : 'bg-neutral-200'
                    }`}
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                        feedbackEnabled ? 'translate-x-6' : 'translate-x-1'
                      }`}
                    />
                  </button>
                </div>

                {/* Voice Selection */}
                {feedbackEnabled && (
                  <>
                    <div>
                      <label className="block text-sm font-medium text-neutral-700 mb-2">
                        Voice
                      </label>
                      <select
                        value={selectedVoice}
                        onChange={(e) => setSelectedVoice(e.target.value)}
                        className="w-full px-3 py-2 border border-neutral-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                      >
                        {voices.map((voice) => (
                          <option key={voice.name} value={voice.name}>
                            {voice.name} ({voice.lang})
                          </option>
                        ))}
                      </select>
                    </div>

                    {/* Rate Control */}
                    <div>
                      <label className="block text-sm font-medium text-neutral-700 mb-2">
                        Speech Rate: {rate.toFixed(1)}x
                      </label>
                      <input
                        type="range"
                        min="0.5"
                        max="2.0"
                        step="0.1"
                        value={rate}
                        onChange={(e) => setRate(parseFloat(e.target.value))}
                        className="w-full"
                      />
                    </div>

                    {/* Pitch Control */}
                    <div>
                      <label className="block text-sm font-medium text-neutral-700 mb-2">
                        Pitch: {pitch.toFixed(1)}
                      </label>
                      <input
                        type="range"
                        min="0.5"
                        max="2.0"
                        step="0.1"
                        value={pitch}
                        onChange={(e) => setPitch(parseFloat(e.target.value))}
                        className="w-full"
                      />
                    </div>

                    {/* Volume Control */}
                    <div>
                      <label className="block text-sm font-medium text-neutral-700 mb-2">
                        Volume: {Math.round(volume * 100)}%
                      </label>
                      <input
                        type="range"
                        min="0.1"
                        max="1.0"
                        step="0.1"
                        value={volume}
                        onChange={(e) => setVolume(parseFloat(e.target.value))}
                        className="w-full"
                      />
                    </div>

                    <Button
                      onClick={handleTestFeedback}
                      variant="outline"
                      className="w-full"
                    >
                      Test Voice Feedback
                    </Button>
                  </>
                )}
              </div>
            </Card>

            {/* Voice Command Statistics */}
            {statistics && statistics.totalCommands > 0 && (
              <Card className="p-4">
                <h3 className="text-lg font-medium text-neutral-900 mb-4">
                  Usage Statistics
                </h3>
                
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-primary-600">
                      {statistics.totalCommands}
                    </div>
                    <div className="text-sm text-neutral-600">Total Commands</div>
                  </div>
                  
                  <div className="text-center">
                    <div className="text-2xl font-bold text-green-600">
                      {Math.round(statistics.averageConfidence * 100)}%
                    </div>
                    <div className="text-sm text-neutral-600">Avg Confidence</div>
                  </div>
                  
                  <div className="text-center">
                    <div className="text-2xl font-bold text-blue-600">
                      {Math.round(statistics.successRate * 100)}%
                    </div>
                    <div className="text-sm text-neutral-600">Success Rate</div>
                  </div>
                  
                  <div className="text-center">
                    <div className="text-lg font-bold text-purple-600 capitalize">
                      {statistics.mostCommonIntent}
                    </div>
                    <div className="text-sm text-neutral-600">Most Common</div>
                  </div>
                </div>
              </Card>
            )}

            {/* Help and Tips */}
            <Card className="p-4 bg-blue-50 border-blue-200">
              <h3 className="text-lg font-medium text-blue-900 mb-2">
                Voice Command Tips
              </h3>
              <ul className="text-sm text-blue-800 space-y-1">
                <li>• Speak clearly and at a normal pace</li>
                <li>• Use specific trading terms like "BTC", "strategy", "analyze"</li>
                <li>• Try commands like "Create momentum strategy for Bitcoin"</li>
                <li>• Say "Show my portfolio risk" for risk analysis</li>
                <li>• Use "Start optimization workflow" for automated processes</li>
              </ul>
            </Card>
          </div>

          {/* Action Buttons */}
          <div className="flex justify-end space-x-3 mt-6 pt-6 border-t border-neutral-200">
            <Button
              onClick={onClose}
              variant="outline"
            >
              Cancel
            </Button>
            <Button
              onClick={handleApplySettings}
              variant="primary"
            >
              Apply Settings
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}