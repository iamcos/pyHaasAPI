import type { 
  Account, 
  Bot, 
  Position, 
  Market, 
  PerformanceMetrics,
  MarketCondition 
} from '@/types/trading'
import type { InsightCard, ProactiveAction } from '@/types/ai'

export interface PortfolioSummary {
  totalValue: number
  totalEquity: number
  unrealizedPnL: number
  realizedPnL: number
  dailyPnL: number
  weeklyPnL: number
  monthlyPnL: number
  activeBots: number
  totalPositions: number
  accountBreakdown: AccountSummary[]
  topPerformers: StrategyPerformance[]
  worstPerformers: StrategyPerformance[]
}

export interface AccountSummary {
  accountId: string
  accountName: string
  balance: number
  equity: number
  unrealizedPnL: number
  positionCount: number
  activeBots: number
  riskScore: number
}

export interface StrategyPerformance {
  strategyId: string
  strategyName: string
  botId?: string
  pnl: number
  pnlPercentage: number
  winRate: number
  trades: number
  status: 'active' | 'inactive' | 'paused'
}

export interface MarketSentiment {
  overall: SentimentIndicator
  byAsset: Record<string, SentimentIndicator>
  volatilityIndex: number
  fearGreedIndex: number
  trendStrength: number
  lastUpdate: Date
}

export interface SentimentIndicator {
  sentiment: 'bullish' | 'bearish' | 'neutral'
  confidence: number
  strength: number
  signals: string[]
  timeframe: string
}

export interface OpportunityAlert {
  id: string
  type: 'arbitrage' | 'breakout' | 'reversal' | 'momentum' | 'correlation'
  title: string
  description: string
  market: string
  confidence: number
  urgency: 'low' | 'medium' | 'high' | 'critical'
  estimatedReturn: number
  riskLevel: number
  expiresAt: Date
  actions: ProactiveAction[]
}

export class DashboardService {
  private static instance: DashboardService
  private portfolioCache: PortfolioSummary | null = null
  private sentimentCache: MarketSentiment | null = null
  private opportunitiesCache: OpportunityAlert[] = []
  private lastUpdate: Date | null = null
  private updateInterval: number = 30000 // 30 seconds

  static getInstance(): DashboardService {
    if (!DashboardService.instance) {
      DashboardService.instance = new DashboardService()
    }
    return DashboardService.instance
  }

  async getPortfolioSummary(
    accounts: Account[], 
    bots: Bot[], 
    positions: Position[]
  ): Promise<PortfolioSummary> {
    // Check cache
    if (this.portfolioCache && this.isDataFresh()) {
      return this.portfolioCache
    }

    // Calculate portfolio metrics
    const totalValue = accounts.reduce((sum, account) => sum + account.equity, 0)
    const totalEquity = accounts.reduce((sum, account) => sum + account.equity, 0)
    const unrealizedPnL = positions.reduce((sum, position) => sum + position.unrealizedPnl, 0)
    
    // Calculate daily/weekly/monthly PnL (mock data for now)
    const dailyPnL = unrealizedPnL * 0.1 // Simplified calculation
    const weeklyPnL = unrealizedPnL * 0.7
    const monthlyPnL = unrealizedPnL * 1.2

    const activeBots = bots.filter(bot => bot.status === 'active').length
    const totalPositions = positions.length

    // Account breakdown
    const accountBreakdown: AccountSummary[] = accounts.map(account => {
      const accountPositions = positions.filter(p => 
        bots.some(bot => bot.accountId === account.id)
      )
      const accountBots = bots.filter(bot => bot.accountId === account.id)
      const accountPnL = accountPositions.reduce((sum, p) => sum + p.unrealizedPnl, 0)
      
      return {
        accountId: account.id,
        accountName: account.name,
        balance: account.balance,
        equity: account.equity,
        unrealizedPnL: accountPnL,
        positionCount: accountPositions.length,
        activeBots: accountBots.filter(bot => bot.status === 'active').length,
        riskScore: this.calculateRiskScore(account, accountPositions)
      }
    })

    // Top and worst performers
    const strategyPerformances = bots.map(bot => ({
      strategyId: bot.labId,
      strategyName: bot.name,
      botId: bot.id,
      pnl: bot.performance.totalReturn,
      pnlPercentage: bot.performance.totalReturn * 100,
      winRate: bot.performance.winRate,
      trades: bot.performance.totalTrades,
      status: bot.status
    }))

    const topPerformers = strategyPerformances
      .sort((a, b) => b.pnl - a.pnl)
      .slice(0, 5)

    const worstPerformers = strategyPerformances
      .sort((a, b) => a.pnl - b.pnl)
      .slice(0, 5)

    this.portfolioCache = {
      totalValue,
      totalEquity,
      unrealizedPnL,
      realizedPnL: 0, // Would need historical data
      dailyPnL,
      weeklyPnL,
      monthlyPnL,
      activeBots,
      totalPositions,
      accountBreakdown,
      topPerformers,
      worstPerformers
    }

    this.lastUpdate = new Date()
    return this.portfolioCache
  }

