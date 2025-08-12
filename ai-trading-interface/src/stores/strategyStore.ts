import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { HaasScriptStrategy, ValidationError as HaasScriptValidationError, StrategyTemplate } from '../types/strategy';

interface StrategyState {
  // Current strategies
  strategies: HaasScriptStrategy[];
  currentStrategy: HaasScriptStrategy | null;
  
  // Templates
  templates: StrategyTemplate[];
  
  // Editor state
  validationErrors: HaasScriptValidationError[];
  isValidating: boolean;
  
  // Actions
  createStrategy: (name: string, description?: string) => HaasScriptStrategy;
  updateStrategy: (id: string, updates: Partial<HaasScriptStrategy>) => void;
  deleteStrategy: (id: string) => void;
  setCurrentStrategy: (strategy: HaasScriptStrategy | null) => void;
  duplicateStrategy: (id: string, newName: string) => HaasScriptStrategy | null;
  
  // Validation
  setValidationErrors: (errors: HaasScriptValidationError[]) => void;
  setValidating: (isValidating: boolean) => void;
  
  // Templates
  loadTemplates: () => void;
  createFromTemplate: (templateId: string, name: string) => HaasScriptStrategy | null;
  
  // Import/Export
  exportStrategy: (id: string) => string | null;
  importStrategy: (data: string) => HaasScriptStrategy | null;
}

const defaultTemplates: StrategyTemplate[] = [
  {
    id: 'simple-rsi',
    name: 'Simple RSI Strategy',
    description: 'Basic RSI-based trading strategy with overbought/oversold levels',
    category: 'Technical Analysis',
    difficulty: 'beginner',
    tags: ['RSI', 'momentum', 'oscillator'],
    code: `// Simple RSI Strategy
// Buy when RSI is oversold (< 30) and sell when overbought (> 70)

var rsiPeriod = 14
var oversoldLevel = 30
var overboughtLevel = 70

var rsi = RSI(Close, rsiPeriod)

// Buy condition: RSI crosses above oversold level
if CrossOver(rsi, oversoldLevel)
    Buy(100, "RSI Oversold Buy")
endif

// Sell condition: RSI crosses below overbought level
if CrossUnder(rsi, overboughtLevel)
    Sell(100, "RSI Overbought Sell")
endif`,
    parameters: [
      {
        id: 'rsiPeriod',
        name: 'RSI Period',
        type: 'number',
        value: 14,
        defaultValue: 14,
        min: 2,
        max: 50,
        description: 'Period for RSI calculation',
        category: 'Technical'
      },
      {
        id: 'oversoldLevel',
        name: 'Oversold Level',
        type: 'number',
        value: 30,
        defaultValue: 30,
        min: 10,
        max: 40,
        description: 'RSI level considered oversold',
        category: 'Signals'
      },
      {
        id: 'overboughtLevel',
        name: 'Overbought Level',
        type: 'number',
        value: 70,
        defaultValue: 70,
        min: 60,
        max: 90,
        description: 'RSI level considered overbought',
        category: 'Signals'
      }
    ]
  },
  {
    id: 'ema-crossover',
    name: 'EMA Crossover Strategy',
    description: 'Moving average crossover strategy using fast and slow EMAs',
    category: 'Trend Following',
    difficulty: 'beginner',
    tags: ['EMA', 'crossover', 'trend'],
    code: `// EMA Crossover Strategy
// Buy when fast EMA crosses above slow EMA, sell when it crosses below

var fastPeriod = 12
var slowPeriod = 26

var fastEMA = EMA(Close, fastPeriod)
var slowEMA = EMA(Close, slowPeriod)

// Buy condition: Fast EMA crosses above slow EMA
if CrossOver(fastEMA, slowEMA)
    Buy(100, "EMA Bullish Crossover")
endif

// Sell condition: Fast EMA crosses below slow EMA
if CrossUnder(fastEMA, slowEMA)
    Sell(100, "EMA Bearish Crossover")
endif`,
    parameters: [
      {
        id: 'fastPeriod',
        name: 'Fast EMA Period',
        type: 'number',
        value: 12,
        defaultValue: 12,
        min: 5,
        max: 50,
        description: 'Period for fast EMA',
        category: 'Technical'
      },
      {
        id: 'slowPeriod',
        name: 'Slow EMA Period',
        type: 'number',
        value: 26,
        defaultValue: 26,
        min: 10,
        max: 100,
        description: 'Period for slow EMA',
        category: 'Technical'
      }
    ]
  },
  {
    id: 'bollinger-bands',
    name: 'Bollinger Bands Strategy',
    description: 'Mean reversion strategy using Bollinger Bands',
    category: 'Mean Reversion',
    difficulty: 'intermediate',
    tags: ['Bollinger Bands', 'mean reversion', 'volatility'],
    code: `// Bollinger Bands Strategy
// Buy when price touches lower band, sell when it touches upper band

var bbPeriod = 20
var bbDeviation = 2

var bb = BB(Close, bbPeriod, bbDeviation)
var upperBand = bb.Upper
var lowerBand = bb.Lower
var middleBand = bb.Middle

// Buy condition: Price crosses above lower band (bounce from support)
if CrossOver(Close, lowerBand)
    Buy(100, "BB Lower Band Bounce")
endif

// Sell condition: Price crosses below upper band (rejection from resistance)
if CrossUnder(Close, upperBand)
    Sell(100, "BB Upper Band Rejection")
endif

// Optional: Close position when price returns to middle band
if GetPosition() > 0 and CrossUnder(Close, middleBand)
    Sell(50, "BB Middle Band Exit")
endif

if GetPosition() < 0 and CrossOver(Close, middleBand)
    Buy(50, "BB Middle Band Exit")
endif`,
    parameters: [
      {
        id: 'bbPeriod',
        name: 'BB Period',
        type: 'number',
        value: 20,
        defaultValue: 20,
        min: 10,
        max: 50,
        description: 'Period for Bollinger Bands calculation',
        category: 'Technical'
      },
      {
        id: 'bbDeviation',
        name: 'BB Deviation',
        type: 'number',
        value: 2,
        defaultValue: 2,
        min: 1,
        max: 3,
        step: 0.1,
        description: 'Standard deviation multiplier',
        category: 'Technical'
      }
    ]
  }
];

