import type { 
  InsightCard, 
  ProactiveAction, 
  ChainOfThoughtStep,
  UIContext
} from '@/types'
import { aiService } from './aiService'
import { ragClient } from './ragClient'
import { mcpClient } from './mcpClient'

// Insight card type definitions
export interface InsightCardTemplate {
  id: string
  type: 'opportunity' | 'risk' | 'performance' | 'market_analysis'
  name: string
  description: string
  dataRequirements: string[]
  visualizationType: 'chart' | 'metric' | 'table' | 'gauge' | 'heatmap'
  priority: 'low' | 'medium' | 'high' | 'critical'
  refreshInterval: number // in milliseconds
}

// Data visualization configuration
interface VisualizationConfig {
  type: 'chart' | 'metric' | 'table' | 'gauge' | 'heatmap'
  chartType?: 'line' | 'bar' | 'pie' | 'candlestick' | 'area'
  colors?: string[]
  dimensions?: { width: number; height: number }
  interactive?: boolean
  realtime?: boolean
}

// Insight generation context
interface InsightGenerationContext {
  userContext: UIContext
  marketData: any
  portfolioData: any
  performanceData: any
  riskData: any
  timeframe: string
  symbols: string[]
}

// Insight Card System class
export class InsightCardSystem {
  private templates: Map<string, InsightCardTemplate> = new Map()
  private activeCards: Map<string, InsightCard> = new Map()
  private refreshTimers: Map<string, NodeJS.Timeout> = new Map()
  private generationQueue: Set<string> = new Set()

  constructor() {
    this.initializeTemplates()
  }

  // Initialize insight card templates
  private initializeTemplates(): void {
    // Opportunity Cards
    this.templates.set('arbitrage-opportunity', {
      id: 'arbitrage-opportunity',
      type: 'opportunity',
      name: 'Arbitrage Opportunity',
      description: 'Cross-exchange price differences for profitable arbitrage',
      dataRequirements: ['market_prices', 'exchange_data', 'liquidity_data'],
      visualizationType: 'table',
      priority: 'high',
      refreshInterval: 5000 // 5 seconds
    })

    this.templates.set('momentum-breakout', {
      id: 'momentum-breakout',
      type: 'opportunity',
      name: 'Momentum Breakout',
      description: 'Technical breakout patterns with strong momentum',
      dataRequirements: ['price_data', 'volume_data', 'technical_indicators'],
      visualizationType: 'chart',
      priority: 'medium',
      refreshInterval: 30000 // 30 seconds
    })

    this.templates.set('mean-reversion', {
      id: 'mean-reversion',
      type: 'opportunity',
      name: 'Mean Reversion Signal',
      description: 'Oversold/overbought conditions for mean reversion trades',
      dataRequirements: ['price_data', 'rsi_data', 'bollinger_bands'],
      visualizationType: 'gauge',
      priority: 'medium',
      refreshInterval: 60000 // 1 minute
    })

    // Risk Cards
    this.templates.set('portfolio-correlation', {
      id: 'portfolio-correlation',
      type: 'risk',
      name: 'Portfolio Correlation Risk',
      description: 'High correlation between positions increases portfolio risk',
      dataRequirements: ['portfolio_positions', 'correlation_matrix', 'price_data'],
      visualizationType: 'heatmap',
      priority: 'high',
      refreshInterval: 300000 // 5 minutes
    })

    this.templates.set('drawdown-alert', {
      id: 'drawdown-alert',
      type: 'risk',
      name: 'Drawdown Alert',
      description: 'Portfolio drawdown approaching risk limits',
      dataRequirements: ['portfolio_value', 'peak_value', 'risk_limits'],
      visualizationType: 'gauge',
      priority: 'critical',
      refreshInterval: 10000 // 10 seconds
    })

    this.templates.set('volatility-spike', {
      id: 'volatility-spike',
      type: 'risk',
      name: 'Volatility Spike',
      description: 'Unusual volatility increase in portfolio positions',
      dataRequirements: ['price_data', 'volatility_data', 'position_data'],
      visualizationType: 'chart',
      priority: 'high',
      refreshInterval: 30000 // 30 seconds
    })

    // Performance Cards
    this.templates.set('strategy-performance', {
      id: 'strategy-performance',
      type: 'performance',
      name: 'Strategy Performance',
      description: 'Real-time performance metrics for active strategies',
      dataRequirements: ['strategy_returns', 'benchmark_data', 'risk_metrics'],
      visualizationType: 'metric',
      priority: 'medium',
      refreshInterval: 60000 // 1 minute
    })

    this.templates.set('win-rate-analysis', {
      id: 'win-rate-analysis',
      type: 'performance',
      name: 'Win Rate Analysis',
      description: 'Trade win rate and profit factor analysis',
      dataRequirements: ['trade_history', 'win_loss_data', 'profit_factor'],
      visualizationType: 'chart',
      priority: 'medium',
      refreshInterval: 300000 // 5 minutes
    })

    this.templates.set('sharpe-ratio-trend', {
      id: 'sharpe-ratio-trend',
      type: 'performance',
      name: 'Sharpe Ratio Trend',
      description: 'Risk-adjusted return trend analysis',
      dataRequirements: ['returns_data', 'risk_free_rate', 'volatility_data'],
      visualizationType: 'chart',
      priority: 'medium',
      refreshInterval: 3600000 // 1 hour
    })

    // Market Analysis Cards
    this.templates.set('market-sentiment', {
      id: 'market-sentiment',
      type: 'market_analysis',
      name: 'Market Sentiment',
      description: 'Overall market sentiment and direction indicators',
      dataRequirements: ['sentiment_data', 'fear_greed_index', 'market_breadth'],
      visualizationType: 'gauge',
      priority: 'medium',
      refreshInterval: 300000 // 5 minutes
    })

    this.templates.set('sector-rotation', {
      id: 'sector-rotation',
      type: 'market_analysis',
      name: 'Sector Rotation',
      description: 'Capital flow between different market sectors',
      dataRequirements: ['sector_performance', 'volume_data', 'relative_strength'],
      visualizationType: 'heatmap',
      priority: 'medium',
      refreshInterval: 3600000 // 1 hour
    })

    this.templates.set('liquidity-analysis', {
      id: 'liquidity-analysis',
      type: 'market_analysis',
      name: 'Market Liquidity',
      description: 'Market depth and liquidity conditions',
      dataRequirements: ['order_book_data', 'spread_data', 'volume_profile'],
      visualizationType: 'chart',
      priority: 'medium',
      refreshInterval: 60000 // 1 minute
    })
  }

