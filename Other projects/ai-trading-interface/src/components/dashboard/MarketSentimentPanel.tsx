import React, { useState } from 'react'
import { 
  TrendingUpIcon,
  TrendingDownIcon,
  MinusIcon,
  EyeIcon,
  ChartBarIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline'
import { Card, CardHeader, CardContent } from '@/components/ui'
import type { MarketSentiment } from '@/services/dashboardService'

interface MarketSentimentPanelProps {
  sentiment: MarketSentiment
  loading?: boolean
}

export function MarketSentimentPanel({ sentiment, loading = false }: MarketSentimentPanelProps) {
  const [expandedAsset, setExpandedAsset] = useState<string | null>(null)

  if (loading) {
    return (
      <Card>
        <CardHeader title="Market Sentiment" />
        <CardContent>
          <div className="animate-pulse space-y-4">
            <div className="h-16 bg-gray-200 rounded"></div>
            <div className="space-y-2">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="h-12 bg-gray-200 rounded"></div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>
    )
  }

  const getSentimentIcon = (sentimentType: string) => {
    switch (sentimentType) {
      case 'bullish': return TrendingUpIcon
      case 'bearish': return TrendingDownIcon
      default: return MinusIcon
    }
  }

  const getSentimentColor = (sentimentType: string) => {
    switch (sentimentType) {
      case 'bullish': return 'text-green-500'
      case 'bearish': return 'text-red-500'
      default: return 'text-gray-500'
    }
  }

  const getSentimentBg = (sentimentType: string) => {
    switch (sentimentType) {
      case 'bullish': return 'bg-green-50 border-green-200'
      case 'bearish': return 'bg-red-50 border-red-200'
      default: return 'bg-gray-50 border-gray-200'
    }
  }

  const OverallIcon = getSentimentIcon(sentiment.overall.sentiment)
  const topAssets = Object.entries(sentiment.byAsset)
    .sort(([,a], [,b]) => b.confidence - a.confidence)
    .slice(0, 5)

  return (
    <Card>
      <CardHeader 
        title="Market Sentiment"
        subtitle={`Updated ${sentiment.lastUpdate.toLocaleTimeString()}`}
      />
      
      <CardContent className="space-y-4">
        {/* Overall Sentiment */}
        <div className={`p-4 rounded-lg border ${getSentimentBg(sentiment.overall.sentiment)}`}>
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-2">
              <OverallIcon className={`h-5 w-5 ${getSentimentColor(sentiment.overall.sentiment)}`} />
              <span className="font-medium text-gray-900 capitalize">
                {sentiment.overall.sentiment} Market
              </span>
            </div>
            <span className="text-sm text-gray-600">
              {(sentiment.overall.confidence * 100).toFixed(0)}% confidence
            </span>
          </div>
          
          <div className="space-y-1">
            {sentiment.overall.signals.map((signal, index) => (
              <div key={index} className="text-xs text-gray-600">
                • {signal}
              </div>
            ))}
          </div>
        </div>

        {/* Market Indices */}
        <div className="grid grid-cols-3 gap-3">
          <div className="text-center p-3 bg-gray-50 rounded-lg">
            <div className="text-lg font-semibold text-gray-900">
              {sentiment.volatilityIndex.toFixed(0)}
            </div>
            <div className="text-xs text-gray-500">Volatility</div>
          </div>
          
          <div className="text-center p-3 bg-gray-50 rounded-lg">
            <div className="text-lg font-semibold text-gray-900">
              {sentiment.fearGreedIndex}
            </div>
            <div className="text-xs text-gray-500">Fear/Greed</div>
          </div>
          
          <div className="text-center p-3 bg-gray-50 rounded-lg">
            <div className="text-lg font-semibold text-gray-900">
              {sentiment.trendStrength.toFixed(0)}%
            </div>
            <div className="text-xs text-gray-500">Trend Strength</div>
          </div>
        </div>

        {/* Top Assets by Sentiment */}
        <div>
          <h4 className="text-sm font-medium text-gray-700 mb-3">
            Asset Sentiment
          </h4>
          <div className="space-y-2">
            {topAssets.map(([symbol, assetSentiment]) => {
              const AssetIcon = getSentimentIcon(assetSentiment.sentiment)
              const isExpanded = expandedAsset === symbol
              
              return (
                <div key={symbol} className="border border-gray-200 rounded-lg overflow-hidden">
                  <button
                    onClick={() => setExpandedAsset(isExpanded ? null : symbol)}
                    className="w-full p-3 text-left hover:bg-gray-50 transition-colors"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <AssetIcon className={`h-4 w-4 ${getSentimentColor(assetSentiment.sentiment)}`} />
                        <div>
                          <div className="text-sm font-medium text-gray-900">
                            {symbol}
                          </div>
                          <div className="text-xs text-gray-500 capitalize">
                            {assetSentiment.sentiment} • {assetSentiment.timeframe}
                          </div>
                        </div>
                      </div>
                      
                      <div className="flex items-center space-x-2">
                        <div className="text-right">
                          <div className="text-sm font-medium text-gray-900">
                            {(assetSentiment.confidence * 100).toFixed(0)}%
                          </div>
                          <div className="text-xs text-gray-500">
                            Confidence
                          </div>
                        </div>
                        <ChartBarIcon className="h-4 w-4 text-gray-400" />
                      </div>
                    </div>
                  </button>
                  
                  {isExpanded && (
                    <div className="px-3 pb-3 border-t border-gray-100">
                      <div className="pt-2 space-y-1">
                        <div className="flex justify-between text-xs">
                          <span className="text-gray-500">Strength:</span>
                          <span className="font-medium">
                            {(assetSentiment.strength * 100).toFixed(0)}%
                          </span>
                        </div>
                        
                        <div className="mt-2">
                          <div className="text-xs text-gray-500 mb-1">Signals:</div>
                          {assetSentiment.signals.map((signal, index) => (
                            <div key={index} className="text-xs text-gray-600 ml-2">
                              • {signal}
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </div>

        {/* Sentiment Distribution */}
        <div>
          <h4 className="text-sm font-medium text-gray-700 mb-3">
            Market Distribution
          </h4>
          
          <div className="space-y-2">
            {['bullish', 'neutral', 'bearish'].map(sentimentType => {
              const count = Object.values(sentiment.byAsset).filter(
                s => s.sentiment === sentimentType
              ).length
              const total = Object.keys(sentiment.byAsset).length
              const percentage = total > 0 ? (count / total) * 100 : 0
              
              return (
                <div key={sentimentType} className="flex items-center space-x-3">
                  <div className={`w-3 h-3 rounded-full ${
                    sentimentType === 'bullish' ? 'bg-green-500' :
                    sentimentType === 'bearish' ? 'bg-red-500' : 'bg-gray-500'
                  }`} />
                  <div className="flex-1">
                    <div className="flex justify-between items-center">
                      <span className="text-sm capitalize text-gray-700">
                        {sentimentType}
                      </span>
                      <span className="text-sm text-gray-600">
                        {count} ({percentage.toFixed(0)}%)
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-1.5 mt-1">
                      <div 
                        className={`h-1.5 rounded-full ${
                          sentimentType === 'bullish' ? 'bg-green-500' :
                          sentimentType === 'bearish' ? 'bg-red-500' : 'bg-gray-500'
                        }`}
                        style={{ width: `${percentage}%` }}
                      />
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Warning for extreme conditions */}
        {(sentiment.volatilityIndex > 80 || sentiment.fearGreedIndex < 20 || sentiment.fearGreedIndex > 80) && (
          <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
            <div className="flex items-center space-x-2">
              <ExclamationTriangleIcon className="h-4 w-4 text-yellow-600" />
              <span className="text-sm font-medium text-yellow-800">
                Extreme Market Conditions
              </span>
            </div>
            <div className="text-xs text-yellow-700 mt-1">
              {sentiment.volatilityIndex > 80 && "High volatility detected. "}
              {sentiment.fearGreedIndex < 20 && "Extreme fear in the market. "}
              {sentiment.fearGreedIndex > 80 && "Extreme greed in the market. "}
              Consider adjusting risk parameters.
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}