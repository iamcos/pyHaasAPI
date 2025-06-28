#!/usr/bin/env python3
"""
Enhanced MCP (Model Context Protocol) Server for pyHaasAPI

This server provides advanced AI tools for HaasOnline trading automation,
including intelligent parameter optimization, market analysis, and bot management.

Features:
- Intelligent parameter sweeping with AI-driven optimization
- Market sentiment analysis and trend detection
- Automated bot deployment and monitoring
- Portfolio optimization and risk management
- Real-time market data analysis
- Multi-exchange strategy execution

Usage:
    python enhanced_mcp_server.py
"""

import asyncio
import json
import logging
import os
import sys
import time
import random
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, Tuple
from dataclasses import dataclass, asdict
from itertools import product
from collections import defaultdict

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pyHaasAPI import api
from pyHaasAPI.model import (
    CreateLabRequest, StartLabExecutionRequest, AddBotFromLabRequest,
    GetBacktestResultRequest
)
from pyHaasAPI.price import PriceAPI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class MCPRequest:
    """MCP request structure"""
    jsonrpc: str
    id: Union[int, str]
    method: str
    params: Optional[Dict[str, Any]] = None

@dataclass
class MCPResponse:
    """MCP response structure"""
    jsonrpc: str = "2.0"
    id: Optional[Union[int, str]] = None
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None

class MarketAnalyzer:
    """AI-powered market analysis tools"""
    
    def __init__(self, executor):
        self.executor = executor
        self.price_api = PriceAPI(executor)
    
    async def analyze_market_sentiment(self, market: str, timeframe: str = "1h") -> Dict[str, Any]:
        """Analyze market sentiment using price data and volume"""
        try:
            # Get market data
            price_data = api.get_market_price(self.executor, market)
            order_book = api.get_order_book(self.executor, market, depth=20)
            trades = api.get_last_trades(self.executor, market, limit=100)
            
            # Calculate sentiment indicators
            current_price = float(price_data.get('price', 0))
            volume_24h = float(price_data.get('volume24h', 0))
            
            # Analyze order book imbalance
            bids = sum(float(bid['quantity']) for bid in order_book.get('bids', []))
            asks = sum(float(ask['quantity']) for ask in order_book.get('asks', []))
            order_imbalance = (bids - asks) / (bids + asks) if (bids + asks) > 0 else 0
            
            # Analyze recent trades
            buy_volume = sum(float(trade['quantity']) for trade in trades if trade.get('side') == 'buy')
            sell_volume = sum(float(trade['quantity']) for trade in trades if trade.get('side') == 'sell')
            trade_imbalance = (buy_volume - sell_volume) / (buy_volume + sell_volume) if (buy_volume + sell_volume) > 0 else 0
            
            # Calculate sentiment score (-1 to 1)
            sentiment_score = (order_imbalance + trade_imbalance) / 2
            
            return {
                "market": market,
                "current_price": current_price,
                "volume_24h": volume_24h,
                "order_imbalance": order_imbalance,
                "trade_imbalance": trade_imbalance,
                "sentiment_score": sentiment_score,
                "sentiment": "bullish" if sentiment_score > 0.1 else "bearish" if sentiment_score < -0.1 else "neutral",
                "confidence": abs(sentiment_score)
            }
        except Exception as e:
            logger.error(f"Market sentiment analysis failed: {e}")
            return {"error": str(e)}
    
    async def detect_trends(self, market: str, period: str = "24h") -> Dict[str, Any]:
        """Detect market trends using price movement analysis"""
        try:
            # Get market snapshot for trend analysis
            snapshot = api.get_market_snapshot(self.executor, market)
            
            # Extract price data points
            prices = snapshot.get('prices', [])
            if len(prices) < 2:
                return {"error": "Insufficient price data"}
            
            # Calculate trend indicators
            recent_prices = prices[-10:]  # Last 10 price points
            price_changes = [recent_prices[i] - recent_prices[i-1] for i in range(1, len(recent_prices))]
            
            # Trend strength calculation
            positive_changes = sum(1 for change in price_changes if change > 0)
            negative_changes = sum(1 for change in price_changes if change < 0)
            
            trend_strength = (positive_changes - negative_changes) / len(price_changes)
            
            # Moving average calculation
            ma_short = sum(recent_prices[-5:]) / 5
            ma_long = sum(recent_prices) / len(recent_prices)
            
            trend_direction = "upward" if ma_short > ma_long else "downward"
            
            return {
                "market": market,
                "trend_direction": trend_direction,
                "trend_strength": trend_strength,
                "ma_short": ma_short,
                "ma_long": ma_long,
                "price_volatility": max(price_changes) - min(price_changes) if price_changes else 0,
                "confidence": abs(trend_strength)
            }
        except Exception as e:
            logger.error(f"Trend detection failed: {e}")
            return {"error": str(e)}

