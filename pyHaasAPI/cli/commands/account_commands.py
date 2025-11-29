"""
Account command handlers - Direct calls to AccountAPI/AccountManager
"""

from typing import Any
from ..base import BaseCLI


class AccountCommands:
    """Account command handlers - thin wrappers around AccountAPI"""
    
    def __init__(self, cli: BaseCLI):
        self.cli = cli
    
    async def handle(self, action: str, args: Any) -> int:
        """Handle account commands"""
        account_api = self.cli.account_api
        account_manager = self.cli.account_manager
        
        if not account_api:
            self.cli.logger.error("Account API not initialized")
            return 1
        
        try:
            if action == 'assign':
                # Get next account using AccountManager (round-robin)
                if not account_manager:
                    self.cli.logger.error("AccountManager not initialized")
                    return 1
                
                exchange = args.exchange if hasattr(args, 'exchange') else "BINANCEFUTURES"
                account = await account_manager.assign_account_round_robin(exchange=exchange)
                account_data = [{
                    'account_id': account.account_id,
                    'account_name': account.name,
                    'server': account_manager.server,
                    'exchange': account.exchange
                }]
                self.cli.format_output(account_data, args.output_format, args.output_file)
                return 0
                
            elif action == 'create':
                # Create account using AccountManager
                if not account_manager:
                    self.cli.logger.error("AccountManager not initialized")
                    return 1
                
                exchange = args.exchange if hasattr(args, 'exchange') else "BINANCEFUTURES"
                account = await account_manager.get_or_create_account(exchange=exchange)
                account_data = [{
                    'account_id': account.account_id,
                    'account_name': account.name,
                    'server': account_manager.server,
                    'exchange': account.exchange
                }]
                self.cli.format_output(account_data, args.output_format, args.output_file)
                return 0
                
            elif action == 'validate':
                # Validate account balance - use AccountAPI directly
                if not args.account_id:
                    self.cli.logger.error("--account-id is required")
                    return 1
                
                balance = await account_api.get_account_balance(args.account_id)
                account_data = await account_api.get_account_data(args.account_id)
                min_balance = account_manager.min_balance if account_manager else 1000.0
                is_valid = balance >= min_balance
                
                validation_data = [{
                    'account_id': args.account_id,
                    'balance': balance,
                    'min_required': min_balance,
                    'valid': is_valid
                }]
                self.cli.format_output(validation_data, args.output_format, args.output_file)
                return 0
                
            elif action == 'list':
                # Direct API call
                accounts = await account_api.get_all_accounts()
                self.cli.format_output(accounts, args.output_format, args.output_file)
                return 0
                
            elif action == 'balance':
                # Direct API call
                if not args.account_id:
                    self.cli.logger.error("--account-id is required")
                    return 1
                
                balance = await account_api.get_account_balance(args.account_id)
                balance_data = [{'account_id': args.account_id, 'balance': balance}]
                self.cli.format_output(balance_data, args.output_format, args.output_file)
                return 0
                
            elif action == 'settings':
                # Direct API call
                if not args.account_id:
                    self.cli.logger.error("--account-id is required")
                    return 1
                
                account_data = await account_api.get_account_data(args.account_id)
                self.cli.format_output([account_data], args.output_format, args.output_file)
                return 0
                
            elif action == 'orders':
                # Direct API call
                if not args.account_id:
                    self.cli.logger.error("--account-id is required")
                    return 1
                
                orders = await account_api.get_account_orders(args.account_id)
                self.cli.format_output(orders, args.output_format, args.output_file)
                return 0
                
            elif action == 'positions':
                # Direct API call
                if not args.account_id:
                    self.cli.logger.error("--account-id is required")
                    return 1
                
                positions = await account_api.get_account_positions(args.account_id)
                self.cli.format_output(positions, args.output_format, args.output_file)
                return 0
                
            else:
                self.cli.logger.error(f"Unknown account action: {action}")
                return 1
                
        except Exception as e:
            self.cli.logger.error(f"Error executing account command: {e}")
            if args.verbose:
                import traceback
                traceback.print_exc()
            return 1

