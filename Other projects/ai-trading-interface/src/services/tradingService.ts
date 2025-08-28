import { mcpClient } from './mcpClient'
import { useTradingStore } from '@/stores/tradingStore'
import type { Lab, Bot, Account, Market, BacktestResult } from '@/types'

// Trading service that connects MCP client to stores
class TradingService {
  private tradingStore = useTradingStore

  // Account operations
  async loadAccounts(): Promise<Account[]> {
    try {
      console.log('💰 Loading accounts...')
      this.tradingStore.getState().setLoading('accounts', true)
      this.tradingStore.getState().setError('accounts', null)
      
      const accounts = await mcpClient.getAllAccounts()
      console.log('📊 Accounts loaded:', accounts)
      this.tradingStore.getState().setAccounts(accounts)
      
      return accounts
    } catch (error) {
      console.error('❌ Failed to load accounts:', error)
      const errorMessage = error instanceof Error ? error.message : 'Failed to load accounts'
      this.tradingStore.getState().setError('accounts', errorMessage)
      throw error
    } finally {
      this.tradingStore.getState().setLoading('accounts', false)
    }
  }

  async createSimulatedAccount(name: string, initialBalance: number): Promise<Account> {
    try {
      this.tradingStore.getState().setLoading('accounts', true)
      
      const account = await mcpClient.createSimulatedAccount({
        name,
        initialBalance,
        currency: 'USD'
      })
      
      this.tradingStore.getState().addAccount(account)
      return account
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to create account'
      this.tradingStore.getState().setError('accounts', errorMessage)
      throw error
    } finally {
      this.tradingStore.getState().setLoading('accounts', false)
    }
  }

  async refreshAccountBalance(accountId: string): Promise<void> {
    try {
      const balance = await mcpClient.getAccountBalance(accountId)
      
      this.tradingStore.getState().updateAccount(accountId, {
        balance: balance.balance,
        equity: balance.equity,
        margin: balance.margin,
        freeMargin: balance.freeMargin,
      })
    } catch (error) {
      console.error('Failed to refresh account balance:', error)
    }
  }

  // Lab operations
  async loadLabs(): Promise<Lab[]> {
    try {
      this.tradingStore.getState().setLoading('labs', true)
      this.tradingStore.getState().setError('labs', null)
      
      const labs = await mcpClient.getAllLabs()
      this.tradingStore.getState().setLabs(labs)
      
      return labs
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to load labs'
      this.tradingStore.getState().setError('labs', errorMessage)
      throw error
    } finally {
      this.tradingStore.getState().setLoading('labs', false)
    }
  }

  async createLab(config: {
    name: string
    scriptId: string
    accountId: string
    parameters?: Record<string, any>
  }): Promise<Lab> {
    try {
      this.tradingStore.getState().setLoading('labs', true)
      
      const lab = await mcpClient.createLab(config)
      this.tradingStore.getState().addLab(lab)
      
      return lab
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to create lab'
      this.tradingStore.getState().setError('labs', errorMessage)
      throw error
    } finally {
      this.tradingStore.getState().setLoading('labs', false)
    }
  }

  async cloneLab(sourceLabId: string, config: {
    name: string
    accountId?: string
    parameters?: Record<string, any>
  }): Promise<Lab> {
    try {
      this.tradingStore.getState().setLoading('labs', true)
      
      const lab = await mcpClient.cloneLab(sourceLabId, config)
      this.tradingStore.getState().addLab(lab)
      
      return lab
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to clone lab'
      this.tradingStore.getState().setError('labs', errorMessage)
      throw error
    } finally {
      this.tradingStore.getState().setLoading('labs', false)
    }
  }

  async deleteLab(labId: string): Promise<void> {
    try {
      await mcpClient.deleteLab(labId)
      this.tradingStore.getState().removeLab(labId)
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to delete lab'
      this.tradingStore.getState().setError('labs', errorMessage)
      throw error
    }
  }

  async backtestLab(labId: string, config: {
    startDate?: string
    endDate?: string
    period?: '1_year' | '2_years' | '3_years'
  } = {}): Promise<string> {
    try {
      this.tradingStore.getState().setLoading('backtesting', true)
      this.tradingStore.getState().setError('backtesting', null)
      
      // Update lab status to running
      this.tradingStore.getState().updateLab(labId, { status: 'running' })
      
      const result = await mcpClient.backtestLab(labId, config)
      
      return result.backtestId
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to start backtest'
      this.tradingStore.getState().setError('backtesting', errorMessage)
      
      // Update lab status to failed
      this.tradingStore.getState().updateLab(labId, { status: 'failed' })
      
      throw error
    } finally {
      this.tradingStore.getState().setLoading('backtesting', false)
    }
  }

  async getBacktestResults(backtestId: string): Promise<BacktestResult> {
    try {
      const result = await mcpClient.getBacktestResults(backtestId)
      
      // Update the associated lab with the backtest result
      if (result.labId) {
        this.tradingStore.getState().updateLab(result.labId, {
          status: result.status === 'completed' ? 'completed' : 'failed',
          lastBacktest: result
        })
      }
      
      return result
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to get backtest results'
      this.tradingStore.getState().setError('backtesting', errorMessage)
      throw error
    }
  }

