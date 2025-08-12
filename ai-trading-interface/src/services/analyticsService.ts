import type { Bot, Position, Market, PerformanceMetrics } from '@/types/trading'

export interface AnalyticsMetrics {
  performanceAnalysis: PerformanceAnalysis
  correlationMatrix: CorrelationMatrix
  patternRecognition: PatternAnalysis
  riskAdjustedReturns: RiskAdjustedMetrics
  drawdownAnalysis: DrawdownAnalysis
  portfolioOptimization: OptimizationSuggestions
}

export interface PerformanceAnalysis {
  timeSeriesData: TimeSeriesPoint[]
  benchmarkComparison: BenchmarkComparison
  performanceAttribution: AttributionAnalysis
  rollingMetrics: RollingMetrics
  periodReturns: PeriodReturns
}

export interface TimeSeriesPoint {
  timestamp: Date
  portfolioValue: number
  returns: number
  drawdown: number
  sharpeRatio: number
  volatility: number
}

export interface BenchmarkComparison {
  benchmarkName: string
  portfolioReturn: number
  benchmarkReturn: number
  alpha: number
  beta: number
  trackingError: number
  informationRatio: number
}

export interface AttributionAnalysis {
  assetContribution: AssetContribution[]
  strategyContribution: StrategyContribution[]
  timeContribution: TimeContribution[]
}

export interface AssetContribution {
  asset: string
  weight: number
  return: number
  contribution: number
  activeWeight: number
}

export interface StrategyContribution {
  strategyId: string
  strategyName: string
  allocation: number
  return: number
  contribution: number
  sharpeRatio: number
}

export interface TimeContribution {
  period: string
  return: number
  contribution: number
  volatility: number
}

export interface RollingMetrics {
  window: number // days
  sharpeRatio: number[]
  volatility: number[]
  maxDrawdown: number[]
  calmarRatio: number[]
  timestamps: Date[]
}

export interface PeriodReturns {
  daily: number
  weekly: number
  monthly: number
  quarterly: number
  yearly: number
  inception: number
}

export interface CorrelationMatrix {
  assets: string[]
  correlations: number[][]
  clusters: AssetCluster[]
  diversificationRatio: number
  concentrationRisk: number
}

export interface AssetCluster {
  name: string
  assets: string[]
  avgCorrelation: number
  riskContribution: number
}

export interface PatternAnalysis {
  trendPatterns: TrendPattern[]
  seasonalPatterns: SeasonalPattern[]
  volatilityRegimes: VolatilityRegime[]
  anomalies: Anomaly[]
  predictiveSignals: PredictiveSignal[]
}

export interface TrendPattern {
  type: 'uptrend' | 'downtrend' | 'sideways'
  strength: number
  duration: number
  confidence: number
  startDate: Date
  endDate: Date
  assets: string[]
}

export interface SeasonalPattern {
  pattern: string
  frequency: 'daily' | 'weekly' | 'monthly' | 'quarterly'
  strength: number
  confidence: number
  description: string
  historicalOccurrences: number
}

export interface VolatilityRegime {
  regime: 'low' | 'medium' | 'high' | 'extreme'
  threshold: number
  currentLevel: number
  duration: number
  probability: number
  expectedDuration: number
}

export interface Anomaly {
  type: 'outlier' | 'structural_break' | 'regime_change'
  severity: number
  confidence: number
  timestamp: Date
  description: string
  affectedAssets: string[]
  impact: number
}

export interface PredictiveSignal {
  signal: string
  type: 'momentum' | 'mean_reversion' | 'volatility' | 'correlation'
  strength: number
  confidence: number
  timeHorizon: string
  expectedReturn: number
  riskLevel: number
}

export interface RiskAdjustedMetrics {
  sharpeRatio: number
  sortinoRatio: number
  calmarRatio: number
  omegaRatio: number
  informationRatio: number
  treynorRatio: number
  jensenAlpha: number
  modigliani: number
  var95: number
  var99: number
  cvar95: number
  cvar99: number
}

