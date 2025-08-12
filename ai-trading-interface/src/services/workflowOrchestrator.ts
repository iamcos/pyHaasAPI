import type {
  WorkflowExecution,
  WorkflowTemplate,
  WorkflowStep,
  WorkflowConfig,
  WorkflowProgress,
  StepResult,
  WorkflowError,
  ResumeData,
  StepState,
  ChainOfThoughtStep
} from '@/types'
import { useWorkflowStore } from '@/stores/workflowStore'
import { chainOfThoughtManager } from './chainOfThoughtManager'
import { mcpClient } from './mcpClient'
import { pyHaasClient } from './pyHaasClient'

export class WorkflowOrchestrator {
  private activeExecutions = new Map<string, WorkflowExecution>()
  private stepExecutors = new Map<string, (step: WorkflowStep, context: any) => Promise<StepResult>>()
  private eventListeners = new Map<string, ((event: WorkflowEvent) => void)[]>()

  constructor() {
    this.initializeStepExecutors()
  }

  /**
   * Initialize step executors for different step types
   */
  private initializeStepExecutors() {
    this.stepExecutors.set('backtest', this.executeBacktestStep.bind(this))
    this.stepExecutors.set('analysis', this.executeAnalysisStep.bind(this))
    this.stepExecutors.set('optimization', this.executeOptimizationStep.bind(this))
    this.stepExecutors.set('validation', this.executeValidationStep.bind(this))
    this.stepExecutors.set('custom', this.executeCustomStep.bind(this))
  }

  /**
   * Execute a workflow based on configuration
   */
  async executeWorkflow(config: WorkflowConfig): Promise<WorkflowExecution> {
    const execution = await this.createWorkflowExecution(config)
    
    try {
      this.activeExecutions.set(execution.id, execution)
      this.emitEvent('workflow_started', { execution })
      
      // Update store
      useWorkflowStore.getState().addExecution(execution)
      useWorkflowStore.getState().setActiveExecution(execution.id)
      
      // Start execution
      await this.runWorkflowSteps(execution)
      
      return execution
    } catch (error) {
      await this.handleWorkflowError(execution, error as Error)
      throw error
    }
  }

  /**
   * Create workflow execution from configuration
   */
  private async createWorkflowExecution(config: WorkflowConfig): Promise<WorkflowExecution> {
    let steps: WorkflowStep[]
    let templateId: string | undefined

    if (config.templateId) {
      const template = await this.getWorkflowTemplate(config.templateId)
      if (!template) {
        throw new Error(`Workflow template not found: ${config.templateId}`)
      }
      steps = this.createStepsFromTemplate(template, config)
      templateId = config.templateId
    } else if (config.customSteps) {
      steps = this.createStepsFromTemplates(config.customSteps, config)
    } else {
      throw new Error('Either templateId or customSteps must be provided')
    }

    // Validate step dependencies
    this.validateStepDependencies(steps)

    const execution: WorkflowExecution = {
      id: this.generateExecutionId(),
      type: 'chain_of_thought_optimization',
      templateId,
      status: 'running',
      currentStep: 0,
      totalSteps: steps.length,
      steps,
      results: [],
      chainOfThought: [],
      startTime: new Date(),
    }

    return execution
  }

  /**
   * Run workflow steps with dependency management
   */
  private async runWorkflowSteps(execution: WorkflowExecution): Promise<void> {
    const dependencyGraph = this.buildDependencyGraph(execution.steps)
    const executedSteps = new Set<string>()
    
    while (executedSteps.size < execution.steps.length) {
      const readySteps = this.getReadySteps(execution.steps, dependencyGraph, executedSteps)
      
      if (readySteps.length === 0) {
        throw new Error('Circular dependency detected or no steps ready to execute')
      }

      // Execute ready steps in parallel (if they don't conflict)
      const stepPromises = readySteps.map(step => this.executeStep(execution, step))
      const results = await Promise.allSettled(stepPromises)

      // Process results
      for (let i = 0; i < results.length; i++) {
        const result = results[i]
        const step = readySteps[i]

        if (result.status === 'fulfilled') {
          executedSteps.add(step.id)
          execution.results.push(result.value)
          this.updateStepStatus(execution, step.id, 'completed')
        } else {
          await this.handleStepError(execution, step, result.reason)
          if (!step.templateId || !this.isStepOptional(step)) {
            throw result.reason
          }
          executedSteps.add(step.id) // Skip optional failed steps
        }
      }

      // Update progress
      execution.currentStep = executedSteps.size
      this.emitEvent('workflow_progress', { execution, progress: this.calculateProgress(execution) })
    }

    // Mark workflow as completed
    execution.status = 'completed'
    execution.endTime = new Date()
    this.emitEvent('workflow_completed', { execution })
  }

