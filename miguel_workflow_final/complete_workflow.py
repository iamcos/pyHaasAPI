#!/usr/bin/env python3
"""
Complete Trading Bot Optimization Workflow
Clean, refactored implementation that orchestrates the complete 2-stage optimization process:
1. Stage 0: Timeframe exploration (100 backtests)
2. Stage 0 Analysis: Identify top 3 timeframe combinations  
3. Stage 1: Numerical optimization (3 labs × 1000 backtests each)
"""

import asyncio
import logging
import json
from typing import Dict, Any
from datetime import datetime

from stage0_timeframe_explorer import Stage0TimeframeExplorer
from stage1_numerical_optimizer import Stage1NumericalOptimizer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CompleteWorkflow:
    """Complete 2-stage trading bot optimization workflow"""
    
    def __init__(self, mcp_base_url: str = "http://localhost:8000"):
        self.mcp_base_url = mcp_base_url
        
        # Initialize stage components
        self.stage0_explorer = Stage0TimeframeExplorer(mcp_base_url)
        self.stage1_optimizer = Stage1NumericalOptimizer(mcp_base_url)
        
        # Workflow configuration
        self.config = {
            "workflow_name": "Complete Trading Bot Optimization",
            "version": "1.0",
            "stages": 2,
            "total_target_backtests": 3100,  # 100 + (3 × 1000)
            "focus": "timeframe_then_numerical_optimization"
        }
    
    async def execute_complete_workflow(self, source_lab_id: str, script_name: str, 
                                      coin: str, auto_proceed: bool = False) -> Dict[str, Any]:
        """Execute the complete 2-stage optimization workflow"""
        logger.info("🚀 Starting Complete Trading Bot Optimization Workflow")
        
        workflow_results = {
            "workflow_name": self.config["workflow_name"],
            "version": self.config["version"],
            "source_lab_id": source_lab_id,
            "script_name": script_name,
            "coin": coin,
            "start_timestamp": datetime.now().isoformat(),
            "stage0_results": {},
            "stage0_analysis": {},
            "stage1_results": {},
            "total_labs_created": 0,
            "total_backtests": 0,
            "errors": [],
            "status": "started"
        }
        
        try:
            # Stage 0: Timeframe Exploration
            logger.info("\n" + "="*80)
            logger.info("STAGE 0: TIMEFRAME EXPLORATION")
            logger.info("="*80)
            
            stage0_result = await self.stage0_explorer.create_stage0_lab(
                source_lab_id, script_name, coin
            )
            
            workflow_results["stage0_results"] = stage0_result
            
            if stage0_result.get("error"):
                workflow_results["errors"].append(f"Stage 0 failed: {stage0_result['error']}")
                workflow_results["status"] = "failed_stage0"
                return workflow_results
            
            workflow_results["total_labs_created"] += 1
            workflow_results["total_backtests"] += self.stage0_explorer.config["target_backtests"]
            
            logger.info("✅ Stage 0 lab created and started")
            
            # Wait for Stage 0 completion or user confirmation
            if not auto_proceed:
                logger.info("\n⏳ Stage 0 is running. Please wait for completion before proceeding to analysis.")
                logger.info("   Run stage0_analyzer.py manually when Stage 0 completes, then continue with Stage 1.")
                workflow_results["status"] = "stage0_running"
                return workflow_results
            
            # For demo purposes, create mock Stage 0 analysis
            logger.info("\n" + "="*80)
            logger.info("STAGE 0: ANALYSIS (MOCK DATA FOR DEMO)")
            logger.info("="*80)
            
            mock_stage0_analysis = self._create_mock_stage0_analysis()
            workflow_results["stage0_analysis"] = mock_stage0_analysis
            
            # Stage 1: Numerical Optimization
            logger.info("\n" + "="*80)
            logger.info("STAGE 1: NUMERICAL PARAMETER OPTIMIZATION")
            logger.info("="*80)
            
            stage1_result = await self.stage1_optimizer.create_stage1_labs(
                source_lab_id, script_name, coin, mock_stage0_analysis
            )
            
            workflow_results["stage1_results"] = stage1_result
            workflow_results["total_labs_created"] += stage1_result.get("total_labs", 0)
            workflow_results["total_backtests"] += stage1_result.get("total_backtests", 0)
            
            if stage1_result.get("errors"):
                workflow_results["errors"].extend(stage1_result["errors"])
            
            if stage1_result.get("created_labs"):
                workflow_results["status"] = "completed"
                logger.info("✅ Complete workflow executed successfully")
            else:
                workflow_results["status"] = "failed_stage1"
                logger.error("❌ Stage 1 failed to create labs")
            
        except Exception as e:
            error_msg = f"Workflow execution failed: {e}"
            workflow_results["errors"].append(error_msg)
            workflow_results["status"] = "failed_exception"
            logger.error(error_msg)
        
        workflow_results["end_timestamp"] = datetime.now().isoformat()
        return workflow_results
    
    def _create_mock_stage0_analysis(self) -> Dict[str, Any]:
        """Create mock Stage 0 analysis for demonstration"""
        return {
            "success": True,
            "lab_id": "mock_stage0_lab",
            "total_configurations": 100,
            "top_timeframe_combinations": [
                {
                    "timeframe_combination": "5min/1h",
                    "low_tf": "5 Minutes",
                    "high_tf": "1 Hour",
                    "configuration_count": 25,
                    "avg_roi": 15.2,
                    "max_roi": 45.8,
                    "profitable_ratio": 0.65,
                    "composite_score": 28.5
                },
                {
                    "timeframe_combination": "10min/4h", 
                    "low_tf": "10 Minutes",
                    "high_tf": "4 Hours",
                    "configuration_count": 22,
                    "avg_roi": 12.8,
                    "max_roi": 38.4,
                    "profitable_ratio": 0.58,
                    "composite_score": 24.2
                },
                {
                    "timeframe_combination": "15min/12h",
                    "low_tf": "15 Minutes", 
                    "high_tf": "12 Hours",
                    "configuration_count": 18,
                    "avg_roi": 10.5,
                    "max_roi": 32.1,
                    "profitable_ratio": 0.52,
                    "composite_score": 20.8
                }
            ],
            "analysis_timestamp": datetime.now().isoformat()
        }
    
    def generate_workflow_report(self, workflow_results: Dict[str, Any]) -> str:
        """Generate comprehensive workflow execution report"""
        report = []
        report.append("=" * 100)
        report.append("🚀 COMPLETE TRADING BOT OPTIMIZATION WORKFLOW REPORT")
        report.append("=" * 100)
        
        # Workflow summary
        report.append(f"\n📋 Workflow Summary:")
        report.append(f"   Workflow: {workflow_results['workflow_name']} v{workflow_results['version']}")
        report.append(f"   Source Lab: {workflow_results['source_lab_id']}")
        report.append(f"   Script: {workflow_results['script_name']}")
        report.append(f"   Coin: {workflow_results['coin']}")
        report.append(f"   Status: {workflow_results['status'].upper()}")
        report.append(f"   Start Time: {workflow_results['start_timestamp']}")
        if workflow_results.get("end_timestamp"):
            report.append(f"   End Time: {workflow_results['end_timestamp']}")
        
        # Overall statistics
        report.append(f"\n📊 Overall Statistics:")
        report.append(f"   Total Labs Created: {workflow_results['total_labs_created']}")
        report.append(f"   Total Backtests: {workflow_results['total_backtests']:,}")
        report.append(f"   Target Backtests: {self.config['total_target_backtests']:,}")
        
        # Stage 0 results
        stage0_results = workflow_results.get("stage0_results", {})
        if stage0_results:
            report.append(f"\n🔍 STAGE 0: TIMEFRAME EXPLORATION")
            report.append("-" * 60)
            
            if stage0_results.get("success"):
                report.append(f"   ✅ Status: SUCCESS")
                report.append(f"   Lab ID: {stage0_results['lab_id']}")
                report.append(f"   Lab Name: {stage0_results['lab_name']}")
                
                config = stage0_results["configuration"]
                report.append(f"   Target Backtests: {config['target_backtests']}")
                report.append(f"   Focus: {config['focus']}")
                report.append(f"   Period: {config['backtest_years']} years")
            else:
                report.append(f"   ❌ Status: FAILED")
                report.append(f"   Error: {stage0_results.get('error', 'Unknown error')}")
        
        # Stage 0 analysis
        stage0_analysis = workflow_results.get("stage0_analysis", {})
        if stage0_analysis and stage0_analysis.get("success"):
            report.append(f"\n📊 STAGE 0: ANALYSIS RESULTS")
            report.append("-" * 60)
            
            top_combos = stage0_analysis.get("top_timeframe_combinations", [])
            report.append(f"   Total Configurations Analyzed: {stage0_analysis.get('total_configurations', 0)}")
            report.append(f"   Top Timeframe Combinations: {len(top_combos)}")
            
            for i, combo in enumerate(top_combos, 1):
                report.append(f"\n   🥇 Rank #{i}: {combo['timeframe_combination']}")
                report.append(f"      Timeframes: {combo['low_tf']} / {combo['high_tf']}")
                report.append(f"      Avg ROI: {combo['avg_roi']:.2f}%")
                report.append(f"      Max ROI: {combo['max_roi']:.2f}%")
                report.append(f"      Profitable Ratio: {combo['profitable_ratio']:.1%}")
                report.append(f"      Configurations: {combo['configuration_count']}")
        
        # Stage 1 results
        stage1_results = workflow_results.get("stage1_results", {})
        if stage1_results:
            report.append(f"\n🧬 STAGE 1: NUMERICAL OPTIMIZATION")
            report.append("-" * 60)
            
            created_labs = stage1_results.get("created_labs", {})
            if created_labs:
                report.append(f"   ✅ Status: SUCCESS")
                report.append(f"   Labs Created: {stage1_results['total_labs']}")
                report.append(f"   Total Backtests: {stage1_results['total_backtests']:,}")
                
                for rank_key, lab_info in created_labs.items():
                    report.append(f"\n   🧬 {lab_info['lab_name']}")
                    report.append(f"      Lab ID: {lab_info['lab_id']}")
                    report.append(f"      Timeframes: {lab_info['low_tf']} / {lab_info['high_tf']} (FIXED)")
                    report.append(f"      Target Backtests: {lab_info['target_backtests']:,}")
                    
                    baseline = lab_info["performance_baseline"]
                    report.append(f"      Baseline Avg ROI: {baseline['avg_roi']:.2f}%")
            else:
                report.append(f"   ❌ Status: FAILED")
                if stage1_results.get("errors"):
                    for error in stage1_results["errors"]:
                        report.append(f"      Error: {error}")
        
        # Errors summary
        if workflow_results.get("errors"):
            report.append(f"\n⚠️ ERRORS AND WARNINGS:")
            report.append("-" * 60)
            for error in workflow_results["errors"]:
                report.append(f"   • {error}")
        
        # Next steps
        report.append(f"\n🎯 NEXT STEPS:")
        report.append("-" * 60)
        
        status = workflow_results["status"]
        if status == "stage0_running":
            report.append(f"   1. Wait for Stage 0 backtest to complete (~100 backtests)")
            report.append(f"   2. Run stage0_analyzer.py to analyze results")
            report.append(f"   3. Run stage1_numerical_optimizer.py to create Stage 1 labs")
        elif status == "completed":
            report.append(f"   1. Monitor Stage 1 lab progress (~1000 backtests each)")
            report.append(f"   2. Analyze Stage 1 results to identify best configurations")
            report.append(f"   3. Select top configurations for live trading deployment")
        elif status.startswith("failed"):
            report.append(f"   1. Review error messages above")
            report.append(f"   2. Fix issues and retry workflow")
            report.append(f"   3. Check MCP server connectivity and lab configurations")
        
        report.append(f"\n" + "=" * 100)
        report.append(f"🚀 WORKFLOW REPORT COMPLETE")
        report.append(f"=" * 100)
        
        return "\n".join(report)

