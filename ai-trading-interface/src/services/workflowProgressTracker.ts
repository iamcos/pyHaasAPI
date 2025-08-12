import type {
  WorkflowExecution,
  WorkflowProgress,
  WorkflowStep,
  StepResult
} from '@/types'
import { useWorkflowStore } from '@/stores/workflowStore'

export class WorkflowProgressTracker {
  private progressUpdateInterval: number = 1000 // 1 second
  private activeTrackers = new Map<string, NodeJS.Timeout>()
  private progressListeners = new Map<string, ((progress: WorkflowProgress) => void)[]>()

  /**
   * Start tracking progress for a workflow execution
   */
  startTracking(executionId: string): void {
    if (this.activeTrackers.has(executionId)) {
      this.stopTracking(executionId)
    }

    const interval = setInterval(() => {
      this.updateProgress(executionId)
    }, this.progressUpdateInterval)

    this.activeTrackers.set(executionId, interval)
  }

  /**
   * Stop tracking progress for a workflow execution
   */
  stopTracking(executionId: string): void {
    const interval = this.activeTrackers.get(executionId)
    if (interval) {
      clearInterval(interval)
      this.activeTrackers.delete(executionId)
    }
  }

  /**
   * Get current progress for a workflow execution
   */
  getProgress(executionId: string): WorkflowProgress | null {
    const execution = this.getExecution(executionId)
    if (!execution) return null

    return this.calculateProgress(execution)
  }

  /**
   * Update progress and notify listeners
   */
  private updateProgress(executionId: string): void {
    const progress = this.getProgress(executionId)
    if (!progress) return

    // Notify listeners
    const listeners = this.progressListeners.get(executionId) || []
    listeners.forEach(listener => listener(progress))

    // Update store if needed
    const store = useWorkflowStore.getState()
    const execution = store.executions.find(e => e.id === executionId)
    if (execution && execution.status === 'completed') {
      this.stopTracking(executionId)
    }
  }

  /**
   * Calculate detailed progress information
   */
  private calculateProgress(execution: WorkflowExecution): WorkflowProgress {
    const totalSteps = execution.steps.length
    const completedSteps = execution.steps.filter(step => step.status === 'completed')
    const runningStep = execution.steps.find(step => step.status === 'running')
    const failedSteps = execution.steps.filter(step => step.status === 'failed')

    // Calculate overall progress
    const overallProgress = totalSteps > 0 ? (completedSteps.length / totalSteps) * 100 : 0

    // Calculate current step progress
    const stepProgress = runningStep?.progress || 0

    // Estimate time remaining
    const estimatedTimeRemaining = this.estimateTimeRemaining(execution)

    // Calculate detailed metrics
    const metrics = this.calculateProgressMetrics(execution)

    return {
      executionId: execution.id,
      currentStep: execution.currentStep,
      totalSteps: execution.totalSteps,
      overallProgress,
      stepProgress,
      estimatedTimeRemaining,
      status: execution.status,
      lastUpdate: new Date(),
      
      // Additional detailed information
      completedSteps: completedSteps.length,
      failedSteps: failedSteps.length,
      runningSteps: execution.steps.filter(s => s.status === 'running').length,
      pendingSteps: execution.steps.filter(s => s.status === 'pending').length,
      
      // Performance metrics
      averageStepDuration: metrics.averageStepDuration,
      totalElapsedTime: metrics.totalElapsedTime,
      efficiency: metrics.efficiency,
      
      // Current step details
      currentStepName: runningStep?.name,
      currentStepType: runningStep?.type,
      currentStepStartTime: runningStep?.startTime,
      
      // Next steps preview
      nextSteps: this.getNextSteps(execution, 3),
      
      // Resource usage
      resourceUsage: this.calculateResourceUsage(execution),
      
      // Quality metrics
      qualityScore: this.calculateQualityScore(execution)
    }
  }

  /**
   * Calculate progress metrics
   */
  private calculateProgressMetrics(execution: WorkflowExecution): ProgressMetrics {
    const completedSteps = execution.steps.filter(step => step.status === 'completed')
    
    // Calculate average step duration
    const stepDurations = completedSteps
      .filter(step => step.startTime && step.endTime)
      .map(step => step.endTime!.getTime() - step.startTime!.getTime())
    
    const averageStepDuration = stepDurations.length > 0 
      ? stepDurations.reduce((sum, duration) => sum + duration, 0) / stepDurations.length
      : 0

    // Calculate total elapsed time
    const totalElapsedTime = execution.startTime 
      ? Date.now() - execution.startTime.getTime()
      : 0

    // Calculate efficiency (actual vs estimated time)
    const estimatedTime = execution.steps.reduce((sum, step) => {
      const template = this.getStepTemplate(step.templateId)
      return sum + (template?.estimatedDuration || 0)
    }, 0)
    
    const efficiency = estimatedTime > 0 ? (estimatedTime / totalElapsedTime) * 100 : 100

    return {
      averageStepDuration,
      totalElapsedTime,
      efficiency
    }
  }

