import { aiService } from './aiService'
import { useAppStore } from '@/stores/appStore'
import { useAIStore } from '@/stores/aiStore'
import { useTradingStore } from '@/stores/tradingStore'
import { useWorkflowStore } from '@/stores/workflowStore'
import type { 
  CommandResult, 
  Suggestion, 
  UIContext,
  ChainOfThoughtStep,
  ProactiveAction 
} from '@/types'

// Command intent classification
export interface CommandIntent {
  type: 'strategy' | 'analysis' | 'navigation' | 'data_query' | 'workflow' | 'risk' | 'bot_management' | 'market_data'
  confidence: number
  entities: CommandEntity[]
  parameters: Record<string, any>
}

export interface CommandEntity {
  type: 'symbol' | 'timeframe' | 'strategy_name' | 'bot_id' | 'account' | 'parameter' | 'value'
  value: string
  confidence: number
  start: number
  end: number
}

// Command history for learning and suggestions
export interface CommandHistory {
  id: string
  command: string
  intent: CommandIntent
  result: CommandResult
  timestamp: Date
  success: boolean
  userFeedback?: 'positive' | 'negative' | 'neutral'
}

// Context-aware command processor
class CommandProcessor {
  private commandHistory: CommandHistory[] = []
  private suggestionCache: Map<string, Suggestion[]> = new Map()
  private intentPatterns: Map<string, RegExp[]> = new Map()

  constructor() {
    this.initializeIntentPatterns()
  }

  // Initialize pattern matching for intent recognition
  private initializeIntentPatterns(): void {
    this.intentPatterns.set('strategy', [
      /create.*strategy/i,
      /build.*strategy/i,
      /new.*strategy/i,
      /strategy.*for/i,
      /develop.*strategy/i,
      /generate.*strategy/i,
    ])

    this.intentPatterns.set('analysis', [
      /analyze/i,
      /analysis/i,
      /show.*performance/i,
      /performance.*of/i,
      /how.*performing/i,
      /market.*analysis/i,
      /sentiment/i,
    ])

    this.intentPatterns.set('navigation', [
      /show.*dashboard/i,
      /go.*to/i,
      /open/i,
      /navigate.*to/i,
      /switch.*to/i,
      /view/i,
    ])

    this.intentPatterns.set('data_query', [
      /what.*is/i,
      /show.*me/i,
      /get.*data/i,
      /fetch/i,
      /retrieve/i,
      /list/i,
    ])

    this.intentPatterns.set('workflow', [
      /optimize/i,
      /backtest/i,
      /run.*workflow/i,
      /execute/i,
      /start.*optimization/i,
      /chain.*of.*thought/i,
    ])

    this.intentPatterns.set('risk', [
      /risk/i,
      /exposure/i,
      /drawdown/i,
      /portfolio.*risk/i,
      /risk.*assessment/i,
      /safety/i,
    ])

    this.intentPatterns.set('bot_management', [
      /bot/i,
      /activate.*bot/i,
      /deactivate.*bot/i,
      /start.*bot/i,
      /stop.*bot/i,
      /bot.*status/i,
    ])

    this.intentPatterns.set('market_data', [
      /market/i,
      /price/i,
      /chart/i,
      /orderbook/i,
      /volume/i,
      /market.*data/i,
    ])
  }

