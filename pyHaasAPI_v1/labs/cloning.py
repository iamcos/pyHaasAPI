"""
Lab Cloning System

This module provides functionality for cloning and managing HaasOnline labs
with support for market discovery, automated configuration, and bulk operations.
"""

import logging
import time
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum

from ..model import CreateLabRequest, CloudMarket, LabDetails
from ..markets.discovery import MarketDiscovery, MarketInfo, MarketType

logger = logging.getLogger(__name__)

@dataclass
class LabCloneRequest:
    """Request for cloning a lab"""
    base_lab_id: str
    new_lab_name: str
    market_info: MarketInfo
    account_id: str
    lab_config: Optional[Dict[str, Any]] = None
    custom_parameters: Optional[Dict[str, Any]] = None

@dataclass
class LabCloneResult:
    """Result of a lab cloning operation"""
    success: bool
    new_lab_id: Optional[str]
    market_tag: str
    error_message: Optional[str] = None
    execution_time: float = 0.0
    clone_request: Optional[LabCloneRequest] = None

class LabCloner:
    """Clones and manages HaasOnline labs with advanced features"""
    
    def __init__(self, executor, market_discovery: MarketDiscovery = None):
        """
        Initialize lab cloner.
        
        Args:
            executor: HaasOnline API executor
            market_discovery: Market discovery instance (optional)
        """
        self.executor = executor
        self.market_discovery = market_discovery or MarketDiscovery(executor)
        
        # Cloning statistics
        self._clone_stats = {
            'total_attempts': 0,
            'total_successes': 0,
            'total_failures': 0,
            'start_time': None
        }
    
    def clone_lab(self, clone_request: LabCloneRequest) -> LabCloneResult:
        """
        Clone a single lab.
        
        Args:
            clone_request: Lab cloning request
            
        Returns:
            Lab cloning result
        """
        start_time = time.time()
        self._clone_stats['total_attempts'] += 1
        
        if self._clone_stats['start_time'] is None:
            self._clone_stats['start_time'] = start_time
        
        logger.info(f"Cloning lab {clone_request.base_lab_id} for market {clone_request.market_info.market_tag}")
        
        try:
            # Get the base lab details
            base_lab = self._get_base_lab_details(clone_request.base_lab_id)
            if not base_lab:
                return self._create_failure_result(
                    clone_request, 
                    "Failed to get base lab details",
                    start_time
                )
            
            # Create the new lab
            new_lab_id = self._create_lab_from_template(base_lab, clone_request)
            
            if new_lab_id:
                # Apply additional configuration if provided
                if clone_request.lab_config:
                    self._apply_lab_configuration(new_lab_id, clone_request.lab_config)
                
                # Apply custom parameters if provided
                if clone_request.custom_parameters:
                    self._apply_custom_parameters(new_lab_id, clone_request.custom_parameters)
                
                self._clone_stats['total_successes'] += 1
                logger.info(f"Successfully cloned lab: {new_lab_id}")
                
                return LabCloneResult(
                    success=True,
                    new_lab_id=new_lab_id,
                    market_tag=clone_request.market_info.market_tag,
                    execution_time=time.time() - start_time,
                    clone_request=clone_request
                )
            else:
                return self._create_failure_result(
                    clone_request,
                    "Lab creation returned None",
                    start_time
                )
                
        except Exception as e:
            return self._create_failure_result(
                clone_request,
                str(e),
                start_time
            )
    
    def clone_lab_for_markets(
        self, 
        base_lab_id: str, 
        markets: List[MarketInfo],
        account_id: str,
        name_template: str = "{base_name}_{symbol}",
        lab_config: Dict[str, Any] = None,
        progress_callback: Callable[[int, int], None] = None
    ) -> List[LabCloneResult]:
        """
        Clone a lab for multiple markets.
        
        Args:
            base_lab_id: Base lab ID to clone from
            markets: List of markets to clone for
            account_id: Account ID to use for new labs
            name_template: Template for generating lab names
            lab_config: Configuration to apply to all cloned labs
            progress_callback: Optional callback for progress updates
            
        Returns:
            List of clone results
        """
        logger.info(f"Cloning lab {base_lab_id} for {len(markets)} markets")
        
        results = []
        
        # Get base lab name for template
        base_lab = self._get_base_lab_details(base_lab_id)
        base_name = base_lab.name if base_lab else "ClonedLab"
        
        for i, market_info in enumerate(markets):
            try:
                # Generate lab name from template
                lab_name = name_template.format(
                    base_name=base_name,
                    symbol=market_info.symbol.replace('/', '_'),
                    base_asset=market_info.base_asset,
                    quote_asset=market_info.quote_asset,
                    exchange=market_info.exchange,
                    market_type=market_info.market_type.value
                )
                
                # Create clone request
                clone_request = LabCloneRequest(
                    base_lab_id=base_lab_id,
                    new_lab_name=lab_name,
                    market_info=market_info,
                    account_id=account_id,
                    lab_config=lab_config
                )
                
                # Clone the lab
                result = self.clone_lab(clone_request)
                results.append(result)
                
                # Call progress callback if provided
                if progress_callback:
                    progress_callback(i + 1, len(markets))
                
                # Brief pause between clones to avoid overwhelming the server
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Failed to clone lab for market {market_info.market_tag}: {e}")
                results.append(LabCloneResult(
                    success=False,
                    new_lab_id=None,
                    market_tag=market_info.market_tag,
                    error_message=str(e)
                ))
        
        # Log summary
        successes = len([r for r in results if r.success])
        logger.info(f"Lab cloning completed: {successes}/{len(results)} successful")
        
        return results
    
    def clone_lab_for_assets(
        self,
        base_lab_id: str,
        base_assets: List[str],
        account_id: str,
        exchanges: List[str] = None,
        market_types: List[MarketType] = None,
        quote_assets: List[str] = None,
        **kwargs
    ) -> List[LabCloneResult]:
        """
        Clone a lab for specific assets across exchanges.
        
        Args:
            base_lab_id: Base lab ID to clone from
            base_assets: List of base assets (e.g., ["BTC", "ETH"])
            account_id: Account ID to use
            exchanges: List of exchanges to use (None for all)
            market_types: List of market types to include (None for all)
            quote_assets: List of quote assets to filter by (None for all)
            **kwargs: Additional arguments passed to clone_lab_for_markets
            
        Returns:
            List of clone results
        """
        logger.info(f"Discovering markets for assets: {base_assets}")
        
        # Discover all markets
        all_markets = self.market_discovery.discover_all_markets(exchanges)
        
        # Filter markets by criteria
        target_markets = []
        for exchange, markets in all_markets.items():
            filtered_markets = self.market_discovery.filter_markets(
                markets,
                base_assets=base_assets,
                market_types=market_types,
                quote_assets=quote_assets,
                active_only=True
            )
            target_markets.extend(filtered_markets)
        
        logger.info(f"Found {len(target_markets)} markets matching criteria")
        
        return self.clone_lab_for_markets(
            base_lab_id=base_lab_id,
            markets=target_markets,
            account_id=account_id,
            **kwargs
        )
    
    def clone_lab_for_perpetual_markets(
        self,
        base_lab_id: str,
        account_id: str,
        base_assets: List[str] = None,
        exchanges: List[str] = None,
        **kwargs
    ) -> List[LabCloneResult]:
        """
        Clone a lab for perpetual markets.
        
        Args:
            base_lab_id: Base lab ID to clone from
            account_id: Account ID to use
            base_assets: List of base assets to include (None for all)
            exchanges: List of exchanges to use (None for default)
            **kwargs: Additional arguments
            
        Returns:
            List of clone results
        """
        return self.clone_lab_for_assets(
            base_lab_id=base_lab_id,
            base_assets=base_assets or ["BTC", "ETH", "BNB", "ADA", "SOL"],
            account_id=account_id,
            exchanges=exchanges,
            market_types=[MarketType.PERPETUAL],
            **kwargs
        )
    
    def get_cloning_statistics(self) -> Dict[str, Any]:
        """Get cloning statistics"""
        stats = self._clone_stats.copy()
        
        if stats['start_time']:
            stats['total_time'] = time.time() - stats['start_time']
            stats['success_rate'] = (stats['total_successes'] / stats['total_attempts'] * 100) if stats['total_attempts'] > 0 else 0
            stats['average_time_per_clone'] = stats['total_time'] / stats['total_attempts'] if stats['total_attempts'] > 0 else 0
        
        return stats
    
    def reset_statistics(self):
        """Reset cloning statistics"""
        self._clone_stats = {
            'total_attempts': 0,
            'total_successes': 0,
            'total_failures': 0,
            'start_time': None
        }
    
    def _get_base_lab_details(self, lab_id: str) -> Optional[LabDetails]:
        """Get base lab details"""
        try:
            from .. import api
            return api.get_lab_details(self.executor, lab_id)
        except Exception as e:
            logger.error(f"Failed to get lab details for {lab_id}: {e}")
            return None
    
    def _create_lab_from_template(self, base_lab: LabDetails, clone_request: LabCloneRequest) -> Optional[str]:
        """Create a new lab based on a template lab"""
        try:
            # Create market object from market info
            market = CloudMarket(
                primary=clone_request.market_info.base_asset,
                secondary=clone_request.market_info.quote_asset,
                # Add other market properties as needed
            )
            
            # Create lab request
            lab_request = CreateLabRequest.with_generated_name(
                script_id=base_lab.script_id,
                account_id=clone_request.account_id,
                market=market,
                exchange_code=clone_request.market_info.exchange,
                interval=base_lab.settings.interval,
                default_price_data_style="CandleStick"  # Default style
            )
            
            # Override name with custom name
            lab_request.name = clone_request.new_lab_name
            
            # Set market tag directly
            lab_request.market = clone_request.market_info.market_tag
            
            # Create the lab
            from .. import api
            new_lab = api.create_lab(self.executor, lab_request)
            
            return new_lab.lab_id if new_lab else None
            
        except Exception as e:
            logger.error(f"Failed to create lab from template: {e}")
            raise
    
    def _apply_lab_configuration(self, lab_id: str, config: Dict[str, Any]):
        """Apply additional configuration to a lab"""
        try:
            from .. import api
            
            # Get current lab details
            lab_details = api.get_lab_details(self.executor, lab_id)
            if not lab_details:
                logger.warning(f"Could not get lab details for {lab_id}")
                return
            
            # Update configuration
            if 'max_population' in config:
                lab_details.config.max_population = config['max_population']
            if 'max_generations' in config:
                lab_details.config.max_generations = config['max_generations']
            if 'max_elites' in config:
                lab_details.config.max_elites = config['max_elites']
            if 'mix_rate' in config:
                lab_details.config.mix_rate = config['mix_rate']
            if 'adjust_rate' in config:
                lab_details.config.adjust_rate = config['adjust_rate']
            
            # Save updated configuration
            api.update_lab_details(self.executor, lab_details)
            
            logger.info(f"Applied configuration to lab {lab_id}")
            
        except Exception as e:
            logger.warning(f"Failed to apply lab configuration to {lab_id}: {e}")
    
    def _apply_custom_parameters(self, lab_id: str, parameters: Dict[str, Any]):
        """Apply custom parameters to a lab"""
        try:
            from .. import api
            
            # Get current lab details
            lab_details = api.get_lab_details(self.executor, lab_id)
            if not lab_details:
                logger.warning(f"Could not get lab details for {lab_id}")
                return
            
            # Update parameters
            for param_key, param_value in parameters.items():
                # Find and update the parameter
                for param in lab_details.parameters:
                    if param.key == param_key:
                        param.options = [str(param_value)]
                        break
            
            # Save updated parameters
            api.update_lab_details(self.executor, lab_details)
            
            logger.info(f"Applied custom parameters to lab {lab_id}")
            
        except Exception as e:
            logger.warning(f"Failed to apply custom parameters to {lab_id}: {e}")
    
    def _create_failure_result(
        self, 
        clone_request: LabCloneRequest, 
        error_message: str, 
        start_time: float
    ) -> LabCloneResult:
        """Create a failure result"""
        self._clone_stats['total_failures'] += 1
        
        return LabCloneResult(
            success=False,
            new_lab_id=None,
            market_tag=clone_request.market_info.market_tag,
            error_message=error_message,
            execution_time=time.time() - start_time,
            clone_request=clone_request
        )

