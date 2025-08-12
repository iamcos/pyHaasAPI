import { vi } from 'vitest'
import type { WorkflowExecution, WorkflowStep, WorkflowTemplate } from '../../types/workflow'

export const mockWorkflowService = {
  executeWorkflow: vi.fn().mockResolvedValue({
    id: 'workflow-1',
    type: 'chain_of_thought_optimization',
    status: 'running',
    currentStep: 1,
    totalSteps: 5,
    steps: [
      {
        id: 'step-1',
        name: 'Initial Analysis',
        status: 'completed',
        type: 'analysis',
        result: { analysis: 'Mock analysis result' },
      },
      {
        id: 'step-2',
        name: 'Backtest',
        status: 'running',
        type: 'backtest',
      },
    ],
    chainOfThought: [],
    startTime: new Date(),
  } as WorkflowExecution),

  getWorkflowTemplates: vi.fn().mockResolvedValue([
    {
      id: 'template-1',
      name: 'Basic Optimization',
      description: 'Basic strategy optimization workflow',
      steps: [
        {
          id: 'step-1',
          name: 'Analysis',
          type: 'analysis',
          description: 'Analyze strategy parameters',
          parameters: {},
          dependencies: [],
          estimatedDuration: 300,
        },
      ],
      estimatedDuration: 1800,
      complexity: 'simple',
    },
  ] as WorkflowTemplate[]),

  resumeWorkflow: vi.fn().mockResolvedValue({
    id: 'workflow-1',
    status: 'resumed',
  }),

  pauseWorkflow: vi.fn().mockResolvedValue(true),
  cancelWorkflow: vi.fn().mockResolvedValue(true),
  
  getWorkflowProgress: vi.fn().mockResolvedValue({
    workflowId: 'workflow-1',
    currentStep: 2,
    totalSteps: 5,
    progress: 40,
    estimatedTimeRemaining: 900,
  }),
}

export const createMockWorkflowExecution = (overrides?: Partial<WorkflowExecution>): WorkflowExecution => ({
  id: 'workflow-1',
  type: 'chain_of_thought_optimization',
  status: 'running',
  currentStep: 1,
  totalSteps: 3,
  steps: [],
  results: [],
  chainOfThought: [],
  startTime: new Date(),
  ...overrides,
})

export const createMockWorkflowStep = (overrides?: Partial<WorkflowStep>): WorkflowStep => ({
  id: 'step-1',
  name: 'Test Step',
  status: 'pending',
  type: 'analysis',
  ...overrides,
})