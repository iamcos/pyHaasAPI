#!/bin/bash

# Release script for pyHaasAPI
set -e

echo "🚀 pyHaasAPI Release Script"
echo "=========================="

# Check if Poetry is available
if ! command -v poetry &> /dev/null; then
    echo "❌ Poetry is not installed or not in PATH"
    echo "Please add Poetry to your PATH:"
    echo "export PATH=\"/Users/georgiigavrilenko/.local/bin:\$PATH\""
    exit 1
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
echo "1) TestPyPI (recommended for testing)"
echo "2) PyPI (production)"
echo "3) Both (TestPyPI first, then PyPI)"
echo "4) Skip publishing"
read -p "Enter choice (1-4): " publish_choice

case $publish_choice in
    1)
        echo "📤 Publishing to TestPyPI..."
        poetry publish --repository testpypi
        echo "✅ Published to TestPyPI!"
        echo "🔗 Test installation: pip install --index-url https://test.pypi.org/simple/ pyHaasAPI"
        ;;
    2)
        echo "📤 Publishing to PyPI..."
        poetry publish
        echo "✅ Published to PyPI!"
        echo "🔗 Package URL: https://pypi.org/project/pyHaasAPI/"
        ;;
    3)
        echo "📤 Publishing to TestPyPI first..."
        poetry publish --repository testpypi
        echo "✅ Published to TestPyPI!"
        
        echo ""
        read -p "TestPyPI publication successful. Continue to PyPI? (y/n): " continue_pypi
        if [[ $continue_pypi =~ ^[Yy]$ ]]; then
            echo "📤 Publishing to PyPI..."
            poetry publish
            echo "✅ Published to PyPI!"
            echo "🔗 Package URL: https://pypi.org/project/pyHaasAPI/"
        else
            echo "⏭️ Skipping PyPI publication"
        fi
        ;;
    4)
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