#!/usr/bin/env python3
"""
Lab Analysis System
Comprehensive analysis of lab backtest results to identify top performing
configurations with distinct trading styles and parameter optimization ranges.
"""

import json
import logging
import math
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class BacktestConfiguration:
    """Individual backtest configuration with performance metrics"""
    result_id: int
    lab_id: str
    backtest_id: str
    parameters: Dict[str, Any]
    performance: Dict[str, float]
    settings: Dict[str, Any]
    status: int
    generations: int
    population: int
    
    def get_parameter_signature(self) -> str:
        """Get a signature string for parameter comparison"""
        key_params = []
        for key, value in sorted(self.parameters.items()):
            if isinstance(value, (int, float, str)):
                key_params.append(f"{key}:{value}")
        return "|".join(key_params)

@dataclass
class TradingStyle:
    """Identified trading style with characteristics"""
    style_id: int
    name: str
    description: str
    key_parameters: Dict[str, Any]
    performance_profile: Dict[str, float]
    configurations: List[BacktestConfiguration]
    avg_performance: float
    
    def get_parameter_ranges(self) -> Dict[str, Dict[str, Any]]:
        """Get parameter ranges for this trading style"""
        ranges = {}
        
        # Collect all parameter values for this style
        param_values = defaultdict(list)
        for config in self.configurations:
            for param, value in config.parameters.items():
                if isinstance(value, (int, float)):
                    param_values[param].append(value)
                elif isinstance(value, str) and value.replace('.', '').replace('-', '').isdigit():
                    param_values[param].append(float(value))
        
        # Calculate ranges
        for param, values in param_values.items():
            if len(values) > 1:
                values = np.array(values)
                ranges[param] = {
                    'min': float(np.min(values)),
                    'max': float(np.max(values)),
                    'mean': float(np.mean(values)),
                    'std': float(np.std(values)),
                    'current_range': float(np.max(values) - np.min(values)),
                    'suggested_min': float(np.mean(values) - 2 * np.std(values)),
                    'suggested_max': float(np.mean(values) + 2 * np.std(values)),
                    'values': values.tolist()
                }
        
        return ranges

