import React from 'react'
import type { 
  GenerativeComponent, 
  ComponentProps, 
  Interaction, 
  Adaptation,
  UIContext,
  InsightCard
} from '@/types'

// Component template definitions for common trading interface patterns
interface ComponentTemplate {
  id: string
  name: string
  description: string
  category: 'chart' | 'table' | 'card' | 'form' | 'dashboard' | 'indicator'
  defaultProps: ComponentProps
  requiredProps: string[]
  optionalProps: string[]
  interactions: Interaction[]
  adaptations: Adaptation[]
}

// Chart type definitions
export interface ChartType {
  type: 'line' | 'candlestick' | 'bar' | 'area' | 'scatter' | 'heatmap' | 'treemap'
  dimensions: '2d' | '3d'
  interactive: boolean
  realtime: boolean
}

export interface ChartCustomization {
  colors?: string[]
  theme?: 'light' | 'dark'
  annotations?: ChartAnnotation[]
  indicators?: TechnicalIndicator[]
  timeframe?: string
  zoom?: boolean
  pan?: boolean
  crosshair?: boolean
}

interface ChartAnnotation {
  type: 'line' | 'rectangle' | 'text' | 'arrow'
  position: { x: number; y: number }
  style: Record<string, any>
  content?: string
}

interface TechnicalIndicator {
  type: 'sma' | 'ema' | 'rsi' | 'macd' | 'bollinger' | 'stochastic'
  period: number
  parameters: Record<string, any>
  visible: boolean
}

// Component validation interface
interface ComponentValidation {
  isValid: boolean
  errors: ValidationError[]
  warnings: ValidationWarning[]
  suggestions: string[]
}

interface ValidationError {
  field: string
  message: string
  severity: 'error' | 'warning' | 'info'
}

interface ValidationWarning {
  field: string
  message: string
  suggestion: string
}

// Generative UI Engine class
export class GenerativeUIEngine {
  private templates: Map<string, ComponentTemplate> = new Map()
  private componentCache: Map<string, React.ComponentType<any>> = new Map()
  private validationRules: Map<string, (props: any) => ComponentValidation> = new Map()

  constructor() {
    this.initializeTemplates()
    this.initializeValidationRules()
  }

