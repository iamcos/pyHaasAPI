import type { Bot, Position, Market, PerformanceMetrics } from '@/types/trading'

export interface StressTestScenario {
  id: string
  name: string
  description: string
  category: 'market_crash' | 'volatility_spike' | 'correlation_breakdown' | 'liquidity_crisis' | 'custom'
  parameters: ScenarioParameters
  severity: 'mild' | 'moderate' | 'severe' | 'extreme'
  duration: number // days
  probability: number // historical probability
  historicalExamples: string[]
}

export interface ScenarioParameters {
  marketShock: MarketShockParams
  volatilityChange: VolatilityParams
  correlationChange: CorrelationParams
  liquidityImpact: LiquidityParams
  customFactors: CustomFactorParams[]
}

export interface MarketShockParams {
  enabled: boolean
  magnitude: number // percentage decline
  affectedAssets: string[]
  shockType: 'instant' | 'gradual' | 'cascading'
  recoveryTime: number // days
  recoveryShape: 'linear' | 'exponential' | 'v_shaped' | 'l_shaped'
}

export interface VolatilityParams {
  enabled: boolean
  multiplier: number // volatility increase factor
  duration: number // days
  affectedAssets: string[]
  volatilityType: 'uniform' | 'clustered' | 'regime_change'
}

export interface CorrelationParams {
  enabled: boolean
  newCorrelation: number // target correlation during stress
  affectedPairs: string[][]
  correlationType: 'increase' | 'decrease' | 'breakdown'
}

export interface LiquidityParams {
  enabled: boolean
  liquidityReduction: number // percentage reduction
  bidAskSpreadIncrease: number // multiplier
  affectedAssets: string[]
  impactType: 'uniform' | 'size_dependent' | 'asset_specific'
}

export interface CustomFactorParams {
  name: string
  type: 'price_multiplier' | 'volatility_multiplier' | 'correlation_shift' | 'volume_impact'
  value: number
  affectedAssets: string[]
  duration: number
}

export interface StressTestResult {
  scenarioId: string
  scenarioName: string
  executionTime: Date
  duration: number
  results: StressTestMetrics
  portfolioImpact: PortfolioImpact
  riskMetrics: StressRiskMetrics
  recommendations: StressTestRecommendation[]
  timeSeriesData: StressTimeSeriesPoint[]
}

export interface StressTestMetrics {
  totalReturn: number
  maxDrawdown: number
  volatility: number
  sharpeRatio: number
  var95: number
  var99: number
  expectedShortfall: number
  recoveryTime: number
  survivabilityScore: number
}

export interface PortfolioImpact {
  initialValue: number
  finalValue: number
  worstValue: number
  peakToTrough: number
  assetImpacts: AssetImpact[]
  strategyImpacts: StrategyImpact[]
}

export interface AssetImpact {
  asset: string
  initialWeight: number
  finalWeight: number
  pnl: number
  pnlPercentage: number
  maxDrawdown: number
  contribution: number
}

export interface StrategyImpact {
  strategyId: string
  strategyName: string
  pnl: number
  pnlPercentage: number
  maxDrawdown: number
  sharpeRatio: number
  survivability: number
}

export interface StressRiskMetrics {
  concentrationRisk: number
  correlationRisk: number
  liquidityRisk: number
  leverageRisk: number
  tailRisk: number
  systemicRisk: number
}

export interface StressTestRecommendation {
  type: 'position_sizing' | 'diversification' | 'hedging' | 'liquidity' | 'risk_management'
  priority: 'high' | 'medium' | 'low'
  title: string
  description: string
  expectedBenefit: number
  implementationCost: number
  timeframe: string
  actions: string[]
}

export interface StressTimeSeriesPoint {
  timestamp: Date
  portfolioValue: number
  drawdown: number
  volatility: number
  var95: number
  liquidityScore: number
  correlationLevel: number
}

export interface StressTestConfiguration {
  scenarios: StressTestScenario[]
  portfolioSettings: PortfolioSettings
  simulationSettings: SimulationSettings
  reportingSettings: ReportingSettings
}

