import React from 'react'
import { Fragment } from 'react'
import { Dialog, Transition } from '@headlessui/react'
import { XMarkIcon } from '@heroicons/react/24/outline'
import {
  HomeIcon,
  ChartBarIcon,
  CogIcon,
  BeakerIcon,
  ShieldCheckIcon,
  GlobeAltIcon,
  DocumentTextIcon,
} from '@heroicons/react/24/outline'
import { useAppStore } from '@/stores/appStore'
import { clsx } from 'clsx'

interface SidebarProps {
  open: boolean
  onClose: () => void
}

const navigation = [
  { name: 'Dashboard', href: '#', icon: HomeIcon, current: true },
  { name: 'Strategy Studio', href: '#', icon: BeakerIcon, current: false },
  { name: 'Analytics', href: '#', icon: ChartBarIcon, current: false },
  { name: 'Market Intelligence', href: '#', icon: GlobeAltIcon, current: false },
  { name: 'Risk Management', href: '#', icon: ShieldCheckIcon, current: false },
  { name: 'Workflows', href: '#', icon: DocumentTextIcon, current: false },
  { name: 'Settings', href: '#', icon: CogIcon, current: false },
]

export function Sidebar({ open, onClose }: SidebarProps) {
  const { uiContext, updateUIContext } = useAppStore()

  const handleNavigation = (item: typeof navigation[0]) => {
    const viewMap: Record<string, string> = {
      'Dashboard': 'dashboard',
      'Strategy Studio': 'strategy_studio',
      'Analytics': 'analytics',
      'Market Intelligence': 'market_intelligence',
      'Risk Management': 'risk_management',
      'Workflows': 'workflows',
      'Settings': 'settings'
    }
    updateUIContext({ currentView: viewMap[item.name] || item.name.toLowerCase().replace(' ', '_') })
    onClose()
  }

  const SidebarContent = () => (
    <div className="flex flex-col h-full">
      {/* Logo */}
      <div className="flex items-center h-16 px-4 border-b border-neutral-200">
        <div className="flex items-center space-x-2">
          <div className="h-8 w-8 bg-primary-600 rounded-lg flex items-center justify-center">
            <span className="text-white font-bold text-sm">AI</span>
          </div>
          <span className="text-lg font-semibold text-neutral-900">
            Trading Interface
          </span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-4 py-4 space-y-1 overflow-y-auto">
        {navigation.map((item) => {
          const viewMap: Record<string, string> = {
            'Dashboard': 'dashboard',
            'Strategy Studio': 'strategy_studio',
            'Analytics': 'analytics',
            'Market Intelligence': 'market_intelligence',
            'Risk Management': 'risk_management',
            'Workflows': 'workflows',
            'Settings': 'settings'
          }
          const isActive = uiContext.currentView === viewMap[item.name]
          return (
            <button
              key={item.name}
              onClick={() => handleNavigation(item)}
              className={clsx(
                'w-full group flex items-center px-2 py-2 text-sm font-medium rounded-md transition-colors duration-200',
                isActive
                  ? 'bg-primary-100 text-primary-900'
                  : 'text-neutral-600 hover:bg-neutral-100 hover:text-neutral-900'
              )}
            >
              <item.icon
                className={clsx(
                  'mr-3 flex-shrink-0 h-5 w-5',
                  isActive ? 'text-primary-500' : 'text-neutral-400 group-hover:text-neutral-500'
                )}
              />
              {item.name}
            </button>
          )
        })}
      </nav>

      {/* Bottom section */}
      <div className="px-4 py-4 border-t border-neutral-200">
        <div className="text-xs text-neutral-500 space-y-1">
          <div>Version 0.1.0</div>
          <div>Connected to HaasOnline</div>
        </div>
      </div>
    </div>
  )

  return (
    <>
      {/* Mobile sidebar */}
      <Transition.Root show={open} as={Fragment}>
        <Dialog as="div" className="relative z-50 lg:hidden" onClose={onClose}>
          <Transition.Child
            as={Fragment}
            enter="transition-opacity ease-linear duration-300"
            enterFrom="opacity-0"
            enterTo="opacity-100"
            leave="transition-opacity ease-linear duration-300"
            leaveFrom="opacity-100"
            leaveTo="opacity-0"
          >
            <div className="fixed inset-0 bg-neutral-600 bg-opacity-75" />
          </Transition.Child>

          <div className="fixed inset-0 flex z-40">
            <Transition.Child
              as={Fragment}
              enter="transition ease-in-out duration-300 transform"
              enterFrom="-translate-x-full"
              enterTo="translate-x-0"
              leave="transition ease-in-out duration-300 transform"
              leaveFrom="translate-x-0"
              leaveTo="-translate-x-full"
            >
              <Dialog.Panel className="relative flex-1 flex flex-col max-w-xs w-full bg-white">
                <Transition.Child
                  as={Fragment}
                  enter="ease-in-out duration-300"
                  enterFrom="opacity-0"
                  enterTo="opacity-100"
                  leave="ease-in-out duration-300"
                  leaveFrom="opacity-100"
                  leaveTo="opacity-0"
                >
                  <div className="absolute top-0 right-0 -mr-12 pt-2">
                    <button
                      type="button"
                      className="ml-1 flex items-center justify-center h-10 w-10 rounded-full focus:outline-none focus:ring-2 focus:ring-inset focus:ring-white"
                      onClick={onClose}
                    >
                      <span className="sr-only">Close sidebar</span>
                      <XMarkIcon className="h-6 w-6 text-white" />
                    </button>
                  </div>
                </Transition.Child>
                <SidebarContent />
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </Dialog>
      </Transition.Root>

      {/* Desktop sidebar */}
      <div className="hidden lg:flex lg:w-64 lg:flex-col lg:fixed lg:inset-y-0">
        <div className="flex-1 flex flex-col min-h-0 border-r border-neutral-200 bg-white">
          <SidebarContent />
        </div>
      </div>
    </>
  )
}