export interface DrawdownAnalysis {
  currentDrawdown: number
  maxDrawdown: number
  avgDrawdown: number
  drawdownDuration: number
  maxDrawdownDuration: number
  avgDrawdownDuration: number
  recoveryTime: number
  avgRecoveryTime: number
  drawdownFrequency: number
  underwaterCurve: DrawdownPoint[]
}

export interface DrawdownPoint {
  timestamp: Date
  drawdown: number
  duration: number
  inDrawdown: boolean
}

export interface OptimizationSuggestions {
  portfolioEfficiency: number
  suggestedAllocations: AllocationSuggestion[]
  riskReduction: RiskReductionSuggestion[]
  returnEnhancement: ReturnEnhancementSuggestion[]
  diversificationOpportunities: DiversificationSuggestion[]
}

export interface AllocationSuggestion {
  asset: string
  currentWeight: number
  suggestedWeight: number
  rationale: string
  expectedImpact: number
  confidence: number
}

export interface RiskReductionSuggestion {
  type: 'correlation' | 'concentration' | 'volatility' | 'drawdown'
  description: string
  currentLevel: number
  targetLevel: number
  actions: string[]
  expectedReduction: number
}

export interface ReturnEnhancementSuggestion {
  type: 'momentum' | 'mean_reversion' | 'carry' | 'arbitrage'
  description: string
  expectedReturn: number
  riskLevel: number
  timeHorizon: string
  implementation: string[]
}

export interface DiversificationSuggestion {
  currentDiversification: number
  targetDiversification: number
  suggestedAssets: string[]
  rationale: string
  expectedBenefit: number
}

export class AnalyticsService {
  private static instance: AnalyticsService
  private cache: Map<string, any> = new Map()
  private cacheExpiry: Map<string, number> = new Map()

  static getInstance(): AnalyticsService {
    if (!AnalyticsService.instance) {
      AnalyticsService.instance = new AnalyticsService()
    }
    return AnalyticsService.instance
  }

  async generateAnalytics(
    bots: Bot[],
    positions: Position[],
    markets: Market[]
  ): Promise<AnalyticsMetrics> {
    const cacheKey = 'analytics-' + Date.now().toString().slice(0, -4) // Cache for ~10 seconds
    
    if (this.isCached(cacheKey)) {
      return this.cache.get(cacheKey)
    }

    const analytics: AnalyticsMetrics = {
      performanceAnalysis: await this.generatePerformanceAnalysis(bots, positions, markets),
      correlationMatrix: await this.generateCorrelationMatrix(positions, markets),
      patternRecognition: await this.generatePatternAnalysis(markets, positions),
      riskAdjustedReturns: await this.calculateRiskAdjustedMetrics(bots),
      drawdownAnalysis: await this.generateDrawdownAnalysis(bots),
      portfolioOptimization: await this.generateOptimizationSuggestions(bots, positions, markets)
    }

    this.setCache(cacheKey, analytics, 30000) // Cache for 30 seconds
    return analytics
  }

