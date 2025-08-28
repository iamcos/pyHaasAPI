import type {
  WorkflowExecution,
  WorkflowConfig,
  WorkflowProgress
} from '@/types'
import { workflowOrchestrator } from './workflowOrchestrator'
import { workflowProgressTracker } from './workflowProgressTracker'
import { useWorkflowStore } from '@/stores/workflowStore'

export class BatchWorkflowManager {
  private activeBatches = new Map<string, BatchExecution>()
  private batchListeners = new Map<string, ((batch: BatchExecution) => void)[]>()
  private resourceManager = new ResourceManager()

  /**
   * Execute multiple workflows in batch
   */
  async executeBatch(batchConfig: BatchConfig): Promise<BatchExecution> {
    const batchId = this.generateBatchId()
    
    const batch: BatchExecution = {
      id: batchId,
      name: batchConfig.name,
      description: batchConfig.description,
      status: 'initializing',
      workflows: [],
      startTime: new Date(),
      totalWorkflows: batchConfig.workflows.length,
      completedWorkflows: 0,
      failedWorkflows: 0,
      progress: 0,
      resourceLimits: batchConfig.resourceLimits,
      concurrencyLimit: batchConfig.concurrencyLimit || 3,
      retryPolicy: batchConfig.retryPolicy,
      results: [],
      errors: []
    }

    this.activeBatches.set(batchId, batch)

    try {
      // Initialize workflows
      batch.status = 'running'
      batch.workflows = await this.initializeWorkflows(batchConfig.workflows, batchId)
      
      // Start batch execution
      await this.executeBatchWorkflows(batch)
      
      return batch
    } catch (error) {
      batch.status = 'failed'
      batch.endTime = new Date()
      batch.errors.push({
        type: 'batch_initialization',
        message: error instanceof Error ? error.message : 'Unknown error',
        timestamp: new Date()
      })
      
      this.emitBatchEvent(batchId, 'batch_failed', { batch, error })
      throw error
    }
  }

  /**
   * Get batch execution status
   */
  getBatchExecution(batchId: string): BatchExecution | null {
    return this.activeBatches.get(batchId) || null
  }

  /**
   * Get all active batches
   */
  getActiveBatches(): BatchExecution[] {
    return Array.from(this.activeBatches.values())
  }

  /**
   * Pause batch execution
   */
  async pauseBatch(batchId: string): Promise<void> {
    const batch = this.activeBatches.get(batchId)
    if (!batch) {
      throw new Error(`Batch not found: ${batchId}`)
    }

    batch.status = 'paused'
    
    // Pause all running workflows
    for (const workflow of batch.workflows) {
      if (workflow.status === 'running') {
        // This would pause individual workflows
        workflow.status = 'paused'
      }
    }

    this.emitBatchEvent(batchId, 'batch_paused', { batch })
  }

  /**
   * Resume batch execution
   */
  async resumeBatch(batchId: string): Promise<void> {
    const batch = this.activeBatches.get(batchId)
    if (!batch) {
      throw new Error(`Batch not found: ${batchId}`)
    }

    batch.status = 'running'
    
    // Resume paused workflows
    await this.continueBatchExecution(batch)
    
    this.emitBatchEvent(batchId, 'batch_resumed', { batch })
  }

  /**
   * Cancel batch execution
   */
  async cancelBatch(batchId: string): Promise<void> {
    const batch = this.activeBatches.get(batchId)
    if (!batch) {
      throw new Error(`Batch not found: ${batchId}`)
    }

    batch.status = 'cancelled'
    batch.endTime = new Date()
    
    // Cancel all workflows
    for (const workflow of batch.workflows) {
      if (workflow.status === 'running' || workflow.status === 'pending') {
        workflow.status = 'cancelled'
      }
    }

    this.emitBatchEvent(batchId, 'batch_cancelled', { batch })
  }

  /**
   * Get batch progress
   */
  getBatchProgress(batchId: string): BatchProgress | null {
    const batch = this.activeBatches.get(batchId)
    if (!batch) return null

    return this.calculateBatchProgress(batch)
  }

