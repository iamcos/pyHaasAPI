import { batchWorkflowManager } from './batchWorkflowManager'

export class BatchMonitoringService {
  private monitoringInterval: number = 10000 // 10 seconds
  private activeMonitors = new Map<string, NodeJS.Timeout>()
  private metricsHistory = new Map<string, BatchMetricsHistory>()
  private alertThresholds: AlertThresholds = {
    failureRate: 0.2, // 20%
    resourceUtilization: 0.9, // 90%
    avgDuration: 1800000, // 30 minutes
    queueLength: 50
  }

  /**
   * Start monitoring a batch execution
   */
  startMonitoring(batchId: string): void {
    if (this.activeMonitors.has(batchId)) {
      this.stopMonitoring(batchId)
    }

    const interval = setInterval(() => {
      this.collectBatchMetrics(batchId)
    }, this.monitoringInterval)

    this.activeMonitors.set(batchId, interval)
    this.initializeMetricsHistory(batchId)
  }

  /**
   * Stop monitoring a batch execution
   */
  stopMonitoring(batchId: string): void {
    const interval = this.activeMonitors.get(batchId)
    if (interval) {
      clearInterval(interval)
      this.activeMonitors.delete(batchId)
    }
  }

  /**
   * Get real-time batch metrics
   */
  getBatchMetrics(batchId: string): BatchMetrics | null {
    const batch = batchWorkflowManager.getBatchExecution(batchId)
    if (!batch) return null

    return this.calculateBatchMetrics(batch)
  }

  /**
   * Get batch metrics history
   */
  getBatchMetricsHistory(batchId: string): BatchMetricsHistory | null {
    return this.metricsHistory.get(batchId) || null
  }

  /**
   * Generate batch report
   */
  generateBatchReport(batchId: string): BatchReport | null {
    const batch = batchWorkflowManager.getBatchExecution(batchId)
    const metricsHistory = this.metricsHistory.get(batchId)
    
    if (!batch) return null

    const currentMetrics = this.calculateBatchMetrics(batch)
    const summary = this.generateBatchSummary(batch, currentMetrics)
    const performance = this.analyzePerformance(batch, metricsHistory)
    const recommendations = this.generateRecommendations(batch, currentMetrics, performance)

    return {
      batchId,
      generatedAt: new Date(),
      summary,
      performance,
      metrics: currentMetrics,
      workflows: this.generateWorkflowReports(batch),
      resourceUsage: this.analyzeResourceUsage(batch, metricsHistory),
      alerts: this.generateAlerts(batch, currentMetrics),
      recommendations
    }
  }

  /**
   * Get system-wide batch statistics
   */
  getSystemBatchStats(): SystemBatchStats {
    const activeBatches = batchWorkflowManager.getActiveBatches()
    
    const totalBatches = activeBatches.length
    const runningBatches = activeBatches.filter(b => b.status === 'running').length
    const completedBatches = activeBatches.filter(b => b.status === 'completed').length
    const failedBatches = activeBatches.filter(b => b.status === 'failed').length

    const totalWorkflows = activeBatches.reduce((sum, batch) => sum + batch.totalWorkflows, 0)
    const completedWorkflows = activeBatches.reduce((sum, batch) => sum + batch.completedWorkflows, 0)
    const failedWorkflows = activeBatches.reduce((sum, batch) => sum + batch.failedWorkflows, 0)

    const avgBatchDuration = this.calculateAverageBatchDuration(activeBatches)
    const systemResourceUtilization = this.calculateSystemResourceUtilization(activeBatches)

    return {
      totalBatches,
      runningBatches,
      completedBatches,
      failedBatches,
      totalWorkflows,
      completedWorkflows,
      failedWorkflows,
      avgBatchDuration,
      systemResourceUtilization,
      lastUpdate: new Date()
    }
  }

