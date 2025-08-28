import type {
  WorkflowExecution,
  WorkflowStep,
  WorkflowError
} from '@/types'
import { useWorkflowStore } from '@/stores/workflowStore'
import { workflowCheckpointManager } from './workflowCheckpointManager'
import { workflowRecoveryService } from './workflowRecoveryService'

export class WorkflowStatusMonitor {
  private monitoringInterval: number = 5000 // 5 seconds
  private activeMonitors = new Map<string, NodeJS.Timeout>()
  private statusListeners = new Map<string, ((status: WorkflowStatus) => void)[]>()
  private healthChecks = new Map<string, HealthCheck>()

  /**
   * Start monitoring a workflow execution
   */
  startMonitoring(executionId: string): void {
    if (this.activeMonitors.has(executionId)) {
      this.stopMonitoring(executionId)
    }

    const interval = setInterval(() => {
      this.checkWorkflowStatus(executionId)
    }, this.monitoringInterval)

    this.activeMonitors.set(executionId, interval)
    
    // Initialize health check
    this.initializeHealthCheck(executionId)
  }

  /**
   * Stop monitoring a workflow execution
   */
  stopMonitoring(executionId: string): void {
    const interval = this.activeMonitors.get(executionId)
    if (interval) {
      clearInterval(interval)
      this.activeMonitors.delete(executionId)
    }
    
    this.healthChecks.delete(executionId)
  }

  /**
   * Get current workflow status
   */
  getWorkflowStatus(executionId: string): WorkflowStatus | null {
    const execution = this.getExecution(executionId)
    if (!execution) return null

    return this.calculateWorkflowStatus(execution)
  }

  /**
   * Check workflow status and detect issues
   */
  private async checkWorkflowStatus(executionId: string): Promise<void> {
    const execution = this.getExecution(executionId)
    if (!execution) {
      this.stopMonitoring(executionId)
      return
    }

    const status = this.calculateWorkflowStatus(execution)
    const healthCheck = this.healthChecks.get(executionId)

    // Update health check
    if (healthCheck) {
      this.updateHealthCheck(executionId, status, healthCheck)
    }

    // Detect and handle issues
    await this.detectAndHandleIssues(execution, status)

    // Notify listeners
    this.notifyStatusListeners(executionId, status)

    // Auto-cleanup completed workflows
    if (status.overall === 'completed' || status.overall === 'failed') {
      setTimeout(() => this.stopMonitoring(executionId), 30000) // Stop monitoring after 30 seconds
    }
  }

  /**
   * Calculate comprehensive workflow status
   */
  private calculateWorkflowStatus(execution: WorkflowExecution): WorkflowStatus {
    const steps = execution.steps
    const totalSteps = steps.length
    const completedSteps = steps.filter(s => s.status === 'completed').length
    const failedSteps = steps.filter(s => s.status === 'failed').length
    const runningSteps = steps.filter(s => s.status === 'running').length
    const pendingSteps = steps.filter(s => s.status === 'pending').length

    // Calculate overall status
    let overallStatus: WorkflowStatus['overall']
    if (execution.status === 'completed') {
      overallStatus = 'completed'
    } else if (execution.status === 'failed') {
      overallStatus = 'failed'
    } else if (execution.status === 'paused') {
      overallStatus = 'paused'
    } else if (runningSteps > 0) {
      overallStatus = 'running'
    } else if (pendingSteps > 0) {
      overallStatus = 'pending'
    } else {
      overallStatus = 'unknown'
    }

    // Calculate health score
    const healthScore = this.calculateHealthScore(execution)

    // Detect issues
    const issues = this.detectIssues(execution)

    // Calculate performance metrics
    const performance = this.calculatePerformanceMetrics(execution)

    // Calculate resource usage
    const resourceUsage = this.calculateResourceUsage(execution)

    return {
      executionId: execution.id,
      overall: overallStatus,
      progress: {
        completed: completedSteps,
        failed: failedSteps,
        running: runningSteps,
        pending: pendingSteps,
        total: totalSteps,
        percentage: totalSteps > 0 ? (completedSteps / totalSteps) * 100 : 0
      },
      health: {
        score: healthScore,
        status: this.getHealthStatus(healthScore),
        issues: issues.length,
        lastCheck: new Date()
      },
      performance,
      resourceUsage,
      issues,
      timestamps: {
        started: execution.startTime,
        lastUpdate: new Date(),
        estimated: this.estimateCompletion(execution)
      }
    }
  }

