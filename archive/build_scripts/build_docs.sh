#!/bin/bash

# Documentation Build Script for pyHaasAPI
set -e

echo "📚 Building pyHaasAPI Documentation"
echo "==================================="

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: pyproject.toml not found. Please run this script from the project root."
    exit 1
fi

# Check if Poetry is available
if ! command -v poetry &> /dev/null; then
    echo "❌ Poetry is not installed or not in PATH"
    echo "Please add Poetry to your PATH:"
    echo "export PATH=\"/Users/georgiigavrilenko/.local/bin:\$PATH\""
    exit 1
fi

# Check if Sphinx is available
if ! python -c "import sphinx" 2>/dev/null; then
    echo "📦 Installing Sphinx and documentation dependencies..."
    python -m pip install sphinx sphinx-rtd-theme myst-parser
fi

echo "🧹 Cleaning previous builds..."
rm -rf docs/build/

echo "📝 Regenerating API documentation..."
sphinx-apidoc -o docs/source/modules pyHaasAPI --separate --module-first --no-toc --force

echo "🔨 Building HTML documentation..."
cd docs
make html

echo "✅ Documentation built successfully!"
echo ""
echo "📋 Summary:"
echo "   - HTML documentation: docs/build/html/"
echo "   - Main page: docs/build/html/index.html"
echo ""
echo "🌐 To view the documentation:"
echo "   open docs/build/html/index.html"
echo ""
echo "📦 To deploy to Read the Docs:"
echo "   1. Push changes to GitHub"
echo "   2. Connect repository to Read the Docs"
echo "   3. Documentation will auto-build"
echo ""
echo "🔧 To clean and rebuild:"
echo "   make clean && make html" 