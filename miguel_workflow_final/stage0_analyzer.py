#!/usr/bin/env python3
"""
Miguel Workflow - Stage 0 Analyzer
Analyzes completed Stage 0 lab results to identify top 3 timeframe/MA combinations
and generates detailed analytical report.
"""

import asyncio
import logging
import time
import requests
from typing import Dict, List, Any, Optional, Tuple
import json
from datetime import datetime
from collections import defaultdict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Stage0Analyzer:
    """Analyzes Stage 0 lab results and identifies top configurations"""
    
    def __init__(self, mcp_base_url: str = "http://localhost:8000"):
        self.mcp_base_url = mcp_base_url
        self.session = requests.Session()
        
        # Analysis configuration
        self.analysis_config = {
            "top_configurations": 3,
            "min_completed_tests": 50,
            "performance_metrics": ["roi", "profit", "trades", "win_rate", "drawdown"],
            "diversity_weight": 0.3,
            "performance_weight": 0.7
        }
    
    async def analyze_stage0_lab(self, lab_id: str) -> Dict[str, Any]:
        """Analyze completed Stage 0 lab and identify top configurations"""
        logger.info(f"🔍 Analyzing Stage 0 lab: {lab_id}")
        
        try:
            # Get lab results
            results = await self._get_lab_results(lab_id)
            
            if results.get("error"):
                return {"error": f"Failed to get lab results: {results['error']}"}
            
            configurations = results["configurations"]
            logger.info(f"Found {len(configurations)} configurations to analyze")
            
            if len(configurations) < self.analysis_config["min_completed_tests"]:
                return {"error": f"Insufficient completed tests: {len(configurations)} < {self.analysis_config['min_completed_tests']}"}
            
            # Extract and classify parameters
            parameter_analysis = self._analyze_parameters(configurations)
            
            # Identify top timeframe/MA combinations
            top_combinations = self._identify_top_combinations(configurations)
            
            # Generate performance analysis
            performance_analysis = self._analyze_performance(configurations)
            
            # Generate analytical report
            analytical_report = self._generate_analytical_report(
                lab_id, configurations, parameter_analysis, top_combinations, performance_analysis
            )
            
            return {
                "success": True,
                "lab_id": lab_id,
                "total_configurations": len(configurations),
                "parameter_analysis": parameter_analysis,
                "top_combinations": top_combinations,
                "performance_analysis": performance_analysis,
                "analytical_report": analytical_report,
                "ready_for_stage1": True
            }
            
        except Exception as e:
            logger.error(f"Error analyzing Stage 0 lab: {e}")
            return {"error": str(e)}
    
    async def _get_lab_results(self, lab_id: str) -> Dict[str, Any]:
        """Get lab backtest results"""
        try:
            payload = {
                "lab_id": lab_id,
                "next_page_id": -1,
                "page_length": 200
            }
            
            response = self.session.post(f"{self.mcp_base_url}/get_backtest_results", json=payload)
            if response.status_code != 200:
                return {"error": f"HTTP {response.status_code}"}
            
            results_data = response.json()
            if not results_data.get("Success"):
                return {"error": results_data.get("Error", "Unknown error")}
            
            raw_data = results_data.get("Data", {})
            if not raw_data or not raw_data.get("I"):
                return {"error": "No configuration data found"}
            
            # Parse configurations
            configurations = []
            for config in raw_data["I"]:
                if config.get("ST") == 3:  # Status 3 = completed
                    configurations.append({
                        "backtest_id": config.get("BID", ""),
                        "parameters": config.get("P", {}),
                        "performance": config.get("S", {}),
                        "settings": config.get("SE", {}),
                        "generation": config.get("NG", 0),
                        "population": config.get("NP", 0)
                    })
            
            return {"configurations": configurations}
            
        except Exception as e:
            return {"error": str(e)}
    
    def _analyze_parameters(self, configurations: List[Dict]) -> Dict[str, Any]:
        """Analyze parameter distribution and classification"""
        logger.info("📊 Analyzing parameter distribution...")
        
        # Get sample configuration for parameter extraction
        sample_config = configurations[0] if configurations else {}
        all_parameters = sample_config.get("parameters", {})
        
        # Classify parameters
        timeframe_params = {}
        ma_type_params = {}
        numerical_params = {}
        
        for param_key, param_value in all_parameters.items():
            if "tf" in param_key.lower() or "timeframe" in param_key.lower():
                timeframe_params[param_key] = param_value
            elif "ma" in param_key.lower() or "type" in param_key.lower():
                ma_type_params[param_key] = param_value
            else:
                try:
                    float(param_value)
                    numerical_params[param_key] = param_value
                except (ValueError, TypeError):
                    pass
        
        # Analyze timeframe distribution
        timeframe_distribution = self._analyze_timeframe_distribution(configurations)
        
        return {
            "total_parameters": len(all_parameters),
            "timeframe_parameters": timeframe_params,
            "ma_type_parameters": ma_type_params,
            "numerical_parameters": numerical_params,
            "timeframe_distribution": timeframe_distribution,
            "parameter_classification": {
                "timeframe_count": len(timeframe_params),
                "ma_type_count": len(ma_type_params),
                "numerical_count": len(numerical_params)
            }
        }
    
    def _analyze_timeframe_distribution(self, configurations: List[Dict]) -> Dict[str, Any]:
        """Analyze distribution of timeframe combinations"""
        timeframe_combinations = defaultdict(list)
        
        for config in configurations:
            params = config.get("parameters", {})
            
            # Extract timeframes (adjust keys based on actual parameter structure)
            low_tf = params.get("20-20-18-30.Low TF", "Unknown")
            high_tf = params.get("21-21-18-30.High TF", "Unknown")
            
            tf_combo = f"{low_tf}/{high_tf}"
            timeframe_combinations[tf_combo].append(config)
        
        # Calculate statistics for each combination
        combination_stats = {}
        for combo, configs in timeframe_combinations.items():
            roi_values = []
            for config in configs:
                perf = config.get("performance", {})
                roi = perf.get("ReturnOnInvestment", 0.0)
                roi_values.append(roi)
            
            combination_stats[combo] = {
                "count": len(configs),
                "avg_roi": sum(roi_values) / len(roi_values) if roi_values else 0.0,
                "max_roi": max(roi_values) if roi_values else 0.0,
                "min_roi": min(roi_values) if roi_values else 0.0,
                "configurations": configs
            }
        
        return {
            "unique_combinations": len(timeframe_combinations),
            "combination_stats": combination_stats,
            "most_common": max(timeframe_combinations.items(), key=lambda x: len(x[1]))[0] if timeframe_combinations else None
        }
    
    def _identify_top_combinations(self, configurations: List[Dict]) -> List[Dict[str, Any]]:
        """Identify top 3 timeframe/MA combinations using performance + diversity"""
        logger.info("🏆 Identifying top 3 timeframe/MA combinations...")
        
        # Group configurations by timeframe combination
        timeframe_groups = defaultdict(list)
        
        for config in configurations:
            params = config.get("parameters", {})
            low_tf = params.get("20-20-18-30.Low TF", "Unknown")
            high_tf = params.get("21-21-18-30.High TF", "Unknown")
            
            tf_combo = f"{low_tf}/{high_tf}"
            timeframe_groups[tf_combo].append(config)
        
        # Score each combination
        combination_scores = []
        
        for tf_combo, configs in timeframe_groups.items():
            if not configs:
                continue
            
            # Calculate performance score
            roi_values = [config.get("performance", {}).get("ReturnOnInvestment", 0.0) for config in configs]
            avg_roi = sum(roi_values) / len(roi_values) if roi_values else 0.0
            max_roi = max(roi_values) if roi_values else 0.0
            
            # Calculate diversity score (based on timeframe characteristics)
            diversity_score = self._calculate_diversity_score(tf_combo)
            
            # Combined score
            performance_score = (avg_roi * 0.7) + (max_roi * 0.3)
            combined_score = (performance_score * self.analysis_config["performance_weight"]) + \
                           (diversity_score * self.analysis_config["diversity_weight"])
            
            combination_scores.append({
                "timeframe_combination": tf_combo,
                "low_tf": tf_combo.split('/')[0] if '/' in tf_combo else "Unknown",
                "high_tf": tf_combo.split('/')[1] if '/' in tf_combo else "Unknown",
                "configurations": configs,
                "performance_metrics": {
                    "avg_roi": avg_roi,
                    "max_roi": max_roi,
                    "min_roi": min(roi_values) if roi_values else 0.0,
                    "config_count": len(configs)
                },
                "diversity_score": diversity_score,
                "combined_score": combined_score,
                "best_config": max(configs, key=lambda x: x.get("performance", {}).get("ReturnOnInvestment", 0.0)) if configs else None
            })
        
        # Sort by combined score and return top 3
        combination_scores.sort(key=lambda x: x["combined_score"], reverse=True)
        top_3 = combination_scores[:self.analysis_config["top_configurations"]]
        
        logger.info(f"Selected top 3 combinations:")
        for i, combo in enumerate(top_3, 1):
            logger.info(f"  {i}. {combo['timeframe_combination']} (score: {combo['combined_score']:.2f})")
        
        return top_3
    
    def _calculate_diversity_score(self, tf_combo: str) -> float:
        """Calculate diversity score for timeframe combination"""
        if '/' not in tf_combo:
            return 0.0
        
        low_tf, high_tf = tf_combo.split('/')
        
        # Timeframe scoring (higher = more diverse/interesting)
        tf_scores = {
            "1 Hour": 4.0, "2 Hours": 5.0, "4 Hours": 6.0, "6 Hours": 6.5,
            "8 Hours": 7.0, "12 Hours": 7.5, "1 Day": 8.0, "2 Days": 8.5,
            "3 Days": 9.0, "1 Week": 9.5, "2 Weeks": 10.0
        }
        
        low_score = tf_scores.get(low_tf, 1.0)
        high_score = tf_scores.get(high_tf, 1.0)
        
        # Bonus for good ratios between timeframes
        ratio_bonus = 0.0
        if low_score > 0 and high_score > 0:
            ratio = high_score / low_score
            if 2 <= ratio <= 8:  # Good separation between timeframes
                ratio_bonus = 2.0
        
        return low_score + high_score + ratio_bonus
    
    def _analyze_performance(self, configurations: List[Dict]) -> Dict[str, Any]:
        """Analyze overall performance metrics"""
        roi_values = []
        profit_values = []
        
        for config in configurations:
            perf = config.get("performance", {})
            roi_values.append(perf.get("ReturnOnInvestment", 0.0))
            profit_values.append(perf.get("RealizedProfits", 0.0))
        
        return {
            "total_configurations": len(configurations),
            "roi_statistics": {
                "mean": sum(roi_values) / len(roi_values) if roi_values else 0.0,
                "max": max(roi_values) if roi_values else 0.0,
                "min": min(roi_values) if roi_values else 0.0,
                "profitable_count": sum(1 for roi in roi_values if roi > 0),
                "profitable_percentage": (sum(1 for roi in roi_values if roi > 0) / len(roi_values) * 100) if roi_values else 0.0
            },
            "profit_statistics": {
                "total_profit": sum(profit_values),
                "avg_profit": sum(profit_values) / len(profit_values) if profit_values else 0.0,
                "max_profit": max(profit_values) if profit_values else 0.0
            }
        }
    
    def _generate_analytical_report(self, lab_id: str, configurations: List[Dict], 
                                  parameter_analysis: Dict[str, Any], top_combinations: List[Dict[str, Any]], 
                                  performance_analysis: Dict[str, Any]) -> str:
        """Generate comprehensive analytical report"""
        report = []
        report.append("=" * 80)
        report.append("📊 STAGE 0 ANALYSIS REPORT - TIMEFRAME & MA TYPE EXPLORATION")
        report.append("=" * 80)
        
        report.append(f"\n🔍 Lab Analysis Summary:")
        report.append(f"   Lab ID: {lab_id}")
        report.append(f"   Total Configurations: {len(configurations)}")
        report.append(f"   Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Parameter analysis
        param_analysis = parameter_analysis
        report.append(f"\n📋 Parameter Classification:")
        report.append(f"   Total Parameters: {param_analysis['total_parameters']}")
        report.append(f"   Timeframe Parameters: {param_analysis['parameter_classification']['timeframe_count']}")
        report.append(f"   MA Type Parameters: {param_analysis['parameter_classification']['ma_type_count']}")
        report.append(f"   Numerical Parameters: {param_analysis['parameter_classification']['numerical_count']}")
        
        # Performance overview
        perf_stats = performance_analysis["roi_statistics"]
        report.append(f"\n📈 Performance Overview:")
        report.append(f"   Average ROI: {perf_stats['mean']:.2f}%")
        report.append(f"   Best ROI: {perf_stats['max']:.2f}%")
        report.append(f"   Worst ROI: {perf_stats['min']:.2f}%")
        report.append(f"   Profitable Configurations: {perf_stats['profitable_count']} ({perf_stats['profitable_percentage']:.1f}%)")
        
        # Top combinations
        report.append(f"\n🏆 TOP 3 TIMEFRAME/MA COMBINATIONS FOR STAGE 1:")
        report.append("-" * 60)
        
        for i, combo in enumerate(top_combinations, 1):
            report.append(f"\n🥇 RANK #{i} - {combo['timeframe_combination']}")
            report.append(f"   Low Timeframe: {combo['low_tf']}")
            report.append(f"   High Timeframe: {combo['high_tf']}")
            report.append(f"   Configurations Tested: {combo['performance_metrics']['config_count']}")
            report.append(f"   Average ROI: {combo['performance_metrics']['avg_roi']:.2f}%")
            report.append(f"   Best ROI: {combo['performance_metrics']['max_roi']:.2f}%")
            report.append(f"   Diversity Score: {combo['diversity_score']:.2f}")
            report.append(f"   Combined Score: {combo['combined_score']:.2f}")
        
        # Stage 1 recommendations
        report.append(f"\n" + "=" * 80)
        report.append(f"🎯 STAGE 1 RECOMMENDATIONS")
        report.append(f"=" * 80)
        
        report.append(f"\n📋 Next Steps:")
        report.append(f"   1. Create 3 Stage 1 labs using the top timeframe combinations")
        report.append(f"   2. Fix timeframes from Stage 0 results")
        report.append(f"   3. Optimize numerical parameters with genetic algorithm")
        report.append(f"   4. Run 1000 backtests per lab (3000 total)")
        report.append(f"   5. Use 3-year backtest period for statistical significance")
        
        report.append(f"\n🔧 Parameters to Optimize in Stage 1:")
        numerical_params = parameter_analysis["numerical_parameters"]
        for param, value in list(numerical_params.items())[:10]:  # Show top 10
            report.append(f"   • {param}: {value}")
        
        report.append(f"\n🧬 Genetic Algorithm Recommendations:")
        report.append(f"   • Generations: 20")
        report.append(f"   • Population: 50")
        report.append(f"   • Total backtests per lab: 1000")
        report.append(f"   • Focus: Numerical parameter optimization")
        report.append(f"   • Fixed: Timeframes from top 3 Stage 0 results")
        
        return "\n".join(report)

async def main():
    """Analyze Stage 0 lab results"""
    print("📊 Miguel Workflow - Stage 0 Analyzer")
    print("=" * 60)
    
    analyzer = Stage0Analyzer()
    
    print("📋 Analysis Configuration:")
    print(f"   Top Configurations: {analyzer.analysis_config['top_configurations']}")
    print(f"   Min Completed Tests: {analyzer.analysis_config['min_completed_tests']}")
    print(f"   Performance Weight: {analyzer.analysis_config['performance_weight']}")
    print(f"   Diversity Weight: {analyzer.analysis_config['diversity_weight']}")
    
    # Example usage
    print(f"\n📝 Example Usage:")
    print(f"   result = await analyzer.analyze_stage0_lab('your_lab_id')")
    print(f"   print(result['analytical_report'])")
    
    print(f"\n🎯 Key Features:")
    print(f"   ✅ Analyzes completed Stage 0 lab results")
    print(f"   ✅ Identifies top 3 timeframe/MA combinations")
    print(f"   ✅ Combines performance + diversity scoring")
    print(f"   ✅ Generates comprehensive analytical report")
    print(f"   ✅ Provides Stage 1 optimization recommendations")
    print(f"   ✅ Classifies parameters for Stage 1 optimization")
    
    print(f"\n🚀 Stage 0 Analyzer: READY!")

if __name__ == "__main__":
    asyncio.run(main())