# Convenience functions
def clone_lab_for_asset(
    executor,
    base_lab_id: str,
    base_asset: str,
    account_id: str,
    exchanges: List[str] = None
) -> List[LabCloneResult]:
    """
    Convenience function to clone a lab for a specific asset.
    
    Args:
        executor: HaasOnline API executor
        base_lab_id: Base lab ID
        base_asset: Base asset symbol
        account_id: Account ID
        exchanges: List of exchanges
        
    Returns:
        List of clone results
    """
    cloner = LabCloner(executor)
    return cloner.clone_lab_for_assets(
        base_lab_id=base_lab_id,
        base_assets=[base_asset],
        account_id=account_id,
        exchanges=exchanges
    )

def clone_lab_for_symbol(
    executor,
    base_lab_id: str,
    symbol: str,
    account_id: str,
    exchanges: List[str] = None
) -> List[LabCloneResult]:
    """
    Convenience function to clone a lab for a specific trading symbol.
    
    Args:
        executor: HaasOnline API executor
        base_lab_id: Base lab ID
        symbol: Trading symbol (e.g., "BTC/USDT")
        account_id: Account ID
        exchanges: List of exchanges
        
    Returns:
        List of clone results
    """
    if '/' not in symbol:
        raise ValueError("Symbol must be in format 'BASE/QUOTE'")
    
    base_asset, quote_asset = symbol.split('/')
    
    cloner = LabCloner(executor)
    return cloner.clone_lab_for_assets(
        base_lab_id=base_lab_id,
        base_assets=[base_asset],
        account_id=account_id,
        exchanges=exchanges,
        quote_assets=[quote_asset]
    )