export interface PortfolioSettings {
  includeAllPositions: boolean
  selectedAssets: string[]
  selectedStrategies: string[]
  rebalancingFrequency: 'none' | 'daily' | 'weekly' | 'monthly'
  cashBuffer: number
}

export interface SimulationSettings {
  timeStep: number // hours
  monteCarloRuns: number
  confidenceLevel: number
  randomSeed?: number
  includeTransactionCosts: boolean
  includeSlippage: boolean
}

export interface ReportingSettings {
  includeTimeSeriesData: boolean
  includeAssetBreakdown: boolean
  includeStrategyBreakdown: boolean
  includeRecommendations: boolean
  exportFormat: 'json' | 'csv' | 'pdf'
}

export class StressTestingService {
  private static instance: StressTestingService
  private predefinedScenarios: StressTestScenario[]
  private runningTests: Map<string, Promise<StressTestResult>> = new Map()

  static getInstance(): StressTestingService {
    if (!StressTestingService.instance) {
      StressTestingService.instance = new StressTestingService()
    }
    return StressTestingService.instance
  }

  constructor() {
    this.predefinedScenarios = this.initializePredefinedScenarios()
  }

  private initializePredefinedScenarios(): StressTestScenario[] {
    return [
      {
        id: 'market-crash-2008',
        name: '2008 Financial Crisis',
        description: 'Severe market crash with high correlation and liquidity crisis',
        category: 'market_crash',
        severity: 'extreme',
        duration: 180,
        probability: 0.02,
        historicalExamples: ['2008 Financial Crisis', 'Black Monday 1987'],
        parameters: {
          marketShock: {
            enabled: true,
            magnitude: -0.4,
            affectedAssets: ['*'],
            shockType: 'cascading',
            recoveryTime: 365,
            recoveryShape: 'l_shaped'
          },
          volatilityChange: {
            enabled: true,
            multiplier: 3.0,
            duration: 90,
            affectedAssets: ['*'],
            volatilityType: 'clustered'
          },
          correlationChange: {
            enabled: true,
            newCorrelation: 0.9,
            affectedPairs: [['*', '*']],
            correlationType: 'increase'
          },
          liquidityImpact: {
            enabled: true,
            liquidityReduction: 0.7,
            bidAskSpreadIncrease: 5.0,
            affectedAssets: ['*'],
            impactType: 'size_dependent'
          },
          customFactors: []
        }
      },
      {
        id: 'crypto-winter',
        name: 'Crypto Winter',
        description: 'Extended bear market in cryptocurrency assets',
        category: 'market_crash',
        severity: 'severe',
        duration: 365,
        probability: 0.15,
        historicalExamples: ['2018 Crypto Winter', '2022 Bear Market'],
        parameters: {
          marketShock: {
            enabled: true,
            magnitude: -0.8,
            affectedAssets: ['BTC/USDT', 'ETH/USDT', 'ADA/USDT'],
            shockType: 'gradual',
            recoveryTime: 730,
            recoveryShape: 'v_shaped'
          },
          volatilityChange: {
            enabled: true,
            multiplier: 2.5,
            duration: 180,
            affectedAssets: ['BTC/USDT', 'ETH/USDT', 'ADA/USDT'],
            volatilityType: 'regime_change'
          },
          correlationChange: {
            enabled: true,
            newCorrelation: 0.95,
            affectedPairs: [['BTC/USDT', 'ETH/USDT'], ['BTC/USDT', 'ADA/USDT']],
            correlationType: 'increase'
          },
          liquidityImpact: {
            enabled: true,
            liquidityReduction: 0.5,
            bidAskSpreadIncrease: 3.0,
            affectedAssets: ['ADA/USDT', 'SOL/USDT'],
            impactType: 'asset_specific'
          },
          customFactors: []
        }
      },
      {
        id: 'volatility-spike',
        name: 'Volatility Spike',
        description: 'Sudden increase in market volatility without major price decline',
        category: 'volatility_spike',
        severity: 'moderate',
        duration: 30,
        probability: 0.3,
        historicalExamples: ['VIX Spike 2018', 'Flash Crash 2010'],
        parameters: {
          marketShock: {
            enabled: false,
            magnitude: 0,
            affectedAssets: [],
            shockType: 'instant',
            recoveryTime: 0,
            recoveryShape: 'linear'
          },
          volatilityChange: {
            enabled: true,
            multiplier: 4.0,
            duration: 14,
            affectedAssets: ['*'],
            volatilityType: 'clustered'
          },
          correlationChange: {
            enabled: true,
            newCorrelation: 0.7,
            affectedPairs: [['*', '*']],
            correlationType: 'increase'
          },
          liquidityImpact: {
            enabled: true,
            liquidityReduction: 0.3,
            bidAskSpreadIncrease: 2.0,
            affectedAssets: ['*'],
            impactType: 'uniform'
          },
          customFactors: []
        }
      },
      {
        id: 'correlation-breakdown',
        name: 'Correlation Breakdown',
        description: 'Sudden breakdown of historical correlations between assets',
        category: 'correlation_breakdown',
        severity: 'moderate',
        duration: 60,
        probability: 0.2,
        historicalExamples: ['COVID-19 Initial Shock', 'Brexit Vote'],
        parameters: {
          marketShock: {
            enabled: true,
            magnitude: -0.15,
            affectedAssets: ['*'],
            shockType: 'instant',
            recoveryTime: 30,
            recoveryShape: 'v_shaped'
          },
          volatilityChange: {
            enabled: true,
            multiplier: 2.0,
            duration: 30,
            affectedAssets: ['*'],
            volatilityType: 'uniform'
          },
          correlationChange: {
            enabled: true,
            newCorrelation: 0.1,
            affectedPairs: [['*', '*']],
            correlationType: 'breakdown'
          },
          liquidityImpact: {
            enabled: false,
            liquidityReduction: 0,
            bidAskSpreadIncrease: 1.0,
            affectedAssets: [],
            impactType: 'uniform'
          },
          customFactors: []
        }
      }
    ]
  }

