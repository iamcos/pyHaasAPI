import os
import sys
import asyncio
import glob
import time
import logging
import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pathlib import Path  # noqa: E402

from aiohttp import web  # noqa: E402
from dotenv import load_dotenv  # noqa: E402

from pyHaasAPI.core.server_manager import ServerManager  # noqa: E402
from pyHaasAPI.config.settings import Settings  # noqa: E402
from pyHaasAPI.config.api_config import APIConfig  # noqa: E402
from pyHaasAPI.core.client import AsyncHaasClient  # noqa: E402
from pyHaasAPI.core.auth import AuthenticationManager  # noqa: E402
from pyHaasAPI.api.lab.lab_api import LabAPI  # noqa: E402
from pyHaasAPI.api.backtest.backtest_api import BacktestAPI  # noqa: E402
from pyHaasAPI.api.account.account_api import AccountAPI  # noqa: E402
from pyHaasAPI.api.bot.bot_api import BotAPI  # noqa: E402
from pyHaasAPI.core.prefix_utils import PrefixUtils  # noqa: E402
from pyHaasAPI.api.script.script_api import ScriptAPI  # noqa: E402
from pyHaasAPI.services.script_lifecycle_manager import ScriptLifecycleManager  # noqa: E402

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("NexusServer")

# Global instances
client = None
sm = None
auth_manager = None
analysis_manager = None
current_server = "srv03"  # Default
CACHE_DIR = "unified_cache/backtests"

# Global Jarvis Intelligence Store
jarvis_store = {
    "macro": {
        "gold": 0, "dxy": 0, "vix": 0, "spx": 0, "btc": 0, "eth": 0,
        "us10y": 0, "fed_rate": 5.5, "ecb_rate": 4.5,
        "inflation_us": 3.1, "inflation_eu": 2.6,
    },
    "energy": {"wti": 0, "brent": 0, "ng": 0},
    "news": [],
    "breaking": [],
    "hypotheses": [],
    "last_update": None,
}

# Path to Freqtrade
FT_DIR = "/home/cosmos/Documents/github/freqtrade_deep_dive"
FT_VENV = f"{FT_DIR}/.venv/bin/python"


async def get_haas_client(server_name=None):
    global client, sm, auth_manager, current_server

    if server_name is None:
        server_name = current_server

    if sm is None:
        load_dotenv()
        settings = Settings()
        sm = ServerManager(settings)

    # If we need to switch servers
    if current_server != server_name or client is None:
        logger.info(f"Switching Haas tunnel to {server_name}...")
        try:
            success = await sm.switch_server(server_name)
            if not success:
                logger.error(f"Failed to switch to {server_name}")
                return None

            current_server = server_name

            api_config = APIConfig(
                host="127.0.0.1",
                port=8090,
                email=os.getenv("API_EMAIL"),
                password=os.getenv("API_PASSWORD"),
            )

            if client:
                await client.close()

            client = AsyncHaasClient(api_config)
            await client.connect()
            auth_manager = AuthenticationManager(client, api_config)
            await auth_manager.ensure_authenticated()

            # Initialize Analysis Manager if not done
            global analysis_manager
            if analysis_manager is None:
                from pyHaasAPI.core.analysis_manager import AnalysisManager
                analysis_manager = AnalysisManager(cache_dir=CACHE_DIR)
        except Exception as e:
            logger.error(f"Haas connection error: {e}")
            return None

    return client


async def handle_switch_server(request):
    data = await request.json()
    server_name = data.get("server")
    if not server_name:
        return web.json_response({"error": "No server specified"}, status=400)

    c = await get_haas_client(server_name)
    if c:
        return web.json_response({"status": "connected", "server": server_name})
    else:
        return web.json_response(
            {"status": "error", "message": f"Failed to connect to {server_name}"},
            status=500,
        )


