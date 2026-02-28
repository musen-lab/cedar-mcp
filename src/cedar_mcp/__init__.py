"""
CEDAR MCP Server

A Model Context Protocol (MCP) server for interacting with the CEDAR metadata repository.
"""

__version__ = "1.0.0"
__author__ = "Josef Hardi"
__description__ = "A CEDAR MCP server"

from .server import main

__all__ = ["main"]
