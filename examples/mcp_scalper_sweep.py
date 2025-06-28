#!/usr/bin/env python3
"""
MCP Scalper Sweep: Automated Lab Deployment and Bot Selection (Improved)

- Input: User-provided list of pairs (e.g., ["BTC/USDT", ...])
- For each pair, find available markets (focused search by exchange)
- For each market:
    - Create a lab with the scalper bot
    - Dynamically discover all sweepable parameters (Stop Loss, Take Profit, etc.)
    - Build a parameter grid for all combinations (0.5 to 2.0, step 0.1 for SL/TP)
    - Run a 6-hour backtest in simulation mode
- Wait for all labs to complete
- For each lab, select the best configuration (by ROI)
- Deploy a simulated bot for each best configuration
- Output a summary report
"""
import time
from datetime import datetime, timedelta
from itertools import product
from pyHaasAPI import api
from pyHaasAPI.model import CreateLabRequest, StartLabExecutionRequest, AddBotFromLabRequest, GetBacktestResultRequest
from pyHaasAPI.price import PriceAPI

# User-provided list of pairs (reduced for testing)
USER_PAIRS = [
    "BTC/USDT",
    "ETH/USDT",
    "SOL/USDT"
]

# Parameter sweep values (0.5 to 2.0, step 0.1 as requested)
PARAM_SWEEP_RANGE = [round(x * 0.1, 1) for x in range(5, 21)]  # 0.5 to 2.0

# Backtest period: last 6 hours
BACKTEST_HOURS = 6


def normalize_pair(pair):
    """Convert 'BTC/USDT' to ('BTC', 'USDT')"""
    parts = pair.replace('-', '/').split('/')
    if len(parts) == 2:
        return parts[0].upper(), parts[1].upper()
    return None, None


def find_sweepable_params(lab_details):
    """Return keys for Stop Loss, Take Profit, and any optimization-enabled params."""
    sweep_keys = []
    for param in lab_details.parameters:
        key = param.get('K', '')
        name = key.split('.')[-1].lower()
        if ("stop loss" in name or "take profit" in name or
            param.get('bruteforce', False) or param.get('intelligent', False) or
            (isinstance(param.get('O', []), list) and len(param.get('O', [])) > 1)):
            sweep_keys.append(key)
    return sweep_keys


def get_markets_efficiently(executor):
    """Get markets efficiently using exchange-specific endpoints instead of full market list"""
    print("📊 Fetching markets efficiently by exchange...")
    
    price_api = PriceAPI(executor)
    all_markets = []
    
    # Use exchange-specific endpoints (much faster than get_all_markets)
    exchanges = ["BINANCE", "KRAKEN"]  # Skip COINBASE as it has issues
    
    for exchange in exchanges:
        try:
            print(f"  🔍 Fetching {exchange} markets...")
            exchange_markets = price_api.get_trade_markets(exchange)
            all_markets.extend(exchange_markets)
            print(f"  ✅ Found {len(exchange_markets)} {exchange} markets")
        except Exception as e:
            print(f"  ⚠️ Failed to get {exchange} markets: {e}")
            continue
    
    print(f"✅ Found {len(all_markets)} total markets across exchanges")
    return all_markets


