# AI Assistant Quick Reference Card

**🤖 FOR AI ASSISTANTS ONLY - Read this first when asked to update repositories**

## 🚨 Critical Rules
1. **NEVER delete `haas-mcp-server-repo/` directory**
2. **ALWAYS use staging for MCP server updates** 
3. **TEST locally before pushing**
4. **READ `INTERNAL_REPOSITORY_MANAGEMENT.md` for full details**

## ⚡ Quick Commands

### Update pyHaasAPI Only
```bash
git add .
git commit -m "Update: [description]"
git push origin master
```

### Update MCP Server Only
```bash
python create_mcp_repo.py
cd haas-mcp-server-repo
git add .
git commit -m "Update: [description]"
git push origin main
cd ..
```

### Update Both (Recommended)
```bash
python update_repositories.py
```

## 📍 Repository Info
- **pyHaasAPI**: https://github.com/iamcos/pyHaasAPI (master branch)
- **MCP Server**: https://github.com/iamcos/haas-mcp-server (main branch)
- **Author**: iamcos (Cosmos)

## 🔍 Before Any Update
1. Check: `git status` (no uncommitted changes)
2. Verify: You're in root directory (pyproject.toml exists)
3. Read: `rules.cursor` for project guidelines
4. Follow: `RUNNING_TESTS.cursor` for testing patterns
5. Test: Changes work locally
6. Read: Full documentation if unsure

## 📝 Commit Message Format
```
[Type]: [Brief description]

- [Detailed change 1]
- [Detailed change 2]
```

Types: Update, Fix, Add, Remove, Refactor, Docs, Config

## 🆘 If Something Goes Wrong
1. **STOP** - don't make more commits
2. **DOCUMENT** what happened
3. **ASK USER** for guidance
4. **REVERT** if safe: `git revert [commit-hash]`

## 📋 File Locations
- **Core Library**: `pyHaasAPI/` folder
- **MCP Server Source**: `mcp_server/` folder  
- **MCP Staging**: `haas-mcp-server-repo/` folder
- **Update Script**: `update_repositories.py`
- **Full Docs**: `INTERNAL_REPOSITORY_MANAGEMENT.md`
- **Project Rules**: `rules.cursor` (READ FIRST!)
- **Testing Guide**: `RUNNING_TESTS.cursor`
- **AI Config**: Gemini integration in `tests/integration/` and `haasscript_rag/`

---
**⚠️ When in doubt, ask the user rather than guessing!**