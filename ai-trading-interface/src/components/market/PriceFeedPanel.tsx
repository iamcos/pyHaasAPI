import React, { useState, useEffect } from 'react';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';
import { Market, PriceData } from '../../types/trading';
import { marketDataService } from '../../services/marketDataService';

interface PriceFeedPanelProps {
  selectedMarkets: Market[];
}

interface PriceFeed {
  marketId: string;
  symbol: string;
  price: number;
  change: number;
  changePercent: number;
  volume: number;
  timestamp: Date;
  priceHistory: number[];
}

export const PriceFeedPanel: React.FC<PriceFeedPanelProps> = ({
  selectedMarkets
}) => {
  const [priceFeeds, setPriceFeeds] = useState<Map<string, PriceFeed>>(new Map());
  const [subscriptions, setSubscriptions] = useState<string[]>([]);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    if (selectedMarkets.length > 0) {
      subscribeToFeeds();
    } else {
      unsubscribeFromFeeds();
    }

    return () => {
      unsubscribeFromFeeds();
    };
  }, [selectedMarkets]);

  const subscribeToFeeds = () => {
    // Unsubscribe from existing feeds
    unsubscribeFromFeeds();

    const newSubscriptions: string[] = [];

    selectedMarkets.forEach(market => {
      const subscriptionId = marketDataService.subscribeToMarketData({
        marketIds: [market.id],
        dataTypes: ['price'],
        callback: (data) => {
          if (data.type === 'price') {
            updatePriceFeed(market, data.data);
          }
        }
      });

      newSubscriptions.push(subscriptionId);

      // Initialize price feed
      const initialFeed: PriceFeed = {
        marketId: market.id,
        symbol: market.symbol,
        price: market.price,
        change: market.change24h || 0,
        changePercent: market.changePercent24h,
        volume: market.volume24h,
        timestamp: new Date(),
        priceHistory: [market.price]
      };

      setPriceFeeds(prev => new Map(prev.set(market.id, initialFeed)));
    });

    setSubscriptions(newSubscriptions);
    setIsConnected(true);
  };

  const unsubscribeFromFeeds = () => {
    subscriptions.forEach(subscriptionId => {
      marketDataService.unsubscribeFromMarketData(subscriptionId);
    });
    setSubscriptions([]);
    setIsConnected(false);
  };

  const updatePriceFeed = (market: Market, priceData: PriceData) => {
    setPriceFeeds(prev => {
      const newFeeds = new Map(prev);
      const existingFeed = newFeeds.get(market.id);

      if (existingFeed) {
        const newPrice = priceData.close;
        const priceChange = newPrice - existingFeed.price;
        const priceChangePercent = (priceChange / existingFeed.price) * 100;

        const updatedFeed: PriceFeed = {
          ...existingFeed,
          price: newPrice,
          change: priceChange,
          changePercent: priceChangePercent,
          volume: priceData.volume,
          timestamp: priceData.timestamp,
          priceHistory: [...existingFeed.priceHistory.slice(-49), newPrice] // Keep last 50 prices
        };

        newFeeds.set(market.id, updatedFeed);
      }

      return newFeeds;
    });
  };

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

  const renderMiniChart = (priceHistory: number[]) => {
    if (priceHistory.length < 2) return null;

    const min = Math.min(...priceHistory);
    const max = Math.max(...priceHistory);
    const range = max - min;

    if (range === 0) return <div className="w-16 h-8 bg-gray-100 rounded"></div>;

    const points = priceHistory.map((price, index) => {
      const x = (index / (priceHistory.length - 1)) * 60; // 60px width
      const y = 24 - ((price - min) / range) * 24; // 24px height, inverted
      return `${x},${y}`;
    }).join(' ');

    const isPositive = priceHistory[priceHistory.length - 1] > priceHistory[0];

    return (
      <svg width="60" height="24" className="inline-block">
        <polyline
          points={points}
          fill="none"
          stroke={isPositive ? '#10b981' : '#ef4444'}
          strokeWidth="1.5"
          className="opacity-80"
        />
      </svg>
    );
  };

  if (selectedMarkets.length === 0) {
    return (
      <Card className="p-8 text-center">
        <div className="text-gray-400 text-lg mb-2">⚡</div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">No Markets Selected</h3>
        <p className="text-gray-600">
          Select markets from the overview or table to view real-time price feeds
        </p>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-gray-900">Real-time Price Feeds</h2>
          <p className="text-gray-600">
            Live price updates for {selectedMarkets.length} selected markets
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <div className={`flex items-center text-sm ${isConnected ? 'text-green-600' : 'text-red-600'}`}>
            <div className={`w-2 h-2 rounded-full mr-2 ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
            {isConnected ? 'Connected' : 'Disconnected'}
          </div>
          <Button
            onClick={subscribeToFeeds}
            variant="outline"
            size="sm"
          >
            Reconnect
          </Button>
        </div>
      </div>

      {/* Price Feed Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {Array.from(priceFeeds.values()).map(feed => (
          <Card key={feed.marketId} className="p-4 hover:shadow-lg transition-shadow">
            <div className="flex items-start justify-between mb-3">
              <div>
                <h3 className="font-semibold text-gray-900 text-lg">
                  {feed.symbol}
                </h3>
                <div className="text-sm text-gray-500">
                  {feed.timestamp.toLocaleTimeString()}
                </div>
              </div>
              <div className="text-right">
                <div className="text-xl font-bold text-gray-900">
                  ${formatPrice(feed.price)}
                </div>
                <div className={`text-sm font-medium flex items-center ${getChangeColor(feed.change)}`}>
                  <span className="mr-1">{getChangeIcon(feed.change)}</span>
                  {feed.change > 0 ? '+' : ''}${Math.abs(feed.change).toFixed(4)}
                </div>
              </div>
            </div>

            <div className="flex items-center justify-between mb-3">
              <div className={`text-sm font-medium ${getChangeColor(feed.changePercent)}`}>
                {feed.changePercent > 0 ? '+' : ''}{feed.changePercent.toFixed(2)}%
              </div>
              <div className="text-sm text-gray-500">
                Vol: {formatVolume(feed.volume)}
              </div>
            </div>

            {/* Mini Chart */}
            <div className="flex items-center justify-between">
              <div className="text-xs text-gray-500">
                Price Trend
              </div>
              <div className="flex items-center">
                {renderMiniChart(feed.priceHistory)}
              </div>
            </div>

            {/* Price Range */}
            <div className="mt-3 pt-3 border-t border-gray-100">
              <div className="flex justify-between text-xs text-gray-500">
                <span>
                  Low: ${formatPrice(Math.min(...feed.priceHistory))}
                </span>
                <span>
                  High: ${formatPrice(Math.max(...feed.priceHistory))}
                </span>
              </div>
            </div>
          </Card>
        ))}
      </div>

      {/* Feed Statistics */}
      <Card className="p-4">
        <h3 className="font-medium text-gray-900 mb-3">Feed Statistics</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <div className="text-gray-500">Active Feeds</div>
            <div className="font-medium text-lg">{priceFeeds.size}</div>
          </div>
          <div>
            <div className="text-gray-500">Connection Status</div>
            <div className={`font-medium text-lg ${isConnected ? 'text-green-600' : 'text-red-600'}`}>
              {isConnected ? 'Live' : 'Offline'}
            </div>
          </div>
          <div>
            <div className="text-gray-500">Updates/Min</div>
            <div className="font-medium text-lg">
              {isConnected ? '~60' : '0'}
            </div>
          </div>
          <div>
            <div className="text-gray-500">Avg Latency</div>
            <div className="font-medium text-lg">
              {isConnected ? '<100ms' : 'N/A'}
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
};