  // Initialize component templates for common trading patterns
  private initializeTemplates(): void {
    // Price Chart Template
    this.templates.set('price-chart', {
      id: 'price-chart',
      name: 'Price Chart',
      description: 'Interactive price chart with technical indicators',
      category: 'chart',
      defaultProps: {
        type: 'candlestick',
        timeframe: '1h',
        height: 400,
        showVolume: true,
        showGrid: true,
        theme: 'dark'
      },
      requiredProps: ['data', 'symbol'],
      optionalProps: ['indicators', 'annotations', 'timeframe', 'height'],
      interactions: [
        {
          type: 'zoom',
          handler: (event: any) => console.log('Chart zoom:', event),
          description: 'Zoom in/out on chart data'
        },
        {
          type: 'hover',
          handler: (event: any) => console.log('Chart hover:', event),
          description: 'Show price details on hover'
        }
      ],
      adaptations: [
        {
          trigger: 'viewport_small',
          modification: 'reduce_height',
          description: 'Reduce chart height on small screens'
        }
      ]
    })

    // Performance Card Template
    this.templates.set('performance-card', {
      id: 'performance-card',
      name: 'Performance Card',
      description: 'Trading performance metrics display',
      category: 'card',
      defaultProps: {
        showPnL: true,
        showDrawdown: true,
        showWinRate: true,
        timeframe: '24h',
        format: 'percentage'
      },
      requiredProps: ['data'],
      optionalProps: ['timeframe', 'format', 'showPnL', 'showDrawdown'],
      interactions: [
        {
          type: 'click',
          handler: (event: any) => console.log('Performance card clicked:', event),
          description: 'Show detailed performance breakdown'
        }
      ],
      adaptations: [
        {
          trigger: 'data_negative',
          modification: 'highlight_red',
          description: 'Highlight negative performance in red'
        }
      ]
    })

    // Strategy Table Template
    this.templates.set('strategy-table', {
      id: 'strategy-table',
      name: 'Strategy Table',
      description: 'Tabular display of trading strategies',
      category: 'table',
      defaultProps: {
        sortable: true,
        filterable: true,
        paginated: true,
        pageSize: 10,
        columns: ['name', 'performance', 'risk', 'status']
      },
      requiredProps: ['data', 'columns'],
      optionalProps: ['sortable', 'filterable', 'pageSize'],
      interactions: [
        {
          type: 'click',
          handler: (event: any) => console.log('Strategy row clicked:', event),
          description: 'Select strategy for detailed view'
        }
      ],
      adaptations: [
        {
          trigger: 'viewport_mobile',
          modification: 'stack_columns',
          description: 'Stack columns vertically on mobile'
        }
      ]
    })

    // Risk Indicator Template
    this.templates.set('risk-indicator', {
      id: 'risk-indicator',
      name: 'Risk Indicator',
      description: 'Visual risk level indicator',
      category: 'indicator',
      defaultProps: {
        type: 'gauge',
        scale: 'low-high',
        showLabel: true,
        animated: true
      },
      requiredProps: ['value', 'maxValue'],
      optionalProps: ['type', 'scale', 'showLabel', 'animated'],
      interactions: [
        {
          type: 'hover',
          handler: (event: any) => console.log('Risk indicator hover:', event),
          description: 'Show risk breakdown on hover'
        }
      ],
      adaptations: [
        {
          trigger: 'value_high',
          modification: 'pulse_animation',
          description: 'Add pulsing animation for high risk'
        }
      ]
    })

    // Market Overview Dashboard Template
    this.templates.set('market-dashboard', {
      id: 'market-dashboard',
      name: 'Market Dashboard',
      description: 'Comprehensive market overview dashboard',
      category: 'dashboard',
      defaultProps: {
        layout: 'grid',
        columns: 3,
        showHeatmap: true,
        showTopMovers: true,
        showSentiment: true,
        refreshInterval: 30000
      },
      requiredProps: ['markets'],
      optionalProps: ['layout', 'columns', 'refreshInterval'],
      interactions: [
        {
          type: 'click',
          handler: (event: any) => console.log('Market clicked:', event),
          description: 'Navigate to market details'
        }
      ],
      adaptations: [
        {
          trigger: 'viewport_tablet',
          modification: 'reduce_columns',
          description: 'Reduce columns on tablet view'
        }
      ]
    })
  }