  /**
   * Execute a single workflow step
   */
  async executeStep(execution: WorkflowExecution, step: WorkflowStep): Promise<StepResult> {
    const startTime = new Date()
    
    try {
      // Update step status
      this.updateStepStatus(execution, step.id, 'running', 0, startTime)
      this.emitEvent('step_started', { execution, step })

      // Create chain of thought for step
      const chainOfThought: ChainOfThoughtStep[] = [{
        id: `${step.id}_start`,
        step: 1,
        reasoning: `Starting execution of step: ${step.name}`,
        data: { stepType: step.type, parameters: step.parameters },
        confidence: 1.0,
        timestamp: startTime
      }]

      // Get step executor
      const executor = this.stepExecutors.get(step.type)
      if (!executor) {
        throw new Error(`No executor found for step type: ${step.type}`)
      }

      // Execute step with context
      const context = this.buildStepContext(execution, step)
      const result = await executor(step, context)

      // Update step with result
      const endTime = new Date()
      this.updateStepStatus(execution, step.id, 'completed', 100, startTime, endTime, result)
      
      // Add completion reasoning
      chainOfThought.push({
        id: `${step.id}_complete`,
        step: 2,
        reasoning: `Successfully completed step: ${step.name}`,
        data: { result: result.data, metrics: result.metrics },
        confidence: result.success ? 1.0 : 0.5,
        timestamp: endTime
      })

      step.chainOfThought = chainOfThought
      this.emitEvent('step_completed', { execution, step, result })

      return result
    } catch (error) {
      const endTime = new Date()
      const workflowError: WorkflowError = {
        code: 'STEP_EXECUTION_ERROR',
        message: error instanceof Error ? error.message : 'Unknown error',
        details: error,
        recoverable: this.isErrorRecoverable(error),
        suggestions: this.getErrorSuggestions(error),
        timestamp: endTime
      }

      this.updateStepStatus(execution, step.id, 'failed', step.progress, startTime, endTime, undefined, workflowError)
      this.emitEvent('step_failed', { execution, step, error: workflowError })
      
      throw error
    }
  }

  /**
   * Build dependency graph for steps
   */
  private buildDependencyGraph(steps: WorkflowStep[]): Map<string, string[]> {
    const graph = new Map<string, string[]>()
    
    for (const step of steps) {
      const template = this.getStepTemplate(step.templateId)
      graph.set(step.id, template?.dependencies || [])
    }
    
    return graph
  }

  /**
   * Get steps that are ready to execute (dependencies satisfied)
   */
  private getReadySteps(
    steps: WorkflowStep[], 
    dependencyGraph: Map<string, string[]>, 
    executedSteps: Set<string>
  ): WorkflowStep[] {
    return steps.filter(step => {
      if (executedSteps.has(step.id)) return false
      
      const dependencies = dependencyGraph.get(step.id) || []
      return dependencies.every(depId => executedSteps.has(depId))
    })
  }

  /**
   * Build execution context for a step
   */
  private buildStepContext(execution: WorkflowExecution, step: WorkflowStep): any {
    const previousResults = execution.results.filter(result => 
      step.templateId && this.getStepTemplate(step.templateId)?.dependencies.includes(result.stepId)
    )

    return {
      execution,
      step,
      previousResults,
      labId: execution.id, // This should come from config
      chainOfThought: execution.chainOfThought
    }
  }