  /**
   * Collect and store batch metrics
   */
  private collectBatchMetrics(batchId: string): void {
    const batch = batchWorkflowManager.getBatchExecution(batchId)
    if (!batch) {
      this.stopMonitoring(batchId)
      return
    }

    const metrics = this.calculateBatchMetrics(batch)
    const history = this.metricsHistory.get(batchId)
    
    if (history) {
      history.dataPoints.push({
        timestamp: new Date(),
        metrics
      })

      // Keep only recent history (last 1000 points)
      if (history.dataPoints.length > 1000) {
        history.dataPoints = history.dataPoints.slice(-1000)
      }

      // Update aggregated metrics
      this.updateAggregatedMetrics(history, metrics)
    }

    // Check for alerts
    this.checkAlerts(batchId, metrics)

    // Auto-stop monitoring for completed batches
    if (batch.status === 'completed' || batch.status === 'failed' || batch.status === 'cancelled') {
      setTimeout(() => this.stopMonitoring(batchId), 60000) // Stop after 1 minute
    }
  }

  /**
   * Calculate comprehensive batch metrics
   */
  private calculateBatchMetrics(batch: any): BatchMetrics {
    const runningWorkflows = batch.workflows.filter((w: any) => w.status === 'running')
    const completedWorkflows = batch.workflows.filter((w: any) => w.status === 'completed')
    const failedWorkflows = batch.workflows.filter((w: any) => w.status === 'failed')

    // Calculate durations
    const workflowDurations = completedWorkflows
      .filter((w: any) => w.startTime && w.endTime)
      .map((w: any) => w.endTime.getTime() - w.startTime.getTime())

    const avgWorkflowDuration = workflowDurations.length > 0
      ? workflowDurations.reduce((sum, duration) => sum + duration, 0) / workflowDurations.length
      : 0

    const minWorkflowDuration = workflowDurations.length > 0 ? Math.min(...workflowDurations) : 0
    const maxWorkflowDuration = workflowDurations.length > 0 ? Math.max(...workflowDurations) : 0

    // Calculate throughput
    const batchDuration = batch.startTime ? Date.now() - batch.startTime.getTime() : 0
    const throughput = batchDuration > 0 ? (completedWorkflows.length / (batchDuration / 3600000)) : 0 // workflows per hour

    // Calculate failure rate
    const totalProcessed = completedWorkflows.length + failedWorkflows.length
    const failureRate = totalProcessed > 0 ? failedWorkflows.length / totalProcessed : 0

    // Calculate efficiency
    const estimatedTotalDuration = batch.workflows.reduce((sum: number, w: any) => sum + w.estimatedDuration, 0)
    const actualTotalDuration = workflowDurations.reduce((sum, duration) => sum + duration, 0)
    const efficiency = estimatedTotalDuration > 0 ? estimatedTotalDuration / actualTotalDuration : 1

    // Calculate resource metrics
    const progress = batchWorkflowManager.getBatchProgress(batch.id)
    const resourceUtilization = progress?.resourceUtilization || {
      cpu: 0, memory: 0, network: 0, storage: 0, overall: 0
    }

    return {
      batchId: batch.id,
      timestamp: new Date(),
      progress: batch.progress,
      throughput,
      failureRate,
      efficiency,
      avgWorkflowDuration,
      minWorkflowDuration,
      maxWorkflowDuration,
      resourceUtilization,
      queueLength: batch.workflows.filter((w: any) => w.status === 'pending').length,
      activeWorkflows: runningWorkflows.length,
      completedWorkflows: completedWorkflows.length,
      failedWorkflows: failedWorkflows.length,
      totalWorkflows: batch.totalWorkflows,
      estimatedTimeRemaining: progress?.estimatedTimeRemaining || 0
    }
  }

  /**
   * Initialize metrics history for a batch
   */
  private initializeMetricsHistory(batchId: string): void {
    this.metricsHistory.set(batchId, {
      batchId,
      startTime: new Date(),
      dataPoints: [],
      aggregatedMetrics: {
        avgThroughput: 0,
        avgFailureRate: 0,
        avgEfficiency: 0,
        avgResourceUtilization: 0,
        peakResourceUtilization: 0,
        totalDataPoints: 0
      }
    })
  }

