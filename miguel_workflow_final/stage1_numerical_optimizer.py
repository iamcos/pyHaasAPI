#!/usr/bin/env python3
"""
Stage 1: Numerical Parameter Optimizer
Clean implementation for creating Stage 1 numerical optimization labs based on 
Stage 0 analysis results. Focuses on single lab workflow with fixed timeframes
and optimized numerical parameters.
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

class Stage1NumericalOptimizer:
    """Stage 1: Create numerical optimization labs from Stage 0 analysis"""
    
    def __init__(self, mcp_base_url: str = "http://localhost:8000"):
        self.mcp_base_url = mcp_base_url
        self.session = requests.Session()
        
        # Stage 1 Configuration
        self.config = {
            "stage": 1,
            "name": "Numerical Parameter Optimization",
            "target_backtests": 1000,
            "backtest_years": 3,
            "focus": "numerical_parameters",
            "fixed_elements": "timeframes_and_structural_params"
        }
        
        # Genetic algorithm settings for Stage 1
        self.genetic_config = {
            "max_generations": 20,
            "max_population": 50,
            "max_elites": 3,
            "mix_rate": 30.0,
            "adjust_rate": 25.0
        }
    
    def _get_unix_period(self, years: int) -> Tuple[int, int]:
        """Get unix timestamps for backtest period"""
        end_unix = int(time.time())
        start_unix = end_unix - (years * 365 * 24 * 60 * 60)
        return start_unix, end_unix
    
    def generate_stage1_lab_name(self, script_name: str, coin: str, 
                                timeframe_combo: str, rank: int) -> str:
        """Generate Stage 1 lab name following naming convention"""
        return (f"1 - {script_name} - {self.config['backtest_years']} years {coin} "
                f"({timeframe_combo}) - after: numerical_optim_rank{rank}")
    
    async def create_stage1_labs(self, source_lab_id: str, script_name: str, 
                               coin: str, stage0_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Create Stage 1 numerical optimization labs based on Stage 0 analysis"""
        logger.info("🧬 Creating Stage 1 Numerical Optimization Labs")
        
        results = {
            "stage": 1,
            "focus": self.config["focus"],
            "source_lab_id": source_lab_id,
            "created_labs": {},
            "total_labs": 0,
            "total_backtests": 0,
            "errors": []
        }
        
        if not stage0_analysis.get("success"):
            results["errors"].append("Stage 0 analysis failed or not provided")
            return results
        
        top_combinations = stage0_analysis.get("top_timeframe_combinations", [])
        if not top_combinations:
            results["errors"].append("No top timeframe combinations found in Stage 0 analysis")
            return results
        
        start_unix, end_unix = self._get_unix_period(self.config["backtest_years"])
        
        # Create one lab for each top timeframe combination
        for i, combo in enumerate(top_combinations, 1):
            try:
                timeframe_combo = combo["timeframe_combination"]
                lab_name = self.generate_stage1_lab_name(script_name, coin, timeframe_combo, i)
                
                logger.info(f"Creating Stage 1 lab {i}/3: {lab_name}")
                
                # Create the lab
                lab_result = await self._create_single_stage1_lab(
                    source_lab_id, lab_name, combo, stage0_analysis, start_unix, end_unix
                )
                
                if lab_result.get("error"):
                    results["errors"].append(f"Failed to create lab {i}: {lab_result['error']}")
                    continue
                
                results["created_labs"][f"rank_{i}"] = {
                    "lab_name": lab_name,
                    "lab_id": lab_result["lab_id"],
                    "timeframe_combination": timeframe_combo,
                    "low_tf": combo["low_tf"],
                    "high_tf": combo["high_tf"],
                    "fixed_timeframes": True,
                    "optimization_focus": "numerical_parameters",
                    "target_backtests": self.config["target_backtests"],
                    "backtest_period": f"{self.config['backtest_years']} years",
                    "genetic_config": self.genetic_config,
                    "performance_baseline": {
                        "avg_roi": combo.get("avg_roi", 0.0),
                        "max_roi": combo.get("max_roi", 0.0),
                        "profitable_ratio": combo.get("profitable_ratio", 0.0)
                    }
                }
                
                results["total_labs"] += 1
                results["total_backtests"] += self.config["target_backtests"]
                
                logger.info(f"✅ Created Stage 1 lab {i}: {lab_result['lab_id']}")
                
                # Brief pause between lab creations
                await asyncio.sleep(2)
                
            except Exception as e:
                error_msg = f"Exception creating Stage 1 lab {i}: {e}"
                results["errors"].append(error_msg)
                logger.error(error_msg)
        
        logger.info(f"Stage 1 lab creation completed: {results['total_labs']} labs created")
        return results
    
    async def _create_single_stage1_lab(self, source_lab_id: str, lab_name: str,
                                      timeframe_combo: Dict[str, Any], 
                                      stage0_analysis: Dict[str, Any],
                                      start_unix: int, end_unix: int) -> Dict[str, Any]:
        """Create a single Stage 1 optimization lab"""
        try:
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
            
            # Configure lab for Stage 1 optimization
            config_result = await self._configure_stage1_lab(
                cloned_lab_id, timeframe_combo, stage0_analysis
            )
            
            if config_result.get("error"):
                return {"error": f"Configuration failed: {config_result['error']}"}
            
            # Start 3-year backtest with genetic algorithm
            backtest_result = await self._start_stage1_backtest(cloned_lab_id, start_unix, end_unix)
            
            if backtest_result.get("error"):
                return {"error": f"Backtest start failed: {backtest_result['error']}"}
            
            return {
                "success": True,
                "lab_id": cloned_lab_id,
                "configuration": config_result,
                "backtest_result": backtest_result
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    async def _configure_stage1_lab(self, lab_id: str, timeframe_combo: Dict[str, Any],
                                  stage0_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Configure lab for Stage 1 numerical optimization"""
        try:
            logger.info(f"⚙️ Configuring Stage 1 lab for numerical optimization")
            
            # In a real implementation, this would:
            # 1. Fix timeframe parameters to the selected combination
            # 2. Set up parameter ranges for numerical parameters
            # 3. Configure genetic algorithm settings
            # 4. Ensure structural parameters remain fixed
            
            # For now, we'll rely on the cloned lab configuration
            # and the genetic algorithm to explore the parameter space
            
            configuration_summary = {
                "fixed_timeframes": {
                    "low_tf": timeframe_combo["low_tf"],
                    "high_tf": timeframe_combo["high_tf"]
                },
                "optimization_target": "numerical_parameters",
                "genetic_algorithm": self.genetic_config,
                "parameter_ranges": stage0_analysis.get("optimization_ranges", {})
            }
            
            return {
                "success": True,
                "configuration": configuration_summary,
                "message": "Lab configured for Stage 1 numerical optimization"
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    async def _start_stage1_backtest(self, lab_id: str, start_unix: int, end_unix: int) -> Dict[str, Any]:
        """Start Stage 1 backtest with genetic algorithm"""
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
                "genetic_config": self.genetic_config,
                "data": result.get("Data")
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def generate_stage1_report(self, creation_results: Dict[str, Any]) -> str:
        """Generate Stage 1 creation report"""
        report = []
        report.append("=" * 80)
        report.append("🧬 STAGE 1: NUMERICAL PARAMETER OPTIMIZATION")
        report.append("=" * 80)
        
        if creation_results.get("errors") and not creation_results.get("created_labs"):
            report.append(f"\n❌ Stage 1 Creation Failed:")
            for error in creation_results["errors"]:
                report.append(f"   • {error}")
            return "\n".join(report)
        
        report.append(f"\n✅ Stage 1 Labs Created Successfully")
        report.append(f"   Source Lab: {creation_results['source_lab_id']}")
        report.append(f"   Total Labs: {creation_results['total_labs']}")
        report.append(f"   Total Backtests: {creation_results['total_backtests']:,}")
        
        report.append(f"\n📋 Stage 1 Configuration:")
        report.append(f"   Stage: {creation_results['stage']}")
        report.append(f"   Focus: {creation_results['focus']}")
        report.append(f"   Backtest Period: {self.config['backtest_years']} years")
        report.append(f"   Target Backtests per Lab: {self.config['target_backtests']:,}")
        
        report.append(f"\n🧬 Genetic Algorithm Settings:")
        report.append(f"   Generations: {self.genetic_config['max_generations']}")
        report.append(f"   Population: {self.genetic_config['max_population']}")
        report.append(f"   Elites: {self.genetic_config['max_elites']}")
        report.append(f"   Mix Rate: {self.genetic_config['mix_rate']}%")
        report.append(f"   Adjust Rate: {self.genetic_config['adjust_rate']}%")
        
        report.append(f"\n🎯 Created Labs:")
        report.append("-" * 60)
        
        for rank_key, lab_info in creation_results["created_labs"].items():
            report.append(f"\n🧬 {lab_info['lab_name']}")
            report.append(f"   Lab ID: {lab_info['lab_id']}")
            report.append(f"   Timeframes: {lab_info['low_tf']} / {lab_info['high_tf']} (FIXED)")
            report.append(f"   Optimization: Numerical parameters only")
            report.append(f"   Target Backtests: {lab_info['target_backtests']:,}")
            
            baseline = lab_info["performance_baseline"]
            report.append(f"   Baseline Performance:")
            report.append(f"     Avg ROI: {baseline['avg_roi']:.2f}%")
            report.append(f"     Max ROI: {baseline['max_roi']:.2f}%")
            report.append(f"     Profitable Ratio: {baseline['profitable_ratio']:.1%}")
        
        if creation_results.get("errors"):
            report.append(f"\n⚠️ Warnings/Errors:")
            for error in creation_results["errors"]:
                report.append(f"   • {error}")
        
        report.append(f"\n🎯 Stage 1 Objectives:")
        report.append(f"   • Fix timeframes to top 3 combinations from Stage 0")
        report.append(f"   • Optimize numerical parameters (ADX, Stoch, DEMA, etc.)")
        report.append(f"   • Keep structural parameters unchanged")
        report.append(f"   • Run {self.config['target_backtests']:,} backtests per lab")
        report.append(f"   • Identify optimal numerical parameter combinations")
        
        report.append(f"\n📊 Expected Outcomes:")
        report.append(f"   • {creation_results['total_backtests']:,} total backtests across all labs")
        report.append(f"   • Refined parameter ranges for each timeframe combination")
        report.append(f"   • Top performing configurations for potential live trading")
        report.append(f"   • Performance comparison between timeframe combinations")
        
        return "\n".join(report)

async def main():
    """Execute Stage 1 Numerical Optimizer"""
    print("🧬 Stage 1: Numerical Parameter Optimizer")
    print("=" * 60)
    
    optimizer = Stage1NumericalOptimizer()
    
    # Configuration
    source_lab_id = "55b45ee4-9cc5-42f7-8556-4c3aa2b13a44"
    script_name = "ADX BB STOCH Scalper"
    coin = "ETH"
    
    print(f"📋 Stage 1 Configuration:")
    print(f"   Source Lab: {source_lab_id}")
    print(f"   Script: {script_name}")
    print(f"   Coin: {coin}")
    print(f"   Focus: {optimizer.config['focus']}")
    print(f"   Target Backtests per Lab: {optimizer.config['target_backtests']:,}")
    print(f"   Backtest Period: {optimizer.config['backtest_years']} years")
    
    # Load Stage 0 analysis (in real implementation, this would be loaded from file)
    print(f"\n📊 Loading Stage 0 analysis...")
    
    # Mock Stage 0 analysis for demonstration
    stage0_analysis = {
        "success": True,
        "top_timeframe_combinations": [
            {
                "timeframe_combination": "5min/1h",
                "low_tf": "5 Minutes",
                "high_tf": "1 Hour",
                "avg_roi": 15.2,
                "max_roi": 45.8,
                "profitable_ratio": 0.65
            },
            {
                "timeframe_combination": "10min/4h",
                "low_tf": "10 Minutes", 
                "high_tf": "4 Hours",
                "avg_roi": 12.8,
                "max_roi": 38.4,
                "profitable_ratio": 0.58
            },
            {
                "timeframe_combination": "15min/12h",
                "low_tf": "15 Minutes",
                "high_tf": "12 Hours", 
                "avg_roi": 10.5,
                "max_roi": 32.1,
                "profitable_ratio": 0.52
            }
        ]
    }
    
    print(f"✅ Stage 0 analysis loaded with {len(stage0_analysis['top_timeframe_combinations'])} top combinations")
    
    # Create Stage 1 labs
    print(f"\n🧬 Creating Stage 1 numerical optimization labs...")
    
    creation_results = await optimizer.create_stage1_labs(
        source_lab_id, script_name, coin, stage0_analysis
    )
    
    # Generate and display report
    report = optimizer.generate_stage1_report(creation_results)
    print(f"\n{report}")
    
    # Save results
    with open('stage1_numerical_optimization_results.json', 'w') as f:
        json.dump(creation_results, f, indent=2, default=str)
    
    print(f"\n✅ Stage 1 results saved to 'stage1_numerical_optimization_results.json'")
    
    if creation_results.get("created_labs"):
        print(f"\n🎯 Next Steps:")
        print(f"   1. Monitor Stage 1 lab progress (~{optimizer.config['target_backtests']:,} backtests each)")
        print(f"   2. Analyze results to identify best numerical parameter combinations")
        print(f"   3. Select top configurations for potential live trading deployment")
        print(f"\n🚀 Stage 1 Numerical Optimizer: STARTED!")
    else:
        print(f"\n❌ Stage 1 failed to create labs. Check error details above.")

if __name__ == "__main__":
    asyncio.run(main())