  // Initialize validation rules for component props
  private initializeValidationRules(): void {
    // Price Chart validation
    this.validationRules.set('price-chart', (props: any): ComponentValidation => {
      const errors: ValidationError[] = []
      const warnings: ValidationWarning[] = []
      const suggestions: string[] = []

      if (!props.data || !Array.isArray(props.data)) {
        errors.push({
          field: 'data',
          message: 'Data must be an array of price points',
          severity: 'error'
        })
      }

      if (!props.symbol || typeof props.symbol !== 'string') {
        errors.push({
          field: 'symbol',
          message: 'Symbol must be a valid string',
          severity: 'error'
        })
      }

      if (props.height && (props.height < 200 || props.height > 800)) {
        warnings.push({
          field: 'height',
          message: 'Chart height should be between 200-800px for optimal viewing',
          suggestion: 'Consider using height between 300-500px'
        })
      }

      if (props.data && props.data.length > 10000) {
        warnings.push({
          field: 'data',
          message: 'Large dataset may impact performance',
          suggestion: 'Consider data pagination or aggregation'
        })
      }

      if (props.indicators && props.indicators.length > 5) {
        suggestions.push('Too many indicators may clutter the chart')
      }

      return {
        isValid: errors.length === 0,
        errors,
        warnings,
        suggestions
      }
    })

    // Performance Card validation
    this.validationRules.set('performance-card', (props: any): ComponentValidation => {
      const errors: ValidationError[] = []
      const warnings: ValidationWarning[] = []
      const suggestions: string[] = []

      if (!props.data || typeof props.data !== 'object') {
        errors.push({
          field: 'data',
          message: 'Performance data must be an object with metrics',
          severity: 'error'
        })
      }

      if (props.data && !props.data.pnl && !props.data.return) {
        warnings.push({
          field: 'data',
          message: 'No P&L or return data found',
          suggestion: 'Include pnl or return metrics for meaningful display'
        })
      }

      return {
        isValid: errors.length === 0,
        errors,
        warnings,
        suggestions
      }
    })

    // Strategy Table validation
    this.validationRules.set('strategy-table', (props: any): ComponentValidation => {
      const errors: ValidationError[] = []
      const warnings: ValidationWarning[] = []
      const suggestions: string[] = []

      if (!props.data || !Array.isArray(props.data)) {
        errors.push({
          field: 'data',
          message: 'Data must be an array of strategy objects',
          severity: 'error'
        })
      }

      if (!props.columns || !Array.isArray(props.columns)) {
        errors.push({
          field: 'columns',
          message: 'Columns must be an array of column definitions',
          severity: 'error'
        })
      }

      if (props.pageSize && props.pageSize > 100) {
        warnings.push({
          field: 'pageSize',
          message: 'Large page size may impact performance',
          suggestion: 'Consider using pageSize <= 50 for better UX'
        })
      }

      return {
        isValid: errors.length === 0,
        errors,
        warnings,
        suggestions
      }
    })
  }

  // Generate UI component from natural language description
  async generateComponent(
    description: string,
    context: UIContext,
    data?: any
  ): Promise<React.ComponentType<any>> {
    try {
      // Analyze description to determine component type
      const componentType = this.analyzeComponentType(description)
      
      // Get appropriate template
      const template = this.templates.get(componentType)
      if (!template) {
        throw new Error(`No template found for component type: ${componentType}`)
      }

      // Generate props from description and context
      const props = await this.generatePropsFromDescription(
        description,
        template,
        context,
        data
      )

      // Validate generated props
      const validation = this.validateComponent(componentType, props)
      if (!validation.isValid) {
        console.warn('Component validation failed:', validation.errors)
        // Apply fixes for common validation errors
        this.applyValidationFixes(props, validation)
      }

      // Generate the actual React component
      const component = this.createReactComponent(template, props, validation)

      // Cache the component for reuse
      const cacheKey = this.generateCacheKey(description, context, data)
      this.componentCache.set(cacheKey, component)

      return component
    } catch (error) {
      console.error('Component generation failed:', error)
      throw error
    }
  }

  // Analyze description to determine component type
  private analyzeComponentType(description: string): string {
    const lowerDesc = description.toLowerCase()

    // Chart patterns
    if (lowerDesc.includes('chart') || lowerDesc.includes('graph') || 
        lowerDesc.includes('plot') || lowerDesc.includes('price')) {
      return 'price-chart'
    }

    // Performance patterns
    if (lowerDesc.includes('performance') || lowerDesc.includes('pnl') || 
        lowerDesc.includes('profit') || lowerDesc.includes('return')) {
      return 'performance-card'
    }

    // Table patterns
    if (lowerDesc.includes('table') || lowerDesc.includes('list') || 
        lowerDesc.includes('strategies') || lowerDesc.includes('rows')) {
      return 'strategy-table'
    }

    // Risk patterns
    if (lowerDesc.includes('risk') || lowerDesc.includes('exposure') || 
        lowerDesc.includes('danger') || lowerDesc.includes('safety')) {
      return 'risk-indicator'
    }

    // Dashboard patterns
    if (lowerDesc.includes('dashboard') || lowerDesc.includes('overview') || 
        lowerDesc.includes('summary') || lowerDesc.includes('market')) {
      return 'market-dashboard'
    }

    // Default to performance card for general requests
    return 'performance-card'
  }

