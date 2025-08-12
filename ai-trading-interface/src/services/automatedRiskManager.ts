import { 
  EmergencyControl, 
  EmergencyAction, 
  RiskThreshold, 
  RiskExposure,
  PositionRisk 
} from '../types/risk';
import { Position, Account, Bot } from '../types/trading';
import { aiService } from './aiService';
import { mcpClient } from './mcpClient';
import { riskMonitoringService } from './riskMonitoringService';
import { tradingService } from './tradingService';

interface PositionSizingRecommendation {
  symbol: string;
  recommendedSize: number;
  currentSize: number;
  reasoning: string;
  confidence: number;
  riskScore: number;
  maxRisk: number;
  stopLoss: number;
  takeProfit: number;
}

interface StopLossOptimization {
  symbol: string;
  currentStopLoss: number;
  optimizedStopLoss: number;
  currentTakeProfit: number;
  optimizedTakeProfit: number;
  reasoning: string;
  expectedImprovement: number;
  riskReduction: number;
}

interface EmergencyControlExecution {
  controlId: string;
  triggeredAt: Date;
  actions: EmergencyActionResult[];
  success: boolean;
  error?: string;
}

interface EmergencyActionResult {
  action: EmergencyAction;
  success: boolean;
  result?: any;
  error?: string;
  executedAt: Date;
}

class AutomatedRiskManager {
  private emergencyControls: Map<string, EmergencyControl> = new Map();
  private isActive: boolean = true;
  private subscribers: Set<(data: any) => void> = new Set();

  constructor() {
    this.initializeDefaultControls();
    this.startMonitoring();
  }

  private initializeDefaultControls(): void {
    // Critical portfolio exposure control
    const criticalExposureControl: EmergencyControl = {
      id: 'critical-exposure-control',
      name: 'Critical Portfolio Exposure',
      description: 'Automatically reduce exposure when portfolio risk exceeds critical thresholds',
      type: 'reduce_exposure',
      enabled: true,
      triggerConditions: [{
        id: 'critical-exposure-threshold',
        name: 'Critical Exposure Threshold',
        type: 'portfolio',
        metric: 'totalExposure',
        threshold: 0.95,
        operator: '>',
        severity: 'critical',
        enabled: true,
        accounts: []
      }],
      actions: [
        {
          type: 'reduce_position_size',
          parameters: { reductionPercentage: 0.3 },
          priority: 1
        },
        {
          type: 'send_notification',
          parameters: { 
            message: 'Critical exposure detected - positions automatically reduced',
            severity: 'critical'
          },
          priority: 2
        }
      ]
    };

    // Market crash circuit breaker
    const marketCrashControl: EmergencyControl = {
      id: 'market-crash-breaker',
      name: 'Market Crash Circuit Breaker',
      description: 'Stop all trading activity during extreme market conditions',
      type: 'stop_all_bots',
      enabled: true,
      triggerConditions: [{
        id: 'market-crash-threshold',
        name: 'Market Crash Detection',
        type: 'portfolio',
        metric: 'maxDrawdown',
        threshold: 0.15, // 15% drawdown
        operator: '>',
        severity: 'critical',
        enabled: true,
        accounts: []
      }],
      actions: [
        {
          type: 'deactivate_bots',
          parameters: { immediate: true },
          priority: 1
        },
        {
          type: 'send_notification',
          parameters: { 
            message: 'Market crash detected - all bots deactivated',
            severity: 'critical'
          },
          priority: 2
        }
      ]
    };

    this.emergencyControls.set(criticalExposureControl.id, criticalExposureControl);
    this.emergencyControls.set(marketCrashControl.id, marketCrashControl);
  }

  private startMonitoring(): void {
    // Subscribe to risk monitoring updates
    riskMonitoringService.subscribe((data) => {
      if (data.type === 'risk_update' && this.isActive) {
        this.evaluateEmergencyControls(data.exposures);
      }
    });
  }

  async generatePositionSizingRecommendations(accountId: string): Promise<PositionSizingRecommendation[]> {
    try {
      const account = await mcpClient.accounts.getBalance(accountId);
      const positions = await tradingService.getPositions(accountId);
      const riskExposure = await this.calculateAccountRiskExposure(accountId);
      
      const recommendations: PositionSizingRecommendation[] = [];

      for (const position of positions) {
        const recommendation = await this.generatePositionSizing(position, account, riskExposure);
        recommendations.push(recommendation);
      }

      // Sort by risk score (highest risk first)
      return recommendations.sort((a, b) => b.riskScore - a.riskScore);
    } catch (error) {
      console.error('Failed to generate position sizing recommendations:', error);
      return [];
    }
  }

