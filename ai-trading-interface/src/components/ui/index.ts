// Core UI Components
export { Button } from './Button'
export { Input } from './Input'
export { Card, CardHeader, CardContent, CardFooter } from './Card'
export { Modal, ModalFooter } from './Modal'
export { Badge } from './Badge'
export { LoadingSpinner, LoadingOverlay } from './LoadingSpinner'
export { Alert } from './Alert'
export { Tooltip } from './Tooltip'

// Re-export commonly used types - simplified approach
export interface ButtonProps {
  variant?: 'primary' | 'secondary' | 'success' | 'danger' | 'ghost'
  size?: 'sm' | 'md' | 'lg'
  loading?: boolean
  icon?: React.ReactNode
  iconPosition?: 'left' | 'right'
}

export interface InputProps {
  label?: string
  error?: string
  helperText?: string
  leftIcon?: React.ReactNode
  rightIcon?: React.ReactNode
  variant?: 'default' | 'success' | 'error'
}