
import { Badge } from '@/components/ui'

interface StatusIndicatorProps {
  status: 'active' | 'inactive' | 'running' | 'completed' | 'failed' | 'paused' | 'error'
  size?: 'sm' | 'md' | 'lg'
  showDot?: boolean
  className?: string
}

export function StatusIndicator({
  status,
  size = 'md',
  showDot = true,
  className,
}: StatusIndicatorProps) {
  const statusConfig = {
    active: {
      variant: 'success' as const,
      label: 'Active',
    },
    inactive: {
      variant: 'default' as const,
      label: 'Inactive',
    },
    running: {
      variant: 'info' as const,
      label: 'Running',
    },
    completed: {
      variant: 'success' as const,
      label: 'Completed',
    },
    failed: {
      variant: 'danger' as const,
      label: 'Failed',
    },
    paused: {
      variant: 'warning' as const,
      label: 'Paused',
    },
    error: {
      variant: 'danger' as const,
      label: 'Error',
    },
  }

  const config = statusConfig[status]

  return (
    <Badge
      variant={config.variant}
      size={size}
      dot={showDot}
      className={className}
    >
      {config.label}
    </Badge>
  )
}