  /**
   * Initialize workflows for batch execution
   */
  private async initializeWorkflows(
    workflowConfigs: WorkflowConfig[], 
    batchId: string
  ): Promise<BatchWorkflow[]> {
    const workflows: BatchWorkflow[] = []

    for (let i = 0; i < workflowConfigs.length; i++) {
      const config = workflowConfigs[i]
      const workflowId = `${batchId}_workflow_${i}`
      
      workflows.push({
        id: workflowId,
        batchId,
        config,
        status: 'pending',
        priority: config.priority || 'normal',
        retryCount: 0,
        maxRetries: config.retryPolicy?.maxRetries || 3,
        estimatedDuration: this.estimateWorkflowDuration(config),
        resourceRequirements: this.calculateResourceRequirements(config),
        dependencies: this.extractDependencies(config, i),
        startTime: undefined,
        endTime: undefined,
        result: undefined,
        error: undefined
      })
    }

    return workflows
  }

  /**
   * Execute batch workflows with concurrency control
   */
  private async executeBatchWorkflows(batch: BatchExecution): Promise<void> {
    const workflowQueue = [...batch.workflows]
    const runningWorkflows = new Set<string>()
    
    this.emitBatchEvent(batch.id, 'batch_started', { batch })

    while (workflowQueue.length > 0 || runningWorkflows.size > 0) {
      // Check if batch was paused or cancelled
      if (batch.status === 'paused' || batch.status === 'cancelled') {
        break
      }

      // Start new workflows up to concurrency limit
      while (
        runningWorkflows.size < batch.concurrencyLimit && 
        workflowQueue.length > 0
      ) {
        const workflow = this.getNextReadyWorkflow(workflowQueue, batch.workflows)
        if (!workflow) break

        // Check resource availability
        if (!this.resourceManager.canAllocateResources(workflow.resourceRequirements)) {
          break
        }

        // Remove from queue and start execution
        const index = workflowQueue.indexOf(workflow)
        workflowQueue.splice(index, 1)
        runningWorkflows.add(workflow.id)

        this.startWorkflowExecution(workflow, batch)
      }

      // Wait for at least one workflow to complete
      await this.waitForWorkflowCompletion(runningWorkflows, batch)
      
      // Update batch progress
      this.updateBatchProgress(batch)
    }

    // Finalize batch
    this.finalizeBatch(batch)
  }

  /**
   * Get next workflow that's ready to execute
   */
  private getNextReadyWorkflow(
    queue: BatchWorkflow[], 
    allWorkflows: BatchWorkflow[]
  ): BatchWorkflow | null {
    for (const workflow of queue) {
      if (this.areDependenciesSatisfied(workflow, allWorkflows)) {
        return workflow
      }
    }
    return null
  }

  /**
   * Check if workflow dependencies are satisfied
   */
  private areDependenciesSatisfied(
    workflow: BatchWorkflow, 
    allWorkflows: BatchWorkflow[]
  ): boolean {
    for (const depId of workflow.dependencies) {
      const dependency = allWorkflows.find(w => w.id === depId)
      if (!dependency || dependency.status !== 'completed') {
        return false
      }
    }
    return true
  }

  /**
   * Start individual workflow execution
   */
  private async startWorkflowExecution(
    workflow: BatchWorkflow, 
    batch: BatchExecution
  ): Promise<void> {
    try {
      workflow.status = 'running'
      workflow.startTime = new Date()
      
      // Allocate resources
      this.resourceManager.allocateResources(workflow.id, workflow.resourceRequirements)
      
      // Start workflow execution
      const execution = await workflowOrchestrator.executeWorkflow(workflow.config)
      workflow.executionId = execution.id
      
      // Track progress
      workflowProgressTracker.startTracking(execution.id)
      workflowProgressTracker.addProgressListener(execution.id, (progress) => {
        this.handleWorkflowProgress(workflow, progress, batch)
      })

      this.emitBatchEvent(batch.id, 'workflow_started', { batch, workflow })
      
    } catch (error) {
      await this.handleWorkflowError(workflow, error, batch)
    }
  }

