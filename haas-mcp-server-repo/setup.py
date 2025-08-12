#!/usr/bin/env python3
"""
Setup script for HaasOnline MCP Server
"""

from setuptools import setup, find_packages

setup(
    name="haas-mcp-server",
    version="1.0.0",
    description="MCP Server for HaasOnline API Integration",
    author="Cosmos",
    author_email="cosmos@example.com",
    url="https://github.com/Cosmos/haas-mcp-server",
    packages=find_packages(),
    install_requires=[
        "mcp>=1.0.0",
        "python-dotenv>=1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "haas-mcp-server=server:main",
        ],
    },
    python_requires=">=3.8",
)