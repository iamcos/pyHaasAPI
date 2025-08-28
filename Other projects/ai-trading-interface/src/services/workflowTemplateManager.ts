import type {
  WorkflowTemplate,
  WorkflowStepTemplate,
  OptimizationParameters
} from '@/types'
import { useWorkflowStore } from '@/stores/workflowStore'

export class WorkflowTemplateManager {
  private predefinedTemplates: WorkflowTemplate[] = []

  constructor() {
    this.initializePredefinedTemplates()
  }

  /**
   * Initialize predefined workflow templates
   */
  private initializePredefinedTemplates(): void {
    this.predefinedTemplates = [
      this.createBasicOptimizationTemplate(),
      this.createAdvancedOptimizationTemplate(),
      this.createQuickValidationTemplate(),
      this.createComprehensiveAnalysisTemplate(),
      this.createRiskAssessmentTemplate()
    ]
  }

  /**
   * Get all available templates
   */
  async getTemplates(): Promise<WorkflowTemplate[]> {
    const store = useWorkflowStore.getState()
    const customTemplates = store.templates
    
    return [...this.predefinedTemplates, ...customTemplates]
  }

  /**
   * Get template by ID
   */
  async getTemplate(templateId: string): Promise<WorkflowTemplate | null> {
    const templates = await this.getTemplates()
    return templates.find(t => t.id === templateId) || null
  }

  /**
   * Create new custom template
   */
  async createTemplate(template: Omit<WorkflowTemplate, 'id' | 'createdAt' | 'updatedAt'>): Promise<WorkflowTemplate> {
    const newTemplate: WorkflowTemplate = {
      ...template,
      id: this.generateTemplateId(),
      createdAt: new Date(),
      updatedAt: new Date()
    }

    // Validate template
    this.validateTemplate(newTemplate)

    // Add to store
    useWorkflowStore.getState().addTemplate(newTemplate)

    return newTemplate
  }

  /**
   * Update existing template
   */
  async updateTemplate(templateId: string, updates: Partial<WorkflowTemplate>): Promise<WorkflowTemplate> {
    const template = await this.getTemplate(templateId)
    if (!template) {
      throw new Error(`Template not found: ${templateId}`)
    }

    // Don't allow updating predefined templates
    if (this.isPredefinedTemplate(templateId)) {
      throw new Error('Cannot update predefined templates')
    }

    const updatedTemplate = {
      ...template,
      ...updates,
      updatedAt: new Date()
    }

    this.validateTemplate(updatedTemplate)
    useWorkflowStore.getState().updateTemplate(templateId, updates)

    return updatedTemplate
  }

  /**
   * Delete template
   */
  async deleteTemplate(templateId: string): Promise<void> {
    if (this.isPredefinedTemplate(templateId)) {
      throw new Error('Cannot delete predefined templates')
    }

    useWorkflowStore.getState().removeTemplate(templateId)
  }

  /**
   * Clone template
   */
  async cloneTemplate(templateId: string, name: string): Promise<WorkflowTemplate> {
    const template = await this.getTemplate(templateId)
    if (!template) {
      throw new Error(`Template not found: ${templateId}`)
    }

    return this.createTemplate({
      ...template,
      name,
      description: `Cloned from ${template.name}`
    })
  }

  /**
   * Get templates by category
   */
  async getTemplatesByCategory(category: WorkflowTemplate['category']): Promise<WorkflowTemplate[]> {
    const templates = await this.getTemplates()
    return templates.filter(t => t.category === category)
  }

  /**
   * Search templates
   */
  async searchTemplates(query: string): Promise<WorkflowTemplate[]> {
    const templates = await this.getTemplates()
    const lowerQuery = query.toLowerCase()
    
    return templates.filter(template => 
      template.name.toLowerCase().includes(lowerQuery) ||
      template.description.toLowerCase().includes(lowerQuery) ||
      template.tags.some(tag => tag.toLowerCase().includes(lowerQuery))
    )
  }

  /**
   * Validate template structure
   */
  private validateTemplate(template: WorkflowTemplate): void {
    if (!template.name || template.name.trim().length === 0) {
      throw new Error('Template name is required')
    }

    if (!template.steps || template.steps.length === 0) {
      throw new Error('Template must have at least one step')
    }

    // Validate step dependencies
    const stepIds = new Set(template.steps.map(s => s.id))
    for (const step of template.steps) {
      for (const depId of step.dependencies) {
        if (!stepIds.has(depId)) {
          throw new Error(`Step ${step.id} depends on non-existent step ${depId}`)
        }
      }
    }

    // Check for circular dependencies
    this.checkCircularDependencies(template.steps)
  }

  /**
   * Check for circular dependencies in steps
   */
  private checkCircularDependencies(steps: WorkflowStepTemplate[]): void {
    const visited = new Set<string>()
    const recursionStack = new Set<string>()

    const hasCycle = (stepId: string): boolean => {
      if (recursionStack.has(stepId)) return true
      if (visited.has(stepId)) return false

      visited.add(stepId)
      recursionStack.add(stepId)

      const step = steps.find(s => s.id === stepId)
      if (step) {
        for (const depId of step.dependencies) {
          if (hasCycle(depId)) return true
        }
      }

      recursionStack.delete(stepId)
      return false
    }

    for (const step of steps) {
      if (hasCycle(step.id)) {
        throw new Error('Circular dependency detected in workflow steps')
      }
    }
  }

