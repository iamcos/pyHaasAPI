import type { CommandIntent, CommandEntity } from './commandProcessor'
import type { UIContext } from '@/types'

// Command validation result
export interface ValidationResult {
  isValid: boolean
  errors: ValidationError[]
  warnings: ValidationWarning[]
  suggestions: ValidationSuggestion[]
  confidence: number
}

export interface ValidationError {
  type: 'syntax' | 'context' | 'permission' | 'data' | 'logic'
  message: string
  severity: 'error' | 'warning' | 'info'
  suggestion?: string
}

export interface ValidationWarning {
  type: 'ambiguous' | 'incomplete' | 'risky' | 'deprecated'
  message: string
  suggestion: string
}

export interface ValidationSuggestion {
  type: 'completion' | 'correction' | 'enhancement' | 'alternative'
  message: string
  replacement?: string
  confidence: number
}

// Context-aware command validator
class CommandValidator {
  // Validate command before processing
  async validateCommand(
    command: string,
    intent: CommandIntent,
    entities: CommandEntity[],
    context: UIContext
  ): Promise<ValidationResult> {
    const errors: ValidationError[] = []
    const warnings: ValidationWarning[] = []
    const suggestions: ValidationSuggestion[] = []
    let confidence = 1.0

    // Basic syntax validation
    const syntaxValidation = this.validateSyntax(command)
    errors.push(...syntaxValidation.errors)
    warnings.push(...syntaxValidation.warnings)
    confidence *= syntaxValidation.confidence

    // Context validation
    const contextValidation = this.validateContext(intent, entities, context)
    errors.push(...contextValidation.errors)
    warnings.push(...contextValidation.warnings)
    confidence *= contextValidation.confidence

    // Entity validation
    const entityValidation = this.validateEntities(entities, intent)
    errors.push(...entityValidation.errors)
    warnings.push(...entityValidation.warnings)
    suggestions.push(...entityValidation.suggestions)
    confidence *= entityValidation.confidence

    // Intent-specific validation
    const intentValidation = await this.validateIntent(intent, entities, context)
    errors.push(...intentValidation.errors)
    warnings.push(...intentValidation.warnings)
    suggestions.push(...intentValidation.suggestions)
    confidence *= intentValidation.confidence

    // Risk validation for trading commands
    const riskValidation = this.validateRisk(intent, entities, context)
    warnings.push(...riskValidation.warnings)
    suggestions.push(...riskValidation.suggestions)

    return {
      isValid: errors.filter(e => e.severity === 'error').length === 0,
      errors,
      warnings,
      suggestions,
      confidence: Math.max(confidence, 0.1)
    }
  }

  // Validate command syntax
  private validateSyntax(command: string): {
    errors: ValidationError[]
    warnings: ValidationWarning[]
    confidence: number
  } {
    const errors: ValidationError[] = []
    const warnings: ValidationWarning[] = []
    let confidence = 1.0

    // Check for empty command
    if (!command.trim()) {
      errors.push({
        type: 'syntax',
        message: 'Command cannot be empty',
        severity: 'error',
        suggestion: 'Please enter a command'
      })
      confidence = 0.0
    }

    // Check for very short commands
    if (command.trim().length < 3) {
      warnings.push({
        type: 'incomplete',
        message: 'Command seems too short',
        suggestion: 'Try providing more details about what you want to do'
      })
      confidence *= 0.7
    }

    // Check for very long commands
    if (command.length > 500) {
      warnings.push({
        type: 'incomplete',
        message: 'Command is very long',
        suggestion: 'Consider breaking this into multiple commands'
      })
      confidence *= 0.8
    }

    // Check for special characters that might cause issues
    const problematicChars = /[<>{}[\]\\]/g
    if (problematicChars.test(command)) {
      warnings.push({
        type: 'ambiguous',
        message: 'Command contains special characters that might cause issues',
        suggestion: 'Consider using simpler language'
      })
      confidence *= 0.9
    }

    return { errors, warnings, confidence }
  }

