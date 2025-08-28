import type {
  WorkflowConfig,
  WorkflowTemplate,
  OptimizationParameters,
  NumericalParameter,
  StructuralParameter,
  OptimizationConstraint,
  RetryPolicy,
  Persona
} from '@/types'
import { workflowTemplateManager } from './workflowTemplateManager'
import { useWorkflowStore } from '@/stores/workflowStore'

export class WorkflowConfigManager {
  private defaultConfigs = new Map<string, Partial<WorkflowConfig>>()

  constructor() {
    this.initializeDefaultConfigs()
  }

  /**
   * Initialize default configurations for different workflow types
   */
  private initializeDefaultConfigs(): void {
    this.defaultConfigs.set('basic_optimization', {
      resumable: true,
      priority: 'normal',
      timeout: 600000, // 10 minutes
      retryPolicy: {
        maxRetries: 3,
        backoffStrategy: 'exponential',
        baseDelay: 1000,
        maxDelay: 10000
      }
    })

    this.defaultConfigs.set('advanced_optimization', {
      resumable: true,
      priority: 'high',
      timeout: 3600000, // 60 minutes
      retryPolicy: {
        maxRetries: 5,
        backoffStrategy: 'exponential',
        baseDelay: 2000,
        maxDelay: 30000
      }
    })

    this.defaultConfigs.set('quick_validation', {
      resumable: false,
      priority: 'high',
      timeout: 300000, // 5 minutes
      retryPolicy: {
        maxRetries: 2,
        backoffStrategy: 'linear',
        baseDelay: 500,
        maxDelay: 2000
      }
    })
  }

  /**
   * Create workflow configuration from template
   */
  async createConfigFromTemplate(
    templateId: string,
    labId: string,
    persona: Persona,
    customParameters?: Partial<OptimizationParameters>
  ): Promise<WorkflowConfig> {
    const template = await workflowTemplateManager.getTemplate(templateId)
    if (!template) {
      throw new Error(`Template not found: ${templateId}`)
    }

    const defaultConfig = this.defaultConfigs.get(templateId) || {}
    const optimizationParams = this.createOptimizationParameters(template, customParameters)

    const config: WorkflowConfig = {
      templateId,
      labId,
      persona,
      parameters: optimizationParams,
      resumable: defaultConfig.resumable ?? true,
      priority: defaultConfig.priority ?? 'normal',
      timeout: defaultConfig.timeout,
      retryPolicy: defaultConfig.retryPolicy
    }

    return this.validateConfig(config)
  }

  /**
   * Create custom workflow configuration
   */
  async createCustomConfig(
    customSteps: any[],
    labId: string,
    persona: Persona,
    parameters: OptimizationParameters,
    options?: Partial<WorkflowConfig>
  ): Promise<WorkflowConfig> {
    const config: WorkflowConfig = {
      customSteps,
      labId,
      persona,
      parameters,
      resumable: options?.resumable ?? true,
      priority: options?.priority ?? 'normal',
      timeout: options?.timeout,
      retryPolicy: options?.retryPolicy ?? this.getDefaultRetryPolicy()
    }

    return this.validateConfig(config)
  }

  /**
   * Update existing configuration
   */
  async updateConfig(
    config: WorkflowConfig,
    updates: Partial<WorkflowConfig>
  ): Promise<WorkflowConfig> {
    const updatedConfig = { ...config, ...updates }
    return this.validateConfig(updatedConfig)
  }

  /**
   * Create optimization parameters based on template and customizations
   */
  private createOptimizationParameters(
    template: WorkflowTemplate,
    customParameters?: Partial<OptimizationParameters>
  ): OptimizationParameters {
    // Default parameters based on template complexity
    const baseParams = this.getBaseParametersByComplexity(template.complexity)
    
    // Merge with custom parameters
    const parameters: OptimizationParameters = {
      timeframes: customParameters?.timeframes || baseParams.timeframes,
      numericalParams: customParameters?.numericalParams || baseParams.numericalParams,
      structuralParams: customParameters?.structuralParams || baseParams.structuralParams,
      constraints: customParameters?.constraints || baseParams.constraints
    }

    return parameters
  }