  /**
   * Handle workflow progress updates
   */
  private handleWorkflowProgress(
    workflow: BatchWorkflow, 
    progress: WorkflowProgress, 
    batch: BatchExecution
  ): void {
    workflow.progress = progress.overallProgress

    // Check if workflow completed
    if (progress.status === 'completed') {
      this.handleWorkflowCompletion(workflow, batch, true)
    } else if (progress.status === 'failed') {
      this.handleWorkflowCompletion(workflow, batch, false)
    }
  }

  /**
   * Handle workflow completion
   */
  private handleWorkflowCompletion(
    workflow: BatchWorkflow, 
    batch: BatchExecution, 
    success: boolean
  ): void {
    workflow.status = success ? 'completed' : 'failed'
    workflow.endTime = new Date()
    
    // Release resources
    this.resourceManager.releaseResources(workflow.id)
    
    // Update batch counters
    if (success) {
      batch.completedWorkflows++
      batch.results.push({
        workflowId: workflow.id,
        success: true,
        duration: workflow.endTime.getTime() - (workflow.startTime?.getTime() || 0),
        result: workflow.result
      })
    } else {
      batch.failedWorkflows++
      batch.errors.push({
        type: 'workflow_execution',
        message: `Workflow ${workflow.id} failed`,
        workflowId: workflow.id,
        timestamp: new Date(),
        error: workflow.error
      })
    }

    this.emitBatchEvent(batch.id, success ? 'workflow_completed' : 'workflow_failed', { 
      batch, 
      workflow 
    })
  }

  /**
   * Handle workflow errors with retry logic
   */
  private async handleWorkflowError(
    workflow: BatchWorkflow, 
    error: any, 
    batch: BatchExecution
  ): Promise<void> {
    workflow.error = error
    workflow.retryCount++

    if (workflow.retryCount <= workflow.maxRetries) {
      // Retry workflow
      const delay = this.calculateRetryDelay(workflow.retryCount, batch.retryPolicy)
      setTimeout(() => {
        this.startWorkflowExecution(workflow, batch)
      }, delay)
      
      this.emitBatchEvent(batch.id, 'workflow_retry', { batch, workflow, retryCount: workflow.retryCount })
    } else {
      // Max retries exceeded
      this.handleWorkflowCompletion(workflow, batch, false)
    }
  }

  /**
   * Wait for at least one workflow to complete
   */
  private async waitForWorkflowCompletion(
    runningWorkflows: Set<string>, 
    batch: BatchExecution
  ): Promise<void> {
    return new Promise((resolve) => {
      const checkCompletion = () => {
        const completedWorkflows = batch.workflows.filter(w => 
          runningWorkflows.has(w.id) && (w.status === 'completed' || w.status === 'failed')
        )

        if (completedWorkflows.length > 0) {
          // Remove completed workflows from running set
          completedWorkflows.forEach(w => runningWorkflows.delete(w.id))
          resolve()
        } else {
          setTimeout(checkCompletion, 1000) // Check every second
        }
      }
      
      checkCompletion()
    })
  }

  /**
   * Continue batch execution after pause
   */
  private async continueBatchExecution(batch: BatchExecution): Promise<void> {
    // Resume paused workflows
    const pausedWorkflows = batch.workflows.filter(w => w.status === 'paused')
    
    for (const workflow of pausedWorkflows) {
      if (workflow.executionId) {
        // Resume individual workflow execution
        workflow.status = 'running'
      }
    }

    // Continue with remaining workflows
    await this.executeBatchWorkflows(batch)
  }

  /**
   * Update batch progress
   */
  private updateBatchProgress(batch: BatchExecution): void {
    const totalWorkflows = batch.totalWorkflows
    const completedWorkflows = batch.completedWorkflows + batch.failedWorkflows
    
    batch.progress = totalWorkflows > 0 ? (completedWorkflows / totalWorkflows) * 100 : 0
    
    this.emitBatchEvent(batch.id, 'batch_progress', { batch })
  }