class IntelligentParameterOptimizer:
    """AI-driven parameter optimization"""
    
    def __init__(self, executor):
        self.executor = executor
    
    async def optimize_parameters(self, lab_id: str, optimization_strategy: str = "genetic") -> Dict[str, Any]:
        """Intelligently optimize lab parameters using AI strategies"""
        try:
            # Get lab details
            lab_details = api.get_lab_details(self.executor, lab_id)
            
            # Identify optimizable parameters
            optimizable_params = []
            for param in lab_details.parameters:
                if param.get('bruteforce', False) or param.get('intelligent', False):
                    optimizable_params.append(param)
            
            if not optimizable_params:
                return {"error": "No optimizable parameters found"}
            
            # Generate optimization ranges based on parameter types
            optimization_ranges = {}
            for param in optimizable_params:
                key = param.get('K', '')
                param_type = param.get('T', 0)
                
                if param_type == 0:  # INTEGER
                    optimization_ranges[key] = list(range(1, 11))
                elif param_type == 1:  # DECIMAL
                    optimization_ranges[key] = [round(x * 0.1, 1) for x in range(5, 21)]  # 0.5 to 2.0
                elif param_type == 4:  # SELECTION
                    optimization_ranges[key] = param.get('O', [])
            
            # Run optimization based on strategy
            if optimization_strategy == "genetic":
                best_params = await self._genetic_optimization(lab_id, optimization_ranges)
            elif optimization_strategy == "grid":
                best_params = await self._grid_search(lab_id, optimization_ranges)
            else:
                best_params = await self._random_search(lab_id, optimization_ranges)
            
            return {
                "lab_id": lab_id,
                "optimization_strategy": optimization_strategy,
                "best_parameters": best_params,
                "optimizable_params_count": len(optimizable_params)
            }
        except Exception as e:
            logger.error(f"Parameter optimization failed: {e}")
            return {"error": str(e)}
    
    async def _genetic_optimization(self, lab_id: str, param_ranges: Dict[str, List]) -> Dict[str, Any]:
        """Genetic algorithm for parameter optimization"""
        # Simplified genetic algorithm implementation
        population_size = 10
        generations = 3
        
        # Generate initial population
        population = []
        for _ in range(population_size):
            individual = {}
            for param, values in param_ranges.items():
                individual[param] = random.choice(values)
            population.append(individual)
        
        best_individual = None
        best_fitness = -float('inf')
        
        for generation in range(generations):
            # Evaluate fitness for each individual
            for individual in population:
                fitness = await self._evaluate_fitness(lab_id, individual)
                if fitness > best_fitness:
                    best_fitness = fitness
                    best_individual = individual.copy()
        
        return best_individual or {}
    
    async def _grid_search(self, lab_id: str, param_ranges: Dict[str, List]) -> Dict[str, Any]:
        """Grid search optimization"""
        # Generate all combinations
        param_names = list(param_ranges.keys())
        param_values = list(param_ranges.values())
        
        best_combination = None
        best_fitness = -float('inf')
        
        # Limit combinations to avoid excessive computation
        max_combinations = 50
        combinations_tested = 0
        
        for combination in product(*param_values):
            if combinations_tested >= max_combinations:
                break
            
            individual = dict(zip(param_names, combination))
            fitness = await self._evaluate_fitness(lab_id, individual)
            
            if fitness > best_fitness:
                best_fitness = fitness
                best_combination = individual.copy()
            
            combinations_tested += 1
        
        return best_combination or {}
    
    async def _random_search(self, lab_id: str, param_ranges: Dict[str, List]) -> Dict[str, Any]:
        """Random search optimization"""
        best_individual = None
        best_fitness = -float('inf')
        
        for _ in range(20):  # Test 20 random combinations
            individual = {}
            for param, values in param_ranges.items():
                individual[param] = random.choice(values)
            
            fitness = await self._evaluate_fitness(lab_id, individual)
            if fitness > best_fitness:
                best_fitness = fitness
                best_individual = individual.copy()
        
        return best_individual or {}
    
    async def _evaluate_fitness(self, lab_id: str, parameters: Dict[str, Any]) -> float:
        """Evaluate fitness of parameter combination"""
        try:
            # Update lab parameters
            lab_details = api.get_lab_details(self.executor, lab_id)
            updated_parameters = []
            
            for param in lab_details.parameters:
                key = param.get('K', '')
                if key in parameters:
                    param['O'] = [str(parameters[key])]
                updated_parameters.append(param)
            
            lab_details.parameters = updated_parameters
            api.update_lab_details(self.executor, lab_details)
            
            # Run quick backtest (1 hour)
            now = int(time.time())
            start_unix = now - 3600  # 1 hour ago
            end_unix = now
            
            api.start_lab_execution(
                self.executor,
                StartLabExecutionRequest(
                    lab_id=lab_id,
                    start_unix=start_unix,
                    end_unix=end_unix,
                    send_email=False
                )
            )
            
            # Wait for completion (simplified)
            time.sleep(5)
            
            # Get results
            results = api.get_backtest_result(
                self.executor,
                GetBacktestResultRequest(
                    lab_id=lab_id,
                    next_page_id=0,
                    page_lenght=1
                )
            )
            
            if results.items:
                roi = results.items[0].summary.ReturnOnInvestment if results.items[0].summary else 0
                return float(roi)
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Fitness evaluation failed: {e}")
            return -1000.0  # Penalty for failed evaluation

