#!/usr/bin/env python3
"""
AI-Powered Trading Tools for HaasOnline

This module provides intelligent trading tools that can be integrated into
the MCP server or used standalone for automated trading strategies.

Features:
- Market sentiment analysis
- Intelligent parameter optimization
- Portfolio risk management
- Automated strategy deployment
"""

import time
import random
from typing import Dict, List, Any, Optional
from collections import defaultdict
from pyHaasAPI_v1 import api
from pyHaasAPI_v1.price import PriceAPI

class MarketSentimentAnalyzer:
    """AI-powered market sentiment analysis"""
    
    def __init__(self, executor):
        self.executor = executor
        self.price_api = PriceAPI(executor)
    
    def analyze_sentiment(self, market: str) -> Dict[str, Any]:
        """Analyze market sentiment using price and volume data"""
        try:
            # Get market data
            price_data = api.get_market_price(self.executor, market)
            order_book = api.get_order_book(self.executor, market, depth=20)
            
            # Calculate sentiment indicators
            current_price = float(price_data.get('price', 0))
            volume_24h = float(price_data.get('volume24h', 0))
            
            # Analyze order book imbalance
            bids = sum(float(bid['quantity']) for bid in order_book.get('bids', []))
            asks = sum(float(ask['quantity']) for ask in order_book.get('asks', []))
            order_imbalance = (bids - asks) / (bids + asks) if (bids + asks) > 0 else 0
            
            # Calculate sentiment score (-1 to 1)
            sentiment_score = order_imbalance
            
            return {
                "market": market,
                "current_price": current_price,
                "volume_24h": volume_24h,
                "order_imbalance": order_imbalance,
                "sentiment_score": sentiment_score,
                "sentiment": "bullish" if sentiment_score > 0.1 else "bearish" if sentiment_score < -0.1 else "neutral"
            }
        except Exception as e:
            return {"error": str(e)}

class IntelligentParameterOptimizer:
    """AI-driven parameter optimization"""
    
    def __init__(self, executor):
        self.executor = executor
    
    def optimize_parameters(self, lab_id: str) -> Dict[str, Any]:
        """Optimize lab parameters using intelligent search"""
        try:
            # Get lab details
            lab_details = api.get_lab_details(self.executor, lab_id)
            
            # Find optimizable parameters
            optimizable_params = []
            for param in lab_details.parameters:
                if param.get('bruteforce', False) or param.get('intelligent', False):
                    optimizable_params.append(param)
            
            if not optimizable_params:
                return {"error": "No optimizable parameters found"}
            
            # Generate optimization ranges
            optimization_ranges = {}
            for param in optimizable_params:
                key = param.get('K', '')
                param_type = param.get('T', 0)
                
                if param_type == 0:  # INTEGER
                    optimization_ranges[key] = list(range(1, 11))
                elif param_type == 1:  # DECIMAL
                    optimization_ranges[key] = [round(x * 0.1, 1) for x in range(5, 21)]
                elif param_type == 4:  # SELECTION
                    optimization_ranges[key] = param.get('O', [])
            
            # Run random search optimization
            best_params = self._random_search(lab_id, optimization_ranges)
            
            return {
                "lab_id": lab_id,
                "best_parameters": best_params,
                "optimizable_params_count": len(optimizable_params)
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _random_search(self, lab_id: str, param_ranges: Dict[str, List]) -> Dict[str, Any]:
        """Random search optimization"""
        best_individual = None
        best_fitness = -float('inf')
        
        for _ in range(10):  # Test 10 random combinations
            individual = {}
            for param, values in param_ranges.items():
                individual[param] = random.choice(values)
            
            fitness = self._evaluate_fitness(lab_id, individual)
            if fitness > best_fitness:
                best_fitness = fitness
                best_individual = individual.copy()
        
        return best_individual or {}
    
    def _evaluate_fitness(self, lab_id: str, parameters: Dict[str, Any]) -> float:
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
            
            # Run quick backtest
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
            return -1000.0

class PortfolioRiskManager:
    """Portfolio risk analysis and management"""
    
    def __init__(self, executor):
        self.executor = executor
    
    def analyze_risk(self, account_id: str) -> Dict[str, Any]:
        """Analyze portfolio risk and diversification"""
        try:
            positions = api.get_account_positions(self.executor, account_id)
            balance = api.get_account_balance(self.executor, account_id)
            
            total_exposure = 0
            position_weights = {}
            market_exposure = defaultdict(float)
            
            for position in positions:
                exposure = float(position.get('quantity', 0)) * float(position.get('price', 0))
                total_exposure += abs(exposure)
                position_weights[position.get('market', '')] = abs(exposure)
                
                market = position.get('market', '').split('_')[0] if '_' in position.get('market', '') else 'unknown'
                market_exposure[market] += abs(exposure)
            
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
            return {"error": str(e)}

class AutomatedStrategyDeployer:
    """Automated strategy deployment based on market conditions"""
    
    def __init__(self, executor):
        self.executor = executor
        self.sentiment_analyzer = MarketSentimentAnalyzer(executor)
        self.parameter_optimizer = IntelligentParameterOptimizer(executor)
    
    def deploy_strategy(self, strategy_type: str, markets: List[str], account_id: str) -> Dict[str, Any]:
        """Deploy trading strategies based on market conditions"""
        try:
            # Get scripts
            scripts = api.get_scripts_by_name(self.executor, f"{strategy_type.title()} Bot")
            if not scripts:
                return {"error": f"No {strategy_type} bot scripts found"}
            
            script = scripts[0]
            deployed_bots = []
            
            for market_pair in markets:
                # Analyze market sentiment
                sentiment = self.sentiment_analyzer.analyze_sentiment(
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
                            account_id=account_id,
                            market=f"BINANCE_{market_pair.replace('/', '_')}_",
                            interval=1,
                            default_price_data_style="CandleStick"
                        )
                    )
                    
                    # Optimize parameters
                    optimization_result = self.parameter_optimizer.optimize_parameters(lab.lab_id)
                    
                    if optimization_result.get("best_parameters"):
                        deployed_bots.append({
                            "market": market_pair,
                            "lab_id": lab.lab_id,
                            "sentiment": sentiment.get("sentiment"),
                            "optimization_strategy": "random_search"
                        })
            
            return {
                "deployed_bots": deployed_bots,
                "total_deployed": len(deployed_bots),
                "strategy_type": strategy_type
            }
            
        except Exception as e:
            return {"error": str(e)}

# Example usage
if __name__ == "__main__":
    # Initialize executor (you would need to authenticate first)
    print("AI Trading Tools for HaasOnline")
    print("This module provides intelligent trading tools for automated strategies.")
    print("Use these classes in your MCP server or trading applications.") 