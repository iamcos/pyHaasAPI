import { 
  RiskExposure, 
  PositionRisk, 
  RiskThreshold, 
  RiskAlert, 
  PortfolioCorrelation, 
  RiskMetrics,
  RiskVisualizationData,
  RiskConfiguration
} from '../types/risk';
import { Account, Position, MarketData } from '../types/trading';
import { mcpClient } from './mcpClient';
import { tradingService } from './tradingService';

class RiskMonitoringService {
  private monitoringInterval: NodeJS.Timeout | null = null;
  private riskConfiguration: RiskConfiguration;
  private activeAlerts: Map<string, RiskAlert> = new Map();
  private correlationCache: Map<string, PortfolioCorrelation[]> = new Map();
  private subscribers: Set<(data: any) => void> = new Set();

  constructor() {
    this.riskConfiguration = this.getDefaultConfiguration();
    this.startRealTimeMonitoring();
  }

  private getDefaultConfiguration(): RiskConfiguration {
    return {
      thresholds: [
        {
          id: 'portfolio-exposure-high',
          name: 'High Portfolio Exposure',
          type: 'portfolio',
          metric: 'totalExposure',
          threshold: 0.8,
          operator: '>',
          severity: 'high',
          enabled: true,
          accounts: []
        },
        {
          id: 'position-concentration-critical',
          name: 'Position Concentration Risk',
          type: 'concentration',
          metric: 'concentrationRisk',
          threshold: 0.3,
          operator: '>',
          severity: 'critical',
          enabled: true,
          accounts: []
        },
        {
          id: 'correlation-risk-medium',
          name: 'High Correlation Risk',
          type: 'correlation',
          metric: 'correlationRisk',
          threshold: 0.7,
          operator: '>',
          severity: 'medium',
          enabled: true,
          accounts: []
        }
      ],
      emergencyControls: [],
      monitoringInterval: 5000, // 5 seconds
      alertRetentionDays: 30,
      correlationLookbackDays: 30,
      enableRealTimeMonitoring: true,
      enableProactiveAlerts: true
    };
  }

  async startRealTimeMonitoring(): Promise<void> {
    if (!this.riskConfiguration.enableRealTimeMonitoring) return;

    if (this.monitoringInterval) {
      clearInterval(this.monitoringInterval);
    }

    this.monitoringInterval = setInterval(async () => {
      try {
        await this.performRiskAssessment();
      } catch (error) {
        console.error('Risk monitoring error:', error);
      }
    }, this.riskConfiguration.monitoringInterval);
  }

  stopRealTimeMonitoring(): void {
    if (this.monitoringInterval) {
      clearInterval(this.monitoringInterval);
      this.monitoringInterval = null;
    }
  }

  async performRiskAssessment(): Promise<void> {
    const accounts = await mcpClient.accounts.getAll();
    const riskExposures: RiskExposure[] = [];

    for (const account of accounts) {
      const exposure = await this.calculateAccountRiskExposure(account);
      riskExposures.push(exposure);
      
      // Check thresholds for this account
      await this.checkRiskThresholds(exposure);
    }

    // Calculate portfolio-wide correlations
    await this.updatePortfolioCorrelations(riskExposures);

    // Notify subscribers
    this.notifySubscribers({
      type: 'risk_update',
      exposures: riskExposures,
      alerts: Array.from(this.activeAlerts.values()),
      timestamp: new Date()
    });
  }

  private async calculateAccountRiskExposure(account: Account): Promise<RiskExposure> {
    const balance = await mcpClient.accounts.getBalance(account.id);
    const positions = await this.getAccountPositions(account.id);
    
    const positionRisks: PositionRisk[] = [];
    let totalExposure = 0;
    let concentrationRisk = 0;

    for (const position of positions) {
      const positionRisk = await this.calculatePositionRisk(position);
      positionRisks.push(positionRisk);
      totalExposure += Math.abs(positionRisk.value);
    }

    // Calculate concentration risk (largest position as % of portfolio)
    if (positionRisks.length > 0) {
      const maxPosition = Math.max(...positionRisks.map(p => Math.abs(p.value)));
      concentrationRisk = balance.totalValue > 0 ? maxPosition / balance.totalValue : 0;
    }

    // Calculate correlation risk
    const correlationRisk = await this.calculateCorrelationRisk(positionRisks);

    return {
      accountId: account.id,
      accountName: account.name,
      totalExposure,
      maxExposure: balance.totalValue * 0.95, // 95% max exposure
      utilizationPercentage: balance.totalValue > 0 ? totalExposure / balance.totalValue : 0,
      positions: positionRisks,
      correlationRisk,
      concentrationRisk,
      lastUpdated: new Date()
    };
  }