  /**
   * Calculate health score (0-100)
   */
  private calculateHealthScore(execution: WorkflowExecution): number {
    let score = 100

    // Deduct points for failed steps
    const failedSteps = execution.steps.filter(s => s.status === 'failed').length
    score -= failedSteps * 20

    // Deduct points for long-running steps
    const longRunningSteps = execution.steps.filter(step => {
      if (step.status !== 'running' || !step.startTime) return false
      const duration = Date.now() - step.startTime.getTime()
      return duration > 600000 // 10 minutes
    }).length
    score -= longRunningSteps * 10

    // Deduct points for stalled workflow
    if (execution.status === 'running') {
      const lastActivity = this.getLastActivityTime(execution)
      if (lastActivity && Date.now() - lastActivity.getTime() > 300000) { // 5 minutes
        score -= 15
      }
    }

    // Deduct points for resource issues
    const resourceIssues = this.detectResourceIssues(execution)
    score -= resourceIssues.length * 5

    return Math.max(0, Math.min(100, score))
  }

  /**
   * Get health status from score
   */
  private getHealthStatus(score: number): 'excellent' | 'good' | 'fair' | 'poor' | 'critical' {
    if (score >= 90) return 'excellent'
    if (score >= 75) return 'good'
    if (score >= 60) return 'fair'
    if (score >= 40) return 'poor'
    return 'critical'
  }

  /**
   * Detect workflow issues
   */
  private detectIssues(execution: WorkflowExecution): WorkflowIssue[] {
    const issues: WorkflowIssue[] = []

    // Check for failed steps
    const failedSteps = execution.steps.filter(s => s.status === 'failed')
    failedSteps.forEach(step => {
      issues.push({
        type: 'step_failure',
        severity: 'high',
        message: `Step "${step.name}" has failed`,
        stepId: step.id,
        timestamp: new Date(),
        recoverable: step.error?.recoverable || false
      })
    })

    // Check for stalled steps
    const stalledSteps = execution.steps.filter(step => {
      if (step.status !== 'running' || !step.startTime) return false
      const duration = Date.now() - step.startTime.getTime()
      return duration > 900000 // 15 minutes
    })
    stalledSteps.forEach(step => {
      issues.push({
        type: 'step_stalled',
        severity: 'medium',
        message: `Step "${step.name}" appears to be stalled`,
        stepId: step.id,
        timestamp: new Date(),
        recoverable: true
      })
    })

    // Check for resource issues
    const resourceIssues = this.detectResourceIssues(execution)
    issues.push(...resourceIssues)

    // Check for dependency issues
    const dependencyIssues = this.detectDependencyIssues(execution)
    issues.push(...dependencyIssues)

    return issues
  }

  /**
   * Detect resource-related issues
   */
  private detectResourceIssues(execution: WorkflowExecution): WorkflowIssue[] {
    const issues: WorkflowIssue[] = []

    // Check memory usage (simulated)
    const memoryUsage = this.getMemoryUsage()
    if (memoryUsage > 0.9) {
      issues.push({
        type: 'resource_exhaustion',
        severity: 'high',
        message: 'High memory usage detected',
        timestamp: new Date(),
        recoverable: true
      })
    }

    // Check for network issues
    if (!navigator.onLine) {
      issues.push({
        type: 'network_issue',
        severity: 'high',
        message: 'Network connectivity lost',
        timestamp: new Date(),
        recoverable: true
      })
    }

    return issues
  }

  /**
   * Detect dependency-related issues
   */
  private detectDependencyIssues(execution: WorkflowExecution): WorkflowIssue[] {
    const issues: WorkflowIssue[] = []

    // Check for circular dependencies (this would be more complex in reality)
    const pendingSteps = execution.steps.filter(s => s.status === 'pending')
    if (pendingSteps.length > 0 && execution.steps.filter(s => s.status === 'running').length === 0) {
      issues.push({
        type: 'dependency_deadlock',
        severity: 'high',
        message: 'Possible dependency deadlock detected',
        timestamp: new Date(),
        recoverable: false
      })
    }

    return issues
  }

