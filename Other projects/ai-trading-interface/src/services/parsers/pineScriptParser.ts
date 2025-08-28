import { ExternalStrategy, ExternalParameter, TranslationError, TranslationWarning } from '../../types/translation';

export class PineScriptParser {
  private errors: TranslationError[] = [];
  private warnings: TranslationWarning[] = [];

  parseStrategy(code: string, name: string = 'Imported Pine Script'): ExternalStrategy {
    this.errors = [];
    this.warnings = [];

    const lines = code.split('\n');
    const metadata = this.extractMetadata(lines);
    const parameters = this.extractParameters(lines);
    const indicators = this.extractIndicators(lines);

    return {
      id: `pine_${Date.now()}`,
      name,
      description: metadata.description || 'Imported from Pine Script',
      sourceFormat: 'pine_script',
      sourceCode: code,
      metadata: {
        author: metadata.author,
        version: metadata.version,
        timeframe: metadata.timeframe,
        markets: metadata.markets,
        indicators,
        parameters
      },
      createdAt: new Date()
    };
  }

  private extractMetadata(lines: string[]): any {
    const metadata: any = {};
    
    // Look for //@version directive
    const versionLine = lines.find(line => line.trim().startsWith('//@version'));
    if (versionLine) {
      metadata.version = versionLine.split('=')[1]?.trim();
    }

    // Look for study/strategy declaration
    const studyLine = lines.find(line => 
      line.trim().startsWith('study(') || 
      line.trim().startsWith('strategy(') ||
      line.trim().startsWith('indicator(')
    );

    if (studyLine) {
      // Extract title
      const titleMatch = studyLine.match(/title\s*=\s*["']([^"']+)["']/);
      if (titleMatch) {
        metadata.title = titleMatch[1];
      }

      // Extract shorttitle
      const shortTitleMatch = studyLine.match(/shorttitle\s*=\s*["']([^"']+)["']/);
      if (shortTitleMatch) {
        metadata.shortTitle = shortTitleMatch[1];
      }

      // Extract overlay
      const overlayMatch = studyLine.match(/overlay\s*=\s*(true|false)/);
      if (overlayMatch) {
        metadata.overlay = overlayMatch[1] === 'true';
      }
    }

    // Look for comments with metadata
    lines.forEach((line, index) => {
      const trimmed = line.trim();
      if (trimmed.startsWith('//')) {
        const comment = trimmed.substring(2).trim();
        
        // Check for author
        if (comment.toLowerCase().includes('author:') || comment.toLowerCase().includes('by:')) {
          metadata.author = comment.split(':')[1]?.trim();
        }
        
        // Check for description
        if (comment.toLowerCase().includes('description:')) {
          metadata.description = comment.split(':')[1]?.trim();
        }
      }
    });

    return metadata;
  }

  private extractParameters(lines: string[]): ExternalParameter[] {
    const parameters: ExternalParameter[] = [];
    
    lines.forEach((line, index) => {
      const trimmed = line.trim();
      
      // Look for input declarations
      const inputMatch = trimmed.match(/^(\w+)\s*=\s*input(?:\.(\w+))?\s*\(\s*([^)]+)\s*\)/);
      if (inputMatch) {
        const [, varName, inputType, params] = inputMatch;
        
        const param = this.parseInputParameters(varName, inputType, params, index + 1);
        if (param) {
          parameters.push(param);
        }
      }
      
      // Look for variable declarations with default values
      const varMatch = trimmed.match(/^var\s+(\w+)\s*=\s*(.+)/);
      if (varMatch) {
        const [, varName, defaultValue] = varMatch;
        
        parameters.push({
          name: varName,
          type: 'variable',
          dataType: this.inferDataType(defaultValue),
          value: this.parseValue(defaultValue),
          defaultValue: this.parseValue(defaultValue),
          description: `Variable: ${varName}`
        });
      }
    });

