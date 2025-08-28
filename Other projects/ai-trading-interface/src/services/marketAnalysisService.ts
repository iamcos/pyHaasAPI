import { Market, PriceData } from '../types/trading';
import { aiService } from './aiService';
import { marketDataService } from './marketDataService';
import { mcpClient } from './mcpClient';

export interface MarketSentiment {
  marketId: string;
  symbol: string;
  sentiment: 'bullish' | 'bearish' | 'neutral';
  confidence: number;
  score: number; // -1 to 1, where -1 is very bearish, 1 is very bullish
  factors: SentimentFactor[];
  timestamp: Date;
  timeframe: string;
}

export interface SentimentFactor {
  type: 'technical' | 'volume' | 'momentum' | 'volatility' | 'correlation';
  description: string;
  impact: number; // -1 to 1
  confidence: number;
}

export interface MarketDirection {
  marketId: string;
  symbol: string;
  direction: 'up' | 'down' | 'sideways';
  confidence: number;
  targetPrice?: number;
  timeframe: string;
  probability: number;
  reasoning: string[];
  supportLevels: number[];
  resistanceLevels: number[];
  timestamp: Date;
}

export interface ArbitrageOpportunity {
  id: string;
  type: 'cross_exchange' | 'triangular' | 'statistical';
  markets: {
    buy: { marketId: string; exchange: string; price: number };
    sell: { marketId: string; exchange: string; price: number };
  };
  profitPercent: number;
  profitAmount: number;
  volume: number;
  risk: 'low' | 'medium' | 'high';
  timeToExpiry: number; // seconds
  confidence: number;
  requirements: string[];
  timestamp: Date;
}

export interface HistoricalPattern {
  id: string;
  marketId: string;
  symbol: string;
  patternType: 'head_and_shoulders' | 'double_top' | 'double_bottom' | 'triangle' | 'flag' | 'wedge' | 'cup_and_handle';
  confidence: number;
  timeframe: string;
  startDate: Date;
  endDate: Date;
  currentPhase: string;
  expectedOutcome: {
    direction: 'up' | 'down';
    targetPrice: number;
    probability: number;
  };
  keyLevels: {
    support: number[];
    resistance: number[];
    breakout: number;
  };
  volume: {
    pattern: 'increasing' | 'decreasing' | 'stable';
    significance: number;
  };
  description: string;
  timestamp: Date;
}

export interface MarketAnalysisResult {
  sentiment: MarketSentiment;
  direction: MarketDirection;
  patterns: HistoricalPattern[];
  arbitrageOpportunities: ArbitrageOpportunity[];
  riskFactors: string[];
  opportunities: string[];
  timestamp: Date;
}

class MarketAnalysisService {
  private sentimentCache = new Map<string, MarketSentiment>();
  private directionCache = new Map<string, MarketDirection>();
  private patternCache = new Map<string, HistoricalPattern[]>();
  private arbitrageCache = new Map<string, ArbitrageOpportunity[]>();

  async analyzeSentiment(marketId: string, timeframe: string = '1h'): Promise<MarketSentiment> {
    const cacheKey = `${marketId}_${timeframe}`;
    
    // Check cache first
    const cached = this.sentimentCache.get(cacheKey);
    if (cached && Date.now() - cached.timestamp.getTime() < 300000) { // 5 minutes
      return cached;
    }

    try {
      // Get market data
      const market = (await marketDataService.getAllMarkets()).find(m => m.id === marketId);
      if (!market) throw new Error('Market not found');

      const priceData = await marketDataService.getPriceData(marketId, timeframe, 100);
      
      // Analyze technical factors
      const technicalFactors = this.analyzeTechnicalFactors(priceData);
      const volumeFactors = this.analyzeVolumeFactors(priceData);
      const momentumFactors = this.analyzeMomentumFactors(priceData);
      const volatilityFactors = this.analyzeVolatilityFactors(priceData);

      const allFactors = [...technicalFactors, ...volumeFactors, ...momentumFactors, ...volatilityFactors];
      
      // Calculate overall sentiment score
      const sentimentScore = allFactors.reduce((sum, factor) => sum + (factor.impact * factor.confidence), 0) / allFactors.length;
      
      let sentiment: 'bullish' | 'bearish' | 'neutral';
      if (sentimentScore > 0.2) sentiment = 'bullish';
      else if (sentimentScore < -0.2) sentiment = 'bearish';
      else sentiment = 'neutral';

      const result: MarketSentiment = {
        marketId,
        symbol: market.symbol,
        sentiment,
        confidence: Math.abs(sentimentScore),
        score: sentimentScore,
        factors: allFactors,
        timestamp: new Date(),
        timeframe
      };

      // Cache result
      this.sentimentCache.set(cacheKey, result);
      return result;
    } catch (error) {
      console.error('Error analyzing sentiment:', error);
      throw error;
    }
  }

