"""
Script Organization and Management System

Provides comprehensive script management including folders, search, tagging, and sharing.
"""

import asyncio
import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from ..utils.logging import get_logger
from ..utils.errors import handle_error, ErrorCategory, ErrorSeverity


class ScriptType(Enum):
    """Script type enumeration"""
    STRATEGY = "strategy"
    INDICATOR = "indicator"
    UTILITY = "utility"
    TEMPLATE = "template"
    EXAMPLE = "example"


class ScriptStatus(Enum):
    """Script status enumeration"""
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"
    SHARED = "shared"
    TEMPLATE = "template"


@dataclass
class ScriptMetadata:
    """Script metadata information"""
    id: str
    name: str
    description: str = ""
    author: str = ""
    version: str = "1.0.0"
    script_type: ScriptType = ScriptType.STRATEGY
    status: ScriptStatus = ScriptStatus.DRAFT
    tags: Set[str] = field(default_factory=set)
    folder_path: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    modified_at: datetime = field(default_factory=datetime.now)
    last_compiled_at: Optional[datetime] = None
    last_tested_at: Optional[datetime] = None
    file_size: int = 0
    line_count: int = 0
    complexity_score: float = 0.0
    dependencies: List[str] = field(default_factory=list)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'author': self.author,
            'version': self.version,
            'script_type': self.script_type.value,
            'status': self.status.value,
            'tags': list(self.tags),
            'folder_path': self.folder_path,
            'created_at': self.created_at.isoformat(),
            'modified_at': self.modified_at.isoformat(),
            'last_compiled_at': self.last_compiled_at.isoformat() if self.last_compiled_at else None,
            'last_tested_at': self.last_tested_at.isoformat() if self.last_tested_at else None,
            'file_size': self.file_size,
            'line_count': self.line_count,
            'complexity_score': self.complexity_score,
            'dependencies': self.dependencies,
            'performance_metrics': self.performance_metrics
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScriptMetadata':
        """Create from dictionary"""
        metadata = cls(
            id=data['id'],
            name=data['name'],
            description=data.get('description', ''),
            author=data.get('author', ''),
            version=data.get('version', '1.0.0'),
            script_type=ScriptType(data.get('script_type', 'strategy')),
            status=ScriptStatus(data.get('status', 'draft')),
            tags=set(data.get('tags', [])),
            folder_path=data.get('folder_path', ''),
            file_size=data.get('file_size', 0),
            line_count=data.get('line_count', 0),
            complexity_score=data.get('complexity_score', 0.0),
            dependencies=data.get('dependencies', []),
            performance_metrics=data.get('performance_metrics', {})
        )
        
        # Parse datetime fields
        if data.get('created_at'):
            metadata.created_at = datetime.fromisoformat(data['created_at'])
        if data.get('modified_at'):
            metadata.modified_at = datetime.fromisoformat(data['modified_at'])
        if data.get('last_compiled_at'):
            metadata.last_compiled_at = datetime.fromisoformat(data['last_compiled_at'])
        if data.get('last_tested_at'):
            metadata.last_tested_at = datetime.fromisoformat(data['last_tested_at'])
        
        return metadata


@dataclass
class ScriptFolder:
    """Script folder information"""
    path: str
    name: str
    description: str = ""
    parent_path: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    script_count: int = 0
    subfolder_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'path': self.path,
            'name': self.name,
            'description': self.description,
            'parent_path': self.parent_path,
            'created_at': self.created_at.isoformat(),
            'script_count': self.script_count,
            'subfolder_count': self.subfolder_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScriptFolder':
        """Create from dictionary"""
        folder = cls(
            path=data['path'],
            name=data['name'],
            description=data.get('description', ''),
            parent_path=data.get('parent_path', ''),
            script_count=data.get('script_count', 0),
            subfolder_count=data.get('subfolder_count', 0)
        )
        
        if data.get('created_at'):
            folder.created_at = datetime.fromisoformat(data['created_at'])
        
        return folder


@dataclass
class SearchFilter:
    """Script search filter"""
    query: str = ""
    script_types: List[ScriptType] = field(default_factory=list)
    statuses: List[ScriptStatus] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    folders: List[str] = field(default_factory=list)
    author: str = ""
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    min_complexity: float = 0.0
    max_complexity: float = 100.0
    has_tests: Optional[bool] = None
    sort_by: str = "modified_at"  # name, created_at, modified_at, complexity_score
    sort_order: str = "desc"  # asc, desc


