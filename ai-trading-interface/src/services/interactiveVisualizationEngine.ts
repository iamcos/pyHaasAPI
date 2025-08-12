import React from 'react'
import type { 
  UIContext
} from '@/types'

// Chart customization interface
export interface ChartCustomizationConfig {
  colors?: string[]
  theme?: 'light' | 'dark'
  annotations?: ChartAnnotation[]
  indicators?: TechnicalIndicator[]
  timeframe?: string
  zoom?: boolean
  pan?: boolean
  crosshair?: boolean
  realtime?: boolean
}

interface ChartAnnotation {
  type: 'line' | 'rectangle' | 'text' | 'arrow'
  mode?: 'horizontal' | 'vertical' | 'point'
  scaleID?: string
  value?: number | string
  endValue?: number | string
  position: { x: number; y: number }
  style: Record<string, any>
  content?: string
  borderColor?: string
  borderWidth?: number
  label?: {
    content: string
    position: 'start' | 'center' | 'end'
  }
}

interface TechnicalIndicator {
  type: 'sma' | 'ema' | 'rsi' | 'macd' | 'bollinger' | 'stochastic'
  period: number
  parameters: Record<string, any>
  visible: boolean
}

// Chart configuration interfaces
export interface ChartConfig {
  type: 'line' | 'candlestick' | 'bar' | 'area' | 'scatter' | 'heatmap' | 'treemap'
  data: any
  options: ChartOptions
  interactions: ChartInteraction[]
  realTimeConfig?: RealTimeConfig
}

export interface ChartOptions {
  responsive: boolean
  maintainAspectRatio: boolean
  animation: AnimationConfig
  scales: ScaleConfig
  plugins: PluginConfig
  layout: LayoutConfig
  elements: ElementConfig
}

export interface AnimationConfig {
  duration: number
  easing: 'linear' | 'easeInQuad' | 'easeOutQuad' | 'easeInOutQuad'
  animateRotate: boolean
  animateScale: boolean
}

export interface ScaleConfig {
  x: AxisConfig
  y: AxisConfig
  y1?: AxisConfig // Secondary y-axis
}

export interface AxisConfig {
  type: 'linear' | 'logarithmic' | 'category' | 'time' | 'timeseries'
  position: 'left' | 'right' | 'top' | 'bottom'
  display: boolean
  grid: GridConfig
  ticks: TickConfig
  title: TitleConfig
  min?: number
  max?: number
  beginAtZero?: boolean
}

export interface GridConfig {
  display: boolean
  color: string
  lineWidth: number
  drawBorder: boolean
  drawOnChartArea: boolean
  drawTicks: boolean
}

export interface TickConfig {
  display: boolean
  color: string
  font: FontConfig
  padding: number
  maxTicksLimit?: number
  stepSize?: number
  callback?: (value: any, index: number, values: any[]) => string
}

export interface TitleConfig {
  display: boolean
  text: string
  color: string
  font: FontConfig
  padding: number
}

export interface FontConfig {
  family: string
  size: number
  style: 'normal' | 'italic' | 'oblique'
  weight: 'normal' | 'bold' | 'lighter' | 'bolder' | number
  lineHeight: number
}

export interface PluginConfig {
  legend: LegendConfig
  tooltip: TooltipConfig
  title: TitleConfig
  subtitle?: TitleConfig
  zoom?: ZoomConfig
  pan?: PanConfig
  crosshair?: CrosshairConfig
  annotation?: AnnotationConfig
}

export interface LegendConfig {
  display: boolean
  position: 'top' | 'left' | 'bottom' | 'right' | 'chartArea'
  align: 'start' | 'center' | 'end'
  labels: LegendLabelConfig
  onClick?: (event: any, legendItem: any, legend: any) => void
}

export interface LegendLabelConfig {
  color: string
  font: FontConfig
  padding: number
  usePointStyle: boolean
  pointStyle: string
  generateLabels?: (chart: any) => any[]
}

export interface TooltipConfig {
  enabled: boolean
  mode: 'point' | 'nearest' | 'index' | 'dataset' | 'x' | 'y'
  intersect: boolean
  position: 'average' | 'nearest'
  backgroundColor: string
  titleColor: string
  titleFont: FontConfig
  bodyColor: string
  bodyFont: FontConfig
  borderColor: string
  borderWidth: number
  displayColors: boolean
  callbacks?: TooltipCallbacks
}