  /**
   * Estimate time remaining based on completed steps
   */
  private estimateTimeRemaining(execution: WorkflowExecution): number {
    const completedSteps = execution.steps.filter(step => step.status === 'completed')
    const remainingSteps = execution.steps.filter(step => 
      step.status === 'pending' || step.status === 'running'
    )

    if (completedSteps.length === 0) {
      // Use template estimates if no completed steps
      return remainingSteps.reduce((sum, step) => {
        const template = this.getStepTemplate(step.templateId)
        return sum + (template?.estimatedDuration || 0)
      }, 0)
    }

    // Calculate average duration from completed steps
    const actualDurations = completedSteps
      .filter(step => step.startTime && step.endTime)
      .map(step => step.endTime!.getTime() - step.startTime!.getTime())

    if (actualDurations.length === 0) return 0

    const averageDuration = actualDurations.reduce((sum, duration) => sum + duration, 0) / actualDurations.length

    // Estimate remaining time
    let remainingTime = 0

    for (const step of remainingSteps) {
      if (step.status === 'running') {
        // For running step, estimate based on progress
        const template = this.getStepTemplate(step.templateId)
        const estimatedStepDuration = template?.estimatedDuration || averageDuration
        remainingTime += estimatedStepDuration * (1 - step.progress / 100)
      } else {
        // For pending steps, use average duration
        remainingTime += averageDuration
      }
    }

    return remainingTime
  }

  /**
   * Get next steps to be executed
   */
  private getNextSteps(execution: WorkflowExecution, count: number): NextStepInfo[] {
    const pendingSteps = execution.steps
      .filter(step => step.status === 'pending')
      .slice(0, count)

    return pendingSteps.map(step => ({
      id: step.id,
      name: step.name,
      type: step.type,
      estimatedDuration: this.getStepTemplate(step.templateId)?.estimatedDuration || 0,
      dependencies: this.getStepTemplate(step.templateId)?.dependencies || []
    }))
  }

  /**
   * Calculate resource usage across all steps
   */
  private calculateResourceUsage(execution: WorkflowExecution): ResourceUsageInfo {
    const completedSteps = execution.steps.filter(step => step.status === 'completed' && step.result)
    
    if (completedSteps.length === 0) {
      return {
        cpu: 0,
        memory: 0,
        network: 0,
        storage: 0,
        trend: 'stable'
      }
    }

    const resourceMetrics = completedSteps.map(step => step.result!.metrics.resourceUsage)
    
    const avgCpu = resourceMetrics.reduce((sum, metrics) => sum + metrics.cpu, 0) / resourceMetrics.length
    const avgMemory = resourceMetrics.reduce((sum, metrics) => sum + metrics.memory, 0) / resourceMetrics.length
    const avgNetwork = resourceMetrics.reduce((sum, metrics) => sum + metrics.network, 0) / resourceMetrics.length
    const avgStorage = resourceMetrics.reduce((sum, metrics) => sum + metrics.storage, 0) / resourceMetrics.length

    // Determine trend based on recent steps
    const recentSteps = completedSteps.slice(-3)
    const trend = this.calculateResourceTrend(recentSteps)

    return {
      cpu: avgCpu,
      memory: avgMemory,
      network: avgNetwork,
      storage: avgStorage,
      trend
    }
  }

  /**
   * Calculate quality score based on step results
   */
  private calculateQualityScore(execution: WorkflowExecution): number {
    const completedSteps = execution.steps.filter(step => step.status === 'completed' && step.result)
    
    if (completedSteps.length === 0) return 0

    const qualityMetrics = completedSteps.map(step => step.result!.metrics.quality)
    
    const avgAccuracy = qualityMetrics.reduce((sum, metrics) => sum + metrics.accuracy, 0) / qualityMetrics.length
    const avgCompleteness = qualityMetrics.reduce((sum, metrics) => sum + metrics.completeness, 0) / qualityMetrics.length
    const avgReliability = qualityMetrics.reduce((sum, metrics) => sum + metrics.reliability, 0) / qualityMetrics.length

    // Weighted average (accuracy is most important)
    return (avgAccuracy * 0.5 + avgCompleteness * 0.3 + avgReliability * 0.2) * 100
  }

