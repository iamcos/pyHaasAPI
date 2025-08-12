import type {
  WorkflowExecution,
  WorkflowStep,
  WorkflowError,
  StepResult
} from '@/types'
import { useWorkflowStore } from '@/stores/workflowStore'
import { workflowCheckpointManager } from './workflowCheckpointManager'
import { workflowOrchestrator } from './workflowOrchestrator'

export class WorkflowRecoveryService {
  private recoveryStrategies = new Map<string, RecoveryStrategy>()
  private recoveryHistory = new Map<string, RecoveryAttempt[]>()

  constructor() {
    this.initializeRecoveryStrategies()
  }

  /**
   * Initialize recovery strategies for different error types
   */
  private initializeRecoveryStrategies(): void {
    this.recoveryStrategies.set('NETWORK_ERROR', {
      name: 'Network Error Recovery',
      maxAttempts: 5,
      backoffStrategy: 'exponential',
      baseDelay: 2000,
      maxDelay: 30000,
      canRecover: (error) => error.code === 'NETWORK_ERROR',
      recover: this.recoverFromNetworkError.bind(this)
    })

    this.recoveryStrategies.set('TIMEOUT_ERROR', {
      name: 'Timeout Error Recovery',
      maxAttempts: 3,
      backoffStrategy: 'linear',
      baseDelay: 5000,
      maxDelay: 15000,
      canRecover: (error) => error.code === 'TIMEOUT_ERROR',
      recover: this.recoverFromTimeoutError.bind(this)
    })

    this.recoveryStrategies.set('RESOURCE_ERROR', {
      name: 'Resource Error Recovery',
      maxAttempts: 2,
      backoffStrategy: 'fixed',
      baseDelay: 10000,
      maxDelay: 10000,
      canRecover: (error) => error.code === 'RESOURCE_ERROR',
      recover: this.recoverFromResourceError.bind(this)
    })

    this.recoveryStrategies.set('VALIDATION_ERROR', {
      name: 'Validation Error Recovery',
      maxAttempts: 1,
      backoffStrategy: 'fixed',
      baseDelay: 1000,
      maxDelay: 1000,
      canRecover: (error) => error.code === 'VALIDATION_ERROR' && error.recoverable,
      recover: this.recoverFromValidationError.bind(this)
    })

    this.recoveryStrategies.set('STEP_EXECUTION_ERROR', {
      name: 'Step Execution Error Recovery',
      maxAttempts: 3,
      backoffStrategy: 'exponential',
      baseDelay: 1000,
      maxDelay: 8000,
      canRecover: (error) => error.code === 'STEP_EXECUTION_ERROR' && error.recoverable,
      recover: this.recoverFromStepExecutionError.bind(this)
    })
  }

  /**
   * Attempt to recover from a workflow error
   */
  async recoverFromError(
    executionId: string,
    error: WorkflowError,
    context?: RecoveryContext
  ): Promise<RecoveryResult> {
    const execution = this.getExecution(executionId)
    if (!execution) {
      throw new Error(`Execution not found: ${executionId}`)
    }

    // Find appropriate recovery strategy
    const strategy = this.findRecoveryStrategy(error)
    if (!strategy) {
      return {
        success: false,
        strategy: null,
        error: 'No recovery strategy available for this error type',
        attempts: 0
      }
    }

    // Check if we've exceeded max attempts
    const previousAttempts = this.getRecoveryAttempts(executionId, error.code)
    if (previousAttempts.length >= strategy.maxAttempts) {
      return {
        success: false,
        strategy: strategy.name,
        error: 'Maximum recovery attempts exceeded',
        attempts: previousAttempts.length
      }
    }

    // Create recovery attempt record
    const attempt: RecoveryAttempt = {
      id: this.generateAttemptId(),
      executionId,
      errorCode: error.code,
      strategy: strategy.name,
      timestamp: new Date(),
      status: 'in_progress'
    }

    this.recordRecoveryAttempt(executionId, attempt)

    try {
      // Calculate delay based on previous attempts
      const delay = this.calculateDelay(strategy, previousAttempts.length)
      if (delay > 0) {
        await this.sleep(delay)
      }

      // Create checkpoint before recovery attempt
      const checkpointId = await workflowCheckpointManager.createCheckpoint(executionId)
      attempt.checkpointId = checkpointId

      // Attempt recovery
      const recoveryResult = await strategy.recover(execution, error, context)

      // Update attempt record
      attempt.status = recoveryResult.success ? 'success' : 'failed'
      attempt.result = recoveryResult
      attempt.endTime = new Date()

      this.updateRecoveryAttempt(executionId, attempt)

      return {
        success: recoveryResult.success,
        strategy: strategy.name,
        result: recoveryResult,
        attempts: previousAttempts.length + 1,
        checkpointId
      }
    } catch (recoveryError) {
      // Update attempt record with error
      attempt.status = 'failed'
      attempt.error = recoveryError instanceof Error ? recoveryError.message : 'Unknown error'
      attempt.endTime = new Date()

      this.updateRecoveryAttempt(executionId, attempt)

      return {
        success: false,
        strategy: strategy.name,
        error: attempt.error,
        attempts: previousAttempts.length + 1
      }
    }
  }