  private async generatePerformanceAnalysis(
    bots: Bot[],
    positions: Position[],
    markets: Market[]
  ): Promise<PerformanceAnalysis> {
    // Generate time series data (mock implementation)
    const timeSeriesData: TimeSeriesPoint[] = []
    const now = new Date()
    
    for (let i = 30; i >= 0; i--) {
      const timestamp = new Date(now.getTime() - i * 24 * 60 * 60 * 1000)
      const portfolioValue = 100000 + Math.random() * 10000 - 5000
      const returns = (Math.random() - 0.5) * 0.04 // ±2% daily returns
      const drawdown = Math.max(0, (Math.random() - 0.8) * 0.2) // 0-4% drawdown
      
      timeSeriesData.push({
        timestamp,
        portfolioValue,
        returns,
        drawdown,
        sharpeRatio: 1.2 + Math.random() * 0.8,
        volatility: 0.15 + Math.random() * 0.1
      })
    }

    // Benchmark comparison
    const benchmarkComparison: BenchmarkComparison = {
      benchmarkName: 'S&P 500',
      portfolioReturn: 0.12,
      benchmarkReturn: 0.08,
      alpha: 0.04,
      beta: 1.2,
      trackingError: 0.05,
      informationRatio: 0.8
    }

    // Performance attribution
    const assetContribution: AssetContribution[] = positions.map(position => ({
      asset: position.symbol,
      weight: Math.random() * 0.3,
      return: (Math.random() - 0.5) * 0.2,
      contribution: (Math.random() - 0.5) * 0.05,
      activeWeight: (Math.random() - 0.5) * 0.1
    }))

    const strategyContribution: StrategyContribution[] = bots.map(bot => ({
      strategyId: bot.id,
      strategyName: bot.name,
      allocation: Math.random() * 0.4,
      return: bot.performance.totalReturn,
      contribution: bot.performance.totalReturn * Math.random() * 0.3,
      sharpeRatio: bot.performance.sharpeRatio
    }))

    const timeContribution: TimeContribution[] = [
      { period: 'Q1', return: 0.03, contribution: 0.015, volatility: 0.12 },
      { period: 'Q2', return: 0.05, contribution: 0.025, volatility: 0.15 },
      { period: 'Q3', return: 0.02, contribution: 0.01, volatility: 0.18 },
      { period: 'Q4', return: 0.04, contribution: 0.02, volatility: 0.14 }
    ]

    // Rolling metrics
    const rollingMetrics: RollingMetrics = {
      window: 30,
      sharpeRatio: Array.from({ length: 30 }, () => 0.8 + Math.random() * 1.2),
      volatility: Array.from({ length: 30 }, () => 0.1 + Math.random() * 0.2),
      maxDrawdown: Array.from({ length: 30 }, () => Math.random() * 0.15),
      calmarRatio: Array.from({ length: 30 }, () => 0.5 + Math.random() * 1.5),
      timestamps: Array.from({ length: 30 }, (_, i) => 
        new Date(now.getTime() - i * 24 * 60 * 60 * 1000)
      )
    }

    return {
      timeSeriesData,
      benchmarkComparison,
      performanceAttribution: {
        assetContribution,
        strategyContribution,
        timeContribution
      },
      rollingMetrics,
      periodReturns: {
        daily: 0.001,
        weekly: 0.007,
        monthly: 0.03,
        quarterly: 0.09,
        yearly: 0.12,
        inception: 0.15
      }
    }
  }

  private async generateCorrelationMatrix(
    positions: Position[],
    markets: Market[]
  ): Promise<CorrelationMatrix> {
    const assets = positions.map(p => p.symbol)
    const n = assets.length
    
    // Generate correlation matrix (mock data)
    const correlations: number[][] = []
    for (let i = 0; i < n; i++) {
      correlations[i] = []
      for (let j = 0; j < n; j++) {
        if (i === j) {
          correlations[i][j] = 1.0
        } else {
          // Generate realistic correlations
          const baseCorr = assets[i].includes('BTC') && assets[j].includes('BTC') ? 0.8 :
                          assets[i].includes('ETH') && assets[j].includes('ETH') ? 0.7 :
                          0.3 + Math.random() * 0.4
          correlations[i][j] = correlations[j] ? correlations[j][i] : baseCorr
        }
      }
    }

    // Identify clusters
    const clusters: AssetCluster[] = [
      {
        name: 'Major Cryptocurrencies',
        assets: assets.filter(a => a.includes('BTC') || a.includes('ETH')),
        avgCorrelation: 0.75,
        riskContribution: 0.6
      },
      {
        name: 'Altcoins',
        assets: assets.filter(a => !a.includes('BTC') && !a.includes('ETH')),
        avgCorrelation: 0.45,
        riskContribution: 0.4
      }
    ]

    return {
      assets,
      correlations,
      clusters,
      diversificationRatio: 0.65,
      concentrationRisk: 0.35
    }
  }

