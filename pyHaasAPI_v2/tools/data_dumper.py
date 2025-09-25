"""
Data Dumper for pyHaasAPI v2

This module provides functionality for dumping any endpoint data to JSON/CSV
for API exploration and analysis as requested by the user.
"""

import asyncio
import json
import csv
import logging
from typing import List, Dict, Any, Optional, Union, Callable
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum

from ..core.logging import get_logger
from ..exceptions import DataDumperError
from ..api.lab import LabAPI
from ..api.bot import BotAPI
from ..api.account import AccountAPI
from ..api.script import ScriptAPI
from ..api.market import MarketAPI
from ..api.backtest import BacktestAPI
from ..api.order import OrderAPI
from ..core.client import AsyncHaasClient
from ..core.auth import AuthenticationManager

logger = get_logger("data_dumper")


class DumpFormat(Enum):
    """Output formats for data dumping"""
    JSON = "json"
    CSV = "csv"
    BOTH = "both"


class DumpScope(Enum):
    """Scope of data to dump"""
    ALL = "all"
    LABS = "labs"
    BOTS = "bots"
    ACCOUNTS = "accounts"
    SCRIPTS = "scripts"
    MARKETS = "markets"
    BACKTESTS = "backtests"
    ORDERS = "orders"
    CUSTOM = "custom"


@dataclass
class DumpConfig:
    """Configuration for data dumping"""
    scope: DumpScope
    format: DumpFormat
    output_directory: str = "dumps"
    include_metadata: bool = True
    max_items_per_endpoint: Optional[int] = None
    filter_criteria: Optional[Dict[str, Any]] = None
    custom_endpoints: Optional[List[str]] = None
    batch_size: int = 100
    include_timestamps: bool = True


@dataclass
class DumpResult:
    """Result of data dumping operation"""
    dump_id: str
    scope: DumpScope
    format: DumpFormat
    files_created: List[str]
    total_items_dumped: int
    endpoints_processed: List[str]
    dump_timestamp: str
    success: bool
    error_message: Optional[str] = None


