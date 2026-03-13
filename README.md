# CEDAR MCP Server

A Model Context Protocol (MCP) server for interacting with the CEDAR (Center for Expanded Data Annotation and Retrieval) metadata repository.

## Prerequisites

Before using this MCP server, you'll need API keys from:

### CEDAR API Key
- Go to [cedar.metadatacenter.org](https://cedar.metadatacenter.org)
- Create an account or log in
- Navigate to: Profile → API Key
- Copy your API key

### BioPortal API Key
- Go to [bioportal.bioontology.org](https://bioportal.bioontology.org)
- Create an account or log in
- Navigate to: Account Settings → API Key
- Copy your API key

## Running the CEDAR MCP Server

Set your API keys as environment variables:

```bash
export CEDAR_API_KEY="your-cedar-key"
export BIOPORTAL_API_KEY="your-bioportal-key"
```

### Option 1: Using UVX (Recommended)

Run directly without installation using `uvx`:

```bash
uvx cedar-mcp
```

### Option 2: Using pip

Install from PyPI and run:

```bash
pip install cedar-mcp
cedar-mcp
```

> **Note:** The `--cedar-api-key` and `--bioportal-api-key` CLI flags are deprecated and will be removed in a future release. Use environment variables instead.

### Transport Options

By default, the server uses `stdio` transport. You can also run it as an HTTP server using SSE or streamable-http transports:

```bash
# SSE transport on default host/port (127.0.0.1:8000)
cedar-mcp --transport sse

# Streamable HTTP on custom host/port
cedar-mcp --transport streamable-http --host 0.0.0.0 --port 9000
```

| Flag | Choices | Default | Description |
|------|---------|---------|-------------|
| `--transport` | `stdio`, `sse`, `streamable-http` | `stdio` | Transport protocol |
| `--host` | — | `127.0.0.1` | Host to bind to (HTTP transports only) |
| `--port` | — | `8000` | Port to bind to (HTTP transports only) |

## Using with Claude Code

Add the CEDAR MCP server to Claude Code:

```bash
claude mcp add cedar-mcp --uvx -e CEDAR_API_KEY=your-cedar-key -e BIOPORTAL_API_KEY=your-bioportal-key
```

## Using with Claude Desktop

To use with Claude Desktop app:

1. **Install the MCP server** using one of the methods above
2. **Add to Claude Desktop configuration** in your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "cedar-mcp": {
      "command": "uvx",
      "args": [
        "cedar-mcp"
      ],
      "env": {
        "CEDAR_API_KEY": "your-cedar-key",
        "BIOPORTAL_API_KEY": "your-bioportal-key",
        "CEDAR_MCP_CACHE_TTL_SECONDS": "86400",
        "CEDAR_MCP_CACHE_DIR": "/path/to/custom/location"
      }
    }
  }
}
```

Or if you have it installed locally:

```json
{
  "mcpServers": {
    "cedar-mcp": {
      "command": "cedar-mcp",
      "env": {
        "CEDAR_API_KEY": "your-cedar-key",
        "BIOPORTAL_API_KEY": "your-bioportal-key",
        "CEDAR_MCP_CACHE_TTL_SECONDS": "86400",
        "CEDAR_MCP_CACHE_DIR": "/path/to/custom/location"
      }
    }
  }
}
```

The `CEDAR_MCP_CACHE_TTL_SECONDS` and `CEDAR_MCP_CACHE_DIR` environment variables are optional. When set under the `"env"` key, Claude Desktop injects them into the server process environment before it starts, so the cache picks them up automatically. If omitted, the defaults apply (24-hour TTL and a platform-specific cache directory — see [Cache Configuration](#cache-configuration)).

## Available Tools

Here is the list of CEDAR tools with a short description

* `get_cedar_template`: Fetches a template from the CEDAR repository.
* `get_instances_based_on_template`: Gets template instances that belong to a specific template with pagination support.
* `term_search_from_branch`: Searches BioPortal for standardized ontology terms within a specific branch.
* `term_search_from_ontology`: Searches BioPortal for standardized ontology terms within an entire ontology.
* `get_branch_children`: Fetches all immediate children terms for a given branch in an ontology.
* `get_ontology_class_tree`: Fetches the hierarchical tree structure for a given class in an ontology.
* `remove_stale_cache_entries`: Removes expired entries from the BioPortal search cache.
* `clear_bioportal_cache`: Clears all entries from the BioPortal search cache.

## Cache Configuration

BioPortal search results are cached locally using SQLite to reduce latency and API load. The cache persists across server restarts.

| Variable | Default | Description |
|----------|---------|-------------|
| `CEDAR_MCP_CACHE_TTL_SECONDS` | `86400` (24 hours) | Time-to-live for cached BioPortal responses |
| `CEDAR_MCP_CACHE_DIR` | Platform-specific (see below) | Override the cache directory location |

**Default cache locations:**
- **macOS:** `~/Library/Caches/cedar-mcp`
- **Linux:** `$XDG_CACHE_HOME/cedar-mcp` or `~/.cache/cedar-mcp`
- **Windows:** `%LOCALAPPDATA%/cedar-mcp/cache`

## Development

### Install Development Dependencies

```bash
pip install -r requirements-dev.txt
```

### Running Tests

This project includes comprehensive integration tests that validate real API interactions with both CEDAR and BioPortal APIs.

For detailed testing information, see [test/README.md](test/README.md).

## Contributing

Contributions are welcome! Please ensure all tests pass before submitting a Pull Request:

```bash
python run_tests.py --integration
```

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
