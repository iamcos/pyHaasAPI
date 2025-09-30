"""
V1 Compatibility Layer for pyHaasAPI v2

Provides compatibility layer and migration tools for transitioning
from pyHaasAPI v1 to v2.
"""

import asyncio
from typing import Dict, Any, Optional, List, Union
from datetime import datetime

from ..core.client import AsyncHaasClient
from ..core.auth import AuthenticationManager
from ..services.lab import LabService
from ..services.bot import BotService
from ..services.analysis import AnalysisService
from ..exceptions import HaasAPIError
from ..core.logging import get_logger


class V1CompatibilityLayer:
    """
    V1 Compatibility Layer
    
    Provides a compatibility layer that mimics v1 API structure
    while using v2 services underneath.
    """
    
    def __init__(self, client: AsyncHaasClient, auth_manager: AuthenticationManager):
        self.client = client
        self.auth_manager = auth_manager
        self.logger = get_logger("v1_compatibility")
        
        # Initialize services
        self._lab_service: Optional[LabService] = None
        self._bot_service: Optional[BotService] = None
        self._analysis_service: Optional[AnalysisService] = None
    
    async def _ensure_services_initialized(self):
        """Ensure services are initialized"""
        if not self._lab_service:
            from ..api.lab import LabAPI
            from ..api.bot import BotAPI
            from ..api.account import AccountAPI
            from ..api.script import ScriptAPI
            from ..api.backtest import BacktestAPI
            
            # Initialize API modules
            lab_api = LabAPI(self.client, self.auth_manager)
            bot_api = BotAPI(self.client, self.auth_manager)
            account_api = AccountAPI(self.client, self.auth_manager)
            script_api = ScriptAPI(self.client, self.auth_manager)
            backtest_api = BacktestAPI(self.client, self.auth_manager)
            
            # Initialize services
            self._lab_service = LabService(lab_api, backtest_api, script_api, account_api)
            self._bot_service = BotService(bot_api, account_api, lab_api, backtest_api)
            self._analysis_service = AnalysisService(lab_api, bot_api, backtest_api, account_api)
    
    # V1-style API methods
    async def get_labs(self) -> List[Dict[str, Any]]:
        """Get all labs (v1 style)"""
        await self._ensure_services_initialized()
        
        from ..api.lab import LabAPI
        lab_api = LabAPI(self.client, self.auth_manager)
        labs = await lab_api.get_labs()
        
        # Convert to v1-style format
        return [
            {
                "lab_id": lab.lab_id,
                "name": lab.name,
                "status": lab.status,
                "script_id": lab.script_id,
                "market_tag": lab.settings.market_tag,
                "account_id": lab.settings.account_id,
                "interval": lab.settings.interval,
                "trade_amount": lab.settings.trade_amount,
                "leverage": lab.settings.leverage
            }
            for lab in labs
        ]
    
    async def get_lab_details(self, lab_id: str) -> Dict[str, Any]:
        """Get lab details (v1 style)"""
        await self._ensure_services_initialized()
        
        from ..api.lab import LabAPI
        lab_api = LabAPI(self.client, self.auth_manager)
        lab_details = await lab_api.get_lab_details(lab_id)
        
        # Convert to v1-style format
        return {
            "lab_id": lab_details.lab_id,
            "name": lab_details.name,
            "status": lab_details.status,
            "script_id": lab_details.script_id,
            "market_tag": lab_details.settings.market_tag,
            "account_id": lab_details.settings.account_id,
            "interval": lab_details.settings.interval,
            "trade_amount": lab_details.settings.trade_amount,
            "leverage": lab_details.settings.leverage,
            "position_mode": lab_details.settings.position_mode,
            "margin_mode": lab_details.settings.margin_mode,
            "created_at": lab_details.created_at.isoformat() if lab_details.created_at else None,
            "updated_at": lab_details.updated_at.isoformat() if lab_details.updated_at else None
        }
    
    async def create_lab(
        self,
        script_id: str,
        name: str,
        account_id: str,
        market: str,
        interval: int = 1,
        trade_amount: float = 100.0,
        leverage: float = 0.0,
        position_mode: int = 0,
        margin_mode: int = 0
    ) -> Dict[str, Any]:
        """Create a lab (v1 style)"""
        await self._ensure_services_initialized()
        
        lab_details = await self._lab_service.create_lab_with_validation(
            script_id=script_id,
            name=name,
            account_id=account_id,
            market=market,
            interval=interval,
            trade_amount=trade_amount,
            leverage=leverage,
            position_mode=position_mode,
            margin_mode=margin_mode,
            validate_config=True
        )
        
        # Convert to v1-style format
        return {
            "lab_id": lab_details.lab_id,
            "name": lab_details.name,
            "status": lab_details.status,
            "script_id": lab_details.script_id,
            "market_tag": lab_details.settings.market_tag,
            "account_id": lab_details.settings.account_id,
            "interval": lab_details.settings.interval,
            "trade_amount": lab_details.settings.trade_amount,
            "leverage": lab_details.settings.leverage,
            "position_mode": lab_details.settings.position_mode,
            "margin_mode": lab_details.settings.margin_mode
        }
    
    async def get_bots(self) -> List[Dict[str, Any]]:
        """Get all bots (v1 style)"""
        await self._ensure_services_initialized()
        
        from ..api.bot import BotAPI
        bot_api = BotAPI(self.client, self.auth_manager)
        bots = await bot_api.get_all_bots()
        
        # Convert to v1-style format
        return [
            {
                "bot_id": bot.bot_id,
                "bot_name": bot.bot_name,
                "status": bot.status,
                "is_active": bot.is_active,
                "script_id": bot.script_id,
                "market_tag": bot.market_tag,
                "account_id": bot.account_id,
                "leverage": bot.configuration.leverage,
                "interval": bot.configuration.interval,
                "trade_amount": bot.configuration.trade_amount,
                "position_mode": bot.configuration.position_mode,
                "margin_mode": bot.configuration.margin_mode
            }
            for bot in bots
        ]
    
    async def create_bot_from_lab(
        self,
        lab_id: str,
        backtest_id: str,
        bot_name: str,
        account_id: str,
        market: str,
        leverage: float = 20.0
    ) -> Dict[str, Any]:
        """Create a bot from lab (v1 style)"""
        await self._ensure_services_initialized()
        
        from ..models.bot import BotConfiguration
        config = BotConfiguration(leverage=leverage)
        
        result = await self._bot_service.create_bot_from_lab_analysis(
            lab_id=lab_id,
            backtest_id=backtest_id,
            bot_name=bot_name,
            account_id=account_id,
            market_tag=market,
            configuration=config,
            validate_backtest=True,
            auto_activate=False
        )
        
        # Convert to v1-style format
        return {
            "bot_id": result.bot_id,
            "bot_name": result.bot_name,
            "backtest_id": result.backtest_id,
            "account_id": result.account_id,
            "market_tag": result.market_tag,
            "success": result.success,
            "activated": result.activated,
            "error_message": result.error_message
        }
    
    async def analyze_lab(self, lab_id: str, top_count: int = 10) -> Dict[str, Any]:
        """Analyze a lab (v1 style)"""
        await self._ensure_services_initialized()
        
        result = await self._analysis_service.analyze_lab_comprehensive(
            lab_id=lab_id,
            top_count=top_count
        )
        
        # Convert to v1-style format
        return {
            "lab_id": result.lab_id,
            "lab_name": result.lab_name,
            "total_backtests": result.total_backtests,
            "analyzed_backtests": result.analyzed_backtests,
            "average_roi": result.average_roi,
            "best_roi": result.best_roi,
            "average_win_rate": result.average_win_rate,
            "best_win_rate": result.best_win_rate,
            "total_trades": result.total_trades,
            "top_performers": result.top_performers,
            "recommendations": result.recommendations,
            "analysis_timestamp": result.analysis_timestamp.isoformat()
        }
    
    async def get_backtest_results(self, lab_id: str, page_size: int = 100) -> Dict[str, Any]:
        """Get backtest results (v1 style)"""
        await self._ensure_services_initialized()
        
        from ..api.backtest import BacktestAPI
        backtest_api = BacktestAPI(self.client, self.auth_manager)
        
        # Get all backtests for the lab
        backtests = await backtest_api.get_all_backtests_for_lab(lab_id)
        
        # Convert to v1-style format
        return {
            "lab_id": lab_id,
            "total_backtests": len(backtests),
            "backtests": [
                {
                    "backtest_id": bt.get("BacktestId", ""),
                    "roi": bt.get("ROI", 0),
                    "win_rate": bt.get("WinRate", 0),
                    "total_trades": bt.get("TotalTrades", 0),
                    "max_drawdown": bt.get("MaxDrawdown", 0),
                    "profit_factor": bt.get("ProfitFactor", 0),
                    "sharpe_ratio": bt.get("SharpeRatio", 0),
                    "success": bt.get("Success", False),
                    "market_tag": bt.get("MarketTag", ""),
                    "script_name": bt.get("ScriptName", "")
                }
                for bt in backtests
            ]
        }