  // Bot operations
  async loadBots(): Promise<Bot[]> {
    try {
      this.tradingStore.getState().setLoading('bots', true)
      this.tradingStore.getState().setError('bots', null)
      
      const bots = await mcpClient.getAllBots()
      this.tradingStore.getState().setBots(bots)
      
      return bots
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to load bots'
      this.tradingStore.getState().setError('bots', errorMessage)
      throw error
    } finally {
      this.tradingStore.getState().setLoading('bots', false)
    }
  }

  async createBotFromLab(labId: string, config: {
    name: string
    accountId: string
  }): Promise<Bot> {
    try {
      this.tradingStore.getState().setLoading('bots', true)
      
      const bot = await mcpClient.createBotFromLab(labId, config)
      this.tradingStore.getState().addBot(bot)
      
      return bot
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to create bot'
      this.tradingStore.getState().setError('bots', errorMessage)
      throw error
    } finally {
      this.tradingStore.getState().setLoading('bots', false)
    }
  }

  async activateBot(botId: string): Promise<void> {
    try {
      await mcpClient.activateBot(botId)
      this.tradingStore.getState().updateBot(botId, { 
        status: 'active',
        activatedAt: new Date()
      })
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to activate bot'
      this.tradingStore.getState().setError('bots', errorMessage)
      throw error
    }
  }

  async deactivateBot(botId: string): Promise<void> {
    try {
      await mcpClient.deactivateBot(botId)
      this.tradingStore.getState().updateBot(botId, { status: 'inactive' })
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to deactivate bot'
      this.tradingStore.getState().setError('bots', errorMessage)
      throw error
    }
  }

  async pauseBot(botId: string): Promise<void> {
    try {
      await mcpClient.pauseBot(botId)
      this.tradingStore.getState().updateBot(botId, { status: 'paused' })
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to pause bot'
      this.tradingStore.getState().setError('bots', errorMessage)
      throw error
    }
  }

  async resumeBot(botId: string): Promise<void> {
    try {
      await mcpClient.resumeBot(botId)
      this.tradingStore.getState().updateBot(botId, { status: 'active' })
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to resume bot'
      this.tradingStore.getState().setError('bots', errorMessage)
      throw error
    }
  }

  async deactivateAllBots(): Promise<number> {
    try {
      const result = await mcpClient.deactivateAllBots()
      
      // Update all bots to inactive status
      const { bots } = this.tradingStore.getState()
      bots.forEach(bot => {
        if (bot.status === 'active') {
          this.tradingStore.getState().updateBot(bot.id, { status: 'inactive' })
        }
      })
      
      return result.deactivated
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to deactivate all bots'
      this.tradingStore.getState().setError('bots', errorMessage)
      throw error
    }
  }

  // Market operations
  async loadMarkets(): Promise<Market[]> {
    try {
      this.tradingStore.getState().setLoading('markets', true)
      this.tradingStore.getState().setError('markets', null)
      
      const markets = await mcpClient.getAllMarkets()
      this.tradingStore.getState().setMarkets(markets)
      
      return markets
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to load markets'
      this.tradingStore.getState().setError('markets', errorMessage)
      throw error
    } finally {
      this.tradingStore.getState().setLoading('markets', false)
    }
  }

  async updateMarketPrice(symbol: string): Promise<void> {
    try {
      const priceData = await mcpClient.getMarketPrice(symbol)
      this.tradingStore.getState().updateMarketPrice(symbol, priceData.price)
    } catch (error) {
      console.error(`Failed to update price for ${symbol}:`, error)
    }
  }

  // Bulk operations
  async bulkBacktestLabs(labIds: string[], config: {
    period?: '1_year' | '2_years' | '3_years'
    autoAdjust?: boolean
  } = {}): Promise<Array<{ labId: string; success: boolean; backtestId?: string; error?: string }>> {
    try {
      this.tradingStore.getState().setLoading('backtesting', true)
      
      const results = await mcpClient.bulkProcessLabs(labIds, {
        operation: 'backtest',
        parameters: config
      })
      
      // Update lab statuses based on results
      results.results.forEach(result => {
        this.tradingStore.getState().updateLab(result.labId, {
          status: result.success ? 'running' : 'failed'
        })
      })
      
      return results.results.map(result => ({
        labId: result.labId,
        success: result.success,
        error: result.error
      }))
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to bulk backtest labs'
      this.tradingStore.getState().setError('backtesting', errorMessage)
      throw error
    } finally {
      this.tradingStore.getState().setLoading('backtesting', false)
    }
  }

  // Health and status
  async checkConnection(): Promise<boolean> {
    try {
      console.log('🔍 Trading service checking MCP connection...')
      const status = await mcpClient.getHaasStatus()
      console.log('📡 MCP status response:', status)
      return status.connected
    } catch (error) {
      console.error('❌ MCP connection check failed:', error)
      return false
    }
  }

  async getSystemHealth(): Promise<{
    status: 'healthy' | 'degraded' | 'unhealthy'
    services: Record<string, boolean>
  }> {
    try {
      return await mcpClient.healthCheck()
    } catch (error) {
      return {
        status: 'unhealthy',
        services: {
          mcp: false,
          haas: false
        }
      }
    }
  }
}

// Create singleton instance
export const tradingService = new TradingService()

// Export the service class for testing
export { TradingService }