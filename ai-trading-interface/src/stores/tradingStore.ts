import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { initializeMockData } from '@/utils/mockData'
import type { 
  TradingStrategy, 
  Lab, 
  Bot, 
  Account, 
  Market, 
  BacktestResult,
  Position 
} from '@/types'

interface TradingState {
  // Trading entities
  strategies: TradingStrategy[]
  labs: Lab[]
  bots: Bot[]
  accounts: Account[]
  markets: Market[]
  positions: Position[]
  
  // Current selections
  selectedStrategy: string | null
  selectedLab: string | null
  selectedBot: string | null
  selectedAccount: string | null
  
  // Loading states
  loading: {
    strategies: boolean
    labs: boolean
    bots: boolean
    accounts: boolean
    markets: boolean
    backtesting: boolean
  }
  
  // Error states
  errors: {
    strategies: string | null
    labs: string | null
    bots: string | null
    accounts: string | null
    markets: string | null
    backtesting: string | null
  }
  
  // Actions
  setStrategies: (strategies: TradingStrategy[]) => void
  addStrategy: (strategy: TradingStrategy) => void
  updateStrategy: (id: string, updates: Partial<TradingStrategy>) => void
  removeStrategy: (id: string) => void
  selectStrategy: (id: string | null) => void
  
  setLabs: (labs: Lab[]) => void
  addLab: (lab: Lab) => void
  updateLab: (id: string, updates: Partial<Lab>) => void
  removeLab: (id: string) => void
  selectLab: (id: string | null) => void
  
  setBots: (bots: Bot[]) => void
  addBot: (bot: Bot) => void
  updateBot: (id: string, updates: Partial<Bot>) => void
  removeBot: (id: string) => void
  selectBot: (id: string | null) => void
  
  setAccounts: (accounts: Account[]) => void
  addAccount: (account: Account) => void
  updateAccount: (id: string, updates: Partial<Account>) => void
  selectAccount: (id: string | null) => void
  
  setMarkets: (markets: Market[]) => void
  updateMarketPrice: (symbol: string, price: number) => void
  
  setPositions: (positions: Position[]) => void
  updatePosition: (symbol: string, updates: Partial<Position>) => void
  
  setLoading: (key: keyof TradingState['loading'], loading: boolean) => void
  setError: (key: keyof TradingState['errors'], error: string | null) => void
  clearErrors: () => void
}

export const useTradingStore = create<TradingState>()(
  persist(
    (set, get) => {
      // Initialize with mock data
      const mockData = initializeMockData()
      
      return {
        // Initial state with mock data
        strategies: [],
        labs: [],
        bots: mockData.bots,
        accounts: mockData.accounts,
        markets: mockData.markets,
        positions: mockData.positions,
      
      selectedStrategy: null,
      selectedLab: null,
      selectedBot: null,
      selectedAccount: null,
      
      loading: {
        strategies: false,
        labs: false,
        bots: false,
        accounts: false,
        markets: false,
        backtesting: false,
      },
      
      errors: {
        strategies: null,
        labs: null,
        bots: null,
        accounts: null,
        markets: null,
        backtesting: null,
      },
      
      // Strategy actions
      setStrategies: (strategies) => set({ strategies }),
      
      addStrategy: (strategy) => set((state) => ({
        strategies: [...state.strategies, strategy]
      })),
      
      updateStrategy: (id, updates) => set((state) => ({
        strategies: state.strategies.map(strategy =>
          strategy.id === id ? { ...strategy, ...updates } : strategy
        )
      })),
      
      removeStrategy: (id) => set((state) => ({
        strategies: state.strategies.filter(strategy => strategy.id !== id),
        selectedStrategy: state.selectedStrategy === id ? null : state.selectedStrategy
      })),
      
      selectStrategy: (id) => set({ selectedStrategy: id }),
      
      // Lab actions
      setLabs: (labs) => set({ labs }),
      
      addLab: (lab) => set((state) => ({
        labs: [...state.labs, lab]
      })),
      
      updateLab: (id, updates) => set((state) => ({
        labs: state.labs.map(lab =>
          lab.id === id ? { ...lab, ...updates } : lab
        )
      })),
      
      removeLab: (id) => set((state) => ({
        labs: state.labs.filter(lab => lab.id !== id),
        selectedLab: state.selectedLab === id ? null : state.selectedLab
      })),
      
      selectLab: (id) => set({ selectedLab: id }),
      
      // Bot actions
      setBots: (bots) => set({ bots }),
      
      addBot: (bot) => set((state) => ({
        bots: [...state.bots, bot]
      })),
      
      updateBot: (id, updates) => set((state) => ({
        bots: state.bots.map(bot =>
          bot.id === id ? { ...bot, ...updates } : bot
        )
      })),
      
      removeBot: (id) => set((state) => ({
        bots: state.bots.filter(bot => bot.id !== id),
        selectedBot: state.selectedBot === id ? null : state.selectedBot
      })),
      
      selectBot: (id) => set({ selectedBot: id }),
      
      // Account actions
      setAccounts: (accounts) => set({ accounts }),
      
      addAccount: (account) => set((state) => ({
        accounts: [...state.accounts, account]
      })),
      
      updateAccount: (id, updates) => set((state) => ({
        accounts: state.accounts.map(account =>
          account.id === id ? { ...account, ...updates } : account
        )
      })),
      
      selectAccount: (id) => set({ selectedAccount: id }),
      
      // Market actions
      setMarkets: (markets) => set({ markets }),
      
      updateMarketPrice: (symbol, price) => set((state) => ({
        markets: state.markets.map(market =>
          market.symbol === symbol 
            ? { ...market, price, lastUpdate: new Date() }
            : market
        )
      })),
      
      // Position actions
      setPositions: (positions) => set({ positions }),
      
      updatePosition: (symbol, updates) => set((state) => ({
        positions: state.positions.map(position =>
          position.symbol === symbol ? { ...position, ...updates } : position
        )
      })),
      
      // Utility actions
      setLoading: (key, loading) => set((state) => ({
        loading: { ...state.loading, [key]: loading }
      })),
      
      setError: (key, error) => set((state) => ({
        errors: { ...state.errors, [key]: error }
      })),
      
      clearErrors: () => set({
        errors: {
          strategies: null,
          labs: null,
          bots: null,
          accounts: null,
          markets: null,
          backtesting: null,
        }
      }),
      }
    },
    {
      name: 'trading-store',
      partialize: (state) => ({
        // Only persist non-volatile data
        strategies: state.strategies,
        selectedStrategy: state.selectedStrategy,
        selectedLab: state.selectedLab,
        selectedBot: state.selectedBot,
        selectedAccount: state.selectedAccount,
        // Don't persist real-time data like markets, positions, loading states
      }),
    }
  )
)