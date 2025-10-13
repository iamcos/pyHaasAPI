"""
Bot Naming Service for pyHaasAPI v2

Centralized bot naming with server-specific schemas and comprehensive metrics.
Supports multiple naming strategies based on server requirements.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, Optional
from datetime import datetime

from ..core.logging import get_logger


@dataclass
class BotNamingContext:
    """Context for bot naming decisions"""
    server: str
    lab_id: str
    lab_name: str
    script_name: str
    market_tag: str
    roi_percentage: float
    win_rate: float
    max_drawdown: float
    total_trades: int
    profit_factor: float = 0.0
    sharpe_ratio: float = 0.0
    generation_idx: int = 0
    population_idx: int = 0
    backtest_id: str = ""
    account_id: str = ""


class BotNamingService:
    """
    Centralized bot naming service with server-specific schemas.
    
    Naming Strategies:
    1. Comprehensive: Full metrics with server prefix
    2. Compact: Essential metrics only
    3. Server-specific: Custom format per server
    4. Legacy: Compatible with existing v1 naming
    """
    
    def __init__(self):
        self.logger = get_logger("bot_naming_service")
        
        # Server-specific naming configurations
        self.server_configs = {
            "srv03": {
                "prefix": "srv03",
                "include_server": True,
                "include_metrics": ["roi", "win_rate", "drawdown", "trades"],
                "max_length": 100,
                "separator": " - "
            },
            "srv01": {
                "prefix": "srv01", 
                "include_server": True,
                "include_metrics": ["roi", "win_rate", "profit_factor"],
                "max_length": 80,
                "separator": " | "
            },
            "default": {
                "prefix": "",
                "include_server": False,
                "include_metrics": ["roi", "win_rate", "drawdown"],
                "max_length": 120,
                "separator": " - "
            }
        }
    
    def generate_bot_name(self, context: BotNamingContext, strategy: str = "comprehensive") -> str:
        """
        Generate bot name based on context and strategy.
        
        Args:
            context: Bot naming context with all relevant data
            strategy: Naming strategy ("comprehensive", "compact", "server-specific", "legacy")
        """
        try:
            if strategy == "comprehensive":
                return self._generate_comprehensive_name(context)
            elif strategy == "compact":
                return self._generate_compact_name(context)
            elif strategy == "server-specific":
                return self._generate_server_specific_name(context)
            elif strategy == "legacy":
                return self._generate_legacy_name(context)
            else:
                self.logger.warning(f"Unknown naming strategy: {strategy}, using comprehensive")
                return self._generate_comprehensive_name(context)
                
        except Exception as e:
            self.logger.error(f"Failed to generate bot name: {e}")
            return self._generate_fallback_name(context)
    
    def _generate_comprehensive_name(self, context: BotNamingContext) -> str:
        """Generate comprehensive bot name with all key metrics"""
        # Clean and format components
        lab_short = self._shorten_lab_name(context.lab_name, context.lab_id)
        script_clean = self._clean_script_name(context.script_name)
        
        # Format metrics
        roi_str = f"{context.roi_percentage:.1f}%"
        wr_str = f"{context.win_rate:.0f}%"
        dd_str = f"{context.max_drawdown:.1f}%"
        trades_str = f"{context.total_trades}T"
        
        # Add profit factor if available
        pf_str = ""
        if context.profit_factor > 0:
            pf_str = f" PF{context.profit_factor:.1f}"
        
        # Add generation/population if available
        pop_gen_str = ""
        if context.generation_idx > 0 or context.population_idx > 0:
            pop_gen_str = f" {context.population_idx}/{context.generation_idx}"
        
        # Build comprehensive name
        name_parts = [
            lab_short,
            script_clean,
            roi_str,
            wr_str,
            dd_str,
            trades_str
        ]
        
        if pf_str:
            name_parts.append(pf_str.strip())
        if pop_gen_str:
            name_parts.append(pop_gen_str.strip())
        
        bot_name = " - ".join(name_parts)
        
        # Add server prefix if configured
        server_config = self.server_configs.get(context.server, self.server_configs["default"])
        if server_config["include_server"] and server_config["prefix"]:
            bot_name = f"{server_config['prefix']}_{bot_name}"
        
        return self._truncate_name(bot_name, server_config["max_length"])
    
    def _generate_compact_name(self, context: BotNamingContext) -> str:
        """Generate compact bot name with essential metrics only"""
        lab_short = self._shorten_lab_name(context.lab_name, context.lab_id)
        script_clean = self._clean_script_name(context.script_name)
        
        # Essential metrics only
        roi_str = f"{context.roi_percentage:.0f}%"
        wr_str = f"{context.win_rate:.0f}%"
        
        bot_name = f"{lab_short} - {script_clean} - {roi_str} {wr_str}"
        
        # Add server prefix if needed
        server_config = self.server_configs.get(context.server, self.server_configs["default"])
        if server_config["include_server"] and server_config["prefix"]:
            bot_name = f"{server_config['prefix']}_{bot_name}"
        
        return self._truncate_name(bot_name, server_config["max_length"])
    
    def _generate_server_specific_name(self, context: BotNamingContext) -> str:
        """Generate server-specific bot name based on server configuration"""
        server_config = self.server_configs.get(context.server, self.server_configs["default"])
        
        lab_short = self._shorten_lab_name(context.lab_name, context.lab_id)
        script_clean = self._clean_script_name(context.script_name)
        
        # Build name based on server-specific metrics
        name_parts = [lab_short, script_clean]
        
        for metric in server_config["include_metrics"]:
            if metric == "roi":
                name_parts.append(f"{context.roi_percentage:.1f}%")
            elif metric == "win_rate":
                name_parts.append(f"{context.win_rate:.0f}%")
            elif metric == "drawdown":
                name_parts.append(f"{context.max_drawdown:.1f}%")
            elif metric == "trades":
                name_parts.append(f"{context.total_trades}T")
            elif metric == "profit_factor":
                if context.profit_factor > 0:
                    name_parts.append(f"PF{context.profit_factor:.1f}")
        
        bot_name = server_config["separator"].join(name_parts)
        
        # Add server prefix
        if server_config["include_server"] and server_config["prefix"]:
            bot_name = f"{server_config['prefix']}_{bot_name}"
        
        return self._truncate_name(bot_name, server_config["max_length"])
    
    def _generate_legacy_name(self, context: BotNamingContext) -> str:
        """Generate legacy-compatible bot name (v1 style)"""
        lab_short = self._shorten_lab_name(context.lab_name, context.lab_id)
        script_clean = self._clean_script_name(context.script_name)
        
        roi_str = f"{context.roi_percentage:.1f}%"
        wr_str = f"{context.win_rate*100:.0f}%"
        
        # Legacy format: LabName - ScriptName - ROI% pop/gen WR%
        pop_gen_str = f"{context.population_idx}/{context.generation_idx}" if context.generation_idx > 0 else "0/0"
        
        bot_name = f"{lab_short} - {script_clean} - {roi_str} {pop_gen_str} {wr_str}"
        
        return self._truncate_name(bot_name, 100)
    
    def _generate_fallback_name(self, context: BotNamingContext) -> str:
        """Generate fallback bot name when all else fails"""
        timestamp = datetime.now().strftime("%m%d_%H%M")
        return f"Bot_{context.lab_id[:6]}_{timestamp}"
    
    def _shorten_lab_name(self, lab_name: str, lab_id: str) -> str:
        """Shorten lab name for bot naming"""
        if not lab_name or lab_name == "Unknown":
            return f"Lab{lab_id[:6]}"
        
        # Clean lab name
        clean_name = lab_name.replace("_", " ").replace("-", " ").strip()
        
        # Take first meaningful words
        words = clean_name.split()[:2]  # First 2 words
        if words:
            return "".join(word[:3].capitalize() for word in words)
        else:
            return f"Lab{lab_id[:6]}"
    
    def _clean_script_name(self, script_name: str) -> str:
        """Clean and shorten script name"""
        if not script_name or script_name == "Unknown":
            return "Script"
        
        # Remove common prefixes and clean
        clean_name = script_name.replace("Strategy", "").replace("Bot", "").strip()
        
        # Take first meaningful words
        words = clean_name.split()[:2]  # First 2 words
        if words:
            return "".join(word[:4].capitalize() for word in words)
        else:
            return "Script"
    
    def _truncate_name(self, name: str, max_length: int) -> str:
        """Truncate name to max length while preserving readability"""
        if len(name) <= max_length:
            return name
        
        # Try to truncate at word boundaries
        truncated = name[:max_length-3]
        last_space = truncated.rfind(" ")
        if last_space > max_length * 0.7:  # If we can truncate at a reasonable word boundary
            return truncated[:last_space] + "..."
        else:
            return truncated + "..."
    
    def get_naming_suggestions(self, context: BotNamingContext) -> Dict[str, str]:
        """Get naming suggestions for all strategies"""
        return {
            "comprehensive": self._generate_comprehensive_name(context),
            "compact": self._generate_compact_name(context),
            "server-specific": self._generate_server_specific_name(context),
            "legacy": self._generate_legacy_name(context)
        }
    
    def validate_bot_name(self, name: str, server: str = "default") -> Dict[str, Any]:
        """Validate bot name against server requirements"""
        server_config = self.server_configs.get(server, self.server_configs["default"])
        
        return {
            "valid": len(name) <= server_config["max_length"],
            "length": len(name),
            "max_length": server_config["max_length"],
            "within_limits": len(name) <= server_config["max_length"],
            "suggestions": []
        }