  // Generate AI-powered insight cards
  async generateInsightCards(
    context: InsightGenerationContext,
    requestedTypes?: string[]
  ): Promise<InsightCard[]> {
    try {
      const cards: InsightCard[] = []
      const templates = requestedTypes 
        ? Array.from(this.templates.values()).filter(t => requestedTypes.includes(t.id))
        : Array.from(this.templates.values())

      // Generate cards in parallel for better performance
      const cardPromises = templates.map(template => 
        this.generateSingleInsightCard(template, context)
      )

      const results = await Promise.allSettled(cardPromises)
      
      results.forEach((result, index) => {
        if (result.status === 'fulfilled' && result.value) {
          cards.push(result.value)
        } else {
          console.warn(`Failed to generate insight card: ${templates[index].id}`, result)
        }
      })

      // Sort cards by priority and confidence
      cards.sort((a, b) => {
        const priorityOrder = { critical: 4, high: 3, medium: 2, low: 1 }
        const aPriority = this.templates.get(a.type)?.priority || 'low'
        const bPriority = this.templates.get(b.type)?.priority || 'low'
        
        if (priorityOrder[aPriority] !== priorityOrder[bPriority]) {
          return priorityOrder[bPriority] - priorityOrder[aPriority]
        }
        
        return b.confidence - a.confidence
      })

      // Store active cards and set up refresh timers
      cards.forEach(card => {
        this.activeCards.set(card.id, card)
        this.setupRefreshTimer(card.id, context)
      })

      return cards
    } catch (error) {
      console.error('Failed to generate insight cards:', error)
      throw error
    }
  }

