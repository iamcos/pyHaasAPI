# AI Assistant Configuration Guide

**🤖 FOR AI ASSISTANTS: Complete guide to project configuration files and AI integration**

## 📋 Overview

This project includes comprehensive configuration for AI assistants, including Cursor AI, Gemini integration, and custom AI workflows. This guide explains all AI-related configuration files and how to use them effectively.

## 🔧 Configuration Files

### 1. Cursor AI Configuration

#### `rules.cursor` - Primary Project Rules
**Location**: Root directory  
**Purpose**: Comprehensive project guidelines and coding standards

**Key Sections**:
- **Market Naming**: Enforced format `<EXCHANGE>_<BASE>_<QUOTE>_`
- **API Optimization**: Exchange-specific market fetching patterns
- **Python Standards**: Type hints, docstrings, testing requirements
- **Architecture Rules**: Package organization and responsibility separation
- **API Endpoints**: Naming conventions and URL construction
- **Authentication**: Two-step authentication process
- **Parameter Handling**: LabParameter field mappings and types
- **Lab Management**: Complete workflow for lab creation and management
- **Error Handling**: Exception handling and logging patterns
- **Testing Guidelines**: Test structure and cleanup procedures

**Critical Rules for AI Assistants**:
```python
# AVOID: Slow, unreliable
api.get_all_markets(executor)

# USE: Fast, reliable, per-exchange
price_api = PriceAPI(executor)
markets = price_api.get_trade_markets("BINANCE")
```

#### `RUNNING_TESTS.cursor` - Testing Best Practices
**Location**: Root directory  
**Purpose**: Testing guidelines and script organization

**Key Guidelines**:
- Configuration loading from `config/settings.py`
- Test placement in appropriate directories (`tests/unit/`, `tests/integration/`, etc.)
- Authentication patterns using `api.RequestsExecutor`
- Import patterns and debugging guidelines
- Template for new test scripts

### 2. Gemini AI Integration

#### Core Integration Files:
- **`tests/integration/test_smart_client.py`** - Gemini API integration testing
- **`haasscript_rag/`** - RAG system for Gemini memory backend
- **`tools/haasscript_rag/`** - Additional RAG tools and utilities

#### Gemini Configuration:
```python
# API Configuration
GEMINI_API_KEY = "your_gemini_api_key"
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')
```

#### Integration Features:
- **Trading Advice**: AI-powered trading recommendations
- **Code Analysis**: Automated script analysis and optimization
- **Interactive Testing**: Natural language queries for trading data
- **RAG Memory**: MongoDB-backed knowledge system

### 3. Repository Management Configuration

#### `AI_ASSISTANT_QUICK_REFERENCE.md`
**Purpose**: Quick reference for repository operations
**Key Commands**:
- Repository update workflows
- Git operations and safety rules
- Emergency procedures

#### `INTERNAL_REPOSITORY_MANAGEMENT.md`
**Purpose**: Complete repository management guide
**Sections**:
- Dual-repository architecture
- Update workflows and safety procedures
- AI assistant configuration details
- Monitoring and health checks

## 🚀 AI Assistant Workflows

### For Code Development:
1. **Read `rules.cursor`** - Understand project standards
2. **Follow architecture rules** - Maintain code organization
3. **Use established patterns** - API calls, authentication, error handling
4. **Test with guidelines** - Follow `RUNNING_TESTS.cursor` patterns

### For Repository Updates:
1. **Use automated scripts** - `update_repositories.py`
2. **Follow safety rules** - Never delete staging directories
3. **Test locally first** - Validate changes before pushing
4. **Use descriptive commits** - Follow established message format

### For AI Integration:
1. **Gemini Integration** - Use established API patterns
2. **RAG System** - Leverage MongoDB backend for memory
3. **Interactive Testing** - Use smart client for natural language queries
4. **Code Analysis** - Integrate AI-powered optimization suggestions

## 🔍 Configuration Validation

### Validation Script: `validate_setup.py`
Checks all configuration files and ensures proper setup:
- File structure validation
- Git remote configuration
- Python environment verification
- Repository status checks

### Usage:
```bash
python validate_setup.py
```

## 📚 AI Integration Examples

### Gemini Trading Advice:
```python
# From test_smart_client.py
context_prompt = """
You are helping with a legitimate HaasOnline trading bot development system.
Provide analysis and recommendations for trading strategies.
"""

response = model.generate_content(context_prompt + "\n\nUser query: " + user_query)
print(f"Gemini response: {response.text}")
```

### RAG System Usage:
```python
# MongoDB-backed knowledge system
# Stores HaasScript functions, examples, and trading strategies
# Provides context-aware responses for development questions
```

### Interactive Testing:
```bash
# Available commands in smart client:
# - search btc (search BTC markets)
# - search scalper (search scalper scripts)  
# - ask gemini (ask Gemini for trading advice)
```

## 🛡️ Security and Best Practices

### API Key Management:
- Store Gemini API keys in environment variables
- Never commit API keys to repositories
- Use `.env` files for local development
- Validate API access before making requests

### Code Quality:
- Follow type hints and docstring requirements
- Use established error handling patterns
- Maintain test coverage for new features
- Document AI integration changes

### Repository Safety:
- Always use staging for MCP server updates
- Test AI integrations locally before pushing
- Validate configuration files after changes
- Monitor AI system performance and accuracy

## 🔧 Troubleshooting

### Common Issues:
1. **Import Errors**: Ensure running from project root or set `PYTHONPATH=.`
2. **Authentication Failures**: Check `.env` file and server status
3. **Gemini API Errors**: Validate API key and quota limits
4. **RAG System Issues**: Check MongoDB connection and data integrity

### Debug Commands:
```bash
# Validate entire setup
python validate_setup.py

# Test Gemini integration
python tests/integration/test_smart_client.py

# Check repository status
python update_repositories.py
```

## 📖 Additional Resources

### Documentation Files:
- `docs/PROJECT_ANALYSIS_DOCUMENTATION.md` - Complete project analysis
- `docs/CONTEXT_PROMPT.md` - Development context and planning
- `MONOREPO_SETUP_SUMMARY.md` - Repository architecture overview

### Configuration References:
- `infrastructure/config_manager.py` - ML analysis configuration
- `.gitignore` - Excludes AI tool directories (`.gemini/`, `.kiro/`)
- `pyproject.toml` - Package configuration and dependencies

---

**⚠️ IMPORTANT**: Always read and follow the configuration files before making changes. These files ensure consistency, safety, and proper AI integration across the entire project.