export interface TooltipCallbacks {
  title?: (tooltipItems: any[]) => string | string[]
  label?: (tooltipItem: any) => string | string[]
  footer?: (tooltipItems: any[]) => string | string[]
  beforeTitle?: (tooltipItems: any[]) => string | string[]
  afterTitle?: (tooltipItems: any[]) => string | string[]
  beforeBody?: (tooltipItems: any[]) => string | string[]
  afterBody?: (tooltipItems: any[]) => string | string[]
  beforeLabel?: (tooltipItem: any) => string | string[]
  afterLabel?: (tooltipItem: any) => string | string[]
  beforeFooter?: (tooltipItems: any[]) => string | string[]
  afterFooter?: (tooltipItems: any[]) => string | string[]
}

export interface ZoomConfig {
  enabled: boolean
  mode: 'x' | 'y' | 'xy'
  speed: number
  threshold: number
  sensitivity: number
  onZoom?: (chart: any) => void
  onZoomComplete?: (chart: any) => void
}

export interface PanConfig {
  enabled: boolean
  mode: 'x' | 'y' | 'xy'
  speed: number
  threshold: number
  onPan?: (chart: any) => void
  onPanComplete?: (chart: any) => void
}

export interface CrosshairConfig {
  enabled: boolean
  color: string
  width: number
  dash: number[]
  sync: boolean
}

export interface AnnotationConfig {
  annotations: Annotation[]
}

export interface Annotation {
  type: 'line' | 'box' | 'ellipse' | 'point' | 'polygon'
  mode: 'horizontal' | 'vertical' | 'point'
  scaleID: string
  value?: number | string
  endValue?: number | string
  backgroundColor?: string
  borderColor?: string
  borderWidth?: number
  label?: AnnotationLabel
}

export interface AnnotationLabel {
  enabled: boolean
  content: string
  position: 'start' | 'center' | 'end'
  backgroundColor: string
  color: string
  font: FontConfig
}

export interface LayoutConfig {
  padding: number | { top: number; right: number; bottom: number; left: number }
}

export interface ElementConfig {
  point: PointConfig
  line: LineConfig
  bar: BarConfig
  arc: ArcConfig
}

export interface PointConfig {
  radius: number
  pointStyle: 'circle' | 'cross' | 'crossRot' | 'dash' | 'line' | 'rect' | 'rectRounded' | 'rectRot' | 'star' | 'triangle'
  backgroundColor: string
  borderColor: string
  borderWidth: number
  hitRadius: number
  hoverRadius: number
  hoverBorderWidth: number
}

export interface LineConfig {
  tension: number
  backgroundColor: string
  borderColor: string
  borderWidth: number
  borderCapStyle: 'butt' | 'round' | 'square'
  borderDash: number[]
  borderDashOffset: number
  borderJoinStyle: 'bevel' | 'round' | 'miter'
  capBezierPoints: boolean
  cubicInterpolationMode: 'default' | 'monotone'
  fill: boolean | string | number
  stepped: boolean | 'before' | 'after' | 'middle'
}

export interface BarConfig {
  backgroundColor: string
  borderColor: string
  borderWidth: number
  borderSkipped: 'start' | 'end' | 'middle' | 'bottom' | 'left' | 'top' | 'right'
  borderRadius: number
  inflateAmount: number
}

export interface ArcConfig {
  backgroundColor: string
  borderColor: string
  borderWidth: number
  borderAlign: 'center' | 'inner'
}

// Chart interaction interfaces
export interface ChartInteraction {
  type: 'click' | 'hover' | 'zoom' | 'pan' | 'brush' | 'crossfilter'
  enabled: boolean
  handler: (event: any, elements: any[], chart: any) => void
  options?: any
}

// Real-time data configuration
export interface RealTimeConfig {
  enabled: boolean
  interval: number // milliseconds
  maxDataPoints: number
  dataSource: string | (() => Promise<any>)
  onUpdate?: (newData: any, chart: any) => void
  onError?: (error: Error) => void
}

// Data binding configuration
export interface DataBinding {
  source: string
  field: string
  transform?: (value: any) => any
  filter?: (value: any) => boolean
  aggregate?: 'sum' | 'avg' | 'min' | 'max' | 'count'
}

// Interactive Visualization Engine class
export class InteractiveVisualizationEngine {
  private chartInstances: Map<string, any> = new Map()
  private realTimeUpdaters: Map<string, NodeJS.Timeout> = new Map()
  private dataBindings: Map<string, DataBinding[]> = new Map()
  private themeConfig: any = null

  constructor() {
    this.initializeThemeConfig()
  }

