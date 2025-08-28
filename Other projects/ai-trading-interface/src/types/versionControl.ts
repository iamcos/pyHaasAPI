export interface StrategyVersion {
  id: string;
  strategyId: string;
  version: number;
  name: string;
  description: string;
  code: string;
  parameters: StrategyParameter[];
  createdAt: Date;
  author: string;
  commitMessage: string;
  tags: string[];
  parentVersionId?: string;
  branchName: string;
  isActive: boolean;
  performance?: PerformanceSnapshot;
  changes: VersionChange[];
}

export interface VersionChange {
  type: 'addition' | 'deletion' | 'modification';
  lineNumber: number;
  oldContent?: string;
  newContent?: string;
  description: string;
  impact: 'low' | 'medium' | 'high';
}

export interface PerformanceSnapshot {
  totalReturn: number;
  sharpeRatio: number;
  maxDrawdown: number;
  winRate: number;
  profitFactor: number;
  totalTrades: number;
  avgTradeReturn: number;
  volatility: number;
  backtestPeriod: {
    start: Date;
    end: Date;
  };
  marketConditions: string[];
}

export interface StrategyComparison {
  id: string;
  name: string;
  strategies: StrategyComparisonItem[];
  createdAt: Date;
  comparisonType: 'version' | 'strategy' | 'performance';
  metrics: ComparisonMetrics;
  insights: ComparisonInsight[];
  recommendations: ComparisonRecommendation[];
}

export interface StrategyComparisonItem {
  strategyId: string;
  versionId?: string;
  name: string;
  version: number;
  code: string;
  parameters: StrategyParameter[];
  performance?: PerformanceSnapshot;
  metadata: {
    author: string;
    createdAt: Date;
    tags: string[];
    branchName: string;
  };
}

export interface ComparisonMetrics {
  codeComplexity: {
    [strategyId: string]: number;
  };
  performanceScore: {
    [strategyId: string]: number;
  };
  riskScore: {
    [strategyId: string]: number;
  };
  maintainabilityScore: {
    [strategyId: string]: number;
  };
  similarity: {
    [key: string]: number; // key format: "strategyId1_vs_strategyId2"
  };
}

export interface ComparisonInsight {
  type: 'performance' | 'risk' | 'code_quality' | 'parameter' | 'logic';
  title: string;
  description: string;
  affectedStrategies: string[];
  severity: 'info' | 'warning' | 'critical';
  recommendation?: string;
  data?: any;
}

export interface ComparisonRecommendation {
  type: 'merge' | 'optimize' | 'rollback' | 'branch' | 'archive';
  title: string;
  description: string;
  targetStrategy: string;
  sourceStrategy?: string;
  confidence: number;
  impact: 'low' | 'medium' | 'high';
  effort: 'easy' | 'moderate' | 'complex';
  actions: RecommendationAction[];
}

export interface RecommendationAction {
  type: 'code_change' | 'parameter_update' | 'test_run' | 'deploy';
  description: string;
  automated: boolean;
  execute?: () => Promise<void>;
}

export interface DiffResult {
  additions: DiffLine[];
  deletions: DiffLine[];
  modifications: DiffLine[];
  unchanged: DiffLine[];
  summary: {
    totalChanges: number;
    linesAdded: number;
    linesDeleted: number;
    linesModified: number;
    complexity: 'low' | 'medium' | 'high';
  };
}

export interface DiffLine {
  lineNumber: number;
  content: string;
  type: 'addition' | 'deletion' | 'modification' | 'unchanged';
  oldLineNumber?: number;
  newLineNumber?: number;
  context?: string;
}

export interface MergeRequest {
  id: string;
  title: string;
  description: string;
  sourceStrategyId: string;
  sourceVersionId: string;
  targetStrategyId: string;
  targetVersionId: string;
  author: string;
  createdAt: Date;
  status: 'pending' | 'approved' | 'rejected' | 'merged';
  conflicts: MergeConflict[];
  reviewers: string[];
  comments: MergeComment[];
  autoMerge: boolean;
}

export interface MergeConflict {
  lineNumber: number;
  sourceContent: string;
  targetContent: string;
  resolution?: 'source' | 'target' | 'custom';
  customContent?: string;
  resolved: boolean;
}

export interface MergeComment {
  id: string;
  author: string;
  content: string;
  lineNumber?: number;
  createdAt: Date;
  type: 'general' | 'suggestion' | 'concern' | 'approval';
}

export interface VersionControlConfig {
  autoVersioning: boolean;
  maxVersionsPerStrategy: number;
  autoCleanup: boolean;
  cleanupThreshold: number; // days
  requireCommitMessages: boolean;
  enableBranching: boolean;
  defaultBranch: string;
  enableMergeRequests: boolean;
  autoBackup: boolean;
  backupInterval: number; // hours
}

export interface StrategyBranch {
  name: string;
  strategyId: string;
  baseVersionId: string;
  headVersionId: string;
  createdAt: Date;
  author: string;
  description: string;
  isActive: boolean;
  isProtected: boolean;
  mergedAt?: Date;
  mergedBy?: string;
}

export interface StrategyParameter {
  id: string;
  name: string;
  type: 'number' | 'string' | 'boolean' | 'select';
  value: any;
  defaultValue: any;
  min?: number;
  max?: number;
  step?: number;
  options?: string[];
  description: string;
  category: string;
}