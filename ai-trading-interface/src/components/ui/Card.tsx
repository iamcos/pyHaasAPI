import React from 'react'
import { clsx } from 'clsx'

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'elevated' | 'outlined'
  padding?: 'none' | 'sm' | 'md' | 'lg'
  hover?: boolean
}

export function Card({
  children,
  variant = 'default',
  padding = 'md',
  hover = false,
  className,
  ...props
}: CardProps) {
  const variantClasses = {
    default: 'bg-white border border-neutral-200 shadow-sm',
    elevated: 'bg-white shadow-lg border border-neutral-100',
    outlined: 'bg-white border-2 border-neutral-200',
  }

  const paddingClasses = {
    none: '',
    sm: 'p-3',
    md: 'p-4',
    lg: 'p-6',
  }

  return (
    <div
      className={clsx(
        'rounded-lg',
        variantClasses[variant],
        paddingClasses[padding],
        hover && 'transition-shadow duration-200 hover:shadow-md',
        className
      )}
      {...props}
    >
      {children}
    </div>
  )
}

interface CardHeaderProps extends React.HTMLAttributes<HTMLDivElement> {
  title?: string
  subtitle?: string
  action?: React.ReactNode
}

export function CardHeader({
  title,
  subtitle,
  action,
  children,
  className,
  ...props
}: CardHeaderProps) {
  return (
    <div className={clsx('flex items-center justify-between mb-4', className)} {...props}>
      <div className="flex-1">
        {title && (
          <h3 className="text-lg font-medium text-neutral-900">{title}</h3>
        )}
        {subtitle && (
          <p className="text-sm text-neutral-500 mt-1">{subtitle}</p>
        )}
        {children}
      </div>
      {action && <div className="flex-shrink-0 ml-4">{action}</div>}
    </div>
  )
}

interface CardContentProps extends React.HTMLAttributes<HTMLDivElement> {}

export function CardContent({ children, className, ...props }: CardContentProps) {
  return (
    <div className={clsx('text-neutral-700', className)} {...props}>
      {children}
    </div>
  )
}

interface CardFooterProps extends React.HTMLAttributes<HTMLDivElement> {}

export function CardFooter({ children, className, ...props }: CardFooterProps) {
  return (
    <div className={clsx('mt-4 pt-4 border-t border-neutral-200', className)} {...props}>
      {children}
    </div>
  )
}