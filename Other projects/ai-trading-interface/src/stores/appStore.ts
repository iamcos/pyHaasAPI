import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { UserPreferences, UIContext, Persona } from '@/types'

interface AppState {
  // Initialization
  isInitialized: boolean
  
  // User preferences and settings
  userPreferences: UserPreferences
  currentPersona: Persona
  
  // UI state
  uiContext: UIContext
  
  // Theme and appearance
  theme: 'light' | 'dark' | 'auto'
  
  // Actions
  initialize: () => Promise<void>
  updateUserPreferences: (preferences: Partial<UserPreferences>) => void
  setPersona: (persona: Persona) => void
  updateUIContext: (context: Partial<UIContext>) => void
  setTheme: (theme: 'light' | 'dark' | 'auto') => void
}

// Default user preferences
const defaultUserPreferences: UserPreferences = {
  theme: 'light',
  language: 'en',
  timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
  currency: 'USD',
  notifications: {
    enabled: true,
    types: [
      { type: 'trade', enabled: true, priority: 'high' },
      { type: 'alert', enabled: true, priority: 'high' },
      { type: 'performance', enabled: true, priority: 'medium' },
      { type: 'risk', enabled: true, priority: 'critical' },
      { type: 'system', enabled: true, priority: 'low' },
    ],
    frequency: 'immediate',
    channels: [
      { type: 'in_app', enabled: true, settings: {} },
      { type: 'sound', enabled: true, settings: {} },
    ],
  },
  dashboard: {
    layout: 'grid',
    widgets: [],
    refreshInterval: 5000, // 5 seconds
    autoRefresh: true,
  },
  accessibility: {
    highContrast: false,
    largeText: false,
    screenReader: false,
    keyboardNavigation: true,
    voiceCommands: false,
    reducedMotion: false,
  },
}

// Default persona (balanced)
const defaultPersona: Persona = {
  id: 'balanced',
  name: 'Balanced Trader',
  type: 'balanced',
  description: 'A balanced approach to trading with moderate risk tolerance',
  riskTolerance: 0.5,
  optimizationStyle: 'balanced',
  decisionSpeed: 'moderate',
  preferences: {
    preferredTimeframes: ['1h', '4h', '1d'],
    riskLimits: {
      maxDrawdown: 0.15,
      maxPositionSize: 0.1,
      maxCorrelation: 0.7,
    },
    optimizationFocus: 'risk_adjusted',
    alertFrequency: 'moderate',
  },
}

// Default UI context
const defaultUIContext: UIContext = {
  currentView: 'dashboard',
  selectedAssets: [],
  activeStrategies: [],
  userPreferences: defaultUserPreferences,
  marketConditions: [],
  riskTolerance: {
    level: 'moderate',
    maxDrawdown: 0.15,
    maxPositionSize: 0.1,
    diversificationRequirement: 0.3,
    stopLossRequirement: true,
  },
  persona: defaultPersona,
}

export const useAppStore = create<AppState>()(
  persist(
    (set, get) => ({
      // Initial state
      isInitialized: false,
      userPreferences: defaultUserPreferences,
      currentPersona: defaultPersona,
      uiContext: defaultUIContext,
      theme: 'light',

      // Actions
      initialize: async () => {
        try {
          // Simulate initialization process
          await new Promise(resolve => setTimeout(resolve, 1000))
          
          // Initialize any required services here
          console.log('AI Trading Interface initialized')
          
          set({ isInitialized: true })
        } catch (error) {
          console.error('Failed to initialize application:', error)
          throw error
        }
      },

      updateUserPreferences: (preferences) => {
        const currentPreferences = get().userPreferences
        const updatedPreferences = { ...currentPreferences, ...preferences }
        
        set({ 
          userPreferences: updatedPreferences,
          uiContext: {
            ...get().uiContext,
            userPreferences: updatedPreferences,
          }
        })
      },

      setPersona: (persona) => {
        set({ 
          currentPersona: persona,
          uiContext: {
            ...get().uiContext,
            persona,
          }
        })
      },

      updateUIContext: (context) => {
        set({
          uiContext: {
            ...get().uiContext,
            ...context,
          }
        })
      },

      setTheme: (theme) => {
        set({ 
          theme,
          userPreferences: {
            ...get().userPreferences,
            theme,
          }
        })
        
        // Apply theme to document
        if (theme === 'dark') {
          document.documentElement.classList.add('dark')
        } else if (theme === 'light') {
          document.documentElement.classList.remove('dark')
        } else {
          // Auto theme - check system preference
          const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
          if (prefersDark) {
            document.documentElement.classList.add('dark')
          } else {
            document.documentElement.classList.remove('dark')
          }
        }
      },
    }),
    {
      name: 'ai-trading-interface-storage',
      partialize: (state) => ({
        userPreferences: state.userPreferences,
        currentPersona: state.currentPersona,
        theme: state.theme,
        uiContext: {
          ...state.uiContext,
          // Don't persist temporary UI state
          selectedAssets: [],
          activeStrategies: [],
          marketConditions: [],
        },
      }),
    }
  )
)