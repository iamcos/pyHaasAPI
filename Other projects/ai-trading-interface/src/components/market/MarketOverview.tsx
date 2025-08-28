import React, { useState, useEffect } from 'react';
import { Card } from '../ui/Card';
import { Market } from '../../types/trading';

interface MarketOverviewProps {
  markets: Market[];
  onMarketSelect: (market: Market) => void;
}

export const MarketOverview: React.FC<MarketOverviewProps> = ({
  markets,
  onMarketSelect
}) => {
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [displayMarkets, setDisplayMarkets] = useState<Market[]>([]);

  useEffect(() => {
    if (selectedCategory === 'all') {
      setDisplayMarkets(markets.slice(0, 100)); // Show top 100 for performance
    } else {
      const filtered = markets.filter(market => 
        market.category.primary === selectedCategory ||
        market.category.secondary === selectedCategory ||
        market.category.tags.includes(selectedCategory)
      ).slice(0, 100);
      setDisplayMarkets(filtered);
    }
  }, [markets, selectedCategory]);

  const categories = React.useMemo(() => {
    const cats = new Set<string>();
    markets.forEach(market => {
      cats.add(market.category.primary);
      if (market.category.secondary) cats.add(market.category.secondary);
      market.category.tags.forEach(tag => cats.add(tag));
    });
    return Array.from(cats).sort();
  }, [markets]);

  const formatPrice = (price: number) => {
    if (price < 0.01) return price.toFixed(6);
    if (price < 1) return price.toFixed(4);
    if (price < 100) return price.toFixed(2);
    return price.toLocaleString();
  };

  const formatVolume = (volume: number) => {
    if (volume >= 1e9) return `$${(volume / 1e9).toFixed(2)}B`;
    if (volume >= 1e6) return `$${(volume / 1e6).toFixed(2)}M`;
    if (volume >= 1e3) return `$${(volume / 1e3).toFixed(2)}K`;
    return `$${volume.toFixed(2)}`;
  };

  const getChangeColor = (change: number) => {
    if (change > 0) return 'text-green-600';
    if (change < 0) return 'text-red-600';
    return 'text-gray-600';
  };

  const getChangeIcon = (change: number) => {
    if (change > 0) return '↗️';
    if (change < 0) return '↘️';
    return '➡️';
  };

  return (
    <div className="space-y-6">
      {/* Category Filter */}
      <div className="flex flex-wrap gap-2">
        <button
          onClick={() => setSelectedCategory('all')}
          className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
            selectedCategory === 'all'
              ? 'bg-blue-100 text-blue-800 border border-blue-200'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          All Markets ({markets.length})
        </button>
        {categories.slice(0, 10).map(category => {
          const count = markets.filter(m => 
            m.category.primary === category ||
            m.category.secondary === category ||
            m.category.tags.includes(category)
          ).length;
          
          return (
            <button
              key={category}
              onClick={() => setSelectedCategory(category)}
              className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                selectedCategory === category
                  ? 'bg-blue-100 text-blue-800 border border-blue-200'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {category} ({count})
            </button>
          );
        })}
      </div>

      {/* Market Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {displayMarkets.map(market => (
          <Card
            key={market.id}
            className="p-4 hover:shadow-lg transition-shadow cursor-pointer border hover:border-blue-200"
            onClick={() => onMarketSelect(market)}
          >
            <div className="flex items-start justify-between mb-3">
              <div>
                <h3 className="font-semibold text-gray-900 text-lg">
                  {market.symbol}
                </h3>
                <p className="text-sm text-gray-500">
                  {market.baseAsset}/{market.quoteAsset}
                </p>
                <p className="text-xs text-gray-400 mt-1">
                  {market.exchange}
                </p>
              </div>
              <div className="text-right">
                <div className="text-lg font-bold text-gray-900">
                  ${formatPrice(market.price)}
                </div>
                <div className={`text-sm font-medium flex items-center ${getChangeColor(market.changePercent24h)}`}>
                  <span className="mr-1">{getChangeIcon(market.changePercent24h)}</span>
                  {market.changePercent24h > 0 ? '+' : ''}{market.changePercent24h.toFixed(2)}%
                </div>
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">24h Volume:</span>
                <span className="font-medium">{formatVolume(market.volume24h)}</span>
              </div>
              
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">24h High:</span>
                <span className="font-medium">${formatPrice(market.high24h)}</span>
              </div>
              
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">24h Low:</span>
                <span className="font-medium">${formatPrice(market.low24h)}</span>
              </div>

              {market.marketCap && (
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Market Cap:</span>
                  <span className="font-medium">{formatVolume(market.marketCap)}</span>
                </div>
              )}
            </div>

            {/* Category Tags */}
            <div className="mt-3 flex flex-wrap gap-1">
              <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
                {market.category.primary}
              </span>
              {market.category.secondary && (
                <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded">
                  {market.category.secondary}
                </span>
              )}
              {market.category.tags.slice(0, 2).map(tag => (
                <span key={tag} className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">
                  {tag}
                </span>
              ))}
            </div>

            {/* Status Indicator */}
            <div className="mt-3 flex items-center justify-between">
              <div className="flex items-center">
                <div className={`w-2 h-2 rounded-full mr-2 ${
                  market.status === 'active' ? 'bg-green-500' : 
                  market.status === 'inactive' ? 'bg-yellow-500' : 'bg-red-500'
                }`}></div>
                <span className="text-xs text-gray-500 capitalize">{market.status}</span>
              </div>
              <span className="text-xs text-gray-400">
                {new Date(market.lastUpdated).toLocaleTimeString()}
              </span>
            </div>
          </Card>
        ))}
      </div>

      {displayMarkets.length === 0 && (
        <div className="text-center py-12">
          <div className="text-gray-400 text-lg mb-2">📊</div>
          <p className="text-gray-500">No markets found for the selected category</p>
        </div>
      )}

      {displayMarkets.length === 100 && markets.length > 100 && (
        <div className="text-center py-4">
          <p className="text-gray-500 text-sm">
            Showing top 100 markets. Use filters to narrow down results.
          </p>
        </div>
      )}
    </div>
  );
};