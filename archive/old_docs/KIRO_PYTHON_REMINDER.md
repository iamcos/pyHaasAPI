# CRITICAL PYTHON ENVIRONMENT REMINDER FOR KIRO

## ⚠️ ALWAYS USE .venv VIRTUAL ENVIRONMENT ⚠️

**NEVER FORGET:** This project has a `.venv` virtual environment that MUST be used for ALL Python operations.

### Commands to ALWAYS use:
- `.venv/bin/python` instead of `python` or `python3`
- `.venv/bin/pip` instead of `pip` or `pip3`

### For executeBash commands:
- When running Python scripts: `.venv/bin/python script.py`
- When installing packages: `.venv/bin/pip install package_name`
- When running from subdirectories: `../.venv/bin/python script.py`

### Environment Variables:
- Local credentials are in .env file
- Use API_EMAIL_LOCAL and API_PASSWORD_LOCAL for local HaasOnline connection
- Host: 127.0.0.1:8090

### MCP Server:
- Always start with: `.venv/bin/python mcp_server/server.py`
- Or use the start_mcp_server.sh script

**THIS IS NON-NEGOTIABLE - ALWAYS USE .venv!!!**