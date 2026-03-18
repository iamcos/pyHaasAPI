import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock
from pyHaasAPI.core.server_log_service import ServerLogService
from pyHaasAPI.core.server_manager import ServerManager

@pytest.fixture
def mock_server_manager():
    sm = MagicMock(spec=ServerManager)
    sm.execute_remote_command = AsyncMock()
    return sm

@pytest.fixture
def log_service(mock_server_manager):
    return ServerLogService(mock_server_manager)

@pytest.mark.asyncio
async def test_list_screen_sessions(log_service, mock_server_manager):
    # Mock output of screen -ls
    mock_stdout = """
There is a screen on:
	7519.pts-2.srv03	(01.11.2025 18:25:02)	(Detached)
1 Socket in /run/screen/S-miguel.
"""
    mock_server_manager.execute_remote_command.return_value = (True, mock_stdout, "")
    
    sessions = await log_service.list_screen_sessions("srv03")
    
    assert len(sessions) == 1
    assert sessions[0]["id"] == "7519"
    assert sessions[0]["name"] == "pts-2.srv03"
    assert "01.11.2025" in sessions[0]["date"]
    assert sessions[0]["status"] == "Detached"

@pytest.mark.asyncio
async def test_get_screen_snapshot(log_service, mock_server_manager):
    mock_server_manager.execute_remote_command.side_effect = [
        (True, "", ""), # rm
        (True, "", ""), # screen -X hardcopy
        (True, "Log Content Line 1\nLog Content Line 2", ""), # cat
        (True, "", "")  # rm cleanup
    ]
    
    snapshot = await log_service.get_screen_snapshot("srv03", "7519")
    assert "Log Content Line 1" in snapshot
    assert "Log Content Line 2" in snapshot

@pytest.mark.asyncio
async def test_export_filtered_logs(log_service, mock_server_manager, tmp_path):
    output_file = tmp_path / "test_export.txt"
    
    mock_server_manager.execute_remote_command.side_effect = [
        (True, "/home/miguel/hts.log", ""), # find
        (True, "ERROR: Something went wrong\nWARNING: Be careful", ""), # grep
    ]
    
    success, msg = await log_service.export_filtered_logs("srv03", str(output_file))
    
    assert success is True
    assert output_file.exists()
    content = output_file.read_text()
    assert "ERROR: Something went wrong" in content
    assert "WARNING: Be careful" in content
