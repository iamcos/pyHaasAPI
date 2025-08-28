import { ValidationError as HaasScriptValidationError, StrategyValidationResult } from '../types/strategy';

export class HaasScriptValidator {
  private keywords = [
    'if', 'else', 'elseif', 'endif', 'while', 'endwhile', 'for', 'endfor',
    'function', 'endfunction', 'return', 'break', 'continue', 'true', 'false',
    'and', 'or', 'not', 'null', 'undefined', 'var', 'const', 'let'
  ];

  private builtinFunctions = [
    'Open', 'High', 'Low', 'Close', 'Volume', 'Timestamp',
    'RSI', 'MACD', 'EMA', 'SMA', 'BB', 'Stoch', 'ADX', 'ATR', 'CCI',
    'Williams', 'MFI', 'OBV', 'VWAP', 'Pivot', 'Fibonacci',
    'Abs', 'Max', 'Min', 'Round', 'Floor', 'Ceil', 'Sqrt', 'Pow',
    'Sin', 'Cos', 'Tan', 'Log', 'Exp', 'Random',
    'Length', 'Sum', 'Average', 'Highest', 'Lowest', 'CrossOver', 'CrossUnder',
    'Buy', 'Sell', 'ClosePosition', 'GetPosition', 'GetBalance', 'GetPrice',
    'SetStopLoss', 'SetTakeProfit', 'GetOrderStatus', 'CancelOrder',
    'Print', 'Alert', 'GetTime', 'FormatNumber', 'ToString', 'ToNumber'
  ];

  validateScript(code: string): StrategyValidationResult {
    const errors: HaasScriptValidationError[] = [];
    const warnings: HaasScriptValidationError[] = [];
    const suggestions: string[] = [];

    const lines = code.split('\n');
    let complexity = 0;
    let estimatedExecutionTime = 0;
    let memoryUsage = 0;

    // Track control structures for proper nesting
    const controlStack: Array<{ type: string; line: number }> = [];
    const declaredVariables = new Set<string>();
    const usedVariables = new Set<string>();

    lines.forEach((line, lineIndex) => {
      const trimmedLine = line.trim();
      const lineNumber = lineIndex + 1;

      // Skip empty lines and comments
      if (!trimmedLine || trimmedLine.startsWith('//') || trimmedLine.startsWith('/*')) {
        return;
      }

      // Check for syntax errors
      this.checkSyntaxErrors(trimmedLine, lineNumber, errors);

      // Check control structure nesting
      this.checkControlStructures(trimmedLine, lineNumber, controlStack, errors);

      // Check variable usage
      this.checkVariableUsage(trimmedLine, lineNumber, declaredVariables, usedVariables, errors, warnings);

      // Check function calls
      this.checkFunctionCalls(trimmedLine, lineNumber, warnings, suggestions);

      // Calculate complexity metrics
      complexity += this.calculateLineComplexity(trimmedLine);
      estimatedExecutionTime += this.estimateLineExecutionTime(trimmedLine);
      memoryUsage += this.estimateLineMemoryUsage(trimmedLine);
    });

    // Check for unclosed control structures
    if (controlStack.length > 0) {
      controlStack.forEach(item => {
        errors.push({
          line: item.line,
          column: 1,
          message: `Unclosed ${item.type} statement`,
          severity: 'error',
          code: 'UNCLOSED_CONTROL'
        });
      });
    }

    // Check for unused variables
    declaredVariables.forEach(variable => {
      if (!usedVariables.has(variable)) {
        warnings.push({
          line: 1,
          column: 1,
          message: `Variable '${variable}' is declared but never used`,
          severity: 'warning',
          code: 'UNUSED_VARIABLE'
        });
      }
    });

    // Add performance suggestions
    if (complexity > 50) {
      suggestions.push('Consider breaking down complex logic into smaller functions');
    }
    if (estimatedExecutionTime > 1000) {
      suggestions.push('Script may have performance issues - consider optimizing loops and calculations');
    }

    return {
      isValid: errors.length === 0,
      errors,
      warnings,
      suggestions,
      performance: {
        complexity,
        estimatedExecutionTime,
        memoryUsage
      }
    };
  }

