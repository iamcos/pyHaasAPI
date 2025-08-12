import React, { ReactElement } from 'react'
import { render, RenderOptions } from '@testing-library/react'
import { vi } from 'vitest'

// Mock Zustand stores
const mockAppStore = {
  currentView: 'dashboard',
  setCurrentView: vi.fn(),
  sidebarOpen: true,
  setSidebarOpen: vi.fn(),
  theme: 'dark',
  setTheme: vi.fn(),
}

const mockTradingStore = {
  markets: [],
  portfolio: null,
  bots: [],
  labs: [],
  setMarkets: vi.fn(),
  setPortfolio: vi.fn(),
  setBots: vi.fn(),
  setLabs: vi.fn(),
  addBot: vi.fn(),
  updateBot: vi.fn(),
  removeBot: vi.fn(),
}

const mockAIStore = {
  chainOfThought: [],
  currentReasoning: null,
  addChainOfThoughtStep: vi.fn(),
  setCurrentReasoning: vi.fn(),
  clearChainOfThought: vi.fn(),
}

const mockWorkflowStore = {
  activeWorkflows: [],
  workflowHistory: [],
  templates: [],
  addWorkflow: vi.fn(),
  updateWorkflow: vi.fn(),
  removeWorkflow: vi.fn(),
  setTemplates: vi.fn(),
}

// Mock the stores
vi.mock('../../stores/appStore', () => ({
  useAppStore: () => mockAppStore,
}))

vi.mock('../../stores/tradingStore', () => ({
  useTradingStore: () => mockTradingStore,
}))

vi.mock('../../stores/aiStore', () => ({
  useAIStore: () => mockAIStore,
}))

vi.mock('../../stores/workflowStore', () => ({
  useWorkflowStore: () => mockWorkflowStore,
}))

// Test wrapper component
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return <div data-testid="test-wrapper">{children}</div>
}

// Custom render function
const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) => render(ui, { wrapper: TestWrapper, ...options })

// Re-export everything
export * from '@testing-library/react'
export { customRender as render }

// Test utilities
export const waitForNextTick = () => new Promise(resolve => setTimeout(resolve, 0))

export const mockIntersectionObserver = () => {
  const mockIntersectionObserver = vi.fn()
  mockIntersectionObserver.mockReturnValue({
    observe: () => null,
    unobserve: () => null,
    disconnect: () => null,
  })
  window.IntersectionObserver = mockIntersectionObserver
  window.IntersectionObserverEntry = vi.fn()
}

export const mockScrollIntoView = () => {
  Element.prototype.scrollIntoView = vi.fn()
}

// Store mocks for direct access in tests
export const storeMocks = {
  appStore: mockAppStore,
  tradingStore: mockTradingStore,
  aiStore: mockAIStore,
  workflowStore: mockWorkflowStore,
}

// Reset all mocks
export const resetAllMocks = () => {
  Object.values(storeMocks).forEach(store => {
    Object.values(store).forEach(fn => {
      if (typeof fn === 'function' && 'mockReset' in fn) {
        fn.mockReset()
      }
    })
  })
}