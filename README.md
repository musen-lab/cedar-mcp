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

### Option 1: Using UVX (Recommended)

Run directly without installation using `uvx`:

```bash
uvx --from git+https://github.com/musen-lab/cedar-mcp.git cedar-mcp \
  --cedar-api-key "your-cedar-key" \
  --bioportal-api-key "your-bioportal-key"
```

### Option 2: Local Installation with UV

Clone and run using `uv`:

```bash
# Clone the repository
git clone https://github.com/musen-lab/cedar-mcp.git
cd cedar-mcp

# Install dependencies and run
uv run python -m cedar_mcp.server \
  --cedar-api-key "your-cedar-key" \
  --bioportal-api-key "your-bioportal-key"
```

### Option 3: Using Environment Variables

Set environment variables instead of command-line arguments:

```bash
# Set environment variables
export CEDAR_API_KEY="your-cedar-key"
export BIOPORTAL_API_KEY="your-bioportal-key"

# Run with uvx
uvx --from git+https://github.com/musen-lab/cedar-mcp.git cedar-mcp

# Or run locally
uv run python -m cedar_mcp.server
```

## Using with Claude Code

Add the CEDAR MCP server to Claude Code:

```bash
# Add using uvx (from Git repository)
claude mcp add cedar-mcp --uvx --from git+https://github.com/musen-lab/cedar-mcp.git \
  --cedar-api-key "your-cedar-key" \
  --bioportal-api-key "your-bioportal-key"
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
        "--from", 
        "git+https://github.com/musen-lab/cedar-mcp.git",
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