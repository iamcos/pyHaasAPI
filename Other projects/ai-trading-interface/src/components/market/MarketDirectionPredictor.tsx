import React, { useState, useEffect } from 'react';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';
import { Market } from '../../types/trading';
import { MarketDirection, marketAnalysisService } from '../../services/marketAnalysisService';

interface MarketDirectionPredictorProps {
  market: Market;
  timeframe?: string;
}

export const MarketDirectionPredictor: React.FC<MarketDirectionPredictorProps> = ({
  market,
  timeframe = '4h'
}) => {
  const [direction, setDirection] = useState<MarketDirection | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadDirection();
  }, [market.id, timeframe]);

  const loadDirection = async () => {
    try {
      setLoading(true);
      setError(null);
      const directionData = await marketAnalysisService.predictMarketDirection(market.id, timeframe);
      setDirection(directionData);
    } catch (err) {
      setError('Failed to predict market direction');
      console.error('Error loading direction:', err);
    } finally {
      setLoading(false);
    }
  };

  const getDirectionColor = (direction: string) => {
    switch (direction) {
      case 'up': return 'text-green-600 bg-green-100';
      case 'down': return 'text-red-600 bg-red-100';
      case 'sideways': return 'text-yellow-600 bg-yellow-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getDirectionIcon = (direction: string) => {
    switch (direction) {
      case 'up': return '📈';
      case 'down': return '📉';
      case 'sideways': return '↔️';
      default: return '❓';
    }
  };

  const formatPrice = (price: number) => {
    if (price < 0.01) return price.toFixed(6);
    if (price < 1) return price.toFixed(4);
    if (price < 100) return price.toFixed(2);
    return price.toLocaleString();
  };

  if (loading) {
    return (
      <Card className="p-6">
        <div className="flex items-center justify-center h-32">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <span className="ml-2 text-gray-600">Predicting direction...</span>
        </div>
      </Card>
    );
  }

  if (error || !direction) {
    return (
      <Card className="p-6">
        <div className="text-center">
          <div className="text-red-600 mb-2">⚠️ Error</div>
          <p className="text-gray-600 mb-4">{error || 'No direction data available'}</p>
          <Button onClick={loadDirection} variant="primary" size="sm">
            Retry Prediction
          </Button>
        </div>
      </Card>
    );
  }

  const priceChange = direction.targetPrice ? 
    ((direction.targetPrice - market.price) / market.price) * 100 : 0;

  return (
    <Card className="p-6">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900">
            Direction Prediction
          </h3>
          <Button onClick={loadDirection} variant="outline" size="sm">
            Refresh
          </Button>
        </div>

        {/* Main Prediction */}
        <div className="text-center">
          <div className="text-4xl mb-2">
            {getDirectionIcon(direction.direction)}
          </div>
          <div className={`inline-flex px-4 py-2 rounded-full text-lg font-semibold ${getDirectionColor(direction.direction)}`}>
            {direction.direction.toUpperCase()}
          </div>
          <div className="mt-2 text-sm text-gray-600">
            Confidence: {(direction.confidence * 100).toFixed(1)}%
          </div>
          <div className="mt-1 text-sm text-gray-600">
            Probability: {(direction.probability * 100).toFixed(1)}%
          </div>
        </div>

        {/* Price Targets */}
        {direction.targetPrice && (
          <div className="grid grid-cols-2 gap-4">
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <div className="text-sm text-gray-500 mb-1">Current Price</div>
              <div className="text-xl font-bold text-gray-900">
                ${formatPrice(market.price)}
              </div>
            </div>
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <div className="text-sm text-gray-500 mb-1">Target Price</div>
              <div className="text-xl font-bold text-blue-600">
                ${formatPrice(direction.targetPrice)}
              </div>
              <div className={`text-sm font-medium mt-1 ${priceChange >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {priceChange >= 0 ? '+' : ''}{priceChange.toFixed(2)}%
              </div>
            </div>
          </div>
        )}

        {/* Confidence Meter */}
        <div>
          <div className="flex justify-between text-sm text-gray-600 mb-2">
            <span>Confidence Level</span>
            <span>{(direction.confidence * 100).toFixed(1)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3">
            <div 
              className="h-3 rounded-full transition-all duration-500 bg-gradient-to-r from-blue-400 to-blue-600"
              style={{ width: `${direction.confidence * 100}%` }}
            />
          </div>
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>Low</span>
            <span>Medium</span>
            <span>High</span>
          </div>
        </div>

        {/* Reasoning */}
        <div>
          <h4 className="font-medium text-gray-900 mb-3">Analysis Reasoning</h4>
          <div className="space-y-2">
            {direction.reasoning.map((reason, index) => (
              <div key={index} className="flex items-start space-x-2 text-sm">
                <div className="w-2 h-2 bg-blue-500 rounded-full mt-2 flex-shrink-0" />
                <span className="text-gray-700">{reason}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Support and Resistance Levels */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Support Levels */}
          <div>
            <h4 className="font-medium text-gray-900 mb-2 flex items-center">
              <span className="mr-2">🛡️</span>
              Support Levels
            </h4>
            <div className="space-y-1">
              {direction.supportLevels.slice(0, 3).map((level, index) => (
                <div key={index} className="flex justify-between text-sm">
                  <span className="text-gray-600">S{index + 1}:</span>
                  <span className="font-medium text-green-600">
                    ${formatPrice(level)}
                  </span>
                </div>
              ))}
              {direction.supportLevels.length === 0 && (
                <div className="text-sm text-gray-500 italic">
                  No significant support levels identified
                </div>
              )}
            </div>
          </div>

          {/* Resistance Levels */}
          <div>
            <h4 className="font-medium text-gray-900 mb-2 flex items-center">
              <span className="mr-2">🚧</span>
              Resistance Levels
            </h4>
            <div className="space-y-1">
              {direction.resistanceLevels.slice(0, 3).map((level, index) => (
                <div key={index} className="flex justify-between text-sm">
                  <span className="text-gray-600">R{index + 1}:</span>
                  <span className="font-medium text-red-600">
                    ${formatPrice(level)}
                  </span>
                </div>
              ))}
              {direction.resistanceLevels.length === 0 && (
                <div className="text-sm text-gray-500 italic">
                  No significant resistance levels identified
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Risk Assessment */}
        <div className="p-4 bg-yellow-50 rounded-lg border border-yellow-200">
          <h4 className="font-medium text-yellow-800 mb-2 flex items-center">
            <span className="mr-2">⚠️</span>
            Risk Assessment
          </h4>
          <div className="text-sm text-yellow-700">
            {direction.confidence > 0.8 ? (
              "High confidence prediction - consider position sizing accordingly"
            ) : direction.confidence > 0.6 ? (
              "Moderate confidence - monitor for confirmation signals"
            ) : (
              "Low confidence prediction - wait for clearer signals or use smaller position sizes"
            )}
          </div>
        </div>

        {/* Timestamp */}
        <div className="text-xs text-gray-500 text-center">
          Prediction updated: {direction.timestamp.toLocaleString()}
          <span className="ml-2">Timeframe: {direction.timeframe}</span>
        </div>
      </div>
    </Card>
  );
};