  // Initialize theme configuration
  private initializeThemeConfig(): void {
    this.themeConfig = {
      light: {
        backgroundColor: '#ffffff',
        textColor: '#374151',
        gridColor: '#e5e7eb',
        borderColor: '#d1d5db',
        colors: [
          '#3b82f6', '#ef4444', '#10b981', '#f59e0b',
          '#8b5cf6', '#f97316', '#06b6d4', '#84cc16'
        ]
      },
      dark: {
        backgroundColor: '#1f2937',
        textColor: '#f9fafb',
        gridColor: '#374151',
        borderColor: '#4b5563',
        colors: [
          '#60a5fa', '#f87171', '#34d399', '#fbbf24',
          '#a78bfa', '#fb923c', '#22d3ee', '#a3e635'
        ]
      }
    }
  }

  // Generate chart with multiple chart types
  async createChart(
    containerId: string,
    chartType: 'line' | 'candlestick' | 'bar' | 'area' | 'scatter' | 'heatmap' | 'treemap',
    data: any[],
    customizations?: ChartCustomizationConfig,
    context?: UIContext
  ): Promise<any> {
    try {
      // Build chart configuration
      const config = await this.buildChartConfig(chartType, data, customizations, context)
      
      // Create chart instance
      const chart = await this.createChartInstance(containerId, config)
      
      // Store chart instance
      this.chartInstances.set(containerId, chart)
      
      // Set up real-time updates if configured
      if (config.realTimeConfig?.enabled) {
        this.setupRealTimeUpdates(containerId, chart, config.realTimeConfig)
      }
      
      // Set up data bindings if configured
      const bindings = this.dataBindings.get(containerId)
      if (bindings) {
        this.setupDataBindings(containerId, chart, bindings)
      }
      
      return chart
    } catch (error) {
      console.error(`Failed to create chart ${containerId}:`, error)
      throw error
    }
  }

  // Build chart configuration based on type and customizations
  private async buildChartConfig(
    chartType: 'line' | 'candlestick' | 'bar' | 'area' | 'scatter' | 'heatmap' | 'treemap',
    data: any[],
    customizations?: ChartCustomizationConfig,
    context?: UIContext
  ): Promise<ChartConfig> {
    const theme = customizations?.theme || context?.userPreferences?.theme || 'dark'
    const themeColors = this.themeConfig[theme]

    // Base configuration
    const baseConfig: ChartConfig = {
      type: chartType,
      data: this.processChartData(data, chartType),
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: {
          duration: 750,
          easing: 'easeInOutQuad',
          animateRotate: true,
          animateScale: true
        },
        scales: this.buildScaleConfig(chartType, themeColors),
        plugins: this.buildPluginConfig(chartType, themeColors, customizations),
        layout: {
          padding: 10
        },
        elements: this.buildElementConfig(themeColors)
      },
      interactions: this.buildInteractionConfig(chartType, customizations),
      realTimeConfig: this.buildRealTimeConfig(customizations)
    }

    // Apply chart-specific configurations
    switch (chartType) {
      case 'candlestick':
        this.applyCandlestickConfig(baseConfig, themeColors)
        break
      case 'heatmap':
        this.applyHeatmapConfig(baseConfig, themeColors)
        break
      case 'treemap':
        this.applyTreemapConfig(baseConfig, themeColors)
        break
      case 'scatter':
        this.applyScatterConfig(baseConfig, themeColors)
        break
    }

    // Apply customizations
    if (customizations) {
      this.applyCustomizations(baseConfig, customizations, themeColors)
    }