class DataDumper:
    """
    Data Dumper for API endpoint exploration and analysis.
    
    Provides comprehensive data dumping functionality for all API endpoints
    with multiple output formats and configurable scope as requested by the user.
    """

    def __init__(
        self,
        lab_api: LabAPI,
        bot_api: BotAPI,
        account_api: AccountAPI,
        script_api: ScriptAPI,
        market_api: MarketAPI,
        backtest_api: BacktestAPI,
        order_api: OrderAPI,
        client: AsyncHaasClient,
        auth_manager: AuthenticationManager
    ):
        self.lab_api = lab_api
        self.bot_api = bot_api
        self.account_api = account_api
        self.script_api = script_api
        self.market_api = market_api
        self.backtest_api = backtest_api
        self.order_api = order_api
        self.client = client
        self.auth_manager = auth_manager
        self.logger = get_logger("data_dumper")

    # Main Dumping Operations

    async def dump_all_data(self, config: DumpConfig) -> DumpResult:
        """
        Dump all available data from all endpoints.

        Args:
            config: Dump configuration

        Returns:
            DumpResult with operation details

        Raises:
            DataDumperError: If dumping fails
        """
        try:
            self.logger.info(f"Starting comprehensive data dump with scope: {config.scope.value}")

            dump_id = f"dump_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            files_created = []
            total_items = 0
            endpoints_processed = []

            # Create output directory
            output_dir = Path(config.output_directory)
            output_dir.mkdir(exist_ok=True)

            # Define endpoint operations based on scope
            endpoint_operations = self._get_endpoint_operations(config.scope)

            # Process each endpoint
            for endpoint_name, operation in endpoint_operations.items():
                try:
                    self.logger.info(f"Processing endpoint: {endpoint_name}")
                    
                    # Execute the operation
                    data = await operation()
                    
                    if data:
                        # Apply filters if specified
                        if config.filter_criteria:
                            data = self._apply_filters(data, config.filter_criteria)

                        # Limit items if specified
                        if config.max_items_per_endpoint and isinstance(data, list):
                            data = data[:config.max_items_per_endpoint]

                        # Dump data in specified format
                        files = await self._dump_endpoint_data(
                            endpoint_name, data, config, output_dir, dump_id
                        )
                        
                        files_created.extend(files)
                        total_items += len(data) if isinstance(data, list) else 1
                        endpoints_processed.append(endpoint_name)

                        self.logger.info(f"✅ {endpoint_name}: {len(data) if isinstance(data, list) else 1} items dumped")

                except Exception as e:
                    self.logger.error(f"Failed to dump {endpoint_name}: {e}")
                    continue

            return DumpResult(
                dump_id=dump_id,
                scope=config.scope,
                format=config.format,
                files_created=files_created,
                total_items_dumped=total_items,
                endpoints_processed=endpoints_processed,
                dump_timestamp=datetime.now().isoformat(),
                success=True
            )

        except Exception as e:
            self.logger.error(f"Failed to dump all data: {e}")
            return DumpResult(
                dump_id="",
                scope=config.scope,
                format=config.format,
                files_created=[],
                total_items_dumped=0,
                endpoints_processed=[],
                dump_timestamp=datetime.now().isoformat(),
                success=False,
                error_message=str(e)
            )

    async def dump_specific_endpoint(
        self,
        endpoint_name: str,
        data: Union[Dict[str, Any], List[Dict[str, Any]]],
        config: DumpConfig
    ) -> DumpResult:
        """
        Dump data from a specific endpoint.

        Args:
            endpoint_name: Name of the endpoint
            data: Data to dump
            config: Dump configuration

        Returns:
            DumpResult with operation details
        """
        try:
            self.logger.info(f"Dumping specific endpoint: {endpoint_name}")

            dump_id = f"dump_{endpoint_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Create output directory
            output_dir = Path(config.output_directory)
            output_dir.mkdir(exist_ok=True)

            # Apply filters if specified
            if config.filter_criteria:
                data = self._apply_filters(data, config.filter_criteria)

            # Limit items if specified
            if config.max_items_per_endpoint and isinstance(data, list):
                data = data[:config.max_items_per_endpoint]

            # Dump data
            files_created = await self._dump_endpoint_data(
                endpoint_name, data, config, output_dir, dump_id
            )

            total_items = len(data) if isinstance(data, list) else 1

            return DumpResult(
                dump_id=dump_id,
                scope=DumpScope.CUSTOM,
                format=config.format,
                files_created=files_created,
                total_items_dumped=total_items,
                endpoints_processed=[endpoint_name],
                dump_timestamp=datetime.now().isoformat(),
                success=True
            )

        except Exception as e:
            self.logger.error(f"Failed to dump specific endpoint: {e}")
            return DumpResult(
                dump_id="",
                scope=DumpScope.CUSTOM,
                format=config.format,
                files_created=[],
                total_items_dumped=0,
                endpoints_processed=[],
                dump_timestamp=datetime.now().isoformat(),
                success=False,
                error_message=str(e)
            )

    # Endpoint Operations

    def _get_endpoint_operations(self, scope: DumpScope) -> Dict[str, Callable]:
        """Get endpoint operations based on scope"""
        operations = {}

        if scope in [DumpScope.ALL, DumpScope.LABS]:
            operations.update({
                "labs": self._get_labs_data,
                "lab_details": self._get_lab_details_data,
                "lab_executions": self._get_lab_executions_data
            })

        if scope in [DumpScope.ALL, DumpScope.BOTS]:
            operations.update({
                "bots": self._get_bots_data,
                "bot_details": self._get_bot_details_data,
                "bot_runtime": self._get_bot_runtime_data
            })

        if scope in [DumpScope.ALL, DumpScope.ACCOUNTS]:
            operations.update({
                "accounts": self._get_accounts_data,
                "account_balances": self._get_account_balances_data,
                "account_orders": self._get_account_orders_data
            })

        if scope in [DumpScope.ALL, DumpScope.SCRIPTS]:
            operations.update({
                "scripts": self._get_scripts_data,
                "script_records": self._get_script_records_data
            })

        if scope in [DumpScope.ALL, DumpScope.MARKETS]:
            operations.update({
                "markets": self._get_markets_data,
                "price_data": self._get_price_data
            })

        if scope in [DumpScope.ALL, DumpScope.BACKTESTS]:
            operations.update({
                "backtest_results": self._get_backtest_results_data,
                "backtest_runtime": self._get_backtest_runtime_data
            })

        if scope in [DumpScope.ALL, DumpScope.ORDERS]:
            operations.update({
                "orders": self._get_orders_data,
                "order_history": self._get_order_history_data
            })

        return operations

    # Data Retrieval Methods

    async def _get_labs_data(self) -> List[Dict[str, Any]]:
        """Get all labs data"""
        try:
            labs = await self.lab_api.get_labs()
            return [asdict(lab) for lab in labs] if labs else []
        except Exception as e:
            self.logger.error(f"Failed to get labs data: {e}")
            return []

    async def _get_lab_details_data(self) -> List[Dict[str, Any]]:
        """Get detailed lab data"""
        try:
            labs = await self.lab_api.get_labs()
            if not labs:
                return []

            lab_details = []
            for lab in labs:
                try:
                    details = await self.lab_api.get_lab_details(lab.lab_id)
                    if details:
                        lab_details.append(asdict(details))
                except Exception as e:
                    self.logger.warning(f"Failed to get details for lab {lab.lab_id}: {e}")
                    continue

            return lab_details
        except Exception as e:
            self.logger.error(f"Failed to get lab details data: {e}")
            return []

    async def _get_lab_executions_data(self) -> List[Dict[str, Any]]:
        """Get lab execution data"""
        try:
            labs = await self.lab_api.get_labs()
            if not labs:
                return []

            executions = []
            for lab in labs:
                try:
                    # Get execution status for each lab
                    execution_data = {
                        "lab_id": lab.lab_id,
                        "lab_name": lab.lab_name,
                        "status": lab.status.value if hasattr(lab, 'status') else "unknown",
                        "created_at": lab.created_at.isoformat() if hasattr(lab, 'created_at') else None
                    }
                    executions.append(execution_data)
                except Exception as e:
                    self.logger.warning(f"Failed to get execution data for lab {lab.lab_id}: {e}")
                    continue

            return executions
        except Exception as e:
            self.logger.error(f"Failed to get lab executions data: {e}")
            return []

    async def _get_bots_data(self) -> List[Dict[str, Any]]:
        """Get all bots data"""
        try:
            bots = await self.bot_api.get_all_bots()
            return [asdict(bot) for bot in bots] if bots else []
        except Exception as e:
            self.logger.error(f"Failed to get bots data: {e}")
            return []

    async def _get_bot_details_data(self) -> List[Dict[str, Any]]:
        """Get detailed bot data"""
        try:
            bots = await self.bot_api.get_all_bots()
            if not bots:
                return []

            bot_details = []
            for bot in bots:
                try:
                    details = await self.bot_api.get_bot_details(bot.bot_id)
                    if details:
                        bot_details.append(asdict(details))
                except Exception as e:
                    self.logger.warning(f"Failed to get details for bot {bot.bot_id}: {e}")
                    continue

            return bot_details
        except Exception as e:
            self.logger.error(f"Failed to get bot details data: {e}")
            return []

    async def _get_bot_runtime_data(self) -> List[Dict[str, Any]]:
        """Get bot runtime data"""
        try:
            bots = await self.bot_api.get_all_bots()
            if not bots:
                return []

            runtime_data = []
            for bot in bots:
                try:
                    runtime = await self.bot_api.get_full_bot_runtime_data(bot.bot_id)
                    if runtime:
                        runtime_data.append({
                            "bot_id": bot.bot_id,
                            "bot_name": bot.bot_name,
                            "runtime_data": asdict(runtime) if hasattr(runtime, '__dict__') else str(runtime)
                        })
                except Exception as e:
                    self.logger.warning(f"Failed to get runtime data for bot {bot.bot_id}: {e}")
                    continue

            return runtime_data
        except Exception as e:
            self.logger.error(f"Failed to get bot runtime data: {e}")
            return []

    async def _get_accounts_data(self) -> List[Dict[str, Any]]:
        """Get all accounts data"""
        try:
            accounts = await self.account_api.get_all_accounts()
            return [asdict(account) for account in accounts] if accounts else []
        except Exception as e:
            self.logger.error(f"Failed to get accounts data: {e}")
            return []

    async def _get_account_balances_data(self) -> List[Dict[str, Any]]:
        """Get account balances data"""
        try:
            accounts = await self.account_api.get_all_accounts()
            if not accounts:
                return []

            balances = []
            for account in accounts:
                try:
                    balance = await self.account_api.get_account_balance(account.account_id)
                    if balance:
                        balances.append({
                            "account_id": account.account_id,
                            "account_name": account.account_name,
                            "balance": balance
                        })
                except Exception as e:
                    self.logger.warning(f"Failed to get balance for account {account.account_id}: {e}")
                    continue

            return balances
        except Exception as e:
            self.logger.error(f"Failed to get account balances data: {e}")
            return []

    async def _get_account_orders_data(self) -> List[Dict[str, Any]]:
        """Get account orders data"""
        try:
            accounts = await self.account_api.get_all_accounts()
            if not accounts:
                return []

            orders = []
            for account in accounts:
                try:
                    account_orders = await self.account_api.get_account_orders(account.account_id)
                    if account_orders:
                        orders.extend([{
                            "account_id": account.account_id,
                            "order": asdict(order) if hasattr(order, '__dict__') else order
                        } for order in account_orders])
                except Exception as e:
                    self.logger.warning(f"Failed to get orders for account {account.account_id}: {e}")
                    continue

            return orders
        except Exception as e:
            self.logger.error(f"Failed to get account orders data: {e}")
            return []

    async def _get_scripts_data(self) -> List[Dict[str, Any]]:
        """Get all scripts data"""
        try:
            scripts = await self.script_api.get_all_scripts()
            return [asdict(script) for script in scripts] if scripts else []
        except Exception as e:
            self.logger.error(f"Failed to get scripts data: {e}")
            return []

    async def _get_script_records_data(self) -> List[Dict[str, Any]]:
        """Get script records data"""
        try:
            scripts = await self.script_api.get_all_scripts()
            if not scripts:
                return []

            records = []
            for script in scripts:
                try:
                    record = await self.script_api.get_script_record(script.script_id)
                    if record:
                        records.append(asdict(record))
                except Exception as e:
                    self.logger.warning(f"Failed to get record for script {script.script_id}: {e}")
                    continue

            return records
        except Exception as e:
            self.logger.error(f"Failed to get script records data: {e}")
            return []

    async def _get_markets_data(self) -> List[Dict[str, Any]]:
        """Get markets data"""
        try:
            markets = await self.market_api.get_trade_markets()
            return [asdict(market) for market in markets] if markets else []
        except Exception as e:
            self.logger.error(f"Failed to get markets data: {e}")
            return []

    async def _get_price_data(self) -> List[Dict[str, Any]]:
        """Get price data for markets"""
        try:
            markets = await self.market_api.get_trade_markets()
            if not markets:
                return []

            price_data = []
            for market in markets[:10]:  # Limit to first 10 markets to avoid too many requests
                try:
                    price = await self.market_api.get_price_data(market.market_tag)
                    if price:
                        price_data.append({
                            "market_tag": market.market_tag,
                            "price_data": asdict(price) if hasattr(price, '__dict__') else price
                        })
                except Exception as e:
                    self.logger.warning(f"Failed to get price for market {market.market_tag}: {e}")
                    continue

            return price_data
        except Exception as e:
            self.logger.error(f"Failed to get price data: {e}")
            return []

    async def _get_backtest_results_data(self) -> List[Dict[str, Any]]:
        """Get backtest results data"""
        try:
            labs = await self.lab_api.get_labs()
            if not labs:
                return []

            backtest_results = []
            for lab in labs:
                try:
                    results = await self.backtest_api.get_backtest_result(lab.lab_id, 0, 50)  # Limit to 50 per lab
                    if results and hasattr(results, 'items'):
                        backtest_results.extend([asdict(item) for item in results.items])
                except Exception as e:
                    self.logger.warning(f"Failed to get backtest results for lab {lab.lab_id}: {e}")
                    continue

            return backtest_results
        except Exception as e:
            self.logger.error(f"Failed to get backtest results data: {e}")
            return []

    async def _get_backtest_runtime_data(self) -> List[Dict[str, Any]]:
        """Get backtest runtime data"""
        try:
            labs = await self.lab_api.get_labs()
            if not labs:
                return []

            runtime_data = []
            for lab in labs:
                try:
                    # Get a few backtest results first
                    results = await self.backtest_api.get_backtest_result(lab.lab_id, 0, 5)  # Limit to 5 per lab
                    if results and hasattr(results, 'items'):
                        for backtest in results.items:
                            try:
                                runtime = await self.backtest_api.get_full_backtest_runtime_data(
                                    lab.lab_id, backtest.backtest_id
                                )
                                if runtime:
                                    runtime_data.append({
                                        "lab_id": lab.lab_id,
                                        "backtest_id": backtest.backtest_id,
                                        "runtime_data": asdict(runtime) if hasattr(runtime, '__dict__') else str(runtime)
                                    })
                            except Exception as e:
                                self.logger.warning(f"Failed to get runtime for backtest {backtest.backtest_id}: {e}")
                                continue
                except Exception as e:
                    self.logger.warning(f"Failed to get backtest results for lab {lab.lab_id}: {e}")
                    continue

            return runtime_data
        except Exception as e:
            self.logger.error(f"Failed to get backtest runtime data: {e}")
            return []

    async def _get_orders_data(self) -> List[Dict[str, Any]]:
        """Get orders data"""
        try:
            orders = await self.order_api.get_all_orders()
            return [asdict(order) for order in orders] if orders else []
        except Exception as e:
            self.logger.error(f"Failed to get orders data: {e}")
            return []

    async def _get_order_history_data(self) -> List[Dict[str, Any]]:
        """Get order history data"""
        try:
            history = await self.order_api.get_order_history()
            return [asdict(order) for order in history] if history else []
        except Exception as e:
            self.logger.error(f"Failed to get order history data: {e}")
            return []

    # Data Processing and Export

    async def _dump_endpoint_data(
        self,
        endpoint_name: str,
        data: Union[Dict[str, Any], List[Dict[str, Any]]],
        config: DumpConfig,
        output_dir: Path,
        dump_id: str
    ) -> List[str]:
        """Dump data for a specific endpoint"""
        files_created = []

        try:
            # Add metadata if requested
            if config.include_metadata:
                data = self._add_metadata(data, endpoint_name, config)

            # Generate files based on format
            if config.format in [DumpFormat.JSON, DumpFormat.BOTH]:
                json_file = await self._save_json_data(data, endpoint_name, output_dir, dump_id)
                files_created.append(json_file)

            if config.format in [DumpFormat.CSV, DumpFormat.BOTH]:
                csv_file = await self._save_csv_data(data, endpoint_name, output_dir, dump_id)
                files_created.append(csv_file)

            return files_created

        except Exception as e:
            self.logger.error(f"Failed to dump endpoint data for {endpoint_name}: {e}")
            return []

    def _add_metadata(
        self,
        data: Union[Dict[str, Any], List[Dict[str, Any]]],
        endpoint_name: str,
        config: DumpConfig
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """Add metadata to data"""
        metadata = {
            "endpoint": endpoint_name,
            "dump_timestamp": datetime.now().isoformat(),
            "total_items": len(data) if isinstance(data, list) else 1,
            "dump_config": {
                "scope": config.scope.value,
                "format": config.format.value,
                "include_metadata": config.include_metadata,
                "max_items": config.max_items_per_endpoint
            }
        }

        if isinstance(data, list):
            return {
                "metadata": metadata,
                "data": data
            }
        else:
            return {
                "metadata": metadata,
                "data": data
            }

    async def _save_json_data(
        self,
        data: Union[Dict[str, Any], List[Dict[str, Any]]],
        endpoint_name: str,
        output_dir: Path,
        dump_id: str
    ) -> str:
        """Save data as JSON file"""
        try:
            filename = f"{dump_id}_{endpoint_name}.json"
            file_path = output_dir / filename

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)

            self.logger.info(f"JSON data saved: {file_path}")
            return str(file_path)

        except Exception as e:
            self.logger.error(f"Failed to save JSON data: {e}")
            raise DataDumperError(f"Failed to save JSON data: {e}") from e

    async def _save_csv_data(
        self,
        data: Union[Dict[str, Any], List[Dict[str, Any]]],
        endpoint_name: str,
        output_dir: Path,
        dump_id: str
    ) -> str:
        """Save data as CSV file"""
        try:
            filename = f"{dump_id}_{endpoint_name}.csv"
            file_path = output_dir / filename

            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                if isinstance(data, list) and data:
                    # List of dictionaries
                    if isinstance(data[0], dict):
                        fieldnames = data[0].keys()
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        writer.writeheader()
                        writer.writerows(data)
                    else:
                        # List of other types
                        writer = csv.writer(f)
                        for item in data:
                            writer.writerow([str(item)])
                elif isinstance(data, dict):
                    # Single dictionary
                    writer = csv.writer(f)
                    for key, value in data.items():
                        writer.writerow([key, str(value)])
                else:
                    # Other types
                    writer = csv.writer(f)
                    writer.writerow([str(data)])

            self.logger.info(f"CSV data saved: {file_path}")
            return str(file_path)

        except Exception as e:
            self.logger.error(f"Failed to save CSV data: {e}")
            raise DataDumperError(f"Failed to save CSV data: {e}") from e

    def _apply_filters(
        self,
        data: List[Dict[str, Any]],
        filter_criteria: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Apply filters to data"""
        try:
            if not data or not filter_criteria:
                return data

            filtered_data = []
            for item in data:
                include_item = True
                for key, value in filter_criteria.items():
                    if key in item:
                        if isinstance(value, dict):
                            # Range filter
                            if "min" in value and item[key] < value["min"]:
                                include_item = False
                                break
                            if "max" in value and item[key] > value["max"]:
                                include_item = False
                                break
                        else:
                            # Exact match filter
                            if item[key] != value:
                                include_item = False
                                break

                if include_item:
                    filtered_data.append(item)

            return filtered_data

        except Exception as e:
            self.logger.error(f"Failed to apply filters: {e}")
            return data

    # Utility Methods

    async def get_dump_summary(self, dump_id: str, output_directory: str = "dumps") -> Dict[str, Any]:
        """
        Get summary of a dump operation.

        Args:
            dump_id: ID of the dump
            output_directory: Directory containing dump files

        Returns:
            Dictionary with dump summary
        """
        try:
            output_dir = Path(output_directory)
            if not output_dir.exists():
                return {"error": "Dump directory not found"}

            # Find files matching the dump ID
            dump_files = list(output_dir.glob(f"{dump_id}_*"))
            
            summary = {
                "dump_id": dump_id,
                "total_files": len(dump_files),
                "files": [str(f) for f in dump_files],
                "total_size": sum(f.stat().st_size for f in dump_files),
                "created_at": datetime.fromtimestamp(dump_files[0].stat().st_ctime).isoformat() if dump_files else None
            }

            return summary

        except Exception as e:
            self.logger.error(f"Failed to get dump summary: {e}")
            return {"error": str(e)}

    async def cleanup_old_dumps(self, output_directory: str = "dumps", days_old: int = 7) -> int:
        """
        Clean up old dump files.

        Args:
            output_directory: Directory containing dump files
            days_old: Number of days after which to delete dumps

        Returns:
            Number of files deleted
        """
        try:
            output_dir = Path(output_directory)
            if not output_dir.exists():
                return 0

            cutoff_time = datetime.now().timestamp() - (days_old * 24 * 60 * 60)
            deleted_count = 0

            for file_path in output_dir.glob("dump_*"):
                if file_path.stat().st_ctime < cutoff_time:
                    file_path.unlink()
                    deleted_count += 1
                    self.logger.info(f"Deleted old dump file: {file_path}")

            return deleted_count

        except Exception as e:
            self.logger.error(f"Failed to cleanup old dumps: {e}")
            return 0