  // Generate a single insight card
  private async generateSingleInsightCard(
    template: InsightCardTemplate,
    context: InsightGenerationContext
  ): Promise<InsightCard | null> {
    try {
      // Check if already generating this card
      if (this.generationQueue.has(template.id)) {
        return null
      }

      this.generationQueue.add(template.id)

      // Gather required data
      const data = await this.gatherInsightData(template, context)
      if (!data || Object.keys(data).length === 0) {
        console.warn(`No data available for insight card: ${template.id}`)
        return null
      }

      // Generate AI analysis
      const aiAnalysis = await this.generateAIAnalysis(template, data, context)

      // Create visualization
      const visualization = await this.createVisualization(
        template.visualizationType,
        data,
        context
      )

      // Generate proactive actions
      const actions = await this.generateProactiveActions(template, data, aiAnalysis, context)

      // Create the insight card
      const card: InsightCard = {
        id: `${template.id}-${Date.now()}`,
        type: template.type,
        title: template.name,
        content: aiAnalysis.content,
        data: {
          ...data,
          visualization
        },
        actions,
        confidence: aiAnalysis.confidence,
        chainOfThought: aiAnalysis.chainOfThought,
        timestamp: new Date()
      }

      return card
    } catch (error) {
      console.error(`Failed to generate insight card ${template.id}:`, error)
      return null
    } finally {
      this.generationQueue.delete(template.id)
    }
  }

  // Gather data required for insight generation
  private async gatherInsightData(
    template: InsightCardTemplate,
    context: InsightGenerationContext
  ): Promise<any> {
    const data: any = {}

    for (const requirement of template.dataRequirements) {
      try {
        switch (requirement) {
          case 'market_prices':
            data.marketPrices = await this.getMarketPrices(context.symbols)
            break
          case 'exchange_data':
            data.exchangeData = await this.getExchangeData(context.symbols)
            break
          case 'liquidity_data':
            data.liquidityData = await this.getLiquidityData(context.symbols)
            break
          case 'price_data':
            data.priceData = await this.getPriceData(context.symbols, context.timeframe)
            break
          case 'volume_data':
            data.volumeData = await this.getVolumeData(context.symbols, context.timeframe)
            break
          case 'technical_indicators':
            data.technicalIndicators = await this.getTechnicalIndicators(context.symbols)
            break
          case 'portfolio_positions':
            data.portfolioPositions = context.portfolioData?.positions || []
            break
          case 'correlation_matrix':
            data.correlationMatrix = await this.getCorrelationMatrix(context.symbols)
            break
          case 'portfolio_value':
            data.portfolioValue = context.portfolioData?.totalValue || 0
            break
          case 'peak_value':
            data.peakValue = context.portfolioData?.peakValue || 0
            break
          case 'risk_limits':
            data.riskLimits = context.userContext.riskTolerance
            break
          case 'volatility_data':
            data.volatilityData = await this.getVolatilityData(context.symbols)
            break
          case 'strategy_returns':
            data.strategyReturns = context.performanceData?.returns || []
            break
          case 'benchmark_data':
            data.benchmarkData = await this.getBenchmarkData(context.timeframe)
            break
          case 'risk_metrics':
            data.riskMetrics = context.riskData || {}
            break
          case 'trade_history':
            data.tradeHistory = context.performanceData?.trades || []
            break
          case 'sentiment_data':
            data.sentimentData = await this.getSentimentData()
            break
          case 'fear_greed_index':
            data.fearGreedIndex = await this.getFearGreedIndex()
            break
          case 'order_book_data':
            data.orderBookData = await this.getOrderBookData(context.symbols)
            break
        }
      } catch (error) {
        console.warn(`Failed to gather ${requirement}:`, error)
      }
    }

    return data
  }

  // Generate AI analysis for the insight
  private async generateAIAnalysis(
    template: InsightCardTemplate,
    data: any,
    context: InsightGenerationContext
  ): Promise<{ content: string; confidence: number; chainOfThought: ChainOfThoughtStep[] }> {
    const prompt = this.buildAnalysisPrompt(template, data, context)
    
    const aiResponse = await aiService.processQuery(prompt, `insight-${template.id}`)
    
    return {
      content: aiResponse.content,
      confidence: aiResponse.confidence,
      chainOfThought: aiResponse.chainOfThought
    }
  }