  // Generate component props from description and context
  private async generatePropsFromDescription(
    description: string,
    template: ComponentTemplate,
    context: UIContext,
    data?: any
  ): Promise<ComponentProps> {
    const props: ComponentProps = { ...template.defaultProps }

    // Add data if provided
    if (data) {
      props.data = data
    }

    // Extract specific requirements from description
    const requirements = this.extractRequirements(description)

    // Apply requirements to props
    requirements.forEach(req => {
      switch (req.type) {
        case 'timeframe':
          props.timeframe = req.value
          break
        case 'height':
          props.height = parseInt(req.value)
          break
        case 'theme':
          props.theme = req.value
          break
        case 'symbol':
          props.symbol = req.value
          break
        case 'format':
          props.format = req.value
          break
      }
    })

    // Apply context-based adaptations
    if (context.userPreferences.theme) {
      props.theme = context.userPreferences.theme
    }

    if (context.selectedAssets.length > 0) {
      props.symbol = context.selectedAssets[0]
      props.symbols = context.selectedAssets
    }

    // Apply persona-based customizations
    if (context.persona) {
      this.applyPersonaCustomizations(props, context.persona, template)
    }

    return props
  }

  // Extract specific requirements from natural language description
  private extractRequirements(description: string): Array<{type: string, value: string}> {
    const requirements: Array<{type: string, value: string}> = []

    // Timeframe patterns
    const timeframeMatch = description.match(/(1m|5m|15m|30m|1h|4h|1d|1w)/i)
    if (timeframeMatch) {
      requirements.push({ type: 'timeframe', value: timeframeMatch[1] })
    }

    // Height patterns
    const heightMatch = description.match(/(\d+)\s*(?:px|pixels?)\s*(?:high|height)/i)
    if (heightMatch) {
      requirements.push({ type: 'height', value: heightMatch[1] })
    }

    // Theme patterns
    const themeMatch = description.match(/(light|dark)\s*(?:theme|mode)/i)
    if (themeMatch) {
      requirements.push({ type: 'theme', value: themeMatch[1].toLowerCase() })
    }

    // Symbol patterns
    const symbolMatch = description.match(/(?:for|of|show)\s+([A-Z]{3,6}(?:\/[A-Z]{3,6})?)/i)
    if (symbolMatch) {
      requirements.push({ type: 'symbol', value: symbolMatch[1].toUpperCase() })
    }

    // Format patterns
    const formatMatch = description.match(/(percentage|decimal|currency)\s*(?:format)?/i)
    if (formatMatch) {
      requirements.push({ type: 'format', value: formatMatch[1].toLowerCase() })
    }

    return requirements
  }

  // Apply persona-based customizations to props
  private applyPersonaCustomizations(
    props: ComponentProps,
    persona: any,
    template: ComponentTemplate
  ): void {
    switch (persona.type) {
      case 'conservative':
        if (template.category === 'chart') {
          props.showRiskIndicators = true
          props.highlightDrawdowns = true
        }
        if (template.category === 'card') {
          props.emphasizeRisk = true
          props.showWorstCase = true
        }
        break

      case 'aggressive':
        if (template.category === 'chart') {
          props.showOpportunities = true
          props.highlightBreakouts = true
        }
        if (template.category === 'card') {
          props.emphasizeReturns = true
          props.showBestCase = true
        }
        break

      case 'balanced':
        if (template.category === 'chart') {
          props.showBothRiskAndOpportunity = true
        }
        if (template.category === 'card') {
          props.balancedView = true
        }
        break
    }

    // Apply risk tolerance settings
    if (persona.riskTolerance !== undefined) {
      props.riskTolerance = persona.riskTolerance
      if (persona.riskTolerance < 0.3) {
        props.conservativeMode = true
      } else if (persona.riskTolerance > 0.7) {
        props.aggressiveMode = true
      }
    }
  }