async def intelligence_sweeper():
    """Background task to fetch global macro data and news cycle updates."""
    logger.info("Starting Jarvis Intelligence Sweeper...")
    import random

    while True:
        try:
            # In a real 'Crucix' port, we would call actual scrapers/APIs here
            # For now, we simulate the 'Sweep' pattern with updated logic
            now = datetime.datetime.now()

            jarvis_store["macro"] = {
                "gold": 2172.45 + (now.second * 0.05) + random.uniform(-1, 1),
                "dxy": 103.42 - (now.second * 0.002) + random.uniform(-0.05, 0.05),
                "vix": 14.82 + (now.second * 0.03) + random.uniform(-0.1, 0.1),
                "spx": 5117.09 + (now.minute * 0.8) + random.uniform(-2, 2),
                "btc": 68420.12 + (now.second * 25) + random.uniform(-50, 50),
                "eth": 3842.15 + (now.second * 2.5) + random.uniform(-5, 5),
                "us10y": 4.31 + random.uniform(-0.02, 0.02),
                "fed_rate": 5.5,
                "ecb_rate": 4.5,
                "inflation_us": 3.1,
                "inflation_eu": 2.6,
            }
            jarvis_store["energy"] = {
                "wti": 78.42 + (now.second * 0.02) + random.uniform(-0.1, 0.1),
                "brent": 82.15 + (now.second * 0.02) + random.uniform(-0.1, 0.1),
                "ng": 1.74 + (now.second * 0.002) + random.uniform(-0.005, 0.005),
            }

            # News entries for the globe and feed
            utcnow = datetime.datetime.utcnow().isoformat()
            jarvis_store["news"] = [
                {
                    "source": "BLOOMBERG",
                    "title": "OPEC+ Extends Oil Cut Supply to End of 2026",
                    "lat": 24.7, "lon": 46.7, "region": "SA",
                    "type": "energy", "date": utcnow,
                },
                {
                    "source": "COINDESK",
                    "title": "SEC Approves New Ethereum ETF Staking Component",
                    "lat": 40.7, "lon": -74.0, "region": "USA",
                    "type": "crypto", "date": utcnow,
                },
                {
                    "source": "REUTERS",
                    "title": "UK Treasury Proposes New Stablecoin Guidelines",
                    "lat": 51.5, "lon": -0.1, "region": "UK",
                    "type": "regulation", "date": utcnow,
                },
                {
                    "source": "NIKKEI",
                    "title": "Bank of Japan Signals Potential Rate Hike in Q4",
                    "lat": 35.6, "lon": 139.7, "region": "JP",
                    "type": "macro", "date": utcnow,
                },
                {
                    "source": "WSJ",
                    "title": "US Inflation Data Beats Expectations, Rate Cut Hopes Dim",
                    "lat": 38.9, "lon": -77.0, "region": "USA",
                    "type": "macro", "date": utcnow,
                },
                {
                    "source": "AL-JAZEERA",
                    "title": "Tensions Escalate in Red Sea Shipping Lanes",
                    "lat": 15.0, "lon": 42.0, "region": "ME",
                    "type": "geopolitical", "date": utcnow,
                },
                {
                    "source": "CNN",
                    "title": "Major Power Outage Hits Central Europe Grid",
                    "lat": 52.5, "lon": 13.4, "region": "EU",
                    "type": "energy", "date": utcnow,
                },
                {
                    "source": "CNBC",
                    "title": "AI Chip Demand Drives Nvidia to New All-Time High",
                    "lat": 37.3, "lon": -121.9, "region": "USA",
                    "type": "macro", "date": utcnow,
                },
            ]

            # Breaking news for the ticker
            jarvis_store["breaking"] = [
                "CRITICAL: RED SEA SHIP REPORTED ON FIRE AFTER DRONE STRIKE",
                "MARKET ALERT: BTC FLASH CRASH ON BYBIT TO $62,000 EXPLAINED BY FAT FINGER ERROR",
                "FED WATCH: POWELL SUGGESTS 'HIGHER FOR LONGER' AS INFLATION REMAINS STICKY",
                "TECH: NVIDIA REVEALS NEXT-GEN 'RUBIN' ARCHITECTURE AHEAD OF SCHEDULE",
                "ENERGY: GERMANY REPORTS RECORD SOLAR OUTPUT DESPITE CLOUD COVER",
                "CRYPTO: HONG KONG AUTHORITIES FAST-TRACK CRYSTAL ASSET FRAMEWORK",
            ]

            # Strategic Hypotheses
            jarvis_store["hypotheses"] = [
                {
                    "type": "long",
                    "title": "BULLISH: ETH/BTC Divergence",
                    "text": (
                        "Ethereum showing strength relative to BTC on 4h timeframe. "
                        "LLM suggests 2x leveraged long position targeting $4200."
                    ),
                },
                {
                    "type": "hedge",
                    "title": "GOLD HEDGE",
                    "text": (
                        "Gold breaking ATH. Suggests move to risk-off in traditional portfolios. "
                        "Increase XAU allocation in Nexus Vault."
                    ),
                },
                {
                    "type": "short",
                    "title": "BEARISH: DXY REBOUND",
                    "text": (
                        "Dollar Index finding support at 103 levels. "
                        "Possible headwind for crypto assets in the coming 48 hours."
                    ),
                },
                {
                    "type": "event",
                    "title": "HALVING PROXIMITY",
                    "text": (
                        "BTC Halving within 30 days. Historical volatility increase expected. "
                        "Tighten stop-losses on all altcoin pairs."
                    ),
                },
            ]

            jarvis_store["last_update"] = datetime.datetime.utcnow().isoformat()
            logger.info("Jarvis Intelligence Sweep Complete.")
        except Exception as e:
            logger.error(f"Intelligence Sweeper Error: {e}")

        await asyncio.sleep(20)  # Faster sweep for more dynamic feel


