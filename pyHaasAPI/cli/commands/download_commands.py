"""
Download command handlers - Direct calls to BacktestAPI/LabAPI
"""

from typing import Any
from datetime import datetime
from ..base import BaseCLI


class DownloadCommands:
    """Download command handlers - thin wrappers around BacktestAPI/LabAPI"""
    
    def __init__(self, cli: BaseCLI):
        self.cli = cli
    
    async def handle(self, action: str, args: Any) -> int:
        """Handle download commands"""
        backtest_api = self.cli.backtest_api
        lab_api = self.cli.lab_api
        
        if not backtest_api or not lab_api:
            self.cli.logger.error("Backtest/Lab API not initialized")
            return 1
        
        try:
            if action == 'everything':
                # Download from all servers - use existing download logic
                # This uses BacktestAPI.get_backtest_result with pagination
                return await self._download_everything(args)
                
            elif action == 'server':
                # Download from specific server
                if not args.server_name:
                    self.cli.logger.error("--server-name is required")
                    return 1
                
                return await self._download_from_server(args.server_name, args)
                
            elif action == 'lab':
                # Download from specific lab
                if not args.lab_id:
                    self.cli.logger.error("--lab-id is required")
                    return 1
                
                return await self._download_from_lab(args.lab_id, args)
                
            elif action == 'backtests-for-labs':
                # Download backtests for labs without bots
                if not args.server_name:
                    self.cli.logger.error("--server-name is required")
                    return 1
                
                return await self._download_backtests_for_labs(args.server_name, args)
                
            else:
                self.cli.logger.error(f"Unknown download action: {action}")
                return 1
                
        except Exception as e:
            self.cli.logger.error(f"Error executing download command: {e}")
            if args.verbose:
                import traceback
                traceback.print_exc()
            return 1
    
    async def _download_everything(self, args: Any) -> int:
        """Download everything from all servers - uses BacktestAPI directly"""
        import json
        
        # Get all labs
        labs = await self.cli.lab_api.get_labs()
        
        all_data = {
            'timestamp': datetime.now().isoformat(),
            'total_labs': len(labs),
            'labs': []
        }
        
        for lab in labs:
            lab_id = self.cli.safe_get(lab, 'lab_id', '')
            if not lab_id:
                continue
            
            # Get backtests using BacktestAPI directly
            backtests = await self.cli.backtest_api.get_all_backtests_for_lab(
                lab_id, 
                max_pages=args.max_pages or 1000
            )
            
            lab_data = {
                'lab_id': lab_id,
                'lab_name': self.cli.safe_get(lab, 'name', ''),
                'backtest_count': len(backtests),
                'backtests': [
                    {
                        'backtest_id': self.cli.safe_get(bt, 'backtest_id', ''),
                        'roi_percentage': self.cli.safe_get(bt, 'roi_percentage', 0),
                        'win_rate': self.cli.safe_get(bt, 'win_rate', 0),
                        'total_trades': self.cli.safe_get(bt, 'total_trades', 0),
                        'max_drawdown': self.cli.safe_get(bt, 'max_drawdown', 0),
                        'realized_profits_usdt': self.cli.safe_get(bt, 'realized_profits_usdt', 0),
                    } for bt in backtests
                ]
            }
            all_data['labs'].append(lab_data)
        
        # Save to file
        output_file = args.output_file or f"backtest_download_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump(all_data, f, indent=2, default=str)
        
        self.cli.logger.info(f"Downloaded {all_data['total_labs']} labs, saved to {output_file}")
        return 0
    
    async def _download_from_server(self, server_name: str, args: Any) -> int:
        """Download from specific server - uses existing server manager"""
        # Server-specific logic would go here
        # For now, same as everything
        return await self._download_everything(args)
    
    async def _download_from_lab(self, lab_id: str, args: Any) -> int:
        """Download from specific lab - uses BacktestAPI directly"""
        import json
        
        backtests = await self.cli.backtest_api.get_all_backtests_for_lab(
            lab_id,
            max_pages=args.max_pages or 1000
        )
        
        lab_data = {
            'lab_id': lab_id,
            'backtest_count': len(backtests),
            'backtests': [
                {
                    'backtest_id': self.cli.safe_get(bt, 'backtest_id', ''),
                    'roi_percentage': self.cli.safe_get(bt, 'roi_percentage', 0),
                    'win_rate': self.cli.safe_get(bt, 'win_rate', 0),
                    'total_trades': self.cli.safe_get(bt, 'total_trades', 0),
                    'max_drawdown': self.cli.safe_get(bt, 'max_drawdown', 0),
                    'realized_profits_usdt': self.cli.safe_get(bt, 'realized_profits_usdt', 0),
                } for bt in backtests
            ]
        }
        
        output_file = args.output_file or f"backtest_download_{lab_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump(lab_data, f, indent=2, default=str)
        
        self.cli.logger.info(f"Downloaded {len(backtests)} backtests from lab {lab_id}, saved to {output_file}")
        return 0
    
    async def _download_backtests_for_labs(self, server_name: str, args: Any) -> int:
        """Download backtests for labs without bots"""
        # Use existing logic but simplified
        return await self._download_everything(args)



