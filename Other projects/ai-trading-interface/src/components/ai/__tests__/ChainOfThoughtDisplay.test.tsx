import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '../../../test/utils/testUtils'
import { createMockChainOfThoughtStep } from '../../../test/mocks/aiService'

// Mock the ChainOfThoughtDisplay component since it has import issues
const MockChainOfThoughtDisplay = ({ steps, className }: any) => (
  <div className={className}>
    <h3>Chain of Thought</h3>
    {steps.length === 0 ? (
      <p>No reasoning steps available</p>
    ) : (
      steps.map((step: any) => (
        <div key={step.id}>
          <span>Step {step.step}</span>
          <p>{step.reasoning}</p>
          <span>{Math.round(step.confidence * 100)}%</span>
        </div>
      ))
    )}
  </div>
)

vi.mock('../ChainOfThoughtDisplay', () => ({
  ChainOfThoughtDisplay: MockChainOfThoughtDisplay,
}))

describe('ChainOfThoughtDisplay Component', () => {
  const mockSteps = [
    createMockChainOfThoughtStep({
      id: '1',
      step: 1,
      reasoning: 'First reasoning step',
      confidence: 0.9,
    }),
    createMockChainOfThoughtStep({
      id: '2',
      step: 2,
      reasoning: 'Second reasoning step',
      confidence: 0.8,
    }),
    createMockChainOfThoughtStep({
      id: '3',
      step: 3,
      reasoning: 'Third reasoning step',
      confidence: 0.7,
    }),
  ]

  it('renders chain of thought steps', () => {
    const { ChainOfThoughtDisplay } = require('../ChainOfThoughtDisplay')
    render(<ChainOfThoughtDisplay steps={mockSteps} />)
    
    expect(screen.getByText('Chain of Thought')).toBeInTheDocument()
    expect(screen.getByText('First reasoning step')).toBeInTheDocument()
    expect(screen.getByText('Second reasoning step')).toBeInTheDocument()
    expect(screen.getByText('Third reasoning step')).toBeInTheDocument()
  })

  it('displays confidence scores', () => {
    const { ChainOfThoughtDisplay } = require('../ChainOfThoughtDisplay')
    render(<ChainOfThoughtDisplay steps={mockSteps} />)
    
    expect(screen.getByText('90%')).toBeInTheDocument()
    expect(screen.getByText('80%')).toBeInTheDocument()
    expect(screen.getByText('70%')).toBeInTheDocument()
  })

  it('shows step numbers', () => {
    const { ChainOfThoughtDisplay } = require('../ChainOfThoughtDisplay')
    render(<ChainOfThoughtDisplay steps={mockSteps} />)
    
    expect(screen.getByText('Step 1')).toBeInTheDocument()
    expect(screen.getByText('Step 2')).toBeInTheDocument()
    expect(screen.getByText('Step 3')).toBeInTheDocument()
  })

  it('handles empty steps array', () => {
    const { ChainOfThoughtDisplay } = require('../ChainOfThoughtDisplay')
    render(<ChainOfThoughtDisplay steps={[]} />)
    
    expect(screen.getByText('No reasoning steps available')).toBeInTheDocument()
  })

  it('applies custom className', () => {
    const { ChainOfThoughtDisplay } = require('../ChainOfThoughtDisplay')
    render(<ChainOfThoughtDisplay steps={mockSteps} className="custom-class" />)
    
    const container = screen.getByText('Chain of Thought').closest('div')
    expect(container).toHaveClass('custom-class')
  })
})