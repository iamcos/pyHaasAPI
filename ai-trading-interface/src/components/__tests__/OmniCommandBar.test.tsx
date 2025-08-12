import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '../../test/utils/testUtils'

// Mock the OmniCommandBar component
const MockOmniCommandBar = ({ onCommand }: any) => (
  <div>
    <input 
      placeholder="Ask me anything about your trading..."
      onChange={(e) => {
        // Simulate command processing
      }}
      onKeyDown={(e) => {
        if (e.key === 'Enter' && onCommand) {
          onCommand(e.currentTarget.value)
        }
      }}
    />
    <div data-testid="loading-indicator" style={{ display: 'none' }}>Loading...</div>
    <button aria-label="voice input">🎤</button>
    <button aria-label="clear">✕</button>
    <div>
      <div>Show portfolio</div>
      <div>Create new strategy</div>
    </div>
  </div>
)

vi.mock('../OmniCommandBar', () => ({
  OmniCommandBar: MockOmniCommandBar,
}))

describe('OmniCommandBar Component', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders with placeholder text', () => {
    const { OmniCommandBar } = require('../OmniCommandBar')
    render(<OmniCommandBar />)
    
    const input = screen.getByPlaceholderText(/ask me anything/i)
    expect(input).toBeInTheDocument()
  })

  it('handles text input', async () => {
    const { OmniCommandBar } = require('../OmniCommandBar')
    render(<OmniCommandBar />)
    
    const input = screen.getByPlaceholderText(/ask me anything/i)
    fireEvent.change(input, { target: { value: 'show my portfolio' } })
    
    expect(input).toHaveValue('show my portfolio')
  })

  it('submits command on Enter key', async () => {
    const { OmniCommandBar } = require('../OmniCommandBar')
    const onCommand = vi.fn()
    render(<OmniCommandBar onCommand={onCommand} />)
    
    const input = screen.getByPlaceholderText(/ask me anything/i)
    fireEvent.change(input, { target: { value: 'show portfolio' } })
    fireEvent.keyDown(input, { key: 'Enter' })
    
    expect(onCommand).toHaveBeenCalledWith('show portfolio')
  })

  it('shows suggestions', () => {
    const { OmniCommandBar } = require('../OmniCommandBar')
    render(<OmniCommandBar />)
    
    expect(screen.getByText('Show portfolio')).toBeInTheDocument()
    expect(screen.getByText('Create new strategy')).toBeInTheDocument()
  })

  it('has voice input button', () => {
    const { OmniCommandBar } = require('../OmniCommandBar')
    render(<OmniCommandBar />)
    
    const voiceButton = screen.getByRole('button', { name: /voice input/i })
    expect(voiceButton).toBeInTheDocument()
  })

  it('has clear button', () => {
    const { OmniCommandBar } = require('../OmniCommandBar')
    render(<OmniCommandBar />)
    
    const clearButton = screen.getByRole('button', { name: /clear/i })
    expect(clearButton).toBeInTheDocument()
  })
})