  /**
   * Calculate performance metrics
   */
  private calculatePerformanceMetrics(execution: WorkflowExecution): PerformanceMetrics {
    const completedSteps = execution.steps.filter(s => s.status === 'completed')
    
    if (completedSteps.length === 0) {
      return {
        averageStepDuration: 0,
        totalDuration: 0,
        efficiency: 100,
        throughput: 0
      }
    }

    // Calculate average step duration
    const stepDurations = completedSteps
      .filter(step => step.startTime && step.endTime)
      .map(step => step.endTime!.getTime() - step.startTime!.getTime())

    const averageStepDuration = stepDurations.length > 0 
      ? stepDurations.reduce((sum, duration) => sum + duration, 0) / stepDurations.length
      : 0

    // Calculate total duration
    const totalDuration = execution.startTime 
      ? Date.now() - execution.startTime.getTime()
      : 0

    // Calculate efficiency (actual vs estimated)
    const efficiency = this.calculateEfficiency(execution)

    // Calculate throughput (steps per minute)
    const throughput = totalDuration > 0 
      ? (completedSteps.length / (totalDuration / 60000))
      : 0

    return {
      averageStepDuration,
      totalDuration,
      efficiency,
      throughput
    }
  }

  /**
   * Calculate resource usage
   */
  private calculateResourceUsage(execution: WorkflowExecution): ResourceUsageMetrics {
    // This would integrate with actual system monitoring
    return {
      cpu: this.getCPUUsage(),
      memory: this.getMemoryUsage(),
      network: this.getNetworkUsage(),
      storage: this.getStorageUsage()
    }
  }

  /**
   * Detect and handle issues automatically
   */
  private async detectAndHandleIssues(execution: WorkflowExecution, status: WorkflowStatus): Promise<void> {
    for (const issue of status.issues) {
      if (issue.recoverable && issue.severity === 'high') {
        await this.handleIssueAutomatically(execution, issue)
      }
    }
  }

  /**
   * Handle issues automatically
   */
  private async handleIssueAutomatically(execution: WorkflowExecution, issue: WorkflowIssue): Promise<void> {
    switch (issue.type) {
      case 'step_failure':
        if (issue.stepId) {
          const step = execution.steps.find(s => s.id === issue.stepId)
          if (step?.error) {
            await workflowRecoveryService.recoverFromError(execution.id, step.error)
          }
        }
        break

      case 'step_stalled':
        // Create a timeout error and attempt recovery
        const timeoutError: WorkflowError = {
          code: 'TIMEOUT_ERROR',
          message: 'Step execution timeout',
          details: { stepId: issue.stepId },
          recoverable: true,
          suggestions: ['Increase timeout', 'Check system resources'],
          timestamp: new Date()
        }
        await workflowRecoveryService.recoverFromError(execution.id, timeoutError)
        break

      case 'network_issue':
        // Create a network error and attempt recovery
        const networkError: WorkflowError = {
          code: 'NETWORK_ERROR',
          message: 'Network connectivity issue',
          details: {},
          recoverable: true,
          suggestions: ['Check network connection', 'Retry operation'],
          timestamp: new Date()
        }
        await workflowRecoveryService.recoverFromError(execution.id, networkError)
        break
    }
  }

  /**
   * Initialize health check for an execution
   */
  private initializeHealthCheck(executionId: string): void {
    this.healthChecks.set(executionId, {
      executionId,
      startTime: new Date(),
      lastCheck: new Date(),
      checkCount: 0,
      issueHistory: [],
      performanceHistory: []
    })
  }

  /**
   * Update health check data
   */
  private updateHealthCheck(executionId: string, status: WorkflowStatus, healthCheck: HealthCheck): void {
    healthCheck.lastCheck = new Date()
    healthCheck.checkCount++
    
    // Record issues
    if (status.issues.length > 0) {
      healthCheck.issueHistory.push({
        timestamp: new Date(),
        issues: [...status.issues]
      })
    }
    
    // Record performance
    healthCheck.performanceHistory.push({
      timestamp: new Date(),
      metrics: { ...status.performance }
    })
    
    // Keep only recent history (last 100 entries)
    if (healthCheck.issueHistory.length > 100) {
      healthCheck.issueHistory = healthCheck.issueHistory.slice(-100)
    }
    if (healthCheck.performanceHistory.length > 100) {
      healthCheck.performanceHistory = healthCheck.performanceHistory.slice(-100)
    }
  }

  /**
   * Helper methods
   */
  private getExecution(executionId: string): WorkflowExecution | null {
    const store = useWorkflowStore.getState()
    return store.executions.find(e => e.id === executionId) || null
  }