    return baseConfig
  }

  // Process chart data based on chart type
  private processChartData(data: any[], chartType: 'line' | 'candlestick' | 'bar' | 'area' | 'scatter' | 'heatmap' | 'treemap'): any {
    switch (chartType) {
      case 'line':
      case 'area':
        return this.processLineData(data)
      case 'bar':
        return this.processBarData(data)
      case 'candlestick':
        return this.processCandlestickData(data)
      case 'scatter':
        return this.processScatterData(data)
      case 'heatmap':
        return this.processHeatmapData(data)
      case 'treemap':
        return this.processTreemapData(data)
      default:
        return this.processLineData(data)
    }
  }

  // Process line chart data
  private processLineData(data: any[]): any {
    if (!Array.isArray(data) || data.length === 0) {
      return { labels: [], datasets: [] }
    }

    // Detect data structure
    const firstItem = data[0]
    
    if (typeof firstItem === 'object' && firstItem.x !== undefined && firstItem.y !== undefined) {
      // XY data format
      return {
        datasets: [{
          label: 'Data',
          data: data.map(item => ({ x: item.x, y: item.y })),
          borderColor: this.themeConfig.dark.colors[0],
          backgroundColor: this.themeConfig.dark.colors[0] + '20',
          tension: 0.4,
          fill: false
        }]
      }
    } else if (typeof firstItem === 'object' && firstItem.timestamp !== undefined) {
      // Time series data
      return {
        labels: data.map(item => new Date(item.timestamp)),
        datasets: [{
          label: 'Value',
          data: data.map(item => item.value || item.close || item.price),
          borderColor: this.themeConfig.dark.colors[0],
          backgroundColor: this.themeConfig.dark.colors[0] + '20',
          tension: 0.4,
          fill: false
        }]
      }
    } else {
      // Simple array data
      return {
        labels: data.map((_, index) => index),
        datasets: [{
          label: 'Data',
          data: data,
          borderColor: this.themeConfig.dark.colors[0],
          backgroundColor: this.themeConfig.dark.colors[0] + '20',
          tension: 0.4,
          fill: false
        }]
      }
    }
  }

  // Process bar chart data
  private processBarData(data: any[]): any {
    if (!Array.isArray(data) || data.length === 0) {
      return { labels: [], datasets: [] }
    }

    const firstItem = data[0]
    
    if (typeof firstItem === 'object' && firstItem.label !== undefined) {
      return {
        labels: data.map(item => item.label),
        datasets: [{
          label: 'Value',
          data: data.map(item => item.value),
          backgroundColor: this.themeConfig.dark.colors.slice(0, data.length),
          borderColor: this.themeConfig.dark.colors.slice(0, data.length),
          borderWidth: 1
        }]
      }
    } else {
      return {
        labels: data.map((_, index) => `Item ${index + 1}`),
        datasets: [{
          label: 'Data',
          data: data,
          backgroundColor: this.themeConfig.dark.colors[0],
          borderColor: this.themeConfig.dark.colors[0],
          borderWidth: 1
        }]
      }
    }
  }

  // Process candlestick data
  private processCandlestickData(data: any[]): any {
    if (!Array.isArray(data) || data.length === 0) {
      return { labels: [], datasets: [] }
    }

    return {
      labels: data.map(item => new Date(item.timestamp || item.time)),
      datasets: [{
        label: 'OHLC',
        data: data.map(item => ({
          x: new Date(item.timestamp || item.time),
          o: item.open,
          h: item.high,
          l: item.low,
          c: item.close
        })),
        borderColor: '#10b981',
        backgroundColor: '#ef4444'
      }]
    }
  }

  // Process scatter plot data
  private processScatterData(data: any[]): any {
    if (!Array.isArray(data) || data.length === 0) {
      return { datasets: [] }
    }

    return {
      datasets: [{
        label: 'Scatter Data',
        data: data.map(item => ({
          x: item.x || item.risk || Math.random(),
          y: item.y || item.return || Math.random()
        })),
        backgroundColor: this.themeConfig.dark.colors[0],
        borderColor: this.themeConfig.dark.colors[0],
        pointRadius: 5
      }]
    }
  }

  // Process heatmap data
  private processHeatmapData(data: any[]): any {
    // Heatmap data processing would depend on the specific heatmap library used
    return {
      data: data,
      colorScale: ['#ef4444', '#fbbf24', '#10b981']
    }
  }

  // Process treemap data
  private processTreemapData(data: any[]): any {
    return {
      datasets: [{
        label: 'Treemap',
        data: data.map(item => ({
          value: item.value || item.size,
          label: item.label || item.name
        })),
        backgroundColor: this.themeConfig.dark.colors
      }]
    }
  }

  // Build scale configuration
  private buildScaleConfig(chartType: 'line' | 'candlestick' | 'bar' | 'area' | 'scatter' | 'heatmap' | 'treemap', themeColors: any): ScaleConfig {
    const baseScale: AxisConfig = {
      type: 'linear',
      position: 'left',
      display: true,
      grid: {
        display: true,
        color: themeColors.gridColor,
        lineWidth: 1,
        drawBorder: true,
        drawOnChartArea: true,
        drawTicks: true
      },
      ticks: {
        display: true,
        color: themeColors.textColor,
        font: {
          family: 'Inter, sans-serif',
          size: 12,
          style: 'normal',
          weight: 'normal',
          lineHeight: 1.2
        },
        padding: 8
      },
      title: {
        display: false,
        text: '',
        color: themeColors.textColor,
        font: {
          family: 'Inter, sans-serif',
          size: 14,
          style: 'normal',
          weight: 'bold',
          lineHeight: 1.2
        },
        padding: 10
      }
    }

    const config: ScaleConfig = {
      x: { ...baseScale, position: 'bottom' },
      y: { ...baseScale, position: 'left' }
    }

    // Chart-specific scale configurations
    switch (chartType) {
      case 'candlestick':
        config.x.type = 'time'
        break
      case 'scatter':
        config.x.type = 'linear'
        config.y.type = 'linear'
        break
      case 'heatmap':
        config.x.type = 'category'
        config.y.type = 'category'
        break
    }

    return config
  }

  // Build plugin configuration
  private buildPluginConfig(
    chartType: 'line' | 'candlestick' | 'bar' | 'area' | 'scatter' | 'heatmap' | 'treemap', 
    themeColors: any, 
    customizations?: ChartCustomizationConfig
  ): PluginConfig {
    return {
      legend: {
        display: true,
        position: 'top',
        align: 'center',
        labels: {
          color: themeColors.textColor,
          font: {
            family: 'Inter, sans-serif',
            size: 12,
            style: 'normal',
            weight: 'normal',
            lineHeight: 1.2
          },
          padding: 20,
          usePointStyle: true,
          pointStyle: 'circle'
        }
      },
      tooltip: {
        enabled: true,
        mode: 'nearest',
        intersect: false,
        position: 'nearest',
        backgroundColor: themeColors.backgroundColor,
        titleColor: themeColors.textColor,
        titleFont: {
          family: 'Inter, sans-serif',
          size: 14,
          style: 'normal',
          weight: 'bold',
          lineHeight: 1.2
        },
        bodyColor: themeColors.textColor,
        bodyFont: {
          family: 'Inter, sans-serif',
          size: 12,
          style: 'normal',
          weight: 'normal',
          lineHeight: 1.2
        },
        borderColor: themeColors.borderColor,
        borderWidth: 1,
        displayColors: true,
        callbacks: this.buildTooltipCallbacks(chartType)
      },
      title: {
        display: false,
        text: '',
        color: themeColors.textColor,
        font: {
          family: 'Inter, sans-serif',
          size: 16,
          style: 'normal',
          weight: 'bold',
          lineHeight: 1.2
        },
        padding: 20
      },
      zoom: customizations?.zoom ? {
        enabled: true,
        mode: 'xy',
        speed: 0.1,
        threshold: 2,
        sensitivity: 3
      } : undefined,
      pan: customizations?.pan ? {
        enabled: true,
        mode: 'xy',
        speed: 20,
        threshold: 10
      } : undefined,
      crosshair: customizations?.crosshair ? {
        enabled: true,
        color: themeColors.textColor,
        width: 1,
        dash: [5, 5],
        sync: false
      } : undefined
    }
  }

  // Build tooltip callbacks
  private buildTooltipCallbacks(chartType: 'line' | 'candlestick' | 'bar' | 'area' | 'scatter' | 'heatmap' | 'treemap'): TooltipCallbacks {
    const callbacks: TooltipCallbacks = {}

    switch (chartType) {
      case 'candlestick':
        callbacks.label = (context: any) => {
          const data = context.raw
          return [
            `Open: ${data.o?.toFixed(2)}`,
            `High: ${data.h?.toFixed(2)}`,
            `Low: ${data.l?.toFixed(2)}`,
            `Close: ${data.c?.toFixed(2)}`
          ]
        }
        break
      case 'scatter':
        callbacks.label = (context: any) => {
          return `Risk: ${context.parsed.x?.toFixed(2)}, Return: ${context.parsed.y?.toFixed(2)}`
        }
        break
      default:
        callbacks.label = (context: any) => {
          return `${context.dataset.label}: ${context.parsed.y?.toFixed(2)}`
        }
    }

    return callbacks
  }

  // Build element configuration
  private buildElementConfig(themeColors: any): ElementConfig {
    return {
      point: {
        radius: 4,
        pointStyle: 'circle',
        backgroundColor: themeColors.colors[0],
        borderColor: themeColors.colors[0],
        borderWidth: 2,
        hitRadius: 10,
        hoverRadius: 6,
        hoverBorderWidth: 3
      },
      line: {
        tension: 0.4,
        backgroundColor: themeColors.colors[0] + '20',
        borderColor: themeColors.colors[0],
        borderWidth: 2,
        borderCapStyle: 'round',
        borderDash: [],
        borderDashOffset: 0,
        borderJoinStyle: 'round',
        capBezierPoints: true,
        cubicInterpolationMode: 'default',
        fill: false,
        stepped: false
      },
      bar: {
        backgroundColor: themeColors.colors[0],
        borderColor: themeColors.colors[0],
        borderWidth: 1,
        borderSkipped: 'start',
        borderRadius: 4,
        inflateAmount: 0
      },
      arc: {
        backgroundColor: themeColors.colors[0],
        borderColor: themeColors.backgroundColor,
        borderWidth: 2,
        borderAlign: 'center'
      }
    }
  }

  // Build interaction configuration
  private buildInteractionConfig(
    chartType: 'line' | 'candlestick' | 'bar' | 'area' | 'scatter' | 'heatmap' | 'treemap', 
    customizations?: ChartCustomizationConfig
  ): ChartInteraction[] {
    const interactions: ChartInteraction[] = []

    // Default click interaction
    interactions.push({
      type: 'click',
      enabled: true,
      handler: (event: any, elements: any[], chart: any) => {
        if (elements.length > 0) {
          const element = elements[0]
          console.log('Chart element clicked:', element)
          // Emit custom event for external handling
          this.emitChartEvent('elementClick', { element, chart })
        }
      }
    })

    // Default hover interaction
    interactions.push({
      type: 'hover',
      enabled: true,
      handler: (event: any, elements: any[], chart: any) => {
        if (elements.length > 0) {
          const element = elements[0]
          this.emitChartEvent('elementHover', { element, chart })
        }
      }
    })

    // Zoom interaction if enabled
    if (customizations?.zoom) {
      interactions.push({
        type: 'zoom',
        enabled: true,
        handler: (event: any, elements: any[], chart: any) => {
          this.emitChartEvent('chartZoom', { event, chart })
        }
      })
    }

    // Pan interaction if enabled
    if (customizations?.pan) {
      interactions.push({
        type: 'pan',
        enabled: true,
        handler: (event: any, elements: any[], chart: any) => {
          this.emitChartEvent('chartPan', { event, chart })
        }
      })
    }

    return interactions
  }

  // Build real-time configuration
  private buildRealTimeConfig(customizations?: ChartCustomizationConfig): RealTimeConfig | undefined {
    if (!customizations || !customizations.realtime) {
      return undefined
    }

    return {
      enabled: true,
      interval: 1000, // 1 second default
      maxDataPoints: 100,
      dataSource: 'websocket', // Would be configured based on actual data source
      onUpdate: (newData: any, chart: any) => {
        this.updateChartData(chart, newData)
      },
      onError: (error: Error) => {
        console.error('Real-time data update error:', error)
      }
    }
  }

  // Apply chart-specific configurations
  private applyCandlestickConfig(config: ChartConfig, themeColors: any): void {
    // Candlestick-specific configuration
    config.options.scales.x.type = 'time'
    // Note: time configuration would be added to the axis config in a real implementation
  }

  private applyHeatmapConfig(config: ChartConfig, themeColors: any): void {
    // Heatmap-specific configuration
    config.options.scales.x.type = 'category'
    config.options.scales.y.type = 'category'
    config.options.plugins.legend.display = false
  }

  private applyTreemapConfig(config: ChartConfig, themeColors: any): void {
    // Treemap-specific configuration
    config.options.plugins.legend.display = false
    // Note: Treemap would use a different scale configuration in a real implementation
  }

  private applyScatterConfig(config: ChartConfig, themeColors: any): void {
    // Scatter plot specific configuration
    config.options.scales.x.type = 'linear'
    config.options.scales.y.type = 'linear'
    config.options.elements.point.radius = 6
  }

  // Apply customizations to chart config
  private applyCustomizations(
    config: ChartConfig, 
    customizations: ChartCustomizationConfig, 
    themeColors: any
  ): void {
    // Apply colors
    if (customizations.colors) {
      const colors = customizations.colors
      if (config.data && Array.isArray(config.data.datasets)) {
        config.data.datasets.forEach((dataset: any, index: number) => {
          dataset.borderColor = colors[index % colors.length]
          dataset.backgroundColor = colors[index % colors.length] + '20'
        })
      }
    }

    // Apply annotations
    if (customizations.annotations) {
      config.options.plugins.annotation = {
        annotations: customizations.annotations.map(annotation => ({
          type: annotation.type === 'rectangle' ? 'box' : annotation.type as 'line' | 'point' | 'ellipse' | 'polygon' | 'box',
          mode: annotation.mode || 'horizontal',
          scaleID: annotation.scaleID || 'y',
          value: annotation.value,
          borderColor: annotation.borderColor || themeColors.colors[0],
          borderWidth: annotation.borderWidth || 2,
          label: annotation.label ? {
            enabled: true,
            content: annotation.label.content,
            position: annotation.label.position || 'center',
            backgroundColor: themeColors.backgroundColor,
            color: themeColors.textColor,
            font: {
              family: 'Inter, sans-serif',
              size: 12,
              style: 'normal',
              weight: 'normal',
              lineHeight: 1.2
            }
          } : undefined
        }))
      }
    }

    // Apply indicators
    if (customizations.indicators) {
      customizations.indicators.forEach((indicator, index) => {
        if (indicator.visible) {
          // Add indicator as additional dataset
          const indicatorData = this.calculateIndicator(indicator, config.data)
          if (indicatorData && config.data && Array.isArray(config.data.datasets)) {
            config.data.datasets.push({
              label: indicator.type.toUpperCase(),
              data: indicatorData,
              borderColor: themeColors.colors[(index + 1) % themeColors.colors.length],
              backgroundColor: 'transparent',
              borderWidth: 1,
              pointRadius: 0,
              yAxisID: indicator.type === 'rsi' ? 'y1' : 'y'
            })

            // Add secondary y-axis for oscillators
            if (indicator.type === 'rsi' || indicator.type === 'stochastic') {
              config.options.scales.y1 = {
                ...config.options.scales.y,
                position: 'right',
                min: 0,
                max: 100
              }
            }
          }
        }
      })
    }
  }

  // Calculate technical indicators (simplified implementation)
  private calculateIndicator(indicator: any, chartData: any): number[] | null {
    const data = chartData.datasets[0]?.data || []
    if (!Array.isArray(data) || data.length === 0) return null

    switch (indicator.type) {
      case 'sma':
        return this.calculateSMA(data, indicator.period)
      case 'ema':
        return this.calculateEMA(data, indicator.period)
      case 'rsi':
        return this.calculateRSI(data, indicator.period)
      case 'macd':
        return this.calculateMACD(data, indicator.parameters)
      default:
        return null
    }
  }

  // Simple Moving Average calculation
  private calculateSMA(data: any[], period: number): number[] {
    const sma: number[] = []
    for (let i = 0; i < data.length; i++) {
      if (i < period - 1) {
        sma.push(null as any)
      } else {
        const sum = data.slice(i - period + 1, i + 1)
          .reduce((acc: number, val: any) => acc + (val.y || val), 0)
        sma.push(sum / period)
      }
    }
    return sma
  }

  // Exponential Moving Average calculation
  private calculateEMA(data: any[], period: number): number[] {
    const ema: number[] = []
    const multiplier = 2 / (period + 1)
    
    for (let i = 0; i < data.length; i++) {
      const value = data[i].y || data[i]
      if (i === 0) {
        ema.push(value)
      } else {
        ema.push((value * multiplier) + (ema[i - 1] * (1 - multiplier)))
      }
    }
    return ema
  }

  // RSI calculation (simplified)
  private calculateRSI(data: any[], period: number): number[] {
    const rsi: number[] = []
    const gains: number[] = []
    const losses: number[] = []
    
    for (let i = 1; i < data.length; i++) {
      const current = data[i].y || data[i]
      const previous = data[i - 1].y || data[i - 1]
      const change = current - previous
      
      gains.push(change > 0 ? change : 0)
      losses.push(change < 0 ? Math.abs(change) : 0)
      
      if (i >= period) {
        const avgGain = gains.slice(-period).reduce((a, b) => a + b, 0) / period
        const avgLoss = losses.slice(-period).reduce((a, b) => a + b, 0) / period
        const rs = avgGain / avgLoss
        rsi.push(100 - (100 / (1 + rs)))
      } else {
        rsi.push(null as any)
      }
    }
    
    return [null as any, ...rsi] // Add null for first data point
  }

  // MACD calculation (simplified)
  private calculateMACD(data: any[], parameters: any): number[] {
    const fastPeriod = parameters.fast || 12
    const slowPeriod = parameters.slow || 26
    const signalPeriod = parameters.signal || 9
    
    const fastEMA = this.calculateEMA(data, fastPeriod)
    const slowEMA = this.calculateEMA(data, slowPeriod)
    
    const macdLine = fastEMA.map((fast, i) => fast - slowEMA[i])
    return macdLine
  }

  // Create chart instance (would integrate with actual charting library)
  private async createChartInstance(containerId: string, config: ChartConfig): Promise<any> {
    // This would integrate with Chart.js, D3.js, or another charting library
    // For now, return a mock chart instance
    return {
      id: containerId,
      config,
      update: (newData: any) => this.updateChartData(this, newData),
      destroy: () => this.destroyChart(containerId),
      resize: () => console.log(`Resizing chart ${containerId}`),
      render: () => console.log(`Rendering chart ${containerId}`)
    }
  }

  // Set up real-time data updates
  private setupRealTimeUpdates(
    chartId: string, 
    chart: any, 
    config: RealTimeConfig
  ): void {
    if (this.realTimeUpdaters.has(chartId)) {
      clearInterval(this.realTimeUpdaters.get(chartId))
    }

    const updater = setInterval(async () => {
      try {
        let newData: any
        
        if (typeof config.dataSource === 'function') {
          newData = await config.dataSource()
        } else {
          // Mock data for demonstration
          newData = {
            timestamp: Date.now(),
            value: Math.random() * 100
          }
        }

        if (config.onUpdate) {
          config.onUpdate(newData, chart)
        } else {
          this.updateChartData(chart, newData)
        }
      } catch (error) {
        if (config.onError) {
          config.onError(error as Error)
        } else {
          console.error('Real-time update error:', error)
        }
      }
    }, config.interval)

    this.realTimeUpdaters.set(chartId, updater)
  }

  // Set up data bindings
  private setupDataBindings(chartId: string, chart: any, bindings: DataBinding[]): void {
    // Implementation would depend on the specific data binding requirements
    console.log(`Setting up data bindings for chart ${chartId}:`, bindings)
  }

  // Update chart data
  private updateChartData(chart: any, newData: any): void {
    if (!chart || !chart.config) return

    const datasets = chart.config.data.datasets
    if (!datasets || datasets.length === 0) return

    // Add new data point
    if (Array.isArray(newData)) {
      // Multiple data points
      newData.forEach(point => {
        datasets[0].data.push(point)
      })
    } else {
      // Single data point
      datasets[0].data.push(newData)
    }

    // Remove old data points if exceeding max
    const maxPoints = chart.config.realTimeConfig?.maxDataPoints || 100
    if (datasets[0].data.length > maxPoints) {
      datasets[0].data.splice(0, datasets[0].data.length - maxPoints)
    }

    // Update chart (would call actual chart library update method)
    console.log(`Updating chart ${chart.id} with new data`)
  }

  // Emit chart events for external handling
  private emitChartEvent(eventType: string, data: any): void {
    const event = new CustomEvent(`chart:${eventType}`, { detail: data })
    window.dispatchEvent(event)
  }

  // Public methods for chart management
  getChart(chartId: string): any {
    return this.chartInstances.get(chartId)
  }

  updateChart(chartId: string, newData: any): void {
    const chart = this.chartInstances.get(chartId)
    if (chart) {
      this.updateChartData(chart, newData)
    }
  }

  destroyChart(chartId: string): void {
    const chart = this.chartInstances.get(chartId)
    if (chart) {
      // Clear real-time updater
      const updater = this.realTimeUpdaters.get(chartId)
      if (updater) {
        clearInterval(updater)
        this.realTimeUpdaters.delete(chartId)
      }

      // Remove chart instance
      this.chartInstances.delete(chartId)
      
      // Clear data bindings
      this.dataBindings.delete(chartId)
      
      console.log(`Chart ${chartId} destroyed`)
    }
  }

  resizeChart(chartId: string): void {
    const chart = this.chartInstances.get(chartId)
    if (chart && chart.resize) {
      chart.resize()
    }
  }

  // Set data binding for a chart
  setDataBinding(chartId: string, bindings: DataBinding[]): void {
    this.dataBindings.set(chartId, bindings)
    
    const chart = this.chartInstances.get(chartId)
    if (chart) {
      this.setupDataBindings(chartId, chart, bindings)
    }
  }

  // Get chart statistics
  getChartStats(): { activeCharts: number; realTimeCharts: number; totalDataPoints: number } {
    const activeCharts = this.chartInstances.size
    const realTimeCharts = this.realTimeUpdaters.size
    
    let totalDataPoints = 0
    this.chartInstances.forEach(chart => {
      if (chart.config?.data?.datasets) {
        chart.config.data.datasets.forEach((dataset: any) => {
          if (Array.isArray(dataset.data)) {
            totalDataPoints += dataset.data.length
          }
        })
      }
    })

    return { activeCharts, realTimeCharts, totalDataPoints }
  }

  // Clear all charts
  clearAllCharts(): void {
    const chartIds = Array.from(this.chartInstances.keys())
    chartIds.forEach(chartId => this.destroyChart(chartId))
  }
}

// Export singleton instance
export const interactiveVisualizationEngine = new InteractiveVisualizationEngine()