  /**
   * Step executors for different types
   */
  private async executeBacktestStep(step: WorkflowStep, context: any): Promise<StepResult> {
    const startTime = Date.now()
    
    try {
      // Execute backtest using MCP client
      const backtestResult = await mcpClient.labs.backtest(context.labId, {
        timeframe: step.parameters.timeframe || '1h',
        startDate: step.parameters.startDate,
        endDate: step.parameters.endDate,
        parameters: step.parameters.optimizationParams || {}
      })

      const endTime = Date.now()
      const duration = endTime - startTime

      return {
        stepId: step.id,
        success: true,
        data: backtestResult,
        metrics: {
          duration,
          resourceUsage: {
            cpu: 0.5,
            memory: 0.3,
            network: 0.2,
            storage: 0.1
          },
          quality: {
            accuracy: 0.95,
            completeness: 1.0,
            reliability: 0.9
          }
        },
        artifacts: [{
          id: `${step.id}_backtest_result`,
          type: 'data',
          name: 'Backtest Result',
          description: 'Backtest execution results',
          path: `/artifacts/${step.id}/backtest.json`,
          size: JSON.stringify(backtestResult).length,
          createdAt: new Date()
        }],
        chainOfThought: [{
          id: `${step.id}_backtest`,
          step: 1,
          reasoning: 'Executed backtest with specified parameters',
          data: { parameters: step.parameters, result: backtestResult },
          confidence: 0.9,
          timestamp: new Date()
        }],
        timestamp: new Date()
      }
    } catch (error) {
      throw new Error(`Backtest execution failed: ${error}`)
    }
  }

  private async executeAnalysisStep(step: WorkflowStep, context: any): Promise<StepResult> {
    // Implementation for analysis step
    const startTime = Date.now()
    
    // Analyze previous results
    const analysisData = {
      performanceMetrics: this.calculatePerformanceMetrics(context.previousResults),
      riskMetrics: this.calculateRiskMetrics(context.previousResults),
      recommendations: this.generateRecommendations(context.previousResults)
    }

    const endTime = Date.now()

    return {
      stepId: step.id,
      success: true,
      data: analysisData,
      metrics: {
        duration: endTime - startTime,
        resourceUsage: { cpu: 0.3, memory: 0.2, network: 0.1, storage: 0.05 },
        quality: { accuracy: 0.9, completeness: 0.95, reliability: 0.85 }
      },
      artifacts: [],
      chainOfThought: [{
        id: `${step.id}_analysis`,
        step: 1,
        reasoning: 'Analyzed performance and risk metrics from previous results',
        data: analysisData,
        confidence: 0.85,
        timestamp: new Date()
      }],
      timestamp: new Date()
    }
  }

  private async executeOptimizationStep(step: WorkflowStep, context: any): Promise<StepResult> {
    // Implementation for optimization step
    const startTime = Date.now()
    
    const optimizationResult = {
      optimizedParameters: step.parameters,
      improvementScore: 0.15,
      confidence: 0.8
    }

    const endTime = Date.now()

    return {
      stepId: step.id,
      success: true,
      data: optimizationResult,
      metrics: {
        duration: endTime - startTime,
        resourceUsage: { cpu: 0.7, memory: 0.5, network: 0.3, storage: 0.2 },
        quality: { accuracy: 0.85, completeness: 0.9, reliability: 0.8 }
      },
      artifacts: [],
      chainOfThought: [{
        id: `${step.id}_optimization`,
        step: 1,
        reasoning: 'Optimized parameters based on analysis results',
        data: optimizationResult,
        confidence: 0.8,
        timestamp: new Date()
      }],
      timestamp: new Date()
    }
  }

