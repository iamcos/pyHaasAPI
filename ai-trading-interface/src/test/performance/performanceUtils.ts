/**
 * Performance Testing Utilities
 * 
 * Utilities for measuring and validating performance requirements:
 * - Response time validation (< 200ms)
 * - Load testing for 100+ concurrent strategies
 * - Memory usage monitoring
 * - Rendering performance
 */

export interface PerformanceMetrics {
  responseTime: number
  memoryUsage: number
  renderTime: number
  throughput: number
  errorRate: number
}

export interface LoadTestConfig {
  concurrentUsers: number
  duration: number // in seconds
  rampUpTime: number // in seconds
  targetEndpoint: string
  requestsPerSecond?: number
}

export interface PerformanceThresholds {
  maxResponseTime: number // 200ms requirement
  maxMemoryUsage: number // in MB
  maxRenderTime: number // in ms
  minThroughput: number // requests per second
  maxErrorRate: number // percentage
}

export class PerformanceMonitor {
  private metrics: PerformanceMetrics[] = []
  private startTime: number = 0
  private memoryBaseline: number = 0

  constructor(private thresholds: PerformanceThresholds) {
    this.memoryBaseline = this.getCurrentMemoryUsage()
  }

  startMeasurement(): void {
    this.startTime = performance.now()
  }

  endMeasurement(): PerformanceMetrics {
    const endTime = performance.now()
    const responseTime = endTime - this.startTime
    const memoryUsage = this.getCurrentMemoryUsage() - this.memoryBaseline
    
    const metrics: PerformanceMetrics = {
      responseTime,
      memoryUsage,
      renderTime: this.measureRenderTime(),
      throughput: 0, // Will be calculated in load tests
      errorRate: 0,
    }

    this.metrics.push(metrics)
    return metrics
  }

  private getCurrentMemoryUsage(): number {
    if ('memory' in performance) {
      return (performance as any).memory.usedJSHeapSize / 1024 / 1024 // MB
    }
    return 0
  }

  private measureRenderTime(): number {
    const paintEntries = performance.getEntriesByType('paint')
    const firstContentfulPaint = paintEntries.find(
      entry => entry.name === 'first-contentful-paint'
    )
    return firstContentfulPaint ? firstContentfulPaint.startTime : 0
  }

  validateThresholds(metrics: PerformanceMetrics): {
    passed: boolean
    violations: string[]
  } {
    const violations: string[] = []

    if (metrics.responseTime > this.thresholds.maxResponseTime) {
      violations.push(
        `Response time ${metrics.responseTime.toFixed(2)}ms exceeds threshold ${this.thresholds.maxResponseTime}ms`
      )
    }

    if (metrics.memoryUsage > this.thresholds.maxMemoryUsage) {
      violations.push(
        `Memory usage ${metrics.memoryUsage.toFixed(2)}MB exceeds threshold ${this.thresholds.maxMemoryUsage}MB`
      )
    }

    if (metrics.renderTime > this.thresholds.maxRenderTime) {
      violations.push(
        `Render time ${metrics.renderTime.toFixed(2)}ms exceeds threshold ${this.thresholds.maxRenderTime}ms`
      )
    }

    if (metrics.throughput < this.thresholds.minThroughput) {
      violations.push(
        `Throughput ${metrics.throughput.toFixed(2)} req/s below threshold ${this.thresholds.minThroughput} req/s`
      )
    }

    if (metrics.errorRate > this.thresholds.maxErrorRate) {
      violations.push(
        `Error rate ${metrics.errorRate.toFixed(2)}% exceeds threshold ${this.thresholds.maxErrorRate}%`
      )
    }

    return {
      passed: violations.length === 0,
      violations,
    }
  }

  getAverageMetrics(): PerformanceMetrics {
    if (this.metrics.length === 0) {
      return {
        responseTime: 0,
        memoryUsage: 0,
        renderTime: 0,
        throughput: 0,
        errorRate: 0,
      }
    }

    const sum = this.metrics.reduce(
      (acc, metrics) => ({
        responseTime: acc.responseTime + metrics.responseTime,
        memoryUsage: acc.memoryUsage + metrics.memoryUsage,
        renderTime: acc.renderTime + metrics.renderTime,
        throughput: acc.throughput + metrics.throughput,
        errorRate: acc.errorRate + metrics.errorRate,
      }),
      { responseTime: 0, memoryUsage: 0, renderTime: 0, throughput: 0, errorRate: 0 }
    )

    const count = this.metrics.length
    return {
      responseTime: sum.responseTime / count,
      memoryUsage: sum.memoryUsage / count,
      renderTime: sum.renderTime / count,
      throughput: sum.throughput / count,
      errorRate: sum.errorRate / count,
    }
  }

  reset(): void {
    this.metrics = []
    this.memoryBaseline = this.getCurrentMemoryUsage()
  }
}

export class LoadTester {
  private results: PerformanceMetrics[] = []
  private errors: Error[] = []

