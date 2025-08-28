import { clsx } from 'clsx'
import { ArrowUpIcon, ArrowDownIcon } from '@heroicons/react/24/solid'

interface ProfitLossIndicatorProps {
  value: number
  percentage?: number
  showIcon?: boolean
  showSign?: boolean
  size?: 'sm' | 'md' | 'lg'
  className?: string
}

export function ProfitLossIndicator({
  value,
  percentage,
  showIcon = true,
  showSign = true,
  size = 'md',
  className,
}: ProfitLossIndicatorProps) {
  const isProfit = value > 0
  const isLoss = value < 0
  const isNeutral = value === 0

  const sizeClasses = {
    sm: 'text-sm',
    md: 'text-base',
    lg: 'text-lg',
  }

  const iconSizeClasses = {
    sm: 'h-3 w-3',
    md: 'h-4 w-4',
    lg: 'h-5 w-5',
  }

  const colorClass = isProfit 
    ? 'text-profit-600' 
    : isLoss 
    ? 'text-loss-600' 
    : 'text-neutral-600'

  const formatValue = (val: number) => {
    const sign = showSign && val > 0 ? '+' : ''
    return `${sign}${val.toLocaleString('en-US', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })}`
  }

  const formatPercentage = (pct: number) => {
    const sign = showSign && pct > 0 ? '+' : ''
    return `${sign}${pct.toFixed(2)}%`
  }

  return (
    <div className={clsx('inline-flex items-center space-x-1', className)}>
      {showIcon && !isNeutral && (
        <span className={colorClass}>
          {isProfit ? (
            <ArrowUpIcon className={iconSizeClasses[size]} />
          ) : (
            <ArrowDownIcon className={iconSizeClasses[size]} />
          )}
        </span>
      )}
      <span className={clsx('font-medium', colorClass, sizeClasses[size])}>
        ${formatValue(Math.abs(value))}
      </span>
      {percentage !== undefined && (
        <span className={clsx('font-medium', colorClass, sizeClasses[size])}>
          ({formatPercentage(percentage)})
        </span>
      )}
    </div>
  )
}