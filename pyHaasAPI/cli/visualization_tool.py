#!/usr/bin/env python3
"""
Visualization Tool CLI

This tool generates charts and graphs for backtest analysis, including:
- Equity curves
- Drawdown charts
- Performance comparisons
- Risk-return scatter plots
- Trade distribution histograms
"""

import os
import sys
import logging
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
import argparse

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from pyHaasAPI import HaasAnalyzer, UnifiedCacheManager
from pyHaasAPI.analysis.models import BacktestAnalysis
from pyHaasAPI.analysis.extraction import BacktestDataExtractor, BacktestSummary
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Try to import visualization libraries
try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    import seaborn as sns
    import pandas as pd
    import numpy as np
    from matplotlib.patches import Rectangle
    VISUALIZATION_AVAILABLE = True
except ImportError:
    VISUALIZATION_AVAILABLE = False
    logger.warning("⚠️ Visualization libraries not available. Install matplotlib, seaborn, pandas, numpy for charts.")


class VisualizationTool:
    """Generates charts and graphs for backtest analysis"""
    
    def __init__(self):
        self.analyzer = None
        self.cache = UnifiedCacheManager()
        self.start_time = time.time()
        
        if VISUALIZATION_AVAILABLE:
            # Set up matplotlib style
            plt.style.use('seaborn-v0_8')
            sns.set_palette("husl")
        
    def connect(self) -> bool:
        """Connect to HaasOnline API"""
        try:
            logger.info("🔌 Connecting to HaasOnline API...")
            
            # Initialize analyzer
            self.analyzer = HaasAnalyzer(self.cache)
            
            # Connect
            if not self.analyzer.connect():
                logger.error("❌ Failed to connect to HaasOnline API")
                return False
                
            logger.info("✅ Connected successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Connection failed: {e}")
            return False
    
    def generate_equity_curve(self, backtest: BacktestAnalysis, save_path: str = None) -> str:
        """Generate equity curve chart for a backtest"""
        if not VISUALIZATION_AVAILABLE:
            logger.error("❌ Visualization libraries not available")
            return ""
        
        try:
            # Load backtest data
            backtest_data = self.cache.load_backtest_cache(backtest.lab_id, backtest.backtest_id)
            if not backtest_data:
                logger.warning(f"⚠️ No cached data for backtest {backtest.backtest_id[:8]}")
                return ""
            
            # Extract trade data
            extractor = BacktestDataExtractor()
            summary = extractor.extract_backtest_summary(backtest_data)
            
            if not summary or not summary.trades:
                logger.warning(f"⚠️ No trade data for backtest {backtest.backtest_id[:8]}")
                return ""
            
            # Create equity curve
            equity_curve = []
            cumulative_pnl = 0
            timestamps = []
            
            for trade in summary.trades:
                cumulative_pnl += trade.net_pnl
                equity_curve.append(cumulative_pnl)
                timestamps.append(trade.exit_time)
            
            # Create the plot
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), height_ratios=[3, 1])
            
            # Equity curve
            ax1.plot(timestamps, equity_curve, linewidth=2, color='blue', alpha=0.8)
            ax1.axhline(y=0, color='red', linestyle='--', alpha=0.5)
            ax1.set_title(f'Equity Curve - {backtest.script_name}\nBacktest: {backtest.backtest_id[:12]}', fontsize=14, fontweight='bold')
            ax1.set_ylabel('Cumulative P&L (USDT)', fontsize=12)
            ax1.grid(True, alpha=0.3)
            ax1.tick_params(axis='x', rotation=45)
            
            # Drawdown chart
            peak = np.maximum.accumulate(equity_curve)
            drawdown = equity_curve - peak
            ax2.fill_between(timestamps, drawdown, 0, color='red', alpha=0.3)
            ax2.plot(timestamps, drawdown, color='red', linewidth=1)
            ax2.set_title('Drawdown', fontsize=12)
            ax2.set_xlabel('Time', fontsize=12)
            ax2.set_ylabel('Drawdown (USDT)', fontsize=12)
            ax2.grid(True, alpha=0.3)
            ax2.tick_params(axis='x', rotation=45)
            
            # Format x-axis
            for ax in [ax1, ax2]:
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
                ax.xaxis.set_major_locator(mdates.MonthLocator())
            
            plt.tight_layout()
            
            # Save the plot
            if not save_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                save_path = f"equity_curve_{backtest.backtest_id[:8]}_{timestamp}.png"
            
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"📊 Equity curve saved: {save_path}")
            return save_path
            
        except Exception as e:
            logger.error(f"❌ Error generating equity curve: {e}")
            return ""
    
    def generate_performance_comparison(self, backtests: List[BacktestAnalysis], save_path: str = None) -> str:
        """Generate performance comparison chart"""
        if not VISUALIZATION_AVAILABLE:
            logger.error("❌ Visualization libraries not available")
            return ""
        
        try:
            if len(backtests) < 2:
                logger.warning("⚠️ Need at least 2 backtests for comparison")
                return ""
            
            # Prepare data
            data = []
            for bt in backtests:
                data.append({
                    'Backtest ID': bt.backtest_id[:8],
                    'Script': bt.script_name[:20],
                    'ROI (%)': bt.roi_percentage,
                    'Win Rate (%)': bt.win_rate * 100,
                    'Total Trades': bt.total_trades,
                    'Profit (USDT)': bt.realized_profits_usdt,
                    'Max DD (%)': bt.max_drawdown
                })
            
            df = pd.DataFrame(data)
            
            # Create subplots
            fig, axes = plt.subplots(2, 2, figsize=(15, 10))
            fig.suptitle('Backtest Performance Comparison', fontsize=16, fontweight='bold')
            
            # ROI comparison
            axes[0, 0].bar(df['Backtest ID'], df['ROI (%)'], color='skyblue', alpha=0.7)
            axes[0, 0].set_title('ROI Comparison', fontweight='bold')
            axes[0, 0].set_ylabel('ROI (%)')
            axes[0, 0].tick_params(axis='x', rotation=45)
            
            # Win Rate comparison
            axes[0, 1].bar(df['Backtest ID'], df['Win Rate (%)'], color='lightgreen', alpha=0.7)
            axes[0, 1].set_title('Win Rate Comparison', fontweight='bold')
            axes[0, 1].set_ylabel('Win Rate (%)')
            axes[0, 1].tick_params(axis='x', rotation=45)
            
            # Risk-Return scatter
            axes[1, 0].scatter(df['Max DD (%)'], df['ROI (%)'], s=100, alpha=0.7, c=df['Total Trades'], cmap='viridis')
            axes[1, 0].set_xlabel('Max Drawdown (%)')
            axes[1, 0].set_ylabel('ROI (%)')
            axes[1, 0].set_title('Risk-Return Analysis', fontweight='bold')
            axes[1, 0].grid(True, alpha=0.3)
            
            # Add labels to scatter points
            for i, row in df.iterrows():
                axes[1, 0].annotate(row['Backtest ID'], (row['Max DD (%)'], row['ROI (%)']), 
                                  xytext=(5, 5), textcoords='offset points', fontsize=8)
            
            # Trade count vs Profit
            axes[1, 1].scatter(df['Total Trades'], df['Profit (USDT)'], s=100, alpha=0.7, c=df['ROI (%)'], cmap='plasma')
            axes[1, 1].set_xlabel('Total Trades')
            axes[1, 1].set_ylabel('Profit (USDT)')
            axes[1, 1].set_title('Trades vs Profit', fontweight='bold')
            axes[1, 1].grid(True, alpha=0.3)
            
            # Add labels to scatter points
            for i, row in df.iterrows():
                axes[1, 1].annotate(row['Backtest ID'], (row['Total Trades'], row['Profit (USDT)']), 
                                  xytext=(5, 5), textcoords='offset points', fontsize=8)
            
            plt.tight_layout()
            
            # Save the plot
            if not save_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                save_path = f"performance_comparison_{timestamp}.png"
            
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"📊 Performance comparison saved: {save_path}")
            return save_path
            
        except Exception as e:
            logger.error(f"❌ Error generating performance comparison: {e}")
            return ""
    
    def generate_risk_analysis(self, backtests: List[BacktestAnalysis], save_path: str = None) -> str:
        """Generate risk analysis charts"""
        if not VISUALIZATION_AVAILABLE:
            logger.error("❌ Visualization libraries not available")
            return ""
        
        try:
            # Prepare data
            data = []
            for bt in backtests:
                # Calculate additional risk metrics
                roe = (bt.realized_profits_usdt / max(bt.starting_balance, 1)) * 100
                dd_usdt = bt.starting_balance - (bt.final_balance - bt.realized_profits_usdt)
                dd_percentage = (dd_usdt / bt.starting_balance) * 100
                
                # Use generation/population if available, otherwise use backtest ID
                gen_pop = f"{bt.generation_idx}/{bt.population_idx}" if bt.generation_idx is not None and bt.population_idx is not None else bt.backtest_id[:8]
                
                data.append({
                    'Gen/Pop': gen_pop,
                    'ROI (%)': bt.roi_percentage,
                    'ROE (%)': roe,
                    'Max DD (%)': bt.max_drawdown,
                    'Win Rate (%)': bt.win_rate * 100,
                    'Total Trades': bt.total_trades,
                    'Profit Factor': bt.profit_factor,
                    'Sharpe Ratio': bt.sharpe_ratio
                })
            
            df = pd.DataFrame(data)
            
            # Create subplots
            fig, axes = plt.subplots(2, 2, figsize=(15, 10))
            fig.suptitle('Risk Analysis Dashboard', fontsize=16, fontweight='bold')
            
            # Risk-Return Matrix (using ROE instead of ROI)
            scatter = axes[0, 0].scatter(df['Max DD (%)'], df['ROE (%)'], 
                                       s=df['Total Trades']*2, 
                                       c=df['Win Rate (%)'], 
                                       cmap='RdYlGn', alpha=0.7)
            axes[0, 0].set_xlabel('Max Drawdown (%)')
            axes[0, 0].set_ylabel('ROE (%)')
            axes[0, 0].set_title('Risk-Return Matrix (ROE)\n(Size = Trades, Color = Win Rate)', fontweight='bold')
            axes[0, 0].grid(True, alpha=0.3)
            
            # Add colorbar
            cbar = plt.colorbar(scatter, ax=axes[0, 0])
            cbar.set_label('Win Rate (%)')
            
            # Win Rate Distribution
            axes[0, 1].hist(df['Win Rate (%)'], bins=10, alpha=0.7, color='lightblue', edgecolor='black')
            axes[0, 1].set_xlabel('Win Rate (%)')
            axes[0, 1].set_ylabel('Frequency')
            axes[0, 1].set_title('Win Rate Distribution', fontweight='bold')
            axes[0, 1].grid(True, alpha=0.3)
            
            # Drawdown Distribution
            axes[1, 0].hist(df['Max DD (%)'], bins=10, alpha=0.7, color='lightcoral', edgecolor='black')
            axes[1, 0].set_xlabel('Max Drawdown (%)')
            axes[1, 0].set_ylabel('Frequency')
            axes[1, 0].set_title('Drawdown Distribution', fontweight='bold')
            axes[1, 0].grid(True, alpha=0.3)
            
            # Performance Metrics Heatmap
            metrics_df = df[['ROI (%)', 'ROE (%)', 'Win Rate (%)', 'Profit Factor', 'Sharpe Ratio']].T
            sns.heatmap(metrics_df, annot=True, fmt='.2f', cmap='RdYlGn', 
                       ax=axes[1, 1], cbar_kws={'label': 'Value'})
            axes[1, 1].set_title('Performance Metrics Heatmap', fontweight='bold')
            axes[1, 1].set_xlabel('Gen/Pop')
            
            plt.tight_layout()
            
            # Save the plot
            if not save_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                save_path = f"risk_analysis_{timestamp}.png"
            
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"📊 Risk analysis saved: {save_path}")
            return save_path
            
        except Exception as e:
            logger.error(f"❌ Error generating risk analysis: {e}")
            return ""
    
    def generate_trade_analysis(self, backtest: BacktestAnalysis, save_path: str = None) -> str:
        """Generate trade analysis charts"""
        if not VISUALIZATION_AVAILABLE:
            logger.error("❌ Visualization libraries not available")
            return ""
        
        try:
            # Load backtest data
            backtest_data = self.cache.load_backtest_cache(backtest.lab_id, backtest.backtest_id)
            if not backtest_data:
                logger.warning(f"⚠️ No cached data for backtest {backtest.backtest_id[:8]}")
                return ""
            
            # Extract trade data
            extractor = BacktestDataExtractor()
            summary = extractor.extract_backtest_summary(backtest_data)
            
            if not summary or not summary.trades:
                logger.warning(f"⚠️ No trade data for backtest {backtest.backtest_id[:8]}")
                return ""
            
            # Prepare trade data
            trades = summary.trades
            pnl_values = [trade.net_pnl for trade in trades]
            win_trades = [pnl for pnl in pnl_values if pnl > 0]
            loss_trades = [pnl for pnl in pnl_values if pnl < 0]
            
            # Create subplots
            fig, axes = plt.subplots(2, 2, figsize=(15, 10))
            fig.suptitle(f'Trade Analysis - {backtest.script_name}\nBacktest: {backtest.backtest_id[:12]}', 
                        fontsize=16, fontweight='bold')
            
            # P&L Distribution
            axes[0, 0].hist(pnl_values, bins=30, alpha=0.7, color='lightblue', edgecolor='black')
            axes[0, 0].axvline(x=0, color='red', linestyle='--', alpha=0.7)
            axes[0, 0].set_xlabel('P&L (USDT)')
            axes[0, 0].set_ylabel('Frequency')
            axes[0, 0].set_title('P&L Distribution', fontweight='bold')
            axes[0, 0].grid(True, alpha=0.3)
            
            # Win vs Loss Trades
            win_loss_data = [len(win_trades), len(loss_trades)]
            labels = ['Winning Trades', 'Losing Trades']
            colors = ['lightgreen', 'lightcoral']
            axes[0, 1].pie(win_loss_data, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
            axes[0, 1].set_title('Win/Loss Trade Ratio', fontweight='bold')
            
            # Trade Size Distribution
            trade_sizes = [abs(trade.net_pnl) for trade in trades]
            axes[1, 0].hist(trade_sizes, bins=20, alpha=0.7, color='orange', edgecolor='black')
            axes[1, 0].set_xlabel('Trade Size (USDT)')
            axes[1, 0].set_ylabel('Frequency')
            axes[1, 0].set_title('Trade Size Distribution', fontweight='bold')
            axes[1, 0].grid(True, alpha=0.3)
            
            # Cumulative P&L over time
            cumulative_pnl = np.cumsum(pnl_values)
            trade_numbers = range(1, len(cumulative_pnl) + 1)
            axes[1, 1].plot(trade_numbers, cumulative_pnl, linewidth=2, color='blue', alpha=0.8)
            axes[1, 1].axhline(y=0, color='red', linestyle='--', alpha=0.5)
            axes[1, 1].set_xlabel('Trade Number')
            axes[1, 1].set_ylabel('Cumulative P&L (USDT)')
            axes[1, 1].set_title('Cumulative P&L Over Time', fontweight='bold')
            axes[1, 1].grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            # Save the plot
            if not save_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                save_path = f"trade_analysis_{backtest.backtest_id[:8]}_{timestamp}.png"
            
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"📊 Trade analysis saved: {save_path}")
            return save_path
            
        except Exception as e:
            logger.error(f"❌ Error generating trade analysis: {e}")
            return ""
    
    def generate_all_charts(self, backtests: List[BacktestAnalysis], output_dir: str = None) -> List[str]:
        """Generate all available charts for backtests"""
        if not VISUALIZATION_AVAILABLE:
            logger.error("❌ Visualization libraries not available")
            return []
        
        if not output_dir:
            output_dir = self.cache.base_dir / "charts"
            output_dir.mkdir(exist_ok=True)
        
        generated_charts = []
        
        try:
            # Generate performance comparison
            if len(backtests) > 1:
                comp_path = self.generate_performance_comparison(backtests, 
                    str(output_dir / f"performance_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"))
                if comp_path:
                    generated_charts.append(comp_path)
            
            # Generate risk analysis
            risk_path = self.generate_risk_analysis(backtests,
                str(output_dir / f"risk_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"))
            if risk_path:
                generated_charts.append(risk_path)
            
            # Generate individual charts for top backtests
            for i, bt in enumerate(backtests[:5]):  # Limit to top 5
                # Equity curve
                equity_path = self.generate_equity_curve(bt,
                    str(output_dir / f"equity_curve_{bt.backtest_id[:8]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"))
                if equity_path:
                    generated_charts.append(equity_path)
                
                # Trade analysis
                trade_path = self.generate_trade_analysis(bt,
                    str(output_dir / f"trade_analysis_{bt.backtest_id[:8]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"))
                if trade_path:
                    generated_charts.append(trade_path)
            
            logger.info(f"📊 Generated {len(generated_charts)} charts in {output_dir}")
            return generated_charts
            
        except Exception as e:
            logger.error(f"❌ Error generating charts: {e}")
            return []


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Visualization Tool - Generate charts and graphs for backtest analysis',
        epilog='''
Examples:
  # Generate charts for all cached labs
  python -m pyHaasAPI.cli.visualization_tool --all-labs
  
  # Generate charts for specific labs
  python -m pyHaasAPI.cli.visualization_tool --lab-ids lab1,lab2
  
  # Generate charts for specific backtests
  python -m pyHaasAPI.cli.visualization_tool --backtest-ids bt1,bt2,bt3
        ''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--lab-ids', nargs='+', type=str,
                       help='Generate charts for specific lab IDs')
    parser.add_argument('--backtest-ids', nargs='+', type=str,
                       help='Generate charts for specific backtest IDs')
    parser.add_argument('--all-labs', action='store_true',
                       help='Generate charts for all cached labs')
    parser.add_argument('--output-dir', type=str,
                       help='Output directory for charts (default: cache/charts)')
    parser.add_argument('--top-count', type=int, default=10,
                       help='Number of top backtests to analyze per lab (default: 10)')
    
    args = parser.parse_args()
    
    if not VISUALIZATION_AVAILABLE:
        logger.error("❌ Visualization libraries not available")
        logger.info("💡 Install required packages: pip install matplotlib seaborn pandas numpy")
        sys.exit(1)
    
    try:
        tool = VisualizationTool()
        
        if not tool.connect():
            sys.exit(1)
        
        # Get backtests to analyze
        backtests = []
        
        if args.backtest_ids:
            # Load specific backtests
            for bt_id in args.backtest_ids:
                # Find the backtest in cached data
                cache_dir = tool.cache.base_dir / "backtests"
                for cache_file in cache_dir.glob("*.json"):
                    if bt_id in cache_file.name:
                        # Extract lab_id from filename
                        lab_id = cache_file.name.split('_')[0]
                        # Create a minimal BacktestAnalysis object
                        bt = BacktestAnalysis(
                            backtest_id=bt_id,
                            lab_id=lab_id,
                            generation_idx=None,
                            population_idx=None,
                            market_tag="",
                            script_id="",
                            script_name="",
                            roi_percentage=0,
                            calculated_roi_percentage=0,
                            roi_difference=0,
                            win_rate=0,
                            total_trades=0,
                            max_drawdown=0,
                            realized_profits_usdt=0,
                            pc_value=0,
                            avg_profit_per_trade=0,
                            profit_factor=0,
                            sharpe_ratio=0,
                            starting_balance=0,
                            final_balance=0,
                            peak_balance=0,
                            analysis_timestamp=""
                        )
                        backtests.append(bt)
                        break
        
        elif args.lab_ids or args.all_labs:
            # Analyze labs to get backtests
            if args.all_labs:
                lab_ids = tool.get_cached_labs()
            else:
                lab_ids = args.lab_ids
            
            for lab_id in lab_ids:
                result = tool.analyzer.analyze_lab(lab_id, top_count=args.top_count)
                if result:
                    backtests.extend(result.top_backtests)
        
        if not backtests:
            logger.warning("⚠️ No backtests found for chart generation")
            sys.exit(1)
        
        logger.info(f"📊 Generating charts for {len(backtests)} backtests")
        
        # Generate all charts
        generated_charts = tool.generate_all_charts(backtests, args.output_dir)
        
        if generated_charts:
            logger.info(f"✅ Generated {len(generated_charts)} charts successfully")
            for chart in generated_charts:
                logger.info(f"   📊 {chart}")
        else:
            logger.warning("⚠️ No charts were generated")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("\n❌ Chart generation interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
