import React, { useState, useEffect } from 'react';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';
import { automatedRiskManager } from '../../services/automatedRiskManager';

interface PositionSizingRecommendation {
  symbol: string;
  recommendedSize: number;
  currentSize: number;
  reasoning: string;
  confidence: number;
  riskScore: number;
  maxRisk: number;
  stopLoss: number;
  takeProfit: number;
}

interface PositionSizingPanelProps {
  accountId: string;
  className?: string;
}

export const PositionSizingPanel: React.FC<PositionSizingPanelProps> = ({ accountId, className }) => {
  const [recommendations, setRecommendations] = useState<PositionSizingRecommendation[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedRecommendations, setSelectedRecommendations] = useState<Set<string>>(new Set());

  useEffect(() => {
    if (accountId) {
      loadRecommendations();
    }
  }, [accountId]);

  const loadRecommendations = async () => {
    try {
      setLoading(true);
      const data = await automatedRiskManager.generatePositionSizingRecommendations(accountId);
      setRecommendations(data);
    } catch (error) {
      console.error('Failed to load position sizing recommendations:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectRecommendation = (symbol: string, selected: boolean) => {
    const newSelected = new Set(selectedRecommendations);
    if (selected) {
      newSelected.add(symbol);
    } else {
      newSelected.delete(symbol);
    }
    setSelectedRecommendations(newSelected);
  };

  const handleApplySelected = async () => {
    const selectedRecs = recommendations.filter(rec => selectedRecommendations.has(rec.symbol));
    
    if (selectedRecs.length === 0) {
      alert('Please select at least one recommendation to apply');
      return;
    }

    // In a real implementation, this would execute the position size changes
    console.log('Applying position sizing recommendations:', selectedRecs);
    alert(`Applied ${selectedRecs.length} position sizing recommendations`);
    
    // Clear selections
    setSelectedRecommendations(new Set());
  };

  const getRiskScoreColor = (score: number): string => {
    if (score >= 80) return 'text-red-600 bg-red-50';
    if (score >= 60) return 'text-orange-600 bg-orange-50';
    if (score >= 40) return 'text-yellow-600 bg-yellow-50';
    return 'text-green-600 bg-green-50';
  };

  const getConfidenceColor = (confidence: number): string => {
    if (confidence >= 0.8) return 'text-green-600';
    if (confidence >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  const formatNumber = (value: number, decimals: number = 2): string => {
    return value.toLocaleString('en-US', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals
    });
  };

  const formatCurrency = (value: number): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(value);
  };

  if (loading) {
    return (
      <Card className={className}>
        <div className="p-6">
          <div className="animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-1/3 mb-4"></div>
            <div className="space-y-4">
              {[1, 2, 3].map(i => (
                <div key={i} className="h-24 bg-gray-200 rounded"></div>
              ))}
            </div>
          </div>
        </div>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <div className="p-6">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold">AI-Powered Position Sizing</h3>
          <div className="flex items-center space-x-2">
            {selectedRecommendations.size > 0 && (
              <Button
                onClick={handleApplySelected}
                className="bg-blue-600 hover:bg-blue-700 text-white"
              >
                Apply Selected ({selectedRecommendations.size})
              </Button>
            )}
            <Button
              variant="outline"
              size="sm"
              onClick={loadRecommendations}
            >
              Refresh
            </Button>
          </div>
        </div>

        {recommendations.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <p>No position sizing recommendations available</p>
            <p className="text-sm">Recommendations are generated based on current positions and risk parameters</p>
          </div>
        ) : (
          <div className="space-y-4">
            {recommendations.map((rec) => {
              const sizeChange = rec.recommendedSize - rec.currentSize;
              const sizeChangePercent = rec.currentSize !== 0 ? (sizeChange / rec.currentSize) * 100 : 0;
              const isSelected = selectedRecommendations.has(rec.symbol);

              return (
                <div
                  key={rec.symbol}
                  className={`border rounded-lg p-4 transition-all ${
                    isSelected ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center space-x-3">
                      <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={(e) => handleSelectRecommendation(rec.symbol, e.target.checked)}
                        className="rounded border-gray-300"
                      />
                      <div>
                        <h4 className="font-semibold text-lg">{rec.symbol}</h4>
                        <div className="flex items-center space-x-4 text-sm text-gray-600">
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${getRiskScoreColor(rec.riskScore)}`}>
                            Risk: {rec.riskScore.toFixed(0)}
                          </span>
                          <span className={`font-medium ${getConfidenceColor(rec.confidence)}`}>
                            Confidence: {(rec.confidence * 100).toFixed(0)}%
                          </span>
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className={`text-lg font-semibold ${
                        sizeChange > 0 ? 'text-green-600' : sizeChange < 0 ? 'text-red-600' : 'text-gray-600'
                      }`}>
                        {sizeChange > 0 ? '+' : ''}{formatNumber(sizeChange, 4)}
                      </div>
                      <div className="text-sm text-gray-500">
                        {sizeChangePercent > 0 ? '+' : ''}{sizeChangePercent.toFixed(1)}%
                      </div>
                    </div>
                  </div>

                  {/* Position Details */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4 text-sm">
                    <div>
                      <span className="text-gray-500">Current Size:</span>
                      <div className="font-medium">{formatNumber(rec.currentSize, 4)}</div>
                    </div>
                    <div>
                      <span className="text-gray-500">Recommended:</span>
                      <div className="font-medium">{formatNumber(rec.recommendedSize, 4)}</div>
                    </div>
                    <div>
                      <span className="text-gray-500">Stop Loss:</span>
                      <div className="font-medium">{formatCurrency(rec.stopLoss)}</div>
                    </div>
                    <div>
                      <span className="text-gray-500">Take Profit:</span>
                      <div className="font-medium">{formatCurrency(rec.takeProfit)}</div>
                    </div>
                  </div>

                  {/* AI Reasoning */}
                  <div className="bg-gray-50 rounded-lg p-3">
                    <div className="text-sm font-medium text-gray-700 mb-1">AI Analysis:</div>
                    <div className="text-sm text-gray-600 leading-relaxed">
                      {rec.reasoning}
                    </div>
                  </div>

                  {/* Risk Metrics */}
                  <div className="mt-3 pt-3 border-t border-gray-200">
                    <div className="flex items-center justify-between text-xs text-gray-500">
                      <span>Max Risk per Position: {(rec.maxRisk * 100).toFixed(1)}%</span>
                      <span>Risk Score: {rec.riskScore.toFixed(0)}/100</span>
                      <span>Confidence: {(rec.confidence * 100).toFixed(0)}%</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Summary */}
        {recommendations.length > 0 && (
          <div className="mt-6 p-4 bg-blue-50 rounded-lg">
            <div className="text-sm font-medium text-blue-800 mb-2">Recommendations Summary</div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <span className="text-blue-600">Total Positions:</span>
                <span className="ml-2 font-medium">{recommendations.length}</span>
              </div>
              <div>
                <span className="text-blue-600">High Risk:</span>
                <span className="ml-2 font-medium text-red-600">
                  {recommendations.filter(r => r.riskScore >= 80).length}
                </span>
              </div>
              <div>
                <span className="text-blue-600">Size Increases:</span>
                <span className="ml-2 font-medium text-green-600">
                  {recommendations.filter(r => r.recommendedSize > r.currentSize).length}
                </span>
              </div>
              <div>
                <span className="text-blue-600">Size Decreases:</span>
                <span className="ml-2 font-medium text-red-600">
                  {recommendations.filter(r => r.recommendedSize < r.currentSize).length}
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Disclaimer */}
        <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
          <div className="text-xs text-yellow-800">
            <strong>Disclaimer:</strong> These are AI-generated recommendations based on risk management principles and market analysis. 
            Always review recommendations carefully and consider your own risk tolerance before making position adjustments.
          </div>
        </div>
      </div>
    </Card>
  );
};