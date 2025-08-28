import React, { useState, useEffect } from 'react';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';
import { PortfolioCorrelation } from '../../types/risk';
import { riskMonitoringService } from '../../services/riskMonitoringService';

interface PortfolioCorrelationAnalysisProps {
  className?: string;
}

export const PortfolioCorrelationAnalysis: React.FC<PortfolioCorrelationAnalysisProps> = ({ className }) => {
  const [correlations, setCorrelations] = useState<PortfolioCorrelation[]>([]);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState<'matrix' | 'list' | 'heatmap'>('matrix');
  const [filterThreshold, setFilterThreshold] = useState(0.3);
  const [sortBy, setSortBy] = useState<'correlation' | 'significance'>('correlation');

  useEffect(() => {
    loadCorrelations();
  }, []);

  const loadCorrelations = async () => {
    try {
      setLoading(true);
      const data = await riskMonitoringService.getPortfolioCorrelations();
      setCorrelations(data);
    } catch (error) {
      console.error('Failed to load correlations:', error);
    } finally {
      setLoading(false);
    }
  };

  const getCorrelationColor = (correlation: number): string => {
    const abs = Math.abs(correlation);
    if (abs >= 0.8) return correlation > 0 ? 'bg-red-500' : 'bg-blue-500';
    if (abs >= 0.6) return correlation > 0 ? 'bg-red-400' : 'bg-blue-400';
    if (abs >= 0.4) return correlation > 0 ? 'bg-red-300' : 'bg-blue-300';
    if (abs >= 0.2) return correlation > 0 ? 'bg-red-200' : 'bg-blue-200';
    return 'bg-gray-200';
  };

  const getCorrelationTextColor = (correlation: number): string => {
    const abs = Math.abs(correlation);
    return abs >= 0.4 ? 'text-white' : 'text-gray-800';
  };

  const getSignificanceIcon = (significance: string): string => {
    switch (significance) {
      case 'high': return '🔴';
      case 'medium': return '🟡';
      case 'low': return '🟢';
      default: return '⚪';
    }
  };

  const filteredCorrelations = correlations
    .filter(c => Math.abs(c.correlation) >= filterThreshold)
    .sort((a, b) => {
      if (sortBy === 'correlation') {
        return Math.abs(b.correlation) - Math.abs(a.correlation);
      } else {
        const significanceOrder = { high: 3, medium: 2, low: 1 };
        return significanceOrder[b.significance] - significanceOrder[a.significance];
      }
    });

  const uniqueSymbols = Array.from(
    new Set([...correlations.map(c => c.symbol1), ...correlations.map(c => c.symbol2)])
  ).sort();

  const getCorrelationValue = (symbol1: string, symbol2: string): number | null => {
    if (symbol1 === symbol2) return 1;
    const correlation = correlations.find(
      c => (c.symbol1 === symbol1 && c.symbol2 === symbol2) ||
           (c.symbol1 === symbol2 && c.symbol2 === symbol1)
    );
    return correlation ? correlation.correlation : null;
  };

  const renderMatrix = () => (
    <div className="overflow-auto">
      <table className="min-w-full">
        <thead>
          <tr>
            <th className="p-2 text-left font-medium text-sm">Symbol</th>
            {uniqueSymbols.map(symbol => (
              <th key={symbol} className="p-2 text-center font-medium text-xs min-w-16">
                {symbol}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {uniqueSymbols.map(symbol1 => (
            <tr key={symbol1}>
              <td className="p-2 font-medium text-sm">{symbol1}</td>
              {uniqueSymbols.map(symbol2 => {
                const correlation = getCorrelationValue(symbol1, symbol2);
                return (
                  <td key={symbol2} className="p-1">
                    <div
                      className={`w-12 h-8 flex items-center justify-center text-xs font-medium rounded ${
                        correlation !== null ? getCorrelationColor(correlation) : 'bg-gray-100'
                      } ${correlation !== null ? getCorrelationTextColor(correlation) : 'text-gray-400'}`}
                      title={correlation !== null ? `${(correlation * 100).toFixed(1)}%` : 'No data'}
                    >
                      {correlation !== null ? (correlation * 100).toFixed(0) : '-'}
                    </div>
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );

  const renderList = () => (
    <div className="space-y-3 max-h-96 overflow-y-auto">
      {filteredCorrelations.map((correlation, index) => (
        <div key={`${correlation.symbol1}-${correlation.symbol2}`} className="border rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-2">
              <span className="font-medium">{correlation.symbol1}</span>
              <span className="text-gray-400">↔</span>
              <span className="font-medium">{correlation.symbol2}</span>
              <span className="text-sm">{getSignificanceIcon(correlation.significance)}</span>
            </div>
            <div className="flex items-center space-x-2">
              <div
                className={`px-3 py-1 rounded-full text-sm font-medium ${
                  getCorrelationColor(correlation.correlation)
                } ${getCorrelationTextColor(correlation.correlation)}`}
              >
                {(correlation.correlation * 100).toFixed(1)}%
              </div>
            </div>
          </div>
          <div className="text-sm text-gray-600 grid grid-cols-3 gap-4">
            <div>
              <span className="font-medium">Significance:</span>
              <span className="ml-1 capitalize">{correlation.significance}</span>
            </div>
            <div>
              <span className="font-medium">P-Value:</span>
              <span className="ml-1">{correlation.pValue.toFixed(4)}</span>
            </div>
            <div>
              <span className="font-medium">Timeframe:</span>
              <span className="ml-1">{correlation.timeframe}</span>
            </div>
          </div>
        </div>
      ))}
    </div>
  );

  const renderHeatmap = () => (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {filteredCorrelations.map((correlation, index) => (
        <div
          key={`${correlation.symbol1}-${correlation.symbol2}`}
          className={`p-4 rounded-lg border-2 ${
            Math.abs(correlation.correlation) >= 0.7 ? 'border-red-300' :
            Math.abs(correlation.correlation) >= 0.5 ? 'border-yellow-300' : 'border-green-300'
          }`}
        >
          <div className="text-center">
            <div className="font-medium text-sm mb-1">
              {correlation.symbol1} ↔ {correlation.symbol2}
            </div>
            <div
              className={`text-2xl font-bold mb-2 ${
                correlation.correlation >= 0 ? 'text-red-600' : 'text-blue-600'
              }`}
            >
              {(correlation.correlation * 100).toFixed(1)}%
            </div>
            <div className="text-xs text-gray-600">
              {correlation.significance} significance
            </div>
          </div>
        </div>
      ))}
    </div>
  );

  if (loading) {
    return (
      <Card className={className}>
        <div className="p-6">
          <div className="animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-1/3 mb-4"></div>
            <div className="grid grid-cols-4 gap-4">
              {[1, 2, 3, 4].map(i => (
                <div key={i} className="h-20 bg-gray-200 rounded"></div>
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
          <h3 className="text-lg font-semibold">Portfolio Correlation Analysis</h3>
          <Button
            variant="outline"
            size="sm"
            onClick={loadCorrelations}
            className="text-xs"
          >
            Refresh
          </Button>
        </div>

        {/* Controls */}
        <div className="flex flex-wrap items-center gap-4 mb-6 p-4 bg-gray-50 rounded-lg">
          <div className="flex items-center space-x-2">
            <label className="text-sm font-medium">View:</label>
            <select
              value={viewMode}
              onChange={(e) => setViewMode(e.target.value as any)}
              className="text-sm border border-gray-300 rounded px-2 py-1"
            >
              <option value="matrix">Matrix</option>
              <option value="list">List</option>
              <option value="heatmap">Heatmap</option>
            </select>
          </div>
          
          <div className="flex items-center space-x-2">
            <label className="text-sm font-medium">Min Correlation:</label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              value={filterThreshold}
              onChange={(e) => setFilterThreshold(parseFloat(e.target.value))}
              className="w-20"
            />
            <span className="text-sm text-gray-600">{(filterThreshold * 100).toFixed(0)}%</span>
          </div>

          <div className="flex items-center space-x-2">
            <label className="text-sm font-medium">Sort by:</label>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as any)}
              className="text-sm border border-gray-300 rounded px-2 py-1"
            >
              <option value="correlation">Correlation</option>
              <option value="significance">Significance</option>
            </select>
          </div>
        </div>

        {/* Legend */}
        <div className="mb-4 p-3 bg-blue-50 rounded-lg">
          <div className="text-sm font-medium mb-2">Correlation Legend:</div>
          <div className="flex flex-wrap items-center gap-4 text-xs">
            <div className="flex items-center space-x-1">
              <div className="w-4 h-4 bg-red-500 rounded"></div>
              <span>Strong Positive (≥80%)</span>
            </div>
            <div className="flex items-center space-x-1">
              <div className="w-4 h-4 bg-red-300 rounded"></div>
              <span>Moderate Positive (40-79%)</span>
            </div>
            <div className="flex items-center space-x-1">
              <div className="w-4 h-4 bg-gray-200 rounded"></div>
              <span>Weak (0-39%)</span>
            </div>
            <div className="flex items-center space-x-1">
              <div className="w-4 h-4 bg-blue-300 rounded"></div>
              <span>Moderate Negative (-40 to -79%)</span>
            </div>
            <div className="flex items-center space-x-1">
              <div className="w-4 h-4 bg-blue-500 rounded"></div>
              <span>Strong Negative (≤-80%)</span>
            </div>
          </div>
        </div>

        {/* Content */}
        {correlations.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <p>No correlation data available</p>
            <p className="text-sm">Correlations are calculated from historical price data</p>
          </div>
        ) : (
          <>
            {viewMode === 'matrix' && renderMatrix()}
            {viewMode === 'list' && renderList()}
            {viewMode === 'heatmap' && renderHeatmap()}
          </>
        )}

        {/* Summary Stats */}
        {correlations.length > 0 && (
          <div className="mt-6 p-4 bg-gray-50 rounded-lg">
            <div className="text-sm font-medium mb-2">Correlation Summary</div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <span className="text-gray-600">Total Pairs:</span>
                <span className="ml-2 font-medium">{correlations.length}</span>
              </div>
              <div>
                <span className="text-gray-600">High Risk (≥70%):</span>
                <span className="ml-2 font-medium text-red-600">
                  {correlations.filter(c => Math.abs(c.correlation) >= 0.7).length}
                </span>
              </div>
              <div>
                <span className="text-gray-600">Medium Risk (40-69%):</span>
                <span className="ml-2 font-medium text-yellow-600">
                  {correlations.filter(c => Math.abs(c.correlation) >= 0.4 && Math.abs(c.correlation) < 0.7).length}
                </span>
              </div>
              <div>
                <span className="text-gray-600">Low Risk (<40%):</span>
                <span className="ml-2 font-medium text-green-600">
                  {correlations.filter(c => Math.abs(c.correlation) < 0.4).length}
                </span>
              </div>
            </div>
          </div>
        )}
      </div>
    </Card>
  );
};