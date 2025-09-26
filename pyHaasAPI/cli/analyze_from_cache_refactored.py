#!/usr/bin/env python3
"""
Refactored Cache Analysis Tool for pyHaasAPI CLI

This tool analyzes cached lab data with advanced filtering and reporting.
Refactored to use base classes and working analyzer.
"""

import argparse
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from .base import BaseAnalysisCLI
from .common import add_common_arguments, get_cached_labs
from .working_analyzer import WorkingLabAnalyzer, BacktestPerformance


@dataclass
class LabAnalysisResult:
    """Data class for lab analysis results"""
    lab_id: str
    lab_name: str
    total_backtests: int
    top_backtests: List[BacktestPerformance]
    analysis_timestamp: str


class CacheAnalyzerRefactored(BaseAnalysisCLI):
    """Refactored cache analysis tool using base classes and working analyzer"""
    
    def __init__(self):
        super().__init__()
        self.working_analyzer = WorkingLabAnalyzer(self.cache)
        
    def run(self, args) -> bool:
        """Main execution method"""
        try:
            # Connect (will use cache-only mode if available)
            if not self.connect():
                return False
            
            # Get cached labs
            cached_lab_ids = get_cached_labs(self.cache)
            if not cached_lab_ids:
                self.logger.error("❌ No cached lab data found")
                self.logger.info("💡 Run 'python -m pyHaasAPI.cli.cache_labs' to cache lab data first")
                return False
            
            self.logger.info(f"📁 Found {len(cached_lab_ids)} labs with cached data")
            
            # Filter labs based on criteria
            if args.lab_ids:
                filtered_lab_ids = [lab_id for lab_id in cached_lab_ids if lab_id in args.lab_ids]
            elif args.exclude_lab_ids:
                filtered_lab_ids = [lab_id for lab_id in cached_lab_ids if lab_id not in args.exclude_lab_ids]
            else:
                filtered_lab_ids = cached_lab_ids
            
            if not filtered_lab_ids:
                self.logger.warning("⚠️ No labs match the specified criteria")
                return False
            
            self.logger.info(f"📊 Analyzing {len(filtered_lab_ids)} labs")
            
            # Analyze labs
            lab_results = self.analyze_cached_labs(filtered_lab_ids, args.top_count)
            
            if not lab_results:
                self.logger.warning("⚠️ No analysis results generated")
                return False
            
            # Show data distribution if requested
            if args.show_data_distribution:
                self.show_data_distribution(lab_results)
            
            # Generate reports if requested
            if args.generate_lab_reports:
                self.generate_and_show_reports(lab_results, args)
            
            # Save results if requested
            if args.save_results:
                self.save_results(lab_results, args)
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error in cache analysis: {e}")
            return False
    
    def analyze_cached_labs(self, lab_ids: List[str], top_count: int) -> List[LabAnalysisResult]:
        """Analyze cached labs using working analyzer"""
        lab_results = []
        
        for i, lab_id in enumerate(lab_ids, 1):
            try:
                self.logger.info(f"🔍 Analyzing lab {i}/{len(lab_ids)}: {lab_id}")
                
                # Use working analyzer to analyze lab
                backtests = self.working_analyzer.analyze_lab_manual(lab_id, top_count)
                
                if backtests:
                    lab_name = self.working_analyzer.get_full_lab_name(lab_id)
                    
                    result = LabAnalysisResult(
                        lab_id=lab_id,
                        lab_name=lab_name,
                        total_backtests=len(backtests),
                        top_backtests=backtests,
                        analysis_timestamp=self.get_timestamp()
                    )
                    
                    lab_results.append(result)
                    self.logger.info(f"✅ Analyzed {len(backtests)} backtests for {lab_name}")
                else:
                    self.logger.warning(f"⚠️ No backtests found for lab {lab_id}")
                    
            except Exception as e:
                self.logger.error(f"❌ Error analyzing lab {lab_id}: {e}")
                continue
        
        return lab_results
    
    def show_data_distribution(self, lab_results: List[LabAnalysisResult]):
        """Show data distribution analysis"""
        distribution = self.working_analyzer.analyze_data_distribution(lab_results)
        self.working_analyzer.print_data_distribution(distribution)
    
    def generate_and_show_reports(self, lab_results: List[LabAnalysisResult], args):
        """Generate and show lab analysis reports"""
        # Create criteria from args
        criteria = {
            'min_roe': args.min_roe,
            'max_roe': args.max_roe,
            'min_winrate': args.min_winrate,
            'max_winrate': args.max_winrate,
            'min_trades': args.min_trades,
            'max_trades': args.max_trades
        }
        
        # Generate reports
        reports = self.working_analyzer.generate_lab_analysis_reports(lab_results, criteria)
        
        # Show reports
        self.working_analyzer.print_lab_analysis_reports(reports, criteria)
    
    def save_results(self, lab_results: List[LabAnalysisResult], args):
        """Save analysis results to file"""
        # Create criteria from args
        criteria = {
            'min_roe': args.min_roe,
            'max_roe': args.max_roe,
            'min_winrate': args.min_winrate,
            'max_winrate': args.max_winrate,
            'min_trades': args.min_trades,
            'max_trades': args.max_trades
        }
        
        # Generate reports
        reports = self.working_analyzer.generate_lab_analysis_reports(lab_results, criteria)
        
        # Save to file
        filename = args.output or f"lab_analysis_reports_{self.get_timestamp()}.{args.output_format}"
        saved_file = self.working_analyzer.save_lab_analysis_reports(reports, filename, args.output_format)
        
        self.logger.info(f"💾 Results saved to: {saved_file}")
    
    def get_timestamp(self) -> str:
        """Get current timestamp string"""
        from datetime import datetime
        return datetime.now().strftime('%Y%m%d_%H%M%S')


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Analyze cached lab data with filtering and reporting")
    
    # Add common arguments
    add_common_arguments(parser)
    
    # Add specific arguments
    parser.add_argument('--show-data-distribution', action='store_true',
                       help='Show data distribution analysis')
    parser.add_argument('--generate-lab-reports', action='store_true',
                       help='Generate and display lab analysis reports')
    parser.add_argument('--save-results', action='store_true',
                       help='Save analysis results to file')
    
    args = parser.parse_args()
    
    # Create and run analyzer
    analyzer = CacheAnalyzerRefactored()
    success = analyzer.run(args)
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
















