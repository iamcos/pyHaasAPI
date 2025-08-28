#!/usr/bin/env node

/**
 * Integration Test Runner
 * 
 * This script runs integration tests that require external services:
 * - MCP Server (port 8080)
 * - RAG Service (port 8081) 
 * - WebSocket Server (port 8082)
 * 
 * Usage:
 * npm run test:integration
 * npm run test:integration -- --service=mcp
 * npm run test:integration -- --service=rag
 * npm run test:integration -- --service=websocket
 */

import { spawn } from 'child_process'
import { existsSync } from 'fs'
import { join } from 'path'

interface ServiceConfig {
  name: string
  port: number
  healthEndpoint: string
  testFile: string
}

const services: ServiceConfig[] = [
  {
    name: 'MCP Server',
    port: 8080,
    healthEndpoint: 'http://localhost:8080/health',
    testFile: 'mcpIntegration.test.ts',
  },
  {
    name: 'RAG Service',
    port: 8081,
    healthEndpoint: 'http://localhost:8081/health',
    testFile: 'ragIntegration.test.ts',
  },
  {
    name: 'WebSocket Server',
    port: 8082,
    healthEndpoint: 'ws://localhost:8082/ws',
    testFile: 'websocketIntegration.test.ts',
  },
]

async function checkServiceHealth(service: ServiceConfig): Promise<boolean> {
  try {
    if (service.healthEndpoint.startsWith('ws://')) {
      // WebSocket health check
      return new Promise((resolve) => {
        const ws = new WebSocket(service.healthEndpoint)
        const timeout = setTimeout(() => {
          ws.close()
          resolve(false)
        }, 3000)

        ws.onopen = () => {
          clearTimeout(timeout)
          ws.close()
          resolve(true)
        }

        ws.onerror = () => {
          clearTimeout(timeout)
          resolve(false)
        }
      })
    } else {
      // HTTP health check
      const response = await fetch(service.healthEndpoint, {
        method: 'GET',
        signal: AbortSignal.timeout(3000),
      })
      return response.ok
    }
  } catch (error) {
    return false
  }
}

async function runTests(testFiles: string[]): Promise<boolean> {
  return new Promise((resolve) => {
    const testPattern = testFiles.length > 0 
      ? testFiles.map(f => `src/test/integration/${f}`).join(' ')
      : 'src/test/integration/*.test.ts'

    const vitestProcess = spawn('npx', ['vitest', 'run', ...testPattern.split(' ')], {
      stdio: 'inherit',
      shell: true,
    })

    vitestProcess.on('close', (code) => {
      resolve(code === 0)
    })

    vitestProcess.on('error', (error) => {
      console.error('Failed to start test process:', error)
      resolve(false)
    })
  })
}

function printServiceStatus(service: ServiceConfig, available: boolean) {
  const status = available ? '✅ Available' : '❌ Unavailable'
  const port = service.port ? `:${service.port}` : ''
  console.log(`  ${service.name}${port}: ${status}`)
}

function printUsage() {
  console.log(`
Integration Test Runner

Usage:
  npm run test:integration                    # Run all integration tests
  npm run test:integration -- --service=mcp  # Run only MCP integration tests
  npm run test:integration -- --service=rag  # Run only RAG integration tests
  npm run test:integration -- --service=ws   # Run only WebSocket integration tests

Services:
  mcp        - MCP Server integration tests (port 8080)
  rag        - RAG Service integration tests (port 8081)  
  ws         - WebSocket Server integration tests (port 8082)

Note: Tests will be skipped for unavailable services.
`)
}

async function main() {
  const args = process.argv.slice(2)
  
  if (args.includes('--help') || args.includes('-h')) {
    printUsage()
    return
  }

  // Parse service filter
  const serviceArg = args.find(arg => arg.startsWith('--service='))
  const serviceFilter = serviceArg ? serviceArg.split('=')[1] : null

  let servicesToTest = services
  if (serviceFilter) {
    const filterMap: Record<string, string> = {
      'mcp': 'mcpIntegration.test.ts',
      'rag': 'ragIntegration.test.ts', 
      'ws': 'websocketIntegration.test.ts',
      'websocket': 'websocketIntegration.test.ts',
    }

    const testFile = filterMap[serviceFilter]
    if (!testFile) {
      console.error(`Unknown service: ${serviceFilter}`)
      printUsage()
      process.exit(1)
    }

    servicesToTest = services.filter(s => s.testFile === testFile)
  }

  console.log('🔍 Checking service availability...\n')

  // Check service health
  const serviceStatus = await Promise.all(
    servicesToTest.map(async (service) => {
      const available = await checkServiceHealth(service)
      printServiceStatus(service, available)
      return { service, available }
    })
  )

  console.log()

  // Determine which tests to run
  const availableServices = serviceStatus
    .filter(({ available }) => available)
    .map(({ service }) => service)

  const unavailableServices = serviceStatus
    .filter(({ available }) => !available)
    .map(({ service }) => service)

  if (unavailableServices.length > 0) {
    console.log('⚠️  Some services are unavailable. Tests for these services will be skipped:')
    unavailableServices.forEach(service => {
      console.log(`   - ${service.name}`)
    })
    console.log()
  }

  if (availableServices.length === 0) {
    console.log('❌ No services are available. Cannot run integration tests.')
    console.log('\nTo run integration tests, please ensure the required services are running:')
    servicesToTest.forEach(service => {
      console.log(`   - ${service.name} on port ${service.port}`)
    })
    process.exit(1)
  }

  console.log('🧪 Running integration tests...\n')

  // Run tests for available services
  const testFiles = availableServices.map(service => service.testFile)
  const success = await runTests(testFiles)

  if (success) {
    console.log('\n✅ All integration tests passed!')
  } else {
    console.log('\n❌ Some integration tests failed.')
    process.exit(1)
  }
}

// Handle unhandled promise rejections
process.on('unhandledRejection', (reason, promise) => {
  console.error('Unhandled Rejection at:', promise, 'reason:', reason)
  process.exit(1)
})

// Handle uncaught exceptions
process.on('uncaughtException', (error) => {
  console.error('Uncaught Exception:', error)
  process.exit(1)
})

if (require.main === module) {
  main().catch((error) => {
    console.error('Integration test runner failed:', error)
    process.exit(1)
  })
}

export { main as runIntegrationTests }