  /**
   * Generate unique template ID
   */
  private generateTemplateId(): string {
    return `template_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  }

  /**
   * Check if template is predefined
   */
  private isPredefinedTemplate(templateId: string): boolean {
    return this.predefinedTemplates.some(t => t.id === templateId)
  }

  /**
   * Predefined template creators
   */
  private createBasicOptimizationTemplate(): WorkflowTemplate {
    return {
      id: 'basic_optimization',
      name: 'Basic Optimization',
      description: 'Simple 3-step optimization workflow for quick parameter tuning',
      category: 'optimization',
      complexity: 'simple',
      estimatedDuration: 300000, // 5 minutes
      tags: ['optimization', 'basic', 'quick'],
      steps: [
        {
          id: 'initial_backtest',
          name: 'Initial Backtest',
          type: 'backtest',
          description: 'Run initial backtest with current parameters',
          parameters: {
            timeframe: '1h',
            duration: 'short'
          },
          dependencies: [],
          estimatedDuration: 120000, // 2 minutes
          optional: false,
          retryable: true
        },
        {
          id: 'parameter_optimization',
          name: 'Parameter Optimization',
          type: 'optimization',
          description: 'Optimize key parameters based on initial results',
          parameters: {
            method: 'grid_search',
            maxIterations: 50
          },
          dependencies: ['initial_backtest'],
          estimatedDuration: 150000, // 2.5 minutes
          optional: false,
          retryable: true
        },
        {
          id: 'validation_backtest',
          name: 'Validation Backtest',
          type: 'backtest',
          description: 'Validate optimized parameters with extended backtest',
          parameters: {
            timeframe: '1h',
            duration: 'medium'
          },
          dependencies: ['parameter_optimization'],
          estimatedDuration: 180000, // 3 minutes
          optional: false,
          retryable: true
        }
      ],
      createdAt: new Date(),
      updatedAt: new Date()
    }
  }

  private createAdvancedOptimizationTemplate(): WorkflowTemplate {
    return {
      id: 'advanced_optimization',
      name: 'Advanced Optimization',
      description: 'Comprehensive 6-step optimization with multiple validation phases',
      category: 'optimization',
      complexity: 'advanced',
      estimatedDuration: 1800000, // 30 minutes
      tags: ['optimization', 'advanced', 'comprehensive'],
      steps: [
        {
          id: 'initial_analysis',
          name: 'Initial Analysis',
          type: 'analysis',
          description: 'Analyze current strategy performance and identify optimization targets',
          parameters: {
            analysisDepth: 'comprehensive'
          },
          dependencies: [],
          estimatedDuration: 180000, // 3 minutes
          optional: false,
          retryable: true
        },
        {
          id: 'parameter_space_exploration',
          name: 'Parameter Space Exploration',
          type: 'optimization',
          description: 'Explore parameter space to identify promising regions',
          parameters: {
            method: 'random_search',
            samples: 100
          },
          dependencies: ['initial_analysis'],
          estimatedDuration: 300000, // 5 minutes
          optional: false,
          retryable: true
        },
        {
          id: 'focused_optimization',
          name: 'Focused Optimization',
          type: 'optimization',
          description: 'Fine-tune parameters in promising regions',
          parameters: {
            method: 'bayesian_optimization',
            maxIterations: 200
          },
          dependencies: ['parameter_space_exploration'],
          estimatedDuration: 600000, // 10 minutes
          optional: false,
          retryable: true
        },
        {
          id: 'robustness_testing',
          name: 'Robustness Testing',
          type: 'validation',
          description: 'Test parameter robustness across different market conditions',
          parameters: {
            testPeriods: ['bull', 'bear', 'sideways'],
            sensitivity: 'high'
          },
          dependencies: ['focused_optimization'],
          estimatedDuration: 420000, // 7 minutes
          optional: false,
          retryable: true
        },
        {
          id: 'risk_assessment',
          name: 'Risk Assessment',
          type: 'analysis',
          description: 'Comprehensive risk analysis of optimized strategy',
          parameters: {
            riskMetrics: ['var', 'cvar', 'maxDrawdown', 'sharpe'],
            confidence: 0.95
          },
          dependencies: ['robustness_testing'],
          estimatedDuration: 180000, // 3 minutes
          optional: false,
          retryable: true
        },
        {
          id: 'final_validation',
          name: 'Final Validation',
          type: 'backtest',
          description: 'Final validation backtest with optimized parameters',
          parameters: {
            timeframe: '1h',
            duration: 'extended',
            outOfSample: true
          },
          dependencies: ['risk_assessment'],
          estimatedDuration: 300000, // 5 minutes
          optional: false,
          retryable: true
        }
      ],
      createdAt: new Date(),
      updatedAt: new Date()
    }
  }

  private createQuickValidationTemplate(): WorkflowTemplate {
    return {
      id: 'quick_validation',
      name: 'Quick Validation',
      description: 'Fast 2-step validation for strategy verification',
      category: 'validation',
      complexity: 'simple',
      estimatedDuration: 180000, // 3 minutes
      tags: ['validation', 'quick', 'verification'],
      steps: [
        {
          id: 'performance_check',
          name: 'Performance Check',
          type: 'backtest',
          description: 'Quick performance validation',
          parameters: {
            timeframe: '1h',
            duration: 'short'
          },
          dependencies: [],
          estimatedDuration: 90000, // 1.5 minutes
          optional: false,
          retryable: true
        },
        {
          id: 'risk_check',
          name: 'Risk Check',
          type: 'analysis',
          description: 'Basic risk metrics validation',
          parameters: {
            riskMetrics: ['maxDrawdown', 'sharpe']
          },
          dependencies: ['performance_check'],
          estimatedDuration: 90000, // 1.5 minutes
          optional: false,
          retryable: true
        }
      ],
      createdAt: new Date(),
      updatedAt: new Date()
    }
  }

  private createComprehensiveAnalysisTemplate(): WorkflowTemplate {
    return {
      id: 'comprehensive_analysis',
      name: 'Comprehensive Analysis',
      description: 'Detailed 4-step analysis workflow for strategy evaluation',
      category: 'analysis',
      complexity: 'moderate',
      estimatedDuration: 720000, // 12 minutes
      tags: ['analysis', 'comprehensive', 'evaluation'],
      steps: [
        {
          id: 'performance_analysis',
          name: 'Performance Analysis',
          type: 'analysis',
          description: 'Detailed performance metrics analysis',
          parameters: {
            metrics: ['returns', 'volatility', 'sharpe', 'sortino', 'calmar'],
            benchmarks: ['market', 'risk_free']
          },
          dependencies: [],
          estimatedDuration: 180000, // 3 minutes
          optional: false,
          retryable: true
        },
        {
          id: 'risk_analysis',
          name: 'Risk Analysis',
          type: 'analysis',
          description: 'Comprehensive risk assessment',
          parameters: {
            riskMetrics: ['var', 'cvar', 'maxDrawdown', 'beta', 'correlation'],
            confidence: [0.95, 0.99]
          },
          dependencies: ['performance_analysis'],
          estimatedDuration: 180000, // 3 minutes
          optional: false,
          retryable: true
        },
        {
          id: 'market_regime_analysis',
          name: 'Market Regime Analysis',
          type: 'analysis',
          description: 'Analyze performance across different market regimes',
          parameters: {
            regimes: ['bull', 'bear', 'high_vol', 'low_vol'],
            detection: 'automatic'
          },
          dependencies: ['risk_analysis'],
          estimatedDuration: 240000, // 4 minutes
          optional: false,
          retryable: true
        },
        {
          id: 'correlation_analysis',
          name: 'Correlation Analysis',
          type: 'analysis',
          description: 'Analyze correlations with market factors',
          parameters: {
            factors: ['market', 'size', 'value', 'momentum', 'volatility'],
            rollingWindow: 252
          },
          dependencies: ['market_regime_analysis'],
          estimatedDuration: 120000, // 2 minutes
          optional: false,
          retryable: true
        }
      ],
      createdAt: new Date(),
      updatedAt: new Date()
    }
  }

  private createRiskAssessmentTemplate(): WorkflowTemplate {
    return {
      id: 'risk_assessment',
      name: 'Risk Assessment',
      description: 'Focused 3-step risk evaluation workflow',
      category: 'analysis',
      complexity: 'moderate',
      estimatedDuration: 480000, // 8 minutes
      tags: ['risk', 'assessment', 'evaluation'],
      steps: [
        {
          id: 'var_analysis',
          name: 'VaR Analysis',
          type: 'analysis',
          description: 'Value at Risk calculation and analysis',
          parameters: {
            methods: ['historical', 'parametric', 'monte_carlo'],
            confidence: [0.95, 0.99],
            horizon: [1, 5, 10]
          },
          dependencies: [],
          estimatedDuration: 180000, // 3 minutes
          optional: false,
          retryable: true
        },
        {
          id: 'stress_testing',
          name: 'Stress Testing',
          type: 'validation',
          description: 'Stress test under extreme market conditions',
          parameters: {
            scenarios: ['market_crash', 'volatility_spike', 'liquidity_crisis'],
            severity: ['moderate', 'severe', 'extreme']
          },
          dependencies: ['var_analysis'],
          estimatedDuration: 240000, // 4 minutes
          optional: false,
          retryable: true
        },
        {
          id: 'risk_attribution',
          name: 'Risk Attribution',
          type: 'analysis',
          description: 'Attribute risk to different factors and positions',
          parameters: {
            factors: ['market', 'sector', 'style', 'specific'],
            decomposition: 'complete'
          },
          dependencies: ['stress_testing'],
          estimatedDuration: 120000, // 2 minutes
          optional: false,
          retryable: true
        }
      ],
      createdAt: new Date(),
      updatedAt: new Date()
    }
  }
}

// Export singleton instance
export const workflowTemplateManager = new WorkflowTemplateManager()