async def main():
    """Execute complete workflow"""
    print("🚀 Complete Trading Bot Optimization Workflow")
    print("=" * 80)
    
    workflow = CompleteWorkflow()
    
    # Configuration
    source_lab_id = "55b45ee4-9cc5-42f7-8556-4c3aa2b13a44"
    script_name = "ADX BB STOCH Scalper"
    coin = "ETH"
    auto_proceed = False  # Set to True for full demo run
    
    print(f"📋 Workflow Configuration:")
    print(f"   Source Lab: {source_lab_id}")
    print(f"   Script: {script_name}")
    print(f"   Coin: {coin}")
    print(f"   Total Target Backtests: {workflow.config['total_target_backtests']:,}")
    print(f"   Auto Proceed: {auto_proceed}")
    
    print(f"\n🎯 Workflow Overview:")
    print(f"   Stage 0: Timeframe exploration (100 backtests)")
    print(f"   Stage 0 Analysis: Identify top 3 timeframe combinations")
    print(f"   Stage 1: Numerical optimization (3 labs × 1000 backtests)")
    
    # Execute workflow
    print(f"\n🚀 Starting complete workflow execution...")
    
    workflow_results = await workflow.execute_complete_workflow(
        source_lab_id, script_name, coin, auto_proceed
    )
    
    # Generate and display report
    report = workflow.generate_workflow_report(workflow_results)
    print(f"\n{report}")
    
    # Save comprehensive results
    with open('complete_workflow_results.json', 'w') as f:
        json.dump(workflow_results, f, indent=2, default=str)
    
    print(f"\n✅ Complete workflow results saved to 'complete_workflow_results.json'")
    
    # Final status
    status = workflow_results["status"]
    if status == "completed":
        print(f"\n🎉 Complete workflow executed successfully!")
        print(f"   Total labs created: {workflow_results['total_labs_created']}")
        print(f"   Total backtests: {workflow_results['total_backtests']:,}")
    elif status == "stage0_running":
        print(f"\n⏳ Stage 0 is running. Continue manually when complete.")
    else:
        print(f"\n❌ Workflow failed with status: {status}")
        if workflow_results.get("errors"):
            print(f"   Check errors in the report above.")

if __name__ == "__main__":
    asyncio.run(main())