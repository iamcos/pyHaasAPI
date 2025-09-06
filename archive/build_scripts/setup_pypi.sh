#!/bin/bash

# PyPI Setup Script for pyHaasAPI
echo "🚀 Setting up PyPI publishing for pyHaasAPI"
echo ""

# Check if Poetry is available
if ! command -v poetry &> /dev/null; then
    echo "❌ Poetry is not installed or not in PATH"
    echo "Please add Poetry to your PATH:"
    echo "export PATH=\"/Users/georgiigavrilenko/.local/bin:\$PATH\""
    exit 1
fi

echo "✅ Poetry is available"
echo ""

# Instructions for PyPI token
echo "📋 Before proceeding, you need to create a PyPI API token:"
echo "1. Go to https://pypi.org/ and log in"
echo "2. Go to Account Settings → API tokens"
echo "3. Click 'Add API token'"
echo "4. Name: pyHaasAPI-publishing"
echo "5. Scope: Entire account (all projects)"
echo "6. Copy the token (starts with 'pypi-')"
echo ""

# Get credentials from user
read -p "Enter your PyPI username: " pypi_username
read -s -p "Enter your PyPI API token: " pypi_token
echo ""

# Configure Poetry with PyPI credentials
echo "🔐 Configuring Poetry with PyPI credentials..."
poetry config pypi-token.pypi "$pypi_token"

# Test the configuration
echo "🧪 Testing PyPI configuration..."
if poetry config pypi-token.pypi | grep -q "pypi-"; then
    echo "✅ PyPI authentication configured successfully!"
else
    echo "❌ Failed to configure PyPI authentication"
    exit 1
fi

echo ""
echo "🎉 Setup complete! You can now publish to PyPI using:"
echo "   poetry publish"
echo ""
echo "📦 To test on TestPyPI first, run:"
echo "   poetry publish --repository testpypi"
echo ""
echo "🔍 To check your current configuration:"
echo "   poetry config --list" 