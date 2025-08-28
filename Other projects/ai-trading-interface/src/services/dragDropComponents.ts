import { DragDropComponent } from '../types/strategy';

export const DRAG_DROP_COMPONENTS: DragDropComponent[] = [
  // Technical Indicators
  {
    id: 'rsi',
    type: 'indicator',
    name: 'RSI',
    description: 'Relative Strength Index - momentum oscillator',
    category: 'Technical Indicators',
    icon: '📈',
    parameters: [
      {
        name: 'period',
        type: 'number',
        defaultValue: 14,
        required: true,
        description: 'Number of periods for RSI calculation',
        validation: { min: 2, max: 100 }
      },
      {
        name: 'source',
        type: 'select',
        defaultValue: 'Close',
        required: true,
        description: 'Price source for calculation',
        validation: { options: ['Open', 'High', 'Low', 'Close'] }
      }
    ],
    codeTemplate: 'var rsi${id} = RSI(${source}, ${period})'
  },
  {
    id: 'ema',
    type: 'indicator',
    name: 'EMA',
    description: 'Exponential Moving Average',
    category: 'Technical Indicators',
    icon: '📊',
    parameters: [
      {
        name: 'period',
        type: 'number',
        defaultValue: 20,
        required: true,
        description: 'Number of periods for EMA calculation',
        validation: { min: 1, max: 200 }
      },
      {
        name: 'source',
        type: 'select',
        defaultValue: 'Close',
        required: true,
        description: 'Price source for calculation',
        validation: { options: ['Open', 'High', 'Low', 'Close'] }
      }
    ],
    codeTemplate: 'var ema${id} = EMA(${source}, ${period})'
  },
  {
    id: 'macd',
    type: 'indicator',
    name: 'MACD',
    description: 'Moving Average Convergence Divergence',
    category: 'Technical Indicators',
    icon: '📉',
    parameters: [
      {
        name: 'fastPeriod',
        type: 'number',
        defaultValue: 12,
        required: true,
        description: 'Fast EMA period',
        validation: { min: 1, max: 50 }
      },
      {
        name: 'slowPeriod',
        type: 'number',
        defaultValue: 26,
        required: true,
        description: 'Slow EMA period',
        validation: { min: 1, max: 100 }
      },
      {
        name: 'signalPeriod',
        type: 'number',
        defaultValue: 9,
        required: true,
        description: 'Signal line period',
        validation: { min: 1, max: 50 }
      }
    ],
    codeTemplate: 'var macd${id} = MACD(Close, ${fastPeriod}, ${slowPeriod}, ${signalPeriod})'
  },
  {
    id: 'bb',
    type: 'indicator',
    name: 'Bollinger Bands',
    description: 'Bollinger Bands volatility indicator',
    category: 'Technical Indicators',
    icon: '📏',
    parameters: [
      {
        name: 'period',
        type: 'number',
        defaultValue: 20,
        required: true,
        description: 'Period for moving average',
        validation: { min: 2, max: 100 }
      },
      {
        name: 'deviation',
        type: 'number',
        defaultValue: 2,
        required: true,
        description: 'Standard deviation multiplier',
        validation: { min: 0.1, max: 5 }
      }
    ],
    codeTemplate: 'var bb${id} = BB(Close, ${period}, ${deviation})'
  },

  // Conditions
  {
    id: 'price_above',
    type: 'condition',
    name: 'Price Above',
    description: 'Check if price is above a value',
    category: 'Price Conditions',
    icon: '⬆️',
    parameters: [
      {
        name: 'source',
        type: 'select',
        defaultValue: 'Close',
        required: true,
        description: 'Price source to compare',
        validation: { options: ['Open', 'High', 'Low', 'Close'] }
      },
      {
        name: 'value',
        type: 'string',
        defaultValue: '100',
        required: true,
        description: 'Value or indicator to compare against'
      }
    ],
    codeTemplate: '${source} > ${value}'
  },
  {
    id: 'price_below',
    type: 'condition',
    name: 'Price Below',
    description: 'Check if price is below a value',
    category: 'Price Conditions',
    icon: '⬇️',
    parameters: [
      {
        name: 'source',
        type: 'select',
        defaultValue: 'Close',
        required: true,
        description: 'Price source to compare',
        validation: { options: ['Open', 'High', 'Low', 'Close'] }
      },
      {
        name: 'value',
        type: 'string',
        defaultValue: '100',
        required: true,
        description: 'Value or indicator to compare against'
      }
    ],
    codeTemplate: '${source} < ${value}'
  },
  {
    id: 'crossover',
    type: 'condition',
    name: 'Crossover',
    description: 'Check if one value crosses above another',
    category: 'Cross Conditions',
    icon: '🔄',
    parameters: [
      {
        name: 'source1',
        type: 'string',
        defaultValue: 'Close',
        required: true,
        description: 'First value or indicator'
      },
      {
        name: 'source2',
        type: 'string',
        defaultValue: 'ema20',
        required: true,
        description: 'Second value or indicator'
      }
    ],
    codeTemplate: 'CrossOver(${source1}, ${source2})'
  },
  {
    id: 'crossunder',
    type: 'condition',
    name: 'Crossunder',
    description: 'Check if one value crosses below another',
    category: 'Cross Conditions',
    icon: '🔄',
    parameters: [
      {
        name: 'source1',
        type: 'string',
        defaultValue: 'Close',
        required: true,
        description: 'First value or indicator'
      },
      {
        name: 'source2',
        type: 'string',
        defaultValue: 'ema20',
        required: true,
        description: 'Second value or indicator'
      }
    ],
    codeTemplate: 'CrossUnder(${source1}, ${source2})'
  },

  // Actions
  {
    id: 'buy_market',
    type: 'action',
    name: 'Buy Market',
    description: 'Execute a market buy order',
    category: 'Trading Actions',
    icon: '🟢',
    parameters: [
      {
        name: 'amount',
        type: 'string',
        defaultValue: '100',
        required: true,
        description: 'Amount to buy (can be percentage or fixed amount)'
      },
      {
        name: 'comment',
        type: 'string',
        defaultValue: 'Buy signal',
        required: false,
        description: 'Optional comment for the order'
      }
    ],
    codeTemplate: 'Buy(${amount}, "${comment}")'
  },
  {
    id: 'sell_market',
    type: 'action',
    name: 'Sell Market',
    description: 'Execute a market sell order',
    category: 'Trading Actions',
    icon: '🔴',
    parameters: [
      {
        name: 'amount',
        type: 'string',
        defaultValue: '100',
        required: true,
        description: 'Amount to sell (can be percentage or fixed amount)'
      },
      {
        name: 'comment',
        type: 'string',
        defaultValue: 'Sell signal',
        required: false,
        description: 'Optional comment for the order'
      }
    ],
    codeTemplate: 'Sell(${amount}, "${comment}")'
  },
  {
    id: 'close_position',
    type: 'action',
    name: 'Close Position',
    description: 'Close current position',
    category: 'Trading Actions',
    icon: '❌',
    parameters: [
      {
        name: 'comment',
        type: 'string',
        defaultValue: 'Close position',
        required: false,
        description: 'Optional comment for closing'
      }
    ],
    codeTemplate: 'ClosePosition("${comment}")'
  },
  {
    id: 'set_stop_loss',
    type: 'action',
    name: 'Set Stop Loss',
    description: 'Set stop loss level',
    category: 'Risk Management',
    icon: '🛡️',
    parameters: [
      {
        name: 'level',
        type: 'string',
        defaultValue: '0.95',
        required: true,
        description: 'Stop loss level (price or percentage)'
      },
      {
        name: 'type',
        type: 'select',
        defaultValue: 'percentage',
        required: true,
        description: 'Stop loss type',
        validation: { options: ['price', 'percentage'] }
      }
    ],
    codeTemplate: 'SetStopLoss(${level}, "${type}")'
  },
  {
    id: 'set_take_profit',
    type: 'action',
    name: 'Set Take Profit',
    description: 'Set take profit level',
    category: 'Risk Management',
    icon: '🎯',
    parameters: [
      {
        name: 'level',
        type: 'string',
        defaultValue: '1.05',
        required: true,
        description: 'Take profit level (price or percentage)'
      },
      {
        name: 'type',
        type: 'select',
        defaultValue: 'percentage',
        required: true,
        description: 'Take profit type',
        validation: { options: ['price', 'percentage'] }
      }
    ],
    codeTemplate: 'SetTakeProfit(${level}, "${type}")'
  },

  // Variables
  {
    id: 'number_variable',
    type: 'variable',
    name: 'Number Variable',
    description: 'Declare a number variable',
    category: 'Variables',
    icon: '🔢',
    parameters: [
      {
        name: 'name',
        type: 'string',
        defaultValue: 'myNumber',
        required: true,
        description: 'Variable name'
      },
      {
        name: 'value',
        type: 'number',
        defaultValue: 0,
        required: true,
        description: 'Initial value'
      }
    ],
    codeTemplate: 'var ${name} = ${value}'
  },
  {
    id: 'string_variable',
    type: 'variable',
    name: 'String Variable',
    description: 'Declare a string variable',
    category: 'Variables',
    icon: '📝',
    parameters: [
      {
        name: 'name',
        type: 'string',
        defaultValue: 'myString',
        required: true,
        description: 'Variable name'
      },
      {
        name: 'value',
        type: 'string',
        defaultValue: 'Hello',
        required: true,
        description: 'Initial value'
      }
    ],
    codeTemplate: 'var ${name} = "${value}"'
  },
  {
    id: 'boolean_variable',
    type: 'variable',
    name: 'Boolean Variable',
    description: 'Declare a boolean variable',
    category: 'Variables',
    icon: '✅',
    parameters: [
      {
        name: 'name',
        type: 'string',
        defaultValue: 'myBool',
        required: true,
        description: 'Variable name'
      },
      {
        name: 'value',
        type: 'boolean',
        defaultValue: false,
        required: true,
        description: 'Initial value'
      }
    ],
    codeTemplate: 'var ${name} = ${value}'
  }
];

export const getComponentsByCategory = () => {
  const categories: Record<string, DragDropComponent[]> = {};
  
  DRAG_DROP_COMPONENTS.forEach(component => {
    if (!categories[component.category]) {
      categories[component.category] = [];
    }
    categories[component.category].push(component);
  });
  
  return categories;
};

export const getComponentById = (id: string): DragDropComponent | undefined => {
  return DRAG_DROP_COMPONENTS.find(component => component.id === id);
};

export const generateCodeFromComponent = (
  component: DragDropComponent, 
  parameters: Record<string, any>,
  instanceId: string
): string => {
  let code = component.codeTemplate;
  
  // Replace parameter placeholders
  Object.entries(parameters).forEach(([key, value]) => {
    const placeholder = `\${${key}}`;
    code = code.replace(new RegExp(placeholder.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g'), value);
  });
  
  // Replace instance ID placeholder
  code = code.replace(/\${id}/g, instanceId);
  
  return code;
};