class V1ToV2Migrator:
    """
    V1 to V2 Migration Tool
    
    Provides tools for migrating from v1 to v2 including:
    - Code migration assistance
    - Configuration migration
    - Data migration
    """
    
    def __init__(self):
        self.logger = get_logger("v1_to_v2_migrator")
    
    def generate_migration_guide(self, v1_code: str) -> str:
        """
        Generate migration guide for v1 code
        
        Args:
            v1_code: V1 code to migrate
            
        Returns:
            Migration guide with v2 equivalent code
        """
        migration_guide = []
        migration_guide.append("# V1 to V2 Migration Guide")
        migration_guide.append("=" * 50)
        migration_guide.append("")
        
        # Common migration patterns
        patterns = {
            "from pyHaasAPI import api": "from pyHaasAPI_v2 import AsyncHaasClient, AuthenticationManager",
            "api.RequestsExecutor": "AsyncHaasClient",
            "api.Guest()": "AuthenticationManager",
            "executor.authenticate": "await auth_manager.authenticate",
            "api.get_labs()": "await lab_api.get_labs()",
            "api.get_bots()": "await bot_api.get_all_bots()",
            "api.create_lab": "await lab_service.create_lab_with_validation",
            "api.add_bot": "await bot_service.create_bot_with_validation",
            "api.get_backtest_result": "await backtest_api.get_backtest_result",
            "HaasAnalyzer": "AnalysisService",
            "analyzer.analyze_lab": "await analysis_service.analyze_lab_comprehensive",
            "analyzer.create_bots_from_analysis": "await analysis_service.generate_bot_recommendations",
        }
        
        migration_guide.append("## Common Migration Patterns")
        migration_guide.append("")
        
        for v1_pattern, v2_pattern in patterns.items():
            if v1_pattern in v1_code:
                migration_guide.append(f"**V1:** `{v1_pattern}`")
                migration_guide.append(f"**V2:** `{v2_pattern}`")
                migration_guide.append("")
        
        migration_guide.append("## Key Changes")
        migration_guide.append("")
        migration_guide.append("1. **Async/Await**: All API calls are now async")
        migration_guide.append("2. **Service Layer**: Business logic moved to service classes")
        migration_guide.append("3. **Type Safety**: Comprehensive type hints throughout")
        migration_guide.append("4. **Error Handling**: Improved exception hierarchy")
        migration_guide.append("5. **Configuration**: Centralized configuration management")
        migration_guide.append("")
        
        migration_guide.append("## Example Migration")
        migration_guide.append("")
        migration_guide.append("### V1 Code:")
        migration_guide.append("```python")
        migration_guide.append("from pyHaasAPI import api")
        migration_guide.append("")
        migration_guide.append("haas_api = api.RequestsExecutor(host='127.0.0.1', port=8090, state=api.Guest())")
        migration_guide.append("executor = haas_api.authenticate(email, password)")
        migration_guide.append("")
        migration_guide.append("labs = api.get_labs(executor)")
        migration_guide.append("for lab in labs:")
        migration_guide.append("    print(f'Lab: {lab.name}')")
        migration_guide.append("```")
        migration_guide.append("")
        
        migration_guide.append("### V2 Code:")
        migration_guide.append("```python")
        migration_guide.append("import asyncio")
        migration_guide.append("from pyHaasAPI_v2 import AsyncHaasClient, AuthenticationManager")
        migration_guide.append("")
        migration_guide.append("async def main():")
        migration_guide.append("    client = AsyncHaasClient(host='127.0.0.1', port=8090)")
        migration_guide.append("    auth_manager = AuthenticationManager(client)")
        migration_guide.append("    await auth_manager.authenticate(email, password)")
        migration_guide.append("")
        migration_guide.append("    from pyHaasAPI_v2.api.lab import LabAPI")
        migration_guide.append("    lab_api = LabAPI(client, auth_manager)")
        migration_guide.append("    labs = await lab_api.get_labs()")
        migration_guide.append("    for lab in labs:")
        migration_guide.append("        print(f'Lab: {lab.name}')")
        migration_guide.append("")
        migration_guide.append("asyncio.run(main())")
        migration_guide.append("```")
        migration_guide.append("")
        
        return "\n".join(migration_guide)
    
    def analyze_v1_usage(self, v1_code: str) -> Dict[str, Any]:
        """
        Analyze v1 code usage patterns
        
        Args:
            v1_code: V1 code to analyze
            
        Returns:
            Analysis results with migration recommendations
        """
        analysis = {
            "total_lines": len(v1_code.split('\n')),
            "api_calls": [],
            "imports": [],
            "migration_complexity": "low",
            "recommendations": []
        }
        
        # Analyze imports
        if "from pyHaasAPI import api" in v1_code:
            analysis["imports"].append("pyHaasAPI.api")
            analysis["recommendations"].append("Replace with pyHaasAPI_v2 imports")
        
        if "HaasAnalyzer" in v1_code:
            analysis["api_calls"].append("HaasAnalyzer")
            analysis["recommendations"].append("Replace with AnalysisService")
            analysis["migration_complexity"] = "medium"
        
        if "analyzer.analyze_lab" in v1_code:
            analysis["api_calls"].append("analyze_lab")
            analysis["recommendations"].append("Use analysis_service.analyze_lab_comprehensive")
        
        if "analyzer.create_bots_from_analysis" in v1_code:
            analysis["api_calls"].append("create_bots_from_analysis")
            analysis["recommendations"].append("Use analysis_service.generate_bot_recommendations + bot_service.create_bot_from_lab_analysis")
            analysis["migration_complexity"] = "high"
        
        # Check for async patterns
        if "async" in v1_code or "await" in v1_code:
            analysis["recommendations"].append("Code already uses async patterns - minimal migration needed")
        else:
            analysis["recommendations"].append("Add async/await patterns throughout")
            analysis["migration_complexity"] = "high"
        
        return analysis
    
    def create_migration_script(self, v1_code: str) -> str:
        """
        Create a migration script for v1 code
        
        Args:
            v1_code: V1 code to migrate
            
        Returns:
            V2 migration script
        """
        script = []
        script.append("#!/usr/bin/env python3")
        script.append('"""')
        script.append("Auto-generated migration script from V1 to V2")
        script.append("Generated by pyHaasAPI v2 migration tool")
        script.append('"""')
        script.append("")
        script.append("import asyncio")
        script.append("from pyHaasAPI_v2 import (")
        script.append("    AsyncHaasClient,")
        script.append("    AuthenticationManager,")
        script.append("    LabService,")
        script.append("    BotService,")
        script.append("    AnalysisService")
        script.append(")")
        script.append("")
        script.append("")
        script.append("async def main():")
        script.append("    # Initialize client and authentication")
        script.append("    client = AsyncHaasClient(host='127.0.0.1', port=8090)")
        script.append("    auth_manager = AuthenticationManager(client)")
        script.append("    await auth_manager.authenticate('your_email@example.com', 'your_password')")
        script.append("")
        script.append("    # Initialize services")
        script.append("    from pyHaasAPI_v2.api.lab import LabAPI")
        script.append("    from pyHaasAPI_v2.api.bot import BotAPI")
        script.append("    from pyHaasAPI_v2.api.account import AccountAPI")
        script.append("    from pyHaasAPI_v2.api.script import ScriptAPI")
        script.append("    from pyHaasAPI_v2.api.backtest import BacktestAPI")
        script.append("")
        script.append("    lab_api = LabAPI(client, auth_manager)")
        script.append("    bot_api = BotAPI(client, auth_manager)")
        script.append("    account_api = AccountAPI(client, auth_manager)")
        script.append("    script_api = ScriptAPI(client, auth_manager)")
        script.append("    backtest_api = BacktestAPI(client, auth_manager)")
        script.append("")
        script.append("    lab_service = LabService(lab_api, backtest_api, script_api, account_api)")
        script.append("    bot_service = BotService(bot_api, account_api, lab_api, backtest_api)")
        script.append("    analysis_service = AnalysisService(lab_api, bot_api, backtest_api, account_api)")
        script.append("")
        script.append("    # TODO: Add your migrated code here")
        script.append("    # Original V1 code:")
        script.append("    # " + v1_code.replace('\n', '\n    # '))
        script.append("")
        script.append("")
        script.append("if __name__ == '__main__':")
        script.append("    asyncio.run(main())")
        
        return "\n".join(script)