def main():
    print("🚦 MCP Scalper Sweep: Automated Lab Deployment and Bot Selection (Improved)\n")
    
    # Authenticate with retries
    print("🔐 Authenticating...")
    executor = None
    for auth_attempt in range(3):
        try:
    executor = api.RequestsExecutor(
        host="127.0.0.1",
        port=8090,
        state=api.Guest()
    ).authenticate(
        email="garrypotterr@gmail.com",
        password="IQYTCQJIQYTCQJ"
    )
            print("✅ Authentication successful")
            break
        except Exception as e:
            print(f"❌ Authentication attempt {auth_attempt + 1} failed: {e}")
            if auth_attempt < 2:
                print("⏳ Waiting 10 seconds before retry...")
                time.sleep(10)
            else:
                print("💥 Authentication failed after all attempts")
                return

    if not executor:
        print("❌ No authenticated executor available")
        return

    # 1. Find scalper bot script
    print("\n🔍 Finding scalper bot script...")
    scripts = api.get_scripts_by_name(executor, "Scalper Bot")
    if not scripts:
        print("❌ No scalper bot scripts found!")
        return
    scalper_script = scripts[0]
    print(f"✅ Using scalper bot script: {scalper_script.script_name} (ID: {scalper_script.script_id})")

    # 2. Get markets efficiently (using exchange-specific endpoints)
    all_markets = get_markets_efficiently(executor)
    if not all_markets:
        print("❌ No markets available, exiting...")
        return

    # 3. Get a valid account (use first available)
    print("\n🏦 Getting accounts...")
    accounts = api.get_accounts(executor)
    if not accounts:
        print("❌ No accounts available!")
        return
    account = accounts[0]
    print(f"✅ Using account: {account.name} ({account.account_id})")

    # 4. For each user pair, find all matching markets
    print(f"\n🔍 Finding markets for pairs: {USER_PAIRS}")
    pair_to_markets = {}
    for pair in USER_PAIRS:
        base, quote = normalize_pair(pair)
        if not base or not quote:
            continue
        matching = [m for m in all_markets if m.primary == base and m.secondary == quote]
        if matching:
            pair_to_markets[pair] = matching
            print(f"  ✅ {pair}: {len(matching)} market(s) found: {[m.price_source for m in matching]}")
        else:
            print(f"  ❌ {pair}: No markets found")
    
    if not pair_to_markets:
        print("❌ No valid markets found for any pairs!")
        return

    # 5. For each market, create a lab and sweep parameters
    print(f"\n🚀 Creating labs and parameter sweeps...")
    now = int(time.time())
    start_unix = now - BACKTEST_HOURS * 3600
    end_unix = now
    labs = []
    
    for pair, markets in pair_to_markets.items():
        for market in markets:
            try:
            lab_name = f"MCP_{pair.replace('/', '_')}_{market.price_source}_{int(time.time())}"
                print(f"\n📋 Creating lab: {lab_name}")
                
                # Create lab
            lab = api.create_lab(
                executor,
                CreateLabRequest(
                    script_id=scalper_script.script_id,
                    name=lab_name,
                    account_id=account.account_id,
                    market=f"{market.price_source.upper()}_{market.primary.upper()}_{market.secondary.upper()}_",
                    interval=1,
                    default_price_data_style="CandleStick"
                )
            )
                print(f"  ✅ Lab created: {lab.lab_id}")
                
            # Fetch lab details and dynamically find sweepable params
            lab_details = api.get_lab_details(executor, lab.lab_id)
            sweep_keys = find_sweepable_params(lab_details)
                
            if not sweep_keys:
                    print(f"  ⚠️ No sweepable parameters found for {lab.name}")
                continue
                
                print(f"  🔑 Sweep keys: {sweep_keys}")
                
            # Build parameter grid (all combinations)
            param_grid = [dict(zip(sweep_keys, values)) for values in product(PARAM_SWEEP_RANGE, repeat=len(sweep_keys))]
                print(f"  📊 Parameter combinations: {len(param_grid)}")
                
                # Update lab parameters for first grid config
            initial_params = param_grid[0]
            updated_parameters = []
            for param in lab_details.parameters:
                key = param.get('K', '')
                if key in initial_params:
                    param['O'] = [str(initial_params[key])]
                updated_parameters.append(param)
            lab_details.parameters = updated_parameters
                
            api.update_lab_details(executor, lab_details)
                print(f"  ✅ Lab parameters updated")
                
            # Start backtest
            api.start_lab_execution(
                executor,
                StartLabExecutionRequest(
                    lab_id=lab.lab_id,
                    start_unix=start_unix,
                    end_unix=end_unix,
                    send_email=False
                )
            )
                print(f"  ✅ Backtest started")
                
            labs.append((lab, param_grid, market, pair, sweep_keys))
                time.sleep(2)  # Avoid rate limits
                
            except Exception as e:
                print(f"  ❌ Failed to create lab for {pair} on {market.price_source}: {e}")
                continue

    if not labs:
        print("❌ No labs were successfully created!")
        return

    # 6. Wait for all labs to complete
    print(f"\n⏳ Waiting for {len(labs)} labs to complete...")
    completed_labs = []
    for lab, param_grid, market, pair, sweep_keys in labs:
        print(f"  🔄 Monitoring lab: {lab.name}")
        while True:
            try:
            details = api.get_lab_details(executor, lab.lab_id)
            if hasattr(details, 'status') and str(details.status) == '3':  # COMPLETED
                    print(f"  ✅ Lab completed: {lab.name}")
                completed_labs.append((lab, param_grid, market, pair, sweep_keys))
                break
            elif hasattr(details, 'status') and str(details.status) == '4':  # CANCELLED
                    print(f"  ❌ Lab cancelled: {lab.name}")
                break
                time.sleep(30)  # Check every 30 seconds
            except Exception as e:
                print(f"  ⚠️ Error checking lab status: {e}")
                time.sleep(30)

    # 7. For each completed lab, get best config and deploy bot
    print(f"\n🏆 Processing {len(completed_labs)} completed labs...")
    deployed_bots = []
    
    for lab, param_grid, market, pair, sweep_keys in completed_labs:
        try:
            print(f"\n📊 Analyzing results for: {lab.name}")
        results = api.get_backtest_result(
            executor,
            GetBacktestResultRequest(
                lab_id=lab.lab_id,
                next_page_id=0,
                page_lenght=1000
            )
        )
            
        if not results.items:
                print(f"  ❌ No backtest results for lab {lab.name}")
            continue
            
        # Find best config by ROI
        best = max(results.items, key=lambda x: x.summary.ReturnOnInvestment if x.summary else 0)
            roi = best.summary.ReturnOnInvestment if best.summary else 0
            print(f"  🎯 Best ROI: {roi}%")
            
        # Deploy simulated bot
        bot_name = f"MCP_Bot_{pair.replace('/', '_')}_{market.price_source}_{int(time.time())}"
        bot = api.add_bot_from_lab(
            executor,
            AddBotFromLabRequest(
                lab_id=lab.lab_id,
                backtest_id=best.backtest_id,
                bot_name=bot_name,
                account_id=account.account_id,
                market=f"{market.price_source.upper()}_{market.primary.upper()}_{market.secondary.upper()}_",
                leverage=0
            )
        )
            print(f"  🤖 Deployed bot: {bot.bot_name} (ID: {bot.bot_id})")
            deployed_bots.append({
                'pair': pair,
                'market': market.price_source,
                'bot_name': bot.bot_name,
                'bot_id': bot.bot_id,
                'roi': roi
            })
            time.sleep(2)
            
        except Exception as e:
            print(f"  ❌ Failed to process lab {lab.name}: {e}")
            continue

    # 8. Summary report
    print(f"\n📋 SUMMARY REPORT")
    print(f"==================")
    print(f"Pairs tested: {len(USER_PAIRS)}")
    print(f"Labs created: {len(labs)}")
    print(f"Labs completed: {len(completed_labs)}")
    print(f"Bots deployed: {len(deployed_bots)}")
    
    if deployed_bots:
        print(f"\n🤖 Deployed Bots:")
        for bot in deployed_bots:
            print(f"  - {bot['pair']} on {bot['market']}: {bot['bot_name']} (ROI: {bot['roi']}%)")
    
    print(f"\n✅ MCP Scalper Sweep complete!")


if __name__ == "__main__":
    main() 