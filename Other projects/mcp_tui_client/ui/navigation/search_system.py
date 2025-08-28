"""
Global Search System

Comprehensive search functionality across all application data.
"""

from typing import Any, Dict, List, Optional, Callable, Union, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import re
import asyncio
from abc import ABC, abstractmethod

from textual.widget import Widget
from textual.widgets import Input, Button, Label, ListView, ListItem, Static
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive
from textual.app import ComposeResult
from textual.binding import Binding


class SearchResultType(Enum):
    """Types of search results"""
    BOT = "bot"
    LAB = "lab"
    SCRIPT = "script"
    WORKFLOW = "workflow"
    MARKET = "market"
    ACCOUNT = "account"
    LOG = "log"
    SETTING = "setting"


@dataclass
class SearchResult:
    """Search result item"""
    id: str
    title: str
    description: str
    result_type: SearchResultType
    score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    action: Optional[Callable] = None
    icon: Optional[str] = None
    
    def __post_init__(self):
        if not self.icon:
            self.icon = self._get_default_icon()
    
    def _get_default_icon(self) -> str:
        """Get default icon for result type"""
        icons = {
            SearchResultType.BOT: "🤖",
            SearchResultType.LAB: "🧪",
            SearchResultType.SCRIPT: "📝",
            SearchResultType.WORKFLOW: "🔄",
            SearchResultType.MARKET: "📈",
            SearchResultType.ACCOUNT: "👤",
            SearchResultType.LOG: "📋",
            SearchResultType.SETTING: "⚙",
        }
        return icons.get(self.result_type, "📄")


class SearchProvider(ABC):
    """Abstract base class for search providers"""
    
    def __init__(self, name: str, result_type: SearchResultType):
        self.name = name
        self.result_type = result_type
        self.enabled = True
    
    @abstractmethod
    async def search(self, query: str, limit: int = 50) -> List[SearchResult]:
        """Perform search and return results"""
        pass
    
    @abstractmethod
    async def get_suggestions(self, partial_query: str) -> List[str]:
        """Get search suggestions for partial query"""
        pass


