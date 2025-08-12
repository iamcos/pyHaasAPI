import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { 
  WorkflowExecution, 
  WorkflowTemplate, 
  WorkflowStep,
  WorkflowConfig,
  WorkflowProgress 
} from '@/types'

interface WorkflowState {
  // Workflow data
  templates: WorkflowTemplate[]
  executions: WorkflowExecution[]
  activeExecution: string | null
  
  // UI state
  selectedTemplate: string | null
  showWorkflowBuilder: boolean
  
  // Loading and error states
  loading: {
    templates: boolean
    executions: boolean
    creating: boolean
    executing: boolean
  }
  
  errors: {
    templates: string | null
    executions: string | null
    execution: string | null
  }
  
  // Actions
  setTemplates: (templates: WorkflowTemplate[]) => void
  addTemplate: (template: WorkflowTemplate) => void
  updateTemplate: (id: string, updates: Partial<WorkflowTemplate>) => void
  removeTemplate: (id: string) => void
  selectTemplate: (id: string | null) => void
  
  setExecutions: (executions: WorkflowExecution[]) => void
  addExecution: (execution: WorkflowExecution) => void
  updateExecution: (id: string, updates: Partial<WorkflowExecution>) => void
  removeExecution: (id: string) => void
  setActiveExecution: (id: string | null) => void
  
  updateExecutionStep: (executionId: string, stepId: string, updates: Partial<WorkflowStep>) => void
  getExecutionProgress: (executionId: string) => WorkflowProgress | null
  
  setShowWorkflowBuilder: (show: boolean) => void
  
  setLoading: (key: keyof WorkflowState['loading'], loading: boolean) => void
  setError: (key: keyof WorkflowState['errors'], error: string | null) => void
  clearErrors: () => void
  
  // Workflow execution helpers
  canResumeExecution: (executionId: string) => boolean
  getNextStep: (executionId: string) => WorkflowStep | null
  isExecutionComplete: (executionId: string) => boolean
}

export const useWorkflowStore = create<WorkflowState>()(
  persist(
    (set, get) => ({
      // Initial state
      templates: [],
      executions: [],
      activeExecution: null,
      selectedTemplate: null,
      showWorkflowBuilder: false,
      
      loading: {
        templates: false,
        executions: false,
        creating: false,
        executing: false,
      },
      
      errors: {
        templates: null,
        executions: null,
        execution: null,
      },
      
      // Template actions
      setTemplates: (templates) => set({ templates }),
      
      addTemplate: (template) => set((state) => ({
        templates: [...state.templates, template]
      })),
      
      updateTemplate: (id, updates) => set((state) => ({
        templates: state.templates.map(template =>
          template.id === id ? { ...template, ...updates, updatedAt: new Date() } : template
        )
      })),
      
      removeTemplate: (id) => set((state) => ({
        templates: state.templates.filter(template => template.id !== id),
        selectedTemplate: state.selectedTemplate === id ? null : state.selectedTemplate
      })),
      
      selectTemplate: (id) => set({ selectedTemplate: id }),
      
      // Execution actions
      setExecutions: (executions) => set({ executions }),
      
      addExecution: (execution) => set((state) => ({
        executions: [...state.executions, execution]
      })),
      
      updateExecution: (id, updates) => set((state) => ({
        executions: state.executions.map(execution =>
          execution.id === id ? { ...execution, ...updates } : execution
        )
      })),
      
      removeExecution: (id) => set((state) => ({
        executions: state.executions.filter(execution => execution.id !== id),
        activeExecution: state.activeExecution === id ? null : state.activeExecution
      })),
      
      setActiveExecution: (id) => set({ activeExecution: id }),
      
      updateExecutionStep: (executionId, stepId, updates) => set((state) => ({
        executions: state.executions.map(execution => {
          if (execution.id !== executionId) return execution
          
          return {
            ...execution,
            steps: execution.steps.map(step =>
              step.id === stepId ? { ...step, ...updates } : step
            )
          }
        })
      })),
      
      getExecutionProgress: (executionId) => {
        const execution = get().executions.find(e => e.id === executionId)
        if (!execution) return null
        
        const completedSteps = execution.steps.filter(step => step.status === 'completed').length
        const totalSteps = execution.steps.length
        const currentStep = execution.steps.find(step => step.status === 'running')
        
        return {
          executionId,
          currentStep: execution.currentStep,
          totalSteps: execution.totalSteps,
          overallProgress: totalSteps > 0 ? (completedSteps / totalSteps) * 100 : 0,
          stepProgress: currentStep?.progress || 0,
          estimatedTimeRemaining: 0, // Calculate based on step durations
          status: execution.status,
          lastUpdate: new Date(),
        }
      },
      
      setShowWorkflowBuilder: (show) => set({ showWorkflowBuilder: show }),
      
      // Utility actions
      setLoading: (key, loading) => set((state) => ({
        loading: { ...state.loading, [key]: loading }
      })),
      
      setError: (key, error) => set((state) => ({
        errors: { ...state.errors, [key]: error }
      })),
      
      clearErrors: () => set({
        errors: {
          templates: null,
          executions: null,
          execution: null,
        }
      }),
      
      // Helper functions
      canResumeExecution: (executionId) => {
        const execution = get().executions.find(e => e.id === executionId)
        return execution?.status === 'paused' || execution?.status === 'failed'
      },
      
      getNextStep: (executionId) => {
        const execution = get().executions.find(e => e.id === executionId)
        if (!execution) return null
        
        return execution.steps.find(step => step.status === 'pending') || null
      },
      
      isExecutionComplete: (executionId) => {
        const execution = get().executions.find(e => e.id === executionId)
        return execution?.status === 'completed'
      },
    }),
    {
      name: 'workflow-store',
      partialize: (state) => ({
        // Persist templates and non-active executions
        templates: state.templates,
        executions: state.executions.filter(e => e.status === 'completed' || e.status === 'paused'),
        selectedTemplate: state.selectedTemplate,
        // Don't persist active executions or UI state
      }),
    }
  )
)