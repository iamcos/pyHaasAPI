import React, { useState, useEffect } from 'react';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';
import { Market, OrderBook, OrderBookEntry } from '../../types/trading';
import { marketDataService } from '../../services/marketDataService';

interface OrderBookVisualizationProps {
  market: Market;
  onBack: () => void;
}

export const OrderBookVisualization: React.FC<OrderBookVisualizationProps> = ({
  market,
  onBack
}) => {
  const [orderBook, setOrderBook] = useState<OrderBook | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [depth, setDepth] = useState(20);
  const [subscriptionId, setSubscriptionId] = useState<string | null>(null);

  useEffect(() => {
    loadOrderBook();
    subscribeToUpdates();

    return () => {
      if (subscriptionId) {
        marketDataService.unsubscribeFromMarketData(subscriptionId);
      }
    };
  }, [market.id, depth]);

  const loadOrderBook = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await marketDataService.getOrderBook(market.id, depth);
      setOrderBook(data);
    } catch (err) {
      setError('Failed to load order book data');
      console.error('Error loading order book:', err);
    } finally {
      setLoading(false);
    }
  };

  const subscribeToUpdates = () => {
    if (subscriptionId) {
      marketDataService.unsubscribeFromMarketData(subscriptionId);
    }

    const newSubscriptionId = marketDataService.subscribeToMarketData({
      marketIds: [market.id],
      dataTypes: ['orderbook'],
      callback: (data) => {
        if (data.type === 'orderbook') {
          setOrderBook(data.data);
        }
      }
    });

    setSubscriptionId(newSubscriptionId);
  };

  const formatPrice = (price: number) => {
    if (price < 0.01) return price.toFixed(6);
    if (price < 1) return price.toFixed(4);
    if (price < 100) return price.toFixed(2);
    return price.toLocaleString();
  };

  const formatQuantity = (quantity: number) => {
    if (quantity >= 1e6) return `${(quantity / 1e6).toFixed(2)}M`;
    if (quantity >= 1e3) return `${(quantity / 1e3).toFixed(2)}K`;
    return quantity.toFixed(4);
  };

  const formatTotal = (total: number) => {
    if (total >= 1e6) return `$${(total / 1e6).toFixed(2)}M`;
    if (total >= 1e3) return `$${(total / 1e3).toFixed(2)}K`;
    return `$${total.toFixed(2)}`;
  };

  const getMaxQuantity = (entries: OrderBookEntry[]) => {
    return Math.max(...entries.map(entry => entry.quantity));
  };

  const renderOrderBookEntry = (
    entry: OrderBookEntry, 
    maxQuantity: number, 
    type: 'bid' | 'ask',
    index: number
  ) => {
    const widthPercent = (entry.quantity / maxQuantity) * 100;
    const bgColor = type === 'bid' ? 'bg-green-100' : 'bg-red-100';
    const textColor = type === 'bid' ? 'text-green-800' : 'text-red-800';

    return (
      <div
        key={`${type}-${index}`}
        className="relative flex items-center justify-between py-1 px-3 hover:bg-gray-50 transition-colors"
      >
        <div
          className={`absolute inset-0 ${bgColor} opacity-30`}
          style={{ width: `${widthPercent}%` }}
        />
        <div className="relative z-10 flex items-center justify-between w-full text-sm">
          <span className={`font-medium ${textColor}`}>
            ${formatPrice(entry.price)}
          </span>
          <span className="text-gray-700">
            {formatQuantity(entry.quantity)}
          </span>
          <span className="text-gray-500">
            {formatTotal(entry.total)}
          </span>
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <Card className="p-6">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <span className="ml-2 text-gray-600">Loading order book...</span>
        </div>
      </Card>
    );
  }

  if (error || !orderBook) {
    return (
      <Card className="p-6">
        <div className="text-center">
          <div className="text-red-600 mb-2">⚠️ Error</div>
          <p className="text-gray-600 mb-4">{error || 'No order book data available'}</p>
          <div className="space-x-2">
            <Button onClick={onBack} variant="outline">
              Back to Markets
            </Button>
            <Button onClick={loadOrderBook} variant="primary">
              Retry
            </Button>
          </div>
        </div>
      </Card>
    );
  }

  const maxBidQuantity = getMaxQuantity(orderBook.bids);
  const maxAskQuantity = getMaxQuantity(orderBook.asks);
  const maxQuantity = Math.max(maxBidQuantity, maxAskQuantity);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Button onClick={onBack} variant="outline" size="sm">
            ← Back
          </Button>
          <div>
            <h2 className="text-xl font-bold text-gray-900">
              {market.symbol} Order Book
            </h2>
            <p className="text-gray-600">
              {market.baseAsset}/{market.quoteAsset} on {market.exchange}
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <select
            value={depth}
            onChange={(e) => setDepth(Number(e.target.value))}
            className="px-3 py-1 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value={10}>10 levels</option>
            <option value={20}>20 levels</option>
            <option value={50}>50 levels</option>
            <option value={100}>100 levels</option>
          </select>
          <Button onClick={loadOrderBook} variant="outline" size="sm">
            Refresh
          </Button>
        </div>
      </div>

      {/* Market Info */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="text-sm text-gray-500">Current Price</div>
          <div className="text-lg font-bold text-gray-900">
            ${formatPrice(market.price)}
          </div>
        </Card>
        <Card className="p-4">
          <div className="text-sm text-gray-500">Spread</div>
          <div className="text-lg font-bold text-gray-900">
            ${formatPrice(orderBook.spread)}
          </div>
          <div className="text-xs text-gray-500">
            {orderBook.spreadPercent.toFixed(3)}%
          </div>
        </Card>
        <Card className="p-4">
          <div className="text-sm text-gray-500">Best Bid</div>
          <div className="text-lg font-bold text-green-600">
            ${formatPrice(orderBook.bids[0]?.price || 0)}
          </div>
        </Card>
        <Card className="p-4">
          <div className="text-sm text-gray-500">Best Ask</div>
          <div className="text-lg font-bold text-red-600">
            ${formatPrice(orderBook.asks[0]?.price || 0)}
          </div>
        </Card>
      </div>

      {/* Order Book */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Asks (Sell Orders) */}
        <Card className="overflow-hidden">
          <div className="bg-red-50 px-4 py-3 border-b">
            <h3 className="font-medium text-red-800">
              Asks (Sell Orders) - {orderBook.asks.length}
            </h3>
            <div className="flex justify-between text-xs text-red-600 mt-1">
              <span>Price</span>
              <span>Quantity</span>
              <span>Total</span>
            </div>
          </div>
          <div className="max-h-96 overflow-y-auto">
            {orderBook.asks.slice().reverse().map((ask, index) =>
              renderOrderBookEntry(ask, maxQuantity, 'ask', index)
            )}
          </div>
        </Card>

        {/* Bids (Buy Orders) */}
        <Card className="overflow-hidden">
          <div className="bg-green-50 px-4 py-3 border-b">
            <h3 className="font-medium text-green-800">
              Bids (Buy Orders) - {orderBook.bids.length}
            </h3>
            <div className="flex justify-between text-xs text-green-600 mt-1">
              <span>Price</span>
              <span>Quantity</span>
              <span>Total</span>
            </div>
          </div>
          <div className="max-h-96 overflow-y-auto">
            {orderBook.bids.map((bid, index) =>
              renderOrderBookEntry(bid, maxQuantity, 'bid', index)
            )}
          </div>
        </Card>
      </div>

      {/* Order Book Stats */}
      <Card className="p-4">
        <h3 className="font-medium text-gray-900 mb-3">Order Book Statistics</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <div className="text-gray-500">Total Bid Volume</div>
            <div className="font-medium">
              {formatQuantity(orderBook.bids.reduce((sum, bid) => sum + bid.quantity, 0))}
            </div>
          </div>
          <div>
            <div className="text-gray-500">Total Ask Volume</div>
            <div className="font-medium">
              {formatQuantity(orderBook.asks.reduce((sum, ask) => sum + ask.quantity, 0))}
            </div>
          </div>
          <div>
            <div className="text-gray-500">Total Bid Value</div>
            <div className="font-medium">
              {formatTotal(orderBook.bids.reduce((sum, bid) => sum + bid.total, 0))}
            </div>
          </div>
          <div>
            <div className="text-gray-500">Total Ask Value</div>
            <div className="font-medium">
              {formatTotal(orderBook.asks.reduce((sum, ask) => sum + ask.total, 0))}
            </div>
          </div>
        </div>
      </Card>

      {/* Last Updated */}
      <div className="text-center text-sm text-gray-500">
        Last updated: {new Date(orderBook.timestamp).toLocaleString()}
        {subscriptionId && (
          <span className="ml-2 text-green-600">● Live</span>
        )}
      </div>
    </div>
  );
};