  private async generatePatternAnalysis(
    markets: Market[],
    positions: Position[]
  ): Promise<PatternAnalysis> {
    const trendPatterns: TrendPattern[] = [
      {
        type: 'uptrend',
        strength: 0.8,
        duration: 14,
        confidence: 0.85,
        startDate: new Date(Date.now() - 14 * 24 * 60 * 60 * 1000),
        endDate: new Date(),
        assets: ['BTC/USDT', 'ETH/USDT']
      },
      {
        type: 'sideways',
        strength: 0.6,
        duration: 7,
        confidence: 0.7,
        startDate: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000),
        endDate: new Date(),
        assets: ['ADA/USDT']
      }
    ]

    const seasonalPatterns: SeasonalPattern[] = [
      {
        pattern: 'Monday Effect',
        frequency: 'weekly',
        strength: 0.3,
        confidence: 0.6,
        description: 'Lower returns typically observed on Mondays',
        historicalOccurrences: 45
      },
      {
        pattern: 'End of Month Rally',
        frequency: 'monthly',
        strength: 0.5,
        confidence: 0.7,
        description: 'Higher returns in last 3 days of month',
        historicalOccurrences: 8
      }
    ]

    const volatilityRegimes: VolatilityRegime[] = [
      {
        regime: 'medium',
        threshold: 0.25,
        currentLevel: 0.22,
        duration: 12,
        probability: 0.7,
        expectedDuration: 18
      }
    ]

