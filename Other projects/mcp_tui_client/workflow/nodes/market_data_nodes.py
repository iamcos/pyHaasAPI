"""
Market data nodes for workflow system.

This module provides nodes for fetching and processing market data.
"""

from typing import Dict, Any, List, Optional
import asyncio
from datetime import datetime, timedelta

from ..node_base import WorkflowNode, DataType, ValidationError
from ..node_registry import register_node, NodeCategory


@register_node(
    category=NodeCategory.MARKET_DATA,
    display_name="Market Data",
    description="Fetch real-time and historical market data",
    icon="📈",
    tags=["market", "data", "price", "realtime"]
)
class MarketDataNode(WorkflowNode):
    """Node for fetching market data."""
    
    _category = NodeCategory.MARKET_DATA
    _display_name = "Market Data"
    _description = "Fetch real-time and historical market data"
    _icon = "📈"
    _tags = ["market", "data", "price", "realtime"]
    
    def _initialize_ports(self) -> None:
        """Initialize input and output ports."""
        # Input ports
        self.add_input_port("trading_pairs", DataType.LIST, True,
                           "List of trading pairs to fetch")
        self.add_input_port("data_type", DataType.STRING, False,
                           "Type of data (price, volume, orderbook)", "price")
        self.add_input_port("timeframe", DataType.STRING, False,
                           "Data timeframe (1m, 5m, 1h, 1d)", "1h")
        
        # Output ports
        self.add_output_port("market_data", DataType.MARKET_DATA,
                            "Fetched market data")
        self.add_output_port("data_timestamp", DataType.STRING,
                            "Data timestamp")
        self.add_output_port("fetch_status", DataType.STRING,
                            "Fetch operation status")
    
    def _initialize_parameters(self) -> None:
        """Initialize node parameters."""
        self.parameters = {
            "exchange": "binance",
            "limit": 1000,
            "include_volume": True,
            "cache_duration": 60,  # seconds
            "timeout": 30
        }
    
    async def execute(self, context) -> Dict[str, Any]:
        """Execute market data fetch."""
        try:
            trading_pairs = self.get_input_value("trading_pairs", context)
            data_type = self.get_input_value("data_type", context)
            timeframe = self.get_input_value("timeframe", context)
            
            if not trading_pairs:
                raise ValueError("Trading pairs list is required")
            
            mcp_client = context.execution_state.get("mcp_client")
            if not mcp_client:
                raise RuntimeError("MCP client not available")
            
            # Prepare request parameters
            request_params = {
                "trading_pairs": trading_pairs,
                "data_type": data_type,
                "timeframe": timeframe,
                "exchange": self.get_parameter("exchange", "binance"),
                "limit": self.get_parameter("limit", 1000),
                "include_volume": self.get_parameter("include_volume", True)
            }
            
            # Fetch market data
            result = await mcp_client.call_tool("get_market_data", request_params)
            
            if result.get("success"):
                market_data = result.get("data", {})
                timestamp = result.get("timestamp", datetime.now().isoformat())
                
                return {
                    "market_data": market_data,
                    "data_timestamp": timestamp,
                    "fetch_status": "success"
                }
            else:
                raise RuntimeError(f"Market data fetch failed: {result.get('error')}")
                
        except Exception as e:
            return {
                "market_data": {},
                "data_timestamp": datetime.now().isoformat(),
                "fetch_status": f"error: {str(e)}"
            }
    
    def _validate_parameters(self) -> List[ValidationError]:
        """Validate node parameters."""
        errors = []
        
        limit = self.get_parameter("limit", 1000)
        if not isinstance(limit, int) or limit <= 0 or limit > 5000:
            errors.append(ValidationError(
                node_id=self.node_id,
                message="Limit must be an integer between 1 and 5000",
                error_type="invalid_parameter"
            ))
        
        return errors


