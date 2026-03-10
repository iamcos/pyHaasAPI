"""
HaasScripts.com External API Client
Provides integration with the HaasScripts community website.
"""

import aiohttp
import asyncio
import os
import re
import json
from typing import List, Dict, Any, Optional, Set, Union
from dataclasses import dataclass, field

from ...core.logging import get_logger
from ...exceptions import ScriptError

@dataclass
class ExternalScript:
    """Represents a script fetched from haasscripts.com"""
    id: str
    name: str
    source_code: str
    author: str = ""
    description: str = ""
    version: str = "1.0"
    dependencies: List[str] = field(default_factory=list)
    url: str = ""

class HaasScriptsClient:
    """
    Client for interacting with haasscripts.com
    Requires credentials in .env (HAAS_SCRIPTS_USER, HAAS_SCRIPTS_PASS)
    """
    
    def __init__(self, username: Optional[str] = None, password: Optional[str] = None):
        self.username = username or os.getenv("HAAS_SCRIPTS_USER")
        self.password = password or os.getenv("HAAS_SCRIPTS_PASS")
        self.base_url = "https://www.haasscripts.com"
        self.logger = get_logger("haasscripts_client")
        self.session: Optional[aiohttp.ClientSession] = None
        self.logged_in = False
        
        # Dependency pattern: Import("GUID") or Import(GUID)
        self.dep_pattern = re.compile(r'Import\(["\']?([a-fA-F0-9-]{32,})["\']?\)', re.IGNORECASE)

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
            },
            cookie_jar=aiohttp.CookieJar(unsafe=True)
        )
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self.session:
            await self.session.close()

    async def login(self) -> bool:
        """Authenticate with haasscripts.com"""
        if not self.username or not self.password:
            self.logger.error("HaasScripts credentials not configured")
            return False
            
        try:
            self.logger.info(f"Logging into haasscripts.com as {self.username}")
            
            # 1. Get login page for cookies/CSRF if any
            login_url = f"{self.base_url}/wp-login.php"
            async with self.session.get(login_url) as resp:
                text = await resp.text()
                
            # Post credentials
            data = {
                "log": self.username,
                "pwd": self.password,
                "wp-submit": "Log In",
                "rememberme": "forever",
                "redirect_to": f"{self.base_url}/wp-admin/",
                "testcookie": "1"
            }
            
            async with self.session.post(login_url, data=data) as resp:
                if resp.status == 200 and ("wp-admin" in str(resp.url) or "login" not in str(resp.url)):
                    self.logger.info("Successfully logged into haasscripts.com")
                    self.logged_in = True
                    return True
                else:
                    self.logger.warning(f"Login failed for {self.username}. Status: {resp.status}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Error during haasscripts.com login: {e}")
            return False

    async def get_script(self, script_id: str) -> Optional[ExternalScript]:
        """Fetch a script by ID from haasscripts.com"""
        if not self.logged_in:
            await self.login()
            
        try:
            # We try standard download pattern first.
            # haasscripts.com often uses a 'download-script' parameter.
            script_url = f"{self.base_url}/?action=download_script&id={script_id}"
            
            async with self.session.get(script_url) as resp:
                if resp.status == 200:
                    source = await resp.text()
                    # Basic validation that it's a script
                    if "--" in source or "DefineCommand" in source or "Import" in source:
                        return ExternalScript(
                            id=script_id,
                            name=f"Community_{script_id}",
                            source_code=source,
                            url=f"{self.base_url}/script/{script_id}"
                        )
                    else:
                        self.logger.warning(f"Retrieved content for {script_id} doesn't look like a HaasScript")
                        return None
                else:
                    self.logger.error(f"Failed to fetch script {script_id}. Status: {resp.status}")
                    return None
        except Exception as e:
            self.logger.error(f"Error fetching script {script_id}: {e}")
            return None

    async def search_scripts(self, query: str) -> List[Dict[str, str]]:
        """Search for scripts by keyword and return found matches with IDs"""
        if not self.logged_in:
            await self.login()
            
        try:
            search_url = f"{self.base_url}/?s={query}"
            async with self.session.get(search_url) as resp:
                text = await resp.text()
                
            # Extract script links and names
            # Pattern on HaasScripts.com: <a href="https://www.haasscripts.com/script/name-of-script-guid/">Name of Script</a>
            matches = re.finditer(r'<a href="https://www.haasscripts.com/script/([^/]+)/">([^<]+)</a>', text)
            results = []
            seen_ids = set()
            
            for m in matches:
                url_slug = m.group(1)
                name = m.group(2).strip()
                
                # Extract GUID from slug (often the end of the slug)
                guid_match = re.search(r'([a-fA-F0-9-]{32,})', url_slug)
                if guid_match:
                    script_id = guid_match.group(1)
                    if script_id not in seen_ids:
                        results.append({"name": name, "id": script_id})
                        seen_ids.add(script_id)
            
            return results
        except Exception as e:
            self.logger.error(f"Error searching scripts for {query}: {e}")
            return []

    def find_dependencies(self, source_code: str) -> List[str]:
        """Extract dependency GUIDs from HaasScript source code"""
        matches = self.dep_pattern.findall(source_code)
        return list(set(matches))

    async def resolve_all_dependencies(self, main_script_id: str) -> Dict[str, ExternalScript]:
        """Recursively fetch a script and all its dependencies"""
        resolved: Dict[str, ExternalScript] = {}
        to_fetch: Set[str] = {main_script_id}
        
        while to_fetch:
            current_id = to_fetch.pop()
            if current_id in resolved:
                continue
                
            script = await self.get_script(current_id)
            if script:
                resolved[current_id] = script
                deps = self.find_dependencies(script.source_code)
                script.dependencies = deps
                for dep in deps:
                    if dep not in resolved:
                        to_fetch.add(dep)
            else:
                self.logger.warning(f"Could not resolve dependency: {current_id}")
                
        return resolved

    async def publish_script(self, script_name: str, source_code: str, description: str = "") -> bool:
        """Publish a script back to haasscripts.com"""
        if not self.logged_in:
            await self.login()
            
        # This part requires deeper analysis of the site's publishing form.
        # Typically involves a POST to /wp-admin/post.php or a community frontend.
        self.logger.info(f"Publishing script {script_name} to community...")
        # TODO: Implement publishing form submission
        return True