  /**
   * Calculate resource usage trend
   */
  private calculateResourceTrend(recentSteps: WorkflowStep[]): 'increasing' | 'decreasing' | 'stable' {
    if (recentSteps.length < 2) return 'stable'

    const resourceUsages = recentSteps
      .filter(step => step.result)
      .map(step => {
        const usage = step.result!.metrics.resourceUsage
        return usage.cpu + usage.memory + usage.network + usage.storage
      })

    if (resourceUsages.length < 2) return 'stable'

    const first = resourceUsages[0]
    const last = resourceUsages[resourceUsages.length - 1]
    const threshold = 0.1 // 10% change threshold

    if (last > first * (1 + threshold)) return 'increasing'
    if (last < first * (1 - threshold)) return 'decreasing'
    return 'stable'
  }

  /**
   * Get step template information
   */
  private getStepTemplate(templateId: string): any {
    // This would fetch step template details from the template manager
    // For now, return null - this would be implemented with actual template lookup
    return null
  }

  /**
   * Get workflow execution
   */
  private getExecution(executionId: string): WorkflowExecution | null {
    const store = useWorkflowStore.getState()
    return store.executions.find(e => e.id === executionId) || null
  }

  /**
   * Add progress listener
   */
  addProgressListener(executionId: string, listener: (progress: WorkflowProgress) => void): void {
    const listeners = this.progressListeners.get(executionId) || []
    listeners.push(listener)
    this.progressListeners.set(executionId, listeners)
  }

  /**
   * Remove progress listener
   */
  removeProgressListener(executionId: string, listener: (progress: WorkflowProgress) => void): void {
    const listeners = this.progressListeners.get(executionId) || []
    const index = listeners.indexOf(listener)
    if (index > -1) {
      listeners.splice(index, 1)
      this.progressListeners.set(executionId, listeners)
    }
  }

  /**
   * Get progress history for visualization
   */
  getProgressHistory(executionId: string): ProgressHistoryPoint[] {
    // This would return historical progress data for charts
    // Implementation would depend on how progress history is stored
    return []
  }

  /**
   * Export progress data
   */
  exportProgressData(executionId: string): ProgressExport {
    const execution = this.getExecution(executionId)
    const progress = this.getProgress(executionId)
    
    if (!execution || !progress) {
      throw new Error(`Execution not found: ${executionId}`)
    }

    return {
      execution: {
        id: execution.id,
        type: execution.type,
        status: execution.status,
        startTime: execution.startTime,
        endTime: execution.endTime
      },
      progress,
      steps: execution.steps.map(step => ({
        id: step.id,
        name: step.name,
        type: step.type,
        status: step.status,
        progress: step.progress,
        startTime: step.startTime,
        endTime: step.endTime,
        duration: step.startTime && step.endTime 
          ? step.endTime.getTime() - step.startTime.getTime()
          : null
      })),
      exportTime: new Date()
    }
  }

  /**
   * Cleanup resources
   */
  cleanup(): void {
    // Stop all active trackers
    for (const [executionId] of this.activeTrackers) {
      this.stopTracking(executionId)
    }
    
    // Clear listeners
    this.progressListeners.clear()
  }
}

// Extended WorkflowProgress interface with additional details
interface ExtendedWorkflowProgress extends WorkflowProgress {
  completedSteps: number
  failedSteps: number
  runningSteps: number
  pendingSteps: number
  averageStepDuration: number
  totalElapsedTime: number
  efficiency: number
  currentStepName?: string
  currentStepType?: string
  currentStepStartTime?: Date
  nextSteps: NextStepInfo[]
  resourceUsage: ResourceUsageInfo
  qualityScore: number
}

interface ProgressMetrics {
  averageStepDuration: number
  totalElapsedTime: number
  efficiency: number
}

interface NextStepInfo {
  id: string
  name: string
  type: string
  estimatedDuration: number
  dependencies: string[]
}

interface ResourceUsageInfo {
  cpu: number
  memory: number
  network: number
  storage: number
  trend: 'increasing' | 'decreasing' | 'stable'
}

interface ProgressHistoryPoint {
  timestamp: Date
  overallProgress: number
  stepProgress: number
  currentStep: number
}

interface ProgressExport {
  execution: {
    id: string
    type: string
    status: string
    startTime: Date
    endTime?: Date
  }
  progress: WorkflowProgress
  steps: {
    id: string
    name: string
    type: string
    status: string
    progress: number
    startTime?: Date
    endTime?: Date
    duration: number | null
  }[]
  exportTime: Date
}

// Export singleton instance
export const workflowProgressTracker = new WorkflowProgressTracker()