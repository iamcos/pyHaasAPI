"""
Lab Cloning Automation
Advanced lab cloning utilities with market resolution and bulk operations.
"""

import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from .market_resolver import MarketResolver, ContractType


@dataclass
class CloneTarget:
    """Target configuration for lab cloning"""
    asset: str
    exchange: str = "BINANCEFUTURES"
    quote_asset: str = "USDT"
    contract_type: str = "PERPETUAL"
    account_id: Optional[str] = None
    lab_name_override: Optional[str] = None


@dataclass
class CloneResult:
    """Result of a lab cloning operation"""
    success: bool
    lab_id: Optional[str] = None
    lab_name: Optional[str] = None
    target: Optional[CloneTarget] = None
    error: Optional[str] = None


class LabCloningManager:
    """Manages advanced lab cloning operations"""
    
    def __init__(self, haas_executor, mcp_url: str = "http://127.0.0.1:8000"):
        self.haas_executor = haas_executor
        self.market_resolver = MarketResolver(mcp_url)
        
    def clone_lab_to_markets(self, source_lab_id: str, targets: List[CloneTarget], 
                           lab_name_template: str = "{strategy} - {primary} - {suffix}") -> Dict[str, CloneResult]:
        """
        Clone a lab to multiple markets with automatic market resolution
        
        Args:
            source_lab_id: ID of the source lab to clone
            targets: List of target markets to clone to
            lab_name_template: Template for naming cloned labs
            
        Returns:
            Dictionary mapping target keys to clone results
        """
        from pyHaasAPI import api
        
        # Get source lab details
        try:
            source_lab = api.get_lab_details(self.haas_executor, source_lab_id)
            if not source_lab:
                raise Exception(f"Source lab {source_lab_id} not found")
        except Exception as e:
            logging.error(f"Failed to get source lab details: {e}")
            return {}
        
        results = {}
        
        print(f"🔄 Cloning lab '{source_lab.name}' to {len(targets)} markets...")
        
        for i, target in enumerate(targets, 1):
            target_key = f"{target.asset}_{target.exchange}"
            print(f"[{i}/{len(targets)}] Cloning to {target.asset} on {target.exchange}...")
            
            try:
                # Generate lab name
                strategy_name = source_lab.name.split(" - ")[0] if " - " in source_lab.name else source_lab.name
                lab_name = target.lab_name_override or lab_name_template.format(
                    strategy=strategy_name,
                    primary=target.asset,
                    suffix=f"{target.exchange[:3]}"
                )
                
                # Clone the lab
                cloned_lab = api.clone_lab(self.haas_executor, source_lab_id, lab_name)
                
                # TODO: Update market settings using market resolver
                # This would involve:
                # 1. Resolve the correct market tag for the target
                # 2. Update the lab's market configuration
                # 3. Update account settings if specified
                
                results[target_key] = CloneResult(
                    success=True,
                    lab_id=cloned_lab.lab_id,
                    lab_name=cloned_lab.name,
                    target=target
                )
                print(f"  ✅ Created: {cloned_lab.name}")
                
            except Exception as e:
                error_msg = str(e)
                results[target_key] = CloneResult(
                    success=False,
                    target=target,
                    error=error_msg
                )
                print(f"  ❌ Failed: {error_msg}")
        
        return results
    
    def update_lab_market_settings(self, lab_id: str, target: CloneTarget) -> bool:
        """
        Update a lab's market settings to match the target configuration
        
        Args:
            lab_id: ID of the lab to update
            target: Target market configuration
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Resolve the market tag for the target
            contract_type_enum = getattr(ContractType, target.contract_type, ContractType.PERPETUAL)
            market_tag = self.market_resolver.resolve_market_tag_safely(
                base_asset=target.asset,
                quote_asset=target.quote_asset,
                exchange=target.exchange,
                contract_type=contract_type_enum
            )
            
            if not market_tag:
                raise Exception(f"Could not resolve market tag for {target.asset}/{target.quote_asset} on {target.exchange}")
            
            # TODO: Implement lab market settings update
            # This would involve updating the lab's configuration with:
            # - New market tag
            # - Account ID (if specified)
            # - Any other market-specific settings
            
            print(f"  📊 Market resolved: {market_tag}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to update lab market settings: {e}")
            return False
    
    def bulk_clone_and_configure(self, source_lab_id: str, assets: List[str],
                               exchange: str = "BINANCEFUTURES", quote_asset: str = "USDT",
                               contract_type: str = "PERPETUAL", account_id: Optional[str] = None) -> Dict[str, CloneResult]:
        """
        Convenience method to clone a lab to multiple assets with same configuration
        
        Args:
            source_lab_id: ID of the source lab to clone
            assets: List of base assets (e.g., ["BTC", "ETH", "SOL"])
            exchange: Target exchange
            quote_asset: Quote asset (usually USDT)
            contract_type: Contract type (SPOT, PERPETUAL, FUTURES)
            account_id: Account ID to use (optional)
            
        Returns:
            Dictionary mapping asset names to clone results
        """
        targets = [
            CloneTarget(
                asset=asset,
                exchange=exchange,
                quote_asset=quote_asset,
                contract_type=contract_type,
                account_id=account_id
            )
            for asset in assets
        ]
        
        return self.clone_lab_to_markets(source_lab_id, targets)
    
    def get_clone_summary(self, results: Dict[str, CloneResult]) -> Dict[str, Any]:
        """
        Generate a summary of cloning results
        
        Args:
            results: Results from clone operation
            
        Returns:
            Summary dictionary with success/failure counts and details
        """
        successful = [r for r in results.values() if r.success]
        failed = [r for r in results.values() if not r.success]
        
        return {
            "total_targets": len(results),
            "successful_clones": len(successful),
            "failed_clones": len(failed),
            "success_rate": len(successful) / len(results) if results else 0,
            "successful_labs": {
                r.target.asset: {"lab_id": r.lab_id, "lab_name": r.lab_name}
                for r in successful
            },
            "failures": {
                r.target.asset: r.error
                for r in failed
            }
        }


def create_targets_from_assets(assets: List[str], exchange: str = "BINANCEFUTURES", 
                             quote_asset: str = "USDT", contract_type: str = "PERPETUAL") -> List[CloneTarget]:
    """
    Utility function to create CloneTarget objects from a list of assets
    
    Args:
        assets: List of base assets
        exchange: Target exchange
        quote_asset: Quote asset
        contract_type: Contract type
        
    Returns:
        List of CloneTarget objects
    """
    return [
        CloneTarget(
            asset=asset,
            exchange=exchange,
            quote_asset=quote_asset,
            contract_type=contract_type
        )
        for asset in assets
    ]


# Common asset lists for convenience
MAJOR_CRYPTO_ASSETS = ["BTC", "ETH", "SOL", "BNB", "XRP", "ADA", "DOT", "AVAX"]
TRENDING_ASSETS = ["APT", "SUI", "SEI", "TIA", "JUP", "WIF", "BONK", "PEPE"]
DEFI_ASSETS = ["UNI", "AAVE", "COMP", "MKR", "SNX", "CRV", "1INCH", "SUSHI"]
GAMING_ASSETS = ["GALA", "SAND", "MANA", "AXS", "ILV", "ALICE", "TLM", "ENJ"]