  /**
   * Update aggregated metrics
   */
  private updateAggregatedMetrics(history: BatchMetricsHistory, metrics: BatchMetrics): void {
    const agg = history.aggregatedMetrics
    const n = agg.totalDataPoints
    
    // Update running averages
    agg.avgThroughput = (agg.avgThroughput * n + metrics.throughput) / (n + 1)
    agg.avgFailureRate = (agg.avgFailureRate * n + metrics.failureRate) / (n + 1)
    agg.avgEfficiency = (agg.avgEfficiency * n + metrics.efficiency) / (n + 1)
    agg.avgResourceUtilization = (agg.avgResourceUtilization * n + metrics.resourceUtilization.overall) / (n + 1)
    
    // Update peak values
    agg.peakResourceUtilization = Math.max(agg.peakResourceUtilization, metrics.resourceUtilization.overall)
    
    agg.totalDataPoints = n + 1
  }

  /**
   * Generate batch summary
   */
  private generateBatchSummary(batch: any, metrics: BatchMetrics): BatchSummary {
    const duration = batch.endTime 
      ? batch.endTime.getTime() - batch.startTime.getTime()
      : Date.now() - batch.startTime.getTime()

    return {
      name: batch.name,
      status: batch.status,
      startTime: batch.startTime,
      endTime: batch.endTime,
      duration,
      totalWorkflows: batch.totalWorkflows,
      completedWorkflows: batch.completedWorkflows,
      failedWorkflows: batch.failedWorkflows,
      successRate: batch.totalWorkflows > 0 ? batch.completedWorkflows / batch.totalWorkflows : 0,
      avgWorkflowDuration: metrics.avgWorkflowDuration,
      throughput: metrics.throughput
    }
  }

  /**
   * Analyze performance trends
   */
  private analyzePerformance(batch: any, history?: BatchMetricsHistory): PerformanceAnalysis {
    if (!history || history.dataPoints.length < 2) {
      return {
        trend: 'stable',
        throughputTrend: 'stable',
        efficiencyTrend: 'stable',
        resourceTrend: 'stable',
        bottlenecks: [],
        improvements: []
      }
    }

    const recent = history.dataPoints.slice(-10) // Last 10 data points
    const earlier = history.dataPoints.slice(-20, -10) // Previous 10 data points

    if (earlier.length === 0) {
      return {
        trend: 'stable',
        throughputTrend: 'stable',
        efficiencyTrend: 'stable',
        resourceTrend: 'stable',
        bottlenecks: [],
        improvements: []
      }
    }

    const recentAvg = this.calculateAverageMetrics(recent)
    const earlierAvg = this.calculateAverageMetrics(earlier)

    const throughputTrend = this.determineTrend(recentAvg.throughput, earlierAvg.throughput)
    const efficiencyTrend = this.determineTrend(recentAvg.efficiency, earlierAvg.efficiency)
    const resourceTrend = this.determineTrend(recentAvg.resourceUtilization, earlierAvg.resourceUtilization)

    const overallTrend = this.determineOverallTrend([throughputTrend, efficiencyTrend, resourceTrend])

    const bottlenecks = this.identifyBottlenecks(recentAvg)
    const improvements = this.identifyImprovements(recentAvg, earlierAvg)

    return {
      trend: overallTrend,
      throughputTrend,
      efficiencyTrend,
      resourceTrend,
      bottlenecks,
      improvements
    }
  }

