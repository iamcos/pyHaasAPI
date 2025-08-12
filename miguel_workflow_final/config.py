#!/usr/bin/env python3
"""
Configuration for Miguel Workflow Final
Clean, centralized configuration for the 2-stage optimization workflow
"""

from dataclasses import dataclass
from typing import Dict, List, Any

@dataclass
class WorkflowConfig:
    """Main workflow configuration"""
    
    # Workflow metadata
    name: str = "Miguel Trading Bot Optimization Workflow"
    version: str = "1.0"
    description: str = "2-stage optimization: timeframes then numerical parameters"
    
    # MCP Server configuration
    mcp_base_url: str = "http://localhost:8000"
    
    # Stage 0 configuration
    stage0_target_backtests: int = 100
    stage0_backtest_years: int = 2
    stage0_focus: str = "timeframes_and_ma_types"
    
    # Stage 1 configuration  
    stage1_target_backtests: int = 1000
    stage1_backtest_years: int = 3
    stage1_focus: str = "numerical_parameters"
    stage1_top_combinations: int = 3
    
    # Genetic algorithm settings
    genetic_max_generations: int = 20
    genetic_max_population: int = 50
    genetic_max_elites: int = 3
    genetic_mix_rate: float = 30.0
    genetic_adjust_rate: float = 25.0
    
    @property
    def total_target_backtests(self) -> int:
        """Calculate total backtests across all stages"""
        return self.stage0_target_backtests + (self.stage1_top_combinations * self.stage1_target_backtests)
    
    def get_genetic_config(self) -> Dict[str, Any]:
        """Get genetic algorithm configuration"""
        return {
            "max_generations": self.genetic_max_generations,
            "max_population": self.genetic_max_population,
            "max_elites": self.genetic_max_elites,
            "mix_rate": self.genetic_mix_rate,
            "adjust_rate": self.genetic_adjust_rate
        }

@dataclass
class LabNamingConfig:
    """Lab naming configuration following Miguel naming scheme"""
    
    # Naming template: "{version} - {script_name} - {period} {coin} ({timeframes}) - after: {details}"
    stage0_template: str = "0 - {script_name} - {period} years {coin} (timeframe_exploration) - after: initial exploration"
    stage1_template: str = "1 - {script_name} - {period} years {coin} ({timeframes}) - after: numerical_optim_rank{rank}"
    
    def generate_stage0_name(self, script_name: str, period: int, coin: str) -> str:
        """Generate Stage 0 lab name"""
        return self.stage0_template.format(
            script_name=script_name,
            period=period,
            coin=coin
        )
    
    def generate_stage1_name(self, script_name: str, period: int, coin: str, 
                           timeframes: str, rank: int) -> str:
        """Generate Stage 1 lab name"""
        return self.stage1_template.format(
            script_name=script_name,
            period=period,
            coin=coin,
            timeframes=timeframes,
            rank=rank
        )

@dataclass
class ParameterClassification:
    """Parameter classification configuration"""
    
    # Keywords for parameter classification
    timeframe_keywords: List[str] = None
    structural_keywords: List[str] = None
    numerical_indicators: List[str] = None
    
    def __post_init__(self):
        if self.timeframe_keywords is None:
            self.timeframe_keywords = ["low tf", "high tf", "timeframe", "interval"]
        
        if self.structural_keywords is None:
            self.structural_keywords = ["ma type", "indicator type", "signal type", "mode"]
        
        if self.numerical_indicators is None:
            self.numerical_indicators = ["ADX", "Stoch", "DEMA", "RSI", "BB", "ATR", "SL", "TP"]

@dataclass
class DefaultParameterRanges:
    """Default parameter ranges for common trading indicators"""
    
    # ADX parameters
    adx_trigger_min: float = 15.0
    adx_trigger_max: float = 35.0
    adx_trigger_step: float = 2.0
    
    # Stochastic parameters
    stoch_oversold_min: float = 10.0
    stoch_oversold_max: float = 30.0
    stoch_oversold_step: float = 5.0
    
    stoch_overbought_min: float = 70.0
    stoch_overbought_max: float = 90.0
    stoch_overbought_step: float = 5.0
    
    # DEMA parameters
    dema_fast_min: float = 5.0
    dema_fast_max: float = 20.0
    dema_fast_step: float = 2.0
    
    dema_slow_min: float = 20.0
    dema_slow_max: float = 50.0
    dema_slow_step: float = 5.0
    
    # Risk management parameters
    small_percentage_multiplier: float = 2.0
    large_percentage_multiplier: float = 1.5
    cooldown_multiplier: float = 2.0
    
    def get_parameter_range(self, param_key: str, current_value: float) -> Dict[str, Any]:
        """Get parameter range based on parameter key and current value"""
        param_key_lower = param_key.lower()
        
        # ADX parameters
        if "adx" in param_key_lower and "trigger" in param_key_lower:
            return {
                "min": self.adx_trigger_min,
                "max": self.adx_trigger_max,
                "step": self.adx_trigger_step,
                "type": "adx_trigger"
            }
        
        # Stochastic parameters
        elif "stoch" in param_key_lower and "low" in param_key_lower:
            return {
                "min": self.stoch_oversold_min,
                "max": self.stoch_oversold_max,
                "step": self.stoch_oversold_step,
                "type": "stoch_oversold"
            }
        elif "stoch" in param_key_lower and "high" in param_key_lower:
            return {
                "min": self.stoch_overbought_min,
                "max": self.stoch_overbought_max,
                "step": self.stoch_overbought_step,
                "type": "stoch_overbought"
            }
        
        # DEMA parameters
        elif "dema" in param_key_lower and "fast" in param_key_lower:
            return {
                "min": self.dema_fast_min,
                "max": self.dema_fast_max,
                "step": self.dema_fast_step,
                "type": "fast_period"
            }
        elif "dema" in param_key_lower and "slow" in param_key_lower:
            return {
                "min": self.dema_slow_min,
                "max": self.dema_slow_max,
                "step": self.dema_slow_step,
                "type": "slow_period"
            }
        
        # Risk management percentages
        elif any(keyword in param_key_lower for keyword in ["sl", "tp"]) and "%" in param_key_lower:
            if current_value <= 10:
                return {
                    "min": max(1, current_value * 0.5),
                    "max": current_value * self.small_percentage_multiplier,
                    "step": 1,
                    "type": "small_percentage"
                }
            else:
                return {
                    "min": max(10, current_value * 0.7),
                    "max": current_value * self.large_percentage_multiplier,
                    "step": 5,
                    "type": "large_percentage"
                }
        
        # Cooldown periods
        elif "colldown" in param_key_lower or "reset" in param_key_lower:
            return {
                "min": max(10, current_value * 0.5),
                "max": current_value * self.cooldown_multiplier,
                "step": 10,
                "type": "cooldown_period"
            }
        
        # General numerical parameters
        else:
            if current_value <= 1:
                return {"min": 0.1, "max": 2.0, "step": 0.1, "type": "small_decimal"}
            elif current_value <= 10:
                return {"min": 1, "max": 20, "step": 1, "type": "small_integer"}
            elif current_value <= 100:
                return {"min": max(5, current_value * 0.5), "max": current_value * 2, "step": 5, "type": "medium_value"}
            else:
                return {"min": max(10, current_value * 0.7), "max": current_value * 1.5, "step": 10, "type": "large_value"}

