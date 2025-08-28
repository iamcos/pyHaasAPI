import React, { useState, useEffect } from 'react';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';
import { Market } from '../../types/trading';
import { MarketAnalysisResult, marketAnalysisService } from '../../services/marketAnalysisService';
import { MarketSentimentAnalysis } from './MarketSentimentAnalysis';
import { MarketDirectionPredictor } from './MarketDirectionPredictor';
import { ArbitrageDetector } from './ArbitrageDetector';
import { HistoricalPatternRecognition } from './HistoricalPatternRecognition';

interface AIMarketAnalysisDashboardProps {
  market: Market;
}

export const AIMarketAnalysisDashboard: React.FC<AIMarketAnalysisDashboardProps> = ({
  market
}) => {
  const [analysis, setAnalysis] = useState<MarketAnalysisResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'sentiment' | 'direction' | 'patterns' | 'arbitrage'>('overview');

  useEffect(() => {
    loadComprehensiveAnalysis();
  }, [market.id]);

  const loadComprehensiveAnalysis = async () => {
    try {
      setLoading(true);
      setError(null);
      const analysisData = await marketAnalysisService.getComprehensiveAnalysis(market.id);
      setAnalysis(analysisData);
    } catch (err) {
      setError('Failed to load market analysis');
      console.error('Error loading analysis:', err);
    } finally {
      setLoading(false);
    }
  };

  const tabs = [
    { id: 'overview', label: 'Overview', icon: '📊' },
    { id: 'sentiment', label: 'Sentiment', icon: '🎭' },
    { id: 'direction', label: 'Direction', icon: '🧭' },
    { id: 'patterns', label: 'Patterns', icon: '📈' },
    { id: 'arbitrage', label: 'Arbitrage', icon: '💱' }
  ];

  const renderOverview = () => {
    if (!analysis) return null;

    return (
      <div className="space-y-6">
        {/* Analysis Summary */}
        <Card className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            AI Analysis Summary for {market.symbol}
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Sentiment Summary */}
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <div className="text-2xl mb-2">
                {analysis.sentiment.sentiment === 'bullish' ? '🐂' : 
                 analysis.sentiment.sentiment === 'bearish' ? '🐻' : '⚖️'}
              </div>
              <div className="font-semibold text-gray-900 capitalize">
                {analysis.sentiment.sentiment}
              </div>
              <div className="text-sm text-gray-600">
                {(analysis.sentiment.confidence * 100).toFixed(0)}% confidence
              </div>
            </div>

            {/* Direction Summary */}
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <div className="text-2xl mb-2">
                {analysis.direction.direction === 'up' ? '📈' : 
                 analysis.direction.direction === 'down' ? '📉' : '↔️'}
              </div>
              <div className="font-semibold text-gray-900 capitalize">
                {analysis.direction.direction}
              </div>
              <div className="text-sm text-gray-600">
                {(analysis.direction.confidence * 100).toFixed(0)}% confidence
              </div>
            </div>

            {/* Patterns Summary */}
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <div className="text-2xl mb-2">🔍</div>
              <div className="font-semibold text-gray-900">
                {analysis.patterns.length} Patterns
              </div>
              <div className="text-sm text-gray-600">
                {analysis.patterns.filter(p => p.confidence > 0.8).length} high confidence
              </div>
            </div>
          </div>
        </Card>

        {/* Risk Factors & Opportunities */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Risk Factors */}
          <Card className="p-6">
            <h4 className="font-semibold text-gray-900 mb-3 flex items-center">
              <span className="mr-2">⚠️</span>
              Risk Factors
            </h4>
            {analysis.riskFactors.length > 0 ? (
              <div className="space-y-2">
                {analysis.riskFactors.map((risk, index) => (
                  <div key={index} className="flex items-start space-x-2 text-sm">
                    <div className="w-2 h-2 bg-red-500 rounded-full mt-2 flex-shrink-0" />
                    <span className="text-gray-700">{risk}</span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-sm text-gray-500 italic">
                No significant risk factors identified
              </div>
            )}
          </Card>

          {/* Opportunities */}
          <Card className="p-6">
            <h4 className="font-semibold text-gray-900 mb-3 flex items-center">
              <span className="mr-2">🎯</span>
              Opportunities
            </h4>
            {analysis.opportunities.length > 0 ? (
              <div className="space-y-2">
                {analysis.opportunities.map((opportunity, index) => (
                  <div key={index} className="flex items-start space-x-2 text-sm">
                    <div className="w-2 h-2 bg-green-500 rounded-full mt-2 flex-shrink-0" />
                    <span className="text-gray-700">{opportunity}</span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-sm text-gray-500 italic">
                No significant opportunities identified
              </div>
            )}
          </Card>
        </div>

        {/* Arbitrage Opportunities Preview */}
        {analysis.arbitrageOpportunities.length > 0 && (
          <Card className="p-6">
            <h4 className="font-semibold text-gray-900 mb-3 flex items-center">
              <span className="mr-2">💱</span>
              Arbitrage Opportunities ({analysis.arbitrageOpportunities.length})
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {analysis.arbitrageOpportunities.slice(0, 3).map((opp) => (
                <div key={opp.id} className="p-3 bg-green-50 rounded-lg border border-green-200">
                  <div className="flex justify-between items-start mb-2">
                    <div className="text-sm font-medium text-green-800">
                      {opp.type.replace('_', ' ')}
                    </div>
                    <div className="text-lg font-bold text-green-600">
                      +{opp.profitPercent.toFixed(2)}%
                    </div>
                  </div>
                  <div className="text-xs text-green-700">
                    {opp.markets.buy.exchange} → {opp.markets.sell.exchange}
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-4">
              <Button 
                onClick={() => setActiveTab('arbitrage')} 
                variant="outline" 
                size="sm"
              >
                View All Opportunities
              </Button>
            </div>
          </Card>
        )}

        {/* Analysis Timestamp */}
        <div className="text-center text-sm text-gray-500">
          Analysis completed: {analysis.timestamp.toLocaleString()}
        </div>
      </div>
    );
  };

  const renderTabContent = () => {
    switch (activeTab) {
      case 'overview':
        return renderOverview();
      case 'sentiment':
        return <MarketSentimentAnalysis market={market} />;
      case 'direction':
        return <MarketDirectionPredictor market={market} />;
      case 'patterns':
        return <HistoricalPatternRecognition market={market} />;
      case 'arbitrage':
        return <ArbitrageDetector selectedMarkets={[market.symbol]} />;
      default:
        return renderOverview();
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          <span className="ml-3 text-gray-600">Running AI market analysis...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <Card className="p-8 text-center">
        <div className="text-red-600 mb-4">⚠️ Analysis Error</div>
        <p className="text-gray-600 mb-4">{error}</p>
        <Button onClick={loadComprehensiveAnalysis} variant="primary">
          Retry Analysis
        </Button>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">
            AI Market Analysis
          </h2>
          <p className="text-gray-600">
            Comprehensive AI-powered analysis for {market.symbol}
          </p>
        </div>
        <Button onClick={loadComprehensiveAnalysis} variant="outline">
          Refresh Analysis
        </Button>
      </div>

      {/* Navigation Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`py-2 px-1 border-b-2 font-medium text-sm whitespace-nowrap ${
                activeTab === tab.id
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

      {/* Tab Content */}
      <div className="min-h-96">
        {renderTabContent()}
      </div>
    </div>
  );
};