  /**
   * Generate recommendations
   */
  private generateRecommendations(
    batch: any, 
    metrics: BatchMetrics, 
    performance: PerformanceAnalysis
  ): string[] {
    const recommendations: string[] = []

    // Failure rate recommendations
    if (metrics.failureRate > this.alertThresholds.failureRate) {
      recommendations.push('High failure rate detected. Consider reviewing workflow configurations and error handling.')
    }

    // Resource utilization recommendations
    if (metrics.resourceUtilization.overall > this.alertThresholds.resourceUtilization) {
      recommendations.push('High resource utilization. Consider reducing concurrency limit or optimizing workflows.')
    }

    // Throughput recommendations
    if (performance.throughputTrend === 'declining') {
      recommendations.push('Throughput is declining. Check for resource constraints or workflow bottlenecks.')
    }

    // Efficiency recommendations
    if (metrics.efficiency < 0.7) {
      recommendations.push('Low efficiency detected. Workflows are taking longer than estimated. Review time estimates.')
    }

    // Queue length recommendations
    if (metrics.queueLength > this.alertThresholds.queueLength) {
      recommendations.push('Large queue detected. Consider increasing concurrency limit or adding more resources.')
    }

    // Bottleneck-specific recommendations
    performance.bottlenecks.forEach(bottleneck => {
      switch (bottleneck) {
        case 'cpu':
          recommendations.push('CPU bottleneck detected. Consider optimizing CPU-intensive operations.')
          break
        case 'memory':
          recommendations.push('Memory bottleneck detected. Review memory usage and consider increasing limits.')
          break
        case 'network':
          recommendations.push('Network bottleneck detected. Check network connectivity and bandwidth.')
          break
        case 'storage':
          recommendations.push('Storage bottleneck detected. Review disk I/O operations and storage capacity.')
          break
      }
    })

    return recommendations
  }

  /**
   * Generate workflow reports
   */
  private generateWorkflowReports(batch: any): WorkflowReport[] {
    return batch.workflows.map((workflow: any) => ({
      id: workflow.id,
      status: workflow.status,
      duration: workflow.startTime && workflow.endTime 
        ? workflow.endTime.getTime() - workflow.startTime.getTime()
        : null,
      retryCount: workflow.retryCount,
      error: workflow.error,
      resourceUsage: workflow.resourceRequirements
    }))
  }

  /**
   * Analyze resource usage patterns
   */
  private analyzeResourceUsage(batch: any, history?: BatchMetricsHistory): ResourceUsageAnalysis {
    if (!history) {
      return {
        peakUsage: { cpu: 0, memory: 0, network: 0, storage: 0 },
        avgUsage: { cpu: 0, memory: 0, network: 0, storage: 0 },
        trends: { cpu: 'stable', memory: 'stable', network: 'stable', storage: 'stable' },
        recommendations: []
      }
    }

    const dataPoints = history.dataPoints
    if (dataPoints.length === 0) {
      return {
        peakUsage: { cpu: 0, memory: 0, network: 0, storage: 0 },
        avgUsage: { cpu: 0, memory: 0, network: 0, storage: 0 },
        trends: { cpu: 'stable', memory: 'stable', network: 'stable', storage: 'stable' },
        recommendations: []
      }
    }

    // Calculate peak usage
    const peakUsage = dataPoints.reduce((peak, point) => ({
      cpu: Math.max(peak.cpu, point.metrics.resourceUtilization.cpu),
      memory: Math.max(peak.memory, point.metrics.resourceUtilization.memory),
      network: Math.max(peak.network, point.metrics.resourceUtilization.network),
      storage: Math.max(peak.storage, point.metrics.resourceUtilization.storage)
    }), { cpu: 0, memory: 0, network: 0, storage: 0 })

    // Calculate average usage
    const avgUsage = dataPoints.reduce((sum, point) => ({
      cpu: sum.cpu + point.metrics.resourceUtilization.cpu,
      memory: sum.memory + point.metrics.resourceUtilization.memory,
      network: sum.network + point.metrics.resourceUtilization.network,
      storage: sum.storage + point.metrics.resourceUtilization.storage
    }), { cpu: 0, memory: 0, network: 0, storage: 0 })

    Object.keys(avgUsage).forEach(key => {
      (avgUsage as any)[key] /= dataPoints.length
    })

    // Analyze trends (simplified)
    const trends = {
      cpu: 'stable' as const,
      memory: 'stable' as const,
      network: 'stable' as const,
      storage: 'stable' as const
    }

    const recommendations: string[] = []
    if (peakUsage.cpu > 0.9) recommendations.push('Consider optimizing CPU usage')
    if (peakUsage.memory > 0.9) recommendations.push('Consider optimizing memory usage')
    if (peakUsage.network > 0.9) recommendations.push('Consider optimizing network usage')
    if (peakUsage.storage > 0.9) recommendations.push('Consider optimizing storage usage')

    return {
      peakUsage,
      avgUsage,
      trends,
      recommendations
    }
  }

