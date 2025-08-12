#!/usr/bin/env python3
"""
Lab Configuration System

This module provides comprehensive lab configuration management for the
distributed trading bot testing automation system, including algorithm
configuration, population settings, and execution management.
"""

import logging
import time
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

class LabAlgorithm(Enum):
    """Lab optimization algorithms"""
    BRUTE_FORCE = "BruteForce"
    INTELLIGENT = "Intelligent"
    GENETIC = "Genetic"
    RANDOM = "Random"

class LabStatus(Enum):
    """Lab execution status"""
    CREATED = "created"
    CONFIGURED = "configured"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ERROR = "error"

@dataclass
class LabAlgorithmConfig:
    """Configuration for lab optimization algorithm"""
    algorithm: LabAlgorithm
    max_population: int
    max_generations: int
    max_elites: int = 3
    mix_rate: float = 40.0
    adjust_rate: float = 25.0
    max_runtime: int = 0  # 0 = unlimited
    auto_restart: int = 0
    max_possibilities: int = 1000

@dataclass
class LabExecutionConfig:
    """Configuration for lab execution"""
    start_unix: int
    end_unix: int
    send_email: bool = False
    priority: int = 1
    timeout_minutes: int = 0  # 0 = no timeout
    retry_on_failure: bool = True
    max_retries: int = 3

@dataclass
class LabMarketConfig:
    """Configuration for lab market settings"""
    market_tag: str
    exchange_code: str
    interval: int = 15  # minutes
    chart_style: int = 300
    price_data_style: str = "CandleStick"
    leverage: float = 0.0
    position_mode: int = 0  # 0=ONE_WAY, 1=HEDGE
    margin_mode: int = 0   # 0=CROSS, 1=ISOLATED

@dataclass
class LabAccountConfig:
    """Configuration for lab account settings"""
    account_id: str
    trade_amount: float = 100.0
    order_template: int = 500
    risk_management: Dict[str, Any] = None

@dataclass
class LabConfiguration:
    """Complete lab configuration"""
    lab_id: str
    lab_name: str
    script_id: str
    server_id: str
    algorithm_config: LabAlgorithmConfig
    execution_config: LabExecutionConfig
    market_config: LabMarketConfig
    account_config: LabAccountConfig
    custom_parameters: Dict[str, Any] = None
    created_time: float = None
    last_modified: float = None
    status: LabStatus = LabStatus.CREATED

