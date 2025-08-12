import React from 'react'
import { clsx } from 'clsx'
import {
  CheckCircleIcon,
  ExclamationTriangleIcon,
  XCircleIcon,
  InformationCircleIcon,
  XMarkIcon,
} from '@heroicons/react/24/outline'

interface AlertProps {
  variant?: 'success' | 'warning' | 'error' | 'info'
  title?: string
  message: string
  dismissible?: boolean
  onDismiss?: () => void
  className?: string
}

export function Alert({
  variant = 'info',
  title,
  message,
  dismissible = false,
  onDismiss,
  className,
}: AlertProps) {
  const variantConfig = {
    success: {
      containerClass: 'bg-profit-50 border-profit-200',
      iconClass: 'text-profit-400',
      titleClass: 'text-profit-800',
      messageClass: 'text-profit-700',
      icon: CheckCircleIcon,
    },
    warning: {
      containerClass: 'bg-yellow-50 border-yellow-200',
      iconClass: 'text-yellow-400',
      titleClass: 'text-yellow-800',
      messageClass: 'text-yellow-700',
      icon: ExclamationTriangleIcon,
    },
    error: {
      containerClass: 'bg-loss-50 border-loss-200',
      iconClass: 'text-loss-400',
      titleClass: 'text-loss-800',
      messageClass: 'text-loss-700',
      icon: XCircleIcon,
    },
    info: {
      containerClass: 'bg-primary-50 border-primary-200',
      iconClass: 'text-primary-400',
      titleClass: 'text-primary-800',
      messageClass: 'text-primary-700',
      icon: InformationCircleIcon,
    },
  }

  const config = variantConfig[variant]
  const Icon = config.icon

  return (
    <div
      className={clsx(
        'rounded-md border p-4',
        config.containerClass,
        className
      )}
    >
      <div className="flex">
        <div className="flex-shrink-0">
          <Icon className={clsx('h-5 w-5', config.iconClass)} />
        </div>
        <div className="ml-3 flex-1">
          {title && (
            <h3 className={clsx('text-sm font-medium', config.titleClass)}>
              {title}
            </h3>
          )}
          <div className={clsx('text-sm', title ? 'mt-2' : '', config.messageClass)}>
            {message}
          </div>
        </div>
        {dismissible && onDismiss && (
          <div className="ml-auto pl-3">
            <div className="-mx-1.5 -my-1.5">
              <button
                type="button"
                className={clsx(
                  'inline-flex rounded-md p-1.5 focus:outline-none focus:ring-2 focus:ring-offset-2',
                  config.iconClass,
                  'hover:bg-opacity-20 focus:ring-offset-2'
                )}
                onClick={onDismiss}
              >
                <span className="sr-only">Dismiss</span>
                <XMarkIcon className="h-5 w-5" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}