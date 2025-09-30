"""
Data Dumper for pyHaasAPI v2

Provides functionality for dumping any endpoint data to JSON/CSV
for API exploration and testing as requested by the user.
"""

import json
import csv
import asyncio
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from ..api.lab import LabAPI
from ..api.bot import BotAPI
from ..api.account import AccountAPI
from ..api.script import ScriptAPI
from ..api.market import MarketAPI
from ..api.backtest import BacktestAPI
from ..api.order import OrderAPI
from ..exceptions import AnalysisError
from ..core.logging import get_logger


class DumpFormat(Enum):
    """Data dump format options"""
    JSON = "json"
    CSV = "csv"
    BOTH = "both"


@dataclass
class DumpConfig:
    """Configuration for data dumping"""
    format: DumpFormat = DumpFormat.JSON
    output_directory: str = "dumps"
    include_metadata: bool = True
    pretty_print: bool = True
    max_records: Optional[int] = None
    filter_conditions: Optional[Dict[str, Any]] = None
    filename_template: str = "{endpoint}_{timestamp}"


class DataDumper:
    """
    Data Dumper for exporting endpoint data
    
    Provides functionality for dumping any endpoint data to JSON/CSV
    for API exploration and testing as requested by the user.
    """
    
    def __init__(
        self,
        lab_api: LabAPI,
        bot_api: BotAPI,
        account_api: AccountAPI,
        script_api: ScriptAPI,
        market_api: MarketAPI,
        backtest_api: BacktestAPI,
        order_api: OrderAPI
    ):
        self.lab_api = lab_api
        self.bot_api = bot_api
        self.account_api = account_api
        self.script_api = script_api
        self.market_api = market_api
        self.backtest_api = backtest_api
        self.order_api = order_api
        self.logger = get_logger("data_dumper")
    
    async def dump_all_endpoints(self, config: DumpConfig) -> Dict[str, str]:
        """
        Dump data from all available endpoints
        
        Args:
            config: Dump configuration
            
        Returns:
            Dictionary mapping endpoint names to output file paths
        """
        try:
            self.logger.info("Starting comprehensive endpoint data dump")
            
            results = {}
            
            # Dump labs data
            results["labs"] = await self.dump_labs_data(config)
            
            # Dump bots data
            results["bots"] = await self.dump_bots_data(config)
            
            # Dump accounts data
            results["accounts"] = await self.dump_accounts_data(config)
            
            # Dump scripts data
            results["scripts"] = await self.dump_scripts_data(config)
            
            # Dump markets data
            results["markets"] = await self.dump_markets_data(config)
            
            # Dump backtests data (for each lab)
            results["backtests"] = await self.dump_backtests_data(config)
            
            # Dump orders data
            results["orders"] = await self.dump_orders_data(config)
            
            self.logger.info(f"Completed comprehensive endpoint data dump: {len(results)} endpoints")
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to dump all endpoints: {e}")
            raise AnalysisError(f"Failed to dump all endpoints: {e}")
    
    async def dump_labs_data(self, config: DumpConfig) -> str:
        """Dump labs endpoint data"""
        try:
            self.logger.info("Dumping labs data")
            
            # Get all labs
            labs = await self.lab_api.get_labs()
            
            # Apply filters if specified
            filtered_labs = self._apply_filters(labs, config.filter_conditions)
            
            # Limit records if specified
            if config.max_records:
                filtered_labs = filtered_labs[:config.max_records]
            
            # Prepare data
            data = {
                "endpoint": "labs",
                "total_records": len(filtered_labs),
                "dumped_at": datetime.now().isoformat(),
                "data": filtered_labs
            }
            
            # Save to file
            return await self._save_dump(data, "labs", config)
            
        except Exception as e:
            self.logger.error(f"Failed to dump labs data: {e}")
            raise AnalysisError(f"Failed to dump labs data: {e}")
    
    async def dump_bots_data(self, config: DumpConfig) -> str:
        """Dump bots endpoint data"""
        try:
            self.logger.info("Dumping bots data")
            
            # Get all bots
            bots = await self.bot_api.get_all_bots()
            
            # Apply filters if specified
            filtered_bots = self._apply_filters(bots, config.filter_conditions)
            
            # Limit records if specified
            if config.max_records:
                filtered_bots = filtered_bots[:config.max_records]
            
            # Prepare data
            data = {
                "endpoint": "bots",
                "total_records": len(filtered_bots),
                "dumped_at": datetime.now().isoformat(),
                "data": filtered_bots
            }
            
            # Save to file
            return await self._save_dump(data, "bots", config)
            
        except Exception as e:
            self.logger.error(f"Failed to dump bots data: {e}")
            raise AnalysisError(f"Failed to dump bots data: {e}")
    
    async def dump_accounts_data(self, config: DumpConfig) -> str:
        """Dump accounts endpoint data"""
        try:
            self.logger.info("Dumping accounts data")
            
            # Get all accounts
            accounts = await self.account_api.get_accounts()
            
            # Apply filters if specified
            filtered_accounts = self._apply_filters(accounts, config.filter_conditions)
            
            # Limit records if specified
            if config.max_records:
                filtered_accounts = filtered_accounts[:config.max_records]
            
            # Prepare data
            data = {
                "endpoint": "accounts",
                "total_records": len(filtered_accounts),
                "dumped_at": datetime.now().isoformat(),
                "data": filtered_accounts
            }
            
            # Save to file
            return await self._save_dump(data, "accounts", config)
            
        except Exception as e:
            self.logger.error(f"Failed to dump accounts data: {e}")
            raise AnalysisError(f"Failed to dump accounts data: {e}")
    
    async def dump_scripts_data(self, config: DumpConfig) -> str:
        """Dump scripts endpoint data"""
        try:
            self.logger.info("Dumping scripts data")
            
            # Get all scripts
            scripts = await self.script_api.get_all_scripts()
            
            # Apply filters if specified
            filtered_scripts = self._apply_filters(scripts, config.filter_conditions)
            
            # Limit records if specified
            if config.max_records:
                filtered_scripts = filtered_scripts[:config.max_records]
            
            # Prepare data
            data = {
                "endpoint": "scripts",
                "total_records": len(filtered_scripts),
                "dumped_at": datetime.now().isoformat(),
                "data": filtered_scripts
            }
            
            # Save to file
            return await self._save_dump(data, "scripts", config)
            
        except Exception as e:
            self.logger.error(f"Failed to dump scripts data: {e}")
            raise AnalysisError(f"Failed to dump scripts data: {e}")
    
    async def dump_markets_data(self, config: DumpConfig) -> str:
        """Dump markets endpoint data"""
        try:
            self.logger.info("Dumping markets data")
            
            # Get all markets
            markets = await self.market_api.get_all_markets()
            
            # Apply filters if specified
            filtered_markets = self._apply_filters(markets, config.filter_conditions)
            
            # Limit records if specified
            if config.max_records:
                filtered_markets = filtered_markets[:config.max_records]
            
            # Prepare data
            data = {
                "endpoint": "markets",
                "total_records": len(filtered_markets),
                "dumped_at": datetime.now().isoformat(),
                "data": filtered_markets
            }
            
            # Save to file
            return await self._save_dump(data, "markets", config)
            
        except Exception as e:
            self.logger.error(f"Failed to dump markets data: {e}")
            raise AnalysisError(f"Failed to dump markets data: {e}")
    
    async def dump_backtests_data(self, config: DumpConfig) -> str:
        """Dump backtests data for all labs"""
        try:
            self.logger.info("Dumping backtests data")
            
            # Get all labs first
            labs = await self.lab_api.get_labs()
            
            all_backtests = []
            
            # Get backtests for each lab
            for lab in labs:
                try:
                    backtests = await self.backtest_api.get_all_backtests_for_lab(lab.lab_id)
                    for backtest in backtests:
                        backtest["lab_id"] = lab.lab_id
                        backtest["lab_name"] = lab.name
                    all_backtests.extend(backtests)
                except Exception as e:
                    self.logger.warning(f"Failed to get backtests for lab {lab.lab_id}: {e}")
                    continue
            
            # Apply filters if specified
            filtered_backtests = self._apply_filters(all_backtests, config.filter_conditions)
            
            # Limit records if specified
            if config.max_records:
                filtered_backtests = filtered_backtests[:config.max_records]
            
            # Prepare data
            data = {
                "endpoint": "backtests",
                "total_records": len(filtered_backtests),
                "dumped_at": datetime.now().isoformat(),
                "data": filtered_backtests
            }
            
            # Save to file
            return await self._save_dump(data, "backtests", config)
            
        except Exception as e:
            self.logger.error(f"Failed to dump backtests data: {e}")
            raise AnalysisError(f"Failed to dump backtests data: {e}")
    
    async def dump_orders_data(self, config: DumpConfig) -> str:
        """Dump orders endpoint data"""
        try:
            self.logger.info("Dumping orders data")
            
            # Get all orders
            orders = await self.order_api.get_all_orders()
            
            # Apply filters if specified
            filtered_orders = self._apply_filters(orders, config.filter_conditions)
            
            # Limit records if specified
            if config.max_records:
                filtered_orders = filtered_orders[:config.max_records]
            
            # Prepare data
            data = {
                "endpoint": "orders",
                "total_records": len(filtered_orders),
                "dumped_at": datetime.now().isoformat(),
                "data": filtered_orders
            }
            
            # Save to file
            return await self._save_dump(data, "orders", config)
            
        except Exception as e:
            self.logger.error(f"Failed to dump orders data: {e}")
            raise AnalysisError(f"Failed to dump orders data: {e}")
    
    async def dump_specific_lab_data(self, lab_id: str, config: DumpConfig) -> str:
        """Dump specific lab data including backtests"""
        try:
            self.logger.info(f"Dumping specific lab data: {lab_id}")
            
            # Get lab details
            lab_details = await self.lab_api.get_lab_details(lab_id)
            
            # Get lab backtests
            backtests = await self.backtest_api.get_all_backtests_for_lab(lab_id)
            
            # Prepare comprehensive data
            data = {
                "endpoint": f"lab_{lab_id}",
                "lab_details": lab_details,
                "backtests": backtests,
                "total_backtests": len(backtests),
                "dumped_at": datetime.now().isoformat()
            }
            
            # Save to file
            return await self._save_dump(data, f"lab_{lab_id}", config)
            
        except Exception as e:
            self.logger.error(f"Failed to dump specific lab data: {e}")
            raise AnalysisError(f"Failed to dump specific lab data: {e}")
    
    async def dump_specific_bot_data(self, bot_id: str, config: DumpConfig) -> str:
        """Dump specific bot data including orders and positions"""
        try:
            self.logger.info(f"Dumping specific bot data: {bot_id}")
            
            # Get bot details
            bot_details = await self.bot_api.get_bot_details(bot_id)
            
            # Get bot orders
            orders = await self.bot_api.get_bot_orders(bot_id)
            
            # Get bot positions
            positions = await self.bot_api.get_bot_positions(bot_id)
            
            # Prepare comprehensive data
            data = {
                "endpoint": f"bot_{bot_id}",
                "bot_details": bot_details,
                "orders": orders,
                "positions": positions,
                "total_orders": len(orders),
                "total_positions": len(positions),
                "dumped_at": datetime.now().isoformat()
            }
            
            # Save to file
            return await self._save_dump(data, f"bot_{bot_id}", config)
            
        except Exception as e:
            self.logger.error(f"Failed to dump specific bot data: {e}")
            raise AnalysisError(f"Failed to dump specific bot data: {e}")
    
    def _apply_filters(self, data: List[Dict[str, Any]], filters: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply filters to data"""
        if not filters:
            return data
        
        filtered_data = []
        
        for item in data:
            include_item = True
            
            for key, value in filters.items():
                if key not in item:
                    include_item = False
                    break
                
                if isinstance(value, dict):
                    # Handle range filters like {"min": 10, "max": 100}
                    if "min" in value and item[key] < value["min"]:
                        include_item = False
                        break
                    if "max" in value and item[key] > value["max"]:
                        include_item = False
                        break
                elif item[key] != value:
                    include_item = False
                    break
            
            if include_item:
                filtered_data.append(item)
        
        return filtered_data
    
    async def _save_dump(self, data: Dict[str, Any], endpoint: str, config: DumpConfig) -> str:
        """Save dump data to file(s)"""
        # Create output directory
        output_dir = Path(config.output_directory)
        output_dir.mkdir(exist_ok=True)
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = config.filename_template.format(
            endpoint=endpoint,
            timestamp=timestamp
        )
        
        saved_files = []
        
        # Save JSON format
        if config.format in [DumpFormat.JSON, DumpFormat.BOTH]:
            json_filename = f"{filename}.json"
            json_path = output_dir / json_filename
            
            with open(json_path, 'w', encoding='utf-8') as f:
                if config.pretty_print:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                else:
                    json.dump(data, f, ensure_ascii=False)
            
            saved_files.append(str(json_path))
            self.logger.info(f"Saved JSON dump: {json_path}")
        
        # Save CSV format
        if config.format in [DumpFormat.CSV, DumpFormat.BOTH]:
            csv_filename = f"{filename}.csv"
            csv_path = output_dir / csv_filename
            
            # Convert data to CSV format
            csv_data = self._convert_to_csv_format(data)
            
            if csv_data:
                with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=csv_data[0].keys())
                    writer.writeheader()
                    writer.writerows(csv_data)
                
                saved_files.append(str(csv_path))
                self.logger.info(f"Saved CSV dump: {csv_path}")
        
        return saved_files[0] if saved_files else ""
    
    def _convert_to_csv_format(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Convert data to CSV format"""
        if "data" not in data:
            return []
        
        csv_data = []
        
        for item in data["data"]:
            if isinstance(item, dict):
                # Flatten nested dictionaries
                flattened_item = self._flatten_dict(item)
                csv_data.append(flattened_item)
        
        return csv_data
    
    def _flatten_dict(self, d: Dict[str, Any], parent_key: str = '', sep: str = '_') -> Dict[str, Any]:
        """Flatten nested dictionary"""
        items = []
        
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                # Convert lists to strings
                items.append((new_key, str(v)))
            else:
                items.append((new_key, v))
        
        return dict(items)
