#!/usr/bin/env python3
"""
Example Comprehensive Backtesting System

Demonstrates how to use the comprehensive backtesting manager for multi-lab backtesting.
"""

import asyncio
import sys
from pathlib import Path

# Add pyHaasAPI_v2 to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from comprehensive_backtesting_manager import (
    ComprehensiveBacktestingManager,
    ProjectConfig,
    BacktestStep,
    LabConfig,
    CoinConfig
)


async def main():
    """Example usage of the comprehensive backtesting manager"""
    
    print("🎯 Comprehensive Backtesting Manager Example")
    print("=" * 60)
    
    # Define a comprehensive project configuration
    project_config = ProjectConfig(
        project_name="Multi-Lab BTC/TRX Optimization",
        description="Comprehensive backtesting project for BTC and TRX optimization",
        steps=[
            # Step 1: Initial parameter optimization
            BacktestStep(
                step_id="step1",
                name="Initial Parameter Optimization",
                lab_configs=[
                    LabConfig(
                        lab_id="305d8510-8bf8-4bcf-8004-8f547c3bc530",
                        lab_name="Source Lab - BTC Strategy",
                        script_id="",  # Will be filled from lab details
                        market_tag="BTC_USDT_PERPETUAL",
                        priority=1,
                        enabled=True
                    )
                ],
                coin_configs=[
                    CoinConfig(
                        symbol="BTC",
                        market_tag="BTC_USDT_PERPETUAL",
                        priority=1,
                        enabled=True
                    ),
                    CoinConfig(
                        symbol="TRX",
                        market_tag="TRX_USDT_PERPETUAL",
                        priority=2,
                        enabled=True
                    )
                ],
                analysis_criteria={
                    'min_win_rate': 0.3,      # 30% minimum win rate
                    'min_trades': 5,          # Minimum 5 trades
                    'max_drawdown': 50.0,     # Maximum 50% drawdown
                    'min_roe': 10.0,          # Minimum 10% ROE
                    'top_count': 10,          # Analyze top 10 backtests
                    'top_configs': 5          # Keep top 5 configurations
                },
                max_iterations=1000,          # 1000 iterations
                cutoff_days=730,              # 2 years of data
                enabled=True
            ),
            
            # Step 2: Advanced optimization (if step 1 succeeds)
            BacktestStep(
                step_id="step2",
                name="Advanced Optimization",
                lab_configs=[],  # Will be populated from step 1 results
                coin_configs=[
                    CoinConfig(symbol="BTC", market_tag="BTC_USDT_PERPETUAL", priority=1),
                    CoinConfig(symbol="TRX", market_tag="TRX_USDT_PERPETUAL", priority=2)
                ],
                analysis_criteria={
                    'min_win_rate': 0.4,      # Higher standards for step 2
                    'min_trades': 10,
                    'max_drawdown': 30.0,
                    'min_roe': 20.0,
                    'top_count': 5,
                    'top_configs': 3
                },
                max_iterations=1500,          # More iterations for step 2
                cutoff_days=365,             # 1 year of data
                enabled=True
            )
        ],
        global_settings={
            'trade_amount': 2000.0,          # $2000 USD
            'leverage': 20.0,                # 20x leverage
            'position_mode': 1,               # HEDGE mode
            'margin_mode': 0,                # CROSS margin
            'interval': 15,                  # 15 minutes
            'chart_style': 300,              # Default chart style
            'order_template': 500            # Default order template
        },
        output_directory="comprehensive_backtesting_results"
    )
    
    print(f"📋 Project: {project_config.project_name}")
    print(f"📝 Description: {project_config.description}")
    print(f"📊 Steps: {len(project_config.steps)}")
    print(f"💾 Output: {project_config.output_directory}")
    
    # Create and initialize the manager
    manager = ComprehensiveBacktestingManager(project_config)
    
    try:
        print("\n🚀 Initializing manager...")
        await manager.initialize()
        print("✅ Manager initialized successfully")
        
        print("\n🎯 Starting comprehensive backtesting project...")
        results = await manager.execute_project()
        
        # Print results summary
        print(f"\n{'='*60}")
        print("📊 PROJECT RESULTS SUMMARY")
        print(f"{'='*60}")
        
        if results.get('success', False):
            print("✅ Project completed successfully!")
            
            # Step results
            steps = results.get('steps', {})
            print(f"\n📋 Steps completed: {len(steps)}")
            
            for step_id, step_result in steps.items():
                success = step_result.get('success', False)
                status = "✅" if success else "❌"
                print(f"   {status} {step_id}: {step_result.get('name', 'Unknown')}")
                
                if success:
                    lab_results = step_result.get('lab_results', {})
                    print(f"      Labs processed: {len(lab_results)}")
                    
                    for lab_key, lab_result in lab_results.items():
                        if lab_result.get('success', False):
                            optimized_lab = lab_result.get('optimized_lab', {})
                            print(f"         💰 {optimized_lab.get('coin_symbol', 'Unknown')}: {optimized_lab.get('lab_name', 'Unknown')}")
                            print(f"            ROE: {optimized_lab.get('best_roe', 0):.2f}%")
                            print(f"            Win Rate: {optimized_lab.get('best_win_rate', 0):.2f}%")
            
            # Final analysis
            final_analysis = results.get('final_analysis', {})
            if final_analysis:
                print(f"\n🏆 Final Analysis:")
                print(f"   Total configurations analyzed: {final_analysis.get('total_configurations_analyzed', 0)}")
                
                top_configs = final_analysis.get('overall_top_configurations', [])
                if top_configs:
                    print(f"   Top configurations:")
                    for i, config in enumerate(top_configs[:5], 1):
                        print(f"     {i}. {config.get('lab_name', 'Unknown')} - {config.get('coin_symbol', 'Unknown')}")
                        print(f"        ROE: {config.get('best_roe', 0):.2f}%")
                        print(f"        Win Rate: {config.get('best_win_rate', 0):.2f}%")
                
                recommendations = final_analysis.get('final_recommendations', [])
                if recommendations:
                    print(f"   Recommendations:")
                    for rec in recommendations:
                        print(f"     • {rec}")
            
            print(f"\n💾 Results saved to: {project_config.output_directory}")
            return 0
            
        else:
            print("❌ Project failed")
            error = results.get('error', 'Unknown error')
            print(f"   Error: {error}")
            return 1
            
    except Exception as e:
        print(f"❌ Error during execution: {e}")
        return 1
    
    finally:
        # Cleanup
        try:
            await manager.cleanup()
            print("🔧 Cleanup completed")
        except Exception as e:
            print(f"⚠️ Cleanup error: {e}")


if __name__ == "__main__":
    print("🎯 Comprehensive Backtesting Manager Example")
    print("This example demonstrates the comprehensive backtesting system")
    print("for multi-lab backtesting with analysis between steps.")
    print()
    
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
