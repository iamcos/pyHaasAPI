import React, { useState, useEffect } from 'react'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import {
  Badge,
  Button,
  Progress,
  Tabs,
  TabsContent,
  TabsList,
  TabsTab,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
  Alert,
  AlertDescription,
} from '@/components/ui'
import {
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  CheckCircle,
  XCircle,
  BarChart3,
  PieChart,
  LineChart,
  DollarSign,
  Percent,
  Shield,
  Target,
  Activity,
  Users,
  Settings,
  Download,
  Play,
  Pause,
  RotateCcw
} from 'lucide-react'
import { Line, Pie, Bar } from 'react-chartjs-2'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  BarElement,
} from 'chart.js'

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  BarElement
)

interface BacktestMetrics {
  profit_multiplier: number
  final_wallet_balance: number
  final_report_profit_percent: number
  final_report_net_bot_profit: number
  final_report_min_margin: number
  final_report_max_margin: number
  margin_utilization_percent: number
  margin_safety_score: number
  max_drawdown: number
  max_drawdown_percent: number
  losing_positions_count: number
  win_rate: number
  sharpe_ratio: number
  sortino_ratio: number
  profit_factor: number
  calmar_ratio: number
  total_trades: number
  winning_trades: number
  losing_trades: number
  average_win: number
  average_loss: number
  largest_win: number
  largest_loss: number
  risk_reward_ratio: number
  equity_curve_stability: number
  consistency_score: number
  deployment_readiness_score: number
}

interface BacktestAnalysisReport {
  backtest_id: string
  script_name: string
  account_name: string
  market_tag: string
  execution_period: {
    start: string
    end: string
    duration_days: number
  }
  metrics: BacktestMetrics
  equity_curve: Array<{
    timestamp: string
    balance: number
    profit_loss: number
    drawdown: number
    trade_id?: string
  }>
  position_analysis: any
  risk_analysis: {
    risk_grade: string
    risk_factors: Record<string, string>
    risk_recommendations: string[]
    value_at_risk: Record<string, number>
    stress_test_scenarios: Record<string, number>
  }
  deployment_recommendation: {
    is_recommended: boolean
    confidence_level: number
    deployment_strategy: any
    risk_management: any
    account_allocation: any
    monitoring_requirements: any
  }
  chart_data: any
  performance_rank?: number
  style_classification?: string
}

interface BacktestAnalysisDashboardProps {
  backtestId?: string
  multipleBacktests?: string[]
  onDeployBot?: (backtestId: string, config: any) => void
}