    const anomalies: Anomaly[] = [
      {
        type: 'outlier',
        severity: 0.8,
        confidence: 0.9,
        timestamp: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000),
        description: 'Unusual price spike detected in BTC/USDT',
        affectedAssets: ['BTC/USDT'],
        impact: 0.05
      }
    ]

    const predictiveSignals: PredictiveSignal[] = [
      {
        signal: 'Momentum Continuation',
        type: 'momentum',
        strength: 0.7,
        confidence: 0.75,
        timeHorizon: '1-3 days',
        expectedReturn: 0.03,
        riskLevel: 0.4
      },
      {
        signal: 'Mean Reversion Setup',
        type: 'mean_reversion',
        strength: 0.6,
        confidence: 0.65,
        timeHorizon: '3-7 days',
        expectedReturn: 0.02,
        riskLevel: 0.3
      }
    ]

    return {
      trendPatterns,
      seasonalPatterns,
      volatilityRegimes,
      anomalies,
      predictiveSignals
    }
  }

  private async calculateRiskAdjustedMetrics(bots: Bot[]): Promise<RiskAdjustedMetrics> {
    // Calculate portfolio-level metrics from bot performances
    const totalReturn = bots.reduce((sum, bot) => sum + bot.performance.totalReturn, 0) / bots.length
    const avgVolatility = bots.reduce((sum, bot) => sum + bot.performance.volatility, 0) / bots.length
    const avgSharpe = bots.reduce((sum, bot) => sum + bot.performance.sharpeRatio, 0) / bots.length

    return {
      sharpeRatio: avgSharpe,
      sortinoRatio: avgSharpe * 1.2, // Approximation
      calmarRatio: totalReturn / 0.1, // Assuming 10% max drawdown
      omegaRatio: 1.5,
      informationRatio: 0.8,
      treynorRatio: totalReturn / 1.2, // Assuming beta of 1.2
      jensenAlpha: 0.02,
      modigliani: avgSharpe * avgVolatility,
      var95: -0.05, // 5% VaR
      var99: -0.08, // 8% VaR
      cvar95: -0.07, // 7% CVaR
      cvar99: -0.12  // 12% CVaR
    }
  }

  private async generateDrawdownAnalysis(bots: Bot[]): Promise<DrawdownAnalysis> {
    const maxDrawdown = Math.max(...bots.map(bot => bot.performance.maxDrawdown))
    
    // Generate underwater curve (mock data)
    const underwaterCurve: DrawdownPoint[] = []
    const now = new Date()
    
    for (let i = 90; i >= 0; i--) {
      const timestamp = new Date(now.getTime() - i * 24 * 60 * 60 * 1000)
      const drawdown = Math.max(0, (Math.random() - 0.85) * 0.3) // Occasional drawdowns
      const inDrawdown = drawdown > 0.01
      
      underwaterCurve.push({
        timestamp,
        drawdown,
        duration: inDrawdown ? Math.floor(Math.random() * 10) + 1 : 0,
        inDrawdown
      })
    }

    return {
      currentDrawdown: 0.03,
      maxDrawdown,
      avgDrawdown: maxDrawdown * 0.4,
      drawdownDuration: 5,
      maxDrawdownDuration: 12,
      avgDrawdownDuration: 3,
      recoveryTime: 8,
      avgRecoveryTime: 6,
      drawdownFrequency: 0.15, // 15% of time in drawdown
      underwaterCurve
    }
  }

  private async generateOptimizationSuggestions(
    bots: Bot[],
    positions: Position[],
    markets: Market[]
  ): Promise<OptimizationSuggestions> {
    const suggestedAllocations: AllocationSuggestion[] = positions.map(position => ({
      asset: position.symbol,
      currentWeight: Math.random() * 0.3,
      suggestedWeight: Math.random() * 0.25 + 0.1,
      rationale: 'Optimize risk-adjusted returns based on correlation analysis',
      expectedImpact: (Math.random() - 0.5) * 0.02,
      confidence: 0.7 + Math.random() * 0.2
    }))

    const riskReduction: RiskReductionSuggestion[] = [
      {
        type: 'correlation',
        description: 'Reduce correlation between BTC and ETH positions',
        currentLevel: 0.85,
        targetLevel: 0.65,
        actions: ['Add uncorrelated assets', 'Reduce position sizes'],
        expectedReduction: 0.15
      },
      {
        type: 'concentration',
        description: 'Diversify away from crypto concentration',
        currentLevel: 0.9,
        targetLevel: 0.7,
        actions: ['Add traditional assets', 'Implement sector rotation'],
        expectedReduction: 0.2
      }
    ]

    const returnEnhancement: ReturnEnhancementSuggestion[] = [
      {
        type: 'momentum',
        description: 'Capitalize on current uptrend momentum',
        expectedReturn: 0.05,
        riskLevel: 0.6,
        timeHorizon: '1-2 weeks',
        implementation: ['Increase momentum strategy allocation', 'Add trend-following filters']
      }
    ]

    const diversificationOpportunities: DiversificationSuggestion[] = [
      {
        currentDiversification: 0.4,
        targetDiversification: 0.7,
        suggestedAssets: ['GOLD/USD', 'SPY', 'TLT'],
        rationale: 'Add non-correlated asset classes to improve risk-adjusted returns',
        expectedBenefit: 0.3
      }
    ]

    return {
      portfolioEfficiency: 0.65,
      suggestedAllocations,
      riskReduction,
      returnEnhancement,
      diversificationOpportunities
    }
  }

  private isCached(key: string): boolean {
    const expiry = this.cacheExpiry.get(key)
    if (!expiry || Date.now() > expiry) {
      this.cache.delete(key)
      this.cacheExpiry.delete(key)
      return false
    }
    return this.cache.has(key)
  }

  private setCache(key: string, value: any, ttl: number): void {
    this.cache.set(key, value)
    this.cacheExpiry.set(key, Date.now() + ttl)
  }

  clearCache(): void {
    this.cache.clear()
    this.cacheExpiry.clear()
  }
}

export const analyticsService = AnalyticsService.getInstance()