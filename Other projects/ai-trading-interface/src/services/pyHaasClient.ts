// pyHaasAPI Integration Client
// This client communicates with a Python backend that uses the pyHaasAPI library

interface PyHaasConfig {
  baseUrl: string
  timeout: number
  retryAttempts: number
}

const defaultConfig: PyHaasConfig = {
  baseUrl: 'http://localhost:8001', // Python backend server
  timeout: 60000, // 60 seconds for long operations
  retryAttempts: 3,
}

// Response wrapper for Python backend
interface PyHaasResponse<T = any> {
  success: boolean
  data?: T
  error?: string
  timestamp: string
  execution_time?: number
}

// Market discovery types
interface MarketInfo {
  symbol: string
  exchange: string
  baseAsset: string
  quoteAsset: string
  isActive: boolean
  minTradeSize: number
  tickSize: number
  category: 'spot' | 'futures' | 'perpetual'
}

interface MarketDiscoveryResult {
  totalMarkets: number
  activeMarkets: number
  exchanges: string[]
  categories: Record<string, number>
  markets: MarketInfo[]
}

// Lab management types
interface LabCloneConfig {
  sourceLabId: string
  targetAssets: string[]
  accountId: string
  namePrefix?: string
  parameters?: Record<string, any>
}

interface LabCloneResult {
  sourceLabId: string
  clonedLabs: Array<{
    labId: string
    name: string
    asset: string
    status: 'created' | 'failed'
    error?: string
  }>
  totalCreated: number
  totalFailed: number
}

// Parameter optimization types
interface ParameterRange {
  name: string
  type: 'integer' | 'float' | 'boolean' | 'choice'
  min?: number
  max?: number
  step?: number
  choices?: any[]
  current: any
}

interface OptimizationConfig {
  labId: string
  parameters: ParameterRange[]
  strategy: 'strategic' | 'intelligent' | 'genetic' | 'grid'
  maxCombinations?: number
  constraints?: {
    maxDrawdown?: number
    minReturn?: number
    maxComplexity?: number
  }
}

interface OptimizationResult {
  labId: string
  totalCombinations: number
  testedCombinations: number
  bestParameters: Record<string, any>
  bestPerformance: {
    totalReturn: number
    sharpeRatio: number
    maxDrawdown: number
    winRate: number
    profitFactor: number
  }
  allResults: Array<{
    parameters: Record<string, any>
    performance: any
    rank: number
  }>
  executionTime: number
}

// History intelligence types
interface HistoryPeriod {
  symbol: string
  exchange: string
  earliestDate: string
  latestDate: string
  dataQuality: number
  gaps: Array<{
    start: string
    end: string
    duration: string
  }>
}

interface BacktestPeriodValidation {
  symbol: string
  requestedStart: string
  requestedEnd: string
  validatedStart: string
  validatedEnd: string
  adjustments: string[]
  warnings: string[]
  dataQuality: number
}

// Miguel workflow types
interface MiguelWorkflowConfig {
  sourceLabId: string
  scriptName: string
  coin: string
  stage0Config?: {
    backtestCount: number
    period: string
    timeframes: string[]
  }
  stage1Config?: {
    labCount: number
    backtestPerLab: number
    period: string
    generations: number
    populationSize: number
  }
}

interface MiguelWorkflowResult {
  workflowId: string
  stage0Results: {
    totalBacktests: number
    completedBacktests: number
    bestTimeframes: string[]
    performance: any[]
  }
  stage1Results: {
    totalLabs: number
    totalBacktests: number
    completedBacktests: number
    bestParameters: Record<string, any>
    finalPerformance: any
  }
  totalExecutionTime: number
  status: 'running' | 'completed' | 'failed' | 'paused'
}

class PyHaasClient {
  private config: PyHaasConfig
  private baseHeaders: Record<string, string>

