#!/usr/bin/env python3
"""
Simple Lab Analyzer
Analyzes lab 55b45ee4-9cc5-42f7-8556-4c3aa2b13a44 results to identify
top 3 trading styles and parameter optimization ranges.
"""

import json
import logging
import math
from typing import Dict, List, Any, Tuple
from collections import defaultdict, Counter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleLabAnalyzer:
    """Simple lab analyzer without external dependencies"""
    
    def __init__(self):
        self.configurations = []
        self.trading_styles = []
    
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
                    # Only include completed backtests (status 3)
                    if result.get('ST', 0) == 3:
                        config = {
                            'result_id': result.get('RID', 0),
                            'lab_id': result.get('LID', ''),
                            'backtest_id': result.get('BID', ''),
                            'parameters': result.get('P', {}),
                            'performance': result.get('S', {}),
                            'settings': result.get('SE', {}),
                            'status': result.get('ST', 0),
                            'generations': result.get('NG', 0),
                            'population': result.get('NP', 0)
                        }
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
        
        for config in self.configurations:
            perf = config['performance']
            roi = perf.get('ReturnOnInvestment', 0.0)
            profit = perf.get('RealizedProfits', 0.0)
            
            roi_values.append(roi)
            profit_values.append(profit)
        
        # Calculate statistics
        def calc_stats(values):
            if not values:
                return {'mean': 0, 'std': 0, 'min': 0, 'max': 0, 'median': 0}
            
            sorted_vals = sorted(values)
            n = len(values)
            mean_val = sum(values) / n
            variance = sum((x - mean_val) ** 2 for x in values) / n
            std_val = math.sqrt(variance)
            median_val = sorted_vals[n // 2] if n % 2 == 1 else (sorted_vals[n // 2 - 1] + sorted_vals[n // 2]) / 2
            
            return {
                'mean': mean_val,
                'std': std_val,
                'min': min(values),
                'max': max(values),
                'median': median_val
            }
        
        roi_stats = calc_stats(roi_values)
        profit_stats = calc_stats(profit_values)
        
        profitable_count = sum(1 for roi in roi_values if roi > 0)
        
        analysis = {
            'total_configurations': len(self.configurations),
            'roi_statistics': {
                **roi_stats,
                'profitable_count': profitable_count,
                'profitable_percentage': (profitable_count / len(roi_values)) * 100 if roi_values else 0
            },
            'profit_statistics': {
                **profit_stats,
                'total_profit': sum(profit_values)
            },
            'top_performers': self._get_top_performers(5)
        }
        
        return analysis
    
    def _get_top_performers(self, count: int) -> List[Dict[str, Any]]:
        """Get top performing configurations"""
        # Sort by ROI
        sorted_configs = sorted(
            self.configurations,
            key=lambda x: x['performance'].get('ReturnOnInvestment', 0.0),
            reverse=True
        )
        
        top_performers = []
        for config in sorted_configs[:count]:
            perf = config['performance']
            top_performers.append({
                'result_id': config['result_id'],
                'roi': perf.get('ReturnOnInvestment', 0.0),
                'profit': perf.get('RealizedProfits', 0.0),
                'parameters': config['parameters']
            })
        
        return top_performers
    
    def identify_trading_styles(self, n_styles: int = 3) -> List[Dict[str, Any]]:
        """Identify distinct trading styles based on timeframes and key parameters"""
        logger.info(f"Identifying {n_styles} distinct trading styles")
        
        # Group by timeframe combinations
        timeframe_groups = defaultdict(list)
        
        for config in self.configurations:
            params = config['parameters']
            low_tf = params.get('20-20-18-30.Low TF', 'Unknown')
            high_tf = params.get('21-21-18-30.High TF', 'Unknown')
            tf_key = f"{low_tf}|{high_tf}"
            timeframe_groups[tf_key].append(config)
        
        # Get top timeframe combinations by count and performance
        tf_performance = []
        for tf_key, configs in timeframe_groups.items():
            if len(configs) >= 3:  # Need at least 3 configs for a style
                roi_values = [c['performance'].get('ReturnOnInvestment', 0.0) for c in configs]
                avg_roi = sum(roi_values) / len(roi_values)
                tf_performance.append((tf_key, configs, avg_roi))
        
        # Sort by performance and take top styles
        tf_performance.sort(key=lambda x: x[2], reverse=True)
        
        # Create trading styles
        trading_styles = []
        for style_id, (tf_key, configs, avg_roi) in enumerate(tf_performance[:n_styles]):
            low_tf, high_tf = tf_key.split('|')
            
            # Calculate key parameter averages
            key_params = self._calculate_key_parameters(configs)
            
            # Generate style description
            style_name, description = self._generate_style_description(style_id, low_tf, high_tf, key_params)
            
            # Calculate performance profile
            performance_profile = self._calculate_performance_profile(configs)
            
            trading_style = {
                'style_id': style_id,
                'name': style_name,
                'description': description,
                'timeframes': {'low_tf': low_tf, 'high_tf': high_tf},
                'key_parameters': key_params,
                'performance_profile': performance_profile,
                'configuration_count': len(configs),
                'avg_performance': avg_roi,
                'configurations': configs
            }
            
            trading_styles.append(trading_style)
        
        self.trading_styles = trading_styles
        logger.info(f"Identified {len(trading_styles)} trading styles")
        
        return trading_styles
    
    def _calculate_key_parameters(self, configs: List[Dict]) -> Dict[str, float]:
        """Calculate average key parameters for a group of configurations"""
        key_param_names = [
            '83-83-19-24.ADX trigger',
            '81-81-12-17.Stoch low line',
            '82-82-12-17.Stoch high line',
            '84-84-16-21.Fast DEMA period',
            '85-85-16-21.Slow DEMA period',
            '88-88-12-17.TP 1st pt, %',
            '79-79-15-20.SL colldown reset'
        ]
        
        param_averages = {}
        
        for param_name in key_param_names:
            values = []
            for config in configs:
                value = config['parameters'].get(param_name)
                if isinstance(value, (int, float)):
                    values.append(float(value))
                elif isinstance(value, str) and value.replace('.', '').replace('-', '').isdigit():
                    values.append(float(value))
            
            if values:
                param_averages[param_name] = sum(values) / len(values)
        
        return param_averages
    
    def _generate_style_description(self, style_id: int, low_tf: str, high_tf: str, 
                                  key_params: Dict[str, float]) -> Tuple[str, str]:
        """Generate name and description for a trading style"""
        
        # Analyze characteristics
        characteristics = []
        
        # Timeframe analysis
        if low_tf != 'Unknown' and high_tf != 'Unknown':
            characteristics.append(f"Timeframes: {low_tf} / {high_tf}")
        
        # ADX analysis
        adx_trigger = key_params.get('83-83-19-24.ADX trigger', 25)
        if adx_trigger < 20:
            characteristics.append("Low ADX (Trending markets)")
        elif adx_trigger > 30:
            characteristics.append("High ADX (Strong trends)")
        else:
            characteristics.append("Medium ADX (Balanced)")
        
        # Stochastic analysis
        stoch_low = key_params.get('81-81-12-17.Stoch low line', 20)
        stoch_high = key_params.get('82-82-12-17.Stoch high line', 80)
        
        if stoch_low < 18:
            characteristics.append("Aggressive oversold entry")
        if stoch_high > 82:
            characteristics.append("Aggressive overbought exit")
        
        # DEMA analysis
        fast_dema = key_params.get('84-84-16-21.Fast DEMA period', 10)
        slow_dema = key_params.get('85-85-16-21.Slow DEMA period', 30)
        
        if fast_dema < 10:
            characteristics.append("Fast DEMA (Quick signals)")
        if slow_dema > 30:
            characteristics.append("Slow DEMA (Stable signals)")
        
        # Generate names based on characteristics
        style_names = [
            "Conservative Scalper",
            "Aggressive Momentum", 
            "Balanced Swing Trader"
        ]
        
        name = style_names[style_id] if style_id < len(style_names) else f"Style {style_id + 1}"
        description = f"Trading style with {', '.join(characteristics[:3])}"
        
        return name, description
    
    def _calculate_performance_profile(self, configs: List[Dict]) -> Dict[str, float]:
        """Calculate performance profile for a group of configurations"""
        roi_values = [c['performance'].get('ReturnOnInvestment', 0.0) for c in configs]
        profit_values = [c['performance'].get('RealizedProfits', 0.0) for c in configs]
        
        profitable_count = sum(1 for roi in roi_values if roi > 0)
        
        return {
            'avg_roi': sum(roi_values) / len(roi_values) if roi_values else 0,
            'roi_std': math.sqrt(sum((x - sum(roi_values)/len(roi_values))**2 for x in roi_values) / len(roi_values)) if len(roi_values) > 1 else 0,
            'max_roi': max(roi_values) if roi_values else 0,
            'min_roi': min(roi_values) if roi_values else 0,
            'avg_profit': sum(profit_values) / len(profit_values) if profit_values else 0,
            'total_profit': sum(profit_values),
            'profitable_ratio': profitable_count / len(roi_values) if roi_values else 0,
            'configuration_count': len(configs)
        }
    
    def generate_parameter_ranges(self) -> Dict[str, Dict[str, Any]]:
        """Generate parameter optimization ranges for each trading style"""
        if not self.trading_styles:
            logger.error("No trading styles identified. Run identify_trading_styles() first.")
            return {}
        
        optimization_ranges = {}
        
        for style in self.trading_styles:
            style_name = style['name']
            configs = style['configurations']
            
            # Get parameter ranges for this style
            param_ranges = self._calculate_parameter_ranges(configs)
            
            # Filter to most important parameters
            important_params = [
                '83-83-19-24.ADX trigger',
                '81-81-12-17.Stoch low line', 
                '82-82-12-17.Stoch high line',
                '84-84-16-21.Fast DEMA period',
                '85-85-16-21.Slow DEMA period',
                '88-88-12-17.TP 1st pt, %',
                '79-79-15-20.SL colldown reset'
            ]
            
            filtered_ranges = {}
            for param in important_params:
                if param in param_ranges:
                    range_info = param_ranges[param]
                    
                    # Create optimization ranges
                    current_range = range_info['max'] - range_info['min']
                    if current_range > 0:
                        # Expand range by 20% for exploration
                        expansion = current_range * 0.2
                        opt_min = max(0, range_info['min'] - expansion)
                        opt_max = range_info['max'] + expansion
                        
                        filtered_ranges[param] = {
                            'current_min': range_info['min'],
                            'current_max': range_info['max'],
                            'current_mean': range_info['mean'],
                            'optimization_min': round(opt_min, 1),
                            'optimization_max': round(opt_max, 1),
                            'step_size': round(current_range / 10, 1),
                            'suggested_values': self._generate_suggested_values(opt_min, opt_max, 10)
                        }
            
            optimization_ranges[style_name] = {
                'style_info': {
                    'name': style_name,
                    'description': style['description'],
                    'avg_performance': style['avg_performance'],
                    'configuration_count': style['configuration_count'],
                    'timeframes': style['timeframes']
                },
                'parameter_ranges': filtered_ranges
            }
        
        return optimization_ranges
    
    def _calculate_parameter_ranges(self, configs: List[Dict]) -> Dict[str, Dict[str, float]]:
        """Calculate parameter ranges for a group of configurations"""
        param_values = defaultdict(list)
        
        # Collect parameter values
        for config in configs:
            for param, value in config['parameters'].items():
                if isinstance(value, (int, float)):
                    param_values[param].append(float(value))
                elif isinstance(value, str) and value.replace('.', '').replace('-', '').isdigit():
                    param_values[param].append(float(value))
        
        # Calculate ranges
        ranges = {}
        for param, values in param_values.items():
            if len(values) > 1:
                mean_val = sum(values) / len(values)
                variance = sum((x - mean_val) ** 2 for x in values) / len(values)
                std_val = math.sqrt(variance)
                
                ranges[param] = {
                    'min': min(values),
                    'max': max(values),
                    'mean': mean_val,
                    'std': std_val,
                    'values': values
                }
        
        return ranges
    
    def _generate_suggested_values(self, min_val: float, max_val: float, steps: int) -> List[float]:
        """Generate suggested values for parameter optimization"""
        if steps <= 1:
            return [min_val]
        
        step_size = (max_val - min_val) / (steps - 1)
        return [round(min_val + i * step_size, 1) for i in range(steps)]
    
    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate comprehensive analysis report"""
        if not self.configurations:
            return {'error': 'No configurations loaded'}
        
        # Performance analysis
        performance_analysis = self.analyze_performance_metrics()
        
        # Trading styles
        if not self.trading_styles:
            self.identify_trading_styles(3)
        
        # Parameter ranges
        parameter_ranges = self.generate_parameter_ranges()
        
        # Generate recommendations
        recommendations = self._generate_recommendations(performance_analysis)
        
        report = {
            'lab_id': '55b45ee4-9cc5-42f7-8556-4c3aa2b13a44',
            'analysis_summary': {
                'total_configurations': len(self.configurations),
                'trading_styles_identified': len(self.trading_styles),
                'avg_roi_all_configs': performance_analysis['roi_statistics']['mean'],
                'profitable_percentage': performance_analysis['roi_statistics']['profitable_percentage'],
                'best_roi': performance_analysis['roi_statistics']['max']
            },
            'performance_analysis': performance_analysis,
            'top_3_trading_styles': self.trading_styles[:3],
            'parameter_optimization_ranges': parameter_ranges,
            'recommendations': recommendations
        }
        
        return report
    
    def _generate_recommendations(self, performance_analysis: Dict[str, Any]) -> List[str]:
        """Generate optimization recommendations"""
        recommendations = []
        
        profitable_pct = performance_analysis['roi_statistics']['profitable_percentage']
        
        if profitable_pct < 10:
            recommendations.append("⚠️ Very low profitability (< 10%) - consider major strategy changes")
        elif profitable_pct < 30:
            recommendations.append("📊 Low profitability - focus on optimizing top performing style parameters")
        else:
            recommendations.append("✅ Reasonable profitability - fine-tune parameters around best styles")
        
        if self.trading_styles:
            best_style = max(self.trading_styles, key=lambda x: x['avg_performance'])
            recommendations.append(f"🎯 Focus on '{best_style['name']}' style (best performance: {best_style['avg_performance']:.2f}%)")
            
            recommendations.append(f"⚙️ Test parameter ranges from top 3 styles for comprehensive optimization")
            recommendations.append(f"🔄 Use 10-step optimization for each key parameter within suggested ranges")
        
        return recommendations

def main():
    """Analyze lab 55b45ee4-9cc5-42f7-8556-4c3aa2b13a44"""
    print("🔬 Lab 55b45ee4-9cc5-42f7-8556-4c3aa2b13a44 Analysis")
    print("=" * 70)
    
    # Initialize analyzer
    analyzer = SimpleLabAnalyzer()
    
    # Load lab results
    print("\n1. Loading lab results...")
    if not analyzer.load_lab_results('lab_55b45ee4_results.json'):
        print("❌ Failed to load lab results")
        return
    
    print(f"✅ Loaded {len(analyzer.configurations)} completed configurations")
    
    # Generate comprehensive report
    print("\n2. Generating comprehensive analysis...")
    report = analyzer.generate_comprehensive_report()
    
    # Display results
    print("\n" + "=" * 70)
    print("📊 COMPREHENSIVE LAB ANALYSIS REPORT")
    print("=" * 70)
    
    # Summary
    summary = report['analysis_summary']
    print(f"\n📋 Analysis Summary:")
    print(f"   Lab ID: {report['lab_id']}")
    print(f"   Total configurations: {summary['total_configurations']}")
    print(f"   Trading styles identified: {summary['trading_styles_identified']}")
    print(f"   Average ROI: {summary['avg_roi_all_configs']:.3f}%")
    print(f"   Profitable configurations: {summary['profitable_percentage']:.1f}%")
    print(f"   Best ROI: {summary['best_roi']:.3f}%")
    
    # Top performers
    print(f"\n🏆 Top 5 Performers:")
    for i, performer in enumerate(report['performance_analysis']['top_performers'], 1):
        print(f"   {i}. ROI: {performer['roi']:.3f}% | Profit: {performer['profit']:.2f}")
    
    # Trading styles
    print(f"\n🎯 Top 3 Trading Styles with Distinct Characteristics:")
    for i, style in enumerate(report['top_3_trading_styles'], 1):
        print(f"\n   {i}. {style['name']}")
        print(f"      Description: {style['description']}")
        print(f"      Timeframes: {style['timeframes']['low_tf']} / {style['timeframes']['high_tf']}")
        print(f"      Avg Performance: {style['avg_performance']:.3f}%")
        print(f"      Configurations: {style['configuration_count']}")
        print(f"      Profitable Ratio: {style['performance_profile']['profitable_ratio']:.1%}")
    
    # Parameter ranges
    print(f"\n⚙️ Parameter Optimization Ranges:")
    for style_name, style_data in report['parameter_optimization_ranges'].items():
        print(f"\n   📊 {style_name}:")
        param_ranges = style_data['parameter_ranges']
        
        # Show key parameters
        for param, range_info in list(param_ranges.items())[:5]:
            print(f"      {param}:")
            print(f"         Current Range: {range_info['current_min']:.1f} - {range_info['current_max']:.1f}")
            print(f"         Optimization Range: {range_info['optimization_min']:.1f} - {range_info['optimization_max']:.1f}")
            print(f"         Step Size: {range_info['step_size']:.1f}")
            print(f"         Suggested Values: {range_info['suggested_values'][:5]}...")
    
    # Recommendations
    print(f"\n💡 Key Recommendations:")
    for i, rec in enumerate(report['recommendations'], 1):
        print(f"   {i}. {rec}")
    
    # Save detailed report
    with open('lab_55b45ee4_analysis_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n✅ Detailed analysis report saved to 'lab_55b45ee4_analysis_report.json'")
    
    print("\n" + "=" * 70)
    print("🎉 Lab analysis completed successfully!")
    print("\n🔍 Key Findings:")
    print(f"   • {summary['trading_styles_identified']} distinct trading styles identified")
    print(f"   • {summary['profitable_percentage']:.1f}% of configurations are profitable")
    print(f"   • Parameter ranges generated for optimization")
    print(f"   • Ready for next iteration with focused parameter ranges")

if __name__ == "__main__":
    main()