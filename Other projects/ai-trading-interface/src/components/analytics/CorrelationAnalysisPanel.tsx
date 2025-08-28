import React, { useState } from 'react'
import { 
  ScaleIcon,
  ChartBarIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon
} from '@heroicons/react/24/outline'
import { Card, CardHeader, CardContent } from '@/components/ui'
import type { CorrelationMatrix } from '@/services/analyticsService'

interface CorrelationAnalysisPanelProps {
  correlationMatrix: CorrelationMatrix
  loading?: boolean
}

export function CorrelationAnalysisPanel({ correlationMatrix, loading = false }: CorrelationAnalysisPanelProps) {
  const [selectedView, setSelectedView] = useState<'matrix' | 'clusters' | 'risk'>('matrix')

  if (loading) {
    return (
      <div className="animate-pulse space-y-6">
        <div className="h-8 bg-gray-200 rounded w-1/4"></div>
        <div className="h-64 bg-gray-200 rounded"></div>
      </div>
    )
  }

  const getCorrelationColor = (correlation: number) => {
    const abs = Math.abs(correlation)
    if (abs >= 0.8) return 'bg-red-500'
    if (abs >= 0.6) return 'bg-orange-500'
    if (abs >= 0.4) return 'bg-yellow-500'
    if (abs >= 0.2) return 'bg-green-500'
    return 'bg-blue-500'
  }

  const getCorrelationIntensity = (correlation: number) => {
    const abs = Math.abs(correlation)
    return `opacity-${Math.round(abs * 100)}`
  }

  const renderMatrixView = () => (
    <div className="space-y-6">
      {/* Correlation Matrix */}
      <Card>
        <CardHeader 
          title="Asset Correlation Matrix"
          subtitle="Correlation coefficients between portfolio assets"
        />
        <CardContent>
          <div className="overflow-x-auto">
            <div className="inline-block min-w-full">
              {/* Matrix Headers */}
              <div className="flex">
                <div className="w-24"></div>
                {correlationMatrix.assets.map((asset, index) => (
                  <div key={index} className="w-16 text-center">
                    <div className="text-xs font-medium text-gray-600 transform -rotate-45 origin-bottom-left">
                      {asset.split('/')[0]}
                    </div>
                  </div>
                ))}
              </div>
              
              {/* Matrix Rows */}
              {correlationMatrix.assets.map((rowAsset, rowIndex) => (
                <div key={rowIndex} className="flex items-center">
                  <div className="w-24 text-right pr-2">
                    <span className="text-xs font-medium text-gray-600">
                      {rowAsset.split('/')[0]}
                    </span>
                  </div>
                  {correlationMatrix.correlations[rowIndex]?.map((correlation, colIndex) => (
                    <div key={colIndex} className="w-16 h-12 flex items-center justify-center">
                      <div 
                        className={`w-10 h-8 rounded flex items-center justify-center text-white text-xs font-medium ${getCorrelationColor(correlation)}`}
                        style={{ opacity: Math.abs(correlation) }}
                        title={`${rowAsset} vs ${correlationMatrix.assets[colIndex]}: ${correlation.toFixed(3)}`}
                      >
                        {correlation.toFixed(2)}
                      </div>
                    </div>
                  )) || []}
                </div>
              ))}
            </div>
          </div>
          
          {/* Legend */}
          <div className="mt-6 flex items-center justify-center space-x-6 text-xs">
            <div className="flex items-center space-x-2">
              <div className="w-4 h-4 bg-red-500 rounded"></div>
              <span>High (0.8+)</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-4 h-4 bg-orange-500 rounded"></div>
              <span>Medium (0.6-0.8)</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-4 h-4 bg-yellow-500 rounded"></div>
              <span>Moderate (0.4-0.6)</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-4 h-4 bg-green-500 rounded"></div>
              <span>Low (0.2-0.4)</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-4 h-4 bg-blue-500 rounded"></div>
              <span>Very Low (0-0.2)</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Summary Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader title="Diversification Metrics" />
          <CardContent>
            <div className="space-y-4">
              <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                <span className="text-sm text-gray-600">Diversification Ratio</span>
                <span className="font-medium text-gray-900">
                  {(correlationMatrix.diversificationRatio * 100).toFixed(1)}%
                </span>
              </div>
              
              <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                <span className="text-sm text-gray-600">Concentration Risk</span>
                <span className={`font-medium ${
                  correlationMatrix.concentrationRisk > 0.5 ? 'text-red-600' : 'text-green-600'
                }`}>
                  {(correlationMatrix.concentrationRisk * 100).toFixed(1)}%
                </span>
              </div>
              
              <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                <span className="text-sm text-gray-600">Asset Count</span>
                <span className="font-medium text-gray-900">
                  {correlationMatrix.assets.length}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader title="Risk Assessment" />
          <CardContent>
            <div className="space-y-3">
              {correlationMatrix.concentrationRisk > 0.7 && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                  <div className="flex items-center space-x-2">
                    <ExclamationTriangleIcon className="h-4 w-4 text-red-600" />
                    <span className="text-sm font-medium text-red-800">High Concentration Risk</span>
                  </div>
                  <p className="text-xs text-red-700 mt-1">
                    Portfolio is heavily concentrated in correlated assets
                  </p>
                </div>
              )}
              
              {correlationMatrix.diversificationRatio < 0.5 && (
                <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                  <div className="flex items-center space-x-2">
                    <ExclamationTriangleIcon className="h-4 w-4 text-yellow-600" />
                    <span className="text-sm font-medium text-yellow-800">Low Diversification</span>
                  </div>
                  <p className="text-xs text-yellow-700 mt-1">
                    Consider adding uncorrelated assets to improve diversification
                  </p>
                </div>
              )}
              
              {correlationMatrix.diversificationRatio >= 0.7 && (
                <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
                  <div className="flex items-center space-x-2">
                    <InformationCircleIcon className="h-4 w-4 text-green-600" />
                    <span className="text-sm font-medium text-green-800">Well Diversified</span>
                  </div>
                  <p className="text-xs text-green-700 mt-1">
                    Portfolio shows good diversification across assets
                  </p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )

  const renderClustersView = () => (
    <div className="space-y-6">
      {correlationMatrix.clusters.map((cluster, index) => (
        <Card key={index}>
          <CardHeader 
            title={cluster.name}
            subtitle={`${cluster.assets.length} assets • Avg correlation: ${(cluster.avgCorrelation * 100).toFixed(1)}%`}
          />
          <CardContent>
            <div className="space-y-4">
              {/* Cluster Assets */}
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                {cluster.assets.map((asset, assetIndex) => (
                  <div key={assetIndex} className="p-3 bg-gray-50 rounded-lg text-center">
                    <div className="font-medium text-gray-900">{asset.split('/')[0]}</div>
                    <div className="text-xs text-gray-500">{asset}</div>
                  </div>
                ))}
              </div>
              
              {/* Cluster Metrics */}
              <div className="grid grid-cols-2 gap-4 pt-4 border-t border-gray-200">
                <div className="text-center">
                  <div className="text-lg font-semibold text-gray-900">
                    {(cluster.avgCorrelation * 100).toFixed(1)}%
                  </div>
                  <div className="text-xs text-gray-500">Average Correlation</div>
                </div>
                <div className="text-center">
                  <div className="text-lg font-semibold text-gray-900">
                    {(cluster.riskContribution * 100).toFixed(1)}%
                  </div>
                  <div className="text-xs text-gray-500">Risk Contribution</div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  )

  const renderRiskView = () => (
    <div className="space-y-6">
      {/* High Correlation Pairs */}
      <Card>
        <CardHeader title="High Correlation Pairs" subtitle="Asset pairs with correlation > 0.7" />
        <CardContent>
          <div className="space-y-3">
            {correlationMatrix.assets.map((asset1, i) => 
              correlationMatrix.assets.slice(i + 1).map((asset2, j) => {
                const correlation = correlationMatrix.correlations[i]?.[i + j + 1]
                if (!correlation || Math.abs(correlation) < 0.7) return null
                
                return (
                  <div key={`${i}-${j}`} className="flex items-center justify-between p-3 border border-gray-200 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <div className={`w-3 h-3 rounded-full ${
                        Math.abs(correlation) >= 0.9 ? 'bg-red-500' : 'bg-orange-500'
                      }`}></div>
                      <div>
                        <div className="font-medium text-gray-900">
                          {asset1.split('/')[0]} ↔ {asset2.split('/')[0]}
                        </div>
                        <div className="text-sm text-gray-500">
                          {asset1} • {asset2}
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className={`font-medium ${
                        Math.abs(correlation) >= 0.9 ? 'text-red-600' : 'text-orange-600'
                      }`}>
                        {correlation.toFixed(3)}
                      </div>
                      <div className="text-xs text-gray-500">
                        {Math.abs(correlation) >= 0.9 ? 'Very High' : 'High'}
                      </div>
                    </div>
                  </div>
                )
              })
            ).filter(Boolean)}
          </div>
        </CardContent>
      </Card>

      {/* Risk Recommendations */}
      <Card>
        <CardHeader title="Risk Management Recommendations" />
        <CardContent>
          <div className="space-y-4">
            {correlationMatrix.concentrationRisk > 0.6 && (
              <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                <div className="flex items-start space-x-3">
                  <ExclamationTriangleIcon className="h-5 w-5 text-red-600 mt-0.5" />
                  <div>
                    <h4 className="font-medium text-red-800">Reduce Concentration Risk</h4>
                    <p className="text-sm text-red-700 mt-1">
                      Your portfolio has high concentration risk ({(correlationMatrix.concentrationRisk * 100).toFixed(1)}%). 
                      Consider reducing position sizes in highly correlated assets.
                    </p>
                  </div>
                </div>
              </div>
            )}
            
            {correlationMatrix.diversificationRatio < 0.5 && (
              <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                <div className="flex items-start space-x-3">
                  <InformationCircleIcon className="h-5 w-5 text-yellow-600 mt-0.5" />
                  <div>
                    <h4 className="font-medium text-yellow-800">Improve Diversification</h4>
                    <p className="text-sm text-yellow-700 mt-1">
                      Diversification ratio is {(correlationMatrix.diversificationRatio * 100).toFixed(1)}%. 
                      Add assets from different sectors or asset classes to improve risk-adjusted returns.
                    </p>
                  </div>
                </div>
              </div>
            )}
            
            <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <div className="flex items-start space-x-3">
                <ChartBarIcon className="h-5 w-5 text-blue-600 mt-0.5" />
                <div>
                  <h4 className="font-medium text-blue-800">Monitor Correlation Changes</h4>
                  <p className="text-sm text-blue-700 mt-1">
                    Asset correlations can change during market stress. Regularly review and rebalance 
                    your portfolio to maintain desired diversification levels.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )

  const viewOptions = [
    { key: 'matrix' as const, label: 'Correlation Matrix', icon: ScaleIcon },
    { key: 'clusters' as const, label: 'Asset Clusters', icon: ChartBarIcon },
    { key: 'risk' as const, label: 'Risk Analysis', icon: ExclamationTriangleIcon }
  ]

  return (
    <div className="space-y-6">
      {/* View Selector */}
      <div className="flex space-x-1 bg-gray-100 rounded-lg p-1">
        {viewOptions.map(option => {
          const Icon = option.icon
          return (
            <button
              key={option.key}
              onClick={() => setSelectedView(option.key)}
              className={`flex items-center space-x-2 px-4 py-2 rounded-md text-sm font-medium transition-colors flex-1 justify-center ${
                selectedView === option.key
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              <Icon className="h-4 w-4" />
              <span>{option.label}</span>
            </button>
          )
        })}
      </div>

      {/* View Content */}
      {selectedView === 'matrix' && renderMatrixView()}
      {selectedView === 'clusters' && renderClustersView()}
      {selectedView === 'risk' && renderRiskView()}
    </div>
  )
}