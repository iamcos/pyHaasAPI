import React from 'react'
import { Sidebar } from './Sidebar'
import { Header } from './Header'
import { MainContent } from './MainContent'
import { OmniCommandBar } from './OmniCommandBar'
import { useAppStore } from '@/stores/appStore'

export function Layout() {
  const { } = useAppStore() // Will use uiContext later
  const [sidebarOpen, setSidebarOpen] = React.useState(false)

  return (
    <div className="h-screen flex overflow-hidden bg-neutral-50">
      {/* Sidebar */}
      <Sidebar 
        open={sidebarOpen} 
        onClose={() => setSidebarOpen(false)} 
      />

      {/* Main content area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <Header onMenuClick={() => setSidebarOpen(true)} />

        {/* Omni-Command Bar */}
        <OmniCommandBar />

        {/* Main content */}
        <MainContent />
      </div>
    </div>
  )
}