@register_node(
    category=NodeCategory.MARKET_DATA,
    display_name="Price Data",
    description="Fetch current price data for trading pairs",
    icon="💰",
    tags=["price", "current", "ticker"]
)
class PriceDataNode(WorkflowNode):
    """Node for fetching current price data."""
    
    _category = NodeCategory.MARKET_DATA
    _display_name = "Price Data"
    _description = "Fetch current price data for trading pairs"
    _icon = "💰"
    _tags = ["price", "current", "ticker"]
    
    def _initialize_ports(self) -> None:
        """Initialize input and output ports."""
        # Input ports
        self.add_input_port("trading_pairs", DataType.LIST, True,
                           "List of trading pairs")
        self.add_input_port("include_24h_stats", DataType.BOOLEAN, False,
                           "Include 24h statistics", True)
        
        # Output ports
        self.add_output_port("price_data", DataType.DICT,
                            "Current price data")
        self.add_output_port("price_changes", DataType.DICT,
                            "Price change information")
        self.add_output_port("market_summary", DataType.DICT,
                            "Market summary statistics")
    
    def _initialize_parameters(self) -> None:
        """Initialize node parameters."""
        self.parameters = {
            "exchange": "binance",
            "currency_format": "USDT",
            "precision": 8,
            "include_bid_ask": True
        }
    
    async def execute(self, context) -> Dict[str, Any]:
        """Execute price data fetch."""
        try:
            trading_pairs = self.get_input_value("trading_pairs", context)
            include_24h_stats = self.get_input_value("include_24h_stats", context)
            
            mcp_client = context.execution_state.get("mcp_client")
            if not mcp_client:
                raise RuntimeError("MCP client not available")
            
            # Fetch price data for each pair
            price_data = {}
            price_changes = {}
            
            for pair in trading_pairs:
                result = await mcp_client.call_tool("get_ticker_price", {
                    "trading_pair": pair,
                    "exchange": self.get_parameter("exchange", "binance"),
                    "include_24h_stats": include_24h_stats,
                    "include_bid_ask": self.get_parameter("include_bid_ask", True)
                })
                
                if result.get("success"):
                    ticker_data = result.get("data", {})
                    price_data[pair] = {
                        "price": ticker_data.get("price", 0),
                        "bid": ticker_data.get("bid", 0),
                        "ask": ticker_data.get("ask", 0),
                        "volume": ticker_data.get("volume", 0),
                        "timestamp": ticker_data.get("timestamp", "")
                    }
                    
                    if include_24h_stats:
                        price_changes[pair] = {
                            "change_24h": ticker_data.get("change_24h", 0),
                            "change_percent_24h": ticker_data.get("change_percent_24h", 0),
                            "high_24h": ticker_data.get("high_24h", 0),
                            "low_24h": ticker_data.get("low_24h", 0),
                            "volume_24h": ticker_data.get("volume_24h", 0)
                        }
            
            # Generate market summary
            market_summary = self._generate_market_summary(price_data, price_changes)
            
            return {
                "price_data": price_data,
                "price_changes": price_changes,
                "market_summary": market_summary
            }
            
        except Exception as e:
            return {
                "price_data": {},
                "price_changes": {},
                "market_summary": {"error": str(e)}
            }
    
    def _generate_market_summary(self, price_data: Dict, price_changes: Dict) -> Dict[str, Any]:
        """Generate market summary statistics."""
        if not price_data:
            return {}
        
        summary = {
            "total_pairs": len(price_data),
            "timestamp": datetime.now().isoformat()
        }
        
        if price_changes:
            changes = [data.get("change_percent_24h", 0) for data in price_changes.values()]
            if changes:
                summary["avg_change_24h"] = sum(changes) / len(changes)
                summary["positive_changes"] = len([c for c in changes if c > 0])
                summary["negative_changes"] = len([c for c in changes if c < 0])
                summary["max_gainer"] = max(changes)
                summary["max_loser"] = min(changes)
        
        # Volume summary
        volumes = [data.get("volume", 0) for data in price_data.values()]
        if volumes:
            summary["total_volume"] = sum(volumes)
            summary["avg_volume"] = sum(volumes) / len(volumes)
        
        return summary


