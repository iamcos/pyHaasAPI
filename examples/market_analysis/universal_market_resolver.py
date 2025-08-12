#!/usr/bin/env python3
"""
Universal Market Resolver for PyHaasAPI
Based on comprehensive exchange pattern analysis

This module provides universal market tag resolution for all supported exchanges,
handling exchange-specific naming patterns and contract types.
"""

import json
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum

class ContractType(Enum):
    SPOT = "SPOT"
    PERPETUAL = "PERPETUAL"
    QUARTERLY = "QUARTERLY"
    FUTURES = "FUTURES"
    MARGIN = "MARGIN"

class ExchangeType(Enum):
    SPOT_ONLY = "SPOT_ONLY"
    FUTURES_ONLY = "FUTURES_ONLY"
    MIXED = "MIXED"

@dataclass
class ExchangeConfig:
    exchange_code: str
    exchange_name: str
    exchange_type: ExchangeType
    spot_pattern: str
    futures_patterns: Dict[str, str]
    supported_contract_types: List[str]
    common_quote_assets: List[str]
    total_markets: int
    is_active: bool = True

class UniversalMarketResolver:
    """Universal market resolver supporting all HaasOnline exchanges"""
    
    def __init__(self):
        self.exchange_configs = self._load_exchange_configs()
        self.exchange_map = {config.exchange_code: config for config in self.exchange_configs}
    
    def _load_exchange_configs(self) -> List[ExchangeConfig]:
        """Load exchange configurations based on analysis results"""
        
        # Based on comprehensive analysis of 24 exchanges and 12,389 markets
        configs = [
            # Major Spot Exchanges
            ExchangeConfig(
                exchange_code="BINANCE",
                exchange_name="Binance Spot",
                exchange_type=ExchangeType.SPOT_ONLY,
                spot_pattern="BINANCE_{PRIMARY}_{SECONDARY}_",
                futures_patterns={},
                supported_contract_types=[],
                common_quote_assets=["USDT", "BTC", "ETH", "BNB", "FDUSD", "EUR", "USD"],
                total_markets=1489
            ),
            
            ExchangeConfig(
                exchange_code="KUCOIN",
                exchange_name="KuCoin Spot",
                exchange_type=ExchangeType.SPOT_ONLY,
                spot_pattern="KUCOIN_{PRIMARY}_{SECONDARY}_",
                futures_patterns={},
                supported_contract_types=[],
                common_quote_assets=["USDT", "BTC", "ETH", "KCS", "USDC"],
                total_markets=1286
            ),
            
            ExchangeConfig(
                exchange_code="KRAKEN",
                exchange_name="Kraken Spot",
                exchange_type=ExchangeType.SPOT_ONLY,
                spot_pattern="KRAKEN_{PRIMARY}_{SECONDARY}_",
                futures_patterns={},
                supported_contract_types=[],
                common_quote_assets=["USD", "EUR", "BTC", "ETH", "USDT", "USDC"],
                total_markets=1140
            ),
            
            ExchangeConfig(
                exchange_code="POLONIEX",
                exchange_name="Poloniex Spot",
                exchange_type=ExchangeType.SPOT_ONLY,
                spot_pattern="POLONIEX_{PRIMARY}_{SECONDARY}_",
                futures_patterns={},
                supported_contract_types=[],
                common_quote_assets=["USDT", "BTC", "ETH", "USDC"],
                total_markets=1076
            ),
            
            ExchangeConfig(
                exchange_code="BITGET",
                exchange_name="Bitget Spot",
                exchange_type=ExchangeType.SPOT_ONLY,
                spot_pattern="BITGET_{PRIMARY}_{SECONDARY}_",
                futures_patterns={},
                supported_contract_types=[],
                common_quote_assets=["USDT", "BTC", "ETH", "USDC"],
                total_markets=809
            ),
            
            ExchangeConfig(
                exchange_code="OKEX",
                exchange_name="OKX Spot",
                exchange_type=ExchangeType.SPOT_ONLY,
                spot_pattern="OKEX_{PRIMARY}_{SECONDARY}_",
                futures_patterns={},
                supported_contract_types=[],
                common_quote_assets=["USDT", "BTC", "ETH", "USD", "USDC"],
                total_markets=755
            ),
            
            ExchangeConfig(
                exchange_code="HUOBI",
                exchange_name="Huobi Spot",
                exchange_type=ExchangeType.SPOT_ONLY,
                spot_pattern="HUOBI_{PRIMARY}_{SECONDARY}_",
                futures_patterns={},
                supported_contract_types=[],
                common_quote_assets=["USDT", "BTC", "ETH", "USDC"],
                total_markets=689
            ),
            
            ExchangeConfig(
                exchange_code="BYBITSPOT",
                exchange_name="Bybit Spot",
                exchange_type=ExchangeType.SPOT_ONLY,
                spot_pattern="BYBITSPOT_{PRIMARY}_{SECONDARY}_",
                futures_patterns={},
                supported_contract_types=[],
                common_quote_assets=["USDT", "BTC", "ETH", "USDC"],
                total_markets=662
            ),
            
            ExchangeConfig(
                exchange_code="BITFINEX",
                exchange_name="Bitfinex Spot",
                exchange_type=ExchangeType.SPOT_ONLY,
                spot_pattern="BITFINEX_{PRIMARY}_{SECONDARY}_",
                futures_patterns={},
                supported_contract_types=[],
                common_quote_assets=["USD", "BTC", "ETH", "EUR", "USDT"],
                total_markets=294
            ),
            
            ExchangeConfig(
                exchange_code="BITMEX",
                exchange_name="BitMEX Spot",
                exchange_type=ExchangeType.SPOT_ONLY,
                spot_pattern="BITMEX_{PRIMARY}_{SECONDARY}_",
                futures_patterns={},
                supported_contract_types=[],
                common_quote_assets=["USD", "USDT", "BTC", "ETH"],
                total_markets=141
            ),
            
            # Futures/Derivatives Exchanges
            ExchangeConfig(
                exchange_code="BINANCEFUTURES",
                exchange_name="Binance Futures",
                exchange_type=ExchangeType.FUTURES_ONLY,
                spot_pattern="BINANCEFUTURES_{PRIMARY}_{SECONDARY}_",
                futures_patterns={
                    "PERPETUAL": "BINANCEFUTURES_{PRIMARY}_{SECONDARY}_PERPETUAL"
                },
                supported_contract_types=["PERPETUAL"],
                common_quote_assets=["USDT", "USDC", "BTC"],
                total_markets=506
            ),
            
            ExchangeConfig(
                exchange_code="BINANCEQUARTERLY",
                exchange_name="Binance Quarterly Futures",
                exchange_type=ExchangeType.FUTURES_ONLY,
                spot_pattern="BINANCEQUARTERLY_{PRIMARY}_{SECONDARY}_",
                futures_patterns={
                    "QUARTERLY": "BINANCEQUARTERLY_{PRIMARY}_{SECONDARY}_QUARTERLY",
                    "PERPETUAL": "BINANCEQUARTERLY_{PRIMARY}_{SECONDARY}_PERPETUAL"
                },
                supported_contract_types=["QUARTERLY", "PERPETUAL"],
                common_quote_assets=["USD"],
                total_markets=51
            ),
            
            ExchangeConfig(
                exchange_code="KRAKENFUTURES",
                exchange_name="Kraken Futures",
                exchange_type=ExchangeType.FUTURES_ONLY,
                spot_pattern="KRAKENFUTURES_{PRIMARY}_{SECONDARY}_",
                futures_patterns={
                    "PERPETUAL": "KRAKENFUTURES_{PRIMARY}_{SECONDARY}_PERPETUAL"
                },
                supported_contract_types=["PERPETUAL"],
                common_quote_assets=["USD"],
                total_markets=355
            ),
            
            ExchangeConfig(
                exchange_code="KUCOINFUTURES",
                exchange_name="KuCoin Futures",
                exchange_type=ExchangeType.FUTURES_ONLY,
                spot_pattern="KUCOINFUTURES_{PRIMARY}_{SECONDARY}_",
                futures_patterns={
                    "PERPETUAL": "KUCOINFUTURES_{PRIMARY}_{SECONDARY}_PERPETUAL"
                },
                supported_contract_types=["PERPETUAL"],
                common_quote_assets=["USDT", "USD", "USDC"],
                total_markets=466
            ),
            
            ExchangeConfig(
                exchange_code="BYBIT",
                exchange_name="Bybit Futures",
                exchange_type=ExchangeType.FUTURES_ONLY,
                spot_pattern="BYBIT_{PRIMARY}_{SECONDARY}_",
                futures_patterns={
                    "PERPETUAL": "BYBIT_{PRIMARY}_{SECONDARY}_PERPETUAL"
                },
                supported_contract_types=["PERPETUAL"],
                common_quote_assets=["USD"],
                total_markets=28
            ),
            
            ExchangeConfig(
                exchange_code="OKEXSWAP",
                exchange_name="OKX Perpetual Swaps",
                exchange_type=ExchangeType.FUTURES_ONLY,
                spot_pattern="OKEXSWAP_{PRIMARY}_{SECONDARY}_",
                futures_patterns={
                    "PERPETUAL": "OKEXSWAP_{PRIMARY}_{SECONDARY}_PERPETUAL"
                },
                supported_contract_types=["PERPETUAL"],
                common_quote_assets=["USDT", "USD", "USDC"],
                total_markets=262
            ),
            
            # Specialized Exchanges
            ExchangeConfig(
                exchange_code="BYBITUSDT",
                exchange_name="Bybit USDT Perpetuals",
                exchange_type=ExchangeType.FUTURES_ONLY,
                spot_pattern="BYBITUSDT_{PRIMARY}_{SECONDARY}_",
                futures_patterns={
                    "PERPETUAL": "BYBITUSDT_{PRIMARY}_{SECONDARY}_PERPETUAL"
                },
                supported_contract_types=["PERPETUAL"],
                common_quote_assets=["USDT"],
                total_markets=567
            ),
            
            ExchangeConfig(
                exchange_code="BITGETFUTURESUSDT",
                exchange_name="Bitget USDT Futures",
                exchange_type=ExchangeType.FUTURES_ONLY,
                spot_pattern="BITGETFUTURESUSDT_{PRIMARY}_{SECONDARY}_",
                futures_patterns={
                    "PERPETUAL": "BITGETFUTURESUSDT_{PRIMARY}_{SECONDARY}_PERPETUAL"
                },
                supported_contract_types=["PERPETUAL"],
                common_quote_assets=["USDT"],
                total_markets=507
            ),
            
            ExchangeConfig(
                exchange_code="PHEMEXCONTRACTS",
                exchange_name="Phemex Contracts",
                exchange_type=ExchangeType.FUTURES_ONLY,
                spot_pattern="PHEMEXCONTRACTS_{PRIMARY}_{SECONDARY}_",
                futures_patterns={
                    "PERPETUAL": "PHEMEXCONTRACTS_{PRIMARY}_{SECONDARY}_PERPETUAL"
                },
                supported_contract_types=["PERPETUAL"],
                common_quote_assets=["USDT", "USD", "USDC"],
                total_markets=496
            ),
            
            ExchangeConfig(
                exchange_code="WOOXFUTURES",
                exchange_name="WOO X Futures",
                exchange_type=ExchangeType.FUTURES_ONLY,
                spot_pattern="WOOXFUTURES_{PRIMARY}_{SECONDARY}_",
                futures_patterns={
                    "PERPETUAL": "WOOXFUTURES_{PRIMARY}_{SECONDARY}_PERPETUAL"
                },
                supported_contract_types=["PERPETUAL"],
                common_quote_assets=["USDT"],
                total_markets=309
            ),
        ]
        
        return configs
    
    def get_supported_exchanges(self) -> List[str]:
        """Get list of all supported exchange codes"""
        return list(self.exchange_map.keys())
    
    def get_exchange_info(self, exchange_code: str) -> Optional[ExchangeConfig]:
        """Get configuration for a specific exchange"""
        return self.exchange_map.get(exchange_code.upper())
    
    def resolve_market_tag(self, exchange: str, primary: str, secondary: str, 
                          contract_type: ContractType = ContractType.SPOT) -> Optional[str]:
        """
        Resolve market tag for any supported exchange
        
        Args:
            exchange: Exchange code (e.g., 'BINANCE', 'BINANCEFUTURES')
            primary: Primary asset (e.g., 'BTC')
            secondary: Secondary asset (e.g., 'USDT')
            contract_type: Contract type (SPOT, PERPETUAL, QUARTERLY, etc.)
        
        Returns:
            Formatted market tag or None if not supported
        """
        exchange_upper = exchange.upper()
        config = self.exchange_map.get(exchange_upper)
        
        if not config:
            return None
        
        # For spot markets or spot-only exchanges
        if contract_type == ContractType.SPOT or config.exchange_type == ExchangeType.SPOT_ONLY:
            return config.spot_pattern.format(PRIMARY=primary, SECONDARY=secondary)
        
        # For futures markets
        if contract_type.value in config.futures_patterns:
            return config.futures_patterns[contract_type.value].format(
                PRIMARY=primary, SECONDARY=secondary
            )
        
        # Fallback to spot pattern if futures not supported
        return config.spot_pattern.format(PRIMARY=primary, SECONDARY=secondary)
    
    def find_best_exchange_for_pair(self, primary: str, secondary: str, 
                                   contract_type: ContractType = ContractType.SPOT,
                                   preferred_exchanges: Optional[List[str]] = None) -> Optional[str]:
        """
        Find the best exchange for a trading pair
        
        Args:
            primary: Primary asset
            secondary: Secondary asset  
            contract_type: Desired contract type
            preferred_exchanges: List of preferred exchanges (in order)
        
        Returns:
            Best exchange code or None
        """
        if preferred_exchanges:
            # Check preferred exchanges first
            for exchange in preferred_exchanges:
                config = self.exchange_map.get(exchange.upper())
                if config and secondary in config.common_quote_assets:
                    if contract_type == ContractType.SPOT or contract_type.value in config.supported_contract_types:
                        return exchange.upper()
        
        # Find exchanges that support the quote asset and contract type
        candidates = []
        for exchange_code, config in self.exchange_map.items():
            if secondary in config.common_quote_assets:
                if contract_type == ContractType.SPOT or contract_type.value in config.supported_contract_types:
                    candidates.append((exchange_code, config.total_markets))
        
        # Sort by market count (more markets = better liquidity)
        candidates.sort(key=lambda x: x[1], reverse=True)
        
        return candidates[0][0] if candidates else None
    
    def get_market_suggestions(self, primary: str, secondary: str = "USDT") -> Dict[str, List[str]]:
        """
        Get market tag suggestions across all exchanges
        
        Args:
            primary: Primary asset
            secondary: Secondary asset (default: USDT)
        
        Returns:
            Dictionary with contract types as keys and list of market tags as values
        """
        suggestions = {
            "SPOT": [],
            "PERPETUAL": [],
            "QUARTERLY": [],
            "FUTURES": []
        }
        
        for exchange_code, config in self.exchange_map.items():
            if secondary in config.common_quote_assets:
                # Add spot market
                spot_tag = self.resolve_market_tag(exchange_code, primary, secondary, ContractType.SPOT)
                if spot_tag:
                    suggestions["SPOT"].append(spot_tag)
                
                # Add futures markets
                for contract_type in config.supported_contract_types:
                    futures_tag = self.resolve_market_tag(
                        exchange_code, primary, secondary, ContractType(contract_type)
                    )
                    if futures_tag:
                        suggestions[contract_type].append(futures_tag)
        
        return suggestions
    
    def validate_market_tag(self, market_tag: str) -> Tuple[bool, Optional[Dict]]:
        """
        Validate and parse a market tag
        
        Args:
            market_tag: Market tag to validate
        
        Returns:
            Tuple of (is_valid, parsed_info)
        """
        if not market_tag:
            return False, None
        
        # Remove trailing underscore
        tag = market_tag.rstrip('_')
        parts = tag.split('_')
        
        if len(parts) < 3:
            return False, None
        
        exchange = parts[0]
        primary = parts[1]
        secondary = parts[2]
        contract_type = parts[3] if len(parts) > 3 else "SPOT"
        
        config = self.exchange_map.get(exchange)
        if not config:
            return False, None
        
        # Check if quote asset is supported
        if secondary not in config.common_quote_assets:
            return False, None
        
        # Check if contract type is supported
        if contract_type != "SPOT" and contract_type not in config.supported_contract_types:
            return False, None
        
        parsed_info = {
            "exchange": exchange,
            "primary": primary,
            "secondary": secondary,
            "contract_type": contract_type,
            "exchange_name": config.exchange_name,
            "exchange_type": config.exchange_type.value
        }
        
        return True, parsed_info
    
    def print_exchange_summary(self):
        """Print summary of all supported exchanges"""
        print(f"\n{'='*80}")
        print("UNIVERSAL MARKET RESOLVER - SUPPORTED EXCHANGES")
        print(f"{'='*80}")
        
        spot_exchanges = [c for c in self.exchange_configs if c.exchange_type == ExchangeType.SPOT_ONLY]
        futures_exchanges = [c for c in self.exchange_configs if c.exchange_type == ExchangeType.FUTURES_ONLY]
        
        print(f"\n📊 SUMMARY:")
        print(f"  Total Exchanges: {len(self.exchange_configs)}")
        print(f"  Spot Exchanges: {len(spot_exchanges)}")
        print(f"  Futures Exchanges: {len(futures_exchanges)}")
        print(f"  Total Markets: {sum(c.total_markets for c in self.exchange_configs)}")
        
        print(f"\n🏪 SPOT EXCHANGES:")
        for config in sorted(spot_exchanges, key=lambda x: x.total_markets, reverse=True):
            print(f"  {config.exchange_code:20} - {config.total_markets:4} markets - {', '.join(config.common_quote_assets[:5])}")
        
        print(f"\n🚀 FUTURES EXCHANGES:")
        for config in sorted(futures_exchanges, key=lambda x: x.total_markets, reverse=True):
            contracts = ', '.join(config.supported_contract_types) if config.supported_contract_types else 'PERPETUAL'
            print(f"  {config.exchange_code:20} - {config.total_markets:4} markets - {contracts}")

