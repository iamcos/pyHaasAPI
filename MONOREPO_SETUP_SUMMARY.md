# Trading Automation Workspace

This workspace contains multiple interconnected projects for HaasOnline trading automation:

## 📦 Published Repositories

### 1. pyHaasAPI
- **Repository**: https://github.com/iamcos/pyHaasAPI
- **Description**: Core Python library for HaasOnline API integration
- **Location**: Root directory + `pyHaasAPI/` folder

### 2. haas-mcp-server  
- **Repository**: https://github.com/Cosmos/haas-mcp-server
- **Description**: MCP server for HaasOnline API access via Kiro
- **Location**: `mcp_server/` folder

## 🏗️ Development Projects

### 3. AI Trading Interface
- **Location**: `ai-trading-interface/`
- **Description**: Advanced React/TypeScript trading interface
- **Status**: In development

### 4. HaasScript Backtesting
- **Location**: `haasscript_backtesting/`
- **Description**: Comprehensive backtesting system
- **Status**: In development

## 🔧 Workspace Structure

```
├── pyHaasAPI/              # Core library (published)
├── mcp_server/             # MCP server (published separately)
├── ai-trading-interface/   # React trading interface
├── haasscript_backtesting/ # Backtesting system
├── examples/               # Usage examples
├── docs/                   # Documentation
└── tools/                  # Development tools
```

## 🚀 Getting Started

1. **For pyHaasAPI development**:
   ```bash
   pip install -e .
   ```

2. **For MCP server development**:
   ```bash
   cd mcp_server
   pip install -r requirements.txt
   ```

3. **For AI interface development**:
   ```bash
   cd ai-trading-interface
   npm install
   ```

## 📚 Documentation

- [pyHaasAPI Documentation](docs/README.md)
- [MCP Server Guide](mcp_server/README.md)
- [AI Interface Guide](ai-trading-interface/README.md)

---

**Maintained by Cosmos**
