# Integration Tests for CEDAR MCP Server

This directory contains comprehensive integration tests for the CEDAR MCP server that test real API interactions with both CEDAR and BioPortal APIs.

## Prerequisites

### 1. Install Test Dependencies

```bash
pip install -r requirements-dev.txt
```

### 2. Set Up API Keys

Create a `.env.test` file in the project root with your actual API keys:

```bash
# .env.test
CEDAR_API_KEY=your-cedar-api-key-here
BIOPORTAL_API_KEY=your-bioportal-api-key-here
```

**Important:** Never commit `.env.test` to version control. It's already in `.gitignore`.

### 3. Get API Keys

#### CEDAR API Key
1. Go to [cedar.metadatacenter.org](https://cedar.metadatacenter.org)
2. Create an account or log in
3. Click on the person icon → Profile
4. Copy your API key from the profile page

#### BioPortal API Key
1. Go to [bioportal.bioontology.org](https://bioportal.bioontology.org)
2. Create an account or log in
3. Go to Account Settings → API Key
4. Copy your API key

## Running Tests

### Run All Tests
```bash
pytest
```

### Run Integration Tests Only
```bash
pytest -m integration
```

### Run Unit Tests Only
```bash
pytest -m unit
```

### Run Tests with Coverage
```bash
pytest --cov=src/cedar_mcp --cov-report=html
```

### Run Specific Test Files
```bash
# Test external API functions
pytest test/test_external_api.py

# Test processing functions  
pytest test/test_processing.py

# Test server functions
pytest test/test_server.py
```

### Run Specific Test Classes
```bash
pytest test/test_external_api.py::TestGetChildrenFromBranch
```

### Run Specific Test Methods
```bash
pytest test/test_external_api.py::TestGetChildrenFromBranch::test_get_children_valid_branch
```

### Skip Slow Tests
```bash
pytest -m "not slow"
```

## Test Categories

### Integration Tests (`@pytest.mark.integration`)
- Test real API calls to CEDAR and BioPortal
- Require actual API keys in `.env.test`
- May be slower due to network requests
- Test actual data transformation with real responses

### Unit Tests (`@pytest.mark.unit`)
- Test logic without external API dependencies
- Use mocked data and responses
- Fast execution
- Test edge cases and error handling

### Slow Tests (`@pytest.mark.slow`)
- Tests that take longer to run (>5 seconds)
- Complex API interactions
- Large data processing

## Troubleshooting

### Tests Skipped Due to Missing API Keys
```
SKIPPED [1] test/conftest.py:15: CEDAR_API_KEY not found in .env.test
```
**Solution**: Create `.env.test` file with valid API keys.

### Network Timeout Errors
```
requests.exceptions.ConnectTimeout: HTTPSConnectionPool
```
**Solution**: Check internet connection and API service status.

### Authentication Errors
```
401 Unauthorized
```
**Solution**: Verify API keys are valid and not expired.

### BioPortal Rate Limiting
```
429 Too Many Requests
```
**Solution**: Add delays between tests or reduce test frequency.

## Contributing

When adding new tests:

1. **Follow Naming Convention**: `test_*.py` files, `test_*` functions
2. **Add Appropriate Markers**: `@pytest.mark.integration` or `@pytest.mark.unit`
3. **Handle API Failures Gracefully**: Use try/except and meaningful assertions
4. **Document Test Purpose**: Clear docstrings explaining what each test validates
5. **Use Fixtures**: Reuse existing fixtures or create new ones in `conftest.py`

## Using the Test Runner

The project includes a convenient test runner script:

```bash
# Run all tests
python run_tests.py

# Run only integration tests
python run_tests.py --integration

# Run only unit tests (no API calls)
python run_tests.py --unit

# Run fast tests (excluding slow ones)
python run_tests.py --fast

# Run with coverage report
python run_tests.py --coverage

# Run specific test modules
python run_tests.py --external-api
python run_tests.py --processing
python run_tests.py --server

# Run with verbose output
python run_tests.py --verbose

# Run without warnings
python run_tests.py --no-warnings
```