export default function BacktestAnalysisDashboard({
  backtestId,
  multipleBacktests,
  onDeployBot
}: BacktestAnalysisDashboardProps) {
  const [analysisReport, setAnalysisReport] = useState<BacktestAnalysisReport | null>(null)
  const [comparisonData, setComparisonData] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState('overview')
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (backtestId) {
      loadSingleAnalysis(backtestId)
    } else if (multipleBacktests) {
      loadComparisonAnalysis(multipleBacktests)
    }
  }, [backtestId, multipleBacktests])

  const loadSingleAnalysis = async (id: string) => {
    setLoading(true)
    setError(null)
    try {
      // Call the comprehensive analyzer
      const response = await fetch('/api/analyze/backtest', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ backtest_id: id })
      })
      
      if (!response.ok) throw new Error('Analysis failed')
      
      const report = await response.json()
      setAnalysisReport(report)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Analysis failed')
    } finally {
      setLoading(false)
    }
  }

  const loadComparisonAnalysis = async (ids: string[]) => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetch('/api/analyze/backtests/compare', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ backtest_ids: ids })
      })
      
      if (!response.ok) throw new Error('Comparison analysis failed')
      
      const comparison = await response.json()
      setComparisonData(comparison)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Comparison failed')
    } finally {
      setLoading(false)
    }
  }

  const handleDeploy = async (report: BacktestAnalysisReport) => {
    if (onDeployBot && report.deployment_recommendation.is_recommended) {
      const deployConfig = {
        backtestId: report.backtest_id,
        scriptName: report.script_name,
        accountAllocation: report.deployment_recommendation.account_allocation,
        riskManagement: report.deployment_recommendation.risk_management,
        deploymentStrategy: report.deployment_recommendation.deployment_strategy
      }
      
      await onDeployBot(report.backtest_id, deployConfig)
    }
  }

  const exportReport = async (report: BacktestAnalysisReport) => {
    try {
      const response = await fetch('/api/analyze/export', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          backtest_id: report.backtest_id,
          format: 'json'
        })
      })
      
      if (response.ok) {
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `backtest_analysis_${report.backtest_id}.json`
        a.click()
        window.URL.revokeObjectURL(url)
      }
    } catch (err) {
      console.error('Export failed:', err)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-2">Analyzing backtest data...</span>
      </div>
    )
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertTriangle className="h-4 w-4" />
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    )
  }

  if (comparisonData) {
    return <ComparisonAnalysisView data={comparisonData} onDeployBot={onDeployBot} />
  }

  if (!analysisReport) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="text-center text-gray-500">
            No backtest selected for analysis
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header with key metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <MetricCard
          title="PROFIT MULTIPLIER"
          value={analysisReport.metrics.profit_multiplier.toFixed(3)}
          icon={<TrendingUp className="h-4 w-4" />}
          color={analysisReport.metrics.profit_multiplier > 1 ? "green" : "red"}
        />
        <MetricCard
          title="FINAL WALLET BALANCE"
          value={`$${analysisReport.metrics.final_wallet_balance.toLocaleString()}`}
          icon={<DollarSign className="h-4 w-4" />}
          color="blue"
        />
        <MetricCard
          title="FINAL REPORT PROFIT %"
          value={`${analysisReport.metrics.final_report_profit_percent.toFixed(2)}%`}
          icon={<Percent className="h-4 w-4" />}
          color={analysisReport.metrics.final_report_profit_percent > 0 ? "green" : "red"}
        />
        <MetricCard
          title="MAX DRAWDOWN"
          value={`${analysisReport.metrics.max_drawdown_percent.toFixed(2)}%`}
          icon={<TrendingDown className="h-4 w-4" />}
          color="orange"
        />
      </div>

      {/* Deployment Readiness Score */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Target className="h-5 w-5" />
            Deployment Readiness
          </CardTitle>
          <CardDescription>
            Overall assessment for live trading deployment
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center gap-4">
              <div className="flex-1">
                <Progress 
                  value={analysisReport.metrics.deployment_readiness_score} 
                  className="h-3"
                />
              </div>
              <Badge 
                variant={analysisReport.deployment_recommendation.is_recommended ? "default" : "destructive"}
              >
                {analysisReport.metrics.deployment_readiness_score.toFixed(0)}%
              </Badge>
            </div>
            
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                {analysisReport.deployment_recommendation.is_recommended ? (
                  <CheckCircle className="h-5 w-5 text-green-500" />
                ) : (
                  <XCircle className="h-5 w-5 text-red-500" />
                )}
                <span className="font-medium">
                  {analysisReport.deployment_recommendation.is_recommended 
                    ? 'Recommended for Deployment' 
                    : 'Not Ready for Deployment'}
                </span>
              </div>
              
              {analysisReport.deployment_recommendation.is_recommended && (
                <Button 
                  onClick={() => handleDeploy(analysisReport)}
                  className="flex items-center gap-2"
                >
                  <Play className="h-4 w-4" />
                  Deploy Live Bot
                </Button>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Detailed Analysis Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-6">
          <TabsTab value="overview">Overview</TabsTab>
          <TabsTab value="performance">Performance</TabsTab>
          <TabsTab value="risk">Risk Analysis</TabsTab>
          <TabsTab value="positions">Positions</TabsTab>
          <TabsTab value="deployment">Deployment</TabsTab>
          <TabsTab value="charts">Charts</TabsTab>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <OverviewTab report={analysisReport} />
        </TabsContent>

        <TabsContent value="performance" className="space-y-4">
          <PerformanceTab report={analysisReport} />
        </TabsContent>

        <TabsContent value="risk" className="space-y-4">
          <RiskAnalysisTab report={analysisReport} />
        </TabsContent>

        <TabsContent value="positions" className="space-y-4">
          <PositionsTab report={analysisReport} />
        </TabsContent>

        <TabsContent value="deployment" className="space-y-4">
          <DeploymentTab report={analysisReport} onDeploy={() => handleDeploy(analysisReport)} />
        </TabsContent>

        <TabsContent value="charts" className="space-y-4">
          <ChartsTab report={analysisReport} />
        </TabsContent>
      </Tabs>

      {/* Export Button */}
      <div className="flex justify-end">
        <Button 
          variant="outline" 
          onClick={() => exportReport(analysisReport)}
          className="flex items-center gap-2"
        >
          <Download className="h-4 w-4" />
          Export Report
        </Button>
      </div>
    </div>
  )
}

// Component for metric cards
function MetricCard({ title, value, icon, color }: {
  title: string
  value: string
  icon: React.ReactNode
  color: string
}) {
  const colorClasses = {
    green: "text-green-600 bg-green-50 border-green-200",
    red: "text-red-600 bg-red-50 border-red-200",
    blue: "text-blue-600 bg-blue-50 border-blue-200",
    orange: "text-orange-600 bg-orange-50 border-orange-200"
  }

  return (
    <Card className={`${colorClasses[color as keyof typeof colorClasses]} border-2`}>
      <CardContent className="p-4">
        <div className="flex items-center gap-2 mb-2">
          {icon}
          <span className="text-sm font-medium">{title}</span>
        </div>
        <div className="text-2xl font-bold">{value}</div>
      </CardContent>
    </Card>
  )
}

// Overview Tab Component
function OverviewTab({ report }: { report: BacktestAnalysisReport }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      <Card>
        <CardHeader>
          <CardTitle>Strategy Information</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex justify-between">
            <span className="text-gray-600">Script Name:</span>
            <span className="font-medium">{report.script_name}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">Market:</span>
            <span className="font-medium">{report.market_tag}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">Duration:</span>
            <span className="font-medium">{report.execution_period.duration_days} days</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">Total Trades:</span>
            <span className="font-medium">{report.metrics.total_trades}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">Win Rate:</span>
            <span className="font-medium">{(report.metrics.win_rate * 100).toFixed(1)}%</span>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Key Performance Metrics</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex justify-between">
            <span className="text-gray-600">NET BOT PROFIT:</span>
            <span className={`font-medium ${report.metrics.final_report_net_bot_profit >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              ${report.metrics.final_report_net_bot_profit.toFixed(2)}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">MIN MARGIN:</span>
            <span className="font-medium">{report.metrics.final_report_min_margin.toFixed(2)}%</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">MAX MARGIN:</span>
            <span className="font-medium">{report.metrics.final_report_max_margin.toFixed(2)}%</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">LOSING POSITIONS:</span>
            <span className="font-medium">{report.metrics.losing_positions_count}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">SHARPE RATIO:</span>
            <span className="font-medium">{report.metrics.sharpe_ratio.toFixed(3)}</span>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

// Performance Tab Component
function PerformanceTab({ report }: { report: BacktestAnalysisReport }) {
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Performance Ratios</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold">{report.metrics.profit_factor.toFixed(2)}</div>
              <div className="text-sm text-gray-600">Profit Factor</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold">{report.metrics.sharpe_ratio.toFixed(2)}</div>
              <div className="text-sm text-gray-600">Sharpe Ratio</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold">{report.metrics.sortino_ratio.toFixed(2)}</div>
              <div className="text-sm text-gray-600">Sortino Ratio</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold">{report.metrics.calmar_ratio.toFixed(2)}</div>
              <div className="text-sm text-gray-600">Calmar Ratio</div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Trade Analysis</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            <div>
              <div className="text-lg font-semibold">${report.metrics.average_win.toFixed(2)}</div>
              <div className="text-sm text-gray-600">Average Win</div>
            </div>
            <div>
              <div className="text-lg font-semibold">${Math.abs(report.metrics.average_loss).toFixed(2)}</div>
              <div className="text-sm text-gray-600">Average Loss</div>
            </div>
            <div>
              <div className="text-lg font-semibold">${report.metrics.largest_win.toFixed(2)}</div>
              <div className="text-sm text-gray-600">Largest Win</div>
            </div>
            <div>
              <div className="text-lg font-semibold">${Math.abs(report.metrics.largest_loss).toFixed(2)}</div>
              <div className="text-sm text-gray-600">Largest Loss</div>
            </div>
            <div>
              <div className="text-lg font-semibold">{report.metrics.risk_reward_ratio.toFixed(2)}</div>
              <div className="text-sm text-gray-600">Risk/Reward</div>
            </div>
            <div>
              <div className="text-lg font-semibold">{report.metrics.consistency_score.toFixed(1)}%</div>
              <div className="text-sm text-gray-600">Consistency</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

// Risk Analysis Tab Component
function RiskAnalysisTab({ report }: { report: BacktestAnalysisReport }) {
  const risk = report.risk_analysis

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5" />
            Risk Assessment
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4 mb-4">
            <div className="text-3xl font-bold">{risk.risk_grade}</div>
            <div>
              <div className="font-medium">Risk Grade</div>
              <div className="text-sm text-gray-600">Overall risk assessment</div>
            </div>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {Object.entries(risk.risk_factors).map(([factor, level]) => (
              <div key={factor} className="text-center">
                <Badge 
                  variant={level === 'LOW' ? 'default' : level === 'MEDIUM' ? 'secondary' : 'destructive'}
                >
                  {level}
                </Badge>
                <div className="text-xs mt-1 capitalize">{factor.replace('_', ' ')}</div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Risk Recommendations</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {risk.risk_recommendations.map((rec, index) => (
              <Alert key={index}>
                <AlertDescription>{rec}</AlertDescription>
              </Alert>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Value at Risk (VaR)</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center">
              <div className="text-xl font-bold">${risk.value_at_risk.daily_var_95?.toFixed(2) || 'N/A'}</div>
              <div className="text-sm text-gray-600">Daily VaR (95%)</div>
            </div>
            <div className="text-center">
              <div className="text-xl font-bold">${risk.value_at_risk.weekly_var_95?.toFixed(2) || 'N/A'}</div>
              <div className="text-sm text-gray-600">Weekly VaR (95%)</div>
            </div>
            <div className="text-center">
              <div className="text-xl font-bold">${risk.value_at_risk.monthly_var_95?.toFixed(2) || 'N/A'}</div>
              <div className="text-sm text-gray-600">Monthly VaR (95%)</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

// Positions Tab Component
function PositionsTab({ report }: { report: BacktestAnalysisReport }) {
  const positions = report.position_analysis

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Position Summary</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold">{positions.total_positions}</div>
              <div className="text-sm text-gray-600">Total Positions</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">{positions.winning_positions}</div>
              <div className="text-sm text-gray-600">Winning</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-red-600">{positions.losing_positions}</div>
              <div className="text-sm text-gray-600">Losing</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold">
                {positions.duration_analysis.average_duration_hours.toFixed(1)}h
              </div>
              <div className="text-sm text-gray-600">Avg Duration</div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Position Breakdown</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Direction</TableHead>
                <TableHead>Wins</TableHead>
                <TableHead>Losses</TableHead>
                <TableHead>Win Rate</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              <TableRow>
                <TableCell>Long</TableCell>
                <TableCell className="text-green-600">{positions.position_breakdown.long_wins}</TableCell>
                <TableCell className="text-red-600">{positions.position_breakdown.long_losses}</TableCell>
                <TableCell>
                  {((positions.position_breakdown.long_wins / (positions.position_breakdown.long_wins + positions.position_breakdown.long_losses)) * 100).toFixed(1)}%
                </TableCell>
              </TableRow>
              <TableRow>
                <TableCell>Short</TableCell>
                <TableCell className="text-green-600">{positions.position_breakdown.short_wins}</TableCell>
                <TableCell className="text-red-600">{positions.position_breakdown.short_losses}</TableCell>
                <TableCell>
                  {((positions.position_breakdown.short_wins / (positions.position_breakdown.short_wins + positions.position_breakdown.short_losses)) * 100).toFixed(1)}%
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  )
}

// Deployment Tab Component
function DeploymentTab({ report, onDeploy }: { 
  report: BacktestAnalysisReport
  onDeploy: () => void 
}) {
  const deployment = report.deployment_recommendation

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            {deployment.is_recommended ? (
              <CheckCircle className="h-5 w-5 text-green-500" />
            ) : (
              <XCircle className="h-5 w-5 text-red-500" />
            )}
            Deployment Status
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span>Confidence Level:</span>
              <Badge variant={deployment.confidence_level >= 70 ? "default" : "destructive"}>
                {deployment.confidence_level.toFixed(0)}%
              </Badge>
            </div>

            {deployment.deployment_strategy && (
              <div>
                <h4 className="font-medium mb-2">Deployment Strategy</h4>
                <div className="bg-gray-50 p-3 rounded text-sm">
                  <p><strong>Approach:</strong> {deployment.deployment_strategy.approach}</p>
                  <p><strong>Initial Capital:</strong> {deployment.deployment_strategy.initial_capital_percent}%</p>
                  <p><strong>Description:</strong> {deployment.deployment_strategy.description}</p>
                </div>
              </div>
            )}

            {deployment.account_allocation && (
              <div>
                <h4 className="font-medium mb-2">Account Allocation</h4>
                <div className="bg-blue-50 p-3 rounded text-sm">
                  <p><strong>Account ID:</strong> {deployment.account_allocation.assigned_account_id}</p>
                  <p><strong>Initial Balance:</strong> ${deployment.account_allocation.initial_balance?.toLocaleString()}</p>
                  <p><strong>Status:</strong> {deployment.account_allocation.deployment_status}</p>
                </div>
              </div>
            )}

            {deployment.risk_management && (
              <div>
                <h4 className="font-medium mb-2">Risk Management</h4>
                <div className="bg-orange-50 p-3 rounded text-sm space-y-1">
                  <p><strong>Stop Loss:</strong> {deployment.risk_management.suggested_stop_loss_percent}%</p>
                  <p><strong>Max Position Size:</strong> {deployment.risk_management.max_position_size_percent}%</p>
                  <p><strong>Daily Loss Limit:</strong> {deployment.risk_management.daily_loss_limit_percent}%</p>
                  <p><strong>Monthly Loss Limit:</strong> {deployment.risk_management.monthly_loss_limit_percent}%</p>
                </div>
              </div>
            )}

            {deployment.is_recommended && (
              <Button 
                onClick={onDeploy}
                className="w-full flex items-center gap-2"
                size="lg"
              >
                <Play className="h-5 w-5" />
                Deploy Live Trading Bot
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {deployment.monitoring_requirements && (
        <Card>
          <CardHeader>
            <CardTitle>Monitoring Requirements</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span>Monitoring Frequency:</span>
                <Badge>{deployment.monitoring_requirements.monitoring_frequency}</Badge>
              </div>
              
              <div>
                <h5 className="font-medium mb-2">Key Metrics to Watch:</h5>
                <div className="flex flex-wrap gap-2">
                  {deployment.monitoring_requirements.key_metrics_to_watch?.map((metric: string, index: number) => (
                    <Badge key={index} variant="outline">{metric.replace('_', ' ')}</Badge>
                  ))}
                </div>
              </div>

              <div>
                <h5 className="font-medium mb-2">Alert Thresholds:</h5>
                <div className="text-sm space-y-1">
                  {Object.entries(deployment.monitoring_requirements.alert_thresholds || {}).map(([key, value]) => (
                    <div key={key} className="flex justify-between">
                      <span className="capitalize">{key.replace('_', ' ')}:</span>
                      <span>{typeof value === 'number' ? value.toFixed(1) : value}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

// Charts Tab Component
function ChartsTab({ report }: { report: BacktestAnalysisReport }) {
  // Prepare equity curve chart
  const equityChartData = {
    labels: report.equity_curve.map(point => 
      new Date(point.timestamp).toLocaleDateString()
    ),
    datasets: [
      {
        label: 'Account Balance',
        data: report.equity_curve.map(point => point.balance),
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        tension: 0.1,
        fill: true
      },
      {
        label: 'Drawdown %',
        data: report.equity_curve.map(point => -point.drawdown),
        borderColor: 'rgb(239, 68, 68)',
        backgroundColor: 'rgba(239, 68, 68, 0.1)',
        tension: 0.1,
        yAxisID: 'y1'
      }
    ]
  }

  // Win/Loss ratio pie chart
  const winLossData = {
    labels: ['Winning Trades', 'Losing Trades'],
    datasets: [{
      data: [report.metrics.winning_trades, report.metrics.losing_trades],
      backgroundColor: ['rgba(34, 197, 94, 0.8)', 'rgba(239, 68, 68, 0.8)'],
      borderColor: ['rgba(34, 197, 94, 1)', 'rgba(239, 68, 68, 1)'],
      borderWidth: 2
    }]
  }

  const chartOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top' as const,
      },
    },
    scales: {
      y: {
        beginAtZero: false,
      },
      y1: {
        type: 'linear' as const,
        display: true,
        position: 'right' as const,
        grid: {
          drawOnChartArea: false,
        },
      },
    },
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <LineChart className="h-5 w-5" />
            Equity Curve & Drawdown
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-80">
            <Line data={equityChartData} options={chartOptions} />
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <PieChart className="h-5 w-5" />
              Win/Loss Ratio
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <Pie data={winLossData} options={{ responsive: true, maintainAspectRatio: false }} />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Trade Summary</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="text-center">
              <div className="text-3xl font-bold">{report.metrics.total_trades}</div>
              <div className="text-gray-600">Total Trades</div>
            </div>
            <div className="grid grid-cols-2 gap-4 text-center">
              <div>
                <div className="text-xl font-bold text-green-600">{report.metrics.winning_trades}</div>
                <div className="text-sm text-gray-600">Winners</div>
              </div>
              <div>
                <div className="text-xl font-bold text-red-600">{report.metrics.losing_trades}</div>
                <div className="text-sm text-gray-600">Losers</div>
              </div>
            </div>
            <div className="text-center">
              <div className="text-xl font-bold">{(report.metrics.win_rate * 100).toFixed(1)}%</div>
              <div className="text-gray-600">Win Rate</div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

// Comparison Analysis Component
function ComparisonAnalysisView({ data, onDeployBot }: { 
  data: any
  onDeployBot?: (backtestId: string, config: any) => void 
}) {
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Backtest Comparison Summary</CardTitle>
          <CardDescription>
            Analysis of {data.comparison_summary.total_analyzed} backtests
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold">{data.comparison_summary.total_analyzed}</div>
              <div className="text-sm text-gray-600">Total Analyzed</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">{data.comparison_summary.deployment_ready_count}</div>
              <div className="text-sm text-gray-600">Deployment Ready</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold">{data.comparison_summary.average_metrics.avg_profit_percent.toFixed(1)}%</div>
              <div className="text-sm text-gray-600">Avg Profit %</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold">{data.comparison_summary.average_metrics.avg_deployment_score.toFixed(0)}%</div>
              <div className="text-sm text-gray-600">Avg Readiness</div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Top Performers - Ready for Deployment</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Rank</TableHead>
                <TableHead>Strategy</TableHead>
                <TableHead>Profit %</TableHead>
                <TableHead>Max Drawdown</TableHead>
                <TableHead>Win Rate</TableHead>
                <TableHead>Readiness Score</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.comparison_summary.recommended_for_deployment.map((strategy: any, index: number) => (
                <TableRow key={strategy.backtest_id}>
                  <TableCell>#{index + 1}</TableCell>
                  <TableCell className="font-medium">{strategy.script_name}</TableCell>
                  <TableCell className={strategy.profit_percent >= 0 ? 'text-green-600' : 'text-red-600'}>
                    {strategy.profit_percent.toFixed(2)}%
                  </TableCell>
                  <TableCell>{strategy.max_drawdown.toFixed(2)}%</TableCell>
                  <TableCell>{strategy.win_rate.toFixed(1)}%</TableCell>
                  <TableCell>
                    <Badge variant={strategy.score >= 85 ? 'default' : 'secondary'}>
                      {strategy.score.toFixed(0)}%
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Button
                      size="sm"
                      onClick={() => onDeployBot?.(strategy.backtest_id, {})}
                      className="flex items-center gap-1"
                    >
                      <Play className="h-3 w-3" />
                      Deploy
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {data.deployment_recommendations && (
        <Card>
          <CardHeader>
            <CardTitle>Deployment Recommendations</CardTitle>
          </CardHeader>
          <CardContent>
            <Alert>
              <AlertDescription>
                <strong>{data.deployment_recommendations.recommendation}:</strong>
                {data.deployment_recommendations.deployment_phases && (
                  <div className="mt-2 space-y-2">
                    {data.deployment_recommendations.deployment_phases.map((phase: any, index: number) => (
                      <div key={index} className="border-l-4 border-blue-500 pl-4">
                        <div className="font-medium">Phase {phase.phase}: {phase.description}</div>
                        <div className="text-sm text-gray-600">
                          {phase.strategies} strategies • {phase.capital_allocation} capital allocation
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </AlertDescription>
            </Alert>
          </CardContent>
        </Card>
      )}
    </div>
  )
}