  async predictMarketDirection(marketId: string, timeframe: string = '4h'): Promise<MarketDirection> {
    const cacheKey = `${marketId}_${timeframe}`;
    
    // Check cache first
    const cached = this.directionCache.get(cacheKey);
    if (cached && Date.now() - cached.timestamp.getTime() < 600000) { // 10 minutes
      return cached;
    }

    try {
      const market = (await marketDataService.getAllMarkets()).find(m => m.id === marketId);
      if (!market) throw new Error('Market not found');

      const priceData = await marketDataService.getPriceData(marketId, timeframe, 200);
      
      // Use AI to analyze price patterns and predict direction
      const aiAnalysis = await aiService.analyzeMarketConditions([market.symbol], timeframe);
      
      // Calculate support and resistance levels
      const supportLevels = this.calculateSupportLevels(priceData);
      const resistanceLevels = this.calculateResistanceLevels(priceData);
      
      // Determine direction based on technical analysis
      const currentPrice = market.price;
      const recentTrend = this.calculateTrend(priceData.slice(-20));
      const volumeTrend = this.calculateVolumeTrend(priceData.slice(-20));
      
      let direction: 'up' | 'down' | 'sideways';
      let confidence = 0.5;
      let probability = 0.5;
      let targetPrice = currentPrice;
      
      const reasoning: string[] = [];
      
      if (recentTrend > 0.02) {
        direction = 'up';
        confidence = Math.min(0.9, 0.5 + recentTrend);
        probability = 0.6 + (recentTrend * 2);
        targetPrice = currentPrice * (1 + recentTrend);
        reasoning.push(`Strong upward trend detected (${(recentTrend * 100).toFixed(2)}%)`);
      } else if (recentTrend < -0.02) {
        direction = 'down';
        confidence = Math.min(0.9, 0.5 + Math.abs(recentTrend));
        probability = 0.6 + (Math.abs(recentTrend) * 2);
        targetPrice = currentPrice * (1 + recentTrend);
        reasoning.push(`Strong downward trend detected (${(recentTrend * 100).toFixed(2)}%)`);
      } else {
        direction = 'sideways';
        confidence = 0.7;
        probability = 0.6;
        reasoning.push('Price consolidating in range');
      }
      
      if (volumeTrend > 0.1) {
        reasoning.push('Increasing volume supports the move');
        confidence += 0.1;
      } else if (volumeTrend < -0.1) {
        reasoning.push('Decreasing volume may signal trend weakness');
        confidence -= 0.1;
      }

      const result: MarketDirection = {
        marketId,
        symbol: market.symbol,
        direction,
        confidence: Math.max(0.1, Math.min(0.95, confidence)),
        targetPrice,
        timeframe,
        probability: Math.max(0.1, Math.min(0.9, probability)),
        reasoning,
        supportLevels,
        resistanceLevels,
        timestamp: new Date()
      };

      // Cache result
      this.directionCache.set(cacheKey, result);
      return result;
    } catch (error) {
      console.error('Error predicting market direction:', error);
      throw error;
    }
  }