  private checkSyntaxErrors(line: string, lineNumber: number, errors: HaasScriptValidationError[]): void {
    // Check for unmatched parentheses
    const openParens = (line.match(/\(/g) || []).length;
    const closeParens = (line.match(/\)/g) || []).length;
    if (openParens !== closeParens) {
      errors.push({
        line: lineNumber,
        column: 1,
        message: 'Unmatched parentheses',
        severity: 'error',
        code: 'UNMATCHED_PARENS'
      });
    }

    // Check for unmatched brackets
    const openBrackets = (line.match(/\[/g) || []).length;
    const closeBrackets = (line.match(/\]/g) || []).length;
    if (openBrackets !== closeBrackets) {
      errors.push({
        line: lineNumber,
        column: 1,
        message: 'Unmatched brackets',
        severity: 'error',
        code: 'UNMATCHED_BRACKETS'
      });
    }

    // Check for invalid characters
    const invalidChars = line.match(/[^\w\s\(\)\[\]\{\}\.,:;=<>!&|\+\-\*\/\%\^~\?'"\\]/g);
    if (invalidChars) {
      errors.push({
        line: lineNumber,
        column: line.indexOf(invalidChars[0]) + 1,
        message: `Invalid character: ${invalidChars[0]}`,
        severity: 'error',
        code: 'INVALID_CHARACTER'
      });
    }
  }

  private checkControlStructures(
    line: string, 
    lineNumber: number, 
    controlStack: Array<{ type: string; line: number }>, 
    errors: HaasScriptValidationError[]
  ): void {
    const trimmedLine = line.trim().toLowerCase();

    // Opening control structures
    if (trimmedLine.startsWith('if ')) {
      controlStack.push({ type: 'if', line: lineNumber });
    } else if (trimmedLine.startsWith('while ')) {
      controlStack.push({ type: 'while', line: lineNumber });
    } else if (trimmedLine.startsWith('for ')) {
      controlStack.push({ type: 'for', line: lineNumber });
    } else if (trimmedLine.startsWith('function ')) {
      controlStack.push({ type: 'function', line: lineNumber });
    }

    // Closing control structures
    else if (trimmedLine === 'endif') {
      const lastControl = controlStack.pop();
      if (!lastControl || lastControl.type !== 'if') {
        errors.push({
          line: lineNumber,
          column: 1,
          message: 'Unexpected endif - no matching if statement',
          severity: 'error',
          code: 'UNMATCHED_ENDIF'
        });
      }
    } else if (trimmedLine === 'endwhile') {
      const lastControl = controlStack.pop();
      if (!lastControl || lastControl.type !== 'while') {
        errors.push({
          line: lineNumber,
          column: 1,
          message: 'Unexpected endwhile - no matching while statement',
          severity: 'error',
          code: 'UNMATCHED_ENDWHILE'
        });
      }
    } else if (trimmedLine === 'endfor') {
      const lastControl = controlStack.pop();
      if (!lastControl || lastControl.type !== 'for') {
        errors.push({
          line: lineNumber,
          column: 1,
          message: 'Unexpected endfor - no matching for statement',
          severity: 'error',
          code: 'UNMATCHED_ENDFOR'
        });
      }
    } else if (trimmedLine === 'endfunction') {
      const lastControl = controlStack.pop();
      if (!lastControl || lastControl.type !== 'function') {
        errors.push({
          line: lineNumber,
          column: 1,
          message: 'Unexpected endfunction - no matching function statement',
          severity: 'error',
          code: 'UNMATCHED_ENDFUNCTION'
        });
      }
    }
  }

  private checkVariableUsage(
    line: string,
    lineNumber: number,
    declaredVariables: Set<string>,
    usedVariables: Set<string>,
    errors: HaasScriptValidationError[],
    warnings: HaasScriptValidationError[]
  ): void {
    // Check for variable declarations
    const varDeclaration = line.match(/(?:var|let|const)\s+(\w+)/);
    if (varDeclaration) {
      const varName = varDeclaration[1];
      if (declaredVariables.has(varName)) {
        warnings.push({
          line: lineNumber,
          column: line.indexOf(varName) + 1,
          message: `Variable '${varName}' is already declared`,
          severity: 'warning',
          code: 'REDECLARED_VARIABLE'
        });
      }
      declaredVariables.add(varName);
    }

    // Check for variable usage
    const variableUsage = line.match(/\b([a-zA-Z_]\w*)\b/g);
    if (variableUsage) {
      variableUsage.forEach(variable => {
        if (!this.keywords.includes(variable.toLowerCase()) && 
            !this.builtinFunctions.includes(variable)) {
          usedVariables.add(variable);
          
          // Check if variable is used before declaration
          if (!declaredVariables.has(variable) && !this.isBuiltinVariable(variable)) {
            errors.push({
              line: lineNumber,
              column: line.indexOf(variable) + 1,
              message: `Variable '${variable}' is used before declaration`,
              severity: 'error',
              code: 'UNDECLARED_VARIABLE'
            });
          }
        }
      });
    }
  }

  private checkFunctionCalls(
    line: string,
    lineNumber: number,
    warnings: HaasScriptValidationError[],
    suggestions: string[]
  ): void {
    // Check for function calls
    const functionCalls = line.match(/(\w+)\s*\(/g);
    if (functionCalls) {
      functionCalls.forEach(call => {
        const funcName = call.replace(/\s*\(/, '');
        if (!this.builtinFunctions.includes(funcName) && !this.keywords.includes(funcName.toLowerCase())) {
          warnings.push({
            line: lineNumber,
            column: line.indexOf(call) + 1,
            message: `Unknown function '${funcName}' - verify function name`,
            severity: 'warning',
            code: 'UNKNOWN_FUNCTION'
          });
        }
      });
    }

    // Check for common performance issues
    if (line.includes('while true') || line.includes('while 1')) {
      warnings.push({
        line: lineNumber,
        column: 1,
        message: 'Infinite loop detected - ensure there is a break condition',
        severity: 'warning',
        code: 'INFINITE_LOOP'
      });
    }
  }

  private calculateLineComplexity(line: string): number {
    let complexity = 1;
    
    // Add complexity for control structures
    if (/\b(if|while|for)\b/.test(line)) complexity += 2;
    if (/\b(else|elseif)\b/.test(line)) complexity += 1;
    
    // Add complexity for logical operators
    const logicalOps = (line.match(/\b(and|or|not)\b/g) || []).length;
    complexity += logicalOps;
    
    // Add complexity for nested function calls
    const functionCalls = (line.match(/\w+\s*\(/g) || []).length;
    complexity += functionCalls * 0.5;
    
    return complexity;
  }

  private estimateLineExecutionTime(line: string): number {
    let time = 1; // Base execution time
    
    // Add time for function calls
    const functionCalls = (line.match(/\w+\s*\(/g) || []).length;
    time += functionCalls * 2;
    
    // Add time for mathematical operations
    const mathOps = (line.match(/[\+\-\*\/\%]/g) || []).length;
    time += mathOps * 0.5;
    
    // Add time for loops
    if (/\b(while|for)\b/.test(line)) time += 10;
    
    return time;
  }

  private estimateLineMemoryUsage(line: string): number {
    let memory = 1; // Base memory usage
    
    // Add memory for variable declarations
    if (/\b(var|let|const)\b/.test(line)) memory += 4;
    
    // Add memory for arrays
    if (/\[.*\]/.test(line)) memory += 8;
    
    // Add memory for string operations
    if (/".*"/.test(line) || /'.*'/.test(line)) memory += 2;
    
    return memory;
  }

  private isBuiltinVariable(variable: string): boolean {
    const builtinVars = ['true', 'false', 'null', 'undefined'];
    return builtinVars.includes(variable.toLowerCase());
  }
}