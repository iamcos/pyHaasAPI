"""
Endpoint registry and resolver for pyHaasAPI v2.

This centralizes endpoint name normalization to ensure we always hit the
correct PHP endpoints (v1-style) from v2 runtime. It accepts either the
simple names (e.g., "Labs", "HaasScript") or explicit PHP endpoints
(e.g., "/LabsAPI.php") and returns a normalized PHP path that the
server expects to return JSON, not HTML.
"""

from __future__ import annotations

from typing import Dict


_CANONICAL: Dict[str, str] = {
    # Simple-name -> PHP endpoint mapping
    "Labs": "/LabsAPI.php",
    "Backtest": "/BacktestAPI.php",
    "HaasScript": "/HaasScriptAPI.php",
    "Account": "/AccountAPI.php",
    "Bot": "/BotAPI.php",
    "Price": "/PriceAPI.php",
    "User": "/UserAPI.php",
    "Setup": "/SetupAPI.php",
}


def resolve_endpoint(endpoint: str) -> str:
    """Resolve an endpoint identifier to a canonical PHP endpoint path.

    Rules:
    - If endpoint matches a known simple name (e.g., "Labs"), map to
      its PHP endpoint ("/LabsAPI.php").
    - If endpoint already looks like a PHP endpoint, normalize to start
      with a leading slash and return as-is.
    - Fallback: if endpoint has no extension and matches a key ignoring
      case, map to canonical; otherwise, return as provided.
    """
    if not endpoint:
        return endpoint

    # Fast path for exact simple-name keys
    if endpoint in _CANONICAL:
        return _CANONICAL[endpoint]

    # Normalize leading slash
    ep = endpoint if endpoint.startswith("/") else f"/{endpoint}"

    # If already looks like a PHP API file, keep it
    if ep.lower().endswith("api.php"):
        return ep

    # If it's exactly like "/Labs" etc, translate
    simple = ep[1:]
    if simple in _CANONICAL:
        return _CANONICAL[simple]

    # Case-insensitive match on simple names
    for k, v in _CANONICAL.items():
        if simple.lower() == k.lower():
            return v

    # Unknown; return normalized ep as-is
    return ep