  constructor(config: Partial<PyHaasConfig> = {}) {
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

        const result: PyHaasResponse<T> = await response.json()
        
        if (!result.success) {
          throw new Error(result.error || 'Unknown server error')
        }

        return result.data as T
      } catch (error) {
        if (attempt === maxAttempts) {
          throw error
        }
        
        // Wait before retry with exponential backoff
        await new Promise(resolve => setTimeout(resolve, 1000 * Math.pow(2, attempt - 1)))
      }
    }

    throw new Error('Max retry attempts exceeded')
  }

  // Market Discovery and Intelligence
  async discoverMarkets(options: {
    exchanges?: string[]
    categories?: string[]
    minVolume?: number
    activeOnly?: boolean
  } = {}): Promise<MarketDiscoveryResult> {
    return this.request('/api/markets/discover', {
      method: 'POST',
      body: JSON.stringify(options),
    })
  }

  async classifyMarkets(symbols: string[]): Promise<Array<{
    symbol: string
    category: string
    riskLevel: 'low' | 'medium' | 'high'
    liquidity: 'low' | 'medium' | 'high'
    volatility: number
    tradingHours: string
  }>> {
    return this.request('/api/markets/classify', {
      method: 'POST',
      body: JSON.stringify({ symbols }),
    })
  }

  async getMarketStatistics(symbol: string, period: string = '30d'): Promise<{
    symbol: string
    volume: {
      avg24h: number
      total: number
      trend: 'increasing' | 'decreasing' | 'stable'
    }
    price: {
      current: number
      high: number
      low: number
      change: number
      volatility: number
    }
    trading: {
      activeHours: number
      avgSpread: number
      depthScore: number
    }
  }> {
    return this.request(`/api/markets/${symbol}/stats?period=${period}`)
  }

  // Advanced Lab Management
  async bulkCloneLabs(config: LabCloneConfig): Promise<LabCloneResult> {
    return this.request('/api/labs/bulk-clone', {
      method: 'POST',
      body: JSON.stringify(config),
    })
  }

  async optimizeLabConfiguration(labId: string, config: {
    targetPerformance?: {
      minReturn?: number
      maxDrawdown?: number
      minSharpe?: number
    }
    constraints?: {
      maxComplexity?: string
      preferredTimeframes?: string[]
      riskTolerance?: string
    }
  }): Promise<{
    originalConfig: Record<string, any>
    optimizedConfig: Record<string, any>
    expectedImprovement: {
      returnIncrease: number
      drawdownReduction: number
      sharpeImprovement: number
    }
    confidence: number
  }> {
    return this.request(`/api/labs/${labId}/optimize-config`, {
      method: 'POST',
      body: JSON.stringify(config),
    })
  }

  async validateLabConfiguration(labId: string): Promise<{
    isValid: boolean
    issues: Array<{
      type: 'error' | 'warning' | 'suggestion'
      component: string
      message: string
      fix?: string
    }>
    score: number
    recommendations: string[]
  }> {
    return this.request(`/api/labs/${labId}/validate`)
  }

  // Parameter Intelligence and Optimization
  async analyzeParameters(labId: string): Promise<{
    parameters: Array<{
      name: string
      type: 'timeframe' | 'numerical' | 'structural'
      currentValue: any
      suggestedRange: ParameterRange
      importance: number
      correlations: Array<{
        parameter: string
        correlation: number
      }>
    }>
    complexity: 'simple' | 'moderate' | 'complex' | 'advanced'
    optimizationPotential: number
  }> {
    return this.request(`/api/labs/${labId}/analyze-parameters`)
  }

  async optimizeParameters(config: OptimizationConfig): Promise<OptimizationResult> {
    return this.request('/api/parameters/optimize', {
      method: 'POST',
      body: JSON.stringify(config),
    })
  }

  async generateParameterRanges(
    parameters: Array<{ name: string; currentValue: any; type?: string }>,
    strategy: 'strategic' | 'intelligent' | 'conservative' | 'aggressive' = 'strategic'
  ): Promise<ParameterRange[]> {
    return this.request('/api/parameters/generate-ranges', {
      method: 'POST',
      body: JSON.stringify({ parameters, strategy }),
    })
  }

  // History Intelligence
  async discoverHistoryPeriod(symbol: string, exchange?: string): Promise<HistoryPeriod> {
    const params = new URLSearchParams({ symbol })
    if (exchange) params.append('exchange', exchange)
    
    return this.request(`/api/history/discover?${params}`)
  }

  async validateBacktestPeriod(config: {
    symbol: string
    startDate: string
    endDate: string
    exchange?: string
    requiredDataPoints?: number
  }): Promise<BacktestPeriodValidation> {
    return this.request('/api/history/validate-period', {
      method: 'POST',
      body: JSON.stringify(config),
    })
  }

  async optimizeBacktestPeriod(config: {
    symbol: string
    preferredDuration: string
    maxGapTolerance?: number
    minDataQuality?: number
  }): Promise<{
    optimizedStart: string
    optimizedEnd: string
    actualDuration: string
    dataQuality: number
    adjustments: string[]
  }> {
    return this.request('/api/history/optimize-period', {
      method: 'POST',
      body: JSON.stringify(config),
    })
  }

  async syncHistoryData(symbols: string[], options: {
    priority?: 'basic' | 'extended'
    maxConcurrent?: number
    timeout?: number
  } = {}): Promise<{
    totalSymbols: number
    syncedSymbols: number
    failedSymbols: Array<{
      symbol: string
      error: string
    }>
    executionTime: number
  }> {
    return this.request('/api/history/sync', {
      method: 'POST',
      body: JSON.stringify({ symbols, options }),
    })
  }

  // Miguel Workflow System
  async startMiguelWorkflow(config: MiguelWorkflowConfig): Promise<{
    workflowId: string
    estimatedDuration: number
    stages: Array<{
      name: string
      estimatedDuration: number
      backtestCount: number
    }>
  }> {
    return this.request('/api/miguel/start', {
      method: 'POST',
      body: JSON.stringify(config),
    })
  }

  async getMiguelWorkflowStatus(workflowId: string): Promise<MiguelWorkflowResult> {
    return this.request(`/api/miguel/${workflowId}/status`)
  }

  async pauseMiguelWorkflow(workflowId: string): Promise<void> {
    return this.request(`/api/miguel/${workflowId}/pause`, {
      method: 'POST',
    })
  }

  async resumeMiguelWorkflow(workflowId: string): Promise<void> {
    return this.request(`/api/miguel/${workflowId}/resume`, {
      method: 'POST',
    })
  }

  async cancelMiguelWorkflow(workflowId: string): Promise<void> {
    return this.request(`/api/miguel/${workflowId}/cancel`, {
      method: 'POST',
    })
  }

  // Account Management
  async createStandardizedAccount(config: {
    name: string
    type: 'simulated' | 'paper' | 'live'
    initialBalance: number
    currency: string
    riskSettings?: {
      maxDrawdown: number
      maxPositionSize: number
      stopLossRequired: boolean
    }
  }): Promise<{
    accountId: string
    name: string
    standardizedName: string
    settings: Record<string, any>
  }> {
    return this.request('/api/accounts/create-standardized', {
      method: 'POST',
      body: JSON.stringify(config),
    })
  }

  async getAccountPerformance(accountId: string, period: string = '30d'): Promise<{
    accountId: string
    period: string
    performance: {
      totalReturn: number
      sharpeRatio: number
      maxDrawdown: number
      winRate: number
      profitFactor: number
      totalTrades: number
      avgTradeReturn: number
      volatility: number
    }
    equity: Array<{
      timestamp: string
      value: number
      drawdown: number
    }>
    trades: Array<{
      timestamp: string
      symbol: string
      side: 'buy' | 'sell'
      quantity: number
      price: number
      pnl: number
    }>
  }> {
    return this.request(`/api/accounts/${accountId}/performance?period=${period}`)
  }

  // Advanced Analytics
  async extractBacktestData(backtestId: string, options: {
    includeTradeDetails?: boolean
    includeHeuristics?: boolean
    includeEquityCurve?: boolean
  } = {}): Promise<{
    backtestId: string
    summary: {
      totalReturn: number
      sharpeRatio: number
      maxDrawdown: number
      winRate: number
      profitFactor: number
      totalTrades: number
    }
    heuristics?: {
      category1: number // Trend following
      category2: number // Mean reversion
      category3: number // Momentum
      category4: number // Volatility
      category5: number // Volume
      category6: number // Risk management
    }
    trades?: Array<{
      entryTime: string
      exitTime: string
      symbol: string
      side: 'long' | 'short'
      quantity: number
      entryPrice: number
      exitPrice: number
      pnl: number
      duration: number
    }>
    equity?: Array<{
      timestamp: string
      value: number
      drawdown: number
    }>
    debugging?: {
      errors: string[]
      warnings: string[]
      performance: {
        processingTime: number
        memoryUsage: number
      }
    }
  }> {
    return this.request(`/api/backtests/${backtestId}/extract`, {
      method: 'POST',
      body: JSON.stringify(options),
    })
  }

  async analyzeBacktestPerformance(backtestId: string): Promise<{
    backtestId: string
    analysis: {
      strengths: string[]
      weaknesses: string[]
      recommendations: string[]
      riskAssessment: {
        level: 'low' | 'medium' | 'high'
        factors: string[]
        mitigation: string[]
      }
    }
    comparison: {
      benchmark: string
      outperformance: number
      correlation: number
      beta: number
    }
    confidence: number
  }> {
    return this.request(`/api/backtests/${backtestId}/analyze`)
  }

  // System Health and Monitoring
  async getSystemStatus(): Promise<{
    status: 'healthy' | 'degraded' | 'unhealthy'
    services: {
      pyhaas_api: boolean
      haas_server: boolean
      database: boolean
      cache: boolean
    }
    performance: {
      avgResponseTime: number
      activeConnections: number
      memoryUsage: number
      cpuUsage: number
    }
    version: {
      pyhaas_api: string
      wrapper: string
      haas_server: string
    }
  }> {
    return this.request('/api/system/status')
  }

  async getOperationLogs(options: {
    operation?: string
    level?: 'debug' | 'info' | 'warning' | 'error'
    limit?: number
    since?: string
  } = {}): Promise<Array<{
    timestamp: string
    level: string
    operation: string
    message: string
    duration?: number
    error?: string
  }>> {
    const params = new URLSearchParams()
    Object.entries(options).forEach(([key, value]) => {
      if (value !== undefined) params.append(key, value.toString())
    })
    
    return this.request(`/api/system/logs?${params}`)
  }

  // Configuration and Utilities
  updateConfig(newConfig: Partial<PyHaasConfig>): void {
    this.config = { ...this.config, ...newConfig }
  }

  setAuthToken(token: string): void {
    this.baseHeaders['Authorization'] = `Bearer ${token}`
  }

  removeAuthToken(): void {
    delete this.baseHeaders['Authorization']
  }

  async healthCheck(): Promise<{
    status: 'healthy' | 'unhealthy'
    timestamp: string
    responseTime: number
  }> {
    const startTime = Date.now()
    try {
      await this.request('/api/health')
      return {
        status: 'healthy',
        timestamp: new Date().toISOString(),
        responseTime: Date.now() - startTime
      }
    } catch (error) {
      return {
        status: 'unhealthy',
        timestamp: new Date().toISOString(),
        responseTime: Date.now() - startTime
      }
    }
  }
}

// Create singleton instance
export const pyHaasClient = new PyHaasClient()

// Export types and client
export type { 
  PyHaasConfig,
  PyHaasResponse,
  MarketInfo,
  MarketDiscoveryResult,
  LabCloneConfig,
  LabCloneResult,
  ParameterRange,
  OptimizationConfig,
  OptimizationResult,
  HistoryPeriod,
  BacktestPeriodValidation,
  MiguelWorkflowConfig,
  MiguelWorkflowResult
}
export { PyHaasClient }