  // Validate command context
  private validateContext(
    intent: CommandIntent,
    entities: CommandEntity[],
    context: UIContext
  ): {
    errors: ValidationError[]
    warnings: ValidationWarning[]
    confidence: number
  } {
    const errors: ValidationError[] = []
    const warnings: ValidationWarning[] = []
    let confidence = 1.0

    // Check if command is appropriate for current view
    const viewCommandCompatibility = this.checkViewCompatibility(intent.type, context.currentView)
    if (!viewCommandCompatibility.compatible) {
      warnings.push({
        type: 'ambiguous',
        message: `${intent.type} commands work better in ${viewCommandCompatibility.suggestedView} view`,
        suggestion: `Consider switching to ${viewCommandCompatibility.suggestedView} first`
      })
      confidence *= 0.8
    }

    // Check if required context is available
    if (intent.type === 'analysis' && context.selectedAssets.length === 0) {
      const hasSymbolEntities = entities.some(e => e.type === 'symbol')
      if (!hasSymbolEntities) {
        warnings.push({
          type: 'incomplete',
          message: 'No assets selected for analysis',
          suggestion: 'Select assets first or specify symbols in your command'
        })
        confidence *= 0.7
      }
    }

    // Check persona compatibility
    if (intent.type === 'risk' && context.persona.type === 'aggressive') {
      warnings.push({
        type: 'risky',
        message: 'Risk analysis with aggressive persona may show higher risk tolerance',
        suggestion: 'Consider your actual risk tolerance when reviewing results'
      })
    }

    return { errors, warnings, confidence }
  }

  // Validate extracted entities
  private validateEntities(
    entities: CommandEntity[],
    intent: CommandIntent
  ): {
    errors: ValidationError[]
    warnings: ValidationWarning[]
    suggestions: ValidationSuggestion[]
    confidence: number
  } {
    const errors: ValidationError[] = []
    const warnings: ValidationWarning[] = []
    const suggestions: ValidationSuggestion[] = []
    let confidence = 1.0

    // Validate symbols
    const symbols = entities.filter(e => e.type === 'symbol')
    for (const symbol of symbols) {
      const symbolValidation = this.validateSymbol(symbol.value)
      if (!symbolValidation.isValid) {
        warnings.push({
          type: 'ambiguous',
          message: `"${symbol.value}" might not be a valid trading symbol`,
          suggestion: symbolValidation.suggestion || 'Please verify the symbol'
        })
        confidence *= 0.8
      }
    }

    // Validate timeframes
    const timeframes = entities.filter(e => e.type === 'timeframe')
    for (const timeframe of timeframes) {
      const timeframeValidation = this.validateTimeframe(timeframe.value)
      if (!timeframeValidation.isValid) {
        warnings.push({
          type: 'ambiguous',
          message: `"${timeframe.value}" might not be a valid timeframe`,
          suggestion: timeframeValidation.suggestion || 'Use formats like 1h, 4h, 1d'
        })
        confidence *= 0.8
      }
    }

    // Check for missing required entities
    const requiredEntities = this.getRequiredEntities(intent.type)
    for (const required of requiredEntities) {
      const hasRequired = entities.some(e => e.type === required.type)
      if (!hasRequired && required.required) {
        suggestions.push({
          type: 'completion',
          message: `Consider specifying ${required.description}`,
          confidence: 0.8
        })
      }
    }

    // Check for conflicting entities
    const conflicts = this.checkEntityConflicts(entities)
    for (const conflict of conflicts) {
      warnings.push({
        type: 'ambiguous',
        message: conflict.message,
        suggestion: conflict.suggestion
      })
      confidence *= 0.7
    }

    return { errors, warnings, suggestions, confidence }
  }

  // Validate specific intent types
  private async validateIntent(
    intent: CommandIntent,
    entities: CommandEntity[],
    context: UIContext
  ): Promise<{
    errors: ValidationError[]
    warnings: ValidationWarning[]
    suggestions: ValidationSuggestion[]
    confidence: number
  }> {
    const errors: ValidationError[] = []
    const warnings: ValidationWarning[] = []
    const suggestions: ValidationSuggestion[] = []
    let confidence = 1.0

    switch (intent.type) {
      case 'strategy':
        const strategyValidation = this.validateStrategyIntent(entities, context)
        errors.push(...strategyValidation.errors)
        warnings.push(...strategyValidation.warnings)
        suggestions.push(...strategyValidation.suggestions)
        confidence *= strategyValidation.confidence
        break

      case 'workflow':
        const workflowValidation = this.validateWorkflowIntent(entities, context)
        errors.push(...workflowValidation.errors)
        warnings.push(...workflowValidation.warnings)
        suggestions.push(...workflowValidation.suggestions)
        confidence *= workflowValidation.confidence
        break

      case 'bot_management':
        const botValidation = this.validateBotManagementIntent(entities, context)
        errors.push(...botValidation.errors)
        warnings.push(...botValidation.warnings)
        suggestions.push(...botValidation.suggestions)
        confidence *= botValidation.confidence
        break

      case 'risk':
        const riskValidation = this.validateRiskIntent(entities, context)
        warnings.push(...riskValidation.warnings)
        suggestions.push(...riskValidation.suggestions)
        confidence *= riskValidation.confidence
        break
    }

    return { errors, warnings, suggestions, confidence }
  }

