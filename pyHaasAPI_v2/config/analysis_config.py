"""
Analysis Configuration for pyHaasAPI v2

This module defines configuration settings for analysis operations,
with strict requirements for zero drawdown strategies.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class AnalysisConfig:
    """Configuration for analysis operations"""
    
    # Default filtering criteria
    min_win_rate: float = 0.3
    min_trades: int = 5
    min_roi: float = 0.0
    
    # CRITICAL: Drawdown requirements
    zero_drawdown_only: bool = True  # Default to True - never recommend negative drawdown
    allow_negative_drawdown: bool = False  # Must be explicitly enabled
    
    # Performance thresholds
    min_roi_for_recommendation: float = 50.0
    min_win_rate_for_recommendation: float = 0.6
    min_trades_for_recommendation: int = 10
    
    # Scoring weights
    roi_weight: float = 0.4
    win_rate_weight: float = 0.3
    trades_weight: float = 0.2
    drawdown_weight: float = 0.1
    
    # Analysis limits
    max_backtests_per_lab: int = 1000
    default_top_count: int = 10
    max_recommendations: int = 50
    
    # Report settings
    default_report_format: str = "csv"
    include_rejected_strategies: bool = False  # Don't include negative drawdown strategies
    
    # Logging
    log_rejected_strategies: bool = True
    log_drawdown_violations: bool = True


@dataclass
class DrawdownPolicy:
    """Strict drawdown policy configuration"""
    
    # Core policy
    reject_negative_drawdown: bool = True
    prefer_zero_drawdown: bool = True
    
    # Scoring adjustments
    zero_drawdown_bonus: float = 1.0  # Perfect score for zero drawdown
    positive_drawdown_penalty: float = 0.1  # Penalty for positive drawdown
    
    # Warning thresholds
    warn_on_positive_drawdown: bool = True
    warn_threshold: float = 5.0  # Warn if drawdown > 5%
    
    # Error messages
    rejection_message: str = "Strategy rejected due to negative drawdown"
    warning_message: str = "Strategy has positive drawdown - consider alternatives"


# Global configuration instance
DEFAULT_ANALYSIS_CONFIG = AnalysisConfig()
DEFAULT_DRAWDOWN_POLICY = DrawdownPolicy()


def get_analysis_config() -> AnalysisConfig:
    """Get the default analysis configuration"""
    return DEFAULT_ANALYSIS_CONFIG


def get_drawdown_policy() -> DrawdownPolicy:
    """Get the default drawdown policy"""
    return DEFAULT_DRAWDOWN_POLICY


def validate_drawdown_requirement(max_drawdown: float, config: Optional[AnalysisConfig] = None) -> bool:
    """
    Validate if a strategy meets drawdown requirements
    
    Args:
        max_drawdown: Maximum drawdown value
        config: Analysis configuration (uses default if None)
        
    Returns:
        True if strategy meets requirements, False otherwise
    """
    if config is None:
        config = DEFAULT_ANALYSIS_CONFIG
    
    # Always reject negative drawdown unless explicitly allowed
    if max_drawdown < 0 and not config.allow_negative_drawdown:
        return False
    
    # If zero drawdown only is required, reject positive drawdown
    if config.zero_drawdown_only and max_drawdown > 0:
        return False
    
    return True


def get_drawdown_score(max_drawdown: float, policy: Optional[DrawdownPolicy] = None) -> float:
    """
    Calculate drawdown score for recommendation scoring
    
    Args:
        max_drawdown: Maximum drawdown value
        policy: Drawdown policy (uses default if None)
        
    Returns:
        Score between 0.0 and 1.0
    """
    if policy is None:
        policy = DEFAULT_DRAWDOWN_POLICY
    
    # Reject negative drawdown
    if max_drawdown < 0:
        return 0.0
    
    # Perfect score for zero drawdown
    if max_drawdown == 0:
        return policy.zero_drawdown_bonus
    
    # Penalize positive drawdown
    penalty = min(max_drawdown / 100.0, 1.0) * policy.positive_drawdown_penalty
    return max(0.0, 1.0 - penalty)


def get_drawdown_warning(max_drawdown: float, policy: Optional[DrawdownPolicy] = None) -> Optional[str]:
    """
    Get warning message for drawdown values
    
    Args:
        max_drawdown: Maximum drawdown value
        policy: Drawdown policy (uses default if None)
        
    Returns:
        Warning message if applicable, None otherwise
    """
    if policy is None:
        policy = DEFAULT_DRAWDOWN_POLICY
    
    if max_drawdown < 0:
        return policy.rejection_message
    
    if max_drawdown > policy.warn_threshold and policy.warn_on_positive_drawdown:
        return f"{policy.warning_message}: {max_drawdown:.2f}%"
    
    return None