# Global configuration instances
WORKFLOW_CONFIG = WorkflowConfig()
NAMING_CONFIG = LabNamingConfig()
PARAMETER_CLASSIFICATION = ParameterClassification()
DEFAULT_RANGES = DefaultParameterRanges()

def get_workflow_summary() -> Dict[str, Any]:
    """Get complete workflow configuration summary"""
    return {
        "workflow": {
            "name": WORKFLOW_CONFIG.name,
            "version": WORKFLOW_CONFIG.version,
            "description": WORKFLOW_CONFIG.description,
            "total_target_backtests": WORKFLOW_CONFIG.total_target_backtests
        },
        "stage0": {
            "target_backtests": WORKFLOW_CONFIG.stage0_target_backtests,
            "backtest_years": WORKFLOW_CONFIG.stage0_backtest_years,
            "focus": WORKFLOW_CONFIG.stage0_focus
        },
        "stage1": {
            "target_backtests": WORKFLOW_CONFIG.stage1_target_backtests,
            "backtest_years": WORKFLOW_CONFIG.stage1_backtest_years,
            "focus": WORKFLOW_CONFIG.stage1_focus,
            "top_combinations": WORKFLOW_CONFIG.stage1_top_combinations
        },
        "genetic_algorithm": WORKFLOW_CONFIG.get_genetic_config(),
        "parameter_classification": {
            "timeframe_keywords": PARAMETER_CLASSIFICATION.timeframe_keywords,
            "structural_keywords": PARAMETER_CLASSIFICATION.structural_keywords,
            "numerical_indicators": PARAMETER_CLASSIFICATION.numerical_indicators
        }
    }

if __name__ == "__main__":
    """Display configuration summary"""
    import json
    
    print("🔧 Miguel Workflow Final - Configuration Summary")
    print("=" * 60)
    
    summary = get_workflow_summary()
    print(json.dumps(summary, indent=2))
    
    print(f"\n📊 Workflow Overview:")
    print(f"   Name: {WORKFLOW_CONFIG.name}")
    print(f"   Version: {WORKFLOW_CONFIG.version}")
    print(f"   Total Target Backtests: {WORKFLOW_CONFIG.total_target_backtests:,}")
    
    print(f"\n🔍 Stage 0 (Timeframe Exploration):")
    print(f"   Target Backtests: {WORKFLOW_CONFIG.stage0_target_backtests}")
    print(f"   Period: {WORKFLOW_CONFIG.stage0_backtest_years} years")
    print(f"   Focus: {WORKFLOW_CONFIG.stage0_focus}")
    
    print(f"\n🧬 Stage 1 (Numerical Optimization):")
    print(f"   Target Backtests per Lab: {WORKFLOW_CONFIG.stage1_target_backtests:,}")
    print(f"   Number of Labs: {WORKFLOW_CONFIG.stage1_top_combinations}")
    print(f"   Total Stage 1 Backtests: {WORKFLOW_CONFIG.stage1_top_combinations * WORKFLOW_CONFIG.stage1_target_backtests:,}")
    print(f"   Period: {WORKFLOW_CONFIG.stage1_backtest_years} years")
    print(f"   Focus: {WORKFLOW_CONFIG.stage1_focus}")
    
    print(f"\n🧬 Genetic Algorithm:")
    ga_config = WORKFLOW_CONFIG.get_genetic_config()
    print(f"   Generations: {ga_config['max_generations']}")
    print(f"   Population: {ga_config['max_population']}")
    print(f"   Elites: {ga_config['max_elites']}")
    print(f"   Mix Rate: {ga_config['mix_rate']}%")
    print(f"   Adjust Rate: {ga_config['adjust_rate']}%")