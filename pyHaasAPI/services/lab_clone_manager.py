"""
Lab Clone Manager for pyHaasAPI v2

Handles cloning labs to different markets and assigning accounts using v2 APIs.
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
    """Manages cloning labs to different markets and assigning accounts using v2 APIs."""
    
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
        Clone template lab to target markets and assign account using v2 APIs.
        
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
            
            # Get template lab details
            template_lab = await self.lab_api.get_lab_details(template_lab_id)
            
            cloned_map = {}
            
            for coin, market_tag in target_markets.items():
                try:
                    self.logger.info(f"📋 Cloning for {coin} ({market_tag})")
                    
                    # Clone the lab using v2 LabAPI
                    clone_result = await self.lab_api.clone_lab(
                        template_lab_id,
                        new_name=f"{template_lab.name} - {coin} ({stage_label})" if hasattr(template_lab, 'name') else f"{coin} ({stage_label})"
                    )
                    
                    if not clone_result or not hasattr(clone_result, 'lab_id'):
                        raise LabError(f"Failed to clone lab for {coin}")
                    
                    lab_id = getattr(clone_result, 'lab_id', None)
                    if not lab_id:
                        raise LabError(f"Clone result missing lab_id for {coin}")
                    
                    self.logger.info(f"✅ Cloned lab {lab_id} for {coin}")
                    
                    # Update market and account using v2 API
                    try:
                        await self.lab_api.update_lab_details(
                            lab_id,
                            market=market_tag,
                            account_id=account_id
                        )
                        
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