class LabConfigurationTemplate:
    """Template for creating lab configurations"""
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.default_algorithm_config = LabAlgorithmConfig(
            algorithm=LabAlgorithm.INTELLIGENT,
            max_population=50,
            max_generations=100,
            max_elites=3,
            mix_rate=40.0,
            adjust_rate=25.0,
            max_runtime=0,
            auto_restart=0,
            max_possibilities=1000
        )
        self.default_market_config = LabMarketConfig(
            market_tag="",
            exchange_code="",
            interval=15,
            chart_style=300,
            price_data_style="CandleStick",
            leverage=0.0,
            position_mode=0,
            margin_mode=0
        )
        self.default_account_config = LabAccountConfig(
            account_id="",
            trade_amount=100.0,
            order_template=500
        )
    
    def create_configuration(
        self,
        lab_id: str,
        lab_name: str,
        script_id: str,
        server_id: str,
        market_tag: str,
        exchange_code: str,
        account_id: str,
        **overrides
    ) -> LabConfiguration:
        """
        Create a lab configuration from this template.
        
        Args:
            lab_id: Lab identifier
            lab_name: Lab name
            script_id: Script identifier
            server_id: Server identifier
            market_tag: Market tag
            exchange_code: Exchange code
            account_id: Account identifier
            **overrides: Override values for configuration
            
        Returns:
            LabConfiguration object
        """
        # Create algorithm config with overrides
        algorithm_config = LabAlgorithmConfig(
            algorithm=overrides.get('algorithm', self.default_algorithm_config.algorithm),
            max_population=overrides.get('max_population', self.default_algorithm_config.max_population),
            max_generations=overrides.get('max_generations', self.default_algorithm_config.max_generations),
            max_elites=overrides.get('max_elites', self.default_algorithm_config.max_elites),
            mix_rate=overrides.get('mix_rate', self.default_algorithm_config.mix_rate),
            adjust_rate=overrides.get('adjust_rate', self.default_algorithm_config.adjust_rate),
            max_runtime=overrides.get('max_runtime', self.default_algorithm_config.max_runtime),
            auto_restart=overrides.get('auto_restart', self.default_algorithm_config.auto_restart),
            max_possibilities=overrides.get('max_possibilities', self.default_algorithm_config.max_possibilities)
        )
        
        # Create execution config
        execution_config = LabExecutionConfig(
            start_unix=overrides.get('start_unix', int(time.time()) - 86400 * 365 * 2),  # 2 years ago
            end_unix=overrides.get('end_unix', int(time.time())),  # Now
            send_email=overrides.get('send_email', False),
            priority=overrides.get('priority', 1),
            timeout_minutes=overrides.get('timeout_minutes', 0),
            retry_on_failure=overrides.get('retry_on_failure', True),
            max_retries=overrides.get('max_retries', 3)
        )
        
        # Create market config
        market_config = LabMarketConfig(
            market_tag=market_tag,
            exchange_code=exchange_code,
            interval=overrides.get('interval', self.default_market_config.interval),
            chart_style=overrides.get('chart_style', self.default_market_config.chart_style),
            price_data_style=overrides.get('price_data_style', self.default_market_config.price_data_style),
            leverage=overrides.get('leverage', self.default_market_config.leverage),
            position_mode=overrides.get('position_mode', self.default_market_config.position_mode),
            margin_mode=overrides.get('margin_mode', self.default_market_config.margin_mode)
        )
        
        # Create account config
        account_config = LabAccountConfig(
            account_id=account_id,
            trade_amount=overrides.get('trade_amount', self.default_account_config.trade_amount),
            order_template=overrides.get('order_template', self.default_account_config.order_template),
            risk_management=overrides.get('risk_management')
        )
        
        return LabConfiguration(
            lab_id=lab_id,
            lab_name=lab_name,
            script_id=script_id,
            server_id=server_id,
            algorithm_config=algorithm_config,
            execution_config=execution_config,
            market_config=market_config,
            account_config=account_config,
            custom_parameters=overrides.get('custom_parameters'),
            created_time=time.time(),
            last_modified=time.time(),
            status=LabStatus.CREATED
        )

