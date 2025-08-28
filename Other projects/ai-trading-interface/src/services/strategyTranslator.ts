import { 
  ExternalStrategy, 
  TranslationResult, 
  StrategyTranslationConfig, 
  TranslationStep,
  TranslationWarning,
  TranslationError,
  OptimizationSuggestion,
  HaasScriptParameter
} from '../types/translation';
import { PineScriptParser } from './parsers/pineScriptParser';
import { aiService } from './aiService';

export class StrategyTranslator {
  private pineScriptParser = new PineScriptParser();
  private chainOfThought: TranslationStep[] = [];

  async translateStrategy(
    sourceCode: string, 
    sourceFormat: ExternalStrategy['sourceFormat'],
    config: StrategyTranslationConfig,
    name?: string
  ): Promise<TranslationResult> {
    this.chainOfThought = [];
    
    try {
      // Step 1: Parse the external strategy
      const externalStrategy = await this.parseExternalStrategy(sourceCode, sourceFormat, name);
      
      // Step 2: Analyze the strategy structure
      const analysis = await this.analyzeStrategy(externalStrategy);
      
      // Step 3: Map to HaasScript concepts
      const mapping = await this.mapToHaasScript(externalStrategy, analysis);
      
      // Step 4: Generate HaasScript code
      const generation = await this.generateHaasScript(mapping, config);
      
      // Step 5: Optimize the generated code
      const optimization = await this.optimizeCode(generation, config);
      
      // Step 6: Validate the result
      const validation = await this.validateTranslation(optimization);
      
      return {
        success: validation.errors.length === 0,
        haasScriptCode: optimization.code,
        translatedParameters: optimization.parameters,
        warnings: validation.warnings,
        errors: validation.errors,
        confidence: this.calculateConfidence(),
        optimizationSuggestions: optimization.suggestions,
        chainOfThought: this.chainOfThought
      };
      
    } catch (error) {
      return {
        success: false,
        haasScriptCode: '',
        translatedParameters: [],
        warnings: [],
        errors: [{
          message: `Translation failed: ${error instanceof Error ? error.message : 'Unknown error'}`,
          category: 'syntax_error',
          originalCode: sourceCode,
          possibleSolutions: ['Check source code syntax', 'Try a different translation approach']
        }],
        confidence: 0,
        optimizationSuggestions: [],
        chainOfThought: this.chainOfThought
      };
    }
  }

  private async parseExternalStrategy(
    sourceCode: string, 
    sourceFormat: ExternalStrategy['sourceFormat'],
    name?: string
  ): Promise<ExternalStrategy> {
    this.addChainOfThoughtStep('parsing', 'Parsing external strategy', sourceCode, '', 
      'Identifying strategy structure, parameters, and indicators');

    let strategy: ExternalStrategy;
    
    switch (sourceFormat) {
      case 'pine_script':
        strategy = this.pineScriptParser.parseStrategy(sourceCode, name);
        break;
      case 'tradingview':
        strategy = this.pineScriptParser.parseStrategy(sourceCode, name);
        break;
      default:
        throw new Error(`Unsupported source format: ${sourceFormat}`);
    }

    this.addChainOfThoughtStep('parsing', 'Strategy parsed successfully', '', 
      JSON.stringify(strategy.metadata, null, 2),
      `Extracted ${strategy.metadata.parameters?.length || 0} parameters and ${strategy.metadata.indicators?.length || 0} indicators`);

    return strategy;
  }

  private async analyzeStrategy(strategy: ExternalStrategy): Promise<any> {
    this.addChainOfThoughtStep('analysis', 'Analyzing strategy logic', '', '',
      'Identifying trading logic patterns, entry/exit conditions, and risk management');

    const analysis = {
      complexity: this.calculateComplexity(strategy.sourceCode),
      tradingLogic: this.extractTradingLogic(strategy.sourceCode),
      indicators: strategy.metadata.indicators || [],
      parameters: strategy.metadata.parameters || [],
      riskManagement: this.identifyRiskManagement(strategy.sourceCode),
      timeframe: strategy.metadata.timeframe || 'unknown'
    };

    this.addChainOfThoughtStep('analysis', 'Strategy analysis complete', '', 
      JSON.stringify(analysis, null, 2),
      `Complexity: ${analysis.complexity}, Trading signals: ${analysis.tradingLogic.length}`);

    return analysis;
  }