  private async calculatePositionRisk(position: Position): Promise<PositionRisk> {
    const marketData = await this.getMarketData(position.symbol);
    const historicalData = await this.getHistoricalData(position.symbol, 30); // 30 days
    
    // Calculate volatility
    const returns = this.calculateReturns(historicalData);
    const volatility = this.calculateVolatility(returns);
    
    // Calculate VaR (95% confidence)
    const var95 = this.calculateVaR(returns, 0.95) * Math.abs(position.value);
    
    // Calculate Expected Shortfall
    const expectedShortfall = this.calculateExpectedShortfall(returns, 0.95) * Math.abs(position.value);
    
    // Calculate beta (simplified - using market correlation)
    const beta = await this.calculateBeta(position.symbol);
    
    // Risk score (0-100)
    const riskScore = Math.min(100, (volatility * 100) + (Math.abs(position.unrealizedPnL) / Math.abs(position.value) * 50));

    return {
      symbol: position.symbol,
      size: position.size,
      value: position.value,
      unrealizedPnL: position.unrealizedPnL,
      riskScore,
      volatility,
      beta,
      var95,
      expectedShortfall,
      maxDrawdown: this.calculateMaxDrawdown(historicalData)
    };
  }

  private async checkRiskThresholds(exposure: RiskExposure): Promise<void> {
    for (const threshold of this.riskConfiguration.thresholds) {
      if (!threshold.enabled) continue;
      
      // Check if threshold applies to this account
      if (threshold.accounts.length > 0 && !threshold.accounts.includes(exposure.accountId)) {
        continue;
      }

      const currentValue = this.getMetricValue(exposure, threshold.metric);
      const thresholdMet = this.evaluateThreshold(currentValue, threshold.threshold, threshold.operator);

      if (thresholdMet) {
        await this.createRiskAlert(threshold, exposure, currentValue);
      } else {
        // Remove alert if threshold is no longer met
        this.resolveRiskAlert(threshold.id, exposure.accountId);
      }
    }
  }