  /**
   * Generate alerts based on thresholds
   */
  private generateAlerts(batch: any, metrics: BatchMetrics): BatchAlert[] {
    const alerts: BatchAlert[] = []

    if (metrics.failureRate > this.alertThresholds.failureRate) {
      alerts.push({
        type: 'high_failure_rate',
        severity: 'high',
        message: `Failure rate (${(metrics.failureRate * 100).toFixed(1)}%) exceeds threshold`,
        timestamp: new Date()
      })
    }

    if (metrics.resourceUtilization.overall > this.alertThresholds.resourceUtilization) {
      alerts.push({
        type: 'high_resource_usage',
        severity: 'medium',
        message: `Resource utilization (${(metrics.resourceUtilization.overall * 100).toFixed(1)}%) is high`,
        timestamp: new Date()
      })
    }

    if (metrics.avgWorkflowDuration > this.alertThresholds.avgDuration) {
      alerts.push({
        type: 'slow_performance',
        severity: 'medium',
        message: `Average workflow duration exceeds threshold`,
        timestamp: new Date()
      })
    }

    if (metrics.queueLength > this.alertThresholds.queueLength) {
      alerts.push({
        type: 'large_queue',
        severity: 'low',
        message: `Queue length (${metrics.queueLength}) is large`,
        timestamp: new Date()
      })
    }

    return alerts
  }

  /**
   * Check alerts and trigger notifications
   */
  private checkAlerts(batchId: string, metrics: BatchMetrics): void {
    const alerts = this.generateAlerts({ id: batchId }, metrics)
    
    alerts.forEach(alert => {
      // This would trigger actual alert notifications
      console.log(`ALERT [${alert.severity}]: ${alert.message}`)
    })
  }

  /**
   * Helper methods
   */
  private calculateAverageBatchDuration(batches: any[]): number {
    const completedBatches = batches.filter(b => b.endTime)
    if (completedBatches.length === 0) return 0

    const totalDuration = completedBatches.reduce((sum, batch) => {
      return sum + (batch.endTime.getTime() - batch.startTime.getTime())
    }, 0)

    return totalDuration / completedBatches.length
  }

  private calculateSystemResourceUtilization(batches: any[]): any {
    // This would calculate actual system resource utilization
    return {
      cpu: 0.5,
      memory: 0.4,
      network: 0.2,
      storage: 0.1,
      overall: 0.5
    }
  }

  private calculateAverageMetrics(dataPoints: any[]): any {
    if (dataPoints.length === 0) return {}

    const sum = dataPoints.reduce((acc, point) => ({
      throughput: acc.throughput + point.metrics.throughput,
      efficiency: acc.efficiency + point.metrics.efficiency,
      resourceUtilization: acc.resourceUtilization + point.metrics.resourceUtilization.overall
    }), { throughput: 0, efficiency: 0, resourceUtilization: 0 })

    return {
      throughput: sum.throughput / dataPoints.length,
      efficiency: sum.efficiency / dataPoints.length,
      resourceUtilization: sum.resourceUtilization / dataPoints.length
    }
  }

  private determineTrend(current: number, previous: number): 'improving' | 'declining' | 'stable' {
    const threshold = 0.1 // 10% change threshold
    const change = (current - previous) / previous

    if (change > threshold) return 'improving'
    if (change < -threshold) return 'declining'
    return 'stable'
  }

  private determineOverallTrend(trends: string[]): 'improving' | 'declining' | 'stable' {
    const improving = trends.filter(t => t === 'improving').length
    const declining = trends.filter(t => t === 'declining').length

    if (improving > declining) return 'improving'
    if (declining > improving) return 'declining'
    return 'stable'
  }

