"""
Lab Config Manager for pyHaasAPI v2

Handles lab configuration including renaming and setting trade amounts.
"""

import asyncio
from typing import Optional
from ..core.logging import get_logger
from ..exceptions import LabError
from ..api.lab.lab_api import LabAPI
from ..api.market.market_api import MarketAPI
from ..core.client import AsyncHaasClient
from ..core.auth import AuthenticationManager

logger = get_logger("lab_config_manager")


class LabConfigManager:
    """Manages lab configuration including renaming and trade amounts."""
    
    def __init__(self, lab_api: LabAPI, market_api: Optional[MarketAPI] = None, client: Optional[AsyncHaasClient] = None, auth_manager: Optional[AuthenticationManager] = None):
        self.lab_api = lab_api
        self.market_api = market_api
        self.client = client
        self.auth_manager = auth_manager
        self.logger = get_logger("lab_config_manager")
    
    async def rename_lab(
        self,
        lab_id: str,
        stage_label: str,
        coin: str,
        script_name: str,
        cutoff_date: Optional[str] = None,
    ) -> bool:
        """
        Rename lab with stage, coin, script, and optional cutoff date using v2 APIs.
        
        Args:
            lab_id: Lab ID to rename
            stage_label: Stage label (e.g., "cutoff_run")
            coin: Coin name (e.g., "BTC")
            script_name: Script name from template
            cutoff_date: Optional cutoff date to append
            
        Returns:
            True if successful
        """
        try:
            # Get current lab details using v2 API
            lab_details = await self.lab_api.get_lab_details(lab_id)
            current_name = getattr(lab_details, 'name', '')
            
            # Build new name
            if cutoff_date:
                new_name = f"{stage_label}_{coin}_{script_name}_{cutoff_date}"
            else:
                new_name = f"{stage_label}_{coin}_{script_name}"
            
            self.logger.info(f"📝 Renaming lab {lab_id}: '{current_name}' → '{new_name}'")
            
            # Update lab name using v2 API
            update_data = {
                'name': new_name
            }
            
            result = await self.lab_api.update_lab_details(lab_id, update_data)
            
            if result:
                self.logger.info(f"✅ Successfully renamed lab {lab_id}")
                return True
            else:
                self.logger.error(f"❌ Failed to rename lab {lab_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error renaming lab {lab_id}: {e}")
            raise LabError(f"Failed to rename lab {lab_id}: {e}")
    
    async def set_trade_amount_usdt_equivalent(
        self,
        lab_id: str,
        usdt_amount: float,
    ) -> bool:
        """
        Set trade amount to USDT equivalent value using v2 APIs.
        
        Args:
            lab_id: Lab ID to configure
            usdt_amount: USDT equivalent amount
            
        Returns:
            True if successful
        """
        try:
            # Get lab details to find market using v2 API
            lab_details = await self.lab_api.get_lab_details(lab_id)
            market_tag = None
            
            if hasattr(lab_details, 'settings') and hasattr(lab_details.settings, 'market_tag'):
                market_tag = lab_details.settings.market_tag
            
            if not market_tag:
                self.logger.warning(f"⚠️ No market tag found for lab {lab_id}, skipping trade amount")
                return True
            
            self.logger.info(f"💰 Setting trade amount to {usdt_amount} USDT for lab {lab_id}")
            
            # Try to get market info for price conversion
            trade_amount = usdt_amount  # Default to USDT amount
            
            if self.market_api:
                try:
                    market_info = await self.market_api.get_market_info(market_tag)
                    if market_info and hasattr(market_info, 'price'):
                        current_price = getattr(market_info, 'price', 1.0)
                        trade_amount = usdt_amount / current_price
                        self.logger.info(f"📊 Converted {usdt_amount} USDT to {trade_amount:.6f} {market_tag.split('_')[0]} at price {current_price}")
                except Exception as market_error:
                    self.logger.warning(f"⚠️ Market API error: {market_error}, using USDT amount directly")
            
            # Update lab settings with trade amount using v2 API
            update_data = {
                'trade_amount': trade_amount
            }
            
            result = await self.lab_api.update_lab_details(lab_id, update_data)
            
            if result:
                self.logger.info(f"✅ Set trade amount to {trade_amount} for lab {lab_id}")
                return True
            else:
                self.logger.error(f"❌ Failed to set trade amount for lab {lab_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error setting trade amount for lab {lab_id}: {e}")
            raise LabError(f"Failed to set trade amount for lab {lab_id}: {e}")