class PortfolioManager:
    """AI-powered portfolio management and risk control"""
    
    def __init__(self, executor):
        self.executor = executor
    
    async def analyze_portfolio_risk(self, account_id: str) -> Dict[str, Any]:
        """Analyze portfolio risk and diversification"""
        try:
            # Get account positions and balances
            positions = api.get_account_positions(self.executor, account_id)
            balance = api.get_account_balance(self.executor, account_id)
            
            # Calculate risk metrics
            total_exposure = 0
            position_weights = {}
            market_exposure = defaultdict(float)
            
            for position in positions:
                exposure = float(position.get('quantity', 0)) * float(position.get('price', 0))
                total_exposure += abs(exposure)
                position_weights[position.get('market', '')] = abs(exposure)
                
                # Group by market
                market = position.get('market', '').split('_')[0] if '_' in position.get('market', '') else 'unknown'
                market_exposure[market] += abs(exposure)
            
            # Calculate diversification metrics
            if total_exposure > 0:
                concentration_risk = max(position_weights.values()) / total_exposure
                market_concentration = max(market_exposure.values()) / total_exposure
            else:
                concentration_risk = 0
                market_concentration = 0
            
            return {
                "account_id": account_id,
                "total_exposure": total_exposure,
                "concentration_risk": concentration_risk,
                "market_concentration": market_concentration,
                "position_count": len(positions),
                "market_count": len(market_exposure),
                "risk_level": "high" if concentration_risk > 0.5 else "medium" if concentration_risk > 0.2 else "low"
            }
        except Exception as e:
            logger.error(f"Portfolio risk analysis failed: {e}")
            return {"error": str(e)}
    
    async def optimize_portfolio_allocation(self, account_id: str, target_risk: str = "medium") -> Dict[str, Any]:
        """Suggest optimal portfolio allocation based on risk tolerance"""
        try:
            # Get available markets
            price_api = PriceAPI(self.executor)
            markets = []
            
            for exchange in ["BINANCE", "KRAKEN"]:
                try:
                    exchange_markets = price_api.get_trade_markets(exchange)
                    markets.extend(exchange_markets)
                except Exception as e:
                    continue
            
            # Filter for major pairs
            major_pairs = ["BTC", "ETH", "SOL", "ADA", "DOT", "LINK", "UNI", "MATIC"]
            filtered_markets = []
            
            for market in markets:
                if market.primary in major_pairs and market.secondary in ["USDT", "USD"]:
                    filtered_markets.append(market)
            
            # Generate allocation suggestions
            if target_risk == "low":
                # Conservative: 60% BTC, 30% ETH, 10% others
                allocation = {
                    "BTC": 0.6,
                    "ETH": 0.3,
                    "others": 0.1
                }
            elif target_risk == "high":
                # Aggressive: 30% BTC, 20% ETH, 50% altcoins
                allocation = {
                    "BTC": 0.3,
                    "ETH": 0.2,
                    "others": 0.5
                }
            else:
                # Medium: 45% BTC, 35% ETH, 20% others
                allocation = {
                    "BTC": 0.45,
                    "ETH": 0.35,
                    "others": 0.2
                }
            
            return {
                "account_id": account_id,
                "target_risk": target_risk,
                "suggested_allocation": allocation,
                "available_markets": len(filtered_markets),
                "major_pairs": major_pairs
            }
        except Exception as e:
            logger.error(f"Portfolio allocation optimization failed: {e}")
            return {"error": str(e)}

