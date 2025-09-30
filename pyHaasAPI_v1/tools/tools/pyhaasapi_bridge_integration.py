#!/usr/bin/env python3
"""
PyHaasAPI Bridge Integration
Bridges UniversalMarketResolver with existing PyHaasAPI CloudMarket methods
"""

from typing import Dict, List, Optional, Union
from dataclasses import dataclass
from examples.market_analysis.universal_market_resolver import UniversalMarketResolver, ContractType
from pyHaasAPI_v1.model import CloudMarket, LabDetails
from pyHaasAPI_v1.api import SyncExecutor, Authenticated
import pyHaasAPI_v1.api as api

class PyHaasAPIBridge:
    """Bridge between UniversalMarketResolver and PyHaasAPI CloudMarket methods"""
    
    def __init__(self):
        self.market_resolver = UniversalMarketResolver()
    
    def create_cloud_market(self, exchange: str, primary: str, secondary: str, 
                           contract_type: ContractType = ContractType.SPOT) -> CloudMarket:
        """
        Create CloudMarket object using UniversalMarketResolver
        
        Args:
            exchange: Exchange code (e.g., 'BINANCEFUTURES')
            primary: Primary asset (e.g., 'BTC')
            secondary: Secondary asset (e.g., 'USDT')
            contract_type: Contract type (SPOT, PERPETUAL, QUARTERLY)
            
        Returns:
            CloudMarket object ready for use with pyhaasapi methods
        """
        # Determine category based on exchange and contract type
        if contract_type == ContractType.SPOT:
            category = "SPOT"
        else:
            category = "FUTURES"
        
        # Create CloudMarket object using field aliases
        cloud_market = CloudMarket(
            C=category,  # category alias
            PS=exchange,  # price_source alias
            P=primary,   # primary alias
            S=secondary, # secondary alias
            CT=contract_type.value if contract_type != ContractType.SPOT else None  # contract_type alias
        )
        
        return cloud_market
    
    def resolve_market_tag(self, exchange: str, primary: str, secondary: str,
                          contract_type: ContractType = ContractType.SPOT) -> str:
        """
        One-step market tag resolution using UniversalMarketResolver
        
        Args:
            exchange: Exchange code
            primary: Primary asset
            secondary: Secondary asset
            contract_type: Contract type
            
        Returns:
            Formatted market tag string
        """
        return self.market_resolver.resolve_market_tag(exchange, primary, secondary, contract_type)
    
    def resolve_and_create_market(self, exchange: str, primary: str, secondary: str,
                                 contract_type: ContractType = ContractType.SPOT) -> tuple[str, CloudMarket]:
        """
        Resolve market tag and create CloudMarket object in one step
        
        Returns:
            Tuple of (market_tag, cloud_market)
        """
        market_tag = self.resolve_market_tag(exchange, primary, secondary, contract_type)
        cloud_market = self.create_cloud_market(exchange, primary, secondary, contract_type)
        
        return market_tag, cloud_market

class BulkLabManager:
    """High-level bulk lab operations using PyHaasAPI"""
    
    def __init__(self, executor: SyncExecutor[Authenticated]):
        self.executor = executor
        self.bridge = PyHaasAPIBridge()
    
    def create_labs_for_assets(self, 
                              source_lab_id: str,
                              assets: List[str],
                              exchange: str = "BINANCEFUTURES",
                              quote_asset: str = "USDT",
                              contract_type: ContractType = ContractType.PERPETUAL,
                              account_id: Optional[str] = None,
                              lab_name_template: str = "{strategy} - {primary} - {suffix}") -> Dict[str, LabDetails]:
        """
        Create multiple labs for different assets using PyHaasAPI
        
        Args:
            source_lab_id: ID of lab to clone
            assets: List of primary assets (e.g., ['BTC', 'ETH', 'SOL'])
            exchange: Exchange code
            quote_asset: Quote asset (default: USDT)
            contract_type: Contract type
            account_id: Account ID (if None, preserves original)
            lab_name_template: Template for lab names
            
        Returns:
            Dictionary mapping asset -> LabDetails
        """
        created_labs = {}
        failed_labs = {}
        
        print(f"🚀 Creating labs for {len(assets)} assets on {exchange}")
        
        for i, asset in enumerate(assets, 1):
            print(f"\n[{i}/{len(assets)}] Processing {asset}...")
            
            try:
                # Generate lab name
                lab_name = lab_name_template.format(
                    strategy="ADX BB STOCH Scalper",  # Could be parameterized
                    primary=asset,
                    suffix="alpha test"
                )
                
                # Clone the lab
                print(f"  📋 Cloning lab: {lab_name}")
                cloned_lab = api.clone_lab(self.executor, source_lab_id, lab_name)
                
                # Get lab details for updating
                lab_details = api.get_lab_details(self.executor, cloned_lab.lab_id)
                
                # Resolve market tag using bridge
                market_tag = self.bridge.resolve_market_tag(exchange, asset, quote_asset, contract_type)
                
                # Update settings
                lab_details.settings.market_tag = market_tag
                if account_id:
                    lab_details.settings.account_id = account_id
                
                print(f"  🏷️  Market: {market_tag}")
                print(f"  👤 Account: {lab_details.settings.account_id}")
                
                # Update lab details
                updated_lab = api.update_lab_details(self.executor, lab_details)
                
                created_labs[asset] = updated_lab
                print(f"  ✅ {asset} lab created successfully")
                
            except Exception as e:
                print(f"  ❌ Failed to create lab for {asset}: {e}")
                failed_labs[asset] = str(e)
        
        print(f"\n📊 Results: {len(created_labs)} successful, {len(failed_labs)} failed")
        
        if failed_labs:
            print("❌ Failed assets:")
            for asset, error in failed_labs.items():
                print(f"  - {asset}: {error}")
        
        return created_labs