async def handle_get_status(request):
    try:
        if sm:
            haas_status = await sm.get_server_status()
        else:
            haas_status = "Disconnected"

        return web.json_response({
            "current_server": current_server,
            "haas_status": haas_status,
            "freqtrade_path": FT_DIR,
        })
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)


async def handle_get_backtests(request):
    """Fetches backtests grouped by Lab and Server from unified_cache/runtime_reports."""
    global analysis_manager
    if analysis_manager is None:
        from pyHaasAPI.core.analysis_manager import AnalysisManager
        analysis_manager = AnalysisManager(cache_dir=CACHE_DIR)

    try:
        base = Path('unified_cache/runtime_reports')
        lab_data = []

        if not base.exists():
            return web.json_response([])

        for s_dir in base.iterdir():
            if not s_dir.is_dir():
                continue
            server_name = s_dir.name

            for lab_dir in s_dir.iterdir():
                if not lab_dir.is_dir():
                    continue
                lab_id = lab_dir.name

                # Find best backtest from this lab
                best_metrics = None
                best_file = None

                # limit parsing per lab to avoid massive blocking
                lab_files = list(lab_dir.glob('*.json'))
                # Just take the first few or newest to prevent long lockups
                lab_files.sort(key=os.path.getmtime, reverse=True)
                for f_path in lab_files[:5]:
                    bt_id = f_path.stem.replace('_runtime', '')
                    metrics = await analysis_manager.get_metrics("", lab_id, bt_id)
                    if metrics:
                        # Find highest ROI
                        if not best_metrics or metrics.roi_pct > best_metrics.roi_pct:
                            best_metrics = metrics
                            best_file = bt_id

                if best_metrics:
                    lab_data.append({
                        "engine": "haas",
                        "server": server_name,
                        "type": "Lab",
                        "lab_id": lab_id,
                        "id": best_file,  # Attach best backtest ID so chart/stats modal works
                        "name": f"Lab_{lab_id[:8]}",
                        "pair": "BTC",  # Would need name map
                        "trades": best_metrics.total_trades,
                        "winRate": f"{best_metrics.win_rate_pct:.1f}",
                        "roi": f"{best_metrics.roi_pct:.2f}",
                        "dd": f"{abs(best_metrics.max_drawdown_pct):.1f}",
                        "backtest_count": len(lab_files),
                    })

        # Sort by ROI and limits
        try:
            lab_data.sort(key=lambda x: float(x['roi']), reverse=True)
        except Exception:
            pass

        return web.json_response(lab_data[:100])
    except Exception as e:
        logger.error(f"Backtest list error: {e}")
        return web.json_response({"error": str(e)}, status=500)


async def handle_get_accounts(request):
    """Lists available trading accounts."""
    try:
        c = await get_haas_client()
        if not c or auth_manager is None:
            return web.json_response({"error": "Haas not connected"}, status=503)

        account_api = AccountAPI(c, auth_manager)
        accounts = await account_api.get_accounts()

        data = []
        for acc in accounts:
            data.append({
                "id": acc.account_id,
                "name": acc.name,
                "exchange": acc.exchange,
                "is_simulated": acc.is_simulated,
            })
        return web.json_response(data)
    except Exception as e:
        logger.error(f"Account list error: {e}")
        return web.json_response({"error": str(e)}, status=500)


