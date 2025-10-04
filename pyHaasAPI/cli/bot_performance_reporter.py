"""
Bot Performance Reporter CLI for pyHaasAPI

This module provides comprehensive bot performance reporting with JSON/CSV export
capabilities for live trading bots across multiple servers.

Features:
- Real-time bot performance metrics extraction
- Realized/Unrealized profit tracking
- Trade statistics and performance analytics
- Maximum drawdown calculation
- Win rate, profit factor, Sharpe ratio
- Multi-server support via existing server manager
- JSON/CSV export for pipeline integration
"""

import asyncio
import argparse
import json
import csv
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass, asdict

from ..core.logging import get_logger
from ..core.server_manager import ServerManager
from ..api.bot.bot_api import BotAPI
from ..api.account.account_api import AccountAPI
from ..core.auth import AuthenticationManager
from ..models.bot import BotDetails, BotRuntimeData
from ..exceptions import BotError, APIError

logger = get_logger("bot_performance_reporter")


@dataclass
class BotPerformanceMetrics:
    """Comprehensive bot performance metrics"""
    bot_id: str
    bot_name: str
    server: str
    status: str
    market_tag: str
    account_id: str
    leverage: float
    trade_amount: float
    
    # Performance Metrics
    realized_profit: float
    unrealized_profit: float
    total_profit: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    profit_factor: float
    sharpe_ratio: float
    max_drawdown: float
    max_drawdown_percentage: float
    
    # Account Metrics
    starting_balance: float
    current_balance: float
    account_balance: float
    
    # Risk Metrics
    total_exposure: float
    open_positions: int
    active_orders: int
    
    # Time Metrics
    uptime_hours: float
    last_trade_time: Optional[str]
    report_timestamp: str