# Analysis of Parameter Handling
class ParameterAnalysis:
    """Analysis of parameter handling between our script and PyHaasAPI"""
    
    @staticmethod
    def compare_parameter_formats():
        """Compare parameter formats between our script and PyHaasAPI"""
        
        print("🔍 PARAMETER HANDLING ANALYSIS")
        print("="*60)
        
        print("\n1. OUR CURRENT SCRIPT FORMAT:")
        print("   Direct JSON to HaasOnline API:")
        print("""   {
       "K": "Interval", 
       "O": [90], 
       "I": False, 
       "IS": True
   }""")
        
        print("\n2. PYHAASAPI FORMAT:")
        print("   Uses LabParameter/ScriptParameter classes:")
        print("""   LabParameter(
       key="Interval",
       options=[90],
       is_enabled=False,
       is_selected=True
   )""")
        
        print("\n3. PYHAASAPI update_lab_details() HANDLING:")
        print("   ✅ Automatically converts LabParameter objects to API format")
        print("   ✅ Handles both dict and object parameters")
        print("   ✅ Preserves data types (numbers as numbers)")
        print("   ✅ Uses correct field aliases (K, O, I, IS)")
        
        print("\n4. INTEGRATION ASSESSMENT:")
        print("   🎯 CONCLUSION: PyHaasAPI parameter handling is MORE SOPHISTICATED")
        print("   📈 RECOMMENDATION: Use PyHaasAPI's parameter classes instead of raw dicts")
        print("   🔧 BENEFIT: Type safety, validation, and automatic serialization")
        
        print("\n5. MIGRATION PATH:")
        print("   Current: parameters = self.get_adx_bb_stoch_parameters()  # Returns List[Dict]")
        print("   Better:  parameters = LabParameter.from_dict_list(param_dicts)")
        print("   Best:    Use PyHaasAPI's parameter management classes")

def main():
    """Demonstrate the bridge integration"""
    
    # Analyze parameter handling
    ParameterAnalysis.compare_parameter_formats()
    
    print(f"\n{'='*60}")
    print("BRIDGE INTEGRATION DEMO")
    print("="*60)
    
    # Create bridge
    bridge = PyHaasAPIBridge()
    
    # Test market resolution
    print("\n🔍 Testing market resolution:")
    
    test_cases = [
        ("BINANCEFUTURES", "BTC", "USDT", ContractType.PERPETUAL),
        ("BINANCE", "ETH", "USDT", ContractType.SPOT),
        ("KRAKENFUTURES", "SOL", "USD", ContractType.PERPETUAL),
    ]
    
    for exchange, primary, secondary, contract_type in test_cases:
        market_tag, cloud_market = bridge.resolve_and_create_market(
            exchange, primary, secondary, contract_type
        )
        
        print(f"\n  {exchange} {primary}/{secondary} ({contract_type.value}):")
        print(f"    Market Tag: {market_tag}")
        print(f"    CloudMarket: {cloud_market.price_source}_{cloud_market.primary}_{cloud_market.secondary}")
        
        # Test CloudMarket methods
        if contract_type == ContractType.SPOT:
            formatted = cloud_market.format_market_tag(exchange)
        else:
            formatted = cloud_market.format_futures_market_tag(exchange, contract_type.value)
        
        print(f"    Formatted:  {formatted}")
        print(f"    Match: {'✅' if market_tag == formatted else '❌'}")

if __name__ == "__main__":
    main()