    return parameters;
  }

  private parseInputParameters(varName: string, inputType: string | undefined, params: string, lineNumber: number): ExternalParameter | null {
    try {
      // Parse parameter string
      const paramParts = this.parseParameterString(params);
      
      const defaultValue = paramParts.defval || paramParts[0];
      const title = paramParts.title || varName;
      const tooltip = paramParts.tooltip;
      const minval = paramParts.minval;
      const maxval = paramParts.maxval;
      const step = paramParts.step;
      const options = paramParts.options;

      return {
        name: varName,
        type: 'input',
        dataType: (inputType as 'int' | 'float' | 'bool' | 'string' | 'color') || this.inferDataType(defaultValue),
        value: this.parseValue(defaultValue),
        defaultValue: this.parseValue(defaultValue),
        description: tooltip || title || `Input parameter: ${varName}`,
        min: minval ? this.parseValue(minval) : undefined,
        max: maxval ? this.parseValue(maxval) : undefined,
        step: step ? this.parseValue(step) : undefined,
        options: options ? this.parseOptions(options) : undefined
      };
    } catch (error) {
      this.errors.push({
        line: lineNumber,
        message: `Failed to parse input parameter: ${varName}`,
        category: 'syntax_error',
        originalCode: `${varName} = input(${params})`,
        possibleSolutions: ['Check parameter syntax', 'Verify parameter types']
      });
      return null;
    }
  }

  private parseParameterString(params: string): Record<string, string> {
    const result: Record<string, string> = {};
    const parts = params.split(',');
    
    parts.forEach((part, index) => {
      const trimmed = part.trim();
      
      if (trimmed.includes('=')) {
        const [key, value] = trimmed.split('=', 2);
        result[key.trim()] = value.trim();
      } else if (index === 0) {
        // First parameter is usually the default value
        result.defval = trimmed;
      }
    });
    
    return result;
  }

  private inferDataType(value: string): 'int' | 'float' | 'bool' | 'string' | 'color' {
    const trimmed = value.trim().replace(/['"]/g, '');
    
    if (trimmed === 'true' || trimmed === 'false') {
      return 'bool';
    }
    
    if (trimmed.startsWith('#') || trimmed.startsWith('color.')) {
      return 'color';
    }
    
    if (/^\d+$/.test(trimmed)) {
      return 'int';
    }
    
    if (/^\d*\.\d+$/.test(trimmed)) {
      return 'float';
    }
    
    return 'string';
  }

  private parseValue(value: string): any {
    const trimmed = value.trim();
    
    // Remove quotes for strings
    if ((trimmed.startsWith('"') && trimmed.endsWith('"')) ||
        (trimmed.startsWith("'") && trimmed.endsWith("'"))) {
      return trimmed.slice(1, -1);
    }
    
    // Boolean values
    if (trimmed === 'true') return true;
    if (trimmed === 'false') return false;
    
    // Numeric values
    if (/^\d+$/.test(trimmed)) {
      return parseInt(trimmed, 10);
    }
    
    if (/^\d*\.\d+$/.test(trimmed)) {
      return parseFloat(trimmed);
    }
    
    return trimmed;
  }

  private parseOptions(optionsStr: string): string[] {
    // Handle options like ["Option 1", "Option 2", "Option 3"]
    const match = optionsStr.match(/\[(.*)\]/);
    if (match) {
      return match[1].split(',').map(opt => opt.trim().replace(/['"]/g, ''));
    }
    return [];
  }

  private extractIndicators(lines: string[]): string[] {
    const indicators = new Set<string>();
    
    const commonIndicators = [
      'sma', 'ema', 'wma', 'rma', 'vwma',
      'rsi', 'macd', 'stoch', 'cci', 'atr',
      'bb', 'bollinger', 'adx', 'mfi', 'obv',
      'williams', 'stochrsi', 'tsi', 'cmo'
    ];
    
    lines.forEach(line => {
      const trimmed = line.trim().toLowerCase();
      
      commonIndicators.forEach(indicator => {
        if (trimmed.includes(`${indicator}(`)) {
          indicators.add(indicator.toUpperCase());
        }
      });
      
      // Look for ta. namespace indicators
      const taMatch = trimmed.match(/ta\.(\w+)\s*\(/g);
      if (taMatch) {
        taMatch.forEach(match => {
          const indicator = match.replace('ta.', '').replace('(', '');
          indicators.add(indicator.toUpperCase());
        });
      }
    });
    
    return Array.from(indicators);
  }

  getErrors(): TranslationError[] {
    return this.errors;
  }

  getWarnings(): TranslationWarning[] {
    return this.warnings;
  }
}