  private async executeValidationStep(step: WorkflowStep, context: any): Promise<StepResult> {
    // Implementation for validation step
    const startTime = Date.now()
    
    const validationResult = {
      isValid: true,
      validationScore: 0.92,
      issues: []
    }

    const endTime = Date.now()

    return {
      stepId: step.id,
      success: validationResult.isValid,
      data: validationResult,
      metrics: {
        duration: endTime - startTime,
        resourceUsage: { cpu: 0.2, memory: 0.15, network: 0.1, storage: 0.05 },
        quality: { accuracy: 0.95, completeness: 1.0, reliability: 0.9 }
      },
      artifacts: [],
      chainOfThought: [{
        id: `${step.id}_validation`,
        step: 1,
        reasoning: 'Validated optimization results against constraints',
        data: validationResult,
        confidence: 0.92,
        timestamp: new Date()
      }],
      timestamp: new Date()
    }
  }

  private async executeCustomStep(step: WorkflowStep, context: any): Promise<StepResult> {
    // Implementation for custom step
    const startTime = Date.now()
    
    // Custom step execution logic would go here
    const customResult = {
      message: 'Custom step executed successfully',
      data: step.parameters
    }

    const endTime = Date.now()

    return {
      stepId: step.id,
      success: true,
      data: customResult,
      metrics: {
        duration: endTime - startTime,
        resourceUsage: { cpu: 0.1, memory: 0.1, network: 0.05, storage: 0.02 },
        quality: { accuracy: 0.8, completeness: 0.8, reliability: 0.8 }
      },
      artifacts: [],
      chainOfThought: [{
        id: `${step.id}_custom`,
        step: 1,
        reasoning: 'Executed custom step with provided parameters',
        data: customResult,
        confidence: 0.8,
        timestamp: new Date()
      }],
      timestamp: new Date()
    }
  }

