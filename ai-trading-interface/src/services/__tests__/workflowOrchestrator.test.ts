import { describe, it, expect, vi, beforeEach } from 'vitest'
import { workflowOrchestrator } from '../workflowOrchestrator'
import { createMockWorkflowExecution, createMockWorkflowStep } from '../../test/mocks/workflowService'
import type { WorkflowConfig, WorkflowStep } from '../../types/workflow'

// Mock dependencies
vi.mock('../mcpClient', () => ({
  mcpClient: {
    labs: {
      backtest: vi.fn().mockResolvedValue({ id: 'backtest-1', status: 'completed' }),
      getStatus: vi.fn().mockResolvedValue({ status: 'running' }),
    },
  },
}))

vi.mock('../workflowCheckpointManager', () => ({
  workflowCheckpointManager: {
    saveCheckpoint: vi.fn().mockResolvedValue(true),
    loadCheckpoint: vi.fn().mockResolvedValue(null),
    deleteCheckpoint: vi.fn().mockResolvedValue(true),
  },
}))

describe('WorkflowOrchestrator', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('executeWorkflow', () => {
    it('executes a simple workflow successfully', async () => {
      const config: WorkflowConfig = {
        templateId: 'basic-optimization',
        labId: 'lab-1',
        parameters: { period: 14 },
        persona: { type: 'balanced', riskTolerance: 0.5 },
        resumable: true,
      }

      const result = await workflowOrchestrator.executeWorkflow(config)

      expect(result).toBeDefined()
      expect(result.id).toBeDefined()
      expect(result.status).toBe('running')
      expect(result.type).toBe('chain_of_thought_optimization')
    })

    it('handles workflow execution errors', async () => {
      const config: WorkflowConfig = {
        templateId: 'invalid-template',
        labId: 'lab-1',
        parameters: {},
        persona: { type: 'balanced', riskTolerance: 0.5 },
        resumable: false,
      }

      await expect(workflowOrchestrator.executeWorkflow(config))
        .rejects.toThrow('Template not found')
    })

    it('saves checkpoints for resumable workflows', async () => {
      const config: WorkflowConfig = {
        templateId: 'basic-optimization',
        labId: 'lab-1',
        parameters: { period: 14 },
        persona: { type: 'balanced', riskTolerance: 0.5 },
        resumable: true,
      }

      await workflowOrchestrator.executeWorkflow(config)

      const { workflowCheckpointManager } = await import('../workflowCheckpointManager')
      expect(workflowCheckpointManager.saveCheckpoint).toHaveBeenCalled()
    })
  })

  describe('executeStep', () => {
    it('executes analysis step successfully', async () => {
      const step: WorkflowStep = createMockWorkflowStep({
        id: 'step-1',
        name: 'Market Analysis',
        type: 'analysis',
        status: 'pending',
      })

      const context = {
        workflowId: 'workflow-1',
        labId: 'lab-1',
        parameters: { period: 14 },
        persona: { type: 'balanced', riskTolerance: 0.5 },
      }

      const result = await workflowOrchestrator.executeStep(step, context)

      expect(result).toBeDefined()
      expect(result.status).toBe('completed')
      expect(result.result).toBeDefined()
    })

    it('executes backtest step successfully', async () => {
      const step: WorkflowStep = createMockWorkflowStep({
        id: 'step-2',
        name: 'Backtest Strategy',
        type: 'backtest',
        status: 'pending',
      })

      const context = {
        workflowId: 'workflow-1',
        labId: 'lab-1',
        parameters: { period: 14 },
        persona: { type: 'balanced', riskTolerance: 0.5 },
      }

      const result = await workflowOrchestrator.executeStep(step, context)

      expect(result).toBeDefined()
      expect(result.status).toBe('completed')
      
      const { mcpClient } = await import('../mcpClient')
      expect(mcpClient.labs.backtest).toHaveBeenCalledWith('lab-1', expect.any(Object))
    })

    it('handles step execution failures', async () => {
      const step: WorkflowStep = createMockWorkflowStep({
        id: 'step-fail',
        name: 'Failing Step',
        type: 'analysis',
        status: 'pending',
      })

      const context = {
        workflowId: 'workflow-1',
        labId: 'invalid-lab',
        parameters: {},
        persona: { type: 'balanced', riskTolerance: 0.5 },
      }

      const result = await workflowOrchestrator.executeStep(step, context)

      expect(result.status).toBe('failed')
      expect(result.error).toBeDefined()
    })
  })

  describe('resumeWorkflow', () => {
    it('resumes workflow from checkpoint', async () => {
      const workflowId = 'workflow-1'
      
      // Mock checkpoint data
      const { workflowCheckpointManager } = await import('../workflowCheckpointManager')
      vi.mocked(workflowCheckpointManager.loadCheckpoint).mockResolvedValue({
        workflowId,
        currentStep: 2,
        completedSteps: ['step-1'],
        context: {
          labId: 'lab-1',
          parameters: { period: 14 },
          persona: { type: 'balanced', riskTolerance: 0.5 },
        },
        timestamp: new Date(),
      })

      const result = await workflowOrchestrator.resumeWorkflow(workflowId)

      expect(result).toBeDefined()
      expect(result.status).toBe('running')
      expect(result.currentStep).toBe(2)
    })

    it('handles missing checkpoint gracefully', async () => {
      const workflowId = 'nonexistent-workflow'

      await expect(workflowOrchestrator.resumeWorkflow(workflowId))
        .rejects.toThrow('Workflow checkpoint not found')
    })
  })

  describe('pauseWorkflow', () => {
    it('pauses running workflow', async () => {
      const workflowId = 'workflow-1'

      const result = await workflowOrchestrator.pauseWorkflow(workflowId)

      expect(result).toBe(true)
    })

    it('handles pausing non-existent workflow', async () => {
      const workflowId = 'nonexistent-workflow'

      await expect(workflowOrchestrator.pauseWorkflow(workflowId))
        .rejects.toThrow('Workflow not found')
    })
  })

  describe('cancelWorkflow', () => {
    it('cancels running workflow', async () => {
      const workflowId = 'workflow-1'

      const result = await workflowOrchestrator.cancelWorkflow(workflowId)

      expect(result).toBe(true)
    })

    it('cleans up resources when cancelling', async () => {
      const workflowId = 'workflow-1'

      await workflowOrchestrator.cancelWorkflow(workflowId)

      const { workflowCheckpointManager } = await import('../workflowCheckpointManager')
      expect(workflowCheckpointManager.deleteCheckpoint).toHaveBeenCalledWith(workflowId)
    })
  })

  describe('getWorkflowProgress', () => {
    it('returns progress for active workflow', async () => {
      const workflowId = 'workflow-1'

      const progress = await workflowOrchestrator.getWorkflowProgress(workflowId)

      expect(progress).toBeDefined()
      expect(progress.workflowId).toBe(workflowId)
      expect(progress.progress).toBeGreaterThanOrEqual(0)
      expect(progress.progress).toBeLessThanOrEqual(100)
    })

    it('handles progress request for non-existent workflow', async () => {
      const workflowId = 'nonexistent-workflow'

      await expect(workflowOrchestrator.getWorkflowProgress(workflowId))
        .rejects.toThrow('Workflow not found')
    })
  })

  describe('state transitions', () => {
    it('transitions workflow states correctly', async () => {
      const workflow = createMockWorkflowExecution({
        status: 'pending',
        currentStep: 0,
      })

      // Start workflow
      const startedWorkflow = await workflowOrchestrator.startWorkflow(workflow)
      expect(startedWorkflow.status).toBe('running')

      // Complete step
      const updatedWorkflow = await workflowOrchestrator.completeStep(
        startedWorkflow.id,
        startedWorkflow.steps[0].id
      )
      expect(updatedWorkflow.currentStep).toBe(1)

      // Complete workflow
      const completedWorkflow = await workflowOrchestrator.completeWorkflow(updatedWorkflow.id)
      expect(completedWorkflow.status).toBe('completed')
    })

    it('validates state transitions', async () => {
      const workflow = createMockWorkflowExecution({
        status: 'completed',
      })

      // Should not be able to start a completed workflow
      await expect(workflowOrchestrator.startWorkflow(workflow))
        .rejects.toThrow('Invalid state transition')
    })
  })

  describe('dependency management', () => {
    it('respects step dependencies', async () => {
      const config: WorkflowConfig = {
        customSteps: [
          {
            id: 'step-1',
            name: 'First Step',
            type: 'analysis',
            description: 'Initial analysis',
            parameters: {},
            dependencies: [],
            estimatedDuration: 300,
          },
          {
            id: 'step-2',
            name: 'Second Step',
            type: 'backtest',
            description: 'Backtest based on analysis',
            parameters: {},
            dependencies: ['step-1'],
            estimatedDuration: 600,
          },
        ],
        labId: 'lab-1',
        parameters: {},
        persona: { type: 'balanced', riskTolerance: 0.5 },
        resumable: true,
      }

      const workflow = await workflowOrchestrator.executeWorkflow(config)

      // Step 2 should not execute until step 1 is completed
      expect(workflow.steps[1].status).toBe('pending')
      expect(workflow.steps[0].status).toBe('running')
    })

    it('handles circular dependencies', async () => {
      const config: WorkflowConfig = {
        customSteps: [
          {
            id: 'step-1',
            name: 'First Step',
            type: 'analysis',
            description: 'First step',
            parameters: {},
            dependencies: ['step-2'],
            estimatedDuration: 300,
          },
          {
            id: 'step-2',
            name: 'Second Step',
            type: 'analysis',
            description: 'Second step',
            parameters: {},
            dependencies: ['step-1'],
            estimatedDuration: 300,
          },
        ],
        labId: 'lab-1',
        parameters: {},
        persona: { type: 'balanced', riskTolerance: 0.5 },
        resumable: false,
      }

      await expect(workflowOrchestrator.executeWorkflow(config))
        .rejects.toThrow('Circular dependency detected')
    })
  })
})