  // Build AI analysis prompt
  private buildAnalysisPrompt(
    template: InsightCardTemplate,
    data: any,
    context: InsightGenerationContext
  ): string {
    return `
Analyze the following data to generate insights for a ${template.name} card:

Template: ${template.description}
Type: ${template.type}
User Persona: ${context.userContext.persona?.type || 'balanced'}
Risk Tolerance: ${context.userContext.riskTolerance?.level || 'moderate'}
Timeframe: ${context.timeframe}
Symbols: ${context.symbols.join(', ')}

Data:
${JSON.stringify(data, null, 2)}

Please provide:
1. Key insights and findings
2. Specific actionable recommendations
3. Risk assessment if applicable
4. Confidence level in your analysis
5. Reasoning for your conclusions

Focus on practical, actionable insights that align with the user's risk tolerance and trading style.
`
  }

  // Create visualization for the insight
  private async createVisualization(
    type: string,
    data: any,
    context: InsightGenerationContext
  ): Promise<any> {
    const config: VisualizationConfig = {
      type: type as any,
      interactive: true,
      realtime: true,
      dimensions: { width: 400, height: 300 }
    }

    switch (type) {
      case 'chart':
        return this.createChartVisualization(data, config)
      case 'metric':
        return this.createMetricVisualization(data, config)
      case 'table':
        return this.createTableVisualization(data, config)
      case 'gauge':
        return this.createGaugeVisualization(data, config)
      case 'heatmap':
        return this.createHeatmapVisualization(data, config)
      default:
        return this.createDefaultVisualization(data, config)
    }
  }