  async runLoadTest(config: LoadTestConfig): Promise<{
    metrics: PerformanceMetrics
    success: boolean
    errors: Error[]
  }> {
    const startTime = Date.now()
    const promises: Promise<void>[] = []
    let completedRequests = 0
    let totalRequests = 0

    // Calculate total requests
    const requestsPerUser = Math.ceil(
      (config.requestsPerSecond || 10) * config.duration / config.concurrentUsers
    )
    totalRequests = config.concurrentUsers * requestsPerUser

    // Ramp up users gradually
    const rampUpInterval = (config.rampUpTime * 1000) / config.concurrentUsers

    for (let i = 0; i < config.concurrentUsers; i++) {
      const userPromise = new Promise<void>((resolve) => {
        setTimeout(async () => {
          await this.simulateUser(config, requestsPerUser)
          resolve()
        }, i * rampUpInterval)
      })
      promises.push(userPromise)
    }

    // Wait for all users to complete
    await Promise.allSettled(promises)

    const endTime = Date.now()
    const duration = (endTime - startTime) / 1000 // seconds
    
    const metrics: PerformanceMetrics = {
      responseTime: this.calculateAverageResponseTime(),
      memoryUsage: this.getCurrentMemoryUsage(),
      renderTime: 0,
      throughput: completedRequests / duration,
      errorRate: (this.errors.length / totalRequests) * 100,
    }

    return {
      metrics,
      success: this.errors.length === 0,
      errors: this.errors,
    }
  }

  private async simulateUser(config: LoadTestConfig, requestCount: number): Promise<void> {
    for (let i = 0; i < requestCount; i++) {
      try {
        const startTime = performance.now()
        
        // Simulate API request
        await this.makeRequest(config.targetEndpoint)
        
        const endTime = performance.now()
        this.results.push({
          responseTime: endTime - startTime,
          memoryUsage: 0,
          renderTime: 0,
          throughput: 0,
          errorRate: 0,
        })
      } catch (error) {
        this.errors.push(error as Error)
      }

      // Add small delay between requests
      await new Promise(resolve => setTimeout(resolve, 100))
    }
  }

  private async makeRequest(endpoint: string): Promise<void> {
    const response = await fetch(endpoint, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    })

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }
  }

  private calculateAverageResponseTime(): number {
    if (this.results.length === 0) return 0
    
    const total = this.results.reduce((sum, result) => sum + result.responseTime, 0)
    return total / this.results.length
  }

  private getCurrentMemoryUsage(): number {
    if ('memory' in performance) {
      return (performance as any).memory.usedJSHeapSize / 1024 / 1024 // MB
    }
    return 0
  }

  reset(): void {
    this.results = []
    this.errors = []
  }
}

export class RenderPerformanceMonitor {
  private observer: PerformanceObserver | null = null
  private renderMetrics: number[] = []

  startMonitoring(): void {
    if ('PerformanceObserver' in window) {
      this.observer = new PerformanceObserver((list) => {
        const entries = list.getEntries()
        entries.forEach((entry) => {
          if (entry.entryType === 'measure' || entry.entryType === 'navigation') {
            this.renderMetrics.push(entry.duration)
          }
        })
      })

      this.observer.observe({ entryTypes: ['measure', 'navigation', 'paint'] })
    }
  }

  stopMonitoring(): void {
    if (this.observer) {
      this.observer.disconnect()
      this.observer = null
    }
  }

  measureComponentRender<T>(
    componentName: string,
    renderFunction: () => T
  ): { result: T; renderTime: number } {
    const startMark = `${componentName}-start`
    const endMark = `${componentName}-end`
    const measureName = `${componentName}-render`

    performance.mark(startMark)
    const result = renderFunction()
    performance.mark(endMark)
    
    performance.measure(measureName, startMark, endMark)
    
    const measure = performance.getEntriesByName(measureName)[0]
    const renderTime = measure ? measure.duration : 0

    // Clean up marks and measures
    performance.clearMarks(startMark)
    performance.clearMarks(endMark)
    performance.clearMeasures(measureName)

    return { result, renderTime }
  }

  getAverageRenderTime(): number {
    if (this.renderMetrics.length === 0) return 0
    
    const total = this.renderMetrics.reduce((sum, time) => sum + time, 0)
    return total / this.renderMetrics.length
  }

  getRenderTimePercentiles(): {
    p50: number
    p90: number
    p95: number
    p99: number
  } {
    if (this.renderMetrics.length === 0) {
      return { p50: 0, p90: 0, p95: 0, p99: 0 }
    }

    const sorted = [...this.renderMetrics].sort((a, b) => a - b)
    const length = sorted.length

    return {
      p50: sorted[Math.floor(length * 0.5)],
      p90: sorted[Math.floor(length * 0.9)],
      p95: sorted[Math.floor(length * 0.95)],
      p99: sorted[Math.floor(length * 0.99)],
    }
  }

  reset(): void {
    this.renderMetrics = []
  }
}

// Default performance thresholds based on requirements
export const DEFAULT_PERFORMANCE_THRESHOLDS: PerformanceThresholds = {
  maxResponseTime: 200, // 200ms requirement
  maxMemoryUsage: 512, // 512MB
  maxRenderTime: 100, // 100ms for UI rendering
  minThroughput: 10, // 10 requests per second minimum
  maxErrorRate: 1, // 1% error rate maximum
}

// Utility function to create a performance test
export function createPerformanceTest(
  name: string,
  testFunction: () => Promise<void> | void,
  thresholds: Partial<PerformanceThresholds> = {}
): () => Promise<void> {
  return async () => {
    const monitor = new PerformanceMonitor({
      ...DEFAULT_PERFORMANCE_THRESHOLDS,
      ...thresholds,
    })

    monitor.startMeasurement()
    await testFunction()
    const metrics = monitor.endMeasurement()

    const validation = monitor.validateThresholds(metrics)
    
    if (!validation.passed) {
      throw new Error(
        `Performance test "${name}" failed:\n${validation.violations.join('\n')}`
      )
    }

    console.log(`✅ Performance test "${name}" passed:`, {
      responseTime: `${metrics.responseTime.toFixed(2)}ms`,
      memoryUsage: `${metrics.memoryUsage.toFixed(2)}MB`,
      renderTime: `${metrics.renderTime.toFixed(2)}ms`,
    })
  }
}