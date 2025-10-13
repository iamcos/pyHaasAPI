"""
ServerContentManager: Server snapshot, gap/duplicate analysis, and resumable backtest fetcher.

This service is designed to be used by thin CLIs and higher-level orchestrators.
It reuses native APIs and services and persists lightweight cache artifacts.
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from ..core.logging import get_logger
from ..api.lab import LabAPI
from ..api.bot import BotAPI
from ..api.backtest import BacktestAPI
from ..api.account import AccountAPI
from .bot_naming_service import BotNamingService, BotNamingContext


@dataclass
class SnapshotResult:
    server: str
    timestamp: str
    labs: List[Any] = field(default_factory=list)
    bots: List[Any] = field(default_factory=list)
    lab_id_to_bots: Dict[str, List[Any]] = field(default_factory=dict)
    coins: Set[str] = field(default_factory=set)
    labs_without_bots: Set[str] = field(default_factory=set)
    coins_without_labs: Set[str] = field(default_factory=set)


class ServerContentManager:
    """
    Native service for server-state snapshotting, gap/duplicate analysis,
    and resumable fetching of backtests per lab.
    """

    def __init__(
        self,
        server: str,
        lab_api: LabAPI,
        bot_api: BotAPI,
        backtest_api: BacktestAPI,
        account_api: Optional[AccountAPI] = None,
        cache_dir: Path | str = "unified_cache",
    ) -> None:
        self.server = server
        self.lab_api = lab_api
        self.bot_api = bot_api
        self.backtest_api = backtest_api
        self.account_api = account_api
        self.cache_dir = Path(cache_dir)
        self.logger = get_logger("server_content_manager")
        self._ensure_directories()
        
        # Initialize services
        self.bot_naming_service = BotNamingService()
        
        # Initialize AccountManager if account_api is provided
        self.account_manager: Optional['AccountManager'] = None
        if self.account_api:
            from .account_manager import AccountManager
            self.account_manager = AccountManager(
                account_api=self.account_api,
                server=server
            )

    def _ensure_directories(self) -> None:
        (self.cache_dir / "snapshots").mkdir(parents=True, exist_ok=True)
        (self.cache_dir / "backtests").mkdir(parents=True, exist_ok=True)

    async def snapshot(self) -> SnapshotResult:
        """
        Snapshot current server content: labs, bots, mappings, inferred coins, coverage.
        """
        self.logger.info(f"Creating server snapshot for {self.server}...")

        labs = await self._safe_list_labs()
        bots = await self._safe_list_bots()

        lab_id_to_bots: Dict[str, List[Any]] = {}
        for bot in bots:
            # Try multiple ways to link bots to labs
            linked_lab_id = None
            
            # Method 1: Direct lab_id field
            linked_lab_id = getattr(bot, "lab_id", None) or getattr(bot, "origin_lab_id", None)
            
            # Method 2: Extract from notes field (common pattern)
            if not linked_lab_id:
                notes = getattr(bot, "notes", "") or ""
                linked_lab_id = self._extract_lab_id_from_notes(notes)
            
            # Method 3: Extract from bot name (if it contains lab info)
            if not linked_lab_id:
                bot_name = getattr(bot, "bot_name", "") or getattr(bot, "name", "") or ""
                linked_lab_id = self._extract_lab_id_from_name(bot_name)
            
            # Method 4: Smart matching by script name, trading pair, and exchange
            if not linked_lab_id:
                linked_lab_id = self._match_bot_to_lab_by_characteristics(bot, labs)
            
            if linked_lab_id:
                lab_id_to_bots.setdefault(linked_lab_id, []).append(bot)
                self.logger.debug(f"Linked bot {getattr(bot, 'bot_id', 'unknown')} to lab {linked_lab_id}")
            else:
                self.logger.debug(f"Could not link bot {getattr(bot, 'bot_id', 'unknown')} to any lab")

        coins: Set[str] = set()
        for lab in labs:
            market = getattr(lab, "market_tag", None) or getattr(lab, "marketTag", None) or ""
            coin = self._extract_coin_from_market(market)
            if coin:
                coins.add(coin)

        lab_ids_with_bots = set(lab_id_to_bots.keys())
        lab_ids = {getattr(l, "lab_id", None) or getattr(l, "id", None) for l in labs if (getattr(l, "lab_id", None) or getattr(l, "id", None))}
        labs_without_bots = lab_ids - lab_ids_with_bots

        # Coins without labs: heuristic based on observed bot markets vs lab markets
        coins_from_bots: Set[str] = set()
        for bot in bots:
            market = getattr(bot, "market_tag", None) or getattr(bot, "market", None) or ""
            coin = self._extract_coin_from_market(market)
            if coin:
                coins_from_bots.add(coin)
        coins_without_labs = coins_from_bots - coins

        snapshot = SnapshotResult(
            server=self.server,
            timestamp=datetime.utcnow().isoformat(),
            labs=labs,
            bots=bots,
            lab_id_to_bots=lab_id_to_bots,
            coins=coins,
            labs_without_bots=labs_without_bots,
            coins_without_labs=coins_without_labs,
        )

        await self._persist_snapshot(snapshot)
        self.logger.info(
            f"Snapshot complete: labs={len(labs)} bots={len(bots)} labs_without_bots={len(labs_without_bots)}"
        )
        return snapshot

    async def fetch_backtests_for_labs(self, lab_ids: List[str], count: int = 5, resume: bool = True) -> Dict[str, int]:
        """
        Download up to `count` backtests per lab using two-step pattern:
        1. Fetch backtest summaries (paginated)
        2. Fetch and cache runtime data for top performers
        
        Returns mapping lab_id -> num_backtests_cached.
        """
        results: Dict[str, int] = {}
        
        for lab_id in lab_ids:
            try:
                # Check existing cached runtime data files
                backtest_cache_dir = self.cache_dir / "backtest_cache" / "backtests"
                backtest_cache_dir.mkdir(parents=True, exist_ok=True)
                
                cached_ids = set()
                if resume:
                    # Find existing cached runtime data files for this lab
                    pattern = f"{lab_id}_*.json"
                    existing_files = list(backtest_cache_dir.glob(pattern))
                    for file in existing_files:
                        # Extract backtest_id from filename: lab_id_backtest_id.json
                        parts = file.stem.split('_', 1)
                        if len(parts) == 2:
                            cached_ids.add(parts[1])
                    self.logger.info(f"Found {len(cached_ids)} existing cached backtests for lab {lab_id[:8]}")
                
                # Step 1: Fetch all backtest summaries with pagination
                all_summaries = []
                next_page_id = 0
                page_length = 1000  # Large page size for efficiency
                
                while True:
                    try:
                        page = await self.backtest_api.get_backtest_result(
                            lab_id=lab_id,
                            next_page_id=next_page_id,
                            page_length=page_length
                        )
                    except Exception as e:
                        self.logger.warning(f"Failed to fetch backtest summaries for {lab_id[:8]} page {next_page_id}: {e}")
                        break
                    
                    items = getattr(page, "items", []) or []
                    if items:
                        all_summaries.extend(items)
                        self.logger.debug(f"Fetched {len(items)} summaries, total: {len(all_summaries)}")
                    
                    # Check pagination
                    has_more = getattr(page, "has_next", False) or getattr(page, "hasNext", False)
                    if not has_more or not items:
                        break
                    
                    next_page_id = getattr(page, "next_page_id", None)
                    if next_page_id is None:
                        break
                
                self.logger.info(f"Fetched {len(all_summaries)} backtest summaries for lab {lab_id[:8]}")
                
                if not all_summaries:
                    results[lab_id] = len(cached_ids)
                    continue
                
                # Step 2: Sort by ROI to get top performers
                sorted_summaries = sorted(
                    all_summaries,
                    key=lambda x: getattr(x, 'roi', getattr(x, 'roi_percentage', 0)),
                    reverse=True
                )
                
                # Step 3: Fetch runtime data for top N (skipping already cached)
                cached_count = len(cached_ids)
                new_cached = 0
                
                for i, summary in enumerate(sorted_summaries):
                    if cached_count >= count:
                        break
                    
                    backtest_id = getattr(summary, 'backtest_id', None) or getattr(summary, 'id', None)
                    if not backtest_id:
                        continue
                    
                    if backtest_id in cached_ids:
                        continue
                    
                    try:
                        # Fetch full runtime data
                        runtime_data = await self.backtest_api.get_backtest_runtime(
                            lab_id=lab_id,
                            backtest_id=backtest_id
                        )
                        
                        # Cache it in the format expected by CachedAnalysisService
                        cache_file = backtest_cache_dir / f"{lab_id}_{backtest_id}.json"
                        with open(cache_file, 'w') as f:
                            json.dump(runtime_data, f, indent=2, default=str)
                        
                        cached_ids.add(backtest_id)
                        cached_count += 1
                        new_cached += 1
                        
                        if new_cached % 10 == 0:
                            self.logger.info(f"Cached {new_cached} new backtests for lab {lab_id[:8]}")
                    
                    except Exception as e:
                        self.logger.warning(f"Failed to fetch/cache runtime data for backtest {backtest_id[:8]}: {e}")
                        continue
                
                results[lab_id] = cached_count
                self.logger.info(f"✅ Lab {lab_id[:8]}: {len(all_summaries)} summaries → {new_cached} new cached → {cached_count} total cached")
            
            except Exception as e:
                self.logger.error(f"Failed to process lab {lab_id[:8]}: {e}")
                results[lab_id] = 0
        
        return results

    def detect_duplicate_bots(self, bots: List[Any]) -> Dict[str, List[str]]:
        """
        Detect potential duplicates by name and origin backtest ID (if present in notes).
        Returns mapping of duplicate_key -> list of bot_ids.
        """
        duplicates: Dict[str, List[str]] = {}
        name_to_ids: Dict[str, List[str]] = {}
        origin_to_ids: Dict[str, List[str]] = {}

        for bot in bots:
            bot_id = getattr(bot, "bot_id", None) or getattr(bot, "id", None)
            name = getattr(bot, "bot_name", None) or getattr(bot, "name", None)
            if name and bot_id:
                key = name.strip().lower()
                name_to_ids.setdefault(key, []).append(bot_id)

            # Try parse origin data from notes
            notes_raw = getattr(bot, "notes", None) or ""
            origin_bt_id = self._extract_origin_backtest_id(notes_raw)
            if origin_bt_id and bot_id:
                origin_to_ids.setdefault(origin_bt_id, []).append(bot_id)

        for key, ids in name_to_ids.items():
            if len(ids) > 1:
                duplicates[f"name:{key}"] = ids
        for key, ids in origin_to_ids.items():
            if len(ids) > 1:
                duplicates[f"origin_bt:{key}"] = ids

        return duplicates

    async def compute_creation_skips(
        self,
        analysis_results: Dict[str, Any],
        existing_bots: List[Any],
    ) -> Set[Tuple[str, str]]:
        """
        Decide which (lab_id, backtest_id) pairs should be skipped based on existing bots.
        Returns a set of pairs to skip.
        """
        skip_pairs: Set[Tuple[str, str]] = set()

        # Build fast lookup from existing bots by origin bt id and by bot name
        existing_by_name = { (getattr(b, "bot_name", None) or getattr(b, "name", "")).strip().lower(): b for b in existing_bots if (getattr(b, "bot_name", None) or getattr(b, "name", None)) }
        existing_by_origin_bt: Set[str] = set()
        for b in existing_bots:
            origin_bt = self._extract_origin_backtest_id(getattr(b, "notes", None) or "")
            if origin_bt:
                existing_by_origin_bt.add(origin_bt)

        for lab_id, result in analysis_results.items():
            if "error" in result:
                continue
            candidates = result.get("best_performers") or result.get("stable_backtests") or []
            for bt in candidates:
                bt_id = getattr(bt, "backtest_id", None) or getattr(bt, "id", None)
                script_name = getattr(bt, "script_name", "Unknown")
                lab_name = result.get("lab_name", f"Lab {lab_id}")
                roi = getattr(bt, "roi_percentage", 0.0)
                win_rate = getattr(bt, "win_rate", 0.0)
                # Check for duplicates by origin backtest ID (most reliable)
                if bt_id and bt_id in existing_by_origin_bt:
                    skip_pairs.add((lab_id, bt_id))
                    continue
                
                # Check for duplicates using enhanced naming service
                naming_context = BotNamingContext(
                    server=self.server,
                    lab_id=lab_id,
                    lab_name=lab_name,
                    script_name=script_name,
                    market_tag=getattr(bt, 'market_tag', ''),
                    roi_percentage=roi,
                    win_rate=win_rate,
                    max_drawdown=getattr(bt, 'max_drawdown', 0.0),
                    total_trades=getattr(bt, 'total_trades', 0),
                    profit_factor=getattr(bt, 'profit_factor', 0.0),
                    sharpe_ratio=getattr(bt, 'sharpe_ratio', 0.0),
                    generation_idx=getattr(bt, 'generation_idx', 0),
                    population_idx=getattr(bt, 'population_idx', 0),
                    backtest_id=bt_id,
                    account_id=""
                )
                
                # Generate expected names using different strategies
                expected_names = self.bot_naming_service.get_naming_suggestions(naming_context)
                
                # Check if any expected name matches existing bots
                for strategy, expected_name in expected_names.items():
                    if expected_name.strip().lower() in existing_by_name:
                        skip_pairs.add((lab_id, bt_id))
                        break

        return skip_pairs

    async def _persist_snapshot(self, snapshot: SnapshotResult) -> None:
        try:
            out = self.cache_dir / "snapshots" / f"{self.server}_snapshot.json"
            payload = {
                "server": snapshot.server,
                "timestamp": snapshot.timestamp,
                "labs": [self._safe_model_dump(l) for l in snapshot.labs],
                "bots": [self._safe_model_dump(b) for b in snapshot.bots],
                "lab_id_to_bots": {k: [self._safe_model_dump(b) for b in v] for k, v in snapshot.lab_id_to_bots.items()},
                "coins": sorted(list(snapshot.coins)),
                "labs_without_bots": sorted(list(snapshot.labs_without_bots)),
                "coins_without_labs": sorted(list(snapshot.coins_without_labs)),
            }
            with open(out, "w") as f:
                json.dump(payload, f, indent=2, default=str)
        except Exception as e:
            self.logger.warning(f"Failed to persist snapshot: {e}")

    def _persist_backtests(self, lab_id: str, backtests: List[Any]) -> None:
        try:
            out = self.cache_dir / "backtests" / f"{lab_id}.json"
            payload = [self._safe_model_dump(b) for b in backtests]
            with open(out, "w") as f:
                json.dump(payload, f, indent=2, default=str)
        except Exception as e:
            self.logger.warning(f"Failed to persist backtests for {lab_id[:8]}: {e}")

    def _load_cached_backtests(self, lab_id: str) -> List[Any]:
        try:
            path = self.cache_dir / "backtests" / f"{lab_id}.json"
            if not path.exists():
                return []
            with open(path, "r") as f:
                data = json.load(f)
            return data or []
        except Exception:
            return []

    async def _safe_list_labs(self) -> List[Any]:
        try:
            # Prefer full lab listing (not only completed)
            labs = await self.lab_api.get_labs()
            return labs or []
        except Exception as e:
            self.logger.warning(f"Failed to list labs: {e}")
            return []

    async def _safe_list_bots(self) -> List[Any]:
        try:
            # Use correct bot listing method
            bots = await self.bot_api.get_all_bots()
            return bots or []
        except Exception as e:
            self.logger.warning(f"Failed to list bots: {e}")
            return []

    def _safe_model_dump(self, obj: Any) -> Dict[str, Any]:
        # Pydantic models have model_dump; objects may be dict-like already
        if hasattr(obj, "model_dump"):
            return obj.model_dump()
        if isinstance(obj, dict):
            return obj
        # Fallback: extract common attributes conservatively
        fields = [
            "lab_id", "id", "name", "lab_name", "bot_id", "bot_name",
            "market", "market_tag", "script_id", "script_name", "backtest_id",
            "roi_percentage", "win_rate", "max_drawdown",
        ]
        result: Dict[str, Any] = {}
        for f in fields:
            if hasattr(obj, f):
                result[f] = getattr(obj, f)
        return result

    def _extract_coin_from_market(self, market_tag: str) -> Optional[str]:
        if not market_tag:
            return None
        try:
            # Examples: BINANCE_BTC_USDT_, BINANCEFUTURES_ETH_USDT_PERPETUAL
            parts = market_tag.split("_")
            for p in parts:
                if len(p) in (3, 4) and p.isalpha():
                    return p
        except Exception:
            return None
        return None

    def _extract_origin_backtest_id(self, notes_raw: str) -> Optional[str]:
        if not notes_raw:
            return None
        try:
            data = json.loads(notes_raw)
            origin = data.get("origin") if isinstance(data, dict) else None
            if origin and isinstance(origin, dict):
                bt = origin.get("backtest_id") or origin.get("backtestId")
                if isinstance(bt, str):
                    return bt
        except Exception:
            return None
        return None
    
    def _extract_lab_id_from_notes(self, notes: str) -> Optional[str]:
        """Extract lab ID from bot notes field"""
        if not notes:
            return None
        # Look for lab ID patterns in notes
        import re
        # Common patterns: "lab_id: xxx", "from lab: xxx", "origin: xxx"
        patterns = [
            r'lab[_-]?id[:\s]+([a-f0-9-]{36})',  # UUID pattern
            r'from[_\s]lab[:\s]+([a-f0-9-]{36})',
            r'origin[:\s]+([a-f0-9-]{36})',
            r'lab[:\s]+([a-f0-9-]{36})'
        ]
        for pattern in patterns:
            match = re.search(pattern, notes, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
    
    def _extract_lab_id_from_name(self, bot_name: str) -> Optional[str]:
        """Extract lab ID from bot name"""
        if not bot_name:
            return None
        # Look for lab ID patterns in bot name
        import re
        # Pattern for UUID in bot name
        pattern = r'([a-f0-9-]{36})'
        match = re.search(pattern, bot_name, re.IGNORECASE)
        if match:
            return match.group(1)
        return None
    
    def _match_bot_to_lab_by_characteristics(self, bot: Any, labs: List[Any]) -> Optional[str]:
        """Match bot to lab by comparing script name, trading pair, and exchange"""
        try:
            # Extract bot characteristics
            bot_name = getattr(bot, "bot_name", "") or getattr(bot, "name", "") or ""
            bot_market = getattr(bot, "market_tag", None) or getattr(bot, "market", None) or ""
            bot_script_name = getattr(bot, "script_name", None) or getattr(bot, "scriptName", None) or ""
            
            # If no script name from field, try to extract from bot name
            if not bot_script_name:
                bot_script_name = self._extract_script_name_from_bot_name(bot_name)
            
            if not bot_script_name or not bot_market:
                return None
            
            # Extract trading pair and exchange from bot market
            bot_trading_pair, bot_exchange = self._parse_market_tag(bot_market)
            
            self.logger.info(f"Bot characteristics: name='{bot_name}', script='{bot_script_name}', market='{bot_market}', pair='{bot_trading_pair}', exchange='{bot_exchange}'")
            
            # Find matching lab
            for lab in labs:
                lab_id = getattr(lab, "lab_id", None) or getattr(lab, "id", None)
                lab_name = getattr(lab, "name", None) or getattr(lab, "lab_name", None) or ""
                
                if not lab_id or not lab_name:
                    continue
                
                # Extract script name and market info from lab name
                # Lab names: "2 -  Simple RSING VWAP Strategy - XRP"
                lab_script_name = self._extract_script_name_from_lab_name(lab_name)
                lab_market = self._extract_market_from_lab_name(lab_name)
                
                if not lab_script_name or not lab_market:
                    continue
                
                # Extract trading pair and exchange from lab market
                lab_trading_pair, lab_exchange = self._parse_market_tag(lab_market)
                
                # Log lab characteristics for debugging
                self.logger.info(f"Lab characteristics: name='{lab_name}', script='{lab_script_name}', market='{lab_market}', pair='{lab_trading_pair}', exchange='{lab_exchange}'")
                
                # Check if this lab matches the bot
                if (bot_script_name.lower() == lab_script_name.lower() and 
                    bot_trading_pair == lab_trading_pair and 
                    bot_exchange == lab_exchange):
                    self.logger.info(f"🎯 MATCH FOUND: Bot '{bot_name}' matches Lab '{lab_name}'")
                    return lab_id
                
                # Check if script names match (case insensitive)
                if bot_script_name.lower() != lab_script_name.lower():
                    self.logger.info(f"Script mismatch: bot='{bot_script_name}' vs lab='{lab_script_name}'")
                    continue
                
                # Check if trading pairs match
                if bot_trading_pair != lab_trading_pair:
                    continue
                
                # Check if exchanges match
                if bot_exchange != lab_exchange:
                    continue
                
                self.logger.info(f"Matched bot to lab {lab_id}: script='{lab_script_name}', market='{lab_market}'")
                return lab_id
            
            return None
            
        except Exception as e:
            self.logger.warning(f"Error matching bot to lab: {e}")
            return None
    
    def _extract_script_name_from_bot_name(self, bot_name: str) -> Optional[str]:
        """Extract script name from bot name using naming schema patterns"""
        if not bot_name:
            return None
        
        # Common bot naming patterns:
        # "2 - Simple RSING VWAP Strategy - BCH 2139 18/35"
        # "2 - Simple RSING VWAP Strategy - BNB 1320% 34/24"
        # "2    Simple RSING VWAP Strategy   APT 11 Sept 24 -  - 1718 24/33 45%"
        
        import re
        
        # Pattern 1: "2 - Simple RSING VWAP Strategy - BCH 2139 18/35"
        # Extract everything between first dash and coin name
        pattern1 = r'^\d+\s*-\s*([^-]+?)\s*-\s*[A-Z]+\s+\d+'
        match1 = re.search(pattern1, bot_name)
        if match1:
            return self._normalize_script_name(match1.group(1).strip())
        
        # Pattern 2: "2    Simple RSING VWAP Strategy   APT 11 Sept 24 -  - 1718 24/33 45%"
        # Extract everything between first number and coin name
        pattern2 = r'^\d+\s+([^-]+?)\s+[A-Z]+\s+\d+'
        match2 = re.search(pattern2, bot_name)
        if match2:
            return self._normalize_script_name(match2.group(1).strip())
        
        # Pattern 3: "Script Name - ROI% pop/gen WinRate%"
        pattern3 = r'^([^-]+?)\s*-\s*\d+\.?\d*%\s*(?:pop/gen)?\s*\d+\.?\d*%'
        match3 = re.search(pattern3, bot_name)
        if match3:
            return self._normalize_script_name(match3.group(1).strip())
        
        # Pattern 4: "Script Name - ROI%"
        pattern4 = r'^([^-]+?)\s*-\s*\d+\.?\d*%'
        match4 = re.search(pattern4, bot_name)
        if match4:
            return self._normalize_script_name(match4.group(1).strip())
        
        # Fallback: return the part before the first dash
        parts = bot_name.split(' - ')
        if len(parts) > 1:
            return self._normalize_script_name(parts[0].strip())
        
        return None
    
    def _normalize_script_name(self, script_name: str) -> str:
        """Normalize script name by removing extra spaces and standardizing format"""
        if not script_name:
            return ""
        
        # Remove multiple spaces and replace with single space
        import re
        normalized = re.sub(r'\s+', ' ', script_name.strip())
        
        # Remove leading/trailing spaces
        return normalized.strip()
    
    def _extract_script_name_from_lab_name(self, lab_name: str) -> Optional[str]:
        """Extract script name from lab name"""
        if not lab_name:
            return None
        
        # Lab names: "2 -  Simple RSING VWAP Strategy - XRP"
        # Extract everything between first dash and last dash
        import re
        
        # Pattern: "2 -  Simple RSING VWAP Strategy - XRP"
        pattern = r'^\d+\s*-\s*([^-]+?)\s*-\s*[A-Z]+'
        match = re.search(pattern, lab_name)
        if match:
            return self._normalize_script_name(match.group(1).strip())
        
        return None
    
    def _extract_market_from_lab_name(self, lab_name: str) -> Optional[str]:
        """Extract market tag from lab name"""
        if not lab_name:
            return None
        
        # Lab names: "2 -  Simple RSING VWAP Strategy - XRP"
        # Extract the coin name and construct market tag
        import re
        
        # Pattern: "2 -  Simple RSING VWAP Strategy - XRP"
        pattern = r'^\d+\s*-\s*[^-]+?\s*-\s*([A-Z]+)'
        match = re.search(pattern, lab_name)
        if match:
            coin = match.group(1)
            # Construct market tag: BINANCEFUTURES_COIN_USDT_PERPETUAL
            return f"BINANCEFUTURES_{coin}_USDT_PERPETUAL"
        
        return None
    
    def _parse_market_tag(self, market_tag: str) -> Tuple[Optional[str], Optional[str]]:
        """Parse market tag to extract trading pair and exchange"""
        if not market_tag:
            return None, None
        
        # Examples: BINANCE_BTC_USDT_, BINANCEFUTURES_ETH_USDT_PERPETUAL
        parts = market_tag.split('_')
        if len(parts) < 3:
            return None, None
        
        # First part is exchange
        exchange = parts[0]
        
        # Remaining parts form the trading pair
        trading_pair = '_'.join(parts[1:])
        
        return trading_pair, exchange