  /**
   * Calculate batch progress details
   */
  private calculateBatchProgress(batch: BatchExecution): BatchProgress {
    const runningWorkflows = batch.workflows.filter(w => w.status === 'running')
    const pendingWorkflows = batch.workflows.filter(w => w.status === 'pending')
    
    // Calculate estimated time remaining
    const avgWorkflowDuration = this.calculateAverageWorkflowDuration(batch)
    const remainingWorkflows = runningWorkflows.length + pendingWorkflows.length
    const estimatedTimeRemaining = remainingWorkflows * avgWorkflowDuration

    // Calculate resource utilization
    const resourceUtilization = this.resourceManager.getUtilization()

    return {
      batchId: batch.id,
      overallProgress: batch.progress,
      completedWorkflows: batch.completedWorkflows,
      failedWorkflows: batch.failedWorkflows,
      runningWorkflows: runningWorkflows.length,
      pendingWorkflows: pendingWorkflows.length,
      totalWorkflows: batch.totalWorkflows,
      estimatedTimeRemaining,
      resourceUtilization,
      status: batch.status,
      startTime: batch.startTime,
      lastUpdate: new Date()
    }
  }

  /**
   * Finalize batch execution
   */
  private finalizeBatch(batch: BatchExecution): void {
    batch.endTime = new Date()
    
    if (batch.failedWorkflows === 0) {
      batch.status = 'completed'
    } else if (batch.completedWorkflows === 0) {
      batch.status = 'failed'
    } else {
      batch.status = 'partial'
    }

    this.emitBatchEvent(batch.id, 'batch_completed', { batch })
    
    // Cleanup after delay
    setTimeout(() => {
      this.activeBatches.delete(batch.id)
    }, 300000) // 5 minutes
  }

