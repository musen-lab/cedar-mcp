# CEDAR MCP Server

A Model Context Protocol (MCP) server for interacting with the CEDAR (Center for Expanded Data Annotation and Retrieval) metadata repository.


## Available Tools

### get_template
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

### Running Tests

This project includes comprehensive integration tests that validate real API interactions with both CEDAR and BioPortal APIs.

For detailed testing information, see [test/README.md](test/README.md).

## Contributing

Contributions are welcome! Please ensure all tests pass before submitting a Pull Request:

```bash
python run_tests.py --integration
```