  async detectArbitrageOpportunities(markets?: string[]): Promise<ArbitrageOpportunity[]> {
    const cacheKey = markets?.join(',') || 'all';
    
    // Check cache first
    const cached = this.arbitrageCache.get(cacheKey);
    if (cached && Date.now() - cached[0]?.timestamp.getTime() < 30000) { // 30 seconds
      return cached;
    }

    try {
      const allMarkets = await marketDataService.getAllMarkets();
      const targetMarkets = markets ? 
        allMarkets.filter(m => markets.includes(m.symbol)) : 
        allMarkets.slice(0, 100); // Limit to top 100 for performance

      const opportunities: ArbitrageOpportunity[] = [];

      // Cross-exchange arbitrage detection
      const marketsBySymbol = new Map<string, Market[]>();
      targetMarkets.forEach(market => {
        const symbol = market.symbol;
        if (!marketsBySymbol.has(symbol)) {
          marketsBySymbol.set(symbol, []);
        }
        marketsBySymbol.get(symbol)!.push(market);
      });

      for (const [symbol, symbolMarkets] of marketsBySymbol) {
        if (symbolMarkets.length < 2) continue;

        // Find price differences between exchanges
        for (let i = 0; i < symbolMarkets.length; i++) {
          for (let j = i + 1; j < symbolMarkets.length; j++) {
            const market1 = symbolMarkets[i];
            const market2 = symbolMarkets[j];
            
            const priceDiff = Math.abs(market1.price - market2.price);
            const avgPrice = (market1.price + market2.price) / 2;
            const profitPercent = (priceDiff / avgPrice) * 100;

            if (profitPercent > 0.5) { // Minimum 0.5% profit
              const buyMarket = market1.price < market2.price ? market1 : market2;
              const sellMarket = market1.price < market2.price ? market2 : market1;
              
              const minVolume = Math.min(buyMarket.volume24h, sellMarket.volume24h);
              const estimatedVolume = minVolume * 0.01; // 1% of daily volume
              const profitAmount = (priceDiff * estimatedVolume) * 0.8; // Account for fees

              opportunities.push({
                id: `cross_${buyMarket.id}_${sellMarket.id}_${Date.now()}`,
                type: 'cross_exchange',
                markets: {
                  buy: { marketId: buyMarket.id, exchange: buyMarket.exchange, price: buyMarket.price },
                  sell: { marketId: sellMarket.id, exchange: sellMarket.exchange, price: sellMarket.price }
                },
                profitPercent,
                profitAmount,
                volume: estimatedVolume,
                risk: profitPercent > 2 ? 'high' : profitPercent > 1 ? 'medium' : 'low',
                timeToExpiry: 300, // 5 minutes
                confidence: Math.min(0.9, profitPercent / 5),
                requirements: [
                  `Account on ${buyMarket.exchange}`,
                  `Account on ${sellMarket.exchange}`,
                  'Sufficient balance for arbitrage',
                  'Fast execution capability'
                ],
                timestamp: new Date()
              });
            }
          }
        }
      }

      // Sort by profit potential
      opportunities.sort((a, b) => b.profitPercent - a.profitPercent);

      // Cache result
      this.arbitrageCache.set(cacheKey, opportunities.slice(0, 20)); // Keep top 20
      return opportunities.slice(0, 20);
    } catch (error) {
      console.error('Error detecting arbitrage opportunities:', error);
      return [];
    }
  }

  async recognizeHistoricalPatterns(marketId: string, timeframe: string = '1d'): Promise<HistoricalPattern[]> {
    const cacheKey = `${marketId}_${timeframe}`;
    
    // Check cache first
    const cached = this.patternCache.get(cacheKey);
    if (cached && Date.now() - cached[0]?.timestamp.getTime() < 3600000) { // 1 hour
      return cached;
    }

    try {
      const market = (await marketDataService.getAllMarkets()).find(m => m.id === marketId);
      if (!market) throw new Error('Market not found');

      const priceData = await marketDataService.getPriceData(marketId, timeframe, 500);
      const patterns: HistoricalPattern[] = [];

      // Detect various patterns
      patterns.push(...this.detectHeadAndShoulders(market, priceData, timeframe));
      patterns.push(...this.detectDoubleTopBottom(market, priceData, timeframe));
      patterns.push(...this.detectTriangles(market, priceData, timeframe));
      patterns.push(...this.detectFlags(market, priceData, timeframe));

      // Sort by confidence
      patterns.sort((a, b) => b.confidence - a.confidence);

      // Cache result
      this.patternCache.set(cacheKey, patterns);
      return patterns;
    } catch (error) {
      console.error('Error recognizing patterns:', error);
      return [];
    }
  }

