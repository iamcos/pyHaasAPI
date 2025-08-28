import { vi } from 'vitest'
import type { Market, Portfolio, TradingBot, Lab } from '../../types/trading'

export const mockTradingService = {
  getMarkets: vi.fn().mockResolvedValue([
    {
      id: 'BTC-USD',
      symbol: 'BTC/USD',
      exchange: 'Binance',
      price: 45000,
      volume24h: 1000000,
      change24h: 2.5,
    },
    {
      id: 'ETH-USD',
      symbol: 'ETH/USD',
      exchange: 'Binance',
      price: 3000,
      volume24h: 500000,
      change24h: -1.2,
    },
  ] as Market[]),

  getPortfolio: vi.fn().mockResolvedValue({
    id: 'portfolio-1',
    totalValue: 100000,
    totalPnL: 5000,
    totalPnLPercent: 5.0,
    positions: [
      {
        symbol: 'BTC/USD',
        quantity: 1.5,
        averagePrice: 42000,
        currentPrice: 45000,
        pnl: 4500,
        pnlPercent: 7.14,
      },
    ],
    accounts: [
      {
        id: 'account-1',
        name: 'Main Account',
        balance: 50000,
        exchange: 'Binance',
      },
    ],
  } as Portfolio),

  getBots: vi.fn().mockResolvedValue([
    {
      id: 'bot-1',
      name: 'Scalper Bot',
      status: 'active',
      strategy: 'scalping',
      pnl: 1500,
      pnlPercent: 3.0,
      trades: 25,
      winRate: 68,
    },
    {
      id: 'bot-2',
      name: 'Trend Bot',
      status: 'paused',
      strategy: 'trend-following',
      pnl: -200,
      pnlPercent: -0.4,
      trades: 8,
      winRate: 37.5,
    },
  ] as TradingBot[]),

  getLabs: vi.fn().mockResolvedValue([
    {
      id: 'lab-1',
      name: 'Test Lab',
      status: 'running',
      strategy: 'RSI Strategy',
      market: 'BTC/USD',
      performance: {
        totalReturn: 15.5,
        sharpeRatio: 1.8,
        maxDrawdown: -8.2,
        winRate: 65,
      },
    },
  ] as Lab[]),

  createBot: vi.fn().mockResolvedValue({
    id: 'new-bot-1',
    name: 'New Bot',
    status: 'created',
  }),

  activateBot: vi.fn().mockResolvedValue(true),
  deactivateBot: vi.fn().mockResolvedValue(true),
  deleteBot: vi.fn().mockResolvedValue(true),
}

export const createMockMarket = (overrides?: Partial<Market>): Market => ({
  id: 'BTC-USD',
  symbol: 'BTC/USD',
  exchange: 'Binance',
  price: 45000,
  volume24h: 1000000,
  change24h: 2.5,
  ...overrides,
})

export const createMockPortfolio = (overrides?: Partial<Portfolio>): Portfolio => ({
  id: 'portfolio-1',
  totalValue: 100000,
  totalPnL: 5000,
  totalPnLPercent: 5.0,
  positions: [],
  accounts: [],
  ...overrides,
})