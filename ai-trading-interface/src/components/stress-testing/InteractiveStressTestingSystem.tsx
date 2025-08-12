import React, { useState, useEffect } from 'react'
import { 
  ExclamationTriangleIcon,
  PlayIcon,
  PauseIcon,
  StopIcon,
  Cog6ToothIcon,
  DocumentArrowDownIcon,
  ChartBarIcon,
  ClockIcon
} from '@heroicons/react/24/outline'
import { Card, CardHeader, CardContent, Button } from '@/components/ui'
import { ScenarioSelector } from './ScenarioSelector'
import { StressTestConfiguration } from './StressTestConfiguration'
import { SimulationControls } from './SimulationControls'
import { StressTestResults } from './StressTestResults'
import { StressTestReporting } from './StressTestReporting'
import { useTradingStore } from '@/stores/tradingStore'
import { stressTestingService } from '@/services/stressTestingService'
import type { 
  StressTestScenario, 
  StressTestResult, 
  StressTestConfiguration as StressTestConfig 
} from '@/services/stressTestingService'

interface InteractiveStressTestingSystemProps {
  className?: string
}

type TestingPhase = 'setup' | 'configuration' | 'running' | 'results' | 'reporting'

export function InteractiveStressTestingSystem({ className = '' }: InteractiveStressTestingSystemProps) {
  const { bots, positions, markets } = useTradingStore()
  
  const [currentPhase, setCurrentPhase] = useState<TestingPhase>('setup')
  const [selectedScenario, setSelectedScenario] = useState<StressTestScenario | null>(null)
  const [configuration, setConfiguration] = useState<Partial<StressTestConfig>>({})
  const [testResults, setTestResults] = useState<StressTestResult[]>([])
  const [currentTest, setCurrentTest] = useState<StressTestResult | null>(null)
  const [isRunning, setIsRunning] = useState(false)
  const [progress, setProgress] = useState(0)
  const [error, setError] = useState<string | null>(null)

  // Available scenarios
  const [scenarios, setScenarios] = useState<StressTestScenario[]>([])

  useEffect(() => {
    // Load predefined scenarios
    const predefinedScenarios = stressTestingService.getPredefinedScenarios()
    setScenarios(predefinedScenarios)
  }, [])

  // Run stress test
  const runStressTest = async () => {
    if (!selectedScenario) return

    try {
      setIsRunning(true)
      setCurrentPhase('running')
      setError(null)
      setProgress(0)

      // Simulate progress updates
      const progressInterval = setInterval(() => {
        setProgress(prev => Math.min(prev + Math.random() * 10, 95))
      }, 500)

      const result = await stressTestingService.runStressTest(
        selectedScenario,
        bots,
        positions,
        markets,
        configuration
      )

      clearInterval(progressInterval)
      setProgress(100)

      setCurrentTest(result)
      setTestResults(prev => [result, ...prev])
      setCurrentPhase('results')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to run stress test')
      setCurrentPhase('setup')
    } finally {
      setIsRunning(false)
    }
  }

  // Stop running test
  const stopTest = async () => {
    try {
      const runningTests = stressTestingService.getRunningTests()
      if (runningTests.length > 0) {
        await stressTestingService.cancelStressTest(runningTests[0])
      }
      setIsRunning(false)
      setCurrentPhase('setup')
      setProgress(0)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to stop test')
    }
  }

  // Reset to setup
  const resetToSetup = () => {
    setCurrentPhase('setup')
    setSelectedScenario(null)
    setConfiguration({})
    setCurrentTest(null)
    setProgress(0)
    setError(null)
  }

  // Phase navigation
  const goToConfiguration = () => {
    if (selectedScenario) {
      setCurrentPhase('configuration')
    }
  }

  const goToReporting = () => {
    if (currentTest) {
      setCurrentPhase('reporting')
    }
  }

  const renderPhaseContent = () => {
    switch (currentPhase) {
      case 'setup':
        return (
          <ScenarioSelector
            scenarios={scenarios}
            selectedScenario={selectedScenario}
            onScenarioSelect={setSelectedScenario}
            onCreateCustom={(scenario) => {
              setScenarios(prev => [...prev, scenario])
              setSelectedScenario(scenario)
            }}
          />
        )

      case 'configuration':
        return (
          <StressTestConfiguration
            scenario={selectedScenario!}
            configuration={configuration}
            onConfigurationChange={setConfiguration}
            portfolioData={{ bots, positions, markets }}
          />
        )

      case 'running':
        return (
          <SimulationControls
            scenario={selectedScenario!}
            progress={progress}
            isRunning={isRunning}
            onStop={stopTest}
            estimatedTimeRemaining={Math.max(0, (100 - progress) * 2)} // seconds
          />
        )

      case 'results':
        return (
          <StressTestResults
            result={currentTest!}
            scenario={selectedScenario!}
            onViewDetails={() => setCurrentPhase('reporting')}
            onRunAnother={resetToSetup}
          />
        )

      case 'reporting':
        return (
          <StressTestReporting
            result={currentTest!}
            scenario={selectedScenario!}
            onBack={() => setCurrentPhase('results')}
            onExport={(format) => {
              // Handle export
              console.log('Exporting in format:', format)
            }}
          />
        )

      default:
        return null
    }
  }

  const getPhaseTitle = () => {
    switch (currentPhase) {
      case 'setup': return 'Scenario Selection'
      case 'configuration': return 'Test Configuration'
      case 'running': return 'Running Simulation'
      case 'results': return 'Test Results'
      case 'reporting': return 'Detailed Report'
      default: return 'Stress Testing'
    }
  }

  const getPhaseDescription = () => {
    switch (currentPhase) {
      case 'setup': return 'Choose a stress test scenario or create a custom one'
      case 'configuration': return 'Configure simulation parameters and portfolio settings'
      case 'running': return 'Simulation in progress - analyzing portfolio under stress'
      case 'results': return 'Review stress test results and key metrics'
      case 'reporting': return 'Detailed analysis and recommendations'
      default: return 'Interactive portfolio stress testing system'
    }
  }

  return (
    <div className={`p-6 space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Interactive Stress Testing System
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Scenario-based portfolio stress testing with interactive controls
          </p>
        </div>
        
        <div className="flex items-center space-x-3">
          {currentPhase !== 'setup' && (
            <Button
              onClick={resetToSetup}
              variant="outline"
              size="sm"
            >
              New Test
            </Button>
          )}
          
          {testResults.length > 0 && (
            <Button
              variant="outline"
              size="sm"
              className="flex items-center space-x-2"
            >
              <DocumentArrowDownIcon className="h-4 w-4" />
              <span>Export All</span>
            </Button>
          )}
        </div>
      </div>

      {/* Progress Indicator */}
      <div className="flex items-center space-x-4 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
        <div className="flex items-center space-x-2">
          <div className={`w-3 h-3 rounded-full ${
            currentPhase === 'setup' ? 'bg-primary-600' : 
            ['configuration', 'running', 'results', 'reporting'].includes(currentPhase) ? 'bg-green-500' : 'bg-gray-300'
          }`} />
          <span className="text-sm font-medium">Setup</span>
        </div>
        
        <div className="w-8 h-px bg-gray-300" />
        
        <div className="flex items-center space-x-2">
          <div className={`w-3 h-3 rounded-full ${
            currentPhase === 'configuration' ? 'bg-primary-600' : 
            ['running', 'results', 'reporting'].includes(currentPhase) ? 'bg-green-500' : 'bg-gray-300'
          }`} />
          <span className="text-sm font-medium">Configure</span>
        </div>
        
        <div className="w-8 h-px bg-gray-300" />
        
        <div className="flex items-center space-x-2">
          <div className={`w-3 h-3 rounded-full ${
            currentPhase === 'running' ? 'bg-primary-600' : 
            ['results', 'reporting'].includes(currentPhase) ? 'bg-green-500' : 'bg-gray-300'
          }`} />
          <span className="text-sm font-medium">Simulate</span>
        </div>
        
        <div className="w-8 h-px bg-gray-300" />
        
        <div className="flex items-center space-x-2">
          <div className={`w-3 h-3 rounded-full ${
            ['results', 'reporting'].includes(currentPhase) ? 'bg-green-500' : 'bg-gray-300'
          }`} />
          <span className="text-sm font-medium">Results</span>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-center space-x-2">
            <ExclamationTriangleIcon className="h-5 w-5 text-red-600" />
            <span className="font-medium text-red-800">Error</span>
          </div>
          <p className="text-sm text-red-700 mt-1">{error}</p>
        </div>
      )}

      {/* Current Phase Card */}
      <Card>
        <CardHeader 
          title={getPhaseTitle()}
          subtitle={getPhaseDescription()}
        />
        <CardContent>
          {renderPhaseContent()}
        </CardContent>
      </Card>

      {/* Phase Navigation */}
      <div className="flex justify-between items-center">
        <div className="flex space-x-3">
          {currentPhase === 'configuration' && (
            <Button
              onClick={() => setCurrentPhase('setup')}
              variant="outline"
            >
              Back to Scenarios
            </Button>
          )}
          
          {currentPhase === 'results' && (
            <Button
              onClick={() => setCurrentPhase('configuration')}
              variant="outline"
            >
              Modify Configuration
            </Button>
          )}
          
          {currentPhase === 'reporting' && (
            <Button
              onClick={() => setCurrentPhase('results')}
              variant="outline"
            >
              Back to Results
            </Button>
          )}
        </div>
        
        <div className="flex space-x-3">
          {currentPhase === 'setup' && selectedScenario && (
            <Button
              onClick={goToConfiguration}
              className="flex items-center space-x-2"
            >
              <Cog6ToothIcon className="h-4 w-4" />
              <span>Configure Test</span>
            </Button>
          )}
          
          {currentPhase === 'configuration' && (
            <Button
              onClick={runStressTest}
              disabled={isRunning}
              className="flex items-center space-x-2"
            >
              <PlayIcon className="h-4 w-4" />
              <span>Run Stress Test</span>
            </Button>
          )}
          
          {currentPhase === 'results' && (
            <Button
              onClick={goToReporting}
              className="flex items-center space-x-2"
            >
              <ChartBarIcon className="h-4 w-4" />
              <span>View Detailed Report</span>
            </Button>
          )}
        </div>
      </div>

      {/* Test History */}
      {testResults.length > 0 && currentPhase !== 'running' && (
        <Card>
          <CardHeader title="Recent Stress Tests" />
          <CardContent>
            <div className="space-y-3">
              {testResults.slice(0, 5).map((result, index) => (
                <div key={index} className="flex items-center justify-between p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer"
                     onClick={() => {
                       setCurrentTest(result)
                       setCurrentPhase('results')
                     }}>
                  <div className="flex items-center space-x-3">
                    <div className={`w-3 h-3 rounded-full ${
                      result.results.survivabilityScore > 0.7 ? 'bg-green-500' :
                      result.results.survivabilityScore > 0.4 ? 'bg-yellow-500' : 'bg-red-500'
                    }`} />
                    <div>
                      <div className="font-medium text-gray-900">{result.scenarioName}</div>
                      <div className="text-sm text-gray-500">
                        {result.executionTime.toLocaleDateString()} • 
                        Max DD: {(result.results.maxDrawdown * 100).toFixed(1)}%
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className={`text-sm font-medium ${
                      result.results.totalReturn >= 0 ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {result.results.totalReturn >= 0 ? '+' : ''}{(result.results.totalReturn * 100).toFixed(1)}%
                    </div>
                    <div className="text-xs text-gray-500">
                      Survivability: {(result.results.survivabilityScore * 100).toFixed(0)}%
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}