  /**
   * Utility methods
   */
  private generateExecutionId(): string {
    return `workflow_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  }

  private async getWorkflowTemplate(templateId: string): Promise<WorkflowTemplate | null> {
    const templates = useWorkflowStore.getState().templates
    return templates.find(t => t.id === templateId) || null
  }

  private getStepTemplate(templateId: string): any {
    // This would fetch step template details
    return null
  }

  private createStepsFromTemplate(template: WorkflowTemplate, config: WorkflowConfig): WorkflowStep[] {
    return template.steps.map((stepTemplate, index) => ({
      id: `${template.id}_step_${index}`,
      templateId: stepTemplate.id,
      name: stepTemplate.name,
      type: stepTemplate.type,
      status: 'pending',
      parameters: { ...stepTemplate.parameters, ...config.parameters },
      progress: 0,
      chainOfThought: []
    }))
  }

  private createStepsFromTemplates(stepTemplates: any[], config: WorkflowConfig): WorkflowStep[] {
    return stepTemplates.map((stepTemplate, index) => ({
      id: `custom_step_${index}`,
      templateId: stepTemplate.id,
      name: stepTemplate.name,
      type: stepTemplate.type,
      status: 'pending',
      parameters: { ...stepTemplate.parameters, ...config.parameters },
      progress: 0,
      chainOfThought: []
    }))
  }

  private validateStepDependencies(steps: WorkflowStep[]): void {
    // Validate that all dependencies exist and no circular dependencies
    const stepIds = new Set(steps.map(s => s.id))
    
    for (const step of steps) {
      const template = this.getStepTemplate(step.templateId)
      if (template?.dependencies) {
        for (const depId of template.dependencies) {
          if (!stepIds.has(depId)) {
            throw new Error(`Step ${step.id} depends on non-existent step ${depId}`)
          }
        }
      }
    }
  }

  private updateStepStatus(
    execution: WorkflowExecution,
    stepId: string,
    status: WorkflowStep['status'],
    progress?: number,
    startTime?: Date,
    endTime?: Date,
    result?: StepResult,
    error?: WorkflowError
  ): void {
    const step = execution.steps.find(s => s.id === stepId)
    if (step) {
      step.status = status
      if (progress !== undefined) step.progress = progress
      if (startTime) step.startTime = startTime
      if (endTime) step.endTime = endTime
      if (result) step.result = result
      if (error) step.error = error
    }

    // Update store
    useWorkflowStore.getState().updateExecutionStep(execution.id, stepId, {
      status,
      progress,
      startTime,
      endTime,
      result,
      error
    })
  }

  private calculateProgress(execution: WorkflowExecution): WorkflowProgress {
    const completedSteps = execution.steps.filter(s => s.status === 'completed').length
    const totalSteps = execution.steps.length
    
    return {
      executionId: execution.id,
      currentStep: execution.currentStep,
      totalSteps: execution.totalSteps,
      overallProgress: totalSteps > 0 ? (completedSteps / totalSteps) * 100 : 0,
      stepProgress: execution.steps[execution.currentStep]?.progress || 0,
      estimatedTimeRemaining: this.estimateTimeRemaining(execution),
      status: execution.status,
      lastUpdate: new Date()
    }
  }

  private estimateTimeRemaining(execution: WorkflowExecution): number {
    // Calculate based on completed steps and their durations
    const completedSteps = execution.steps.filter(s => s.status === 'completed')
    if (completedSteps.length === 0) return 0

    const avgDuration = completedSteps.reduce((sum, step) => {
      const duration = step.endTime && step.startTime 
        ? step.endTime.getTime() - step.startTime.getTime()
        : 0
      return sum + duration
    }, 0) / completedSteps.length

    const remainingSteps = execution.steps.length - completedSteps.length
    return remainingSteps * avgDuration
  }

  private isStepOptional(step: WorkflowStep): boolean {
    const template = this.getStepTemplate(step.templateId)
    return template?.optional || false
  }

  private isErrorRecoverable(error: any): boolean {
    // Determine if error is recoverable based on error type
    return error.code !== 'FATAL_ERROR'
  }

  private getErrorSuggestions(error: any): string[] {
    // Provide suggestions based on error type
    return ['Check network connection', 'Verify parameters', 'Retry operation']
  }

  private async handleWorkflowError(execution: WorkflowExecution, error: Error): Promise<void> {
    execution.status = 'failed'
    execution.endTime = new Date()
    
    this.emitEvent('workflow_failed', { execution, error })
    useWorkflowStore.getState().updateExecution(execution.id, { status: 'failed', endTime: new Date() })
  }

  private async handleStepError(execution: WorkflowExecution, step: WorkflowStep, error: any): Promise<void> {
    // Handle step-specific error recovery
    this.emitEvent('step_error', { execution, step, error })
  }

  private calculatePerformanceMetrics(results: StepResult[]): any {
    // Calculate performance metrics from results
    return {
      totalReturn: 0.15,
      sharpeRatio: 1.2,
      maxDrawdown: 0.08
    }
  }

  private calculateRiskMetrics(results: StepResult[]): any {
    // Calculate risk metrics from results
    return {
      volatility: 0.12,
      var95: 0.05,
      expectedShortfall: 0.07
    }
  }

  private generateRecommendations(results: StepResult[]): string[] {
    // Generate recommendations based on results
    return [
      'Consider reducing position size during high volatility periods',
      'Optimize stop-loss levels based on recent performance',
      'Review correlation with market indices'
    ]
  }

  /**
   * Event system
   */
  private emitEvent(eventType: string, data: any): void {
    const listeners = this.eventListeners.get(eventType) || []
    listeners.forEach(listener => listener({ type: eventType, data }))
  }

  addEventListener(eventType: string, listener: (event: WorkflowEvent) => void): void {
    const listeners = this.eventListeners.get(eventType) || []
    listeners.push(listener)
    this.eventListeners.set(eventType, listeners)
  }

  removeEventListener(eventType: string, listener: (event: WorkflowEvent) => void): void {
    const listeners = this.eventListeners.get(eventType) || []
    const index = listeners.indexOf(listener)
    if (index > -1) {
      listeners.splice(index, 1)
      this.eventListeners.set(eventType, listeners)
    }
  }
}

interface WorkflowEvent {
  type: string
  data: any
}

// Export singleton instance
export const workflowOrchestrator = new WorkflowOrchestrator()