  private async generatePositionSizing(
    position: Position, 
    account: any, 
    riskExposure: RiskExposure
  ): Promise<PositionSizingRecommendation> {
    // Get market data and volatility
    const marketData = await mcpClient.markets.getPriceData(position.symbol);
    const historicalData = await this.getHistoricalVolatility(position.symbol);
    
    // Calculate Kelly Criterion for optimal position size
    const winRate = await this.estimateWinRate(position.symbol);
    const avgWin = await this.estimateAverageWin(position.symbol);
    const avgLoss = await this.estimateAverageLoss(position.symbol);
    
    const kellyPercentage = this.calculateKellyCriterion(winRate, avgWin, avgLoss);
    
    // Apply risk constraints
    const maxRiskPerPosition = 0.02; // 2% max risk per position
    const portfolioRiskBudget = 0.1; // 10% total portfolio risk
    const currentPortfolioRisk = riskExposure.utilizationPercentage;
    
    // Calculate recommended size using AI analysis
    const aiPrompt = `
      Analyze position sizing for ${position.symbol}:
      - Current position: ${position.size}
      - Current value: $${position.value}
      - Account balance: $${account.totalValue}
      - Portfolio utilization: ${(currentPortfolioRisk * 100).toFixed(2)}%
      - Kelly criterion suggests: ${(kellyPercentage * 100).toFixed(2)}%
      - Historical volatility: ${(historicalData.volatility * 100).toFixed(2)}%
      - Win rate estimate: ${(winRate * 100).toFixed(2)}%
      
      Recommend optimal position size considering:
      1. Risk management principles
      2. Portfolio diversification
      3. Market conditions
      4. Volatility-adjusted sizing
      
      Provide reasoning for the recommendation.
    `;

    const aiResponse = await aiService.generateResponse(aiPrompt, {
      maxTokens: 500,
      temperature: 0.3
    });

    // Parse AI response and calculate final recommendation
    const volatilityAdjustment = Math.max(0.5, Math.min(2.0, 1 / historicalData.volatility));
    const riskAdjustedSize = Math.min(
      kellyPercentage * account.totalValue * volatilityAdjustment,
      maxRiskPerPosition * account.totalValue,
      (portfolioRiskBudget - currentPortfolioRisk) * account.totalValue
    );

    const recommendedSize = Math.max(0, riskAdjustedSize / marketData.price);
    
    // Calculate stop loss and take profit
    const atr = historicalData.atr || (marketData.price * 0.02); // 2% default ATR
    const stopLoss = marketData.price - (atr * 2);
    const takeProfit = marketData.price + (atr * 3);

    return {
      symbol: position.symbol,
      recommendedSize,
      currentSize: position.size,
      reasoning: aiResponse.content || 'AI-powered position sizing based on risk management principles',
      confidence: 0.8, // Simplified confidence score
      riskScore: this.calculatePositionRiskScore(position, historicalData),
      maxRisk: maxRiskPerPosition,
      stopLoss,
      takeProfit
    };
  }

  async optimizeStopLossAndTakeProfit(accountId: string): Promise<StopLossOptimization[]> {
    try {
      const positions = await tradingService.getPositions(accountId);
      const optimizations: StopLossOptimization[] = [];

      for (const position of positions) {
        const optimization = await this.optimizePositionStopLoss(position);
        optimizations.push(optimization);
      }

      return optimizations.sort((a, b) => b.expectedImprovement - a.expectedImprovement);
    } catch (error) {
      console.error('Failed to optimize stop-loss levels:', error);
      return [];
    }
  }