  private identifyBottlenecks(metrics: any): string[] {
    const bottlenecks: string[] = []
    const threshold = 0.8

    if (metrics.resourceUtilization > threshold) {
      // This would identify specific resource bottlenecks
      bottlenecks.push('cpu', 'memory')
    }

    return bottlenecks
  }

  private identifyImprovements(current: any, previous: any): string[] {
    const improvements: string[] = []

    if (current.throughput > previous.throughput * 1.1) {
      improvements.push('Throughput improved significantly')
    }

    if (current.efficiency > previous.efficiency * 1.1) {
      improvements.push('Efficiency improved significantly')
    }

    return improvements
  }

  /**
   * Cleanup resources
   */
  cleanup(): void {
    // Stop all active monitors
    for (const [batchId] of this.activeMonitors) {
      this.stopMonitoring(batchId)
    }
    
    // Clear metrics history
    this.metricsHistory.clear()
  }
}

// Interfaces
interface BatchMetrics {
  batchId: string
  timestamp: Date
  progress: number
  throughput: number
  failureRate: number
  efficiency: number
  avgWorkflowDuration: number
  minWorkflowDuration: number
  maxWorkflowDuration: number
  resourceUtilization: any
  queueLength: number
  activeWorkflows: number
  completedWorkflows: number
  failedWorkflows: number
  totalWorkflows: number
  estimatedTimeRemaining: number
}

interface BatchMetricsHistory {
  batchId: string
  startTime: Date
  dataPoints: {
    timestamp: Date
    metrics: BatchMetrics
  }[]
  aggregatedMetrics: {
    avgThroughput: number
    avgFailureRate: number
    avgEfficiency: number
    avgResourceUtilization: number
    peakResourceUtilization: number
    totalDataPoints: number
  }
}

interface BatchReport {
  batchId: string
  generatedAt: Date
  summary: BatchSummary
  performance: PerformanceAnalysis
  metrics: BatchMetrics
  workflows: WorkflowReport[]
  resourceUsage: ResourceUsageAnalysis
  alerts: BatchAlert[]
  recommendations: string[]
}

interface BatchSummary {
  name: string
  status: string
  startTime: Date
  endTime?: Date
  duration: number
  totalWorkflows: number
  completedWorkflows: number
  failedWorkflows: number
  successRate: number
  avgWorkflowDuration: number
  throughput: number
}

interface PerformanceAnalysis {
  trend: 'improving' | 'declining' | 'stable'
  throughputTrend: 'improving' | 'declining' | 'stable'
  efficiencyTrend: 'improving' | 'declining' | 'stable'
  resourceTrend: 'improving' | 'declining' | 'stable'
  bottlenecks: string[]
  improvements: string[]
}

interface WorkflowReport {
  id: string
  status: string
  duration: number | null
  retryCount: number
  error?: any
  resourceUsage: any
}

interface ResourceUsageAnalysis {
  peakUsage: { cpu: number; memory: number; network: number; storage: number }
  avgUsage: { cpu: number; memory: number; network: number; storage: number }
  trends: { cpu: string; memory: string; network: string; storage: string }
  recommendations: string[]
}

interface BatchAlert {
  type: 'high_failure_rate' | 'high_resource_usage' | 'slow_performance' | 'large_queue'
  severity: 'low' | 'medium' | 'high'
  message: string
  timestamp: Date
}

interface SystemBatchStats {
  totalBatches: number
  runningBatches: number
  completedBatches: number
  failedBatches: number
  totalWorkflows: number
  completedWorkflows: number
  failedWorkflows: number
  avgBatchDuration: number
  systemResourceUtilization: any
  lastUpdate: Date
}

interface AlertThresholds {
  failureRate: number
  resourceUtilization: number
  avgDuration: number
  queueLength: number
}

// Export singleton instance
export const batchMonitoringService = new BatchMonitoringService()