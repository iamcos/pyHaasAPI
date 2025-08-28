import React, { useState } from 'react';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';
import { MarketFilter } from '../../types/trading';

interface MarketFiltersProps {
  filter: MarketFilter;
  onFilterChange: (filter: MarketFilter) => void;
  availableExchanges: string[];
  availableCategories: string[];
}

export const MarketFilters: React.FC<MarketFiltersProps> = ({
  filter,
  onFilterChange,
  availableExchanges,
  availableCategories
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [localFilter, setLocalFilter] = useState<MarketFilter>(filter);

  const handleApplyFilters = () => {
    onFilterChange(localFilter);
  };

  const handleClearFilters = () => {
    const emptyFilter: MarketFilter = {};
    setLocalFilter(emptyFilter);
    onFilterChange(emptyFilter);
  };

  const updateFilter = (key: keyof MarketFilter, value: any) => {
    setLocalFilter(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const toggleExchange = (exchange: string) => {
    const currentExchanges = localFilter.exchange || [];
    const newExchanges = currentExchanges.includes(exchange)
      ? currentExchanges.filter(e => e !== exchange)
      : [...currentExchanges, exchange];
    
    updateFilter('exchange', newExchanges.length > 0 ? newExchanges : undefined);
  };

  const toggleCategory = (category: string) => {
    const currentCategories = localFilter.category || [];
    const newCategories = currentCategories.includes(category)
      ? currentCategories.filter(c => c !== category)
      : [...currentCategories, category];
    
    updateFilter('category', newCategories.length > 0 ? newCategories : undefined);
  };

  const hasActiveFilters = Object.keys(filter).length > 0;

  return (
    <Card className="p-4">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-4">
          <h3 className="font-medium text-gray-900">Filters</h3>
          {hasActiveFilters && (
            <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full">
              {Object.keys(filter).length} active
            </span>
          )}
        </div>
        <div className="flex items-center space-x-2">
          <Button
            onClick={() => setIsExpanded(!isExpanded)}
            variant="outline"
            size="sm"
          >
            {isExpanded ? 'Hide Filters' : 'Show Filters'}
          </Button>
          {hasActiveFilters && (
            <Button
              onClick={handleClearFilters}
              variant="outline"
              size="sm"
            >
              Clear All
            </Button>
          )}
        </div>
      </div>

      {/* Quick Search */}
      <div className="mb-4">
        <input
          type="text"
          placeholder="Search markets by symbol, asset, or exchange..."
          value={localFilter.search || ''}
          onChange={(e) => updateFilter('search', e.target.value || undefined)}
          onKeyPress={(e) => e.key === 'Enter' && handleApplyFilters()}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>

      {isExpanded && (
        <div className="space-y-6">
          {/* Exchange Filter */}
          <div>
            <h4 className="font-medium text-gray-700 mb-2">Exchanges</h4>
            <div className="flex flex-wrap gap-2">
              {availableExchanges.slice(0, 10).map(exchange => (
                <button
                  key={exchange}
                  onClick={() => toggleExchange(exchange)}
                  className={`px-3 py-1 rounded-full text-sm transition-colors ${
                    (localFilter.exchange || []).includes(exchange)
                      ? 'bg-blue-100 text-blue-800 border border-blue-200'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {exchange}
                </button>
              ))}
            </div>
          </div>

          {/* Category Filter */}
          <div>
            <h4 className="font-medium text-gray-700 mb-2">Categories</h4>
            <div className="flex flex-wrap gap-2">
              {availableCategories.slice(0, 15).map(category => (
                <button
                  key={category}
                  onClick={() => toggleCategory(category)}
                  className={`px-3 py-1 rounded-full text-sm transition-colors ${
                    (localFilter.category || []).includes(category)
                      ? 'bg-green-100 text-green-800 border border-green-200'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {category}
                </button>
              ))}
            </div>
          </div>

          {/* Volume Range */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Min Volume (24h)
              </label>
              <input
                type="number"
                placeholder="0"
                value={localFilter.minVolume || ''}
                onChange={(e) => updateFilter('minVolume', e.target.value ? Number(e.target.value) : undefined)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Max Volume (24h)
              </label>
              <input
                type="number"
                placeholder="No limit"
                value={localFilter.maxVolume || ''}
                onChange={(e) => updateFilter('maxVolume', e.target.value ? Number(e.target.value) : undefined)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          {/* Price Range */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Min Price
              </label>
              <input
                type="number"
                step="0.000001"
                placeholder="0"
                value={localFilter.minPrice || ''}
                onChange={(e) => updateFilter('minPrice', e.target.value ? Number(e.target.value) : undefined)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Max Price
              </label>
              <input
                type="number"
                step="0.000001"
                placeholder="No limit"
                value={localFilter.maxPrice || ''}
                onChange={(e) => updateFilter('maxPrice', e.target.value ? Number(e.target.value) : undefined)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          {/* Change Range */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Min Change (24h %)
              </label>
              <input
                type="number"
                step="0.1"
                placeholder="-100"
                value={localFilter.changeRange?.min || ''}
                onChange={(e) => updateFilter('changeRange', {
                  ...localFilter.changeRange,
                  min: e.target.value ? Number(e.target.value) : undefined
                })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Max Change (24h %)
              </label>
              <input
                type="number"
                step="0.1"
                placeholder="1000"
                value={localFilter.changeRange?.max || ''}
                onChange={(e) => updateFilter('changeRange', {
                  ...localFilter.changeRange,
                  max: e.target.value ? Number(e.target.value) : undefined
                })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          {/* Apply/Reset Buttons */}
          <div className="flex justify-end space-x-2 pt-4 border-t">
            <Button
              onClick={handleClearFilters}
              variant="outline"
            >
              Reset
            </Button>
            <Button
              onClick={handleApplyFilters}
              variant="primary"
            >
              Apply Filters
            </Button>
          </div>
        </div>
      )}
    </Card>
  );
};