  /**
   * Helper methods
   */
  private generateBatchId(): string {
    return `batch_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  }

  private estimateWorkflowDuration(config: WorkflowConfig): number {
    // This would estimate based on template or historical data
    return 300000 // 5 minutes default
  }

  private calculateResourceRequirements(config: WorkflowConfig): ResourceRequirements {
    // Calculate based on workflow complexity
    return {
      cpu: 0.2,
      memory: 0.1,
      network: 0.05,
      storage: 0.02
    }
  }

  private extractDependencies(config: WorkflowConfig, index: number): string[] {
    // Extract dependencies from config or use index-based dependencies
    return index > 0 ? [`${config.labId}_workflow_${index - 1}`] : []
  }

  private calculateRetryDelay(retryCount: number, retryPolicy?: any): number {
    const baseDelay = retryPolicy?.baseDelay || 5000
    const maxDelay = retryPolicy?.maxDelay || 30000
    
    switch (retryPolicy?.backoffStrategy || 'exponential') {
      case 'exponential':
        return Math.min(baseDelay * Math.pow(2, retryCount - 1), maxDelay)
      case 'linear':
        return Math.min(baseDelay * retryCount, maxDelay)
      case 'fixed':
        return baseDelay
      default:
        return baseDelay
    }
  }

  private calculateAverageWorkflowDuration(batch: BatchExecution): number {
    const completedWorkflows = batch.workflows.filter(w => 
      w.status === 'completed' && w.startTime && w.endTime
    )
    
    if (completedWorkflows.length === 0) return 300000 // 5 minutes default

    const totalDuration = completedWorkflows.reduce((sum, workflow) => {
      return sum + (workflow.endTime!.getTime() - workflow.startTime!.getTime())
    }, 0)

    return totalDuration / completedWorkflows.length
  }

  /**
   * Event system
   */
  private emitBatchEvent(batchId: string, eventType: string, data: any): void {
    const listeners = this.batchListeners.get(batchId) || []
    listeners.forEach(listener => listener(data.batch))
  }

  addBatchListener(batchId: string, listener: (batch: BatchExecution) => void): void {
    const listeners = this.batchListeners.get(batchId) || []
    listeners.push(listener)
    this.batchListeners.set(batchId, listeners)
  }

  removeBatchListener(batchId: string, listener: (batch: BatchExecution) => void): void {
    const listeners = this.batchListeners.get(batchId) || []
    const index = listeners.indexOf(listener)
    if (index > -1) {
      listeners.splice(index, 1)
      this.batchListeners.set(batchId, listeners)
    }
  }

  /**
   * Cleanup resources
   */
  cleanup(): void {
    this.activeBatches.clear()
    this.batchListeners.clear()
    this.resourceManager.cleanup()
  }
}

/**
 * Resource Manager for batch processing
 */
class ResourceManager {
  private allocatedResources = new Map<string, ResourceRequirements>()
  private totalLimits: ResourceRequirements = {
    cpu: 1.0,
    memory: 1.0,
    network: 1.0,
    storage: 1.0
  }

  canAllocateResources(requirements: ResourceRequirements): boolean {
    const currentUsage = this.getCurrentUsage()
    
    return (
      currentUsage.cpu + requirements.cpu <= this.totalLimits.cpu &&
      currentUsage.memory + requirements.memory <= this.totalLimits.memory &&
      currentUsage.network + requirements.network <= this.totalLimits.network &&
      currentUsage.storage + requirements.storage <= this.totalLimits.storage
    )
  }

  allocateResources(workflowId: string, requirements: ResourceRequirements): void {
    this.allocatedResources.set(workflowId, requirements)
  }

  releaseResources(workflowId: string): void {
    this.allocatedResources.delete(workflowId)
  }

  getCurrentUsage(): ResourceRequirements {
    const usage = { cpu: 0, memory: 0, network: 0, storage: 0 }
    
    for (const requirements of this.allocatedResources.values()) {
      usage.cpu += requirements.cpu
      usage.memory += requirements.memory
      usage.network += requirements.network
      usage.storage += requirements.storage
    }
    
    return usage
  }

  getUtilization(): ResourceUtilization {
    const usage = this.getCurrentUsage()
    
    return {
      cpu: usage.cpu / this.totalLimits.cpu,
      memory: usage.memory / this.totalLimits.memory,
      network: usage.network / this.totalLimits.network,
      storage: usage.storage / this.totalLimits.storage,
      overall: Math.max(
        usage.cpu / this.totalLimits.cpu,
        usage.memory / this.totalLimits.memory,
        usage.network / this.totalLimits.network,
        usage.storage / this.totalLimits.storage
      )
    }
  }

  cleanup(): void {
    this.allocatedResources.clear()
  }
}

// Interfaces
interface BatchConfig {
  name: string
  description: string
  workflows: WorkflowConfig[]
  concurrencyLimit?: number
  resourceLimits?: ResourceRequirements
  retryPolicy?: {
    maxRetries: number
    backoffStrategy: 'exponential' | 'linear' | 'fixed'
    baseDelay: number
    maxDelay: number
  }
}

interface BatchExecution {
  id: string
  name: string
  description: string
  status: 'initializing' | 'running' | 'paused' | 'completed' | 'failed' | 'cancelled' | 'partial'
  workflows: BatchWorkflow[]
  startTime: Date
  endTime?: Date
  totalWorkflows: number
  completedWorkflows: number
  failedWorkflows: number
  progress: number
  resourceLimits?: ResourceRequirements
  concurrencyLimit: number
  retryPolicy?: any
  results: BatchResult[]
  errors: BatchError[]
}

interface BatchWorkflow {
  id: string
  batchId: string
  config: WorkflowConfig
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled' | 'paused'
  priority: 'low' | 'normal' | 'high'
  retryCount: number
  maxRetries: number
  estimatedDuration: number
  resourceRequirements: ResourceRequirements
  dependencies: string[]
  startTime?: Date
  endTime?: Date
  executionId?: string
  progress?: number
  result?: any
  error?: any
}

interface BatchProgress {
  batchId: string
  overallProgress: number
  completedWorkflows: number
  failedWorkflows: number
  runningWorkflows: number
  pendingWorkflows: number
  totalWorkflows: number
  estimatedTimeRemaining: number
  resourceUtilization: ResourceUtilization
  status: string
  startTime: Date
  lastUpdate: Date
}

interface BatchResult {
  workflowId: string
  success: boolean
  duration: number
  result?: any
}

interface BatchError {
  type: 'batch_initialization' | 'workflow_execution' | 'resource_exhaustion'
  message: string
  workflowId?: string
  timestamp: Date
  error?: any
}

interface ResourceRequirements {
  cpu: number
  memory: number
  network: number
  storage: number
}

interface ResourceUtilization {
  cpu: number
  memory: number
  network: number
  storage: number
  overall: number
}

// Export singleton instance
export const batchWorkflowManager = new BatchWorkflowManager()