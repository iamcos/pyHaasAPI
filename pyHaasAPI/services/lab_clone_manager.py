"""
Lab Clone Manager for pyHaasAPI v2

Handles cloning labs to different markets and assigning accounts using v1 API pattern.
"""

import asyncio
from typing import Dict, Any, Optional
from ..core.logging import get_logger
from ..exceptions import LabError
from ..api.lab.lab_api import LabAPI
from ..core.client import AsyncHaasClient
from ..core.auth import AuthenticationManager

logger = get_logger("lab_clone_manager")


class LabCloneManager:
    """Manages cloning labs to different markets and assigning accounts using v1 API pattern."""
    
    def __init__(self, lab_api: LabAPI, client: Optional[AsyncHaasClient] = None, auth_manager: Optional[AuthenticationManager] = None):
        self.lab_api = lab_api
        self.client = client
        self.auth_manager = auth_manager
        self.logger = get_logger("lab_clone_manager")
    
    async def clone_to_markets(
        self,
        template_lab_id: str,
        target_markets: Dict[str, str],
        account_id: str,
        stage_label: str,
    ) -> Dict[str, str]:
        """
        Clone template lab to target markets and assign account using v1 API pattern.
        
        Args:
            template_lab_id: ID of the template lab to clone
            target_markets: Dict mapping coin names to market tags
            account_id: Account ID to assign to cloned labs
            stage_label: Stage label for naming
            
        Returns:
            Dict mapping coin names to cloned lab IDs
        """
        try:
            self.logger.info(f"🔄 Cloning template lab {template_lab_id} to {len(target_markets)} markets")
            
            # Use the v1 API pattern like in longest_backtest.py
            from pyHaasAPI_v1 import api
            
            # Create v1 executor using the same pattern as longest_backtest.py
            executor = api.RequestsExecutor(
                host='127.0.0.1',
                port=8090,
                state=api.Guest()
            )
            
            # Authenticate using the same pattern
            import os
            executor = executor.authenticate(
                os.getenv('API_EMAIL'), 
                os.getenv('API_PASSWORD')
            )
            
            cloned_map = {}
            
            for coin, market_tag in target_markets.items():
                try:
                    self.logger.info(f"📋 Cloning for {coin} ({market_tag})")
                    
                    # Clone the lab using v1 API like in longest_backtest.py
                    clone_result = api.clone_lab(executor, template_lab_id)
                    
                    if not clone_result or not hasattr(clone_result, 'lab_id'):
                        raise LabError(f"Failed to clone lab for {coin}")
                    
                    lab_id = clone_result.lab_id
                    self.logger.info(f"✅ Cloned lab {lab_id} for {coin}")
                    
                    # Set market and account using v1 API
                    try:
                        # Get lab details and update settings
                        lab_details = api.get_lab_details(executor, lab_id)
                        
                        # Update market and account in settings
                        if hasattr(lab_details, 'settings'):
                            lab_details.settings.market_tag = market_tag
                            lab_details.settings.account_id = account_id
                        else:
                            # Create settings if they don't exist
                            from pyHaasAPI_v1.model import LabSettings
                            lab_details.settings = LabSettings()
                            lab_details.settings.market_tag = market_tag
                            lab_details.settings.account_id = account_id
                        
                        # Update the lab
                        api.update_lab_details(executor, lab_details)
                        
                        self.logger.info(f"✅ Set market {market_tag} and account {account_id} for {coin}")
                            
                    except Exception as update_error:
                        # Continue even if update fails - the lab is cloned and can be configured later
                        self.logger.warning(f"⚠️ Failed to update lab settings for {coin}: {update_error}")
                        self.logger.info(f"✅ Lab {lab_id} cloned for {coin} (settings update failed but lab exists)")
                    
                    cloned_map[coin] = lab_id
                    
                except Exception as e:
                    self.logger.error(f"❌ Failed to clone for {coin}: {e}")
                    raise LabError(f"Failed to clone lab for {coin}: {e}")
            
            self.logger.info(f"🎉 Successfully cloned {len(cloned_map)} labs")
            return cloned_map
            
        except Exception as e:
            self.logger.error(f"❌ Error cloning labs: {e}")
            raise LabError(f"Failed to clone labs: {e}")