  async runStressTest(
    scenario: StressTestScenario,
    bots: Bot[],
    positions: Position[],
    markets: Market[],
    configuration: Partial<StressTestConfiguration> = {}
  ): Promise<StressTestResult> {
    const testId = `${scenario.id}-${Date.now()}`
    
    // Check if test is already running
    if (this.runningTests.has(testId)) {
      return this.runningTests.get(testId)!
    }

    const testPromise = this.executeStressTest(scenario, bots, positions, markets, configuration)
    this.runningTests.set(testId, testPromise)

    try {
      const result = await testPromise
      return result
    } finally {
      this.runningTests.delete(testId)
    }
  }

  private async executeStressTest(
    scenario: StressTestScenario,
    bots: Bot[],
    positions: Position[],
    markets: Market[],
    configuration: Partial<StressTestConfiguration>
  ): Promise<StressTestResult> {
    const startTime = Date.now()
    
    // Initialize portfolio
    const initialPortfolioValue = this.calculatePortfolioValue(positions, markets)
    
    // Run simulation
    const timeSeriesData = await this.runSimulation(scenario, bots, positions, markets, configuration)
    
    // Calculate metrics
    const metrics = this.calculateStressMetrics(timeSeriesData, initialPortfolioValue)
    const portfolioImpact = this.calculatePortfolioImpact(positions, markets, timeSeriesData)
    const riskMetrics = this.calculateStressRiskMetrics(timeSeriesData, positions)
    const recommendations = this.generateRecommendations(scenario, metrics, portfolioImpact, riskMetrics)
    
    const executionTime = Date.now() - startTime

    return {
      scenarioId: scenario.id,
      scenarioName: scenario.name,
      executionTime: new Date(),
      duration: executionTime,
      results: metrics,
      portfolioImpact,
      riskMetrics,
      recommendations,
      timeSeriesData
    }
  }