  // Validate component props against template requirements
  validateComponent(componentType: string, props: ComponentProps): ComponentValidation {
    const validator = this.validationRules.get(componentType)
    if (!validator) {
      return {
        isValid: true,
        errors: [],
        warnings: [],
        suggestions: []
      }
    }

    return validator(props)
  }

  // Apply automatic fixes for common validation errors
  private applyValidationFixes(props: ComponentProps, validation: ComponentValidation): void {
    validation.errors.forEach(error => {
      switch (error.field) {
        case 'data':
          if (!props.data) {
            props.data = []
          }
          break
        case 'symbol':
          if (!props.symbol) {
            props.symbol = 'BTC/USDT'
          }
          break
        case 'columns':
          if (!props.columns) {
            props.columns = ['name', 'value']
          }
          break
      }
    })

    validation.warnings.forEach(warning => {
      switch (warning.field) {
        case 'height':
          if (props.height < 200) props.height = 300
          if (props.height > 800) props.height = 500
          break
        case 'pageSize':
          if (props.pageSize > 100) props.pageSize = 50
          break
      }
    })
  }

  // Create the actual React component from template and props
  private createReactComponent(
    template: ComponentTemplate,
    props: ComponentProps,
    validation: ComponentValidation
  ): React.ComponentType<any> {
    const componentName = `Generated${template.name.replace(/\s+/g, '')}`

    // Create component based on template category
    switch (template.category) {
      case 'chart':
        return this.createChartComponent(componentName, props, template)
      case 'card':
        return this.createCardComponent(componentName, props, template)
      case 'table':
        return this.createTableComponent(componentName, props, template)
      case 'indicator':
        return this.createIndicatorComponent(componentName, props, template)
      case 'dashboard':
        return this.createDashboardComponent(componentName, props, template)
      default:
        return this.createGenericComponent(componentName, props, template)
    }
  }

  // Create chart component
  private createChartComponent(
    name: string,
    props: ComponentProps,
    template: ComponentTemplate
  ): React.ComponentType<any> {
    return React.memo((componentProps: any) => {
      const mergedProps = { ...props, ...componentProps }
      
      return React.createElement('div', {
        className: 'generated-chart-component bg-gray-900 rounded-lg p-4',
        style: { height: mergedProps.height || 400 }
      }, [
        React.createElement('h3', {
          key: 'title',
          className: 'text-white text-lg font-semibold mb-4'
        }, `${mergedProps.symbol || 'Chart'} - ${mergedProps.timeframe || '1h'}`),
        
        React.createElement('div', {
          key: 'chart-placeholder',
          className: 'w-full h-full bg-gray-800 rounded flex items-center justify-center text-gray-400',
          style: { minHeight: (mergedProps.height || 400) - 80 }
        }, `${template.name} Component - Data: ${Array.isArray(mergedProps.data) ? mergedProps.data.length : 0} points`)
      ])
    })
  }

  // Create card component
  private createCardComponent(
    name: string,
    props: ComponentProps,
    template: ComponentTemplate
  ): React.ComponentType<any> {
    return React.memo((componentProps: any) => {
      const mergedProps = { ...props, ...componentProps }
      
      return React.createElement('div', {
        className: 'generated-card-component bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6'
      }, [
        React.createElement('h3', {
          key: 'title',
          className: 'text-lg font-semibold text-gray-900 dark:text-white mb-4'
        }, template.name),
        
        React.createElement('div', {
          key: 'content',
          className: 'space-y-2'
        }, [
          mergedProps.data && Object.entries(mergedProps.data).map(([key, value]: [string, any], index: number) =>
            React.createElement('div', {
              key: `metric-${index}`,
              className: 'flex justify-between items-center'
            }, [
              React.createElement('span', {
                key: 'label',
                className: 'text-gray-600 dark:text-gray-300'
              }, key.charAt(0).toUpperCase() + key.slice(1)),
              React.createElement('span', {
                key: 'value',
                className: `font-semibold ${typeof value === 'number' && value < 0 ? 'text-red-500' : 'text-green-500'}`
              }, typeof value === 'number' ? 
                (mergedProps.format === 'percentage' ? `${(value * 100).toFixed(2)}%` : value.toFixed(2)) : 
                String(value))
            ])
          )
        ])
      ])
    })
  }

