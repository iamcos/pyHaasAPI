// Workflow Management Types
export interface WorkflowExecution {
  id: string
  type: 'chain_of_thought_optimization'
  templateId?: string
  status: 'running' | 'paused' | 'completed' | 'failed'
  currentStep: number
  totalSteps: number
  steps: WorkflowStep[]
  results: StepResult[]
  resumeData?: ResumeData
  chainOfThought: ChainOfThoughtStep[]
  startTime: Date
  endTime?: Date
  estimatedCompletion?: Date
}

export interface WorkflowTemplate {
  id: string
  name: string
  description: string
  steps: WorkflowStepTemplate[]
  estimatedDuration: number
  complexity: 'simple' | 'moderate' | 'complex' | 'advanced'
  category: 'optimization' | 'analysis' | 'validation' | 'custom'
  tags: string[]
  createdAt: Date
  updatedAt: Date
}

export interface WorkflowStepTemplate {
  id: string
  name: string
  type: 'backtest' | 'analysis' | 'optimization' | 'validation' | 'custom'
  description: string
  parameters: StepParameters
  dependencies: string[] // IDs of prerequisite steps
  estimatedDuration: number
  optional: boolean
  retryable: boolean
}

export interface WorkflowStep {
  id: string
  templateId: string
  name: string
  type: 'backtest' | 'analysis' | 'optimization' | 'validation' | 'custom'
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped'
  parameters: StepParameters
  startTime?: Date
  endTime?: Date
  progress: number
  result?: StepResult
  error?: WorkflowError
  chainOfThought: ChainOfThoughtStep[]
}

export interface StepParameters {
  [key: string]: any
}

export interface StepResult {
  stepId: string
  success: boolean
  data: any
  metrics: StepMetrics
  artifacts: Artifact[]
  chainOfThought: ChainOfThoughtStep[]
  timestamp: Date
}

export interface StepMetrics {
  duration: number
  resourceUsage: ResourceUsage
  quality: QualityMetrics
}

export interface ResourceUsage {
  cpu: number
  memory: number
  network: number
  storage: number
}

export interface QualityMetrics {
  accuracy: number
  completeness: number
  reliability: number
}

export interface Artifact {
  id: string
  type: 'data' | 'chart' | 'report' | 'model' | 'script'
  name: string
  description: string
  path: string
  size: number
  createdAt: Date
}

export interface ResumeData {
  checkpointId: string
  stepStates: StepState[]
  contextData: any
  timestamp: Date
}

export interface StepState {
  stepId: string
  status: string
  progress: number
  data: any
}

export interface WorkflowError {
  code: string
  message: string
  details: any
  recoverable: boolean
  suggestions: string[]
  timestamp: Date
}

export interface WorkflowConfig {
  templateId?: string // Use predefined template
  customSteps?: WorkflowStepTemplate[] // Or define custom steps
  labId: string
  parameters: OptimizationParameters
  persona: Persona
  resumable: boolean
  priority: 'low' | 'normal' | 'high'
  timeout?: number
  retryPolicy?: RetryPolicy
}

export interface OptimizationParameters {
  timeframes: string[]
  numericalParams: NumericalParameter[]
  structuralParams: StructuralParameter[]
  constraints: OptimizationConstraint[]
}

export interface NumericalParameter {
  name: string
  min: number
  max: number
  step: number
  current: number
  type: 'integer' | 'float'
}

export interface StructuralParameter {
  name: string
  value: any
  type: 'indicator' | 'method' | 'boolean'
  fixed: boolean
}

export interface OptimizationConstraint {
  type: 'performance' | 'risk' | 'resource' | 'time'
  condition: string
  value: number
  operator: '>' | '<' | '=' | '>=' | '<='
}

export interface RetryPolicy {
  maxRetries: number
  backoffStrategy: 'linear' | 'exponential' | 'fixed'
  baseDelay: number
  maxDelay: number
}

export interface WorkflowProgress {
  executionId: string
  currentStep: number
  totalSteps: number
  overallProgress: number
  stepProgress: number
  estimatedTimeRemaining: number
  status: string
  lastUpdate: Date
  
  // Extended progress information
  completedSteps?: number
  failedSteps?: number
  runningSteps?: number
  pendingSteps?: number
  averageStepDuration?: number
  totalElapsedTime?: number
  efficiency?: number
  currentStepName?: string
  currentStepType?: string
  currentStepStartTime?: Date
  nextSteps?: NextStepInfo[]
  resourceUsage?: ResourceUsageInfo
  qualityScore?: number
}

export interface NextStepInfo {
  id: string
  name: string
  type: string
  estimatedDuration: number
  dependencies: string[]
}

export interface ResourceUsageInfo {
  cpu: number
  memory: number
  network: number
  storage: number
  trend: 'increasing' | 'decreasing' | 'stable'
}

// Import ChainOfThoughtStep and Persona from ai.ts
import type { ChainOfThoughtStep, Persona } from './ai'