  /**
   * Get base parameters by template complexity
   */
  private getBaseParametersByComplexity(complexity: WorkflowTemplate['complexity']): OptimizationParameters {
    const baseTimeframes = ['1h', '4h', '1d']
    
    switch (complexity) {
      case 'simple':
        return {
          timeframes: ['1h'],
          numericalParams: [
            {
              name: 'rsi_period',
              min: 10,
              max: 30,
              step: 2,
              current: 14,
              type: 'integer'
            },
            {
              name: 'rsi_oversold',
              min: 20,
              max: 40,
              step: 5,
              current: 30,
              type: 'integer'
            },
            {
              name: 'rsi_overbought',
              min: 60,
              max: 80,
              step: 5,
              current: 70,
              type: 'integer'
            }
          ],
          structuralParams: [
            {
              name: 'use_stop_loss',
              value: true,
              type: 'boolean',
              fixed: false
            }
          ],
          constraints: [
            {
              type: 'performance',
              condition: 'sharpe_ratio',
              value: 1.0,
              operator: '>'
            }
          ]
        }

      case 'moderate':
        return {
          timeframes: ['1h', '4h'],
          numericalParams: [
            {
              name: 'rsi_period',
              min: 8,
              max: 35,
              step: 1,
              current: 14,
              type: 'integer'
            },
            {
              name: 'ma_fast',
              min: 5,
              max: 25,
              step: 1,
              current: 12,
              type: 'integer'
            },
            {
              name: 'ma_slow',
              min: 20,
              max: 50,
              step: 2,
              current: 26,
              type: 'integer'
            },
            {
              name: 'stop_loss_pct',
              min: 0.01,
              max: 0.05,
              step: 0.005,
              current: 0.02,
              type: 'float'
            }
          ],
          structuralParams: [
            {
              name: 'ma_type',
              value: 'EMA',
              type: 'indicator',
              fixed: false
            },
            {
              name: 'use_trailing_stop',
              value: false,
              type: 'boolean',
              fixed: false
            }
          ],
          constraints: [
            {
              type: 'performance',
              condition: 'sharpe_ratio',
              value: 1.2,
              operator: '>'
            },
            {
              type: 'risk',
              condition: 'max_drawdown',
              value: 0.15,
              operator: '<'
            }
          ]
        }

      case 'complex':
      case 'advanced':
        return {
          timeframes: baseTimeframes,
          numericalParams: [
            {
              name: 'rsi_period',
              min: 5,
              max: 50,
              step: 1,
              current: 14,
              type: 'integer'
            },
            {
              name: 'bb_period',
              min: 10,
              max: 30,
              step: 1,
              current: 20,
              type: 'integer'
            },
            {
              name: 'bb_std',
              min: 1.5,
              max: 3.0,
              step: 0.1,
              current: 2.0,
              type: 'float'
            },
            {
              name: 'ma_fast',
              min: 3,
              max: 30,
              step: 1,
              current: 12,
              type: 'integer'
            },
            {
              name: 'ma_slow',
              min: 15,
              max: 100,
              step: 2,
              current: 26,
              type: 'integer'
            },
            {
              name: 'stop_loss_pct',
              min: 0.005,
              max: 0.08,
              step: 0.002,
              current: 0.02,
              type: 'float'
            },
            {
              name: 'take_profit_pct',
              min: 0.01,
              max: 0.15,
              step: 0.005,
              current: 0.04,
              type: 'float'
            }
          ],
          structuralParams: [
            {
              name: 'ma_type',
              value: 'EMA',
              type: 'indicator',
              fixed: false
            },
            {
              name: 'signal_confirmation',
              value: 'volume',
              type: 'method',
              fixed: false
            },
            {
              name: 'use_trailing_stop',
              value: true,
              type: 'boolean',
              fixed: false
            },
            {
              name: 'position_sizing',
              value: 'fixed',
              type: 'method',
              fixed: false
            }
          ],
          constraints: [
            {
              type: 'performance',
              condition: 'sharpe_ratio',
              value: 1.5,
              operator: '>'
            },
            {
              type: 'performance',
              condition: 'total_return',
              value: 0.15,
              operator: '>'
            },
            {
              type: 'risk',
              condition: 'max_drawdown',
              value: 0.12,
              operator: '<'
            },
            {
              type: 'risk',
              condition: 'var_95',
              value: 0.03,
              operator: '<'
            },
            {
              type: 'resource',
              condition: 'execution_time',
              value: 3600,
              operator: '<'
            }
          ]
        }

      default:
        return this.getBaseParametersByComplexity('moderate')
    }
  }

