import React, { useState, useEffect } from 'react';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';
import { ArbitrageOpportunity, marketAnalysisService } from '../../services/marketAnalysisService';

interface ArbitrageDetectorProps {
  selectedMarkets?: string[];
}

export const ArbitrageDetector: React.FC<ArbitrageDetectorProps> = ({
  selectedMarkets
}) => {
  const [opportunities, setOpportunities] = useState<ArbitrageOpportunity[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadOpportunities();
  }, [selectedMarkets]);

  const loadOpportunities = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await marketAnalysisService.detectArbitrageOpportunities(selectedMarkets);
      setOpportunities(data);
    } catch (err) {
      setError('Failed to detect arbitrage opportunities');
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatPrice = (price: number) => {
    if (price < 0.01) return price.toFixed(6);
    if (price < 1) return price.toFixed(4);
    return price.toFixed(2);
  };

  if (loading) {
    return (
      <Card className="p-6">
        <div className="flex items-center justify-center h-32">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <span className="ml-2">Scanning for opportunities...</span>
        </div>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">Arbitrage Opportunities</h3>
        <Button onClick={loadOpportunities} variant="outline" size="sm">
          Refresh
        </Button>
      </div>

      {error && (
        <Card className="p-4 border-red-200 bg-red-50">
          <div className="text-red-600">{error}</div>
        </Card>
      )}

      {opportunities.length > 0 ? (
        <div className="space-y-4">
          {opportunities.map((opp) => (
            <Card key={opp.id} className="p-4">
              <div className="flex justify-between items-start">
                <div>
                  <h4 className="font-medium">{opp.type.replace('_', ' ')}</h4>
                  <div className="text-sm text-gray-600">
                    Buy: {opp.markets.buy.exchange} @ ${formatPrice(opp.markets.buy.price)}
                  </div>
                  <div className="text-sm text-gray-600">
                    Sell: {opp.markets.sell.exchange} @ ${formatPrice(opp.markets.sell.price)}
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-lg font-bold text-green-600">
                    +{opp.profitPercent.toFixed(2)}%
                  </div>
                  <div className="text-sm text-gray-600">
                    ${opp.profitAmount.toFixed(2)} profit
                  </div>
                </div>
              </div>
            </Card>
          ))}
        </div>
      ) : (
        <Card className="p-8 text-center">
          <div className="text-gray-500">No arbitrage opportunities found</div>
        </Card>
      )}
    </div>
  );
};