  private async mapToHaasScript(strategy: ExternalStrategy, analysis: any): Promise<any> {
    this.addChainOfThoughtStep('mapping', 'Mapping to HaasScript concepts', '', '',
      'Converting external indicators and functions to HaasScript equivalents');

    const mapping = {
      indicators: this.mapIndicators(analysis.indicators),
      parameters: this.mapParameters(strategy.metadata.parameters || []),
      tradingLogic: this.mapTradingLogic(analysis.tradingLogic),
      functions: this.mapFunctions(strategy.sourceCode)
    };

    this.addChainOfThoughtStep('mapping', 'Mapping complete', '', 
      JSON.stringify(mapping, null, 2),
      'Successfully mapped external concepts to HaasScript equivalents');

    return mapping;
  }

  private async generateHaasScript(mapping: any, config: StrategyTranslationConfig): Promise<any> {
    this.addChainOfThoughtStep('generation', 'Generating HaasScript code', '', '',
      'Creating HaasScript code from mapped concepts');

    let code = '// Translated Strategy\n';
    code += '// Generated by AI-Powered Trading Interface\n\n';

    // Add parameters
    if (mapping.parameters.length > 0) {
      code += '// Parameters\n';
      mapping.parameters.forEach((param: any) => {
        code += `var ${param.name} = ${param.defaultValue}\n`;
      });
      code += '\n';
    }

    // Add indicators
    if (mapping.indicators.length > 0) {
      code += '// Indicators\n';
      mapping.indicators.forEach((indicator: any) => {
        code += `${indicator.code}\n`;
      });
      code += '\n';
    }

    // Add trading logic
    if (mapping.tradingLogic.length > 0) {
      code += '// Trading Logic\n';
      mapping.tradingLogic.forEach((logic: any) => {
        code += `${logic.code}\n`;
      });
    }

    // Use AI assistance if enabled
    if (config.aiAssistance) {
      code = await this.enhanceWithAI(code, mapping);
    }

    const result = {
      code,
      parameters: mapping.parameters,
      suggestions: [] as OptimizationSuggestion[]
    };

    this.addChainOfThoughtStep('generation', 'HaasScript code generated', '', code,
      `Generated ${code.split('\n').length} lines of HaasScript code`);

    return result;
  }

  private async optimizeCode(generation: any, config: StrategyTranslationConfig): Promise<any> {
    this.addChainOfThoughtStep('optimization', 'Optimizing generated code', generation.code, '',
      'Applying performance and readability optimizations');

    let optimizedCode = generation.code;
    const suggestions: OptimizationSuggestion[] = [];

    // Apply optimizations based on config
    if (config.targetOptimizations.includes('performance')) {
      const perfOptimization = this.applyPerformanceOptimizations(optimizedCode);
      optimizedCode = perfOptimization.code;
      suggestions.push(...perfOptimization.suggestions);
    }

    if (config.targetOptimizations.includes('readability')) {
      const readabilityOptimization = this.applyReadabilityOptimizations(optimizedCode);
      optimizedCode = readabilityOptimization.code;
      suggestions.push(...readabilityOptimization.suggestions);
    }

    if (config.targetOptimizations.includes('haas_best_practices')) {
      const bestPracticesOptimization = this.applyHaasBestPractices(optimizedCode);
      optimizedCode = bestPracticesOptimization.code;
      suggestions.push(...bestPracticesOptimization.suggestions);
    }

    this.addChainOfThoughtStep('optimization', 'Code optimization complete', generation.code, optimizedCode,
      `Applied ${suggestions.length} optimizations`);

    return {
      code: optimizedCode,
      parameters: generation.parameters,
      suggestions
    };
  }

  private async validateTranslation(optimization: any): Promise<{ warnings: TranslationWarning[], errors: TranslationError[] }> {
    this.addChainOfThoughtStep('validation', 'Validating translated code', optimization.code, '',
      'Checking for syntax errors and logical issues');

    const warnings: TranslationWarning[] = [];
    const errors: TranslationError[] = [];

    // Basic syntax validation
    const syntaxIssues = this.validateSyntax(optimization.code);
    errors.push(...syntaxIssues);

    // Logic validation
    const logicIssues = this.validateLogic(optimization.code);
    warnings.push(...logicIssues);

    this.addChainOfThoughtStep('validation', 'Validation complete', '', '',
      `Found ${errors.length} errors and ${warnings.length} warnings`);

    return { warnings, errors };
  }

