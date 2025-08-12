# Quick Release Guide

## 🚀 Fast Release Commands

### Option 1: Interactive Script (Recommended)
```bash
./release_twine.sh
```

### Option 2: Manual Commands
```bash
# 1. Update version
poetry version patch  # or minor/major

# 2. Build package
poetry build

# 3. Publish to PyPI
python -m twine upload --username __token__ --password "pypi-AgEIcHlwaS5vcmcCJGNiNDVmNWUzLTY5MDYtNDVkZS05MTJmLTAyODRlOWNiMmY3NQACKlszLCI4OTFiYjJiYi1jMzY5LTQwYzItYmJkZC01NWE1OTFlZmY1ZTciXQAABiB8qfg6s1RdVCam3ZJdIaZmm9ovX0VruJSnCgn89tz14Q" dist/*

# 4. Test installation
pip install pyHaasAPI
```

## 📦 Current Package Info
- **Name**: `pyHaasAPI`
- **Current Version**: `0.1.0`
- **PyPI URL**: https://pypi.org/project/pyHaasAPI/
- **Install**: `pip install pyHaasAPI`

## 🔑 Authentication
- **Username**: `iamcos`
- **Token**: `pypi-AgEIcHlwaS5vcmcCJGNiNDVmNWUzLTY5MDYtNDVkZS05MTJmLTAyODRlOWNiMmY3NQACKlszLCI4OTFiYjJiYi1jMzY5LTQwYzItYmJkZC01NWE1OTFlZmY1ZTciXQAABiB8qfg6s1RdVCam3ZJdIaZmm9ovX0VruJSnCgn89tz14Q`

## 🎯 Version Bumping
```bash
poetry version patch   # 0.1.0 → 0.1.1
poetry version minor   # 0.1.0 → 0.2.0
poetry version major   # 0.1.0 → 1.0.0
poetry version 0.1.2   # Set specific version
```

## ✅ Verification
```bash
# Check current version
poetry version -s

# Test build
poetry build

# Test installation
pip install pyHaasAPI

# Test import
python -c "import pyHaasAPI; print('✅ Success!')"
```

## 🚨 Important Notes
- Always increment version before publishing
- Use twine for reliable publishing
- Test installation after publishing
- Create Git tags for releases 