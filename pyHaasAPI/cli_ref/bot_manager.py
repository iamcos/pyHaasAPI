"""
Centralized bot creation and management functionality.
Extracts common bot creation logic from duplicated CLI files.
"""

import asyncio
from typing import Dict, List, Any, Optional
from pyHaasAPI.core.logging import get_logger


class BotManager:
    """Centralized bot creation and management"""
    
    def __init__(self, bot_service):
        self.bot_service = bot_service
        self.logger = get_logger("bot_manager")

    async def create_bot_from_backtest(self, backtest_id: str, lab_name: str, script_name: str, 
                                     roi_percentage: float, win_rate: float) -> Dict[str, Any]:
        """Unified bot creation from backtest"""
        try:
            self.logger.info(f"Creating bot from backtest {backtest_id}")
            
            # Generate bot name using centralized naming convention
            bot_name = self.generate_bot_name(lab_name, script_name, roi_percentage, win_rate)
            
            # Get default bot configuration
            bot_config = self.get_default_bot_config()
            
            # Create bot using bot service
            bot_result = await self.bot_service.create_bot_from_backtest(
                backtest_id=backtest_id,
                bot_name=bot_name,
                **bot_config
            )
            
            if bot_result:
                return {
                    "success": True,
                    "bot_id": getattr(bot_result, 'id', None),
                    "bot_name": bot_name,
                    "backtest_id": backtest_id,
                    "lab_name": lab_name,
                    "script_name": script_name,
                    "roi_percentage": roi_percentage,
                    "win_rate": win_rate,
                    "bot_config": bot_config
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to create bot",
                    "bot_name": bot_name,
                    "backtest_id": backtest_id
                }
                
        except Exception as e:
            self.logger.error(f"Error creating bot from backtest {backtest_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "backtest_id": backtest_id
            }

    async def create_bots_from_analysis(self, lab_results: Dict[str, Any], bots_per_lab: int = 2) -> List[Dict[str, Any]]:
        """Unified bot creation from analysis results"""
        try:
            self.logger.info(f"Creating bots from analysis results (max {bots_per_lab} per lab)")
            
            created_bots = []
            
            for lab_id, lab_result in lab_results.items():
                if "error" in lab_result:
                    continue
                    
                lab_name = lab_result.get("lab_name", f"Lab {lab_id}")
                zero_drawdown_backtests = lab_result.get("zero_drawdown_backtests", [])
                
                # Take top N backtests for bot creation
                top_backtests = zero_drawdown_backtests[:bots_per_lab]
                
                for backtest in top_backtests:
                    backtest_id = getattr(backtest, 'id', None)
                    script_name = getattr(backtest, 'script_name', 'Unknown Script')
                    roi_percentage = getattr(backtest, 'roi_percentage', 0)
                    win_rate = getattr(backtest, 'win_rate', 0)
                    
                    if backtest_id:
                        bot_result = await self.create_bot_from_backtest(
                            backtest_id, lab_name, script_name, roi_percentage, win_rate
                        )
                        created_bots.append(bot_result)
            
            self.logger.info(f"Created {len(created_bots)} bots from analysis results")
            return created_bots
            
        except Exception as e:
            self.logger.error(f"Error creating bots from analysis: {e}")
            return []

    def generate_bot_name(self, lab_name: str, script_name: str, roi_percentage: float, win_rate: float) -> str:
        """Centralized bot naming convention"""
        try:
            # Format: "Lab Name - Script Name - ROI% pop/gen WinRate%"
            bot_name = f"{lab_name} - {script_name} - {roi_percentage:.1f}% pop/gen {win_rate*100:.0f}%"
            return bot_name
            
        except Exception as e:
            self.logger.error(f"Error generating bot name: {e}")
            return f"{lab_name} - {script_name} - Bot"

    def get_default_bot_config(self) -> Dict[str, Any]:
        """Centralized bot configuration"""
        return {
            "trade_amount_usdt": 2000.0,  # $2000 USDT
            "leverage": 20.0,  # 20x leverage
            "margin_mode": "CROSS",  # Cross margin
            "position_mode": "HEDGE"  # Hedge mode
        }





