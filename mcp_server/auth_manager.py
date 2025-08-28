#!/usr/bin/env python3
"""
Authentication Manager for HaasOnline MCP Server
Handles multiple credential sets and automatic authentication cycling
"""

import os
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
from pathlib import Path

try:
    from pyHaasAPI import api
    PYHAAS_AVAILABLE = True
except ImportError:
    PYHAAS_AVAILABLE = False

logger = logging.getLogger("haas-auth-manager")

@dataclass
class CredentialSet:
    """Represents a set of API credentials"""
    name: str
    email: str
    password: str
    host: str = None
    port: int = None
    description: str = ""
    last_successful: Optional[datetime] = None
    success_count: int = 0
    failure_count: int = 0

@dataclass
class AuthResult:
    """Result of authentication attempt"""
    success: bool
    executor: Optional[object] = None
    credential_set: Optional[CredentialSet] = None
    error_message: str = ""
    server_info: Dict = None

class AuthenticationManager:
    """Manages multiple credential sets and automatic authentication cycling"""
    
    def __init__(self, cache_file: str = "mcp_server/.auth_cache.json"):
        self.credential_sets: List[CredentialSet] = []
        self.current_session: Optional[AuthResult] = None
        self.cache_file = Path(cache_file)
        self.session_timeout = timedelta(hours=24)  # Session validity period
        
        # Load credentials from environment
        self._load_credentials_from_env()
        
        # Load auth cache
        self._load_auth_cache()
    
    def _load_credentials_from_env(self):
        """Load credential sets from environment variables"""
        
        # Get server connection details
        api_host = os.getenv("API_HOST", "localhost")
        api_port = int(os.getenv("API_PORT", 8090))
        
        credential_configs = [
            {
                "name": "primary",
                "email_key": "API_EMAIL",
                "password_key": "API_PASSWORD",
                "description": "Primary API credentials"
            },
            {
                "name": "local",
                "email_key": "API_EMAIL_LOCAL", 
                "password_key": "API_PASSWORD_LOCAL",
                "description": "Local server credentials"
            },
            {
                "name": "backup",
                "email_key": "API_EMAIL_BACKUP",
                "password_key": "API_PASSWORD_BACKUP", 
                "description": "Backup credentials"
            },
            {
                "name": "dev",
                "email_key": "API_EMAIL_DEV",
                "password_key": "API_PASSWORD_DEV",
                "description": "Development environment credentials"
            }
        ]
        
        for config in credential_configs:
            email = os.getenv(config["email_key"])
            password = os.getenv(config["password_key"])
            
            if email and password:
                cred_set = CredentialSet(
                    name=config["name"],
                    email=email,
                    password=password,
                    host=api_host,
                    port=api_port,
                    description=config["description"]
                )
                self.credential_sets.append(cred_set)
                logger.info(f"Loaded credential set: {config['name']} ({email})")
        
        if not self.credential_sets:
            logger.warning("No credential sets found in environment variables")
        else:
            logger.info(f"Loaded {len(self.credential_sets)} credential sets")
    
    def _load_auth_cache(self):
        """Load authentication cache from disk"""
        if not self.cache_file.exists():
            return
        
        try:
            with open(self.cache_file, 'r') as f:
                cache_data = json.load(f)
            
            # Update success/failure counts and last successful times
            for cred_set in self.credential_sets:
                cache_entry = cache_data.get(cred_set.name, {})
                
                if 'last_successful' in cache_entry:
                    cred_set.last_successful = datetime.fromisoformat(cache_entry['last_successful'])
                
                cred_set.success_count = cache_entry.get('success_count', 0)
                cred_set.failure_count = cache_entry.get('failure_count', 0)
            
            logger.info("Loaded authentication cache")
            
        except Exception as e:
            logger.warning(f"Failed to load auth cache: {e}")
    
    def _save_auth_cache(self):
        """Save authentication cache to disk"""
        try:
            # Ensure directory exists
            self.cache_file.parent.mkdir(exist_ok=True)
            
            cache_data = {}
            for cred_set in self.credential_sets:
                cache_data[cred_set.name] = {
                    'success_count': cred_set.success_count,
                    'failure_count': cred_set.failure_count,
                    'last_successful': cred_set.last_successful.isoformat() if cred_set.last_successful else None
                }
            
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
            
            logger.debug("Saved authentication cache")
            
        except Exception as e:
            logger.warning(f"Failed to save auth cache: {e}")
    
    def _get_credential_priority_order(self) -> List[CredentialSet]:
        """Get credential sets ordered by priority (most likely to succeed first)"""
        
        def priority_score(cred_set: CredentialSet) -> Tuple[int, datetime]:
            # Higher score = higher priority
            score = 0
            
            # Recent success bonus
            if cred_set.last_successful:
                hours_since = (datetime.now() - cred_set.last_successful).total_seconds() / 3600
                if hours_since < 1:
                    score += 1000
                elif hours_since < 24:
                    score += 500
                elif hours_since < 168:  # 1 week
                    score += 100
            
            # Success rate bonus
            total_attempts = cred_set.success_count + cred_set.failure_count
            if total_attempts > 0:
                success_rate = cred_set.success_count / total_attempts
                score += int(success_rate * 100)
            
            # Prefer certain credential types based on naming
            if 'local' in cred_set.name.lower():
                score += 50  # Local credentials often work in dev environments
            elif 'primary' in cred_set.name.lower():
                score += 25  # Primary credentials are usually stable
            
            last_success_time = cred_set.last_successful or datetime.min
            
            return (score, last_success_time)
        
        # Sort by priority score (descending) then by last successful time (descending)
        return sorted(self.credential_sets, key=priority_score, reverse=True)
    
    def authenticate(self, force_refresh: bool = False) -> AuthResult:
        """Attempt authentication with available credential sets"""
        
        if not PYHAAS_AVAILABLE:
            return AuthResult(
                success=False,
                error_message="pyHaasAPI not available"
            )
        
        # Check if we have a valid current session
        if not force_refresh and self.current_session and self.current_session.success:
            if (self.current_session.credential_set.last_successful and 
                datetime.now() - self.current_session.credential_set.last_successful < self.session_timeout):
                
                logger.info(f"Using cached session with {self.current_session.credential_set.name} credentials")
                return self.current_session
        
        if not self.credential_sets:
            return AuthResult(
                success=False,
                error_message="No credential sets available"
            )
        
        logger.info("Attempting authentication with available credential sets...")
        
        # Try each credential set in priority order
        ordered_creds = self._get_credential_priority_order()
        
        for i, cred_set in enumerate(ordered_creds, 1):
            logger.info(f"Attempt {i}/{len(ordered_creds)}: Trying {cred_set.name} credentials ({cred_set.email})")
            
            try:
                # Create executor with this credential set using the correct pyHaasAPI pattern
                executor = api.RequestsExecutor(
                    host=cred_set.host,
                    port=cred_set.port,
                    state=api.Guest()
                ).authenticate(
                    email=cred_set.email,
                    password=cred_set.password
                )
                
                # Test the connection with a simple API call
                test_result = api.get_all_labs(executor)
                
                # get_all_labs returns a list of LabRecord objects, not a dict
                # If we get here without exception and have a list (even empty), auth succeeded
                if test_result is not None and isinstance(test_result, list):
                    # Authentication successful
                    cred_set.last_successful = datetime.now()
                    cred_set.success_count += 1
                    
                    # Get server info
                    server_info = {
                        'host': cred_set.host,
                        'port': cred_set.port,
                        'user': cred_set.email,
                        'credential_set': cred_set.name,
                        'labs_count': len(test_result)
                    }
                    
                    # Try to get more server details from the authenticated state
                    try:
                        if hasattr(executor.state, 'user_id'):
                            server_info['user_id'] = executor.state.user_id
                        if hasattr(executor.state, 'interface_key'):
                            server_info['interface_key'] = getattr(executor.state, 'interface_key')[:8] + "..." if getattr(executor.state, 'interface_key') else None
                    except Exception:
                        pass
                    
                    auth_result = AuthResult(
                        success=True,
                        executor=executor,
                        credential_set=cred_set,
                        server_info=server_info
                    )
                    
                    self.current_session = auth_result
                    self._save_auth_cache()
                    
                    logger.info(f"✅ Authentication successful with {cred_set.name} credentials")
                    logger.info(f"Connected to: {cred_set.host}:{cred_set.port}")
                    
                    return auth_result
                    
                else:
                    error_msg = f"Unexpected response type: {type(test_result)}"
                    logger.warning(f"❌ Authentication failed with {cred_set.name}: {error_msg}")
                    cred_set.failure_count += 1
                    
            except Exception as e:
                logger.warning(f"❌ Exception with {cred_set.name} credentials: {e}")
                cred_set.failure_count += 1
        
        # All credential sets failed
        self._save_auth_cache()
        
        error_msg = f"Authentication failed with all {len(self.credential_sets)} credential sets"
        logger.error(error_msg)
        
        return AuthResult(
            success=False,
            error_message=error_msg
        )
    
    def get_current_session(self) -> Optional[AuthResult]:
        """Get the current authenticated session"""
        return self.current_session
    
    def is_authenticated(self) -> bool:
        """Check if currently authenticated"""
        return (self.current_session is not None and 
                self.current_session.success and 
                self.current_session.executor is not None)
    
    def get_executor(self) -> Optional[object]:
        """Get the current authenticated executor"""
        if self.is_authenticated():
            return self.current_session.executor
        return None
    
    def refresh_authentication(self) -> AuthResult:
        """Force refresh of authentication"""
        logger.info("Forcing authentication refresh...")
        return self.authenticate(force_refresh=True)
    
    def get_authentication_status(self) -> Dict:
        """Get detailed authentication status"""
        status = {
            'authenticated': self.is_authenticated(),
            'credential_sets_available': len(self.credential_sets),
            'current_session': None,
            'credential_sets': []
        }
        
        if self.current_session:
            status['current_session'] = {
                'success': self.current_session.success,
                'credential_set': self.current_session.credential_set.name if self.current_session.credential_set else None,
                'server_info': self.current_session.server_info,
                'error': self.current_session.error_message if not self.current_session.success else None
            }
        
        # Add credential set statistics
        for cred_set in self.credential_sets:
            total_attempts = cred_set.success_count + cred_set.failure_count
            success_rate = (cred_set.success_count / total_attempts * 100) if total_attempts > 0 else 0
            
            status['credential_sets'].append({
                'name': cred_set.name,
                'email': cred_set.email,
                'description': cred_set.description,
                'success_count': cred_set.success_count,
                'failure_count': cred_set.failure_count,
                'success_rate': f"{success_rate:.1f}%",
                'last_successful': cred_set.last_successful.isoformat() if cred_set.last_successful else None
            })
        
        return status
    
    def add_credential_set(self, name: str, email: str, password: str, 
                          host: str = None, port: int = None, description: str = "") -> bool:
        """Add a new credential set"""
        
        # Check if credential set already exists
        if any(cs.name == name for cs in self.credential_sets):
            logger.warning(f"Credential set '{name}' already exists")
            return False
        
        # Use default host/port if not provided
        if not host:
            host = os.getenv("API_HOST", "localhost")
        if not port:
            port = int(os.getenv("API_PORT", 8090))
        
        cred_set = CredentialSet(
            name=name,
            email=email,
            password=password,
            host=host,
            port=port,
            description=description
        )
        
        self.credential_sets.append(cred_set)
        logger.info(f"Added credential set: {name} ({email})")
        
        return True
    
    def remove_credential_set(self, name: str) -> bool:
        """Remove a credential set"""
        
        for i, cred_set in enumerate(self.credential_sets):
            if cred_set.name == name:
                # If this is the current session, invalidate it
                if (self.current_session and 
                    self.current_session.credential_set and 
                    self.current_session.credential_set.name == name):
                    self.current_session = None
                
                del self.credential_sets[i]
                logger.info(f"Removed credential set: {name}")
                return True
        
        logger.warning(f"Credential set '{name}' not found")
        return False

# Global authentication manager instance
auth_manager = AuthenticationManager()

def get_auth_manager() -> AuthenticationManager:
    """Get the global authentication manager instance"""
    return auth_manager

def get_authenticated_executor():
    """Get an authenticated executor, attempting authentication if needed"""
    result = auth_manager.authenticate()
    
    if result.success:
        return result.executor
    else:
        logger.error(f"Failed to get authenticated executor: {result.error_message}")
        return None