  async getMarketSentiment(markets: Market[]): Promise<MarketSentiment> {
    // Check cache
    if (this.sentimentCache && this.isDataFresh()) {
      return this.sentimentCache
    }

    // Analyze market sentiment based on price movements
    const byAsset: Record<string, SentimentIndicator> = {}
    let bullishCount = 0
    let bearishCount = 0

    markets.forEach(market => {
      const sentiment = this.analyzeSentiment(market)
      byAsset[market.symbol] = sentiment
      
      if (sentiment.sentiment === 'bullish') bullishCount++
      else if (sentiment.sentiment === 'bearish') bearishCount++
    })

    // Overall sentiment
    const totalMarkets = markets.length
    const bullishRatio = bullishCount / totalMarkets
    const bearishRatio = bearishCount / totalMarkets

    let overallSentiment: 'bullish' | 'bearish' | 'neutral'
    if (bullishRatio > 0.6) overallSentiment = 'bullish'
    else if (bearishRatio > 0.6) overallSentiment = 'bearish'
    else overallSentiment = 'neutral'

    // Calculate indices
    const volatilityIndex = this.calculateVolatilityIndex(markets)
    const fearGreedIndex = this.calculateFearGreedIndex(markets)
    const trendStrength = this.calculateTrendStrength(markets)

    this.sentimentCache = {
      overall: {
        sentiment: overallSentiment,
        confidence: Math.max(bullishRatio, bearishRatio),
        strength: Math.abs(bullishRatio - bearishRatio),
        signals: this.generateOverallSignals(overallSentiment, bullishRatio, bearishRatio),
        timeframe: '1h'
      },
      byAsset,
      volatilityIndex,
      fearGreedIndex,
      trendStrength,
      lastUpdate: new Date()
    }

    return this.sentimentCache
  }

  async getOpportunityAlerts(
    markets: Market[], 
    positions: Position[]
  ): Promise<OpportunityAlert[]> {
    const alerts: OpportunityAlert[] = []

    // Arbitrage opportunities
    const arbitrageOpps = this.findArbitrageOpportunities(markets)
    alerts.push(...arbitrageOpps)

    // Breakout opportunities
    const breakoutOpps = this.findBreakoutOpportunities(markets)
    alerts.push(...breakoutOpps)

    // Correlation opportunities
    const correlationOpps = this.findCorrelationOpportunities(markets, positions)
    alerts.push(...correlationOpps)

    // Sort by urgency and confidence
    alerts.sort((a, b) => {
      const urgencyWeight = { critical: 4, high: 3, medium: 2, low: 1 }
      const aScore = urgencyWeight[a.urgency] * a.confidence
      const bScore = urgencyWeight[b.urgency] * b.confidence
      return bScore - aScore
    })

    this.opportunitiesCache = alerts
    return alerts
  }

  private calculateRiskScore(account: Account, positions: Position[]): number {
    // Simple risk score calculation
    const leverageRisk = account.marginLevel > 200 ? 0 : (200 - account.marginLevel) / 200
    const concentrationRisk = positions.length < 3 ? 0.3 : 0
    const drawdownRisk = positions.reduce((sum, p) => 
      sum + (p.unrealizedPnl < 0 ? Math.abs(p.unrealizedPnl) / account.equity : 0), 0
    )
    
    return Math.min(10, (leverageRisk + concentrationRisk + drawdownRisk) * 10)
  }

  private analyzeSentiment(market: Market): SentimentIndicator {
    const change = market.change24h
    let sentiment: 'bullish' | 'bearish' | 'neutral'
    let confidence: number
    let strength: number

    if (change > 5) {
      sentiment = 'bullish'
      confidence = Math.min(0.9, change / 10)
      strength = Math.min(1, change / 15)
    } else if (change < -5) {
      sentiment = 'bearish'
      confidence = Math.min(0.9, Math.abs(change) / 10)
      strength = Math.min(1, Math.abs(change) / 15)
    } else {
      sentiment = 'neutral'
      confidence = 0.5
      strength = 0.3
    }

    const signals = this.generateSentimentSignals(market, sentiment)

    return {
      sentiment,
      confidence,
      strength,
      signals,
      timeframe: '24h'
    }
  }

  private generateSentimentSignals(market: Market, sentiment: string): string[] {
    const signals: string[] = []
    
    if (sentiment === 'bullish') {
      signals.push(`${market.symbol} up ${market.change24h.toFixed(2)}% in 24h`)
      if (market.volume24h > 1000000) signals.push('High volume supporting move')
    } else if (sentiment === 'bearish') {
      signals.push(`${market.symbol} down ${Math.abs(market.change24h).toFixed(2)}% in 24h`)
      if (market.volume24h > 1000000) signals.push('High volume on decline')
    } else {
      signals.push(`${market.symbol} consolidating`)
    }

    return signals
  }

