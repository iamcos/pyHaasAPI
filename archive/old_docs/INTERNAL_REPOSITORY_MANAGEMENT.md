# Internal Repository Management Guide

**FOR AI ASSISTANTS: This document contains critical instructions for managing the dual-repository setup. Read this completely before making any repository changes.**

## 🏗️ Repository Architecture Overview

This workspace uses a **monorepo-to-dual-repo** architecture:

- **Development**: All work happens in this monorepo workspace
- **Publishing**: Two separate public repositories are maintained and synchronized

### Repository Structure

```
pyHaasAPI/ (Root - Development Monorepo)
├── pyHaasAPI/                  # Core library source
├── mcp_server/                 # MCP server source  
├── haas-mcp-server-repo/       # Publishing staging for MCP server
├── ai-trading-interface/       # React interface (not published)
├── haasscript_backtesting/     # Backtesting system (not published)
└── [other development folders]

Published Repositories:
├── https://github.com/iamcos/pyHaasAPI (master branch)
├── https://github.com/iamcos/haas-mcp-server (main branch)
```

## 📋 Repository Details

### 1. pyHaasAPI Repository
- **URL**: https://github.com/iamcos/pyHaasAPI
- **Branch**: `master`
- **Source**: Root directory + `pyHaasAPI/` folder
- **Purpose**: Core Python library for HaasOnline API integration
- **Publishing Method**: Direct push from monorepo root

### 2. haas-mcp-server Repository  
- **URL**: https://github.com/iamcos/haas-mcp-server
- **Branch**: `main`
- **Source**: `mcp_server/` folder → staged in `haas-mcp-server-repo/`
- **Purpose**: MCP server for HaasOnline API access via Kiro
- **Publishing Method**: Staged copy then push

## 🔄 Update Workflows

### Updating pyHaasAPI Repository

**When to update**: After changes to core library code in `pyHaasAPI/` folder or root configuration files.

```bash
# 1. Make changes in the monorepo
# 2. Test changes locally
# 3. Commit and push to pyHaasAPI repository
git add .
git commit -m "Update: [describe changes]

- [specific change 1]
- [specific change 2]
- [etc.]"
git push origin master
```

**Critical Files to Monitor**:
- `pyproject.toml` (package configuration)
- `README.md` (main documentation)
- `LICENSE` (license file)
- `pyHaasAPI/` (all core library code)
- `examples/` (usage examples)
- `docs/` (documentation)

### Updating haas-mcp-server Repository

**When to update**: After changes to MCP server code in `mcp_server/` folder.

**CRITICAL**: Always use the staging process - never push directly to haas-mcp-server.

```bash
# 1. Make changes in mcp_server/ folder
# 2. Regenerate the staging repository
python create_mcp_repo.py

# 3. Navigate to staging area and push updates
cd haas-mcp-server-repo

# 4. Check what changed
git status
git diff

# 5. Add, commit, and push changes
git add .
git commit -m "Update: [describe changes]

- [specific change 1]  
- [specific change 2]
- [etc.]"
git push origin main

# 6. Return to root directory
cd ..
```

## 🚨 Critical Rules for AI Assistants

### DO NOT:
1. **Never delete `haas-mcp-server-repo/` directory** - it contains the git history
2. **Never push directly from `mcp_server/` to GitHub** - always use staging
3. **Never change repository URLs or branch names** without updating this document
4. **Never merge or rebase between the two repositories** - they are independent
5. **Never commit sensitive information** (API keys, passwords, etc.)

### ALWAYS:
1. **Test changes locally** before pushing to any repository
2. **Use descriptive commit messages** with bullet points for changes
3. **Update version numbers** in `pyproject.toml` files when making releases
4. **Regenerate MCP staging** using `create_mcp_repo.py` before MCP updates
5. **Verify repository URLs** before pushing

## 🛠️ Maintenance Scripts

### Available Scripts

1. **`create_mcp_repo.py`** - Regenerates MCP server staging repository
   ```bash
   python create_mcp_repo.py
   ```

2. **`publish_repos.py`** - Full publishing workflow (use with caution)
   ```bash
   python publish_repos.py
   ```

### Script Usage Guidelines

- **Use `create_mcp_repo.py`** for routine MCP server updates
- **Use `publish_repos.py`** only for major restructuring or initial setup
- **Always review** generated files before committing

## 📝 Commit Message Standards

### Format
```
[Type]: [Brief description]

- [Detailed change 1]
- [Detailed change 2]
- [etc.]

[Optional: Breaking changes, migration notes, etc.]
```

### Types
- `Update`: Regular feature updates or improvements
- `Fix`: Bug fixes
- `Add`: New features or files
- `Remove`: Deleted features or files
- `Refactor`: Code restructuring without functional changes
- `Docs`: Documentation updates
- `Config`: Configuration changes

### Examples
```bash
# Good commit message
git commit -m "Update: Enhanced market analysis capabilities

- Add new arbitrage detection algorithms
- Improve market data processing speed by 40%
- Fix memory leak in continuous data streaming
- Update documentation with new API endpoints"

# Bad commit message  
git commit -m "updates"
```