  // Main command processing method
  async processCommand(command: string, context: UIContext): Promise<CommandResult> {
    try {
      const startTime = Date.now()
      
      // Step 1: Parse and classify the command
      const intent = await this.classifyIntent(command, context)
      
      // Step 2: Extract entities and parameters
      const entities = this.extractEntities(command, intent)
      
      // Step 3: Generate chain of thought for the command processing
      const chainOfThought: ChainOfThoughtStep[] = []
      
      chainOfThought.push({
        id: `cmd-${Date.now()}-1`,
        step: 1,
        reasoning: `Classified command "${command}" as ${intent.type} with ${intent.confidence.toFixed(2)} confidence`,
        data: { intent, entities },
        confidence: intent.confidence,
        alternatives: [],
        timestamp: new Date()
      })

      // Step 4: Process based on intent type
      let result: CommandResult
      
      switch (intent.type) {
        case 'strategy':
          result = await this.processStrategyCommand(command, intent, entities, context, chainOfThought)
          break
        case 'analysis':
          result = await this.processAnalysisCommand(command, intent, entities, context, chainOfThought)
          break
        case 'navigation':
          result = await this.processNavigationCommand(command, intent, entities, context, chainOfThought)
          break
        case 'data_query':
          result = await this.processDataQueryCommand(command, intent, entities, context, chainOfThought)
          break
        case 'workflow':
          result = await this.processWorkflowCommand(command, intent, entities, context, chainOfThought)
          break
        case 'risk':
          result = await this.processRiskCommand(command, intent, entities, context, chainOfThought)
          break
        case 'bot_management':
          result = await this.processBotManagementCommand(command, intent, entities, context, chainOfThought)
          break
        case 'market_data':
          result = await this.processMarketDataCommand(command, intent, entities, context, chainOfThought)
          break
        default:
          result = await this.processGenericCommand(command, intent, entities, context, chainOfThought)
      }

      // Step 5: Add processing time to chain of thought
      const processingTime = Date.now() - startTime
      chainOfThought.push({
        id: `cmd-${Date.now()}-final`,
        step: chainOfThought.length + 1,
        reasoning: `Command processed successfully in ${processingTime}ms`,
        data: { processingTime, resultType: result.type },
        confidence: 0.9,
        alternatives: [],
        timestamp: new Date()
      })

      result.chainOfThought = chainOfThought

      // Step 6: Store in command history for learning
      this.addToHistory(command, intent, result)

      return result
    } catch (error) {
      console.error('Command processing failed:', error)
      return {
        type: 'navigation',
        payload: { error: (error as Error).message },
        success: false,
        message: `Failed to process command: ${(error as Error).message}`,
        chainOfThought: [{
          id: `cmd-error-${Date.now()}`,
          step: 1,
          reasoning: `Command processing failed: ${(error as Error).message}`,
          data: { error: (error as Error).message },
          confidence: 0.1,
          alternatives: [],
          timestamp: new Date()
        }]
      }
    }
  }

  // Intent classification using pattern matching and AI
  private async classifyIntent(command: string, context: UIContext): Promise<CommandIntent> {
    const lowerCommand = command.toLowerCase()
    let bestMatch: { type: string; confidence: number } = { type: 'data_query', confidence: 0.3 }

    // Pattern-based classification
    for (const [intentType, patterns] of this.intentPatterns.entries()) {
      for (const pattern of patterns) {
        if (pattern.test(lowerCommand)) {
          const confidence = this.calculatePatternConfidence(command, pattern)
          if (confidence > bestMatch.confidence) {
            bestMatch = { type: intentType, confidence }
          }
        }
      }
    }

    // Context-based confidence adjustment
    bestMatch.confidence = this.adjustConfidenceByContext(bestMatch, context)

    // If confidence is low, use AI for better classification
    if (bestMatch.confidence < 0.7) {
      try {
        const aiClassification = await this.classifyWithAI(command, context)
        if (aiClassification.confidence > bestMatch.confidence) {
          bestMatch = aiClassification
        }
      } catch (error) {
        console.warn('AI classification failed, using pattern-based result:', error)
      }
    }

    return {
      type: bestMatch.type as any,
      confidence: bestMatch.confidence,
      entities: [],
      parameters: {}
    }
  }

