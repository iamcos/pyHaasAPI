"""
Google Sheets integration service for pyHaasAPI.
Provides functionality to publish trading data to Google Sheets.
"""

import os
import pickle
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

import gspread
from google.oauth2.service_account import Credentials
from google.auth.transport.requests import Request

from pyHaasAPI import api
from pyHaasAPI.core.data_manager import ComprehensiveDataManager

logger = logging.getLogger(__name__)


class GoogleSheetsService:
    """Service for publishing pyHaasAPI data to Google Sheets."""
    
    def __init__(self, credentials_path: str, sheet_id: str):
        """
        Initialize Google Sheets service.
        
        Args:
            credentials_path: Path to Google service account credentials JSON
            sheet_id: Google Sheets document ID
        """
        self.credentials_path = credentials_path
        self.sheet_id = sheet_id
        self.gc = None
        self.spreadsheet = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Google Sheets API."""
        try:
            # Load credentials
            creds = Credentials.from_service_account_file(
                self.credentials_path,
                scopes=['https://www.googleapis.com/auth/spreadsheets']
            )
            
            # Create gspread client
            self.gc = gspread.authorize(creds)
            self.spreadsheet = self.gc.open_by_key(self.sheet_id)
            logger.info("Google Sheets authentication successful")
            
        except Exception as e:
            logger.error(f"Google Sheets authentication failed: {e}")
            raise
    
    def publish_server_data(self, server_name: str, data: Dict[str, Any]):
        """
        Publish data for a specific server to Google Sheets.
        
        Args:
            server_name: Name of the server (srv01, srv02, srv03)
            data: Dictionary containing labs, bots, and accounts data
        """
        try:
            # Get or create worksheet for this server
            try:
                worksheet = self.spreadsheet.worksheet(server_name)
            except gspread.WorksheetNotFound:
                worksheet = self.spreadsheet.add_worksheet(server_name, rows=1000, cols=20)
            
            # Clear existing data
            worksheet.clear()
            
            # Write headers
            headers = [
                'Type', 'ID', 'Name', 'Status', 'Market', 'Script ID', 
                'Account ID', 'ROI %', 'Realized Profit', 'Unrealized Profit',
                'Win Rate', 'Total Trades', 'Error Status', 'URL'
            ]
            worksheet.append_row(headers)
            
            # Write labs data
            for lab in data.get('labs', []):
                row = [
                    'Lab',
                    lab.get('lab_id', ''),
                    lab.get('name', ''),
                    lab.get('status', ''),
                    lab.get('market_tag', ''),
                    lab.get('script_id', ''),
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    lab.get('lab_url', '')
                ]
                worksheet.append_row(row)
            
            # Write bots data
            for bot in data.get('bots', []):
                row = [
                    'Bot',
                    bot.get('bot_id', ''),
                    bot.get('bot_name', ''),
                    bot.get('status', ''),
                    bot.get('market_tag', ''),
                    bot.get('script_id', ''),
                    bot.get('account_id', ''),
                    bot.get('roi_percentage', ''),
                    bot.get('realized_profit', ''),
                    bot.get('unrealized_profit', ''),
                    bot.get('win_rate', ''),
                    bot.get('total_trades', ''),
                    bot.get('error_status', ''),
                    bot.get('bot_url', '')
                ]
                worksheet.append_row(row)
            
            # Write accounts data
            for account in data.get('accounts', []):
                row = [
                    'Account',
                    account.get('account_id', ''),
                    account.get('name', ''),
                    account.get('status', ''),
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    account.get('account_url', '')
                ]
                worksheet.append_row(row)
            
            logger.info(f"Published data for {server_name}")
            
        except Exception as e:
            logger.error(f"Failed to publish data for {server_name}: {e}")
            raise
    
    def publish_summary(self, all_data: Dict[str, Dict[str, Any]]):
        """
        Publish summary data across all servers.
        
        Args:
            all_data: Dictionary with server names as keys and their data as values
        """
        try:
            # Get or create summary worksheet
            try:
                worksheet = self.spreadsheet.worksheet('Summary')
            except gspread.WorksheetNotFound:
                worksheet = self.spreadsheet.add_worksheet('Summary', rows=1000, cols=20)
            
            # Clear existing data
            worksheet.clear()
            
            # Write summary headers
            headers = ['Server', 'Labs Count', 'Bots Count', 'Accounts Count', 'Active Bots', 'Error Bots']
            worksheet.append_row(headers)
            
            # Write summary data for each server
            for server_name, data in all_data.items():
                labs_count = len(data.get('labs', []))
                bots_count = len(data.get('bots', []))
                accounts_count = len(data.get('accounts', []))
                active_bots = len([b for b in data.get('bots', []) if b.get('status') == 'ACTIVE'])
                error_bots = len([b for b in data.get('bots', []) if b.get('error_status') == 'ERROR'])
                
                row = [server_name, labs_count, bots_count, accounts_count, active_bots, error_bots]
                worksheet.append_row(row)
            
            logger.info("Published summary data")
            
        except Exception as e:
            logger.error(f"Failed to publish summary: {e}")
            raise


class MultiServerDataCollector:
    """Collects data from multiple pyHaasAPI servers."""
    
    def __init__(self):
        """Initialize data collector."""
        self.data_manager = ComprehensiveDataManager()
    
    async def collect_all_server_data(self, server_configs: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """
        Collect data from all configured servers.
        
        Args:
            server_configs: Dictionary with server configurations
            
        Returns:
            Dictionary with server names as keys and collected data as values
        """
        all_data = {}
        
        for server_name, config in server_configs.items():
            try:
                logger.info(f"Collecting data from {server_name}")
                
                # Connect to server
                await self.data_manager.connect_to_server(server_name)
                
                # Collect data
                data = {
                    'labs': await self._collect_labs_data(),
                    'bots': await self._collect_bots_data(),
                    'accounts': await self._collect_accounts_data()
                }
                
                all_data[server_name] = data
                logger.info(f"Collected data from {server_name}: {len(data['labs'])} labs, {len(data['bots'])} bots, {len(data['accounts'])} accounts")
                
            except Exception as e:
                logger.error(f"Failed to collect data from {server_name}: {e}")
                all_data[server_name] = {'labs': [], 'bots': [], 'accounts': []}
        
        return all_data
    
    async def _collect_labs_data(self) -> List[Dict[str, Any]]:
        """Collect labs data from current server."""
        try:
            labs = await self.data_manager.get_all_labs()
            labs_data = []
            
            for lab in labs:
                lab_data = {
                    'lab_id': getattr(lab, 'lab_id', None) or getattr(lab, 'LID', ''),
                    'name': getattr(lab, 'name', None) or getattr(lab, 'Name', ''),
                    'status': getattr(lab, 'status', None) or getattr(lab, 'Status', ''),
                    'market_tag': getattr(lab, 'market_tag', None) or getattr(lab, 'MarketTag', ''),
                    'script_id': getattr(lab, 'script_id', None) or getattr(lab, 'ScriptID', ''),
                    'lab_url': f"http://127.0.0.1:8090/Labs/{getattr(lab, 'lab_id', None) or getattr(lab, 'LID', '')}"
                }
                labs_data.append(lab_data)
            
            return labs_data
            
        except Exception as e:
            logger.error(f"Failed to collect labs data: {e}")
            return []
    
    async def _collect_bots_data(self) -> List[Dict[str, Any]]:
        """Collect bots data from current server."""
        try:
            bots = await self.data_manager.get_all_bots()
            bots_data = []
            
            for bot in bots:
                bot_data = {
                    'bot_id': getattr(bot, 'bot_id', None) or getattr(bot, 'ID', ''),
                    'bot_name': getattr(bot, 'bot_name', None) or getattr(bot, 'Name', ''),
                    'status': getattr(bot, 'status', None) or getattr(bot, 'Status', ''),
                    'market_tag': getattr(bot, 'market_tag', None) or getattr(bot, 'MarketTag', ''),
                    'script_id': getattr(bot, 'script_id', None) or getattr(bot, 'ScriptID', ''),
                    'account_id': getattr(bot, 'account_id', None) or getattr(bot, 'AccountID', ''),
                    'roi_percentage': '',
                    'realized_profit': '',
                    'unrealized_profit': '',
                    'win_rate': '',
                    'total_trades': '',
                    'error_status': 'ERROR' if getattr(bot, 'status', '') in ['ERROR', 'FAILED'] else '',
                    'bot_url': f"http://127.0.0.1:8090/Bots/{getattr(bot, 'bot_id', None) or getattr(bot, 'ID', '')}"
                }
                
                # Try to get performance data
                try:
                    runtime_data = await self.data_manager.get_bot_runtime_data(bot_data['bot_id'])
                    if runtime_data:
                        bot_data['roi_percentage'] = getattr(runtime_data, 'return_on_investment', '')
                        bot_data['realized_profit'] = getattr(runtime_data, 'realized_profit', '')
                        bot_data['unrealized_profit'] = getattr(runtime_data, 'unrealized_profit', '')
                except Exception:
                    pass
                
                bots_data.append(bot_data)
            
            return bots_data
            
        except Exception as e:
            logger.error(f"Failed to collect bots data: {e}")
            return []
    
    async def _collect_accounts_data(self) -> List[Dict[str, Any]]:
        """Collect accounts data from current server."""
        try:
            accounts = await self.data_manager.get_all_accounts()
            accounts_data = []
            
            for account in accounts:
                account_data = {
                    'account_id': getattr(account, 'id', None) or getattr(account, 'AID', ''),
                    'name': getattr(account, 'name', None) or getattr(account, 'Name', ''),
                    'status': getattr(account, 'status', None) or getattr(account, 'Status', ''),
                    'balance': getattr(account, 'balance', None) or getattr(account, 'Balance', ''),
                    'currency': getattr(account, 'currency', None) or getattr(account, 'Currency', ''),
                    'exchange': getattr(account, 'exchange', None) or getattr(account, 'Exchange', ''),
                    'account_url': f"http://127.0.0.1:8090/Accounts/{getattr(account, 'id', None) or getattr(account, 'AID', '')}"
                }
                accounts_data.append(account_data)
            
            return accounts_data
            
        except Exception as e:
            logger.error(f"Failed to collect accounts data: {e}")
            return []