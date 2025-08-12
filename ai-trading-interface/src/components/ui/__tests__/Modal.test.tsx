import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '../../../test/utils/testUtils'
import { Modal } from '../Modal'

describe('Modal Component', () => {
  it('renders when open is true', () => {
    render(
      <Modal open onClose={vi.fn()} title="Test Modal">
        Modal content
      </Modal>
    )
    
    expect(screen.getByText('Test Modal')).toBeInTheDocument()
    expect(screen.getByText('Modal content')).toBeInTheDocument()
  })

  it('does not render when open is false', () => {
    render(
      <Modal open={false} onClose={vi.fn()} title="Test Modal">
        Modal content
      </Modal>
    )
    
    expect(screen.queryByText('Test Modal')).not.toBeInTheDocument()
    expect(screen.queryByText('Modal content')).not.toBeInTheDocument()
  })

  it('calls onClose when close button is clicked', () => {
    const onClose = vi.fn()
    render(
      <Modal open onClose={onClose} title="Test Modal">
        Modal content
      </Modal>
    )
    
    const closeButton = screen.getByRole('button', { name: /close/i })
    fireEvent.click(closeButton)
    
    expect(onClose).toHaveBeenCalledTimes(1)
  })

  it('calls onClose when overlay is clicked', () => {
    const onClose = vi.fn()
    render(
      <Modal open onClose={onClose} title="Test Modal">
        Modal content
      </Modal>
    )
    
    // Click on the backdrop overlay
    const overlay = document.querySelector('.fixed.inset-0.bg-neutral-500')
    if (overlay) {
      fireEvent.click(overlay)
      expect(onClose).toHaveBeenCalledTimes(1)
    }
  })

  it('does not call onClose when modal content is clicked', () => {
    const onClose = vi.fn()
    render(
      <Modal open onClose={onClose} title="Test Modal">
        Modal content
      </Modal>
    )
    
    const modalContent = screen.getByText('Modal content')
    fireEvent.click(modalContent)
    
    expect(onClose).not.toHaveBeenCalled()
  })

  it('renders with different sizes', () => {
    const { rerender } = render(
      <Modal open onClose={vi.fn()} title="Test Modal" size="sm">
        Small modal
      </Modal>
    )
    
    // Find the dialog panel, not the dialog wrapper
    let modalPanel = document.querySelector('[data-headlessui-state="open"]')
    expect(modalPanel).toHaveClass('max-w-md')

    rerender(
      <Modal open onClose={vi.fn()} title="Test Modal" size="xl">
        Large modal
      </Modal>
    )
    
    modalPanel = document.querySelector('[data-headlessui-state="open"]')
    expect(modalPanel).toHaveClass('max-w-4xl')
  })

  it('renders with description', () => {
    render(
      <Modal open onClose={vi.fn()} title="Test Modal" description="Modal description">
        Modal content
      </Modal>
    )
    
    expect(screen.getByText('Modal description')).toBeInTheDocument()
  })

  it('handles keyboard events', () => {
    const onClose = vi.fn()
    render(
      <Modal open onClose={onClose} title="Test Modal">
        Modal content
      </Modal>
    )
    
    fireEvent.keyDown(document, { key: 'Escape' })
    expect(onClose).toHaveBeenCalledTimes(1)
  })

  it('can disable close on overlay click', () => {
    const onClose = vi.fn()
    render(
      <Modal open onClose={onClose} title="Test Modal" closeOnOverlayClick={false}>
        Modal content
      </Modal>
    )
    
    // Try to click on the backdrop overlay
    const overlay = document.querySelector('.fixed.inset-0.bg-neutral-500')
    if (overlay) {
      fireEvent.click(overlay)
      expect(onClose).not.toHaveBeenCalled()
    }
  })
})