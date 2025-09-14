# pyHaasAPI Development Workflow

## 🏗️ **Clean Library Structure**

### **Core Library Organization**
```
pyHaasAPI/
├── pyHaasAPI/                    # Main library package
│   ├── __init__.py              # Main exports
│   ├── api.py                   # Core API functions
│   ├── model.py                 # Data models
│   ├── analysis/                # Analysis module
│   │   ├── analyzer.py         # Main analysis engine
│   │   ├── models.py           # Analysis data classes
│   │   ├── cache.py            # Cache management
│   │   └── extraction.py       # Data extraction
│   ├── accounts/                # Account management
│   ├── labs/                    # Lab management
│   ├── markets/                 # Market management
│   ├── utils/                   # Utility functions
│   ├── cli/                     # Command-line interfaces
│   │   ├── __init__.py
│   │   ├── main.py             # Main CLI entry point
│   │   └── simple_cli.py       # Simple CLI implementation
│   └── examples/                # Example scripts
│       ├── __init__.py
│       ├── example_usage.py    # Basic usage examples
│       └── complete_bot_management_example.py
├── tests/                       # Test files
├── docs/                        # Documentation
├── archive/                     # Archived/obsolete files
│   ├── old_scripts/            # Old experimental scripts
│   ├── old_docs/               # Obsolete documentation
│   └── experimental/           # Experimental features
└── unified_cache/              # Cache directory
```

## 🔄 **Development Workflow**

### **1. New Feature Development**
```bash
# 1. Create experimental script in root (for testing)
touch new_feature_experiment.py

# 2. Develop and test functionality
python new_feature_experiment.py

# 3. Once working, integrate into pyHaasAPI package
#    - Add to appropriate module (api.py, analysis/, etc.)
#    - Create proper data models if needed
#    - Add to __init__.py exports

# 4. Create example/CLI script
#    - Move to pyHaasAPI/examples/ or pyHaasAPI/cli/
#    - Update imports to use library modules

# 5. Archive experimental script
mv new_feature_experiment.py archive/experimental/
```

### **2. CLI Development**
```bash
# CLI scripts go in pyHaasAPI/cli/
# Examples go in pyHaasAPI/examples/

# Run CLI:
python -m pyHaasAPI.cli analyze lab-id --create-count 3
python -m pyHaasAPI.cli list-labs
python -m pyHaasAPI.cli complete-workflow lab-id --activate
```

### **3. Library Usage**
```python
# Import from main package
from pyHaasAPI import HaasAnalyzer, UnifiedCacheManager

# Use integrated functionality
cache = UnifiedCacheManager()
analyzer = HaasAnalyzer(cache)
analyzer.connect()
result = analyzer.analyze_lab("lab-id", top_count=5)
```

## 📋 **File Organization Rules**

### **✅ Keep in Root:**
- `README.md` - Main documentation
- `pyproject.toml` - Package configuration
- `requirements.txt` - Dependencies
- `.cursorrules` - Development rules
- `DEVELOPMENT_WORKFLOW.md` - This file

### **✅ Move to pyHaasAPI/:**
- Core functionality → `pyHaasAPI/`
- CLI scripts → `pyHaasAPI/cli/`
- Examples → `pyHaasAPI/examples/`
- Tests → `tests/`

### **🗄️ Archive:**
- Experimental scripts → `archive/experimental/`
- Obsolete docs → `archive/old_docs/`
- Old scripts → `archive/old_scripts/`

## 🚀 **Usage Examples**

### **CLI Usage**
```bash
# Simple analysis
python -m pyHaasAPI.cli analyze e4616b35-8065-4095-966b-546de68fd493

# Complete workflow
python -m pyHaasAPI.cli complete-workflow e4616b35-8065-4095-966b-546de68fd493 --create-count 3 --activate --verify

# List labs
python -m pyHaasAPI.cli list-labs
```

### **Library Usage**
```python
from pyHaasAPI import HaasAnalyzer, UnifiedCacheManager

# Setup
cache = UnifiedCacheManager()
analyzer = HaasAnalyzer(cache)
analyzer.connect()

# Analyze and create bots
result = analyzer.analyze_lab("lab-id", top_count=5)
bots = analyzer.create_and_activate_bots(result, create_count=3, activate=True)
```

## 🧹 **Cleanup Checklist**

- [x] Move CLI scripts to `pyHaasAPI/cli/`
- [x] Move examples to `pyHaasAPI/examples/`
- [x] Archive obsolete scripts
- [x] Create proper module structure
- [x] Update imports and references
- [x] Create development workflow documentation

## 📝 **Next Steps**

1. **Update imports** in moved files
2. **Test CLI functionality** with new structure
3. **Update documentation** to reflect new organization
4. **Create setup.py** entry points for CLI commands
5. **Add more examples** as needed
