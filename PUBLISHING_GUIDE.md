# Publishing Guide

**Complete guide for publishing pyHaasAPI and MCP server repositories**

## 🏗️ Architecture Overview

This project uses a **monorepo-to-selective-publishing** architecture:

- **Local Development**: Full monorepo with all projects (ai-trading-interface, mcp_server, haasscript_backtesting, etc.)
- **Published Repositories**: Clean, focused repositories with only essential files

### Published Repositories:
1. **pyHaasAPI**: https://github.com/iamcos/pyHaasAPI (core library only)
2. **haas_mcp_server**: https://github.com/iamcos/haas_mcp_server (private MCP server repository)

## 🚀 Publishing pyHaasAPI

### Quick Publishing
```bash
python publish.py
```

This will:
- ✅ Keep your local files completely untouched
- ✅ Create a temporary clean copy with only essential files
- ✅ Push the clean version to GitHub
- ✅ Clean up temporary files automatically

### What Gets Published:
- `pyHaasAPI/` - Core library code
- `docs/` - Documentation
- `examples/` - Usage examples
- `experiments/` - Experimental features
- `tests/` - Test suite
- `pyproject.toml` - Package configuration
- `README.md` - Main documentation
- `LICENSE` - MIT License
- `.gitignore` - Git ignore rules
- `rules.cursor` - Development rules
- `RUNNING_TESTS.cursor` - Testing guidelines

### What Gets Excluded:
- `ai-trading-interface/` - React trading interface
- `mcp_server/` - MCP server (published separately)
- `haasscript_backtesting/` - Backtesting system
- `publishing/` - Publishing scripts
- All monorepo management files
- Development tools and temporary files

## 🔧 Publishing MCP Server

### Publishing to Private Repository:
```bash
cd publishing
python publish_mcp_server.py
```

This publishes the MCP server to the private `haas_mcp_server` repository.

**Note**: The MCP server is **not available on PyPI** - install from source:
```bash
pip install git+https://github.com/iamcos/haas_mcp_server.git
```

## 📋 Publishing Workflow

### For Regular Updates:

1. **Make changes** in your local monorepo
2. **Test locally** to ensure everything works
3. **Run publishing script**:
   ```bash
   python publish.py
   ```
4. **Enter descriptive commit message** when prompted
5. **Verify on GitHub** that only essential files are published

### For Major Updates:

1. **Update version numbers** in `pyproject.toml`
2. **Update documentation** in `docs/` and `README.md`
3. **Test all examples** to ensure they still work
4. **Run publishing script** with detailed commit message
5. **Create GitHub release** if needed

## 🛡️ Safety Features

### Local Protection:
- ✅ **No local files are ever modified** during publishing
- ✅ **Temporary files are automatically cleaned up**
- ✅ **Publishing uses isolated temporary directories**
- ✅ **Original monorepo structure is preserved**

### Publishing Safety:
- ✅ **Force push protection** - script confirms before overwriting
- ✅ **File validation** - checks that essential files exist before publishing
- ✅ **Clear feedback** - shows exactly what's being published
- ✅ **Rollback capability** - can revert if needed

## 📁 Directory Structure

### Local Monorepo (Development):
```
pyHaasAPI/ (Root)
├── pyHaasAPI/              # Core library
├── ai-trading-interface/   # React interface
├── mcp_server/             # MCP server
├── haasscript_backtesting/ # Backtesting system
├── publishing/             # Publishing scripts
├── temp/                   # Temporary execution folder
├── docs/                   # Documentation
├── examples/               # Usage examples
├── experiments/            # Experimental features
├── tests/                  # Test suite
└── [other development folders]
```

### Published pyHaasAPI Repository:
```
pyHaasAPI/ (GitHub)
├── pyHaasAPI/              # Core library
├── docs/                   # Documentation
├── examples/               # Usage examples
├── experiments/            # Experimental features
├── tests/                  # Test suite
├── pyproject.toml          # Package configuration
├── README.md               # Main documentation
├── LICENSE                 # MIT License
├── .gitignore              # Git ignore rules
├── rules.cursor            # Development rules
└── RUNNING_TESTS.cursor    # Testing guidelines
```

## 🔧 Available Scripts

### `publish.py` (Root Directory)
Simple launcher for the main publishing script.
```bash
python publish.py
```

### `publishing/publish_pyhaasapi_only.py`
Main selective publishing script that:
- Creates clean temporary copy
- Publishes only essential files
- Cleans up automatically

### `publishing/create_mcp_repo.py`
Creates clean MCP server repository structure.

### `publishing/validate_setup.py`
Validates that publishing setup is correct.

## 🚨 Important Notes for AI Assistants

### Critical Rules:
1. **NEVER delete local files** - only publish clean copies
2. **ALWAYS use the publishing scripts** - don't manually copy files
3. **TEST locally first** - ensure changes work before publishing
4. **USE temp/ folder** for any temporary operations
5. **KEEP monorepo intact** - all development happens locally

### Before Publishing:
- [ ] Test changes locally
- [ ] Update version in `pyproject.toml` if needed
- [ ] Update documentation if needed
- [ ] Ensure examples still work
- [ ] Run `python publish.py`

### After Publishing:
- [ ] Verify GitHub repository looks correct
- [ ] Check that only essential files are present
- [ ] Test installation from GitHub if needed
- [ ] Create release if it's a version update

## 🔍 Troubleshooting

### Common Issues:

**"Repository not found" error:**
- Check GitHub repository exists and is accessible
- Verify repository URL in script

**"Permission denied" error:**
- Ensure you have push access to the repository
- Check GitHub authentication

**"Files missing" error:**
- Verify all essential files exist locally
- Check file paths in publishing script

### Recovery:
If something goes wrong:
1. **Your local files are safe** - nothing was modified
2. **GitHub can be restored** by running the script again
3. **Temporary files are cleaned up** automatically

## 📚 Documentation Updates

When updating documentation:
1. **Edit files locally** in the monorepo
2. **Test documentation builds** if applicable
3. **Run publishing script** to update GitHub
4. **Verify documentation** appears correctly on GitHub

## 🎯 Best Practices

### Commit Messages:
Use descriptive commit messages:
```
Update: Enhanced market analysis capabilities

- Add new arbitrage detection algorithms
- Improve market data processing speed
- Fix memory leak in continuous streaming
- Update documentation with new examples
```

### Version Management:
- Update `pyproject.toml` version for releases
- Use semantic versioning (1.0.0, 1.0.1, 1.1.0, etc.)
- Create GitHub releases for major versions

### Testing:
- Always test locally before publishing
- Verify examples work with changes
- Check that imports work correctly
- Test installation process if possible

---

**This publishing system ensures your development workflow stays smooth while keeping the public repositories clean and focused.**