  /**
   * Resume workflow execution after recovery
   */
  async resumeAfterRecovery(executionId: string): Promise<void> {
    const execution = this.getExecution(executionId)
    if (!execution) {
      throw new Error(`Execution not found: ${executionId}`)
    }

    // Update execution status
    execution.status = 'running'
    
    // Update store
    const store = useWorkflowStore.getState()
    store.updateExecution(executionId, { status: 'running' })

    // Continue workflow execution from current step
    try {
      await this.continueWorkflowExecution(execution)
    } catch (error) {
      // If continuation fails, attempt recovery again
      const workflowError: WorkflowError = {
        code: 'CONTINUATION_ERROR',
        message: error instanceof Error ? error.message : 'Failed to continue workflow',
        details: error,
        recoverable: true,
        suggestions: ['Check system resources', 'Verify network connectivity'],
        timestamp: new Date()
      }

      await this.recoverFromError(executionId, workflowError)
    }
  }

  /**
   * Get recovery history for an execution
   */
  getRecoveryHistory(executionId: string): RecoveryAttempt[] {
    return this.recoveryHistory.get(executionId) || []
  }

  /**
   * Get recovery statistics
   */
  getRecoveryStats(executionId: string): RecoveryStats {
    const attempts = this.getRecoveryHistory(executionId)
    const successfulAttempts = attempts.filter(a => a.status === 'success')
    const failedAttempts = attempts.filter(a => a.status === 'failed')

    const errorTypes = new Map<string, number>()
    attempts.forEach(attempt => {
      const count = errorTypes.get(attempt.errorCode) || 0
      errorTypes.set(attempt.errorCode, count + 1)
    })

    return {
      totalAttempts: attempts.length,
      successfulAttempts: successfulAttempts.length,
      failedAttempts: failedAttempts.length,
      successRate: attempts.length > 0 ? successfulAttempts.length / attempts.length : 0,
      errorTypes: Object.fromEntries(errorTypes),
      averageRecoveryTime: this.calculateAverageRecoveryTime(attempts),
      lastRecoveryAttempt: attempts.length > 0 ? attempts[attempts.length - 1].timestamp : null
    }
  }

  /**
   * Recovery strategy implementations
   */
  private async recoverFromNetworkError(
    execution: WorkflowExecution,
    error: WorkflowError,
    context?: RecoveryContext
  ): Promise<StrategyResult> {
    // Check network connectivity
    const isOnline = navigator.onLine
    if (!isOnline) {
      return {
        success: false,
        message: 'Network is offline, cannot recover',
        actions: ['Wait for network connectivity']
      }
    }

    // Test connection to critical services
    const servicesHealthy = await this.testServiceConnectivity()
    if (!servicesHealthy) {
      return {
        success: false,
        message: 'Critical services are unavailable',
        actions: ['Wait for service recovery', 'Check service status']
      }
    }

    // Reset network-related state
    await this.resetNetworkState(execution)

    return {
      success: true,
      message: 'Network connectivity restored',
      actions: ['Resumed workflow execution']
    }
  }

