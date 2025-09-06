#!/bin/bash

# Release script for pyHaasAPI using twine
set -e

echo "🚀 pyHaasAPI Release Script (Twine)"
echo "==================================="

# Check if Poetry is available
if ! command -v poetry &> /dev/null; then
    echo "❌ Poetry is not installed or not in PATH"
    echo "Please add Poetry to your PATH:"
    echo "export PATH=\"/Users/georgiigavrilenko/.local/bin:\$PATH\""
    exit 1
fi

# Check if twine is available
if ! python -c "import twine" 2>/dev/null; then
    echo "📦 Installing twine..."
    python -m pip install twine
fi

# Get current version
current_version=$(poetry version -s)
echo "📦 Current version: $current_version"

# Ask for version bump type
echo ""
echo "Select version bump type:"
echo "1) patch (0.1.0 → 0.1.1)"
echo "2) minor (0.1.0 → 0.2.0)"
echo "3) major (0.1.0 → 1.0.0)"
echo "4) custom version"
echo "5) keep current version"
read -p "Enter choice (1-5): " choice

case $choice in
    1)
        poetry version patch
        ;;
    2)
        poetry version minor
        ;;
    3)
        poetry version major
        ;;
    4)
        read -p "Enter custom version (e.g., 0.1.2): " custom_version
        poetry version "$custom_version"
        ;;
    5)
        echo "Keeping current version: $current_version"
        ;;
    *)
        echo "Invalid choice. Exiting."
        exit 1
        ;;
esac

new_version=$(poetry version -s)
echo "📦 New version: $new_version"

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf dist/ build/ *.egg-info/

# Build the package
echo "🔨 Building package..."
poetry build

# Verify build artifacts
echo "✅ Build artifacts:"
ls -la dist/

# Ask for publishing target
echo ""
echo "Select publishing target:"
echo "1) TestPyPI (requires separate TestPyPI account)"
echo "2) PyPI (production)"
echo "3) Skip publishing"
read -p "Enter choice (1-3): " publish_choice

case $publish_choice in
    1)
        echo "📤 Publishing to TestPyPI..."
        echo "Note: You need a separate TestPyPI account and token"
        read -p "Enter TestPyPI token: " testpypi_token
        python -m twine upload --repository testpypi --username __token__ --password "$testpypi_token" dist/*
        echo "✅ Published to TestPyPI!"
        echo "🔗 Test installation: pip install --index-url https://test.pypi.org/simple/ pyHaasAPI"
        ;;
    2)
        echo "📤 Publishing to PyPI..."
        echo "Using your main PyPI token..."
        python -m twine upload --username __token__ --password "pypi-AgEIcHlwaS5vcmcCJGNiNDVmNWUzLTY5MDYtNDVkZS05MTJmLTAyODRlOWNiMmY3NQACKlszLCI4OTFiYjJiYi1jMzY5LTQwYzItYmJkZC01NWE1OTFlZmY1ZTciXQAABiB8qfg6s1RdVCam3ZJdIaZmm9ovX0VruJSnCgn89tz14Q" dist/*
        echo "✅ Published to PyPI!"
        echo "🔗 Package URL: https://pypi.org/project/pyHaasAPI/"
        ;;
    3)
        echo "⏭️ Skipping publication"
        ;;
    *)
        echo "Invalid choice. Exiting."
        exit 1
        ;;
esac

echo ""
echo "🎉 Release process completed!"
echo "📋 Summary:"
echo "   - Version: $new_version"
echo "   - Build artifacts: dist/"
echo "   - Next steps:"
echo "     - Test installation in clean environment"
echo "     - Update documentation if needed"
echo "     - Create Git tag: git tag v$new_version"
echo "     - Push tag: git push origin v$new_version" 