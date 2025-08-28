import React, { useState } from 'react'
import { ErrorBoundary } from './components/ErrorBoundary'
import { Header } from './components/Header'
import { Sidebar } from './components/Sidebar'
import { MainContent } from './components/MainContent'
import { OmniCommandBar } from './components/OmniCommandBar'
import { HelpButton } from './components/help/HelpButton'

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false)

  return (
    <ErrorBoundary>
      <div className="min-h-screen bg-gray-50">
        <Header onMenuClick={() => setSidebarOpen(true)} />
        <div className="flex">
          <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
          <MainContent />
        </div>
        <OmniCommandBar />
        <HelpButton />
      </div>
    </ErrorBoundary>
  )
}

export default App