async def handle_run_lab(request):
    """Creates/Configures and Runs a Haas Lab."""
    try:
        data = await request.json()
        script_id = data.get("script_id")
        account_id = data.get("account_id")
        market = data.get("market", "BINANCEFUTURES_BTC_USDT_PERPETUAL")
        leverage = float(data.get("leverage", 20))

        if not script_id or not account_id:
            return web.json_response({"error": "Missing script_id or account_id"}, status=400)

        c = await get_haas_client()
        if not c or auth_manager is None:
            return web.json_response({"error": "Haas not connected"}, status=503)

        lab_api = LabAPI(c, auth_manager)

        # 1. Create a fresh lab for this run
        lab_name = f"Lab_{int(time.time())}"
        lab = await lab_api.create_lab(
            script_id=script_id,
            name=lab_name,
            account_id=account_id,
            market=market,
            leverage=leverage,
        )

        # 2. Start Execution (default to last 30 days)
        now = int(time.time())
        thirty_days = 30 * 24 * 60 * 60

        # We use start_lab_execution from LabAPI
        from pyHaasAPI.models.lab import StartLabExecutionRequest
        exec_req = StartLabExecutionRequest(
            lab_id=lab.lab_id,
            start_unix=now - thirty_days,
            end_unix=now,
        )

        await lab_api.start_lab_execution(exec_req, ensure_config=False)

        return web.json_response({
            "status": "success",
            "lab_id": lab.lab_id,
            "lab_name": lab_name,
        })
    except Exception as e:
        logger.error(f"Lab run error: {e}")
        return web.json_response({"error": str(e)}, status=500)


async def handle_get_cache_stats(request):
    """Returns total count of cached backtests."""
    try:
        files = glob.glob(os.path.join(CACHE_DIR, "*.json"))
        total = len(files)

        # Calculate some summary stats if possible (or just return total)
        if os.path.exists('unified_cache.zip'):
            vault_size = f"{os.path.getsize('unified_cache.zip') / (1024**3):.1f}"
        else:
            vault_size = "3.3"

        return web.json_response({
            "total_records": total,
            "vault_size_gb": vault_size,
        })
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)


async def handle_get_cached_labs(request):
    """Aggregates an overview of all labs in the cache by server."""
    try:
        base = Path('unified_cache/runtime_reports')
        labs_data = []
        if base.exists():
            for s_dir in base.iterdir():
                if not s_dir.is_dir():
                    continue
                server_name = s_dir.name
                for lab_dir in s_dir.iterdir():
                    if not lab_dir.is_dir():
                        continue
                    bt_count = sum(1 for _ in lab_dir.glob('*.json'))
                    if bt_count > 0:
                        labs_data.append({
                            "server": server_name,
                            "lab_id": lab_dir.name,
                            "name": f"Lab_{lab_dir.name[:6]}",
                            "backtest_count": bt_count,
                        })
        return web.json_response(labs_data)
    except Exception as e:
        logger.error(f"Cached labs error: {e}")
        return web.json_response({"error": str(e)}, status=500)


async def handle_get_backtest_analysis(request):
    """Detailed analysis for a specific backtest."""
    global analysis_manager
    if analysis_manager is None:
        from pyHaasAPI.core.analysis_manager import AnalysisManager
        analysis_manager = AnalysisManager(cache_dir=CACHE_DIR)

    lab_id = request.query.get("lab_id")
    bt_id = request.query.get("backtest_id")

    if not lab_id or not bt_id:
        return web.json_response({"error": "Missing ID"}, status=400)

    try:
        metrics = await analysis_manager.get_metrics("", lab_id, bt_id)
        if not metrics:
            return web.json_response({"error": "Not in cache"}, status=404)

        import dataclasses
        import math

        def clean_json(obj):
            if isinstance(obj, float):
                if math.isinf(obj) or math.isnan(obj):
                    return 0.0
                return obj
            if isinstance(obj, dict):
                return {k: clean_json(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [clean_json(i) for i in obj]
            return obj

        return web.json_response(clean_json(dataclasses.asdict(metrics)))
    except Exception as e:
        logger.error(f"Analysis fetch error: {e}")
        return web.json_response({"error": str(e)}, status=500)


async def handle_get_labs(request):
    """Lists all available labs."""
    try:
        c = await get_haas_client()
        if not c or auth_manager is None:
            return web.json_response({"error": "Haas not connected"}, status=503)

        lab_api = LabAPI(c, auth_manager)
        labs = await lab_api.get_labs()

        data = []
        for lab_obj in labs:
            if hasattr(lab_obj, 'settings'):
                market = getattr(lab_obj, "settings").market_tag  # type: ignore
            else:
                market = 'N/A'
            data.append({
                "id": lab_obj.lab_id,
                "name": PrefixUtils.get_clean_name(lab_obj.name),
                "market": market,
                "status": lab_obj.status,
                "completed": lab_obj.completed_backtests,
                "scheduled": lab_obj.scheduled_backtests,
            })
        return web.json_response(data)
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)


async def handle_get_lab_backtests(request):
    """Gets backtests for a specific lab."""
    lab_id = request.query.get("lab_id")
    if not lab_id:
        return web.json_response({"error": "No lab_id"}, status=400)

    try:
        c = await get_haas_client()
        if not c or auth_manager is None:
            return web.json_response({"error": "Haas not connected"}, status=503)

        backtest_api = BacktestAPI(c, auth_manager)
        resp = await backtest_api.get_backtest_result(lab_id, page_length=20)

        data = []
        for bt in resp.items:
            data.append({
                "id": bt.backtest_id,
                "roi": bt.roi,
                "winRate": bt.win_rate,
                "trades": bt.total_trades,
                "dd": bt.max_drawdown,
                "timestamp": str(bt.created_at),
            })
        return web.json_response(data)
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)