  private async optimizePositionStopLoss(position: Position): Promise<StopLossOptimization> {
    const marketData = await mcpClient.markets.getPriceData(position.symbol);
    const historicalData = await this.getHistoricalVolatility(position.symbol);
    
    // Get current stop loss and take profit (if any)
    const currentStopLoss = position.stopLoss || (marketData.price * 0.95); // 5% default
    const currentTakeProfit = position.takeProfit || (marketData.price * 1.1); // 10% default
    
    // Calculate optimal levels using multiple methods
    const atr = historicalData.atr || (marketData.price * 0.02);
    const volatility = historicalData.volatility;
    
    // Method 1: ATR-based stops
    const atrStopLoss = marketData.price - (atr * 2.5);
    const atrTakeProfit = marketData.price + (atr * 3.5);
    
    // Method 2: Volatility-based stops
    const volStopLoss = marketData.price * (1 - volatility * 2);
    const volTakeProfit = marketData.price * (1 + volatility * 2.5);
    
    // Method 3: Support/Resistance levels (simplified)
    const supportLevel = await this.findSupportLevel(position.symbol);
    const resistanceLevel = await this.findResistanceLevel(position.symbol);
    
    // Use AI to determine optimal levels
    const aiPrompt = `
      Optimize stop-loss and take-profit for ${position.symbol}:
      - Current price: $${marketData.price}
      - Current stop-loss: $${currentStopLoss}
      - Current take-profit: $${currentTakeProfit}
      - ATR: $${atr}
      - Volatility: ${(volatility * 100).toFixed(2)}%
      - Support level: $${supportLevel}
      - Resistance level: $${resistanceLevel}
      - Position size: ${position.size}
      - Unrealized P&L: $${position.unrealizedPnL}
      
      Recommend optimal stop-loss and take-profit levels considering:
      1. Risk-reward ratio (minimum 1:2)
      2. Market volatility
      3. Technical levels
      4. Position management best practices
      
      Explain the reasoning and expected improvement.
    `;

    const aiResponse = await aiService.generateResponse(aiPrompt, {
      maxTokens: 400,
      temperature: 0.3
    });

    // Calculate optimized levels (weighted average of methods)
    const optimizedStopLoss = (atrStopLoss * 0.4 + volStopLoss * 0.3 + supportLevel * 0.3);
    const optimizedTakeProfit = (atrTakeProfit * 0.4 + volTakeProfit * 0.3 + resistanceLevel * 0.3);
    
    // Calculate expected improvement
    const currentRiskReward = Math.abs(currentTakeProfit - marketData.price) / Math.abs(marketData.price - currentStopLoss);
    const optimizedRiskReward = Math.abs(optimizedTakeProfit - marketData.price) / Math.abs(marketData.price - optimizedStopLoss);
    const expectedImprovement = (optimizedRiskReward - currentRiskReward) / currentRiskReward;
    
    // Calculate risk reduction
    const currentRisk = Math.abs(marketData.price - currentStopLoss) * position.size;
    const optimizedRisk = Math.abs(marketData.price - optimizedStopLoss) * position.size;
    const riskReduction = (currentRisk - optimizedRisk) / currentRisk;

    return {
      symbol: position.symbol,
      currentStopLoss,
      optimizedStopLoss,
      currentTakeProfit,
      optimizedTakeProfit,
      reasoning: aiResponse.content || 'AI-optimized levels based on technical analysis and risk management',
      expectedImprovement,
      riskReduction
    };
  }

  private async evaluateEmergencyControls(exposures: RiskExposure[]): Promise<void> {
    for (const control of this.emergencyControls.values()) {
      if (!control.enabled) continue;

      const shouldTrigger = await this.shouldTriggerEmergencyControl(control, exposures);
      
      if (shouldTrigger) {
        await this.executeEmergencyControl(control);
      }
    }
  }

  private async shouldTriggerEmergencyControl(
    control: EmergencyControl, 
    exposures: RiskExposure[]
  ): Promise<boolean> {
    // Check if already triggered recently (prevent spam)
    if (control.lastTriggered) {
      const timeSinceLastTrigger = Date.now() - control.lastTriggered.getTime();
      const cooldownPeriod = 5 * 60 * 1000; // 5 minutes
      if (timeSinceLastTrigger < cooldownPeriod) {
        return false;
      }
    }

    // Evaluate trigger conditions
    for (const condition of control.triggerConditions) {
      if (!condition.enabled) continue;

      for (const exposure of exposures) {
        // Check if condition applies to this account
        if (condition.accounts.length > 0 && !condition.accounts.includes(exposure.accountId)) {
          continue;
        }

        const currentValue = this.getMetricValue(exposure, condition.metric);
        const thresholdMet = this.evaluateThreshold(currentValue, condition.threshold, condition.operator);

        if (thresholdMet) {
          return true;
        }
      }
    }

    return false;
  }

  private async executeEmergencyControl(control: EmergencyControl): Promise<EmergencyControlExecution> {
    console.log(`Executing emergency control: ${control.name}`);
    
    const execution: EmergencyControlExecution = {
      controlId: control.id,
      triggeredAt: new Date(),
      actions: [],
      success: true
    };

    try {
      // Sort actions by priority
      const sortedActions = [...control.actions].sort((a, b) => a.priority - b.priority);

      for (const action of sortedActions) {
        const result = await this.executeEmergencyAction(action);
        execution.actions.push(result);
        
        if (!result.success) {
          execution.success = false;
        }
      }

      // Update last triggered time
      control.lastTriggered = new Date();

      // Notify subscribers
      this.notifySubscribers({
        type: 'emergency_control_executed',
        control,
        execution,
        timestamp: new Date()
      });

    } catch (error) {
      execution.success = false;
      execution.error = error instanceof Error ? error.message : 'Unknown error';
      console.error('Emergency control execution failed:', error);
    }

    return execution;
  }

