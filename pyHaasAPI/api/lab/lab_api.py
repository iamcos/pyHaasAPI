"""
Lab API module for pyHaasAPI v2

Provides comprehensive lab management functionality including creation,
configuration, execution, and monitoring of trading labs.
"""

import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime

from ...core.client import AsyncHaasClient
from ...core.auth import AuthenticationManager
from ...exceptions import LabError, LabNotFoundError, LabExecutionError, LabConfigurationError
from ...core.logging import get_logger
from ...core.field_utils import (
    safe_get_field, safe_get_nested_field, safe_get_dict_field,
    safe_get_success_flag, safe_get_market_tag, safe_get_account_id,
    safe_get_status, log_field_mapping_issues
)
from ...models.lab import LabDetails, LabRecord, LabConfig, StartLabExecutionRequest, LabExecutionUpdate
from ..account.account_api import AccountAPI
from ..script.script_api import ScriptAPI


class LabAPI:
    """
    Lab API for managing trading labs
    
    Provides comprehensive lab management functionality including creation,
    configuration, execution, and monitoring of trading labs.
    """
    
    def __init__(self, client: AsyncHaasClient, auth_manager: AuthenticationManager):
        self.client = client
        self.auth_manager = auth_manager
        self.logger = get_logger("lab_api")
    
    async def create_lab(
        self,
        script_id: str,
        name: str = "",
        account_id: str = "",
        market: str = "",
        interval: int = 1,
        default_price_data_style: str = "CandleStick",
        trade_amount: float = 100.0,
        chart_style: int = 300,
        order_template: int = 500,
        leverage: float = 0.0,
        position_mode: int = 0,
        margin_mode: int = 0,
        **kwargs: Any
    ) -> LabDetails:
        """
        Create a new lab
        
        Args:
            script_id: ID of the script to use
            name: Name for the lab
            account_id: ID of the account to use
            market: Market tag (e.g., "BINANCE_BTC_USDT_")
            interval: Data interval in minutes
            default_price_data_style: Price data style (default: "CandleStick")
            trade_amount: Trade amount
            chart_style: Chart style ID
            order_template: Order template ID
            leverage: Leverage value
            position_mode: Position mode (0=ONE_WAY, 1=HEDGE)
            margin_mode: Margin mode (0=CROSS, 1=ISOLATED)
            
        Returns:
            LabDetails object for the created lab
            
        Raises:
            LabError: If lab creation fails
        """
        try:
            await self.auth_manager.ensure_authenticated()
            
            # Support tests that pass 'lab_name' instead of 'name'
            lab_name = safe_get_dict_field(kwargs, "lab_name") or name
            if not lab_name:
                raise LabError("Lab name is required")
            self.logger.info(f"Creating lab: {lab_name}")
            
            # Authentication parameters required for write operations
            session = self.auth_manager.session
            if not session:
                raise LabError("Not authenticated")
            
            # Map alternate kwarg names used by tests to server-expected keys
            market_tag = safe_get_dict_field(kwargs, "market_tag") or market
            provided_script_id = script_id
            provided_account_id = account_id
            
            # Resolve script_id if a human-friendly name was provided
            if provided_script_id and len(provided_script_id) < 16:
                try:
                    scripts_api = ScriptAPI(self.client, self.auth_manager)
                    scripts = await scripts_api.get_all_scripts()
                    for si in scripts:
                        name = getattr(si, 'name', '') or getattr(si, 'Name', '')
                        sid = getattr(si, 'script_id', '') or getattr(si, 'SID', '') or getattr(si, 'id', '')
                        if name == provided_script_id or sid == provided_script_id:
                            provided_script_id = sid or provided_script_id
                            break
                except Exception:
                    pass
            
            # Resolve account_id if a label/email was provided
            if provided_account_id and ('@' in provided_account_id or len(provided_account_id) < 16):
                try:
                    account_api = AccountAPI(self.client, self.auth_manager)
                    accounts = await account_api.get_accounts()
                    for acc in accounts:
                        uid = getattr(acc, 'UID', '') or getattr(acc, 'account_id', '') or getattr(acc, 'id', '')
                        name = getattr(acc, 'Name', '') or getattr(acc, 'name', '')
                        if provided_account_id in (uid, name):
                            provided_account_id = uid or provided_account_id
                            break
                except Exception:
                    pass
            # Normalize interval: support "1h", "5m", numeric strings
            norm_interval = interval
            if isinstance(norm_interval, str):
                s = norm_interval.strip().lower()
                try:
                    if s.endswith("h"):
                        norm_interval = int(float(s[:-1]) * 60)
                    elif s.endswith("m"):
                        norm_interval = int(float(s[:-1]))
                    else:
                        norm_interval = int(float(s))
                except Exception:
                    norm_interval = 1
            # Normalize chart style
            norm_chart_style = chart_style
            if isinstance(norm_chart_style, str):
                if norm_chart_style.lower() in {"candles", "candlestick", "candle"}:
                    norm_chart_style = 300
                elif norm_chart_style.lower() in {"line", "spark"}:
                    norm_chart_style = 100
                else:
                    # Fallback default
                    norm_chart_style = 300
            
            # Try multiple canonical permutations: endpoints, channels, and key casings
            attempts = []
            def camel_payload():
                return {
                    "userid": session.user_id,
                    "interfacekey": session.interface_key,
                    "scriptId": provided_script_id,
                    "name": lab_name,
                    "accountId": provided_account_id,
                    "market": market_tag,
                    "interval": norm_interval,
                    "style": default_price_data_style,
                    "tradeAmount": trade_amount,
                    "chartStyle": norm_chart_style,
                    "orderTemplate": order_template,
                    "leverage": leverage,
                    "positionMode": position_mode,
                    "marginMode": margin_mode,
                }
            def snake_payload():
                return {
                    "userid": session.user_id,
                    "interfacekey": session.interface_key,
                    "scriptid": provided_script_id,
                    "name": lab_name,
                    "accountid": provided_account_id,
                    "market": market_tag,
                    "interval": norm_interval,
                    "style": default_price_data_style,
                    "tradeamount": trade_amount,
                    "chartstyle": norm_chart_style,
                    "ordertemplate": order_template,
                    "leverage": leverage,
                    "positionmode": position_mode,
                    "marginmode": margin_mode,
                }
            for endpoint in ("Labs",):
                for channel in ("CREATE_LAB", "ADD_LAB"):
                    attempts.append((endpoint, channel, camel_payload()))
                    attempts.append((endpoint, channel, snake_payload()))
            response = None
            last_error = None
            for endpoint, channel, payload in attempts:
                try:
                    resp = await self.client.post_json(
                        endpoint,
                        params={
                            "channel": channel,
                            "userid": session.user_id,
                            "interfacekey": session.interface_key,
                        },
                        data=payload
                    )
                    if safe_get_success_flag(resp):
                        response = resp
                        break
                    else:
                        last_error = safe_get_field(resp, "Error", f"Attempt {channel} on {endpoint} failed")
                except Exception as e:
                    last_error = str(e)
                    continue
            if response is None:
                # Fallback: clone an existing lab then update details
                try:
                    self.logger.info("CREATE_LAB failed; attempting CLONE_LAB fallback")
                    existing_labs = await self.get_labs()
                    if not existing_labs:
                        raise LabError(message=f"No labs available to clone; last error: {last_error}")
                    source_lab = existing_labs[0]
                    clone_resp = await self.client.post_json(
                        "/LabsAPI.php",
                        data={
                            "channel": "CLONE_LAB",
                            "userid": session.user_id,
                            "interfacekey": session.interface_key,
                            "labid": getattr(source_lab, 'lab_id', None) or getattr(source_lab, 'LID', ''),
                            "name": lab_name,
                        }
                    )
                    if not safe_get_success_flag(clone_resp):
                        err = safe_get_field(clone_resp, "Error", last_error or "CLONE_LAB failed")
                        raise LabError(message=f"Failed to clone lab: {err}")
                    cloned_data = safe_get_field(clone_resp, "Data", {})
                    cloned_lab = LabDetails(**cloned_data)
                    # Apply requested settings
                    update_payload = {
                        "name": lab_name,
                        "script_id": provided_script_id,
                        "account_id": provided_account_id,
                        "market": market_tag,
                        "interval": norm_interval,
                        "trade_amount": trade_amount,
                        "chart_style": norm_chart_style,
                        "order_template": order_template,
                        "leverage": leverage,
                        "position_mode": position_mode,
                        "margin_mode": margin_mode,
                    }
                    updated = await self.update_lab_details(cloned_lab.lab_id, update_payload)
                    return updated
                except Exception as e:
                    raise LabError(message=f"Failed to create lab via fallback: {e}")
            
            if not safe_get_success_flag(response):
                error_msg = safe_get_field(response, "Error", "Lab creation failed")
                raise LabError(message=f"Failed to create lab: {error_msg}")
            
            lab_data = safe_get_field(response, "Data", {})
            if not lab_data:
                raise LabError(message="No lab data returned from API")
            
            # Log field mapping for debugging
            log_field_mapping_issues(lab_data, "lab creation response")
            
            lab_details = LabDetails(**lab_data)
            
            self.logger.info(f"Lab created successfully: {lab_details.lab_id}")
            return lab_details
            
        except Exception as e:
            self.logger.error(f"Lab creation failed: {e}")
            if isinstance(e, LabError):
                raise
            else:
                raise LabError(message=f"Lab creation failed: {e}")
    
    async def get_labs(self) -> List[LabRecord]:
        """
        Get all labs for the authenticated user
        
        Based on the most recent v1 implementation from pyHaasAPI/api.py (lines 816-825)
        
        Returns:
            List of LabRecord objects
            
        Raises:
            LabError: If API request fails
        """
        try:
            await self.auth_manager.ensure_authenticated()
            
            self.logger.info("Fetching all labs")
            
            # Use POST with auth parameters in body
            session = self.auth_manager.session
            if not session:
                raise LabError("Not authenticated")
            
            post_data = {
                'interfacekey': session.interface_key,
                'userid': session.user_id
            }
            
            response = await self.client.post_json(
                endpoint="Labs",
                params={"channel": "GET_LABS"},
                data=post_data
            )
            
            # Parse response data - v1 returns data directly for list responses
            if isinstance(response, list):
                # Direct list response
                labs_data = response
            else:
                # Wrapped response - use dict field access for dictionary responses
                if not safe_get_dict_field(response, "Success", False):
                    error_msg = safe_get_dict_field(response, "Error", "Unknown error")
                    raise LabError(message=f"API request failed: {error_msg}")
                
                labs_data = safe_get_dict_field(response, "Data", [])
            
            # Convert to LabRecord objects
            labs = [LabRecord(**lab_data) for lab_data in labs_data]
            
            self.logger.info(f"Successfully fetched {len(labs)} labs")
            return labs
            
        except Exception as e:
            self.logger.error(f"Error fetching labs: {e}")
            raise LabError(message=f"Failed to fetch labs: {e}")
    
    async def get_lab_details(self, lab_id: str) -> LabDetails:
        """
        Get details for a specific lab
        
        Args:
            lab_id: ID of the lab to get details for
            
        Returns:
            LabDetails object containing the lab configuration
            
        Raises:
            LabNotFoundError: If lab is not found
            LabError: If API request fails
        """
        try:
            await self.auth_manager.ensure_authenticated()
            
            self.logger.info(f"Getting details for lab: {lab_id}")
            
            # Use POST with auth parameters in body
            session = self.auth_manager.session
            if not session:
                raise LabError("Not authenticated")
            
            post_data = {
                'labid': lab_id,
                'interfacekey': session.interface_key,
                'userid': session.user_id
            }
            
            response = await self.client.post_json(
                "/LabsAPI.php",
                params={"channel": "GET_LAB_DETAILS"},
                data=post_data
            )
            
            if not safe_get_success_flag(response):
                error_msg = safe_get_field(response, "Error", "Failed to get lab details")
                if "not found" in error_msg.lower():
                    raise LabNotFoundError(lab_id)
                else:
                    raise LabError(message=f"Failed to get lab details: {error_msg}")
            
            # Debug: Log the actual response structure
            self.logger.debug(f"Raw API response type: {type(response)}")
            self.logger.debug(f"Raw API response: {response}")
            
            # Try to get lab data from different possible locations
            if isinstance(response, dict):
                # Response is a dictionary - use dict access
                lab_data = response.get("Data", None)
                if not lab_data:
                    # If no Data field, check if response is the lab data directly
                    if "LID" in response:
                        lab_data = response
                    else:
                        # Log available keys for debugging
                        self.logger.debug(f"Available keys in response: {list(response.keys())}")
                        raise LabError(message="No lab data returned from API")
            else:
                # Response is an object - use safe_get_field
                lab_data = safe_get_field(response, "Data", None)
                if not lab_data:
                    # If no Data field, check if response is the lab data directly
                    if hasattr(response, "LID"):
                        lab_data = response
                    else:
                        raise LabError(message="No lab data returned from API")
            
            self.logger.debug(f"Raw lab data: {lab_data}")
            
            # Log field mapping for debugging
            log_field_mapping_issues(lab_data, f"lab {lab_id}")
            
            # Debug ST (settings) data structure
            st_data = safe_get_field(lab_data, "ST", {})
            self.logger.debug(f"ST (settings) data: {st_data}")
            if st_data:
                self.logger.debug(f"ST data keys: {list(st_data.keys())}")
            
            # Use safe field access for market tag
            market_tag = safe_get_market_tag(lab_data)
            if not market_tag:
                self.logger.warning(f"Market tag not found in lab {lab_id}")
            else:
                self.logger.debug(f"Found market tag: {market_tag}")
            
            # Use safe field access for account ID
            account_id = safe_get_account_id(lab_data)
            if not account_id:
                self.logger.warning(f"Account ID not found in lab {lab_id}")
            
            # Map API response to LabDetails model using dictionary access for dict responses
            if isinstance(lab_data, dict):
                # Use dictionary access for dict responses
                mapped_data = {
                    "labId": lab_data.get("LID", ""),
                    "name": lab_data.get("N", ""),
                    "scriptId": lab_data.get("SID", ""),
                    "scriptName": lab_data.get("SN", ""),  # Script name not in response
                    "settings": {
                        "accountId": lab_data.get("ST", {}).get("accountId", ""),
                        "marketTag": lab_data.get("ST", {}).get("marketTag", ""),
                        "interval": lab_data.get("ST", {}).get("interval", 1),
                        "tradeAmount": lab_data.get("ST", {}).get("tradeAmount", 100.0),
                        "chartStyle": lab_data.get("ST", {}).get("chartStyle", 300),
                        "orderTemplate": lab_data.get("ST", {}).get("orderTemplate", 500),
                        "leverage": lab_data.get("ST", {}).get("leverage", 0.0),
                        "positionMode": lab_data.get("ST", {}).get("positionMode", 0),
                        "marginMode": lab_data.get("ST", {}).get("marginMode", 0)
                    },
                    "config": {
                        "max_parallel": lab_data.get("C", {}).get("MP", 10),
                        "max_generations": lab_data.get("C", {}).get("MG", 30),
                        "max_epochs": lab_data.get("C", {}).get("ME", 3),
                        "max_runtime": lab_data.get("C", {}).get("MR", 0),
                        "auto_restart": lab_data.get("C", {}).get("AR", 0)
                    },
                    "status": self._map_status(lab_data.get("S", 0)),  # Map status number to string
                    "createdAt": lab_data.get("CA"),
                    "updatedAt": lab_data.get("UA"),
                    "backtestCount": lab_data.get("CB", 0)
                }
            else:
                # Use safe field access for object responses
                mapped_data = {
                    "labId": safe_get_field(lab_data, "LID", required=True),
                    "name": safe_get_field(lab_data, "N", required=True),
                    "scriptId": safe_get_field(lab_data, "SID", required=True),
                    "scriptName": safe_get_field(lab_data, "SN", ""),  # Script name not in response
                    "settings": {
                        "accountId": account_id,
                        "marketTag": market_tag,
                        "interval": safe_get_nested_field(lab_data, "ST.interval", 1),
                        "tradeAmount": safe_get_nested_field(lab_data, "ST.tradeAmount", 100.0) or safe_get_nested_field(lab_data, "ST.trade_amount", 100.0),
                        "chartStyle": safe_get_nested_field(lab_data, "ST.chartStyle", 300) or safe_get_nested_field(lab_data, "ST.chart_style", 300),
                        "orderTemplate": safe_get_nested_field(lab_data, "ST.orderTemplate", 500) or safe_get_nested_field(lab_data, "ST.order_template", 500),
                        "leverage": safe_get_nested_field(lab_data, "ST.leverage", 0.0),
                        "positionMode": safe_get_nested_field(lab_data, "ST.positionMode", 0) or safe_get_nested_field(lab_data, "ST.position_mode", 0),
                        "marginMode": safe_get_nested_field(lab_data, "ST.marginMode", 0) or safe_get_nested_field(lab_data, "ST.margin_mode", 0)
                    },
                    "config": {
                        "max_parallel": safe_get_nested_field(lab_data, "C.MP", 10),
                        "max_generations": safe_get_nested_field(lab_data, "C.MG", 30),
                        "max_epochs": safe_get_nested_field(lab_data, "C.ME", 3),
                        "max_runtime": safe_get_nested_field(lab_data, "C.MR", 0),
                        "auto_restart": safe_get_nested_field(lab_data, "C.AR", 0)
                    },
                    "status": self._map_status(safe_get_field(lab_data, "S", 0)),  # Map status number to string
                    "createdAt": safe_get_field(lab_data, "CA"),
                    "updatedAt": safe_get_field(lab_data, "UA"),
                    "backtestCount": safe_get_field(lab_data, "CB", 0)
                }
            
            lab_details = LabDetails(**mapped_data)
            
            self.logger.info(f"Retrieved lab details: {lab_details.name}")
            return lab_details
            
        except LabNotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to get lab details: {e}")
            if isinstance(e, LabError):
                raise
            else:
                raise LabError(message=f"Failed to get lab details: {e}")
    
    def _map_status(self, status_code: int) -> str:
        """Map numeric status code to string status"""
        status_map = {
            0: "ACTIVE",
            1: "ACTIVE", 
            2: "RUNNING",
            3: "COMPLETED",
            4: "COMPLETED",  # Based on the error, 4 seems to be completed
            5: "FAILED",
            6: "CANCELLED"
        }
        return safe_get_dict_field(status_map, status_code, "ACTIVE")
    
    async def update_lab_details(self, lab_id_or_details, update_data: Optional[Dict[str, Any]] = None) -> LabDetails:
        """
        Update lab details and verify the update
        
        Args:
            lab_id_or_details: Either LabDetails object or lab_id string
            update_data: Dict with fields to update when lab_id is provided
            
        Returns:
            LabDetails object containing the updated lab configuration
            
        Raises:
            LabError: If API request fails
        """
        try:
            await self.auth_manager.ensure_authenticated()
            
            # Normalize inputs
            if isinstance(lab_id_or_details, LabDetails):
                lab_id = lab_id_or_details.lab_id
                # Build payload from LabDetails object
                payload = {
                    "labid": lab_id_or_details.lab_id,
                    "name": getattr(lab_id_or_details, 'name', None) or getattr(lab_id_or_details, 'lab_name', None),
                    "scriptid": getattr(lab_id_or_details, 'script_id', None) or getattr(lab_id_or_details, 'SID', None),
                    "accountid": getattr(getattr(lab_id_or_details, 'settings', None), 'account_id', None),
                    "market": getattr(getattr(lab_id_or_details, 'settings', None), 'market_tag', None),
                    "interval": getattr(getattr(lab_id_or_details, 'settings', None), 'interval', None),
                    "tradeamount": getattr(getattr(lab_id_or_details, 'settings', None), 'trade_amount', None),
                    "chartstyle": getattr(getattr(lab_id_or_details, 'settings', None), 'chart_style', None),
                    "ordertemplate": getattr(getattr(lab_id_or_details, 'settings', None), 'order_template', None),
                    "leverage": getattr(getattr(lab_id_or_details, 'settings', None), 'leverage', None),
                    "positionmode": getattr(getattr(lab_id_or_details, 'settings', None), 'position_mode', None),
                    "marginmode": getattr(getattr(lab_id_or_details, 'settings', None), 'margin_mode', None),
                }
            else:
                lab_id = str(lab_id_or_details)
                # Map update_data keys to server expectations (accept snake/camel/test keys)
                ud = update_data or {}
                def pick(*keys, default=None):
                    for k in keys:
                        if k in ud and ud[k] is not None:
                            return ud[k]
                    return default
                payload = {
                    "labid": lab_id,
                    "name": pick('name','lab_name'),
                    "scriptid": pick('scriptid','script_id','scriptId'),
                    "accountid": pick('accountid','account_id','accountId'),
                    "market": pick('market','market_tag','marketTag'),
                    "interval": pick('interval'),
                    "tradeamount": pick('tradeamount','trade_amount','tradeAmount'),
                    "chartstyle": pick('chartstyle','chart_style','chartStyle'),
                    "ordertemplate": pick('ordertemplate','order_template','orderTemplate'),
                    "leverage": pick('leverage'),
                    "positionmode": pick('positionmode','position_mode','positionMode'),
                    "marginmode": pick('marginmode','margin_mode','marginMode'),
                }
            
            self.logger.info(f"Updating lab details: {lab_id}")
            
            # Remove None values
            payload = {k: v for k, v in payload.items() if v is not None}
            
            # Build v1-style form payload with JSON blocks
            import json
            form_data = {
                'labid': safe_get_dict_field(payload, 'labid'),
                'name': safe_get_dict_field(payload, 'name'),
            }
            # Optional header fields if present
            if 'type' in payload:
                form_data['type'] = str(payload['type'])
            if 'startunix' in payload:
                form_data['startunix'] = str(payload['startunix'])
            if 'endunix' in payload:
                form_data['endunix'] = str(payload['endunix'])
            
            # Config JSON (short keys per server expectations)
            config_json = {
                "MP": safe_get_dict_field(payload, 'maxparallel') or safe_get_dict_field(payload, 'max_parallel') or safe_get_dict_field(payload, 'maxParallel'),
                "MG": safe_get_dict_field(payload, 'maxgenerations') or safe_get_dict_field(payload, 'max_generations') or safe_get_dict_field(payload, 'maxGenerations'),
                "ME": safe_get_dict_field(payload, 'maxepochs') or safe_get_dict_field(payload, 'max_epochs') or safe_get_dict_field(payload, 'maxEpochs'),
                "MR": safe_get_dict_field(payload, 'maxruntime') or safe_get_dict_field(payload, 'max_runtime') or safe_get_dict_field(payload, 'maxRuntime'),
                "AR": safe_get_dict_field(payload, 'autorestart') or safe_get_dict_field(payload, 'auto_restart') or safe_get_dict_field(payload, 'autoRestart'),
            }
            config_json = {k: v for k, v in config_json.items() if v is not None}
            if config_json:
                form_data['config'] = json.dumps(config_json)
            
            # Settings JSON (camelCase per v1)
            settings_json = {
                "botId": safe_get_dict_field(payload, 'botid') or safe_get_dict_field(payload, 'bot_id'),
                "botName": safe_get_dict_field(payload, 'botname') or safe_get_dict_field(payload, 'bot_name'),
                "accountId": safe_get_dict_field(payload, 'accountid') or safe_get_dict_field(payload, 'account_id') or safe_get_dict_field(payload, 'accountId'),
                "marketTag": safe_get_dict_field(payload, 'market') or safe_get_dict_field(payload, 'market_tag') or safe_get_dict_field(payload, 'marketTag'),
                "leverage": safe_get_dict_field(payload, 'leverage'),
                "positionMode": safe_get_dict_field(payload, 'positionmode') or safe_get_dict_field(payload, 'position_mode') or safe_get_dict_field(payload, 'positionMode'),
                "marginMode": safe_get_dict_field(payload, 'marginmode') or safe_get_dict_field(payload, 'margin_mode') or safe_get_dict_field(payload, 'marginMode'),
                "interval": safe_get_dict_field(payload, 'interval'),
                "chartStyle": safe_get_dict_field(payload, 'chartstyle') or safe_get_dict_field(payload, 'chart_style') or safe_get_dict_field(payload, 'chartStyle'),
                "tradeAmount": safe_get_dict_field(payload, 'tradeamount') or safe_get_dict_field(payload, 'trade_amount') or safe_get_dict_field(payload, 'tradeAmount'),
                "orderTemplate": safe_get_dict_field(payload, 'ordertemplate') or safe_get_dict_field(payload, 'order_template') or safe_get_dict_field(payload, 'orderTemplate'),
                "scriptParameters": safe_get_dict_field(payload, 'scriptparameters') or safe_get_dict_field(payload, 'script_parameters') or safe_get_dict_field(payload, 'scriptParameters') or {},
            }
            settings_json = {k: v for k, v in settings_json.items() if v is not None}
            if settings_json:
                form_data['settings'] = json.dumps(settings_json)
            
            # Authentication
            form_data['interfacekey'] = self.auth_manager.interface_key
            form_data['userid'] = self.auth_manager.user_id
            
            # Send with channel in query params
            response = await self.client.post_json(
                "/LabsAPI.php",
                params={"channel": "UPDATE_LAB_DETAILS"},
                data=form_data
            )
            
            if not safe_get_success_flag(response):
                error_msg = safe_get_field(response, "Error", "Failed to update lab details")
                raise LabError(message=f"Failed to update lab details: {error_msg}")
            
            updated_data = safe_get_field(response, "Data", {})
            if not updated_data:
                raise LabError(message="No updated lab data returned from API")
            
            updated_lab = LabDetails(**updated_data)
            
            self.logger.info(f"Lab details updated successfully: {updated_lab.name}")
            return updated_lab
            
        except Exception as e:
            self.logger.error(f"Failed to update lab details: {e}")
            if isinstance(e, LabError):
                raise
            else:
                raise LabError(message=f"Failed to update lab details: {e}")
    
    async def delete_lab(self, lab_id: str) -> bool:
        """
        Delete a lab
        
        Args:
            lab_id: ID of the lab to delete
            
        Returns:
            True if deletion was successful
            
        Raises:
            LabNotFoundError: If lab is not found
            LabError: If API request fails
        """
        try:
            await self.auth_manager.ensure_authenticated()
            
            self.logger.info(f"Deleting lab: {lab_id}")
            
            session = self.auth_manager.session
            if not session:
                raise LabError("Not authenticated")
            
            response = await self.client.post_json(
                "/LabsAPI.php",
                params={"channel": "DELETE_LAB"},
                data={
                    "userid": session.user_id,
                    "interfacekey": session.interface_key,
                    "labid": lab_id
                }
            )
            
            if not safe_get_success_flag(response):
                error_msg = safe_get_field(response, "Error", "Failed to delete lab")
                if "not found" in error_msg.lower():
                    raise LabNotFoundError(lab_id)
                else:
                    raise LabError(message=f"Failed to delete lab: {error_msg}")
            
            self.logger.info(f"Lab deleted successfully: {lab_id}")
            return True
            
        except LabNotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to delete lab: {e}")
            if isinstance(e, LabError):
                raise
            else:
                raise LabError(message=f"Failed to delete lab: {e}")
    
    async def clone_lab(self, lab_id: str, new_name: Optional[str] = None) -> LabDetails:
        """
        Clone an existing lab with all settings and parameters preserved
        
        Args:
            lab_id: ID of the lab to clone
            new_name: Optional new name for the cloned lab
            
        Returns:
            LabDetails object for the newly created lab
            
        Raises:
            LabNotFoundError: If source lab is not found
            LabError: If API request fails
        """
        try:
            await self.auth_manager.ensure_authenticated()
            
            # Get the original lab details first
            original_lab = await self.get_lab_details(lab_id)
            
            # Generate new name if not provided
            if not new_name:
                new_name = f"Clone of {original_lab.name}"
            
            self.logger.info(f"Cloning lab {lab_id} to {new_name}")
            
            session = self.auth_manager.session
            if not session:
                raise LabError("Not authenticated")
            
            post_data = {
                'labid': lab_id,
                'name': new_name,
                'interfacekey': session.interface_key,
                'userid': session.user_id
            }
            
            response = await self.client.post_json(
                "/LabsAPI.php",
                params={"channel": "CLONE_LAB"},
                data=post_data
            )
            
            # Debug: Log the actual response structure
            self.logger.debug(f"Raw clone_lab response type: {type(response)}")
            self.logger.debug(f"Raw clone_lab response: {response}")
            
            if not safe_get_success_flag(response):
                error_msg = safe_get_field(response, "Error", "Failed to clone lab")
                raise LabError(message=f"Failed to clone lab: {error_msg}")
            
            # Handle the response structure - it has Success, Error, Data
            if isinstance(response, dict) and "Data" in response:
                cloned_data = response["Data"]
            else:
                cloned_data = safe_get_field(response, "Data", {})
            
            if not cloned_data:
                # Log available keys for debugging
                if isinstance(response, dict):
                    self.logger.debug(f"Available keys in clone response: {list(response.keys())}")
                raise LabError(message="No cloned lab data returned from API")
            
            # Map the API response to the expected model structure
            mapped_data = self._map_lab_response_to_model(cloned_data)
            cloned_lab = LabDetails(**mapped_data)
            
            self.logger.info(f"Lab cloned successfully: {cloned_lab.lab_id}")
            return cloned_lab
            
        except LabNotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to clone lab: {e}")
            if isinstance(e, LabError):
                raise
            else:
                raise LabError(message=f"Failed to clone lab: {e}")
    
    def _map_lab_response_to_model(self, lab_data: dict) -> dict:
        """Map API response to LabDetails model structure"""
        try:
            # Extract basic fields
            lab_id = lab_data.get("LID", "")
            name = lab_data.get("N", "")
            script_id = lab_data.get("SID", "")
            
            # Extract settings from ST field
            st_data = lab_data.get("ST", {})
            settings = {
                "accountId": st_data.get("accountId", ""),
                "marketTag": st_data.get("marketTag", ""),
                "interval": st_data.get("interval", 1),
                "tradeAmount": st_data.get("tradeAmount", 100.0),
                "chartStyle": st_data.get("chartStyle", 300),
                "orderTemplate": st_data.get("orderTemplate", 500),
                "leverage": st_data.get("leverage", 0.0),
                "positionMode": st_data.get("positionMode", 0),
                "marginMode": st_data.get("marginMode", 0),
            }
            
            # Extract config from C field
            c_data = lab_data.get("C", {})
            config = {
                "max_parallel": c_data.get("MP", 10),
                "max_generations": c_data.get("MG", 30),
                "max_epochs": c_data.get("ME", 3),
                "max_runtime": c_data.get("MR", 0),
                "auto_restart": c_data.get("AR", 0),
            }
            
            # Extract parameters from P field
            parameters = []
            p_data = lab_data.get("P", [])
            for param in p_data:
                # Get the first option as the default value
                options = param.get("O", [])
                default_value = options[0] if options else ""
                
                parameters.append({
                    "key": param.get("K", ""),
                    "value": default_value,
                    "type": param.get("T", 0),
                    "options": options,
                    "included": param.get("I", True),
                    "selected": param.get("IS", False),
                })
            
            # Map status
            status_map = {0: "ACTIVE", 1: "RUNNING", 2: "COMPLETED", 3: "FAILED", 4: "CANCELLED"}
            status = status_map.get(lab_data.get("S", 0), "ACTIVE")
            
            return {
                "labId": lab_id,
                "name": name,
                "scriptId": script_id,
                "scriptName": name,  # Use lab name as script name for now
                "settings": settings,
                "config": config,
                "parameters": parameters,
                "status": status,
                "backtestCount": lab_data.get("CB", 0),
            }
            
        except Exception as e:
            self.logger.error(f"Failed to map lab response: {e}")
            raise LabError(message=f"Failed to map lab response: {e}")
    
    async def change_lab_script(self, lab_id: str, script_id: str) -> LabDetails:
        """
        Change the script associated with a lab
        
        Args:
            lab_id: ID of the lab to modify
            script_id: ID of the new script to use
            
        Returns:
            Updated LabDetails object
            
        Raises:
            LabNotFoundError: If lab is not found
            LabError: If API request fails
        """
        try:
            await self.auth_manager.ensure_authenticated()
            
            self.logger.info(f"Changing script for lab {lab_id} to {script_id}")
            
            session = self.auth_manager.session
            if not session:
                raise LabError("Not authenticated")
            
            response = await self.client.post_json(
                "/LabsAPI.php",
                data={
                    "channel": "CHANGE_LAB_SCRIPT",
                    "userid": session.user_id,
                    "interfacekey": session.interface_key,
                    "labid": lab_id,
                    "scriptid": script_id,
                }
            )
            
            if not safe_get_success_flag(response):
                error_msg = safe_get_field(response, "Error", "Failed to change lab script")
                if "not found" in error_msg.lower():
                    raise LabNotFoundError(lab_id)
                else:
                    raise LabError(message=f"Failed to change lab script: {error_msg}")
            
            updated_data = safe_get_field(response, "Data", {})
            if not updated_data:
                raise LabError(message="No updated lab data returned from API")
            
            updated_lab = LabDetails(**updated_data)
            
            self.logger.info(f"Lab script changed successfully: {updated_lab.name}")
            return updated_lab
            
        except LabNotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to change lab script: {e}")
            if isinstance(e, LabError):
                raise
            else:
                raise LabError(message=f"Failed to change lab script: {e}")
    
    async def start_lab_execution(
        self,
        request: StartLabExecutionRequest,
        ensure_config: bool = True,
        config: Optional[LabConfig] = None
    ) -> Dict[str, Any]:
        """
        Start lab execution with specified parameters using v1 patterns
        
        Based on v1 implementation from pyHaasAPI_v1/api.py (lines 547-585)
        Uses direct POST with form data to match browser/curl behavior
        
        Args:
            request: StartLabExecutionRequest with execution parameters
            ensure_config: Whether to ensure proper config parameters before execution
            config: Optional LabConfig for configuration
            
        Returns:
            Dictionary with execution response
            
        Raises:
            LabExecutionError: If execution fails
            LabError: If API request fails
        """
        try:
            await self.auth_manager.ensure_authenticated()
            
            if ensure_config:
                self.logger.info(f"Ensuring proper config parameters for lab {request.lab_id}")
                await self.ensure_lab_config_parameters(request.lab_id, config)
            
            self.logger.info(f"Starting lab execution: {request.lab_id}")
            
            session = self.auth_manager.session
            if not session:
                raise LabError("Not authenticated")
            
            # Use v1-style form data POST (matches browser/curl behavior)
            form_data = {
                "labid": request.lab_id,
                "startunix": request.start_unix,
                "endunix": request.end_unix,
                "sendemail": str(request.send_email).lower(),
                "interfacekey": session.interface_key,
                "userid": session.user_id
            }
            
            # Use v1-style headers for better compatibility
            headers = {
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7,pl;q=0.6,de;q=0.5,fr;q=0.4',
                'Connection': 'keep-alive',
                'Content-Type': 'application/x-www-form-urlencoded',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
            }
            
            response = await self.client.post_form(
                "/LabsAPI.php",
                params={"channel": "START_LAB_EXECUTION"},
                data=form_data,
                headers=headers
            )
            
            if not safe_get_success_flag(response):
                error_msg = safe_get_field(response, "Error", "Failed to start lab execution")
                raise LabExecutionError(request.lab_id, error_msg)
            
            self.logger.info(f"Lab execution started successfully: {request.lab_id}")
            return response
            
        except LabExecutionError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to start lab execution: {e}")
            if isinstance(e, LabError):
                raise
            else:
                raise LabExecutionError(request.lab_id, f"Failed to start execution: {e}")
    
    async def cancel_lab_execution(self, lab_id: str) -> bool:
        """
        Cancel a running lab execution
        
        Args:
            lab_id: ID of the lab to cancel execution for
            
        Returns:
            True if cancellation was successful
            
        Raises:
            LabError: If API request fails
        """
        try:
            await self.auth_manager.ensure_authenticated()
            
            self.logger.info(f"Cancelling lab execution: {lab_id}")
            
            session = self.auth_manager.session
            if not session:
                raise LabError("Not authenticated")
            
            response = await self.client.post_json(
                "/LabsAPI.php",
                data={
                    "channel": "CANCEL_LAB_EXECUTION",
                    "userid": session.user_id,
                    "interfacekey": session.interface_key,
                    "labid": lab_id
                }
            )
            
            if not safe_get_success_flag(response):
                error_msg = safe_get_field(response, "Error", "Failed to cancel lab execution")
                raise LabError(message=f"Failed to cancel lab execution: {error_msg}")
            
            self.logger.info(f"Lab execution cancelled successfully: {lab_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to cancel lab execution: {e}")
            if isinstance(e, LabError):
                raise
            else:
                raise LabError(message=f"Failed to cancel lab execution: {e}")
    
    async def get_lab_execution_status(self, lab_id: str) -> LabExecutionUpdate:
        """
        Get the current execution status of a lab
        
        Args:
            lab_id: ID of the lab to check
            
        Returns:
            LabExecutionUpdate object with current status
            
        Raises:
            LabError: If API request fails
        """
        try:
            await self.auth_manager.ensure_authenticated()
            
            session = self.auth_manager.session
            if not session:
                raise LabError("Not authenticated")
            
            post_data = {
                'labid': lab_id,
                'interfacekey': session.interface_key,
                'userid': session.user_id
            }
            
            response = await self.client.post_json(
                "/LabsAPI.php",
                params={"channel": "GET_LAB_EXECUTION_UPDATE"},
                data=post_data
            )
            
            if not safe_get_success_flag(response):
                error_msg = safe_get_field(response, "Error", "Failed to get lab execution status")
                raise LabError(message=f"Failed to get lab execution status: {error_msg}")
            
            status_data = safe_get_field(response, "Data", {})
            if not status_data:
                raise LabError(message="No execution status data returned from API")
            
            execution_update = LabExecutionUpdate(**status_data)
            
            return execution_update
            
        except Exception as e:
            self.logger.error(f"Failed to get lab execution status: {e}")
            if isinstance(e, LabError):
                raise
            else:
                raise LabError(message=f"Failed to get lab execution status: {e}")
    
    async def ensure_lab_config_parameters(
        self,
        lab_id: str,
        config: Optional[LabConfig] = None
    ) -> LabDetails:
        """
        Ensure a lab has proper config parameters before backtesting
        
        Args:
            lab_id: ID of the lab to configure
            config: Optional LabConfig object
            
        Returns:
            LabDetails object with updated config parameters
            
        Raises:
            LabConfigurationError: If configuration fails
            LabError: If API request fails
        """
        try:
            await self.auth_manager.ensure_authenticated()
            
            # Use default config if not provided
            if config is None:
                config = LabConfig()  # Use default intelligent mode config
            
            self.logger.info(f"Ensuring config parameters for lab: {lab_id}")
            
            session = self.auth_manager.session
            if not session:
                raise LabError("Not authenticated")
            
            response = await self.client.post_json(
                "/LabsAPI.php",
                data={
                    "channel": "UPDATE_LAB_CONFIG",
                    "userid": session.user_id,
                    "interfacekey": session.interface_key,
                    "labid": lab_id,
                    "maxParallel": config.max_parallel,
                    "maxGenerations": config.max_generations,
                    "maxEpochs": config.max_epochs,
                    "maxRuntime": config.max_runtime,
                    "autoRestart": config.auto_restart,
                }
            )
            
            if not safe_get_success_flag(response):
                error_msg = safe_get_field(response, "Error", "Failed to update lab config")
                raise LabConfigurationError("max_parallel", config.max_parallel, error_msg)
            
            # Get updated lab details
            updated_lab = await self.get_lab_details(lab_id)
            
            self.logger.info(f"Lab config parameters updated successfully: {lab_id}")
            return updated_lab
            
        except LabConfigurationError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to ensure lab config parameters: {e}")
            if isinstance(e, LabError):
                raise
            else:
                raise LabConfigurationError("config", str(config), f"Failed to configure lab: {e}")
    
    async def get_complete_labs(self) -> List[LabRecord]:
        """
        Get only completed labs (labs with backtest results)
        
        Returns:
            List of completed LabRecord objects
            
        Raises:
            LabError: If API request fails
        """
        try:
            all_labs = await self.get_labs()
            complete_labs = [lab for lab in all_labs if lab.status == "COMPLETED"]
            
            self.logger.info(f"Found {len(complete_labs)} completed labs out of {len(all_labs)} total")
            return complete_labs
            
        except Exception as e:
            self.logger.error(f"Failed to get complete labs: {e}")
            if isinstance(e, LabError):
                raise
            else:
                raise LabError(message=f"Failed to get complete labs: {e}")
    
    async def get_labs_by_script(self, script_id: str) -> List[LabRecord]:
        """
        Get labs filtered by script ID
        
        Args:
            script_id: ID of the script to filter by
            
        Returns:
            List of LabRecord objects for the specified script
            
        Raises:
            LabError: If API request fails
        """
        try:
            all_labs = await self.get_labs()
            filtered_labs = [lab for lab in all_labs if lab.script_id == script_id]
            
            self.logger.info(f"Found {len(filtered_labs)} labs for script: {script_id}")
            return filtered_labs
            
        except Exception as e:
            self.logger.error(f"Failed to get labs by script: {e}")
            if isinstance(e, LabError):
                raise
            else:
                raise LabError(message=f"Failed to get labs by script: {e}")
    
    async def get_labs_by_market(self, market_tag: str) -> List[LabRecord]:
        """
        Get labs filtered by market tag
        
        Args:
            market_tag: Market tag to filter by (e.g., "BINANCE_BTC_USDT_")
            
        Returns:
            List of LabRecord objects for the specified market
            
        Raises:
            LabError: If API request fails
        """
        try:
            all_labs = await self.get_labs()
            filtered_labs = [lab for lab in all_labs if lab.market_tag == market_tag]
            
            self.logger.info(f"Found {len(filtered_labs)} labs for market: {market_tag}")
            return filtered_labs
            
        except Exception as e:
            self.logger.error(f"Failed to get labs by market: {e}")
            if isinstance(e, LabError):
                raise
            else:
                raise LabError(message=f"Failed to get labs by market: {e}")
    
    async def validate_lab_configuration(self, lab_id: str) -> bool:
        """
        Validate that a lab has proper configuration for backtesting
        
        Args:
            lab_id: ID of the lab to validate
            
        Returns:
            True if lab configuration is valid
            
        Raises:
            LabError: If validation fails
        """
        try:
            lab_details = await self.get_lab_details(lab_id)
            
            # Check required fields
            if not lab_details.script_id:
                raise LabConfigurationError("script_id", "", "Script ID is required")
            
            if not lab_details.settings.account_id:
                raise LabConfigurationError("account_id", "", "Account ID is required")
            
            if not lab_details.settings.market_tag:
                raise LabConfigurationError("market_tag", "", "Market tag is required")
            
            if lab_details.settings.interval <= 0:
                raise LabConfigurationError("interval", lab_details.settings.interval, "Interval must be positive")
            
            if lab_details.settings.trade_amount <= 0:
                raise LabConfigurationError("trade_amount", lab_details.settings.trade_amount, "Trade amount must be positive")
            
            self.logger.info(f"Lab configuration is valid: {lab_id}")
            return True
            
        except LabConfigurationError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to validate lab configuration: {e}")
            if isinstance(e, LabError):
                raise
            else:
                raise LabError(message=f"Failed to validate lab configuration: {e}")
