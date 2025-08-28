import React from 'react'
import { clsx } from 'clsx'

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: 'default' | 'success' | 'warning' | 'danger' | 'info'
  size?: 'sm' | 'md' | 'lg'
  dot?: boolean
}

export function Badge({
  children,
  variant = 'default',
  size = 'md',
  dot = false,
  className,
  ...props
}: BadgeProps) {
  const variantClasses = {
    default: 'bg-neutral-100 text-neutral-800',
    success: 'bg-profit-100 text-profit-800',
    warning: 'bg-yellow-100 text-yellow-800',
    danger: 'bg-loss-100 text-loss-800',
    info: 'bg-primary-100 text-primary-800',
  }

  const sizeClasses = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-0.5 text-sm',
    lg: 'px-3 py-1 text-sm',
  }

  const dotClasses = {
    default: 'bg-neutral-400',
    success: 'bg-profit-400',
    warning: 'bg-yellow-400',
    danger: 'bg-loss-400',
    info: 'bg-primary-400',
  }

  return (
    <span
      className={clsx(
        'inline-flex items-center font-medium rounded-full',
        variantClasses[variant],
        sizeClasses[size],
        className
      )}
      {...props}
    >
      {dot && (
        <span
          className={clsx(
            'w-1.5 h-1.5 rounded-full mr-1.5',
            dotClasses[variant]
          )}
        />
      )}
      {children}
    </span>
  )
}