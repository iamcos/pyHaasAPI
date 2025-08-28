import type {
  WorkflowExecution,
  WorkflowStep,
  ResumeData,
  StepState,
  WorkflowError
} from '@/types'
import { useWorkflowStore } from '@/stores/workflowStore'

export class WorkflowCheckpointManager {
  private checkpointStorage = new Map<string, WorkflowCheckpoint>()
  private checkpointInterval: number = 30000 // 30 seconds
  private activeCheckpointers = new Map<string, NodeJS.Timeout>()

  /**
   * Start automatic checkpointing for a workflow execution
   */
  startCheckpointing(executionId: string): void {
    if (this.activeCheckpointers.has(executionId)) {
      this.stopCheckpointing(executionId)
    }

    const interval = setInterval(() => {
      this.createCheckpoint(executionId)
    }, this.checkpointInterval)

    this.activeCheckpointers.set(executionId, interval)
  }

  /**
   * Stop automatic checkpointing for a workflow execution
   */
  stopCheckpointing(executionId: string): void {
    const interval = this.activeCheckpointers.get(executionId)
    if (interval) {
      clearInterval(interval)
      this.activeCheckpointers.delete(executionId)
    }
  }

  /**
   * Create a checkpoint for the current workflow state
   */
  async createCheckpoint(executionId: string): Promise<string> {
    const execution = this.getExecution(executionId)
    if (!execution) {
      throw new Error(`Execution not found: ${executionId}`)
    }

    const checkpointId = this.generateCheckpointId(executionId)
    
    const checkpoint: WorkflowCheckpoint = {
      id: checkpointId,
      executionId,
      timestamp: new Date(),
      executionState: this.captureExecutionState(execution),
      stepStates: this.captureStepStates(execution.steps),
      contextData: this.captureContextData(execution),
      version: this.getCheckpointVersion(),
      metadata: {
        currentStep: execution.currentStep,
        totalSteps: execution.totalSteps,
        status: execution.status,
        completedSteps: execution.steps.filter(s => s.status === 'completed').length,
        failedSteps: execution.steps.filter(s => s.status === 'failed').length
      }
    }

    // Store checkpoint
    this.checkpointStorage.set(checkpointId, checkpoint)
    
    // Persist to IndexedDB for durability
    await this.persistCheckpoint(checkpoint)
    
    // Update execution with latest checkpoint
    this.updateExecutionResumeData(execution, checkpointId, checkpoint)

    return checkpointId
  }

  /**
   * Resume workflow from a checkpoint
   */
  async resumeFromCheckpoint(checkpointId: string): Promise<WorkflowExecution> {
    const checkpoint = await this.getCheckpoint(checkpointId)
    if (!checkpoint) {
      throw new Error(`Checkpoint not found: ${checkpointId}`)
    }

    // Validate checkpoint compatibility
    await this.validateCheckpoint(checkpoint)

    // Restore execution state
    const execution = await this.restoreExecutionFromCheckpoint(checkpoint)
    
    // Update workflow store
    const store = useWorkflowStore.getState()
    store.updateExecution(execution.id, execution)
    
    // Restart checkpointing
    this.startCheckpointing(execution.id)

    return execution
  }

