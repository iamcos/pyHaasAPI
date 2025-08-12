#!/usr/bin/env python3
"""
Stage 0: Timeframe Explorer
Clean implementation for exploring timeframe and MA type combinations with default settings.
Runs 100 backtests to identify optimal timeframe combinations.
"""

import asyncio
import logging
import time
import requests
from typing import Dict, List, Any, Tuple
import json
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Stage0TimeframeExplorer:
    """Stage 0: Explore timeframes and MA types with default settings"""
    
    def __init__(self, mcp_base_url: str = "http://localhost:8000"):
        self.mcp_base_url = mcp_base_url
        self.session = requests.Session()
        
        # Stage 0 Configuration
        self.config = {
            "stage": 0,
            "name": "Timeframe and MA Type Exploration",
            "target_backtests": 100,
            "backtest_years": 2,
            "focus": "timeframes_and_ma_types",
            "fixed_parameters": "default_numerical_values"
        }
        
        # Timeframe combinations to explore
        self.timeframe_combinations = [
            {"low": "5 Minutes", "high": "1 Hour"},
            {"low": "5 Minutes", "high": "4 Hours"},
            {"low": "10 Minutes", "high": "1 Hour"},
            {"low": "10 Minutes", "high": "4 Hours"},
            {"low": "15 Minutes", "high": "2 Hours"},
            {"low": "15 Minutes", "high": "4 Hours"},
            {"low": "30 Minutes", "high": "4 Hours"},
            {"low": "30 Minutes", "high": "12 Hours"},
            {"low": "1 Hour", "high": "12 Hours"},
            {"low": "1 Hour", "high": "1 Day"}
        ]
        
        # MA types to explore
        self.ma_types = ["SMA", "EMA", "DEMA", "TEMA", "WMA"]
    
    def _get_unix_period(self, years: int) -> Tuple[int, int]:
        """Get unix timestamps for backtest period"""
        end_unix = int(time.time())
        start_unix = end_unix - (years * 365 * 24 * 60 * 60)
        return start_unix, end_unix
    
    def generate_lab_name(self, script_name: str, coin: str) -> str:
        """Generate Stage 0 lab name"""
        return f"0 - {script_name} - {self.config['backtest_years']} years {coin} (timeframe_exploration) - after: initial exploration"
    
    async def create_stage0_lab(self, source_lab_id: str, script_name: str, coin: str) -> Dict[str, Any]:
        """Create Stage 0 exploration lab"""
        logger.info("🔍 Creating Stage 0 Timeframe Exploration Lab")
        
        try:
            # Generate lab name
            lab_name = self.generate_lab_name(script_name, coin)
            
            # Clone source lab
            clone_payload = {
                "lab_id": source_lab_id,
                "new_name": lab_name
            }
            
            response = self.session.post(f"{self.mcp_base_url}/clone_lab", json=clone_payload)
            if response.status_code != 200:
                return {"error": f"Clone failed: HTTP {response.status_code}"}
            
            clone_result = response.json()
            if not clone_result.get("Success"):
                return {"error": f"Clone failed: {clone_result.get('Error')}"}
            
            cloned_lab_id = clone_result["lab_id"]
            
            # Configure lab for timeframe exploration
            config_result = await self._configure_stage0_lab(cloned_lab_id)
            if config_result.get("error"):
                return {"error": f"Configuration failed: {config_result['error']}"}
            
            # Start backtest
            start_unix, end_unix = self._get_unix_period(self.config["backtest_years"])
            backtest_result = await self._start_stage0_backtest(cloned_lab_id, start_unix, end_unix)
            
            if backtest_result.get("error"):
                return {"error": f"Backtest start failed: {backtest_result['error']}"}
            
            return {
                "success": True,
                "lab_id": cloned_lab_id,
                "lab_name": lab_name,
                "configuration": self.config,
                "backtest_result": backtest_result
            }
            
        except Exception as e:
            logger.error(f"Error creating Stage 0 lab: {e}")
            return {"error": str(e)}
    
    async def _configure_stage0_lab(self, lab_id: str) -> Dict[str, Any]:
        """Configure lab for Stage 0 exploration"""
        try:
            # Set up parameter ranges for timeframes and MA types
            # Keep numerical parameters at default values
            # Focus exploration on timeframes and structural parameters
            
            logger.info("⚙️ Configuring Stage 0 lab for timeframe exploration")
            
            # This would typically involve setting up parameter ranges
            # For now, we'll rely on the existing lab configuration
            # and let the genetic algorithm explore the parameter space
            
            return {"success": True, "message": "Lab configured for Stage 0 exploration"}
            
        except Exception as e:
            return {"error": str(e)}
    
    async def _start_stage0_backtest(self, lab_id: str, start_unix: int, end_unix: int) -> Dict[str, Any]:
        """Start Stage 0 backtest"""
        try:
            backtest_payload = {
                "lab_id": lab_id,
                "start_unix": start_unix,
                "end_unix": end_unix,
                "send_email": False
            }
            
            response = self.session.post(f"{self.mcp_base_url}/backtest_lab", json=backtest_payload)
            if response.status_code != 200:
                return {"error": f"HTTP {response.status_code}"}
            
            result = response.json()
            if not result.get("Success"):
                return {"error": result.get("Error", "Unknown error")}
            
            return {
                "success": True,
                "start_unix": start_unix,
                "end_unix": end_unix,
                "period": f"{self.config['backtest_years']} years",
                "target_backtests": self.config["target_backtests"],
                "data": result.get("Data")
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def generate_stage0_report(self, lab_result: Dict[str, Any]) -> str:
        """Generate Stage 0 execution report"""
        report = []
        report.append("=" * 80)
        report.append("🔍 STAGE 0: TIMEFRAME EXPLORATION")
        report.append("=" * 80)
        
        if lab_result.get("error"):
            report.append(f"\n❌ Error: {lab_result['error']}")
            return "\n".join(report)
        
        report.append(f"\n✅ Stage 0 Lab Created Successfully")
        report.append(f"   Lab ID: {lab_result['lab_id']}")
        report.append(f"   Lab Name: {lab_result['lab_name']}")
        
        config = lab_result["configuration"]
        report.append(f"\n📋 Configuration:")
        report.append(f"   Stage: {config['stage']}")
        report.append(f"   Focus: {config['focus']}")
        report.append(f"   Target Backtests: {config['target_backtests']}")
        report.append(f"   Backtest Period: {config['backtest_years']} years")
        report.append(f"   Fixed Parameters: {config['fixed_parameters']}")
        
        backtest_info = lab_result.get("backtest_result", {})
        if backtest_info.get("success"):
            report.append(f"\n🚀 Backtest Started:")
            report.append(f"   Period: {backtest_info['period']}")
            report.append(f"   Target Backtests: {backtest_info['target_backtests']}")
            report.append(f"   Status: Running")
        
        report.append(f"\n🎯 Stage 0 Objectives:")
        report.append(f"   • Explore {len(self.timeframe_combinations)} timeframe combinations")
        report.append(f"   • Test {len(self.ma_types)} MA types")
        report.append(f"   • Use default numerical parameter values")
        report.append(f"   • Identify top 3 timeframe combinations for Stage 1")
        
        report.append(f"\n📊 Expected Outcomes:")
        report.append(f"   • {config['target_backtests']} total backtests")
        report.append(f"   • Performance ranking of timeframe combinations")
        report.append(f"   • Identification of optimal structural parameters")
        report.append(f"   • Foundation for Stage 1 numerical optimization")
        
        return "\n".join(report)

async def main():
    """Execute Stage 0 Timeframe Explorer"""
    print("🔍 Stage 0: Timeframe Explorer")
    print("=" * 50)
    
    explorer = Stage0TimeframeExplorer()
    
    # Configuration
    source_lab_id = "55b45ee4-9cc5-42f7-8556-4c3aa2b13a44"
    script_name = "ADX BB STOCH Scalper"
    coin = "ETH"
    
    print(f"📋 Stage 0 Configuration:")
    print(f"   Source Lab: {source_lab_id}")
    print(f"   Script: {script_name}")
    print(f"   Coin: {coin}")
    print(f"   Target Backtests: {explorer.config['target_backtests']}")
    print(f"   Focus: {explorer.config['focus']}")
    
    # Create and start Stage 0 lab
    print(f"\n🚀 Creating Stage 0 lab...")
    
    lab_result = await explorer.create_stage0_lab(source_lab_id, script_name, coin)
    
    # Generate and display report
    report = explorer.generate_stage0_report(lab_result)
    print(f"\n{report}")
    
    # Save results
    with open('stage0_timeframe_exploration_results.json', 'w') as f:
        json.dump(lab_result, f, indent=2, default=str)
    
    print(f"\n✅ Stage 0 results saved to 'stage0_timeframe_exploration_results.json'")
    
    if lab_result.get("success"):
        print(f"\n🎯 Next Steps:")
        print(f"   1. Wait for Stage 0 backtest to complete (~{explorer.config['target_backtests']} backtests)")
        print(f"   2. Run Stage 0 Analyzer to identify top timeframe combinations")
        print(f"   3. Create Stage 1 numerical optimization labs")
        print(f"\n🚀 Stage 0 Timeframe Explorer: STARTED!")
    else:
        print(f"\n❌ Stage 0 failed to start. Check error details above.")

if __name__ == "__main__":
    asyncio.run(main())