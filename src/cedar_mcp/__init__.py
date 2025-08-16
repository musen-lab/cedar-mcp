"""
CEDAR MCP Server

A Model Context Protocol (MCP) server for interacting with the CEDAR metadata repository.
"""

__version__ = "0.1.0"
__author__ = "CEDAR Team"
__description__ = "A CEDAR MCP server"

from .server import main

__all__ = ["main"]