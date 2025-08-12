// Core Trading Data Models
export interface TradingStrategy {
  id: string
  name: string
  description: string
  haasScript: string
  parameters: StrategyParameter[]
  performance: PerformanceMetrics
  riskProfile: RiskProfile
  marketConditions: MarketCondition[]
  chainOfThought: any[] // Will be properly typed when ai.ts is imported
  createdAt: Date
  updatedAt: Date
}

export interface StrategyParameter {
  id: string
  name: string
  type: 'number' | 'boolean' | 'string' | 'timeframe' | 'indicator'
  value: any
  min?: number
  max?: number
  step?: number
  options?: string[]
  description: string
}

export interface PerformanceMetrics {
  totalReturn: number
  sharpeRatio: number
  maxDrawdown: number
  winRate: number
  profitFactor: number
  totalTrades: number
  avgTradeReturn: number
  volatility: number
  calmarRatio: number
  sortinoRatio: number
}

export interface RiskProfile {
  riskLevel: 'conservative' | 'moderate' | 'aggressive' | 'high_risk'
  maxDrawdownLimit: number
  positionSizeLimit: number
  correlationLimit: number
  volatilityLimit: number
}

export interface MarketCondition {
  type: 'trending' | 'ranging' | 'volatile' | 'low_volume' | 'high_volume'
  confidence: number
  timeframe: string
  description: string
}

// Lab and Bot Models
export interface Lab {
  id: string
  name: string
  scriptId: string
  accountId: string
  parameters: Record<string, any>
  status: 'idle' | 'running' | 'completed' | 'failed'
  createdAt: Date
  lastBacktest?: BacktestResult
}

export interface Bot {
  id: string
  name: string
  labId: string
  accountId: string
  status: 'active' | 'inactive' | 'paused' | 'error'
  performance: PerformanceMetrics
  currentPosition?: Position
  createdAt: Date
  activatedAt?: Date
}

export interface BacktestResult {
  id: string
  labId: string
  startDate: Date
  endDate: Date
  performance: PerformanceMetrics
  trades: Trade[]
  equity: EquityPoint[]
  status: 'completed' | 'failed' | 'running'
  duration: number
}

export interface Trade {
  id: string
  symbol: string
  side: 'buy' | 'sell'
  quantity: number
  price: number
  timestamp: Date
  pnl: number
  commission: number
}

export interface EquityPoint {
  timestamp: Date
  equity: number
  drawdown: number
}

export interface Position {
  symbol: string
  side: 'long' | 'short'
  quantity: number
  entryPrice: number
  currentPrice: number
  unrealizedPnl: number
  timestamp: Date
}

// Account and Market Models
export interface Account {
  id: string
  name: string
  type: 'simulated' | 'live'
  balance: number
  equity: number
  margin: number
  freeMargin: number
  marginLevel: number
  currency: string
}

export interface Market {
  id: string
  symbol: string
  baseAsset: string
  quoteAsset: string
  exchange: string
  price: number
  volume24h: number
  change24h: number
  changePercent24h: number
  high24h: number
  low24h: number
  marketCap?: number
  category: MarketCategory
  status: 'active' | 'inactive' | 'delisted'
  lastUpdated: Date
}

export interface MarketCategory {
  primary: string // e.g., 'crypto', 'forex', 'stocks'
  secondary?: string // e.g., 'defi', 'gaming', 'layer1'
  tags: string[]
}

export interface OrderBook {
  marketId: string
  timestamp: Date
  bids: OrderBookEntry[]
  asks: OrderBookEntry[]
  spread: number
  spreadPercent: number
}

export interface OrderBookEntry {
  price: number
  quantity: number
  total: number
}

export interface PriceData {
  marketId: string
  timestamp: Date
  open: number
  high: number
  low: number
  close: number
  volume: number
}

export interface MarketFilter {
  exchange?: string[]
  category?: string[]
  minVolume?: number
  maxVolume?: number
  minPrice?: number
  maxPrice?: number
  changeRange?: {
    min: number
    max: number
  }
  search?: string
}

export interface MarketSort {
  field: 'symbol' | 'price' | 'volume24h' | 'change24h' | 'marketCap'
  direction: 'asc' | 'desc'
}

export interface MarketStats {
  totalMarkets: number
  activeMarkets: number
  totalVolume24h: number
  topGainers: Market[]
  topLosers: Market[]
  mostActive: Market[]
}

export interface MarketDataSubscription {
  marketIds: string[]
  dataTypes: ('price' | 'orderbook' | 'trades')[]
  callback: (data: any) => void
}