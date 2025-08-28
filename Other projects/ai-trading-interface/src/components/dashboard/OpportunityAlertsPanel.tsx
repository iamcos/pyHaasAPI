import React, { useState } from 'react'
import { 
  ExclamationTriangleIcon,
  LightBulbIcon,
  TrendingUpIcon,
  ArrowsRightLeftIcon,
  ChartBarIcon,
  ClockIcon,
  FireIcon
} from '@heroicons/react/24/outline'
import { Card, CardHeader, CardContent, Button } from '@/components/ui'
import type { OpportunityAlert } from '@/services/dashboardService'

interface OpportunityAlertsPanelProps {
  opportunities: OpportunityAlert[]
  loading?: boolean
}

export function OpportunityAlertsPanel({ opportunities, loading = false }: OpportunityAlertsPanelProps) {
  const [filter, setFilter] = useState<'all' | 'high' | 'critical'>('all')
  const [expandedAlert, setExpandedAlert] = useState<string | null>(null)

  if (loading) {
    return (
      <Card>
        <CardHeader title="Opportunity Alerts" />
        <CardContent>
          <div className="animate-pulse space-y-3">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="h-16 bg-gray-200 rounded"></div>
            ))}
          </div>
        </CardContent>
      </Card>
    )
  }

  const getOpportunityIcon = (type: string) => {
    switch (type) {
      case 'arbitrage': return ArrowsRightLeftIcon
      case 'breakout': return TrendingUpIcon
      case 'reversal': return ChartBarIcon
      case 'momentum': return FireIcon
      case 'correlation': return ExclamationTriangleIcon
      default: return LightBulbIcon
    }
  }

  const getUrgencyColor = (urgency: string) => {
    switch (urgency) {
      case 'critical': return 'text-red-600 bg-red-50 border-red-200'
      case 'high': return 'text-orange-600 bg-orange-50 border-orange-200'
      case 'medium': return 'text-yellow-600 bg-yellow-50 border-yellow-200'
      default: return 'text-blue-600 bg-blue-50 border-blue-200'
    }
  }

  const getUrgencyBadgeColor = (urgency: string) => {
    switch (urgency) {
      case 'critical': return 'bg-red-100 text-red-800'
      case 'high': return 'bg-orange-100 text-orange-800'
      case 'medium': return 'bg-yellow-100 text-yellow-800'
      default: return 'bg-blue-100 text-blue-800'
    }
  }

  const filteredOpportunities = opportunities.filter(opp => {
    if (filter === 'all') return true
    return opp.urgency === filter
  })

  const urgencyCounts = {
    critical: opportunities.filter(o => o.urgency === 'critical').length,
    high: opportunities.filter(o => o.urgency === 'high').length,
    medium: opportunities.filter(o => o.urgency === 'medium').length,
    low: opportunities.filter(o => o.urgency === 'low').length
  }

  const getTimeRemaining = (expiresAt: Date) => {
    const now = new Date()
    const diff = expiresAt.getTime() - now.getTime()
    
    if (diff <= 0) return 'Expired'
    
    const minutes = Math.floor(diff / 60000)
    const hours = Math.floor(minutes / 60)
    
    if (hours > 0) return `${hours}h ${minutes % 60}m`
    return `${minutes}m`
  }

  return (
    <Card>
      <CardHeader 
        title="Opportunity Alerts"
        subtitle={`${opportunities.length} active opportunities`}
        action={
          <div className="flex space-x-1">
            {[
              { key: 'all' as const, label: 'All', count: opportunities.length },
              { key: 'high' as const, label: 'High', count: urgencyCounts.high },
              { key: 'critical' as const, label: 'Critical', count: urgencyCounts.critical }
            ].map(filterOption => (
              <button
                key={filterOption.key}
                onClick={() => setFilter(filterOption.key)}
                className={`flex items-center space-x-1 px-2 py-1 text-xs font-medium rounded transition-colors ${
                  filter === filterOption.key
                    ? 'bg-primary-100 text-primary-700'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                <span>{filterOption.label}</span>
                {filterOption.count > 0 && (
                  <span className="bg-gray-200 text-gray-700 px-1 rounded-full text-xs">
                    {filterOption.count}
                  </span>
                )}
              </button>
            ))}
          </div>
        }
      />
      
      <CardContent>
        {filteredOpportunities.length === 0 ? (
          <div className="text-center py-8">
            <LightBulbIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-sm font-medium text-gray-900 mb-2">
              No Opportunities Found
            </h3>
            <p className="text-xs text-gray-600">
              {filter === 'all' 
                ? "We're scanning the markets for opportunities..."
                : `No ${filter} priority opportunities at the moment.`
              }
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {filteredOpportunities.map((opportunity) => {
              const OpportunityIcon = getOpportunityIcon(opportunity.type)
              const isExpanded = expandedAlert === opportunity.id
              const timeRemaining = getTimeRemaining(opportunity.expiresAt)
              const isExpiring = opportunity.expiresAt.getTime() - Date.now() < 300000 // 5 minutes
              
              return (
                <div 
                  key={opportunity.id} 
                  className={`border rounded-lg overflow-hidden ${getUrgencyColor(opportunity.urgency)}`}
                >
                  <button
                    onClick={() => setExpandedAlert(isExpanded ? null : opportunity.id)}
                    className="w-full p-3 text-left hover:bg-opacity-50 transition-colors"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-start space-x-3 flex-1">
                        <OpportunityIcon className="h-5 w-5 mt-0.5 flex-shrink-0" />
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center space-x-2 mb-1">
                            <h4 className="text-sm font-medium truncate">
                              {opportunity.title}
                            </h4>
                            <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${getUrgencyBadgeColor(opportunity.urgency)}`}>
                              {opportunity.urgency}
                            </span>
                          </div>
                          
                          <p className="text-xs opacity-90 mb-2">
                            {opportunity.description}
                          </p>
                          
                          <div className="flex items-center space-x-4 text-xs">
                            <span className="font-medium">
                              {opportunity.market}
                            </span>
                            <span>
                              {(opportunity.confidence * 100).toFixed(0)}% confidence
                            </span>
                            <div className="flex items-center space-x-1">
                              <ClockIcon className="h-3 w-3" />
                              <span className={isExpiring ? 'text-red-600 font-medium' : ''}>
                                {timeRemaining}
                              </span>
                            </div>
                          </div>
                        </div>
                      </div>
                      
                      <div className="text-right ml-3">
                        <div className="text-sm font-medium">
                          +{opportunity.estimatedReturn.toFixed(1)}%
                        </div>
                        <div className="text-xs opacity-75">
                          Risk: {opportunity.riskLevel}/10
                        </div>
                      </div>
                    </div>
                  </button>
                  
                  {isExpanded && (
                    <div className="px-3 pb-3 border-t border-current border-opacity-20">
                      <div className="pt-3 space-y-3">
                        {/* Detailed metrics */}
                        <div className="grid grid-cols-2 gap-4 text-xs">
                          <div>
                            <span className="opacity-75">Type:</span>
                            <span className="ml-2 font-medium capitalize">
                              {opportunity.type.replace('_', ' ')}
                            </span>
                          </div>
                          <div>
                            <span className="opacity-75">Market:</span>
                            <span className="ml-2 font-medium">
                              {opportunity.market}
                            </span>
                          </div>
                          <div>
                            <span className="opacity-75">Confidence:</span>
                            <span className="ml-2 font-medium">
                              {(opportunity.confidence * 100).toFixed(0)}%
                            </span>
                          </div>
                          <div>
                            <span className="opacity-75">Risk Level:</span>
                            <span className="ml-2 font-medium">
                              {opportunity.riskLevel}/10
                            </span>
                          </div>
                        </div>
                        
                        {/* Actions */}
                        {opportunity.actions.length > 0 && (
                          <div>
                            <div className="text-xs opacity-75 mb-2">Suggested Actions:</div>
                            <div className="space-y-1">
                              {opportunity.actions.map((action, index) => (
                                <Button
                                  key={index}
                                  size="sm"
                                  variant="outline"
                                  className="text-xs mr-2 mb-1"
                                  onClick={() => action.action()}
                                >
                                  {action.title}
                                </Button>
                              ))}
                            </div>
                          </div>
                        )}
                        
                        {/* Expiration warning */}
                        {isExpiring && (
                          <div className="flex items-center space-x-2 p-2 bg-red-100 rounded text-red-800">
                            <ExclamationTriangleIcon className="h-4 w-4" />
                            <span className="text-xs font-medium">
                              Opportunity expires in {timeRemaining}
                            </span>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        )}
        
        {/* Summary stats */}
        {opportunities.length > 0 && (
          <div className="mt-4 pt-4 border-t border-gray-200">
            <div className="grid grid-cols-4 gap-2 text-center">
              <div className="text-xs">
                <div className="font-medium text-red-600">{urgencyCounts.critical}</div>
                <div className="text-gray-500">Critical</div>
              </div>
              <div className="text-xs">
                <div className="font-medium text-orange-600">{urgencyCounts.high}</div>
                <div className="text-gray-500">High</div>
              </div>
              <div className="text-xs">
                <div className="font-medium text-yellow-600">{urgencyCounts.medium}</div>
                <div className="text-gray-500">Medium</div>
              </div>
              <div className="text-xs">
                <div className="font-medium text-blue-600">{urgencyCounts.low}</div>
                <div className="text-gray-500">Low</div>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}