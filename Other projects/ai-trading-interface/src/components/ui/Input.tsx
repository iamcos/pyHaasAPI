import React from 'react'
import { clsx } from 'clsx'

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
  helperText?: string
  leftIcon?: React.ReactNode
  rightIcon?: React.ReactNode
  variant?: 'default' | 'success' | 'error'
}

export function Input({
  label,
  error,
  helperText,
  leftIcon,
  rightIcon,
  variant = 'default',
  className,
  id,
  ...props
}: InputProps) {
  const inputId = id || React.useId()
  const errorId = `${inputId}-error`
  const helperTextId = `${inputId}-helper`

  const variantClasses = {
    default: 'border-neutral-300 focus:ring-primary-500 focus:border-primary-500',
    success: 'border-profit-300 focus:ring-profit-500 focus:border-profit-500',
    error: 'border-loss-300 focus:ring-loss-500 focus:border-loss-500',
  }

  const actualVariant = error ? 'error' : variant

  return (
    <div className="w-full">
      {label && (
        <label htmlFor={inputId} className="block text-sm font-medium text-neutral-700 mb-1">
          {label}
        </label>
      )}
      
      <div className="relative">
        {leftIcon && (
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <span className="text-neutral-400">{leftIcon}</span>
          </div>
        )}
        
        <input
          id={inputId}
          className={clsx(
            'block w-full rounded-md border px-3 py-2 text-sm placeholder-neutral-500 focus:outline-none focus:ring-2 focus:ring-offset-0 disabled:bg-neutral-50 disabled:text-neutral-500',
            variantClasses[actualVariant],
            leftIcon && 'pl-10',
            rightIcon && 'pr-10',
            className
          )}
          aria-describedby={clsx(
            error && errorId,
            helperText && helperTextId
          )}
          aria-invalid={error ? 'true' : 'false'}
          {...props}
        />
        
        {rightIcon && (
          <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
            <span className="text-neutral-400">{rightIcon}</span>
          </div>
        )}
      </div>
      
      {error && (
        <p id={errorId} className="mt-1 text-sm text-loss-600">
          {error}
        </p>
      )}
      
      {helperText && !error && (
        <p id={helperTextId} className="mt-1 text-sm text-neutral-500">
          {helperText}
        </p>
      )}
    </div>
  )
}