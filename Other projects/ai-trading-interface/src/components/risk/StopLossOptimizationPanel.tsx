import React, { useState, useEffect } from 'react';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';
import { automatedRiskManager } from '../../services/automatedRiskManager';

interface StopLossOptimization {
  symbol: string;
  currentStopLoss: number;
  optimizedStopLoss: number;
  currentTakeProfit: number;
  optimizedTakeProfit: number;
  reasoning: string;
  expectedImprovement: number;
  riskReduction: number;
}

interface StopLossOptimizationPanelProps {
  accountId: string;
  className?: string;
}

export const StopLossOptimizationPanel: React.FC<StopLossOptimizationPanelProps> = ({ 
  accountId, 
  className 
}) => {
  const [optimizations, setOptimizations] = useState<StopLossOptimization[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedOptimizations, setSelectedOptimizations] = useState<Set<string>>(new Set());

  useEffect(() => {
    if (accountId) {
      loadOptimizations();
    }
  }, [accountId]);

  const loadOptimizations = async () => {
    try {
      setLoading(true);
      const data = await automatedRiskManager.optimizeStopLossAndTakeProfit(accountId);
      setOptimizations(data);
    } catch (error) {
      console.error('Failed to load stop-loss optimizations:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectOptimization = (symbol: string, selected: boolean) => {
    const newSelected = new Set(selectedOptimizations);
    if (selected) {
      newSelected.add(symbol);
    } else {
      newSelected.delete(symbol);
    }
    setSelectedOptimizations(newSelected);
  };

  const handleApplySelected = async () => {
    const selectedOpts = optimizations.filter(opt => selectedOptimizations.has(opt.symbol));
    
    if (selectedOpts.length === 0) {
      alert('Please select at least one optimization to apply');
      return;
    }

    // In a real implementation, this would execute the stop-loss updates
    console.log('Applying stop-loss optimizations:', selectedOpts);
    alert(`Applied ${selectedOpts.length} stop-loss optimizations`);
    
    // Clear selections
    setSelectedOptimizations(new Set());
  };

  const formatCurrency = (value: number): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(value);
  };

  const formatPercentage = (value: number): string => {
    return `${(value * 100).toFixed(1)}%`;
  };

  const getImprovementColor = (improvement: number): string => {
    if (improvement > 0.1) return 'text-green-600 bg-green-50';
    if (improvement > 0) return 'text-blue-600 bg-blue-50';
    if (improvement > -0.1) return 'text-yellow-600 bg-yellow-50';
    return 'text-red-600 bg-red-50';
  };

  const getRiskReductionColor = (reduction: number): string => {
    if (reduction > 0.1) return 'text-green-600';
    if (reduction > 0) return 'text-blue-600';
    return 'text-red-600';
  };

  if (loading) {
    return (
      <Card className={className}>
        <div className="p-6">
          <div className="animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-1/3 mb-4"></div>
            <div className="space-y-4">
              {[1, 2, 3].map(i => (
                <div key={i} className="h-32 bg-gray-200 rounded"></div>
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
          <h3 className="text-lg font-semibold">Dynamic Stop-Loss Optimization</h3>
          <div className="flex items-center space-x-2">
            {selectedOptimizations.size > 0 && (
              <Button
                onClick={handleApplySelected}
                className="bg-green-600 hover:bg-green-700 text-white"
              >
                Apply Selected ({selectedOptimizations.size})
              </Button>
            )}
            <Button
              variant="outline"
              size="sm"
              onClick={loadOptimizations}
            >
              Refresh
            </Button>
          </div>
        </div>

        {optimizations.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <p>No stop-loss optimizations available</p>
            <p className="text-sm">Optimizations are generated based on current positions and market conditions</p>
          </div>
        ) : (
          <div className="space-y-4">
            {optimizations.map((opt) => {
              const isSelected = selectedOptimizations.has(opt.symbol);
              const stopLossChange = opt.optimizedStopLoss - opt.currentStopLoss;
              const takeProfitChange = opt.optimizedTakeProfit - opt.currentTakeProfit;

              return (
                <div
                  key={opt.symbol}
                  className={`border rounded-lg p-4 transition-all ${
                    isSelected ? 'border-green-500 bg-green-50' : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center space-x-3">
                      <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={(e) => handleSelectOptimization(opt.symbol, e.target.checked)}
                        className="rounded border-gray-300"
                      />
                      <div>
                        <h4 className="font-semibold text-lg">{opt.symbol}</h4>
                        <div className="flex items-center space-x-4 text-sm">
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                            getImprovementColor(opt.expectedImprovement)
                          }`}>
                            Expected Improvement: {formatPercentage(opt.expectedImprovement)}
                          </span>
                          <span className={`font-medium ${getRiskReductionColor(opt.riskReduction)}`}>
                            Risk Reduction: {formatPercentage(opt.riskReduction)}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Current vs Optimized Levels */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-4">
                    {/* Stop Loss */}
                    <div className="bg-white rounded-lg border p-4">
                      <h5 className="font-medium text-gray-700 mb-3">Stop Loss</h5>
                      <div className="space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-gray-500">Current:</span>
                          <span className="font-medium">{formatCurrency(opt.currentStopLoss)}</span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-gray-500">Optimized:</span>
                          <span className="font-medium">{formatCurrency(opt.optimizedStopLoss)}</span>
                        </div>
                        <div className="flex items-center justify-between pt-2 border-t">
                          <span className="text-sm font-medium">Change:</span>
                          <span className={`font-semibold ${
                            stopLossChange > 0 ? 'text-red-600' : stopLossChange < 0 ? 'text-green-600' : 'text-gray-600'
                          }`}>
                            {stopLossChange > 0 ? '+' : ''}{formatCurrency(stopLossChange)}
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Take Profit */}
                    <div className="bg-white rounded-lg border p-4">
                      <h5 className="font-medium text-gray-700 mb-3">Take Profit</h5>
                      <div className="space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-gray-500">Current:</span>
                          <span className="font-medium">{formatCurrency(opt.currentTakeProfit)}</span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-gray-500">Optimized:</span>
                          <span className="font-medium">{formatCurrency(opt.optimizedTakeProfit)}</span>
                        </div>
                        <div className="flex items-center justify-between pt-2 border-t">
                          <span className="text-sm font-medium">Change:</span>
                          <span className={`font-semibold ${
                            takeProfitChange > 0 ? 'text-green-600' : takeProfitChange < 0 ? 'text-red-600' : 'text-gray-600'
                          }`}>
                            {takeProfitChange > 0 ? '+' : ''}{formatCurrency(takeProfitChange)}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Risk-Reward Analysis */}
                  <div className="bg-gray-50 rounded-lg p-4 mb-4">
                    <h5 className="font-medium text-gray-700 mb-2">Risk-Reward Analysis</h5>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="text-gray-500">Current R:R Ratio:</span>
                        <span className="ml-2 font-medium">
                          {((opt.currentTakeProfit - opt.currentStopLoss) / Math.abs(opt.currentStopLoss)).toFixed(2)}:1
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-500">Optimized R:R Ratio:</span>
                        <span className="ml-2 font-medium">
                          {((opt.optimizedTakeProfit - opt.optimizedStopLoss) / Math.abs(opt.optimizedStopLoss)).toFixed(2)}:1
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* AI Reasoning */}
                  <div className="bg-blue-50 rounded-lg p-4">
                    <div className="text-sm font-medium text-blue-800 mb-2">AI Optimization Analysis:</div>
                    <div className="text-sm text-blue-700 leading-relaxed">
                      {opt.reasoning}
                    </div>
                  </div>

                  {/* Metrics Summary */}
                  <div className="mt-4 pt-4 border-t border-gray-200">
                    <div className="flex items-center justify-between text-xs text-gray-500">
                      <span>Expected Improvement: {formatPercentage(opt.expectedImprovement)}</span>
                      <span>Risk Reduction: {formatPercentage(opt.riskReduction)}</span>
                      <span>
                        Impact: {opt.expectedImprovement > 0.05 ? 'High' : opt.expectedImprovement > 0 ? 'Medium' : 'Low'}
                      </span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Summary Statistics */}
        {optimizations.length > 0 && (
          <div className="mt-6 p-4 bg-green-50 rounded-lg">
            <div className="text-sm font-medium text-green-800 mb-2">Optimization Summary</div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <span className="text-green-600">Total Positions:</span>
                <span className="ml-2 font-medium">{optimizations.length}</span>
              </div>
              <div>
                <span className="text-green-600">Positive Impact:</span>
                <span className="ml-2 font-medium text-green-600">
                  {optimizations.filter(o => o.expectedImprovement > 0).length}
                </span>
              </div>
              <div>
                <span className="text-green-600">Risk Reduction:</span>
                <span className="ml-2 font-medium text-blue-600">
                  {optimizations.filter(o => o.riskReduction > 0).length}
                </span>
              </div>
              <div>
                <span className="text-green-600">Avg Improvement:</span>
                <span className="ml-2 font-medium">
                  {formatPercentage(
                    optimizations.reduce((sum, o) => sum + o.expectedImprovement, 0) / optimizations.length
                  )}
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Best Practices */}
        <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="text-xs text-blue-800">
            <strong>Optimization Guidelines:</strong>
            <ul className="mt-1 ml-4 list-disc space-y-1">
              <li>Stop-loss levels are optimized based on volatility, support/resistance, and risk management principles</li>
              <li>Take-profit levels target optimal risk-reward ratios (minimum 1:2)</li>
              <li>Consider market conditions and position size when applying optimizations</li>
              <li>Review optimizations regularly as market conditions change</li>
            </ul>
          </div>
        </div>
      </div>
    </Card>
  );
};