## 🔍 Verification Checklist

Before pushing to either repository, verify:

### For pyHaasAPI Updates:
- [ ] All tests pass locally
- [ ] `pyproject.toml` version updated if needed
- [ ] README.md reflects any new features
- [ ] No sensitive data in commits
- [ ] Examples still work with changes
- [ ] Follow guidelines in `rules.cursor` for code standards
- [ ] Test scripts follow patterns in `RUNNING_TESTS.cursor`

### For MCP Server Updates:
- [ ] `create_mcp_repo.py` executed successfully
- [ ] Staging repository (`haas-mcp-server-repo/`) contains expected changes
- [ ] MCP server starts without errors
- [ ] All endpoints respond correctly
- [ ] Requirements.txt updated if dependencies changed
- [ ] Gemini integration tests pass (if applicable)

## 🚨 Emergency Procedures

### If Wrong Repository is Updated:
1. **Stop immediately** - don't make more commits
2. **Document what happened** in detail
3. **Revert the incorrect commit** if possible:
   ```bash
   git revert [commit-hash]
   git push origin [branch-name]
   ```
4. **Apply changes to correct repository** using proper workflow

### If Repositories Get Out of Sync:
1. **Identify the source of truth** (usually the monorepo)
2. **Backup current state** of both repositories
3. **Regenerate staging** using `create_mcp_repo.py`
4. **Carefully merge** any unique changes from published repos
5. **Test thoroughly** before pushing updates

### If Git History is Corrupted:
1. **Do not force push** - this will break things for users
2. **Create a new branch** with correct history
3. **Gradually migrate** users to new branch
4. **Update documentation** to reflect branch changes

## 🤖 AI Assistant Configuration Files

This project includes several configuration files specifically for AI assistants:

### Core Configuration Files:
1. **`rules.cursor`** - Comprehensive project rules and guidelines
   - Market naming conventions and API patterns
   - Python coding standards and architecture rules
   - API endpoint naming and authentication patterns
   - Parameter handling and lab management workflows
   - Error handling and testing guidelines

2. **`RUNNING_TESTS.cursor`** - Testing best practices
   - Configuration and credential management
   - Test script placement and organization
   - Import patterns and authentication setup
   - Debugging guidelines and templates

3. **`AI_ASSISTANT_QUICK_REFERENCE.md`** - Quick reference for AI assistants
   - Critical safety rules and commands
   - Repository information and workflows
   - Emergency procedures

### Gemini Integration:
The project includes Gemini AI integration in several areas:
- **Test Integration**: `tests/integration/test_smart_client.py` includes Gemini API integration
- **RAG System**: `haasscript_rag/` and `tools/haasscript_rag/` provide memory backend for Gemini
- **Configuration**: Infrastructure includes Gemini CLI path configuration
- **Interactive Testing**: Smart client includes Gemini-powered trading advice

### Usage Guidelines for AI Assistants:
- **Always read `rules.cursor`** before making code changes
- **Follow testing patterns** from `RUNNING_TESTS.cursor`
- **Respect project architecture** defined in configuration files
- **Use established patterns** for API calls, authentication, and error handling
- **Maintain consistency** with existing code standards

## 📊 Monitoring and Health Checks

### Regular Checks (Weekly):
- [ ] Both repositories are accessible
- [ ] Latest commits are properly synchronized
- [ ] No security alerts on GitHub
- [ ] Dependencies are up to date
- [ ] Documentation links work correctly
- [ ] AI assistant configuration files are up to date

### Monthly Reviews:
- [ ] Repository statistics and usage
- [ ] Outstanding issues and pull requests
- [ ] Version number consistency
- [ ] License and attribution accuracy
- [ ] AI integration functionality (Gemini, RAG systems)
- [ ] Configuration file accuracy and completeness

## 📞 Support Information

### Repository URLs:
- **pyHaasAPI**: https://github.com/iamcos/pyHaasAPI
- **haas-mcp-server**: https://github.com/iamcos/haas-mcp-server

### Key Files to Never Delete:
- `create_mcp_repo.py` - MCP staging generator
- `publish_repos.py` - Publishing workflow
- `INTERNAL_REPOSITORY_MANAGEMENT.md` - This document
- `MONOREPO_SETUP_SUMMARY.md` - Architecture overview
- `haas-mcp-server-repo/.git/` - MCP server git history
- `rules.cursor` - Cursor AI assistant rules and project guidelines
- `RUNNING_TESTS.cursor` - Testing guidelines for AI assistants
- `AI_ASSISTANT_QUICK_REFERENCE.md` - Quick reference for AI assistants

### Author Information:
- **GitHub Username**: iamcos
- **Display Name**: Cosmos
- **License**: MIT License

---

**⚠️ IMPORTANT FOR AI ASSISTANTS**: 
- Always read this document completely before making repository changes
- When in doubt, ask the user for clarification rather than guessing
- Test changes locally before pushing to public repositories
- Keep this document updated when making architectural changes