import React, { useState, useEffect } from 'react';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';
import { MarketOverview } from './MarketOverview';
import { MarketFilters } from './MarketFilters';
import { MarketDataTable } from './MarketDataTable';
import { OrderBookVisualization } from './OrderBookVisualization';
import { PriceFeedPanel } from './PriceFeedPanel';
import { MarketStats } from './MarketStats';
import { AIMarketAnalysisDashboard } from './AIMarketAnalysisDashboard';
import { Market, MarketFilter, MarketSort } from '../../types/trading';
import { marketDataService } from '../../services/marketDataService';

interface MarketIntelligenceHubProps {
  className?: string;
}

export const MarketIntelligenceHub: React.FC<MarketIntelligenceHubProps> = ({
  className = ''
}) => {
  const [markets, setMarkets] = useState<Market[]>([]);
  const [filteredMarkets, setFilteredMarkets] = useState<Market[]>([]);
  const [selectedMarket, setSelectedMarket] = useState<Market | null>(null);
  const [filter, setFilter] = useState<MarketFilter>({});
  const [sort, setSort] = useState<MarketSort>({ field: 'volume24h', direction: 'desc' });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeView, setActiveView] = useState<'overview' | 'table' | 'orderbook' | 'feeds' | 'ai-analysis'>('overview');

  useEffect(() => {
    loadMarkets();
  }, []);

  useEffect(() => {
    applyFiltersAndSort();
  }, [markets, filter, sort]);

  const loadMarkets = async () => {
    try {
      setLoading(true);
      setError(null);
      const marketData = await marketDataService.getAllMarkets();
      setMarkets(marketData);
    } catch (err) {
      setError('Failed to load market data');
      console.error('Error loading markets:', err);
    } finally {
      setLoading(false);
    }
  };

  const applyFiltersAndSort = async () => {
    try {
      const filtered = await marketDataService.getFilteredMarkets(filter, sort);
      setFilteredMarkets(filtered);
    } catch (err) {
      console.error('Error filtering markets:', err);
    }
  };

  const handleFilterChange = (newFilter: MarketFilter) => {
    setFilter(newFilter);
  };

  const handleSortChange = (newSort: MarketSort) => {
    setSort(newSort);
  };

  const handleMarketSelect = (market: Market) => {
    setSelectedMarket(market);
    setActiveView('orderbook');
  };

  const renderActiveView = () => {
    switch (activeView) {
      case 'overview':
        return (
          <MarketOverview 
            markets={filteredMarkets}
            onMarketSelect={handleMarketSelect}
          />
        );
      case 'table':
        return (
          <MarketDataTable
            markets={filteredMarkets}
            sort={sort}
            onSortChange={handleSortChange}
            onMarketSelect={handleMarketSelect}
          />
        );
      case 'orderbook':
        return selectedMarket ? (
          <OrderBookVisualization
            market={selectedMarket}
            onBack={() => setActiveView('overview')}
          />
        ) : (
          <div className="flex items-center justify-center h-64 text-gray-500">
            Select a market to view order book
          </div>
        );
      case 'feeds':
        return (
          <PriceFeedPanel
            selectedMarkets={selectedMarket ? [selectedMarket] : []}
          />
        );
      case 'ai-analysis':
        return selectedMarket ? (
          <AIMarketAnalysisDashboard market={selectedMarket} />
        ) : (
          <div className="flex items-center justify-center h-64 text-gray-500">
            Select a market to view AI analysis
          </div>
        );
      default:
        return null;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-2 text-gray-600">Loading market data...</span>
      </div>
    );
  }

  if (error) {
    return (
      <Card className="p-6">
        <div className="text-center">
          <div className="text-red-600 mb-2">⚠️ Error</div>
          <p className="text-gray-600 mb-4">{error}</p>
          <Button onClick={loadMarkets} variant="primary">
            Retry
          </Button>
        </div>
      </Card>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Market Intelligence Hub</h1>
          <p className="text-gray-600">
            Real-time data for {markets.length.toLocaleString()}+ markets across multiple exchanges
          </p>
        </div>
        <Button onClick={loadMarkets} variant="outline" size="sm">
          Refresh Data
        </Button>
      </div>

      {/* Market Stats */}
      <MarketStats />

      {/* Navigation Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'overview', label: 'Market Overview', icon: '📊' },
            { id: 'table', label: 'Data Table', icon: '📋' },
            { id: 'orderbook', label: 'Order Book', icon: '📈' },
            { id: 'feeds', label: 'Price Feeds', icon: '⚡' },
            { id: 'ai-analysis', label: 'AI Analysis', icon: '🤖' }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveView(tab.id as any)}
              className={`py-2 px-1 border-b-2 font-medium text-sm whitespace-nowrap ${
                activeView === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <span className="mr-2">{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Filters */}
      <MarketFilters
        filter={filter}
        onFilterChange={handleFilterChange}
        availableExchanges={marketDataService.getAvailableExchanges()}
        availableCategories={marketDataService.getAvailableCategories()}
      />

      {/* Main Content */}
      <div className="min-h-96">
        {renderActiveView()}
      </div>

      {/* Footer Info */}
      <div className="text-sm text-gray-500 text-center">
        Showing {filteredMarkets.length.toLocaleString()} of {markets.length.toLocaleString()} markets
        {selectedMarket && (
          <span className="ml-4">
            Selected: <strong>{selectedMarket.symbol}</strong> on {selectedMarket.exchange}
          </span>
        )}
      </div>
    </div>
  );
};