class ScriptManager:
    """Comprehensive script management system"""
    
    def __init__(self, mcp_client=None, storage_path: str = None):
        self.mcp_client = mcp_client
        self.logger = get_logger(__name__)
        
        # Storage configuration
        self.storage_path = Path(storage_path or "scripts")
        self.metadata_file = self.storage_path / "metadata.json"
        self.folders_file = self.storage_path / "folders.json"
        
        # In-memory caches
        self._scripts_cache: Dict[str, ScriptMetadata] = {}
        self._folders_cache: Dict[str, ScriptFolder] = {}
        self._content_cache: Dict[str, str] = {}
        
        # Search index
        self._search_index: Dict[str, Set[str]] = {}
        
        # Initialize storage
        self._initialize_storage()
    
    def _initialize_storage(self) -> None:
        """Initialize script storage directory and files"""
        try:
            # Create storage directory
            self.storage_path.mkdir(parents=True, exist_ok=True)
            
            # Load existing metadata
            self._load_metadata()
            self._load_folders()
            
            # Build search index
            self._build_search_index()
            
            self.logger.info(f"Script manager initialized with {len(self._scripts_cache)} scripts in {len(self._folders_cache)} folders")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize script storage: {e}")
    
    def _load_metadata(self) -> None:
        """Load script metadata from storage"""
        try:
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r') as f:
                    data = json.load(f)
                    for script_data in data.get('scripts', []):
                        metadata = ScriptMetadata.from_dict(script_data)
                        self._scripts_cache[metadata.id] = metadata
        except Exception as e:
            self.logger.error(f"Failed to load script metadata: {e}")
    
    def _load_folders(self) -> None:
        """Load folder structure from storage"""
        try:
            if self.folders_file.exists():
                with open(self.folders_file, 'r') as f:
                    data = json.load(f)
                    for folder_data in data.get('folders', []):
                        folder = ScriptFolder.from_dict(folder_data)
                        self._folders_cache[folder.path] = folder
        except Exception as e:
            self.logger.error(f"Failed to load folder structure: {e}")
    
    def _save_metadata(self) -> None:
        """Save script metadata to storage"""
        try:
            data = {
                'scripts': [metadata.to_dict() for metadata in self._scripts_cache.values()],
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.metadata_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Failed to save script metadata: {e}")
    
    def _save_folders(self) -> None:
        """Save folder structure to storage"""
        try:
            data = {
                'folders': [folder.to_dict() for folder in self._folders_cache.values()],
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.folders_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Failed to save folder structure: {e}")
    
    def _build_search_index(self) -> None:
        """Build search index for fast text search"""
        self._search_index.clear()
        
        for script_id, metadata in self._scripts_cache.items():
            # Index searchable text
            searchable_text = f"{metadata.name} {metadata.description} {metadata.author} {' '.join(metadata.tags)}"
            words = searchable_text.lower().split()
            
            for word in words:
                if word not in self._search_index:
                    self._search_index[word] = set()
                self._search_index[word].add(script_id)
    
    def _get_script_file_path(self, script_id: str) -> Path:
        """Get file path for script content"""
        return self.storage_path / f"{script_id}.haas"
    
    def _calculate_complexity_score(self, content: str) -> float:
        """Calculate script complexity score"""
        try:
            lines = content.split('\n')
            non_empty_lines = [line for line in lines if line.strip() and not line.strip().startswith('//')]
            
            # Basic complexity metrics
            line_count = len(non_empty_lines)
            function_count = content.lower().count('function ')
            loop_count = content.lower().count('for ') + content.lower().count('while ')
            condition_count = content.lower().count('if ') + content.lower().count('elseif ')
            
            # Simple complexity formula
            complexity = (line_count * 0.1) + (function_count * 2) + (loop_count * 3) + (condition_count * 1.5)
            
            return min(complexity, 100.0)  # Cap at 100
            
        except Exception as e:
            self.logger.error(f"Failed to calculate complexity score: {e}")
            return 0.0
    
    async def create_script(
        self, 
        name: str, 
        content: str = "", 
        folder_path: str = "",
        script_type: ScriptType = ScriptType.STRATEGY,
        description: str = "",
        tags: Set[str] = None
    ) -> str:
        """Create a new script"""
        try:
            # Generate unique ID
            import uuid
            script_id = str(uuid.uuid4())
            
            # Calculate metadata
            line_count = len(content.split('\n'))
            complexity_score = self._calculate_complexity_score(content)
            
            # Create metadata
            metadata = ScriptMetadata(
                id=script_id,
                name=name,
                description=description,
                script_type=script_type,
                folder_path=folder_path,
                tags=tags or set(),
                file_size=len(content.encode('utf-8')),
                line_count=line_count,
                complexity_score=complexity_score
            )
            
            # Save script content
            script_file = self._get_script_file_path(script_id)
            with open(script_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Update caches
            self._scripts_cache[script_id] = metadata
            self._content_cache[script_id] = content
            
            # Update search index
            self._build_search_index()
            
            # Save metadata
            self._save_metadata()
            
            # Update folder counts
            if folder_path:
                await self._update_folder_counts(folder_path)
            
            self.logger.info(f"Created script '{name}' with ID {script_id}")
            return script_id
            
        except Exception as e:
            self.logger.error(f"Failed to create script: {e}")
            raise
    
    async def update_script(
        self, 
        script_id: str, 
        content: str = None,
        name: str = None,
        description: str = None,
        tags: Set[str] = None,
        folder_path: str = None
    ) -> bool:
        """Update an existing script"""
        try:
            if script_id not in self._scripts_cache:
                raise ValueError(f"Script {script_id} not found")
            
            metadata = self._scripts_cache[script_id]
            
            # Update content if provided
            if content is not None:
                script_file = self._get_script_file_path(script_id)
                with open(script_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                # Update content cache
                self._content_cache[script_id] = content
                
                # Update metadata
                metadata.file_size = len(content.encode('utf-8'))
                metadata.line_count = len(content.split('\n'))
                metadata.complexity_score = self._calculate_complexity_score(content)
            
            # Update other fields
            if name is not None:
                metadata.name = name
            if description is not None:
                metadata.description = description
            if tags is not None:
                metadata.tags = tags
            if folder_path is not None:
                old_folder = metadata.folder_path
                metadata.folder_path = folder_path
                
                # Update folder counts
                if old_folder != folder_path:
                    if old_folder:
                        await self._update_folder_counts(old_folder)
                    if folder_path:
                        await self._update_folder_counts(folder_path)
            
            # Update modification time
            metadata.modified_at = datetime.now()
            
            # Update search index
            self._build_search_index()
            
            # Save metadata
            self._save_metadata()
            
            self.logger.info(f"Updated script {script_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update script {script_id}: {e}")
            return False
    
    async def delete_script(self, script_id: str) -> bool:
        """Delete a script"""
        try:
            if script_id not in self._scripts_cache:
                raise ValueError(f"Script {script_id} not found")
            
            metadata = self._scripts_cache[script_id]
            
            # Delete script file
            script_file = self._get_script_file_path(script_id)
            if script_file.exists():
                script_file.unlink()
            
            # Remove from caches
            del self._scripts_cache[script_id]
            if script_id in self._content_cache:
                del self._content_cache[script_id]
            
            # Update search index
            self._build_search_index()
            
            # Save metadata
            self._save_metadata()
            
            # Update folder counts
            if metadata.folder_path:
                await self._update_folder_counts(metadata.folder_path)
            
            self.logger.info(f"Deleted script {script_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete script {script_id}: {e}")
            return False
    
    def get_script_content(self, script_id: str) -> Optional[str]:
        """Get script content"""
        try:
            # Check cache first
            if script_id in self._content_cache:
                return self._content_cache[script_id]
            
            # Load from file
            script_file = self._get_script_file_path(script_id)
            if script_file.exists():
                with open(script_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self._content_cache[script_id] = content
                    return content
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get script content for {script_id}: {e}")
            return None
    
    def get_script_metadata(self, script_id: str) -> Optional[ScriptMetadata]:
        """Get script metadata"""
        return self._scripts_cache.get(script_id)
    
    def list_scripts(self, folder_path: str = None) -> List[ScriptMetadata]:
        """List scripts, optionally filtered by folder"""
        scripts = list(self._scripts_cache.values())
        
        if folder_path is not None:
            scripts = [s for s in scripts if s.folder_path == folder_path]
        
        return sorted(scripts, key=lambda s: s.modified_at, reverse=True)
    
    async def search_scripts(self, search_filter: SearchFilter) -> List[ScriptMetadata]:
        """Search scripts with comprehensive filtering"""
        try:
            results = set()
            
            # Text search
            if search_filter.query:
                query_words = search_filter.query.lower().split()
                for word in query_words:
                    # Find matching words in index
                    matching_scripts = set()
                    for indexed_word, script_ids in self._search_index.items():
                        if word in indexed_word:
                            matching_scripts.update(script_ids)
                    
                    if not results:
                        results = matching_scripts
                    else:
                        results &= matching_scripts  # Intersection
            else:
                results = set(self._scripts_cache.keys())
            
            # Apply filters
            filtered_scripts = []
            for script_id in results:
                metadata = self._scripts_cache[script_id]
                
                # Type filter
                if search_filter.script_types and metadata.script_type not in search_filter.script_types:
                    continue
                
                # Status filter
                if search_filter.statuses and metadata.status not in search_filter.statuses:
                    continue
                
                # Tags filter
                if search_filter.tags and not any(tag in metadata.tags for tag in search_filter.tags):
                    continue
                
                # Folder filter
                if search_filter.folders and metadata.folder_path not in search_filter.folders:
                    continue
                
                # Author filter
                if search_filter.author and search_filter.author.lower() not in metadata.author.lower():
                    continue
                
                # Date filters
                if search_filter.date_from and metadata.modified_at < search_filter.date_from:
                    continue
                if search_filter.date_to and metadata.modified_at > search_filter.date_to:
                    continue
                
                # Complexity filter
                if not (search_filter.min_complexity <= metadata.complexity_score <= search_filter.max_complexity):
                    continue
                
                # Test filter
                if search_filter.has_tests is not None:
                    has_tests = metadata.last_tested_at is not None
                    if search_filter.has_tests != has_tests:
                        continue
                
                filtered_scripts.append(metadata)
            
            # Sort results
            sort_key = lambda s: getattr(s, search_filter.sort_by, s.modified_at)
            reverse = search_filter.sort_order == "desc"
            filtered_scripts.sort(key=sort_key, reverse=reverse)
            
            return filtered_scripts
            
        except Exception as e:
            self.logger.error(f"Failed to search scripts: {e}")
            return []
    
    async def create_folder(self, path: str, name: str, description: str = "") -> bool:
        """Create a new folder"""
        try:
            if path in self._folders_cache:
                raise ValueError(f"Folder {path} already exists")
            
            # Determine parent path
            parent_path = str(Path(path).parent) if Path(path).parent != Path('.') else ""
            
            folder = ScriptFolder(
                path=path,
                name=name,
                description=description,
                parent_path=parent_path
            )
            
            self._folders_cache[path] = folder
            self._save_folders()
            
            # Update parent folder counts
            if parent_path:
                await self._update_folder_counts(parent_path)
            
            self.logger.info(f"Created folder '{name}' at path {path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create folder: {e}")
            return False
    
    async def delete_folder(self, path: str, delete_scripts: bool = False) -> bool:
        """Delete a folder and optionally its scripts"""
        try:
            if path not in self._folders_cache:
                raise ValueError(f"Folder {path} not found")
            
            # Check for scripts in folder
            scripts_in_folder = [s for s in self._scripts_cache.values() if s.folder_path == path]
            
            if scripts_in_folder and not delete_scripts:
                raise ValueError(f"Folder {path} contains {len(scripts_in_folder)} scripts. Use delete_scripts=True to delete them.")
            
            # Delete scripts if requested
            if delete_scripts:
                for script in scripts_in_folder:
                    await self.delete_script(script.id)
            
            # Delete folder
            del self._folders_cache[path]
            self._save_folders()
            
            # Update parent folder counts
            folder = self._folders_cache.get(path)
            if folder and folder.parent_path:
                await self._update_folder_counts(folder.parent_path)
            
            self.logger.info(f"Deleted folder {path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete folder {path}: {e}")
            return False
    
    def list_folders(self, parent_path: str = "") -> List[ScriptFolder]:
        """List folders under a parent path"""
        folders = [f for f in self._folders_cache.values() if f.parent_path == parent_path]
        return sorted(folders, key=lambda f: f.name)
    
    def get_folder_tree(self) -> Dict[str, Any]:
        """Get complete folder tree structure"""
        tree = {}
        
        def add_to_tree(folder: ScriptFolder, tree_node: Dict[str, Any]):
            parts = folder.path.split('/')
            current = tree_node
            
            for part in parts:
                if part not in current:
                    current[part] = {'folders': {}, 'scripts': []}
                current = current[part]['folders']
        
        # Build tree structure
        for folder in self._folders_cache.values():
            add_to_tree(folder, tree)
        
        # Add scripts to tree
        for script in self._scripts_cache.values():
            if script.folder_path:
                parts = script.folder_path.split('/')
                current = tree
                for part in parts:
                    if part in current:
                        current = current[part]['folders']
                if 'scripts' in current:
                    current['scripts'].append(script.to_dict())
        
        return tree
    
    async def _update_folder_counts(self, folder_path: str) -> None:
        """Update script and subfolder counts for a folder"""
        try:
            if folder_path not in self._folders_cache:
                return
            
            folder = self._folders_cache[folder_path]
            
            # Count scripts
            folder.script_count = len([s for s in self._scripts_cache.values() if s.folder_path == folder_path])
            
            # Count subfolders
            folder.subfolder_count = len([f for f in self._folders_cache.values() if f.parent_path == folder_path])
            
            self._save_folders()
            
        except Exception as e:
            self.logger.error(f"Failed to update folder counts for {folder_path}: {e}")
    
    def get_tags(self) -> List[Tuple[str, int]]:
        """Get all tags with usage counts"""
        tag_counts = {}
        
        for script in self._scripts_cache.values():
            for tag in script.tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        return sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get script management statistics"""
        scripts = list(self._scripts_cache.values())
        
        return {
            'total_scripts': len(scripts),
            'total_folders': len(self._folders_cache),
            'scripts_by_type': {
                script_type.value: len([s for s in scripts if s.script_type == script_type])
                for script_type in ScriptType
            },
            'scripts_by_status': {
                status.value: len([s for s in scripts if s.status == status])
                for status in ScriptStatus
            },
            'total_lines': sum(s.line_count for s in scripts),
            'average_complexity': sum(s.complexity_score for s in scripts) / len(scripts) if scripts else 0,
            'most_used_tags': self.get_tags()[:10],
            'recent_activity': len([s for s in scripts if (datetime.now() - s.modified_at).days <= 7])
        }
    
    async def export_script(self, script_id: str, export_path: str) -> bool:
        """Export script to external file"""
        try:
            metadata = self.get_script_metadata(script_id)
            content = self.get_script_content(script_id)
            
            if not metadata or not content:
                return False
            
            export_data = {
                'metadata': metadata.to_dict(),
                'content': content,
                'exported_at': datetime.now().isoformat(),
                'exported_by': 'MCP TUI Client'
            }
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2)
            
            self.logger.info(f"Exported script {script_id} to {export_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export script {script_id}: {e}")
            return False
    
    async def import_script(self, import_path: str) -> Optional[str]:
        """Import script from external file"""
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            metadata_dict = import_data['metadata']
            content = import_data['content']
            
            # Create new script (generate new ID)
            script_id = await self.create_script(
                name=metadata_dict['name'],
                content=content,
                folder_path=metadata_dict.get('folder_path', ''),
                script_type=ScriptType(metadata_dict.get('script_type', 'strategy')),
                description=metadata_dict.get('description', ''),
                tags=set(metadata_dict.get('tags', []))
            )
            
            self.logger.info(f"Imported script from {import_path} with new ID {script_id}")
            return script_id
            
        except Exception as e:
            self.logger.error(f"Failed to import script from {import_path}: {e}")
            return None
    
    async def cleanup(self) -> None:
        """Cleanup manager resources"""
        try:
            # Save any pending changes
            self._save_metadata()
            self._save_folders()
            
            # Clear caches
            self._scripts_cache.clear()
            self._folders_cache.clear()
            self._content_cache.clear()
            self._search_index.clear()
            
            self.logger.info("Script manager cleaned up")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")