  async getComprehensiveAnalysis(marketId: string): Promise<MarketAnalysisResult> {
    try {
      const [sentiment, direction, patterns, arbitrageOpportunities] = await Promise.all([
        this.analyzeSentiment(marketId),
        this.predictMarketDirection(marketId),
        this.recognizeHistoricalPatterns(marketId),
        this.detectArbitrageOpportunities([marketId])
      ]);

      // Generate risk factors and opportunities
      const riskFactors: string[] = [];
      const opportunities: string[] = [];

      if (sentiment.sentiment === 'bearish' && sentiment.confidence > 0.7) {
        riskFactors.push('Strong bearish sentiment detected');
      }
      
      if (direction.direction === 'down' && direction.confidence > 0.7) {
        riskFactors.push('Technical analysis suggests downward movement');
      }

      if (patterns.some(p => p.confidence > 0.8 && p.expectedOutcome.direction === 'up')) {
        opportunities.push('Strong bullish pattern formation detected');
      }

      if (arbitrageOpportunities.length > 0) {
        opportunities.push(`${arbitrageOpportunities.length} arbitrage opportunities available`);
      }

      return {
        sentiment,
        direction,
        patterns,
        arbitrageOpportunities,
        riskFactors,
        opportunities,
        timestamp: new Date()
      };
    } catch (error) {
      console.error('Error getting comprehensive analysis:', error);
      throw error;
    }
  }

  // Helper methods for technical analysis
  private analyzeTechnicalFactors(priceData: PriceData[]): SentimentFactor[] {
    const factors: SentimentFactor[] = [];
    
    if (priceData.length < 20) return factors;

    // Moving average analysis
    const sma20 = this.calculateSMA(priceData.slice(-20).map(p => p.close));
    const sma50 = this.calculateSMA(priceData.slice(-50).map(p => p.close));
    const currentPrice = priceData[priceData.length - 1].close;

    if (currentPrice > sma20 && sma20 > sma50) {
      factors.push({
        type: 'technical',
        description: 'Price above moving averages (bullish)',
        impact: 0.3,
        confidence: 0.8
      });
    } else if (currentPrice < sma20 && sma20 < sma50) {
      factors.push({
        type: 'technical',
        description: 'Price below moving averages (bearish)',
        impact: -0.3,
        confidence: 0.8
      });
    }

    return factors;
  }

  private analyzeVolumeFactors(priceData: PriceData[]): SentimentFactor[] {
    const factors: SentimentFactor[] = [];
    
    if (priceData.length < 10) return factors;

    const recentVolume = priceData.slice(-5).reduce((sum, p) => sum + p.volume, 0) / 5;
    const historicalVolume = priceData.slice(-20, -5).reduce((sum, p) => sum + p.volume, 0) / 15;
    
    const volumeRatio = recentVolume / historicalVolume;

    if (volumeRatio > 1.5) {
      factors.push({
        type: 'volume',
        description: 'Above average volume (increased interest)',
        impact: 0.2,
        confidence: 0.7
      });
    } else if (volumeRatio < 0.5) {
      factors.push({
        type: 'volume',
        description: 'Below average volume (decreased interest)',
        impact: -0.1,
        confidence: 0.6
      });
    }

    return factors;
  }

  private analyzeMomentumFactors(priceData: PriceData[]): SentimentFactor[] {
    const factors: SentimentFactor[] = [];
    
    if (priceData.length < 14) return factors;

    // RSI calculation
    const rsi = this.calculateRSI(priceData.map(p => p.close));
    
    if (rsi > 70) {
      factors.push({
        type: 'momentum',
        description: 'Overbought conditions (RSI > 70)',
        impact: -0.2,
        confidence: 0.8
      });
    } else if (rsi < 30) {
      factors.push({
        type: 'momentum',
        description: 'Oversold conditions (RSI < 30)',
        impact: 0.2,
        confidence: 0.8
      });
    }

    return factors;
  }

