// Central type exports
export * from './trading'
export * from './ai'
export * from './workflow'

// Export strategy types explicitly to avoid conflicts
export type {
  HaasScriptStrategy,
  StrategyParameter as HaasScriptParameter,
  ValidationError as HaasScriptValidationError,
  PerformanceMetrics as HaasScriptPerformanceMetrics,
  DragDropComponent,
  ComponentParameter,
  StrategyTemplate,
  CodeCompletion,
  SyntaxHighlightRule,
  StrategyValidationResult
} from './strategy'

// Export translation types
export type {
  ExternalStrategy,
  ExternalParameter,
  TranslationResult,
  TranslationWarning,
  TranslationError,
  OptimizationSuggestion,
  TranslationStep,
  StrategyTranslationConfig,
  TranslationTemplate,
  MappingRule,
  PatternMapping,
  ParameterMapping,
  ValidationRule
} from './translation'

// Export version control types
export type {
  StrategyVersion,
  VersionChange,
  PerformanceSnapshot,
  StrategyComparison,
  StrategyComparisonItem,
  ComparisonMetrics,
  ComparisonInsight,
  ComparisonRecommendation,
  RecommendationAction,
  DiffResult,
  DiffLine,
  MergeRequest,
  MergeConflict,
  MergeComment,
  VersionControlConfig,
  StrategyBranch
} from './versionControl'

// Export UI types without Position to avoid conflict with trading Position
export type { 
  UIContext,
  UserPreferences,
  CommandResult,
  Layout,
  ThemeConfig,
  NotificationSettings,
  DashboardSettings,
  AccessibilitySettings,
  RiskTolerance,
  Suggestion,
  VoiceCommand,
} from './ui'

// Export generative UI types
export type {
  ChartType,
  ChartCustomization
} from './ui'