  // Create table component
  private createTableComponent(
    name: string,
    props: ComponentProps,
    template: ComponentTemplate
  ): React.ComponentType<any> {
    return React.memo((componentProps: any) => {
      const mergedProps = { ...props, ...componentProps }
      const data = mergedProps.data || []
      const columns = mergedProps.columns || []
      
      return React.createElement('div', {
        className: 'generated-table-component bg-white dark:bg-gray-800 rounded-lg shadow-lg overflow-hidden'
      }, [
        React.createElement('div', {
          key: 'header',
          className: 'px-6 py-4 border-b border-gray-200 dark:border-gray-700'
        }, React.createElement('h3', {
          className: 'text-lg font-semibold text-gray-900 dark:text-white'
        }, template.name)),
        
        React.createElement('div', {
          key: 'table-container',
          className: 'overflow-x-auto'
        }, React.createElement('table', {
          className: 'w-full'
        }, [
          React.createElement('thead', {
            key: 'thead',
            className: 'bg-gray-50 dark:bg-gray-700'
          }, React.createElement('tr', {}, 
            columns.map((column: string, index: number) =>
              React.createElement('th', {
                key: `header-${index}`,
                className: 'px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider'
              }, column.charAt(0).toUpperCase() + column.slice(1))
            )
          )),
          
          React.createElement('tbody', {
            key: 'tbody',
            className: 'bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700'
          }, data.slice(0, mergedProps.pageSize || 10).map((row: any, rowIndex: number) =>
            React.createElement('tr', {
              key: `row-${rowIndex}`,
              className: 'hover:bg-gray-50 dark:hover:bg-gray-700'
            }, columns.map((column: string, colIndex: number) =>
              React.createElement('td', {
                key: `cell-${rowIndex}-${colIndex}`,
                className: 'px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white'
              }, String(row[column] || '-'))
            ))
          ))
        ]))
      ])
    })
  }

  // Create indicator component
  private createIndicatorComponent(
    name: string,
    props: ComponentProps,
    template: ComponentTemplate
  ): React.ComponentType<any> {
    return React.memo((componentProps: any) => {
      const mergedProps = { ...props, ...componentProps }
      const value = mergedProps.value || 0
      const maxValue = mergedProps.maxValue || 100
      const percentage = (value / maxValue) * 100
      
      return React.createElement('div', {
        className: 'generated-indicator-component bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6'
      }, [
        React.createElement('h3', {
          key: 'title',
          className: 'text-lg font-semibold text-gray-900 dark:text-white mb-4'
        }, template.name),
        
        React.createElement('div', {
          key: 'indicator',
          className: 'relative'
        }, [
          React.createElement('div', {
            key: 'background',
            className: 'w-full bg-gray-200 dark:bg-gray-700 rounded-full h-4'
          }),
          React.createElement('div', {
            key: 'fill',
            className: `absolute top-0 left-0 h-4 rounded-full transition-all duration-300 ${
              percentage < 30 ? 'bg-green-500' : 
              percentage < 70 ? 'bg-yellow-500' : 'bg-red-500'
            }`,
            style: { width: `${Math.min(percentage, 100)}%` }
          }),
          React.createElement('div', {
            key: 'label',
            className: 'mt-2 text-center text-sm text-gray-600 dark:text-gray-300'
          }, `${value}${mergedProps.unit || ''} / ${maxValue}${mergedProps.unit || ''}`)
        ])
      ])
    })
  }

