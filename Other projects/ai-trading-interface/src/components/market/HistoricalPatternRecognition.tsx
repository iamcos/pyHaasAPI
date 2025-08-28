import React, { useState, useEffect } from 'react';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';
import { Market } from '../../types/trading';
import { HistoricalPattern, marketAnalysisService } from '../../services/marketAnalysisService';

interface HistoricalPatternRecognitionProps {
  market: Market;
  timeframe?: string;
}

export const HistoricalPatternRecognition: React.FC<HistoricalPatternRecognitionProps> = ({
  market,
  timeframe = '1d'
}) => {
  const [patterns, setPatterns] = useState<HistoricalPattern[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadPatterns();
  }, [market.id, timeframe]);

  const loadPatterns = async () => {
    try {
      setLoading(true);
      setError(null);
      const patternData = await marketAnalysisService.recognizeHistoricalPatterns(market.id, timeframe);
      setPatterns(patternData);
    } catch (err) {
      setError('Failed to recognize patterns');
      console.error('Error loading patterns:', err);
    } finally {
      setLoading(false);
    }
  };

  const getPatternIcon = (patternType: string) => {
    switch (patternType) {
      case 'head_and_shoulders': return '👤';
      case 'double_top': return '⛰️';
      case 'double_bottom': return '🏔️';
      case 'triangle': return '🔺';
      case 'flag': return '🏁';
      case 'wedge': return '📐';
      case 'cup_and_handle': return '☕';
      default: return '📊';
    }
  };

  const getDirectionColor = (direction: string) => {
    return direction === 'up' ? 'text-green-600' : 'text-red-600';
  };

  const getDirectionIcon = (direction: string) => {
    return direction === 'up' ? '📈' : '📉';
  };

  const formatPrice = (price: number) => {
    if (price < 0.01) return price.toFixed(6);
    if (price < 1) return price.toFixed(4);
    if (price < 100) return price.toFixed(2);
    return price.toLocaleString();
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence > 0.8) return 'text-green-600 bg-green-100';
    if (confidence > 0.6) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  if (loading) {
    return (
      <Card className="p-6">
        <div className="flex items-center justify-center h-32">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <span className="ml-2 text-gray-600">Analyzing patterns...</span>
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="p-6">
        <div className="text-center">
          <div className="text-red-600 mb-2">⚠️ Error</div>
          <p className="text-gray-600 mb-4">{error}</p>
          <Button onClick={loadPatterns} variant="primary" size="sm">
            Retry Analysis
          </Button>
        </div>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">
            Pattern Recognition
          </h3>
          <p className="text-gray-600">
            Historical chart patterns for {market.symbol}
          </p>
        </div>
        <Button onClick={loadPatterns} variant="outline" size="sm">
          Refresh
        </Button>
      </div>

      {/* Patterns List */}
      {patterns.length > 0 ? (
        <div className="space-y-4">
          {patterns.map((pattern) => (
            <Card key={pattern.id} className="p-6">
              <div className="space-y-4">
                {/* Pattern Header */}
                <div className="flex items-start justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="text-2xl">{getPatternIcon(pattern.patternType)}</div>
                    <div>
                      <h4 className="font-semibold text-gray-900 capitalize">
                        {pattern.patternType.replace('_', ' ')}
                      </h4>
                      <div className="flex items-center space-x-2 mt-1">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getConfidenceColor(pattern.confidence)}`}>
                          {(pattern.confidence * 100).toFixed(0)}% Confidence
                        </span>
                        <span className="text-xs text-gray-500">
                          {pattern.timeframe}
                        </span>
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className={`flex items-center text-lg font-bold ${getDirectionColor(pattern.expectedOutcome.direction)}`}>
                      <span className="mr-1">{getDirectionIcon(pattern.expectedOutcome.direction)}</span>
                      {pattern.expectedOutcome.direction.toUpperCase()}
                    </div>
                    <div className="text-sm text-gray-600">
                      {(pattern.expectedOutcome.probability * 100).toFixed(0)}% probability
                    </div>
                  </div>
                </div>

                {/* Pattern Details */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="p-3 bg-gray-50 rounded-lg">
                    <div className="text-sm text-gray-500 mb-1">Current Phase</div>
                    <div className="font-medium">{pattern.currentPhase}</div>
                  </div>
                  <div className="p-3 bg-blue-50 rounded-lg">
                    <div className="text-sm text-gray-500 mb-1">Target Price</div>
                    <div className="font-medium text-blue-600">
                      ${formatPrice(pattern.expectedOutcome.targetPrice)}
                    </div>
                  </div>
                  <div className="p-3 bg-purple-50 rounded-lg">
                    <div className="text-sm text-gray-500 mb-1">Breakout Level</div>
                    <div className="font-medium text-purple-600">
                      ${formatPrice(pattern.keyLevels.breakout)}
                    </div>
                  </div>
                </div>

                {/* Key Levels */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Support Levels */}
                  <div>
                    <h5 className="font-medium text-gray-900 mb-2 flex items-center">
                      <span className="mr-2">🛡️</span>
                      Support Levels
                    </h5>
                    <div className="space-y-1">
                      {pattern.keyLevels.support.slice(0, 3).map((level, index) => (
                        <div key={index} className="flex justify-between text-sm">
                          <span className="text-gray-600">S{index + 1}:</span>
                          <span className="font-medium text-green-600">
                            ${formatPrice(level)}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Resistance Levels */}
                  <div>
                    <h5 className="font-medium text-gray-900 mb-2 flex items-center">
                      <span className="mr-2">🚧</span>
                      Resistance Levels
                    </h5>
                    <div className="space-y-1">
                      {pattern.keyLevels.resistance.slice(0, 3).map((level, index) => (
                        <div key={index} className="flex justify-between text-sm">
                          <span className="text-gray-600">R{index + 1}:</span>
                          <span className="font-medium text-red-600">
                            ${formatPrice(level)}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Volume Analysis */}
                <div className="p-4 bg-gray-50 rounded-lg">
                  <h5 className="font-medium text-gray-900 mb-2 flex items-center">
                    <span className="mr-2">📊</span>
                    Volume Analysis
                  </h5>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-gray-600">Pattern:</span>
                      <span className="ml-2 font-medium capitalize">
                        {pattern.volume.pattern}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-600">Significance:</span>
                      <span className="ml-2 font-medium">
                        {(pattern.volume.significance * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                </div>

                {/* Pattern Description */}
                <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                  <h5 className="font-medium text-blue-800 mb-2">Pattern Analysis</h5>
                  <p className="text-sm text-blue-700">{pattern.description}</p>
                </div>

                {/* Timeline */}
                <div className="flex justify-between text-sm text-gray-500 pt-4 border-t border-gray-200">
                  <span>
                    Started: {new Date(pattern.startDate).toLocaleDateString()}
                  </span>
                  <span>
                    Ended: {new Date(pattern.endDate).toLocaleDateString()}
                  </span>
                  <span>
                    Analyzed: {new Date(pattern.timestamp).toLocaleDateString()}
                  </span>
                </div>
              </div>
            </Card>
          ))}
        </div>
      ) : (
        <Card className="p-8 text-center">
          <div className="text-gray-400 text-lg mb-2">🔍</div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Patterns Detected</h3>
          <p className="text-gray-600 mb-4">
            No significant historical patterns found for {market.symbol} in the {timeframe} timeframe.
          </p>
          <div className="text-sm text-gray-500">
            Try adjusting the timeframe or check back later as new patterns may emerge.
          </div>
        </Card>
      )}

      {/* Pattern Summary */}
      {patterns.length > 0 && (
        <Card className="p-4">
          <h4 className="font-medium text-gray-900 mb-3">Pattern Summary</h4>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div className="text-center">
              <div className="text-lg font-bold text-blue-600">{patterns.length}</div>
              <div className="text-gray-500">Total Patterns</div>
            </div>
            <div className="text-center">
              <div className="text-lg font-bold text-green-600">
                {patterns.filter(p => p.expectedOutcome.direction === 'up').length}
              </div>
              <div className="text-gray-500">Bullish</div>
            </div>
            <div className="text-center">
              <div className="text-lg font-bold text-red-600">
                {patterns.filter(p => p.expectedOutcome.direction === 'down').length}
              </div>
              <div className="text-gray-500">Bearish</div>
            </div>
            <div className="text-center">
              <div className="text-lg font-bold text-purple-600">
                {patterns.filter(p => p.confidence > 0.8).length}
              </div>
              <div className="text-gray-500">High Confidence</div>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
};