  private async runSimulation(
    scenario: StressTestScenario,
    bots: Bot[],
    positions: Position[],
    markets: Market[],
    configuration: Partial<StressTestConfiguration>
  ): Promise<StressTimeSeriesPoint[]> {
    const timeSeriesData: StressTimeSeriesPoint[] = []
    const timeStep = configuration.simulationSettings?.timeStep || 24 // hours
    const totalHours = scenario.duration * 24
    const steps = Math.floor(totalHours / timeStep)

    // Initialize stressed markets
    const stressedMarkets = this.applyStressToMarkets(markets, scenario.parameters)
    
    for (let step = 0; step <= steps; step++) {
      const timestamp = new Date(Date.now() + step * timeStep * 60 * 60 * 1000)
      const progress = step / steps
      
      // Apply time-dependent stress factors
      const currentMarkets = this.applyTimeVaryingStress(stressedMarkets, scenario.parameters, progress)
      
      // Calculate portfolio metrics at this point
      const portfolioValue = this.calculatePortfolioValue(positions, currentMarkets)
      const drawdown = this.calculateDrawdown(timeSeriesData, portfolioValue)
      const volatility = this.calculateRollingVolatility(timeSeriesData, 24) // 24-hour window
      const var95 = this.calculateVaR(timeSeriesData, 0.95)
      const liquidityScore = this.calculateLiquidityScore(currentMarkets, scenario.parameters.liquidityImpact)
      const correlationLevel = this.calculateCorrelationLevel(currentMarkets, scenario.parameters.correlationChange)
      
      timeSeriesData.push({
        timestamp,
        portfolioValue,
        drawdown,
        volatility,
        var95,
        liquidityScore,
        correlationLevel
      })
    }

    return timeSeriesData
  }

  private applyStressToMarkets(markets: Market[], parameters: ScenarioParameters): Market[] {
    return markets.map(market => {
      let stressedMarket = { ...market }
      
      // Apply market shock
      if (parameters.marketShock.enabled) {
        if (this.isAssetAffected(market.symbol, parameters.marketShock.affectedAssets)) {
          stressedMarket.price *= (1 + parameters.marketShock.magnitude)
          stressedMarket.change24h = parameters.marketShock.magnitude * 100
        }
      }
      
      // Apply volatility changes
      if (parameters.volatilityChange.enabled) {
        if (this.isAssetAffected(market.symbol, parameters.volatilityChange.affectedAssets)) {
          const volatilityIncrease = (parameters.volatilityChange.multiplier - 1) * 0.1
          stressedMarket.high24h = market.price * (1 + volatilityIncrease)
          stressedMarket.low24h = market.price * (1 - volatilityIncrease)
        }
      }
      
      // Apply liquidity impact
      if (parameters.liquidityImpact.enabled) {
        if (this.isAssetAffected(market.symbol, parameters.liquidityImpact.affectedAssets)) {
          stressedMarket.volume24h *= (1 - parameters.liquidityImpact.liquidityReduction)
        }
      }
      
      return stressedMarket
    })
  }

  private applyTimeVaryingStress(
    markets: Market[],
    parameters: ScenarioParameters,
    progress: number
  ): Market[] {
    // Apply time-dependent stress factors based on progress through scenario
    return markets.map(market => {
      let adjustedMarket = { ...market }
      
      // Recovery curve for market shock
      if (parameters.marketShock.enabled && parameters.marketShock.recoveryTime > 0) {
        const recoveryFactor = this.calculateRecoveryFactor(progress, parameters.marketShock.recoveryShape)
        const currentShock = parameters.marketShock.magnitude * (1 - recoveryFactor)
        adjustedMarket.price = market.price * (1 + currentShock)
      }
      
      return adjustedMarket
    })
  }

  private calculateRecoveryFactor(progress: number, recoveryShape: string): number {
    switch (recoveryShape) {
      case 'linear':
        return progress
      case 'exponential':
        return 1 - Math.exp(-3 * progress)
      case 'v_shaped':
        return progress < 0.5 ? 0 : 2 * (progress - 0.5)
      case 'l_shaped':
        return progress < 0.8 ? 0 : 5 * (progress - 0.8)
      default:
        return progress
    }
  }

