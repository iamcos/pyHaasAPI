export interface RiskExposure {
  accountId: string;
  accountName: string;
  totalExposure: number;
  maxExposure: number;
  utilizationPercentage: number;
  positions: PositionRisk[];
  correlationRisk: number;
  concentrationRisk: number;
  lastUpdated: Date;
}

export interface PositionRisk {
  symbol: string;
  size: number;
  value: number;
  unrealizedPnL: number;
  riskScore: number;
  volatility: number;
  beta: number;
  var95: number; // Value at Risk 95%
  expectedShortfall: number;
  maxDrawdown: number;
}

export interface RiskThreshold {
  id: string;
  name: string;
  type: 'portfolio' | 'position' | 'correlation' | 'concentration';
  metric: string;
  threshold: number;
  operator: '>' | '<' | '>=' | '<=' | '==';
  severity: 'low' | 'medium' | 'high' | 'critical';
  enabled: boolean;
  accounts: string[]; // Empty array means all accounts
}

export interface RiskAlert {
  id: string;
  thresholdId: string;
  accountId: string;
  symbol?: string;
  message: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  currentValue: number;
  thresholdValue: number;
  timestamp: Date;
  acknowledged: boolean;
  resolvedAt?: Date;
}

export interface PortfolioCorrelation {
  symbol1: string;
  symbol2: string;
  correlation: number;
  pValue: number;
  significance: 'low' | 'medium' | 'high';
  timeframe: string;
  lastUpdated: Date;
}

export interface RiskMetrics {
  totalPortfolioValue: number;
  totalExposure: number;
  maxDrawdown: number;
  sharpeRatio: number;
  sortinoRatio: number;
  var95: number;
  expectedShortfall: number;
  beta: number;
  alpha: number;
  volatility: number;
  correlationRisk: number;
  concentrationRisk: number;
  liquidityRisk: number;
}

export interface RiskVisualizationData {
  exposureByAccount: { account: string; exposure: number; percentage: number }[];
  exposureByAsset: { asset: string; exposure: number; percentage: number }[];
  riskOverTime: { timestamp: Date; var95: number; exposure: number }[];
  correlationMatrix: { asset1: string; asset2: string; correlation: number }[];
  alertsOverTime: { timestamp: Date; severity: string; count: number }[];
}

export interface EmergencyControl {
  id: string;
  name: string;
  description: string;
  type: 'stop_all_bots' | 'close_all_positions' | 'reduce_exposure' | 'custom';
  enabled: boolean;
  triggerConditions: RiskThreshold[];
  actions: EmergencyAction[];
  lastTriggered?: Date;
}

export interface EmergencyAction {
  type: 'deactivate_bots' | 'close_positions' | 'send_notification' | 'reduce_position_size';
  parameters: Record<string, any>;
  priority: number;
}

export interface RiskConfiguration {
  thresholds: RiskThreshold[];
  emergencyControls: EmergencyControl[];
  monitoringInterval: number; // milliseconds
  alertRetentionDays: number;
  correlationLookbackDays: number;
  enableRealTimeMonitoring: boolean;
  enableProactiveAlerts: boolean;
}