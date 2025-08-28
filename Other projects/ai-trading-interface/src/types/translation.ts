export interface ExternalStrategy {
  id: string;
  name: string;
  description: string;
  sourceFormat: 'pine_script' | 'mql4' | 'mql5' | 'ninjatrader' | 'tradingview' | 'custom';
  sourceCode: string;
  metadata: {
    author?: string;
    version?: string;
    timeframe?: string;
    markets?: string[];
    indicators?: string[];
    parameters?: ExternalParameter[];
  };
  createdAt: Date;
}

export interface ExternalParameter {
  name: string;
  type: 'input' | 'variable' | 'constant';
  dataType: 'int' | 'float' | 'bool' | 'string' | 'color';
  value: any;
  defaultValue: any;
  description?: string;
  min?: number;
  max?: number;
  step?: number;
  options?: string[];
}

export interface TranslationResult {
  success: boolean;
  haasScriptCode: string;
  translatedParameters: HaasScriptParameter[];
  warnings: TranslationWarning[];
  errors: TranslationError[];
  confidence: number;
  optimizationSuggestions: OptimizationSuggestion[];
  chainOfThought: TranslationStep[];
}

export interface TranslationWarning {
  line?: number;
  column?: number;
  message: string;
  severity: 'low' | 'medium' | 'high';
  category: 'syntax' | 'logic' | 'performance' | 'compatibility';
  originalCode?: string;
  suggestedFix?: string;
}

export interface TranslationError {
  line?: number;
  column?: number;
  message: string;
  category: 'unsupported_feature' | 'syntax_error' | 'logic_error' | 'missing_dependency';
  originalCode: string;
  possibleSolutions: string[];
}

export interface OptimizationSuggestion {
  type: 'performance' | 'readability' | 'best_practice' | 'haas_specific';
  title: string;
  description: string;
  originalCode: string;
  optimizedCode: string;
  impact: 'low' | 'medium' | 'high';
  effort: 'easy' | 'moderate' | 'complex';
}

export interface TranslationStep {
  step: number;
  phase: 'parsing' | 'analysis' | 'mapping' | 'generation' | 'optimization' | 'validation';
  description: string;
  input?: string;
  output?: string;
  reasoning: string;
  confidence: number;
  alternatives?: string[];
  timestamp: Date;
}

export interface HaasScriptParameter {
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

export interface StrategyTranslationConfig {
  sourceFormat: ExternalStrategy['sourceFormat'];
  targetOptimizations: ('performance' | 'readability' | 'haas_best_practices')[];
  preserveComments: boolean;
  generateDocumentation: boolean;
  includeOriginalCode: boolean;
  validationLevel: 'basic' | 'comprehensive' | 'strict';
  aiAssistance: boolean;
}

export interface TranslationTemplate {
  id: string;
  name: string;
  sourceFormat: ExternalStrategy['sourceFormat'];
  description: string;
  mappingRules: MappingRule[];
  commonPatterns: PatternMapping[];
  unsupportedFeatures: string[];
  limitations: string[];
}

export interface MappingRule {
  sourcePattern: string;
  targetPattern: string;
  description: string;
  examples: {
    source: string;
    target: string;
  }[];
  conditions?: string[];
  priority: number;
}

export interface PatternMapping {
  name: string;
  description: string;
  sourcePattern: RegExp;
  targetTemplate: string;
  parameterMappings: ParameterMapping[];
  validationRules?: ValidationRule[];
}

export interface ParameterMapping {
  sourceName: string;
  targetName: string;
  transformation?: (value: any) => any;
  validation?: (value: any) => boolean;
  defaultValue?: any;
}

export interface ValidationRule {
  type: 'syntax' | 'logic' | 'performance';
  rule: string;
  message: string;
  severity: 'error' | 'warning' | 'info';
}