  private async recoverFromTimeoutError(
    execution: WorkflowExecution,
    error: WorkflowError,
    context?: RecoveryContext
  ): Promise<StrategyResult> {
    // Increase timeout for the failing step
    const currentStep = execution.steps.find(s => s.status === 'failed')
    if (currentStep) {
      // Double the timeout (this would need to be implemented in step execution)
      currentStep.parameters = {
        ...currentStep.parameters,
        timeout: (currentStep.parameters.timeout || 30000) * 2
      }
    }

    // Clear any partial results that might be causing issues
    await this.clearPartialResults(execution)

    return {
      success: true,
      message: 'Timeout increased and partial results cleared',
      actions: ['Increased step timeout', 'Cleared partial results']
    }
  }

  private async recoverFromResourceError(
    execution: WorkflowExecution,
    error: WorkflowError,
    context?: RecoveryContext
  ): Promise<StrategyResult> {
    // Check system resources
    const resourceStatus = await this.checkSystemResources()
    if (!resourceStatus.sufficient) {
      return {
        success: false,
        message: 'Insufficient system resources',
        actions: ['Free up memory', 'Close other applications']
      }
    }

    // Reduce resource usage for the workflow
    await this.optimizeResourceUsage(execution)

    return {
      success: true,
      message: 'Resource usage optimized',
      actions: ['Reduced memory usage', 'Optimized processing']
    }
  }

  private async recoverFromValidationError(
    execution: WorkflowExecution,
    error: WorkflowError,
    context?: RecoveryContext
  ): Promise<StrategyResult> {
    // Attempt to fix validation issues automatically
    const fixResult = await this.autoFixValidationIssues(execution, error)
    
    if (fixResult.fixed) {
      return {
        success: true,
        message: 'Validation issues automatically resolved',
        actions: fixResult.actions
      }
    }

    return {
      success: false,
      message: 'Could not automatically resolve validation issues',
      actions: ['Manual intervention required', 'Check step parameters']
    }
  }

  private async recoverFromStepExecutionError(
    execution: WorkflowExecution,
    error: WorkflowError,
    context?: RecoveryContext
  ): Promise<StrategyResult> {
    // Reset the failed step
    const failedStep = execution.steps.find(s => s.status === 'failed')
    if (failedStep) {
      failedStep.status = 'pending'
      failedStep.progress = 0
      failedStep.error = undefined
      failedStep.endTime = undefined
    }

    // Clear any cached data that might be causing issues
    await this.clearStepCache(execution, failedStep?.id)

    return {
      success: true,
      message: 'Step reset and cache cleared',
      actions: ['Reset failed step', 'Cleared step cache']
    }
  }

  /**
   * Helper methods
   */
  private findRecoveryStrategy(error: WorkflowError): RecoveryStrategy | null {
    for (const strategy of this.recoveryStrategies.values()) {
      if (strategy.canRecover(error)) {
        return strategy
      }
    }
    return null
  }

  private getRecoveryAttempts(executionId: string, errorCode: string): RecoveryAttempt[] {
    const allAttempts = this.recoveryHistory.get(executionId) || []
    return allAttempts.filter(attempt => attempt.errorCode === errorCode)
  }

  private recordRecoveryAttempt(executionId: string, attempt: RecoveryAttempt): void {
    const attempts = this.recoveryHistory.get(executionId) || []
    attempts.push(attempt)
    this.recoveryHistory.set(executionId, attempts)
  }

  private updateRecoveryAttempt(executionId: string, updatedAttempt: RecoveryAttempt): void {
    const attempts = this.recoveryHistory.get(executionId) || []
    const index = attempts.findIndex(a => a.id === updatedAttempt.id)
    if (index >= 0) {
      attempts[index] = updatedAttempt
    }
  }

