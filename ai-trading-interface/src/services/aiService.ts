import { ragClient } from './ragClient'
import { useAIStore } from '@/stores/aiStore'
import type { 
  StrategyAnalysis, 
  MarketAnalysis, 
  ChainOfThoughtStep,
  InsightCard,
  ProactiveAction,
  AIResponse,
  Persona,
  HaasScriptResult,
  RiskAssessment
} from '@/types'
import type { 
  TradingMemory, 
  ScriptAnalysis, 
  ExternalStrategy, 
  TranslationResult 
} from './ragClient'

// AI Provider interface for different AI services
interface AIProvider {
  name: string
  model: string
  apiKey: string
  baseUrl?: string
  maxTokens: number
  temperature: number
}

// AI Configuration
interface AIConfig {
  primaryProvider: AIProvider
  fallbackProviders: AIProvider[]
  retryAttempts: number
  timeoutMs: number
  contextWindowSize: number
}

// Prompt templates for trading-specific use cases
class PromptTemplates {
  static readonly STRATEGY_ANALYSIS = `
You are an expert trading strategy analyst. Analyze the following strategy description and provide detailed insights.

Strategy Description: {description}
Market Context: {marketContext}
User Persona: {persona}

Please provide:
1. Feasibility assessment (0-1 scale)
2. Complexity level (simple/moderate/complex/advanced)
3. Expected performance metrics
4. Required parameters
5. Market suitability analysis
6. Risk assessment
7. Specific recommendations

Use chain-of-thought reasoning and show your analysis steps.
`

  static readonly MARKET_ANALYSIS = `
You are a professional market analyst. Analyze the current market conditions for the specified symbols.

Symbols: {symbols}
Timeframe: {timeframe}
Historical Data: {historicalData}
Current Conditions: {currentConditions}

Provide:
1. Overall market sentiment (bullish/bearish/neutral)
2. Trend analysis for each timeframe
3. Opportunity identification
4. Risk assessment
5. Actionable recommendations

Show your reasoning process step by step.
`

  static readonly HAASSCRIPT_GENERATION = `
You are a HaasScript expert. Generate a complete HaasScript trading bot based on the strategy description.

Strategy: {strategy}
Parameters: {parameters}
Risk Profile: {riskProfile}
Market Conditions: {marketConditions}

Requirements:
- Generate syntactically correct HaasScript
- Include proper error handling
- Add comprehensive comments
- Implement risk management
- Follow HaasScript best practices

Provide the complete script with parameter definitions and usage instructions.
`

  static readonly RISK_ASSESSMENT = `
You are a risk management specialist. Assess the risk profile of the given trading setup.

Portfolio: {portfolio}
Proposed Changes: {proposedChanges}
Market Conditions: {marketConditions}
Risk Tolerance: {riskTolerance}

Analyze:
1. Position sizing risks
2. Correlation risks
3. Market risks
4. Liquidity risks
5. Operational risks

Provide specific mitigation strategies and risk scores.
`

  static readonly CHAIN_OF_THOUGHT = `
Explain your decision-making process for the following trading decision:

Decision: {decision}
Context: {context}
Available Data: {data}

Break down your reasoning into clear steps:
1. Data analysis
2. Pattern recognition
3. Risk evaluation
4. Decision rationale
5. Alternative considerations
6. Confidence assessment

Be thorough and transparent in your reasoning.
`
}

// Enhanced AI Service with GPT-5/Claude integration
class AIService {
  private aiStore = useAIStore
  private currentProjectId = 'default' // Could be made configurable
  private config: AIConfig
  private conversationContext: Map<string, any[]> = new Map()
  private requestQueue: Map<string, Promise<any>> = new Map()

  constructor() {
    this.config = this.initializeConfig()
  }

  private initializeConfig(): AIConfig {
    return {
      primaryProvider: {
        name: 'openai',
        model: 'gpt-4', // Will be upgraded to GPT-5 when available
        apiKey: process.env.OPENAI_API_KEY || '',
        baseUrl: 'https://api.openai.com/v1',
        maxTokens: 4096,
        temperature: 0.7
      },
      fallbackProviders: [
        {
          name: 'anthropic',
          model: 'claude-3-sonnet-20240229',
          apiKey: process.env.ANTHROPIC_API_KEY || '',
          baseUrl: 'https://api.anthropic.com/v1',
          maxTokens: 4096,
          temperature: 0.7
        }
      ],
      retryAttempts: 3,
      timeoutMs: 30000,
      contextWindowSize: 8192
    }
  }

