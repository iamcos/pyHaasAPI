// HaasScript RAG Client for AI-powered script intelligence
interface RAGConfig {
  baseUrl: string
  timeout: number
  retryAttempts: number
}

const defaultConfig: RAGConfig = {
  baseUrl: 'http://localhost:5001',
  timeout: 30000,
  retryAttempts: 3,
}

// RAG API Response types
interface RAGResponse<T = any> {
  success: boolean
  data?: T
  error?: string
  timestamp: string
}

interface TradingMemory {
  id: string
  content: string
  metadata: {
    type: 'strategy' | 'analysis' | 'optimization' | 'insight'
    tags: string[]
    confidence: number
    source: string
    timestamp: string
  }
}

interface ScriptAnalysis {
  complexity: 'simple' | 'moderate' | 'complex' | 'advanced'
  indicators: string[]
  timeframes: string[]
  riskLevel: 'low' | 'medium' | 'high'
  marketSuitability: string[]
  estimatedPerformance: {
    expectedReturn: number
    maxDrawdown: number
    confidence: number
  }
  suggestions: string[]
}

interface ScriptImprovement {
  type: 'performance' | 'risk' | 'logic' | 'optimization'
  description: string
  impact: 'low' | 'medium' | 'high'
  implementation: string
  confidence: number
}

interface TranslationResult {
  haasScript: string
  confidence: number
  warnings: string[]
  suggestions: string[]
  parameters: Array<{
    name: string
    type: string
    defaultValue: any
    description: string
  }>
}

interface ExternalStrategy {
  source: 'tradingview' | 'mt4' | 'mt5' | 'custom'
  language: 'pinescript' | 'mql4' | 'mql5' | 'python' | 'other'
  code: string
  description?: string
  parameters?: Record<string, any>
}

class RAGClient {
  private config: RAGConfig
  private baseHeaders: Record<string, string>