class BotPerformanceReporter:
    """
    Comprehensive bot performance reporter with multi-server support.
    
    Extracts detailed performance metrics from live trading bots and exports
    to JSON/CSV formats for pipeline integration.
    """
    
    def __init__(self):
        self.logger = get_logger("bot_performance_reporter")
        self.server_manager = ServerManager()
        self.bot_apis = {}
        self.account_apis = {}
        self.auth_managers = {}
        
    async def connect_to_servers(self, servers: List[str]) -> bool:
        """Connect to specified servers using existing server manager"""
        try:
            self.logger.info(f"Connecting to servers: {servers}")
            
            for server in servers:
                # Connect to server
                await self.server_manager.connect_to_server(server)
                
                # Create API clients for this server
                client = self.server_manager.get_client(server)
                auth_manager = AuthenticationManager(
                    email=client.email,
                    password=client.password
                )
                await auth_manager.authenticate()
                
                self.auth_managers[server] = auth_manager
                self.bot_apis[server] = BotAPI(client)
                self.account_apis[server] = AccountAPI(client)
                
                self.logger.info(f"✅ Connected to {server}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to servers: {e}")
            return False
    
    async def get_all_bots_performance(self, servers: List[str]) -> List[BotPerformanceMetrics]:
        """Get comprehensive performance metrics for all bots across servers"""
        all_metrics = []
        
        for server in servers:
            try:
                self.logger.info(f"📊 Extracting bot performance from {server}")
                
                # Get all bots from this server
                bots = await self.bot_apis[server].get_all_bots()
                
                for bot in bots:
                    try:
                        metrics = await self._extract_bot_metrics(bot, server)
                        if metrics:
                            all_metrics.append(metrics)
                    except Exception as e:
                        self.logger.warning(f"Failed to extract metrics for bot {bot.bot_id} on {server}: {e}")
                        continue
                        
            except Exception as e:
                self.logger.error(f"Failed to get bots from {server}: {e}")
                continue
        
        self.logger.info(f"📈 Extracted performance metrics for {len(all_metrics)} bots")
        return all_metrics
    
    async def _extract_bot_metrics(self, bot: BotDetails, server: str) -> Optional[BotPerformanceMetrics]:
        """Extract comprehensive performance metrics for a single bot"""
        try:
            # Get detailed bot runtime data
            runtime_data = await self.bot_apis[server].get_full_bot_runtime_data(bot.bot_id)
            
            # Get account balance
            account_balance = await self.account_apis[server].get_account_balance(bot.account_id)
            
            # Get bot orders and positions for detailed metrics
            orders = await self.bot_apis[server].get_bot_orders(bot.bot_id)
            positions = await self.bot_apis[server].get_bot_positions(bot.bot_id)
            
            # Calculate performance metrics
            metrics = self._calculate_performance_metrics(
                bot, runtime_data, orders, positions, account_balance, server
            )
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Failed to extract metrics for bot {bot.bot_id}: {e}")
            return None
    
    def _calculate_performance_metrics(
        self, 
        bot: BotDetails, 
        runtime_data: BotRuntimeData, 
        orders: List[Dict], 
        positions: List[Dict], 
        account_balance: float,
        server: str
    ) -> BotPerformanceMetrics:
        """Calculate comprehensive performance metrics from bot data"""
        
        # Basic trade statistics
        total_trades = len(orders)
        winning_trades = sum(1 for order in orders if order.get('profit_loss', 0) > 0)
        losing_trades = sum(1 for order in orders if order.get('profit_loss', 0) < 0)
        
        # Calculate win rate
        win_rate = (winning_trades / total_trades) if total_trades > 0 else 0.0
        
        # PnL calculations
        realized_profit = sum(order.get('realized_pnl', 0) for order in orders)
        unrealized_profit = sum(pos.get('unrealized_pnl', 0) for pos in positions)
        total_profit = realized_profit + unrealized_profit
        
        # Account metrics
        starting_balance = getattr(runtime_data, 'starting_balance', 10000.0)
        current_balance = account_balance
        
        # Calculate profit factor
        gross_profit = sum(order.get('profit_loss', 0) for order in orders if order.get('profit_loss', 0) > 0)
        gross_loss = abs(sum(order.get('profit_loss', 0) for order in orders if order.get('profit_loss', 0) < 0))
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else 0.0
        
        # Calculate Sharpe ratio (simplified)
        if total_trades > 1:
            trade_returns = [order.get('profit_loss', 0) for order in orders]
            avg_return = sum(trade_returns) / len(trade_returns)
            variance = sum((r - avg_return) ** 2 for r in trade_returns) / len(trade_returns)
            std_dev = variance ** 0.5
            sharpe_ratio = (avg_return / std_dev) if std_dev > 0 else 0.0
        else:
            sharpe_ratio = 0.0
        
        # Calculate maximum drawdown
        max_drawdown, max_drawdown_pct = self._calculate_max_drawdown(orders, starting_balance)
        
        # Position and order metrics
        open_positions = len(positions)
        active_orders = sum(1 for order in orders if order.get('status') in ['NEW', 'PARTIALLY_FILLED'])
        
        # Calculate total exposure
        total_exposure = sum(pos.get('size', 0) * pos.get('entry_price', 0) for pos in positions)
        
        # Time metrics
        uptime_hours = self._calculate_uptime_hours(bot.created_at)
        last_trade_time = self._get_last_trade_time(orders)
        
        return BotPerformanceMetrics(
            bot_id=bot.bot_id,
            bot_name=bot.bot_name,
            server=server,
            status=bot.status,
            market_tag=bot.market_tag,
            account_id=bot.account_id,
            leverage=bot.leverage,
            trade_amount=bot.trade_amount,
            
            # Performance Metrics
            realized_profit=realized_profit,
            unrealized_profit=unrealized_profit,
            total_profit=total_profit,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            profit_factor=profit_factor,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            max_drawdown_percentage=max_drawdown_pct,
            
            # Account Metrics
            starting_balance=starting_balance,
            current_balance=current_balance,
            account_balance=account_balance,
            
            # Risk Metrics
            total_exposure=total_exposure,
            open_positions=open_positions,
            active_orders=active_orders,
            
            # Time Metrics
            uptime_hours=uptime_hours,
            last_trade_time=last_trade_time,
            report_timestamp=datetime.now().isoformat()
        )
    
    def _calculate_max_drawdown(self, orders: List[Dict], starting_balance: float) -> tuple[float, float]:
        """Calculate maximum drawdown from trade history"""
        if not orders:
            return 0.0, 0.0
        
        # Sort orders by timestamp
        sorted_orders = sorted(orders, key=lambda x: x.get('timestamp', 0))
        
        # Calculate running balance
        running_balance = starting_balance
        peak_balance = starting_balance
        max_drawdown = 0.0
        max_drawdown_pct = 0.0
        
        for order in sorted_orders:
            running_balance += order.get('profit_loss', 0)
            
            if running_balance > peak_balance:
                peak_balance = running_balance
            
            drawdown = peak_balance - running_balance
            if drawdown > max_drawdown:
                max_drawdown = drawdown
                max_drawdown_pct = (drawdown / peak_balance) * 100 if peak_balance > 0 else 0.0
        
        return max_drawdown, max_drawdown_pct
    
    def _calculate_uptime_hours(self, created_at: datetime) -> float:
        """Calculate bot uptime in hours"""
        if not created_at:
            return 0.0
        
        uptime = datetime.now() - created_at
        return uptime.total_seconds() / 3600.0
    
    def _get_last_trade_time(self, orders: List[Dict]) -> Optional[str]:
        """Get timestamp of last trade"""
        if not orders:
            return None
        
        # Find most recent order
        last_order = max(orders, key=lambda x: x.get('timestamp', 0))
        timestamp = last_order.get('timestamp')
        
        if timestamp:
            return datetime.fromtimestamp(timestamp).isoformat()
        return None
    
    def export_to_json(self, metrics: List[BotPerformanceMetrics], output_file: str) -> None:
        """Export metrics to JSON file"""
        try:
            data = {
                "report_timestamp": datetime.now().isoformat(),
                "total_bots": len(metrics),
                "servers": list(set(m.server for m in metrics)),
                "metrics": [asdict(m) for m in metrics]
            }
            
            with open(output_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            self.logger.info(f"📄 Exported {len(metrics)} bot metrics to {output_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to export JSON: {e}")
            raise
    
    def export_to_csv(self, metrics: List[BotPerformanceMetrics], output_file: str) -> None:
        """Export metrics to CSV file"""
        try:
            if not metrics:
                self.logger.warning("No metrics to export")
                return
            
            fieldnames = list(asdict(metrics[0]).keys())
            
            with open(output_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for metric in metrics:
                    writer.writerow(asdict(metric))
            
            self.logger.info(f"📊 Exported {len(metrics)} bot metrics to {output_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to export CSV: {e}")
            raise
    
    def print_summary(self, metrics: List[BotPerformanceMetrics]) -> None:
        """Print performance summary to console"""
        if not metrics:
            print("No bot performance data available")
            return
        
        # Calculate summary statistics
        total_bots = len(metrics)
        active_bots = sum(1 for m in metrics if m.status == 'ACTIVE')
        total_profit = sum(m.total_profit for m in metrics)
        avg_win_rate = sum(m.win_rate for m in metrics) / total_bots if total_bots > 0 else 0
        
        print(f"\n🤖 Bot Performance Summary")
        print(f"{'='*60}")
        print(f"Total Bots: {total_bots}")
        print(f"Active Bots: {active_bots}")
        print(f"Total Profit: ${total_profit:,.2f}")
        print(f"Average Win Rate: {avg_win_rate:.1%}")
        print(f"Servers: {', '.join(set(m.server for m in metrics))}")
        print(f"{'='*60}")
        
        # Top performers
        top_profit = sorted(metrics, key=lambda x: x.total_profit, reverse=True)[:5]
        print(f"\n🏆 Top 5 Performers by Profit:")
        print(f"{'Bot Name':<30} {'Server':<10} {'Profit':<12} {'Win Rate':<10}")
        print(f"{'-'*65}")
        for bot in top_profit:
            print(f"{bot.bot_name[:30]:<30} {bot.server:<10} ${bot.total_profit:<11,.2f} {bot.win_rate:<9.1%}")


async def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Bot Performance Reporter - Extract comprehensive bot performance metrics",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Export all bot metrics to JSON
  python -m pyHaasAPI.cli.bot_performance_reporter --servers srv01,srv02,srv03 --format json --output bot_metrics.json
  
  # Export active bots only to CSV
  python -m pyHaasAPI.cli.bot_performance_reporter --servers srv01,srv02 --format csv --output active_bots.csv --status active
  
  # Export with filtering
  python -m pyHaasAPI.cli.bot_performance_reporter --servers srv01 --format json --min-profit 100 --sort-by profit
        """
    )
    
    parser.add_argument('--servers', required=True, help='Comma-separated list of servers (e.g., srv01,srv02,srv03)')
    parser.add_argument('--format', choices=['json', 'csv'], default='json', help='Output format')
    parser.add_argument('--output', required=True, help='Output file path')
    parser.add_argument('--status', choices=['ACTIVE', 'INACTIVE', 'PAUSED'], help='Filter by bot status')
    parser.add_argument('--min-profit', type=float, help='Filter bots with minimum profit')
    parser.add_argument('--min-trades', type=int, help='Filter bots with minimum trades')
    parser.add_argument('--sort-by', choices=['profit', 'winrate', 'trades', 'drawdown'], help='Sort results')
    parser.add_argument('--limit', type=int, help='Limit number of results')
    parser.add_argument('--summary', action='store_true', help='Print summary to console')
    
    args = parser.parse_args()
    
    try:
        # Initialize reporter
        reporter = BotPerformanceReporter()
        
        # Parse servers
        servers = [s.strip() for s in args.servers.split(',')]
        
        # Connect to servers
        if not await reporter.connect_to_servers(servers):
            logger.error("Failed to connect to servers")
            return 1
        
        # Get bot performance metrics
        logger.info("📊 Extracting bot performance metrics...")
        metrics = await reporter.get_all_bots_performance(servers)
        
        if not metrics:
            logger.warning("No bot performance data found")
            return 0
        
        # Apply filters
        if args.status:
            metrics = [m for m in metrics if m.status == args.status]
        
        if args.min_profit is not None:
            metrics = [m for m in metrics if m.total_profit >= args.min_profit]
        
        if args.min_trades is not None:
            metrics = [m for m in metrics if m.total_trades >= args.min_trades]
        
        # Apply sorting
        if args.sort_by == 'profit':
            metrics.sort(key=lambda x: x.total_profit, reverse=True)
        elif args.sort_by == 'winrate':
            metrics.sort(key=lambda x: x.win_rate, reverse=True)
        elif args.sort_by == 'trades':
            metrics.sort(key=lambda x: x.total_trades, reverse=True)
        elif args.sort_by == 'drawdown':
            metrics.sort(key=lambda x: x.max_drawdown_percentage)
        
        # Apply limit
        if args.limit:
            metrics = metrics[:args.limit]
        
        # Export data
        if args.format == 'json':
            reporter.export_to_json(metrics, args.output)
        elif args.format == 'csv':
            reporter.export_to_csv(metrics, args.output)
        
        # Print summary if requested
        if args.summary:
            reporter.print_summary(metrics)
        
        logger.info(f"✅ Successfully exported {len(metrics)} bot metrics to {args.output}")
        return 0
        
    except Exception as e:
        logger.error(f"Bot performance reporter failed: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)



