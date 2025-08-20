"""
Entry point for running cedar_mcp as a module.

This allows the package to be executed with: python -m cedar_mcp
"""

from .server import main

if __name__ == "__main__":
    main()
