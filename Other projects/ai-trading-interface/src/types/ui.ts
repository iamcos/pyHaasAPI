// UI and User Experience Types
export interface UIContext {
  currentView: 'dashboard' | 'market-intelligence' | 'strategy-studio' | 'analytics' | 'risk-management' | 'workflow' | string
  selectedAssets: string[]
  activeStrategies: string[]
  userPreferences: UserPreferences
  marketConditions: MarketCondition[]
  riskTolerance: RiskTolerance
  persona: Persona
}

export interface UserPreferences {
  theme: 'light' | 'dark' | 'auto'
  language: string
  timezone: string
  currency: string
  notifications: NotificationSettings
  dashboard: DashboardSettings
  accessibility: AccessibilitySettings
}

export interface NotificationSettings {
  enabled: boolean
  types: NotificationType[]
  frequency: 'immediate' | 'batched' | 'daily'
  channels: NotificationChannel[]
}

export interface NotificationType {
  type: 'trade' | 'alert' | 'performance' | 'risk' | 'system'
  enabled: boolean
  priority: 'low' | 'medium' | 'high' | 'critical'
}

export interface NotificationChannel {
  type: 'in_app' | 'email' | 'push' | 'sound'
  enabled: boolean
  settings: any
}

export interface DashboardSettings {
  layout: 'grid' | 'list' | 'custom'
  widgets: WidgetConfig[]
  refreshInterval: number
  autoRefresh: boolean
}

export interface WidgetConfig {
  id: string
  type: string
  position: Position
  size: Size
  settings: any
  visible: boolean
}

export interface Position {
  x: number
  y: number
}

export interface Size {
  width: number
  height: number
}

export interface AccessibilitySettings {
  highContrast: boolean
  largeText: boolean
  screenReader: boolean
  keyboardNavigation: boolean
  voiceCommands: boolean
  reducedMotion: boolean
}

export interface RiskTolerance {
  level: 'conservative' | 'moderate' | 'aggressive' | 'high_risk'
  maxDrawdown: number
  maxPositionSize: number
  diversificationRequirement: number
  stopLossRequirement: boolean
}

// Command and Interaction Types
export interface CommandResult {
  type: 'ui_generation' | 'data_query' | 'workflow_trigger' | 'navigation'
  payload: any
  chainOfThought?: ChainOfThoughtStep[]
  proactiveActions?: ProactiveAction[]
  success: boolean
  message?: string
}

export interface Suggestion {
  id: string
  text: string
  type: 'command' | 'query' | 'action'
  confidence: number
  context: string
  icon?: string
}

export interface VoiceCommand {
  id: string
  transcript: string
  confidence: number
  intent: string
  entities: Entity[]
  timestamp: Date
}

export interface Entity {
  type: string
  value: string
  confidence: number
  start: number
  end: number
}

// Layout and Component Types
export interface Layout {
  id: string
  name: string
  components: LayoutComponent[]
  responsive: ResponsiveConfig
  theme: ThemeConfig
}

export interface LayoutComponent {
  id: string
  type: string
  props: any
  children?: LayoutComponent[]
  constraints: LayoutConstraints
}

export interface LayoutConstraints {
  minWidth?: number
  maxWidth?: number
  minHeight?: number
  maxHeight?: number
  aspectRatio?: number
}

export interface ResponsiveConfig {
  breakpoints: Breakpoint[]
  behavior: 'stack' | 'hide' | 'resize' | 'reorder'
}

export interface Breakpoint {
  name: string
  minWidth: number
  layout: LayoutComponent[]
}

export interface ThemeConfig {
  colors: ColorPalette
  typography: Typography
  spacing: Spacing
  animations: AnimationConfig
}

export interface ColorPalette {
  primary: ColorScale
  secondary: ColorScale
  success: ColorScale
  warning: ColorScale
  error: ColorScale
  neutral: ColorScale
}

export interface ColorScale {
  50: string
  100: string
  200: string
  300: string
  400: string
  500: string
  600: string
  700: string
  800: string
  900: string
}

export interface Typography {
  fontFamily: string
  fontSize: FontSizeScale
  fontWeight: FontWeightScale
  lineHeight: LineHeightScale
}

export interface FontSizeScale {
  xs: string
  sm: string
  base: string
  lg: string
  xl: string
  '2xl': string
  '3xl': string
  '4xl': string
}

export interface FontWeightScale {
  thin: number
  light: number
  normal: number
  medium: number
  semibold: number
  bold: number
  extrabold: number
}

export interface LineHeightScale {
  tight: number
  normal: number
  relaxed: number
  loose: number
}

export interface Spacing {
  scale: SpacingScale
  component: ComponentSpacing
}

export interface SpacingScale {
  0: string
  1: string
  2: string
  3: string
  4: string
  5: string
  6: string
  8: string
  10: string
  12: string
  16: string
  20: string
  24: string
  32: string
}

export interface ComponentSpacing {
  padding: SpacingScale
  margin: SpacingScale
  gap: SpacingScale
}

export interface AnimationConfig {
  duration: DurationScale
  easing: EasingScale
  transitions: TransitionConfig
}

export interface DurationScale {
  fast: string
  normal: string
  slow: string
}

export interface EasingScale {
  linear: string
  easeIn: string
  easeOut: string
  easeInOut: string
}

export interface TransitionConfig {
  default: string
  colors: string
  opacity: string
  transform: string
}

// Chart and Visualization Types
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
  realtime?: boolean
}

export interface ChartAnnotation {
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

export interface TechnicalIndicator {
  type: 'sma' | 'ema' | 'rsi' | 'macd' | 'bollinger' | 'stochastic'
  period: number
  parameters: Record<string, any>
  visible: boolean
}

// Import types from other files
import type { MarketCondition } from './trading'
import type { Persona, ChainOfThoughtStep, ProactiveAction } from './ai'