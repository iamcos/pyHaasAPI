import type { Account, Bot, Position, Market, TradingStrategy } from '@/types/trading'

export function generateMockAccounts(): Account[] {
  return [
    {
      id: 'acc-1',
      name: 'Main Trading Account',
      type: 'live',
      balance: 50000,
      equity: 52500,
      margin: 5000,
      freeMargin: 47500,
      marginLevel: 1050,
      currency: 'USD'
    },
    {
      id: 'acc-2', 
      name: 'Demo Account',
      type: 'simulated',
      balance: 10000,
      equity: 9750,
      margin: 1000,
      freeMargin: 8750,
      marginLevel: 975,
      currency: 'USD'
    },
    {
      id: 'acc-3',
      name: 'Conservative Portfolio',
      type: 'live',
      balance: 25000,
      equity: 25800,
      margin: 2000,
      freeMargin: 23800,
      marginLevel: 1290,
      currency: 'USD'
    }
  ]
}

export function generateMockBots(): Bot[] {
  return [
    {
      id: 'bot-1',
      name: 'BTC Momentum Scalper',
      labId: 'lab-1',
      accountId: 'acc-1',
      status: 'active',
      performance: {
        totalReturn: 0.15,
        sharpeRatio: 1.8,
        maxDrawdown: 0.08,
        winRate: 0.65,
        profitFactor: 1.4,
        totalTrades: 127,
        avgTradeReturn: 0.012,
        volatility: 0.25,
        calmarRatio: 1.9,
        sortinoRatio: 2.1
      },
      currentPosition: {
        symbol: 'BTC/USDT',
        side: 'long',
        quantity: 0.5,
        entryPrice: 45000,
        currentPrice: 46200,
        unrealizedPnl: 600,
        timestamp: new Date()
      },
      createdAt: new Date('2024-01-15'),
      activatedAt: new Date('2024-01-16')
    },
    {
      id: 'bot-2',
      name: 'ETH Grid Trading',
      labId: 'lab-2',
      accountId: 'acc-1',
      status: 'active',
      performance: {
        totalReturn: 0.08,
        sharpeRatio: 1.2,
        maxDrawdown: 0.05,
        winRate: 0.72,
        profitFactor: 1.6,
        totalTrades: 89,
        avgTradeReturn: 0.009,
        volatility: 0.18,
        calmarRatio: 1.6,
        sortinoRatio: 1.8
      },
      currentPosition: {
        symbol: 'ETH/USDT',
        side: 'long',
        quantity: 5,
        entryPrice: 2800,
        currentPrice: 2850,
        unrealizedPnl: 250,
        timestamp: new Date()
      },
      createdAt: new Date('2024-01-20'),
      activatedAt: new Date('2024-01-21')
    },
    {
      id: 'bot-3',
      name: 'DOGE Swing Strategy',
      labId: 'lab-3',
      accountId: 'acc-2',
      status: 'paused',
      performance: {
        totalReturn: -0.03,
        sharpeRatio: 0.8,
        maxDrawdown: 0.12,
        winRate: 0.45,
        profitFactor: 0.9,
        totalTrades: 45,
        avgTradeReturn: -0.007,
        volatility: 0.35,
        calmarRatio: -0.25,
        sortinoRatio: 0.6
      },
      createdAt: new Date('2024-02-01'),
      activatedAt: new Date('2024-02-02')
    }
  ]
}

export function generateMockPositions(): Position[] {
  return [
    {
      symbol: 'BTC/USDT',
      side: 'long',
      quantity: 0.5,
      entryPrice: 45000,
      currentPrice: 46200,
      unrealizedPnl: 600,
      timestamp: new Date()
    },
    {
      symbol: 'ETH/USDT',
      side: 'long',
      quantity: 5,
      entryPrice: 2800,
      currentPrice: 2850,
      unrealizedPnl: 250,
      timestamp: new Date()
    },
    {
      symbol: 'ADA/USDT',
      side: 'short',
      quantity: 1000,
      entryPrice: 0.45,
      currentPrice: 0.42,
      unrealizedPnl: 30,
      timestamp: new Date()
    },
    {
      symbol: 'SOL/USDT',
      side: 'long',
      quantity: 10,
      entryPrice: 95,
      currentPrice: 98,
      unrealizedPnl: 30,
      timestamp: new Date()
    }
  ]
}

export function generateMockMarkets(): Market[] {
  return [
    {
      id: 'btc-usdt',
      symbol: 'BTC/USDT',
      exchange: 'Binance',
      baseAsset: 'BTC',
      quoteAsset: 'USDT',
      price: 46200,
      volume24h: 28500000,
      change24h: 2.8,
      high24h: 46800,
      low24h: 44500,
      lastUpdate: new Date()
    },
    {
      id: 'eth-usdt',
      symbol: 'ETH/USDT',
      exchange: 'Binance',
      baseAsset: 'ETH',
      quoteAsset: 'USDT',
      price: 2850,
      volume24h: 15200000,
      change24h: 1.8,
      high24h: 2890,
      low24h: 2780,
      lastUpdate: new Date()
    },
    {
      id: 'ada-usdt',
      symbol: 'ADA/USDT',
      exchange: 'Binance',
      baseAsset: 'ADA',
      quoteAsset: 'USDT',
      price: 0.42,
      volume24h: 8500000,
      change24h: -6.7,
      high24h: 0.46,
      low24h: 0.41,
      lastUpdate: new Date()
    },
    {
      id: 'sol-usdt',
      symbol: 'SOL/USDT',
      exchange: 'Binance',
      baseAsset: 'SOL',
      quoteAsset: 'USDT',
      price: 98,
      volume24h: 12000000,
      change24h: 3.2,
      high24h: 102,
      low24h: 94,
      lastUpdate: new Date()
    },
    {
      id: 'doge-usdt',
      symbol: 'DOGE/USDT',
      exchange: 'Binance',
      baseAsset: 'DOGE',
      quoteAsset: 'USDT',
      price: 0.08,
      volume24h: 5500000,
      change24h: -2.1,
      high24h: 0.085,
      low24h: 0.078,
      lastUpdate: new Date()
    }
  ]
}

export function initializeMockData() {
  return {
    accounts: generateMockAccounts(),
    bots: generateMockBots(),
    positions: generateMockPositions(),
    markets: generateMockMarkets()
  }
}