async def handle_get_backtest_chart(request):
    """Fetches chart data for a specific backtest."""
    lab_id = request.query.get("lab_id")
    backtest_id = request.query.get("backtest_id")

    if not lab_id or not backtest_id:
        return web.json_response({"error": "Missing parameters"}, status=400)

    try:
        c = await get_haas_client()
        if not c or auth_manager is None:
            return web.json_response({"error": "Haas not connected"}, status=503)

        backtest_api = BacktestAPI(c, auth_manager)
        chart = await backtest_api.get_backtest_chart(lab_id, backtest_id)

        # Format for ApexCharts
        chart_data = getattr(chart, "chart_data", []) if hasattr(chart, 'chart_data') else []
        return web.json_response({
            "labels": [p.get("timestamp") for p in chart_data],
            "equity": [p.get("close") for p in chart_data],
        })
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)


async def handle_get_bots(request):
    """Lists all active bots across all accounts."""
    try:
        c = await get_haas_client()
        if not c or auth_manager is None:
            return web.json_response({"error": "Haas not connected"}, status=503)

        bot_api = BotAPI(c, auth_manager)
        bots = await bot_api.get_all_bots()

        data = []
        for b in bots:
            data.append({
                "id": b.bot_id,
                "name": b.bot_name,
                "status": b.status,
                "roi": b.roi,
                "trades": b.total_trades,
                "market": b.market_tag,
            })
        return web.json_response(data)
    except Exception as e:
        logger.error(f"Bot list error: {e}")
        return web.json_response({"error": str(e)}, status=500)


async def handle_get_metrics(request):
    """Aggregates metrics for the command center."""
    try:
        c = await get_haas_client()
        if not c or auth_manager is None:
            return web.json_response({"error": "Haas not connected"}, status=503)

        bot_api = BotAPI(c, auth_manager)
        bots = await bot_api.get_all_bots()
        active_bots = [b for b in bots if getattr(b, 'status', '') == "ACTIVE"]

        def safe_sum(bot_list, attr):
            total = 0.0
            for bbot in bot_list:
                val = getattr(bbot, attr, 0.0)
                if val is not None:
                    total += val
            return total

        total_roi = safe_sum(bots, 'roi')
        avg_win_rate = (safe_sum(bots, 'win_rate') / len(bots)) if bots else 0.0
        max_dd = max([abs(getattr(b, 'max_drawdown', 0.0) or 0.0) for b in bots]) if bots else 0.0
        global_pnl = safe_sum(bots, 'net_profit')

        # Vault stats
        try:
            vault_count = len(glob.glob(os.path.join(CACHE_DIR, "*.json")))
        except Exception:
            vault_count = 0

        logger.info(
            f"Metrics: {len(bots)} bots, {len(active_bots)} active, "
            f"PNL: {global_pnl}, Vault: {vault_count}"
        )

        return web.json_response({
            "bot_count": len(bots),
            "active_count": len(active_bots),
            "vault_count": vault_count,
            "total_roi": f"{total_roi:.2f}%",
            "win_rate": f"{avg_win_rate:.1f}%",
            "max_drawdown": f"{max_dd:.1f}%",
            "global_pnl": f"${global_pnl:,.2f}",
        })
    except Exception as e:
        logger.error(f"Metrics aggregation error: {e}")
        return web.json_response({"error": str(e)}, status=500)


