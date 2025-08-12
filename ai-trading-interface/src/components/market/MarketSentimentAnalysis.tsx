import React, { useState, useEffect } from 'react';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';
import { Market } from '../../types/trading';
import { MarketSentiment, marketAnalysisService } from '../../services/marketAnalysisService';

interface MarketSentimentAnalysisProps {
  market: Market;
  timeframe?: string;
}

export const MarketSentimentAnalysis: React.FC<MarketSentimentAnalysisProps> = ({
  market,
  timeframe = '1h'
}) => {
  const [sentiment, setSentiment] = useState<MarketSentiment | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadSentiment();
  }, [market.id, timeframe]);

  const loadSentiment = async () => {
    try {
      setLoading(true);
      setError(null);
      const sentimentData = await marketAnalysisService.analyzeSentiment(market.id, timeframe);
      setSentiment(sentimentData);
    } catch (err) {
      setError('Failed to analyze market sentiment');
      console.error('Error loading sentiment:', err);
    } finally {
      setLoading(false);
    }
  };

  const getSentimentColor = (sentiment: string) => {
    switch (sentiment) {
      case 'bullish': return 'text-green-600 bg-green-100';
      case 'bearish': return 'text-red-600 bg-red-100';
      case 'neutral': return 'text-gray-600 bg-gray-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getSentimentIcon = (sentiment: string) => {
    switch (sentiment) {
      case 'bullish': return '🐂';
      case 'bearish': return '🐻';
      case 'neutral': return '⚖️';
      default: return '❓';
    }
  };

  const getFactorIcon = (type: string) => {
    switch (type) {
      case 'technical': return '📈';
      case 'volume': return '📊';
      case 'momentum': return '⚡';
      case 'volatility': return '🌊';
      case 'correlation': return '🔗';
      default: return '📋';
    }
  };

  const getImpactColor = (impact: number) => {
    if (impact > 0.1) return 'text-green-600';
    if (impact < -0.1) return 'text-red-600';
    return 'text-gray-600';
  };

  if (loading) {
    return (
      <Card className="p-6">
        <div className="flex items-center justify-center h-32">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <span className="ml-2 text-gray-600">Analyzing sentiment...</span>
        </div>
      </Card>
    );
  }

  if (error || !sentiment) {
    return (
      <Card className="p-6">
        <div className="text-center">
          <div className="text-red-600 mb-2">⚠️ Error</div>
          <p className="text-gray-600 mb-4">{error || 'No sentiment data available'}</p>
          <Button onClick={loadSentiment} variant="primary" size="sm">
            Retry Analysis
          </Button>
        </div>
      </Card>
    );
  }

  return (
    <Card className="p-6">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900">
            Market Sentiment Analysis
          </h3>
          <Button onClick={loadSentiment} variant="outline" size="sm">
            Refresh
          </Button>
        </div>

        {/* Overall Sentiment */}
        <div className="text-center">
          <div className="text-4xl mb-2">
            {getSentimentIcon(sentiment.sentiment)}
          </div>
          <div className={`inline-flex px-4 py-2 rounded-full text-lg font-semibold ${getSentimentColor(sentiment.sentiment)}`}>
            {sentiment.sentiment.toUpperCase()}
          </div>
          <div className="mt-2 text-sm text-gray-600">
            Confidence: {(sentiment.confidence * 100).toFixed(1)}%
          </div>
          <div className="mt-1 text-xs text-gray-500">
            Score: {sentiment.score.toFixed(3)} ({sentiment.score > 0 ? 'Bullish' : sentiment.score < 0 ? 'Bearish' : 'Neutral'})
          </div>
        </div>

        {/* Sentiment Gauge */}
        <div className="relative">
          <div className="w-full bg-gray-200 rounded-full h-3">
            <div 
              className="h-3 rounded-full transition-all duration-500"
              style={{
                width: `${Math.abs(sentiment.score) * 50}%`,
                marginLeft: sentiment.score < 0 ? `${50 + sentiment.score * 50}%` : '50%',
                backgroundColor: sentiment.score > 0 ? '#10b981' : sentiment.score < 0 ? '#ef4444' : '#6b7280'
              }}
            />
          </div>
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>Very Bearish</span>
            <span>Neutral</span>
            <span>Very Bullish</span>
          </div>
        </div>

        {/* Sentiment Factors */}
        <div>
          <h4 className="font-medium text-gray-900 mb-3">Contributing Factors</h4>
          <div className="space-y-3">
            {sentiment.factors.map((factor, index) => (
              <div key={index} className="flex items-start space-x-3 p-3 bg-gray-50 rounded-lg">
                <div className="text-lg">{getFactorIcon(factor.type)}</div>
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-medium text-gray-900 capitalize">
                      {factor.type}
                    </span>
                    <div className="flex items-center space-x-2">
                      <span className={`text-sm font-medium ${getImpactColor(factor.impact)}`}>
                        {factor.impact > 0 ? '+' : ''}{(factor.impact * 100).toFixed(1)}%
                      </span>
                      <span className="text-xs text-gray-500">
                        ({(factor.confidence * 100).toFixed(0)}% confidence)
                      </span>
                    </div>
                  </div>
                  <p className="text-sm text-gray-600">{factor.description}</p>
                  
                  {/* Impact bar */}
                  <div className="mt-2 relative">
                    <div className="w-full bg-gray-200 rounded-full h-1">
                      <div 
                        className="h-1 rounded-full transition-all duration-300"
                        style={{
                          width: `${Math.abs(factor.impact) * 100}%`,
                          marginLeft: factor.impact < 0 ? `${100 - Math.abs(factor.impact) * 100}%` : '0%',
                          backgroundColor: factor.impact > 0 ? '#10b981' : '#ef4444'
                        }}
                      />
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Summary Stats */}
        <div className="grid grid-cols-3 gap-4 pt-4 border-t border-gray-200">
          <div className="text-center">
            <div className="text-sm text-gray-500">Bullish Factors</div>
            <div className="text-lg font-semibold text-green-600">
              {sentiment.factors.filter(f => f.impact > 0).length}
            </div>
          </div>
          <div className="text-center">
            <div className="text-sm text-gray-500">Neutral Factors</div>
            <div className="text-lg font-semibold text-gray-600">
              {sentiment.factors.filter(f => Math.abs(f.impact) < 0.05).length}
            </div>
          </div>
          <div className="text-center">
            <div className="text-sm text-gray-500">Bearish Factors</div>
            <div className="text-lg font-semibold text-red-600">
              {sentiment.factors.filter(f => f.impact < 0).length}
            </div>
          </div>
        </div>

        {/* Timestamp */}
        <div className="text-xs text-gray-500 text-center">
          Analysis updated: {sentiment.timestamp.toLocaleString()}
          <span className="ml-2">Timeframe: {sentiment.timeframe}</span>
        </div>
      </div>
    </Card>
  );
};