  private analyzeVolatilityFactors(priceData: PriceData[]): SentimentFactor[] {
    const factors: SentimentFactor[] = [];
    
    if (priceData.length < 20) return factors;

    const returns = priceData.slice(1).map((p, i) => 
      (p.close - priceData[i].close) / priceData[i].close
    );
    
    const volatility = Math.sqrt(returns.reduce((sum, r) => sum + r * r, 0) / returns.length);
    
    if (volatility > 0.05) { // 5% daily volatility
      factors.push({
        type: 'volatility',
        description: 'High volatility detected',
        impact: -0.1,
        confidence: 0.7
      });
    }

    return factors;
  }

  private calculateSMA(prices: number[]): number {
    return prices.reduce((sum, price) => sum + price, 0) / prices.length;
  }

  private calculateRSI(prices: number[], period: number = 14): number {
    if (prices.length < period + 1) return 50;

    const gains: number[] = [];
    const losses: number[] = [];

    for (let i = 1; i < prices.length; i++) {
      const change = prices[i] - prices[i - 1];
      gains.push(change > 0 ? change : 0);
      losses.push(change < 0 ? Math.abs(change) : 0);
    }

    const avgGain = gains.slice(-period).reduce((sum, gain) => sum + gain, 0) / period;
    const avgLoss = losses.slice(-period).reduce((sum, loss) => sum + loss, 0) / period;

    if (avgLoss === 0) return 100;
    
    const rs = avgGain / avgLoss;
    return 100 - (100 / (1 + rs));
  }

  private calculateTrend(priceData: PriceData[]): number {
    if (priceData.length < 2) return 0;
    
    const firstPrice = priceData[0].close;
    const lastPrice = priceData[priceData.length - 1].close;
    
    return (lastPrice - firstPrice) / firstPrice;
  }

  private calculateVolumeTrend(priceData: PriceData[]): number {
    if (priceData.length < 2) return 0;
    
    const firstHalf = priceData.slice(0, Math.floor(priceData.length / 2));
    const secondHalf = priceData.slice(Math.floor(priceData.length / 2));
    
    const firstAvgVolume = firstHalf.reduce((sum, p) => sum + p.volume, 0) / firstHalf.length;
    const secondAvgVolume = secondHalf.reduce((sum, p) => sum + p.volume, 0) / secondHalf.length;
    
    return (secondAvgVolume - firstAvgVolume) / firstAvgVolume;
  }

  private calculateSupportLevels(priceData: PriceData[]): number[] {
    const lows = priceData.map(p => p.low).sort((a, b) => a - b);
    const levels: number[] = [];
    
    // Find significant low levels
    for (let i = 0; i < lows.length - 1; i++) {
      const level = lows[i];
      const occurrences = lows.filter(low => Math.abs(low - level) / level < 0.02).length;
      
      if (occurrences >= 2 && !levels.some(l => Math.abs(l - level) / level < 0.02)) {
        levels.push(level);
      }
    }
    
    return levels.slice(0, 5); // Return top 5 support levels
  }

  private calculateResistanceLevels(priceData: PriceData[]): number[] {
    const highs = priceData.map(p => p.high).sort((a, b) => b - a);
    const levels: number[] = [];
    
    // Find significant high levels
    for (let i = 0; i < highs.length - 1; i++) {
      const level = highs[i];
      const occurrences = highs.filter(high => Math.abs(high - level) / level < 0.02).length;
      
      if (occurrences >= 2 && !levels.some(l => Math.abs(l - level) / level < 0.02)) {
        levels.push(level);
      }
    }
    
    return levels.slice(0, 5); // Return top 5 resistance levels
  }

  // Pattern detection methods (simplified implementations)
  private detectHeadAndShoulders(market: Market, priceData: PriceData[], timeframe: string): HistoricalPattern[] {
    // Simplified head and shoulders detection
    // In a real implementation, this would be much more sophisticated
    return [];
  }

  private detectDoubleTopBottom(market: Market, priceData: PriceData[], timeframe: string): HistoricalPattern[] {
    // Simplified double top/bottom detection
    return [];
  }

  private detectTriangles(market: Market, priceData: PriceData[], timeframe: string): HistoricalPattern[] {
    // Simplified triangle pattern detection
    return [];
  }

  private detectFlags(market: Market, priceData: PriceData[], timeframe: string): HistoricalPattern[] {
    // Simplified flag pattern detection
    return [];
  }
}

export const marketAnalysisService = new MarketAnalysisService();