  /**
   * Get available checkpoints for an execution
   */
  async getCheckpointsForExecution(executionId: string): Promise<WorkflowCheckpoint[]> {
    const checkpoints: WorkflowCheckpoint[] = []
    
    // Get from memory
    for (const checkpoint of this.checkpointStorage.values()) {
      if (checkpoint.executionId === executionId) {
        checkpoints.push(checkpoint)
      }
    }
    
    // Get from persistent storage
    const persistedCheckpoints = await this.getPersistedCheckpoints(executionId)
    
    // Merge and deduplicate
    const allCheckpoints = [...checkpoints, ...persistedCheckpoints]
    const uniqueCheckpoints = allCheckpoints.filter((checkpoint, index, array) => 
      array.findIndex(c => c.id === checkpoint.id) === index
    )
    
    // Sort by timestamp (newest first)
    return uniqueCheckpoints.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime())
  }

  /**
   * Delete checkpoint
   */
  async deleteCheckpoint(checkpointId: string): Promise<void> {
    this.checkpointStorage.delete(checkpointId)
    await this.deletePersistedCheckpoint(checkpointId)
  }

  /**
   * Clean up old checkpoints
   */
  async cleanupOldCheckpoints(executionId: string, keepCount: number = 5): Promise<void> {
    const checkpoints = await this.getCheckpointsForExecution(executionId)
    const toDelete = checkpoints.slice(keepCount)
    
    for (const checkpoint of toDelete) {
      await this.deleteCheckpoint(checkpoint.id)
    }
  }

  /**
   * Capture execution state
   */
  private captureExecutionState(execution: WorkflowExecution): ExecutionState {
    return {
      id: execution.id,
      type: execution.type,
      templateId: execution.templateId,
      status: execution.status,
      currentStep: execution.currentStep,
      totalSteps: execution.totalSteps,
      startTime: execution.startTime,
      chainOfThought: [...execution.chainOfThought],
      results: [...execution.results]
    }
  }

  /**
   * Capture step states
   */
  private captureStepStates(steps: WorkflowStep[]): StepState[] {
    return steps.map(step => ({
      stepId: step.id,
      status: step.status,
      progress: step.progress,
      data: {
        templateId: step.templateId,
        name: step.name,
        type: step.type,
        parameters: { ...step.parameters },
        startTime: step.startTime,
        endTime: step.endTime,
        result: step.result ? { ...step.result } : undefined,
        error: step.error ? { ...step.error } : undefined,
        chainOfThought: [...step.chainOfThought]
      }
    }))
  }

  /**
   * Capture context data
   */
  private captureContextData(execution: WorkflowExecution): any {
    return {
      executionId: execution.id,
      templateId: execution.templateId,
      timestamp: new Date(),
      environment: {
        userAgent: navigator.userAgent,
        timestamp: Date.now(),
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone
      }
    }
  }

  /**
   * Restore execution from checkpoint
   */
  private async restoreExecutionFromCheckpoint(checkpoint: WorkflowCheckpoint): Promise<WorkflowExecution> {
    const executionState = checkpoint.executionState
    const stepStates = checkpoint.stepStates

    // Restore steps
    const restoredSteps: WorkflowStep[] = stepStates.map(stepState => ({
      id: stepState.stepId,
      templateId: stepState.data.templateId,
      name: stepState.data.name,
      type: stepState.data.type,
      status: stepState.status,
      parameters: stepState.data.parameters,
      startTime: stepState.data.startTime,
      endTime: stepState.data.endTime,
      progress: stepState.progress,
      result: stepState.data.result,
      error: stepState.data.error,
      chainOfThought: stepState.data.chainOfThought
    }))

    // Create restored execution
    const restoredExecution: WorkflowExecution = {
      id: executionState.id,
      type: executionState.type,
      templateId: executionState.templateId,
      status: 'paused', // Always resume as paused initially
      currentStep: executionState.currentStep,
      totalSteps: executionState.totalSteps,
      steps: restoredSteps,
      results: executionState.results,
      chainOfThought: executionState.chainOfThought,
      startTime: executionState.startTime,
      resumeData: {
        checkpointId: checkpoint.id,
        stepStates: checkpoint.stepStates,
        contextData: checkpoint.contextData,
        timestamp: checkpoint.timestamp
      }
    }

    return restoredExecution
  }

  /**
   * Validate checkpoint compatibility
   */
  private async validateCheckpoint(checkpoint: WorkflowCheckpoint): Promise<void> {
    // Check version compatibility
    const currentVersion = this.getCheckpointVersion()
    if (!this.isVersionCompatible(checkpoint.version, currentVersion)) {
      throw new Error(`Checkpoint version ${checkpoint.version} is not compatible with current version ${currentVersion}`)
    }

    // Validate checkpoint integrity
    if (!checkpoint.executionState || !checkpoint.stepStates) {
      throw new Error('Checkpoint data is corrupted or incomplete')
    }

    // Validate step consistency
    const stepIds = new Set(checkpoint.stepStates.map(s => s.stepId))
    if (stepIds.size !== checkpoint.stepStates.length) {
      throw new Error('Checkpoint contains duplicate step states')
    }
  }

  /**
   * Update execution with resume data
   */
  private updateExecutionResumeData(
    execution: WorkflowExecution, 
    checkpointId: string, 
    checkpoint: WorkflowCheckpoint
  ): void {
    execution.resumeData = {
      checkpointId,
      stepStates: checkpoint.stepStates,
      contextData: checkpoint.contextData,
      timestamp: checkpoint.timestamp
    }

    // Update in store
    const store = useWorkflowStore.getState()
    store.updateExecution(execution.id, { resumeData: execution.resumeData })
  }

  /**
   * Persist checkpoint to IndexedDB
   */
  private async persistCheckpoint(checkpoint: WorkflowCheckpoint): Promise<void> {
    try {
      const db = await this.openCheckpointDB()
      const transaction = db.transaction(['checkpoints'], 'readwrite')
      const store = transaction.objectStore('checkpoints')
      
      await new Promise<void>((resolve, reject) => {
        const request = store.put({
          ...checkpoint,
          timestamp: checkpoint.timestamp.toISOString() // Serialize date
        })
        request.onsuccess = () => resolve()
        request.onerror = () => reject(request.error)
      })
    } catch (error) {
      console.error('Failed to persist checkpoint:', error)
      // Don't throw - checkpointing should be resilient
    }
  }

  /**
   * Get persisted checkpoints
   */
  private async getPersistedCheckpoints(executionId: string): Promise<WorkflowCheckpoint[]> {
    try {
      const db = await this.openCheckpointDB()
      const transaction = db.transaction(['checkpoints'], 'readonly')
      const store = transaction.objectStore('checkpoints')
      const index = store.index('executionId')
      
      return new Promise<WorkflowCheckpoint[]>((resolve, reject) => {
        const request = index.getAll(executionId)
        request.onsuccess = () => {
          const checkpoints = request.result.map((data: any) => ({
            ...data,
            timestamp: new Date(data.timestamp) // Deserialize date
          }))
          resolve(checkpoints)
        }
        request.onerror = () => reject(request.error)
      })
    } catch (error) {
      console.error('Failed to get persisted checkpoints:', error)
      return []
    }
  }

  /**
   * Delete persisted checkpoint
   */
  private async deletePersistedCheckpoint(checkpointId: string): Promise<void> {
    try {
      const db = await this.openCheckpointDB()
      const transaction = db.transaction(['checkpoints'], 'readwrite')
      const store = transaction.objectStore('checkpoints')
      
      await new Promise<void>((resolve, reject) => {
        const request = store.delete(checkpointId)
        request.onsuccess = () => resolve()
        request.onerror = () => reject(request.error)
      })
    } catch (error) {
      console.error('Failed to delete persisted checkpoint:', error)
    }
  }

  /**
   * Open IndexedDB for checkpoints
   */
  private async openCheckpointDB(): Promise<IDBDatabase> {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open('WorkflowCheckpoints', 1)
      
      request.onerror = () => reject(request.error)
      request.onsuccess = () => resolve(request.result)
      
      request.onupgradeneeded = (event) => {
        const db = (event.target as IDBOpenDBRequest).result
        
        if (!db.objectStoreNames.contains('checkpoints')) {
          const store = db.createObjectStore('checkpoints', { keyPath: 'id' })
          store.createIndex('executionId', 'executionId', { unique: false })
          store.createIndex('timestamp', 'timestamp', { unique: false })
        }
      }
    })
  }

  /**
   * Get checkpoint
   */
  private async getCheckpoint(checkpointId: string): Promise<WorkflowCheckpoint | null> {
    // Try memory first
    const memoryCheckpoint = this.checkpointStorage.get(checkpointId)
    if (memoryCheckpoint) return memoryCheckpoint

    // Try persistent storage
    try {
      const db = await this.openCheckpointDB()
      const transaction = db.transaction(['checkpoints'], 'readonly')
      const store = transaction.objectStore('checkpoints')
      
      return new Promise<WorkflowCheckpoint | null>((resolve, reject) => {
        const request = store.get(checkpointId)
        request.onsuccess = () => {
          const data = request.result
          if (data) {
            const checkpoint: WorkflowCheckpoint = {
              ...data,
              timestamp: new Date(data.timestamp)
            }
            resolve(checkpoint)
          } else {
            resolve(null)
          }
        }
        request.onerror = () => reject(request.error)
      })
    } catch (error) {
      console.error('Failed to get checkpoint:', error)
      return null
    }
  }

  /**
   * Get execution from store
   */
  private getExecution(executionId: string): WorkflowExecution | null {
    const store = useWorkflowStore.getState()
    return store.executions.find(e => e.id === executionId) || null
  }

  /**
   * Generate checkpoint ID
   */
  private generateCheckpointId(executionId: string): string {
    return `checkpoint_${executionId}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  }

  /**
   * Get current checkpoint version
   */
  private getCheckpointVersion(): string {
    return '1.0.0'
  }

  /**
   * Check version compatibility
   */
  private isVersionCompatible(checkpointVersion: string, currentVersion: string): boolean {
    // Simple version compatibility check
    const [checkpointMajor] = checkpointVersion.split('.').map(Number)
    const [currentMajor] = currentVersion.split('.').map(Number)
    
    return checkpointMajor === currentMajor
  }

  /**
   * Get checkpoint statistics
   */
  async getCheckpointStats(executionId: string): Promise<CheckpointStats> {
    const checkpoints = await this.getCheckpointsForExecution(executionId)
    
    return {
      totalCheckpoints: checkpoints.length,
      oldestCheckpoint: checkpoints.length > 0 ? 
        checkpoints[checkpoints.length - 1].timestamp : null,
      newestCheckpoint: checkpoints.length > 0 ? 
        checkpoints[0].timestamp : null,
      totalSize: checkpoints.reduce((sum, cp) => sum + this.estimateCheckpointSize(cp), 0),
      averageInterval: this.calculateAverageInterval(checkpoints)
    }
  }

  /**
   * Estimate checkpoint size
   */
  private estimateCheckpointSize(checkpoint: WorkflowCheckpoint): number {
    return JSON.stringify(checkpoint).length
  }

  /**
   * Calculate average interval between checkpoints
   */
  private calculateAverageInterval(checkpoints: WorkflowCheckpoint[]): number {
    if (checkpoints.length < 2) return 0
    
    const intervals: number[] = []
    for (let i = 0; i < checkpoints.length - 1; i++) {
      const interval = checkpoints[i].timestamp.getTime() - checkpoints[i + 1].timestamp.getTime()
      intervals.push(interval)
    }
    
    return intervals.reduce((sum, interval) => sum + interval, 0) / intervals.length
  }

  /**
   * Cleanup resources
   */
  cleanup(): void {
    // Stop all active checkpointers
    for (const [executionId] of this.activeCheckpointers) {
      this.stopCheckpointing(executionId)
    }
    
    // Clear memory storage
    this.checkpointStorage.clear()
  }
}

interface WorkflowCheckpoint {
  id: string
  executionId: string
  timestamp: Date
  executionState: ExecutionState
  stepStates: StepState[]
  contextData: any
  version: string
  metadata: CheckpointMetadata
}

interface ExecutionState {
  id: string
  type: string
  templateId?: string
  status: string
  currentStep: number
  totalSteps: number
  startTime: Date
  chainOfThought: any[]
  results: any[]
}

interface CheckpointMetadata {
  currentStep: number
  totalSteps: number
  status: string
  completedSteps: number
  failedSteps: number
}

interface CheckpointStats {
  totalCheckpoints: number
  oldestCheckpoint: Date | null
  newestCheckpoint: Date | null
  totalSize: number
  averageInterval: number
}

// Export singleton instance
export const workflowCheckpointManager = new WorkflowCheckpointManager()