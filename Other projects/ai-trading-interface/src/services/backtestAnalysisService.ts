import { mcpClient } from './mcpClient'

export interface BacktestAnalysisRequest {
  backtest_id: string
}

export interface ComparisonAnalysisRequest {
  backtest_ids: string[]
}

export interface DeploymentRequest {
  backtest_id: string
  deployment_config: {
    account_allocation?: any
    risk_management?: any
    deployment_strategy?: any
  }
}

export interface BacktestMetrics {
  profit_multiplier: number
  final_wallet_balance: number
  final_report_profit_percent: number
  final_report_net_bot_profit: number
  final_report_min_margin: number
  final_report_max_margin: number
  margin_utilization_percent: number
  margin_safety_score: number
  max_drawdown: number
  max_drawdown_percent: number
  losing_positions_count: number
  win_rate: number
  sharpe_ratio: number
  sortino_ratio: number
  profit_factor: number
  calmar_ratio: number
  total_trades: number
  winning_trades: number
  losing_trades: number
  average_win: number
  average_loss: number
  largest_win: number
  largest_loss: number
  risk_reward_ratio: number
  equity_curve_stability: number
  consistency_score: number
  deployment_readiness_score: number
}

export interface BacktestAnalysisReport {
  backtest_id: string
  script_name: string
  account_name: string
  market_tag: string
  execution_period: {
    start: string
    end: string
    duration_days: number
  }
  metrics: BacktestMetrics
  equity_curve: Array<{
    timestamp: string
    balance: number
    profit_loss: number
    drawdown: number
    trade_id?: string
  }>
  position_analysis: {
    total_positions: number
    long_positions: number
    short_positions: number
    winning_positions: number
    losing_positions: number
    position_breakdown: {
      long_wins: number
      long_losses: number
      short_wins: number
      short_losses: number
    }
    duration_analysis: {
      average_duration_hours: number
      min_duration_hours: number
      max_duration_hours: number
      median_duration_hours: number
    }
    profit_distribution: {
      wins_total_profit: number
      losses_total_loss: number
      average_win_size: number
      average_loss_size: number
      largest_win: number
      largest_loss: number
    }
  }
  risk_analysis: {
    risk_grade: string
    risk_factors: Record<string, string>
    risk_recommendations: string[]
    value_at_risk: Record<string, number>
    stress_test_scenarios: Record<string, number>
  }
  deployment_recommendation: {
    is_recommended: boolean
    confidence_level: number
    deployment_strategy: {
      approach: string
      initial_capital_percent: number
      leverage_multiplier: number
      description: string
    }
    risk_management: {
      suggested_stop_loss_percent: number
      max_position_size_percent: number
      daily_loss_limit_percent: number
      monthly_loss_limit_percent: number
      profit_protection: {
        enable_trailing_stop: boolean
        trailing_stop_percent: number
      }
    }
    account_allocation?: {
      assigned_account_id?: string
      server_id?: string
      allocation_time?: string
      initial_balance?: number
      deployment_status?: string
      deployment_config?: any
    }
    monitoring_requirements: {
      monitoring_frequency: string
      key_metrics_to_watch: string[]
      alert_thresholds: Record<string, number>
      review_schedule: {
        daily_review: boolean
        weekly_analysis: boolean
        monthly_optimization: boolean
      }
    }
  }
  chart_data: {
    equity_curve: any
    pnl_distribution: any
    win_loss_ratio: any
    summary_stats: {
      total_trades: number
      profit_trades: number
      loss_trades: number
      win_rate: number
    }
  }
  performance_rank?: number
  style_classification?: string
}

export interface ComparisonAnalysisResult {
  comparison_summary: {
    total_analyzed: number
    deployment_ready_count: number
    top_performer: {
      backtest_id: string
      score: number
      profit_percent: number
    }
    average_metrics: {
      avg_profit_multiplier: number
      avg_profit_percent: number
      avg_max_drawdown: number
      avg_win_rate: number
      avg_sharpe_ratio: number
      avg_deployment_score: number
    }
    recommended_for_deployment: Array<{
      backtest_id: string
      script_name: string
      score: number
      profit_percent: number
      max_drawdown: number
      win_rate: number
    }>
  }
  detailed_reports: BacktestAnalysisReport[]
  deployment_recommendations: {
    recommendation: string
    total_deployable?: number
    deployment_phases?: Array<{
      phase: number
      description: string
      strategies: number
      capital_allocation: string
      strategies_list: string[]
    }>
    risk_management?: {
      max_simultaneous_deployments: number
      total_risk_budget_percent: number
      monitoring_frequency: string
      performance_review_days: number
    }
  }
}