  private isAssetAffected(asset: string, affectedAssets: string[]): boolean {
    return affectedAssets.includes('*') || affectedAssets.includes(asset)
  }

  private calculatePortfolioValue(positions: Position[], markets: Market[]): number {
    return positions.reduce((total, position) => {
      const market = markets.find(m => m.symbol === position.symbol)
      if (!market) return total
      
      const positionValue = position.quantity * market.price
      return total + positionValue
    }, 0)
  }

  private calculateDrawdown(timeSeriesData: StressTimeSeriesPoint[], currentValue: number): number {
    if (timeSeriesData.length === 0) return 0
    
    const peak = Math.max(...timeSeriesData.map(point => point.portfolioValue), currentValue)
    return (peak - currentValue) / peak
  }

  private calculateRollingVolatility(timeSeriesData: StressTimeSeriesPoint[], windowHours: number): number {
    if (timeSeriesData.length < 2) return 0
    
    const returns = timeSeriesData.slice(-windowHours).map((point, index, arr) => {
      if (index === 0) return 0
      return (point.portfolioValue - arr[index - 1].portfolioValue) / arr[index - 1].portfolioValue
    }).filter(r => r !== 0)
    
    if (returns.length < 2) return 0
    
    const mean = returns.reduce((sum, r) => sum + r, 0) / returns.length
    const variance = returns.reduce((sum, r) => sum + Math.pow(r - mean, 2), 0) / (returns.length - 1)
    
    return Math.sqrt(variance * 24 * 365) // Annualized volatility
  }

  private calculateVaR(timeSeriesData: StressTimeSeriesPoint[], confidence: number): number {
    if (timeSeriesData.length < 2) return 0
    
    const returns = timeSeriesData.slice(1).map((point, index) => {
      const prevValue = timeSeriesData[index].portfolioValue
      return (point.portfolioValue - prevValue) / prevValue
    })
    
    returns.sort((a, b) => a - b)
    const index = Math.floor((1 - confidence) * returns.length)
    
    return returns[index] || 0
  }

  private calculateLiquidityScore(markets: Market[], liquidityParams: LiquidityParams): number {
    if (!liquidityParams.enabled) return 1.0
    
    const avgVolume = markets.reduce((sum, market) => sum + market.volume24h, 0) / markets.length
    const normalizedVolume = avgVolume / 1000000 // Normalize to millions
    
    return Math.max(0, Math.min(1, normalizedVolume * (1 - liquidityParams.liquidityReduction)))
  }

  private calculateCorrelationLevel(markets: Market[], correlationParams: CorrelationParams): number {
    if (!correlationParams.enabled) return 0.5 // Neutral correlation
    
    // Simplified correlation calculation
    return correlationParams.newCorrelation
  }