  // AI-powered intent classification for complex commands
  private async classifyWithAI(command: string, context: UIContext): Promise<{ type: string; confidence: number }> {
    const prompt = `
Classify the following trading command into one of these categories:
- strategy: Creating, modifying, or discussing trading strategies
- analysis: Analyzing performance, markets, or data
- navigation: Moving between different views or sections
- data_query: Requesting specific data or information
- workflow: Running optimization, backtesting, or automated processes
- risk: Risk assessment, management, or monitoring
- bot_management: Managing trading bots (start, stop, configure)
- market_data: Requesting market prices, charts, or market information

Command: "${command}"
Context: Current view is "${context.currentView}", user has ${context.selectedAssets.length} selected assets

Respond with just the category name and confidence (0-1) in format: "category:confidence"
`

    const response = await aiService.processQuery(prompt, 'command-classification')
    const match = response.content.match(/(\w+):([0-9.]+)/)
    
    if (match) {
      return {
        type: match[1],
        confidence: parseFloat(match[2])
      }
    }

    return { type: 'data_query', confidence: 0.5 }
  }

  // Extract entities from command text
  private extractEntities(command: string, intent: CommandIntent): CommandEntity[] {
    const entities: CommandEntity[] = []
    const lowerCommand = command.toLowerCase()

    // Symbol extraction (BTC, ETH, BTC/USD, etc.)
    const symbolPattern = /\b([A-Z]{2,5}(?:\/[A-Z]{2,5})?)\b/g
    let match
    while ((match = symbolPattern.exec(command)) !== null) {
      entities.push({
        type: 'symbol',
        value: match[1],
        confidence: 0.9,
        start: match.index,
        end: match.index + match[1].length
      })
    }

    // Timeframe extraction (1h, 4h, 1d, etc.)
    const timeframePattern = /\b(\d+[mhd]|daily|hourly|weekly)\b/gi
    while ((match = timeframePattern.exec(command)) !== null) {
      entities.push({
        type: 'timeframe',
        value: match[1].toLowerCase(),
        confidence: 0.8,
        start: match.index,
        end: match.index + match[1].length
      })
    }

    // Strategy name extraction (quoted strings or common strategy names)
    const strategyPattern = /"([^"]+)"|'([^']+)'|\b(RSI|MACD|Bollinger|Moving Average|Scalper|Grid|Arbitrage)\b/gi
    while ((match = strategyPattern.exec(command)) !== null) {
      const strategyName = match[1] || match[2] || match[3]
      entities.push({
        type: 'strategy_name',
        value: strategyName,
        confidence: 0.7,
        start: match.index,
        end: match.index + match[0].length
      })
    }

    // Numeric values
    const numberPattern = /\b(\d+(?:\.\d+)?)\b/g
    while ((match = numberPattern.exec(command)) !== null) {
      entities.push({
        type: 'value',
        value: match[1],
        confidence: 0.6,
        start: match.index,
        end: match.index + match[1].length
      })
    }

    return entities
  }

  // Calculate pattern matching confidence
  private calculatePatternConfidence(command: string, pattern: RegExp): number {
    const match = command.match(pattern)
    if (!match) return 0

    // Base confidence
    let confidence = 0.7

    // Adjust based on match length vs command length
    const matchRatio = match[0].length / command.length
    confidence += matchRatio * 0.2

    // Adjust based on position (earlier matches are more confident)
    const position = match.index || 0
    const positionRatio = 1 - (position / command.length)
    confidence += positionRatio * 0.1

    return Math.min(confidence, 1.0)
  }

  // Adjust confidence based on current context
  private adjustConfidenceByContext(match: { type: string; confidence: number }, context: UIContext): number {
    let adjustedConfidence = match.confidence

    // Boost confidence if command type matches current view
    if (context.currentView === 'dashboard' && match.type === 'analysis') {
      adjustedConfidence += 0.1
    }
    if (context.currentView === 'strategy-studio' && match.type === 'strategy') {
      adjustedConfidence += 0.1
    }
    if (context.currentView === 'risk-management' && match.type === 'risk') {
      adjustedConfidence += 0.1
    }

    // Boost confidence if user has relevant assets selected
    if (context.selectedAssets.length > 0 && (match.type === 'analysis' || match.type === 'market_data')) {
      adjustedConfidence += 0.05
    }

    return Math.min(adjustedConfidence, 1.0)
  }

  // Process strategy-related commands
  private async processStrategyCommand(
    command: string,
    intent: CommandIntent,
    entities: CommandEntity[],
    context: UIContext,
    chainOfThought: ChainOfThoughtStep[]
  ): Promise<CommandResult> {
    chainOfThought.push({
      id: `cmd-strategy-${Date.now()}`,
      step: chainOfThought.length + 1,
      reasoning: 'Processing strategy command - will analyze description and generate strategy',
      data: { entities },
      confidence: 0.8,
      alternatives: [],
      timestamp: new Date()
    })

    // Extract strategy description from command
    const strategyDescription = this.extractStrategyDescription(command, entities)
    
    // Use AI service to analyze the strategy
    const analysis = await aiService.analyzeStrategyDescription(strategyDescription, {
      symbols: entities.filter(e => e.type === 'symbol').map(e => e.value),
      timeframe: entities.find(e => e.type === 'timeframe')?.value || '1h',
      marketConditions: context.marketConditions.map(mc => mc.type)
    })

    const proactiveActions: ProactiveAction[] = [
      {
        id: `strategy-action-${Date.now()}`,
        type: 'suggestion',
        title: 'Generate HaasScript',
        description: 'Generate executable HaasScript code for this strategy',
        action: async () => {
          const script = await aiService.generateHaasScript(strategyDescription)
          console.log('Generated HaasScript:', script)
        },
        priority: 'high',
        chainOfThought: [],
        timestamp: new Date()
      }
    ]

    return {
      type: 'ui_generation',
      payload: {
        componentType: 'strategy_analysis',
        data: analysis,
        description: strategyDescription
      },
      proactiveActions,
      success: true,
      message: `Strategy analysis completed for: ${strategyDescription}`
    }
  }

  // Process analysis-related commands
  private async processAnalysisCommand(
    command: string,
    intent: CommandIntent,
    entities: CommandEntity[],
    context: UIContext,
    chainOfThought: ChainOfThoughtStep[]
  ): Promise<CommandResult> {
    chainOfThought.push({
      id: `cmd-analysis-${Date.now()}`,
      step: chainOfThought.length + 1,
      reasoning: 'Processing analysis command - will generate market or performance analysis',
      data: { entities },
      confidence: 0.8,
      alternatives: [],
      timestamp: new Date()
    })

    const symbols = entities.filter(e => e.type === 'symbol').map(e => e.value)
    const timeframe = entities.find(e => e.type === 'timeframe')?.value || '1d'

    // If no symbols specified, use selected assets from context
    const analysisSymbols = symbols.length > 0 ? symbols : context.selectedAssets

    if (analysisSymbols.length === 0) {
      return {
        type: 'ui_generation',
        payload: {
          componentType: 'error',
          message: 'Please specify symbols to analyze or select assets first'
        },
        success: false,
        message: 'No symbols specified for analysis'
      }
    }

    // Perform market analysis
    const analysis = await aiService.analyzeMarketConditions(analysisSymbols, timeframe)

    return {
      type: 'ui_generation',
      payload: {
        componentType: 'market_analysis',
        data: analysis,
        symbols: analysisSymbols,
        timeframe
      },
      success: true,
      message: `Market analysis completed for ${analysisSymbols.join(', ')}`
    }
  }

  // Process navigation commands
  private async processNavigationCommand(
    command: string,
    intent: CommandIntent,
    entities: CommandEntity[],
    context: UIContext,
    chainOfThought: ChainOfThoughtStep[]
  ): Promise<CommandResult> {
    const lowerCommand = command.toLowerCase()
    let targetView = 'dashboard'

    // Determine target view
    if (lowerCommand.includes('dashboard')) targetView = 'dashboard'
    else if (lowerCommand.includes('strategy') || lowerCommand.includes('studio')) targetView = 'strategy-studio'
    else if (lowerCommand.includes('risk')) targetView = 'risk-management'
    else if (lowerCommand.includes('market')) targetView = 'market-intelligence'
    else if (lowerCommand.includes('analytics')) targetView = 'analytics'
    else if (lowerCommand.includes('bot')) targetView = 'bot-management'

    chainOfThought.push({
      id: `cmd-nav-${Date.now()}`,
      step: chainOfThought.length + 1,
      reasoning: `Navigating to ${targetView} based on command keywords`,
      data: { targetView, currentView: context.currentView },
      confidence: 0.9,
      alternatives: [],
      timestamp: new Date()
    })

    // Update app store with new view
    useAppStore.getState().updateUIContext({ currentView: targetView })

    return {
      type: 'navigation',
      payload: { targetView },
      success: true,
      message: `Navigated to ${targetView}`
    }
  }

  // Process data query commands
  private async processDataQueryCommand(
    command: string,
    intent: CommandIntent,
    entities: CommandEntity[],
    context: UIContext,
    chainOfThought: ChainOfThoughtStep[]
  ): Promise<CommandResult> {
    // Use AI to understand what data is being requested
    const dataQuery = await aiService.processQuery(
      `Extract the specific data request from this command: "${command}". 
       Available data includes: bot status, portfolio performance, market prices, account balances, strategy performance.
       Respond with the data type and any specific parameters.`,
      'data-query'
    )

    chainOfThought.push({
      id: `cmd-data-${Date.now()}`,
      step: chainOfThought.length + 1,
      reasoning: 'Processing data query using AI to understand specific request',
      data: { query: dataQuery.content },
      confidence: 0.7,
      alternatives: [],
      timestamp: new Date()
    })

    return {
      type: 'data_query',
      payload: {
        query: dataQuery.content,
        entities,
        originalCommand: command
      },
      success: true,
      message: 'Data query processed'
    }
  }

  // Process workflow commands
  private async processWorkflowCommand(
    command: string,
    intent: CommandIntent,
    entities: CommandEntity[],
    context: UIContext,
    chainOfThought: ChainOfThoughtStep[]
  ): Promise<CommandResult> {
    const workflowStore = useWorkflowStore.getState()
    
    chainOfThought.push({
      id: `cmd-workflow-${Date.now()}`,
      step: chainOfThought.length + 1,
      reasoning: 'Processing workflow command - will trigger optimization or backtesting workflow',
      data: { entities },
      confidence: 0.8,
      alternatives: [],
      timestamp: new Date()
    })

    // Determine workflow type
    let workflowType = 'chain_of_thought_optimization'
    if (command.toLowerCase().includes('backtest')) workflowType = 'backtest'
    else if (command.toLowerCase().includes('optimize')) workflowType = 'optimization'

    const proactiveActions: ProactiveAction[] = [
      {
        id: `workflow-action-${Date.now()}`,
        type: 'suggestion',
        title: 'Start Workflow',
        description: `Start ${workflowType} workflow with current settings`,
        action: async () => {
          // This would trigger the actual workflow
          console.log(`Starting ${workflowType} workflow`)
        },
        priority: 'high',
        chainOfThought: [],
        timestamp: new Date()
      }
    ]

    return {
      type: 'workflow_trigger',
      payload: {
        workflowType,
        entities,
        command
      },
      proactiveActions,
      success: true,
      message: `${workflowType} workflow prepared`
    }
  }

  // Process risk-related commands
  private async processRiskCommand(
    command: string,
    intent: CommandIntent,
    entities: CommandEntity[],
    context: UIContext,
    chainOfThought: ChainOfThoughtStep[]
  ): Promise<CommandResult> {
    const tradingStore = useTradingStore.getState()
    
    chainOfThought.push({
      id: `cmd-risk-${Date.now()}`,
      step: chainOfThought.length + 1,
      reasoning: 'Processing risk command - will analyze portfolio risk and exposure',
      data: { entities },
      confidence: 0.8,
      alternatives: [],
      timestamp: new Date()
    })

    // Get current portfolio data
    const { accounts, positions } = tradingStore
    const portfolio = { accounts, positions }
    
    // Perform risk assessment using AI
    const riskAssessment = await aiService.assessRisk(portfolio, [])

    return {
      type: 'ui_generation',
      payload: {
        componentType: 'risk_assessment',
        data: riskAssessment,
        portfolio
      },
      success: true,
      message: 'Risk assessment completed'
    }
  }

  // Process bot management commands
  private async processBotManagementCommand(
    command: string,
    intent: CommandIntent,
    entities: CommandEntity[],
    context: UIContext,
    chainOfThought: ChainOfThoughtStep[]
  ): Promise<CommandResult> {
    chainOfThought.push({
      id: `cmd-bot-${Date.now()}`,
      step: chainOfThought.length + 1,
      reasoning: 'Processing bot management command',
      data: { entities },
      confidence: 0.8,
      alternatives: [],
      timestamp: new Date()
    })

    const lowerCommand = command.toLowerCase()
    let action = 'status'
    
    if (lowerCommand.includes('start') || lowerCommand.includes('activate')) action = 'start'
    else if (lowerCommand.includes('stop') || lowerCommand.includes('deactivate')) action = 'stop'
    else if (lowerCommand.includes('status')) action = 'status'

    return {
      type: 'ui_generation',
      payload: {
        componentType: 'bot_management',
        action,
        entities
      },
      success: true,
      message: `Bot ${action} command processed`
    }
  }

  // Process market data commands
  private async processMarketDataCommand(
    command: string,
    intent: CommandIntent,
    entities: CommandEntity[],
    context: UIContext,
    chainOfThought: ChainOfThoughtStep[]
  ): Promise<CommandResult> {
    const symbols = entities.filter(e => e.type === 'symbol').map(e => e.value)
    const timeframe = entities.find(e => e.type === 'timeframe')?.value || '1h'

    chainOfThought.push({
      id: `cmd-market-${Date.now()}`,
      step: chainOfThought.length + 1,
      reasoning: `Processing market data request for ${symbols.join(', ')} on ${timeframe} timeframe`,
      data: { symbols, timeframe },
      confidence: 0.8,
      alternatives: [],
      timestamp: new Date()
    })

    return {
      type: 'ui_generation',
      payload: {
        componentType: 'market_data',
        symbols: symbols.length > 0 ? symbols : context.selectedAssets,
        timeframe
      },
      success: true,
      message: `Market data request processed for ${symbols.join(', ') || 'selected assets'}`
    }
  }

  // Process generic commands using AI
  private async processGenericCommand(
    command: string,
    intent: CommandIntent,
    entities: CommandEntity[],
    context: UIContext,
    chainOfThought: ChainOfThoughtStep[]
  ): Promise<CommandResult> {
    chainOfThought.push({
      id: `cmd-generic-${Date.now()}`,
      step: chainOfThought.length + 1,
      reasoning: 'Processing generic command using AI for interpretation',
      data: { command },
      confidence: 0.6,
      alternatives: [],
      timestamp: new Date()
    })

    // Use AI to process the command
    const aiResponse = await aiService.processQuery(command, 'generic-command')

    return {
      type: 'ui_generation',
      payload: {
        componentType: 'ai_response',
        data: aiResponse
      },
      success: true,
      message: 'Command processed by AI'
    }
  }

  // Extract strategy description from command
  private extractStrategyDescription(command: string, entities: CommandEntity[]): string {
    // Remove command keywords to get the strategy description
    const cleanCommand = command
      .replace(/create|build|new|strategy|for|generate/gi, '')
      .trim()

    return cleanCommand || 'General trading strategy'
  }

  // Generate context-aware suggestions
  async generateSuggestions(query: string, context: UIContext): Promise<Suggestion[]> {
    const cacheKey = `${query}-${context.currentView}-${context.selectedAssets.join(',')}`
    
    // Check cache first
    if (this.suggestionCache.has(cacheKey)) {
      return this.suggestionCache.get(cacheKey)!
    }

    const suggestions: Suggestion[] = []

    // Base suggestions based on current context
    if (context.currentView === 'dashboard') {
      suggestions.push(
        { id: '1', text: 'Show portfolio performance', type: 'query', confidence: 0.9, context: 'dashboard', icon: '📊' },
        { id: '2', text: 'Analyze market sentiment', type: 'query', confidence: 0.8, context: 'dashboard', icon: '📈' },
        { id: '3', text: 'Check risk exposure', type: 'query', confidence: 0.8, context: 'dashboard', icon: '⚠️' }
      )
    }

    // Query-based suggestions
    if (query.length > 0) {
      const queryLower = query.toLowerCase()
      
      // Strategy suggestions
      if (queryLower.includes('strategy') || queryLower.includes('create')) {
        suggestions.push(
          { id: 'str1', text: 'Create momentum strategy for BTC', type: 'command', confidence: 0.9, context: 'strategy', icon: '🚀' },
          { id: 'str2', text: 'Build RSI strategy for ETH', type: 'command', confidence: 0.8, context: 'strategy', icon: '📊' },
          { id: 'str3', text: 'Generate scalping strategy', type: 'command', confidence: 0.7, context: 'strategy', icon: '⚡' }
        )
      }

      // Analysis suggestions
      if (queryLower.includes('analyze') || queryLower.includes('analysis')) {
        suggestions.push(
          { id: 'ana1', text: 'Analyze BTC price action', type: 'query', confidence: 0.9, context: 'analysis', icon: '🔍' },
          { id: 'ana2', text: 'Market correlation analysis', type: 'query', confidence: 0.8, context: 'analysis', icon: '📊' },
          { id: 'ana3', text: 'Performance analysis last 30 days', type: 'query', confidence: 0.7, context: 'analysis', icon: '📈' }
        )
      }

      // Bot suggestions
      if (queryLower.includes('bot')) {
        suggestions.push(
          { id: 'bot1', text: 'Show active bots status', type: 'query', confidence: 0.9, context: 'bots', icon: '🤖' },
          { id: 'bot2', text: 'Start all paused bots', type: 'command', confidence: 0.8, context: 'bots', icon: '▶️' },
          { id: 'bot3', text: 'Create bot from strategy', type: 'command', confidence: 0.7, context: 'bots', icon: '➕' }
        )
      }
    }

    // Historical command suggestions
    const recentCommands = this.commandHistory
      .filter(h => h.success)
      .slice(-5)
      .map((h, i) => ({
        id: `hist-${i}`,
        text: h.command,
        type: 'command' as const,
        confidence: 0.6,
        context: 'history',
        icon: '🕒'
      }))

    suggestions.push(...recentCommands)

    // Cache the suggestions
    this.suggestionCache.set(cacheKey, suggestions.slice(0, 8)) // Limit to 8 suggestions
    
    return suggestions.slice(0, 8)
  }

  // Add command to history for learning
  private addToHistory(command: string, intent: CommandIntent, result: CommandResult): void {
    const historyEntry: CommandHistory = {
      id: `hist-${Date.now()}`,
      command,
      intent,
      result,
      timestamp: new Date(),
      success: result.success
    }

    this.commandHistory.push(historyEntry)

    // Keep only last 100 commands
    if (this.commandHistory.length > 100) {
      this.commandHistory.splice(0, this.commandHistory.length - 100)
    }
  }

  // Get command history for analysis
  getCommandHistory(): CommandHistory[] {
    return [...this.commandHistory]
  }

  // Clear suggestion cache
  clearSuggestionCache(): void {
    this.suggestionCache.clear()
  }

  // Provide user feedback on command results
  provideFeedback(commandId: string, feedback: 'positive' | 'negative' | 'neutral'): void {
    const historyEntry = this.commandHistory.find(h => h.id === commandId)
    if (historyEntry) {
      historyEntry.userFeedback = feedback
    }
  }
}

// Export singleton instance
export const commandProcessor = new CommandProcessor()