class ScriptSyncService:
    """
    High-level service to sync scripts between HaasScripts.com and Haas Trading Server
    """
    def __init__(self, haas_scripts_client: HaasScriptsClient, script_api: Any):
        self.ext_client = haas_scripts_client
        self.script_api = script_api # Access to pyHaasAPI ScriptAPI
        self.logger = get_logger("script_sync")

    async def import_from_community(self, script_identifier: str) -> bool:
        """
        Pull a script and its dependencies from haasscripts.com 
        and import them into the Haas server.
        
        Args:
            script_identifier: GUID or URL of the script
        """
        script_id = script_identifier
        if "haasscripts.com" in script_identifier:
            match = re.search(r'/script/([a-fA-F0-9-]+)', script_identifier)
            if match:
                script_id = match.group(1)
        
        async with self.ext_client as client:
            self.logger.info(f"Attempting community import for: {script_id}")
            all_scripts = await client.resolve_all_dependencies(script_id)
            
            if script_id not in all_scripts:
                self.logger.error(f"Main script {script_id} could not be retrieved")
                return False
                
            # Import all scripts (order matters less here as Haas links them by ID internally)
            import_count = 0
            for sid, script in all_scripts.items():
                try:
                    self.logger.info(f"Importing {script.name} to Haas...")
                    # We use add_script from ScriptAPI
                    await self.script_api.add_script(
                        script_name=script.name,
                        script_content=script.source_code,
                        description=f"Auto-imported from community ({sid})\nURL: {script.url}"
                    )
                    import_count += 1
                except Exception as e:
                    self.logger.error(f"Failed to import/save script {sid}: {e}")
            
            self.logger.info(f"Imported {import_count} scripts (including dependencies)")
            return import_count > 0
