#!/usr/bin/env python3
"""
Unified Analysis CLI for pyHaasAPI

This tool provides a unified interface for all analysis operations:
- Cache analysis with filtering and reporting
- Interactive analysis and selection
- Lab data caching
- Walk Forward Optimization (WFO)

Combines the best functionality from multiple analysis tools.
"""

import argparse
import sys
from typing import List, Dict, Any, Optional

from .base import BaseAnalysisCLI
from .common import add_common_arguments, get_cached_labs
from .working_analyzer import WorkingLabAnalyzer


class UnifiedAnalysisCLI(BaseAnalysisCLI):
    """Unified analysis CLI combining all analysis functionality"""
    
    def __init__(self):
        super().__init__()
        self.working_analyzer = WorkingLabAnalyzer(self.cache)
        
    def run(self, args) -> bool:
        """Main execution method"""
        try:
            # Connect (will use cache-only mode if available)
            if not self.connect():
                return False
            
            # Route to appropriate subcommand
            if args.command == 'cache':
                return self.run_cache_analysis(args)
            elif args.command == 'interactive':
                return self.run_interactive_analysis(args)
            elif args.command == 'cache-labs':
                return self.run_cache_labs(args)
            elif args.command == 'wfo':
                return self.run_wfo_analysis(args)
            else:
                self.logger.error(f"❌ Unknown command: {args.command}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error in unified analysis: {e}")
            return False
    
    def run_cache_analysis(self, args) -> bool:
        """Run cache analysis with filtering and reporting"""
        try:
            # Get cached labs
            cached_lab_ids = get_cached_labs(self.cache)
            if not cached_lab_ids:
                self.logger.error("❌ No cached lab data found")
                self.logger.info("💡 Run 'analysis cache-labs' to cache lab data first")
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
    
    def run_interactive_analysis(self, args) -> bool:
        """Run interactive analysis and selection"""
        try:
            self.logger.info("🎯 Starting Interactive Analysis")
            self.logger.info("=" * 60)
            
            # Get cached labs
            cached_lab_ids = get_cached_labs(self.cache)
            if not cached_lab_ids:
                self.logger.error("❌ No cached lab data found")
                self.logger.info("💡 Run 'analysis cache-labs' to cache lab data first")
                return False
            
            # Filter labs if specified
            if args.lab_ids:
                filtered_lab_ids = [lab_id for lab_id in cached_lab_ids if lab_id in args.lab_ids]
            elif args.exclude_lab_ids:
                filtered_lab_ids = [lab_id for lab_id in cached_lab_ids if lab_id not in args.exclude_lab_ids]
            else:
                filtered_lab_ids = cached_lab_ids
            
            if not filtered_lab_ids:
                self.logger.warning("⚠️ No labs match the specified criteria")
                return False
            
            # Interactive lab selection
            selected_labs = self.interactive_lab_selection(filtered_lab_ids)
            
            if not selected_labs:
                self.logger.info("👋 No labs selected - exiting")
                return True
            
            # Analyze selected labs
            lab_results = self.analyze_cached_labs(selected_labs, args.top_count)
            
            if not lab_results:
                self.logger.warning("⚠️ No analysis results generated")
                return False
            
            # Interactive backtest selection
            selected_backtests = self.interactive_backtest_selection(lab_results)
            
            if not selected_backtests:
                self.logger.info("👋 No backtests selected - exiting")
                return True
            
            # Show selected backtests
            self.show_selected_backtests(selected_backtests)
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error in interactive analysis: {e}")
            return False
    
    def run_cache_labs(self, args) -> bool:
        """Run lab data caching"""
        try:
            self.logger.info("📁 Starting Lab Data Caching")
            self.logger.info("=" * 60)
            
            # Get all complete labs
            all_labs = self.analyzer.get_complete_labs()
            if not all_labs:
                self.logger.error("❌ No complete labs found")
                return False
            
            # Filter labs based on criteria
            filtered_labs = self.filter_labs(all_labs, args.lab_ids, args.exclude_lab_ids)
            
            if not filtered_labs:
                self.logger.warning("⚠️ No labs match the specified criteria")
                return False
            
            self.logger.info(f"📊 Caching data for {len(filtered_labs)} labs")
            
            # Cache lab data
            success = self.cache_lab_data(filtered_labs, args.analyze_count)
            
            if success:
                self.logger.info("✅ Lab data caching completed successfully")
            else:
                self.logger.error("❌ Lab data caching failed")
            
            return success
            
        except Exception as e:
            self.logger.error(f"❌ Error in lab caching: {e}")
            return False
    
    def run_wfo_analysis(self, args) -> bool:
        """Run Walk Forward Optimization analysis"""
        try:
            self.logger.info("🔄 Starting Walk Forward Optimization Analysis")
            self.logger.info("=" * 60)
            
            if not args.lab_id:
                self.logger.error("❌ Lab ID is required for WFO analysis")
                return False
            
            # Import WFO analyzer
            from .wfo_analyzer import WFOAnalyzerCLI
            
            # Create WFO analyzer
            wfo_analyzer = WFOAnalyzerCLI()
            
            # Run WFO analysis
            success = wfo_analyzer.analyze_lab_wfo(
                lab_id=args.lab_id,
                start_date=args.start_date,
                end_date=args.end_date,
                training_days=args.training_days,
                testing_days=args.testing_days,
                mode=args.mode,
                step_days=args.step_days,
                dry_run=args.dry_run
            )
            
            return success
            
        except Exception as e:
            self.logger.error(f"❌ Error in WFO analysis: {e}")
            return False
    
    def analyze_cached_labs(self, lab_ids: List[str], top_count: int):
        """Analyze cached labs using working analyzer"""
        from .analyze_from_cache_refactored import LabAnalysisResult
        
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
    
    def show_data_distribution(self, lab_results):
        """Show data distribution analysis"""
        distribution = self.working_analyzer.analyze_data_distribution(lab_results)
        self.working_analyzer.print_data_distribution(distribution)
    
    def generate_and_show_reports(self, lab_results, args):
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
    
    def save_results(self, lab_results, args):
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
    
    def interactive_lab_selection(self, lab_ids: List[str]) -> List[str]:
        """Interactive lab selection"""
        self.logger.info(f"\n📋 Available Labs ({len(lab_ids)}):")
        for i, lab_id in enumerate(lab_ids, 1):
            lab_name = self.working_analyzer.get_full_lab_name(lab_id)
            self.logger.info(f"  {i:2d}. {lab_name} ({lab_id[:8]})")
        
        try:
            selection = input(f"\n🎯 Select labs (comma-separated numbers, or 'all'): ").strip()
            
            if selection.lower() == 'all':
                return lab_ids
            
            # Parse selection
            selected_indices = [int(x.strip()) - 1 for x in selection.split(',')]
            selected_labs = [lab_ids[i] for i in selected_indices if 0 <= i < len(lab_ids)]
            
            return selected_labs
            
        except (ValueError, IndexError) as e:
            self.logger.error(f"❌ Invalid selection: {e}")
            return []
    
    def interactive_backtest_selection(self, lab_results):
        """Interactive backtest selection"""
        all_backtests = []
        for result in lab_results:
            for backtest in result.top_backtests:
                all_backtests.append((result.lab_name, backtest))
        
        self.logger.info(f"\n📊 Available Backtests ({len(all_backtests)}):")
        for i, (lab_name, backtest) in enumerate(all_backtests, 1):
            roe = (backtest.realized_profits_usdt / max(backtest.starting_balance, 1)) * 100
            self.logger.info(f"  {i:2d}. {lab_name} - {backtest.script_name} - ROE: {roe:.1f}% - WR: {backtest.win_rate:.1f}%")
        
        try:
            selection = input(f"\n🎯 Select backtests (comma-separated numbers, or 'all'): ").strip()
            
            if selection.lower() == 'all':
                return all_backtests
            
            # Parse selection
            selected_indices = [int(x.strip()) - 1 for x in selection.split(',')]
            selected_backtests = [all_backtests[i] for i in selected_indices if 0 <= i < len(all_backtests)]
            
            return selected_backtests
            
        except (ValueError, IndexError) as e:
            self.logger.error(f"❌ Invalid selection: {e}")
            return []
    
    def show_selected_backtests(self, selected_backtests):
        """Show selected backtests"""
        self.logger.info(f"\n🎯 Selected Backtests ({len(selected_backtests)}):")
        self.logger.info("=" * 80)
        
        for lab_name, backtest in selected_backtests:
            roe = (backtest.realized_profits_usdt / max(backtest.starting_balance, 1)) * 100
            self.logger.info(f"📊 {lab_name} - {backtest.script_name}")
            self.logger.info(f"   ROE: {roe:.1f}%")
            self.logger.info(f"   WR: {backtest.win_rate:.1f}%")
            self.logger.info(f"   Trades: {backtest.total_trades}")
            self.logger.info(f"   Market: {backtest.market_tag}")
            self.logger.info()
    
    def cache_lab_data(self, labs, analyze_count: int) -> bool:
        """Cache lab data"""
        try:
            for i, lab in enumerate(labs, 1):
                lab_id = getattr(lab, 'id', None) or getattr(lab, 'lab_id', None) or getattr(lab, 'LID', None)
                lab_name = getattr(lab, 'name', None) or getattr(lab, 'lab_name', None) or f"Lab {lab_id[:8]}"
                
                self.logger.info(f"📁 Caching lab {i}/{len(labs)}: {lab_name}")
                
                # Cache lab data using analyzer
                success = self.analyzer.cache_lab_data(lab_id, analyze_count)
                
                if success:
                    self.logger.info(f"✅ Cached data for {lab_name}")
                else:
                    self.logger.warning(f"⚠️ Failed to cache data for {lab_name}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error caching lab data: {e}")
            return False
    
    def get_timestamp(self) -> str:
        """Get current timestamp string"""
        from datetime import datetime
        return datetime.now().strftime('%Y%m%d_%H%M%S')


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Unified analysis CLI for pyHaasAPI")
    
    # Add subcommands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Cache analysis subcommand
    cache_parser = subparsers.add_parser('cache', help='Analyze cached lab data')
    add_common_arguments(cache_parser)
    cache_parser.add_argument('--show-data-distribution', action='store_true',
                             help='Show data distribution analysis')
    cache_parser.add_argument('--generate-lab-reports', action='store_true',
                             help='Generate and display lab analysis reports')
    cache_parser.add_argument('--save-results', action='store_true',
                             help='Save analysis results to file')
    
    # Interactive analysis subcommand
    interactive_parser = subparsers.add_parser('interactive', help='Interactive analysis and selection')
    add_common_arguments(interactive_parser)
    
    # Cache labs subcommand
    cache_labs_parser = subparsers.add_parser('cache-labs', help='Cache lab data')
    add_common_arguments(cache_labs_parser)
    
    # WFO analysis subcommand
    wfo_parser = subparsers.add_parser('wfo', help='Walk Forward Optimization analysis')
    wfo_parser.add_argument('--lab-id', required=True, help='Lab ID for WFO analysis')
    wfo_parser.add_argument('--start-date', required=True, help='Start date (YYYY-MM-DD)')
    wfo_parser.add_argument('--end-date', required=True, help='End date (YYYY-MM-DD)')
    wfo_parser.add_argument('--training-days', type=int, default=365, help='Training period in days')
    wfo_parser.add_argument('--testing-days', type=int, default=90, help='Testing period in days')
    wfo_parser.add_argument('--mode', choices=['rolling', 'fixed', 'expanding'], default='rolling',
                           help='WFO mode')
    wfo_parser.add_argument('--step-days', type=int, help='Step size in days (for fixed mode)')
    wfo_parser.add_argument('--dry-run', action='store_true', help='Show what would be done')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Create and run unified analysis CLI
    analysis_cli = UnifiedAnalysisCLI()
    success = analysis_cli.run(args)
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())















