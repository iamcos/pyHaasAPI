import React from 'react'
import { Bars3Icon, BellIcon, UserCircleIcon } from '@heroicons/react/24/outline'
import { useAppStore } from '@/stores/appStore'
import { VoiceStatusDot } from '@/components/voice/VoiceIndicator'

interface HeaderProps {
  onMenuClick: () => void
}

export function Header({ onMenuClick }: HeaderProps) {
  const { currentPersona, theme, setTheme } = useAppStore()

  return (
    <header className="bg-white border-b border-neutral-200 px-4 py-3">
      <div className="flex items-center justify-between">
        {/* Left side */}
        <div className="flex items-center space-x-4">
          <button
            onClick={onMenuClick}
            className="p-2 rounded-md text-neutral-400 hover:text-neutral-500 hover:bg-neutral-100 focus-visible lg:hidden"
          >
            <span className="sr-only">Open sidebar</span>
            <Bars3Icon className="h-6 w-6" />
          </button>
          
          <div className="flex items-center space-x-2">
            <div className="h-8 w-8 bg-primary-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">AI</span>
            </div>
            <h1 className="text-xl font-semibold text-neutral-900">
              Trading Interface
            </h1>
          </div>
        </div>

        {/* Center - Status indicators */}
        <div className="hidden md:flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <div className="h-2 w-2 bg-profit-500 rounded-full animate-pulse"></div>
            <span className="text-sm text-neutral-600">Connected</span>
          </div>
          
          <div className="flex items-center space-x-2">
            <VoiceStatusDot />
            <span className="text-sm text-neutral-500">Persona:</span>
            <span className="text-sm font-medium text-neutral-700">
              {currentPersona.name}
            </span>
          </div>
        </div>

        {/* Right side */}
        <div className="flex items-center space-x-3">
          {/* Theme toggle */}
          <button
            onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')}
            className="p-2 rounded-md text-neutral-400 hover:text-neutral-500 hover:bg-neutral-100 focus-visible"
          >
            <span className="sr-only">Toggle theme</span>
            {theme === 'light' ? (
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
              </svg>
            ) : (
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
              </svg>
            )}
          </button>

          {/* Notifications */}
          <button className="p-2 rounded-md text-neutral-400 hover:text-neutral-500 hover:bg-neutral-100 focus-visible relative">
            <span className="sr-only">View notifications</span>
            <BellIcon className="h-5 w-5" />
            <span className="absolute top-1 right-1 h-2 w-2 bg-loss-500 rounded-full"></span>
          </button>

          {/* User menu */}
          <button className="p-2 rounded-md text-neutral-400 hover:text-neutral-500 hover:bg-neutral-100 focus-visible">
            <span className="sr-only">Open user menu</span>
            <UserCircleIcon className="h-6 w-6" />
          </button>
        </div>
      </div>
    </header>
  )
}