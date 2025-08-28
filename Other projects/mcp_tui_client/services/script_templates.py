"""
Script Templates and Examples Library

Provides script templates, examples, and snippets for HaasScript development.
"""

import json
from datetime import datetime
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum

from ..utils.logging import get_logger


class TemplateCategory(Enum):
    """Template category enumeration"""
    BASIC = "basic"
    INDICATORS = "indicators"
    STRATEGIES = "strategies"
    UTILITIES = "utilities"
    ADVANCED = "advanced"


@dataclass
class ScriptTemplate:
    """Script template definition"""
    id: str
    name: str
    description: str
    category: TemplateCategory
    content: str
    parameters: List[Dict[str, Any]] = field(default_factory=list)
    tags: Set[str] = field(default_factory=set)
    difficulty: str = "beginner"  # beginner, intermediate, advanced
    estimated_time: str = "5 minutes"
    author: str = "HaasOnline"
    version: str = "1.0.0"
    created_at: datetime = field(default_factory=datetime.now)
    usage_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'category': self.category.value,
            'content': self.content,
            'parameters': self.parameters,
            'tags': list(self.tags),
            'difficulty': self.difficulty,
            'estimated_time': self.estimated_time,
            'author': self.author,
            'version': self.version,
            'created_at': self.created_at.isoformat(),
            'usage_count': self.usage_count
        }


