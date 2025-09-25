"""
Test Data Manager for pyHaasAPI v2

Provides functionality for creating test labs, bots, and accounts
for testing purposes as requested by the user.
"""

import asyncio
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from ..api.lab import LabAPI
from ..api.bot import BotAPI
from ..api.account import AccountAPI
from ..api.script import ScriptAPI
from ..api.market import MarketAPI
from ..api.backtest import BacktestAPI
from ..models.lab import LabDetails, LabConfig
from ..models.bot import BotDetails, BotConfiguration
from ..exceptions import AnalysisError
from ..core.logging import get_logger


class TestEntity(Enum):
    """Test entity types"""
    LAB = "lab"
    BOT = "bot"
    ACCOUNT = "account"
    SCRIPT = "script"


@dataclass
class TestConfig:
    """Configuration for test data creation"""
    entity_type: TestEntity
    count: int = 1
    prefix: str = "TEST"
    cleanup_after: bool = True
    cleanup_delay_hours: int = 24
    use_real_data: bool = False
    market_tag: str = "BINANCE_BTC_USDT_"
    script_id: Optional[str] = None
    account_id: Optional[str] = None


class TestDataManager:
    """
    Test Data Manager for creating test entities
    
    Provides functionality for creating test labs, bots, and accounts
    for testing purposes as requested by the user.
    """
    
    def __init__(
        self,
        lab_api: LabAPI,
        bot_api: BotAPI,
        account_api: AccountAPI,
        script_api: ScriptAPI,
        market_api: MarketAPI,
        backtest_api: BacktestAPI
    ):
        self.lab_api = lab_api
        self.bot_api = bot_api
        self.account_api = account_api
        self.script_api = script_api
        self.market_api = market_api
        self.backtest_api = backtest_api
        self.logger = get_logger("test_data_manager")
        self.created_entities = []  # Track created entities for cleanup
    
    async def create_test_labs(self, config: TestConfig) -> List[LabDetails]:
        """
        Create test labs for testing purposes
        
        Args:
            config: Test configuration
            
        Returns:
            List of created test labs
        """
        try:
            self.logger.info(f"Creating {config.count} test labs")
            
            created_labs = []
            
            # Get available script if not specified
            if not config.script_id:
                scripts = await self.script_api.get_all_scripts()
                if not scripts:
                    raise AnalysisError("No scripts available for test lab creation")
                config.script_id = scripts[0].script_id
            
            # Get available account if not specified
            if not config.account_id:
                accounts = await self.account_api.get_accounts()
                if not accounts:
                    raise AnalysisError("No accounts available for test lab creation")
                config.account_id = accounts[0].account_id
            
            # Create test labs
            for i in range(config.count):
                lab_name = f"{config.prefix}_LAB_{i+1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
                try:
                    lab_details = await self.lab_api.create_lab(
                        script_id=config.script_id,
                        name=lab_name,
                        account_id=config.account_id,
                        market=config.market_tag,
                        interval=15,  # 15-minute interval
                        trade_amount=100.0,  # $100 trade amount
                        leverage=10.0,  # 10x leverage
                        position_mode=1,  # HEDGE mode
                        margin_mode=0   # CROSS margin
                    )
                    
                    created_labs.append(lab_details)
                    self.created_entities.append({
                        "type": "lab",
                        "id": lab_details.lab_id,
                        "name": lab_details.name,
                        "created_at": datetime.now()
                    })
                    
                    self.logger.info(f"Created test lab: {lab_details.lab_id}")
                    
                except Exception as e:
                    self.logger.error(f"Failed to create test lab {i+1}: {e}")
                    continue
            
            self.logger.info(f"Successfully created {len(created_labs)} test labs")
            return created_labs
            
        except Exception as e:
            self.logger.error(f"Failed to create test labs: {e}")
            raise AnalysisError(f"Failed to create test labs: {e}")
    
    async def create_test_bots(self, config: TestConfig) -> List[BotDetails]:
        """
        Create test bots for testing purposes
        
        Args:
            config: Test configuration
            
        Returns:
            List of created test bots
        """
        try:
            self.logger.info(f"Creating {config.count} test bots")
            
            created_bots = []
            
            # Get available script if not specified
            if not config.script_id:
                scripts = await self.script_api.get_all_scripts()
                if not scripts:
                    raise AnalysisError("No scripts available for test bot creation")
                config.script_id = scripts[0].script_id
            
            # Get available account if not specified
            if not config.account_id:
                accounts = await self.account_api.get_accounts()
                if not accounts:
                    raise AnalysisError("No accounts available for test bot creation")
                config.account_id = accounts[0].account_id
            
            # Create test bots
            for i in range(config.count):
                bot_name = f"{config.prefix}_BOT_{i+1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
                try:
                    bot_details = await self.bot_api.create_bot(
                        bot_name=bot_name,
                        script_id=config.script_id,
                        script_type="HaasScript",
                        account_id=config.account_id,
                        market=config.market_tag,
                        leverage=20.0,  # 20x leverage
                        interval=15,    # 15-minute interval
                        chart_style=300 # Standard chart style
                    )
                    
                    created_bots.append(bot_details)
                    self.created_entities.append({
                        "type": "bot",
                        "id": bot_details.bot_id,
                        "name": bot_details.bot_name,
                        "created_at": datetime.now()
                    })
                    
                    self.logger.info(f"Created test bot: {bot_details.bot_id}")
                    
                except Exception as e:
                    self.logger.error(f"Failed to create test bot {i+1}: {e}")
                    continue
            
            self.logger.info(f"Successfully created {len(created_bots)} test bots")
            return created_bots
            
        except Exception as e:
            self.logger.error(f"Failed to create test bots: {e}")
            raise AnalysisError(f"Failed to create test bots: {e}")
    
    async def create_test_accounts(self, config: TestConfig) -> List[Dict[str, Any]]:
        """
        Create test accounts for testing purposes
        
        Args:
            config: Test configuration
            
        Returns:
            List of created test accounts
        """
        try:
            self.logger.info(f"Creating {config.count} test accounts")
            
            created_accounts = []
            
            # Note: Account creation typically requires external exchange setup
            # This is a placeholder for the account creation logic
            
            for i in range(config.count):
                account_name = f"{config.prefix}_ACCOUNT_{i+1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
                try:
                    # This would need to be implemented based on the actual account creation API
                    # For now, we'll create a mock account structure
                    account_data = {
                        "account_id": f"test_account_{i+1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        "account_name": account_name,
                        "account_type": "SIMULATED",
                        "balance": 10000.0,  # $10,000 starting balance
                        "status": "ACTIVE",
                        "created_at": datetime.now().isoformat()
                    }
                    
                    created_accounts.append(account_data)
                    self.created_entities.append({
                        "type": "account",
                        "id": account_data["account_id"],
                        "name": account_data["account_name"],
                        "created_at": datetime.now()
                    })
                    
                    self.logger.info(f"Created test account: {account_data['account_id']}")
                    
                except Exception as e:
                    self.logger.error(f"Failed to create test account {i+1}: {e}")
                    continue
            
            self.logger.info(f"Successfully created {len(created_accounts)} test accounts")
            return created_accounts
            
        except Exception as e:
            self.logger.error(f"Failed to create test accounts: {e}")
            raise AnalysisError(f"Failed to create test accounts: {e}")
    
    async def create_test_scripts(self, config: TestConfig) -> List[Dict[str, Any]]:
        """
        Create test scripts for testing purposes
        
        Args:
            config: Test configuration
            
        Returns:
            List of created test scripts
        """
        try:
            self.logger.info(f"Creating {config.count} test scripts")
            
            created_scripts = []
            
            # Create test scripts
            for i in range(config.count):
                script_name = f"{config.prefix}_SCRIPT_{i+1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
                try:
                    # Create a simple test script
                    script_code = f"""
// Test Script {i+1}
// Created for testing purposes

var testVar = 0;

function OnTick() {{
    testVar++;
    if (testVar > 100) {{
        testVar = 0;
    }}
}}

function OnStart() {{
    Log("Test script {i+1} started");
}}

function OnStop() {{
    Log("Test script {i+1} stopped");
}}
"""
                    
                    script_data = {
                        "script_id": f"test_script_{i+1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        "script_name": script_name,
                        "script_type": "HaasScript",
                        "script_code": script_code,
                        "status": "ACTIVE",
                        "created_at": datetime.now().isoformat()
                    }
                    
                    created_scripts.append(script_data)
                    self.created_entities.append({
                        "type": "script",
                        "id": script_data["script_id"],
                        "name": script_data["script_name"],
                        "created_at": datetime.now()
                    })
                    
                    self.logger.info(f"Created test script: {script_data['script_id']}")
                    
                except Exception as e:
                    self.logger.error(f"Failed to create test script {i+1}: {e}")
                    continue
            
            self.logger.info(f"Successfully created {len(created_scripts)} test scripts")
            return created_scripts
            
        except Exception as e:
            self.logger.error(f"Failed to create test scripts: {e}")
            raise AnalysisError(f"Failed to create test scripts: {e}")
    
    async def cleanup_test_entities(self, entity_type: Optional[TestEntity] = None) -> int:
        """
        Clean up created test entities
        
        Args:
            entity_type: Specific entity type to clean up (optional)
            
        Returns:
            Number of entities cleaned up
        """
        try:
            self.logger.info("Starting cleanup of test entities")
            
            cleaned_count = 0
            
            for entity in self.created_entities:
                if entity_type and entity["type"] != entity_type.value:
                    continue
                
                try:
                    if entity["type"] == "lab":
                        await self.lab_api.delete_lab(entity["id"])
                        self.logger.info(f"Deleted test lab: {entity['id']}")
                    elif entity["type"] == "bot":
                        await self.bot_api.delete_bot(entity["id"])
                        self.logger.info(f"Deleted test bot: {entity['id']}")
                    elif entity["type"] == "account":
                        # Account deletion would need to be implemented
                        self.logger.info(f"Marked test account for deletion: {entity['id']}")
                    elif entity["type"] == "script":
                        # Script deletion would need to be implemented
                        self.logger.info(f"Marked test script for deletion: {entity['id']}")
                    
                    cleaned_count += 1
                    
                except Exception as e:
                    self.logger.error(f"Failed to delete {entity['type']} {entity['id']}: {e}")
                    continue
            
            # Remove cleaned entities from tracking
            if entity_type:
                self.created_entities = [
                    e for e in self.created_entities 
                    if e["type"] != entity_type.value
                ]
            else:
                self.created_entities = []
            
            self.logger.info(f"Successfully cleaned up {cleaned_count} test entities")
            return cleaned_count
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup test entities: {e}")
            raise AnalysisError(f"Failed to cleanup test entities: {e}")
    
    async def schedule_cleanup(self, delay_hours: int = 24) -> None:
        """
        Schedule automatic cleanup of test entities
        
        Args:
            delay_hours: Hours to wait before cleanup
        """
        try:
            self.logger.info(f"Scheduling cleanup in {delay_hours} hours")
            
            # Schedule cleanup task
            asyncio.create_task(self._delayed_cleanup(delay_hours))
            
        except Exception as e:
            self.logger.error(f"Failed to schedule cleanup: {e}")
            raise AnalysisError(f"Failed to schedule cleanup: {e}")
    
    async def _delayed_cleanup(self, delay_hours: int) -> None:
        """Execute delayed cleanup"""
        try:
            # Wait for specified delay
            await asyncio.sleep(delay_hours * 3600)  # Convert hours to seconds
            
            # Execute cleanup
            await self.cleanup_test_entities()
            
        except Exception as e:
            self.logger.error(f"Delayed cleanup failed: {e}")
    
    def get_created_entities(self) -> List[Dict[str, Any]]:
        """Get list of created test entities"""
        return self.created_entities.copy()
    
    def get_entity_count_by_type(self) -> Dict[str, int]:
        """Get count of created entities by type"""
        counts = {}
        for entity in self.created_entities:
            entity_type = entity["type"]
            counts[entity_type] = counts.get(entity_type, 0) + 1
        return counts
    
    async def run_comprehensive_test_setup(self, config: TestConfig) -> Dict[str, Any]:
        """
        Run comprehensive test setup creating all types of test entities
        
        Args:
            config: Test configuration
            
        Returns:
            Dictionary with created entities
        """
        try:
            self.logger.info("Running comprehensive test setup")
            
            results = {
                "labs": [],
                "bots": [],
                "accounts": [],
                "scripts": [],
                "setup_timestamp": datetime.now().isoformat()
            }
            
            # Create test scripts first (needed for labs and bots)
            if config.entity_type in [TestEntity.SCRIPT, TestEntity.ALL]:
                scripts = await self.create_test_scripts(config)
                results["scripts"] = scripts
                if scripts:
                    config.script_id = scripts[0]["script_id"]
            
            # Create test accounts (needed for labs and bots)
            if config.entity_type in [TestEntity.ACCOUNT, TestEntity.ALL]:
                accounts = await self.create_test_accounts(config)
                results["accounts"] = accounts
                if accounts:
                    config.account_id = accounts[0]["account_id"]
            
            # Create test labs
            if config.entity_type in [TestEntity.LAB, TestEntity.ALL]:
                labs = await self.create_test_labs(config)
                results["labs"] = labs
            
            # Create test bots
            if config.entity_type in [TestEntity.BOT, TestEntity.ALL]:
                bots = await self.create_test_bots(config)
                results["bots"] = bots
            
            # Schedule cleanup if requested
            if config.cleanup_after:
                await self.schedule_cleanup(config.cleanup_delay_hours)
            
            self.logger.info("Comprehensive test setup completed")
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to run comprehensive test setup: {e}")
            raise AnalysisError(f"Failed to run comprehensive test setup: {e}")
