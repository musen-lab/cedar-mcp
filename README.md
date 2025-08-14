# CEDAR MCP Server

A Model Context Protocol (MCP) server for interacting with the CEDAR (Center for Expanded Data Annotation and Retrieval) metadata repository.


## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/cedar-mcp.git
cd cedar-mcp
```

2. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

Set your CEDAR API key as an environment variable:

```bash
export CEDAR_API_KEY="your-api-key-here"
```

Or create a `.env` file in the project root:
```
CEDAR_API_KEY=your-api-key-here
```

## Usage

### Running the Server

```bash
python src/server.py
```

Or provide the API key via command line:
```bash
python src/server.py --cedar-api-key "your-api-key-here"
```

### Available Tools

#### get_template
Fetches a template from the CEDAR repository.

**Parameters:**
- `template_id` (str): The template ID or full URL from CEDAR repository

**Example:**
```python
template_id = "https://repo.metadatacenter.org/templates/e019284e-48d1-4494-bc83-ddefd28dfbac"
result = get_template(template_id)
```

## Development

### Install Development Dependencies

```bash
pip install -r requirements-dev.txt
```

## Dependencies

- **fastmcp**: MCP server framework
- **requests**: HTTP client for CEDAR API calls
- **python-dotenv**: Environment variable management


## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.