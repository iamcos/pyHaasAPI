import React, { useState, useEffect } from 'react';
import { Card } from '../ui/Card';
import { MarketStats as MarketStatsType } from '../../types/trading';
import { marketDataService } from '../../services/marketDataService';

export const MarketStats: React.FC = () => {
  const [stats, setStats] = useState<MarketStatsType | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadStats();
    
    // Refresh stats every 30 seconds
    const interval = setInterval(loadStats, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadStats = async () => {
    try {
      setError(null);
      const marketStats = await marketDataService.getMarketStats();
      setStats(marketStats);
    } catch (err) {
      setError('Failed to load market statistics');
      console.error('Error loading market stats:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatVolume = (volume: number) => {
    if (volume >= 1e12) return `$${(volume / 1e12).toFixed(2)}T`;
    if (volume >= 1e9) return `$${(volume / 1e9).toFixed(2)}B`;
    if (volume >= 1e6) return `$${(volume / 1e6).toFixed(2)}M`;
    if (volume >= 1e3) return `$${(volume / 1e3).toFixed(2)}K`;
    return `$${volume.toFixed(2)}`;
  };

  const formatPrice = (price: number) => {
    if (price < 0.01) return price.toFixed(6);
    if (price < 1) return price.toFixed(4);
    if (price < 100) return price.toFixed(2);
    return price.toLocaleString();
  };

  const getChangeColor = (change: number) => {
    if (change > 0) return 'text-green-600';
    if (change < 0) return 'text-red-600';
    return 'text-gray-600';
  };

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <Card key={i} className="p-4 animate-pulse">
            <div className="h-4 bg-gray-200 rounded mb-2"></div>
            <div className="h-8 bg-gray-200 rounded"></div>
          </Card>
        ))}
      </div>
    );
  }

  if (error || !stats) {
    return (
      <Card className="p-4 text-center">
        <div className="text-red-600 mb-2">⚠️ Error</div>
        <p className="text-gray-600 text-sm">{error || 'No statistics available'}</p>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Main Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-gray-500">Total Markets</div>
              <div className="text-2xl font-bold text-gray-900">
                {stats.totalMarkets.toLocaleString()}
              </div>
            </div>
            <div className="text-2xl">🌐</div>
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-gray-500">Active Markets</div>
              <div className="text-2xl font-bold text-green-600">
                {stats.activeMarkets.toLocaleString()}
              </div>
            </div>
            <div className="text-2xl">✅</div>
          </div>
          <div className="text-xs text-gray-500 mt-1">
            {((stats.activeMarkets / stats.totalMarkets) * 100).toFixed(1)}% active
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-gray-500">24h Volume</div>
              <div className="text-2xl font-bold text-blue-600">
                {formatVolume(stats.totalVolume24h)}
              </div>
            </div>
            <div className="text-2xl">💰</div>
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-gray-500">Avg Volume/Market</div>
              <div className="text-2xl font-bold text-purple-600">
                {formatVolume(stats.totalVolume24h / stats.activeMarkets)}
              </div>
            </div>
            <div className="text-2xl">📊</div>
          </div>
        </Card>
      </div>

      {/* Top Performers */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Top Gainers */}
        <Card className="p-4">
          <h3 className="font-medium text-gray-900 mb-3 flex items-center">
            <span className="mr-2">🚀</span>
            Top Gainers (24h)
          </h3>
          <div className="space-y-2">
            {stats.topGainers.slice(0, 5).map((market, index) => (
              <div key={market.id} className="flex items-center justify-between text-sm">
                <div className="flex items-center">
                  <span className="w-4 text-gray-400 text-xs">{index + 1}.</span>
                  <span className="font-medium ml-2">{market.symbol}</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-gray-600">${formatPrice(market.price)}</span>
                  <span className="text-green-600 font-medium">
                    +{market.changePercent24h.toFixed(2)}%
                  </span>
                </div>
              </div>
            ))}
          </div>
        </Card>

        {/* Top Losers */}
        <Card className="p-4">
          <h3 className="font-medium text-gray-900 mb-3 flex items-center">
            <span className="mr-2">📉</span>
            Top Losers (24h)
          </h3>
          <div className="space-y-2">
            {stats.topLosers.slice(0, 5).map((market, index) => (
              <div key={market.id} className="flex items-center justify-between text-sm">
                <div className="flex items-center">
                  <span className="w-4 text-gray-400 text-xs">{index + 1}.</span>
                  <span className="font-medium ml-2">{market.symbol}</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-gray-600">${formatPrice(market.price)}</span>
                  <span className="text-red-600 font-medium">
                    {market.changePercent24h.toFixed(2)}%
                  </span>
                </div>
              </div>
            ))}
          </div>
        </Card>

        {/* Most Active */}
        <Card className="p-4">
          <h3 className="font-medium text-gray-900 mb-3 flex items-center">
            <span className="mr-2">🔥</span>
            Most Active (24h)
          </h3>
          <div className="space-y-2">
            {stats.mostActive.slice(0, 5).map((market, index) => (
              <div key={market.id} className="flex items-center justify-between text-sm">
                <div className="flex items-center">
                  <span className="w-4 text-gray-400 text-xs">{index + 1}.</span>
                  <span className="font-medium ml-2">{market.symbol}</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-gray-600">${formatPrice(market.price)}</span>
                  <span className="text-blue-600 font-medium">
                    {formatVolume(market.volume24h)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* Market Distribution */}
      <Card className="p-4">
        <h3 className="font-medium text-gray-900 mb-3">Market Distribution</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div className="text-center">
            <div className="text-2xl mb-1">🥇</div>
            <div className="font-medium">
              {stats.topGainers.filter(m => m.changePercent24h > 10).length}
            </div>
            <div className="text-gray-500 text-xs">Gainers {'>'} 10%</div>
          </div>
          <div className="text-center">
            <div className="text-2xl mb-1">📈</div>
            <div className="font-medium">
              {stats.topGainers.filter(m => m.changePercent24h > 0).length}
            </div>
            <div className="text-gray-500 text-xs">Positive</div>
          </div>
          <div className="text-center">
            <div className="text-2xl mb-1">📉</div>
            <div className="font-medium">
              {stats.topLosers.filter(m => m.changePercent24h < 0).length}
            </div>
            <div className="text-gray-500 text-xs">Negative</div>
          </div>
          <div className="text-center">
            <div className="text-2xl mb-1">🥉</div>
            <div className="font-medium">
              {stats.topLosers.filter(m => m.changePercent24h < -10).length}
            </div>
            <div className="text-gray-500 text-xs">Losers {'>'} 10%</div>
          </div>
        </div>
      </Card>

      {/* Last Updated */}
      <div className="text-center text-sm text-gray-500">
        Last updated: {new Date().toLocaleString()}
        <span className="ml-2 text-green-600">● Live</span>
      </div>
    </div>
  );
};