  constructor(config: Partial<RAGConfig> = {}) {
    this.config = { ...defaultConfig, ...config }
    this.baseHeaders = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    }
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const maxAttempts = this.config.retryAttempts

    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
      try {
        const controller = new AbortController()
        const timeoutId = setTimeout(() => controller.abort(), this.config.timeout)

        const response = await fetch(`${this.config.baseUrl}${endpoint}`, {
          ...options,
          headers: {
            ...this.baseHeaders,
            ...options.headers,
          },
          signal: controller.signal,
        })

        clearTimeout(timeoutId)

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`)
        }

        const result: RAGResponse<T> = await response.json()
        
        if (!result.success) {
          throw new Error(result.error || 'Unknown server error')
        }

        return result.data as T
      } catch (error) {
        if (attempt === maxAttempts) {
          throw error
        }
        
        // Wait before retry
        await new Promise(resolve => setTimeout(resolve, 1000 * attempt))
      }
    }

    throw new Error('Max retry attempts exceeded')
  }

  // Memory Management
  async addMemory(projectId: string, memory: Omit<TradingMemory, 'id'>): Promise<TradingMemory> {
    return this.request(`/api/projects/${projectId}/memories`, {
      method: 'POST',
      body: JSON.stringify(memory),
    })
  }

  async searchMemories(projectId: string, query: string, options: {
    limit?: number
    type?: string
    minConfidence?: number
  } = {}): Promise<TradingMemory[]> {
    const params = new URLSearchParams({
      q: query,
      limit: (options.limit || 10).toString(),
      ...(options.type && { type: options.type }),
      ...(options.minConfidence && { min_confidence: options.minConfidence.toString() }),
    })

    return this.request(`/api/projects/${projectId}/memories/search?${params}`)
  }

  async getMemory(projectId: string, memoryId: string): Promise<TradingMemory> {
    return this.request(`/api/projects/${projectId}/memories/${memoryId}`)
  }

  async updateMemory(
    projectId: string, 
    memoryId: string, 
    updates: Partial<TradingMemory>
  ): Promise<TradingMemory> {
    return this.request(`/api/projects/${projectId}/memories/${memoryId}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    })
  }

  async deleteMemory(projectId: string, memoryId: string): Promise<void> {
    return this.request(`/api/projects/${projectId}/memories/${memoryId}`, {
      method: 'DELETE',
    })
  }

  // Project Management
  async createProject(name: string, description?: string): Promise<{ id: string; name: string }> {
    return this.request('/api/projects', {
      method: 'POST',
      body: JSON.stringify({ name, description }),
    })
  }

  async getProjects(): Promise<Array<{ id: string; name: string; description?: string }>> {
    return this.request('/api/projects')
  }

  async deleteProject(projectId: string): Promise<void> {
    return this.request(`/api/projects/${projectId}`, {
      method: 'DELETE',
    })
  }

  // Script Intelligence
  async analyzeScript(script: string, context?: {
    marketType?: string
    timeframe?: string
    riskTolerance?: string
  }): Promise<ScriptAnalysis> {
    return this.request('/api/scripts/analyze', {
      method: 'POST',
      body: JSON.stringify({ script, context }),
    })
  }

  async suggestImprovements(
    script: string, 
    performance?: {
      totalReturn: number
      maxDrawdown: number
      sharpeRatio: number
      winRate: number
    }
  ): Promise<ScriptImprovement[]> {
    return this.request('/api/scripts/improve', {
      method: 'POST',
      body: JSON.stringify({ script, performance }),
    })
  }

  async optimizeParameters(
    script: string,
    currentParams: Record<string, any>,
    constraints?: {
      maxDrawdown?: number
      minReturn?: number
      maxComplexity?: string
    }
  ): Promise<{
    optimizedParams: Record<string, any>
    expectedImprovement: number
    confidence: number
    reasoning: string[]
  }> {
    return this.request('/api/scripts/optimize-params', {
      method: 'POST',
      body: JSON.stringify({ script, currentParams, constraints }),
    })
  }

  // Strategy Translation
  async translateStrategy(
    externalStrategy: ExternalStrategy,
    options: {
      preserveLogic?: boolean
      addComments?: boolean
      optimizeForHaas?: boolean
    } = {}
  ): Promise<TranslationResult> {
    return this.request('/api/translate', {
      method: 'POST',
      body: JSON.stringify({ 
        strategy: externalStrategy, 
        options: {
          preserveLogic: true,
          addComments: true,
          optimizeForHaas: true,
          ...options
        }
      }),
    })
  }

  async validateTranslation(
    originalCode: string,
    translatedCode: string,
    sourceLanguage: string
  ): Promise<{
    isValid: boolean
    accuracy: number
    issues: Array<{
      type: 'logic' | 'syntax' | 'performance' | 'compatibility'
      description: string
      severity: 'low' | 'medium' | 'high'
      suggestion?: string
    }>
  }> {
    return this.request('/api/translate/validate', {
      method: 'POST',
      body: JSON.stringify({ originalCode, translatedCode, sourceLanguage }),
    })
  }

  // Knowledge Base Queries
  async queryKnowledgeBase(
    query: string,
    context?: {
      projectId?: string
      type?: string
      timeframe?: string
    }
  ): Promise<{
    answer: string
    confidence: number
    sources: TradingMemory[]
    suggestions: string[]
  }> {
    return this.request('/api/knowledge/query', {
      method: 'POST',
      body: JSON.stringify({ query, context }),
    })
  }

  async getRelatedStrategies(
    strategy: string,
    options: {
      limit?: number
      minSimilarity?: number
      includePerformance?: boolean
    } = {}
  ): Promise<Array<{
    strategy: string
    similarity: number
    performance?: {
      return: number
      drawdown: number
      sharpe: number
    }
    description: string
  }>> {
    return this.request('/api/knowledge/related', {
      method: 'POST',
      body: JSON.stringify({ strategy, options }),
    })
  }

  // Market Intelligence
  async getMarketInsights(
    symbols: string[],
    timeframe: string = '1d'
  ): Promise<Array<{
    symbol: string
    sentiment: 'bullish' | 'bearish' | 'neutral'
    confidence: number
    keyFactors: string[]
    suggestedStrategies: string[]
  }>> {
    return this.request('/api/market/insights', {
      method: 'POST',
      body: JSON.stringify({ symbols, timeframe }),
    })
  }

  async analyzeMarketConditions(
    symbols: string[],
    period: string = '30d'
  ): Promise<{
    overallSentiment: 'bullish' | 'bearish' | 'neutral'
    volatility: 'low' | 'medium' | 'high'
    trendStrength: number
    correlations: Array<{
      pair: [string, string]
      correlation: number
    }>
    recommendations: string[]
  }> {
    return this.request('/api/market/conditions', {
      method: 'POST',
      body: JSON.stringify({ symbols, period }),
    })
  }

  // Batch Operations
  async batchAnalyzeScripts(scripts: Array<{
    id: string
    script: string
    context?: any
  }>): Promise<Array<{
    id: string
    analysis: ScriptAnalysis
    error?: string
  }>> {
    return this.request('/api/scripts/batch-analyze', {
      method: 'POST',
      body: JSON.stringify({ scripts }),
    })
  }

  async batchTranslateStrategies(strategies: Array<{
    id: string
    strategy: ExternalStrategy
    options?: any
  }>): Promise<Array<{
    id: string
    result: TranslationResult
    error?: string
  }>> {
    return this.request('/api/translate/batch', {
      method: 'POST',
      body: JSON.stringify({ strategies }),
    })
  }

  // Health and Status
  async healthCheck(): Promise<{
    status: 'healthy' | 'degraded' | 'unhealthy'
    services: {
      mongodb: boolean
      ai_model: boolean
      knowledge_base: boolean
    }
    version: string
  }> {
    return this.request('/api/health')
  }

  async getStats(): Promise<{
    totalMemories: number
    totalProjects: number
    totalTranslations: number
    avgResponseTime: number
  }> {
    return this.request('/api/stats')
  }

  // Configuration
  updateConfig(newConfig: Partial<RAGConfig>): void {
    this.config = { ...this.config, ...newConfig }
  }

  setAuthToken(token: string): void {
    this.baseHeaders['Authorization'] = `Bearer ${token}`
  }

  removeAuthToken(): void {
    delete this.baseHeaders['Authorization']
  }
}

// Create singleton instance
export const ragClient = new RAGClient()

// Export types and client
export type { 
  RAGConfig,
  RAGResponse,
  TradingMemory,
  ScriptAnalysis,
  ScriptImprovement,
  TranslationResult,
  ExternalStrategy
}
export { RAGClient }