  private calculateComplexity(code: string): number {
    const lines = code.split('\n').filter(line => line.trim() && !line.trim().startsWith('//'));
    const conditions = (code.match(/if\s*\(/g) || []).length;
    const loops = (code.match(/for\s*\(/g) || []).length;
    const functions = (code.match(/\w+\s*\(/g) || []).length;
    
    return lines.length + conditions * 2 + loops * 3 + functions * 0.5;
  }

  private extractTradingLogic(code: string): any[] {
    const logic: any[] = [];
    const lines = code.split('\n');
    
    lines.forEach((line, index) => {
      const trimmed = line.trim();
      
      // Look for strategy.entry, strategy.exit, etc.
      if (trimmed.includes('strategy.entry') || trimmed.includes('strategy.exit') ||
          trimmed.includes('strategy.close') || trimmed.includes('buy') || trimmed.includes('sell')) {
        logic.push({
          type: 'trade_action',
          line: index + 1,
          code: trimmed,
          action: this.identifyTradeAction(trimmed)
        });
      }
      
      // Look for conditions
      if (trimmed.includes('if ') || trimmed.includes('when ')) {
        logic.push({
          type: 'condition',
          line: index + 1,
          code: trimmed,
          condition: this.extractCondition(trimmed)
        });
      }
    });
    
    return logic;
  }

  private identifyRiskManagement(code: string): any {
    const riskFeatures = {
      stopLoss: code.includes('stop_loss') || code.includes('sl'),
      takeProfit: code.includes('take_profit') || code.includes('tp'),
      positionSizing: code.includes('qty') || code.includes('size'),
      maxDrawdown: code.includes('max_drawdown'),
      riskPerTrade: code.includes('risk')
    };
    
    return riskFeatures;
  }

  private mapIndicators(indicators: string[]): any[] {
    const indicatorMap: Record<string, string> = {
      'SMA': 'SMA(Close, period)',
      'EMA': 'EMA(Close, period)',
      'RSI': 'RSI(Close, period)',
      'MACD': 'MACD(Close, fast, slow, signal)',
      'BB': 'BB(Close, period, deviation)',
      'STOCH': 'Stoch(High, Low, Close, period)',
      'ATR': 'ATR(High, Low, Close, period)',
      'ADX': 'ADX(High, Low, Close, period)'
    };

    return indicators.map(indicator => ({
      original: indicator,
      haasScript: indicatorMap[indicator] || `// TODO: Map ${indicator}`,
      code: `var ${indicator.toLowerCase()} = ${indicatorMap[indicator] || `UnknownIndicator(${indicator})`}`
    }));
  }

  private mapParameters(parameters: any[]): HaasScriptParameter[] {
    return parameters.map(param => ({
      id: `param_${param.name}`,
      name: param.name,
      type: this.mapParameterType(param.dataType),
      value: param.value,
      defaultValue: param.defaultValue,
      min: param.min,
      max: param.max,
      step: param.step,
      options: param.options,
      description: param.description || `Parameter: ${param.name}`,
      category: 'Strategy'
    }));
  }

  private mapParameterType(dataType: string): 'number' | 'string' | 'boolean' | 'select' {
    switch (dataType) {
      case 'int':
      case 'float':
        return 'number';
      case 'bool':
        return 'boolean';
      case 'string':
        return 'string';
      default:
        return 'string';
    }
  }

  private mapTradingLogic(logic: any[]): any[] {
    return logic.map(item => {
      switch (item.type) {
        case 'trade_action':
          return {
            type: 'trade_action',
            code: this.mapTradeAction(item.action, item.code)
          };
        case 'condition':
          return {
            type: 'condition',
            code: this.mapCondition(item.condition, item.code)
          };
        default:
          return {
            type: 'unknown',
            code: `// TODO: Map ${item.code}`
          };
      }
    });
  }

  private mapFunctions(code: string): any[] {
    // Extract and map custom functions
    const functions: any[] = [];
    const functionMatches = code.match(/(\w+)\s*\([^)]*\)\s*=>/g);
    
    if (functionMatches) {
      functionMatches.forEach(match => {
        functions.push({
          original: match,
          haasScript: `// TODO: Convert function ${match}`
        });
      });
    }
    
    return functions;
  }

  private identifyTradeAction(code: string): string {
    if (code.includes('strategy.entry') || code.includes('buy')) return 'buy';
    if (code.includes('strategy.exit') || code.includes('sell')) return 'sell';
    if (code.includes('strategy.close')) return 'close';
    return 'unknown';
  }

  private extractCondition(code: string): string {
    // Extract the condition part from if statements
    const match = code.match(/if\s+(.+?)(?:\s+then|\s*$)/);
    return match ? match[1] : code;
  }

  private mapTradeAction(action: string, originalCode: string): string {
    switch (action) {
      case 'buy':
        return 'Buy(100, "Translated Buy Signal")';
      case 'sell':
        return 'Sell(100, "Translated Sell Signal")';
      case 'close':
        return 'ClosePosition("Translated Close Signal")';
      default:
        return `// TODO: Map trade action: ${originalCode}`;
    }
  }

  private mapCondition(condition: string, originalCode: string): string {
    // Basic condition mapping
    let mappedCondition = condition
      .replace(/\band\b/g, 'and')
      .replace(/\bor\b/g, 'or')
      .replace(/\bnot\b/g, 'not')
      .replace(/==/g, '=')
      .replace(/!=/g, '<>');
    
    return `if ${mappedCondition}\n    // TODO: Add action\nendif`;
  }

  private async enhanceWithAI(code: string, mapping: any): Promise<string> {
    try {
      const prompt = `
        Enhance this HaasScript code translation:
        
        ${code}
        
        Original mapping context:
        ${JSON.stringify(mapping, null, 2)}
        
        Please improve the code by:
        1. Adding proper error handling
        2. Optimizing indicator calculations
        3. Adding meaningful comments
        4. Ensuring HaasScript best practices
        
        Return only the improved HaasScript code.
      `;
      
      const response = await aiService.processQuery(prompt, 'strategy_translation');
      return response.content || code;
    } catch (error) {
      console.warn('AI enhancement failed, using original code:', error);
      return code;
    }
  }

  private applyPerformanceOptimizations(code: string): { code: string, suggestions: OptimizationSuggestion[] } {
    const suggestions: OptimizationSuggestion[] = [];
    let optimizedCode = code;

    // Example optimization: Cache indicator calculations
    if (code.includes('RSI(Close,')) {
      suggestions.push({
        type: 'performance',
        title: 'Cache RSI Calculation',
        description: 'Store RSI result in a variable to avoid recalculation',
        originalCode: 'RSI(Close, 14)',
        optimizedCode: 'var rsi14 = RSI(Close, 14)',
        impact: 'medium',
        effort: 'easy'
      });
    }

    return { code: optimizedCode, suggestions };
  }

  private applyReadabilityOptimizations(code: string): { code: string, suggestions: OptimizationSuggestion[] } {
    const suggestions: OptimizationSuggestion[] = [];
    let optimizedCode = code;

    // Add proper indentation and spacing
    const lines = optimizedCode.split('\n');
    const formattedLines = lines.map(line => {
      if (line.trim().startsWith('if ') || line.trim().startsWith('while ')) {
        return line;
      }
      if (line.trim().startsWith('endif') || line.trim().startsWith('endwhile')) {
        return line;
      }
      if (line.includes('Buy(') || line.includes('Sell(')) {
        return '    ' + line.trim();
      }
      return line;
    });

    optimizedCode = formattedLines.join('\n');

    return { code: optimizedCode, suggestions };
  }

  private applyHaasBestPractices(code: string): { code: string, suggestions: OptimizationSuggestion[] } {
    const suggestions: OptimizationSuggestion[] = [];
    let optimizedCode = code;

    // Add HaasScript-specific best practices
    if (!code.includes('// Risk Management')) {
      suggestions.push({
        type: 'best_practice',
        title: 'Add Risk Management',
        description: 'Include stop loss and take profit mechanisms',
        originalCode: 'Buy(100, "Signal")',
        optimizedCode: 'Buy(100, "Signal")\nSetStopLoss(0.95)\nSetTakeProfit(1.05)',
        impact: 'high',
        effort: 'moderate'
      });
    }

    return { code: optimizedCode, suggestions };
  }

  private validateSyntax(code: string): TranslationError[] {
    const errors: TranslationError[] = [];
    const lines = code.split('\n');

    lines.forEach((line, index) => {
      const trimmed = line.trim();
      
      // Check for unmatched parentheses
      const openParens = (line.match(/\(/g) || []).length;
      const closeParens = (line.match(/\)/g) || []).length;
      
      if (openParens !== closeParens) {
        errors.push({
          line: index + 1,
          message: 'Unmatched parentheses',
          category: 'syntax_error',
          originalCode: line,
          possibleSolutions: ['Check parentheses balance', 'Verify function call syntax']
        });
      }
    });

    return errors;
  }

  private validateLogic(code: string): TranslationWarning[] {
    const warnings: TranslationWarning[] = [];
    
    // Check for potential logic issues
    if (code.includes('TODO')) {
      warnings.push({
        message: 'Code contains TODO items that need manual review',
        severity: 'high',
        category: 'logic'
      });
    }

    return warnings;
  }

  private calculateConfidence(): number {
    const totalSteps = this.chainOfThought.length;
    if (totalSteps === 0) return 0;
    
    const avgConfidence = this.chainOfThought.reduce((sum, step) => sum + step.confidence, 0) / totalSteps;
    return Math.round(avgConfidence * 100) / 100;
  }

  private addChainOfThoughtStep(
    phase: TranslationStep['phase'],
    description: string,
    input: string,
    output: string,
    reasoning: string,
    confidence: number = 0.8
  ): void {
    this.chainOfThought.push({
      step: this.chainOfThought.length + 1,
      phase,
      description,
      input,
      output,
      reasoning,
      confidence,
      timestamp: new Date()
    });
  }
}

export const strategyTranslator = new StrategyTranslator();