import asyncio
import os
import logging
from typing import Optional

from pyHaasAPI.core.server_manager import ServerManager
from pyHaasAPI.config.settings import Settings
from pyHaasAPI.config.api_config import APIConfig
from pyHaasAPI.core.client import AsyncHaasClient
from pyHaasAPI.core.auth import AuthenticationManager
from pyHaasAPI.api.lab.lab_api import LabAPI
from pyHaasAPI.api.backtest.backtest_api import BacktestAPI
from pyHaasAPI.api.bot.bot_api import BotAPI
from pyHaasAPI.api.account.account_api import AccountAPI
from pyHaasAPI.services.bot_naming_service import BotNamingService, BotNamingContext
from pyHaasAPI.core.prefix_utils import PrefixUtils, AccountPrefix

from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BotDeployment")

async def deploy_best_lab_as_bot():
    """
    1. Scan all Labs for the best performing backtest.
    2. Pick the result with highest ROI.
    3. Use BotNamingService to generate a professional name.
    4. Deploy as a live bot to a Sim account.
    """
    load_dotenv()
    settings = Settings()
    sm = ServerManager(settings)
    
    logger.info("Connecting to srv03...")
    if not await sm.connect_server('srv03'):
        logger.error("Failed to connect.")
        return

    api_config = APIConfig(
        host="127.0.0.1", port=8090,
        email=os.getenv("API_EMAIL"), password=os.getenv("API_PASSWORD")
    )
    
    client = AsyncHaasClient(api_config)
    await client.connect()
    auth_manager = AuthenticationManager(client, api_config)
    await auth_manager.ensure_authenticated()
    
    lab_api = LabAPI(client, auth_manager)
    backtest_api = BacktestAPI(client, auth_manager)
    bot_api = BotAPI(client, auth_manager)
    account_api = AccountAPI(client, auth_manager)
    naming_service = BotNamingService()
    
    try:
        # 1. Find the best lab result
        logger.info("Scanning labs for best performance...")
        labs = await lab_api.get_labs()
        
        best_overall_bt = None
        best_lab = None
        
        for lab in labs[:5]: # Search top 5 labs
            try:
                results = await backtest_api.get_backtest_result(lab.lab_id, page_length=10)
                for bt in results.items:
                    if best_overall_bt is None or bt.roi > best_overall_bt.roi:
                        best_overall_bt = bt
                        best_lab = lab
            except Exception as e:
                logger.warning(f"Skipping lab {lab.lab_id}: {e}")

        if not best_overall_bt:
            logger.error("No backtest results found to deploy.")
            return

        logger.info(f"Found Best Result: Lab='{best_lab.name}', ROI={best_overall_bt.roi}%")

        # 2. Select Target Account
        accounts = await account_api.get_accounts()
        # Prefer Simulated accounts for safety in demo
        sim_accounts = [acc for acc in accounts if PrefixUtils.is_simulated(acc.name)]
        target_account = sim_accounts[0] if sim_accounts else accounts[0]
        
        logger.info(f"Target Account: {target_account.name} ({target_account.exchange})")

        # 3. Generate Professional Name
        # Fetch trades if available to provide win rate in name
        trades = []
        try:
            runtime = await backtest_api.get_backtest_runtime_data(best_lab.lab_id, best_overall_bt.backtest_id)
            trades = getattr(runtime, 'trades', [])
        except:
            pass

        context = BotNamingContext(
            server="srv03",
            lab_id=best_lab.lab_id,
            lab_name=best_lab.name,
            script_name="Strategy",
            market_tag=best_lab.settings.market_tag,
            trades=trades,
            starting_balance=10000.0,
            roi_percentage=best_overall_bt.roi if hasattr(best_overall_bt, 'roi') else 0.0,
            win_rate=best_overall_bt.win_rate if hasattr(best_overall_bt, 'win_rate') else 0.0,
            drawdown=best_overall_bt.max_drawdown if hasattr(best_overall_bt, 'max_drawdown') else 0.0,
            total_trades=best_overall_bt.total_trades if hasattr(best_overall_bt, 'total_trades') else 0
        )
        
        # Override some metrics from the BT result directly if available
        context.roi_percentage = best_overall_bt.roi
        context.win_rate = best_overall_bt.win_rate
        context.max_drawdown = best_overall_bt.max_drawdown
        context.total_trades = best_overall_bt.total_trades
        
        bot_name = naming_service.generate_bot_name(context, strategy="comprehensive")
        logger.info(f"Generated Bot Name: {bot_name}")

        # 4. Deploy Bot
        # Using create_bot_from_lab which is the safest way to clone parameters
        logger.info("Deploying bot from lab result...")
        new_bot = await bot_api.create_bot_from_lab(
            lab_id=best_lab.lab_id,
            backtest_id=best_overall_bt.backtest_id,
            bot_name=bot_name,
            account_id=target_account.account_id,
            market=best_lab.settings.market_tag,
            leverage=best_lab.settings.leverage
        )
        
        logger.info(f"Bot deployed successfully! ID: {new_bot.bot_id}")

    except Exception as e:
        logger.error(f"Deployment failed: {e}", exc_info=True)
    finally:
        await client.close()
        await sm.shutdown()

if __name__ == "__main__":
    asyncio.run(deploy_best_lab_as_bot())
