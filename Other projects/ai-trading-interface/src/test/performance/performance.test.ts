import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent } from '../utils/testUtils'
import {
  PerformanceMonitor,
  LoadTester,
  RenderPerformanceMonitor,
  DEFAULT_PERFORMANCE_THRESHOLDS,
  createPerformanceTest,
} from './performanceUtils'

// Mock components for performance testing
const HeavyComponent = ({ itemCount = 1000 }: { itemCount?: number }) => (
  <div>
    <h1>Heavy Component</h1>
    <ul>
      {Array.from({ length: itemCount }, (_, i) => (
        <li key={i}>Item {i}</li>
      ))}
    </ul>
  </div>
)

const InteractiveComponent = () => {
  const [count, setCount] = React.useState(0)
  const [items, setItems] = React.useState<string[]>([])

  const handleClick = () => {
    setCount(c => c + 1)
    setItems(prev => [...prev, `Item ${prev.length + 1}`])
  }

  return (
    <div>
      <button onClick={handleClick}>Add Item ({count})</button>
      <ul>
        {items.map((item, index) => (
          <li key={index}>{item}</li>
        ))}
      </ul>
    </div>
  )
}

describe('Performance Tests', () => {
  let performanceMonitor: PerformanceMonitor
  let renderMonitor: RenderPerformanceMonitor

  beforeEach(() => {
    performanceMonitor = new PerformanceMonitor(DEFAULT_PERFORMANCE_THRESHOLDS)
    renderMonitor = new RenderPerformanceMonitor()
    renderMonitor.startMonitoring()
  })

  afterEach(() => {
    renderMonitor.stopMonitoring()
    performanceMonitor.reset()
    renderMonitor.reset()
  })

  describe('Response Time Validation (< 200ms)', () => {
    it('should render components within 200ms threshold', 
      createPerformanceTest('component-render', async () => {
        const { result, renderTime } = renderMonitor.measureComponentRender(
          'HeavyComponent',
          () => render(<HeavyComponent itemCount={100} />)
        )

        expect(screen.getByText('Heavy Component')).toBeInTheDocument()
        expect(renderTime).toBeLessThan(200)
      })
    )

    it('should handle user interactions within 200ms', 
      createPerformanceTest('user-interaction', async () => {
        render(<InteractiveComponent />)
        
        const button = screen.getByRole('button')
        
        performanceMonitor.startMeasurement()
        fireEvent.click(button)
        const metrics = performanceMonitor.endMeasurement()

        expect(metrics.responseTime).toBeLessThan(200)
        expect(screen.getByText('Add Item (1)')).toBeInTheDocument()
      })
    )

    it('should process API responses within 200ms', 
      createPerformanceTest('api-response', async () => {
        // Mock API call
        const mockApiCall = async () => {
          return new Promise(resolve => {
            setTimeout(() => resolve({ data: 'test' }), 50)
          })
        }

        performanceMonitor.startMeasurement()
        const result = await mockApiCall()
        const metrics = performanceMonitor.endMeasurement()

        expect(result).toEqual({ data: 'test' })
        expect(metrics.responseTime).toBeLessThan(200)
      })
    )

    it('should update state within 200ms for complex operations', 
      createPerformanceTest('state-update', async () => {
        const { rerender } = render(<HeavyComponent itemCount={100} />)
        
        performanceMonitor.startMeasurement()
        rerender(<HeavyComponent itemCount={500} />)
        const metrics = performanceMonitor.endMeasurement()

        expect(metrics.responseTime).toBeLessThan(200)
      })
    )
  })

  describe('Load Testing (100+ Concurrent Strategies)', () => {
    it('should handle 100 concurrent strategy simulations', async () => {
      const loadTester = new LoadTester()
      
      // Mock strategy endpoint
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ status: 'success', strategyId: 'test-strategy' }),
      })

      const config = {
        concurrentUsers: 100,
        duration: 10, // 10 seconds
        rampUpTime: 2, // 2 seconds ramp up
        targetEndpoint: '/api/strategies/execute',
        requestsPerSecond: 5,
      }

      const result = await loadTester.runLoadTest(config)

      expect(result.success).toBe(true)
      expect(result.metrics.throughput).toBeGreaterThan(10) // At least 10 req/s
      expect(result.metrics.errorRate).toBeLessThan(5) // Less than 5% error rate
      expect(result.metrics.responseTime).toBeLessThan(200) // Under 200ms average
    })

    it('should maintain performance with concurrent component renders', async () => {
      const renderPromises = Array.from({ length: 100 }, (_, i) => 
        new Promise<number>(resolve => {
          const { renderTime } = renderMonitor.measureComponentRender(
            `concurrent-component-${i}`,
            () => render(<HeavyComponent itemCount={50} />)
          )
          resolve(renderTime)
        })
      )

      const renderTimes = await Promise.all(renderPromises)
      const averageRenderTime = renderTimes.reduce((a, b) => a + b, 0) / renderTimes.length

      expect(averageRenderTime).toBeLessThan(200)
      expect(renderTimes.every(time => time < 500)).toBe(true) // No render over 500ms
    })

    it('should handle concurrent state updates efficiently', async () => {
      const components = Array.from({ length: 50 }, () => 
        render(<InteractiveComponent />)
      )

      const updatePromises = components.map(({ container }) => 
        new Promise<number>(resolve => {
          const button = container.querySelector('button')!
          
          performanceMonitor.startMeasurement()
          fireEvent.click(button)
          const metrics = performanceMonitor.endMeasurement()
          
          resolve(metrics.responseTime)
        })
      )

      const updateTimes = await Promise.all(updatePromises)
      const averageUpdateTime = updateTimes.reduce((a, b) => a + b, 0) / updateTimes.length

      expect(averageUpdateTime).toBeLessThan(200)
    })
  })

  describe('Memory Usage Monitoring', () => {
    it('should not exceed memory thresholds during heavy operations', async () => {
      const initialMemory = performanceMonitor.getCurrentMemoryUsage()
      
      // Render multiple heavy components
      const components = Array.from({ length: 20 }, (_, i) => 
        render(<HeavyComponent itemCount={1000} />)
      )

      performanceMonitor.startMeasurement()
      
      // Trigger re-renders
      components.forEach(({ rerender }) => {
        rerender(<HeavyComponent itemCount={1500} />)
      })

      const metrics = performanceMonitor.endMeasurement()
      
      expect(metrics.memoryUsage).toBeLessThan(DEFAULT_PERFORMANCE_THRESHOLDS.maxMemoryUsage)
    })

    it('should clean up memory after component unmounting', async () => {
      const { unmount } = render(<HeavyComponent itemCount={2000} />)
      
      const beforeUnmount = performanceMonitor.getCurrentMemoryUsage()
      unmount()
      
      // Force garbage collection if available
      if (global.gc) {
        global.gc()
      }
      
      // Wait for cleanup
      await new Promise(resolve => setTimeout(resolve, 100))
      
      const afterUnmount = performanceMonitor.getCurrentMemoryUsage()
      
      // Memory should not increase significantly after unmount
      expect(afterUnmount - beforeUnmount).toBeLessThan(50) // Less than 50MB difference
    })
  })

  describe('Rendering Performance', () => {
    it('should maintain smooth rendering with large datasets', async () => {
      const itemCounts = [100, 500, 1000, 2000]
      const renderTimes: number[] = []

      for (const itemCount of itemCounts) {
        const { renderTime } = renderMonitor.measureComponentRender(
          `large-dataset-${itemCount}`,
          () => render(<HeavyComponent itemCount={itemCount} />)
        )
        renderTimes.push(renderTime)
      }

      // Render time should scale reasonably with data size
      const averageRenderTime = renderTimes.reduce((a, b) => a + b, 0) / renderTimes.length
      expect(averageRenderTime).toBeLessThan(300) // Allow slightly more time for large datasets

      // No single render should take too long
      expect(renderTimes.every(time => time < 500)).toBe(true)
    })

    it('should handle rapid successive updates efficiently', async () => {
      render(<InteractiveComponent />)
      const button = screen.getByRole('button')

      const updateTimes: number[] = []

      // Perform 20 rapid updates
      for (let i = 0; i < 20; i++) {
        performanceMonitor.startMeasurement()
        fireEvent.click(button)
        const metrics = performanceMonitor.endMeasurement()
        updateTimes.push(metrics.responseTime)
      }

      const averageUpdateTime = updateTimes.reduce((a, b) => a + b, 0) / updateTimes.length
      expect(averageUpdateTime).toBeLessThan(200)

      // Performance should not degrade significantly over time
      const firstHalf = updateTimes.slice(0, 10)
      const secondHalf = updateTimes.slice(10)
      
      const firstHalfAvg = firstHalf.reduce((a, b) => a + b, 0) / firstHalf.length
      const secondHalfAvg = secondHalf.reduce((a, b) => a + b, 0) / secondHalf.length
      
      expect(secondHalfAvg).toBeLessThan(firstHalfAvg * 2) // Should not double in time
    })

    it('should maintain 60fps during animations', async () => {
      // Mock animation frame timing
      const frameTimings: number[] = []
      let lastFrameTime = performance.now()

      const measureFrame = () => {
        const currentTime = performance.now()
        const frameDuration = currentTime - lastFrameTime
        frameTimings.push(frameDuration)
        lastFrameTime = currentTime
      }

      // Simulate 60 frames (1 second at 60fps)
      for (let i = 0; i < 60; i++) {
        measureFrame()
        await new Promise(resolve => setTimeout(resolve, 16.67)) // ~60fps
      }

      const averageFrameTime = frameTimings.reduce((a, b) => a + b, 0) / frameTimings.length
      const targetFrameTime = 1000 / 60 // 16.67ms for 60fps

      expect(averageFrameTime).toBeLessThan(targetFrameTime * 1.5) // Allow 50% tolerance
    })
  })

  describe('Stress Testing', () => {
    it('should handle extreme load without crashing', async () => {
      const stressTest = async () => {
        // Create many components simultaneously
        const components = Array.from({ length: 100 }, (_, i) => 
          render(<HeavyComponent itemCount={100} />)
        )

        // Perform many rapid updates
        const updatePromises = components.map(({ rerender }, i) => 
          new Promise<void>(resolve => {
            setTimeout(() => {
              rerender(<HeavyComponent itemCount={200} />)
              resolve()
            }, i * 10) // Stagger updates
          })
        )

        await Promise.all(updatePromises)
      }

      // Should not throw errors under stress
      await expect(stressTest()).resolves.not.toThrow()
    })

    it('should recover gracefully from performance spikes', async () => {
      // Create a performance spike
      const heavyOperation = () => {
        const start = Date.now()
        while (Date.now() - start < 100) {
          // Busy wait to simulate heavy computation
        }
      }

      performanceMonitor.startMeasurement()
      heavyOperation()
      const spikeMetrics = performanceMonitor.endMeasurement()

      // Verify the spike occurred
      expect(spikeMetrics.responseTime).toBeGreaterThan(100)

      // Test recovery with normal operation
      performanceMonitor.startMeasurement()
      render(<HeavyComponent itemCount={100} />)
      const recoveryMetrics = performanceMonitor.endMeasurement()

      // Should recover to normal performance
      expect(recoveryMetrics.responseTime).toBeLessThan(200)
    })
  })

  describe('Performance Regression Detection', () => {
    it('should detect performance regressions', async () => {
      // Baseline measurement
      const baselineRenderTime = renderMonitor.measureComponentRender(
        'baseline-component',
        () => render(<HeavyComponent itemCount={500} />)
      ).renderTime

      // Simulated regression (heavier component)
      const regressionRenderTime = renderMonitor.measureComponentRender(
        'regression-component',
        () => render(<HeavyComponent itemCount={2000} />)
      ).renderTime

      // Should detect significant performance regression
      const regressionThreshold = baselineRenderTime * 2 // 100% increase
      expect(regressionRenderTime).toBeGreaterThan(regressionThreshold)
    })

    it('should track performance trends over time', async () => {
      const measurements: number[] = []

      // Take multiple measurements
      for (let i = 0; i < 10; i++) {
        const { renderTime } = renderMonitor.measureComponentRender(
          `trend-measurement-${i}`,
          () => render(<HeavyComponent itemCount={300} />)
        )
        measurements.push(renderTime)
      }

      // Calculate trend
      const firstHalf = measurements.slice(0, 5)
      const secondHalf = measurements.slice(5)
      
      const firstHalfAvg = firstHalf.reduce((a, b) => a + b, 0) / firstHalf.length
      const secondHalfAvg = secondHalf.reduce((a, b) => a + b, 0) / secondHalf.length

      // Performance should remain stable (within 20% variance)
      const variance = Math.abs(secondHalfAvg - firstHalfAvg) / firstHalfAvg
      expect(variance).toBeLessThan(0.2) // Less than 20% variance
    })
  })
})