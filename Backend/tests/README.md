# TimeWell Backend Tests

This directory contains tests for the TimeWell backend application.

## Running Tests

To run all tests:

```bash
python -m pytest
```

To run a specific test file:

```bash
python -m pytest tests/test_users.py
```

To run with verbose output:

```bash
python -m pytest -v
```

## Test Files

- `test_database.py`: Tests for database connectivity
- `test_users.py`: Tests for user-related functionality (create, retrieve, authenticate)
- `test_user_endpoints.py`: Tests for the user API endpoints (requires more work)

## Notes

### Working Tests

The following tests are fully working:

- `test_database.py` - Tests for database connectivity
- `test_users.py` - Tests for user model/service functions

### Tests Needing Work

The endpoint tests in `test_user_endpoints.py` need improvement to work with FastAPI's TestClient. The main challenge is dealing with asynchronous database operations in the FastAPI routes during testing.

Possible solutions:
1. Use dependency overrides to replace database functions with mocks
2. Use a separate test database with a clear separation between test data
3. Create a test-specific FastAPI app instance

### Troubleshooting

If you encounter the error `ImportError: cannot import name '_QUERY_OPTIONS' from 'pymongo.cursor'`, make sure you have compatible versions of pymongo and motor:

```bash
pip install pymongo==4.5.0 motor==3.2.0
``` 