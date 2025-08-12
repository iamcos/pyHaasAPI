#!/usr/bin/env python3
"""
Comprehensive Lab Management and Parameter Iteration Test

This script consolidates advanced lab management and parameter iteration backtesting tests.
"""
import os
import time
from datetime import datetime
from typing import Dict, List, Any
from config import settings
from dotenv import load_dotenv
load_dotenv()
from pyHaasAPI import api
from pyHaasAPI.model import CreateLabRequest, StartLabExecutionRequest, GetBacktestResultRequest
from pyHaasAPI.price import PriceAPI

class LabIntegrationTester:
    def __init__(self):
        self.executor = None
        self.price_api = None

    def authenticate(self):
        print("\n🔐 Authenticating with HaasOnline API...")
        for attempt in range(3):
            try:
                self.executor = api.RequestsExecutor(
                    host=settings.API_HOST,
                    port=settings.API_PORT,
                    state=api.Guest()
                ).authenticate(
                    email=settings.API_EMAIL,
                    password=settings.API_PASSWORD
                )
                self.price_api = PriceAPI(self.executor)
                print("✅ Authentication successful!")
                return True
            except Exception as e:
                print(f"❌ Authentication attempt {attempt + 1} failed: {e}")
                if attempt < 2:
                    time.sleep(10)
                else:
                    return False

    def basic_lab_management_checks(self, lab_id: str):
        print(f"\n🧪 Basic Lab Management Checks for lab {lab_id}")
        try:
            status = api.get_lab_execution_status(self.executor, lab_id)
            print(f"  ✅ get_lab_execution_status: {status}")
        except Exception as e:
            print(f"  ❌ get_lab_execution_status: {e}")
        try:
            details = api.get_lab_details(self.executor, lab_id)
            print(f"  ✅ get_lab_details: {details}")
        except Exception as e:
            print(f"  ❌ get_lab_details: {e}")
        try:
            start_status = api.start_lab_execution_status(self.executor, lab_id)
            print(f"  ✅ start_lab_execution_status: {start_status}")
        except Exception as e:
            print(f"  ❌ start_lab_execution_status: {e}")
        try:
            cancel_status = api.cancel_lab_execution_status(self.executor, lab_id)
            print(f"  ✅ cancel_lab_execution_status: {cancel_status}")
        except Exception as e:
            print(f"  ❌ cancel_lab_execution_status: {e}")

    def get_markets(self, exchanges: List[str] = None) -> List[Any]:
        if exchanges is None:
            exchanges = ["BINANCE"]
        print(f"📈 Fetching markets from {exchanges}...")
        all_markets = []
        for exchange in exchanges:
            try:
                exchange_markets = self.price_api.get_trade_markets(exchange)
                all_markets.extend(exchange_markets)
                print(f"  ✅ Found {len(exchange_markets)} {exchange} markets")
            except Exception as e:
                print(f"  ⚠️ Failed to get {exchange} markets: {e}")
        return all_markets

    def find_trading_pairs(self, markets: List[Any], pairs: List[str]) -> Dict[str, List[Any]]:
        print(f"🔍 Finding markets for pairs: {pairs}")
        pair_to_markets = {}
        for pair in pairs:
            base, quote = pair.split('/')
            matching = [m for m in markets if m.primary == base.upper() and m.secondary == quote.upper()]
            if matching:
                pair_to_markets[pair] = matching
                print(f"  ✅ {pair}: {len(matching)} market(s) found")
        return pair_to_markets

    def get_bot_scripts(self, script_names: List[str]) -> Dict[str, Any]:
        print(f"🔍 Finding bot scripts: {script_names}")
        scripts = {}
        for script_name in script_names:
            try:
                found_scripts = api.get_scripts_by_name(self.executor, script_name)
                if found_scripts:
                    scripts[script_name] = found_scripts[0]
                    print(f"  ✅ {script_name}: Found")
            except Exception as e:
                print(f"  ❌ {script_name}: Error - {e}")
        return scripts

    def get_accounts(self) -> List[Any]:
        print("🏦 Getting accounts...")
        try:
            accounts = api.get_accounts(self.executor)
            if accounts:
                print(f"✅ Found {len(accounts)} account(s)")
                return accounts
            else:
                return []
        except Exception as e:
            print(f"❌ Error getting accounts: {e}")
            return []

    def create_lab_with_optimization(self, script_id: str, lab_name: str, account_id: str, market: str, param_ranges: Dict[str, List[float]] = None) -> Any:
        print(f"📋 Creating lab with optimization: {lab_name}")
        try:
            lab = api.create_lab(
                self.executor,
                CreateLabRequest(
                    script_id=script_id,
                    name=lab_name,
                    account_id=account_id,
                    market=market,
                    interval=1,
                    default_price_data_style="CandleStick"
                )
            )
            print(f"  ✅ Lab created: {lab.lab_id}")
            if param_ranges:
                # Get current parameters (may be empty)
                lab_details = api.get_lab_details(self.executor, lab.lab_id)
                params = lab_details.get('P', []) if isinstance(lab_details, dict) else getattr(lab_details, 'parameters', [])
                # Update or add parameters as needed
                for key, values in param_ranges.items():
                    found = False
                    for param in params:
                        if param['K'] == key:
                            param['O'] = values
                            param['I'] = True
                            param['IS'] = True
                            found = True
                            break
                    if not found:
                        # Add new parameter if not present
                        params.append({"K": key, "O": values, "I": True, "IS": True})
                try:
                    api.update_lab_parameters(self.executor, lab.lab_id, params)
                    print(f"  ✅ Lab parameters updated with optimization")
                except Exception as e:
                    print(f"  ⚠️ Failed to update lab parameters: {e}")
            return lab
        except Exception as e:
            print(f"  ❌ Failed to create lab: {e}")
            return None

    def run_backtest(self, lab_id: str, backtest_hours: int) -> bool:
        print(f"🚀 Starting {backtest_hours}-hour backtest for lab {lab_id}")
        try:
            now = int(time.time())
            start_unix = now - (backtest_hours * 3600)
            end_unix = now
            api.start_lab_execution(
                self.executor,
                StartLabExecutionRequest(
                    lab_id=lab_id,
                    start_unix=start_unix,
                    end_unix=end_unix,
                    send_email=False
                )
            )
            print(f"  ✅ Backtest started")
            return True
        except Exception as e:
            print(f"  ❌ Failed to start backtest: {e}")
            return False

    def get_backtest_results(self, lab_id: str) -> Any:
        print(f"📊 Getting backtest results for lab {lab_id}")
        try:
            results = api.get_backtest_result(
                self.executor,
                GetBacktestResultRequest(
                    lab_id=lab_id,
                    next_page_id=0,
                    page_lenght=1000
                )
            )
            if not results.items:
                print(f"  ❌ No backtest results found")
                return None
            best_result = max(results.items, key=lambda x: x.summary.ReturnOnInvestment if x.summary else 0)
            print(f"  ✅ Best ROI: {best_result.summary.ReturnOnInvestment if best_result.summary else 0}")
            return results
        except Exception as e:
            print(f"  ❌ Failed to get results: {e}")
            return None
    
    def delete_lab(self, lab_id: str):
        try:
            api.delete_lab(self.executor, lab_id)
            print(f"  🧹 Lab {lab_id} cleaned up")
        except Exception as e:
            print(f"  ⚠️ Failed to clean up lab {lab_id}: {e}")

    def run(self):
        if not self.authenticate():
            return
        print("\n🔍 Fetching all labs...")
        labs = api.get_all_labs(self.executor)
        if not labs:
            print("❌ No labs available.")
            return
        # Import the utility functions for parameter extraction and update
        import sys
        import importlib.util
        import os
        script_util_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'pyHaasAPI', 'api', 'scripts.py')
        spec = importlib.util.spec_from_file_location('scripts_util', script_util_path)
        scripts_util = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(scripts_util)
        extract_script_parameter_ranges = scripts_util.extract_script_parameter_ranges
        update_lab_parameters_by_key = scripts_util.update_lab_parameters_by_key
        # Parse MadHatter example for reference
        import json
        with open(os.path.join(os.path.dirname(__file__), '../../example.txt'), 'r') as f:
            lines = f.readlines()
            for line in lines:
                if line.strip().startswith('{"Success"'):
                    mad_hatter_example = json.loads(line.strip())['Data']
                    break
        mad_hatter_account = mad_hatter_example['ST']['accountId']
        mad_hatter_market = mad_hatter_example['ST']['marketTag']
        mad_hatter_params = mad_hatter_example['P']
        updated_count = 0
        for lab in labs:
            # Only update labs that are not running
            if hasattr(lab, 'status') and str(lab.status).upper() in ('RUNNING', '2'):
                print(f"  ⏩ Skipping running lab: {lab.lab_id} ({lab.name})")
                continue
            print(f"\n🛠️ Updating lab: {lab.lab_id} ({lab.name})")
            # Fetch script record
            script_id = getattr(lab, 'script_id', None) or getattr(lab, 'SID', None)
            if not script_id:
                print(f"  ⚠️ No script_id for lab {lab.lab_id}, skipping.")
                continue
            # Fetch script record from API
            script_record_resp = api.get_script_record(self.executor, script_id)
            if hasattr(script_record_resp, 'compile_result'):
                script_record = script_record_resp.compile_result.model_dump()
            elif isinstance(script_record_resp, dict) and 'compile_result' in script_record_resp:
                script_record = script_record_resp['compile_result']
            else:
                print(f"  ⚠️ Could not extract compile_result for lab {lab.lab_id}, skipping.")
                continue
            param_defs = extract_script_parameter_ranges(script_record)
            # Decide which parameters to update
            updates = {}
            script_name = getattr(lab, 'script_name', None) or getattr(lab, 'SN', '').lower()
            if not script_name:
                script_name = script_record_resp.script_name.lower() if hasattr(script_record_resp, 'script_name') else ''
            if 'mad' in script_name or 'hatter' in script_name:
                # Use accountId, marketTag, and parameters from example
                lab_details = api.get_lab_details(self.executor, lab.lab_id)
                # Set settings fields for both object and dict
                if hasattr(lab_details, 'settings'):
                    lab_details.settings.account_id = mad_hatter_account
                    lab_details.settings.market_tag = mad_hatter_market
                elif isinstance(lab_details, dict):
                    # Try both camelCase and snake_case for compatibility
                    lab_details['ST']['accountId'] = mad_hatter_account
                    lab_details['ST']['marketTag'] = mad_hatter_market
                    lab_details['ST']['account_id'] = mad_hatter_account
                    lab_details['ST']['market_tag'] = mad_hatter_market
                # Set parameters exactly as in example
                if hasattr(lab_details, 'parameters'):
                    lab_details.parameters = mad_hatter_params
                elif isinstance(lab_details, dict):
                    lab_details['P'] = mad_hatter_params
                print(f"  [DEBUG] Payload before update: settings={lab_details.settings if hasattr(lab_details, 'settings') else lab_details['ST']}, parameters={lab_details.parameters if hasattr(lab_details, 'parameters') else lab_details['P']}")
            elif 'scalper' in script_name:
                # For scalper, use first available account and market
                accounts = self.get_accounts()
                markets = self.get_markets(["BINANCE"])
                account_id = accounts[0].account_id if accounts else ''
                market_tag = f"{markets[0].price_source.upper()}_{markets[0].primary.upper()}_{markets[0].secondary.upper()}_" if markets else ''
                lab_details = api.get_lab_details(self.executor, lab.lab_id)
                if hasattr(lab_details, 'settings'):
                    lab_details.settings.account_id = account_id
                    lab_details.settings.market_tag = market_tag
                elif isinstance(lab_details, dict):
                    lab_details['ST']['accountId'] = account_id
                    lab_details['ST']['marketTag'] = market_tag
                    lab_details['ST']['account_id'] = account_id
                    lab_details['ST']['market_tag'] = market_tag
                # Update Take Profit and Stop Loss with a range
                updates = {}
                for param in param_defs:
                    if 'take profit' in (param['N'] or '').lower():
                        updates[param['K']] = [round(x * 0.2, 2) for x in range(11)]
                    if 'stop loss' in (param['N'] or '').lower():
                        updates[param['K']] = [1, 2]
                lab_details = update_lab_parameters_by_key(lab_details, updates)
                print(f"  [DEBUG] Payload before update: settings={lab_details.settings if hasattr(lab_details, 'settings') else lab_details['ST']}, parameters={lab_details.parameters if hasattr(lab_details, 'parameters') else lab_details['P']}")
            else:
                print(f"  ⚠️ Unknown script type for lab {lab.lab_id}, skipping.")
                continue
            try:
                # Set required fields to non-zero values before update
                if hasattr(lab_details, 'settings'):
                    lab_details.settings.trade_amount = 100.0
                    lab_details.settings.chart_style = 300
                elif isinstance(lab_details, dict):
                    lab_details['ST']['tradeAmount'] = 100.0
                    lab_details['ST']['chartStyle'] = 300
                # Print the actual outgoing JSON for settings
                if hasattr(lab_details, 'settings'):
                    print(f"  [OUTGOING JSON] settings: {lab_details.settings.model_dump_json(by_alias=True)}")
                elif isinstance(lab_details, dict):
                    import json as _json
                    print(f"  [OUTGOING JSON] settings: {_json.dumps(lab_details['ST'])}")
                api.update_lab_details(self.executor, lab_details)
                print(f"  ✅ Updated parameters for lab {lab.lab_id}")
                # Fetch and save updated lab details
                details = api.get_lab_details(self.executor, lab.lab_id)
                print(f"  🔍 After update: accountId={details.settings.account_id if hasattr(details, 'settings') else details['ST']['accountId']}, marketTag={details.settings.market_tag if hasattr(details, 'settings') else details['ST']['marketTag']}")
                print(f"  🔍 Parameters: {details.parameters if hasattr(details, 'parameters') else details['P']}")
                with open(f"lab_config_{lab.lab_id}_updated.json", "w") as f:
                    json.dump(details if isinstance(details, dict) else details.__dict__, f, indent=2, default=str)
                updated_count += 1
            except Exception as e:
                print(f"  ❌ Failed to update lab {lab.lab_id}: {e}")
        print(f"\n✅ Updated and saved {updated_count} labs that were not running.")

    @staticmethod
    def _frange(start, stop, step):
        while start <= stop:
            yield start
            start += step

def main():
    tester = LabIntegrationTester()
    tester.run()

if __name__ == "__main__":
    main() 