  private getLastActivityTime(execution: WorkflowExecution): Date | null {
    const times = [
      execution.startTime,
      ...execution.steps.map(s => s.startTime).filter(Boolean),
      ...execution.steps.map(s => s.endTime).filter(Boolean)
    ].filter(Boolean) as Date[]

    return times.length > 0 ? new Date(Math.max(...times.map(t => t.getTime()))) : null
  }

  private estimateCompletion(execution: WorkflowExecution): Date | null {
    const completedSteps = execution.steps.filter(s => s.status === 'completed')
    const remainingSteps = execution.steps.filter(s => s.status !== 'completed')

    if (completedSteps.length === 0 || remainingSteps.length === 0) {
      return null
    }

    const avgDuration = completedSteps.reduce((sum, step) => {
      if (!step.startTime || !step.endTime) return sum
      return sum + (step.endTime.getTime() - step.startTime.getTime())
    }, 0) / completedSteps.length

    const estimatedRemainingTime = remainingSteps.length * avgDuration
    return new Date(Date.now() + estimatedRemainingTime)
  }

  private calculateEfficiency(execution: WorkflowExecution): number {
    // This would compare actual vs estimated performance
    return 85 // Placeholder
  }

  private getCPUUsage(): number {
    // This would integrate with actual system monitoring
    return Math.random() * 0.5 + 0.2 // Simulated 20-70%
  }

  private getMemoryUsage(): number {
    // This would integrate with actual system monitoring
    return Math.random() * 0.4 + 0.3 // Simulated 30-70%
  }

  private getNetworkUsage(): number {
    // This would integrate with actual system monitoring
    return Math.random() * 0.3 + 0.1 // Simulated 10-40%
  }

  private getStorageUsage(): number {
    // This would integrate with actual system monitoring
    return Math.random() * 0.2 + 0.05 // Simulated 5-25%
  }

  /**
   * Event listeners
   */
  addStatusListener(executionId: string, listener: (status: WorkflowStatus) => void): void {
    const listeners = this.statusListeners.get(executionId) || []
    listeners.push(listener)
    this.statusListeners.set(executionId, listeners)
  }

  removeStatusListener(executionId: string, listener: (status: WorkflowStatus) => void): void {
    const listeners = this.statusListeners.get(executionId) || []
    const index = listeners.indexOf(listener)
    if (index > -1) {
      listeners.splice(index, 1)
      this.statusListeners.set(executionId, listeners)
    }
  }

  private notifyStatusListeners(executionId: string, status: WorkflowStatus): void {
    const listeners = this.statusListeners.get(executionId) || []
    listeners.forEach(listener => listener(status))
  }

  /**
   * Cleanup resources
   */
  cleanup(): void {
    // Stop all active monitors
    for (const [executionId] of this.activeMonitors) {
      this.stopMonitoring(executionId)
    }
    
    // Clear listeners
    this.statusListeners.clear()
    this.healthChecks.clear()
  }
}

interface WorkflowStatus {
  executionId: string
  overall: 'pending' | 'running' | 'paused' | 'completed' | 'failed' | 'unknown'
  progress: {
    completed: number
    failed: number
    running: number
    pending: number
    total: number
    percentage: number
  }
  health: {
    score: number
    status: 'excellent' | 'good' | 'fair' | 'poor' | 'critical'
    issues: number
    lastCheck: Date
  }
  performance: PerformanceMetrics
  resourceUsage: ResourceUsageMetrics
  issues: WorkflowIssue[]
  timestamps: {
    started: Date
    lastUpdate: Date
    estimated: Date | null
  }
}

interface WorkflowIssue {
  type: 'step_failure' | 'step_stalled' | 'resource_exhaustion' | 'network_issue' | 'dependency_deadlock'
  severity: 'low' | 'medium' | 'high' | 'critical'
  message: string
  stepId?: string
  timestamp: Date
  recoverable: boolean
}

interface PerformanceMetrics {
  averageStepDuration: number
  totalDuration: number
  efficiency: number
  throughput: number
}

interface ResourceUsageMetrics {
  cpu: number
  memory: number
  network: number
  storage: number
}

interface HealthCheck {
  executionId: string
  startTime: Date
  lastCheck: Date
  checkCount: number
  issueHistory: {
    timestamp: Date
    issues: WorkflowIssue[]
  }[]
  performanceHistory: {
    timestamp: Date
    metrics: PerformanceMetrics
  }[]
}

// Export singleton instance
export const workflowStatusMonitor = new WorkflowStatusMonitor()