class EnhancedHaasOnlineMCPServer:
    """Enhanced MCP Server with AI-powered trading tools"""
    
    def __init__(self):
        self.authenticated = False
        self.executor = None
        self.market_analyzer = None
        self.parameter_optimizer = None
        self.portfolio_manager = None
        
    async def initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize the enhanced MCP server"""
        try:
            host = params.get("host", "127.0.0.1")
            port = params.get("port", 8090)
            email = params.get("email")
            password = params.get("password")
            
            if not email or not password:
                return {"error": "Email and password are required"}
            
            self.executor = api.RequestsExecutor(
                host=host,
                port=port,
                state=api.Guest()
            ).authenticate(email=email, password=password)
            
            self.authenticated = True
            
            # Initialize AI components
            self.market_analyzer = MarketAnalyzer(self.executor)
            self.parameter_optimizer = IntelligentParameterOptimizer(self.executor)
            self.portfolio_manager = PortfolioManager(self.executor)
            
            return {
                "status": "initialized",
                "message": f"Enhanced HaasOnline MCP Server connected at {host}:{port}",
                "user": email,
                "ai_features": [
                    "market_sentiment_analysis",
                    "trend_detection", 
                    "intelligent_parameter_optimization",
                    "portfolio_risk_analysis",
                    "automated_bot_deployment"
                ]
            }
        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            return {"error": f"Initialization failed: {str(e)}"}
    
    # Enhanced market analysis tools
    async def analyze_market_sentiment(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze market sentiment using AI"""
        if not self.authenticated:
            return {"error": "Not authenticated"}
        
        market = params.get("market")
        timeframe = params.get("timeframe", "1h")
        
        if not market:
            return {"error": "Market parameter required"}
        
        return await self.market_analyzer.analyze_market_sentiment(market, timeframe)
    
    async def detect_market_trends(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Detect market trends using AI analysis"""
        if not self.authenticated:
            return {"error": "Not authenticated"}
        
        market = params.get("market")
        period = params.get("period", "24h")
        
        if not market:
            return {"error": "Market parameter required"}
        
        return await self.market_analyzer.detect_trends(market, period)
    
    # Enhanced parameter optimization
    async def intelligent_parameter_optimization(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Intelligently optimize lab parameters using AI"""
        if not self.authenticated:
            return {"error": "Not authenticated"}
        
        lab_id = params.get("lab_id")
        strategy = params.get("strategy", "genetic")
        
        if not lab_id:
            return {"error": "Lab ID required"}
        
        return await self.parameter_optimizer.optimize_parameters(lab_id, strategy)
    
    # Portfolio management tools
    async def analyze_portfolio_risk(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze portfolio risk and diversification"""
        if not self.authenticated:
            return {"error": "Not authenticated"}
        
        account_id = params.get("account_id")
        if not account_id:
            return {"error": "Account ID required"}
        
        return await self.portfolio_manager.analyze_portfolio_risk(account_id)
    
    async def optimize_portfolio_allocation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Suggest optimal portfolio allocation"""
        if not self.authenticated:
            return {"error": "Not authenticated"}
        
        account_id = params.get("account_id")
        target_risk = params.get("target_risk", "medium")
        
        if not account_id:
            return {"error": "Account ID required"}
        
        return await self.portfolio_manager.optimize_portfolio_allocation(account_id, target_risk)
    
    # Automated trading tools
    async def automated_strategy_deployment(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Automatically deploy trading strategies based on market conditions"""
        if not self.authenticated:
            return {"error": "Not authenticated"}
        
        try:
            strategy_type = params.get("strategy_type", "scalper")
            markets = params.get("markets", ["BTC/USDT"])
            risk_level = params.get("risk_level", "medium")
            
            # Get accounts
            accounts = api.get_accounts(self.executor)
            if not accounts:
                return {"error": "No accounts available"}
            
            account = accounts[0]
            
            # Get scripts
            scripts = api.get_scripts_by_name(self.executor, f"{strategy_type.title()} Bot")
            if not scripts:
                return {"error": f"No {strategy_type} bot scripts found"}
            
            script = scripts[0]
            
            deployed_bots = []
            
            for market_pair in markets:
                # Analyze market sentiment
                sentiment = await self.market_analyzer.analyze_market_sentiment(
                    f"BINANCE_{market_pair.replace('/', '_')}_"
                )
                
                # Only deploy if sentiment is favorable
                if sentiment.get("sentiment") in ["bullish", "neutral"]:
                    # Create lab
                    lab_name = f"Auto_{strategy_type}_{market_pair.replace('/', '_')}_{int(time.time())}"
                    lab = api.create_lab(
                        self.executor,
                        CreateLabRequest(
                            script_id=script.script_id,
                            name=lab_name,
                            account_id=account.account_id,
                            market=f"BINANCE_{market_pair.replace('/', '_')}_",
                            interval=1,
                            default_price_data_style="CandleStick"
                        )
                    )
                    
                    # Optimize parameters
                    optimization_result = await self.parameter_optimizer.optimize_parameters(
                        lab.lab_id, "genetic"
                    )
                    
                    if optimization_result.get("best_parameters"):
                        # Update lab with optimized parameters
                        lab_details = api.get_lab_details(self.executor, lab.lab_id)
                        updated_parameters = []
                        
                        for param in lab_details.parameters:
                            key = param.get('K', '')
                            if key in optimization_result["best_parameters"]:
                                param['O'] = [str(optimization_result["best_parameters"][key])]
                            updated_parameters.append(param)
                        
                        lab_details.parameters = updated_parameters
                        api.update_lab_details(self.executor, lab_details)
                        
                        # Start backtest
                        now = int(time.time())
                        api.start_lab_execution(
                            self.executor,
                            StartLabExecutionRequest(
                                lab_id=lab.lab_id,
                                start_unix=now - 3600 * 6,  # 6 hours
                                end_unix=now,
                                send_email=False
                            )
                        )
                        
                        deployed_bots.append({
                            "market": market_pair,
                            "lab_id": lab.lab_id,
                            "sentiment": sentiment.get("sentiment"),
                            "optimization_strategy": "genetic"
                        })
            
            return {
                "deployed_bots": deployed_bots,
                "total_deployed": len(deployed_bots),
                "strategy_type": strategy_type,
                "risk_level": risk_level
            }
            
        except Exception as e:
            logger.error(f"Automated strategy deployment failed: {e}")
            return {"error": str(e)}
    
    # Multi-exchange tools
    async def get_markets_efficiently(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get markets efficiently using exchange-specific endpoints"""
        if not self.authenticated:
            return {"error": "Not authenticated"}
        
        try:
            exchanges = params.get("exchanges", ["BINANCE", "KRAKEN"])
            all_markets = []
            
            for exchange in exchanges:
                try:
                    price_api = PriceAPI(self.executor)
                    exchange_markets = price_api.get_trade_markets(exchange)
                    all_markets.extend(exchange_markets)
                except Exception as e:
                    logger.warning(f"Failed to get {exchange} markets: {e}")
                    continue
            
            return {
                "markets": [
                    {
                        "price_source": market.price_source,
                        "primary": market.primary,
                        "secondary": market.secondary,
                        "market_id": getattr(market, 'market_id', '')
                    }
                    for market in all_markets
                ],
                "total_markets": len(all_markets),
                "exchanges": exchanges
            }
        except Exception as e:
            logger.error(f"Efficient market fetching failed: {e}")
            return {"error": str(e)}

# Global server instance
server = EnhancedHaasOnlineMCPServer()

async def handle_request(request: MCPRequest) -> MCPResponse:
    """Handle enhanced MCP requests"""
    try:
        method = request.method
        params = request.params or {}
        
        # Route to appropriate handler
        if method == "initialize":
            result = await server.initialize(params)
        elif method == "analyze_market_sentiment":
            result = await server.analyze_market_sentiment(params)
        elif method == "detect_market_trends":
            result = await server.detect_market_trends(params)
        elif method == "intelligent_parameter_optimization":
            result = await server.intelligent_parameter_optimization(params)
        elif method == "analyze_portfolio_risk":
            result = await server.analyze_portfolio_risk(params)
        elif method == "optimize_portfolio_allocation":
            result = await server.optimize_portfolio_allocation(params)
        elif method == "automated_strategy_deployment":
            result = await server.automated_strategy_deployment(params)
        elif method == "get_markets_efficiently":
            result = await server.get_markets_efficiently(params)
        else:
            return MCPResponse(
                id=request.id,
                error={
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            )
        
        if "error" in result:
            return MCPResponse(
                id=request.id,
                error={
                    "code": -32000,
                    "message": result["error"]
                }
            )
        
        return MCPResponse(
            id=request.id,
            result=result
        )
        
    except Exception as e:
        logger.error(f"Request handling error: {e}")
        return MCPResponse(
            id=request.id,
            error={
                "code": -32603,
                "message": f"Internal error: {str(e)}"
            }
        )

async def main():
    """Main enhanced MCP server loop"""
    logger.info("Starting Enhanced HaasOnline MCP Server...")
    
    # Send initialization message
    init_message = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {
                    "ai_market_analysis": True,
                    "intelligent_optimization": True,
                    "portfolio_management": True,
                    "automated_deployment": True
                }
            },
            "clientInfo": {
                "name": "enhanced-haasonline-mcp-server",
                "version": "2.0.0"
            }
        }
    }
    
    print(json.dumps(init_message))
    sys.stdout.flush()
    
    # Main request loop
    while True:
        try:
            line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
            if not line:
                break
            
            request_data = json.loads(line.strip())
            request = MCPRequest(**request_data)
            
            response = await handle_request(request)
            response_dict = asdict(response)
            
            # Remove None values
            response_dict = {k: v for k, v in response_dict.items() if v is not None}
            
            print(json.dumps(response_dict))
            sys.stdout.flush()
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            error_response = MCPResponse(
                error={
                    "code": -32700,
                    "message": "Parse error"
                }
            )
            print(json.dumps(asdict(error_response)))
            sys.stdout.flush()
            
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            error_response = MCPResponse(
                error={
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            )
            print(json.dumps(asdict(error_response)))
            sys.stdout.flush()

if __name__ == "__main__":
    asyncio.run(main()) 