class ScriptTemplateLibrary:
    """Script template and examples library"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.templates: Dict[str, ScriptTemplate] = {}
        self._initialize_templates()
    
    def _initialize_templates(self) -> None:
        """Initialize built-in templates"""
        self._create_basic_templates()
        self._create_indicator_templates()
        self._create_strategy_templates()
        self._create_utility_templates()
        self._create_advanced_templates()
        
        self.logger.info(f"Initialized {len(self.templates)} script templates")
    
    def _create_basic_templates(self) -> None:
        """Create basic templates"""
        # Hello World template
        self.templates["hello_world"] = ScriptTemplate(
            id="hello_world",
            name="Hello World",
            description="Basic script template with print statement",
            category=TemplateCategory.BASIC,
            content='''// Hello World Script
// This is a basic HaasScript template

// Print a welcome message
Print("Hello, HaasOnline World!")

// Get current price
currentPrice = Close
Print("Current price: " + ToString(currentPrice))

// Simple condition
if currentPrice > 0
    Print("Price is positive")
endif''',
            tags={"beginner", "example", "print"},
            difficulty="beginner",
            estimated_time="2 minutes"
        )
        
        # Variable Declaration template
        self.templates["variables"] = ScriptTemplate(
            id="variables",
            name="Variable Declaration",
            description="Examples of variable declaration and usage",
            category=TemplateCategory.BASIC,
            content='''// Variable Declaration Examples

// Number variables
price = 100.50
volume = 1000
percentage = 0.15

// String variables
symbol = "BTC"
message = "Trading " + symbol

// Boolean variables
isActive = true
hasPosition = false

// Array variables (if supported)
prices = [100, 101, 102, 103, 104]

// Print variables
Print("Symbol: " + symbol)
Print("Price: " + ToString(price))
Print("Volume: " + ToString(volume))
Print("Active: " + ToString(isActive))''',
            tags={"beginner", "variables", "basics"},
            difficulty="beginner",
            estimated_time="3 minutes"
        )
    
    def _create_indicator_templates(self) -> None:
        """Create technical indicator templates"""
        # Simple Moving Average
        self.templates["sma_basic"] = ScriptTemplate(
            id="sma_basic",
            name="Simple Moving Average",
            description="Basic SMA calculation and usage",
            category=TemplateCategory.INDICATORS,
            content='''// Simple Moving Average Example

// Parameters
smaPeriod = 20

// Calculate SMA
sma = SMA(Close, smaPeriod)

// Print current values
Print("Current Price: " + ToString(Close))
Print("SMA(" + ToString(smaPeriod) + "): " + ToString(sma))

// Check trend
if Close > sma
    Print("Price is above SMA - Uptrend")
else
    Print("Price is below SMA - Downtrend")
endif

// Check crossover
if CrossOver(Close, sma)
    Print("Price crossed above SMA - Buy signal")
endif

if CrossUnder(Close, sma)
    Print("Price crossed below SMA - Sell signal")
endif''',
            parameters=[
                {"name": "smaPeriod", "type": "int", "default": 20, "description": "SMA period"}
            ],
            tags={"sma", "indicator", "trend"},
            difficulty="beginner",
            estimated_time="5 minutes"
        )
        
        # RSI Indicator
        self.templates["rsi_basic"] = ScriptTemplate(
            id="rsi_basic",
            name="RSI Indicator",
            description="RSI calculation with overbought/oversold levels",
            category=TemplateCategory.INDICATORS,
            content='''// RSI Indicator Example

// Parameters
rsiPeriod = 14
overboughtLevel = 70
oversoldLevel = 30

// Calculate RSI
rsi = RSI(Close, rsiPeriod)

// Print current RSI
Print("RSI(" + ToString(rsiPeriod) + "): " + ToString(rsi))

// Check overbought condition
if rsi > overboughtLevel
    Print("RSI Overbought - Consider selling")
endif

// Check oversold condition
if rsi < oversoldLevel
    Print("RSI Oversold - Consider buying")
endif

// Check RSI momentum
if rsi > 50
    Print("RSI above 50 - Bullish momentum")
else
    Print("RSI below 50 - Bearish momentum")
endif''',
            parameters=[
                {"name": "rsiPeriod", "type": "int", "default": 14, "description": "RSI period"},
                {"name": "overboughtLevel", "type": "float", "default": 70, "description": "Overbought threshold"},
                {"name": "oversoldLevel", "type": "float", "default": 30, "description": "Oversold threshold"}
            ],
            tags={"rsi", "indicator", "momentum"},
            difficulty="beginner",
            estimated_time="7 minutes"
        )
    
    def _create_strategy_templates(self) -> None:
        """Create trading strategy templates"""
        # Simple SMA Strategy
        self.templates["sma_strategy"] = ScriptTemplate(
            id="sma_strategy",
            name="SMA Crossover Strategy",
            description="Simple moving average crossover trading strategy",
            category=TemplateCategory.STRATEGIES,
            content='''// SMA Crossover Strategy

// Parameters
fastPeriod = 10
slowPeriod = 20
tradeAmount = 100

// Calculate moving averages
fastSMA = SMA(Close, fastPeriod)
slowSMA = SMA(Close, slowPeriod)

// Print current values
Print("Fast SMA: " + ToString(fastSMA))
Print("Slow SMA: " + ToString(slowSMA))
Print("Current Position: " + ToString(Position))

// Buy signal: Fast SMA crosses above Slow SMA
if CrossOver(fastSMA, slowSMA) and Position == 0
    Buy(tradeAmount, Close)
    Print("BUY SIGNAL: Fast SMA crossed above Slow SMA")
    Alert("SMA Strategy: Buy signal triggered", "info")
endif

// Sell signal: Fast SMA crosses below Slow SMA
if CrossUnder(fastSMA, slowSMA) and Position > 0
    Sell(Position, Close)
    Print("SELL SIGNAL: Fast SMA crossed below Slow SMA")
    Alert("SMA Strategy: Sell signal triggered", "info")
endif''',
            parameters=[
                {"name": "fastPeriod", "type": "int", "default": 10, "description": "Fast SMA period"},
                {"name": "slowPeriod", "type": "int", "default": 20, "description": "Slow SMA period"},
                {"name": "tradeAmount", "type": "float", "default": 100, "description": "Trade amount"}
            ],
            tags={"strategy", "sma", "crossover", "trading"},
            difficulty="intermediate",
            estimated_time="15 minutes"
        )
        
        # RSI Mean Reversion Strategy
        self.templates["rsi_strategy"] = ScriptTemplate(
            id="rsi_strategy",
            name="RSI Mean Reversion",
            description="RSI-based mean reversion trading strategy",
            category=TemplateCategory.STRATEGIES,
            content='''// RSI Mean Reversion Strategy

// Parameters
rsiPeriod = 14
oversoldLevel = 30
overboughtLevel = 70
tradeAmount = 100
stopLossPercent = 0.02
takeProfitPercent = 0.04

// Calculate RSI
rsi = RSI(Close, rsiPeriod)

// Track entry price
entryPrice = 0

// Buy on oversold condition
if rsi < oversoldLevel and Position == 0
    Buy(tradeAmount, Close)
    entryPrice = Close
    Print("BUY: RSI oversold at " + ToString(rsi))
    Alert("RSI Strategy: Oversold buy signal", "info")
endif

// Sell on overbought condition
if rsi > overboughtLevel and Position > 0
    Sell(Position, Close)
    Print("SELL: RSI overbought at " + ToString(rsi))
    Alert("RSI Strategy: Overbought sell signal", "info")
endif

// Risk management
if Position > 0 and entryPrice > 0
    // Stop loss
    if Close < entryPrice * (1 - stopLossPercent)
        Sell(Position, Close)
        Print("STOP LOSS: Price fell below " + ToString(stopLossPercent * 100) + "%")
    endif
    
    // Take profit
    if Close > entryPrice * (1 + takeProfitPercent)
        Sell(Position, Close)
        Print("TAKE PROFIT: Price rose above " + ToString(takeProfitPercent * 100) + "%")
    endif
endif''',
            parameters=[
                {"name": "rsiPeriod", "type": "int", "default": 14, "description": "RSI period"},
                {"name": "oversoldLevel", "type": "float", "default": 30, "description": "Oversold threshold"},
                {"name": "overboughtLevel", "type": "float", "default": 70, "description": "Overbought threshold"},
                {"name": "tradeAmount", "type": "float", "default": 100, "description": "Trade amount"},
                {"name": "stopLossPercent", "type": "float", "default": 0.02, "description": "Stop loss percentage"},
                {"name": "takeProfitPercent", "type": "float", "default": 0.04, "description": "Take profit percentage"}
            ],
            tags={"strategy", "rsi", "mean-reversion", "risk-management"},
            difficulty="intermediate",
            estimated_time="20 minutes"
        )
    
    def _create_utility_templates(self) -> None:
        """Create utility templates"""
        # Logging Template
        self.templates["logging"] = ScriptTemplate(
            id="logging",
            name="Logging and Alerts",
            description="Examples of logging and alert functionality",
            category=TemplateCategory.UTILITIES,
            content='''// Logging and Alerts Example

// Basic logging
Print("Script started at: " + ToString(Timestamp))

// Log with different levels
Log("This is an info message", "info")
Log("This is a warning message", "warning")
Log("This is an error message", "error")

// Conditional logging
if Close > Open
    Print("Green candle: Close (" + ToString(Close) + ") > Open (" + ToString(Open) + ")")
else
    Print("Red candle: Close (" + ToString(Close) + ") <= Open (" + ToString(Open) + ")")
endif

// Alerts for important events
if Volume > Average(Volume, 20) * 2
    Alert("High volume detected: " + ToString(Volume), "warning")
endif

// Performance logging
profit = Equity - 10000  // Assuming starting balance of 10000
Print("Current P&L: " + ToString(profit))

if profit > 0
    Alert("Strategy is profitable: +" + ToString(profit), "success")
elseif profit < -500
    Alert("Strategy has significant loss: " + ToString(profit), "error")
endif''',
            tags={"logging", "alerts", "debugging", "monitoring"},
            difficulty="beginner",
            estimated_time="8 minutes"
        )
    
    def _create_advanced_templates(self) -> None:
        """Create advanced templates"""
        # Multi-Timeframe Analysis
        self.templates["multi_timeframe"] = ScriptTemplate(
            id="multi_timeframe",
            name="Multi-Timeframe Analysis",
            description="Advanced multi-timeframe analysis template",
            category=TemplateCategory.ADVANCED,
            content='''// Multi-Timeframe Analysis Template

// Parameters
shortTF = 5    // 5-minute timeframe
mediumTF = 15  // 15-minute timeframe
longTF = 60    // 1-hour timeframe

// Calculate indicators on different timeframes
// Note: This is a conceptual example - actual implementation
// would depend on HaasOnline's multi-timeframe capabilities

// Short-term trend (5min)
shortSMA = SMA(Close, 10)
shortTrend = Close > shortSMA

// Medium-term trend (15min)
mediumSMA = SMA(Close, 20)
mediumTrend = Close > mediumSMA

// Long-term trend (1hour)
longSMA = SMA(Close, 50)
longTrend = Close > longSMA

// Print trend analysis
Print("=== Multi-Timeframe Analysis ===")
Print("Short-term (5m): " + ToString(shortTrend))
Print("Medium-term (15m): " + ToString(mediumTrend))
Print("Long-term (1h): " + ToString(longTrend))

// Trading logic based on trend alignment
allTrendsUp = shortTrend and mediumTrend and longTrend
allTrendsDown = not shortTrend and not mediumTrend and not longTrend

if allTrendsUp and Position == 0
    Buy(100, Close)
    Print("STRONG BUY: All timeframes bullish")
    Alert("Multi-TF: Strong buy signal", "success")
endif

if allTrendsDown and Position > 0
    Sell(Position, Close)
    Print("STRONG SELL: All timeframes bearish")
    Alert("Multi-TF: Strong sell signal", "warning")
endif''',
            tags={"advanced", "multi-timeframe", "trend-analysis"},
            difficulty="advanced",
            estimated_time="30 minutes"
        )
    
    def get_template(self, template_id: str) -> Optional[ScriptTemplate]:
        """Get template by ID"""
        return self.templates.get(template_id)
    
    def list_templates(self, category: TemplateCategory = None) -> List[ScriptTemplate]:
        """List templates, optionally filtered by category"""
        templates = list(self.templates.values())
        
        if category:
            templates = [t for t in templates if t.category == category]
        
        return sorted(templates, key=lambda t: t.name)
    
    def search_templates(self, query: str) -> List[ScriptTemplate]:
        """Search templates by name, description, or tags"""
        query_lower = query.lower()
        results = []
        
        for template in self.templates.values():
            # Search in name and description
            if (query_lower in template.name.lower() or 
                query_lower in template.description.lower()):
                results.append(template)
                continue
            
            # Search in tags
            if any(query_lower in tag.lower() for tag in template.tags):
                results.append(template)
        
        return sorted(results, key=lambda t: t.usage_count, reverse=True)
    
    def get_categories(self) -> List[Tuple[TemplateCategory, int]]:
        """Get all categories with template counts"""
        category_counts = {}
        
        for template in self.templates.values():
            category = template.category
            category_counts[category] = category_counts.get(category, 0) + 1
        
        return [(cat, count) for cat, count in category_counts.items()]
    
    def get_popular_templates(self, limit: int = 10) -> List[ScriptTemplate]:
        """Get most popular templates by usage count"""
        templates = list(self.templates.values())
        templates.sort(key=lambda t: t.usage_count, reverse=True)
        return templates[:limit]
    
    def use_template(self, template_id: str) -> Optional[str]:
        """Use a template and increment usage count"""
        template = self.templates.get(template_id)
        if template:
            template.usage_count += 1
            return template.content
        return None
    
    def create_script_from_template(
        self, 
        template_id: str, 
        parameters: Dict[str, Any] = None
    ) -> Optional[str]:
        """Create script content from template with parameter substitution"""
        template = self.templates.get(template_id)
        if not template:
            return None
        
        content = template.content
        
        # Apply parameter substitutions if provided
        if parameters and template.parameters:
            for param in template.parameters:
                param_name = param["name"]
                if param_name in parameters:
                    # Simple parameter substitution
                    old_value = str(param["default"])
                    new_value = str(parameters[param_name])
                    content = content.replace(f"{param_name} = {old_value}", f"{param_name} = {new_value}")
        
        # Increment usage count
        template.usage_count += 1
        
        return content
    
    def get_template_statistics(self) -> Dict[str, Any]:
        """Get template library statistics"""
        templates = list(self.templates.values())
        
        return {
            'total_templates': len(templates),
            'categories': dict(self.get_categories()),
            'difficulty_distribution': {
                'beginner': len([t for t in templates if t.difficulty == 'beginner']),
                'intermediate': len([t for t in templates if t.difficulty == 'intermediate']),
                'advanced': len([t for t in templates if t.difficulty == 'advanced'])
            },
            'total_usage': sum(t.usage_count for t in templates),
            'most_popular': self.get_popular_templates(5),
            'newest_templates': sorted(templates, key=lambda t: t.created_at, reverse=True)[:5]
        }