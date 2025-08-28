import type { 
  Lab, 
  Bot, 
  Account, 
  Market, 
  BacktestResult,
  PriceData,
  OrderBook 
} from '@/types'

// MCP Server configuration
interface MCPConfig {
  baseUrl: string
  timeout: number
  retryAttempts: number
  retryDelay: number
}

const defaultConfig: MCPConfig = {
  baseUrl: 'http://localhost:3002',
  timeout: 30000, // 30 seconds
  retryAttempts: 3,
  retryDelay: 1000, // 1 second
}

// API Response wrapper
interface MCPResponse<T = any> {
  success: boolean
  data?: T
  error?: string
  timestamp: string
}

// Request options
interface RequestOptions {
  timeout?: number
  retryAttempts?: number
  signal?: AbortSignal
}

class MCPClient {
  private config: MCPConfig
  private baseHeaders: Record<string, string>

  constructor(config: Partial<MCPConfig> = {}) {
    this.config = { ...defaultConfig, ...config }
    this.baseHeaders = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    }
  }

  // Generic request method with retry logic
  private async request<T>(
    endpoint: string,
    options: RequestInit & RequestOptions = {}
  ): Promise<T> {
    const { timeout, retryAttempts, signal, ...fetchOptions } = options
    const maxAttempts = retryAttempts ?? this.config.retryAttempts
    const requestTimeout = timeout ?? this.config.timeout

    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
      try {
        const controller = new AbortController()
        const timeoutId = setTimeout(() => controller.abort(), requestTimeout)
        
        // Combine signals if provided
        const combinedSignal = signal ? this.combineSignals([signal, controller.signal]) : controller.signal

        const response = await fetch(`${this.config.baseUrl}${endpoint}`, {
          ...fetchOptions,
          headers: {
            ...this.baseHeaders,
            ...fetchOptions.headers,
          },
          signal: combinedSignal,
        })

        clearTimeout(timeoutId)

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`)
        }

        const result: MCPResponse<T> = await response.json()
        
        if (!result.success) {
          throw new Error(result.error || 'Unknown server error')
        }

        return result.data as T
      } catch (error) {
        if (attempt === maxAttempts) {
          throw error
        }
        
        // Wait before retry
        await new Promise(resolve => setTimeout(resolve, this.config.retryDelay * attempt))
      }
    }

    throw new Error('Max retry attempts exceeded')
  }

  private combineSignals(signals: AbortSignal[]): AbortSignal {
    const controller = new AbortController()
    
    signals.forEach(signal => {
      if (signal.aborted) {
        controller.abort()
      } else {
        signal.addEventListener('abort', () => controller.abort())
      }
    })
    
    return controller.signal
  }

  // Account Management Endpoints
  async getHaasStatus(): Promise<{ connected: boolean; version: string }> {
    return this.request('/api/haas/status')
  }

  async getAllAccounts(): Promise<Account[]> {
    return this.request('/api/accounts')
  }

  async createSimulatedAccount(config: {
    name: string
    initialBalance: number
    currency: string
  }): Promise<Account> {
    return this.request('/api/accounts/simulated', {
      method: 'POST',
      body: JSON.stringify(config),
    })
  }

  async getAccountBalance(accountId: string): Promise<{
    balance: number
    equity: number
    margin: number
    freeMargin: number
  }> {
    return this.request(`/api/accounts/${accountId}/balance`)
  }

  async depositFunds(accountId: string, amount: number): Promise<void> {
    return this.request(`/api/accounts/${accountId}/deposit`, {
      method: 'POST',
      body: JSON.stringify({ amount }),
    })
  }

  // Lab Management Endpoints
  async getAllLabs(): Promise<Lab[]> {
    return this.request('/api/labs')
  }

  async createLab(config: {
    name: string
    scriptId: string
    accountId: string
    parameters?: Record<string, any>
  }): Promise<Lab> {
    return this.request('/api/labs', {
      method: 'POST',
      body: JSON.stringify(config),
    })
  }

  async cloneLab(sourceLabId: string, config: {
    name: string
    accountId?: string
    parameters?: Record<string, any>
  }): Promise<Lab> {
    return this.request(`/api/labs/${sourceLabId}/clone`, {
      method: 'POST',
      body: JSON.stringify(config),
    })
  }

  async deleteLab(labId: string): Promise<void> {
    return this.request(`/api/labs/${labId}`, {
      method: 'DELETE',
    })
  }

  async backtestLab(labId: string, config: {
    startDate?: string
    endDate?: string
    period?: '1_year' | '2_years' | '3_years'
  } = {}): Promise<{ backtestId: string }> {
    return this.request(`/api/labs/${labId}/backtest`, {
      method: 'POST',
      body: JSON.stringify(config),
    })
  }

  async getBacktestResults(backtestId: string): Promise<BacktestResult> {
    return this.request(`/api/backtests/${backtestId}`)
  }

  async getLabBacktests(labId: string): Promise<BacktestResult[]> {
    return this.request(`/api/labs/${labId}/backtests`)
  }

  // Bot Management Endpoints
  async getAllBots(): Promise<Bot[]> {
    return this.request('/api/bots')
  }

  async createBotFromLab(labId: string, config: {
    name: string
    accountId: string
  }): Promise<Bot> {
    return this.request('/api/bots/from-lab', {
      method: 'POST',
      body: JSON.stringify({ labId, ...config }),
    })
  }

  async activateBot(botId: string): Promise<void> {
    return this.request(`/api/bots/${botId}/activate`, {
      method: 'POST',
    })
  }

  async deactivateBot(botId: string): Promise<void> {
    return this.request(`/api/bots/${botId}/deactivate`, {
      method: 'POST',
    })
  }

  async pauseBot(botId: string): Promise<void> {
    return this.request(`/api/bots/${botId}/pause`, {
      method: 'POST',
    })
  }

  async resumeBot(botId: string): Promise<void> {
    return this.request(`/api/bots/${botId}/resume`, {
      method: 'POST',
    })
  }

  async deactivateAllBots(): Promise<{ deactivated: number }> {
    return this.request('/api/bots/deactivate-all', {
      method: 'POST',
    })
  }

  async getBotPerformance(botId: string): Promise<{
    totalReturn: number
    sharpeRatio: number
    maxDrawdown: number
    winRate: number
    totalTrades: number
  }> {
    return this.request(`/api/bots/${botId}/performance`)
  }

  // Market Data Endpoints
  markets = {
    getAll: async (): Promise<Market[]> => {
      return this.request('/api/markets')
    },

    getPriceData: async (marketId: string, options: {
      timeframe?: string
      limit?: number
    } = {}): Promise<PriceData[]> => {
      const params = new URLSearchParams()
      if (options.timeframe) params.append('timeframe', options.timeframe)
      if (options.limit) params.append('limit', options.limit.toString())
      
      const query = params.toString() ? `?${params.toString()}` : ''
      return this.request(`/api/markets/${marketId}/price-data${query}`)
    },

    getOrderBook: async (marketId: string, depth: number = 20): Promise<OrderBook> => {
      return this.request(`/api/markets/${marketId}/orderbook?depth=${depth}`)
    },

    getSnapshot: async (marketId: string): Promise<{
      price: number
      volume24h: number
      change24h: number
      high24h: number
      low24h: number
    }> => {
      return this.request(`/api/markets/${marketId}/snapshot`)
    },

    getRecentTrades: async (marketId: string, limit: number = 50): Promise<Array<{
      price: number
      quantity: number
      timestamp: string
      side: 'buy' | 'sell'
    }>> => {
      return this.request(`/api/markets/${marketId}/trades?limit=${limit}`)
    }
  }

  // Legacy methods for backward compatibility
  async getAllMarkets(): Promise<Market[]> {
    return this.markets.getAll()
  }

  async getMarketPrice(symbol: string): Promise<PriceData> {
    const priceData = await this.markets.getPriceData(symbol, { limit: 1 })
    return priceData[0]
  }

  async getOrderBook(symbol: string, depth: number = 10): Promise<OrderBook> {
    return this.markets.getOrderBook(symbol, depth)
  }

  async getMarketSnapshot(symbol: string): Promise<{
    price: number
    volume24h: number
    change24h: number
    high24h: number
    low24h: number
  }> {
    return this.markets.getSnapshot(symbol)
  }

  async getRecentTrades(symbol: string, limit: number = 50): Promise<Array<{
    price: number
    quantity: number
    timestamp: string
    side: 'buy' | 'sell'
  }>> {
    return this.markets.getRecentTrades(symbol, limit)
  }

  // History Intelligence Endpoints
  async discoverDataPeriod(symbol: string): Promise<{
    earliestDate: string
    latestDate: string
    dataQuality: number
  }> {
    return this.request(`/api/history/${symbol}/discover`)
  }

  async validateBacktestPeriod(config: {
    symbol: string
    startDate: string
    endDate: string
  }): Promise<{
    valid: boolean
    adjustedStartDate?: string
    adjustedEndDate?: string
    warnings: string[]
  }> {
    return this.request('/api/history/validate', {
      method: 'POST',
      body: JSON.stringify(config),
    })
  }

  async executeIntelligentBacktest(labId: string, config: {
    symbol: string
    preferredPeriod: string
    autoAdjust: boolean
  }): Promise<{ backtestId: string; adjustments: string[] }> {
    return this.request(`/api/labs/${labId}/intelligent-backtest`, {
      method: 'POST',
      body: JSON.stringify(config),
    })
  }

  async bulkProcessLabs(labIds: string[], config: {
    operation: 'backtest' | 'validate' | 'sync'
    parameters?: Record<string, any>
  }): Promise<{ results: Array<{ labId: string; success: boolean; error?: string }> }> {
    return this.request('/api/labs/bulk-process', {
      method: 'POST',
      body: JSON.stringify({ labIds, ...config }),
    })
  }

  // Script Management Endpoints
  async getAllScripts(): Promise<Array<{
    id: string
    name: string
    description: string
    category: string
    parameters: Array<{ name: string; type: string; default: any }>
  }>> {
    return this.request('/api/scripts')
  }

  async getScript(scriptId: string): Promise<{
    id: string
    name: string
    source: string
    parameters: Record<string, any>
  }> {
    return this.request(`/api/scripts/${scriptId}`)
  }

  async createScript(config: {
    name: string
    description: string
    source: string
    category: string
  }): Promise<{ id: string }> {
    return this.request('/api/scripts', {
      method: 'POST',
      body: JSON.stringify(config),
    })
  }

  async updateScript(scriptId: string, updates: {
    name?: string
    description?: string
    source?: string
  }): Promise<void> {
    return this.request(`/api/scripts/${scriptId}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    })
  }

  async deleteScript(scriptId: string): Promise<void> {
    return this.request(`/api/scripts/${scriptId}`, {
      method: 'DELETE',
    })
  }

  async validateScript(source: string): Promise<{
    valid: boolean
    errors: Array<{ line: number; message: string }>
    warnings: Array<{ line: number; message: string }>
  }> {
    return this.request('/api/scripts/validate', {
      method: 'POST',
      body: JSON.stringify({ source }),
    })
  }

  // Utility methods
  updateConfig(newConfig: Partial<MCPConfig>): void {
    this.config = { ...this.config, ...newConfig }
  }

  setAuthToken(token: string): void {
    this.baseHeaders['Authorization'] = `Bearer ${token}`
  }

  removeAuthToken(): void {
    delete this.baseHeaders['Authorization']
  }

  // Health check
  async healthCheck(): Promise<{
    status: 'healthy' | 'degraded' | 'unhealthy'
    services: Record<string, boolean>
    timestamp: string
  }> {
    return this.request('/api/health')
  }
}

// Create singleton instance
export const mcpClient = new MCPClient()

// Export types and client
export type { MCPConfig, MCPResponse, RequestOptions }
export { MCPClient }