export const useStrategyStore = create<StrategyState>()(
  persist(
    (set, get) => ({
      strategies: [],
      currentStrategy: null,
      templates: defaultTemplates,
      validationErrors: [],
      isValidating: false,

      createStrategy: (name: string, description = '') => {
        const newStrategy: HaasScriptStrategy = {
          id: `strategy_${Date.now()}`,
          name,
          description,
          code: '// New HaasScript Strategy\n// Write your trading logic here\n\n',
          parameters: [],
          version: 1,
          createdAt: new Date(),
          updatedAt: new Date(),
          author: 'User',
          tags: [],
          validationErrors: [],
          isValid: true
        };

        set(state => ({
          strategies: [...state.strategies, newStrategy],
          currentStrategy: newStrategy
        }));

        return newStrategy;
      },

      updateStrategy: (id: string, updates: Partial<HaasScriptStrategy>) => {
        set(state => ({
          strategies: state.strategies.map(strategy =>
            strategy.id === id
              ? { ...strategy, ...updates, updatedAt: new Date(), version: strategy.version + 1 }
              : strategy
          ),
          currentStrategy: state.currentStrategy?.id === id
            ? { ...state.currentStrategy, ...updates, updatedAt: new Date(), version: state.currentStrategy.version + 1 }
            : state.currentStrategy
        }));
      },

      deleteStrategy: (id: string) => {
        set(state => ({
          strategies: state.strategies.filter(strategy => strategy.id !== id),
          currentStrategy: state.currentStrategy?.id === id ? null : state.currentStrategy
        }));
      },

      setCurrentStrategy: (strategy: HaasScriptStrategy | null) => {
        set({ currentStrategy: strategy });
      },

      duplicateStrategy: (id: string, newName: string) => {
        const strategy = get().strategies.find(s => s.id === id);
        if (!strategy) return null;

        const duplicatedStrategy: HaasScriptStrategy = {
          ...strategy,
          id: `strategy_${Date.now()}`,
          name: newName,
          version: 1,
          createdAt: new Date(),
          updatedAt: new Date()
        };

        set(state => ({
          strategies: [...state.strategies, duplicatedStrategy]
        }));

        return duplicatedStrategy;
      },

      setValidationErrors: (errors: HaasScriptValidationError[]) => {
        set({ validationErrors: errors });
      },

      setValidating: (isValidating: boolean) => {
        set({ isValidating });
      },

      loadTemplates: () => {
        // Templates are already loaded in the initial state
        // This could be extended to load from an API
      },

      createFromTemplate: (templateId: string, name: string) => {
        const template = get().templates.find(t => t.id === templateId);
        if (!template) return null;

        const newStrategy: HaasScriptStrategy = {
          id: `strategy_${Date.now()}`,
          name,
          description: template.description,
          code: template.code,
          parameters: template.parameters.map(param => ({
            ...param,
            id: `param_${Date.now()}_${param.name}`
          })),
          version: 1,
          createdAt: new Date(),
          updatedAt: new Date(),
          author: 'User',
          tags: [...template.tags],
          validationErrors: [],
          isValid: true
        };

        set(state => ({
          strategies: [...state.strategies, newStrategy],
          currentStrategy: newStrategy
        }));

        return newStrategy;
      },

      exportStrategy: (id: string) => {
        const strategy = get().strategies.find(s => s.id === id);
        if (!strategy) return null;

        try {
          return JSON.stringify(strategy, null, 2);
        } catch (error) {
          console.error('Failed to export strategy:', error);
          return null;
        }
      },

      importStrategy: (data: string) => {
        try {
          const importedStrategy = JSON.parse(data) as HaasScriptStrategy;
          
          // Generate new ID and update timestamps
          const newStrategy: HaasScriptStrategy = {
            ...importedStrategy,
            id: `strategy_${Date.now()}`,
            createdAt: new Date(),
            updatedAt: new Date(),
            version: 1
          };

          set(state => ({
            strategies: [...state.strategies, newStrategy]
          }));

          return newStrategy;
        } catch (error) {
          console.error('Failed to import strategy:', error);
          return null;
        }
      }
    }),
    {
      name: 'strategy-store',
      partialize: (state) => ({
        strategies: state.strategies,
        templates: state.templates
      })
    }
  )
);