  // Core AI interaction method with error handling and fallbacks
  private async callAI(
    prompt: string, 
    context?: any, 
    options?: {
      temperature?: number
      maxTokens?: number
      systemPrompt?: string
    }
  ): Promise<AIResponse> {
    const requestId = `req-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
    
    // Check if similar request is already in progress
    const existingRequest = this.requestQueue.get(prompt)
    if (existingRequest) {
      return existingRequest
    }

    const requestPromise = this.executeAIRequest(prompt, context, options, requestId)
    this.requestQueue.set(prompt, requestPromise)

    try {
      const result = await requestPromise
      return result
    } finally {
      this.requestQueue.delete(prompt)
    }
  }

  private async executeAIRequest(
    prompt: string,
    context: any,
    options: any,
    requestId: string
  ): Promise<AIResponse> {
    const startTime = Date.now()
    let lastError: Error | null = null

    // Try primary provider first
    for (let attempt = 0; attempt < this.config.retryAttempts; attempt++) {
      try {
        const response = await this.callProvider(
          this.config.primaryProvider,
          prompt,
          context,
          options,
          requestId
        )
        return response
      } catch (error) {
        lastError = error as Error
        console.warn(`Primary provider attempt ${attempt + 1} failed:`, error)
        
        // Wait before retry (exponential backoff)
        if (attempt < this.config.retryAttempts - 1) {
          await new Promise(resolve => setTimeout(resolve, Math.pow(2, attempt) * 1000))
        }
      }
    }

    // Try fallback providers
    for (const provider of this.config.fallbackProviders) {
      try {
        console.log(`Trying fallback provider: ${provider.name}`)
        const response = await this.callProvider(provider, prompt, context, options, requestId)
        return response
      } catch (error) {
        lastError = error as Error
        console.warn(`Fallback provider ${provider.name} failed:`, error)
      }
    }

    // All providers failed, return error response
    throw new Error(`All AI providers failed. Last error: ${lastError?.message}`)
  }

  private async callProvider(
    provider: AIProvider,
    prompt: string,
    context: any,
    options: any,
    requestId: string
  ): Promise<AIResponse> {
    const chainOfThought: ChainOfThoughtStep[] = []
    
    // Add initial reasoning step
    chainOfThought.push({
      id: `${requestId}-cot-1`,
      step: 1,
      reasoning: `Processing request with ${provider.name} (${provider.model})`,
      data: { provider: provider.name, model: provider.model },
      confidence: 0.9,
      alternatives: [],
      timestamp: new Date()
    })

    const startTime = Date.now()

    try {
      let response: any

      if (provider.name === 'openai') {
        response = await this.callOpenAI(provider, prompt, context, options)
      } else if (provider.name === 'anthropic') {
        response = await this.callAnthropic(provider, prompt, context, options)
      } else {
        throw new Error(`Unsupported provider: ${provider.name}`)
      }

      const processingTime = Date.now() - startTime

      // Add success reasoning step
      chainOfThought.push({
        id: `${requestId}-cot-2`,
        step: 2,
        reasoning: `Successfully received response from ${provider.name}`,
        data: { 
          processingTime,
          tokenCount: response.usage?.total_tokens || 0
        },
        confidence: 0.95,
        alternatives: [],
        timestamp: new Date()
      })

      // Parse proactive actions from response if any
      const proactiveActions = this.extractProactiveActions(response.content, requestId)

      return {
        content: response.content,
        confidence: this.calculateResponseConfidence(response),
        chainOfThought,
        proactiveActions,
        metadata: {
          model: provider.model,
          tokens: response.usage?.total_tokens || 0,
          processingTime
        }
      }
    } catch (error) {
      chainOfThought.push({
        id: `${requestId}-cot-error`,
        step: chainOfThought.length + 1,
        reasoning: `Error occurred with ${provider.name}: ${(error as Error).message}`,
        data: { error: (error as Error).message },
        confidence: 0.1,
        alternatives: [],
        timestamp: new Date()
      })
      
      throw error
    }
  }

  private async callOpenAI(
    provider: AIProvider,
    prompt: string,
    context: any,
    options: any
  ): Promise<any> {
    const messages = [
      {
        role: 'system',
        content: options?.systemPrompt || 'You are an expert AI trading assistant with deep knowledge of financial markets, trading strategies, and risk management.'
      },
      {
        role: 'user',
        content: this.formatPromptWithContext(prompt, context)
      }
    ]

    const response = await fetch(`${provider.baseUrl}/chat/completions`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${provider.apiKey}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        model: provider.model,
        messages,
        max_tokens: options?.maxTokens || provider.maxTokens,
        temperature: options?.temperature || provider.temperature,
        stream: false
      })
    })

    if (!response.ok) {
      throw new Error(`OpenAI API error: ${response.status} ${response.statusText}`)
    }

    const data = await response.json()
    
    if (data.error) {
      throw new Error(`OpenAI API error: ${data.error.message}`)
    }

    return {
      content: data.choices[0].message.content,
      usage: data.usage
    }
  }

  private async callAnthropic(
    provider: AIProvider,
    prompt: string,
    context: any,
    options: any
  ): Promise<any> {
    const response = await fetch(`${provider.baseUrl}/messages`, {
      method: 'POST',
      headers: {
        'x-api-key': provider.apiKey,
        'Content-Type': 'application/json',
        'anthropic-version': '2023-06-01'
      },
      body: JSON.stringify({
        model: provider.model,
        max_tokens: options?.maxTokens || provider.maxTokens,
        temperature: options?.temperature || provider.temperature,
        system: options?.systemPrompt || 'You are an expert AI trading assistant with deep knowledge of financial markets, trading strategies, and risk management.',
        messages: [
          {
            role: 'user',
            content: this.formatPromptWithContext(prompt, context)
          }
        ]
      })
    })

    if (!response.ok) {
      throw new Error(`Anthropic API error: ${response.status} ${response.statusText}`)
    }

    const data = await response.json()
    
    if (data.error) {
      throw new Error(`Anthropic API error: ${data.error.message}`)
    }

    return {
      content: data.content[0].text,
      usage: data.usage
    }
  }

  private formatPromptWithContext(prompt: string, context: any): string {
    if (!context) return prompt

    let formattedPrompt = prompt

    // Replace template variables
    Object.keys(context).forEach(key => {
      const placeholder = `{${key}}`
      if (formattedPrompt.includes(placeholder)) {
        const value = typeof context[key] === 'object' 
          ? JSON.stringify(context[key], null, 2)
          : String(context[key])
        formattedPrompt = formattedPrompt.replace(new RegExp(placeholder, 'g'), value)
      }
    })

    return formattedPrompt
  }

  private calculateResponseConfidence(response: any): number {
    // Simple confidence calculation based on response characteristics
    let confidence = 0.7 // Base confidence

    // Adjust based on response length (longer responses often more detailed)
    const contentLength = response.content?.length || 0
    if (contentLength > 500) confidence += 0.1
    if (contentLength > 1000) confidence += 0.1

    // Adjust based on token usage efficiency
    const tokens = response.usage?.total_tokens || 0
    if (tokens > 0 && contentLength / tokens > 3) confidence += 0.1

    return Math.min(confidence, 1.0)
  }

  private extractProactiveActions(content: string, requestId: string): ProactiveAction[] {
    const actions: ProactiveAction[] = []

    // Look for action indicators in the response
    const actionPatterns = [
      /I recommend (.*?)(?:\.|$)/gi,
      /You should consider (.*?)(?:\.|$)/gi,
      /It would be wise to (.*?)(?:\.|$)/gi,
      /Consider (.*?)(?:\.|$)/gi
    ]

    actionPatterns.forEach((pattern, index) => {
      const matches = content.match(pattern)
      if (matches) {
        matches.forEach((match, matchIndex) => {
          const actionText = match.replace(pattern, '$1').trim()
          if (actionText.length > 10) { // Filter out very short matches
            actions.push({
              id: `${requestId}-action-${index}-${matchIndex}`,
              type: 'suggestion',
              title: 'AI Recommendation',
              description: actionText,
              action: async () => {
                console.log('Executing AI recommendation:', actionText)
                // This would integrate with actual trading actions
              },
              priority: 'medium',
              chainOfThought: [],
              timestamp: new Date()
            })
          }
        })
      }
    })

    return actions
  }

  // Context management for conversational interactions
  private updateConversationContext(contextId: string, entry: any): void {
    if (!this.conversationContext.has(contextId)) {
      this.conversationContext.set(contextId, [])
    }

    const context = this.conversationContext.get(contextId)!
    context.push(entry)

    // Limit context size to prevent token overflow
    if (context.length > 10) {
      context.splice(0, context.length - 10)
    }
  }

  private getConversationContext(contextId: string): any[] {
    return this.conversationContext.get(contextId) || []
  }

  // Public method to process general queries
  async processQuery(query: string, contextId: string = 'default'): Promise<AIResponse> {
    try {
      this.aiStore.getState().setProcessing(true)
      this.aiStore.getState().setLastQuery(query)

      const context = {
        query,
        conversationHistory: this.getConversationContext(contextId),
        userPersona: this.aiStore.getState().currentPersona,
        timestamp: new Date().toISOString()
      }

      const response = await this.callAI(
        `User query: ${query}\n\nPlease provide a helpful and detailed response based on your trading expertise.`,
        context,
        {
          systemPrompt: 'You are an expert AI trading assistant. Provide helpful, accurate, and actionable advice for trading and investment decisions. Always consider risk management and show your reasoning process.'
        }
      )

      // Update conversation context
      this.updateConversationContext(contextId, {
        type: 'query',
        content: query,
        response: response.content,
        timestamp: new Date()
      })

      // Store in AI store
      this.aiStore.getState().addConversationEntry(response)
      response.chainOfThought.forEach(step => {
        this.aiStore.getState().addChainOfThoughtStep(step)
      })
      response.proactiveActions.forEach(action => {
        this.aiStore.getState().addProactiveAction(action)
      })

      return response
    } catch (error) {
      console.error('Query processing failed:', error)
      throw error
    } finally {
      this.aiStore.getState().setProcessing(false)
    }
  }

  // Strategy Analysis with AI integration
  async analyzeStrategyDescription(
    description: string,
    marketContext?: {
      symbols: string[]
      timeframe: string
      marketConditions: string[]
    }
  ): Promise<StrategyAnalysis> {
    try {
      this.aiStore.getState().setProcessing(true)
      
      // First, gather context from RAG system
      const knowledgeQuery = await ragClient.queryKnowledgeBase(
        `Strategy analysis: ${description}`,
        {
          projectId: this.currentProjectId,
          type: 'strategy',
          timeframe: marketContext?.timeframe
        }
      )

      const relatedStrategies = await ragClient.getRelatedStrategies(description, {
        limit: 5,
        minSimilarity: 0.6,
        includePerformance: true
      })

      let marketInsights = null
      if (marketContext?.symbols) {
        marketInsights = await ragClient.getMarketInsights(
          marketContext.symbols,
          marketContext.timeframe || '1d'
        )
      }

      // Use AI to analyze the strategy with full context
      const aiContext = {
        description,
        marketContext: marketContext || {},
        persona: this.aiStore.getState().currentPersona,
        knowledgeBase: knowledgeQuery,
        relatedStrategies,
        marketInsights
      }

      const aiResponse = await this.callAI(
        PromptTemplates.STRATEGY_ANALYSIS,
        aiContext,
        {
          systemPrompt: 'You are an expert trading strategy analyst. Provide detailed, actionable analysis with specific metrics and recommendations.',
          temperature: 0.3 // Lower temperature for more consistent analysis
        }
      )

      // Parse AI response into structured analysis
      const analysis = await this.parseStrategyAnalysis(aiResponse, {
        knowledgeQuery,
        relatedStrategies,
        marketInsights
      })

      // Store analysis in AI store
      this.aiStore.getState().setStrategyAnalysis(analysis)

      // Add chain of thought steps to store
      analysis.chainOfThought.forEach(step => {
        this.aiStore.getState().addChainOfThoughtStep(step)
      })

      // Add proactive actions
      aiResponse.proactiveActions.forEach(action => {
        this.aiStore.getState().addProactiveAction(action)
      })

      // Store the analysis as a memory for future reference
      await ragClient.addMemory(this.currentProjectId, {
        content: `AI Strategy analysis: ${description}`,
        metadata: {
          type: 'strategy',
          tags: ['strategy', 'analysis', 'ai_generated', ...(marketContext?.symbols || [])],
          confidence: analysis.feasibility,
          source: 'ai_service',
          timestamp: new Date().toISOString(),
        }
      })

      return analysis
    } catch (error) {
      console.error('Strategy analysis failed:', error)
      throw error
    } finally {
      this.aiStore.getState().setProcessing(false)
    }
  }

  private async parseStrategyAnalysis(
    aiResponse: AIResponse, 
    context: any
  ): Promise<StrategyAnalysis> {
    // Extract structured data from AI response
    // This is a simplified parser - in production, you'd use more sophisticated NLP
    const content = aiResponse.content

    // Extract feasibility score
    const feasibilityMatch = content.match(/feasibility[:\s]*([0-9.]+)/i)
    const feasibility = feasibilityMatch ? parseFloat(feasibilityMatch[1]) : 0.7

    // Extract complexity level
    const complexityMatch = content.match(/complexity[:\s]*(simple|moderate|complex|advanced)/i)
    const complexity = (complexityMatch?.[1]?.toLowerCase() as any) || 'moderate'

    // Extract performance estimates
    const returnMatch = content.match(/expected return[:\s]*([0-9.]+)/i)
    const drawdownMatch = content.match(/drawdown[:\s]*([0-9.]+)/i)

    const estimatedPerformance = {
      expectedReturn: returnMatch ? parseFloat(returnMatch[1]) : 0.12,
      expectedDrawdown: drawdownMatch ? parseFloat(drawdownMatch[1]) : 0.08,
      confidence: aiResponse.confidence,
      timeframe: '1 year'
    }

    // Extract risks from AI response
    const risks: RiskAssessment[] = this.extractRisksFromAIResponse(content)

    // Extract recommendations
    const recommendations = this.extractRecommendationsFromAIResponse(content)

    return {
      feasibility,
      complexity,
      estimatedPerformance,
      requiredParameters: this.extractParameters(content, context.knowledgeQuery),
      marketSuitability: this.assessMarketSuitability(context.marketInsights, context.knowledgeQuery),
      risks,
      recommendations,
      chainOfThought: aiResponse.chainOfThought
    }
  }

  private extractRisksFromAIResponse(content: string): RiskAssessment[] {
    const risks: RiskAssessment[] = []
    
    // Look for risk patterns in the AI response
    const riskPatterns = [
      /risk[:\s]*([^.]+)/gi,
      /danger[:\s]*([^.]+)/gi,
      /concern[:\s]*([^.]+)/gi,
      /warning[:\s]*([^.]+)/gi
    ]

    riskPatterns.forEach(pattern => {
      const matches = content.match(pattern)
      if (matches) {
        matches.forEach((match, index) => {
          const description = match.replace(pattern, '$1').trim()
          if (description.length > 10) {
            risks.push({
              type: 'market',
              level: 'medium',
              description,
              mitigation: 'Monitor closely and adjust parameters as needed',
              impact: 0.3
            })
          }
        })
      }
    })

    // Add default risk if none found
    if (risks.length === 0) {
      risks.push({
        type: 'market',
        level: 'medium',
        description: 'General market risk applies to all trading strategies',
        mitigation: 'Implement proper risk management and position sizing',
        impact: 0.2
      })
    }

    return risks
  }

  private extractRecommendationsFromAIResponse(content: string): string[] {
    const recommendations: string[] = []
    
    // Look for recommendation patterns
    const recPatterns = [
      /recommend[:\s]*([^.]+)/gi,
      /suggest[:\s]*([^.]+)/gi,
      /advise[:\s]*([^.]+)/gi,
      /consider[:\s]*([^.]+)/gi
    ]

    recPatterns.forEach(pattern => {
      const matches = content.match(pattern)
      if (matches) {
        matches.forEach(match => {
          const rec = match.replace(pattern, '$1').trim()
          if (rec.length > 10 && !recommendations.includes(rec)) {
            recommendations.push(rec)
          }
        })
      }
    })

    // Add default recommendations if none found
    if (recommendations.length === 0) {
      recommendations.push(
        'Backtest the strategy on historical data',
        'Start with small position sizes',
        'Monitor performance closely',
        'Implement proper risk management'
      )
    }

    return recommendations.slice(0, 5) // Limit to 5 recommendations
  }

  // Market Analysis with AI integration
  async analyzeMarketConditions(
    symbols: string[],
    timeframe: string = '1d'
  ): Promise<MarketAnalysis> {
    try {
      this.aiStore.getState().setProcessing(true)

      // Get market data from RAG system
      const marketInsights = await ragClient.getMarketInsights(symbols, timeframe)
      const marketConditions = await ragClient.analyzeMarketConditions(symbols)

      // Prepare context for AI analysis
      const aiContext = {
        symbols: symbols.join(', '),
        timeframe,
        historicalData: marketInsights,
        currentConditions: marketConditions,
        persona: this.aiStore.getState().currentPersona
      }

      // Get AI analysis
      const aiResponse = await this.callAI(
        PromptTemplates.MARKET_ANALYSIS,
        aiContext,
        {
          systemPrompt: 'You are a professional market analyst with expertise in technical analysis, market sentiment, and risk assessment.',
          temperature: 0.4 // Slightly higher for more nuanced market analysis
        }
      )

      // Parse AI response into structured analysis
      const analysis = await this.parseMarketAnalysis(aiResponse, {
        marketInsights,
        marketConditions
      })

      // Store analysis
      this.aiStore.getState().setMarketAnalysis(analysis)

      // Add chain of thought
      analysis.chainOfThought.forEach(step => {
        this.aiStore.getState().addChainOfThoughtStep(step)
      })

      // Add proactive actions
      aiResponse.proactiveActions.forEach(action => {
        this.aiStore.getState().addProactiveAction(action)
      })

      return analysis
    } catch (error) {
      console.error('Market analysis failed:', error)
      throw error
    } finally {
      this.aiStore.getState().setProcessing(false)
    }
  }

  private async parseMarketAnalysis(
    aiResponse: AIResponse,
    context: any
  ): Promise<MarketAnalysis> {
    const content = aiResponse.content

    // Extract sentiment
    const sentimentMatch = content.match(/sentiment[:\s]*(bullish|bearish|neutral)/i)
    const sentiment = (sentimentMatch?.[1]?.toLowerCase() as any) || 'neutral'

    // Extract trends from AI response
    const trends = this.extractTrendsFromAIResponse(content)

    // Extract opportunities
    const opportunities = this.extractOpportunitiesFromAIResponse(content)

    // Extract risks
    const risks = this.extractMarketRisksFromAIResponse(content)

    // Extract recommendations
    const recommendations = this.extractRecommendationsFromAIResponse(content)

    return {
      sentiment,
      confidence: aiResponse.confidence,
      trends,
      opportunities,
      risks,
      recommendations,
      chainOfThought: aiResponse.chainOfThought
    }
  }

  private extractTrendsFromAIResponse(content: string): any[] {
    const trends: any[] = []
    
    // Look for trend patterns
    const trendPatterns = [
      /trend[:\s]*([^.]+)/gi,
      /(upward|downward|sideways)[:\s]*([^.]+)/gi,
      /(bullish|bearish)[:\s]*([^.]+)/gi
    ]

    trendPatterns.forEach(pattern => {
      const matches = content.match(pattern)
      if (matches) {
        matches.forEach((match, index) => {
          const description = match.trim()
          if (description.length > 10) {
            trends.push({
              timeframe: '1d',
              direction: this.extractDirection(description),
              strength: 0.7,
              confidence: 0.8,
              description
            })
          }
        })
      }
    })

    return trends.slice(0, 3) // Limit to 3 trends
  }

  private extractOpportunitiesFromAIResponse(content: string): any[] {
    const opportunities: any[] = []
    
    const oppPatterns = [
      /opportunity[:\s]*([^.]+)/gi,
      /potential[:\s]*([^.]+)/gi,
      /breakout[:\s]*([^.]+)/gi
    ]

    oppPatterns.forEach(pattern => {
      const matches = content.match(pattern)
      if (matches) {
        matches.forEach(match => {
          const description = match.trim()
          if (description.length > 10) {
            opportunities.push({
              type: 'momentum',
              description,
              potential: 0.12,
              timeframe: '4h',
              confidence: 0.7
            })
          }
        })
      }
    })

    return opportunities.slice(0, 3) // Limit to 3 opportunities
  }

  private extractMarketRisksFromAIResponse(content: string): any[] {
    const risks: any[] = []
    
    const riskPatterns = [
      /volatility[:\s]*([^.]+)/gi,
      /risk[:\s]*([^.]+)/gi,
      /concern[:\s]*([^.]+)/gi
    ]

    riskPatterns.forEach(pattern => {
      const matches = content.match(pattern)
      if (matches) {
        matches.forEach(match => {
          const description = match.trim()
          if (description.length > 10) {
            risks.push({
              type: 'volatility',
              level: 0.6,
              description,
              mitigation: 'Monitor closely and adjust position sizes'
            })
          }
        })
      }
    })

    return risks.slice(0, 3) // Limit to 3 risks
  }

  private extractDirection(text: string): 'up' | 'down' | 'sideways' {
    const lowerText = text.toLowerCase()
    if (lowerText.includes('up') || lowerText.includes('bullish') || lowerText.includes('rising')) {
      return 'up'
    }
    if (lowerText.includes('down') || lowerText.includes('bearish') || lowerText.includes('falling')) {
      return 'down'
    }
    return 'sideways'
  }

  // HaasScript Generation with AI
  async generateHaasScript(
    strategyDescription: string,
    parameters?: Record<string, any>
  ): Promise<HaasScriptResult> {
    try {
      this.aiStore.getState().setProcessing(true)

      // Get related strategies from RAG
      const relatedStrategies = await ragClient.getRelatedStrategies(strategyDescription, {
        limit: 3,
        minSimilarity: 0.7
      })

      // Get current market conditions for context
      const marketConditions = await ragClient.analyzeMarketConditions([])

      // Prepare context for AI
      const aiContext = {
        strategy: strategyDescription,
        parameters: parameters || {},
        riskProfile: this.aiStore.getState().currentPersona.riskTolerance,
        marketConditions,
        relatedStrategies,
        persona: this.aiStore.getState().currentPersona
      }

      // Generate HaasScript using AI
      const aiResponse = await this.callAI(
        PromptTemplates.HAASSCRIPT_GENERATION,
        aiContext,
        {
          systemPrompt: 'You are a HaasScript expert. Generate syntactically correct, well-commented HaasScript code with proper error handling and risk management.',
          temperature: 0.2, // Low temperature for consistent code generation
          maxTokens: 2048
        }
      )

      // Parse the AI response into structured result
      const result = await this.parseHaasScriptResult(aiResponse, {
        relatedStrategies,
        marketConditions
      })

      // Store the generated script as a memory
      await ragClient.addMemory(this.currentProjectId, {
        content: `Generated HaasScript: ${strategyDescription}`,
        metadata: {
          type: 'strategy',
          tags: ['haasscript', 'generated', 'ai'],
          confidence: result.validation.isValid ? 0.8 : 0.6,
          source: 'ai_service',
          timestamp: new Date().toISOString(),
        }
      })

      return result
    } catch (error) {
      console.error('HaasScript generation failed:', error)
      throw error
    } finally {
      this.aiStore.getState().setProcessing(false)
    }
  }

  private async parseHaasScriptResult(
    aiResponse: AIResponse,
    context: any
  ): Promise<HaasScriptResult> {
    const content = aiResponse.content

    // Extract the script code (look for code blocks)
    const scriptMatch = content.match(/```(?:haasscript|javascript)?\n([\s\S]*?)\n```/i)
    const script = scriptMatch ? scriptMatch[1].trim() : this.generateMockHaasScript('', {})

    // Extract parameters from the AI response
    const parameters = this.extractParametersFromAIResponse(content)

    // Validate the script
    const validation = await this.validateHaasScript(script)

    // Extract optimization suggestions
    const optimization = this.extractOptimizationSuggestions(content)

    return {
      script,
      parameters,
      validation,
      optimization,
      chainOfThought: aiResponse.chainOfThought
    }
  }

  private extractParametersFromAIResponse(content: string): any[] {
    const parameters: any[] = []
    
    // Look for parameter definitions in the AI response
    const paramPatterns = [
      /parameter[:\s]*(\w+)[:\s]*([^,\n]+)/gi,
      /var[:\s]*(\w+)[:\s]*=[:\s]*([^,\n;]+)/gi
    ]

    paramPatterns.forEach(pattern => {
      const matches = [...content.matchAll(pattern)]
      matches.forEach(match => {
        const name = match[1]?.trim()
        const description = match[2]?.trim()
        
        if (name && description) {
          parameters.push({
            name,
            type: this.inferParameterType(description),
            defaultValue: this.extractDefaultValue(description),
            description
          })
        }
      })
    })

    // Add default parameters if none found
    if (parameters.length === 0) {
      parameters.push(
        {
          name: 'RSI_Period',
          type: 'number',
          defaultValue: 14,
          description: 'RSI calculation period'
        },
        {
          name: 'RSI_Oversold',
          type: 'number',
          defaultValue: 30,
          description: 'RSI oversold threshold'
        },
        {
          name: 'RSI_Overbought',
          type: 'number',
          defaultValue: 70,
          description: 'RSI overbought threshold'
        }
      )
    }

    return parameters
  }

  private inferParameterType(description: string): string {
    const lowerDesc = description.toLowerCase()
    if (lowerDesc.includes('period') || lowerDesc.includes('length') || lowerDesc.includes('threshold')) {
      return 'number'
    }
    if (lowerDesc.includes('enable') || lowerDesc.includes('use') || lowerDesc.includes('allow')) {
      return 'boolean'
    }
    return 'string'
  }

  private extractDefaultValue(description: string): any {
    const numberMatch = description.match(/(\d+(?:\.\d+)?)/);
    if (numberMatch) {
      return parseFloat(numberMatch[1])
    }
    
    if (description.toLowerCase().includes('true') || description.toLowerCase().includes('enable')) {
      return true
    }
    if (description.toLowerCase().includes('false') || description.toLowerCase().includes('disable')) {
      return false
    }
    
    return ''
  }

  private async validateHaasScript(script: string): Promise<any> {
    // Basic HaasScript validation
    const errors: any[] = []
    const warnings: any[] = []
    const suggestions: string[] = []

    // Check for required functions
    if (!script.includes('function Initialize()')) {
      errors.push({
        line: 1,
        column: 1,
        message: 'Missing Initialize() function',
        severity: 'error'
      })
    }

    if (!script.includes('function Tick()')) {
      errors.push({
        line: 1,
        column: 1,
        message: 'Missing Tick() function',
        severity: 'error'
      })
    }

    // Check for basic syntax issues
    const openBraces = (script.match(/{/g) || []).length
    const closeBraces = (script.match(/}/g) || []).length
    
    if (openBraces !== closeBraces) {
      errors.push({
        line: 1,
        column: 1,
        message: 'Mismatched braces',
        severity: 'error'
      })
    }

    // Add suggestions
    if (!script.includes('HasPosition()')) {
      suggestions.push('Consider adding position checks before trading')
    }
    
    if (!script.includes('StopLoss') && !script.includes('TakeProfit')) {
      suggestions.push('Consider adding risk management with stop loss and take profit')
    }

    return {
      isValid: errors.length === 0,
      errors,
      warnings,
      suggestions
    }
  }

  private extractOptimizationSuggestions(content: string): any[] {
    const suggestions: any[] = []
    
    const optimizationPatterns = [
      /optimize[:\s]*([^.]+)/gi,
      /improve[:\s]*([^.]+)/gi,
      /enhance[:\s]*([^.]+)/gi
    ]

    optimizationPatterns.forEach(pattern => {
      const matches = content.match(pattern)
      if (matches) {
        matches.forEach(match => {
          const description = match.trim()
          if (description.length > 10) {
            suggestions.push({
              type: 'performance',
              description,
              impact: 'medium',
              implementation: 'Review and test the suggested optimization',
              confidence: 0.7
            })
          }
        })
      }
    })

    return suggestions.slice(0, 5) // Limit to 5 suggestions
  }

  // Strategy Translation
  async translateExternalStrategy(
    externalStrategy: ExternalStrategy
  ): Promise<TranslationResult> {
    try {
      this.aiStore.getState().setProcessing(true)

      const result = await ragClient.translateStrategy(externalStrategy, {
        preserveLogic: true,
        addComments: true,
        optimizeForHaas: true
      })

      // Store the translation as a memory
      await ragClient.addMemory(this.currentProjectId, {
        content: `Translated ${externalStrategy.source} strategy to HaasScript`,
        metadata: {
          type: 'strategy',
          tags: ['translation', externalStrategy.source, externalStrategy.language],
          confidence: result.confidence,
          source: 'translation_service',
          timestamp: new Date().toISOString(),
        }
      })

      return result
    } catch (error) {
      console.error('Strategy translation failed:', error)
      throw error
    } finally {
      this.aiStore.getState().setProcessing(false)
    }
  }

  // Risk Assessment with AI
  async assessRisk(
    portfolio: any,
    proposedChanges: any[]
  ): Promise<RiskAssessment[]> {
    try {
      this.aiStore.getState().setProcessing(true)

      const aiContext = {
        portfolio,
        proposedChanges,
        marketConditions: await ragClient.analyzeMarketConditions([]),
        riskTolerance: this.aiStore.getState().currentPersona.riskTolerance
      }

      const aiResponse = await this.callAI(
        PromptTemplates.RISK_ASSESSMENT,
        aiContext,
        {
          systemPrompt: 'You are a risk management specialist. Provide detailed risk analysis with specific mitigation strategies.',
          temperature: 0.3
        }
      )

      // Parse risk assessment from AI response
      const risks = this.extractRisksFromAIResponse(aiResponse.content)

      // Add chain of thought to store
      aiResponse.chainOfThought.forEach(step => {
        this.aiStore.getState().addChainOfThoughtStep(step)
      })

      return risks
    } catch (error) {
      console.error('Risk assessment failed:', error)
      throw error
    } finally {
      this.aiStore.getState().setProcessing(false)
    }
  }

  // Chain-of-Thought explanation
  async explainDecision(
    decision: any,
    context: any
  ): Promise<ChainOfThoughtStep[]> {
    try {
      const aiContext = {
        decision,
        context,
        data: context.data || {}
      }

      const aiResponse = await this.callAI(
        PromptTemplates.CHAIN_OF_THOUGHT,
        aiContext,
        {
          systemPrompt: 'You are an expert at explaining complex trading decisions. Break down your reasoning into clear, logical steps.',
          temperature: 0.4
        }
      )

      // The AI response already contains chain of thought steps
      // Add them to the store
      aiResponse.chainOfThought.forEach(step => {
        this.aiStore.getState().addChainOfThoughtStep(step)
      })

      return aiResponse.chainOfThought
    } catch (error) {
      console.error('Decision explanation failed:', error)
      return []
    }
  }

  // Script Analysis with AI enhancement
  async analyzeHaasScript(script: string): Promise<ScriptAnalysis> {
    try {
      this.aiStore.getState().setProcessing(true)
      
      // Get basic analysis from RAG
      const ragAnalysis = await ragClient.analyzeScript(script)
      
      // Enhance with AI insights
      const aiContext = {
        script,
        basicAnalysis: ragAnalysis
      }

      const aiResponse = await this.callAI(
        `Analyze this HaasScript and provide detailed insights:\n\n${script}\n\nProvide analysis of logic, potential improvements, and risk factors.`,
        aiContext,
        {
          systemPrompt: 'You are a HaasScript expert. Analyze the code for logic, performance, and risk factors.',
          temperature: 0.3
        }
      )

      // Combine RAG analysis with AI insights
      const enhancedAnalysis = {
        ...ragAnalysis,
        aiInsights: aiResponse.content,
        chainOfThought: aiResponse.chainOfThought
      }

      return enhancedAnalysis
    } catch (error) {
      console.error('Script analysis failed:', error)
      throw error
    } finally {
      this.aiStore.getState().setProcessing(false)
    }
  }

  // Generate AI-powered insights
  async generateInsights(context?: {
    strategies?: string[]
    markets?: string[]
    timeframe?: string
  }): Promise<InsightCard[]> {
    try {
      const insights: InsightCard[] = []

      // Generate market-based insights with AI
      if (context?.markets) {
        const marketInsights = await ragClient.getMarketInsights(context.markets)
        
        // Use AI to generate more sophisticated insights
        const aiContext = {
          markets: context.markets,
          timeframe: context.timeframe || '1d',
          marketData: marketInsights,
          persona: this.aiStore.getState().currentPersona
        }

        const aiResponse = await this.callAI(
          `Generate trading insights for the following markets: ${context.markets.join(', ')}. 
           Focus on opportunities, risks, and actionable recommendations based on current market conditions.`,
          aiContext,
          {
            systemPrompt: 'You are a market analyst. Generate specific, actionable trading insights with clear reasoning.',
            temperature: 0.6
          }
        )

        // Parse AI insights into insight cards
        const aiInsights = this.parseAIInsights(aiResponse, context.markets)
        insights.push(...aiInsights)
      }

      // Generate strategy-based insights
      if (context?.strategies) {
        for (const strategy of context.strategies) {
          const strategyInsight = await this.generateStrategyInsight(strategy)
          if (strategyInsight) {
            insights.push(strategyInsight)
          }
        }
      }

      // Add insights to store
      insights.forEach(insight => {
        this.aiStore.getState().addInsightCard(insight)
      })

      return insights
    } catch (error) {
      console.error('Insight generation failed:', error)
      return []
    }
  }

  private parseAIInsights(aiResponse: AIResponse, markets: string[]): InsightCard[] {
    const insights: InsightCard[] = []
    const content = aiResponse.content

    // Look for insight patterns in AI response
    const insightPatterns = [
      /opportunity[:\s]*([^.]+)/gi,
      /risk[:\s]*([^.]+)/gi,
      /recommendation[:\s]*([^.]+)/gi
    ]

    insightPatterns.forEach((pattern, patternIndex) => {
      const matches = content.match(pattern)
      if (matches) {
        matches.forEach((match, matchIndex) => {
          const description = match.trim()
          if (description.length > 20) {
            const type = patternIndex === 0 ? 'opportunity' : 
                        patternIndex === 1 ? 'risk' : 'market_analysis'
            
            insights.push({
              id: `ai-insight-${Date.now()}-${patternIndex}-${matchIndex}`,
              type,
              title: `AI ${type.charAt(0).toUpperCase() + type.slice(1)} Alert`,
              content: description,
              data: { markets, source: 'ai_analysis' },
              actions: this.generateInsightActions({ description, markets }),
              confidence: aiResponse.confidence,
              chainOfThought: aiResponse.chainOfThought,
              timestamp: new Date()
            })
          }
        })
      }
    })

    return insights.slice(0, 5) // Limit to 5 insights
  }

  private async generateStrategyInsight(strategy: string): Promise<InsightCard | null> {
    try {
      const aiResponse = await this.callAI(
        `Analyze the performance and current status of this trading strategy: ${strategy}. 
         Provide insights on optimization opportunities or concerns.`,
        { strategy },
        {
          systemPrompt: 'You are a strategy optimization expert. Provide actionable insights for strategy improvement.',
          temperature: 0.5
        }
      )

      return {
        id: `strategy-insight-${Date.now()}`,
        type: 'performance',
        title: `Strategy Analysis: ${strategy}`,
        content: aiResponse.content,
        data: { strategy },
        actions: [],
        confidence: aiResponse.confidence,
        chainOfThought: aiResponse.chainOfThought,
        timestamp: new Date()
      }
    } catch (error) {
      console.error('Strategy insight generation failed:', error)
      return null
    }
  }

  // Configuration methods
  updateConfig(newConfig: Partial<AIConfig>): void {
    this.config = { ...this.config, ...newConfig }
  }

  getConfig(): AIConfig {
    return { ...this.config }
  }

  // Context management methods
  clearConversationContext(contextId: string = 'default'): void {
    this.conversationContext.delete(contextId)
  }

  getContextSize(contextId: string = 'default'): number {
    return this.getConversationContext(contextId).length
  }

  // Health check method
  async healthCheck(): Promise<{
    primaryProvider: boolean
    fallbackProviders: boolean[]
    overallHealth: boolean
  }> {
    const results = {
      primaryProvider: false,
      fallbackProviders: [] as boolean[],
      overallHealth: false
    }

    try {
      // Test primary provider
      await this.callProvider(
        this.config.primaryProvider,
        'Health check',
        {},
        { maxTokens: 10 },
        'health-check'
      )
      results.primaryProvider = true
    } catch (error) {
      console.warn('Primary provider health check failed:', error)
    }

    // Test fallback providers
    for (const provider of this.config.fallbackProviders) {
      try {
        await this.callProvider(provider, 'Health check', {}, { maxTokens: 10 }, 'health-check')
        results.fallbackProviders.push(true)
      } catch (error) {
        console.warn(`Fallback provider ${provider.name} health check failed:`, error)
        results.fallbackProviders.push(false)
      }
    }

    results.overallHealth = results.primaryProvider || results.fallbackProviders.some(Boolean)
    return results
  }

  // Helper methods
  private calculateFeasibility(knowledgeQuery: any, relatedStrategies: any[]): number {
    const baseScore = knowledgeQuery.confidence || 0.5
    const strategyBonus = Math.min(relatedStrategies.length * 0.1, 0.3)
    return Math.min(baseScore + strategyBonus, 1.0)
  }

  private determineComplexity(description: string, relatedStrategies: any[]): 'simple' | 'moderate' | 'complex' | 'advanced' {
    const indicators = (description.match(/\b(RSI|MACD|EMA|SMA|Bollinger|Stochastic|ADX)\b/gi) || []).length
    const conditions = (description.match(/\b(if|when|and|or|then)\b/gi) || []).length
    
    const complexityScore = indicators + conditions + (relatedStrategies.length > 0 ? -1 : 1)
    
    if (complexityScore <= 2) return 'simple'
    if (complexityScore <= 4) return 'moderate'
    if (complexityScore <= 6) return 'complex'
    return 'advanced'
  }

  private estimatePerformance(relatedStrategies: any[], marketInsights: any): {
    expectedReturn: number
    expectedDrawdown: number
    confidence: number
    timeframe: string
  } {
    if (relatedStrategies.length > 0) {
      const avgReturn = relatedStrategies.reduce((sum, s) => sum + (s.performance?.return || 0), 0) / relatedStrategies.length
      const avgDrawdown = relatedStrategies.reduce((sum, s) => sum + (s.performance?.drawdown || 0), 0) / relatedStrategies.length
      
      return {
        expectedReturn: avgReturn * 0.8, // Conservative estimate
        expectedDrawdown: avgDrawdown * 1.2, // Conservative estimate
        confidence: 0.75,
        timeframe: '1 year'
      }
    }

    return {
      expectedReturn: 0.1,
      expectedDrawdown: 0.15,
      confidence: 0.5,
      timeframe: '1 year'
    }
  }

  private extractParameters(description: string, knowledgeQuery: any): any[] {
    // Mock parameter extraction - in real implementation, this would use NLP
    const commonParams = [
      { name: 'RSI_Period', type: 'number', default: 14 },
      { name: 'RSI_Overbought', type: 'number', default: 70 },
      { name: 'RSI_Oversold', type: 'number', default: 30 },
    ]
    
    return commonParams
  }

  private assessMarketSuitability(marketInsights: any, knowledgeQuery: any): any[] {
    return [
      { type: 'trending', confidence: 0.8, timeframe: '1d', description: 'Works well in trending markets' },
      { type: 'volatile', confidence: 0.6, timeframe: '4h', description: 'Moderate performance in volatile conditions' }
    ]
  }

  private identifyRisks(description: string, relatedStrategies: any[], marketInsights: any): any[] {
    return [
      {
        type: 'market',
        level: 'medium',
        description: 'Strategy may underperform in ranging markets',
        mitigation: 'Add trend filter',
        impact: 0.3
      }
    ]
  }

  private generateRecommendations(knowledgeQuery: any, relatedStrategies: any[]): string[] {
    const recommendations = ['Test on multiple timeframes', 'Implement proper risk management']
    
    if (relatedStrategies.length > 0) {
      recommendations.push('Consider insights from similar strategies')
    }
    
    return recommendations
  }

  private calculateMarketConfidence(marketInsights: any[]): number {
    if (marketInsights.length === 0) return 0.5
    return marketInsights.reduce((sum, insight) => sum + insight.confidence, 0) / marketInsights.length
  }

  private extractTrends(marketInsights: any[], marketConditions: any): any[] {
    return marketInsights.map(insight => ({
      timeframe: '1d',
      direction: insight.sentiment === 'bullish' ? 'up' : insight.sentiment === 'bearish' ? 'down' : 'sideways',
      strength: insight.confidence,
      confidence: insight.confidence,
      description: `${insight.symbol} showing ${insight.sentiment} sentiment`
    }))
  }

  private identifyOpportunities(marketInsights: any[], marketConditions: any): any[] {
    return marketInsights
      .filter(insight => insight.sentiment === 'bullish' && insight.confidence > 0.7)
      .map(insight => ({
        type: 'momentum',
        description: `${insight.symbol} momentum opportunity`,
        potential: insight.confidence * 0.15,
        timeframe: '4h',
        confidence: insight.confidence
      }))
  }

  private identifyMarketRisks(marketConditions: any): any[] {
    return [
      {
        type: 'volatility',
        level: marketConditions.volatility === 'high' ? 0.8 : marketConditions.volatility === 'medium' ? 0.5 : 0.3,
        description: `${marketConditions.volatility} volatility detected`,
        mitigation: 'Adjust position sizes accordingly'
      }
    ]
  }

  private generateInsightActions(insight: any): ProactiveAction[] {
    const actions: ProactiveAction[] = []

    if (insight.markets) {
      actions.push({
        id: `action-${Date.now()}-analyze`,
        type: 'suggestion',
        title: `Analyze Markets`,
        description: `Deep dive analysis of ${insight.markets.join(', ')}`,
        action: async () => {
          await this.analyzeMarketConditions(insight.markets)
        },
        priority: 'medium',
        chainOfThought: [],
        timestamp: new Date()
      })
    }

    if (insight.symbol) {
      actions.push({
        id: `action-${Date.now()}-strategy`,
        type: 'suggestion',
        title: `Create Strategy`,
        description: `Generate a trading strategy for ${insight.symbol}`,
        action: async () => {
          await this.analyzeStrategyDescription(`Strategy for ${insight.symbol} based on ${insight.sentiment} signal`)
        },
        priority: 'medium',
        chainOfThought: [],
        timestamp: new Date()
      })
    }

    return actions
  }

  private generateMockHaasScript(description: string, parameters?: Record<string, any>): string {
    return `// Generated HaasScript for: ${description}
// This is a mock implementation - replace with actual generation logic

function Initialize() {
    // Initialize indicators and variables
    var rsi = RSI(14);
    var ema = EMA(20);
}

function Tick() {
    // Main trading logic
    if (rsi.Value < 30 && Close > ema.Value) {
        // Buy signal
        if (!HasPosition()) {
            Buy("RSI Oversold + EMA Bullish");
        }
    }
    
    if (rsi.Value > 70 && Close < ema.Value) {
        // Sell signal
        if (HasPosition()) {
            Sell("RSI Overbought + EMA Bearish");
        }
    }
}`
  }

  private extractMockParameters(description: string): Array<{ name: string; type: string; defaultValue: any; description: string }> {
    return [
      {
        name: 'RSI_Period',
        type: 'number',
        defaultValue: 14,
        description: 'RSI calculation period'
      },
      {
        name: 'EMA_Period',
        type: 'number',
        defaultValue: 20,
        description: 'EMA calculation period'
      },
      {
        name: 'RSI_Oversold',
        type: 'number',
        defaultValue: 30,
        description: 'RSI oversold threshold'
      },
      {
        name: 'RSI_Overbought',
        type: 'number',
        defaultValue: 70,
        description: 'RSI overbought threshold'
      }
    ]
  }
}

// Create singleton instance
export const aiService = new AIService()

// Export the service class
export { AIService }