class SearchIndex:
    """Search index for fast text searching"""
    
    def __init__(self):
        self.documents: Dict[str, Dict[str, Any]] = {}
        self.word_index: Dict[str, Set[str]] = {}
        self.last_updated = datetime.now()
    
    def add_document(self, doc_id: str, title: str, content: str, metadata: Dict[str, Any] = None) -> None:
        """Add document to search index"""
        doc = {
            "id": doc_id,
            "title": title,
            "content": content,
            "metadata": metadata or {},
            "indexed_at": datetime.now()
        }
        
        self.documents[doc_id] = doc
        self._index_document(doc_id, title + " " + content)
        self.last_updated = datetime.now()
    
    def remove_document(self, doc_id: str) -> None:
        """Remove document from index"""
        if doc_id in self.documents:
            self._remove_from_word_index(doc_id)
            del self.documents[doc_id]
            self.last_updated = datetime.now()
    
    def search(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Search documents and return ranked results"""
        if not query.strip():
            return []
        
        # Tokenize query
        query_words = self._tokenize(query.lower())
        if not query_words:
            return []
        
        # Find matching documents
        matching_docs = set()
        for word in query_words:
            if word in self.word_index:
                if not matching_docs:
                    matching_docs = self.word_index[word].copy()
                else:
                    matching_docs &= self.word_index[word]
        
        # Score and rank results
        results = []
        for doc_id in matching_docs:
            if doc_id in self.documents:
                doc = self.documents[doc_id]
                score = self._calculate_score(doc, query_words)
                results.append({
                    "document": doc,
                    "score": score
                })
        
        # Sort by score and limit results
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]
    
    def get_suggestions(self, partial_query: str, limit: int = 10) -> List[str]:
        """Get search suggestions"""
        if not partial_query.strip():
            return []
        
        partial_words = self._tokenize(partial_query.lower())
        if not partial_words:
            return []
        
        last_word = partial_words[-1]
        suggestions = set()
        
        # Find words that start with the partial word
        for word in self.word_index:
            if word.startswith(last_word) and len(word) > len(last_word):
                # Reconstruct suggestion
                suggestion_words = partial_words[:-1] + [word]
                suggestion = " ".join(suggestion_words)
                suggestions.add(suggestion)
                
                if len(suggestions) >= limit:
                    break
        
        return sorted(list(suggestions))
    
    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text into words"""
        # Simple tokenization - can be enhanced
        words = re.findall(r'\b\w+\b', text.lower())
        return [word for word in words if len(word) > 2]  # Filter short words
    
    def _index_document(self, doc_id: str, text: str) -> None:
        """Index document text"""
        words = self._tokenize(text)
        for word in words:
            if word not in self.word_index:
                self.word_index[word] = set()
            self.word_index[word].add(doc_id)
    
    def _remove_from_word_index(self, doc_id: str) -> None:
        """Remove document from word index"""
        for word_set in self.word_index.values():
            word_set.discard(doc_id)
    
    def _calculate_score(self, doc: Dict[str, Any], query_words: List[str]) -> float:
        """Calculate relevance score for document"""
        title = doc["title"].lower()
        content = doc["content"].lower()
        
        score = 0.0
        
        # Title matches get higher score
        for word in query_words:
            if word in title:
                score += 10.0
            if word in content:
                score += 1.0
        
        # Boost score for exact phrase matches
        query_phrase = " ".join(query_words)
        if query_phrase in title:
            score += 20.0
        elif query_phrase in content:
            score += 5.0
        
        return score


class BotSearchProvider(SearchProvider):
    """Search provider for trading bots"""
    
    def __init__(self, mcp_client=None):
        super().__init__("Bots", SearchResultType.BOT)
        self.mcp_client = mcp_client
        self.index = SearchIndex()
    
    async def search(self, query: str, limit: int = 50) -> List[SearchResult]:
        """Search bots"""
        # Update index if needed
        await self._update_index()
        
        # Search index
        index_results = self.index.search(query, limit)
        
        # Convert to SearchResult objects
        results = []
        for item in index_results:
            doc = item["document"]
            result = SearchResult(
                id=doc["id"],
                title=doc["title"],
                description=doc["content"][:100] + "..." if len(doc["content"]) > 100 else doc["content"],
                result_type=self.result_type,
                score=item["score"],
                metadata=doc["metadata"],
                action=lambda bot_id=doc["id"]: self._open_bot(bot_id)
            )
            results.append(result)
        
        return results
    
    async def get_suggestions(self, partial_query: str) -> List[str]:
        """Get bot search suggestions"""
        await self._update_index()
        return self.index.get_suggestions(partial_query)
    
    async def _update_index(self) -> None:
        """Update bot search index"""
        if not self.mcp_client:
            return
        
        try:
            # Get bots from MCP server
            bots = await self.mcp_client.call_tool("get_bots", {})
            
            # Clear and rebuild index
            self.index = SearchIndex()
            
            for bot in bots.get("bots", []):
                content = f"{bot.get('name', '')} {bot.get('description', '')} {bot.get('status', '')}"
                self.index.add_document(
                    doc_id=bot.get("id", ""),
                    title=bot.get("name", "Unnamed Bot"),
                    content=content,
                    metadata=bot
                )
        except Exception as e:
            # Handle error silently for now
            pass
    
    async def _open_bot(self, bot_id: str) -> None:
        """Open bot details"""
        # Navigate to bot management view and select bot
        if hasattr(self.app, 'action_show_bots'):
            await self.app.action_show_bots()
            # TODO: Select specific bot


class LabSearchProvider(SearchProvider):
    """Search provider for labs"""
    
    def __init__(self, mcp_client=None):
        super().__init__("Labs", SearchResultType.LAB)
        self.mcp_client = mcp_client
        self.index = SearchIndex()
    
    async def search(self, query: str, limit: int = 50) -> List[SearchResult]:
        """Search labs"""
        await self._update_index()
        
        index_results = self.index.search(query, limit)
        
        results = []
        for item in index_results:
            doc = item["document"]
            result = SearchResult(
                id=doc["id"],
                title=doc["title"],
                description=doc["content"][:100] + "..." if len(doc["content"]) > 100 else doc["content"],
                result_type=self.result_type,
                score=item["score"],
                metadata=doc["metadata"],
                action=lambda lab_id=doc["id"]: self._open_lab(lab_id)
            )
            results.append(result)
        
        return results
    
    async def get_suggestions(self, partial_query: str) -> List[str]:
        """Get lab search suggestions"""
        await self._update_index()
        return self.index.get_suggestions(partial_query)
    
    async def _update_index(self) -> None:
        """Update lab search index"""
        if not self.mcp_client:
            return
        
        try:
            labs = await self.mcp_client.call_tool("get_labs", {})
            
            self.index = SearchIndex()
            
            for lab in labs.get("labs", []):
                content = f"{lab.get('name', '')} {lab.get('description', '')} {lab.get('status', '')}"
                self.index.add_document(
                    doc_id=lab.get("id", ""),
                    title=lab.get("name", "Unnamed Lab"),
                    content=content,
                    metadata=lab
                )
        except Exception:
            pass
    
    async def _open_lab(self, lab_id: str) -> None:
        """Open lab details"""
        if hasattr(self.app, 'action_show_labs'):
            await self.app.action_show_labs()


class GlobalSearch(Container):
    """Global search interface"""
    
    DEFAULT_CSS = """
    GlobalSearch {
        height: 1fr;
        width: 1fr;
        border: solid $primary;
        padding: 1;
    }
    
    GlobalSearch .search-header {
        dock: top;
        height: 3;
        background: $surface;
        padding: 1;
    }
    
    GlobalSearch .search-input {
        width: 1fr;
        margin: 0 1 0 0;
    }
    
    GlobalSearch .search-button {
        width: auto;
    }
    
    GlobalSearch .search-filters {
        dock: top;
        height: 3;
        background: $surface;
        padding: 0 1;
        layout: horizontal;
    }
    
    GlobalSearch .search-results {
        height: 1fr;
        padding: 1;
    }
    
    GlobalSearch .search-result-item {
        height: 3;
        border: solid $accent;
        margin: 0 0 1 0;
        padding: 1;
    }
    
    GlobalSearch .result-title {
        text-style: bold;
    }
    
    GlobalSearch .result-description {
        color: $text-muted;
    }
    
    GlobalSearch .result-metadata {
        color: $text-muted;
        text-style: italic;
    }
    
    GlobalSearch .no-results {
        text-align: center;
        color: $text-muted;
        margin: 10 0;
    }
    """
    
    BINDINGS = [
        Binding("ctrl+f", "focus_search", "Search", show=False),
        Binding("escape", "clear_search", "Clear", show=False),
        Binding("enter", "perform_search", "Search", show=False),
    ]
    
    query = reactive("")
    is_searching = reactive(False)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.providers: List[SearchProvider] = []
        self.current_results: List[SearchResult] = []
        self.selected_filters: Set[SearchResultType] = set()
    
    def compose(self) -> ComposeResult:
        """Compose search interface"""
        # Search header
        header = Horizontal(classes="search-header")
        search_input = Input(
            placeholder="Search bots, labs, scripts, workflows...",
            classes="search-input",
            id="search-input"
        )
        search_button = Button("Search", variant="primary", classes="search-button", id="search-button")
        header.mount(search_input)
        header.mount(search_button)
        yield header
        
        # Search filters
        filters = Horizontal(classes="search-filters")
        filters.mount(Label("Filter by:"))
        
        filter_types = [
            (SearchResultType.BOT, "Bots"),
            (SearchResultType.LAB, "Labs"),
            (SearchResultType.SCRIPT, "Scripts"),
            (SearchResultType.WORKFLOW, "Workflows"),
        ]
        
        for result_type, label in filter_types:
            filter_button = Button(
                label,
                variant="outline",
                size="small",
                id=f"filter-{result_type.value}"
            )
            filters.mount(filter_button)
        
        yield filters
        
        # Results area
        yield Container(classes="search-results", id="search-results")
    
    def add_provider(self, provider: SearchProvider) -> None:
        """Add search provider"""
        self.providers.append(provider)
    
    async def on_input_changed(self, event: Input.Changed) -> None:
        """Handle search input changes"""
        if event.input.id == "search-input":
            self.query = event.value
            
            # Perform search with debouncing
            if len(self.query) >= 3:
                await asyncio.sleep(0.3)  # Simple debouncing
                if self.query == event.value:  # Check if query hasn't changed
                    await self.perform_search()
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses"""
        button_id = event.button.id
        
        if button_id == "search-button":
            await self.perform_search()
        elif button_id and button_id.startswith("filter-"):
            filter_type = button_id[7:]  # Remove "filter-" prefix
            await self.toggle_filter(SearchResultType(filter_type))
    
    async def perform_search(self) -> None:
        """Perform search across all providers"""
        if not self.query.strip():
            await self.clear_results()
            return
        
        self.is_searching = True
        all_results = []
        
        # Search all enabled providers
        search_tasks = []
        for provider in self.providers:
            if provider.enabled:
                # Apply filters
                if not self.selected_filters or provider.result_type in self.selected_filters:
                    search_tasks.append(provider.search(self.query))
        
        # Execute searches concurrently
        if search_tasks:
            provider_results = await asyncio.gather(*search_tasks, return_exceptions=True)
            
            for results in provider_results:
                if isinstance(results, list):
                    all_results.extend(results)
        
        # Sort results by score
        all_results.sort(key=lambda x: x.score, reverse=True)
        
        # Limit total results
        self.current_results = all_results[:100]
        
        await self.display_results()
        self.is_searching = False
    
    async def display_results(self) -> None:
        """Display search results"""
        results_container = self.query_one("#search-results")
        results_container.remove_children()
        
        if not self.current_results:
            no_results = Label("No results found", classes="no-results")
            results_container.mount(no_results)
            return
        
        # Create result list
        result_list = ListView(id="result-list")
        
        for result in self.current_results:
            result_item = self.create_result_item(result)
            result_list.append(result_item)
        
        results_container.mount(result_list)
    
    def create_result_item(self, result: SearchResult) -> ListItem:
        """Create result list item"""
        item_content = Vertical()
        
        # Title with icon
        title_container = Horizontal()
        if result.icon:
            title_container.mount(Label(result.icon))
        title_container.mount(Label(result.title, classes="result-title"))
        item_content.mount(title_container)
        
        # Description
        if result.description:
            item_content.mount(Label(result.description, classes="result-description"))
        
        # Metadata
        metadata_parts = []
        metadata_parts.append(f"Type: {result.result_type.value.title()}")
        if result.score > 0:
            metadata_parts.append(f"Score: {result.score:.1f}")
        
        metadata_text = " | ".join(metadata_parts)
        item_content.mount(Label(metadata_text, classes="result-metadata"))
        
        return ListItem(item_content, id=f"result-{result.id}")
    
    async def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle result selection"""
        if event.list_view.id == "result-list":
            item_id = event.item.id
            if item_id and item_id.startswith("result-"):
                result_id = item_id[7:]  # Remove "result-" prefix
                
                # Find and execute result action
                result = next((r for r in self.current_results if r.id == result_id), None)
                if result and result.action:
                    await result.action()
    
    async def toggle_filter(self, filter_type: SearchResultType) -> None:
        """Toggle search filter"""
        if filter_type in self.selected_filters:
            self.selected_filters.remove(filter_type)
        else:
            self.selected_filters.add(filter_type)
        
        # Update filter button appearance
        filter_button = self.query_one(f"#filter-{filter_type.value}", Button)
        if filter_type in self.selected_filters:
            filter_button.variant = "primary"
        else:
            filter_button.variant = "outline"
        
        # Re-perform search with new filters
        if self.query:
            await self.perform_search()
    
    async def clear_results(self) -> None:
        """Clear search results"""
        results_container = self.query_one("#search-results")
        results_container.remove_children()
        self.current_results = []
    
    async def action_focus_search(self) -> None:
        """Focus search input"""
        search_input = self.query_one("#search-input", Input)
        search_input.focus()
    
    async def action_clear_search(self) -> None:
        """Clear search"""
        search_input = self.query_one("#search-input", Input)
        search_input.value = ""
        self.query = ""
        await self.clear_results()
    
    async def action_perform_search(self) -> None:
        """Perform search action"""
        await self.perform_search()
    
    def watch_is_searching(self, searching: bool) -> None:
        """React to search state changes"""
        search_button = self.query_one("#search-button", Button)
        if searching:
            search_button.label = "Searching..."
            search_button.disabled = True
        else:
            search_button.label = "Search"
            search_button.disabled = False