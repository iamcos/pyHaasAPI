#!/usr/bin/env python3
"""
Comprehensive Backtest Analysis Runner

This script runs the complete backtest data extraction and heuristics analysis
pipeline, addressing the debugging issues identified in the development plan.
"""

import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Any

from data_extractor import BacktestDataExtractor, BacktestSummary
from heuristics_analyzer import HeuristicsAnalyzer, ConfigurationAnalysis

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BacktestAnalysisRunner:
    """Main runner for the complete backtest analysis pipeline"""
    
    def __init__(self, lab_id: str, results_directory: str):
        self.lab_id = lab_id
        self.results_directory = results_directory
        self.extractor = BacktestDataExtractor(results_directory)
        self.analyzer = HeuristicsAnalyzer()
        
    def run_complete_analysis(self) -> Dict[str, Any]:
        """
        Run the complete analysis pipeline and return comprehensive results.
        
        Returns:
            Dictionary containing all analysis results and statistics
        """
        logger.info("Starting complete backtest analysis pipeline...")
        
        analysis_results = {
            'lab_id': self.lab_id,
            'analysis_timestamp': datetime.now().isoformat(),
            'extraction_results': {},
            'heuristics_results': {},
            'top_configurations': [],
            'summary_statistics': {},
            'debug_information': {}
        }
        
        # Step 1: Extract backtest data
        logger.info("Step 1: Extracting backtest data...")
        backtest_summaries = self.extractor.process_all_backtests()
        
        analysis_results['extraction_results'] = {
            'total_files_processed': len([f for f in os.listdir(self.results_directory) if f.endswith('.json')]),
            'successful_extractions': len(backtest_summaries),
            'extraction_success_rate': len(backtest_summaries) / len([f for f in os.listdir(self.results_directory) if f.endswith('.json')]) if os.path.exists(self.results_directory) else 0.0
        }
        
        if not backtest_summaries:
            logger.error("No backtest data extracted. Analysis cannot continue.")
            analysis_results['debug_information']['error'] = "No backtest data extracted"
            return analysis_results
        
        # Step 2: Debug data extraction on sample
        logger.info("Step 2: Running debug analysis on sample data...")
        sample_file = os.path.join(self.results_directory, os.listdir(self.results_directory)[0])
        debug_report = self.extractor.debug_data_extraction(sample_file)
        analysis_results['debug_information'] = debug_report
        
        # Step 3: Apply heuristics analysis
        logger.info("Step 3: Applying advanced heuristics analysis...")
        top_configurations = self.analyzer.identify_top_configurations(
            backtest_summaries,
            top_count=5,
            diversity_threshold=0.3
        )
        
        # Step 4: Generate comprehensive statistics
        logger.info("Step 4: Generating comprehensive statistics...")
        summary_stats = self._generate_summary_statistics(backtest_summaries, top_configurations)
        analysis_results['summary_statistics'] = summary_stats
        
        # Step 5: Format top configurations for output
        analysis_results['top_configurations'] = self._format_top_configurations(top_configurations)
        
        # Step 6: Generate recommendations
        analysis_results['recommendations'] = self._generate_recommendations(top_configurations, summary_stats)
        
        logger.info("Complete analysis pipeline finished successfully!")
        return analysis_results
    
    def _generate_summary_statistics(self, backtest_summaries: List[BacktestSummary], top_configurations: List[ConfigurationAnalysis]) -> Dict[str, Any]:
        """Generate comprehensive summary statistics"""
        if not backtest_summaries:
            return {}
        
        # Overall statistics
        total_trades = sum(len(bs.trades) for bs in backtest_summaries)
        total_profit = sum(bs.total_profit for bs in backtest_summaries)
        total_fees = sum(bs.total_fees for bs in backtest_summaries)
        
        # ROI statistics
        roi_values = [bs.roi for bs in backtest_summaries]
        roi_stats = {
            'mean': sum(roi_values) / len(roi_values),
            'min': min(roi_values),
            'max': max(roi_values),
            'std': (sum((x - sum(roi_values) / len(roi_values))**2 for x in roi_values) / len(roi_values))**0.5
        }
        
        # Trade count statistics
        trade_counts = [len(bs.trades) for bs in backtest_summaries]
        trade_stats = {
            'mean': sum(trade_counts) / len(trade_counts),
            'min': min(trade_counts),
            'max': max(trade_counts),
            'total': total_trades
        }
        
        # Win rate statistics
        win_rates = [bs.winning_trades / len(bs.trades) if bs.trades else 0.0 for bs in backtest_summaries]
        win_rate_stats = {
            'mean': sum(win_rates) / len(win_rates),
            'min': min(win_rates),
            'max': max(win_rates)
        }
        
        # Top configuration statistics
        top_config_stats = {}
        if top_configurations:
            top_scores = [config.overall_score for config in top_configurations]
            top_config_stats = {
                'best_score': max(top_scores),
                'worst_score': min(top_scores),
                'average_score': sum(top_scores) / len(top_scores),
                'score_range': max(top_scores) - min(top_scores)
            }
        
        return {
            'total_backtests': len(backtest_summaries),
            'total_trades': total_trades,
            'total_profit': total_profit,
            'total_fees': total_fees,
            'roi_statistics': roi_stats,
            'trade_statistics': trade_stats,
            'win_rate_statistics': win_rate_stats,
            'top_configuration_statistics': top_config_stats
        }
    
    def _format_top_configurations(self, top_configurations: List[ConfigurationAnalysis]) -> List[Dict[str, Any]]:
        """Format top configurations for JSON output"""
        formatted_configs = []
        
        for config in top_configurations:
            formatted_config = {
                'backtest_id': config.backtest_id,
                'rank': config.rank,
                'overall_score': round(config.overall_score, 2),
                'recommendation': config.recommendation,
                'performance_summary': {
                    'roi': round(config.backtest_summary.roi, 2),
                    'total_trades': len(config.backtest_summary.trades),
                    'winning_trades': config.backtest_summary.winning_trades,
                    'losing_trades': config.backtest_summary.losing_trades,
                    'win_rate': round(config.backtest_summary.winning_trades / len(config.backtest_summary.trades) * 100, 1) if config.backtest_summary.trades else 0.0,
                    'total_profit': round(config.backtest_summary.total_profit, 2),
                    'total_fees': round(config.backtest_summary.total_fees, 2)
                },
                'heuristic_scores': {
                    score.name: {
                        'score': round(score.score, 2),
                        'explanation': score.explanation,
                        'key_details': {k: v for k, v in score.details.items() if isinstance(v, (int, float, str))}
                    }
                    for score in config.heuristic_scores
                },
                'parameters': config.backtest_summary.parameters,
                'settings': config.backtest_summary.settings
            }
            formatted_configs.append(formatted_config)
        
        return formatted_configs
    
    def _generate_recommendations(self, top_configurations: List[ConfigurationAnalysis], summary_stats: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations based on analysis results"""
        recommendations = []
        
        if not top_configurations:
            recommendations.append("No viable configurations found. Consider adjusting strategy parameters or testing different market conditions.")
            return recommendations
        
        # Best configuration recommendations
        best_config = top_configurations[0]
        recommendations.append(f"Top configuration ({best_config.backtest_id}) shows excellent performance with {best_config.overall_score:.1f}/100 score.")
        
        # ROI analysis
        if summary_stats.get('roi_statistics', {}).get('max', 0) > 500:
            recommendations.append("High ROI configurations identified. Consider risk management and position sizing optimization.")
        
        # Trade frequency analysis
        avg_trades = summary_stats.get('trade_statistics', {}).get('mean', 0)
        if avg_trades > 100:
            recommendations.append("High-frequency trading detected. Monitor transaction costs and slippage impact.")
        elif avg_trades < 20:
            recommendations.append("Low-frequency trading detected. Consider increasing signal sensitivity or reducing filters.")
        
        # Diversity analysis
        if len(top_configurations) < 3:
            recommendations.append("Limited diversity in top configurations. Consider expanding parameter ranges for optimization.")
        
        # Heuristic-specific recommendations
        for config in top_configurations[:2]:  # Top 2 configurations
            for score in config.heuristic_scores:
                if score.score < 50:
                    recommendations.append(f"Configuration {config.backtest_id}: Improve {score.name.lower()} - {score.explanation}")
        
        return recommendations
    
    def save_results(self, analysis_results: Dict[str, Any], output_file: str = None) -> str:
        """Save analysis results to JSON file"""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"backtest_analysis_results_{self.lab_id}_{timestamp}.json"
        
        output_path = os.path.join(os.path.dirname(__file__), output_file)
        
        with open(output_path, 'w') as f:
            json.dump(analysis_results, f, indent=2, default=str)
        
        logger.info(f"Analysis results saved to: {output_path}")
        return output_path
    
    def print_summary_report(self, analysis_results: Dict[str, Any]):
        """Print a comprehensive summary report to console"""
        print("\n" + "="*80)
        print("BACKTEST ANALYSIS SUMMARY REPORT")
        print("="*80)
        
        # Basic information
        print(f"\nLab ID: {analysis_results['lab_id']}")
        print(f"Analysis Time: {analysis_results['analysis_timestamp']}")
        
        # Extraction results
        extraction = analysis_results.get('extraction_results', {})
        print(f"\nDATA EXTRACTION:")
        print(f"  Files Processed: {extraction.get('total_files_processed', 0)}")
        print(f"  Successful Extractions: {extraction.get('successful_extractions', 0)}")
        print(f"  Success Rate: {extraction.get('extraction_success_rate', 0):.1%}")
        
        # Summary statistics
        stats = analysis_results.get('summary_statistics', {})
        if stats:
            print(f"\nOVERALL STATISTICS:")
            print(f"  Total Backtests: {stats.get('total_backtests', 0)}")
            print(f"  Total Trades: {stats.get('total_trades', 0)}")
            print(f"  Total Profit: ${stats.get('total_profit', 0):,.2f}")
            print(f"  Total Fees: ${stats.get('total_fees', 0):,.2f}")
            
            roi_stats = stats.get('roi_statistics', {})
            if roi_stats:
                print(f"  ROI Range: {roi_stats.get('min', 0):.1f}% to {roi_stats.get('max', 0):.1f}%")
                print(f"  Average ROI: {roi_stats.get('mean', 0):.1f}%")
        
        # Top configurations
        top_configs = analysis_results.get('top_configurations', [])
        if top_configs:
            print(f"\nTOP {len(top_configs)} CONFIGURATIONS:")
            for i, config in enumerate(top_configs):
                print(f"\n  {i+1}. Backtest ID: {config['backtest_id']}")
                print(f"     Overall Score: {config['overall_score']}/100")
                print(f"     ROI: {config['performance_summary']['roi']}%")
                print(f"     Trades: {config['performance_summary']['total_trades']}")
                print(f"     Win Rate: {config['performance_summary']['win_rate']}%")
                print(f"     Recommendation: {config['recommendation']}")
        
        # Recommendations
        recommendations = analysis_results.get('recommendations', [])
        if recommendations:
            print(f"\nRECOMMENDATIONS:")
            for i, rec in enumerate(recommendations):
                print(f"  {i+1}. {rec}")
        
        # Debug information
        debug_info = analysis_results.get('debug_information', {})
        if debug_info.get('recommendations'):
            print(f"\nDEBUG STATUS:")
            for rec in debug_info['recommendations']:
                print(f"  ✓ {rec}")
        
        print("\n" + "="*80)

def main():
    """Main execution function"""
    # Configuration
    LAB_ID = '55b45ee4-9cc5-42f7-8556-4c3aa2b13a44'
    RESULTS_DIR = f'/Users/georgiigavrilenko/Documents/GitHub/pyHaasAPI/experiments/bt_analysis/raw_results/lab_{LAB_ID}'
    
    # Check if results directory exists
    if not os.path.exists(RESULTS_DIR):
        logger.error(f"Results directory not found: {RESULTS_DIR}")
        return
    
    # Initialize and run analysis
    runner = BacktestAnalysisRunner(LAB_ID, RESULTS_DIR)
    
    try:
        # Run complete analysis
        analysis_results = runner.run_complete_analysis()
        
        # Print summary report
        runner.print_summary_report(analysis_results)
        
        # Save results
        output_file = runner.save_results(analysis_results)
        
        print(f"\nAnalysis complete! Results saved to: {output_file}")
        
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()