  private calculateStressMetrics(
    timeSeriesData: StressTimeSeriesPoint[],
    initialValue: number
  ): StressTestMetrics {
    if (timeSeriesData.length === 0) {
      return {
        totalReturn: 0,
        maxDrawdown: 0,
        volatility: 0,
        sharpeRatio: 0,
        var95: 0,
        var99: 0,
        expectedShortfall: 0,
        recoveryTime: 0,
        survivabilityScore: 0
      }
    }

    const finalValue = timeSeriesData[timeSeriesData.length - 1].portfolioValue
    const totalReturn = (finalValue - initialValue) / initialValue
    const maxDrawdown = Math.max(...timeSeriesData.map(point => point.drawdown))
    const avgVolatility = timeSeriesData.reduce((sum, point) => sum + point.volatility, 0) / timeSeriesData.length
    
    // Calculate Sharpe ratio (simplified)
    const avgReturn = totalReturn / (timeSeriesData.length / (24 * 365)) // Annualized
    const sharpeRatio = avgVolatility > 0 ? avgReturn / avgVolatility : 0
    
    // VaR calculations
    const var95 = this.calculateVaR(timeSeriesData, 0.95)
    const var99 = this.calculateVaR(timeSeriesData, 0.99)
    
    // Expected Shortfall (CVaR)
    const returns = timeSeriesData.slice(1).map((point, index) => {
      const prevValue = timeSeriesData[index].portfolioValue
      return (point.portfolioValue - prevValue) / prevValue
    })
    returns.sort((a, b) => a - b)
    const var95Index = Math.floor(0.05 * returns.length)
    const expectedShortfall = returns.slice(0, var95Index).reduce((sum, r) => sum + r, 0) / var95Index || 0
    
    // Recovery time (days to recover from max drawdown)
    const maxDrawdownIndex = timeSeriesData.findIndex(point => point.drawdown === maxDrawdown)
    let recoveryTime = 0
    for (let i = maxDrawdownIndex + 1; i < timeSeriesData.length; i++) {
      if (timeSeriesData[i].drawdown < 0.01) { // Recovered to within 1%
        recoveryTime = i - maxDrawdownIndex
        break
      }
    }
    
    // Survivability score (0-1, based on various factors)
    const survivabilityScore = Math.max(0, Math.min(1, 
      (1 - maxDrawdown) * 0.4 + 
      (totalReturn > -0.5 ? 0.3 : 0) + 
      (recoveryTime < timeSeriesData.length * 0.5 ? 0.3 : 0)
    ))

    return {
      totalReturn,
      maxDrawdown,
      volatility: avgVolatility,
      sharpeRatio,
      var95,
      var99,
      expectedShortfall,
      recoveryTime,
      survivabilityScore
    }
  }

  private calculatePortfolioImpact(
    positions: Position[],
    markets: Market[],
    timeSeriesData: StressTimeSeriesPoint[]
  ): PortfolioImpact {
    const initialValue = timeSeriesData[0]?.portfolioValue || 0
    const finalValue = timeSeriesData[timeSeriesData.length - 1]?.portfolioValue || 0
    const worstValue = Math.min(...timeSeriesData.map(point => point.portfolioValue))
    const peakToTrough = (initialValue - worstValue) / initialValue

    // Calculate asset impacts (simplified)
    const assetImpacts: AssetImpact[] = positions.map(position => {
      const market = markets.find(m => m.symbol === position.symbol)
      if (!market) {
        return {
          asset: position.symbol,
          initialWeight: 0,
          finalWeight: 0,
          pnl: 0,
          pnlPercentage: 0,
          maxDrawdown: 0,
          contribution: 0
        }
      }

      const initialPositionValue = position.quantity * position.entryPrice
      const finalPositionValue = position.quantity * market.price
      const pnl = finalPositionValue - initialPositionValue
      const pnlPercentage = pnl / initialPositionValue

      return {
        asset: position.symbol,
        initialWeight: initialPositionValue / initialValue,
        finalWeight: finalPositionValue / finalValue,
        pnl,
        pnlPercentage,
        maxDrawdown: Math.max(0, (position.entryPrice - market.price) / position.entryPrice),
        contribution: pnl / initialValue
      }
    })

    // Strategy impacts would be calculated similarly
    const strategyImpacts: StrategyImpact[] = []

    return {
      initialValue,
      finalValue,
      worstValue,
      peakToTrough,
      assetImpacts,
      strategyImpacts
    }
  }

  private calculateStressRiskMetrics(
    timeSeriesData: StressTimeSeriesPoint[],
    positions: Position[]
  ): StressRiskMetrics {
    // Simplified risk metric calculations
    const avgCorrelation = timeSeriesData.reduce((sum, point) => sum + point.correlationLevel, 0) / timeSeriesData.length
    const avgLiquidity = timeSeriesData.reduce((sum, point) => sum + point.liquidityScore, 0) / timeSeriesData.length
    
    return {
      concentrationRisk: this.calculateConcentrationRisk(positions),
      correlationRisk: avgCorrelation,
      liquidityRisk: 1 - avgLiquidity,
      leverageRisk: 0.3, // Simplified
      tailRisk: Math.abs(timeSeriesData[timeSeriesData.length - 1]?.var95 || 0),
      systemicRisk: 0.4 // Simplified
    }
  }