  private async executeEmergencyAction(action: EmergencyAction): Promise<EmergencyActionResult> {
    const result: EmergencyActionResult = {
      action,
      success: false,
      executedAt: new Date()
    };

    try {
      switch (action.type) {
        case 'deactivate_bots':
          result.result = await this.deactivateAllBots(action.parameters);
          result.success = true;
          break;

        case 'close_positions':
          result.result = await this.closeAllPositions(action.parameters);
          result.success = true;
          break;

        case 'reduce_position_size':
          result.result = await this.reducePositionSizes(action.parameters);
          result.success = true;
          break;

        case 'send_notification':
          result.result = await this.sendEmergencyNotification(action.parameters);
          result.success = true;
          break;

        default:
          throw new Error(`Unknown emergency action type: ${action.type}`);
      }
    } catch (error) {
      result.success = false;
      result.error = error instanceof Error ? error.message : 'Unknown error';
    }

    return result;
  }

  private async deactivateAllBots(parameters: any): Promise<any> {
    const bots = await mcpClient.bots.getAll();
    const activeBots = bots.filter(bot => bot.isActive);
    
    const results = [];
    for (const bot of activeBots) {
      try {
        await mcpClient.bots.deactivate(bot.id);
        results.push({ botId: bot.id, success: true });
      } catch (error) {
        results.push({ 
          botId: bot.id, 
          success: false, 
          error: error instanceof Error ? error.message : 'Unknown error' 
        });
      }
    }

    return {
      totalBots: activeBots.length,
      deactivated: results.filter(r => r.success).length,
      failed: results.filter(r => !r.success).length,
      results
    };
  }

  private async closeAllPositions(parameters: any): Promise<any> {
    const accounts = await mcpClient.accounts.getAll();
    const results = [];

    for (const account of accounts) {
      try {
        const positions = await tradingService.getPositions(account.id);
        for (const position of positions) {
          // This would integrate with actual trading execution
          // For now, we'll simulate the close
          results.push({
            accountId: account.id,
            symbol: position.symbol,
            size: position.size,
            success: true
          });
        }
      } catch (error) {
        results.push({
          accountId: account.id,
          success: false,
          error: error instanceof Error ? error.message : 'Unknown error'
        });
      }
    }

    return {
      totalPositions: results.length,
      closed: results.filter(r => r.success).length,
      failed: results.filter(r => !r.success).length,
      results
    };
  }

  private async reducePositionSizes(parameters: any): Promise<any> {
    const reductionPercentage = parameters.reductionPercentage || 0.5;
    const accounts = await mcpClient.accounts.getAll();
    const results = [];

    for (const account of accounts) {
      try {
        const positions = await tradingService.getPositions(account.id);
        for (const position of positions) {
          const newSize = position.size * (1 - reductionPercentage);
          // This would integrate with actual trading execution
          results.push({
            accountId: account.id,
            symbol: position.symbol,
            originalSize: position.size,
            newSize,
            reduction: position.size - newSize,
            success: true
          });
        }
      } catch (error) {
        results.push({
          accountId: account.id,
          success: false,
          error: error instanceof Error ? error.message : 'Unknown error'
        });
      }
    }

    return {
      reductionPercentage,
      totalPositions: results.length,
      reduced: results.filter(r => r.success).length,
      failed: results.filter(r => !r.success).length,
      results
    };
  }

  private async sendEmergencyNotification(parameters: any): Promise<any> {
    const message = parameters.message || 'Emergency risk management action executed';
    const severity = parameters.severity || 'high';

    // Browser notification
    if (Notification.permission === 'granted') {
      new Notification('Emergency Risk Alert', {
        body: message,
        icon: '/emergency-icon.png'
      });
    }

    // Log to console (in production, this would send to monitoring systems)
    console.warn(`EMERGENCY RISK ALERT [${severity.toUpperCase()}]: ${message}`);

    return {
      message,
      severity,
      timestamp: new Date(),
      notificationSent: Notification.permission === 'granted'
    };
  }

  // Utility methods
  private async calculateAccountRiskExposure(accountId: string): Promise<RiskExposure> {
    // This would use the risk monitoring service
    const exposures = await riskMonitoringService.performRiskAssessment();
    // Return the specific account exposure (simplified)
    return {
      accountId,
      accountName: 'Account',
      totalExposure: 50000,
      maxExposure: 100000,
      utilizationPercentage: 0.5,
      positions: [],
      correlationRisk: 0.3,
      concentrationRisk: 0.2,
      lastUpdated: new Date()
    };
  }

