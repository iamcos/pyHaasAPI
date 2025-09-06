from pyHaasAPI import api
from pyHaasAPI.model import StartLabExecutionRequest
import time

class LabSyncAndBacktestOrchestrator:
    def __init__(self, executor, source_lab_id, market_configs, account_id, start_unix, end_unix, history_months=36):
        self.executor = executor
        self.source_lab_id = source_lab_id
        self.market_configs = market_configs  # List of dicts: [{'market_tag': ..., 'name': ...}, ...]
        self.account_id = account_id
        self.start_unix = start_unix
        self.end_unix = end_unix
        self.history_months = history_months
        self.cloned_labs = []

    def clone_labs(self):
        for config in self.market_configs:
            lab = api.clone_lab(self.executor, self.source_lab_id, config['name'])
            lab_details = api.get_lab_details(self.executor, lab.lab_id)
            lab_details.settings.market_tag = config['market_tag']
            lab_details.settings.account_id = self.account_id
            api.update_lab_details(self.executor, lab_details)
            self.cloned_labs.append(lab_details)

    def register_markets(self):
        for lab in self.cloned_labs:
            try:
                api.get_chart(self.executor, lab.settings.market_tag, interval=15, style=301)
            except Exception:
                pass  # Ignore errors, just want to trigger sync

    def wait_for_basic_sync(self, poll_interval=30, timeout=1800):
        waited = 0
        while waited < timeout:
            status = api.get_history_status(self.executor)
            all_synced = all(
                status.get(lab.settings.market_tag, {}).get("Status") == 3
                for lab in self.cloned_labs
            )
            if all_synced:
                return True
            time.sleep(poll_interval)
            waited += poll_interval
        return False

    def set_history_depth(self):
        for lab in self.cloned_labs:
            api.set_history_depth(self.executor, lab.settings.market_tag, self.history_months)

    def wait_for_full_sync(self, poll_interval=30, timeout=3600):
        waited = 0
        while waited < timeout:
            status = api.get_history_status(self.executor)
            all_full = all(
                status.get(lab.settings.market_tag, {}).get("months", 0) >= self.history_months
                for lab in self.cloned_labs
            )
            if all_full:
                return True
            time.sleep(poll_interval)
            waited += poll_interval
        return False

    def start_backtests(self):
        for lab in self.cloned_labs:
            req = StartLabExecutionRequest(
                lab_id=lab.lab_id,
                start_unix=self.start_unix,
                end_unix=self.end_unix,
                send_email=False
            )
            api.start_lab_execution(self.executor, req)
            # Optionally poll get_lab_execution_update to confirm status is running/queued

    def run(self):
        self.clone_labs()
        self.register_markets()
        self.wait_for_basic_sync()
        self.set_history_depth()
        self.wait_for_full_sync()
        self.start_backtests() 