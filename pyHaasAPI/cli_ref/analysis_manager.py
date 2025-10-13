"""
Centralized analysis functionality for all CLIs.
Extracts common analysis logic from duplicated CLI files.
"""

import asyncio
from typing import Dict, List, Any, Optional
from pyHaasAPI.core.logging import get_logger


class AnalysisManager:
    """Centralized analysis functionality for all CLIs"""
    
    def __init__(self, lab_api, analysis_service):
        self.lab_api = lab_api
        self.analysis_service = analysis_service
        self.logger = get_logger("analysis_manager")

    async def analyze_lab_with_zero_drawdown(self, lab_id: str, min_winrate: float, sort_by: str) -> Dict[str, Any]:
        """Unified lab analysis with zero drawdown filtering"""
        try:
            self.logger.info(f"Analyzing lab {lab_id} with min_winrate={min_winrate}, sort_by={sort_by}")
            
            # Get lab details
            lab_details = await self.lab_api.get_lab(lab_id)
            if not lab_details:
                return {"error": f"Lab {lab_id} not found", "lab_id": lab_id}
            
            # Get backtest results
            result = await self.analysis_service.analyze_lab(lab_id)
            if not result or not hasattr(result, 'top_backtests'):
                return {"error": f"No backtest results for lab {lab_id}", "lab_id": lab_id}
            
            # Filter for zero drawdown backtests
            filtered_backtests = self.filter_zero_drawdown_backtests(result.top_backtests, min_winrate)
            
            # Sort by specified metric
            sorted_backtests = self.sort_backtests_by_metric(filtered_backtests, sort_by)
            
            return {
                "lab_id": lab_id,
                "lab_name": getattr(lab_details, 'name', f'Lab {lab_id}'),
                "total_backtests": len(result.top_backtests),
                "filtered_backtests": len(filtered_backtests),
                "zero_drawdown_backtests": sorted_backtests,
                "analysis_summary": {
                    "min_winrate": min_winrate,
                    "sort_by": sort_by,
                    "filtered_count": len(filtered_backtests)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing lab {lab_id}: {e}")
            return {"error": str(e), "lab_id": lab_id}

    async def analyze_all_labs_with_zero_drawdown(self, min_winrate: float, sort_by: str) -> Dict[str, Any]:
        """Unified analysis of all labs"""
        try:
            self.logger.info(f"Analyzing all labs with min_winrate={min_winrate}, sort_by={sort_by}")
            
            # Get all labs
            labs = await self.lab_api.get_labs()
            if not labs:
                return {"error": "No labs found", "labs": []}
            
            all_results = {}
            total_filtered = 0
            
            for lab in labs:
                lab_id = getattr(lab, 'id', None)
                if not lab_id:
                    continue
                    
                lab_result = await self.analyze_lab_with_zero_drawdown(lab_id, min_winrate, sort_by)
                if "error" not in lab_result:
                    all_results[lab_id] = lab_result
                    total_filtered += lab_result.get("filtered_backtests", 0)
            
            return {
                "total_labs": len(labs),
                "analyzed_labs": len(all_results),
                "total_filtered_backtests": total_filtered,
                "lab_results": all_results,
                "analysis_summary": {
                    "min_winrate": min_winrate,
                    "sort_by": sort_by,
                    "total_labs": len(labs),
                    "analyzed_labs": len(all_results)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing all labs: {e}")
            return {"error": str(e), "labs": []}

    def filter_zero_drawdown_backtests(self, backtests: List, min_winrate: float) -> List:
        """Centralized zero drawdown filtering logic"""
        try:
            filtered = []
            for bt in backtests:
                # Check for zero drawdown (max_drawdown >= 0)
                max_drawdown = getattr(bt, 'max_drawdown', -1)
                win_rate = getattr(bt, 'win_rate', 0)
                
                if max_drawdown >= 0 and win_rate >= (min_winrate / 100.0):
                    filtered.append(bt)
            
            self.logger.info(f"Filtered {len(filtered)} backtests from {len(backtests)} total (min_winrate={min_winrate}%)")
            return filtered
            
        except Exception as e:
            self.logger.error(f"Error filtering backtests: {e}")
            return []

    def sort_backtests_by_metric(self, backtests: List, sort_by: str) -> List:
        """Centralized sorting logic"""
        try:
            if not backtests:
                return backtests
                
            if sort_by == "roi":
                sorted_backtests = sorted(backtests, key=lambda x: getattr(x, 'roi_percentage', 0), reverse=True)
            elif sort_by == "roe":
                # Calculate ROE: (realized_profits_usdt / starting_balance) * 100
                sorted_backtests = sorted(backtests, 
                    key=lambda x: (getattr(x, 'realized_profits_usdt', 0) / max(getattr(x, 'starting_balance', 1), 1)) * 100, 
                    reverse=True)
            elif sort_by == "winrate":
                sorted_backtests = sorted(backtests, key=lambda x: getattr(x, 'win_rate', 0), reverse=True)
            else:
                # Default to ROI
                sorted_backtests = sorted(backtests, key=lambda x: getattr(x, 'roi_percentage', 0), reverse=True)
            
            self.logger.info(f"Sorted {len(sorted_backtests)} backtests by {sort_by}")
            return sorted_backtests
            
        except Exception as e:
            self.logger.error(f"Error sorting backtests: {e}")
            return backtests