@register_node(
    category=NodeCategory.MARKET_DATA,
    display_name="Historical Data",
    description="Fetch historical OHLCV data",
    icon="📊",
    tags=["historical", "ohlcv", "candles"]
)
class HistoricalDataNode(WorkflowNode):
    """Node for fetching historical market data."""
    
    _category = NodeCategory.MARKET_DATA
    _display_name = "Historical Data"
    _description = "Fetch historical OHLCV data"
    _icon = "📊"
    _tags = ["historical", "ohlcv", "candles"]
    
    def _initialize_ports(self) -> None:
        """Initialize input and output ports."""
        # Input ports
        self.add_input_port("trading_pair", DataType.STRING, True,
                           "Trading pair to fetch")
        self.add_input_port("timeframe", DataType.STRING, True,
                           "Timeframe (1m, 5m, 1h, 1d)")
        self.add_input_port("start_date", DataType.STRING, False,
                           "Start date (ISO format)")
        self.add_input_port("end_date", DataType.STRING, False,
                           "End date (ISO format)")
        self.add_input_port("limit", DataType.INTEGER, False,
                           "Number of candles to fetch", 1000)
        
        # Output ports
        self.add_output_port("ohlcv_data", DataType.LIST,
                            "OHLCV candle data")
        self.add_output_port("data_info", DataType.DICT,
                            "Data information and metadata")
        self.add_output_port("fetch_status", DataType.STRING,
                            "Fetch operation status")
    
    def _initialize_parameters(self) -> None:
        """Initialize node parameters."""
        self.parameters = {
            "exchange": "binance",
            "validate_data": True,
            "fill_gaps": False,
            "include_volume": True,
            "timeout": 60
        }
    
    async def execute(self, context) -> Dict[str, Any]:
        """Execute historical data fetch."""
        try:
            trading_pair = self.get_input_value("trading_pair", context)
            timeframe = self.get_input_value("timeframe", context)
            start_date = self.get_input_value("start_date", context)
            end_date = self.get_input_value("end_date", context)
            limit = self.get_input_value("limit", context)
            
            mcp_client = context.execution_state.get("mcp_client")
            if not mcp_client:
                raise RuntimeError("MCP client not available")
            
            # Prepare request parameters
            request_params = {
                "trading_pair": trading_pair,
                "timeframe": timeframe,
                "exchange": self.get_parameter("exchange", "binance"),
                "limit": limit,
                "include_volume": self.get_parameter("include_volume", True)
            }
            
            if start_date:
                request_params["start_date"] = start_date
            if end_date:
                request_params["end_date"] = end_date
            
            # Fetch historical data
            result = await mcp_client.call_tool("get_historical_data", request_params)
            
            if result.get("success"):
                ohlcv_data = result.get("data", [])
                
                # Validate data if requested
                if self.get_parameter("validate_data", True):
                    ohlcv_data = self._validate_ohlcv_data(ohlcv_data)
                
                # Fill gaps if requested
                if self.get_parameter("fill_gaps", False):
                    ohlcv_data = self._fill_data_gaps(ohlcv_data, timeframe)
                
                # Generate data info
                data_info = self._generate_data_info(ohlcv_data, trading_pair, timeframe)
                
                return {
                    "ohlcv_data": ohlcv_data,
                    "data_info": data_info,
                    "fetch_status": "success"
                }
            else:
                raise RuntimeError(f"Historical data fetch failed: {result.get('error')}")
                
        except Exception as e:
            return {
                "ohlcv_data": [],
                "data_info": {"error": str(e)},
                "fetch_status": f"error: {str(e)}"
            }
    
    def _validate_ohlcv_data(self, ohlcv_data: List[Dict]) -> List[Dict]:
        """Validate OHLCV data for consistency."""
        validated_data = []
        
        for candle in ohlcv_data:
            # Check required fields
            required_fields = ["timestamp", "open", "high", "low", "close"]
            if not all(field in candle for field in required_fields):
                continue
            
            # Validate OHLC relationships
            open_price = candle["open"]
            high_price = candle["high"]
            low_price = candle["low"]
            close_price = candle["close"]
            
            # High should be >= max(open, close) and low should be <= min(open, close)
            if (high_price >= max(open_price, close_price) and 
                low_price <= min(open_price, close_price) and
                all(price > 0 for price in [open_price, high_price, low_price, close_price])):
                validated_data.append(candle)
        
        return validated_data
    
    def _fill_data_gaps(self, ohlcv_data: List[Dict], timeframe: str) -> List[Dict]:
        """Fill gaps in OHLCV data."""
        if len(ohlcv_data) < 2:
            return ohlcv_data
        
        # Calculate timeframe interval in seconds
        timeframe_seconds = self._get_timeframe_seconds(timeframe)
        if timeframe_seconds == 0:
            return ohlcv_data
        
        filled_data = []
        
        for i in range(len(ohlcv_data)):
            filled_data.append(ohlcv_data[i])
            
            # Check for gap to next candle
            if i < len(ohlcv_data) - 1:
                current_time = datetime.fromisoformat(ohlcv_data[i]["timestamp"].replace('Z', '+00:00'))
                next_time = datetime.fromisoformat(ohlcv_data[i + 1]["timestamp"].replace('Z', '+00:00'))
                
                expected_next_time = current_time + timedelta(seconds=timeframe_seconds)
                
                # Fill gaps with synthetic candles
                while expected_next_time < next_time:
                    # Create synthetic candle with previous close as OHLC
                    prev_close = ohlcv_data[i]["close"]
                    synthetic_candle = {
                        "timestamp": expected_next_time.isoformat(),
                        "open": prev_close,
                        "high": prev_close,
                        "low": prev_close,
                        "close": prev_close,
                        "volume": 0,
                        "synthetic": True
                    }
                    filled_data.append(synthetic_candle)
                    expected_next_time += timedelta(seconds=timeframe_seconds)
        
        return filled_data
    
    def _get_timeframe_seconds(self, timeframe: str) -> int:
        """Convert timeframe string to seconds."""
        timeframe_map = {
            "1m": 60,
            "5m": 300,
            "15m": 900,
            "30m": 1800,
            "1h": 3600,
            "4h": 14400,
            "1d": 86400,
            "1w": 604800
        }
        return timeframe_map.get(timeframe, 0)
    
    def _generate_data_info(self, ohlcv_data: List[Dict], trading_pair: str, timeframe: str) -> Dict[str, Any]:
        """Generate information about the fetched data."""
        if not ohlcv_data:
            return {"error": "No data available"}
        
        info = {
            "trading_pair": trading_pair,
            "timeframe": timeframe,
            "candle_count": len(ohlcv_data),
            "start_time": ohlcv_data[0]["timestamp"],
            "end_time": ohlcv_data[-1]["timestamp"],
            "fetch_timestamp": datetime.now().isoformat()
        }
        
        # Calculate data statistics
        closes = [candle["close"] for candle in ohlcv_data]
        volumes = [candle.get("volume", 0) for candle in ohlcv_data]
        
        if closes:
            info["price_range"] = {
                "min": min(closes),
                "max": max(closes),
                "first": closes[0],
                "last": closes[-1],
                "change": closes[-1] - closes[0],
                "change_percent": ((closes[-1] - closes[0]) / closes[0]) * 100 if closes[0] != 0 else 0
            }
        
        if volumes:
            info["volume_stats"] = {
                "total": sum(volumes),
                "average": sum(volumes) / len(volumes),
                "max": max(volumes),
                "min": min(volumes)
            }
        
        # Data quality metrics
        synthetic_count = len([c for c in ohlcv_data if c.get("synthetic", False)])
        info["data_quality"] = {
            "synthetic_candles": synthetic_count,
            "real_candles": len(ohlcv_data) - synthetic_count,
            "completeness": ((len(ohlcv_data) - synthetic_count) / len(ohlcv_data)) * 100 if ohlcv_data else 0
        }
        
        return info