class LabConfigurator:
    """Main lab configuration management system"""
    
    def __init__(self):
        self.templates = self._initialize_templates()
        self.configurations: Dict[str, LabConfiguration] = {}
        self.server_configs: Dict[str, Dict[str, int]] = {}  # server_id -> config limits
    
    def _initialize_templates(self) -> Dict[str, LabConfigurationTemplate]:
        """Initialize configuration templates"""
        templates = {}
        
        # Standard backtesting template
        standard_template = LabConfigurationTemplate(
            "standard_backtest",
            "Standard backtesting configuration for 2-year historical data"
        )
        templates["standard"] = standard_template
        
        # High-frequency template
        hf_template = LabConfigurationTemplate(
            "high_frequency",
            "High-frequency backtesting with smaller populations"
        )
        hf_template.default_algorithm_config.max_population = 30
        hf_template.default_algorithm_config.max_generations = 50
        hf_template.default_market_config.interval = 1  # 1 minute
        templates["high_frequency"] = hf_template
        
        # Extended optimization template
        extended_template = LabConfigurationTemplate(
            "extended_optimization",
            "Extended optimization for 3-year historical data with larger populations"
        )
        extended_template.default_algorithm_config.max_population = 100
        extended_template.default_algorithm_config.max_generations = 200
        extended_template.default_algorithm_config.max_possibilities = 2000
        templates["extended"] = extended_template
        
        # Futures trading template
        futures_template = LabConfigurationTemplate(
            "futures_trading",
            "Futures trading configuration with leverage and position management"
        )
        futures_template.default_market_config.leverage = 20.0
        futures_template.default_market_config.position_mode = 1  # HEDGE
        futures_template.default_market_config.margin_mode = 0   # CROSS
        templates["futures"] = futures_template
        
        return templates
    
    def register_server_config(self, server_id: str, max_population: int, max_concurrent_tasks: int):
        """
        Register server configuration limits.
        
        Args:
            server_id: Server identifier
            max_population: Maximum population for this server
            max_concurrent_tasks: Maximum concurrent tasks
        """
        self.server_configs[server_id] = {
            'max_population': max_population,
            'max_concurrent_tasks': max_concurrent_tasks
        }
        logger.info(f"Registered server config for {server_id}: pop={max_population}, tasks={max_concurrent_tasks}")
    
    def create_lab_configuration(
        self,
        template_name: str,
        lab_id: str,
        lab_name: str,
        script_id: str,
        server_id: str,
        market_tag: str,
        exchange_code: str,
        account_id: str,
        **overrides
    ) -> LabConfiguration:
        """
        Create a lab configuration from a template.
        
        Args:
            template_name: Name of the template to use
            lab_id: Lab identifier
            lab_name: Lab name
            script_id: Script identifier
            server_id: Server identifier
            market_tag: Market tag
            exchange_code: Exchange code
            account_id: Account identifier
            **overrides: Override values for configuration
            
        Returns:
            LabConfiguration object
        """
        if template_name not in self.templates:
            raise ValueError(f"Unknown template: {template_name}")
        
        template = self.templates[template_name]
        
        # Apply server-specific limits
        if server_id in self.server_configs:
            server_config = self.server_configs[server_id]
            max_server_population = server_config['max_population']
            
            # Ensure population doesn't exceed server limits
            if 'max_population' not in overrides:
                overrides['max_population'] = min(
                    template.default_algorithm_config.max_population,
                    max_server_population
                )
            else:
                overrides['max_population'] = min(overrides['max_population'], max_server_population)
        
        # Create configuration
        config = template.create_configuration(
            lab_id=lab_id,
            lab_name=lab_name,
            script_id=script_id,
            server_id=server_id,
            market_tag=market_tag,
            exchange_code=exchange_code,
            account_id=account_id,
            **overrides
        )
        
        # Store configuration
        self.configurations[lab_id] = config
        
        logger.info(f"Created lab configuration {lab_id} using template {template_name}")
        return config
    
    def update_lab_configuration(self, lab_id: str, **updates) -> Optional[LabConfiguration]:
        """
        Update an existing lab configuration.
        
        Args:
            lab_id: Lab identifier
            **updates: Fields to update
            
        Returns:
            Updated LabConfiguration or None if not found
        """
        if lab_id not in self.configurations:
            logger.error(f"Lab configuration {lab_id} not found")
            return None
        
        config = self.configurations[lab_id]
        
        # Update algorithm config
        if any(key.startswith('algorithm_') for key in updates):
            for key, value in updates.items():
                if key.startswith('algorithm_'):
                    field_name = key.replace('algorithm_', '')
                    if hasattr(config.algorithm_config, field_name):
                        setattr(config.algorithm_config, field_name, value)
        
        # Update execution config
        if any(key.startswith('execution_') for key in updates):
            for key, value in updates.items():
                if key.startswith('execution_'):
                    field_name = key.replace('execution_', '')
                    if hasattr(config.execution_config, field_name):
                        setattr(config.execution_config, field_name, value)
        
        # Update market config
        if any(key.startswith('market_') for key in updates):
            for key, value in updates.items():
                if key.startswith('market_'):
                    field_name = key.replace('market_', '')
                    if hasattr(config.market_config, field_name):
                        setattr(config.market_config, field_name, value)
        
        # Update account config
        if any(key.startswith('account_') for key in updates):
            for key, value in updates.items():
                if key.startswith('account_'):
                    field_name = key.replace('account_', '')
                    if hasattr(config.account_config, field_name):
                        setattr(config.account_config, field_name, value)
        
        # Update top-level fields
        for key, value in updates.items():
            if not key.startswith(('algorithm_', 'execution_', 'market_', 'account_')):
                if hasattr(config, key):
                    setattr(config, key, value)
        
        # Update modification time
        config.last_modified = time.time()
        
        logger.info(f"Updated lab configuration {lab_id}")
        return config
    
    def configure_lab_algorithm(
        self,
        lab_id: str,
        algorithm: LabAlgorithm,
        max_possibilities: int = 1000,
        **algorithm_params
    ) -> bool:
        """
        Configure lab optimization algorithm.
        
        Args:
            lab_id: Lab identifier
            algorithm: Algorithm type
            max_possibilities: Maximum possibilities for optimization
            **algorithm_params: Additional algorithm parameters
            
        Returns:
            True if successful, False otherwise
        """
        if lab_id not in self.configurations:
            logger.error(f"Lab configuration {lab_id} not found")
            return False
        
        config = self.configurations[lab_id]
        
        # Update algorithm configuration
        config.algorithm_config.algorithm = algorithm
        config.algorithm_config.max_possibilities = max_possibilities
        
        # Update additional parameters
        for param, value in algorithm_params.items():
            if hasattr(config.algorithm_config, param):
                setattr(config.algorithm_config, param, value)
        
        config.last_modified = time.time()
        
        logger.info(f"Configured {algorithm.value} algorithm for lab {lab_id}")
        return True
    
    def update_lab_market(self, lab_id: str, market_tag: str, exchange_code: str = None) -> bool:
        """
        Update lab market configuration.
        
        Args:
            lab_id: Lab identifier
            market_tag: New market tag
            exchange_code: Optional exchange code
            
        Returns:
            True if successful, False otherwise
        """
        if lab_id not in self.configurations:
            logger.error(f"Lab configuration {lab_id} not found")
            return False
        
        config = self.configurations[lab_id]
        config.market_config.market_tag = market_tag
        
        if exchange_code:
            config.market_config.exchange_code = exchange_code
        
        config.last_modified = time.time()
        
        logger.info(f"Updated market for lab {lab_id} to {market_tag}")
        return True
    
    def set_lab_execution_timeframe(
        self,
        lab_id: str,
        start_unix: int,
        end_unix: int,
        **execution_params
    ) -> bool:
        """
        Set lab execution timeframe.
        
        Args:
            lab_id: Lab identifier
            start_unix: Start timestamp
            end_unix: End timestamp
            **execution_params: Additional execution parameters
            
        Returns:
            True if successful, False otherwise
        """
        if lab_id not in self.configurations:
            logger.error(f"Lab configuration {lab_id} not found")
            return False
        
        config = self.configurations[lab_id]
        config.execution_config.start_unix = start_unix
        config.execution_config.end_unix = end_unix
        
        # Update additional parameters
        for param, value in execution_params.items():
            if hasattr(config.execution_config, param):
                setattr(config.execution_config, param, value)
        
        config.last_modified = time.time()
        
        # Calculate timeframe for logging
        days = (end_unix - start_unix) / 86400
        logger.info(f"Set execution timeframe for lab {lab_id}: {days:.1f} days")
        return True
    
    def get_lab_configuration(self, lab_id: str) -> Optional[LabConfiguration]:
        """
        Get lab configuration.
        
        Args:
            lab_id: Lab identifier
            
        Returns:
            LabConfiguration or None if not found
        """
        return self.configurations.get(lab_id)
    
    def get_all_configurations(self, server_id: str = None) -> List[LabConfiguration]:
        """
        Get all lab configurations, optionally filtered by server.
        
        Args:
            server_id: Optional server filter
            
        Returns:
            List of LabConfiguration objects
        """
        if server_id:
            return [config for config in self.configurations.values() if config.server_id == server_id]
        else:
            return list(self.configurations.values())
    
    def validate_configuration(self, lab_id: str) -> Tuple[bool, List[str]]:
        """
        Validate a lab configuration.
        
        Args:
            lab_id: Lab identifier
            
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        if lab_id not in self.configurations:
            return False, [f"Configuration {lab_id} not found"]
        
        config = self.configurations[lab_id]
        issues = []
        
        # Validate algorithm config
        if config.algorithm_config.max_population <= 0:
            issues.append("Max population must be positive")
        
        if config.algorithm_config.max_generations <= 0:
            issues.append("Max generations must be positive")
        
        if not (0 <= config.algorithm_config.mix_rate <= 100):
            issues.append("Mix rate must be between 0 and 100")
        
        if not (0 <= config.algorithm_config.adjust_rate <= 100):
            issues.append("Adjust rate must be between 0 and 100")
        
        # Validate execution config
        if config.execution_config.start_unix >= config.execution_config.end_unix:
            issues.append("Start time must be before end time")
        
        # Validate market config
        if not config.market_config.market_tag:
            issues.append("Market tag is required")
        
        if not config.market_config.exchange_code:
            issues.append("Exchange code is required")
        
        if config.market_config.interval <= 0:
            issues.append("Interval must be positive")
        
        # Validate account config
        if not config.account_config.account_id:
            issues.append("Account ID is required")
        
        if config.account_config.trade_amount <= 0:
            issues.append("Trade amount must be positive")
        
        # Server-specific validation
        if config.server_id in self.server_configs:
            server_limits = self.server_configs[config.server_id]
            if config.algorithm_config.max_population > server_limits['max_population']:
                issues.append(f"Population {config.algorithm_config.max_population} exceeds server limit {server_limits['max_population']}")
        
        return len(issues) == 0, issues
    
    def export_configuration(self, lab_id: str) -> Optional[Dict[str, Any]]:
        """
        Export lab configuration to dictionary.
        
        Args:
            lab_id: Lab identifier
            
        Returns:
            Configuration dictionary or None if not found
        """
        if lab_id not in self.configurations:
            return None
        
        config = self.configurations[lab_id]
        return asdict(config)
    
    def import_configuration(self, config_dict: Dict[str, Any]) -> LabConfiguration:
        """
        Import lab configuration from dictionary.
        
        Args:
            config_dict: Configuration dictionary
            
        Returns:
            LabConfiguration object
        """
        # Reconstruct nested objects
        algorithm_config = LabAlgorithmConfig(**config_dict['algorithm_config'])
        execution_config = LabExecutionConfig(**config_dict['execution_config'])
        market_config = LabMarketConfig(**config_dict['market_config'])
        account_config = LabAccountConfig(**config_dict['account_config'])
        
        # Create configuration
        config = LabConfiguration(
            lab_id=config_dict['lab_id'],
            lab_name=config_dict['lab_name'],
            script_id=config_dict['script_id'],
            server_id=config_dict['server_id'],
            algorithm_config=algorithm_config,
            execution_config=execution_config,
            market_config=market_config,
            account_config=account_config,
            custom_parameters=config_dict.get('custom_parameters'),
            created_time=config_dict.get('created_time'),
            last_modified=config_dict.get('last_modified'),
            status=LabStatus(config_dict.get('status', 'created'))
        )
        
        # Store configuration
        self.configurations[config.lab_id] = config
        
        return config
    
    def get_configuration_summary(self) -> Dict[str, Any]:
        """Get summary of all configurations"""
        total_configs = len(self.configurations)
        
        # Group by status
        status_counts = {}
        for config in self.configurations.values():
            status = config.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Group by server
        server_counts = {}
        for config in self.configurations.values():
            server = config.server_id
            server_counts[server] = server_counts.get(server, 0) + 1
        
        # Group by algorithm
        algorithm_counts = {}
        for config in self.configurations.values():
            algorithm = config.algorithm_config.algorithm.value
            algorithm_counts[algorithm] = algorithm_counts.get(algorithm, 0) + 1
        
        return {
            'total_configurations': total_configs,
            'status_distribution': status_counts,
            'server_distribution': server_counts,
            'algorithm_distribution': algorithm_counts,
            'available_templates': list(self.templates.keys()),
            'registered_servers': list(self.server_configs.keys())
        }

def main():
    """Test the lab configuration system"""
    print("Testing Lab Configuration System...")
    print("=" * 50)
    
    # Initialize configurator
    configurator = LabConfigurator()
    
    # Register server configurations
    configurator.register_server_config("srv01", 50, 5)
    configurator.register_server_config("srv02", 30, 3)
    configurator.register_server_config("srv03", 20, 2)
    
    print("1. Testing configuration creation:")
    
    # Create standard configuration
    config = configurator.create_lab_configuration(
        template_name="standard",
        lab_id="test-lab-001",
        lab_name="Test Standard Lab",
        script_id="script-123",
        server_id="srv01",
        market_tag="BINANCEFUTURES_BTC_USDT_PERPETUAL",
        exchange_code="BINANCEFUTURES",
        account_id="account-456"
    )
    
    print(f"  ✓ Created standard config: {config.lab_name}")
    print(f"    Algorithm: {config.algorithm_config.algorithm.value}")
    print(f"    Population: {config.algorithm_config.max_population}")
    print(f"    Market: {config.market_config.market_tag}")
    
    # Create futures configuration
    futures_config = configurator.create_lab_configuration(
        template_name="futures",
        lab_id="test-lab-002",
        lab_name="Test Futures Lab",
        script_id="script-123",
        server_id="srv02",
        market_tag="BINANCEQUARTERLY_ETH_USD_PERPETUAL",
        exchange_code="BINANCEQUARTERLY",
        account_id="account-789",
        max_population=25  # Override default
    )
    
    print(f"  ✓ Created futures config: {futures_config.lab_name}")
    print(f"    Leverage: {futures_config.market_config.leverage}")
    print(f"    Position Mode: {futures_config.market_config.position_mode}")
    print(f"    Population: {futures_config.algorithm_config.max_population}")
    
    print("\n2. Testing configuration updates:")
    
    # Update algorithm
    success = configurator.configure_lab_algorithm(
        "test-lab-001",
        LabAlgorithm.BRUTE_FORCE,
        max_possibilities=500
    )
    print(f"  ✓ Algorithm update: {success}")
    
    # Update market
    success = configurator.update_lab_market(
        "test-lab-001",
        "BINANCEFUTURES_ETH_USDT_PERPETUAL"
    )
    print(f"  ✓ Market update: {success}")
    
    # Update execution timeframe
    success = configurator.set_lab_execution_timeframe(
        "test-lab-001",
        int(time.time()) - 86400 * 365 * 3,  # 3 years ago
        int(time.time()),
        send_email=True
    )
    print(f"  ✓ Timeframe update: {success}")
    
    print("\n3. Testing configuration validation:")
    
    # Validate configurations
    for lab_id in ["test-lab-001", "test-lab-002"]:
        is_valid, issues = configurator.validate_configuration(lab_id)
        print(f"  {lab_id}: {'✓ Valid' if is_valid else '✗ Invalid'}")
        if issues:
            for issue in issues:
                print(f"    - {issue}")
    
    print("\n4. Testing configuration export/import:")
    
    # Export configuration
    exported = configurator.export_configuration("test-lab-001")
    print(f"  ✓ Exported config: {len(exported)} fields")
    
    # Import configuration with new ID
    exported['lab_id'] = "test-lab-003"
    exported['lab_name'] = "Imported Lab"
    imported_config = configurator.import_configuration(exported)
    print(f"  ✓ Imported config: {imported_config.lab_name}")
    
    print("\n5. Testing configuration summary:")
    
    summary = configurator.get_configuration_summary()
    print(f"  Total configurations: {summary['total_configurations']}")
    print(f"  Available templates: {summary['available_templates']}")
    print(f"  Registered servers: {summary['registered_servers']}")
    print(f"  Status distribution: {summary['status_distribution']}")
    print(f"  Algorithm distribution: {summary['algorithm_distribution']}")
    
    print("\n" + "=" * 50)
    print("Lab configuration system test completed!")
    print("Key features implemented:")
    print("  - Template-based configuration creation")
    print("  - Algorithm and parameter management")
    print("  - Market and execution configuration")
    print("  - Server-specific limits and validation")
    print("  - Configuration export/import")
    print("  - Comprehensive validation and reporting")

if __name__ == "__main__":
    main()