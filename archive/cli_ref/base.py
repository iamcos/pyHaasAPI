"""
Enhanced BaseCLI with centralized managers.
Provides common functionality for all CLI modules.
"""

import asyncio
from typing import Dict, List, Any, Optional
from pyHaasAPI.cli.base import BaseCLI
from pyHaasAPI.cli_ref.analysis_manager import AnalysisManager
from pyHaasAPI.cli_ref.bot_manager import BotManager
from pyHaasAPI.cli_ref.report_manager import ReportManager
from pyHaasAPI.core.logging import get_logger


class EnhancedBaseCLI(BaseCLI):
    """Enhanced base CLI with centralized managers"""
    
    def __init__(self):
        super().__init__()
        self.analysis_manager: Optional[AnalysisManager] = None
        self.bot_manager: Optional[BotManager] = None
        self.report_manager: Optional[ReportManager] = None
        self.logger = get_logger("enhanced_base_cli")

    async def connect(self) -> bool:
        """Connect to APIs and initialize managers"""
        try:
            # Connect using parent class
            connected = await super().connect()
            if not connected:
                return False
            
            # Initialize managers
            self.analysis_manager = AnalysisManager(self.lab_api, self.analysis_service)
            self.bot_manager = BotManager(self.bot_service)
            self.report_manager = ReportManager()
            
            self.logger.info("Enhanced BaseCLI connected with managers initialized")
            return True
            
        except Exception as e:
            self.logger.error(f"Error connecting Enhanced BaseCLI: {e}")
            return False

    async def analyze_lab_with_zero_drawdown(self, lab_id: str, min_winrate: float = 55.0, sort_by: str = "roe") -> Dict[str, Any]:
        """Analyze a single lab with zero drawdown requirement"""
        if not self.analysis_manager:
            return {"error": "Analysis manager not initialized"}
        
        return await self.analysis_manager.analyze_lab_with_zero_drawdown(lab_id, min_winrate, sort_by)

    async def analyze_all_labs_with_zero_drawdown(self, min_winrate: float = 55.0, sort_by: str = "roe") -> Dict[str, Any]:
        """Analyze all labs with zero drawdown requirement"""
        if not self.analysis_manager:
            return {"error": "Analysis manager not initialized"}
        
        return await self.analysis_manager.analyze_all_labs_with_zero_drawdown(min_winrate, sort_by)

    async def create_bot_from_backtest(self, backtest_id: str, lab_name: str, script_name: str, 
                                     roi_percentage: float, win_rate: float) -> Dict[str, Any]:
        """Create a bot from a backtest"""
        if not self.bot_manager:
            return {"success": False, "error": "Bot manager not initialized"}
        
        return await self.bot_manager.create_bot_from_backtest(backtest_id, lab_name, script_name, roi_percentage, win_rate)

    async def create_bots_from_analysis(self, lab_results: Dict[str, Any], bots_per_lab: int = 2) -> List[Dict[str, Any]]:
        """Create top bots for each lab with zero drawdown"""
        if not self.bot_manager:
            return []
        
        return await self.bot_manager.create_bots_from_analysis(lab_results, bots_per_lab)

    def print_analysis_report(self, lab_results: Dict[str, Any]):
        """Print analysis results"""
        if not self.report_manager:
            print("❌ Report manager not initialized")
            return
        
        self.report_manager.print_analysis_report(lab_results)

    def print_bot_creation_report(self, created_bots: List[Dict[str, Any]]):
        """Print bot creation results"""
        if not self.report_manager:
            print("❌ Report manager not initialized")
            return
        
        self.report_manager.print_bot_creation_report(created_bots)

    def print_summary_report(self, analysis_results: Dict[str, Any], bot_results: List[Dict[str, Any]]):
        """Print combined summary report"""
        if not self.report_manager:
            print("❌ Report manager not initialized")
            return
        
        self.report_manager.print_summary_report(analysis_results, bot_results)

    async def run_comprehensive_analysis_and_bot_creation(self, lab_ids: List[str] = None, 
                                                        min_winrate: float = 55.0, 
                                                        sort_by: str = "roe", 
                                                        bots_per_lab: int = 2) -> Dict[str, Any]:
        """Run comprehensive analysis and bot creation workflow"""
        try:
            self.logger.info("Starting comprehensive analysis and bot creation workflow")
            
            # Step 1: Analyze labs
            if lab_ids:
                # Analyze specific labs
                analysis_results = {}
                for lab_id in lab_ids:
                    lab_result = await self.analyze_lab_with_zero_drawdown(lab_id, min_winrate, sort_by)
                    if "error" not in lab_result:
                        analysis_results[lab_id] = lab_result
            else:
                # Analyze all labs
                analysis_results = await self.analyze_all_labs_with_zero_drawdown(min_winrate, sort_by)
            
            # Step 2: Print analysis report
            self.print_analysis_report(analysis_results)
            
            # Step 3: Create bots from analysis
            if "error" not in analysis_results:
                lab_results = analysis_results.get("lab_results", analysis_results)
                bot_results = await self.create_bots_from_analysis(lab_results, bots_per_lab)
                
                # Step 4: Print bot creation report
                self.print_bot_creation_report(bot_results)
                
                # Step 5: Print summary
                self.print_summary_report(analysis_results, bot_results)
                
                return {
                    "success": True,
                    "analysis_results": analysis_results,
                    "bot_results": bot_results,
                    "summary": {
                        "analyzed_labs": len(lab_results),
                        "created_bots": len([b for b in bot_results if b.get("success", False)]),
                        "failed_bots": len([b for b in bot_results if not b.get("success", False)])
                    }
                }
            else:
                return {
                    "success": False,
                    "error": analysis_results.get("error", "Analysis failed"),
                    "analysis_results": analysis_results,
                    "bot_results": []
                }
                
        except Exception as e:
            self.logger.error(f"Error in comprehensive workflow: {e}")
            return {
                "success": False,
                "error": str(e),
                "analysis_results": {},
                "bot_results": []
            }