export interface DeploymentResult {
  success: boolean
  deployment_id?: string
  bot_id?: string
  account_id?: string
  message: string
  deployment_config?: any
}

export class BacktestAnalysisService {
  private static instance: BacktestAnalysisService

  static getInstance(): BacktestAnalysisService {
    if (!BacktestAnalysisService.instance) {
      BacktestAnalysisService.instance = new BacktestAnalysisService()
    }
    return BacktestAnalysisService.instance
  }

  /**
   * Analyze a single backtest with comprehensive metrics
   */
  async analyzeSingleBacktest(request: BacktestAnalysisRequest): Promise<BacktestAnalysisReport> {
    try {
      const result = await mcpClient.callTool('analyze_backtest_comprehensive', {
        backtest_id: request.backtest_id
      })

      if (!result.success) {
        throw new Error(result.error || 'Analysis failed')
      }

      return result.data as BacktestAnalysisReport
    } catch (error) {
      console.error('Single backtest analysis failed:', error)
      throw new Error(`Analysis failed: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  }

  /**
   * Compare multiple backtests and rank them
   */
  async compareMultipleBacktests(request: ComparisonAnalysisRequest): Promise<ComparisonAnalysisResult> {
    try {
      const result = await mcpClient.callTool('compare_backtests_comprehensive', {
        backtest_ids: request.backtest_ids
      })

      if (!result.success) {
        throw new Error(result.error || 'Comparison failed')
      }

      return result.data as ComparisonAnalysisResult
    } catch (error) {
      console.error('Backtest comparison failed:', error)
      throw new Error(`Comparison failed: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  }

  /**
   * Get available simulation accounts for deployment
   */
  async getAvailableAccounts(): Promise<Array<{
    account_id: string
    account_name: string
    balance: number
    status: string
    server_id: string
  }>> {
    try {
      const result = await mcpClient.callTool('get_available_simulation_accounts', {})

      if (!result.success) {
        throw new Error(result.error || 'Failed to get accounts')
      }

      return result.data.accounts || []
    } catch (error) {
      console.error('Failed to get available accounts:', error)
      throw new Error(`Failed to get accounts: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  }

  /**
   * Deploy a backtest as a live trading bot
   */
  async deployLiveBot(request: DeploymentRequest): Promise<DeploymentResult> {
    try {
      const result = await mcpClient.callTool('deploy_backtest_as_live_bot', {
        backtest_id: request.backtest_id,
        deployment_config: request.deployment_config
      })

      if (!result.success) {
        throw new Error(result.error || 'Deployment failed')
      }

      return {
        success: true,
        deployment_id: result.data.deployment_id,
        bot_id: result.data.bot_id,
        account_id: result.data.account_id,
        message: result.data.message || 'Bot deployed successfully',
        deployment_config: result.data.deployment_config
      }
    } catch (error) {
      console.error('Bot deployment failed:', error)
      return {
        success: false,
        message: `Deployment failed: ${error instanceof Error ? error.message : 'Unknown error'}`
      }
    }
  }

  /**
   * Export analysis report
   */
  async exportAnalysisReport(backtestId: string, format: 'json' | 'csv' = 'json'): Promise<Blob> {
    try {
      const result = await mcpClient.callTool('export_analysis_report', {
        backtest_id: backtestId,
        format: format
      })

      if (!result.success) {
        throw new Error(result.error || 'Export failed')
      }

      // Convert the result data to a blob
      const jsonData = JSON.stringify(result.data, null, 2)
      return new Blob([jsonData], { type: 'application/json' })
    } catch (error) {
      console.error('Export failed:', error)
      throw new Error(`Export failed: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  }

  /**
   * Get backtest history for analysis
   */
  async getBacktestHistory(filters?: {
    startDate?: Date
    endDate?: Date
    minProfit?: number
    maxDrawdown?: number
    minTrades?: number
  }): Promise<Array<{
    backtest_id: string
    script_name: string
    market_tag: string
    execution_date: string
    profit_percent: number
    max_drawdown: number
    total_trades: number
    win_rate: number
    status: string
  }>> {
    try {
      const result = await mcpClient.callTool('get_backtest_history_for_analysis', {
        filters: filters || {}
      })

      if (!result.success) {
        throw new Error(result.error || 'Failed to get backtest history')
      }

      return result.data.backtests || []
    } catch (error) {
      console.error('Failed to get backtest history:', error)
      throw new Error(`Failed to get history: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  }

  /**
   * Get lab analysis results for multiple labs
   */
  async analyzeLabResults(labId: string): Promise<{
    trading_styles: Array<{
      name: string
      description: string
      avg_performance: number
      configuration_count: number
      performance_profile: any
    }>
    optimization_ranges: Record<string, any>
    recommendations: string[]
  }> {
    try {
      const result = await mcpClient.callTool('analyze_lab_comprehensive', {
        lab_id: labId
      })

      if (!result.success) {
        throw new Error(result.error || 'Lab analysis failed')
      }

      return result.data
    } catch (error) {
      console.error('Lab analysis failed:', error)
      throw new Error(`Lab analysis failed: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  }

  /**
   * Monitor deployed bots performance
   */
  async monitorDeployedBots(): Promise<Array<{
    bot_id: string
    backtest_id: string
    account_id: string
    status: string
    current_pnl: number
    daily_pnl: number
    drawdown_percent: number
    trades_today: number
    alerts: string[]
    deployment_date: string
  }>> {
    try {
      const result = await mcpClient.callTool('monitor_deployed_bots', {})

      if (!result.success) {
        throw new Error(result.error || 'Monitoring failed')
      }

      return result.data.deployed_bots || []
    } catch (error) {
      console.error('Bot monitoring failed:', error)
      throw new Error(`Monitoring failed: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  }

  /**
   * Stop a deployed bot
   */
  async stopDeployedBot(botId: string, reason?: string): Promise<boolean> {
    try {
      const result = await mcpClient.callTool('stop_deployed_bot', {
        bot_id: botId,
        reason: reason || 'Manual stop'
      })

      return result.success
    } catch (error) {
      console.error('Failed to stop bot:', error)
      return false
    }
  }

  /**
   * Get real-time performance metrics for a deployed bot
   */
  async getBotPerformanceMetrics(botId: string): Promise<{
    current_balance: number
    unrealized_pnl: number
    realized_pnl: number
    open_positions: number
    todays_trades: number
    win_rate_today: number
    current_drawdown: number
    margin_usage: number
    alerts: Array<{
      type: string
      message: string
      timestamp: string
      severity: 'info' | 'warning' | 'error'
    }>
  }> {
    try {
      const result = await mcpClient.callTool('get_bot_performance_real_time', {
        bot_id: botId
      })

      if (!result.success) {
        throw new Error(result.error || 'Failed to get performance metrics')
      }

      return result.data
    } catch (error) {
      console.error('Failed to get bot performance:', error)
      throw new Error(`Failed to get performance: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  }

  /**
   * Bulk deploy multiple strategies with risk management
   */
  async bulkDeployStrategies(requests: Array<{
    backtest_id: string
    deployment_config: any
  }>): Promise<{
    successful_deployments: number
    failed_deployments: number
    deployment_results: Array<{
      backtest_id: string
      success: boolean
      bot_id?: string
      account_id?: string
      error?: string
    }>
  }> {
    try {
      const result = await mcpClient.callTool('bulk_deploy_strategies', {
        deployment_requests: requests
      })

      if (!result.success) {
        throw new Error(result.error || 'Bulk deployment failed')
      }

      return result.data
    } catch (error) {
      console.error('Bulk deployment failed:', error)
      throw new Error(`Bulk deployment failed: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  }

  /**
   * Get account allocation status for deployment planning
   */
  async getAccountAllocationStatus(): Promise<{
    total_accounts: number
    available_accounts: number
    allocated_accounts: number
    accounts_by_type: Record<string, number>
    allocation_breakdown: Array<{
      account_id: string
      account_name: string
      status: string
      assigned_bot?: string
      allocation_date?: string
    }>
  }> {
    try {
      const result = await mcpClient.callTool('get_account_allocation_status', {})

      if (!result.success) {
        throw new Error(result.error || 'Failed to get allocation status')
      }

      return result.data
    } catch (error) {
      console.error('Failed to get allocation status:', error)
      throw new Error(`Failed to get status: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  }
}

export const backtestAnalysisService = BacktestAnalysisService.getInstance()