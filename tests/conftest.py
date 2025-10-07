"""
Global test configuration enforcing single-tunnel preflight and guardrails.
"""

import os
import pytest
import asyncio


@pytest.fixture(scope="session", autouse=True)
def enforce_no_skips_xfails(pytestconfig):
    """Fail fast if any test is marked skip or xfail."""
    for item in pytestconfig.session.items:
        if item.get_closest_marker("skip") or item.get_closest_marker("xfail"):
            pytest.fail(f"Prohibited marker detected on {item.nodeid}: skip/xfail not allowed")


@pytest.fixture(scope="session", autouse=True)
def srv_tunnel_preflight():
    """Suite-wide preflight check for mandated SSH tunnel on 8090/8092."""
    try:
        from pyHaasAPI.core.server_manager import ServerManager
        from pyHaasAPI.config.settings import Settings
    except Exception as e:
        pytest.fail(f"Failed to import ServerManager/Settings: {e}")

    sm = ServerManager(Settings())

    async def _check():
        ok = await sm.preflight_check()
        if not ok:
            pytest.fail(
                "Tunnel preflight failed. Start the mandated SSH tunnel: "
                "ssh -N -L 8090:127.0.0.1:8090 -L 8092:127.0.0.1:8092 prod@srv03"
            )

    asyncio.get_event_loop().run_until_complete(_check())