  // Create dashboard component
  private createDashboardComponent(
    name: string,
    props: ComponentProps,
    template: ComponentTemplate
  ): React.ComponentType<any> {
    return React.memo((componentProps: any) => {
      const mergedProps = { ...props, ...componentProps }
      const markets = mergedProps.markets || []
      
      return React.createElement('div', {
        className: 'generated-dashboard-component space-y-6'
      }, [
        React.createElement('h2', {
          key: 'title',
          className: 'text-2xl font-bold text-gray-900 dark:text-white'
        }, template.name),
        
        React.createElement('div', {
          key: 'grid',
          className: `grid grid-cols-1 md:grid-cols-${mergedProps.columns || 3} gap-6`
        }, markets.slice(0, 9).map((market: any, index: number) =>
          React.createElement('div', {
            key: `market-${index}`,
            className: 'bg-white dark:bg-gray-800 rounded-lg shadow-lg p-4'
          }, [
            React.createElement('h3', {
              key: 'market-name',
              className: 'font-semibold text-gray-900 dark:text-white'
            }, market.symbol || `Market ${index + 1}`),
            React.createElement('p', {
              key: 'market-price',
              className: 'text-lg font-bold text-green-500'
            }, market.price ? `$${market.price.toFixed(2)}` : '$0.00'),
            React.createElement('p', {
              key: 'market-change',
              className: `text-sm ${(market.change || 0) >= 0 ? 'text-green-500' : 'text-red-500'}`
            }, market.change ? `${market.change > 0 ? '+' : ''}${(market.change * 100).toFixed(2)}%` : '0.00%')
          ])
        ))
      ])
    })
  }

  // Create generic component fallback
  private createGenericComponent(
    name: string,
    props: ComponentProps,
    template: ComponentTemplate
  ): React.ComponentType<any> {
    return React.memo((componentProps: any) => {
      const mergedProps = { ...props, ...componentProps }
      
      return React.createElement('div', {
        className: 'generated-generic-component bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6'
      }, [
        React.createElement('h3', {
          key: 'title',
          className: 'text-lg font-semibold text-gray-900 dark:text-white mb-4'
        }, template.name),
        React.createElement('p', {
          key: 'description',
          className: 'text-gray-600 dark:text-gray-300'
        }, template.description),
        React.createElement('pre', {
          key: 'props',
          className: 'mt-4 text-xs bg-gray-100 dark:bg-gray-700 p-2 rounded overflow-auto'
        }, JSON.stringify(mergedProps, null, 2))
      ])
    })
  }

  // Generate cache key for component caching
  private generateCacheKey(description: string, context: UIContext, data?: any): string {
    const contextHash = JSON.stringify({
      view: context.currentView,
      assets: context.selectedAssets,
      persona: context.persona?.type,
      theme: context.userPreferences.theme
    })
    
    const dataHash = data ? JSON.stringify(data).substring(0, 100) : 'no-data'
    
    return `${description.substring(0, 50)}-${btoa(contextHash).substring(0, 10)}-${btoa(dataHash).substring(0, 10)}`
  }

  // Get available component templates
  getAvailableTemplates(): ComponentTemplate[] {
    return Array.from(this.templates.values())
  }

  // Get template by ID
  getTemplate(templateId: string): ComponentTemplate | undefined {
    return this.templates.get(templateId)
  }

  // Clear component cache
  clearCache(): void {
    this.componentCache.clear()
  }

  // Get cache statistics
  getCacheStats(): { size: number; keys: string[] } {
    return {
      size: this.componentCache.size,
      keys: Array.from(this.componentCache.keys())
    }
  }
}

// Export singleton instance
export const generativeUIEngine = new GenerativeUIEngine()