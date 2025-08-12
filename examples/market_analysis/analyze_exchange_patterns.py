#!/usr/bin/env python3
"""
Exchange Pattern Analysis Script
Analyzes all available exchanges and their market naming patterns
Dumps data for analysis and updates codebase accordingly
"""

import requests
import json
import time
from typing import Dict, List, Set, Optional, Tuple
from collections import defaultdict
from dataclasses import dataclass, asdict
import re

MCP_SERVER_URL = "http://127.0.0.1:8000"

@dataclass
class MarketPattern:
    exchange: str
    exchange_type: str
    market_tag: str
    primary: str
    secondary: str
    category: str
    contract_type: Optional[str]
    is_active: bool
    pattern_type: str  # SPOT, FUTURES, PERPETUAL, etc.

@dataclass
class ExchangeAnalysis:
    exchange_code: str
    exchange_name: str
    total_markets: int
    spot_markets: int
    futures_markets: int
    perpetual_markets: int
    quarterly_markets: int
    unique_primaries: Set[str]
    unique_secondaries: Set[str]
    naming_patterns: List[str]
    sample_markets: List[MarketPattern]

class ExchangePatternAnalyzer:
    def __init__(self, mcp_url: str):
        self.mcp_url = mcp_url
        self.session = requests.Session()
        self.raw_data = {}
        self.analysis_results = {}
        
    def check_server_status(self) -> bool:
        """Check if MCP server is running"""
        try:
            response = self.session.get(f"{self.mcp_url}/status")
            if response.status_code == 200:
                data = response.json()
                return data.get("haas_api_connected", False)
            return False
        except Exception as e:
            print(f"Error checking server status: {e}")
            return False
    
    def get_all_markets(self) -> List[Dict]:
        """Get all available markets from HaasOnline"""
        try:
            response = self.session.get(f"{self.mcp_url}/get_all_markets")
            if response.status_code == 200:
                data = response.json()
                if data.get("Success"):
                    return data.get("Data", [])
            return []
        except Exception as e:
            print(f"Error getting markets: {e}")
            return []
    
    def get_all_accounts(self) -> List[Dict]:
        """Get all available accounts to understand exchange types"""
        try:
            response = self.session.get(f"{self.mcp_url}/get_all_accounts")
            if response.status_code == 200:
                data = response.json()
                if data.get("Success"):
                    return data.get("Data", [])
            return []
        except Exception as e:
            print(f"Error getting accounts: {e}")
            return []
    
    def parse_market_tag(self, market_tag: str) -> Tuple[str, str, str, Optional[str]]:
        """Parse market tag to extract components"""
        if not market_tag:
            return "", "", "", None
            
        # Remove trailing underscore if present
        tag = market_tag.rstrip('_')
        parts = tag.split('_')
        
        if len(parts) < 3:
            return "", "", "", None
        
        exchange = parts[0]
        primary = parts[1]
        secondary = parts[2]
        contract_type = parts[3] if len(parts) > 3 else None
        
        return exchange, primary, secondary, contract_type
    
    def determine_pattern_type(self, market_tag: str, market_data: Dict) -> str:
        """Determine the pattern type from market tag and data"""
        tag_lower = market_tag.lower()
        
        # Check for specific patterns
        if 'perpetual' in tag_lower or 'perp' in tag_lower:
            return "PERPETUAL"
        elif 'quarterly' in tag_lower or 'quarter' in tag_lower:
            return "QUARTERLY"
        elif 'futures' in tag_lower or 'fut' in tag_lower:
            return "FUTURES"
        elif 'margin' in tag_lower:
            return "MARGIN"
        else:
            return "SPOT"
    
    def analyze_market_data(self, markets: List[Dict]) -> Dict[str, ExchangeAnalysis]:
        """Analyze all market data and group by exchange"""
        print(f"🔍 Analyzing {len(markets)} markets...")
        
        exchange_data = defaultdict(lambda: {
            'markets': [],
            'spot_count': 0,
            'futures_count': 0,
            'perpetual_count': 0,
            'quarterly_count': 0,
            'primaries': set(),
            'secondaries': set(),
            'patterns': set()
        })
        
        for market in markets:
            # Handle pyhaasapi CloudMarket format
            exchange = market.get('PS', '')  # Price Source
            primary = market.get('P', '')    # Primary asset
            secondary = market.get('S', '')  # Secondary asset
            category = market.get('C', '')   # Category
            contract_type = market.get('CT') # Contract Type
            
            if not exchange or not primary or not secondary:
                continue
            
            # Generate market tag using pyhaasapi format
            if contract_type:
                market_tag = f"{exchange}_{primary}_{secondary}_{contract_type}"
                pattern_type = contract_type.upper() if contract_type else "FUTURES"
            else:
                market_tag = f"{exchange}_{primary}_{secondary}_"
                pattern_type = "SPOT"
            
            # Override pattern type based on category if available
            if category:
                if category.upper() == "FUTURES":
                    pattern_type = "FUTURES"
                elif category.upper() == "SPOT":
                    pattern_type = "SPOT"
            
            # Create market pattern object
            market_pattern = MarketPattern(
                exchange=exchange,
                exchange_type=category or 'UNKNOWN',
                market_tag=market_tag,
                primary=primary,
                secondary=secondary,
                category=category or 'UNKNOWN',
                contract_type=contract_type,
                is_active=True,  # Assume active since we got it from API
                pattern_type=pattern_type
            )
            
            # Group by exchange
            exchange_data[exchange]['markets'].append(market_pattern)
            exchange_data[exchange]['primaries'].add(primary)
            exchange_data[exchange]['secondaries'].add(secondary)
            exchange_data[exchange]['patterns'].add(f"{exchange}_{pattern_type}")
            
            # Count by type
            if pattern_type == "SPOT":
                exchange_data[exchange]['spot_count'] += 1
            elif pattern_type == "PERPETUAL":
                exchange_data[exchange]['perpetual_count'] += 1
            elif pattern_type == "QUARTERLY":
                exchange_data[exchange]['quarterly_count'] += 1
            elif pattern_type in ["FUTURES", "MARGIN"]:
                exchange_data[exchange]['futures_count'] += 1
        
        # Convert to ExchangeAnalysis objects
        results = {}
        for exchange_code, data in exchange_data.items():
            # Get sample markets (up to 10 per exchange)
            sample_markets = data['markets'][:10]
            
            # Generate naming patterns
            naming_patterns = list(data['patterns'])
            
            analysis = ExchangeAnalysis(
                exchange_code=exchange_code,
                exchange_name=exchange_code,  # Could be enhanced with full names
                total_markets=len(data['markets']),
                spot_markets=data['spot_count'],
                futures_markets=data['futures_count'],
                perpetual_markets=data['perpetual_count'],
                quarterly_markets=data['quarterly_count'],
                unique_primaries=data['primaries'],
                unique_secondaries=data['secondaries'],
                naming_patterns=naming_patterns,
                sample_markets=sample_markets
            )
            
            results[exchange_code] = analysis
        
        return results
    
    def save_raw_data(self, markets: List[Dict], accounts: List[Dict]):
        """Save raw data for reference"""
        raw_data = {
            'timestamp': int(time.time()),
            'markets': markets,
            'accounts': accounts,
            'total_markets': len(markets),
            'total_accounts': len(accounts)
        }
        
        with open('exchange_raw_data.json', 'w') as f:
            json.dump(raw_data, f, indent=2, default=str)
        
        print(f"💾 Raw data saved to exchange_raw_data.json")
    
    def save_analysis_results(self, analysis: Dict[str, ExchangeAnalysis]):
        """Save analysis results"""
        # Convert to serializable format
        serializable_analysis = {}
        for exchange_code, analysis_obj in analysis.items():
            data = asdict(analysis_obj)
            # Convert sets to lists for JSON serialization
            data['unique_primaries'] = list(data['unique_primaries'])
            data['unique_secondaries'] = list(data['unique_secondaries'])
            serializable_analysis[exchange_code] = data
        
        with open('exchange_analysis_results.json', 'w') as f:
            json.dump(serializable_analysis, f, indent=2, default=str)
        
        print(f"💾 Analysis results saved to exchange_analysis_results.json")
    
    def print_comprehensive_analysis(self, analysis: Dict[str, ExchangeAnalysis]):
        """Print comprehensive analysis results"""
        print(f"\n{'='*100}")
        print("COMPREHENSIVE EXCHANGE PATTERN ANALYSIS")
        print(f"{'='*100}")
        
        # Summary statistics
        total_exchanges = len(analysis)
        total_markets = sum(a.total_markets for a in analysis.values())
        total_spot = sum(a.spot_markets for a in analysis.values())
        total_futures = sum(a.futures_markets for a in analysis.values())
        total_perpetual = sum(a.perpetual_markets for a in analysis.values())
        total_quarterly = sum(a.quarterly_markets for a in analysis.values())
        
        print(f"\n📊 SUMMARY STATISTICS:")
        print(f"  Total Exchanges: {total_exchanges}")
        print(f"  Total Markets: {total_markets}")
        print(f"  Spot Markets: {total_spot}")
        print(f"  Futures Markets: {total_futures}")
        print(f"  Perpetual Markets: {total_perpetual}")
        print(f"  Quarterly Markets: {total_quarterly}")
        
        # Sort exchanges by total markets (descending)
        sorted_exchanges = sorted(analysis.items(), key=lambda x: x[1].total_markets, reverse=True)
        
        for exchange_code, analysis_obj in sorted_exchanges:
            print(f"\n{'='*80}")
            print(f"🏢 EXCHANGE: {exchange_code}")
            print(f"{'='*80}")
            
            print(f"📈 Market Statistics:")
            print(f"  Total Markets: {analysis_obj.total_markets}")
            print(f"  Spot: {analysis_obj.spot_markets}")
            print(f"  Futures: {analysis_obj.futures_markets}")
            print(f"  Perpetual: {analysis_obj.perpetual_markets}")
            print(f"  Quarterly: {analysis_obj.quarterly_markets}")
            
            print(f"\n🪙 Asset Coverage:")
            print(f"  Primary Assets: {len(analysis_obj.unique_primaries)} ({', '.join(sorted(list(analysis_obj.unique_primaries))[:10])}{'...' if len(analysis_obj.unique_primaries) > 10 else ''})")
            print(f"  Quote Assets: {len(analysis_obj.unique_secondaries)} ({', '.join(sorted(list(analysis_obj.unique_secondaries)))})")
            
            print(f"\n🏷️  Naming Patterns:")
            for pattern in analysis_obj.naming_patterns:
                print(f"  - {pattern}")
            
            print(f"\n📋 Sample Market Tags:")
            for i, market in enumerate(analysis_obj.sample_markets[:5], 1):
                print(f"  {i}. {market.market_tag} ({market.pattern_type})")
                if i == 5 and len(analysis_obj.sample_markets) > 5:
                    print(f"     ... and {len(analysis_obj.sample_markets) - 5} more")
    
    def generate_pattern_rules(self, analysis: Dict[str, ExchangeAnalysis]) -> Dict[str, Dict]:
        """Generate pattern rules for each exchange"""
        print(f"\n{'='*100}")
        print("GENERATING PATTERN RULES")
        print(f"{'='*100}")
        
        pattern_rules = {}
        
        for exchange_code, analysis_obj in analysis.items():
            rules = {
                'exchange_code': exchange_code,
                'spot_pattern': f"{exchange_code}_{{PRIMARY}}_{{SECONDARY}}_",
                'futures_patterns': {},
                'supported_contract_types': [],
                'common_quote_assets': list(analysis_obj.unique_secondaries),
                'sample_markets': {}
            }
            
            # Analyze contract types and patterns
            contract_patterns = defaultdict(list)
            for market in analysis_obj.sample_markets:
                if market.contract_type:
                    contract_patterns[market.contract_type].append(market.market_tag)
                    if market.contract_type not in rules['supported_contract_types']:
                        rules['supported_contract_types'].append(market.contract_type)
            
            # Generate futures patterns
            for contract_type, sample_tags in contract_patterns.items():
                if sample_tags:
                    # Use first sample to generate pattern
                    sample_tag = sample_tags[0]
                    pattern = sample_tag.replace(
                        sample_tag.split('_')[1], '{PRIMARY}'
                    ).replace(
                        sample_tag.split('_')[2], '{SECONDARY}'
                    )
                    rules['futures_patterns'][contract_type] = pattern
            
            # Add sample markets for reference
            for market in analysis_obj.sample_markets[:3]:
                rules['sample_markets'][market.pattern_type] = market.market_tag
            
            pattern_rules[exchange_code] = rules
        
        # Save pattern rules
        with open('exchange_pattern_rules.json', 'w') as f:
            json.dump(pattern_rules, f, indent=2, default=str)
        
        print(f"💾 Pattern rules saved to exchange_pattern_rules.json")
        
        # Print rules summary
        for exchange_code, rules in pattern_rules.items():
            print(f"\n🏢 {exchange_code}:")
            print(f"  Spot Pattern: {rules['spot_pattern']}")
            if rules['futures_patterns']:
                print(f"  Futures Patterns:")
                for contract_type, pattern in rules['futures_patterns'].items():
                    print(f"    {contract_type}: {pattern}")
            print(f"  Supported Contracts: {rules['supported_contract_types']}")
            print(f"  Quote Assets: {rules['common_quote_assets']}")
        
        return pattern_rules
    
    def run_full_analysis(self):
        """Run complete exchange pattern analysis"""
        print("🚀 Starting comprehensive exchange pattern analysis...")
        
        # Check server status
        if not self.check_server_status():
            print("❌ MCP server is not running or not authenticated")
            return
        
        print("✅ MCP server is running and authenticated")
        
        # Get raw data
        print("\n📡 Fetching market data...")
        markets = self.get_all_markets()
        if not markets:
            print("❌ No markets found")
            return
        
        print("\n📡 Fetching account data...")
        accounts = self.get_all_accounts()
        
        print(f"✅ Retrieved {len(markets)} markets and {len(accounts)} accounts")
        
        # Save raw data
        self.save_raw_data(markets, accounts)
        
        # Analyze patterns
        print("\n🔍 Analyzing exchange patterns...")
        analysis = self.analyze_market_data(markets)
        
        # Save analysis results
        self.save_analysis_results(analysis)
        
        # Print comprehensive analysis
        self.print_comprehensive_analysis(analysis)
        
        # Generate pattern rules
        pattern_rules = self.generate_pattern_rules(analysis)
        
        print(f"\n✨ Analysis complete! Generated files:")
        print(f"  - exchange_raw_data.json (raw market/account data)")
        print(f"  - exchange_analysis_results.json (detailed analysis)")
        print(f"  - exchange_pattern_rules.json (pattern rules for implementation)")
        
        return analysis, pattern_rules

def main():
    print("🎯 EXCHANGE PATTERN ANALYSIS")
    print("Analyzing all available exchanges and their market naming patterns")
    
    analyzer = ExchangePatternAnalyzer(MCP_SERVER_URL)
    analysis, pattern_rules = analyzer.run_full_analysis()
    
    if analysis and pattern_rules:
        print(f"\n🎉 SUCCESS! Analyzed {len(analysis)} exchanges")
        print(f"Ready to update codebase with universal exchange support")
    else:
        print("❌ Analysis failed")

if __name__ == "__main__":
    main()