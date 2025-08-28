# Publishing Scripts

This folder contains scripts for publishing the monorepo projects to separate GitHub repositories.

## Scripts

### `publish_pyhaasapi_only.py`
Publishes only the core pyHaasAPI library to GitHub while keeping the local monorepo intact.

**Usage:**
```bash
cd publishing
python publish_pyhaasapi_only.py
```

**What it publishes:**
- `pyHaasAPI/` - Core library
- `docs/` - Documentation
- `examples/` - Usage examples
- `experiments/` - Experimental features
- `tests/` - Test suite
- Essential config files (pyproject.toml, README.md, LICENSE, etc.)

### `create_mcp_repo.py`
Creates a clean MCP server repository structure for publishing.

### `publish_repos.py`
Legacy publishing workflow for both repositories.

### `update_repositories.py`
Automated update script for both repositories.

### `validate_setup.py`
Validation script to ensure proper repository setup.

## Usage Notes

- All scripts use the `temp/` folder for temporary operations
- Your local monorepo files are never modified
- Scripts automatically clean up temporary files after execution
- Run scripts from the project root directory

## Safety

These scripts are designed to:
- ✅ Keep your local development environment intact
- ✅ Only publish selected files to GitHub
- ✅ Clean up temporary files automatically
- ✅ Provide clear feedback on what's being published