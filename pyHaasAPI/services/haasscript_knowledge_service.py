"""
HaasScript Knowledge Base Service

Manages HaasScript command reference, syntax patterns, and examples
for AI-driven script generation.
"""

import json
import asyncio
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime, timedelta

from ..api.script.script_api import ScriptAPI
from ..core.logging import get_logger
from ..exceptions.script import ScriptError


class HaasScriptKnowledgeService:
    """
    Service for managing HaasScript knowledge base including commands,
    syntax patterns, and examples for AI generation.
    """
    
    def __init__(
        self,
        script_api: ScriptAPI,
        cache_dir: Optional[Path] = None
    ):
        """
        Initialize the knowledge service.
        
        Args:
            script_api: ScriptAPI instance for fetching commands
            cache_dir: Directory for caching knowledge data
        """
        self.script_api = script_api
        self.logger = get_logger("haasscript_knowledge")
        
        # Set up cache directory
        if cache_dir is None:
            cache_dir = Path.home() / ".pyhaasapi" / "knowledge_cache"
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.commands_cache_file = self.cache_dir / "commands.json"
        self.examples_cache_file = self.cache_dir / "examples.json"
        self.cache_ttl = timedelta(hours=24)  # Refresh cache daily
        
        self._commands: Optional[List[Dict[str, Any]]] = None
        self._examples: List[Dict[str, str]] = []
    
    async def fetch_and_cache_commands(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Fetch HaasScript commands from API and cache locally.
        
        Args:
            force_refresh: Force refresh even if cache is valid
            
        Returns:
            List of command dictionaries
            
        Raises:
            ScriptError: If command retrieval fails
        """
        # Check cache validity
        if not force_refresh and self._is_cache_valid(self.commands_cache_file):
            self.logger.debug("Loading commands from cache")
            return self._load_from_cache(self.commands_cache_file)
        
        try:
            self.logger.info("Fetching HaasScript commands from API")
            commands = await self.script_api.get_haasscript_commands()
            
            # Cache the results
            self._save_to_cache(self.commands_cache_file, commands)
            self._commands = commands
            
            self.logger.info(f"Cached {len(commands)} HaasScript commands")
            return commands
            
        except Exception as e:
            self.logger.error(f"Failed to fetch commands: {e}")
            # Try to load from cache as fallback
            if self.commands_cache_file.exists():
                self.logger.warning("Using stale cache as fallback")
                return self._load_from_cache(self.commands_cache_file)
            raise ScriptError(f"Failed to fetch HaasScript commands: {e}") from e
    
    def get_command_reference(self, format: str = "markdown") -> str:
        """
        Get formatted command reference for AI prompts.
        
        Args:
            format: Output format ('markdown', 'json', 'text')
            
        Returns:
            Formatted command reference string
        """
        if self._commands is None:
            raise ScriptError("Commands not loaded. Call fetch_and_cache_commands() first.")
        
        if format == "markdown":
            return self._format_commands_markdown()
        elif format == "json":
            return json.dumps(self._commands, indent=2)
        else:  # text
            return self._format_commands_text()
    
    def _format_commands_markdown(self) -> str:
        """Format commands as markdown for AI context."""
        lines = ["# HaasScript Commands Reference\n"]
        
        for cmd in self._commands:
            name = cmd.get('name', cmd.get('Name', 'Unknown'))
            description = cmd.get('description', cmd.get('Description', ''))
            syntax = cmd.get('syntax', cmd.get('Syntax', ''))
            
            lines.append(f"## {name}")
            if description:
                lines.append(f"**Description**: {description}")
            if syntax:
                lines.append(f"**Syntax**: `{syntax}`")
            lines.append("")
        
        return "\n".join(lines)
    
    def _format_commands_text(self) -> str:
        """Format commands as plain text."""
        lines = []
        for cmd in self._commands:
            name = cmd.get('name', cmd.get('Name', 'Unknown'))
            description = cmd.get('description', cmd.get('Description', ''))
            lines.append(f"{name}: {description}")
        return "\n".join(lines)
    
    def add_example(self, name: str, code: str, description: str = ""):
        """
        Add a HaasScript example to the knowledge base.
        
        Args:
            name: Example name
            code: HaasScript source code
            description: Example description
        """
        example = {
            "name": name,
            "code": code,
            "description": description,
            "added_at": datetime.now().isoformat()
        }
        
        self._examples.append(example)
        self._save_to_cache(self.examples_cache_file, self._examples)
        self.logger.debug(f"Added example: {name}")
    
    def get_syntax_examples(self, limit: int = 5) -> List[Dict[str, str]]:
        """
        Get HaasScript syntax examples for AI context.
        
        Args:
            limit: Maximum number of examples to return
            
        Returns:
            List of example dictionaries
        """
        # Load examples from cache if not in memory
        if not self._examples and self.examples_cache_file.exists():
            self._examples = self._load_from_cache(self.examples_cache_file)
        
        return self._examples[:limit]
    
    def get_ai_context(self) -> str:
        """
        Get complete context string for AI prompts.
        
        Returns:
            Formatted context including commands and examples
        """
        context_parts = []
        
        # Add command reference
        if self._commands:
            context_parts.append(self.get_command_reference(format="markdown"))
        
        # Add examples
        examples = self.get_syntax_examples()
        if examples:
            context_parts.append("\n# Example Scripts\n")
            for ex in examples:
                context_parts.append(f"## {ex['name']}")
                if ex.get('description'):
                    context_parts.append(f"{ex['description']}\n")
                context_parts.append(f"```haasscript\n{ex['code']}\n```\n")
        
        return "\n".join(context_parts)
    
    def _is_cache_valid(self, cache_file: Path) -> bool:
        """Check if cache file exists and is not expired."""
        if not cache_file.exists():
            return False
        
        mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
        age = datetime.now() - mtime
        return age < self.cache_ttl
    
    def _save_to_cache(self, cache_file: Path, data: Any):
        """Save data to cache file."""
        try:
            with open(cache_file, 'w') as f:
                json.dump(data, f, indent=2)
            self.logger.debug(f"Saved cache to {cache_file}")
        except Exception as e:
            self.logger.warning(f"Failed to save cache: {e}")
    
    def _load_from_cache(self, cache_file: Path) -> Any:
        """Load data from cache file."""
        try:
            with open(cache_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            self.logger.warning(f"Failed to load cache: {e}")
            return [] if cache_file == self.examples_cache_file else None