class LabAnalysisSystem:
    """Comprehensive lab analysis system"""
    
    def __init__(self):
        self.configurations: List[BacktestConfiguration] = []
        self.trading_styles: List[TradingStyle] = []
        self.parameter_importance: Dict[str, float] = {}
        
    def load_lab_results(self, results_file: str) -> bool:
        """Load lab results from JSON file"""
        try:
            with open(results_file, 'r') as f:
                data = json.load(f)
            
            if not data.get('Success'):
                logger.error(f"Lab results indicate failure: {data.get('Error', 'Unknown error')}")
                return False
            
            results = data['Data']['I']
            logger.info(f"Loading {len(results)} backtest results")
            
            # Parse each result
            for result in results:
                try:
                    config = BacktestConfiguration(
                        result_id=result.get('RID', 0),
                        lab_id=result.get('LID', ''),
                        backtest_id=result.get('BID', ''),
                        parameters=result.get('P', {}),
                        performance=result.get('S', {}),
                        settings=result.get('SE', {}),
                        status=result.get('ST', 0),
                        generations=result.get('NG', 0),
                        population=result.get('NP', 0)
                    )
                    
                    # Only include completed backtests
                    if config.status == 3:  # Status 3 = completed
                        self.configurations.append(config)
                        
                except Exception as e:
                    logger.warning(f"Failed to parse result {result.get('RID', 'unknown')}: {e}")
            
            logger.info(f"Successfully loaded {len(self.configurations)} completed configurations")
            return len(self.configurations) > 0
            
        except Exception as e:
            logger.error(f"Failed to load lab results: {e}")
            return False
    
    def analyze_performance_metrics(self) -> Dict[str, Any]:
        """Analyze performance metrics across all configurations"""
        if not self.configurations:
            return {'error': 'No configurations loaded'}
        
        # Extract performance metrics
        roi_values = []
        profit_values = []
        fee_values = []
        
        for config in self.configurations:
            perf = config.performance
            roi = perf.get('ReturnOnInvestment', 0.0)
            profit = perf.get('RealizedProfits', 0.0)
            fees = perf.get('FeeCosts', 0.0)
            
            roi_values.append(roi)
            profit_values.append(profit)
            fee_values.append(fees)
        
        # Calculate statistics
        roi_array = np.array(roi_values)
        profit_array = np.array(profit_values)
        
        analysis = {
            'total_configurations': len(self.configurations),
            'roi_statistics': {
                'mean': float(np.mean(roi_array)),
                'std': float(np.std(roi_array)),
                'min': float(np.min(roi_array)),
                'max': float(np.max(roi_array)),
                'median': float(np.median(roi_array)),
                'profitable_count': int(np.sum(roi_array > 0)),
                'profitable_percentage': float(np.sum(roi_array > 0) / len(roi_array) * 100)
            },
            'profit_statistics': {
                'mean': float(np.mean(profit_array)),
                'std': float(np.std(profit_array)),
                'min': float(np.min(profit_array)),
                'max': float(np.max(profit_array)),
                'total_profit': float(np.sum(profit_array))
            },
            'top_performers': self._get_top_performers(5)
        }
        
        return analysis
    
    def _get_top_performers(self, count: int) -> List[Dict[str, Any]]:
        """Get top performing configurations"""
        # Sort by ROI
        sorted_configs = sorted(
            self.configurations,
            key=lambda x: x.performance.get('ReturnOnInvestment', 0.0),
            reverse=True
        )
        
        top_performers = []
        for config in sorted_configs[:count]:
            perf = config.performance
            top_performers.append({
                'result_id': config.result_id,
                'roi': perf.get('ReturnOnInvestment', 0.0),
                'profit': perf.get('RealizedProfits', 0.0),
                'parameters': config.parameters,
                'parameter_signature': config.get_parameter_signature()
            })
        
        return top_performers
    
    def identify_trading_styles(self, n_styles: int = 3) -> List[TradingStyle]:
        """Identify distinct trading styles using simple clustering"""
        if len(self.configurations) < n_styles:
            logger.warning(f"Not enough configurations ({len(self.configurations)}) for {n_styles} styles")
            n_styles = len(self.configurations)
        
        logger.info(f"Identifying {n_styles} distinct trading styles")
        
        # Simple clustering based on key parameters
        # Group by timeframe combinations first
        timeframe_groups = defaultdict(list)
        
        for config in self.configurations:
            low_tf = config.parameters.get('20-20-18-30.Low TF', 'Unknown')
            high_tf = config.parameters.get('21-21-18-30.High TF', 'Unknown')
            tf_key = f"{low_tf}|{high_tf}"
            timeframe_groups[tf_key].append(config)
        
        # Get top timeframe combinations by count
        sorted_tf_groups = sorted(timeframe_groups.items(), key=lambda x: len(x[1]), reverse=True)
        
        # Create trading styles from top groups
        trading_styles = []
        for style_id, (tf_key, configs) in enumerate(sorted_tf_groups[:n_styles]):
            if not configs:
                continue
            
            # Calculate average performance
            roi_values = [config.performance.get('ReturnOnInvestment', 0.0) for config in configs]
            avg_roi = sum(roi_values) / len(roi_values) if roi_values else 0.0
            
            # Get representative parameters (averages)
            key_parameters = self._calculate_average_parameters(configs)
            
            # Create style description
            style_name, description = self._generate_style_description(style_id, configs, key_parameters)
            
            # Calculate performance profile
            performance_profile = self._calculate_performance_profile(configs)
            
            trading_style = TradingStyle(
                style_id=style_id,
                name=style_name,
                description=description,
                key_parameters=key_parameters,
                performance_profile=performance_profile,
                configurations=configs,
                avg_performance=avg_roi
            )
            
            trading_styles.append(trading_style)
        
        # Sort by average performance
        trading_styles.sort(key=lambda x: x.avg_performance, reverse=True)
        
        self.trading_styles = trading_styles
        logger.info(f"Identified {len(trading_styles)} trading styles")
        
        return trading_styles
    
    def _calculate_average_parameters(self, configs: List[BacktestConfiguration]) -> Dict[str, Any]:
        """Calculate average parameters for a group of configurations"""
        param_sums = defaultdict(list)
        
        for config in configs:
            for param, value in config.parameters.items():
                if isinstance(value, (int, float)):
                    param_sums[param].append(float(value))
                elif isinstance(value, str) and value.replace('.', '').replace('-', '').isdigit():
                    param_sums[param].append(float(value))
        
        # Calculate averages
        avg_params = {}
        for param, values in param_sums.items():
            if values:
                avg_params[param] = sum(values) / len(values)
        
        return avg_params
    
    def _generate_style_description(self, style_id: int, configs: List[BacktestConfiguration], 
                                  key_params: Dict[str, Any]) -> Tuple[str, str]:
        """Generate name and description for a trading style"""
        
        # Analyze key parameter characteristics
        style_characteristics = []
        
        # Check timeframe characteristics
        low_tf_values = [config.parameters.get('20-20-18-30.Low TF', '') for config in configs]
        high_tf_values = [config.parameters.get('21-21-18-30.High TF', '') for config in configs]
        
        # Most common timeframes
        low_tf_common = max(set(low_tf_values), key=low_tf_values.count) if low_tf_values else ''
        high_tf_common = max(set(high_tf_values), key=high_tf_values.count) if high_tf_values else ''
        
        if low_tf_common:
            style_characteristics.append(f"Low TF: {low_tf_common}")
        if high_tf_common:
            style_characteristics.append(f"High TF: {high_tf_common}")
        
        # Check ADX trigger levels
        adx_values = [float(config.parameters.get('83-83-19-24.ADX trigger', 25)) for config in configs]
        avg_adx = np.mean(adx_values)
        
        if avg_adx < 20:
            style_characteristics.append("Low ADX (Trending)")
        elif avg_adx > 30:
            style_characteristics.append("High ADX (Strong Trends)")
        else:
            style_characteristics.append("Medium ADX (Balanced)")
        
        # Check Stochastic levels
        stoch_low = [float(config.parameters.get('81-81-12-17.Stoch low line', 20)) for config in configs]
        stoch_high = [float(config.parameters.get('82-82-12-17.Stoch high line', 80)) for config in configs]
        
        avg_stoch_low = np.mean(stoch_low)
        avg_stoch_high = np.mean(stoch_high)
        
        if avg_stoch_low < 18:
            style_characteristics.append("Aggressive Oversold")
        if avg_stoch_high > 82:
            style_characteristics.append("Aggressive Overbought")
        
        # Generate name and description
        if style_id == 0:
            name = "Conservative Scalper"
        elif style_id == 1:
            name = "Aggressive Momentum"
        elif style_id == 2:
            name = "Balanced Swing"
        else:
            name = f"Style {style_id + 1}"
        
        description = f"Trading style characterized by: {', '.join(style_characteristics[:3])}"
        
        return name, description
    
    def _calculate_performance_profile(self, configs: List[BacktestConfiguration]) -> Dict[str, float]:
        """Calculate performance profile for a group of configurations"""
        roi_values = [config.performance.get('ReturnOnInvestment', 0.0) for config in configs]
        profit_values = [config.performance.get('RealizedProfits', 0.0) for config in configs]
        
        return {
            'avg_roi': float(np.mean(roi_values)),
            'roi_std': float(np.std(roi_values)),
            'max_roi': float(np.max(roi_values)),
            'min_roi': float(np.min(roi_values)),
            'avg_profit': float(np.mean(profit_values)),
            'total_profit': float(np.sum(profit_values)),
            'profitable_ratio': float(np.sum(np.array(roi_values) > 0) / len(roi_values)),
            'configuration_count': len(configs)
        }
    
    def generate_optimization_ranges(self) -> Dict[str, Dict[str, Any]]:
        """Generate parameter optimization ranges for each trading style"""
        if not self.trading_styles:
            logger.error("No trading styles identified. Run identify_trading_styles() first.")
            return {}
        
        optimization_ranges = {}
        
        for style in self.trading_styles:
            style_ranges = style.get_parameter_ranges()
            
            # Filter to most important parameters
            important_params = self._identify_important_parameters(style)
            
            filtered_ranges = {}
            for param in important_params:
                if param in style_ranges:
                    range_info = style_ranges[param]
                    
                    # Adjust ranges for optimization
                    current_range = range_info['current_range']
                    if current_range > 0:
                        # Expand range by 20% for exploration
                        expansion = current_range * 0.2
                        optimized_min = max(0, range_info['min'] - expansion)
                        optimized_max = range_info['max'] + expansion
                        
                        filtered_ranges[param] = {
                            'current_min': range_info['min'],
                            'current_max': range_info['max'],
                            'current_mean': range_info['mean'],
                            'optimization_min': optimized_min,
                            'optimization_max': optimized_max,
                            'step_size': current_range / 10,  # 10 steps across range
                            'priority': 'high' if param in important_params[:3] else 'medium'
                        }
            
            optimization_ranges[style.name] = {
                'style_info': {
                    'name': style.name,
                    'description': style.description,
                    'avg_performance': style.avg_performance,
                    'configuration_count': len(style.configurations)
                },
                'parameter_ranges': filtered_ranges
            }
        
        return optimization_ranges
    
    def _identify_important_parameters(self, style: TradingStyle) -> List[str]:
        """Identify most important parameters for a trading style"""
        # Parameters that typically have the most impact on trading performance
        high_priority_params = [
            '83-83-19-24.ADX trigger',
            '81-81-12-17.Stoch low line',
            '82-82-12-17.Stoch high line',
            '84-84-16-21.Fast DEMA period',
            '85-85-16-21.Slow DEMA period',
            '88-88-12-17.TP 1st pt, %',
            '79-79-15-20.SL colldown reset'
        ]
        
        # Get parameters that exist in this style
        available_params = set()
        for config in style.configurations:
            available_params.update(config.parameters.keys())
        
        # Return high priority params that exist, plus others
        important_params = []
        
        # Add high priority params first
        for param in high_priority_params:
            if param in available_params:
                important_params.append(param)
        
        # Add other numeric parameters
        for param in sorted(available_params):
            if param not in important_params:
                # Check if parameter has numeric variation
                values = [config.parameters.get(param) for config in style.configurations]
                numeric_values = []
                for val in values:
                    if isinstance(val, (int, float)):
                        numeric_values.append(val)
                    elif isinstance(val, str) and val.replace('.', '').replace('-', '').isdigit():
                        numeric_values.append(float(val))
                
                if len(set(numeric_values)) > 1:  # Has variation
                    important_params.append(param)
        
        return important_params[:10]  # Top 10 most important
    
    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate comprehensive analysis report"""
        if not self.configurations:
            return {'error': 'No configurations loaded'}
        
        # Performance analysis
        performance_analysis = self.analyze_performance_metrics()
        
        # Trading styles
        if not self.trading_styles:
            self.identify_trading_styles(3)
        
        # Optimization ranges
        optimization_ranges = self.generate_optimization_ranges()
        
        # Summary statistics
        summary = {
            'lab_analysis_summary': {
                'total_configurations': len(self.configurations),
                'trading_styles_identified': len(self.trading_styles),
                'avg_roi_all_configs': performance_analysis['roi_statistics']['mean'],
                'profitable_percentage': performance_analysis['roi_statistics']['profitable_percentage'],
                'best_roi': performance_analysis['roi_statistics']['max']
            },
            'performance_analysis': performance_analysis,
            'trading_styles': [
                {
                    'name': style.name,
                    'description': style.description,
                    'avg_performance': style.avg_performance,
                    'configuration_count': len(style.configurations),
                    'performance_profile': style.performance_profile
                }
                for style in self.trading_styles
            ],
            'optimization_ranges': optimization_ranges,
            'recommendations': self._generate_recommendations()
        }
        
        return summary
    
    def _generate_recommendations(self) -> List[str]:
        """Generate optimization recommendations"""
        recommendations = []
        
        if not self.trading_styles:
            recommendations.append("Run trading style identification first")
            return recommendations
        
        # Analyze overall performance
        performance_analysis = self.analyze_performance_metrics()
        profitable_pct = performance_analysis['roi_statistics']['profitable_percentage']
        
        if profitable_pct < 10:
            recommendations.append("Very low profitability - consider different strategy or major parameter adjustments")
        elif profitable_pct < 30:
            recommendations.append("Low profitability - focus on top performing style parameters")
        else:
            recommendations.append("Reasonable profitability - optimize around best performing styles")
        
        # Style-specific recommendations
        best_style = max(self.trading_styles, key=lambda x: x.avg_performance)
        recommendations.append(f"Focus optimization on '{best_style.name}' style (best avg performance: {best_style.avg_performance:.2f}%)")
        
        # Parameter recommendations
        if len(self.trading_styles) >= 2:
            recommendations.append("Test parameter ranges from top 2 trading styles for broader exploration")
        
        recommendations.append("Use identified parameter ranges with 10-step optimization for each key parameter")
        
        return recommendations

def main():
    """Test the lab analysis system"""
    print("Lab Analysis System - Comprehensive Analysis")
    print("=" * 60)
    
    # Initialize analysis system
    analyzer = LabAnalysisSystem()
    
    # Load lab results
    print("\n1. Loading lab results...")
    if not analyzer.load_lab_results('lab_55b45ee4_results.json'):
        print("❌ Failed to load lab results")
        return
    
    print(f"✓ Loaded {len(analyzer.configurations)} configurations")
    
    # Generate comprehensive report
    print("\n2. Generating comprehensive analysis...")
    report = analyzer.generate_comprehensive_report()
    
    # Display results
    print("\n" + "=" * 60)
    print("📊 COMPREHENSIVE LAB ANALYSIS REPORT")
    print("=" * 60)
    
    # Summary
    summary = report['lab_analysis_summary']
    print(f"\n📋 Summary:")
    print(f"   Total configurations: {summary['total_configurations']}")
    print(f"   Trading styles identified: {summary['trading_styles_identified']}")
    print(f"   Average ROI: {summary['avg_roi_all_configs']:.2f}%")
    print(f"   Profitable configurations: {summary['profitable_percentage']:.1f}%")
    print(f"   Best ROI: {summary['best_roi']:.2f}%")
    
    # Trading styles
    print(f"\n🎯 Top 3 Trading Styles:")
    for i, style in enumerate(report['trading_styles'][:3]):
        print(f"\n   {i+1}. {style['name']}")
        print(f"      Description: {style['description']}")
        print(f"      Avg Performance: {style['avg_performance']:.2f}%")
        print(f"      Configurations: {style['configuration_count']}")
        print(f"      Profitable Ratio: {style['performance_profile']['profitable_ratio']:.1%}")
    
    # Optimization ranges
    print(f"\n🔧 Parameter Optimization Ranges:")
    for style_name, style_data in report['optimization_ranges'].items():
        print(f"\n   Style: {style_name}")
        param_ranges = style_data['parameter_ranges']
        
        # Show top 5 parameters
        for param, range_info in list(param_ranges.items())[:5]:
            print(f"      {param}:")
            print(f"         Current: {range_info['current_min']:.1f} - {range_info['current_max']:.1f}")
            print(f"         Optimize: {range_info['optimization_min']:.1f} - {range_info['optimization_max']:.1f}")
            print(f"         Step: {range_info['step_size']:.2f}")
    
    # Recommendations
    print(f"\n💡 Recommendations:")
    for i, rec in enumerate(report['recommendations'], 1):
        print(f"   {i}. {rec}")
    
    # Save detailed report
    with open('lab_analysis_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n✓ Detailed report saved to 'lab_analysis_report.json'")
    print("\n" + "=" * 60)
    print("Lab analysis completed successfully!")

if __name__ == "__main__":
    main()