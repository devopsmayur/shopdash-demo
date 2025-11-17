# Backend Unit Tests

## Overview
Comprehensive unit tests for `app.py` covering all endpoints, security scenarios, edge cases, and error handling.

## Test Coverage

### Endpoints Tested
- `/health` - Health check endpoint
- `/login` - Authentication endpoint (with security fixes)
- `/price` - Product price lookup endpoint
- `/calc` - Calculator endpoint

### Test Categories

1. **TestHealthEndpoint** - Health check functionality
2. **TestLoginEndpoint** - Authentication with focus on SQL injection prevention
3. **TestPriceEndpoint** - Product price queries
4. **TestCalcEndpoint** - Calculator operations
5. **TestGetDbFunction** - Database connection handling
6. **TestAppConfiguration** - Flask app configuration
7. **TestEndpointMethods** - HTTP method restrictions
8. **TestResponseContentTypes** - JSON response validation
9. **TestSecurityConcerns** - Security vulnerability documentation
10. **TestEdgeCases** - Boundary conditions and edge cases
11. **TestDatabaseConnectionHandling** - Connection lifecycle management

### Security Tests
- SQL injection prevention in login endpoint (FIXED)
- SQL injection vulnerability in price endpoint (DOCUMENTED)
- Arbitrary code execution in calc endpoint (DOCUMENTED)
- Weak MD5 password hashing (DOCUMENTED)

## Installation

Install testing dependencies:
```bash
pip install -r requirements-test.txt
```

## Running Tests

Run all tests:
```bash
pytest test_app.py -v
```

Run with coverage report:
```bash
pytest test_app.py -v --cov=app --cov-report=html
```

Run specific test class:
```bash
pytest test_app.py::TestLoginEndpoint -v
```

Run specific test:
```bash
pytest test_app.py::TestLoginEndpoint::test_login_successful_with_valid_credentials -v
```

## Test Statistics

- **Total Tests**: 80+
- **Test Classes**: 11
- **Lines of Test Code**: 900+

## Key Security Findings

### Fixed Issues ✅
- Login endpoint now uses parameterized queries to prevent SQL injection

### Remaining Issues ⚠️
1. **Price endpoint**: SQL injection vulnerability (line 39)
2. **Calc endpoint**: Arbitrary code execution via eval() (line 49)
3. **Password hashing**: MD5 is cryptographically broken (line 23)
4. **Database connection**: Uses invalid `connect13` instead of `connect` (line 11)

## Test Design

- Uses pytest fixtures for test client and database setup
- Mocks database connections to avoid external dependencies
- Tests both happy paths and error conditions
- Validates security vulnerabilities are fixed or documented
- Includes edge cases like null bytes, unicode, and extremely long inputs
- Tests concurrent request handling
- Validates proper resource cleanup (database connections)

## Contributing

When adding new endpoints or functionality to `app.py`, ensure:
1. Add corresponding test class
2. Test happy path, error cases, and edge cases
3. Test security implications
4. Mock external dependencies
5. Validate resource cleanup
6. Use descriptive test names

## Notes

- Tests use mocking to avoid requiring an actual database
- Some tests document existing vulnerabilities rather than asserting they don't exist
- The test suite serves both as validation and security documentation