  private getMetricValue(exposure: RiskExposure, metric: string): number {
    switch (metric) {
      case 'totalExposure':
        return exposure.utilizationPercentage;
      case 'correlationRisk':
        return exposure.correlationRisk;
      case 'concentrationRisk':
        return exposure.concentrationRisk;
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

  private async createRiskAlert(
    threshold: RiskThreshold, 
    exposure: RiskExposure, 
    currentValue: number
  ): Promise<void> {
    const alertId = `${threshold.id}-${exposure.accountId}`;
    
    if (this.activeAlerts.has(alertId)) return; // Alert already exists

    const alert: RiskAlert = {
      id: alertId,
      thresholdId: threshold.id,
      accountId: exposure.accountId,
      message: `${threshold.name}: ${(currentValue * 100).toFixed(2)}% exceeds threshold of ${(threshold.threshold * 100).toFixed(2)}%`,
      severity: threshold.severity,
      currentValue,
      thresholdValue: threshold.threshold,
      timestamp: new Date(),
      acknowledged: false
    };

    this.activeAlerts.set(alertId, alert);
    
    // Notify subscribers immediately for critical alerts
    if (threshold.severity === 'critical') {
      this.notifySubscribers({
        type: 'critical_alert',
        alert,
        timestamp: new Date()
      });
    }
  }

  private resolveRiskAlert(thresholdId: string, accountId: string): void {
    const alertId = `${thresholdId}-${accountId}`;
    const alert = this.activeAlerts.get(alertId);
    
    if (alert) {
      alert.resolvedAt = new Date();
      this.activeAlerts.delete(alertId);
    }
  }

  async getPortfolioCorrelations(): Promise<PortfolioCorrelation[]> {
    const cacheKey = 'portfolio_correlations';
    const cached = this.correlationCache.get(cacheKey);
    
    if (cached && this.isCacheValid(cached[0]?.lastUpdated)) {
      return cached;
    }

    const correlations = await this.calculatePortfolioCorrelations();
    this.correlationCache.set(cacheKey, correlations);
    return correlations;
  }

  private async calculatePortfolioCorrelations(): Promise<PortfolioCorrelation[]> {
    const accounts = await mcpClient.accounts.getAll();
    const allSymbols = new Set<string>();
    
    // Collect all unique symbols across accounts
    for (const account of accounts) {
      const positions = await this.getAccountPositions(account.id);
      positions.forEach(p => allSymbols.add(p.symbol));
    }

    const symbols = Array.from(allSymbols);
    const correlations: PortfolioCorrelation[] = [];

    // Calculate pairwise correlations
    for (let i = 0; i < symbols.length; i++) {
      for (let j = i + 1; j < symbols.length; j++) {
        const correlation = await this.calculatePairwiseCorrelation(symbols[i], symbols[j]);
        correlations.push(correlation);
      }
    }

    return correlations;
  }

  async getRiskVisualizationData(): Promise<RiskVisualizationData> {
    const accounts = await mcpClient.accounts.getAll();
    const exposureByAccount: { account: string; exposure: number; percentage: number }[] = [];
    const exposureByAsset: Map<string, number> = new Map();
    let totalExposure = 0;

    for (const account of accounts) {
      const exposure = await this.calculateAccountRiskExposure(account);
      exposureByAccount.push({
        account: account.name,
        exposure: exposure.totalExposure,
        percentage: exposure.utilizationPercentage * 100
      });
      totalExposure += exposure.totalExposure;

      // Aggregate by asset
      exposure.positions.forEach(pos => {
        const current = exposureByAsset.get(pos.symbol) || 0;
        exposureByAsset.set(pos.symbol, current + Math.abs(pos.value));
      });
    }

    const exposureByAssetArray = Array.from(exposureByAsset.entries()).map(([asset, exposure]) => ({
      asset,
      exposure,
      percentage: totalExposure > 0 ? (exposure / totalExposure) * 100 : 0
    }));

    // Get historical risk data (simplified)
    const riskOverTime = await this.getRiskHistoricalData();
    
    // Get correlation matrix
    const correlations = await this.getPortfolioCorrelations();
    const correlationMatrix = correlations.map(c => ({
      asset1: c.symbol1,
      asset2: c.symbol2,
      correlation: c.correlation
    }));

    // Get alerts over time
    const alertsOverTime = await this.getAlertsHistoricalData();

    return {
      exposureByAccount,
      exposureByAsset: exposureByAssetArray,
      riskOverTime,
      correlationMatrix,
      alertsOverTime
    };
  }

  // Utility methods
  private async getAccountPositions(accountId: string): Promise<Position[]> {
    // This would integrate with the actual trading service
    return tradingService.getPositions(accountId);
  }

  private async getMarketData(symbol: string): Promise<MarketData> {
    return mcpClient.markets.getPriceData(symbol);
  }

  private async getHistoricalData(symbol: string, days: number): Promise<number[]> {
    // Simplified - would get actual historical price data
    return Array.from({ length: days }, () => Math.random() * 100);
  }

  private calculateReturns(prices: number[]): number[] {
    const returns: number[] = [];
    for (let i = 1; i < prices.length; i++) {
      returns.push((prices[i] - prices[i - 1]) / prices[i - 1]);
    }
    return returns;
  }

  private calculateVolatility(returns: number[]): number {
    const mean = returns.reduce((sum, r) => sum + r, 0) / returns.length;
    const variance = returns.reduce((sum, r) => sum + Math.pow(r - mean, 2), 0) / returns.length;
    return Math.sqrt(variance * 252); // Annualized
  }

  private calculateVaR(returns: number[], confidence: number): number {
    const sorted = [...returns].sort((a, b) => a - b);
    const index = Math.floor((1 - confidence) * sorted.length);
    return sorted[index] || 0;
  }

  private calculateExpectedShortfall(returns: number[], confidence: number): number {
    const var95 = this.calculateVaR(returns, confidence);
    const tailReturns = returns.filter(r => r <= var95);
    return tailReturns.length > 0 ? tailReturns.reduce((sum, r) => sum + r, 0) / tailReturns.length : 0;
  }

  private calculateMaxDrawdown(prices: number[]): number {
    let maxDrawdown = 0;
    let peak = prices[0];
    
    for (const price of prices) {
      if (price > peak) {
        peak = price;
      }
      const drawdown = (peak - price) / peak;
      maxDrawdown = Math.max(maxDrawdown, drawdown);
    }
    
    return maxDrawdown;
  }

  private async calculateBeta(symbol: string): Promise<number> {
    // Simplified beta calculation - would use actual market data
    return 1.0 + (Math.random() - 0.5) * 0.5;
  }

  private async calculateCorrelationRisk(positions: PositionRisk[]): Promise<number> {
    if (positions.length < 2) return 0;
    
    // Simplified correlation risk calculation
    // In reality, this would calculate the weighted average correlation
    return Math.random() * 0.8; // Placeholder
  }

  private async calculatePairwiseCorrelation(symbol1: string, symbol2: string): Promise<PortfolioCorrelation> {
    // Simplified correlation calculation
    const correlation = (Math.random() - 0.5) * 2; // -1 to 1
    
    return {
      symbol1,
      symbol2,
      correlation,
      pValue: Math.random() * 0.1, // Simplified p-value
      significance: Math.abs(correlation) > 0.7 ? 'high' : Math.abs(correlation) > 0.3 ? 'medium' : 'low',
      timeframe: '30d',
      lastUpdated: new Date()
    };
  }

  private async updatePortfolioCorrelations(exposures: RiskExposure[]): Promise<void> {
    // Update correlation cache
    await this.getPortfolioCorrelations();
  }

  private isCacheValid(lastUpdated?: Date): boolean {
    if (!lastUpdated) return false;
    const maxAge = 5 * 60 * 1000; // 5 minutes
    return Date.now() - lastUpdated.getTime() < maxAge;
  }

  private async getRiskHistoricalData(): Promise<{ timestamp: Date; var95: number; exposure: number }[]> {
    // Simplified historical data - would come from actual storage
    return Array.from({ length: 30 }, (_, i) => ({
      timestamp: new Date(Date.now() - (29 - i) * 24 * 60 * 60 * 1000),
      var95: Math.random() * 10000,
      exposure: Math.random() * 100000
    }));
  }

  private async getAlertsHistoricalData(): Promise<{ timestamp: Date; severity: string; count: number }[]> {
    // Simplified alerts data
    return Array.from({ length: 7 }, (_, i) => ({
      timestamp: new Date(Date.now() - (6 - i) * 24 * 60 * 60 * 1000),
      severity: ['low', 'medium', 'high', 'critical'][Math.floor(Math.random() * 4)],
      count: Math.floor(Math.random() * 10)
    }));
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
        console.error('Error notifying risk monitoring subscriber:', error);
      }
    });
  }

  async acknowledgeAlert(alertId: string): Promise<void> {
    const alert = this.activeAlerts.get(alertId);
    if (alert) {
      alert.acknowledged = true;
    }
  }

  async getActiveAlerts(): Promise<RiskAlert[]> {
    return Array.from(this.activeAlerts.values());
  }

  async getRiskConfiguration(): Promise<RiskConfiguration> {
    return this.riskConfiguration;
  }

  async updateRiskConfiguration(config: Partial<RiskConfiguration>): Promise<void> {
    this.riskConfiguration = { ...this.riskConfiguration, ...config };
    
    if (config.monitoringInterval) {
      this.startRealTimeMonitoring();
    }
  }

  async getRiskMetrics(): Promise<RiskMetrics> {
    const accounts = await mcpClient.accounts.getAll();
    let totalPortfolioValue = 0;
    let totalExposure = 0;
    const allPositions: PositionRisk[] = [];

    for (const account of accounts) {
      const balance = await mcpClient.accounts.getBalance(account.id);
      const exposure = await this.calculateAccountRiskExposure(account);
      
      totalPortfolioValue += balance.totalValue;
      totalExposure += exposure.totalExposure;
      allPositions.push(...exposure.positions);
    }

    // Calculate portfolio-wide metrics
    const var95 = allPositions.reduce((sum, pos) => sum + pos.var95, 0);
    const expectedShortfall = allPositions.reduce((sum, pos) => sum + pos.expectedShortfall, 0);
    const maxDrawdown = Math.max(...allPositions.map(pos => pos.maxDrawdown));
    const volatility = Math.sqrt(allPositions.reduce((sum, pos) => sum + Math.pow(pos.volatility, 2), 0) / allPositions.length);

    return {
      totalPortfolioValue,
      totalExposure,
      maxDrawdown,
      sharpeRatio: 1.2, // Simplified
      sortinoRatio: 1.5, // Simplified
      var95,
      expectedShortfall,
      beta: allPositions.reduce((sum, pos) => sum + pos.beta, 0) / allPositions.length,
      alpha: 0.05, // Simplified
      volatility,
      correlationRisk: 0.6, // Simplified
      concentrationRisk: 0.3, // Simplified
      liquidityRisk: 0.2 // Simplified
    };
  }
}

export const riskMonitoringService = new RiskMonitoringService();