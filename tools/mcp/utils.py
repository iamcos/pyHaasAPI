"""
Shared utilities for MCP server/client consolidation.
- Data loading
- Caching
- Search/indexing
- Prompt building (for Gemini/NLP)
- Request/response formatting
"""

# TODO: Implement data loading helpers
def load_data_from_server(client, method: str, params: dict = None):
    """Stub for loading data from the MCP server."""
    pass

# TODO: Implement caching utilities
class DataCache:
    def __init__(self):
        self.scripts = []
        self.markets = []
        self.accounts = []
        # ...

# TODO: Implement search/indexing helpers
def search_markets(markets, query):
    """Stub for fast market search."""
    pass

def search_scripts(scripts, query):
    """Stub for fast script search."""
    pass

# TODO: Implement prompt building for Gemini/NLP
def build_gemini_prompt(context):
    """Stub for building system prompt for Gemini/NLP."""
    pass

# TODO: Implement request/response formatting helpers 