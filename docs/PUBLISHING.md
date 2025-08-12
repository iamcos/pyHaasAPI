# Publishing pyHaasAPI to PyPI

This guide walks you through publishing the pyHaasAPI package to PyPI using Poetry.

## Prerequisites

1. **PyPI Account**: You need an account on https://pypi.org/
2. **Poetry**: Already installed and configured
3. **API Token**: Create a PyPI API token for authentication

## Step 1: Create PyPI API Token

1. Go to https://pypi.org/ and log in to your account
2. Navigate to **Account Settings** → **API tokens**
3. Click **"Add API token"**
4. Configure the token:
   - **Name**: `pyHaasAPI-publishing`
   - **Scope**: **Entire account (all projects)**
5. Copy the generated token (starts with `pypi-`)

## Step 2: Configure Authentication

### Option A: Use the Setup Script (Recommended)
```bash
./setup_pypi.sh
```

### Option B: Manual Configuration
```bash
# Configure Poetry with your PyPI token
poetry config pypi-token.pypi "YOUR_API_TOKEN_HERE"

# Verify configuration
poetry config --list
```

## Step 3: Test Build

Before publishing, ensure the package builds correctly:

```bash
# Clean previous builds
rm -rf dist/ build/ *.egg-info/

# Build the package
poetry build

# Verify the build artifacts
ls -la dist/
```

You should see:
- `pyhaasapi-0.1.0.tar.gz` (source distribution)
- `pyhaasapi-0.1.0-py3-none-any.whl` (wheel distribution)

## Step 4: Test on TestPyPI (Recommended)

Before publishing to the main PyPI, test on TestPyPI:

```bash
# Publish to TestPyPI
poetry publish --repository testpypi

# Test installation from TestPyPI
pip install --index-url https://test.pypi.org/simple/ pyHaasAPI
```

## Step 5: Publish to PyPI

Once you've tested on TestPyPI and everything works:

```bash
# Publish to main PyPI
poetry publish
```

## Step 6: Verify Publication

1. Check your package on PyPI: https://pypi.org/project/pyHaasAPI/
2. Test installation: `pip install pyHaasAPI`
3. Verify it works in a new environment

## Version Management

To update the package:

1. **Update version** in `pyproject.toml`:
   ```toml
   version = "0.1.1"  # or use poetry version patch/minor/major
   ```

2. **Build and publish**:
   ```bash
   poetry build
   poetry publish
   ```

## Poetry Version Commands

```bash
# Increment patch version (0.1.0 → 0.1.1)
poetry version patch

# Increment minor version (0.1.0 → 0.2.0)
poetry version minor

# Increment major version (0.1.0 → 1.0.0)
poetry version major

# Set specific version
poetry version 0.1.2
```

## Troubleshooting

### Build Errors
- **Multiple packages detected**: Check `pyproject.toml` package configuration
- **License warnings**: Ensure license is specified as string, not table
- **Missing files**: Verify `MANIFEST.in` includes all necessary files

### Authentication Errors
- **Invalid token**: Regenerate your PyPI API token
- **Token scope**: Ensure token has "Entire account" scope
- **Configuration**: Run `poetry config --list` to verify settings

### Publishing Errors
- **Package name conflict**: Check if package name is already taken on PyPI
- **Version conflict**: Ensure version number is unique and higher than previous
- **File size limits**: PyPI has limits on package size

## Best Practices

1. **Always test on TestPyPI first**
2. **Use semantic versioning** (MAJOR.MINOR.PATCH)
3. **Update CHANGELOG.md** with release notes
4. **Tag releases in Git** after successful publication
5. **Test installation** in a clean environment
6. **Monitor package downloads** and user feedback

## Useful Commands

```bash
# Check current configuration
poetry config --list

# View package information
poetry show

# Check for outdated dependencies
poetry show --outdated

# Update dependencies
poetry update

# Clean build artifacts
poetry build --clean
```

## Support

If you encounter issues:
1. Check the [Poetry documentation](https://python-poetry.org/docs/)
2. Review [PyPI packaging guide](https://packaging.python.org/)
3. Check the [setuptools documentation](https://setuptools.pypa.io/) 