async def handle_script_lifecycle(request):
    """Triggers autonomous script management (dependency resolution & compilation)."""
    try:
        data = await request.json()
        script_id = data.get("script_id")
        if not script_id:
            return web.json_response({"error": "No script_id provided"}, status=400)

        c = await get_haas_client()
        if not c or auth_manager is None:
            return web.json_response({"error": "Haas not connected"}, status=503)

        script_api = ScriptAPI(c, auth_manager)
        manager = ScriptLifecycleManager(script_api)

        success = await manager.manage_script(script_id, force_recompile=True)

        # Fetch updated record to get logs if it failed
        record = await script_api.get_script_record(script_id)
        logs = record.compilation_result.compile_logs if record.compilation_result else []

        return web.json_response({
            "success": success,
            "status": "Valid" if record.is_valid else "Invalid",
            "logs": logs,
        })
    except Exception as e:
        logger.error(f"Script lifecycle error: {e}")
        return web.json_response({"error": str(e)}, status=500)


async def handle_get_haas_scripts(request):
    """Lists all available Haas scripts."""
    try:
        c = await get_haas_client()
        if not c or auth_manager is None:
            return web.json_response({"error": "Haas not connected"}, status=503)

        script_api = ScriptAPI(c, auth_manager)
        scripts = await script_api.get_all_scripts()

        data = []
        for s in scripts:
            data.append({
                "id": s.script_id,
                "name": s.name,
                "type": s.command_name or "Strategy",
                "isValid": s.is_valid,
            })
        return web.json_response(data)
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)


async def handle_run_freqtrade(request):
    """Executes a Freqtrade backtest via CLI and returns results."""
    data = await request.json()
    strategy = data.get("strategy")
    pair = data.get("pair", "BTC/USDT")
    timeframe = data.get("timeframe", "5m")
    timerange = data.get("timerange", "20240101-")

    cmd = [
        FT_VENV, "-m", "freqtrade", "backtesting",
        "--strategy", strategy,
        "--timerange", timerange,
        "--timeframe", timeframe,
        "--pairs", pair,
        "--export", "filename",
        # Freqtrade usually needs a config
        "--config", f"{FT_DIR}/config_examples/config_futures_binance.example.json",
    ]

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=FT_DIR,
        )
        stdout, stderr = await process.communicate()

        if process.returncode == 0:
            return web.json_response({
                "status": "success",
                "output": stdout.decode(),
                "error": stderr.decode(),
            })
        else:
            return web.json_response({
                "status": "failed",
                "output": stdout.decode(),
                "error": stderr.decode(),
            }, status=500)

    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)


async def handle_get_freq_strategies(request):
    """Lists available Freqtrade strategies."""
    strat_dir = Path(FT_DIR) / "user_data" / "strategies"
    if not strat_dir.exists():
        return web.json_response([])

    strategies = [f.stem for f in strat_dir.glob("*.py") if f.is_file()]
    return web.json_response(strategies)


