import { Market, MarketFilter, MarketSort, OrderBook, PriceData, MarketStats, MarketDataSubscription } from '../types/trading';
import { mcpClient } from './mcpClient';
import { websocketService } from './websocketService';

class MarketDataService {
  private subscriptions = new Map<string, MarketDataSubscription>();
  private marketCache = new Map<string, Market>();
  private priceCache = new Map<string, PriceData[]>();
  private orderBookCache = new Map<string, OrderBook>();

  async getAllMarkets(): Promise<Market[]> {
    try {
      const markets = await mcpClient.markets.getAll();
      
      // Update cache
      markets.forEach(market => {
        this.marketCache.set(market.id, market);
      });
      
      return markets;
    } catch (error) {
      console.error('Failed to fetch markets:', error);
      // Return cached data if available
      return Array.from(this.marketCache.values());
    }
  }

  async getFilteredMarkets(filter: MarketFilter, sort?: MarketSort): Promise<Market[]> {
    const allMarkets = await this.getAllMarkets();
    
    let filteredMarkets = allMarkets.filter(market => {
      // Exchange filter
      if (filter.exchange && filter.exchange.length > 0) {
        if (!filter.exchange.includes(market.exchange)) return false;
      }
      
      // Category filter
      if (filter.category && filter.category.length > 0) {
        const hasCategory = filter.category.some(cat => 
          market.category.primary === cat || 
          market.category.secondary === cat ||
          market.category.tags.includes(cat)
        );
        if (!hasCategory) return false;
      }
      
      // Volume filter
      if (filter.minVolume && market.volume24h < filter.minVolume) return false;
      if (filter.maxVolume && market.volume24h > filter.maxVolume) return false;
      
      // Price filter
      if (filter.minPrice && market.price < filter.minPrice) return false;
      if (filter.maxPrice && market.price > filter.maxPrice) return false;
      
      // Change filter
      if (filter.changeRange) {
        if (market.changePercent24h < filter.changeRange.min || 
            market.changePercent24h > filter.changeRange.max) return false;
      }
      
      // Search filter
      if (filter.search) {
        const searchLower = filter.search.toLowerCase();
        const matchesSearch = 
          market.symbol.toLowerCase().includes(searchLower) ||
          market.baseAsset.toLowerCase().includes(searchLower) ||
          market.quoteAsset.toLowerCase().includes(searchLower) ||
          market.exchange.toLowerCase().includes(searchLower);
        if (!matchesSearch) return false;
      }
      
      return true;
    });
    
    // Apply sorting
    if (sort) {
      filteredMarkets.sort((a, b) => {
        let aValue: number;
        let bValue: number;
        
        switch (sort.field) {
          case 'symbol':
            return sort.direction === 'asc' 
              ? a.symbol.localeCompare(b.symbol)
              : b.symbol.localeCompare(a.symbol);
          case 'price':
            aValue = a.price;
            bValue = b.price;
            break;
          case 'volume24h':
            aValue = a.volume24h;
            bValue = b.volume24h;
            break;
          case 'change24h':
            aValue = a.changePercent24h;
            bValue = b.changePercent24h;
            break;
          case 'marketCap':
            aValue = a.marketCap || 0;
            bValue = b.marketCap || 0;
            break;
          default:
            return 0;
        }
        
        return sort.direction === 'asc' ? aValue - bValue : bValue - aValue;
      });
    }
    
    return filteredMarkets;
  }

  async getPriceData(marketId: string, timeframe: string = '1h', limit: number = 100): Promise<PriceData[]> {
    try {
      const priceData = await mcpClient.markets.getPriceData(marketId, { timeframe, limit });
      
      // Update cache
      this.priceCache.set(`${marketId}_${timeframe}`, priceData);
      
      return priceData;
    } catch (error) {
      console.error(`Failed to fetch price data for ${marketId}:`, error);
      // Return cached data if available
      return this.priceCache.get(`${marketId}_${timeframe}`) || [];
    }
  }