  /**
   * Validate workflow configuration
   */
  private validateConfig(config: WorkflowConfig): WorkflowConfig {
    // Validate required fields
    if (!config.labId) {
      throw new Error('Lab ID is required')
    }

    if (!config.persona) {
      throw new Error('Persona is required')
    }

    if (!config.parameters) {
      throw new Error('Optimization parameters are required')
    }

    // Validate template or custom steps
    if (!config.templateId && !config.customSteps) {
      throw new Error('Either templateId or customSteps must be provided')
    }

    if (config.templateId && config.customSteps) {
      throw new Error('Cannot specify both templateId and customSteps')
    }

    // Validate parameters
    this.validateOptimizationParameters(config.parameters)

    // Validate retry policy
    if (config.retryPolicy) {
      this.validateRetryPolicy(config.retryPolicy)
    }

    return config
  }

  /**
   * Validate optimization parameters
   */
  private validateOptimizationParameters(params: OptimizationParameters): void {
    // Validate timeframes
    if (!params.timeframes || params.timeframes.length === 0) {
      throw new Error('At least one timeframe must be specified')
    }

    const validTimeframes = ['1m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '1d', '3d', '1w']
    for (const timeframe of params.timeframes) {
      if (!validTimeframes.includes(timeframe)) {
        throw new Error(`Invalid timeframe: ${timeframe}`)
      }
    }

    // Validate numerical parameters
    for (const param of params.numericalParams) {
      if (param.min >= param.max) {
        throw new Error(`Invalid range for parameter ${param.name}: min must be less than max`)
      }
      
      if (param.current < param.min || param.current > param.max) {
        throw new Error(`Current value for parameter ${param.name} is outside valid range`)
      }
      
      if (param.step <= 0) {
        throw new Error(`Step size for parameter ${param.name} must be positive`)
      }
    }

    // Validate constraints
    for (const constraint of params.constraints) {
      if (!['performance', 'risk', 'resource', 'time'].includes(constraint.type)) {
        throw new Error(`Invalid constraint type: ${constraint.type}`)
      }
      
      if (!['>', '<', '=', '>=', '<='].includes(constraint.operator)) {
        throw new Error(`Invalid constraint operator: ${constraint.operator}`)
      }
    }
  }

  /**
   * Validate retry policy
   */
  private validateRetryPolicy(policy: RetryPolicy): void {
    if (policy.maxRetries < 0) {
      throw new Error('Max retries cannot be negative')
    }

    if (!['linear', 'exponential', 'fixed'].includes(policy.backoffStrategy)) {
      throw new Error(`Invalid backoff strategy: ${policy.backoffStrategy}`)
    }

    if (policy.baseDelay < 0) {
      throw new Error('Base delay cannot be negative')
    }

    if (policy.maxDelay < policy.baseDelay) {
      throw new Error('Max delay cannot be less than base delay')
    }
  }

  /**
   * Get default retry policy
   */
  private getDefaultRetryPolicy(): RetryPolicy {
    return {
      maxRetries: 3,
      backoffStrategy: 'exponential',
      baseDelay: 1000,
      maxDelay: 10000
    }
  }

  /**
   * Create configuration preset
   */
  createPreset(
    name: string,
    description: string,
    baseConfig: WorkflowConfig
  ): ConfigPreset {
    const preset: ConfigPreset = {
      id: this.generatePresetId(),
      name,
      description,
      config: { ...baseConfig },
      createdAt: new Date(),
      updatedAt: new Date()
    }

    return preset
  }

  /**
   * Apply persona-specific adjustments to configuration
   */
  applyPersonaAdjustments(config: WorkflowConfig, persona: Persona): WorkflowConfig {
    const adjustedConfig = { ...config }

    switch (persona.type) {
      case 'conservative':
        // More conservative constraints
        adjustedConfig.parameters.constraints = adjustedConfig.parameters.constraints.map(constraint => {
          if (constraint.type === 'risk' && constraint.condition === 'max_drawdown') {
            return { ...constraint, value: Math.min(constraint.value, 0.08) }
          }
          if (constraint.type === 'performance' && constraint.condition === 'sharpe_ratio') {
            return { ...constraint, value: Math.max(constraint.value, 1.5) }
          }
          return constraint
        })
        
        // Lower timeout for conservative approach
        adjustedConfig.timeout = Math.min(adjustedConfig.timeout || 3600000, 1800000) // Max 30 minutes
        break

      case 'aggressive':
        // More aggressive constraints
        adjustedConfig.parameters.constraints = adjustedConfig.parameters.constraints.map(constraint => {
          if (constraint.type === 'risk' && constraint.condition === 'max_drawdown') {
            return { ...constraint, value: Math.max(constraint.value, 0.20) }
          }
          return constraint
        })
        
        // Higher timeout for aggressive optimization
        adjustedConfig.timeout = Math.max(adjustedConfig.timeout || 3600000, 7200000) // Min 2 hours
        break

      case 'balanced':
        // Keep default values
        break

      case 'custom':
        // Apply custom persona settings
        if (persona.settings) {
          this.applyCustomPersonaSettings(adjustedConfig, persona.settings)
        }
        break
    }

    return adjustedConfig
  }

  /**
   * Apply custom persona settings
   */
  private applyCustomPersonaSettings(config: WorkflowConfig, settings: any): void {
    if (settings.riskTolerance) {
      const riskMultiplier = settings.riskTolerance === 'high' ? 1.5 : 
                           settings.riskTolerance === 'low' ? 0.7 : 1.0

      config.parameters.constraints = config.parameters.constraints.map(constraint => {
        if (constraint.type === 'risk') {
          return { ...constraint, value: constraint.value * riskMultiplier }
        }
        return constraint
      })
    }

    if (settings.optimizationIntensity) {
      const intensityMultiplier = settings.optimizationIntensity === 'high' ? 2.0 :
                                 settings.optimizationIntensity === 'low' ? 0.5 : 1.0

      config.timeout = (config.timeout || 3600000) * intensityMultiplier
    }
  }

  /**
   * Generate configuration summary
   */
  generateConfigSummary(config: WorkflowConfig): ConfigSummary {
    const template = config.templateId ? 
      workflowTemplateManager.getTemplate(config.templateId) : null

    return {
      type: config.templateId ? 'template' : 'custom',
      templateName: template?.then(t => t?.name) || 'Custom Workflow',
      complexity: template?.then(t => t?.complexity) || 'moderate',
      estimatedDuration: template?.then(t => t?.estimatedDuration) || 0,
      stepCount: config.customSteps?.length || 0,
      parameterCount: config.parameters.numericalParams.length + config.parameters.structuralParams.length,
      constraintCount: config.parameters.constraints.length,
      timeframes: config.parameters.timeframes,
      persona: config.persona.type,
      resumable: config.resumable,
      priority: config.priority
    }
  }

  /**
   * Export configuration
   */
  exportConfig(config: WorkflowConfig): string {
    return JSON.stringify(config, null, 2)
  }

  /**
   * Import configuration
   */
  importConfig(configJson: string): WorkflowConfig {
    try {
      const config = JSON.parse(configJson) as WorkflowConfig
      return this.validateConfig(config)
    } catch (error) {
      throw new Error(`Invalid configuration format: ${error}`)
    }
  }

  /**
   * Generate preset ID
   */
  private generatePresetId(): string {
    return `preset_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  }
}

interface ConfigPreset {
  id: string
  name: string
  description: string
  config: WorkflowConfig
  createdAt: Date
  updatedAt: Date
}

interface ConfigSummary {
  type: 'template' | 'custom'
  templateName: string | Promise<string | undefined>
  complexity: WorkflowTemplate['complexity']
  estimatedDuration: number | Promise<number | undefined>
  stepCount: number
  parameterCount: number
  constraintCount: number
  timeframes: string[]
  persona: string
  resumable: boolean
  priority: string
}

// Export singleton instance
export const workflowConfigManager = new WorkflowConfigManager()