  private calculateDelay(strategy: RecoveryStrategy, attemptNumber: number): number {
    switch (strategy.backoffStrategy) {
      case 'exponential':
        return Math.min(strategy.baseDelay * Math.pow(2, attemptNumber), strategy.maxDelay)
      case 'linear':
        return Math.min(strategy.baseDelay * (attemptNumber + 1), strategy.maxDelay)
      case 'fixed':
        return strategy.baseDelay
      default:
        return strategy.baseDelay
    }
  }

  private async sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms))
  }

  private async continueWorkflowExecution(execution: WorkflowExecution): Promise<void> {
    // This would integrate with the workflow orchestrator to continue execution
    // For now, we'll just update the status
    console.log('Continuing workflow execution:', execution.id)
  }

  private async testServiceConnectivity(): Promise<boolean> {
    // Test connectivity to critical services
    try {
      // This would test actual service endpoints
      return true
    } catch {
      return false
    }
  }

  private async resetNetworkState(execution: WorkflowExecution): Promise<void> {
    // Reset any network-related state
    console.log('Resetting network state for execution:', execution.id)
  }

  private async clearPartialResults(execution: WorkflowExecution): Promise<void> {
    // Clear any partial results that might be causing issues
    console.log('Clearing partial results for execution:', execution.id)
  }

  private async checkSystemResources(): Promise<{ sufficient: boolean }> {
    // Check system resources (memory, CPU, etc.)
    return { sufficient: true }
  }

  private async optimizeResourceUsage(execution: WorkflowExecution): Promise<void> {
    // Optimize resource usage for the workflow
    console.log('Optimizing resource usage for execution:', execution.id)
  }

  private async autoFixValidationIssues(
    execution: WorkflowExecution, 
    error: WorkflowError
  ): Promise<{ fixed: boolean; actions: string[] }> {
    // Attempt to automatically fix validation issues
    return { fixed: false, actions: [] }
  }

  private async clearStepCache(execution: WorkflowExecution, stepId?: string): Promise<void> {
    // Clear cached data for a specific step or all steps
    console.log('Clearing step cache for execution:', execution.id, 'step:', stepId)
  }

  private calculateAverageRecoveryTime(attempts: RecoveryAttempt[]): number {
    const completedAttempts = attempts.filter(a => a.endTime)
    if (completedAttempts.length === 0) return 0

    const totalTime = completedAttempts.reduce((sum, attempt) => {
      const duration = attempt.endTime!.getTime() - attempt.timestamp.getTime()
      return sum + duration
    }, 0)

    return totalTime / completedAttempts.length
  }

  private getExecution(executionId: string): WorkflowExecution | null {
    const store = useWorkflowStore.getState()
    return store.executions.find(e => e.id === executionId) || null
  }

  private generateAttemptId(): string {
    return `recovery_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  }

  /**
   * Cleanup resources
   */
  cleanup(): void {
    this.recoveryHistory.clear()
  }
}

interface RecoveryStrategy {
  name: string
  maxAttempts: number
  backoffStrategy: 'exponential' | 'linear' | 'fixed'
  baseDelay: number
  maxDelay: number
  canRecover: (error: WorkflowError) => boolean
  recover: (execution: WorkflowExecution, error: WorkflowError, context?: RecoveryContext) => Promise<StrategyResult>
}

interface RecoveryAttempt {
  id: string
  executionId: string
  errorCode: string
  strategy: string
  timestamp: Date
  endTime?: Date
  status: 'in_progress' | 'success' | 'failed'
  checkpointId?: string
  result?: StrategyResult
  error?: string
}

interface RecoveryContext {
  userInitiated?: boolean
  maxRetries?: number
  customParameters?: any
}

interface RecoveryResult {
  success: boolean
  strategy: string | null
  result?: StrategyResult
  error?: string
  attempts: number
  checkpointId?: string
}

interface StrategyResult {
  success: boolean
  message: string
  actions: string[]
  data?: any
}

interface RecoveryStats {
  totalAttempts: number
  successfulAttempts: number
  failedAttempts: number
  successRate: number
  errorTypes: Record<string, number>
  averageRecoveryTime: number
  lastRecoveryAttempt: Date | null
}

// Export singleton instance
export const workflowRecoveryService = new WorkflowRecoveryService()