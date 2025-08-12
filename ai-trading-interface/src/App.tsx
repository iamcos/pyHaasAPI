import React from 'react'
import { ErrorBoundary } from './components/ErrorBoundary'
import { Layout } from './components/Layout'
import { useAppStore } from './stores/appStore'

function App() {
  const { isInitialized, initialize } = useAppStore()

  React.useEffect(() => {
    // Initialize the application
    initialize()
  }, [initialize])

  if (!isInitialized) {
    return (
      <div className="min-h-screen bg-neutral-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
          <p className="text-neutral-600">Initializing AI Trading Interface...</p>
        </div>
      </div>
    )
  }

  return (
    <ErrorBoundary>
      <div className="min-h-screen bg-neutral-50">
        <Layout />
      </div>
    </ErrorBoundary>
  )
}

export default App