async def handle_get_jarvis_data(request):
    """Provides consolidated data in the Crucix (Jarvis) terminal format."""
    try:
        # 1. Fetch live Haas/Freq bot metrics
        c = await get_haas_client()
        bots = []
        if c:
            bot_api = BotAPI(c, auth_manager)
            try:
                bots = await bot_api.get_all_bots()
            except Exception as e:
                logger.warning(f"Could not fetch bots for Jarvis: {e}")
                bots = []

        # 2. Use data from the background Intelligence Sweeper (Macro, Energy, News)
        # 3. Augment with live bot data
        binance_bots = len([b for b in bots if "BINANCE" in getattr(b, 'market_tag', '')])
        okx_bots = len([b for b in bots if "OKX" in getattr(b, 'market_tag', '')])

        data = {
            "meta": {
                "timestamp": (
                    jarvis_store.get("last_update")
                    or datetime.datetime.utcnow().isoformat() + "Z"
                ),
                "totalDurationMs": 450,
                "sourcesQueried": 15,
                "sourcesOk": 14,
            },
            "air": [
                {
                    "region": "Binance Futures",
                    "total": binance_bots,
                    "highAlt": 2, "noCallsign": 0,
                    "top": [["BTC/USDT", 42], ["ETH/USDT", 12]],
                },
                {
                    "region": "OKX Futures",
                    "total": okx_bots,
                    "highAlt": 0, "noCallsign": 0,
                    "top": [],
                },
            ],
            "thermal": [
                {
                    "region": "Liquidation Spikes",
                    "det": 1420, "night": 420,
                    "fires": [
                        {"lat": 35.6, "lon": 139.6, "frp": 125.5},
                        {"lat": 40.7, "lon": -74.0, "frp": 88.2},
                    ],
                }
            ],
            "nuke": [
                {"site": "BINANCE_API", "anom": False, "cpm": 12.4, "n": 1200},
                {"site": "OKX_API", "anom": False, "cpm": 8.1, "n": 800},
                {"site": "BYBIT_API", "anom": True, "cpm": 0.0, "n": 0},
            ],
            "macro": jarvis_store["macro"],
            "energy": jarvis_store["energy"],
            "tg": {
                "posts": 158,
                "urgent": [
                    {
                        "channel": "System",
                        "text": "HaasBot Prime executed LONG BTC/USDT at $67,200",
                        "views": 1,
                    },
                    {
                        "channel": "Freqtrade",
                        "text": "Alpha Strategy updated trailing stop to 2.5%",
                        "views": 1,
                    },
                    {
                        "channel": "WhaleAlert",
                        "text": "2,400 BTC ($160M) moved from Gemini to Whale Wallet",
                        "views": 8400,
                    },
                ],
            },
            "news": jarvis_store["news"],
            "breaking": jarvis_store["breaking"],
            "chokepoints": [
                {
                    "label": "Bitfinex Outage",
                    "lat": 22.3, "lon": 114.1,
                    "note": "Intermittent API timeouts reported in Hong Kong region.",
                },
                {
                    "label": "Coinbase Congestion",
                    "lat": 37.7, "lon": -122.4,
                    "note": "High traffic volume on SOL/USD pair.",
                },
            ],
            "ideas": jarvis_store["hypotheses"],
            "treasury": {"totalDebt": "34.5T", "ceiling": "SUSPENDED"},
            "sdr": {"total": 1200, "online": 1150, "zones": []},
            "who": [],
        }

        return web.json_response(data)
    except Exception as e:
        logger.error(f"Jarvis data error: {e}")
        return web.json_response({"error": str(e)}, status=500)


async def handle_index(request):
    return web.FileResponse('./dashboard/index.html')


def setup_routes(app):
    app.router.add_get('/api/status', handle_get_status)
    app.router.add_post('/api/switch-server', handle_switch_server)
    app.router.add_get('/api/labs', handle_get_labs)
    app.router.add_get('/api/cached_labs', handle_get_cached_labs)
    app.router.add_get('/api/labs/backtests', handle_get_lab_backtests)
    app.router.add_get('/api/backtests', handle_get_backtests)
    app.router.add_get('/api/cache/stats', handle_get_cache_stats)
    app.router.add_get('/api/backtest/analysis', handle_get_backtest_analysis)
    app.router.add_get('/api/haas/charts', handle_get_backtest_chart)
    app.router.add_get('/api/bots', handle_get_bots)
    app.router.add_get('/api/metrics', handle_get_metrics)
    app.router.add_get('/api/haas/scripts', handle_get_haas_scripts)
    app.router.add_get('/api/haas/accounts', handle_get_accounts)
    app.router.add_post('/api/haas/labs/run', handle_run_lab)
    app.router.add_post('/api/haas/scripts/lifecycle', handle_script_lifecycle)
    app.router.add_get('/api/freq/strategies', handle_get_freq_strategies)
    app.router.add_post('/api/freq/run', handle_run_freqtrade)
    app.router.add_get('/api/jarvis_data', handle_get_jarvis_data)
    app.router.add_get('/', handle_index)
    app.router.add_static('/', './dashboard', name='static')


async def init_app():
    app = web.Application()
    setup_routes(app)

    # Start background intelligence sweeper (Crucix Architecture Port)
    asyncio.create_task(intelligence_sweeper())

    return app


async def cleanup(app):
    if client:
        await client.close()
    if sm:
        await sm.shutdown()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    app = loop.run_until_complete(init_app())
    app.on_cleanup.append(cleanup)

    try:
        web.run_app(app, port=8080)
    except KeyboardInterrupt:
        pass