  // Validate risk implications of commands
  private validateRisk(
    intent: CommandIntent,
    entities: CommandEntity[],
    context: UIContext
  ): {
    warnings: ValidationWarning[]
    suggestions: ValidationSuggestion[]
  } {
    const warnings: ValidationWarning[] = []
    const suggestions: ValidationSuggestion[] = []

    // High-risk command types
    const highRiskIntents = ['bot_management', 'workflow']
    if (highRiskIntents.includes(intent.type)) {
      warnings.push({
        type: 'risky',
        message: 'This command may affect live trading',
        suggestion: 'Ensure you understand the implications before proceeding'
      })
    }

    // Check for aggressive persona with risky commands
    if (context.persona.type === 'aggressive' && intent.type === 'strategy') {
      suggestions.push({
        type: 'enhancement',
        message: 'Consider adding risk management parameters',
        confidence: 0.8
      })
    }

    // Check for conservative persona with aggressive commands
    if (context.persona.type === 'conservative' && intent.type === 'workflow') {
      suggestions.push({
        type: 'alternative',
        message: 'Consider starting with backtesting before live optimization',
        confidence: 0.9
      })
    }

    return { warnings, suggestions }
  }

  // Check view compatibility
  private checkViewCompatibility(intentType: string, currentView: string): {
    compatible: boolean
    suggestedView: string
  } {
    const viewMapping: Record<string, string> = {
      'strategy': 'strategy-studio',
      'analysis': 'analytics',
      'risk': 'risk-management',
      'bot_management': 'bot-management',
      'market_data': 'market-intelligence',
      'workflow': 'dashboard'
    }

    const suggestedView = viewMapping[intentType] || 'dashboard'
    const compatible = currentView === suggestedView || currentView === 'dashboard'

    return { compatible, suggestedView }
  }

  // Validate trading symbols
  private validateSymbol(symbol: string): { isValid: boolean; suggestion?: string } {
    // Basic symbol format validation
    const symbolPattern = /^[A-Z]{2,5}(\/[A-Z]{2,5})?$/
    
    if (!symbolPattern.test(symbol)) {
      return {
        isValid: false,
        suggestion: 'Use format like BTC, ETH, or BTC/USD'
      }
    }

    // Check for common symbol formats
    const commonSymbols = ['BTC', 'ETH', 'ADA', 'DOT', 'LINK', 'UNI', 'AAVE']
    const commonPairs = ['BTC/USD', 'ETH/USD', 'BTC/USDT', 'ETH/USDT']
    
    if (commonSymbols.includes(symbol) || commonPairs.includes(symbol)) {
      return { isValid: true }
    }

    // If not in common list, still consider valid but with lower confidence
    return { isValid: true }
  }

  // Validate timeframes
  private validateTimeframe(timeframe: string): { isValid: boolean; suggestion?: string } {
    const validTimeframes = [
      '1m', '5m', '15m', '30m',
      '1h', '2h', '4h', '6h', '8h', '12h',
      '1d', '3d', '1w', '1M'
    ]

    const normalizedTimeframe = timeframe.toLowerCase()
    
    if (validTimeframes.includes(normalizedTimeframe)) {
      return { isValid: true }
    }

    // Check for alternative formats
    if (/^\d+[mhd]$/.test(normalizedTimeframe)) {
      return { isValid: true }
    }

    return {
      isValid: false,
      suggestion: 'Use formats like 1m, 1h, 1d, or 1w'
    }
  }

  // Get required entities for intent types
  private getRequiredEntities(intentType: string): Array<{
    type: string
    required: boolean
    description: string
  }> {
    const requirements: Record<string, Array<{ type: string; required: boolean; description: string }>> = {
      'strategy': [
        { type: 'symbol', required: false, description: 'trading symbols (e.g., BTC, ETH)' },
        { type: 'timeframe', required: false, description: 'timeframe (e.g., 1h, 1d)' }
      ],
      'analysis': [
        { type: 'symbol', required: false, description: 'symbols to analyze' },
        { type: 'timeframe', required: false, description: 'analysis timeframe' }
      ],
      'market_data': [
        { type: 'symbol', required: true, description: 'market symbols' }
      ],
      'bot_management': [
        { type: 'bot_id', required: false, description: 'specific bot ID' }
      ]
    }

    return requirements[intentType] || []
  }