  async getOrderBook(marketId: string, depth: number = 20): Promise<OrderBook | null> {
    try {
      const orderBook = await mcpClient.markets.getOrderBook(marketId, depth);
      
      // Update cache
      this.orderBookCache.set(marketId, orderBook);
      
      return orderBook;
    } catch (error) {
      console.error(`Failed to fetch order book for ${marketId}:`, error);
      // Return cached data if available
      return this.orderBookCache.get(marketId) || null;
    }
  }

  async getMarketStats(): Promise<MarketStats> {
    const allMarkets = await this.getAllMarkets();
    const activeMarkets = allMarkets.filter(m => m.status === 'active');
    
    // Calculate total volume
    const totalVolume24h = activeMarkets.reduce((sum, market) => sum + market.volume24h, 0);
    
    // Get top gainers (top 10)
    const topGainers = [...activeMarkets]
      .sort((a, b) => b.changePercent24h - a.changePercent24h)
      .slice(0, 10);
    
    // Get top losers (bottom 10)
    const topLosers = [...activeMarkets]
      .sort((a, b) => a.changePercent24h - b.changePercent24h)
      .slice(0, 10);
    
    // Get most active by volume (top 10)
    const mostActive = [...activeMarkets]
      .sort((a, b) => b.volume24h - a.volume24h)
      .slice(0, 10);
    
    return {
      totalMarkets: allMarkets.length,
      activeMarkets: activeMarkets.length,
      totalVolume24h,
      topGainers,
      topLosers,
      mostActive
    };
  }

  subscribeToMarketData(subscription: MarketDataSubscription): string {
    const subscriptionId = `sub_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    this.subscriptions.set(subscriptionId, subscription);
    
    // Subscribe to WebSocket updates for the specified markets
    subscription.marketIds.forEach(marketId => {
      subscription.dataTypes.forEach(dataType => {
        websocketService.subscribe(`market.${marketId}.${dataType}`, (data) => {
          subscription.callback({
            type: dataType,
            marketId,
            data
          });
        });
      });
    });
    
    return subscriptionId;
  }

  unsubscribeFromMarketData(subscriptionId: string): void {
    const subscription = this.subscriptions.get(subscriptionId);
    if (subscription) {
      // Unsubscribe from WebSocket updates
      subscription.marketIds.forEach(marketId => {
        subscription.dataTypes.forEach(dataType => {
          websocketService.unsubscribe(`market.${marketId}.${dataType}`);
        });
      });
      
      this.subscriptions.delete(subscriptionId);
    }
  }

  getAvailableExchanges(): string[] {
    const exchanges = new Set<string>();
    this.marketCache.forEach(market => {
      exchanges.add(market.exchange);
    });
    return Array.from(exchanges).sort();
  }

  getAvailableCategories(): string[] {
    const categories = new Set<string>();
    this.marketCache.forEach(market => {
      categories.add(market.category.primary);
      if (market.category.secondary) {
        categories.add(market.category.secondary);
      }
      market.category.tags.forEach(tag => categories.add(tag));
    });
    return Array.from(categories).sort();
  }

  // Real-time price update handler
  private handlePriceUpdate = (marketId: string, priceData: PriceData) => {
    // Update market cache with latest price
    const market = this.marketCache.get(marketId);
    if (market) {
      market.price = priceData.close;
      market.lastUpdated = new Date();
      this.marketCache.set(marketId, market);
    }
    
    // Update price cache
    const cacheKey = `${marketId}_realtime`;
    const existingData = this.priceCache.get(cacheKey) || [];
    existingData.push(priceData);
    
    // Keep only last 1000 data points for real-time cache
    if (existingData.length > 1000) {
      existingData.shift();
    }
    
    this.priceCache.set(cacheKey, existingData);
  };

  // Order book update handler
  private handleOrderBookUpdate = (marketId: string, orderBook: OrderBook) => {
    this.orderBookCache.set(marketId, orderBook);
  };
}

export const marketDataService = new MarketDataService();