import { describe, it, expect } from 'vitest'
import { render, screen } from '../../../test/utils/testUtils'
import { Card } from '../Card'

describe('Card Component', () => {
  it('renders with default props', () => {
    render(<Card>Card content</Card>)
    
    const card = screen.getByText('Card content')
    expect(card).toBeInTheDocument()
    expect(card).toHaveClass('bg-white', 'rounded-lg', 'shadow-sm')
  })

  it('renders with different variants', () => {
    const { rerender } = render(<Card variant="elevated">Elevated card</Card>)
    expect(screen.getByText('Elevated card')).toHaveClass('shadow-lg')

    rerender(<Card variant="outlined">Outlined card</Card>)
    expect(screen.getByText('Outlined card')).toHaveClass('border-2')
  })

  it('renders with different padding', () => {
    const { rerender } = render(<Card padding="sm">Small padding</Card>)
    expect(screen.getByText('Small padding')).toHaveClass('p-3')

    rerender(<Card padding="lg">Large padding</Card>)
    expect(screen.getByText('Large padding')).toHaveClass('p-6')

    rerender(<Card padding="none">No padding</Card>)
    expect(screen.getByText('No padding')).not.toHaveClass('p-4')
  })

  it('applies hover effect when hover prop is true', () => {
    render(<Card hover>Hoverable card</Card>)
    
    const card = screen.getByText('Hoverable card')
    expect(card).toHaveClass('hover:shadow-md', 'transition-shadow')
  })

  it('applies custom className', () => {
    render(<Card className="custom-class">Custom card</Card>)
    
    expect(screen.getByText('Custom card')).toHaveClass('custom-class')
  })

  it('applies custom className', () => {
    render(<Card className="custom-class">Custom card</Card>)
    
    expect(screen.getByText('Custom card')).toHaveClass('custom-class')
  })
})