  // Create chart visualization
  private createChartVisualization(data: any, config: VisualizationConfig): any {
    return {
      type: 'chart',
      chartType: 'line',
      data: data.priceData || data.performanceData || [],
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: { type: 'time' },
          y: { beginAtZero: false }
        },
        plugins: {
          legend: { display: true },
          tooltip: { enabled: true }
        }
      }
    }
  }

  // Create metric visualization
  private createMetricVisualization(data: any, config: VisualizationConfig): any {
    const metrics = []
    
    if (data.portfolioValue) {
      metrics.push({
        label: 'Portfolio Value',
        value: data.portfolioValue,
        format: 'currency',
        change: data.portfolioChange || 0
      })
    }
    
    if (data.strategyReturns) {
      const totalReturn = data.strategyReturns.reduce((sum: number, r: number) => sum + r, 0)
      metrics.push({
        label: 'Total Return',
        value: totalReturn,
        format: 'percentage',
        change: data.returnChange || 0
      })
    }

    return {
      type: 'metric',
      metrics,
      layout: 'grid'
    }
  }

  // Create table visualization
  private createTableVisualization(data: any, config: VisualizationConfig): any {
    let tableData: any[] = []
    let columns: string[] = []

    if (data.marketPrices) {
      columns = ['Symbol', 'Price', 'Change', 'Volume']
      tableData = Object.entries(data.marketPrices).map(([symbol, price]: [string, any]) => ({
        Symbol: symbol,
        Price: price.current || 0,
        Change: price.change || 0,
        Volume: price.volume || 0
      }))
    } else if (data.portfolioPositions) {
      columns = ['Symbol', 'Size', 'Value', 'P&L']
      tableData = data.portfolioPositions.map((position: any) => ({
        Symbol: position.symbol,
        Size: position.size,
        Value: position.value,
        'P&L': position.pnl
      }))
    }

    return {
      type: 'table',
      columns,
      data: tableData,
      sortable: true,
      filterable: true
    }
  }

  // Create gauge visualization
  private createGaugeVisualization(data: any, config: VisualizationConfig): any {
    let value = 0
    let maxValue = 100
    let label = 'Value'

    if (data.riskMetrics && data.riskMetrics.riskScore) {
      value = data.riskMetrics.riskScore * 100
      maxValue = 100
      label = 'Risk Score'
    } else if (data.sentimentData) {
      value = (data.sentimentData.score + 1) * 50 // Convert -1 to 1 range to 0-100
      maxValue = 100
      label = 'Market Sentiment'
    } else if (data.fearGreedIndex) {
      value = data.fearGreedIndex.value
      maxValue = 100
      label = 'Fear & Greed Index'
    }

    return {
      type: 'gauge',
      value,
      maxValue,
      label,
      thresholds: [
        { value: 30, color: 'green', label: 'Low' },
        { value: 70, color: 'yellow', label: 'Medium' },
        { value: 100, color: 'red', label: 'High' }
      ]
    }
  }

  // Create heatmap visualization
  private createHeatmapVisualization(data: any, config: VisualizationConfig): any {
    let heatmapData: any[] = []
    let labels: string[] = []

    if (data.correlationMatrix) {
      labels = Object.keys(data.correlationMatrix)
      heatmapData = labels.map(symbol1 => 
        labels.map(symbol2 => data.correlationMatrix[symbol1][symbol2] || 0)
      )
    } else if (data.sectorPerformance) {
      labels = Object.keys(data.sectorPerformance)
      heatmapData = [labels.map(sector => data.sectorPerformance[sector] || 0)]
    }

    return {
      type: 'heatmap',
      data: heatmapData,
      labels,
      colorScale: ['#ff0000', '#ffff00', '#00ff00'], // Red to Yellow to Green
      showValues: true
    }
  }

  // Create default visualization
  private createDefaultVisualization(data: any, config: VisualizationConfig): any {
    return {
      type: 'default',
      data: JSON.stringify(data, null, 2),
      message: 'Data visualization not available for this insight type'
    }
  }

  // Generate proactive actions for the insight
  private async generateProactiveActions(
    template: InsightCardTemplate,
    data: any,
    aiAnalysis: any,
    context: InsightGenerationContext
  ): Promise<ProactiveAction[]> {
    const actions: ProactiveAction[] = []

    // Generate actions based on insight type
    switch (template.type) {
      case 'opportunity':
        actions.push(...this.generateOpportunityActions(template, data, context))
        break
      case 'risk':
        actions.push(...this.generateRiskActions(template, data, context))
        break
      case 'performance':
        actions.push(...this.generatePerformanceActions(template, data, context))
        break
      case 'market_analysis':
        actions.push(...this.generateMarketActions(template, data, context))
        break
    }

    // Add generic actions
    actions.push({
      id: `${template.id}-refresh`,
      type: 'suggestion',
      title: 'Refresh Data',
      description: 'Update this insight with the latest data',
      action: async () => {
        await this.refreshInsightCard(template.id, context)
      },
      priority: 'low',
      chainOfThought: [],
      timestamp: new Date()
    })

    return actions
  }

  // Generate opportunity-specific actions
  private generateOpportunityActions(
    template: InsightCardTemplate,
    data: any,
    context: InsightGenerationContext
  ): ProactiveAction[] {
    const actions: ProactiveAction[] = []

    if (template.id === 'arbitrage-opportunity' && data.marketPrices) {
      actions.push({
        id: `${template.id}-execute-arbitrage`,
        type: 'suggestion',
        title: 'Execute Arbitrage',
        description: 'Set up arbitrage trade for identified opportunity',
        action: async () => {
          console.log('Executing arbitrage trade...')
          // Integration with trading system would go here
        },
        priority: 'high',
        chainOfThought: [],
        timestamp: new Date()
      })
    }

    if (template.id === 'momentum-breakout' && data.priceData) {
      actions.push({
        id: `${template.id}-create-strategy`,
        type: 'suggestion',
        title: 'Create Momentum Strategy',
        description: 'Generate a momentum-based trading strategy',
        action: async () => {
          console.log('Creating momentum strategy...')
          // Integration with strategy builder would go here
        },
        priority: 'medium',
        chainOfThought: [],
        timestamp: new Date()
      })
    }

    return actions
  }

  // Generate risk-specific actions
  private generateRiskActions(
    template: InsightCardTemplate,
    data: any,
    context: InsightGenerationContext
  ): ProactiveAction[] {
    const actions: ProactiveAction[] = []

    if (template.id === 'drawdown-alert') {
      actions.push({
        id: `${template.id}-reduce-exposure`,
        type: 'alert',
        title: 'Reduce Exposure',
        description: 'Consider reducing position sizes to limit further drawdown',
        action: async () => {
          console.log('Reducing portfolio exposure...')
          // Integration with position management would go here
        },
        priority: 'critical',
        chainOfThought: [],
        timestamp: new Date()
      })
    }

    if (template.id === 'portfolio-correlation') {
      actions.push({
        id: `${template.id}-diversify`,
        type: 'suggestion',
        title: 'Diversify Portfolio',
        description: 'Add uncorrelated assets to reduce portfolio risk',
        action: async () => {
          console.log('Suggesting diversification options...')
          // Integration with portfolio optimizer would go here
        },
        priority: 'medium',
        chainOfThought: [],
        timestamp: new Date()
      })
    }

    return actions
  }

  // Generate performance-specific actions
  private generatePerformanceActions(
    template: InsightCardTemplate,
    data: any,
    context: InsightGenerationContext
  ): ProactiveAction[] {
    const actions: ProactiveAction[] = []

    actions.push({
      id: `${template.id}-optimize`,
      type: 'optimization',
      title: 'Optimize Strategy',
      description: 'Run optimization to improve strategy performance',
      action: async () => {
        console.log('Starting strategy optimization...')
        // Integration with optimization engine would go here
      },
      priority: 'medium',
      chainOfThought: [],
      timestamp: new Date()
    })

    return actions
  }

  // Generate market analysis actions
  private generateMarketActions(
    template: InsightCardTemplate,
    data: any,
    context: InsightGenerationContext
  ): ProactiveAction[] {
    const actions: ProactiveAction[] = []

    actions.push({
      id: `${template.id}-adjust-strategy`,
      type: 'suggestion',
      title: 'Adjust Strategy',
      description: 'Modify strategy parameters based on market conditions',
      action: async () => {
        console.log('Adjusting strategy for market conditions...')
        // Integration with strategy adjustment would go here
      },
      priority: 'medium',
      chainOfThought: [],
      timestamp: new Date()
    })

    return actions
  }

  // Set up refresh timer for insight card
  private setupRefreshTimer(cardId: string, context: InsightGenerationContext): void {
    const card = this.activeCards.get(cardId)
    if (!card) return

    const template = Array.from(this.templates.values()).find(t => card.type === t.type)
    if (!template) return

    // Clear existing timer
    const existingTimer = this.refreshTimers.get(cardId)
    if (existingTimer) {
      clearTimeout(existingTimer)
    }

    // Set new timer
    const timer = setTimeout(async () => {
      await this.refreshInsightCard(template.id, context)
    }, template.refreshInterval)

    this.refreshTimers.set(cardId, timer)
  }

  // Refresh a specific insight card
  async refreshInsightCard(templateId: string, context: InsightGenerationContext): Promise<void> {
    const template = this.templates.get(templateId)
    if (!template) return

    try {
      const newCard = await this.generateSingleInsightCard(template, context)
      if (newCard) {
        // Remove old card
        const oldCards = Array.from(this.activeCards.values()).filter(c => c.type === template.type)
        oldCards.forEach(card => {
          this.activeCards.delete(card.id)
          const timer = this.refreshTimers.get(card.id)
          if (timer) {
            clearTimeout(timer)
            this.refreshTimers.delete(card.id)
          }
        })

        // Add new card
        this.activeCards.set(newCard.id, newCard)
        this.setupRefreshTimer(newCard.id, context)
      }
    } catch (error) {
      console.error(`Failed to refresh insight card ${templateId}:`, error)
    }
  }

  // Data gathering helper methods (these would integrate with actual data sources)
  private async getMarketPrices(symbols: string[]): Promise<any> {
    try {
      const prices: any = {}
      for (const symbol of symbols) {
        // This would integrate with MCP client or other data source
        prices[symbol] = {
          current: Math.random() * 50000 + 10000, // Mock data
          change: (Math.random() - 0.5) * 0.1,
          volume: Math.random() * 1000000
        }
      }
      return prices
    } catch (error) {
      console.error('Failed to get market prices:', error)
      return {}
    }
  }

  private async getExchangeData(symbols: string[]): Promise<any> {
    // Mock implementation - would integrate with actual exchange APIs
    return symbols.map(symbol => ({
      symbol,
      exchange: 'Binance',
      price: Math.random() * 50000,
      volume: Math.random() * 1000000
    }))
  }

  private async getLiquidityData(symbols: string[]): Promise<any> {
    // Mock implementation
    return symbols.map(symbol => ({
      symbol,
      bidAskSpread: Math.random() * 0.01,
      marketDepth: Math.random() * 1000000
    }))
  }

  private async getPriceData(symbols: string[], timeframe: string): Promise<any> {
    // Mock implementation - would integrate with historical data API
    const data: any = {}
    symbols.forEach(symbol => {
      data[symbol] = Array.from({ length: 100 }, (_, i) => ({
        timestamp: Date.now() - (100 - i) * 60000,
        open: Math.random() * 50000,
        high: Math.random() * 50000,
        low: Math.random() * 50000,
        close: Math.random() * 50000,
        volume: Math.random() * 1000000
      }))
    })
    return data
  }

  private async getVolumeData(symbols: string[], timeframe: string): Promise<any> {
    // Mock implementation
    const data: any = {}
    symbols.forEach(symbol => {
      data[symbol] = Array.from({ length: 100 }, (_, i) => ({
        timestamp: Date.now() - (100 - i) * 60000,
        volume: Math.random() * 1000000
      }))
    })
    return data
  }

  private async getTechnicalIndicators(symbols: string[]): Promise<any> {
    // Mock implementation
    const indicators: any = {}
    symbols.forEach(symbol => {
      indicators[symbol] = {
        rsi: Math.random() * 100,
        macd: {
          macd: Math.random() * 100 - 50,
          signal: Math.random() * 100 - 50,
          histogram: Math.random() * 100 - 50
        },
        bollinger: {
          upper: Math.random() * 60000,
          middle: Math.random() * 50000,
          lower: Math.random() * 40000
        }
      }
    })
    return indicators
  }

  private async getCorrelationMatrix(symbols: string[]): Promise<any> {
    // Mock implementation
    const matrix: any = {}
    symbols.forEach(symbol1 => {
      matrix[symbol1] = {}
      symbols.forEach(symbol2 => {
        matrix[symbol1][symbol2] = symbol1 === symbol2 ? 1 : Math.random() * 2 - 1
      })
    })
    return matrix
  }

  private async getVolatilityData(symbols: string[]): Promise<any> {
    // Mock implementation
    const volatility: any = {}
    symbols.forEach(symbol => {
      volatility[symbol] = {
        current: Math.random() * 0.5,
        average: Math.random() * 0.3,
        percentile: Math.random() * 100
      }
    })
    return volatility
  }

  private async getBenchmarkData(timeframe: string): Promise<any> {
    // Mock implementation
    return {
      symbol: 'SPY',
      returns: Array.from({ length: 100 }, () => Math.random() * 0.02 - 0.01),
      volatility: 0.15,
      sharpe: 1.2
    }
  }

  private async getSentimentData(): Promise<any> {
    // Mock implementation
    return {
      score: Math.random() * 2 - 1, // -1 to 1
      confidence: Math.random(),
      sources: ['twitter', 'reddit', 'news']
    }
  }

  private async getFearGreedIndex(): Promise<any> {
    // Mock implementation
    return {
      value: Math.random() * 100,
      classification: ['Extreme Fear', 'Fear', 'Neutral', 'Greed', 'Extreme Greed'][Math.floor(Math.random() * 5)]
    }
  }

  private async getOrderBookData(symbols: string[]): Promise<any> {
    // Mock implementation
    const orderBooks: any = {}
    symbols.forEach(symbol => {
      orderBooks[symbol] = {
        bids: Array.from({ length: 10 }, (_, i) => ({
          price: 50000 - i * 10,
          size: Math.random() * 10
        })),
        asks: Array.from({ length: 10 }, (_, i) => ({
          price: 50000 + i * 10,
          size: Math.random() * 10
        }))
      }
    })
    return orderBooks
  }

  // Public methods for managing insight cards
  getActiveCards(): InsightCard[] {
    return Array.from(this.activeCards.values())
  }

  getCardById(cardId: string): InsightCard | undefined {
    return this.activeCards.get(cardId)
  }

  dismissCard(cardId: string): void {
    const card = this.activeCards.get(cardId)
    if (card) {
      card.dismissed = true
      this.activeCards.delete(cardId)
      
      const timer = this.refreshTimers.get(cardId)
      if (timer) {
        clearTimeout(timer)
        this.refreshTimers.delete(cardId)
      }
    }
  }

  clearAllCards(): void {
    this.activeCards.clear()
    this.refreshTimers.forEach(timer => clearTimeout(timer))
    this.refreshTimers.clear()
  }

  getAvailableTemplates(): InsightCardTemplate[] {
    return Array.from(this.templates.values())
  }
}

// Export singleton instance
export const insightCardSystem = new InsightCardSystem()