def main():
    """Test the universal market resolver"""
    resolver = UniversalMarketResolver()
    
    # Print exchange summary
    resolver.print_exchange_summary()
    
    # Test market resolution
    print(f"\n{'='*80}")
    print("MARKET RESOLUTION EXAMPLES")
    print(f"{'='*80}")
    
    test_pairs = [
        ("BTC", "USDT", ContractType.SPOT),
        ("BTC", "USDT", ContractType.PERPETUAL),
        ("ETH", "USDT", ContractType.SPOT),
        ("ETH", "USD", ContractType.PERPETUAL),
    ]
    
    for primary, secondary, contract_type in test_pairs:
        print(f"\n🔍 {primary}/{secondary} ({contract_type.value}):")
        
        # Find best exchange
        best_exchange = resolver.find_best_exchange_for_pair(primary, secondary, contract_type)
        if best_exchange:
            market_tag = resolver.resolve_market_tag(best_exchange, primary, secondary, contract_type)
            print(f"  Best: {market_tag}")
        
        # Get all suggestions
        suggestions = resolver.get_market_suggestions(primary, secondary)
        relevant_suggestions = suggestions.get(contract_type.value, [])[:3]
        if relevant_suggestions:
            print(f"  Alternatives: {', '.join(relevant_suggestions)}")

if __name__ == "__main__":
    main()