  private calculateConcentrationRisk(positions: Position[]): number {
    const totalValue = positions.reduce((sum, pos) => sum + Math.abs(pos.unrealizedPnl), 0)
    if (totalValue === 0) return 0
    
    const weights = positions.map(pos => Math.abs(pos.unrealizedPnl) / totalValue)
    const herfindahlIndex = weights.reduce((sum, weight) => sum + weight * weight, 0)
    
    return herfindahlIndex
  }

  private generateRecommendations(
    scenario: StressTestScenario,
    metrics: StressTestMetrics,
    portfolioImpact: PortfolioImpact,
    riskMetrics: StressRiskMetrics
  ): StressTestRecommendation[] {
    const recommendations: StressTestRecommendation[] = []

    // High drawdown recommendation
    if (metrics.maxDrawdown > 0.2) {
      recommendations.push({
        type: 'position_sizing',
        priority: 'high',
        title: 'Reduce Position Sizes',
        description: `Maximum drawdown of ${(metrics.maxDrawdown * 100).toFixed(1)}% exceeds acceptable levels`,
        expectedBenefit: 0.3,
        implementationCost: 0.1,
        timeframe: 'immediate',
        actions: [
          'Reduce individual position sizes by 20-30%',
          'Implement dynamic position sizing based on volatility',
          'Set maximum position limits per asset'
        ]
      })
    }

    // High correlation risk
    if (riskMetrics.correlationRisk > 0.8) {
      recommendations.push({
        type: 'diversification',
        priority: 'high',
        title: 'Improve Diversification',
        description: 'High correlation during stress periods reduces diversification benefits',
        expectedBenefit: 0.25,
        implementationCost: 0.15,
        timeframe: '1-2 weeks',
        actions: [
          'Add uncorrelated asset classes',
          'Implement sector rotation strategies',
          'Consider alternative investments'
        ]
      })
    }

    // Liquidity risk
    if (riskMetrics.liquidityRisk > 0.5) {
      recommendations.push({
        type: 'liquidity',
        priority: 'medium',
        title: 'Improve Liquidity Management',
        description: 'Portfolio may face liquidity constraints during stress periods',
        expectedBenefit: 0.2,
        implementationCost: 0.05,
        timeframe: '1 week',
        actions: [
          'Maintain higher cash reserves',
          'Focus on more liquid assets',
          'Implement liquidity scoring system'
        ]
      })
    }

    // Hedging recommendation
    if (metrics.survivabilityScore < 0.6) {
      recommendations.push({
        type: 'hedging',
        priority: 'high',
        title: 'Implement Hedging Strategies',
        description: 'Low survivability score indicates need for downside protection',
        expectedBenefit: 0.4,
        implementationCost: 0.2,
        timeframe: '2-3 weeks',
        actions: [
          'Add protective put options',
          'Implement pairs trading strategies',
          'Consider volatility hedging'
        ]
      })
    }

    return recommendations
  }

  getPredefinedScenarios(): StressTestScenario[] {
    return [...this.predefinedScenarios]
  }

  createCustomScenario(
    name: string,
    description: string,
    parameters: ScenarioParameters
  ): StressTestScenario {
    return {
      id: `custom-${Date.now()}`,
      name,
      description,
      category: 'custom',
      severity: 'moderate',
      duration: 30,
      probability: 0.1,
      historicalExamples: [],
      parameters
    }
  }

  async cancelStressTest(testId: string): Promise<boolean> {
    if (this.runningTests.has(testId)) {
      // In a real implementation, you would cancel the running simulation
      this.runningTests.delete(testId)
      return true
    }
    return false
  }

  getRunningTests(): string[] {
    return Array.from(this.runningTests.keys())
  }
}

export const stressTestingService = StressTestingService.getInstance()