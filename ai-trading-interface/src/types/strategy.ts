export interface HaasScriptStrategy {
  id: string;
  name: string;
  description: string;
  code: string;
  parameters: StrategyParameter[];
  version: number;
  createdAt: Date;
  updatedAt: Date;
  author: string;
  tags: string[];
  performance?: PerformanceMetrics;
  validationErrors: ValidationError[];
  isValid: boolean;
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

export interface ValidationError {
  line: number;
  column: number;
  message: string;
  severity: 'error' | 'warning' | 'info';
  code: string;
}

export interface PerformanceMetrics {
  totalReturn: number;
  sharpeRatio: number;
  maxDrawdown: number;
  winRate: number;
  profitFactor: number;
  totalTrades: number;
  avgTradeReturn: number;
  volatility: number;
}

export interface DragDropComponent {
  id: string;
  type: 'indicator' | 'condition' | 'action' | 'variable';
  name: string;
  description: string;
  category: string;
  icon: string;
  parameters: ComponentParameter[];
  codeTemplate: string;
  dependencies?: string[];
}

export interface ComponentParameter {
  name: string;
  type: 'number' | 'string' | 'boolean' | 'select';
  defaultValue: any;
  required: boolean;
  description: string;
  validation?: {
    min?: number;
    max?: number;
    pattern?: string;
    options?: string[];
  };
}

export interface StrategyTemplate {
  id: string;
  name: string;
  description: string;
  category: string;
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  code: string;
  parameters: StrategyParameter[];
  tags: string[];
  estimatedPerformance?: PerformanceMetrics;
}

export interface CodeCompletion {
  label: string;
  kind: 'function' | 'variable' | 'keyword' | 'snippet';
  insertText: string;
  documentation: string;
  detail?: string;
}

export interface SyntaxHighlightRule {
  token: string;
  foreground: string;
  fontStyle?: 'bold' | 'italic' | 'underline';
}

export interface StrategyValidationResult {
  isValid: boolean;
  errors: ValidationError[];
  warnings: ValidationError[];
  suggestions: string[];
  performance?: {
    complexity: number;
    estimatedExecutionTime: number;
    memoryUsage: number;
  };
}