  // Check for conflicting entities
  private checkEntityConflicts(entities: CommandEntity[]): Array<{
    message: string
    suggestion: string
  }> {
    const conflicts: Array<{ message: string; suggestion: string }> = []

    // Check for multiple conflicting timeframes
    const timeframes = entities.filter(e => e.type === 'timeframe')
    if (timeframes.length > 1) {
      conflicts.push({
        message: 'Multiple timeframes specified',
        suggestion: 'Please specify only one timeframe'
      })
    }

    // Check for too many symbols (might be overwhelming)
    const symbols = entities.filter(e => e.type === 'symbol')
    if (symbols.length > 5) {
      conflicts.push({
        message: 'Many symbols specified',
        suggestion: 'Consider analyzing fewer symbols for better focus'
      })
    }

    return conflicts
  }

  // Validate strategy-specific requirements
  private validateStrategyIntent(
    entities: CommandEntity[],
    context: UIContext
  ): {
    errors: ValidationError[]
    warnings: ValidationWarning[]
    suggestions: ValidationSuggestion[]
    confidence: number
  } {
    const errors: ValidationError[] = []
    const warnings: ValidationWarning[] = []
    const suggestions: ValidationSuggestion[] = []
    let confidence = 1.0

    // Check if strategy description is meaningful
    const strategyNames = entities.filter(e => e.type === 'strategy_name')
    if (strategyNames.length === 0) {
      suggestions.push({
        type: 'completion',
        message: 'Consider specifying the type of strategy (e.g., RSI, MACD, momentum)',
        confidence: 0.7
      })
    }

    // Suggest risk management for aggressive personas
    if (context.persona.type === 'aggressive') {
      suggestions.push({
        type: 'enhancement',
        message: 'Consider adding stop-loss and take-profit parameters',
        confidence: 0.8
      })
    }

    return { errors, warnings, suggestions, confidence }
  }

  // Validate workflow-specific requirements
  private validateWorkflowIntent(
    entities: CommandEntity[],
    context: UIContext
  ): {
    errors: ValidationError[]
    warnings: ValidationWarning[]
    suggestions: ValidationSuggestion[]
    confidence: number
  } {
    const errors: ValidationError[] = []
    const warnings: ValidationWarning[] = []
    const suggestions: ValidationSuggestion[] = []
    let confidence = 1.0

    // Check if user has active strategies to optimize
    if (context.activeStrategies.length === 0) {
      warnings.push({
        type: 'incomplete',
        message: 'No active strategies found',
        suggestion: 'Create a strategy first before running optimization workflows'
      })
      confidence *= 0.6
    }

    // Warn about resource-intensive operations
    warnings.push({
      type: 'risky',
      message: 'Optimization workflows can be resource-intensive',
      suggestion: 'Ensure your system has sufficient resources'
    })

    return { errors, warnings, suggestions, confidence }
  }

  // Validate bot management requirements
  private validateBotManagementIntent(
    entities: CommandEntity[],
    context: UIContext
  ): {
    errors: ValidationError[]
    warnings: ValidationWarning[]
    suggestions: ValidationSuggestion[]
    confidence: number
  } {
    const errors: ValidationError[] = []
    const warnings: ValidationWarning[] = []
    const suggestions: ValidationSuggestion[] = []
    let confidence = 1.0

    // Warn about live trading implications
    warnings.push({
      type: 'risky',
      message: 'Bot management commands affect live trading',
      suggestion: 'Ensure you understand the implications before proceeding'
    })

    // Check for conservative persona with bot commands
    if (context.persona.type === 'conservative') {
      suggestions.push({
        type: 'alternative',
        message: 'Consider reviewing bot settings before activation',
        confidence: 0.8
      })
    }

    return { errors, warnings, suggestions, confidence }
  }

  // Validate risk analysis requirements
  private validateRiskIntent(
    entities: CommandEntity[],
    context: UIContext
  ): {
    warnings: ValidationWarning[]
    suggestions: ValidationSuggestion[]
    confidence: number
  } {
    const warnings: ValidationWarning[] = []
    const suggestions: ValidationSuggestion[] = []
    let confidence = 1.0

    // Suggest comprehensive risk analysis
    suggestions.push({
      type: 'enhancement',
      message: 'Consider analyzing both portfolio and individual position risks',
      confidence: 0.7
    })

    // Suggest regular risk monitoring
    suggestions.push({
      type: 'enhancement',
      message: 'Set up automated risk alerts for continuous monitoring',
      confidence: 0.8
    })

    return { warnings, suggestions, confidence }
  }
}

// Export singleton instance
export const commandValidator = new CommandValidator()