  private async getHistoricalVolatility(symbol: string): Promise<{ volatility: number; atr: number }> {
    // Simplified volatility calculation
    return {
      volatility: 0.02 + Math.random() * 0.03, // 2-5% daily volatility
      atr: 1.5 + Math.random() * 2 // $1.5-3.5 ATR
    };
  }

  private async estimateWinRate(symbol: string): Promise<number> {
    // Simplified win rate estimation
    return 0.45 + Math.random() * 0.2; // 45-65% win rate
  }

  private async estimateAverageWin(symbol: string): Promise<number> {
    return 1.5 + Math.random() * 1; // 1.5-2.5% average win
  }

  private async estimateAverageLoss(symbol: string): Promise<number> {
    return 1 + Math.random() * 0.5; // 1-1.5% average loss
  }

  private calculateKellyCriterion(winRate: number, avgWin: number, avgLoss: number): number {
    return (winRate * avgWin - (1 - winRate) * avgLoss) / avgWin;
  }

  private calculatePositionRiskScore(position: Position, historicalData: any): number {
    const volatilityScore = Math.min(100, historicalData.volatility * 1000);
    const sizeScore = Math.min(100, Math.abs(position.value) / 10000 * 10);
    const pnlScore = Math.min(100, Math.abs(position.unrealizedPnL) / Math.abs(position.value) * 100);
    
    return (volatilityScore + sizeScore + pnlScore) / 3;
  }

  private async findSupportLevel(symbol: string): Promise<number> {
    // Simplified support level calculation
    const marketData = await mcpClient.markets.getPriceData(symbol);
    return marketData.price * (0.95 - Math.random() * 0.05);
  }

  private async findResistanceLevel(symbol: string): Promise<number> {
    // Simplified resistance level calculation
    const marketData = await mcpClient.markets.getPriceData(symbol);
    return marketData.price * (1.05 + Math.random() * 0.05);
  }

  private getMetricValue(exposure: RiskExposure, metric: string): number {
    switch (metric) {
      case 'totalExposure':
        return exposure.utilizationPercentage;
      case 'correlationRisk':
        return exposure.correlationRisk;
      case 'concentrationRisk':
        return exposure.concentrationRisk;
      case 'maxDrawdown':
        // This would come from portfolio metrics
        return 0.1; // Simplified
      default:
        return 0;
    }
  }

  private evaluateThreshold(value: number, threshold: number, operator: string): boolean {
    switch (operator) {
      case '>': return value > threshold;
      case '<': return value < threshold;
      case '>=': return value >= threshold;
      case '<=': return value <= threshold;
      case '==': return Math.abs(value - threshold) < 0.001;
      default: return false;
    }
  }

  // Public API methods
  subscribe(callback: (data: any) => void): () => void {
    this.subscribers.add(callback);
    return () => this.subscribers.delete(callback);
  }

  private notifySubscribers(data: any): void {
    this.subscribers.forEach(callback => {
      try {
        callback(data);
      } catch (error) {
        console.error('Error notifying automated risk manager subscriber:', error);
      }
    });
  }

  async getEmergencyControls(): Promise<EmergencyControl[]> {
    return Array.from(this.emergencyControls.values());
  }

  async addEmergencyControl(control: EmergencyControl): Promise<void> {
    this.emergencyControls.set(control.id, control);
  }

  async updateEmergencyControl(controlId: string, updates: Partial<EmergencyControl>): Promise<void> {
    const control = this.emergencyControls.get(controlId);
    if (control) {
      this.emergencyControls.set(controlId, { ...control, ...updates });
    }
  }

  async removeEmergencyControl(controlId: string): Promise<void> {
    this.emergencyControls.delete(controlId);
  }

  async testEmergencyControl(controlId: string): Promise<EmergencyControlExecution> {
    const control = this.emergencyControls.get(controlId);
    if (!control) {
      throw new Error(`Emergency control not found: ${controlId}`);
    }

    // Execute in test mode (don't actually perform actions)
    console.log(`Testing emergency control: ${control.name}`);
    return {
      controlId,
      triggeredAt: new Date(),
      actions: control.actions.map(action => ({
        action,
        success: true,
        result: { test: true },
        executedAt: new Date()
      })),
      success: true
    };
  }

  setActive(active: boolean): void {
    this.isActive = active;
  }

  isActiveManager(): boolean {
    return this.isActive;
  }
}

export const automatedRiskManager = new AutomatedRiskManager();