  private generateOverallSignals(
    sentiment: string, 
    bullishRatio: number, 
    bearishRatio: number
  ): string[] {
    const signals: string[] = []
    
    if (sentiment === 'bullish') {
      signals.push(`${(bullishRatio * 100).toFixed(0)}% of markets showing bullish signals`)
    } else if (sentiment === 'bearish') {
      signals.push(`${(bearishRatio * 100).toFixed(0)}% of markets showing bearish signals`)
    } else {
      signals.push('Mixed market conditions')
    }

    return signals
  }

  private calculateVolatilityIndex(markets: Market[]): number {
    const avgVolatility = markets.reduce((sum, market) => {
      const volatility = Math.abs(market.change24h) / 100
      return sum + volatility
    }, 0) / markets.length

    return Math.min(100, avgVolatility * 100)
  }

  private calculateFearGreedIndex(markets: Market[]): number {
    // Simplified fear/greed calculation
    const positiveChanges = markets.filter(m => m.change24h > 0).length
    const totalMarkets = markets.length
    const greedRatio = positiveChanges / totalMarkets
    
    return Math.round(greedRatio * 100)
  }

  private calculateTrendStrength(markets: Market[]): number {
    const strongTrends = markets.filter(m => Math.abs(m.change24h) > 5).length
    return (strongTrends / markets.length) * 100
  }

  private findArbitrageOpportunities(markets: Market[]): OpportunityAlert[] {
    // Simplified arbitrage detection
    const opportunities: OpportunityAlert[] = []
    
    // Group by base asset
    const assetGroups: Record<string, Market[]> = {}
    markets.forEach(market => {
      if (!assetGroups[market.baseAsset]) {
        assetGroups[market.baseAsset] = []
      }
      assetGroups[market.baseAsset].push(market)
    })

    // Find price differences
    Object.entries(assetGroups).forEach(([asset, assetMarkets]) => {
      if (assetMarkets.length < 2) return

      const prices = assetMarkets.map(m => m.price)
      const minPrice = Math.min(...prices)
      const maxPrice = Math.max(...prices)
      const priceDiff = ((maxPrice - minPrice) / minPrice) * 100

      if (priceDiff > 1) { // 1% arbitrage opportunity
        opportunities.push({
          id: `arb-${asset}-${Date.now()}`,
          type: 'arbitrage',
          title: `${asset} Arbitrage Opportunity`,
          description: `${priceDiff.toFixed(2)}% price difference detected`,
          market: asset,
          confidence: Math.min(0.9, priceDiff / 5),
          urgency: priceDiff > 3 ? 'high' : 'medium',
          estimatedReturn: priceDiff,
          riskLevel: 2,
          expiresAt: new Date(Date.now() + 300000), // 5 minutes
          actions: []
        })
      }
    })

    return opportunities
  }

  private findBreakoutOpportunities(markets: Market[]): OpportunityAlert[] {
    const opportunities: OpportunityAlert[] = []

    markets.forEach(market => {
      const priceRange = market.high24h - market.low24h
      const currentFromHigh = (market.high24h - market.price) / market.high24h
      const currentFromLow = (market.price - market.low24h) / market.low24h

      // Near 24h high (potential breakout)
      if (currentFromHigh < 0.02 && market.change24h > 3) {
        opportunities.push({
          id: `breakout-${market.symbol}-${Date.now()}`,
          type: 'breakout',
          title: `${market.symbol} Breakout Signal`,
          description: `Price near 24h high with strong momentum`,
          market: market.symbol,
          confidence: 0.7,
          urgency: 'medium',
          estimatedReturn: 5,
          riskLevel: 4,
          expiresAt: new Date(Date.now() + 900000), // 15 minutes
          actions: []
        })
      }
    })

    return opportunities
  }

  private findCorrelationOpportunities(
    markets: Market[], 
    positions: Position[]
  ): OpportunityAlert[] {
    const opportunities: OpportunityAlert[] = []

    // Check for over-correlation in portfolio
    const positionSymbols = positions.map(p => p.symbol)
    const correlatedAssets = markets.filter(m => 
      positionSymbols.includes(m.symbol) && 
      m.baseAsset === 'BTC' || m.baseAsset === 'ETH'
    )

    if (correlatedAssets.length > 3) {
      opportunities.push({
        id: `correlation-${Date.now()}`,
        type: 'correlation',
        title: 'High Portfolio Correlation Detected',
        description: 'Consider diversifying into uncorrelated assets',
        market: 'Portfolio',
        confidence: 0.8,
        urgency: 'medium',
        estimatedReturn: 0,
        riskLevel: 6,
        expiresAt: new Date(Date.now() + 3600000), // 1 hour
        actions: []
      })
    }

    return opportunities
  }

  private isDataFresh(): boolean {
    if (!this.lastUpdate) return false
    return Date.now() - this.lastUpdate.getTime() < this.updateInterval
  }

  // Real-time update methods
  invalidateCache(): void {
    this.portfolioCache = null
    this.sentimentCache = null
    this.opportunitiesCache = []
    this.lastUpdate = null
  }

  setUpdateInterval(interval: number): void {
    this.updateInterval = interval
  }
}

export const dashboardService = DashboardService.getInstance()