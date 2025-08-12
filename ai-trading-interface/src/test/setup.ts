import '@testing-library/jest-dom'
import { vi } from 'vitest'

// Mock IndexedDB
const mockIDBRequest = {
  result: null,
  error: null,
  onsuccess: null,
  onerror: null,
  readyState: 'done',
  source: null,
  transaction: null,
}

const mockIDBDatabase = {
  close: vi.fn(),
  createObjectStore: vi.fn(),
  deleteObjectStore: vi.fn(),
  transaction: vi.fn(),
  version: 1,
  name: 'test-db',
  objectStoreNames: [],
  onabort: null,
  onclose: null,
  onerror: null,
  onversionchange: null,
}

const mockIDBTransaction = {
  abort: vi.fn(),
  commit: vi.fn(),
  objectStore: vi.fn(),
  db: mockIDBDatabase,
  durability: 'default',
  mode: 'readonly',
  objectStoreNames: [],
  onabort: null,
  oncomplete: null,
  onerror: null,
}

const mockIDBObjectStore = {
  add: vi.fn().mockReturnValue(mockIDBRequest),
  clear: vi.fn().mockReturnValue(mockIDBRequest),
  count: vi.fn().mockReturnValue(mockIDBRequest),
  createIndex: vi.fn(),
  delete: vi.fn().mockReturnValue(mockIDBRequest),
  deleteIndex: vi.fn(),
  get: vi.fn().mockReturnValue(mockIDBRequest),
  getAll: vi.fn().mockReturnValue(mockIDBRequest),
  getAllKeys: vi.fn().mockReturnValue(mockIDBRequest),
  getKey: vi.fn().mockReturnValue(mockIDBRequest),
  index: vi.fn(),
  openCursor: vi.fn().mockReturnValue(mockIDBRequest),
  openKeyCursor: vi.fn().mockReturnValue(mockIDBRequest),
  put: vi.fn().mockReturnValue(mockIDBRequest),
  autoIncrement: false,
  indexNames: [],
  keyPath: null,
  name: 'test-store',
  transaction: mockIDBTransaction,
}

mockIDBTransaction.objectStore.mockReturnValue(mockIDBObjectStore)
mockIDBDatabase.transaction.mockReturnValue(mockIDBTransaction)

global.indexedDB = {
  open: vi.fn().mockReturnValue({
    ...mockIDBRequest,
    result: mockIDBDatabase,
  }),
  deleteDatabase: vi.fn().mockReturnValue(mockIDBRequest),
  databases: vi.fn().mockResolvedValue([]),
  cmp: vi.fn(),
}

// Mock WebSocket
global.WebSocket = vi.fn().mockImplementation(() => ({
  close: vi.fn(),
  send: vi.fn(),
  addEventListener: vi.fn(),
  removeEventListener: vi.fn(),
  readyState: 1,
  CONNECTING: 0,
  OPEN: 1,
  CLOSING: 2,
  CLOSED: 3,
}))

// Mock Web Speech API
global.SpeechRecognition = vi.fn().mockImplementation(() => ({
  start: vi.fn(),
  stop: vi.fn(),
  abort: vi.fn(),
  addEventListener: vi.fn(),
  removeEventListener: vi.fn(),
  continuous: false,
  interimResults: false,
  lang: 'en-US',
  maxAlternatives: 1,
  serviceURI: '',
}))

global.webkitSpeechRecognition = global.SpeechRecognition

// Mock ResizeObserver
global.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}))

// Mock matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
})